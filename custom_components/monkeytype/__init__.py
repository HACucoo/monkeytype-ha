"""Monkeytype integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypedDict

import aiohttp

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BASE_URL,
    CLIENT_VERSION,
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_MODE,
    CONF_MODE2,
    DEFAULT_LANGUAGE,
    DEFAULT_MODE,
    DEFAULT_MODE2,
    DOMAIN,
    SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

INITIAL_REFRESH_DELAY = 30  # seconds
RATE_LIMIT_FALLBACK_MINUTES = 30
RATE_LIMIT_BUFFER_SECONDS = 10


class MonkeytypeData(TypedDict):
    today_best_wpm: float | None
    rank: int | None
    daily_rank: int | None


class _RateLimitError(Exception):
    """Raised when Monkeytype returns 479."""

    def __init__(self, reset_ts: int | None = None) -> None:
        self.reset_ts = reset_ts


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the Lovelace card as a static asset (once per HA start)."""
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/monkeytype/monkeytype-card.js",
            str(Path(__file__).parent / "www" / "monkeytype-card.js"),
            cache_headers=False,
        )
    ])
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = MonkeytypeCoordinator(hass, entry.data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # First refresh in background after a short delay – avoids a burst right
    # after the config_flow validation request and keeps HA startup non-blocking.
    async def _delayed_refresh() -> None:
        await asyncio.sleep(INITIAL_REFRESH_DELAY)
        await coordinator.async_refresh()

    entry.async_create_background_task(
        hass, _delayed_refresh(), "monkeytype_initial_refresh"
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False


class MonkeytypeCoordinator(DataUpdateCoordinator[MonkeytypeData]):
    """Fetches data from the Monkeytype API."""

    def __init__(self, hass: HomeAssistant, data: dict) -> None:
        self._default_interval = timedelta(minutes=SCAN_INTERVAL_MINUTES)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=self._default_interval,
        )
        self._api_key: str = data[CONF_API_KEY]
        self._mode: str = data.get(CONF_MODE, DEFAULT_MODE)
        self._mode2: str = data.get(CONF_MODE2, DEFAULT_MODE2)
        self._language: str = data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"ApeKey {self._api_key}",
            "X-Client-Version": CLIENT_VERSION,
        }

    async def _async_update_data(self) -> MonkeytypeData:
        try:
            session = async_get_clientsession(self.hass)
            today_wpm = await self._fetch_today_best_wpm(session)
            rank = await self._fetch_rank(session, "/leaderboards/rank")
            daily_rank = await self._fetch_rank(session, "/daily/rank")
        except _RateLimitError as err:
            self._apply_rate_limit_backoff(err.reset_ts)
            if self.data:
                return self.data
            raise UpdateFailed("Monkeytype rate limit hit on first fetch – will retry")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Monkeytype API: {err}") from err

        # Successful fetch – restore normal poll interval
        self.update_interval = self._default_interval
        return MonkeytypeData(today_best_wpm=today_wpm, rank=rank, daily_rank=daily_rank)

    def _apply_rate_limit_backoff(self, reset_ts: int | None) -> None:
        if reset_ts:
            wait = max(60, reset_ts - int(datetime.now(tz=timezone.utc).timestamp()))
            self.update_interval = timedelta(seconds=wait + RATE_LIMIT_BUFFER_SECONDS)
            _LOGGER.warning(
                "Monkeytype rate limit hit – next retry in %d min %d sec",
                wait // 60, wait % 60,
            )
        else:
            self.update_interval = timedelta(minutes=RATE_LIMIT_FALLBACK_MINUTES)
            _LOGGER.warning(
                "Monkeytype rate limit hit – backing off for %d min",
                RATE_LIMIT_FALLBACK_MINUTES,
            )

    async def _request(
        self,
        session: aiohttp.ClientSession,
        path: str,
        params: dict[str, Any],
    ) -> dict | None:
        """Single GET with shared status-code handling. Returns parsed JSON or None for 404/204."""
        async with session.get(
            f"{BASE_URL}{path}", headers=self._headers, params=params
        ) as resp:
            if resp.status in (204, 404):
                return None
            if resp.status == 401:
                raise ConfigEntryAuthFailed("Invalid ApeKey")
            if resp.status == 471:
                raise UpdateFailed("ApeKey is inactive – enable it on monkeytype.com")
            if resp.status == 479:
                reset_ts = resp.headers.get("x-ratelimit-reset")
                raise _RateLimitError(int(reset_ts) if reset_ts else None)
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_today_best_wpm(self, session: aiohttp.ClientSession) -> float | None:
        # Use the API's onOrAfterTimestamp filter so we only fetch today's results
        start_of_today = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_ts_ms = int(start_of_today.timestamp() * 1000)

        payload = await self._request(
            session,
            "/results",
            {"limit": 100, "onOrAfterTimestamp": start_ts_ms},
        )
        results = (payload or {}).get("data") or []
        wpms = [
            r["wpm"]
            for r in results
            if r.get("mode") == self._mode
            and str(r.get("mode2", "")) == str(self._mode2)
        ]
        return round(max(wpms), 2) if wpms else None

    async def _fetch_rank(
        self, session: aiohttp.ClientSession, path: str
    ) -> int | None:
        payload = await self._request(
            session,
            path,
            {"language": self._language, "mode": self._mode, "mode2": self._mode2},
        )
        entry = (payload or {}).get("data")
        return entry.get("rank") if entry else None

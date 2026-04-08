"""Monkeytype integration for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.http import StaticPathConfig

from .const import (
    DOMAIN,
    BASE_URL,
    CLIENT_VERSION,
    SCAN_INTERVAL_MINUTES,
    CONF_API_KEY,
    CONF_MODE,
    CONF_MODE2,
    CONF_LANGUAGE,
    DEFAULT_MODE,
    DEFAULT_MODE2,
    DEFAULT_LANGUAGE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


class _RateLimitError(Exception):
    """Raised when Monkeytype returns 479."""
    def __init__(self, reset_ts: int | None = None) -> None:
        self.reset_ts = reset_ts


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the Lovelace card as a static asset."""
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
    # First refresh in background after a short delay to avoid rate limiting
    # the config_flow validation request that just ran.
    async def _delayed_refresh():
        await asyncio.sleep(30)
        await coordinator.async_refresh()

    entry.async_create_background_task(
        hass,
        _delayed_refresh(),
        "monkeytype_initial_refresh",
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


class MonkeytypeCoordinator(DataUpdateCoordinator):
    """Fetches data from Monkeytype API."""

    def __init__(self, hass: HomeAssistant, data: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._api_key = data[CONF_API_KEY]
        self._mode = data.get(CONF_MODE, DEFAULT_MODE)
        self._mode2 = data.get(CONF_MODE2, DEFAULT_MODE2)
        self._language = data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        self._default_interval = timedelta(minutes=SCAN_INTERVAL_MINUTES)

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"ApeKey {self._api_key}",
            "X-Client-Version": CLIENT_VERSION,
        }

    async def _async_update_data(self) -> dict:
        try:
            session = async_get_clientsession(self.hass)
            today_wpm = await self._fetch_today_best_wpm(session)
            rank = await self._fetch_rank(session)
            # Successful fetch – restore normal interval
            self.update_interval = self._default_interval
            return {
                "today_best_wpm": today_wpm,
                "rank": rank,
            }
        except _RateLimitError as err:
            self._apply_rate_limit_backoff(err.reset_ts)
            if self.data:
                return self.data
            raise UpdateFailed("Monkeytype rate limit hit on first fetch – will retry")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Monkeytype API: {err}") from err

    def _apply_rate_limit_backoff(self, reset_ts: int | None) -> None:
        if reset_ts:
            wait = max(60, reset_ts - int(datetime.now(tz=timezone.utc).timestamp()))
            self.update_interval = timedelta(seconds=wait + 10)
            _LOGGER.warning(
                "Monkeytype rate limit hit – next retry in %d min %d sec",
                wait // 60, wait % 60,
            )
        else:
            # No reset timestamp – back off for 30 minutes
            self.update_interval = timedelta(minutes=30)
            _LOGGER.warning("Monkeytype rate limit hit – backing off for 30 min")

    async def _fetch_today_best_wpm(self, session: aiohttp.ClientSession) -> float | None:
        url = f"{BASE_URL}/results"
        params = {"limit": 100}

        async with session.get(url, headers=self.headers, params=params) as resp:
            if resp.status == 401:
                raise UpdateFailed("Invalid ApeKey – check your API key")
            if resp.status == 479:
                reset_ts = resp.headers.get("x-ratelimit-reset")
                raise _RateLimitError(int(reset_ts) if reset_ts else None)
            resp.raise_for_status()
            data = await resp.json()

        results = (data or {}).get("data") or []
        if not results:
            return None

        now = datetime.now(tz=timezone.utc)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = start_of_today.timestamp() * 1000

        today_wpms = [
            r["wpm"]
            for r in results
            if r.get("timestamp", 0) >= start_ts
            and r.get("mode") == self._mode
            and str(r.get("mode2", "")) == str(self._mode2)
        ]

        return round(max(today_wpms), 2) if today_wpms else None

    async def _fetch_rank(self, session: aiohttp.ClientSession) -> int | None:
        url = f"{BASE_URL}/leaderboards/rank"
        params = {
            "language": self._language,
            "mode": self._mode,
            "mode2": self._mode2,
        }

        async with session.get(url, headers=self.headers, params=params) as resp:
            if resp.status in (404, 204):
                return None
            if resp.status == 401:
                raise UpdateFailed("Invalid ApeKey – check your API key")
            if resp.status == 479:
                reset_ts = resp.headers.get("x-ratelimit-reset")
                raise _RateLimitError(int(reset_ts) if reset_ts else None)
            resp.raise_for_status()
            data = await resp.json()
            _LOGGER.debug("Leaderboard rank response (%s): %s", resp.status, data)

        entry = (data or {}).get("data")
        return entry.get("rank") if entry else None

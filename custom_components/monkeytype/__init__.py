"""Monkeytype integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    BASE_URL,
    SCAN_INTERVAL_MINUTES,
    CONF_API_KEY,
    CONF_MODE,
    CONF_MODE2,
    CONF_LANGUAGE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for entry_config in config[DOMAIN] if isinstance(config[DOMAIN], list) else [config[DOMAIN]]:
        coordinator = MonkeytypeCoordinator(hass, entry_config)
        await coordinator.async_refresh()
        hass.data[DOMAIN][entry_config[CONF_API_KEY]] = coordinator

        hass.async_create_task(
            hass.helpers.discovery.async_load_platform("sensor", DOMAIN, entry_config, config)
        )

    return True


class MonkeytypeCoordinator(DataUpdateCoordinator):
    """Fetches data from Monkeytype API."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._api_key = config[CONF_API_KEY]
        self._mode = config.get(CONF_MODE, "time")
        self._mode2 = config.get(CONF_MODE2, "60")
        self._language = config.get(CONF_LANGUAGE, "english")

    @property
    def headers(self) -> dict:
        return {"Authorization": f"ApeKey {self._api_key}"}

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                today_wpm = await self._fetch_today_best_wpm(session)
                rank = await self._fetch_rank(session)
            return {
                "today_best_wpm": today_wpm,
                "rank": rank,
            }
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Monkeytype API: {err}") from err

    async def _fetch_today_best_wpm(self, session: aiohttp.ClientSession) -> float | None:
        """Fetch results and return today's highest WPM."""
        url = f"{BASE_URL}/users/results"
        params = {"limit": 100}

        async with session.get(url, headers=self.headers, params=params) as resp:
            if resp.status == 401:
                raise UpdateFailed("Invalid ApeKey – check your API key")
            resp.raise_for_status()
            data = await resp.json()

        results = data.get("data", [])
        if not results:
            return None

        now = datetime.now(tz=timezone.utc)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_ts = start_of_today.timestamp() * 1000  # API uses milliseconds

        today_wpms = [
            r["wpm"]
            for r in results
            if r.get("timestamp", 0) >= start_ts
            and r.get("mode") == self._mode
            and str(r.get("mode2", "")) == str(self._mode2)
        ]

        return round(max(today_wpms), 2) if today_wpms else None

    async def _fetch_rank(self, session: aiohttp.ClientSession) -> int | None:
        """Fetch the user's leaderboard rank."""
        url = f"{BASE_URL}/leaderboards/rank"
        params = {
            "language": self._language,
            "mode": self._mode,
            "mode2": self._mode2,
        }

        async with session.get(url, headers=self.headers, params=params) as resp:
            if resp.status in (404, 204):
                return None  # user not on leaderboard
            if resp.status == 401:
                raise UpdateFailed("Invalid ApeKey – check your API key")
            resp.raise_for_status()
            data = await resp.json()

        return data.get("data", {}).get("rank")

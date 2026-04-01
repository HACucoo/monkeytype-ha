"""Monkeytype sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_API_KEY, CONF_MODE, CONF_MODE2, CONF_LANGUAGE
from . import MonkeytypeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up sensors from configuration.yaml discovery."""
    if discovery_info is None:
        return

    api_key = discovery_info[CONF_API_KEY]
    coordinator: MonkeytypeCoordinator = hass.data[DOMAIN][api_key]

    mode = discovery_info.get(CONF_MODE, "time")
    mode2 = discovery_info.get(CONF_MODE2, "60")
    language = discovery_info.get(CONF_LANGUAGE, "english")
    label = f"{mode}{mode2}_{language}"

    async_add_entities([
        MonkeytypeTodayBestWpmSensor(coordinator, label),
        MonkeytypeRankSensor(coordinator, label),
    ], update_before_add=True)


class MonkeytypeTodayBestWpmSensor(CoordinatorEntity, SensorEntity):
    """Sensor for today's highest WPM."""

    _attr_icon = "mdi:keyboard"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "WPM"

    def __init__(self, coordinator: MonkeytypeCoordinator, label: str) -> None:
        super().__init__(coordinator)
        self._label = label
        self._attr_name = f"Monkeytype Today Best WPM ({label})"
        self._attr_unique_id = f"monkeytype_today_best_wpm_{label}"

    @property
    def native_value(self):
        return self.coordinator.data.get("today_best_wpm") if self.coordinator.data else None


class MonkeytypeRankSensor(CoordinatorEntity, SensorEntity):
    """Sensor for leaderboard rank."""

    _attr_icon = "mdi:podium"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: MonkeytypeCoordinator, label: str) -> None:
        super().__init__(coordinator)
        self._label = label
        self._attr_name = f"Monkeytype Rank ({label})"
        self._attr_unique_id = f"monkeytype_rank_{label}"

    @property
    def native_value(self):
        return self.coordinator.data.get("rank") if self.coordinator.data else None

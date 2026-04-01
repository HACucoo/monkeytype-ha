"""Monkeytype sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_MODE, CONF_MODE2, CONF_LANGUAGE, DEFAULT_MODE, DEFAULT_MODE2, DEFAULT_LANGUAGE
from . import MonkeytypeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: MonkeytypeCoordinator = hass.data[DOMAIN][entry.entry_id]

    mode = entry.data.get(CONF_MODE, DEFAULT_MODE)
    mode2 = entry.data.get(CONF_MODE2, DEFAULT_MODE2)
    language = entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    label = f"{mode}{mode2}_{language}"

    async_add_entities([
        MonkeytypeTodayBestWpmSensor(coordinator, label),
        MonkeytypeRankSensor(coordinator, label),
    ])


class MonkeytypeTodayBestWpmSensor(CoordinatorEntity, SensorEntity):
    """Sensor for today's highest WPM."""

    _attr_icon = "mdi:keyboard"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "WPM"

    def __init__(self, coordinator: MonkeytypeCoordinator, label: str) -> None:
        super().__init__(coordinator)
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
        self._attr_name = f"Monkeytype Rank ({label})"
        self._attr_unique_id = f"monkeytype_rank_{label}"

    @property
    def native_value(self):
        return self.coordinator.data.get("rank") if self.coordinator.data else None

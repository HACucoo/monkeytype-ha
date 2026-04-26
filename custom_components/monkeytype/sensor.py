"""Monkeytype sensors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MonkeytypeCoordinator, MonkeytypeData
from .const import (
    CONF_LANGUAGE,
    CONF_MODE,
    CONF_MODE2,
    DEFAULT_LANGUAGE,
    DEFAULT_MODE,
    DEFAULT_MODE2,
    DOMAIN,
)


@dataclass(frozen=True, kw_only=True)
class MonkeytypeSensorDescription(SensorEntityDescription):
    """Describes a Monkeytype sensor."""

    value_fn: Callable[[MonkeytypeData], float | int | None]


SENSOR_DESCRIPTIONS: tuple[MonkeytypeSensorDescription, ...] = (
    MonkeytypeSensorDescription(
        key="today_best_wpm",
        translation_key="today_best_wpm",
        name="Today Best WPM",
        icon="mdi:keyboard",
        native_unit_of_measurement="WPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("today_best_wpm"),
    ),
    MonkeytypeSensorDescription(
        key="rank",
        translation_key="rank",
        name="Rank",
        icon="mdi:podium",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("rank"),
    ),
    MonkeytypeSensorDescription(
        key="daily_rank",
        translation_key="daily_rank",
        name="Daily Rank",
        icon="mdi:podium-gold",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("daily_rank"),
    ),
)


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

    async_add_entities(
        MonkeytypeSensor(coordinator, description, label)
        for description in SENSOR_DESCRIPTIONS
    )


class MonkeytypeSensor(CoordinatorEntity[MonkeytypeCoordinator], SensorEntity):
    """A single Monkeytype sensor – behaviour driven by SENSOR_DESCRIPTIONS."""

    entity_description: MonkeytypeSensorDescription

    def __init__(
        self,
        coordinator: MonkeytypeCoordinator,
        description: MonkeytypeSensorDescription,
        label: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"Monkeytype {description.name} ({label})"
        self._attr_unique_id = f"monkeytype_{description.key}_{label}"

    @property
    def native_value(self) -> float | int | None:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

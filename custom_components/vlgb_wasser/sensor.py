"""
Quellennachweis/Data Source Disclaimer
Datenquelle/Fetches data from „Amt der Vorarlberger Landesregierung, Abt. VIId Wasserwirtschaft
https://www.vorarlberg.at/abfluss
Es wird keinerlei Gewährleistung für die zur Verfügung gestellten Messwerte übernommen. Alle Daten sind ungeprüft und haben den Status von Rohdaten.
Wir weisen ausdrücklich darauf hin, dass wir hinsichtlich Verfügbarkeit, Performance oder Kontinuität des Dienstes keine Garantie übernehmen können.
"""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VlbgWasserDataUpdateCoordinator
from .const import DOMAIN, RIVER_STATIONS, MEASUREMENT_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: VlbgWasserDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    # For now, create a single sensor for the hardcoded station
    # In future versions, this will be dynamic based on configuration
    sensors = [VlbgWasserSensor(coordinator, "200014", "w")]
    
    async_add_entities(sensors)


class VlbgWasserSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Vorarlberg Wasser sensor."""

    def __init__(
        self,
        coordinator: VlbgWasserDataUpdateCoordinator,
        station_id: str,
        measurement_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._measurement_type = measurement_type
        
        # Find station info from constants
        station_info = None
        for station in RIVER_STATIONS:
            if station["id"] == station_id:
                station_info = station
                break
        
        self._station_info = station_info
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{measurement_type}"
        
        # Set sensor name
        if station_info:
            station_name = station_info["name"]
            river_name = station_info["river"]
            measurement_name = MEASUREMENT_TYPES.get(measurement_type, measurement_type)
            self._attr_name = f"{river_name} {station_name} {measurement_name.title()}"
        else:
            self._attr_name = f"Station {station_id} {measurement_type.upper()}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("latest_value")
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.coordinator.data:
            unit = self.coordinator.data.get("unit", "")
            # Map API units to Home Assistant units
            if unit.lower() == "cm":
                return UnitOfLength.CENTIMETERS
            return unit
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        if self._measurement_type == "w":  # Water depth
            return SensorDeviceClass.DISTANCE
        elif self._measurement_type == "wt":  # Water temperature
            return SensorDeviceClass.TEMPERATURE
        elif self._measurement_type == "q":  # Water flow
            return None  # No specific device class for flow rate
        return None

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class."""
        return SensorStateClass.MEASUREMENT

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        attrs = {}
        
        if self.coordinator.data:
            attrs.update({
                "station_id": self._station_id,
                "parameter": self.coordinator.data.get("parameter"),
                "timezone": self.coordinator.data.get("timezone"),
                "last_updated": self.coordinator.data.get("latest_time"),
                "measurement_type": self._measurement_type,
            })
            
        if self._station_info:
            attrs.update({
                "station_name": self._station_info["name"],
                "river": self._station_info["river"],
            })
            
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def device_info(self):
        """Return device information."""
        if self._station_info:
            return {
                "identifiers": {(DOMAIN, self._station_id)},
                "name": f"{self._station_info['river']} {self._station_info['name']}",
                "manufacturer": "Vorarlberg Wasser",
                "model": "Water Monitoring Station",
                "sw_version": "1.0.0",
            }
        return None
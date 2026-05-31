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

from . import VlbgWasserDataUpdateCoordinator, BodenseeDataUpdateCoordinator
from .const import DOMAIN, RIVER_STATIONS, MEASUREMENT_TYPES, BODENSEE_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinators = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: VlbgWasserDataUpdateCoordinator = coordinators["river"]
    bodensee_coordinator: BodenseeDataUpdateCoordinator = coordinators["bodensee"]

    station_map = {s["id"]: s for s in RIVER_STATIONS}
    mtype_capabilities = {"w": "supports_depth", "q": "supports_flow", "wt": "supports_temperature"}

    sensors = []
    for station_id in config_entry.data.get("station_ids", []):
        station = station_map.get(station_id)
        if not station:
            continue
        for mtype, cap in mtype_capabilities.items():
            if station[cap]:
                sensors.append(VlbgWasserSensor(coordinator, station_id, mtype))

    for sensor_def in BODENSEE_SENSORS:
        sensors.append(BodenseeSensor(bodensee_coordinator, sensor_def))

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

    def _measurement(self) -> dict:
        """Return this sensor's slice of coordinator data."""
        if not self.coordinator.data:
            return {}
        return self.coordinator.data.get(self._station_id, {}).get(self._measurement_type, {})

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self._measurement().get("latest_value")

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        unit = self._measurement().get("unit", "")
        if unit.lower() == "cm":
            return UnitOfLength.CENTIMETERS
        return unit or None

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
        attrs = {"station_id": self._station_id, "measurement_type": self._measurement_type}
        m = self._measurement()
        if m:
            attrs.update({
                "parameter": m.get("parameter"),
                "timezone": m.get("timezone"),
                "last_updated": m.get("latest_time"),
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
        return (
            self.coordinator.last_update_success
            and bool(self._measurement())
        )

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


class BodenseeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Bodensee sensor."""

    def __init__(
        self,
        coordinator: BodenseeDataUpdateCoordinator,
        sensor_def: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = sensor_def["key"]
        self._unit = sensor_def["unit"]
        self._device_class = sensor_def["device_class"]
        self._attr_unique_id = f"{DOMAIN}_{self._key}"
        self._attr_name = self._key.replace("_", " ").title()
        if sensor_def.get("icon"):
            self._attr_icon = sensor_def["icon"]

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        return self._device_class

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class."""
        return SensorStateClass.MEASUREMENT

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "bodensee")},
            "name": "Bodensee Bregenz",
            "manufacturer": "Wasserwirtschaft Vorarlberg",
            "model": "Lake Monitoring Station",
        }
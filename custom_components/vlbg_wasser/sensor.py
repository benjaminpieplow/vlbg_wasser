"""
Quellennachweis/Data Source Disclaimer
Datenquelle/Fetches data from „Amt der Vorarlberger Landesregierung, Abt. VIId Wasserwirtschaft
https://www.vorarlberg.at/abfluss
Es wird keinerlei Gewährleistung für die zur Verfügung gestellten Messwerte übernommen. Alle Daten sind ungeprüft und haben den Status von Rohdaten.
Wir weisen ausdrücklich darauf hin, dass wir hinsichtlich Verfügbarkeit, Performance oder Kontinuität des Dienstes keine Garantie übernehmen können.
"""

from __future__ import annotations

import logging

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
from .const import DOMAIN, RIVER_STATIONS, MEASUREMENT_TYPES, ALL_MEASUREMENT_TYPES, BODENSEE_SENSORS

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

    capabilities = config_entry.data.get("capabilities", {})

    sensors = []
    for station_id in config_entry.data.get("station_ids", []):
        station_caps = capabilities.get(station_id, {})
        for mtype in ALL_MEASUREMENT_TYPES:
            enabled = station_caps.get(mtype, True)
            sensors.append(VlbgWasserSensor(coordinator, station_id, mtype, enabled))

    for sensor_def in BODENSEE_SENSORS:
        sensors.append(BodenseeSensor(bodensee_coordinator, sensor_def))

    async_add_entities(sensors)


_STATION_MAP = {s["id"]: s for s in RIVER_STATIONS}


class VlbgWasserSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Vorarlberg Wasser sensor."""

    def __init__(
        self,
        coordinator: VlbgWasserDataUpdateCoordinator,
        station_id: str,
        measurement_type: str,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._measurement_type = measurement_type
        self._enabled_default = enabled_default

        self._station_info = _STATION_MAP.get(station_id)
        self._attr_unique_id = f"{DOMAIN}_{station_id}_{measurement_type}"

        if self._station_info:
            station_name = self._station_info["name"]
            river_name = self._station_info["river"]
            measurement_name = MEASUREMENT_TYPES.get(measurement_type, measurement_type)
            self._attr_name = f"{river_name} {station_name} {measurement_name.title()}"
        else:
            self._attr_name = f"Station {station_id} {measurement_type.upper()}"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return whether the entity should be enabled when first added."""
        return self._enabled_default

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
        if self._measurement_type == "w":
            return SensorDeviceClass.DISTANCE
        if self._measurement_type == "wt":
            return SensorDeviceClass.TEMPERATURE
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

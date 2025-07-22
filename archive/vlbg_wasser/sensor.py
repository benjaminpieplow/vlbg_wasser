"""
Quellennachweis/Data Source Disclaimer
Datenquelle/Fetches data from „Amt der Vorarlberger Landesregierung, Abt. VIId Wasserwirtschaft
https://www.vorarlberg.at/abfluss
Es wird keinerlei Gewährleistung für die zur Verfügung gestellten Messwerte übernommen. Alle Daten sind ungeprüft und haben den Status von Rohdaten.
Wir weisen ausdrücklich darauf hin, dass wir hinsichtlich Verfügbarkeit, Performance oder Kontinuität des Dienstes keine Garantie übernehmen können.
"""


from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VOWIS sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Always add bodensee sensors - these are enabled by default
    # Bodensee provides comprehensive weather and water data
    bodensee_sensors = [
        VowisBodenseeSensor(coordinator, "air_humidity", "Air Humidity", PERCENTAGE, SensorDeviceClass.HUMIDITY),
        VowisBodenseeSensor(coordinator, "air_temperature", "Air Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        VowisBodenseeSensor(coordinator, "water_level", "Water Level", "cm", None),
        VowisBodenseeSensor(coordinator, "water_temperature", "Water Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        VowisBodenseeSensor(coordinator, "water_temperature_05m", "Water Temperature 0.5m", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        VowisBodenseeSensor(coordinator, "water_temperature_25m", "Water Temperature 2.5m", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
        VowisBodenseeSensor(coordinator, "wind_speed", "Wind Speed", UnitOfSpeed.KILOMETERS_PER_HOUR, SensorDeviceClass.WIND_SPEED),
        VowisBodenseeSensor(coordinator, "wind_direction", "Wind Direction", DEGREE, None),
        VowisBodenseeSensor(coordinator, "wind_gust", "Wind Gust", UnitOfSpeed.KILOMETERS_PER_HOUR, SensorDeviceClass.WIND_SPEED),
    ]
    entities.extend(bodensee_sensors)
    
    # Add river sensors only for stations enabled by the user
    # This helps reduce API calls and only monitors relevant stations
    enabled_stations = config_entry.data.get("enabled_stations", [])
    river_stations = config_entry.data.get("river_stations", [])
    
    for station_id in enabled_stations:
        # Find the station configuration
        station_config = next(
            (s for s in river_stations if s["id"] == station_id),
            None
        )
        
        if not station_config:
            _LOGGER.warning("Station configuration not found for ID: %s", station_id)
            continue
            
        # Create sensors based on what measurements this station supports
        # Not all stations support all measurement types
        if station_config.get("supports_depth", False):
            entities.append(
                VowisRiverSensor(
                    coordinator, station_id, "depth", 
                    f"{station_config['name']} Water Depth",
                    "m", None, station_config
                )
            )
        
        if station_config.get("supports_flow", False):
            entities.append(
                VowisRiverSensor(
                    coordinator, station_id, "flow",
                    f"{station_config['name']} Water Flow",
                    "m³/s", SensorDeviceClass.VOLUME_FLOW_RATE, station_config
                )
            )
        
        if station_config.get("supports_temperature", False):
            entities.append(
                VowisRiverSensor(
                    coordinator, station_id, "temperature",
                    f"{station_config['name']} Water Temperature", 
                    UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, station_config
                )
            )
    
    # Add all entities to Home Assistant
    async_add_entities(entities)


class VowisBodenseeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a VOWIS bodensee sensor.
    
    Bodensee sensors monitor comprehensive weather and water conditions
    for Bodensee (Bodensee). The data comes from a single API
    endpoint that provides all measurements in one JSON response.
    """

    def __init__(
        self,
        coordinator,
        sensor_type: str,
        name: str,
        unit: str,
        device_class: SensorDeviceClass | None,
    ) -> None:
        """Initialize the bodensee sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"Bodensee {name}"
        self._attr_unique_id = f"vowis_bodensee_{sensor_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Map our sensor types to the actual API field names
        # The API uses German field names, so we map them here
        self._field_map = {
            "air_humidity": "luftfeuchte",           # Air humidity
            "air_temperature": "lufttemperatur",     # Air temperature
            "water_level": "wasserstand",            # Water level
            "water_temperature": "wTemperatur",      # Water temperature (surface)
            "water_temperature_05m": "wtMilli05",    # Water temp at 0.5m depth
            "water_temperature_25m": "wtMilli25",    # Water temp at 2.5m depth
            "wind_speed": "windgeschwindigkeit",     # Wind speed
            "wind_direction": "windrichtung",        # Wind direction
            "wind_gust": "windboe",                  # Wind gust
        }

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information for grouping sensors."""
        return {
            "identifiers": {(DOMAIN, "bodensee")},
            "name": "Bodensee Station",
            "manufacturer": "VOWIS",
            "model": "Bodensee Station",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current sensor value.
        
        Extracts the 'wert' (value) field from the API response.
        Returns None if data is unavailable or malformed.
        """
        if not self.coordinator.data or "bodensee" not in self.coordinator.data:
            return None
            
        bodensee_data = self.coordinator.data["bodensee"]
        field_name = self._field_map.get(self._sensor_type)
        
        if not field_name or field_name not in bodensee_data:
            return None
            
        field_data = bodensee_data[field_name]
        
        # API returns data in format: {"datum": "timestamp", "wert": value}
        if isinstance(field_data, dict) and "wert" in field_data:
            return field_data["wert"]
            
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        """Return additional sensor attributes.
        
        Includes timestamp of last measurement and special attributes
        like reference levels for certain measurements.
        """
        if not self.coordinator.data or "bodensee" not in self.coordinator.data:
            return None
            
        bodensee_data = self.coordinator.data["bodensee"]
        field_name = self._field_map.get(self._sensor_type)
        
        if not field_name or field_name not in bodensee_data:
            return None
            
        field_data = bodensee_data[field_name]
        attributes = {}
        
        # Extract timestamp from the measurement data
        if isinstance(field_data, dict) and "datum" in field_data:
            try:
                # Convert ISO timestamp to proper datetime
                timestamp = datetime.fromisoformat(field_data["datum"].replace("Z", "+00:00"))
                attributes["last_updated"] = timestamp.isoformat()
            except (ValueError, TypeError) as e:
                _LOGGER.debug("Failed to parse timestamp for %s: %s", self._sensor_type, e)
        
        # Add special attributes for water level sensor
        # The reference level helps interpret absolute water level measurements
        if self._sensor_type == "water_level" and "pegelnullpunkt" in bodensee_data:
            attributes["reference_level"] = bodensee_data["pegelnullpunkt"]
            attributes["reference_level_unit"] = "m"
        
        return attributes if attributes else None


class VowisRiverSensor(CoordinatorEntity, SensorEntity):
    """Representation of a VOWIS river sensor.
    
    River sensors monitor specific measurements (depth, flow, temperature)
    for individual river monitoring stations. Each measurement type requires
    a separate API call to the messwerte endpoint.
    """

    def __init__(
        self,
        coordinator,
        station_id: str,
        measurement_type: str,
        name: str,
        unit: str,
        device_class: SensorDeviceClass | None,
        station_config: Dict[str, Any],
    ) -> None:
        """Initialize the river sensor."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._measurement_type = measurement_type
        self._station_config = station_config
        self._attr_name = name
        self._attr_unique_id = f"vowis_river_{station_id}_{measurement_type}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information for grouping sensors by station."""
        return {
            "identifiers": {(DOMAIN, f"river_station_{self._station_id}")},
            "name": self._station_config["name"],
            "manufacturer": "VOWIS",
            "model": "River Station",
            "suggested_area": self._station_config["river"],  # Group by river name
        }

    @property
    def native_value(self) -> float | None:
        """Return the current sensor value.
        
        Extracts the most recent measurement value from the API response.
        River data contains time-series measurements, so we take the latest.
        """
        # Check if we have data for this station
        if (not self.coordinator.data or 
            "rivers" not in self.coordinator.data or
            self._station_id not in self.coordinator.data["rivers"]):
            return None
            
        station_data = self.coordinator.data["rivers"][self._station_id]
        
        # Check if this measurement type is available for this station
        if self._measurement_type not in station_data:
            return None
            
        measurement_data = station_data[self._measurement_type]
        
        # Extract the most recent measurement value
        # API format: {"Messwerte": {"2025-06-25T19:00:00": 5.534, ...}}
        if "Messwerte" in measurement_data and measurement_data["Messwerte"]:
            messwerte = measurement_data["Messwerte"]
            if messwerte:
                # Get the measurement with the latest timestamp
                latest_timestamp = max(messwerte.keys())
                return messwerte[latest_timestamp]
                
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        """Return additional sensor attributes.
        
        Includes metadata about the measurement (parameter type, unit, timezone)
        and timestamp of the latest measurement.
        """
        # Check if we have data for this station
        if (not self.coordinator.data or 
            "rivers" not in self.coordinator.data or
            self._station_id not in self.coordinator.data["rivers"]):
            return None
            
        station_data = self.coordinator.data["rivers"][self._station_id]
        
        if self._measurement_type not in station_data:
            return None
            
        measurement_data = station_data[self._measurement_type]
        attributes = {}
        
        # Add metadata from the API response
        if "Parameter" in measurement_data:
            attributes["parameter"] = measurement_data["Parameter"]
        if "Einheit" in measurement_data:
            attributes["api_unit"] = measurement_data["Einheit"]  # Original unit from API
        if "Zeit" in measurement_data:
            attributes["timezone"] = measurement_data["Zeit"]
            
        # Add timestamp of the latest measurement
        if "Messwerte" in measurement_data and measurement_data["Messwerte"]:
            messwerte = measurement_data["Messwerte"]
            if messwerte:
                latest_timestamp = max(messwerte.keys())
                try:
                    # Parse and format the timestamp
                    timestamp = datetime.fromisoformat(latest_timestamp)
                    attributes["last_updated"] = timestamp.isoformat()
                except (ValueError, TypeError):
                    # If parsing fails, store the raw timestamp
                    attributes["last_updated"] = latest_timestamp
        
        # Add station metadata for context
        attributes["station_id"] = self._station_id
        attributes["river"] = self._station_config["river"]
        
        return attributes if attributes else None

    @property
    def available(self) -> bool:
        """Return True if the sensor data is available.
        
        A river sensor is considered available if:
        1. The coordinator has data
        2. This station has data
        3. This measurement type has data for this station
        """
        return (
            self.coordinator.data is not None and
            "rivers" in self.coordinator.data and
            self._station_id in self.coordinator.data["rivers"] and
            self._measurement_type in self.coordinator.data["rivers"][self._station_id] and
            bool(self.coordinator.data["rivers"][self._station_id][self._measurement_type].get("Messwerte"))
        )
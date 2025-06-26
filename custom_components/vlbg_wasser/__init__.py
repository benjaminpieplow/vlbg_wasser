"""
Vorarlberg Wasser Daten
"""


from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from const import DOMAIN
from vowis_api import VowisApi 

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VOWIS from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    session = async_get_clientsession(hass)
    api = VowisApi(session)
    
    coordinator = VowisDataUpdateCoordinator(hass, api, entry)
    
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class VowisDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the VOWIS API."""

    def __init__(self, hass: HomeAssistant, api: VowisApi, entry: ConfigEntry) -> None:
        """Initialize."""
        self.api = api
        self.entry = entry
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            data = {}
            
            # Always fetch bodensee data
            bodensee_data = await self.api.get_bodensee_data()
            if bodensee_data:
                data["bodensee"] = bodensee_data[0]  # API returns array with single element
            
            # Fetch river data for enabled stations
            enabled_stations = self.entry.data.get("enabled_stations", [])
            data["rivers"] = {}
            
            for station_id in enabled_stations:
                station_data = {}
                station_config = next(
                    (s for s in self.entry.data.get("river_stations", []) if s["id"] == station_id),
                    None
                )
                
                if not station_config:
                    continue
                
                # Fetch each supported measurement type
                if station_config.get("supports_depth", False):
                    depth_data = await self.api.get_river_data(station_id, "w")
                    if depth_data and station_id in depth_data.get("Stationen", {}):
                        station_data["depth"] = depth_data["Stationen"][station_id]
                
                if station_config.get("supports_flow", False):
                    flow_data = await self.api.get_river_data(station_id, "q")
                    if flow_data and station_id in flow_data.get("Stationen", {}):
                        station_data["flow"] = flow_data["Stationen"][station_id]
                
                if station_config.get("supports_temperature", False):
                    temp_data = await self.api.get_river_data(station_id, "wt")
                    if temp_data and station_id in temp_data.get("Stationen", {}):
                        station_data["temperature"] = temp_data["Stationen"][station_id]
                
                if station_data:
                    data["rivers"][station_id] = station_data
            
            return data
            
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with VOWIS API: {exception}") from exception
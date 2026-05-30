"""The vlbg_wasser integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, RIVER_STATIONS
from .api import VlbgWasserAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up vlbg_wasser from a config entry."""
    _LOGGER.debug("sensor.async_setup_entry called")
    hass.data.setdefault(DOMAIN, {})
    
    # Create API client
    api = VlbgWasserAPI(hass)
    
    # Create coordinator
    station_ids = entry.data.get("station_ids", [])
    coordinator = VlbgWasserDataUpdateCoordinator(hass, api, station_ids)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok


_MTYPE_CAPABILITIES = {
    "w": "supports_depth",
    "q": "supports_flow",
    "wt": "supports_temperature",
}

_STATION_MAP = {s["id"]: s for s in RIVER_STATIONS}


class VlbgWasserDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, api: VlbgWasserAPI, station_ids: list[str]) -> None:
        """Initialize."""
        self.api = api
        self._station_ids = station_ids
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch all measurements for all selected stations in parallel."""
        coros = []
        keys = []
        for station_id in self._station_ids:
            station = _STATION_MAP.get(station_id)
            if not station:
                continue
            for mtype, cap in _MTYPE_CAPABILITIES.items():
                if station[cap]:
                    coros.append(self.api.get_measurement_data(station_id, mtype))
                    keys.append((station_id, mtype))

        try:
            results = await asyncio.gather(*coros)
        except Exception as exc:
            raise UpdateFailed() from exc

        data: dict = {}
        for (station_id, mtype), result in zip(keys, results):
            data.setdefault(station_id, {})[mtype] = result
        return data
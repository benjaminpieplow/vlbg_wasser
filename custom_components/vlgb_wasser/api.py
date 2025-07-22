"""API client for vlbg_wasser integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class VlbgWasserAPIError(HomeAssistantError):
    """Exception to indicate a general API error."""


class VlbgWasserAPIConnectionError(VlbgWasserAPIError):
    """Exception to indicate a connection error."""


class VlbgWasserAPI:
    """API client for Vorarlberg Wasser data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the API client."""
        self._hass = hass
        self._session = hass.helpers.aiohttp_client.async_get_clientsession()

    async def get_measurement_data(self, station_id: str, measurement_type: str) -> dict[str, Any]:
        """Get measurement data for a specific station and type."""
        url = f"{API_BASE_URL}messwerte/{measurement_type}"
        params = {"hzbnr": station_id}
        
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with self._session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    _LOGGER.debug("API response for station %s, type %s: %s", station_id, measurement_type, data)
                    
                    return self._process_data(data, station_id)
                    
        except aiohttp.ClientError as error:
            _LOGGER.error("Connection error fetching data from %s: %s", url, error)
            raise VlbgWasserAPIConnectionError(f"Connection error: {error}") from error
        except Exception as error:
            _LOGGER.error("Unexpected error fetching data from %s: %s", url, error)
            raise VlbgWasserAPIError(f"Unexpected error: {error}") from error

    def _process_data(self, data: dict[str, Any], station_id: str) -> dict[str, Any]:
        """Process the API response data."""
        try:
            station_data = data["Stationen"][station_id]
            measurements = station_data["Messwerte"]
            
            if not measurements:
                _LOGGER.warning("No measurements found for station %s", station_id)
                return {}
            
            # Get the latest measurement (last item in the dict)
            latest_time = max(measurements.keys())
            latest_value = measurements[latest_time]
            
            return {
                "station_id": station_id,
                "parameter": station_data.get("Parameter"),
                "unit": station_data.get("Einheit"),
                "timezone": station_data.get("Zeit"),
                "latest_time": latest_time,
                "latest_value": latest_value,
                "all_measurements": measurements,
            }
            
        except KeyError as error:
            _LOGGER.error("Unexpected API response structure: %s", error)
            raise VlbgWasserAPIError(f"Unexpected API response structure: {error}") from error
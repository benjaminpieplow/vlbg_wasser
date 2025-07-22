"""
API client to scrape Vorarlberg Abfluss Data
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
import async_timeout

from const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class VowisApiError(Exception):
  """Exception to indicate a general API error."""


class VowisApi:
  """VOWIS API client."""

  def __init__(self, session: aiohttp.ClientSession) -> None:
    """Initialize the API client."""
    self._session = session
    self._base_url = API_BASE_URL

  async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make an API request."""
    url = f"{self._base_url}{endpoint}"

    try:
      async with async_timeout.timeout(API_TIMEOUT):
        async with self._session.get(url, params=params) as response:
          response.raise_for_status()
          data = await response.json()
          return data
    except asyncio.TimeoutError as exception:
      raise VowisApiError(f"Request to {url} timed out") from exception
    except aiohttp.ClientError as exception:
      raise VowisApiError(
        f"Request to {url} failed: {exception}") from exception
    except Exception as exception:
      raise VowisApiError(
        f"Unexpected error for {url}: {exception}") from exception

  async def get_bodensee_data(self) -> Optional[list]:
    """Get bodensee station data."""
    try:
      data = await self._make_request("see/")
      if isinstance(data, list) and len(data) > 0:
        return data
      else:
        _LOGGER.warning("Unexpected bodensee data format: %s", data)
        return None
    except VowisApiError as exception:
      _LOGGER.error("Error fetching bodensee data: %s", exception)
      return None

  async def get_river_data(self, station_id: str, measurement_type: str) -> Optional[Dict[str, Any]]:
    """Get river station data for a specific measurement type.

    Args:
      station_id: The station ID (e.g., "200329")
      measurement_type: Type of measurement ("w", "wt", "q")
    """
    try:
      params = {"hzbnr": station_id}
      data = await self._make_request(f"messwerte/{measurement_type}", params=params)

      # Validate that we have the expected structure
      if (isinstance(data, dict) and
        "Stationen" in data and
        isinstance(data["Stationen"], dict) and
          station_id in data["Stationen"]):
        return data
      else:
        _LOGGER.warning(
          "Unexpected river data format for station %s, measurement %s: %s",
          station_id, measurement_type, data
        )
        return None

    except VowisApiError as exception:
      _LOGGER.error(
        "Error fetching river data for station %s, measurement %s: %s",
        station_id, measurement_type, exception
      )
      return None

  async def test_connection(self) -> bool:
    """Test the connection to the API."""
    try:
      # Test against the bodensee's API
      bodensee_data = await self.get_bodensee_data()
      return bodensee_data is not None
    except Exception as exception:
      _LOGGER.error("Connection test failed: %s", exception)
      return False

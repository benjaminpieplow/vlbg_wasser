"""Config flow for VOWIS integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, RIVER_STATIONS
from .vowis_api import VowisApi, VowisApiError

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = VowisApi(session)
    
    if not await api.test_connection():
        raise VowisApiError("Cannot connect to VOWIS API")
    
    return {"title": "VOWIS"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VOWIS."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._selected_stations: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if we already have this configured
                await self.async_set_unique_id("vowis_integration")
                self._abort_if_unique_id_configured()
                
                return await self.async_step_river_stations()
                
            except VowisApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "bodensee_info": "The integration will automatically include the Lake Constance station with all available sensors."
            },
        )

    async def async_step_river_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle river station selection."""
        if user_input is not None:
            self._selected_stations = user_input.get("river_stations", [])
            
            return self.async_create_entry(
                title="VOWIS",
                data={
                    "enabled_stations": self._selected_stations,
                    "river_stations": RIVER_STATIONS,
                }
            )

        # Create options for river stations
        station_options = {}
        for station in RIVER_STATIONS:
            features = []
            if station["supports_depth"]:
                features.append("Depth")
            if station["supports_flow"]:
                features.append("Flow")
            if station["supports_temperature"]:
                features.append("Temperature")
            
            station_options[station["id"]] = f"{station['name']} ({', '.join(features)})"

        return self.async_show_form(
            step_id="river_stations",
            data_schema=vol.Schema({
                vol.Optional("river_stations", default=[]): vol.All(
                    vol.Ensure_list, [vol.In(station_options)]
                ),
            }),
            description_placeholders={
                "info": "Select which river stations you want to monitor. You can always change this later in the integration options. River stations are disabled by default to reduce API calls."
            },
        )

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for VOWIS."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            # Update config entry with new station selection
            data = dict(self.config_entry.data)
            data["enabled_stations"] = user_input.get("river_stations", [])
            
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=data
            )
            
            return self.async_create_entry(title="", data={})

        # Get current enabled stations
        current_stations = self.config_entry.data.get("enabled_stations", [])
        
        # Create options for river stations
        station_options = {}
        for station in RIVER_STATIONS:
            features = []
            if station["supports_depth"]:
                features.append("Depth")
            if station["supports_flow"]:
                features.append("Flow")
            if station["supports_temperature"]:
                features.append("Temperature")
            
            station_options[station["id"]] = f"{station['name']} ({', '.join(features)})"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("river_stations", default=current_stations): vol.All(
                    vol.Ensure_list, [vol.In(station_options)]
                ),
            }),
        )
"""Config flow for vlbg_wasser integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import VlbgWasserAPI, VlbgWasserAPIError
from .const import DOMAIN, RIVER_STATIONS

_LOGGER = logging.getLogger(__name__)

STATION_OPTIONS = {
    s["id"]: f"{s['name']} ({s['river']})"
    for s in RIVER_STATIONS
}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("station_ids"): cv.multi_select(STATION_OPTIONS),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input and probe station capabilities."""
    station_ids = data.get("station_ids", [])
    if not station_ids:
        raise CannotConnect

    api = VlbgWasserAPI(hass)
    try:
        caps_list = await asyncio.gather(
            *[api.probe_capabilities(sid) for sid in station_ids]
        )
    except VlbgWasserAPIError as err:
        _LOGGER.error("API error while probing stations %s: %s", station_ids, err)
        raise CannotConnect from err

    capabilities = dict(zip(station_ids, caps_list))
    _LOGGER.info("Probed capabilities for all stations: %s", capabilities)
    return {
        "title": "Vorarlberg Wasser",
        "capabilities": capabilities,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for vlbg_wasser."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        "station_ids": user_input["station_ids"],
                        "capabilities": info["capabilities"],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

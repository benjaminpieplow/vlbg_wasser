"""The vlbg_wasser integration."""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import timedelta

from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue, async_delete_issue
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import ALL_MEASUREMENT_TYPES, DEFAULT_SCAN_INTERVAL, DOMAIN, RIVER_STATIONS
from .api import VlbgWasserAPI, BodenseeAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

_STATION_NAME_MAP = {s["id"]: s["name"] for s in RIVER_STATIONS}
_MTYPE_LABELS = {"w": "depth", "q": "flow rate", "wt": "temperature"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up vlbg_wasser from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api = VlbgWasserAPI(hass)
    bodensee_api = BodenseeAPI(hass)

    # Migrate entries created before capability probing was introduced
    if "capabilities" not in entry.data:
        _LOGGER.debug("Probing capabilities for migration of existing config entry")
        station_ids = entry.data.get("station_ids", [])
        caps_list = await asyncio.gather(
            *[api.probe_capabilities(sid) for sid in station_ids],
            return_exceptions=True,
        )
        capabilities = {
            sid: caps if isinstance(caps, dict) else {}
            for sid, caps in zip(station_ids, caps_list)
        }
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "capabilities": capabilities}
        )

    station_ids = entry.data.get("station_ids", [])
    coordinator = VlbgWasserDataUpdateCoordinator(hass, api, station_ids)
    bodensee_coordinator = BodenseeDataUpdateCoordinator(hass, bodensee_api)

    await coordinator.async_config_entry_first_refresh()
    await bodensee_coordinator.async_config_entry_first_refresh()

    # Schedule daily capability check at a random time between 02:00 and 03:59
    rand_hour = random.randint(2, 3)
    rand_minute = random.randint(0, 59)

    @callback
    def _schedule_capability_check(now) -> None:
        hass.async_create_task(_check_capabilities(hass, entry, api))

    unsub_repair = async_track_time_change(
        hass, _schedule_capability_check, hour=rand_hour, minute=rand_minute, second=0
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "river": coordinator,
        "bodensee": bodensee_coordinator,
        "unsub_repair_check": unsub_repair,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    if unsub := entry_data.get("unsub_repair_check"):
        unsub()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _check_capabilities(hass: HomeAssistant, entry: ConfigEntry, api: VlbgWasserAPI) -> None:
    """Probe station capabilities and issue repairs if anything has changed."""
    station_ids = entry.data.get("station_ids", [])
    stored_caps = entry.data.get("capabilities", {})

    results = await asyncio.gather(
        *[api.probe_capabilities(sid) for sid in station_ids],
        return_exceptions=True,
    )

    new_capabilities = {}
    changed = False

    for station_id, result in zip(station_ids, results):
        if isinstance(result, Exception):
            _LOGGER.warning("Capability check failed for station %s: %s", station_id, result)
            continue

        new_capabilities[station_id] = result
        old_caps = stored_caps.get(station_id, {})

        for mtype in ALL_MEASUREMENT_TYPES:
            issue_id = f"capability_changed_{station_id}_{mtype}"
            old_val = old_caps.get(mtype)
            new_val = result.get(mtype)

            if old_val == new_val:
                async_delete_issue(hass, DOMAIN, issue_id)
                continue

            changed = True
            station_name = _STATION_NAME_MAP.get(station_id, station_id)
            change_desc = "now supported" if new_val else "no longer supported"

            async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="capability_changed",
                translation_placeholders={
                    "station_name": station_name,
                    "measurement_type": _MTYPE_LABELS[mtype],
                    "change": change_desc,
                },
            )

    if changed:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "capabilities": {**stored_caps, **new_capabilities}},
        )


class BodenseeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Bodensee data."""

    def __init__(self, hass: HomeAssistant, api: BodenseeAPI) -> None:
        """Initialize."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_bodensee",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch Bodensee measurements."""
        try:
            return await self.api.get_data()
        except Exception as exc:
            raise UpdateFailed() from exc


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
        """Fetch all measurement types for all selected stations in parallel."""
        coros = []
        keys = []
        for station_id in self._station_ids:
            for mtype in ALL_MEASUREMENT_TYPES:
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

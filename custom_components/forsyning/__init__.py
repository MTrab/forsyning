"""Adds support for Forsyning sensors."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from functools import partial
from importlib import import_module
from uuid import uuid4

from aiohttp import ServerDisconnectedError
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.loader import async_get_integration
from pytz import timezone

from .api_handler import ForsyningsAPI
from .connectors import Connectors
from .const import DOMAIN, PLATFORMS, STARTUP, UPDATE_SIGNAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Forsyning from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    integration = await async_get_integration(hass, DOMAIN)

    _LOGGER.info(STARTUP, integration.version)
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry options: %s", entry.options)

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=str(uuid4()))

    _LOGGER.debug("Entry unique ID: %s", entry.unique_id)

    api = ForsyningsAPI(
        hass,
        entry,
    )

    hass.data[DOMAIN][entry.entry_id] = api

    await api.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        return True

    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

"""API handler."""
from __future__ import annotations

import logging
from datetime import datetime
from importlib import import_module
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..custom_components.forsyning.const import CONF_CONNECTOR, UPDATE_SIGNAL

_LOGGER = logging.getLogger(__name__)


class ForsyningsAPI(DataUpdateCoordinator[Optional[datetime]]):
    """API data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the update coordinator object."""
        self.hass = hass
        self._config = entry
        self._client = async_get_clientsession(hass)
        self._tz = hass.config.time_zone

        self.friendly_name = self._config.data[CONF_NAME]

        module = import_module(self._config.options[CONF_CONNECTOR].namespace, __name__)

        self.connector = module.Connector(
            self._client,
            self._tz,
            self._config.options[CONF_USERNAME],
            self._config.options[CONF_PASSWORD],
        )

        super().__init__(
            hass, _LOGGER, name=self.name, update_interval=module.SCAN_INTERVAL
        )

    async def _async_update_data(self) -> datetime | None:
        """Update API data."""
        result = await self.connector.async_update()
        dispatcher_send(self.hass, UPDATE_SIGNAL)
        return result

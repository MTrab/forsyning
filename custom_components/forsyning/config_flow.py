"""Config flow for Forsyning integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from . import async_setup_entry, async_unload_entry
from .connectors import Connectors, scheme_config_connector
from .const import CONF_CONNECTOR, DOMAIN

# from .utils.configuration_schema import (
#     forsyning_config_option_info_schema,
#     forsyning_config_option_initial_schema,
# )
# from .utils.regionhandler import RegionHandler

_LOGGER = logging.getLogger(__name__)


# class ForsyningOptionsFlowHandler(config_entries.OptionsFlow):
#     """Forsyning config flow options handler."""

#     def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
#         """Initialize Forsyning options flow."""
#         self.connectors = Connectors()
#         self.config_entry = config_entry
#         self._errors = {}
#         # Cast from MappingProxy to dict to allow update.
#         self.options = dict(config_entry.options)
#         config = self.config_entry.options or self.config_entry.data
#         _LOGGER.debug("Config: %s", config)

#     async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
#         """Handle options flow."""
#         schema = scheme_config_connector()

#         return self.async_show_form(
#             step_id="initial",
#             data_schema=vol.Schema(schema),
#             errors=self._errors,
#         )

#     async def async_step_initial(self, user_input: Any | None = None) -> FlowResult:
#         """Handle region options flow."""

#         async def _do_update(_=None) -> None:
#             """Update after settings change."""
#             await async_unload_entry(self.hass, self.config_entry)
#             await async_setup_entry(self.hass, self.config_entry)

#         self._errors = {}

#         if user_input is not None:
#             self.options.update(user_input)
#             _LOGGER.debug(self.options)

        # schema = forsyning_config_option_info_schema(self.config_entry.options)
        # return self.async_show_form(
        #     step_id="region",
        #     data_schema=vol.Schema(schema),
        #     errors=self._errors,
        #     description_placeholders={
        #         "name": self.config_entry.data[CONF_NAME],
        #         "country": self.config_entry.options[CONF_COUNTRY],
        #     },
        # )


class ForsyningConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Forsyning"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    # @staticmethod
    # @callback
    # def async_get_options_flow(
    #     config_entry: config_entries.ConfigEntry,
    # ) -> ForsyningOptionsFlowHandler:
    #     """Get the options flow for this handler."""
    #     return ForsyningOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.connectors = Connectors()
        self.user_input = None
        self._errors = {}

    async def async_step_user(self, user_input: Any | None = None) -> FlowResult:
        """Handle the initial config flow step - select connector."""
        self._errors = {}

        if user_input is not None:
            self.user_input = user_input
            return await self.async_step_connector_select()

        schema = scheme_config_connector()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(schema), errors=self._errors
        )

    async def async_step_connector_select(
        self, user_input: Any | None = None
    ) -> FlowResult:
        """Handle step 2, setting connector specifics."""
        self._errors = {}

        if user_input is not None:
            user_input = {**user_input, **self.user_input}
            await self.async_set_unique_id(user_input[CONF_NAME])

            if "base" not in self._errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    description=f"API connector for {user_input[CONF_NAME]}",
                )

        connector = self.connectors.get_connector(user_input[CONF_CONNECTOR])
        schema = connector.options_scheme(self.user_input)

        return self.async_show_form(
            step_id="connector_select",
            data_schema=vol.Schema(schema),
            errors=self._errors,
            last_step=True,
        )

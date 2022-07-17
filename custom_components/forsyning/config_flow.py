"""Config flow for Forsyning integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.template import Template

from . import async_setup_entry, async_unload_entry
from .connectors import Connectors
from .const import CONF_TEMPLATE, DEFAULT_TEMPLATE, DOMAIN

# from .utils.configuration_schema import (
#     forsyning_config_option_info_schema,
#     forsyning_config_option_initial_schema,
# )
# from .utils.regionhandler import RegionHandler

_LOGGER = logging.getLogger(__name__)


class ForsyningFlowHandler(config_entries.OptionsFlow):
    """Forsyning config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Forsyning options flow."""
        self.connectors = Connectors()
        self.config_entry = config_entry
        self._errors = {}
        # Cast from MappingProxy to dict to allow update.
        self.options = dict(config_entry.options)
        config = self.config_entry.options or self.config_entry.data
        _LOGGER.debug("Config: %s", config)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Handle options flow."""
        schema = forsyning_config_option_info_schema(self.config_entry.options)
        country = self.config_entry.options.get(
            CONF_COUNTRY,
            RegionHandler.country_from_region(self.config_entry.options.get(CONF_AREA))
            or RegionHandler.country_from_region(
                RegionHandler.description_to_region(
                    self.config_entry.options.get(CONF_AREA)
                )
            ),
        )
        return self.async_show_form(
            step_id="region",
            data_schema=vol.Schema(schema),
            errors=self._errors,
            description_placeholders={
                "name": self.config_entry.data[CONF_NAME],
                "country": country,
            },
        )

    async def async_step_region(self, user_input: Any | None = None) -> FlowResult:
        """Handle region options flow."""

        async def _do_update(_=None) -> None:
            """Update after settings change."""
            await async_unload_entry(self.hass, self.config_entry)
            await async_setup_entry(self.hass, self.config_entry)

        self._errors = {}

        if user_input is not None:
            self.options.update(user_input)
            _LOGGER.debug(self.options)
            template_ok = False
            if user_input[CONF_TEMPLATE] in (None, ""):
                user_input[CONF_TEMPLATE] = DEFAULT_TEMPLATE
            else:
                # Check if template for additional costs is valid or not
                user_input[CONF_TEMPLATE] = re.sub(
                    r"\s{2,}", "", user_input[CONF_TEMPLATE]
                )

            template_ok = await _validate_template(self.hass, user_input[CONF_TEMPLATE])
            # self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
            if template_ok:
                async_call_later(self.hass, 2, _do_update)
                return self.async_create_entry(
                    title=self.options.get(CONF_NAME),
                    data=self.options,
                )
            else:
                self._errors["base"] = "invalid_template"
        schema = forsyning_config_option_info_schema(self.config_entry.options)
        return self.async_show_form(
            step_id="region",
            data_schema=vol.Schema(schema),
            errors=self._errors,
            description_placeholders={
                "name": self.config_entry.data[CONF_NAME],
                "country": self.config_entry.options[CONF_COUNTRY],
            },
        )


class ForsyningConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Forsyning"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ForsyningOptionsFlowHandler:
        """Get the options flow for this handler."""
        return ForsyningOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.connectors = Connectors()
        self._errors = {}

    async def async_step_user(self, user_input: Any | None = None) -> FlowResult:
        """Handle the initial config flow step."""
        self._errors = {}

        if user_input is not None:
            self.user_input = user_input
            return await self.async_step_region()

        schema = forsyning_config_option_initial_schema()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(schema), errors=self._errors
        )

    async def async_step_region(self, user_input: Any | None = None) -> FlowResult:
        """Handle step 2, setting region and templates."""
        self._errors = {}

        if user_input is not None:
            user_input = {**user_input, **self.user_input}
            await self.async_set_unique_id(user_input[CONF_NAME])

            _LOGGER.debug(user_input)

            template_ok = False
            if user_input[CONF_TEMPLATE] in (None, ""):
                user_input[CONF_TEMPLATE] = DEFAULT_TEMPLATE
            else:
                # Check if template for additional costs is valid or not
                user_input[CONF_TEMPLATE] = re.sub(
                    r"\s{2,}", "", user_input[CONF_TEMPLATE]
                )

            template_ok = await _validate_template(self.hass, user_input[CONF_TEMPLATE])
            self._async_abort_entries_match({CONF_NAME: user_input[CONF_NAME]})
            if template_ok:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={"name": user_input[CONF_NAME]},
                    options=user_input,
                )
            else:
                self._errors["base"] = "invalid_template"

        schema = forsyning_config_option_info_schema(self.user_input)
        return self.async_show_form(
            step_id="region",
            data_schema=vol.Schema(schema),
            errors=self._errors,
            last_step=True,
            description_placeholders={
                "name": self.user_input[CONF_NAME],
                "country": self.user_input[CONF_COUNTRY],
            },
        )

    async def async_step_import(
        self, user_input: Any | None
    ) -> Any:  # pylint: disable=unused-argument
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        return self.async_create_entry(
            title="Imported from configuration.yaml", data={}
        )


async def _validate_template(hass: HomeAssistant, user_template: Any) -> bool:
    """Validate template to eliminate most user errors."""
    try:
        _LOGGER.debug("Template:")
        _LOGGER.debug(user_template)
        user_template = Template(user_template, hass).async_render()
        return bool(isinstance(user_template, float))
    except Exception as err:
        _LOGGER.error(err)

    return False

"""Config flow for Forsyning integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class ForsyningConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Forsyning"""

    VERSION = 1

    async def async_step_user(self, info):
        if info is not None:
            pass  # TODO: process info

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("password"): str})
        )

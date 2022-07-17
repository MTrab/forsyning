"""Integration til Aalborg forsyning.

API dokumentation:
https://aalborgforsyning.dk/erhverv/energioptimering/datadeling-for-fjernaflaeste-varmemalere/api-for-adgang-til-malerdata
"""
# pylint: disable=dangerous-default-value
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers import selector

__all__ = ["Connector", "scheme_config_options", "SOURCE_NAME", "SCAN_INTERVAL"]

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://services.aalborgforsyning.dk/"
SOURCE_NAME = "Aalborg Forsyning"
SCAN_INTERVAL = 9 * (60 * 60)  # Only allowed to poll 3 times pr. day


def scheme_config_options(options: ConfigEntry = {}) -> dict:
    """Return a schema for initial configuration options."""
    if not options:
        options = {
            CONF_NAME: "Aalborg Forsyning",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
        }

    schema = {
        vol.Required(CONF_NAME, default=options.get(CONF_NAME)): str,
        vol.Required(CONF_USERNAME, default=options.get(CONF_USERNAME)): str,
        vol.Required(
            CONF_PASSWORD, default=options.get(CONF_PASSWORD)
        ): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD),
        ),
    }
    return schema


class Connector:
    """API handler for Aalborg forsyning."""

    def __init__(
        self, client, tz, email: str, password: str  # pylint: disable=invalid-name
    ) -> None:
        """Initialize the connector."""
        self.client = client
        self._result = {}
        self._tz = tz
        self._email = email
        self._password = password

    async def _async_authorize(self) -> str | None:
        """Get access_token."""
        token_url = f"{BASE_URL}Token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = (
            f"username={self._email}&password={self._password}&grant_type=password"
        )

        resp = await self.client.post(token_url, headers=headers, payload=payload)

        if resp.status == 200:
            res = await resp.json()
            return res["access_token"]

        return None

    async def _async_get_meters(self, token: str) -> list:
        """Get a list of all meter ID's available to this account."""
        meter_url = f"{BASE_URL}api/data/Meters"
        headers = {"Authorization": f"Bearer {token}"}

        resp = await self.client.get(meter_url, headers=headers)

        if resp.status == 200:
            res = await resp.json()
            return res["RegisteredMeters"]

        return []

    async def async_update(self) -> bool:
        """Update data from the API."""
        token = await self._async_authorize()
        if isinstance(token, type(None)):
            _LOGGER.error(
                "Couldn't authorise against Aalborg Forsyning API "
                "using email %s and password ***",
                self._email,
            )
            return False

        meters = await self._async_get_meters(token)
        if len(meters) == 0:
            _LOGGER.error("Error fetching meters list")
            return False

        headers = {"Authorization": f"Bearer {token}"}
        data_url = f"{BASE_URL}/api/data?meterid="

        self._result.clear()
        for meter in meters:
            resp = await self.client.get(f"{data_url}{meter}", headers=headers)
            if resp.status == 200:
                res = await resp.json()
                self._result.update(res[0])

        return True

    @property
    def meter_data(self) -> dict:
        """Return dict of meter data."""
        return self._result

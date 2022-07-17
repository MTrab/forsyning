"""Dynamically load all available connectors."""
from __future__ import annotations

from collections import namedtuple
from importlib import import_module
from logging import getLogger
from os import listdir
from posixpath import dirname

import voluptuous as vol
from genericpath import isdir

from ..const import CONF_CONNECTOR

_LOGGER = getLogger(__name__)

ConnectorTuple = namedtuple(
    "Connector", "module namespace friendly_name options_scheme update_rate"
)


def scheme_config_connector() -> dict:
    """Return dict of available connectors."""
    conn = Connectors()

    return {vol.Required(CONF_CONNECTOR): vol.In(conn.connectors, True)}


class Connectors:
    """Handle connector modules."""

    def __init__(self):
        """Initialize connector handler."""

        self._connectors = []
        for module in listdir(f"{dirname(__file__)}"):
            mod_path = f"{dirname(__file__)}/{module}"
            if isdir(mod_path) and not module.endswith("__pycache__"):

                _LOGGER.debug("Adding module %s", module)
                api_ns = f".{module}"
                mod = import_module(api_ns, __name__)
                con = ConnectorTuple(
                    module,
                    f".connectors{api_ns}",
                    mod.SOURCE_NAME,
                    mod.scheme_config_options,
                    mod.SCAN_INTERVAL,
                )

                self._connectors.append(con)

    @property
    def connectors(self) -> list:
        """Return valid connectors."""
        conn_names = []

        for connector in self._connectors:
            conn_names.append(connector.friendly_name)

        return self._connectors

    def get_connector(self, connector_name: str) -> ConnectorTuple | None:
        """Get connector."""

        for connector in self._connectors:
            if connector.friendly_name == connector_name:
                return connector

        return None

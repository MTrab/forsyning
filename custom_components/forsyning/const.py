"""Forsyning consts."""

STARTUP = """
-------------------------------------------------------------------
Forsyning integration

Version: %s
This is a custom integration
If you have any issues with this you need to open an issue here:
https://github.com/mtrab/forsyning/issues
-------------------------------------------------------------------
"""

PLATFORMS = ["sensor"]

CONF_CURRENCY_IN_CENT = "in_cent"
CONF_DECIMALS = "decimals"
CONF_VAT = "vat"

CONF_CONNECTOR = "connector"

DATA = "data"
DEFAULT_NAME = "Forsyning"
DOMAIN = "FORSYNING"

UNIQUE_ID = "unique_id"

UPDATE_SIGNAL = "forsyning_update_{}"

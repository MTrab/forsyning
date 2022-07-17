"""Forsyning consts."""
from collections import namedtuple

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
CONF_TEMPLATE = "cost_template"
CONF_VAT = "vat"

CONF_CONNECTOR = "connector"

DATA = "data"
DEFAULT_NAME = "Forsyning"
DEFAULT_TEMPLATE = "{{0.0|float}}"
DOMAIN = "Forsyning"

UNIQUE_ID = "unique_id"

UPDATE_SIGNAL = "forsyning_update_{}"

# # Multiplier mappings
# UNIT_TO_MULTIPLIER = {"MWh": 0, "kWh": 1000, "Wh": 1000000}
# MULTIPLIER_TO_UNIT = {0: "MWh", 1000: "kWh", 1000000: "Wh"}
# CENT_MULTIPLIER = 100

# # Regions
# # Format:
# #   "Region": [CURRENCY_LIST, "Country", "Region description", VAT]
# REGIONS = {
#     "DK1": [CURRENCY_LIST["DKK"], "Denmark", "West of the great belt", 0.25],
#     "DK2": [CURRENCY_LIST["DKK"], "Denmark", "East of the great belt", 0.25],
#     "FI": [CURRENCY_LIST["EUR"], "Finland", "Finland", 0.24],
#     "EE": [CURRENCY_LIST["EUR"], "Estonia", "Estonia", 0.20],
#     "LT": [CURRENCY_LIST["EUR"], "Lithuania", "Lithuania", 0.21],
#     "LV": [CURRENCY_LIST["EUR"], "Latvia", "Latvia", 0.21],
#     "NO1": [CURRENCY_LIST["NOK"], "Norway", "Oslo", 0.25],
#     "NO2": [CURRENCY_LIST["NOK"], "Norway", "Kristiansand", 0.25],
#     "NO3": [CURRENCY_LIST["NOK"], "Norway", "Molde, Trondheim", 0.25],
#     "NO4": [CURRENCY_LIST["NOK"], "Norway", "Tromsø", 0.25],
#     "NO5": [CURRENCY_LIST["NOK"], "Norway", "Bergen", 0.25],
#     "SE1": [CURRENCY_LIST["SEK"], "Sweden", "Luleå", 0.25],
#     "SE2": [CURRENCY_LIST["SEK"], "Sweden", "Sundsvall", 0.25],
#     "SE3": [CURRENCY_LIST["SEK"], "Sweden", "Stockholm", 0.25],
#     "SE4": [CURRENCY_LIST["SEK"], "Sweden", "Malmö", 0.25],
#     "FR": [CURRENCY_LIST["EUR"], "France", "France", 0.055],
#     "NL": [CURRENCY_LIST["EUR"], "Netherlands", "Netherlands", 0.21],
#     "BE": [CURRENCY_LIST["EUR"], "Belgium", "Belgium", 0.21],
#     "AT": [CURRENCY_LIST["EUR"], "Austria", "Austria", 0.20],
#     "DE": [CURRENCY_LIST["EUR"], "Germany", "Germany", 0.19],
#     "LU": [CURRENCY_LIST["EUR"], "Luxemburg", "Luxemburg", 0.08],
# }

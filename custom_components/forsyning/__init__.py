"""Adds support for Forsyning sensors."""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import partial
from importlib import import_module
import logging

from aiohttp import ServerDisconnectedError
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.loader import async_get_integration
from pytz import timezone

from .connectors import Connectors
from .const import CONF_AREA, DOMAIN, STARTUP, UPDATE_EDS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the component."""

    hass.data.setdefault(DOMAIN, {})

    if DOMAIN not in config:
        return True

    for conf in config[DOMAIN]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=conf,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Forsyning from a config entry."""
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry options: %s", entry.options)
    result = await _setup(hass, entry)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return result


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


async def _setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup the integration using a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP, integration.version)

    api = APIConnector(
        hass,
        entry.options.get(CONF_AREA) or entry.data.get(CONF_AREA),
        entry.entry_id,
    )
    hass.data[DOMAIN][entry.entry_id] = api

    async def new_day(n):  # type: ignore pylint: disable=unused-argument, invalid-name
        """Handle data on new day."""
        _LOGGER.debug("New day function called")
        api.today = api.tomorrow
        api.tomorrow = None
        api._tomorrow_valid = False  # pylint: disable=protected-access
        api.tomorrow_calculated = False
        async_dispatcher_send(hass, UPDATE_EDS)

    async def new_hour(n):  # type: ignore pylint: disable=unused-argument, invalid-name
        """Callback to tell the sensors to update on a new hour."""
        _LOGGER.debug("New hour, updating state")
        async_dispatcher_send(hass, UPDATE_EDS)

    async def get_new_data(n):  # type: ignore pylint: disable=unused-argument, invalid-name
        """Fetch new data for tomorrows prices at 13:00ish CET."""
        _LOGGER.debug("Getting latest dataset")
        await api.update()
        async_dispatcher_send(hass, UPDATE_EDS)

    # Handle dataset updates
    update_tomorrow = async_track_time_change(
        hass,
        get_new_data,
        hour=13,
        minute=RANDOM_MINUTE,
        second=RANDOM_SECOND,
    )

    update_new_day = async_track_time_change(
        hass,
        new_day,
        hour=0,
        minute=0,
        second=0,
    )

    update_new_hour = async_track_time_change(hass, new_hour, minute=0, second=0)

    api.listeners.append(update_tomorrow)
    api.listeners.append(update_new_hour)
    api.listeners.append(update_new_day)

    return True


class APIConnector:
    """An object to store Forsyning data."""

    def __init__(self, hass, region, entry_id) -> None:
        """Initialize Forsyning Connector."""
        self._connectors = Connectors()
        self.hass = hass
        self._last_tick = None
        self._tomorrow_valid = False
        self._entry_id = entry_id

        self.today = None
        self.tomorrow = None
        self.today_calculated = False
        self.tomorrow_calculated = False
        self.listeners = []

        self.next_retry_delay = RETRY_MINUTES
        self.retry_count = 0

        self._client = async_get_clientsession(hass)
        self._region = RegionHandler(region)
        self._tz = hass.config.time_zone
        self._source = None

    async def update(self, dt=None):  # type: ignore pylint: disable=unused-argument,invalid-name
        """Fetch latest prices from Forsyning API"""
        connectors = self._connectors.get_connectors(self._region.region)

        try:
            for endpoint in connectors:
                module = import_module(endpoint.namespace, __name__)
                api = module.Connector(self._region, self._client, self._tz)
                await api.async_get_spotprices()
                if api.today:
                    self.today = api.today
                    self.tomorrow = api.tomorrow
                    _LOGGER.debug(
                        "%s got values from %s (namespace='%s'), breaking loop",
                        self._region.region,
                        endpoint.module,
                        endpoint.namespace,
                    )
                    self._source = module.SOURCE_NAME
                    break

            self.today_calculated = False
            self.tomorrow_calculated = False
            if not self.tomorrow:
                self._tomorrow_valid = False
                self.tomorrow = None

                midnight = datetime.strptime("23:59:59", "%H:%M:%S")
                refresh = datetime.strptime(self.next_data_refresh, "%H:%M:%S")
                local_tz = timezone(self.hass.config.time_zone)
                now = datetime.now().astimezone(local_tz)
                _LOGGER.debug(
                    "Now: %s:%s:%s",
                    f"{now.hour:02d}",
                    f"{now.minute:02d}",
                    f"{now.second:02d}",
                )
                _LOGGER.debug(
                    "Refresh: %s:%s:%s",
                    f"{refresh.hour:02d}",
                    f"{refresh.minute:02d}",
                    f"{refresh.second:02d}",
                )
                if (
                    f"{midnight.hour}:{midnight.minute}:{midnight.second}"
                    > f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
                    and f"{refresh.hour:02d}:{refresh.minute:02d}:{refresh.second:02d}"
                    < f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
                ):
                    retry_update(self)
                else:
                    _LOGGER.debug(
                        "Not forcing refresh, as we are past midnight and haven't reached next update time"  # pylint: disable=line-too-long
                    )
            else:
                self.retry_count = 0
                self._tomorrow_valid = True
        except ServerDisconnectedError:
            _LOGGER.warning("Server disconnected.")
            retry_update(self)

    @property
    def tomorrow_valid(self) -> bool:
        """Is tomorrows prices valid?"""
        return self._tomorrow_valid

    @property
    def source(self) -> str:
        """Is tomorrows prices valid?"""
        return self._source

    @property
    def next_data_refresh(self) -> str:
        """When is next data update?"""
        return f"13:{RANDOM_MINUTE:02d}:{RANDOM_SECOND:02d}"

    @property
    def entry_id(self) -> str:
        """Return entry_id."""
        return self._entry_id


def retry_update(self) -> None:
    """Retry update on error."""
    self.retry_count += 1
    self.next_retry_delay = RETRY_MINUTES * self.retry_count
    if self.next_retry_delay > MAX_RETRY_MINUTES:
        self.next_retry_delay = MAX_RETRY_MINUTES

    _LOGGER.warning(
        "Couldn't get data from Forsyning, retrying in %s minutes.",
        self.next_retry_delay,
    )

    local_tz = timezone(self.hass.config.time_zone)
    now = (datetime.now() + timedelta(minutes=self.next_retry_delay)).astimezone(
        local_tz
    )
    _LOGGER.debug(
        "Next retry: %s:%s:%s",
        f"{now.hour:02d}",
        f"{now.minute:02d}",
        f"{now.second:02d}",
    )
    async_call_later(
        self.hass,
        timedelta(minutes=self.next_retry_delay),
        partial(self.update),
    )

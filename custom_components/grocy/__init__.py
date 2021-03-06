"""
The integration for grocy.
"""
import asyncio
import hashlib
import os
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_PORT, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import callback
from homeassistant.helpers import discovery, entity_component
from homeassistant.util import Throttle
from integrationhelper.const import CC_STARTUP_VERSION
from datetime import datetime
import iso8601

from .const import (
    LOGGER,
    DOMAIN,
    ISSUE_URL,
    REQUIRED_FILES,
    STARTUP,
    VERSION,
)

from .services import async_setup_services
from .instance import GrocyInstance

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)


async def async_setup(hass, config):
    """Old setup way."""
    return True


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""

    conf = hass.data.get(DOMAIN)
    if config_entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
        return False

    # Print startup message
    LOGGER.info(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )

    if not await hass.async_add_executor_job(check_files, hass):
        return False

    hass.data[DOMAIN] = {}

    instance = GrocyInstance(hass, config_entry)
    hass.data[DOMAIN]["instance"] = instance

    if not await instance.async_setup():
        return False

    # Setup services
    await async_setup_services(hass)

    return True


def check_files(hass):
    """Return bool that indicates if all files are present."""
    # Verify that the user downloaded all files.
    base = "{}/custom_components/{}/".format(hass.config.path(), DOMAIN)
    missing = []
    for file in REQUIRED_FILES:
        fullpath = "{}{}".format(base, file)
        if not os.path.exists(fullpath):
            missing.append(file)

    if missing:
        LOGGER.critical("The following files are missing: %s", str(missing))
        returnvalue = False
    else:
        returnvalue = True

    return returnvalue


async def async_unload_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        LOGGER.info("Successfully removed sensor from the grocy integration")
    except ValueError as error:
        LOGGER.exception(error)
        pass
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, "binary_sensor"
        )
        LOGGER.info("Successfully removed sensor from the grocy integration")
    except ValueError as error:
        LOGGER.exception(error)
        pass

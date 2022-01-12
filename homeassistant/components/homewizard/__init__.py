"""The Homewizard integration."""
import asyncio
import logging

from aiohwenergy import DisabledError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import COORDINATOR, DOMAIN, PLATFORMS
from .coordinator import HWEnergyDeviceUpdateCoordinator as Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Homewizard from a config entry."""

    _LOGGER.debug("__init__ async_setup_entry")

    # Create coordinator
    coordinator = Coordinator(hass, entry.data[CONF_IP_ADDRESS])
    try:
        await coordinator.initialize_api()

    except DisabledError:
        _LOGGER.error("API is disabled, enable API in HomeWizard Energy app")
        return False

    except UpdateFailed as ex:
        raise ConfigEntryNotReady from ex

    await coordinator.async_config_entry_first_refresh()

    # Finalize
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("__init__ async_unload_entry")

    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            )
        )
    )

    if unload_ok:
        config_data = hass.data[DOMAIN].pop(entry.entry_id)
        await config_data[COORDINATOR].api.close()

    return unload_ok

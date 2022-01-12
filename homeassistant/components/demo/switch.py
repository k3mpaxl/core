"""Demo platform that has two fake switches."""
from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEVICE_DEFAULT_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the demo switches."""
    async_add_entities(
        [
            DemoSwitch("switch1", "Decorative Lights", True, None, True),
            DemoSwitch(
                "switch2",
                "AC",
                False,
                "mdi:air-conditioner",
                False,
                device_class=SwitchDeviceClass.OUTLET,
            ),
        ]
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Demo config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoSwitch(SwitchEntity):
    """Representation of a demo switch."""

    _attr_should_poll = False

    def __init__(
        self,
        unique_id: str,
        name: str,
        state: bool,
        icon: str | None,
        assumed: bool,
        device_class: SwitchDeviceClass | None = None,
    ) -> None:
        """Initialize the Demo switch."""
        self._attr_assumed_state = assumed
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_is_on = state
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
        )

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._attr_is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._attr_is_on = False
        self.schedule_update_ha_state()

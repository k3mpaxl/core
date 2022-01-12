"""Common libraries for test setup."""

from collections.abc import Awaitable, Callable
import time
from unittest.mock import patch

from google_nest_sdm.device_manager import DeviceManager
from google_nest_sdm.event import EventMessage
from google_nest_sdm.event_media import CachePolicy
from google_nest_sdm.google_nest_subscriber import GoogleNestSubscriber

from homeassistant.components.nest import DOMAIN
from homeassistant.components.nest.const import SDM_SCOPES
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry

PROJECT_ID = "some-project-id"
CLIENT_ID = "some-client-id"
CLIENT_SECRET = "some-client-secret"

CONFIG = {
    "nest": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        # Required fields for using SDM API
        "project_id": PROJECT_ID,
        "subscriber_id": "projects/example/subscriptions/subscriber-id-9876",
    },
}

FAKE_TOKEN = "some-token"
FAKE_REFRESH_TOKEN = "some-refresh-token"


def create_config_entry(hass, token_expiration_time=None) -> MockConfigEntry:
    """Create a ConfigEntry and add it to Home Assistant."""
    if token_expiration_time is None:
        token_expiration_time = time.time() + 86400
    config_entry_data = {
        "sdm": {},  # Indicates new SDM API, not legacy API
        "auth_implementation": "nest",
        "token": {
            "access_token": FAKE_TOKEN,
            "refresh_token": FAKE_REFRESH_TOKEN,
            "scope": " ".join(SDM_SCOPES),
            "token_type": "Bearer",
            "expires_at": token_expiration_time,
        },
    }
    config_entry = MockConfigEntry(domain=DOMAIN, data=config_entry_data)
    config_entry.add_to_hass(hass)
    return config_entry


class FakeSubscriber(GoogleNestSubscriber):
    """Fake subscriber that supplies a FakeDeviceManager."""

    def __init__(self):
        """Initialize Fake Subscriber."""
        self._device_manager = DeviceManager()

    def set_update_callback(self, callback: Callable[[EventMessage], Awaitable[None]]):
        """Capture the callback set by Home Assistant."""
        self._device_manager.set_update_callback(callback)

    async def create_subscription(self):
        """Create the subscription."""
        return

    async def delete_subscription(self):
        """Delete the subscription."""
        return

    async def start_async(self):
        """Return the fake device manager."""
        return self._device_manager

    async def async_get_device_manager(self) -> DeviceManager:
        """Return the fake device manager."""
        return self._device_manager

    @property
    def cache_policy(self) -> CachePolicy:
        """Return the cache policy."""
        return self._device_manager.cache_policy

    def stop_async(self):
        """No-op to stop the subscriber."""
        return None

    async def async_receive_event(self, event_message: EventMessage):
        """Simulate a received pubsub message, invoked by tests."""
        # Update device state, then invoke HomeAssistant to refresh
        await self._device_manager.async_handle_event(event_message)


async def async_setup_sdm_platform(
    hass, platform, devices={}, structures={}, with_config=True
):
    """Set up the platform and prerequisites."""
    if with_config:
        create_config_entry(hass)
    subscriber = FakeSubscriber()
    device_manager = await subscriber.async_get_device_manager()
    if devices:
        for device in devices.values():
            device_manager.add_device(device)
    if structures:
        for structure in structures.values():
            device_manager.add_structure(structure)
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
    ), patch("homeassistant.components.nest.PLATFORMS", [platform]), patch(
        "homeassistant.components.nest.api.GoogleNestSubscriber",
        return_value=subscriber,
    ):
        assert await async_setup_component(hass, DOMAIN, CONFIG)
        await hass.async_block_till_done()
    return subscriber

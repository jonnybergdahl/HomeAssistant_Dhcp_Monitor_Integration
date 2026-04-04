"""Test the DHCP Monitor integration."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.fixture
def hass():
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    
    # Bus mocking
    hass.bus = MagicMock()
    listeners = []
    def async_listen(event_type, callback):
        listeners.append((event_type, callback))
        return lambda: None
    hass.bus.async_listen.side_effect = async_listen
    
    def async_fire(event_type, data):
        for et, cb in listeners:
            if et == event_type:
                event = MagicMock()
                event.data = data
                cb(event)
    hass.bus.async_fire.side_effect = async_fire

    hass.async_block_till_done = AsyncMock()
    return hass

from custom_components.dhcp_monitor import async_setup_entry, async_unload_entry
from custom_components.dhcp_monitor.const import DOMAIN

@pytest.mark.asyncio
async def test_setup_and_unload(hass) -> None:
    """Test setting up and unloading the integration."""
    entry = MagicMock()
    entry.async_on_unload = MagicMock()
    
    # Setup
    assert await async_setup_entry(hass, entry)
    assert DOMAIN in hass.data
    assert "history" in hass.data[DOMAIN]
    
    # Unload
    assert await async_unload_entry(hass, entry)
    assert DOMAIN not in hass.data

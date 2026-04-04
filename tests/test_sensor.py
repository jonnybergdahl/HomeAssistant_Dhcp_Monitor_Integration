"""Test the DHCP Monitor sensors."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque

@pytest.fixture
def hass():
    hass = MagicMock()
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    
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

from custom_components.dhcp_monitor import async_setup_entry
from custom_components.dhcp_monitor.const import DOMAIN, ATTR_IP_ADDRESS

@pytest.mark.asyncio
async def test_sensor_updates(hass) -> None:
    """Test sensors update on DHCP discovery."""
    entry = MagicMock()
    entry.async_on_unload = MagicMock()
    
    # Setup integration
    await async_setup_entry(hass, entry)
    
    # At this point, hass.data[DOMAIN]["history"] is initialized
    history = hass.data[DOMAIN]["history"]
    assert len(history) == 0

    # Simulate DHCP discovery via event
    discovery_data = {
        "ip": "192.168.1.100",
        "mac": "00:11:22:33:44:55",
        "hostname": "test-device",
    }
    
    # Fire the event
    hass.bus.async_fire("dhcp_discovered", discovery_data)
    
    # Check history
    assert len(history) == 1
    assert history[0]["ip_address"] == "192.168.1.100"
    
    # Simulate another discovery
    discovery_data_2 = {
        "ip": "192.168.1.101",
        "mac": "66:77:88:99:AA:BB",
        "hostname": "test-device-2",
    }
    hass.bus.async_fire("dhcp_discovered", discovery_data_2)
    
    assert len(history) == 2
    assert history[0]["ip_address"] == "192.168.1.101"
    assert history[1]["ip_address"] == "192.168.1.100"

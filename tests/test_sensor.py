"""Test the DHCP Monitor sensors."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque

@pytest.fixture
def hass_and_mock():
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

    # Mock dhcp data
    mock_dhcp_data = MagicMock()
    mock_dhcp_data.callbacks = set()
    hass.data["dhcp"] = mock_dhcp_data

    # Task management
    tasks = []
    def async_create_task(coro):
        task = MagicMock()
        tasks.append(coro)
        return task
    hass.async_create_task.side_effect = async_create_task

    async def async_block_till_done():
        while tasks:
            coro = tasks.pop(0)
            await coro
    hass.async_block_till_done = async_block_till_done
    
    return hass, mock_dhcp_data

from custom_components.dhcp_monitor import async_setup, async_setup_entry
from custom_components.dhcp_monitor.const import DOMAIN, ATTR_IP_ADDRESS

@pytest.mark.asyncio
async def test_sensor_updates(hass_and_mock) -> None:
    """Test sensors update on DHCP discovery."""
    hass, mock_dhcp_data = hass_and_mock
    entry = MagicMock()
    entry.async_on_unload = MagicMock()
    
    # Mock dhcp component
    with patch("custom_components.dhcp_monitor.DOMAIN", DOMAIN):
        # Setup integration component
        await async_setup(hass, {})
        await hass.async_block_till_done()
        
        # Setup entry
        await async_setup_entry(hass, entry)
        
        # Verify callback was registered
        assert len(mock_dhcp_data.callbacks) == 1
        # Get the callback function that was registered
        callback_func = list(mock_dhcp_data.callbacks)[0]
        
    # At this point, hass.data[DOMAIN]["history"] is initialized
    history = hass.data[DOMAIN]["history"]
    assert len(history) == 0

    # Simulate DHCP discovery via callback
    # The new callback expects dict[mac, {ip, hostname}]
    discovery_data = {
        "00:11:22:33:44:55": {
            "ip": "192.168.1.100",
            "hostname": "test-device"
        }
    }
    
    # Trigger the callback
    callback_func(discovery_data)
    
    # Check history
    assert len(history) == 1
    assert history[0]["ip_address"] == "192.168.1.100"
    assert history[0]["mac_address"] == "00:11:22:33:44:55"
    
    # Simulate another discovery
    discovery_data_2 = {
        "66:77:88:99:AA:BB": {
            "ip": "192.168.1.101",
            "hostname": "test-device-2"
        }
    }
    
    callback_func(discovery_data_2)
    
    assert len(history) == 2
    assert history[0]["ip_address"] == "192.168.1.101"
    assert history[1]["ip_address"] == "192.168.1.100"

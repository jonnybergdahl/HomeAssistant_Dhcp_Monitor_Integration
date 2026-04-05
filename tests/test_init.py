"""Test the DHCP Monitor integration."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.fixture
def hass_and_mock():
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

    def is_running():
        return True
    hass.is_running = is_running
    
    # Event listening
    event_listeners = {}
    def async_listen_once(event_type, callback):
        event_listeners[event_type] = callback
        return lambda: None
    hass.bus.async_listen_once.side_effect = async_listen_once

    async def async_block_till_done():
        while tasks:
            coro = tasks.pop(0)
            await coro
        # Also trigger EVENT_HOMEASSISTANT_STARTED if present
        if "homeassistant_started" in event_listeners:
            callback = event_listeners.pop("homeassistant_started")
            await callback(None)
    hass.async_block_till_done = async_block_till_done
    
    return hass, mock_dhcp_data

from custom_components.dhcp_monitor import async_setup, async_setup_entry, async_unload_entry
from custom_components.dhcp_monitor.const import DOMAIN

@pytest.mark.asyncio
async def test_setup_and_unload(hass_and_mock) -> None:
    """Test setting up and unloading the integration."""
    hass, mock_dhcp_data = hass_and_mock
    entry = MagicMock()
    entry.async_on_unload = MagicMock()
    
    # Mock dhcp component
    with patch("custom_components.dhcp_monitor.DOMAIN", DOMAIN):
        # Component Setup
        assert await async_setup(hass, {})
        await hass.async_block_till_done()
        
        assert len(mock_dhcp_data.callbacks) == 1
        
        # Entry Setup
        assert await async_setup_entry(hass, entry)
        
    assert DOMAIN in hass.data
    assert "history" in hass.data[DOMAIN]
    
    # Unload
    assert await async_unload_entry(hass, entry)
    assert DOMAIN not in hass.data

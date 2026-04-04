"""The DHCP Monitor integration."""
from __future__ import annotations

import logging
from collections import deque
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, CONF_COUNT

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DHCP Monitor from a config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    # Use a deque to store the last 5 devices
    hass.data[DOMAIN]["history"] = deque(maxlen=CONF_COUNT)

    @callback
    def async_handle_dhcp_discovery(data: dict) -> None:
        """Handle DHCP discovery data."""
        # data contains: ip, mac, hostname
        ip_address = data.get("ip")
        mac_address = data.get("mac")
        hostname = data.get("hostname")

        _LOGGER.debug("DHCP discovery detected: %s, %s, %s", ip_address, mac_address, hostname)

        device_info = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "hostname": hostname,
            "last_updated": datetime.now().isoformat(),
        }

        # Add to history
        history = hass.data[DOMAIN]["history"]
        # Avoid duplicate consecutive entries for the same MAC if desired, 
        # but here we just append as it's a "last 5 detected" log.
        history.appendleft(device_info)
        
        # Notify sensors to update
        async_dispatcher_send(hass, f"{DOMAIN}_update")

    # Register the DHCP discovery callback
    # The 'dhcp' integration provides a way to register for all discoveries
    # However, standard practice for many integrations is to use 'dhcp' in manifest
    # and HA will call async_setup_entry for EACH discovered device if we matched it.
    # But we want to monitor ALL DHCP discoveries.
    # We can listen to the event 'dhcp_discovered' if available or use internal API.
    
    entry.async_on_unload(
        hass.bus.async_listen("dhcp_discovered", lambda ev: async_handle_dhcp_discovery(ev.data))
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)

    return unload_ok

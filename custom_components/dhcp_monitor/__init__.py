"""The DHCP Monitor integration."""
from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, CONF_COUNT

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Use a TYPE_CHECKING block to avoid importing 'dhcp' at runtime during tests
# if it's not available, or just use it inside async_setup_entry if needed.
# However, HA uses it for type hinting.
try:
    from homeassistant.components import dhcp
except ImportError:
    # This might happen in environments without all HA dependencies installed
    dhcp = None

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the DHCP Monitor component."""
    _LOGGER.debug("Setting up DHCP Monitor component")
    
    # Check if 'dhcp' integration is loaded
    if "dhcp" not in hass.config.components:
        _LOGGER.warning("'dhcp' integration is not loaded. DHCP Monitor might not receive any events.")
    else:
        _LOGGER.debug("'dhcp' integration is loaded and should be firing events.")

    hass.data.setdefault(DOMAIN, {})
    # Use a deque to store the last 5 devices
    hass.data[DOMAIN]["history"] = deque(maxlen=CONF_COUNT)

    @callback
    def _dev_sniffer_callback(data: dict[str, Any]):
        """Handle DHCP packet."""
        # The data is a dict of {mac_address: {ip: ..., hostname: ...}}
        for mac_address, details in data.items():
            ip_address = details.get("ip")
            hostname = details.get("hostname")

            _LOGGER.debug(
                "DHCP packet received: IP=%s, MAC=%s, Hostname=%s",
                ip_address,
                mac_address,
                hostname,
            )

            device_info = {
                "ip_address": ip_address,
                "mac_address": mac_address,
                "hostname": hostname,
                "last_updated": datetime.now().isoformat(),
            }

            # Add to history
            history = hass.data[DOMAIN]["history"]
            history.appendleft(device_info)
            _LOGGER.debug("Updated history with new discovery, count: %d", len(history))

        # Notify sensors to update
        async_dispatcher_send(hass, f"{DOMAIN}_update")

    # This registers your listener to the GLOBAL dhcp signal
    _LOGGER.debug("Registering DHCP sniffer callback")
    # In Home Assistant, dhcp component stores its data in hass.data["dhcp"]
    # We add our callback to the callbacks set.
    try:
        from homeassistant.components.dhcp.models import DATA_DHCP
        # Try to use DATA_DHCP key (recommended)
        dhcp_data = hass.data.get(DATA_DHCP)
        if dhcp_data and hasattr(dhcp_data, "callbacks"):
            dhcp_data.callbacks.add(_dev_sniffer_callback)
            _LOGGER.debug("Successfully registered DHCP callback")
        else:
            # Fallback for older HA or different structure
            if "dhcp" in hass.data:
                # Some versions might use the string key directly
                d_data = hass.data["dhcp"]
                if hasattr(d_data, "callbacks"):
                    # DHCPData object
                    d_data.callbacks.add(_dev_sniffer_callback)
                    _LOGGER.debug("Successfully registered DHCP callback (fallback)")
                elif isinstance(d_data, dict) and "callbacks" in d_data:
                    # Dict storage
                    d_data["callbacks"].add(_dev_sniffer_callback)
                    _LOGGER.debug("Successfully registered DHCP callback (dict fallback)")
                else:
                    _LOGGER.error("DHCP data found but no callbacks member")
            else:
                _LOGGER.error("DHCP data not found in hass.data")
    except ImportError:
        # DATA_DHCP not available, try string key fallback
        if "dhcp" in hass.data:
            d_data = hass.data["dhcp"]
            if hasattr(d_data, "callbacks"):
                d_data.callbacks.add(_dev_sniffer_callback)
                _LOGGER.debug("Successfully registered DHCP callback (ImportError fallback)")
            elif isinstance(d_data, dict) and "callbacks" in d_data:
                d_data["callbacks"].add(_dev_sniffer_callback)
                _LOGGER.debug("Successfully registered DHCP callback (ImportError dict fallback)")
    except Exception as err:
        _LOGGER.error("Failed to register DHCP callback: %s", err)

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DHCP Monitor from a config entry."""
    _LOGGER.debug("Setting up DHCP Monitor integration entry")
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading DHCP Monitor integration")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)

    return unload_ok

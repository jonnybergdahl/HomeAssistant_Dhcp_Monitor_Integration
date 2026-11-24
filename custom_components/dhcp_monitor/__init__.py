"""The DHCP Monitor integration."""
from __future__ import annotations

import logging
from collections import deque
from typing import Any

from homeassistant.components.dhcp.helpers import (
    async_register_dhcp_callback_internal,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_COUNT

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DHCP Monitor from a config entry."""
    _LOGGER.debug("Setting up DHCP Monitor integration entry")

    history: deque[dict[str, Any]] = deque(maxlen=CONF_COUNT)
    hass.data.setdefault(DOMAIN, {})["history"] = history

    @callback
    def _dhcp_callback(data: dict[str, Any]) -> None:
        """Handle a DHCP address update ({mac_address: {ip, hostname}})."""
        for mac_address, details in data.items():
            ip_address = details.get("ip")
            hostname = details.get("hostname")

            _LOGGER.debug(
                "DHCP packet received: IP=%s, MAC=%s, Hostname=%s",
                ip_address,
                mac_address,
                hostname,
            )

            # Format MAC address to 00:00:00... style
            formatted_mac = mac_address
            if ":" not in mac_address:
                formatted_mac = ":".join(
                    mac_address[i : i + 2] for i in range(0, len(mac_address), 2)
                )

            history.appendleft(
                {
                    "ip_address": ip_address,
                    "mac_address": formatted_mac,
                    "hostname": hostname,
                    "last_updated": dt_util.now(),
                }
            )
            _LOGGER.debug("Updated history with new discovery, count: %d", len(history))

        async_dispatcher_send(hass, f"{DOMAIN}_update")

    _LOGGER.debug("Registering DHCP sniffer callback")
    # Relies on an internal helper of the dhcp integration; there is no public
    # API for subscribing to DHCP packets.
    entry.async_on_unload(
        async_register_dhcp_callback_internal(hass, _dhcp_callback)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading DHCP Monitor integration")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN, None)

    return unload_ok

"""Sensor platform for DHCP Monitor."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_COUNT, ATTR_IP_ADDRESS, ATTR_MAC_ADDRESS, ATTR_HOSTNAME, ATTR_LAST_UPDATED

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DHCP Monitor sensors."""
    
    entities = []
    for i in range(1, CONF_COUNT + 1):
        entities.append(DhcpDeviceSensor(i))
    
    async_add_entities(entities)

class DhcpDeviceSensor(SensorEntity):
    """Sensor that shows information about the Nth last detected DHCP device."""

    def __init__(self, index: int) -> None:
        """Initialize the sensor."""
        self._index = index
        self._attr_name = f"DHCP Device {index}"
        self._attr_unique_id = f"dhcp_monitor_device_{index}"
        self._attr_icon = "mdi:lan-connect"
        self._state_attributes = {}

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        history = self.hass.data[DOMAIN].get("history", [])
        if len(history) >= self._index:
            device = history[self._index - 1]
            return device.get("ip_address", "Unknown")
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        history = self.hass.data[DOMAIN].get("history", [])
        if len(history) >= self._index:
            device = history[self._index - 1]
            return {
                ATTR_IP_ADDRESS: device.get("ip_address"),
                ATTR_MAC_ADDRESS: device.get("mac_address"),
                ATTR_HOSTNAME: device.get("hostname"),
                ATTR_LAST_UPDATED: device.get("last_updated"),
            }
        return {}

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update", self.async_write_ha_state
            )
        )

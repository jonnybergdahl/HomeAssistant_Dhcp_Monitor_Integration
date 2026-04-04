"""Config flow for DHCP Monitor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class DhcpMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DHCP Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Handling user step of config flow: %s", user_input)
        if self._async_current_entries():
            _LOGGER.debug("Aborting config flow as an instance is already configured")
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            _LOGGER.debug("Creating entry for DHCP Monitor")
            return self.async_create_entry(title="DHCP Monitor", data={})

        return self.async_show_form(step_id="user")

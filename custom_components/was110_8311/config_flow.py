"""Config flow for 8311 ONU Monitor integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import asyncssh
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=10, max=300)
        ),
    }
)


async def validate_connection(
    host: str, port: int, username: str, password: str
) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    errors: dict[str, str] = {}

    try:
        async with asyncio.timeout(10):
            conn = await asyncssh.connect(
                host,
                port=port,
                username=username,
                password=password,
                known_hosts=None,
                connect_timeout=10,
            )
            # Test a simple command
            result = await conn.run("echo test", check=True)
            conn.close()
            await conn.wait_closed()

            if result.stdout.strip() != "test":
                errors["base"] = "cannot_connect"

    except asyncssh.PermissionDenied:
        errors["base"] = "invalid_auth"
    except asyncssh.HostKeyNotVerifiable:
        errors["base"] = "cannot_connect"
    except (OSError, asyncssh.Error) as err:
        _LOGGER.debug("Connection error: %s", err)
        errors["base"] = "cannot_connect"
    except TimeoutError:
        errors["base"] = "timeout"

    return errors


class WAS110ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 8311 ONU Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            # Validate connection
            errors = await validate_connection(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            if not errors:
                return self.async_create_entry(
                    title=f"8311 ONU ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]  # noqa: ARG002
    ) -> FlowResult:
        """Handle reauthorization."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauthorization confirmation."""
        errors: dict[str, str] = {}

        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            errors = await validate_connection(
                reauth_entry.data[CONF_HOST],
                reauth_entry.data[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            if not errors:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_USERNAME,
                        default=reauth_entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "host": reauth_entry.data[CONF_HOST],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return WAS110OptionsFlowHandler(config_entry)


class WAS110OptionsFlowHandler(OptionsFlow):
    """Handle options flow for 8311 ONU."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        ),
                    ): vol.All(int, vol.Range(min=10, max=300)),
                }
            ),
        )

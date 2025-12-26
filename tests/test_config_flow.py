"""Tests for 8311 ONU config flow."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.was110_8311.const import DOMAIN


async def test_form_user(hass: HomeAssistant, mock_asyncssh) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.was110_8311.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.11.1",
                CONF_USERNAME: "root",
                CONF_PASSWORD: "testpass",
                CONF_PORT: 22,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "8311 ONU (192.168.11.1)"
    assert result2["data"] == {
        CONF_HOST: "192.168.11.1",
        CONF_USERNAME: "root",
        CONF_PASSWORD: "testpass",
        CONF_PORT: 22,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.was110_8311.config_flow.asyncssh.connect",
        side_effect=Exception("Permission denied"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.11.1",
                CONF_USERNAME: "root",
                CONF_PASSWORD: "wrongpass",
                CONF_PORT: 22,
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.was110_8311.config_flow.asyncssh.connect",
        side_effect=OSError("Connection refused"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "192.168.11.1",
                CONF_USERNAME: "root",
                CONF_PASSWORD: "testpass",
                CONF_PORT: 22,
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}

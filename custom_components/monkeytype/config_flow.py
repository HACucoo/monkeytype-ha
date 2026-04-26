"""Config flow for Monkeytype."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    BASE_URL,
    CLIENT_VERSION,
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_MODE,
    CONF_MODE2,
    DEFAULT_LANGUAGE,
    DEFAULT_MODE,
    DEFAULT_MODE2,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

VALID_MODES = ["time", "words", "quote", "custom", "zen"]

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_MODE, default=DEFAULT_MODE): vol.In(VALID_MODES),
        vol.Optional(CONF_MODE2, default=DEFAULT_MODE2): str,
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): str,
    }
)

STEP_REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


class MonkeytypeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Monkeytype config flow including reauth."""

    VERSION = 1

    def __init__(self) -> None:
        self._reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = (
                f"{user_input[CONF_MODE]}"
                f"{user_input[CONF_MODE2]}"
                f"_{user_input[CONF_LANGUAGE]}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            errors = await _validate_api_key(self.hass, user_input[CONF_API_KEY])
            if not errors:
                title = (
                    f"Monkeytype "
                    f"{user_input[CONF_MODE]}/{user_input[CONF_MODE2]} "
                    f"({user_input[CONF_LANGUAGE]})"
                )
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(self, _entry_data: dict[str, Any]) -> FlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        assert self._reauth_entry is not None

        if user_input is not None:
            errors = await _validate_api_key(self.hass, user_input[CONF_API_KEY])
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={**self._reauth_entry.data, CONF_API_KEY: user_input[CONF_API_KEY]},
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=STEP_REAUTH_SCHEMA, errors=errors
        )


async def _validate_api_key(hass, api_key: str) -> dict[str, str]:
    """Probe the API with the given key. Empty dict = OK."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"{BASE_URL}/results",
            headers={"Authorization": f"ApeKey {api_key}", "X-Client-Version": CLIENT_VERSION},
            params={"limit": 1},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            _LOGGER.debug("Monkeytype validation response: %s", resp.status)
            if resp.status == 200:
                return {}
            if resp.status == 401:
                return {"base": "invalid_auth"}
            if resp.status == 471:
                return {"base": "ape_key_inactive"}
            if resp.status == 479:
                return {}  # Rate limited but key is valid – allow setup
            _LOGGER.warning("Monkeytype API returned unexpected status %s", resp.status)
            return {"base": "cannot_connect"}
    except aiohttp.ClientError as err:
        _LOGGER.warning("Monkeytype connection error: %s", err)
        return {"base": "cannot_connect"}

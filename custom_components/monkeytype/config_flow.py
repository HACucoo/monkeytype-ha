"""Config flow for Monkeytype."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    BASE_URL,
    CONF_API_KEY,
    CONF_MODE,
    CONF_MODE2,
    CONF_LANGUAGE,
    DEFAULT_MODE,
    DEFAULT_MODE2,
    DEFAULT_LANGUAGE,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_MODE, default=DEFAULT_MODE): vol.In(
            ["time", "words", "quote", "custom", "zen"]
        ),
        vol.Optional(CONF_MODE2, default=DEFAULT_MODE2): str,
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): str,
    }
)


class MonkeytypeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = (
                f"{user_input[CONF_MODE]}"
                f"{user_input[CONF_MODE2]}"
                f"_{user_input[CONF_LANGUAGE]}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            errors = await _validate_api_key(user_input[CONF_API_KEY])

            if not errors:
                title = (
                    f"Monkeytype "
                    f"{user_input[CONF_MODE]}/{user_input[CONF_MODE2]} "
                    f"({user_input[CONF_LANGUAGE]})"
                )
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )


async def _validate_api_key(api_key: str) -> dict[str, str]:
    """Test the ApeKey against the API. Returns errors dict (empty = OK)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/results",
                headers={"Authorization": f"ApeKey {api_key}"},
                params={"limit": 1},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    return {"base": "invalid_auth"}
                if resp.status != 200:
                    return {"base": "cannot_connect"}
    except aiohttp.ClientError:
        return {"base": "cannot_connect"}
    return {}

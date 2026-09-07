"""Config flow for XPENG Vehicles integration."""
from __future__ import annotations

import os
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_CLEANUP_FILES,
    CONF_DATA_DIR,
    CONF_HOME_CHARGE_ENABLED,
    CONF_HOME_CHARGE_END_HOUR,
    CONF_HOME_CHARGE_MAX_POWER,
    CONF_HOME_CHARGE_MIN_POWER,
    CONF_HOME_CHARGE_START_HOUR,
    CONF_MODE,
    CONF_OPEN_ID,
    CONF_VEHICLE_NAME,
    DEFAULT_CLEANUP_FILES,
    DEFAULT_DATA_DIR,
    DEFAULT_HOME_CHARGE_ENABLED,
    DEFAULT_HOME_CHARGE_END_HOUR,
    DEFAULT_HOME_CHARGE_MAX_POWER,
    DEFAULT_HOME_CHARGE_MIN_POWER,
    DEFAULT_HOME_CHARGE_START_HOUR,
    DEFAULT_VEHICLE_NAME,
    DOMAIN,
    MODE_API,
    MODE_LOCAL_DIR,
)


class XpengConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for XPENG Vehicles."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._mode: str = MODE_LOCAL_DIR
        self._vehicle_name: str = DEFAULT_VEHICLE_NAME

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step where user selects the mode."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._mode = user_input[CONF_MODE]
            self._vehicle_name = user_input.get(CONF_VEHICLE_NAME, DEFAULT_VEHICLE_NAME)

            if self._mode == MODE_LOCAL_DIR:
                return await self.async_step_local_dir()
            return await self.async_step_api()

        schema = vol.Schema(
            {
                vol.Required(CONF_VEHICLE_NAME, default=DEFAULT_VEHICLE_NAME): str,
                vol.Required(CONF_MODE, default=MODE_LOCAL_DIR): vol.In(
                    {
                        MODE_LOCAL_DIR: "Local Directory (CSV Drop)",
                        MODE_API: "XPENG Open Platform API",
                    }
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_local_dir(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle local directory configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data_dir = user_input[CONF_DATA_DIR]
            # Ensure directory exists or create it
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as err:
                errors["base"] = "cannot_create_dir"

            if not errors:
                return self.async_create_entry(
                    title=f"XPENG {self._vehicle_name}",
                    data={
                        CONF_VEHICLE_NAME: self._vehicle_name,
                        CONF_MODE: MODE_LOCAL_DIR,
                        CONF_DATA_DIR: data_dir,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_DATA_DIR, default=DEFAULT_DATA_DIR): str,
            }
        )

        return self.async_show_form(step_id="local_dir", data_schema=schema, errors=errors)

    async def async_step_api(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle XPENG API credentials configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data_dir = user_input.get(CONF_DATA_DIR, DEFAULT_DATA_DIR)
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception:
                pass

            return self.async_create_entry(
                title=f"XPENG {self._vehicle_name} (API)",
                data={
                    CONF_VEHICLE_NAME: self._vehicle_name,
                    CONF_MODE: MODE_API,
                    CONF_APP_ID: user_input[CONF_APP_ID],
                    CONF_APP_SECRET: user_input[CONF_APP_SECRET],
                    CONF_OPEN_ID: user_input[CONF_OPEN_ID],
                    CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                    CONF_DATA_DIR: data_dir,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_APP_ID): str,
                vol.Required(CONF_APP_SECRET): str,
                vol.Required(CONF_OPEN_ID): str,
                vol.Required(CONF_ACCESS_TOKEN): str,
                vol.Optional(CONF_DATA_DIR, default=DEFAULT_DATA_DIR): str,
            }
        )

        return self.async_show_form(step_id="api", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow handler for this handler."""
        return XpengOptionsFlowHandler(config_entry)


class XpengOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle XPENG options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CLEANUP_FILES,
                    default=options.get(CONF_CLEANUP_FILES, DEFAULT_CLEANUP_FILES),
                ): bool,
                vol.Optional(
                    CONF_HOME_CHARGE_ENABLED,
                    default=options.get(CONF_HOME_CHARGE_ENABLED, DEFAULT_HOME_CHARGE_ENABLED),
                ): bool,
                vol.Optional(
                    CONF_HOME_CHARGE_MIN_POWER,
                    default=options.get(CONF_HOME_CHARGE_MIN_POWER, DEFAULT_HOME_CHARGE_MIN_POWER),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_HOME_CHARGE_MAX_POWER,
                    default=options.get(CONF_HOME_CHARGE_MAX_POWER, DEFAULT_HOME_CHARGE_MAX_POWER),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_HOME_CHARGE_START_HOUR,
                    default=options.get(CONF_HOME_CHARGE_START_HOUR, DEFAULT_HOME_CHARGE_START_HOUR),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                vol.Optional(
                    CONF_HOME_CHARGE_END_HOUR,
                    default=options.get(CONF_HOME_CHARGE_END_HOUR, DEFAULT_HOME_CHARGE_END_HOUR),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)

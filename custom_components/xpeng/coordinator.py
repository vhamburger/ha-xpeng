"""DataUpdateCoordinator for XPENG Vehicles."""
from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XpengApiClient, XpengApiError
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
    CONF_VEHICLE_MODEL,
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
    MODEL_AUTO,
    VMODEL_CODE_MAP,
)
from .parser import XpengCsvParser, XpengParsedData

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_cumulative_storage"


class XpengDataUpdateCoordinator(DataUpdateCoordinator[XpengParsedData]):
    """Class to manage fetching and parsing XPENG vehicle data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.vehicle_name = entry.data.get(CONF_VEHICLE_NAME, DEFAULT_VEHICLE_NAME)
        self.mode = entry.data.get(CONF_MODE, MODE_LOCAL_DIR)
        self.data_dir = entry.data.get(CONF_DATA_DIR, DEFAULT_DATA_DIR)

        # Storage for persistent cumulative values across runs
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self._stored_cumulative: dict[str, Any] = {
            "cumulative_total_energy_kwh": 0.0,
            "cumulative_home_energy_kwh": 0.0,
            "processed_file_hashes": [],
        }

        # Initialize API client if in API mode
        self._api_client: XpengApiClient | None = None
        if self.mode == MODE_API:
            self._api_client = XpengApiClient(
                app_id=entry.data.get(CONF_APP_ID, ""),
                app_secret=entry.data.get(CONF_APP_SECRET, ""),
                open_id=entry.data.get(CONF_OPEN_ID, ""),
                access_token=entry.data.get(CONF_ACCESS_TOKEN, ""),
                session=async_get_clientsession(hass),
            )

        # Check every 30 minutes for new CSV drops or API updates
        super().__init__(
            hass,
            _LOGGER,
            name=f"XPENG {self.vehicle_name}",
            update_interval=timedelta(minutes=30),
        )

    @property
    def home_charge_enabled(self) -> bool:
        """Return whether home charging classification is enabled."""
        return self.entry.options.get(CONF_HOME_CHARGE_ENABLED, DEFAULT_HOME_CHARGE_ENABLED)

    @property
    def home_charge_min_power(self) -> float:
        """Return minimum power for home charging classification."""
        return float(self.entry.options.get(CONF_HOME_CHARGE_MIN_POWER, DEFAULT_HOME_CHARGE_MIN_POWER))

    @property
    def home_charge_max_power(self) -> float:
        """Return maximum power for home charging classification."""
        return float(self.entry.options.get(CONF_HOME_CHARGE_MAX_POWER, DEFAULT_HOME_CHARGE_MAX_POWER))

    @property
    def home_charge_start_hour(self) -> int:
        """Return starting hour for night home charge window."""
        return int(self.entry.options.get(CONF_HOME_CHARGE_START_HOUR, DEFAULT_HOME_CHARGE_START_HOUR))

    @property
    def home_charge_end_hour(self) -> int:
        """Return ending hour for night home charge window."""
        return int(self.entry.options.get(CONF_HOME_CHARGE_END_HOUR, DEFAULT_HOME_CHARGE_END_HOUR))

    @property
    def cleanup_files(self) -> bool:
        """Return whether processed files should be deleted to save disk space."""
        return self.entry.options.get(CONF_CLEANUP_FILES, DEFAULT_CLEANUP_FILES)

    @property
    def resolved_model(self) -> str:
        """Resolve commercial vehicle model from user setting or telemetry code."""
        configured_model = self.entry.data.get(CONF_VEHICLE_MODEL, MODEL_AUTO)
        if configured_model and configured_model != MODEL_AUTO:
            return f"XPENG {configured_model}" if not configured_model.startswith("XPENG") else configured_model

        raw_model = self.data.vmodel if self.data and self.data.vmodel else ""
        if raw_model:
            for prefix, name in VMODEL_CODE_MAP.items():
                if raw_model.startswith(prefix) or prefix in raw_model:
                    return f"XPENG {name}"
            return f"XPENG {raw_model}"

        return "XPENG Vehicle"

    async def _async_setup(self) -> None:
        """Load stored persistent data on startup."""
        stored = await self._store.async_load()
        if stored:
            self._stored_cumulative.update(stored)

    async def _async_update_data(self) -> XpengParsedData:
        """Fetch and parse new data from CSV drops or API."""
        if not self._stored_cumulative.get("loaded"):
            await self._async_setup()
            self._stored_cumulative["loaded"] = True

        parser = XpengCsvParser(
            home_charge_enabled=self.home_charge_enabled,
            home_charge_min_power=self.home_charge_min_power,
            home_charge_max_power=self.home_charge_max_power,
            home_charge_start_hour=self.home_charge_start_hour,
            home_charge_end_hour=self.home_charge_end_hour,
        )

        # 1. API Mode: check if we should trigger an API download
        if self.mode == MODE_API and self._api_client:
            try:
                # Trigger export task or check task
                res = await self._api_client.submit_query_task()
                download_url = res.get("data", {}).get("downloadUrl")
                if download_url:
                    os.makedirs(self.data_dir, exist_ok=True)
                    dest_zip = os.path.join(self.data_dir, "xpeng_export.zip")
                    await self._api_client.download_file(download_url, dest_zip)
            except XpengApiError as err:
                _LOGGER.warning("XPENG API query failed (will fallback to existing files): %s", err)

        # 2. Parse directory
        parsed_data, processed_files = await self.hass.async_add_executor_job(
            parser.parse_directory, self.data_dir
        )

        if not parsed_data:
            # If no new files were found, retain last known state
            if self.data is not None:
                return self.data
            # Restore previous state from storage if available
            restored = XpengParsedData()
            restored.total_energy_charged_kwh = self._stored_cumulative.get("cumulative_total_energy_kwh", 0.0)
            restored.home_energy_charged_kwh = self._stored_cumulative.get("cumulative_home_energy_kwh", 0.0)
            restored.battery_level = self._stored_cumulative.get("battery_level")
            restored.range_km = self._stored_cumulative.get("range_km")
            restored.odometer = self._stored_cumulative.get("odometer")
            restored.battery_voltage = self._stored_cumulative.get("battery_voltage")
            restored.battery_current = self._stored_cumulative.get("battery_current")
            restored.battery_temp_max = self._stored_cumulative.get("battery_temp_max")
            restored.battery_temp_min = self._stored_cumulative.get("battery_temp_min")
            restored.tire_pressure_fl = self._stored_cumulative.get("tire_pressure_fl")
            restored.tire_pressure_fr = self._stored_cumulative.get("tire_pressure_fr")
            restored.tire_pressure_rl = self._stored_cumulative.get("tire_pressure_rl")
            restored.tire_pressure_rr = self._stored_cumulative.get("tire_pressure_rr")
            restored.last_charge_kwh = self._stored_cumulative.get("last_charge_kwh")
            restored.last_charge_timestamp = self._stored_cumulative.get("last_charge_timestamp")
            restored.vin = self._stored_cumulative.get("vin")
            restored.vmodel = self._stored_cumulative.get("vmodel")
            restored.last_timestamp = self._stored_cumulative.get("last_timestamp")
            return restored

        # 3. Accumulate Energy & Update Persistent Telemetry
        prev_total = self._stored_cumulative.get("cumulative_total_energy_kwh", 0.0)
        prev_home = self._stored_cumulative.get("cumulative_home_energy_kwh", 0.0)

        # The parsed file contains energy charged during the batch period
        new_total = round(prev_total + parsed_data.total_energy_charged_kwh, 3)
        new_home = round(prev_home + parsed_data.home_energy_charged_kwh, 3)

        parsed_data.total_energy_charged_kwh = new_total
        parsed_data.home_energy_charged_kwh = new_home

        self._stored_cumulative.update({
            "cumulative_total_energy_kwh": new_total,
            "cumulative_home_energy_kwh": new_home,
            "battery_level": parsed_data.battery_level,
            "range_km": parsed_data.range_km,
            "odometer": parsed_data.odometer,
            "battery_voltage": parsed_data.battery_voltage,
            "battery_current": parsed_data.battery_current,
            "battery_temp_max": parsed_data.battery_temp_max,
            "battery_temp_min": parsed_data.battery_temp_min,
            "tire_pressure_fl": parsed_data.tire_pressure_fl,
            "tire_pressure_fr": parsed_data.tire_pressure_fr,
            "tire_pressure_rl": parsed_data.tire_pressure_rl,
            "tire_pressure_rr": parsed_data.tire_pressure_rr,
            "last_charge_kwh": parsed_data.last_charge_kwh,
            "last_charge_timestamp": parsed_data.last_charge_timestamp,
            "vin": parsed_data.vin,
            "vmodel": parsed_data.vmodel,
            "last_timestamp": parsed_data.last_timestamp,
        })
        await self._store.async_save(self._stored_cumulative)

        # 4. Retention / Cleanup: Remove processed files if enabled (via executor to avoid blocking event loop)
        if self.cleanup_files and processed_files:
            await self.hass.async_add_executor_job(self._cleanup_processed, processed_files)

        return parsed_data

    def _cleanup_processed(self, processed_files: list[str]) -> None:
        """Clean up processed files and empty directories in executor thread."""
        _LOGGER.info("Cleaning up %d processed XPENG CSV/ZIP files to save disk space", len(processed_files))
        for file_path in processed_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    _LOGGER.debug("Removed processed file: %s", file_path)
            except Exception as err:
                _LOGGER.error("Failed to delete processed file %s: %s", file_path, err)

        # Also remove any empty subdirectories left behind by zip extraction
        for root, dirs, _ in os.walk(self.data_dir, topdown=False):
            for d in dirs:
                d_path = os.path.join(root, d)
                try:
                    if not os.listdir(d_path):
                        os.rmdir(d_path)
                except Exception:
                    pass

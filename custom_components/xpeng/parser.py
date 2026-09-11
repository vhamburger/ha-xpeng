"""Data parser for XPENG vehicle GDPR / Open Platform CSV exports."""
from __future__ import annotations

import csv
import glob
import logging
import os
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class ChargingSession:
    """Represents a discrete charging session."""

    start_timestamp: int
    end_timestamp: int
    energy_kwh: float
    avg_power_kw: float
    max_power_kw: float
    is_home_charge: bool = False
    prev_trip_end_ts: int | None = None

    @property
    def start_datetime(self) -> datetime:
        """Return start datetime in UTC."""
        return datetime.fromtimestamp(self.start_timestamp, tz=timezone.utc)

    @property
    def end_datetime(self) -> datetime:
        """Return end datetime in UTC."""
        return datetime.fromtimestamp(self.end_timestamp, tz=timezone.utc)


@dataclass
class DrivingTrip:
    """Represents a discrete driving trip."""

    start_timestamp: int
    end_timestamp: int
    duration_seconds: int
    rolling_seconds: int


@dataclass
class XpengParsedData:
    """Aggregated parsed vehicle data from all CSV exports."""

    vin: str | None = None
    vmodel: str | None = None
    last_timestamp: int | None = None

    # Telemetry
    battery_level: float | None = None  # %
    range_km: float | None = None  # km
    odometer: float | None = None  # km
    battery_voltage: float | None = None  # V
    battery_current: float | None = None  # A
    battery_temp_max: float | None = None  # °C
    battery_temp_min: float | None = None  # °C

    # Tire Pressure (in bar, converted from kPa)
    tire_pressure_fl: float | None = None
    tire_pressure_fr: float | None = None
    tire_pressure_rl: float | None = None
    tire_pressure_rr: float | None = None

    # Doors / Trunk (0=closed, 1=open)
    door_driver_open: bool | None = None
    door_passenger_open: bool | None = None
    door_rear_left_open: bool | None = None
    door_rear_right_open: bool | None = None
    trunk_open: bool | None = None

    # Charging
    is_charging: bool = False
    current_charge_power_kw: float = 0.0
    total_energy_charged_kwh: float = 0.0
    home_energy_charged_kwh: float = 0.0
    last_charge_kwh: float = 0.0
    last_charge_timestamp: int | None = None

    charging_sessions: list[ChargingSession] = field(default_factory=list)

    # Driving
    driving_trips: list[DrivingTrip] = field(default_factory=list)
    driving_seconds: int = 0
    driving_rolling_seconds: int = 0
    total_driving_hours: float = 0.0


class XpengCsvParser:
    """Parser for XPENG GDPR / Open Platform CSV exports."""

    def __init__(
        self,
        home_charge_enabled: bool = True,
        home_charge_min_power: float = 8.0,
        home_charge_max_power: float = 12.0,
        home_charge_start_hour: int = 20,
        home_charge_end_hour: int = 7,
    ) -> None:
        """Initialize the parser with home charge configuration."""
        self.home_charge_enabled = home_charge_enabled
        self.home_charge_min_power = home_charge_min_power
        self.home_charge_max_power = home_charge_max_power
        self.home_charge_start_hour = home_charge_start_hour
        self.home_charge_end_hour = home_charge_end_hour

    def parse_directory(self, directory_path: str) -> tuple[XpengParsedData | None, list[str]]:
        """Find and parse XPENG CSV or ZIP files in the given directory.

        Returns a tuple of (parsed_data, list_of_processed_file_paths).
        """
        if not os.path.isdir(directory_path):
            _LOGGER.warning("Directory does not exist: %s", directory_path)
            return None, []

        processed_files: list[str] = []

        # 1. Find all ZIP files (recursive and case-insensitive)
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(".zip"):
                    zip_path = os.path.join(root, file)
                    try:
                        _LOGGER.info("Extracting XPENG ZIP archive: %s", zip_path)
                        with zipfile.ZipFile(zip_path, "r") as zip_ref:
                            zip_ref.extractall(directory_path)
                        processed_files.append(zip_path)
                    except Exception as err:
                        _LOGGER.error("Failed to extract zip file %s: %s", zip_path, err)

        # 2. Locate the 3 CSV categories (recursive across any subfolder and case-insensitive)
        power_files: list[str] = []
        operation_files: list[str] = []
        status_files: list[str] = []

        for root, _, files in os.walk(directory_path):
            for file in files:
                lower = file.lower()
                if not lower.endswith(".csv"):
                    continue
                full_path = os.path.join(root, file)
                if "power_energy" in lower:
                    power_files.append(full_path)
                elif "operation" in lower:
                    operation_files.append(full_path)
                elif "status" in lower:
                    status_files.append(full_path)

        if not power_files and not operation_files and not status_files:
            _LOGGER.warning("No XPENG CSV files found in %s (searched subfolders)", directory_path)
            return None, processed_files

        data = XpengParsedData()

        # Parse power & energy (primary source for battery & charging)
        if power_files:
            # Sort files chronologically if multiple exist
            power_files.sort()
            for p_file in power_files:
                self._parse_power_energy(p_file, data)
                processed_files.append(p_file)

        # Parse operation (odometer, speed)
        if operation_files:
            operation_files.sort()
            for o_file in operation_files:
                self._parse_operation(o_file, data)
                processed_files.append(o_file)

        # Parse status (tire pressures, doors)
        if status_files:
            status_files.sort()
            for s_file in status_files:
                self._parse_status(s_file, data)
                processed_files.append(s_file)

        data.driving_seconds = sum(t.duration_seconds for t in data.driving_trips)
        data.driving_rolling_seconds = sum(t.rolling_seconds for t in data.driving_trips)
        data.total_driving_hours = round(data.driving_seconds / 3600.0, 2)

        # Correlate charging sessions with preceding driving trips to mark arrival time
        for session in data.charging_sessions:
            prev_trips = [t for t in data.driving_trips if t.end_timestamp <= session.start_timestamp]
            if prev_trips:
                session.prev_trip_end_ts = max(t.end_timestamp for t in prev_trips)
            else:
                session.prev_trip_end_ts = max(0, session.start_timestamp - 14400)

        return data, list(set(processed_files))

    def _parse_power_energy(self, file_path: str, data: XpengParsedData) -> None:
        """Parse driving_power_energy CSV file."""
        _LOGGER.debug("Parsing power energy file: %s", file_path)
        active_session_seconds = 0
        active_session_power_sum = 0.0
        active_session_max_power = 0.0
        active_session_start_ts = 0
        last_charge_ts = 0
        latest_energy_ts = 0

        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not data.vin and row.get("vin"):
                    data.vin = row["vin"]
                if not data.vmodel and row.get("vmodel"):
                    data.vmodel = row["vmodel"]

                ts_str = row.get("timer")
                if not ts_str:
                    continue
                try:
                    ts = int(ts_str)
                except ValueError:
                    continue

                if data.last_timestamp is None or ts > data.last_timestamp:
                    data.last_timestamp = ts

                if ts >= latest_energy_ts:
                    latest_energy_ts = ts
                    # Battery SoC
                    soc_str = row.get("ldcu_bms_soc_disp")
                    if soc_str:
                        try:
                            data.battery_level = float(soc_str)
                        except ValueError:
                            pass

                    # Range
                    range_str = row.get("ldcu_dstbatdisp_dynamic")
                    if range_str:
                        try:
                            data.range_km = float(range_str)
                        except ValueError:
                            pass

                    # Battery Voltage & Current
                    volt_str = row.get("bms_battvolt")
                    curr_str = row.get("bms_battcurr")
                    if volt_str:
                        try:
                            data.battery_voltage = float(volt_str)
                        except ValueError:
                            pass
                    if curr_str:
                        try:
                            data.battery_current = float(curr_str)
                        except ValueError:
                            pass

                    # Battery Temperatures
                    tmax_str = row.get("bms_batttempmax_gb")
                    tmin_str = row.get("bms_batttempmin_gb")
                    if tmax_str:
                        try:
                            data.battery_temp_max = float(tmax_str)
                        except ValueError:
                            pass
                    if tmin_str:
                        try:
                            data.battery_temp_min = float(tmin_str)
                        except ValueError:
                            pass

                # Charging power integration
                chrg_str = row.get("ldcu_chrgpwr")
                chrg_pwr = 0.0
                if chrg_str:
                    try:
                        chrg_pwr = float(chrg_str)
                    except ValueError:
                        pass

                if chrg_pwr > 0:
                    # 1 second of charging at chrg_pwr kW = (chrg_pwr / 3600) kWh
                    kwh_sec = chrg_pwr / 3600.0
                    data.total_energy_charged_kwh += kwh_sec

                    # Session tracking: if gap > 120s from previous second, finish old session
                    if active_session_seconds > 0 and (ts - last_charge_ts) > 120:
                        self._finalize_session(
                            data,
                            active_session_start_ts,
                            last_charge_ts,
                            active_session_power_sum,
                            active_session_seconds,
                            active_session_max_power,
                        )
                        active_session_seconds = 0
                        active_session_power_sum = 0.0
                        active_session_max_power = 0.0

                    if active_session_seconds == 0:
                        active_session_start_ts = ts

                    active_session_seconds += 1
                    active_session_power_sum += chrg_pwr
                    if chrg_pwr > active_session_max_power:
                        active_session_max_power = chrg_pwr
                    last_charge_ts = ts
                else:
                    if active_session_seconds > 0 and (ts - last_charge_ts) > 120:
                        self._finalize_session(
                            data,
                            active_session_start_ts,
                            last_charge_ts,
                            active_session_power_sum,
                            active_session_seconds,
                            active_session_max_power,
                        )
                        active_session_seconds = 0
                        active_session_power_sum = 0.0
                        active_session_max_power = 0.0

            # Finalize any ongoing session at EOF
            if active_session_seconds > 0:
                self._finalize_session(
                    data,
                    active_session_start_ts,
                    last_charge_ts,
                    active_session_power_sum,
                    active_session_seconds,
                    active_session_max_power,
                )

        data.total_energy_charged_kwh = round(data.total_energy_charged_kwh, 3)
        data.home_energy_charged_kwh = round(data.home_energy_charged_kwh, 3)

    def _finalize_session(
        self,
        data: XpengParsedData,
        start_ts: int,
        end_ts: int,
        power_sum: float,
        seconds: int,
        max_power: float,
    ) -> None:
        """Finalize a detected charging session and classify home vs away."""
        if seconds <= 0:
            return

        energy_kwh = round(power_sum / 3600.0, 3)
        avg_power = round(power_sum / seconds, 2)

        # Check home charging condition
        is_home = False
        if self.home_charge_enabled:
            # Check power window
            power_matches = self.home_charge_min_power <= avg_power <= self.home_charge_max_power

            # Check night hour window
            dt = datetime.fromtimestamp(start_ts, tz=timezone.utc).astimezone()
            hour = dt.hour
            if self.home_charge_start_hour > self.home_charge_end_hour:
                # e.g. 20:00 to 07:00
                hour_matches = hour >= self.home_charge_start_hour or hour < self.home_charge_end_hour
            else:
                hour_matches = self.home_charge_start_hour <= hour < self.home_charge_end_hour

            if power_matches and hour_matches:
                is_home = True

        if is_home:
            data.home_energy_charged_kwh += energy_kwh

        session = ChargingSession(
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            energy_kwh=energy_kwh,
            avg_power_kw=avg_power,
            max_power_kw=round(max_power, 2),
            is_home_charge=is_home,
        )
        data.charging_sessions.append(session)
        data.last_charge_kwh = energy_kwh
        data.last_charge_timestamp = end_ts

    def _parse_operation(self, file_path: str, data: XpengParsedData) -> None:
        """Parse driving_operation CSV file (odometer, speed, discrete driving trips)."""
        _LOGGER.debug("Parsing operation file: %s", file_path)
        current_start: int | None = None
        trip_secs = 0
        trip_rolling_secs = 0
        last_ts = 0

        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts_str = row.get("timer")
                ts = 0
                if ts_str:
                    try:
                        ts = int(ts_str)
                        if data.last_timestamp is None or ts > data.last_timestamp:
                            data.last_timestamp = ts
                    except ValueError:
                        ts = 0

                # Speed
                spd_str = row.get("esp_vehspd")
                spd = 0.0
                if spd_str:
                    try:
                        spd = float(spd_str)
                    except ValueError:
                        spd = 0.0

                # Ignore invalid CAN-SNA sentinel (255.0 / 0xFF)
                if spd >= 250.0:
                    spd = 0.0

                # Gear: 1.0=D (Drive), 2.0=N (Neutral), 3.0=R (Reverse), 4.0=P (Park)
                gear = row.get("ldcu_currentgearlev")
                if gear:
                    in_gear = gear in ("1.0", "2.0", "3.0")
                else:
                    in_gear = spd > 0.5

                if in_gear and ts > 0:
                    if current_start is None:
                        current_start = ts
                        trip_secs = 0
                        trip_rolling_secs = 0
                    elif last_ts and (ts - last_ts) > 120:
                        # Time gap > 2 min: finalize trip
                        if trip_secs >= 10:
                            data.driving_trips.append(
                                DrivingTrip(
                                    start_timestamp=current_start,
                                    end_timestamp=last_ts,
                                    duration_seconds=trip_secs,
                                    rolling_seconds=trip_rolling_secs,
                                )
                            )
                        current_start = ts
                        trip_secs = 0
                        trip_rolling_secs = 0

                    trip_secs += 1
                    if spd > 0.5:
                        trip_rolling_secs += 1
                    last_ts = ts
                else:
                    # Vehicle parked or not in drive gear
                    if current_start is not None:
                        if trip_secs >= 10:
                            data.driving_trips.append(
                                DrivingTrip(
                                    start_timestamp=current_start,
                                    end_timestamp=last_ts if last_ts else ts,
                                    duration_seconds=trip_secs,
                                    rolling_seconds=trip_rolling_secs,
                                )
                            )
                        current_start = None
                        trip_secs = 0
                        trip_rolling_secs = 0

                # Monotonic odometer
                odo_str = row.get("cdcu_totalodometer")
                if odo_str:
                    try:
                        odo = float(odo_str)
                        if data.odometer is None or odo > data.odometer:
                            data.odometer = odo
                    except ValueError:
                        pass

            # Finalize open trip at EOF
            if current_start is not None and trip_secs >= 10:
                data.driving_trips.append(
                    DrivingTrip(
                        start_timestamp=current_start,
                        end_timestamp=last_ts if last_ts else current_start + trip_secs,
                        duration_seconds=trip_secs,
                        rolling_seconds=trip_rolling_secs,
                    )
                )

    def _parse_status(self, file_path: str, data: XpengParsedData) -> None:
        """Parse driving_status CSV file (tire pressures, doors)."""
        _LOGGER.debug("Parsing status file: %s", file_path)
        latest_status_ts = 0
        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts_str = row.get("timer")
                if ts_str:
                    try:
                        ts = int(ts_str)
                        if data.last_timestamp is None or ts > data.last_timestamp:
                            data.last_timestamp = ts
                    except ValueError:
                        ts = 0
                else:
                    ts = 0

                if ts >= latest_status_ts:
                    latest_status_ts = ts
                    # Tire pressures (kPa -> bar)
                    for key, attr in (
                        ("ldcu_tpmsprfl", "tire_pressure_fl"),
                        ("ldcu_tpmsprfr", "tire_pressure_fr"),
                        ("ldcu_tpmsprrl", "tire_pressure_rl"),
                        ("ldcu_tpmsprrr", "tire_pressure_rr"),
                    ):
                        val_str = row.get(key)
                        if val_str:
                            try:
                                # 1 kPa = 0.01 bar
                                setattr(data, attr, round(float(val_str) / 100.0, 2))
                            except ValueError:
                                pass

                    # Doors
                    for key, attr in (
                        ("ldcu_driverdoorajarst", "door_driver_open"),
                        ("rdcu_psngrdoorajarst", "door_passenger_open"),
                        ("ldcu_rldoorajarst", "door_rear_left_open"),
                        ("rdcu_rrdoorajarst", "door_rear_right_open"),
                    ):
                        val_str = row.get(key)
                        if val_str:
                            try:
                                setattr(data, attr, float(val_str) > 0)
                            except ValueError:
                                pass

                    # Trunk
                    tr_str = row.get("rdm_tropenersts")
                    if tr_str:
                        try:
                            data.trunk_open = float(tr_str) > 0
                        except ValueError:
                            pass

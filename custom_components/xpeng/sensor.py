"""Sensor platform for XPENG Vehicles."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XpengDataUpdateCoordinator
from .parser import XpengParsedData


@dataclass(frozen=True, kw_only=True)
class XpengSensorDescription(SensorEntityDescription):
    """Describes XPENG sensor entity."""

    value_fn: Callable[[XpengParsedData], Any]


SENSOR_DESCRIPTIONS: tuple[XpengSensorDescription, ...] = (
    # Energy Dashboard Sensors
    XpengSensorDescription(
        key="energy_charged",
        translation_key="energy_charged",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda d: d.total_energy_charged_kwh,
    ),
    XpengSensorDescription(
        key="home_energy_charged",
        translation_key="home_energy_charged",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda d: d.home_energy_charged_kwh,
    ),
    XpengSensorDescription(
        key="last_charge_energy",
        translation_key="last_charge_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda d: d.last_charge_kwh,
    ),
    # Battery & Range
    XpengSensorDescription(
        key="battery_level",
        translation_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.battery_level,
    ),
    XpengSensorDescription(
        key="range",
        translation_key="range",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=lambda d: d.range_km,
    ),
    XpengSensorDescription(
        key="odometer",
        translation_key="odometer",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        value_fn=lambda d: d.odometer,
    ),
    # Temperatures & Voltage
    XpengSensorDescription(
        key="battery_temp_max",
        translation_key="battery_temp_max",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.battery_temp_max,
    ),
    XpengSensorDescription(
        key="battery_temp_min",
        translation_key="battery_temp_min",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.battery_temp_min,
    ),
    XpengSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: d.battery_voltage,
    ),
    # Tire Pressures (bar)
    XpengSensorDescription(
        key="tire_pressure_front_left",
        translation_key="tire_pressure_front_left",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        value_fn=lambda d: d.tire_pressure_fl,
    ),
    XpengSensorDescription(
        key="tire_pressure_front_right",
        translation_key="tire_pressure_front_right",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        value_fn=lambda d: d.tire_pressure_fr,
    ),
    XpengSensorDescription(
        key="tire_pressure_rear_left",
        translation_key="tire_pressure_rear_left",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        value_fn=lambda d: d.tire_pressure_rl,
    ),
    XpengSensorDescription(
        key="tire_pressure_rear_right",
        translation_key="tire_pressure_rear_right",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        value_fn=lambda d: d.tire_pressure_rr,
    ),
    # Data Freshness & Driving Time
    XpengSensorDescription(
        key="last_data_update",
        translation_key="last_data_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: datetime.fromtimestamp(d.last_timestamp, tz=timezone.utc) if d.last_timestamp else None,
    ),
    XpengSensorDescription(
        key="total_driving_time",
        translation_key="total_driving_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=2,
        value_fn=lambda d: d.total_driving_hours,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XPENG sensor entities based on a config entry."""
    coordinator: XpengDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        XpengSensorEntity(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class XpengSensorEntity(CoordinatorEntity[XpengDataUpdateCoordinator], SensorEntity):
    """Representation of an XPENG sensor."""

    entity_description: XpengSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XpengDataUpdateCoordinator,
        description: XpengSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if self.entity_description.key == "last_data_update" and self.coordinator.data:
            data = self.coordinator.data
            age_hours: float | None = None
            if data.last_timestamp:
                age_hours = round((datetime.now(timezone.utc).timestamp() - data.last_timestamp) / 3600.0, 1)
            return {
                "data_age_hours": age_hours,
                "data_source": self.coordinator.mode,
                "raw_timestamp": data.last_timestamp,
            }
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the vehicle device."""
        vin = self.coordinator.data.vin if self.coordinator.data and self.coordinator.data.vin else None
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.vehicle_name,
            manufacturer="XPENG",
            model=self.coordinator.resolved_model,
            serial_number=vin,
        )

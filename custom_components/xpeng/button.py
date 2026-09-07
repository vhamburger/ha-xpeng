"""Button platform for XPENG Vehicles."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XpengDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up XPENG button entities."""
    coordinator: XpengDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([XpengSyncButton(coordinator)])


class XpengSyncButton(CoordinatorEntity[XpengDataUpdateCoordinator], ButtonEntity):
    """Button to manually trigger XPENG data refresh."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: XpengDataUpdateCoordinator) -> None:
        """Initialize the sync button."""
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(
            key="sync_data",
            translation_key="sync_data",
            icon="mdi:sync",
        )
        vin = coordinator.data.vin if coordinator.data and coordinator.data.vin else coordinator.entry.entry_id
        self._attr_unique_id = f"{vin}_sync_data"

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the vehicle device."""
        vin = self.coordinator.data.vin if self.coordinator.data and self.coordinator.data.vin else self.coordinator.entry.entry_id
        model = self.coordinator.data.vmodel if self.coordinator.data and self.coordinator.data.vmodel else "X9"
        return DeviceInfo(
            identifiers={(DOMAIN, vin)},
            name=self.coordinator.vehicle_name,
            manufacturer="XPENG",
            model=model,
            serial_number=vin,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()

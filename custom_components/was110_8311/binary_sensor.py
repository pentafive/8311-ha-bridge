"""Binary sensor platform for 8311 ONU Monitor."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CONSECUTIVE_ERRORS,
    ATTR_STATE_CODE,
    ATTR_STATE_NAME,
    ATTR_TIME_IN_STATE,
    ATTR_TIME_IN_STATE_FORMATTED,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import WAS110Coordinator

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="pon_link",
        name="PON Link",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:wan",
    ),
    BinarySensorEntityDescription(
        key="ssh_connected",
        name="SSH Connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:ssh",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up 8311 ONU binary sensors based on a config entry."""
    coordinator: WAS110Coordinator = entry.runtime_data

    async_add_entities(
        WAS110BinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class WAS110BinarySensor(CoordinatorEntity[WAS110Coordinator], BinarySensorEntity):
    """Representation of an 8311 ONU binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WAS110Coordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.host}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_info = self.coordinator.device_info
        serial = device_info.get("serial_number", self.coordinator.host)

        return DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"8311 ONU ({serial})",
            manufacturer=device_info.get("vendor", MANUFACTURER),
            model=device_info.get("part_number", MODEL),
            sw_version=device_info.get("firmware_bank"),
            hw_version=device_info.get("hardware_revision"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {}

        attrs: dict[str, str | int | None] = {}

        if self.entity_description.key == "pon_link":
            attrs[ATTR_STATE_CODE] = self.coordinator.data.get("pon_state_code")
            attrs[ATTR_STATE_NAME] = self.coordinator.data.get("pon_state_name")
            time_in_state = self.coordinator.data.get("pon_time_in_state")
            if time_in_state is not None:
                attrs[ATTR_TIME_IN_STATE] = time_in_state
                attrs[ATTR_TIME_IN_STATE_FORMATTED] = self._format_duration(
                    time_in_state
                )

        if self.entity_description.key == "ssh_connected":
            attrs[ATTR_CONSECUTIVE_ERRORS] = self.coordinator.data.get(
                "consecutive_errors", 0
            )

        return attrs

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration in human-readable format."""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, secs = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if secs or not parts:
            parts.append(f"{secs}s")

        return " ".join(parts)

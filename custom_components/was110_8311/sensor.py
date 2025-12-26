"""Sensor platform for 8311 ONU Monitor."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfInformation,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import WAS110Coordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="rx_power_dbm",
        name="RX Power",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-down-bold-hexagon-outline",
    ),
    SensorEntityDescription(
        key="rx_power_mw",
        name="RX Power (mW)",
        native_unit_of_measurement=UnitOfPower.MILLIWATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-down-bold-hexagon-outline",
    ),
    SensorEntityDescription(
        key="tx_power_dbm",
        name="TX Power",
        native_unit_of_measurement="dBm",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-bold-hexagon-outline",
    ),
    SensorEntityDescription(
        key="tx_power_mw",
        name="TX Power (mW)",
        native_unit_of_measurement=UnitOfPower.MILLIWATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-up-bold-hexagon-outline",
    ),
    SensorEntityDescription(
        key="optic_temperature",
        name="Optic Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="voltage",
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    SensorEntityDescription(
        key="tx_bias_current",
        name="TX Bias Current",
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
    ),
    SensorEntityDescription(
        key="cpu0_temperature",
        name="CPU0 Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="cpu1_temperature",
        name="CPU1 Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="ethernet_speed",
        name="Ethernet Speed",
        native_unit_of_measurement="Mbps",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:ethernet",
    ),
    SensorEntityDescription(
        key="vendor",
        name="Vendor",
        icon="mdi:factory",
        entity_category=None,
    ),
    SensorEntityDescription(
        key="part_number",
        name="Part Number",
        icon="mdi:barcode",
        entity_category=None,
    ),
    SensorEntityDescription(
        key="hardware_revision",
        name="Hardware Revision",
        icon="mdi:chip",
        entity_category=None,
    ),
    SensorEntityDescription(
        key="pon_mode",
        name="PON Mode",
        icon="mdi:wan",
        entity_category=None,
    ),
    SensorEntityDescription(
        key="firmware_bank",
        name="Active Firmware Bank",
        icon="mdi:memory",
        entity_category=None,
    ),
    # New sensors - ISP and system info
    SensorEntityDescription(
        key="isp",
        name="ISP",
        icon="mdi:web",
        entity_category=None,
    ),
    SensorEntityDescription(
        key="gpon_serial",
        name="GPON Serial",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,  # Sensitive - disabled by default
    ),
    SensorEntityDescription(
        key="module_type",
        name="Module Type",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="pon_vendor_id",
        name="PON Vendor ID",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="onu_uptime",
        name="ONU Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="memory_percent",
        name="Memory Usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="memory_used",
        name="Memory Used",
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:memory",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # PON state details
    SensorEntityDescription(
        key="pon_state_name",
        name="PON State",
        icon="mdi:state-machine",
        entity_category=None,
    ),
    SensorEntityDescription(
        key="pon_previous_state",
        name="PON Previous State",
        icon="mdi:history",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="pon_time_in_state",
        name="PON Time in State",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # GTC error counters (diagnostic)
    SensorEntityDescription(
        key="gtc_bip_errors",
        name="GTC BIP Errors",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gtc_fec_corrected",
        name="GTC FEC Corrected",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:check-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gtc_fec_uncorrected",
        name="GTC FEC Uncorrected",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:close-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="gtc_lods_events",
        name="GTC LODS Events",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:signal-off",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up 8311 ONU sensors based on a config entry."""
    coordinator: WAS110Coordinator = entry.runtime_data

    async_add_entities(
        WAS110Sensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class WAS110Sensor(CoordinatorEntity[WAS110Coordinator], SensorEntity):
    """Representation of an 8311 ONU sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WAS110Coordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)

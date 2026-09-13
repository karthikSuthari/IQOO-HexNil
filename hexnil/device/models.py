"""Data models for Hexnil device foundation and experiment records."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceState(str, Enum):
    """Possible ADB device states."""

    DEVICE = "device"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    AUTHORIZING = "authorizing"
    RECOVERY = "recovery"
    BOOTLOADER = "bootloader"
    SIDELOAD = "sideload"
    UNKNOWN = "unknown"

    @classmethod
    def from_str(cls, val: str) -> "DeviceState":
        cleaned = val.strip().lower()
        for member in cls:
            if member.value == cleaned:
                return member
        return cls.UNKNOWN


class DiscoveredDevice(BaseModel):
    """Represents an Android device identified via 'adb devices'."""

    serial: str
    state: DeviceState
    product: Optional[str] = None
    model: Optional[str] = None
    device: Optional[str] = None
    transport_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @property
    def is_usable(self) -> bool:
        """Indicates whether this device is authorized and online."""
        return self.state == DeviceState.DEVICE


class DeviceMetadata(BaseModel):
    """Hardware and OS metadata collected from an Android device."""

    serial: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    codename: Optional[str] = None
    android_version: Optional[str] = None
    sdk: Optional[int] = None
    build_id: Optional[str] = None
    build_fingerprint: Optional[str] = None
    abi: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class AdbStatus(BaseModel):
    """ADB connection status for the target device."""

    state: str = "device"
    connected: bool = True

    model_config = ConfigDict(extra="ignore")


class ExperimentRecord(BaseModel):
    """Complete Phase 1 persisted experiment record."""

    experiment_id: str
    created_at: str
    device: DeviceMetadata
    adb: AdbStatus
    phase: str = "01_android_device_foundation"
    status: str = "ready"
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

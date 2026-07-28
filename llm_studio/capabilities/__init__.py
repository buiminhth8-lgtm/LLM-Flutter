"""Feature capability status registry."""

from .registry import CapabilityInfo, get_capabilities
from .status import CapabilityStatus

__all__ = ["CapabilityInfo", "CapabilityStatus", "get_capabilities"]

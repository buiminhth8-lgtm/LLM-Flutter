"""Feature capability status registry."""

from .registry import CapabilityInfo, get_capabilities, get_capabilities_for_config
from .status import CapabilityStatus

__all__ = ["CapabilityInfo", "CapabilityStatus", "get_capabilities", "get_capabilities_for_config"]

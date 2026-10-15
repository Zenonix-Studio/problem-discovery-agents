"""Problem Discovery Agents research-pilot foundation."""

from .contracts import EvidenceItem, EvidenceRegistry
from .validation import ContractValidationError, stage1_result, validate_handoffs

__version__ = "0.1.0"

__all__ = [
    "ContractValidationError",
    "EvidenceItem",
    "EvidenceRegistry",
    "stage1_result",
    "validate_handoffs",
]

"""Mechanical program-snapshot Worlds: construction, receipt schema, comparison.

Extraction and spine construction live in :mod:`.typescript`;
cross-snapshot comparison, delta, and correspondence in :mod:`.comparison`.
Neither assigns semantic standing nor makes workflow decisions; both serve
application maintenance and case assembly.
"""

from .schemas import (
    CAPABILITY_VERSIONS,
    CORE_SPEC_ID,
    CORE_SPEC_VERSION,
    RECEIPT_VERSION,
    SpineConstructionReceipt,
    SpineReceiptError,
    load_receipt,
)

from .typescript import (
    TypeScriptBoundary,
    TypeScriptSpineResult,
    build_typescript_spine,
    localize_source_range,
    validate_typescript_spine,
)
from .comparison import (
    ComparisonError,
    CorrespondenceClaim,
    CorrespondenceGroup,
    ProgramDelta,
    SpineComparisonReceipt,
    SpineComparisonResult,
    compare_program_spines,
    compare_spines,
    load_comparison,
)

__all__ = [
    "CAPABILITY_VERSIONS",
    "CORE_SPEC_ID",
    "CORE_SPEC_VERSION",
    "RECEIPT_VERSION",
    "SpineConstructionReceipt",
    "SpineReceiptError",
    "TypeScriptBoundary",
    "TypeScriptSpineResult",
    "build_typescript_spine",
    "localize_source_range",
    "validate_typescript_spine",
    "load_receipt",
    "ComparisonError",
    "CorrespondenceClaim",
    "CorrespondenceGroup",
    "ProgramDelta",
    "SpineComparisonReceipt",
    "SpineComparisonResult",
    "compare_program_spines",
    "compare_spines",
    "load_comparison",
]

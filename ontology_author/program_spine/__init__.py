"""Language-specific program-spine builders."""

from .typescript import (
    TypeScriptBoundary,
    TypeScriptSpineResult,
    build_typescript_spine,
    localize_source_range,
    validate_typescript_spine,
)

__all__ = [
    "TypeScriptBoundary",
    "TypeScriptSpineResult",
    "build_typescript_spine",
    "localize_source_range",
    "validate_typescript_spine",
]

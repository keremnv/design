"""Checkout-specific reconstructible Markdown observation.

The constructor names the supporting line range. This is a fixture adapter,
not a Markdown ontology or evidence-discovery engine.
"""

from __future__ import annotations

from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.material_support import content_digest, extract_line_range
from ontology_author.world.runtime.source_helpers import Source

AVAILABILITY_REQUIREMENT_HANDLE = "checkout-requirements.md"
AVAILABILITY_REQUIREMENT_LINES = (3, 6)


def observe_markdown_line_range(
    source: Source,
    handle: str,
    start: int,
    end: int,
) -> tuple[SourceObservation, dict[str, str]] | None:
    """Bind a claim to an exact current line range in a text source."""

    text = source.read_text(handle)
    region = extract_line_range(text, start, end)
    if region is None:
        return None
    location = f"lines:{start}-{end}"
    revision = source.file_hash(handle)
    observation = SourceObservation(
        provider="file",
        native_handle=handle,
        source_revision=revision,
        native_location=location,
    )
    support = {
        "kind": "MARKDOWN_LINE_RANGE",
        "native_handle": handle,
        "native_location": location,
        "source_revision": revision,
        "content_digest": content_digest(region),
        "role": "requirement_basis",
    }
    return observation, support


def observe_availability_requirement(
    source: Source,
) -> tuple[SourceObservation, dict[str, str]] | None:
    """The constructor-declared availability requirement region for this fixture."""

    start, end = AVAILABILITY_REQUIREMENT_LINES
    return observe_markdown_line_range(
        source, AVAILABILITY_REQUIREMENT_HANDLE, start, end
    )

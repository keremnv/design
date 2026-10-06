"""Phase 1 provenance conformance for retained assertion evidence."""

from __future__ import annotations

from pathlib import Path

from ontology_author.software_governance.validation import (
    CONTRACT_ID,
    validate_governance_world,
)
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from tests.test_software_governance_construction import (
    _assert_completeness,
    _assert_sample_proposition,
    _authority_observation,
    _binding_values,
    _sample_world,
)


def test_binding_rejects_unreconstructible_recorded_program_observation(
    tmp_path: Path,
) -> None:
    """A valid semantic source cannot mask a broken program-side observation."""

    world = _sample_world(tmp_path)
    try:
        semantic = _authority_observation(
            world,
            "policy.md",
            "A stated requirement.",
        )
        broken_program = SourceObservation(
            provider="program",
            native_handle="app.ts@sha256:" + "0" * 64,
            source_revision="sha256:" + "0" * 64,
            native_location="bytes:0:1",
        )
        _assert_sample_proposition(world, semantic)
        world.assert_tuple(
            "governance_binding",
            _binding_values(),
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                (semantic, broken_program),
                construction_method="phase1 broken-program-evidence probe",
                extra={
                    "contract": CONTRACT_ID,
                    "profile_id": "test",
                    "relation_support": "CROSS_EVIDENCE",
                    "endpoint_resolution": "AGENT_RESOLVED",
                    "software_evidence": "backend:123",
                },
            ),
        )
        _assert_completeness(world, semantic)

        errors = validate_governance_world(world)
    finally:
        world.close()

    assert any(
        "governance_binding proposition:sample has 1 unreconstructible recorded evidence observation(s)"
        in error
        for error in errors
    )

"""Phase 1 regression for semantic-persistence program evidence normalization."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ontology_author.evidence.program_source import (
    PROGRAM_INPUTS_DIR,
    source_evidence_record,
)
from ontology_author.semantic_binding import (
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
)
from ontology_author.semantic_binding.admission import _observations_for_candidate
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_semantic_persistence import _alias, _case, _draft, _obligation


def test_program_source_record_survives_catalog_candidate_and_grounding(
    tmp_path: Path,
) -> None:
    payload = b"export function openRetentionFlow() { return true; }\n"
    digest = hashlib.sha256(payload).hexdigest()
    native_handle = f"src/retention.ts@sha256:{digest}"

    world = ConstructionWorld.create(
        tmp_path / "world.sqlite",
        world_id="phase1-program-observation",
    )
    try:
        inputs = world.path.parent / PROGRAM_INPUTS_DIR
        inputs.mkdir(parents=True, exist_ok=True)
        (inputs / digest).write_bytes(payload)
        record = source_evidence_record(
            world=world,
            entity="program:openRetentionFlow",
            side="OLD",
            snapshot_id="snapshot:s0",
            inclusion_reason="selected bounded realization evidence",
            selected_by="phase1-conformance",
            observation={
                "provider": "typescript",
                "native_handle": native_handle,
                "source_revision": f"sha256:{digest}",
                "native_location": f"bytes:0:{len(payload)}",
            },
        )
    finally:
        world.close()

    assert record["reconstruction"] == "OK"
    assert record["native_handle"] == native_handle
    assert record["handle"] == native_handle  # compatibility alias

    obligation = _obligation()
    catalog = build_semantic_construction_catalog(
        obligation,
        _case(),
        bounded_program_source=(record,),
    )
    selected = [
        _alias(catalog, "AUTHORITATIVE_EVIDENCE"),
        _alias(catalog, "PROGRAM_SOURCE"),
        _alias(catalog, "MECHANICAL_FACT"),
    ]
    candidate = compile_semantic_candidate_draft(
        obligation,
        catalog,
        _draft(catalog, evidence=selected),
    )

    observations = _observations_for_candidate(candidate, catalog)
    handles = {item.native_handle for item in observations}
    assert "docs/subscriptions.md" in handles
    assert native_handle in handles

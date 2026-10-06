"""Phase 1 closure for governance publication program-evidence retention."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ontology_author.evidence.program_source import (
    PROGRAM_INPUTS_DIR,
    verify_retained_program_inputs,
)
from ontology_author.software_governance.construction import (
    BindingSpec,
    CompletenessSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
)
from ontology_author.software_governance.validation import BINDINGS_CAPABILITY
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld


PROGRAM_BYTES = b"export const customerExport = true;\n"
GOVERNANCE_BYTES = b"Customer export is governed.\n"
SOURCE_STATE = "snapshot-source-state:phase1-governance"


def _program_world(root: Path, *, retain_blob: bool) -> tuple[Path, SourceObservation]:
    root.mkdir(parents=True)
    digest = hashlib.sha256(PROGRAM_BYTES).hexdigest()
    observation = SourceObservation(
        provider="typescript",
        native_handle=f"src/export.ts@sha256:{digest}",
        source_revision=SOURCE_STATE,
        native_location=f"bytes:0:{len(PROGRAM_BYTES)}",
    )
    world = ConstructionWorld.create(root / "world.sqlite", world_id="phase1-governance")
    try:
        world.add_referent("snapshot:test", label="snapshot:test")
        world.add_referent(
            "subject:known",
            label="subject:known",
            observations=(observation,),
        )
        world.declare_relation(
            "program_snapshot",
            [
                Role("snapshot", RoleType.REFERENT),
                Role("source_state", RoleType.TEXT),
            ],
            description="Minimal program snapshot contract for Phase 1.",
        )
        world.assert_tuple(
            "program_snapshot",
            {"snapshot": "snapshot:test", "source_state": SOURCE_STATE},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding(
                (observation,),
                construction_method="phase1 program snapshot fixture",
            ),
        )
    finally:
        world.close()
    if retain_blob:
        directory = root / PROGRAM_INPUTS_DIR
        directory.mkdir(parents=True)
        (directory / digest).write_bytes(PROGRAM_BYTES)
    return root, observation


def _governance_observation() -> tuple[SourceObservation, dict[str, bytes]]:
    digest = hashlib.sha256(GOVERNANCE_BYTES).hexdigest()
    return (
        SourceObservation(
            provider="markdown",
            native_handle=f"policy.md@sha256:{digest}",
            source_revision=f"sha256:{digest}",
            native_location=f"bytes:0:{len(GOVERNANCE_BYTES)}",
        ),
        {digest: GOVERNANCE_BYTES},
    )


def _construct(source: Path, output: Path):
    governance, blobs = _governance_observation()
    return construct_software_governance(
        software_world=source,
        output=output,
        profile_id="phase1/test",
        evidence_blobs=blobs,
        propositions=(
            PropositionSpec(
                proposition_id="proposition:sample",
                statement="Customer export is governed.",
                domain_relation="sample_requirement",
                observations=(governance,),
            ),
        ),
        bindings=(
            BindingSpec(
                proposition_id="proposition:sample",
                software_subject="subject:known",
                support="SOURCE_EXPLICIT",
                endpoint_resolution="DETERMINISTIC",
                construction_method="phase1 governance binding fixture",
                observations=(governance,),
                software_evidence="declared subject receipt",
            ),
        ),
        subjects=(
            SoftwareSubjectSpec(
                subject_id="subject:known",
                snapshot_id="snapshot:test",
                kind="callable",
                capability="phase1.fixture",
                version="v1",
                observations=(governance,),
            ),
        ),
        completeness=CompletenessSpec(
            capability=BINDINGS_CAPABILITY,
            status="INCOMPLETE",
            universe="snapshot:test",
            basis="Phase 1 fixture covers one supplied subject.",
            known_gaps=("unsurveyed_subjects",),
        ),
    )


def test_governance_publish_rejects_broken_referent_program_evidence(
    tmp_path: Path,
) -> None:
    source, _observation = _program_world(tmp_path / "source-broken", retain_blob=False)
    output = tmp_path / "published-broken"

    result = _construct(source, output)

    assert not result.succeeded
    assert not output.exists()
    assert any(
        "program source observation cannot reconstruct retained bytes" in error
        for error in result.errors
    )


def test_governance_publish_accepts_closed_program_evidence(
    tmp_path: Path,
) -> None:
    source, _observation = _program_world(tmp_path / "source-ok", retain_blob=True)
    output = tmp_path / "published-ok"

    result = _construct(source, output)

    assert result.succeeded, result.errors
    world = ConstructionWorld.open(output / "world.sqlite", read_only=True)
    try:
        assert verify_retained_program_inputs(world) == []
    finally:
        world.close()

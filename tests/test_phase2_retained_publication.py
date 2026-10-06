"""Phase 2 conformance: accepted history grows by retained publication.

Each test establishes one write-semantics invariant. Publication order
carries no semantic currentness: nothing here supersedes, withdraws, or
corrects a prior publication.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import stat
from pathlib import Path

import pytest

from ontology_author.evidence.program_source import PROGRAM_INPUTS_DIR
from ontology_author.software_governance import (
    BindingSpec,
    CompletenessSpec,
    PropositionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
)
from ontology_author.software_governance.judgment import assemble_case, verify_case
from ontology_author.software_governance.reads import open_governance_world
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime import commit as commit_module
from ontology_author.world.runtime.commit import publish_candidate, write_sidecars
from ontology_author.world.runtime.publication import PublicationRef, verify_publication_ref
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld

_MEANING_TOKENS = (
    "supersed",
    "withdraw",
    "retract",
    "obsolet",
    "current",
    "latest",
    "active_publication",
    "operative",
)


def _hash_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            out[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _grounding(method: str = "phase2 fixture") -> AssertionGrounding:
    return AssertionGrounding(
        (
            SourceObservation(
                provider="test",
                native_handle="fixture/note.md",
                source_revision="fixture-revision:1",
                native_location="bytes:0:4",
            ),
        ),
        construction_method=method,
    )


def _declare_note(world: ConstructionWorld) -> None:
    world.declare_relation(
        "note",
        [Role("note", RoleType.REFERENT), Role("text", RoleType.TEXT)],
        description="Phase 2 publication fixture.",
    )


def _assert_note(world: ConstructionWorld, note: str, text: str) -> None:
    world.add_referent(note, label=note)
    world.assert_tuple(
        "note",
        {"note": note, "text": text},
        origin=ConstructionOrigin.MECHANICAL,
        grounding=_grounding(),
    )


def _writable_copy(source: Path, dest: Path) -> None:
    shutil.copytree(source, dest)
    for path in dest.rglob("*"):
        mode = path.stat().st_mode
        path.chmod(mode | (0o700 if path.is_dir() else 0o600))
    dest.chmod(dest.stat().st_mode | 0o700)


def _governed(root: Path, output: Path) -> Path:
    """Publish one minimal governance publication without a program spine."""
    software = root / "software"
    software.mkdir(parents=True, exist_ok=True)
    if not (software / "world.sqlite").exists():
        seed = ConstructionWorld.create(software / "world.sqlite", world_id="phase2-software")
        try:
            seed.add_referent("snapshot:test", label="snapshot:test")
            seed.add_referent("subject:known", label="subject:known")
        finally:
            seed.close()
    text = b"A stated requirement."
    digest = hashlib.sha256(text).hexdigest()
    observation = SourceObservation(
        provider="markdown",
        native_handle=f"policy.md@sha256:{digest}",
        source_revision=f"sha256:{digest}",
        native_location=f"bytes:0:{len(text)}",
    )
    result = construct_software_governance(
        software_world=software,
        output=output,
        profile_id="phase2-conformance",
        propositions=(
            PropositionSpec(
                proposition_id="proposition:sample",
                statement="A stated requirement.",
                domain_relation="sample_requirement",
                observations=(observation,),
            ),
        ),
        bindings=(
            BindingSpec(
                proposition_id="proposition:sample",
                software_subject="subject:known",
                support="CROSS_EVIDENCE",
                endpoint_resolution="AGENT_RESOLVED",
                construction_method="phase2 binding",
                observations=(observation,),
                software_evidence="declared subject",
            ),
        ),
        subjects=(
            SoftwareSubjectSpec(
                subject_id="subject:known",
                snapshot_id="snapshot:test",
                kind="coordinate",
                capability="phase2.producer",
                version="v0",
                observations=(observation,),
            ),
        ),
        completeness=CompletenessSpec(
            capability="software_governance.bindings/v0",
            status="INCOMPLETE",
            universe="snapshot:test",
            basis="phase2 basis",
            known_gaps=("unsurveyed_subjects",),
        ),
        evidence_blobs={digest: text},
    )
    assert result.succeeded, result.errors
    assert result.world_dir is not None
    return result.world_dir


def test_publish_requires_a_fresh_address(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate-w1"
    candidate.mkdir()
    world = ConstructionWorld.create(candidate / "world.sqlite", world_id="phase2-fresh")
    try:
        _declare_note(world)
        _assert_note(world, "note:first", "first")
        write_sidecars(world)
    finally:
        world.close()
    first = tmp_path / "W1"
    publish_candidate(candidate, first)
    before = _hash_tree(first)

    clash = tmp_path / "candidate-w2"
    clash.mkdir()
    other = ConstructionWorld.create(clash / "world.sqlite", world_id="phase2-fresh")
    try:
        _declare_note(other)
        _assert_note(other, "note:second", "second")
        write_sidecars(other)
    finally:
        other.close()
    with pytest.raises(ConstructionError, match="already exists"):
        publish_candidate(clash, first)
    assert _hash_tree(first) == before
    assert clash.exists()

    blocker = tmp_path / "blocker"
    blocker.write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(ConstructionError, match="already exists"):
        publish_candidate(clash, blocker)
    assert blocker.read_text(encoding="utf-8") == "do not overwrite"


def test_historical_publication_survives_new_publication(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate-w1"
    candidate.mkdir()
    world = ConstructionWorld.create(candidate / "world.sqlite", world_id="phase2-history")
    try:
        _declare_note(world)
        _assert_note(world, "note:first", "first")
        write_sidecars(world)
    finally:
        world.close()
    first = tmp_path / "W1"
    publish_candidate(candidate, first)
    before = _hash_tree(first)

    work = tmp_path / "candidate-w2"
    _writable_copy(first, work)
    grown = ConstructionWorld.open(work / "world.sqlite", read_only=False)
    try:
        _assert_note(grown, "note:second", "second")
    finally:
        grown.close()
    second = tmp_path / "W2"
    publish_candidate(work, second)

    assert _hash_tree(first) == before
    assert (second / "world.sqlite").exists()
    old = ConstructionWorld.open(first / "world.sqlite", read_only=True)
    new = ConstructionWorld.open(second / "world.sqlite", read_only=True)
    try:
        assert {row["note"] for row in old.relation_rows("note")} == {"note:first"}
        assert {row["note"] for row in new.relation_rows("note")} == {
            "note:first",
            "note:second",
        }
    finally:
        old.close()
        new.close()


def test_identical_contents_have_distinct_occurrence_identity(tmp_path: Path) -> None:
    first = _governed(tmp_path / "root-a", tmp_path / "W1")
    second = _governed(tmp_path / "root-b", tmp_path / "W2")

    view_a = open_governance_world(first)
    try:
        ref_a = PublicationRef.from_world(view_a.world)
        subjects = view_a.subjects_for_proposition("proposition:sample")
        case = assemble_case(
            view_a,
            case_id="phase2-occurrence",
            question="Does this route satisfy the stated route rule?",
            proposition_ids=("proposition:sample",),
            subject_ids=tuple(subjects),
        )
    finally:
        view_a.world.close()
    view_b = open_governance_world(second)
    try:
        ref_b = PublicationRef.from_world(view_b.world)
        assert ref_a != ref_b
        assert ref_a.world_id == ref_b.world_id
        errors = verify_case(view_b, case)
    finally:
        view_b.world.close()
    assert "world address differs from the opened publication" in errors


def test_publication_introduces_no_supersession(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate-w1"
    candidate.mkdir()
    world = ConstructionWorld.create(candidate / "world.sqlite", world_id="phase2-nosup")
    try:
        _declare_note(world)
        _assert_note(world, "note:kept", "kept")
        write_sidecars(world)
    finally:
        world.close()
    first = tmp_path / "W1"
    publish_candidate(candidate, first)

    work = tmp_path / "candidate-w2"
    _writable_copy(first, work)
    grown = ConstructionWorld.open(work / "world.sqlite", read_only=False)
    try:
        _assert_note(grown, "note:added", "added")
    finally:
        grown.close()
    second = tmp_path / "W2"
    publish_candidate(work, second)

    for bundle in (first, second):
        opened = ConstructionWorld.open(bundle / "world.sqlite", read_only=True)
        try:
            names = [
                str(row["name"])
                for row in opened.query("SELECT name FROM _world_relations ORDER BY name")
            ]
            assert names == ["note"]
            assert not any(
                token in name for name in names for token in _MEANING_TOKENS
            )
        finally:
            opened.close()


def test_omission_carries_no_negative_meaning(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate-w1"
    candidate.mkdir()
    world = ConstructionWorld.create(candidate / "world.sqlite", world_id="phase2-omission")
    try:
        _declare_note(world)
        _assert_note(world, "note:kept", "kept")
        _assert_note(world, "note:dropped", "dropped")
        write_sidecars(world)
    finally:
        world.close()
    first = tmp_path / "W1"
    publish_candidate(candidate, first)

    work = tmp_path / "candidate-w2"
    _writable_copy(first, work)
    narrowed = ConstructionWorld.open(work / "world.sqlite", read_only=False)
    try:
        assert narrowed.retract_tuple(
            "note", {"note": "note:dropped", "text": "dropped"}
        )
    finally:
        narrowed.close()
    second = tmp_path / "W2"
    publish_candidate(work, second)

    opened = ConstructionWorld.open(second / "world.sqlite", read_only=True)
    try:
        names = [
            str(row["name"])
            for row in opened.query("SELECT name FROM _world_relations ORDER BY name")
        ]
        assert names == ["note"]
        rows = opened.relation_rows("note")
        assert {row["note"] for row in rows} == {"note:kept"}
        blob = "\n".join(
            f"{name}={value}" for row in rows for name, value in sorted(row.items())
        )
        assert not any(token in blob for token in _MEANING_TOKENS)
    finally:
        opened.close()
    old = ConstructionWorld.open(first / "world.sqlite", read_only=True)
    try:
        assert {row["note"] for row in old.relation_rows("note")} == {
            "note:kept",
            "note:dropped",
        }
    finally:
        old.close()


def test_independent_historical_reads(tmp_path: Path) -> None:
    first = _governed(tmp_path / "root-a", tmp_path / "W1")
    second = _governed(tmp_path / "root-b", tmp_path / "W2")
    view_a = open_governance_world(first)
    view_b = open_governance_world(second)
    try:
        assert verify_publication_ref(
            view_a.world, PublicationRef.from_world(view_a.world)
        ) == []
        assert (
            view_a.inspect_governance_proposition("proposition:sample")["statement"]
            == view_b.inspect_governance_proposition("proposition:sample")["statement"]
            == "A stated requirement."
        )
        assert PublicationRef.from_world(view_a.world) != PublicationRef.from_world(
            view_b.world
        )
    finally:
        view_a.world.close()
        view_b.world.close()


def test_failed_second_publication_leaves_first_untouched(tmp_path: Path) -> None:
    payload = b"export const retained = true;\n"
    digest = hashlib.sha256(payload).hexdigest()
    source_state = "snapshot-source-state:phase2-first"
    good = SourceObservation(
        provider="typescript",
        native_handle=f"src/kept.ts@sha256:{digest}",
        source_revision=source_state,
        native_location=f"bytes:0:{len(payload)}",
    )
    candidate = tmp_path / "candidate-w1"
    candidate.mkdir()
    world = ConstructionWorld.create(candidate / "world.sqlite", world_id="phase2-failure")
    try:
        world.add_referent("program:kept", label="program:kept", observations=(good,))
        world.add_referent("snapshot:first", label="snapshot:first")
        world.declare_relation(
            "program_snapshot",
            [Role("snapshot", RoleType.REFERENT), Role("source_state", RoleType.TEXT)],
            description="Snapshot revision contract.",
        )
        world.assert_tuple(
            "program_snapshot",
            {"snapshot": "snapshot:first", "source_state": source_state},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding((good,), construction_method="phase2 fixture"),
        )
    finally:
        world.close()
    inputs = candidate / PROGRAM_INPUTS_DIR
    inputs.mkdir(parents=True)
    (inputs / digest).write_bytes(payload)
    first = tmp_path / "W1"
    publish_candidate(candidate, first)
    before = _hash_tree(first)

    broken = SourceObservation(
        provider="typescript",
        native_handle="src/missing.ts@sha256:" + "0" * 64,
        source_revision="snapshot-source-state:phase2-second",
        native_location="bytes:0:1",
    )
    bad = tmp_path / "candidate-w2"
    bad.mkdir()
    ruined = ConstructionWorld.create(bad / "world.sqlite", world_id="phase2-failure")
    try:
        ruined.add_referent("program:missing", label="program:missing", observations=(broken,))
        ruined.add_referent("snapshot:second", label="snapshot:second")
        ruined.declare_relation(
            "program_snapshot",
            [Role("snapshot", RoleType.REFERENT), Role("source_state", RoleType.TEXT)],
            description="Snapshot revision contract.",
        )
        ruined.assert_tuple(
            "program_snapshot",
            {"snapshot": "snapshot:second", "source_state": broken.source_revision},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding((broken,), construction_method="phase2 fixture"),
        )
    finally:
        ruined.close()
    second = tmp_path / "W2"
    with pytest.raises(ConstructionError, match="retained program evidence verification failed"):
        publish_candidate(bad, second)

    assert not second.exists()
    assert bad.exists()
    assert _hash_tree(first) == before
    opened = ConstructionWorld.open(first / "world.sqlite", read_only=True)
    try:
        assert verify_publication_ref(opened, PublicationRef.from_world(opened)) == []
    finally:
        opened.close()


def test_retained_evidence_is_independent_per_publication(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    first = _governed(workspace / "a", tmp_path / "W1")
    second = _governed(workspace / "b", tmp_path / "W2")

    shutil.rmtree(workspace)
    assert not workspace.exists()

    for bundle in (first, second):
        view = open_governance_world(bundle)
        try:
            detail = view.inspect_governance_binding("proposition:sample", "subject:known")
            assert detail["evidence"], bundle
            for item in detail["evidence"]:
                assert item["status"] == "OK", (bundle, item)
        finally:
            view.world.close()

    aside = tmp_path / "W1-aside"
    os.rename(first, aside)
    try:
        view = open_governance_world(second)
        try:
            detail = view.inspect_governance_binding("proposition:sample", "subject:known")
            assert detail["evidence"]
            assert all(item["status"] == "OK" for item in detail["evidence"])
            assert detail["evidence"][0]["text"] == "A stated requirement."
        finally:
            view.world.close()
    finally:
        os.rename(aside, first)

    first_blobs = list((first / "governance_evidence").iterdir())
    second_blobs = list((second / "governance_evidence").iterdir())
    assert len(first_blobs) == len(second_blobs) == 1
    assert first_blobs[0].read_bytes() == second_blobs[0].read_bytes()
    assert first_blobs[0].resolve().parent != second_blobs[0].resolve().parent

def test_alias_descendant_destination_is_rejected_without_cleanup(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    world = ConstructionWorld.create(candidate / "world.sqlite", world_id="phase2-alias")
    world.close()

    alias = tmp_path / "candidate-alias"
    alias.symlink_to(candidate, target_is_directory=True)

    with pytest.raises(ConstructionError, match="inside its own candidate"):
        publish_candidate(candidate, alias / "W")

    assert candidate.exists()
    assert (candidate / "world.sqlite").exists()
    assert not (candidate / "W").exists()


def test_candidate_cleanup_does_not_chmod_symlink_target(
    tmp_path: Path,
) -> None:
    source_candidate = tmp_path / "source-candidate"
    source_candidate.mkdir()
    source_world = ConstructionWorld.create(
        source_candidate / "world.sqlite", world_id="phase2-symlink-source"
    )
    source_world.close()
    first = tmp_path / "W1"
    publish_candidate(source_candidate, first)

    sealed = first / "world.sqlite"
    before_mode = stat.S_IMODE(sealed.stat().st_mode)

    candidate = tmp_path / "candidate"
    candidate.mkdir()
    world = ConstructionWorld.create(
        candidate / "world.sqlite", world_id="phase2-symlink-cleanup"
    )
    world.close()
    (candidate / "borrowed.sqlite").symlink_to(sealed)

    second = tmp_path / "W2"
    publish_candidate(candidate, second)

    assert second.exists()
    assert not candidate.exists()
    assert stat.S_IMODE(sealed.stat().st_mode) == before_mode


def test_invalid_publication_identity_fails_before_commit(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    world = ConstructionWorld.create(
        candidate / "world.sqlite", world_id="phase2-invalid-identity"
    )
    world.close()

    with sqlite3.connect(candidate / "world.sqlite") as db:
        db.execute("UPDATE _world_meta SET revision = 'not-an-integer' WHERE singleton = 1")
        db.commit()

    destination = tmp_path / "W-invalid"
    with pytest.raises(ValueError):
        publish_candidate(candidate, destination)

    assert candidate.exists()
    assert not destination.exists()


def test_no_replace_fails_closed_when_atomic_primitive_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "marker").write_text("source", encoding="utf-8")
    destination = tmp_path / "destination"

    monkeypatch.setattr(commit_module, "_rename_noreplace", lambda _source, _dest: None)

    with pytest.raises(OSError) as exc:
        commit_module._exclusive_rename(source, destination)

    assert exc.value.errno is not None
    assert source.exists()
    assert not destination.exists()


def test_governance_staging_name_cannot_delete_prior_publication(
    tmp_path: Path,
) -> None:
    historical = _governed(
        tmp_path / "historical-root",
        tmp_path / "W2.sg-work",
    )
    before = _hash_tree(historical)

    current = _governed(
        tmp_path / "current-root",
        tmp_path / "W2",
    )

    assert current.exists()
    assert historical.exists()
    assert _hash_tree(historical) == before


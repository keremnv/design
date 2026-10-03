"""Test-local probe: producer comparison evidence is not governance renewal."""

from __future__ import annotations

import ast
import hashlib
import shutil
from pathlib import Path

import pytest

from ontology_author.evidence.program_source import (
    program_source_observations, reconstruct_program_observation,
)
from ontology_author.program_spine import CorrespondenceGroup, compare_program_spines
from ontology_author.software_governance import open_governance_world
from tests.test_program_spine_comparison import _entity, _pair, _close
from tests.software_governance_judgment_fixtures import build_worlds


ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not (ROOT / "frontend/node_modules/typescript").exists(),
    reason="the accepted TypeScript producer needs node and TypeScript",
)


def _claim(old_world, new_world, old_label: str, kind: str = "callable"):
    old_id = _entity(old_world, old_label, kind)
    comparison = compare_program_spines(old_world, new_world)
    claims = [item for item in comparison.correspondences if item.old_entity == old_id]
    return comparison, old_id, claims


def _call_sites_with_text(world, text: str) -> list[str]:
    found = []
    for row in world.relation_rows("program_entity_kind"):
        if row["kind"] != "call_site":
            continue
        entity = str(row["entity"])
        observations = program_source_observations(world, entity)
        if any(reconstruct_program_observation(world, observation) == (text, "OK")
               for observation in observations):
            found.append(entity)
    return found


@pytest.mark.parametrize("shape,old_files,new_files,old_label,new_label,outcome", [
    ("surrounding_edit",
     {"src/a.ts": "export function keep(): number { return 1; }\nexport const neighbor = 1;\n"},
     {"src/a.ts": "// preceding note\nexport function keep(): number { return 1; }\nexport const neighbor = 2;\n"},
     "keep", "keep", "UNCHANGED_OR_CONTINUED"),
    ("local_edit",
     {"src/a.ts": "export function keep(): number { return 1; }\n"},
     {"src/a.ts": "export function keep(): number { return 2; }\n"},
     "keep", "keep", "UNCHANGED_OR_CONTINUED"),
    ("move",
     {"src/a.ts": "export function keep(): number { return 1; }\n"},
     {"src/b.ts": "export function keep(): number { return 1; }\n"},
     "keep", "keep", "MOVE"),
    ("rename",
     {"src/a.ts": "export function before(value: string): string { return value; }\n"},
     {"src/a.ts": "export function after(value: string): string { return value; }\n"},
     "before", "after", "RENAME"),
])
def test_spine_change_shapes_are_qualified_heuristic_evidence(
    tmp_path, shape, old_files, new_files, old_label, new_label, outcome
):
    _, _, _, old_world, new_world = _pair(tmp_path, old_files, new_files)
    try:
        result, old_id, claims = _claim(old_world, new_world, old_label)
        assert len(claims) == 1, shape
        claim = claims[0]
        assert claim.continuity == "CONTINUED"
        assert claim.new_entity == _entity(new_world, new_label, "callable")
        assert claim.outcome == outcome
        assert claim.basis_class == "HEURISTIC"
        assert old_id != claim.new_entity
        assert result.receipt.comparison_mechanism["version"] == "v0"
        assert result.receipt.validate() == []
        if shape == "move":
            assert claim.changes["source_location"] == "CHANGED"
        if shape == "local_edit":
            assert claim.changes["source_manifestation"] == "CHANGED"
        if shape == "surrounding_edit":
            # The spine's file-level manifestation flag is coarse; local
            # declaration bytes are identical despite an unrelated edit.
            assert "function keep(): number { return 1; }" in old_files["src/a.ts"]
            assert "function keep(): number { return 1; }" in new_files["src/a.ts"]
            assert claim.changes["source_manifestation"] == "CHANGED"
    finally:
        _close(old_world, new_world)


def test_delete_replacement_can_look_like_continuation_but_is_not_proof(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function old(value: string): string { return value; }\n"},
        {"src/a.ts": "export function replacement(value: string): string { return value; }\n"},
    )
    try:
        _, old_id, claims = _claim(old_world, new_world, "old")
        assert len(claims) == 1
        claim = claims[0]
        assert claim.old_entity == old_id
        new_id = _entity(new_world, "replacement", "callable")
        assert claim.new_entity == new_id
        old_location = program_source_observations(old_world, old_id)[0]["native_location"]
        new_location = program_source_observations(new_world, new_id)[0]["native_location"]
        assert old_location.split(":")[1] == new_location.split(":")[1]
        assert claim.continuity == "CONTINUED"  # existing matcher vocabulary
        assert claim.basis_class == "HEURISTIC"
        assert any("not mechanically entailed" in item for item in claim.limitations)
        # The fixture intentionally represents deletion plus an unrelated
        # replacement. A downstream reader must not upgrade this to identity.
        assert claim.basis_class != "DETERMINISTIC"
    finally:
        _close(old_world, new_world)


def test_duplicate_candidates_remain_ambiguous_and_do_not_choose_a_winner(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function source(value: string): string { return value; }\n"},
        {"src/a.ts": "export function first(value: string): string { return value; }\n"
                     "export function second(value: string): string { return value; }\n"},
    )
    try:
        result, old_id, claims = _claim(old_world, new_world, "source")
        assert len(claims) == 1
        assert claims[0].continuity == "AMBIGUOUS"
        assert set(claims[0].candidate_entities) == {
            _entity(new_world, "first", "callable"),
            _entity(new_world, "second", "callable"),
        }
        assert not any(item.continuity == "CONTINUED" for item in result.correspondences
                       if item.old_entity == old_id)
    finally:
        _close(old_world, new_world)


def test_identical_local_manifestations_are_distinct_occurrences(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "function fire(): void {}\nexport function run(): void { fire(); }\n"},
        {"src/a.ts": "function fire(): void {}\nexport function run(): void { fire(); fire(); }\n"},
    )
    try:
        old = _call_sites_with_text(old_world, "fire()")
        current = _call_sites_with_text(new_world, "fire()")
        assert len(old) == 1 and len(current) == 2
        assert len(set(current)) == 2
        comparison = compare_program_spines(old_world, new_world)
        claims = [item for item in comparison.correspondences if item.old_entity == old[0]]
        assert all(item.basis_class != "DETERMINISTIC" for item in claims)
        # Byte equality alone cannot identify which identical occurrence
        # continued. The producer may use order, but that remains heuristic.
    finally:
        _close(old_world, new_world)


def test_insert_before_exposes_source_order_false_continuity(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "function charge(): void {}\nfunction audit(): void {}\n"
                     "export function run(): void { charge(); }\n"},
        {"src/a.ts": "function charge(): void {}\nfunction audit(): void {}\n"
                     "export function run(): void { audit(); charge(); }\n"},
    )
    try:
        old = _call_sites_with_text(old_world, "charge()")
        new_charge = _call_sites_with_text(new_world, "charge()")
        new_audit = _call_sites_with_text(new_world, "audit()")
        assert len(old) == len(new_charge) == len(new_audit) == 1
        result = compare_program_spines(old_world, new_world)
        claim = next(item for item in result.correspondences if item.old_entity == old[0])
        assert claim.new_entity == new_audit[0]
        assert claim.new_entity != new_charge[0]
        assert claim.basis_class == "HEURISTIC"
        # A one-winner comparison outcome is still not safe continuity here.
    finally:
        _close(old_world, new_world)


def test_unmatched_membership_is_not_proof_of_no_correspondence(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function old(value: string): string { return value; }\n"},
        {"src/a.ts": "export function replacement(value: number): number { return value; }\n"},
    )
    try:
        result, old_id, claims = _claim(old_world, new_world, "old")
        # A complete entity inventory licenses removed/added *matcher*
        # membership. Its heuristic rules are not complete continuity proof.
        assert claims == []
        assert old_id in result.delta.identity["removed"]
        assert result.delta.identity["universe_basis"] == "complete comparable program universe"
    finally:
        _close(old_world, new_world)
    # The existing comparison test covers PARTIAL spine.code_structure ->
    # UNRESOLVED. This probe preserves that distinction without corrupting
    # sealed publications to manufacture a partial fixture here.


def test_split_merge_requires_supplied_group_evidence(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function process(): void {}\n"},
        {"src/a.ts": "export function validate(): void {}\n"
                     "export function authorize(): void {}\n"},
    )
    try:
        old_id = _entity(old_world, "process", "callable")
        new_ids = (_entity(new_world, "validate", "callable"),
                   _entity(new_world, "authorize", "callable"))
        automatic = compare_program_spines(old_world, new_world)
        assert automatic.delta.identity["split"] == []
        group = CorrespondenceGroup(
            event="SPLIT", old_entities=(old_id,), new_entities=new_ids,
            basis_class="OBSERVATIONAL",
            evidence=({"kind": "OBSERVATIONAL", "rule": "explicit fixture-supplied grouping"},),
        )
        supplied = compare_program_spines(old_world, new_world, groups=(group,))
        assert supplied.delta.identity["split"]
        assert supplied.groups[0].basis_class == "OBSERVATIONAL"
        reverse = CorrespondenceGroup(
            event="MERGE", old_entities=new_ids, new_entities=(old_id,),
            basis_class="OBSERVATIONAL",
            evidence=({"kind": "OBSERVATIONAL", "rule": "explicit fixture-supplied grouping"},),
        )
        merged = compare_program_spines(new_world, old_world, groups=(reverse,))
        assert merged.delta.identity["merged"]
        assert not any(item.basis_class == "DETERMINISTIC" for item in supplied.correspondences)
    finally:
        _close(old_world, new_world)


def test_comparison_sidecar_needs_exact_publication_envelope(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function keep(): number { return 1; }\n"},
        {"src/a.ts": "export function keep(): number { return 2; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        envelope = {"prior_publication": str(old_world.path.parent),
                    "current_publication": str(new_world.path.parent),
                    "comparison": result.to_dict()}
        assert envelope["prior_publication"] != envelope["current_publication"]
        assert result.receipt.snapshots["old"]["id"] != result.receipt.snapshots["new"]["id"]

        def verify_addresses(prior: Path, current: Path) -> None:
            if (str(prior) != envelope["prior_publication"] or
                    str(current) != envelope["current_publication"]):
                raise ValueError("comparison publication address mismatch")

        verify_addresses(old_world.path.parent, new_world.path.parent)
        with pytest.raises(ValueError, match="address mismatch"):
            verify_addresses(new_world.path.parent, old_world.path.parent)
        # The spine receipt identifies snapshot IDs. Exact publication
        # addresses must be retained by the Design-side consumer envelope.
    finally:
        _close(old_world, new_world)


def test_config_record_id_and_world_id_do_not_establish_correspondence(tmp_path):
    worlds = build_worlds(tmp_path)
    before = open_governance_world(worlds["config"])
    after = open_governance_world(worlds["config_conflict"])
    try:
        old = next(row for row in before.world.relation_rows("config_route")
                   if row["record_id"] == "customer-export")
        new = next(row for row in after.world.relation_rows("config_route")
                   if row["record_id"] == "customer-export")
        assert before.world.world_id == after.world.world_id
        assert before.world.path.parent != after.world.path.parent
        assert old["record_id"] == new["record_id"]
        assert old["subject"] != new["subject"]
        assert old["path"] != new["path"]
        old_manifestation = before.local_manifestation_for_subject(str(old["subject"]))
        new_manifestation = after.local_manifestation_for_subject(str(new["subject"]))
        assert old_manifestation["scheme"] == "canonical-json-record"
        assert new_manifestation["status"] == "NOT_PRODUCED"
        # The conflict fixture has no published local manifestation. The
        # changed config_route path is visible, but a digest comparison is not.
        # config.routes/v1 observes record IDs; it declares no cross-snapshot
        # stable-key or comparison rule. The honest comparison is unresolved.
        assert not hasattr(before, "compare_route_subjects")
        assert before.propositions_for_subject(str(old["subject"]))
        assert after.propositions_for_subject(str(new["subject"]))
        assert before.propositions_for_subject(str(new["subject"])) == []
        assert after.propositions_for_subject(str(old["subject"])) == []
    finally:
        before.world.close()
        after.world.close()


def test_qualified_historical_navigation_does_not_publish_current_binding(tmp_path):
    worlds = build_worlds(tmp_path)
    before = open_governance_world(worlds["config"])
    after = open_governance_world(worlds["config_conflict"])
    try:
        old = next(row for row in before.world.relation_rows("config_route")
                   if row["record_id"] == "customer-export")
        new = next(row for row in after.world.relation_rows("config_route")
                   if row["record_id"] == "customer-export")
        # This explicitly supplied comparison is conditional input, not an
        # inference by the config producer and not a World assertion.
        comparison = {
            "prior_publication": str(before.world.path.parent),
            "current_publication": str(after.world.path.parent),
            "prior_subject": str(old["subject"]),
            "current_subject": str(new["subject"]),
            "basis": "SUPPLIED",
            "method": "test fixture observation/v1",
            "evidence": "fixture stipulates that the modified route is the continuation",
        }
        assert comparison["prior_publication"] != comparison["current_publication"]
        historical = before.propositions_for_subject(comparison["prior_subject"])
        current = after.propositions_for_subject(comparison["current_subject"])
        assert historical == current  # independently published in both worlds
        old_binding = before.inspect_governance_binding(historical[0], comparison["prior_subject"])
        new_binding = after.inspect_governance_binding(current[0], comparison["current_subject"])
        assert old_binding["software_subject"] != new_binding["software_subject"]
        assert old_binding["evidence"] != new_binding["evidence"] or old_binding["subject_manifestation"] != new_binding["subject_manifestation"]
        assert all(row["software_subject"] != comparison["current_subject"]
                   for row in before.world.relation_rows("governance_binding"))
        assert all(row["software_subject"] != comparison["prior_subject"]
                   for row in after.world.relation_rows("governance_binding"))
        # The output has two sections; equality of proposition IDs is not
        # evidence that the old binding was carried forward.
        display = {"comparison": comparison, "historical_governance": historical,
                   "current_governance": current}
        assert display["historical_governance"] == historical
    finally:
        before.world.close()
        after.world.close()


def test_probe_is_read_only_and_has_no_core_or_maintenance_imports(tmp_path):
    path = Path(__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
               for alias in node.names]
    imports += [node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module]
    forbidden = ("ontology_author.design_checkout", "ontology_author.governance",
                 "ontology_author.semantic_binding", "ontology_author.authority")
    assert not any(name == prefix or name.startswith(prefix + ".")
                   for name in imports for prefix in forbidden)
    worlds = build_worlds(tmp_path)
    before = worlds["config"] / "world.sqlite"
    digest = hashlib.sha256(before.read_bytes()).hexdigest()
    view = open_governance_world(worlds["config"])
    try:
        subject = next(row["subject"] for row in view.world.relation_rows("config_route")
                       if row["record_id"] == "customer-export")
        assert view.propositions_for_subject(str(subject))
    finally:
        view.world.close()
    assert hashlib.sha256(before.read_bytes()).hexdigest() == digest

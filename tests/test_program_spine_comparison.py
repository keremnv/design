from __future__ import annotations

import json
import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from ontology_author.program_spine import (
    ComparisonError,
    CorrespondenceGroup,
    SpineComparisonReceipt,
    TypeScriptBoundary,
    build_typescript_spine,
    compare_program_spines,
    load_comparison,
)
from ontology_author.world.runtime.world import ConstructionWorld


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT_MODULE = REPOSITORY_ROOT / "frontend" / "node_modules" / "typescript"
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not TYPESCRIPT_MODULE.exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def _write_files(root: Path, files: dict[str, str]) -> None:
    source_root = root / "src"
    source_root.mkdir(parents=True, exist_ok=True)
    existing = sorted(path for path in source_root.rglob("*") if path.is_file())
    for path in existing:
        path.unlink()
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")


def _project(root: Path, files: dict[str, str], output: str):
    _write_files(root, files)
    tsconfig = root / "tsconfig.json"
    if not tsconfig.exists():
        tsconfig.write_text(
            json.dumps(
                {
                    "compilerOptions": {
                        "target": "ES2020",
                        "module": "commonjs",
                        "moduleResolution": "node",
                        "strict": True,
                    },
                    "include": ["src/**/*.ts", "src/**/*.tsx"],
                }
            ),
            encoding="utf-8",
        )
    boundary = TypeScriptBoundary(
        workspace_roots=("src",),
        projects=("tsconfig.json",),
        package_roots=("src",),
    )
    result = build_typescript_spine(root, root / output, boundary=boundary)
    assert result.succeeded, result.errors
    world = ConstructionWorld.open(root / output / "world.sqlite")
    return result, world, boundary


def _pair(tmp_path: Path, old_files: dict[str, str], new_files: dict[str, str]):
    old, old_world, boundary = _project(tmp_path, old_files, "world-old")
    new, new_world, _ = _project(tmp_path, new_files, "world-new")
    return old, new, boundary, old_world, new_world


def _entities(world: ConstructionWorld, kind: str | None = None) -> list[dict]:
    rows = world.relation_rows("program_entity_kind")
    labels = {
        str(row["id"]): str(row["label"])
        for row in world.query("SELECT id, label FROM _world_referents")
    }
    return [
        {**row, "label": labels.get(str(row["entity"]), "")}
        for row in rows
        if kind is None or row["kind"] == kind
    ]


def _entity(world: ConstructionWorld, label: str, kind: str) -> str:
    matches = [row["entity"] for row in _entities(world, kind) if row["label"] == label]
    assert len(matches) == 1, (label, kind, matches)
    return str(matches[0])


def _close(*worlds: ConstructionWorld) -> None:
    for world in worlds:
        world.close()


def _unseal(path: Path) -> None:
    path.parent.chmod(path.parent.stat().st_mode | 0o700)
    path.chmod(path.stat().st_mode | 0o600)


def test_identical_snapshots_have_deterministic_empty_delta(tmp_path):
    files = {"src/index.ts": "export function stable(value: string): string { return value; }\n"}
    first, first_world, boundary = _project(tmp_path, files, "world-a")
    first_world.close()
    second, second_world, _ = _project(tmp_path, files, "world-b")
    try:
        result = compare_program_spines(tmp_path / "world-a", tmp_path / "world-b")
        repeat = compare_program_spines(tmp_path / "world-a", tmp_path / "world-b")
        assert first.snapshot_id == second.snapshot_id
        assert result.to_dict() == repeat.to_dict()
        assert result.delta.identity["added"] == []
        assert result.delta.identity["removed"] == []
        assert result.receipt.correspondence_summary["outcomes"]["unchanged_or_continued"] > 0
        assert result.receipt.correspondence_summary["basis_classes"]["heuristic"] > 0
        assert result.receipt.correspondence_summary["basis_classes"]["deterministic"] == 0
        assert result.receipt.comparison_mechanism["configuration"]["automatic_correspondence_basis"] == "HEURISTIC"
        assert result.receipt.validate() == []
        continued = [item for item in result.correspondences if item.continuity == "CONTINUED"]
        assert continued
        assert all(item.basis_class == "HEURISTIC" for item in continued)
        # Identical-input reconstruction shares snapshot identity, so manifestation
        # IDs may coincide. That is reconstruction, not cross-snapshot stability.
        assert all(item.old_entity == item.new_entity for item in continued)
    finally:
        second_world.close()


def test_body_only_change_preserves_identity_and_reports_manifestation_change(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function run(value: number): number { return value; }\n"},
        {"src/index.ts": "export function run(value: number): number { return value + 1; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        run_change = next(
            item for item in result.delta.manifestations
            if item["old_entity"] and item["new_entity"]
            and _entity(old_world, "run", "callable") == item["old_entity"]
        )
        assert run_change["outcome"] == "UNCHANGED_OR_CONTINUED"
        assert run_change["changes"]["name"] == "PRESERVED"
        assert run_change["changes"]["source_manifestation"] == "CHANGED"
        assert run_change["old_entity"] != run_change["new_entity"]
        assert result.delta.identity["removed"] == []
        assert result.delta.identity["added"] == []
    finally:
        _close(old_world, new_world)


def test_deterministic_rename_uses_context_and_signature(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {
            "src/index.ts": (
                "function submitOrder(value: string): string { return value; }\n"
                "export function run(): string { return submitOrder('x'); }\n"
            )
        },
        {
            "src/index.ts": (
                "function placeOrder(value: string): string { return value; }\n"
                "export function run(): string { return placeOrder('x'); }\n"
            )
        },
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "submitOrder", "callable")
        claim = next(item for item in result.correspondences if item.old_entity == old_id)
        assert claim.outcome == "RENAME"
        assert claim.continuity == "CONTINUED"
        assert claim.basis_class == "HEURISTIC"
        assert all(item["kind"] == "HEURISTIC" for item in claim.evidence)
        assert any(item["rule"] == "preserved structural context" for item in claim.evidence)
        assert "DETERMINISTIC" not in {item["kind"] for item in claim.evidence}
        assert claim.old_entity != claim.new_entity
        assert result.delta.relations["program_invokes"]["preserved"]
        hook = next(item for item in result.delta.maintenance if item["old_entity"] == old_id)
        assert hook["manifestation_continued"] is True
        assert hook["name_changed"] is True
        assert hook["structural_context_changed"] is False
        assert compare_program_spines(old_world, new_world).to_dict() == result.to_dict()
    finally:
        _close(old_world, new_world)


def test_deterministic_move(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function submitOrder(value: string): string { return value; }\n"},
        {"src/b.ts": "export function submitOrder(value: string): string { return value; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "submitOrder", "callable")
        claim = next(item for item in result.correspondences if item.old_entity == old_id)
        assert claim.outcome == "MOVE"
        assert claim.changes["name"] == "PRESERVED"
        assert claim.changes["source_location"] == "CHANGED"
        assert claim.changes["structural_context"] == "PRESERVED"
    finally:
        _close(old_world, new_world)


def test_deterministic_rename_and_move(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/a.ts": "export function submitOrder(value: string): string { return value; }\n"},
        {"src/b.ts": "export function placeOrder(value: string): string { return value; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "submitOrder", "callable")
        claim = next(item for item in result.correspondences if item.old_entity == old_id)
        assert claim.outcome == "RENAME_AND_MOVE"
        assert claim.changes["source_location"] == "CHANGED"
        assert claim.changes["structural_context"] == "PRESERVED"
    finally:
        _close(old_world, new_world)


def test_call_site_target_retargeting_is_relation_delta(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {
            "src/index.ts": (
                "function submitOrder(): void {}\n"
                "function saveDraft(): void {}\n"
                "export function run(): void { submitOrder(); }\n"
            )
        },
        {
            "src/index.ts": (
                "function submitOrder(): void {}\n"
                "function saveDraft(): void {}\n"
                "export function run(): void { saveDraft(); }\n"
            )
        },
    )
    try:
        result = compare_program_spines(old_world, new_world)
        retargets = result.delta.relations["program_invokes"]["retargeted"]
        assert len(retargets) == 1
        assert retargets[0]["changed_endpoint"] == "target"
        assert retargets[0]["old"]["target"] != retargets[0]["new"]["target"]
        call_site = next(item for item in result.correspondences if item.old_entity == retargets[0]["old"]["call_site"])
        assert call_site.continuity == "CONTINUED"
        assert call_site.basis_class == "HEURISTIC"
        assert call_site.old_entity != call_site.new_entity
        assert any(item["kind"] == "relation_retarget" for item in result.receipt.representative_examples)
    finally:
        _close(old_world, new_world)


def test_added_and_removed_identities_are_delta_membership(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function oldHelper(): void {}\n"},
        {
            "src/index.ts": (
                "export function oldHelper(): void {}\n"
                "export function newHelper(): void {}\n"
            )
        },
    )
    try:
        result = compare_program_spines(old_world, new_world)
        assert _entity(new_world, "newHelper", "callable") in result.delta.identity["added"]
        assert result.delta.identity["removed"] == []
    finally:
        _close(old_world, new_world)

    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function oldHelper(): void {}\n"},
        {"src/index.ts": "export function replacement(): number { return 1; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        assert _entity(old_world, "oldHelper", "callable") in result.delta.identity["removed"]
        assert _entity(new_world, "replacement", "callable") in result.delta.identity["added"]
    finally:
        _close(old_world, new_world)


def test_delete_and_add_with_compatible_signature_is_heuristic_not_entailed(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function oldHelper(value: string): string { return value; }\n"},
        {"src/index.ts": "export function replacement(value: string): string { return value; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "oldHelper", "callable")
        new_id = _entity(new_world, "replacement", "callable")
        claim = next(item for item in result.correspondences if item.old_entity == old_id)
        assert old_id != new_id
        assert claim.new_entity == new_id
        assert claim.continuity == "CONTINUED"
        assert claim.outcome == "RENAME"
        assert claim.basis_class == "HEURISTIC"
        assert all(item["kind"] == "HEURISTIC" for item in claim.evidence)
        assert claim.basis_class != "DETERMINISTIC"
        assert any(
            "not mechanically entailed" in item
            for item in claim.limitations
        )
    finally:
        _close(old_world, new_world)


def test_ambiguous_duplicate_candidates_are_retained_without_selection(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function source(value: string): string { return value; }\n"},
        {
            "src/index.ts": (
                "export function first(value: string): string { return value; }\n"
                "export function second(value: string): string { return value; }\n"
            )
        },
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "source", "callable")
        ambiguous = [item for item in result.delta.identity["ambiguous"] if item["old_entity"] == old_id]
        assert len(ambiguous) == 1
        assert len(ambiguous[0]["candidate_entities"]) == 2
        assert not any(
            item in result.delta.identity["added"]
            for item in [row["entity"] for row in _entities(new_world, "callable")]
        )
        assert not result.delta.identity["removed"]
        assert all(item.continuity == "AMBIGUOUS" for item in result.correspondences if item.old_entity == old_id)
        assert all(item.basis_class == "HEURISTIC" for item in result.correspondences if item.old_entity == old_id)
    finally:
        _close(old_world, new_world)


def test_partial_identity_universe_keeps_unmatched_correspondence_unresolved(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function oldHelper(value: string): string { return value; }\n"},
        {"src/index.ts": "export function replacement(value: number): number { return value; }\n"},
    )
    old_path, new_path = old_world.path, new_world.path
    _close(old_world, new_world)
    for path in (old_path, new_path):
        _unseal(path)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "UPDATE program_capability SET status='PARTIAL' "
                "WHERE capability='spine.code_structure'"
            )
    old_world = ConstructionWorld.open(old_path)
    new_world = ConstructionWorld.open(new_path)
    try:
        result = compare_program_spines(old_world, new_world)
        assert result.delta.identity["added"] == []
        assert result.delta.identity["removed"] == []
        assert result.delta.identity["unresolved"]
        assert result.receipt.correspondence_summary["outcomes"]["unresolved"] > 0
    finally:
        _close(old_world, new_world)


def test_structural_owner_change_is_reported(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {
            "src/index.ts": (
                "export function outer(): void { function helper(): void {} helper(); }\n"
            )
        },
        {
            "src/index.ts": (
                "export function outer(): void {}\n"
                "export function helper(): void {}\n"
            )
        },
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "helper", "callable")
        change = next(item for item in result.delta.manifestations if item["old_entity"] == old_id)
        assert change["changes"]["structural_context"] == "CHANGED"
        assert change["outcome"] == "MOVE"
    finally:
        _close(old_world, new_world)


def test_external_endpoint_change_is_added_removed_and_call_retarget(tmp_path):
    root = tmp_path
    (root / "node_modules" / "payments").mkdir(parents=True)
    (root / "node_modules" / "payments" / "index.d.ts").write_text(
        "export declare function authorize(): void;\n", encoding="utf-8"
    )
    (root / "node_modules" / "payments" / "package.json").write_text(
        '{"name":"payments","version":"1.0.0","types":"index.d.ts"}', encoding="utf-8"
    )
    old, old_world, boundary = _project(
        root,
        {"src/index.ts": "import { authorize } from 'payments'; export function run(): void { authorize(); }\n"},
        "world-old",
    )
    (root / "node_modules" / "payments" / "package.json").write_text(
        '{"name":"payments","version":"2.0.0","types":"index.d.ts"}', encoding="utf-8"
    )
    new, new_world, _ = _project(
        root,
        {"src/index.ts": "import { authorize } from 'payments'; export function run(): void { authorize(); }\n"},
        "world-new",
    )
    try:
        result = compare_program_spines(old_world.path, new_world.path)
        old_external = {row["entity"] for row in old_world.relation_rows("program_entity") if row["boundary"] == "EXTERNAL_BOUNDARY"}
        new_external = {row["entity"] for row in new_world.relation_rows("program_entity") if row["boundary"] == "EXTERNAL_BOUNDARY"}
        assert old_external.isdisjoint(new_external)
        assert result.delta.identity["removed"]
        assert result.delta.identity["added"]
        assert result.delta.relations["program_invokes"]["retargeted"]
    finally:
        _close(old_world, new_world)


def test_incompatible_capability_versions_are_not_comparable(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function run(): void {}\n"},
        {"src/index.ts": "export function run(): void {}\n"},
    )
    old_path, new_path = old_world.path, new_world.path
    _close(old_world, new_world)
    _unseal(new_path)
    with sqlite3.connect(new_path) as connection:
        connection.execute(
            "UPDATE program_capability SET version='v2' "
            "WHERE capability='spine.calls'"
        )
    old_world = ConstructionWorld.open(old_path)
    new_world = ConstructionWorld.open(new_path)
    try:
        result = compare_program_spines(old_world, new_world)
        calls = result.delta.relations["program_invokes"]
        assert calls["status"] == "NOT_COMPARABLE"
        assert "spine.calls/v1" in result.receipt.not_comparable_capabilities or "spine.calls/v2" in result.receipt.not_comparable_capabilities
    finally:
        _close(old_world, new_world)


def test_whitespace_source_movement_preserves_mechanical_identity(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function run(): void {}\n"},
        {"src/index.ts": "\n\nexport function run(): void {}\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world)
        old_id = _entity(old_world, "run", "callable")
        claim = next(item for item in result.correspondences if item.old_entity == old_id)
        assert claim.outcome == "UNCHANGED_OR_CONTINUED"
        assert claim.changes["source_location"] == "CHANGED"
        assert claim.changes["name"] == "PRESERVED"
    finally:
        _close(old_world, new_world)


def test_split_and_merge_groups_are_representation_ready(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function process(): void {}\n"},
        {
            "src/index.ts": (
                "export function validate(): void {}\n"
                "export function authorize(): void {}\n"
            )
        },
    )
    old_id = _entity(old_world, "process", "callable")
    new_ids = (
        _entity(new_world, "validate", "callable"),
        _entity(new_world, "authorize", "callable"),
    )
    split = CorrespondenceGroup(
        event="SPLIT",
        old_entities=(old_id,),
        new_entities=new_ids,
        basis_class="OBSERVATIONAL",
        evidence=({"kind": "OBSERVATIONAL", "rule": "fixture-supplied cardinality evidence"},),
    )
    try:
        result = compare_program_spines(old_world, new_world, groups=(split,))
        assert result.delta.identity["split"][0]["group_id"] == split.group_id
        assert result.receipt.split_merge_summary["split"]
        assert not any(
            item in result.delta.identity["added"]
            for item in [row["entity"] for row in _entities(new_world, "callable")]
        )
        assert not any(
            item in result.delta.identity["removed"]
            for item in [row["entity"] for row in _entities(old_world, "callable")]
        )
        payload = result.to_dict()
        assert "correspondence_groups" in payload
        merge = CorrespondenceGroup(
            event="MERGE",
            old_entities=new_ids,
            new_entities=(old_id,),
            basis_class="OBSERVATIONAL",
            evidence=({"kind": "OBSERVATIONAL", "rule": "fixture-supplied cardinality evidence"},),
        )
        reversed_result = compare_program_spines(new_world, old_world, groups=(merge,))
        assert reversed_result.delta.identity["merged"][0]["group_id"] == merge.group_id
    finally:
        _close(old_world, new_world)


def test_comparison_receipt_round_trip_and_malformed_receipt_validation(tmp_path):
    _, _, _, old_world, new_world = _pair(
        tmp_path,
        {"src/index.ts": "export function run(): void {}\n"},
        {"src/index.ts": "export function run(): void { return; }\n"},
    )
    try:
        result = compare_program_spines(old_world, new_world, output_dir=tmp_path / "comparison")
        loaded = load_comparison(tmp_path / "comparison" / "spine.comparison.json")
        assert loaded.to_dict() == result.to_dict()
        malformed = result.receipt.to_dict()
        malformed["receipt_version"] = "spine_comparison_receipt/v2"
        assert SpineComparisonReceipt.from_dict(malformed).validate()
        malformed = result.receipt.to_dict()
        malformed["comparison_mechanism"]["lineage_quality"] = 0.9
        assert any(
            "lineage-quality" in error
            for error in SpineComparisonReceipt.from_dict(malformed).validate()
        )
    finally:
        _close(old_world, new_world)


def test_comparison_rejects_missing_manifest(tmp_path):
    files = {"src/index.ts": "export function run(): void {}\n"}
    _, world, _ = _project(tmp_path, files, "world")
    world.close()
    output_dir = tmp_path / "world"
    os.chmod(output_dir, output_dir.stat().st_mode | 0o700)
    (output_dir / "typescript.manifest.json").unlink()
    with pytest.raises(ComparisonError, match="manifest"):
        compare_program_spines(tmp_path / "world", tmp_path / "world")

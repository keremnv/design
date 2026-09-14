from __future__ import annotations

import json
import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from ontology_author.program_spine import (
    TypeScriptBoundary,
    build_typescript_spine,
    localize_source_range,
    validate_typescript_spine,
)
from ontology_author.program_spine.typescript import utf16_range_to_utf8
from ontology_author.world.runtime.world import ConstructionWorld


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT_MODULE = REPOSITORY_ROOT / "frontend" / "node_modules" / "typescript"
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not TYPESCRIPT_MODULE.exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def _project(tmp_path: Path, files: dict[str, str], *, package_roots=("src",), workspace_roots=("src",)):
    (tmp_path / "src").mkdir(exist_ok=True)
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
    (tmp_path / "tsconfig.json").write_text(
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
        workspace_roots=tuple(workspace_roots),
        projects=("tsconfig.json",),
        package_roots=tuple(package_roots),
    )
    result = build_typescript_spine(tmp_path, tmp_path / "world", boundary=boundary)
    assert result.succeeded, result.errors
    world = ConstructionWorld.open(tmp_path / "world" / "world.sqlite")
    return result, world, boundary


def _labels_by_metaclass(world: ConstructionWorld, metaclass: str) -> list[tuple[str, str]]:
    rows = [
        row for row in world.relation_rows("kdm_element_type")
        if row["metaclass"] == metaclass
    ]
    return [
        (str(row["entity"]), str(world.query(
            "SELECT label FROM _world_referents WHERE id=?", (row["entity"],)
        )[0]["label"]))
        for row in rows
    ]


def test_required_kdm_entities_universe_imports_and_calls(tmp_path):
    result, world, boundary = _project(
        tmp_path,
        {
            "src/helper.ts": "export function submitOrder(value: string): string { return value; }\n",
            "src/index.ts": (
                "import { submitOrder } from './helper';\n"
                "export interface Order { id: string }\n"
                "export class CheckoutPage { submit(order: Order): string { return submitOrder(order.id); } }\n"
                "function unattachedHelper(): void {}\n"
                "export function run(order: Order): string { return new CheckoutPage().submit(order); }\n"
            ),
        },
    )
    try:
        assert result.snapshot_id
        assert {row["metaclass"] for row in world.relation_rows("kdm_element_type")} >= {
            "CompilationUnit",
            "ClassUnit",
            "InterfaceUnit",
            "CallableUnit",
            "MethodUnit",
            "Signature",
            "ParameterUnit",
            "MemberUnit",
            "ActionElement",
        }
        assert len(world.relation_rows("program_entity")) == len(
            world.relation_rows("kdm_element_type")
        )
        assert len(world.relation_rows("kdm_imports")) == 1
        assert any(row["status"] == "RESOLVED" for row in world.relation_rows("typescript_resolution"))
        assert world.relation_rows("kdm_calls")
        assert any(label == "unattachedHelper" for _, label in _labels_by_metaclass(world, "CallableUnit"))
        assert any(row["kind"] == "action" for row in world.relation_rows("program_entity"))
        assert set(result.capabilities) == {
            "program_universe",
            "source_evidence",
            "code_structure",
            "imports",
            "calls",
            "external_endpoints",
        }
        assert all(value == "COMPLETE" for value in result.capabilities.values())
        assert boundary.payload(tmp_path)["projects"] == ["tsconfig.json"]
    finally:
        world.close()


def test_call_site_is_owned_action_element_and_exactly_grounded(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {
            "src/index.ts": "function target(): void {}\nexport function run(): void { target(); }\n",
        },
    )
    try:
        actions = {
            row["entity"]
            for row in world.relation_rows("kdm_element_type")
            if row["metaclass"] == "ActionElement"
        }
        assert len(actions) == 1
        action = next(iter(actions))
        assert any(row["owned_element"] == action for row in world.relation_rows("kdm_ownership"))
        call = world.relation_rows("kdm_calls")[0]
        assert call["from"] == action
        assertion = world.query(
            "SELECT assertion_id FROM _world_assertions WHERE relation_name='kdm_calls'"
        )[0]["assertion_id"]
        groundings = world.query(
            "SELECT detail FROM _world_groundings WHERE subject_type='ASSERTION' AND subject_id=?",
            (assertion,),
        )
        assert any('"native_location":"bytes:' in row["detail"] for row in groundings)
    finally:
        world.close()


def test_external_package_is_preserved_as_boundary_stub(tmp_path):
    package = tmp_path / "node_modules" / "third-party"
    package.mkdir(parents=True)
    (package / "package.json").write_text(
        '{"name":"third-party","types":"index.d.ts"}', encoding="utf-8"
    )
    (package / "index.d.ts").write_text(
        "export declare function externalCall(value: string): string;\n",
        encoding="utf-8",
    )
    _, world, _ = _project(
        tmp_path,
        {"src/index.ts": "import { externalCall } from 'third-party'; export function run(x: string) { return externalCall(x); }\n"},
    )
    try:
        external = [row for row in world.relation_rows("program_entity") if row["boundary"] == "EXTERNAL_BOUNDARY"]
        assert external
        assert any(row["kind"] == "function" for row in external)
        assert any(row["to"] in {item["entity"] for item in external} for row in world.relation_rows("kdm_calls"))
        assert not any(
            row["boundary"] == "IN_SCOPE" and "node_modules" in row["entity"]
            for row in world.relation_rows("program_entity")
        )
    finally:
        world.close()


def test_demo_world_keeps_presence_sparse_significance_and_external_endpoint(tmp_path):
    package = tmp_path / "node_modules" / "payments"
    package.mkdir(parents=True)
    (package / "package.json").write_text(
        '{"name":"payments","version":"1.0.0","types":"index.d.ts"}', encoding="utf-8"
    )
    (package / "index.d.ts").write_text(
        "export declare function authorize(): void;\n", encoding="utf-8"
    )
    _, world, _ = _project(
        tmp_path,
        {
            "src/checkout.ts": (
                "import { authorize } from 'payments';\n"
                "export function submitOrder(): void { authorize(); }\n"
                "export class PurchaseButton {}\n"
                "export class CheckoutPage {}\n"
                "function unattachedHelper(): void {}\n"
            )
        },
    )
    try:
        labels = {label for _, label in _labels_by_metaclass(world, "CallableUnit")}
        assert {"submitOrder", "unattachedHelper"} <= labels
        assert {"PurchaseButton", "CheckoutPage"} <= {
            label for _, label in _labels_by_metaclass(world, "ClassUnit")
        }
        assert any(row["boundary"] == "EXTERNAL_BOUNDARY" for row in world.relation_rows("program_entity"))
        assert world.relation_rows("kdm_calls")
    finally:
        world.close()


def test_workspace_material_outside_package_boundary_is_external(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {
            "src/app/index.ts": "import { shared } from '../shared/index'; export function run() { return shared(); }\n",
            "src/shared/index.ts": "export function shared(): string { return 'shared'; }\n",
        },
        workspace_roots=("src",),
        package_roots=("src/app",),
    )
    try:
        assert any(row["boundary"] == "EXTERNAL_BOUNDARY" for row in world.relation_rows("program_entity"))
        assert any(row["boundary"] == "IN_SCOPE" for row in world.relation_rows("program_entity"))
    finally:
        world.close()


def test_unresolved_dynamic_call_has_outcome_without_guessed_edge(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {"src/index.ts": "const handlers: Record<string, () => void> = {}; export function run(k: string) { handlers[k](); }\n"},
    )
    try:
        outcomes = [row for row in world.relation_rows("typescript_resolution") if row["relation_name"] == "kdm_calls"]
        assert len(outcomes) == 1
        assert outcomes[0]["status"] in {"UNRESOLVED", "MULTIPLE_CANDIDATES"}
        assert not world.relation_rows("kdm_calls")
    finally:
        world.close()


def test_nested_and_anonymous_callables_use_profile_identities(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {
            "src/index.ts": (
                "export function outer(): void { function nested(): void {} nested(); }\n"
                "export const namedArrow = (value: string): string => value;\n"
                "function target(): void {}\n"
                "export function callbackUse(values: string[]): void { values.map(value => value); [() => target()]; }\n"
            )
        },
    )
    try:
        callable_labels = [label for _, label in _labels_by_metaclass(world, "CallableUnit")]
        assert "outer" in callable_labels
        assert "nested" in callable_labels
        assert "namedArrow" in callable_labels
        assert len(callable_labels) >= 5  # the arrow containing target() is required call-site support
    finally:
        world.close()


def test_overloads_have_signatures_and_call_targets_bound_callable(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {
            "src/index.ts": (
                "export function overloaded(value: string): string;\n"
                "export function overloaded(value: number): number;\n"
                "export function overloaded(value: string | number): string | number { return value; }\n"
                "export function run(): number { return overloaded(1) as number; }\n"
            )
        },
    )
    try:
        assert len(_labels_by_metaclass(world, "Signature")) >= 3
        outcome = next(
            row for row in world.relation_rows("typescript_resolution")
            if row["relation_name"] == "kdm_calls"
        )
        assert outcome["status"] == "RESOLVED"
        details = json.loads(outcome["details"])
        assert details["selectedSignature"]
        assert details["candidateSignatures"]
        assert len(world.relation_rows("kdm_calls")) >= 1
    finally:
        world.close()


def test_union_method_call_retains_multiple_candidates_without_positive_edge(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {
            "src/index.ts": (
                "interface First { run(): void } interface Second { run(): void }\n"
                "declare const value: First | Second; export function use(): void { value.run(); }\n"
            )
        },
    )
    try:
        outcome = next(
            row for row in world.relation_rows("typescript_resolution")
            if row["relation_name"] == "kdm_calls"
        )
        assert outcome["status"] == "MULTIPLE_CANDIDATES"
        assert len(world.relation_rows("typescript_resolution_candidate")) >= 2
        assert not world.relation_rows("kdm_calls")
    finally:
        world.close()


def test_localization_returns_program_entities_without_semantic_impact(tmp_path):
    source = "function helper(): void {}\nexport function run(): void { helper(); }\n"
    _, world, _ = _project(tmp_path, {"src/index.ts": source})
    try:
        start = source.index("helper();")
        results = localize_source_range(
            world,
            tmp_path / "src/index.ts",
            start,
            start + len("helper();"),
            workspace=tmp_path,
        )
        labels = {
            row["label"]
            for row in world.query(
                "SELECT label FROM _world_referents WHERE id IN (%s)"
                % ",".join("?" for _ in results),
                results,
            )
        }
        assert "run" in labels
        assert "helper" not in labels
    finally:
        world.close()


@pytest.mark.parametrize(
    ("text", "start", "end", "expected"),
    [
        ("abc", 1, 3, (1, 3)),
        ("a😀b", 1, 3, (1, 5)),
        ("a\r\n😀", 3, 5, (3, 7)),
    ],
)
def test_typescript_utf16_positions_become_utf8_byte_ranges(text, start, end, expected):
    assert utf16_range_to_utf8(text, start, end) == expected


def test_utf16_range_cannot_split_surrogate_pair():
    with pytest.raises(ValueError, match="surrogate"):
        utf16_range_to_utf8("😀", 1, 2)


def test_same_immutable_input_reconstructs_identical_world_facts(tmp_path):
    files = {"src/index.ts": "export function stable(value: string): string { return value; }\n"}
    first, world, boundary = _project(tmp_path, files)
    try:
        first_rows = {
            relation: world.relation_rows(relation)
            for relation in ("program_entity", "kdm_element_type", "kdm_ownership", "program_capability")
        }
        world.close()
        world = None
        second = build_typescript_spine(tmp_path, tmp_path / "world", boundary=boundary)
        assert second.succeeded
        reopened = ConstructionWorld.open(tmp_path / "world" / "world.sqlite")
        try:
            assert first.snapshot_id == second.snapshot_id
            assert first_rows == {
                relation: reopened.relation_rows(relation)
                for relation in first_rows
            }
            assert json.loads((tmp_path / "world" / "typescript.manifest.json").read_text())[
                "snapshot_id"
            ] == first.snapshot_id
        finally:
            reopened.close()
    finally:
        if world is not None:
            world.close()


def test_admission_rejects_relation_endpoint_missing_from_program_universe(tmp_path):
    _, world, _ = _project(
        tmp_path,
        {"src/index.ts": "function target(): void {} export function run() { target(); }\n"},
    )
    world.close()
    database = tmp_path / "world" / "world.sqlite"
    mode = database.stat().st_mode
    directory = database.parent
    directory_mode = directory.stat().st_mode
    os.chmod(directory, directory_mode | 0o700)
    os.chmod(database, mode | 0o600)
    try:
        with sqlite3.connect(database) as connection:
            connection.execute(
                "DELETE FROM program_entity WHERE entity_id IN "
                "(SELECT to_id FROM kdm_calls LIMIT 1)"
            )
    finally:
        os.chmod(database, mode)
        os.chmod(directory, directory_mode)
    malformed = ConstructionWorld.open(database)
    try:
        manifest = json.loads((tmp_path / "world" / "typescript.manifest.json").read_text())
        errors = validate_typescript_spine(malformed, manifest)
        assert any("endpoint is not in program_entity" in error for error in errors)
    finally:
        malformed.close()

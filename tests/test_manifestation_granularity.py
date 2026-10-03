"""Historical manifestation-granularity experiment.

Excluded from the default gate. Run with `pytest -m historical`.

Compares three mechanical manifestation grains against the existing
TypeScript spine, without changing spine contracts or comparison:

* file grain: digest of the whole grounded source input
* entity/occurrence grain: digest of the extractor's exact byte range,
  excluding the offset itself
* source location: that offset, reported separately from content

Call-site correspondence is whatever the current comparison already
claims. This module does not invent continuity.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from ontology_author.evidence.program_source import (
    program_source_observations,
    reconstruct_program_observation,
)
from ontology_author.program_spine import (
    TypeScriptBoundary,
    build_typescript_spine,
    compare_program_spines,
)
from ontology_author.world.runtime.world import ConstructionWorld

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT_MODULE = REPOSITORY_ROOT / "frontend" / "node_modules" / "typescript"
pytestmark = [
    pytest.mark.historical,
    pytest.mark.skipif(
        shutil.which("node") is None or not TYPESCRIPT_MODULE.exists(),
        reason="the TypeScript compiler API dependency is not installed",
    ),
]

SUBJECTS = """\
export function report(label: string): string {
  return label;
}

export function neighbor(label: string): string {
  return report(label);
}

export function governed(amount: number): number {
  const prepared = amount + 1;
  return charge(prepared);
}

export function charge(value: number): number {
  return value;
}

export function refund(value: number): number {
  return value;
}
"""

OTHER = """\
export function outside(value: number): number {
  return value;
}
"""

# Edits are full-file replacements of the baseline so each control is obvious.
def _patched(old: str, new: str) -> str:
    assert old in SUBJECTS, old
    patched = SUBJECTS.replace(old, new, 1)
    assert patched != SUBJECTS
    return patched


CONTROLS: dict[str, dict[str, str]] = {
    "A_body_local": {
        "src/subjects.ts": _patched(
            "const prepared = amount + 1;",
            "const prepared = amount + 2;",
        ),
        "src/other.ts": OTHER,
    },
    "B_preceding_neighbor": {
        "src/subjects.ts": _patched("return label;", "return label.trim();"),
        "src/other.ts": OTHER,
    },
    "B_following_neighbor": {
        "src/subjects.ts": _patched(
            "export function refund(value: number): number {\n  return value;\n}",
            "export function refund(value: number): number {\n  return value + 1;\n}",
        ),
        "src/other.ts": OTHER,
    },
    "C_outside_file": {
        "src/subjects.ts": SUBJECTS,
        "src/other.ts": OTHER.replace("return value;", "return value + 1;"),
    },
    "D_signature": {
        "src/subjects.ts": _patched(
            "export function governed(amount: number): number {",
            "export function governed(amount: number, note: string): number {",
        ),
        "src/other.ts": OTHER,
    },
    "E_leading_trivia": {
        "src/subjects.ts": _patched(
            "export function governed(amount: number): number {",
            "// governed note\nexport function governed(amount: number): number {",
        ),
        "src/other.ts": OTHER,
    },
    "E_interior_trivia": {
        "src/subjects.ts": _patched(
            "const prepared = amount + 1;",
            "const  prepared = amount + 1;",
        ),
        "src/other.ts": OTHER,
    },
    "E_call_trivia": {
        "src/subjects.ts": _patched(
            "return charge(prepared);",
            "return  charge(prepared);",
        ),
        "src/other.ts": OTHER,
    },
    "F_retarget": {
        "src/subjects.ts": _patched(
            "return charge(prepared);",
            "return refund(prepared);",
        ),
        "src/other.ts": OTHER,
    },
    "G_insert_call_before": {
        "src/subjects.ts": _patched(
            "  const prepared = amount + 1;\n  return charge(prepared);\n",
            "  const prepared = amount + 1;\n  audit(prepared);\n  return charge(prepared);\n",
        ).replace(
            "export function refund(value: number): number {\n  return value;\n}\n",
            "export function refund(value: number): number {\n  return value;\n}\n\n"
            "export function audit(value: number): number {\n  return value;\n}\n",
        ),
        "src/other.ts": OTHER,
    },
    "G_insert_call_after": {
        "src/subjects.ts": _patched(
            "  return charge(prepared);\n",
            "  return charge(prepared);\n  charge(0);\n",
        ),
        "src/other.ts": OTHER,
    },
}


def _build(root: Path, files: dict[str, str]) -> Path:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    (root / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "moduleResolution": "node",
                    "strict": True,
                },
                "include": ["src/**/*.ts"],
            }
        ),
        encoding="utf-8",
    )
    boundary = TypeScriptBoundary(
        workspace_roots=("src",),
        projects=("tsconfig.json",),
        package_roots=("src",),
    )
    world_dir = root / "world"
    result = build_typescript_spine(root, world_dir, boundary=boundary)
    assert result.succeeded, result.errors
    return world_dir


def _status(old: str, new: str) -> str:
    return "PRESERVED" if old == new else "CHANGED"


def _offsets(location: str) -> tuple[str, str]:
    start, end = location.removeprefix("bytes:").split(":")
    return start, end


def _catalog(world_dir: Path) -> dict[str, Any]:
    world = ConstructionWorld.open(world_dir / "world.sqlite")
    try:
        labels = {
            str(row["id"]): str(row["label"])
            for row in world.query("SELECT id, label FROM _world_referents")
        }
        kinds = {
            str(row["entity"]): str(row["kind"])
            for row in world.relation_rows("program_entity_kind")
        }
        descriptors = {
            str(row["entity"]): str(row["descriptor"])
            for row in world.relation_rows("program_identity_descriptor")
        }
        parents: dict[str, list[str]] = {}
        for row in world.relation_rows("structural_context"):
            parents.setdefault(str(row["child"]), []).append(str(row["parent"]))
        invokes = [
            {
                "call_site": str(row["call_site"]),
                "target": str(row["target"]),
                "target_label": labels.get(str(row["target"]), ""),
            }
            for row in world.relation_rows("program_invokes")
        ]
        snapshot = world.relation_rows("program_snapshot")[0]
        capabilities = {
            f"{row['capability']}/{row['version']}": {
                "status": str(row["status"]),
                "basis": str(row["basis"]),
            }
            for row in world.relation_rows("program_capability")
        }
        entities: dict[str, dict[str, Any]] = {}
        for entity_id, kind in kinds.items():
            observations = []
            for observation in program_source_observations(world, entity_id):
                text, reconstruction = reconstruct_program_observation(world, observation)
                handle = observation["native_handle"]
                digest = handle.rsplit("@sha256:", 1)[-1]
                location = observation["native_location"]
                observations.append(
                    {
                        "provider": observation["provider"],
                        "handle_path": handle.split("@sha256:", 1)[0],
                        "file_sha256": digest,
                        "source_revision": observation["source_revision"],
                        "native_location": location,
                        "reconstruction": reconstruction,
                        "region_text": text,
                        "region_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()
                        if reconstruction == "OK"
                        else "",
                    }
                )
            parent_ids = parents.get(entity_id, [])
            entities[entity_id] = {
                "id": entity_id,
                "label": labels.get(entity_id, ""),
                "kind": kind,
                "descriptor": descriptors.get(entity_id, ""),
                "parent_labels": [labels.get(parent, "") for parent in parent_ids],
                "observations": observations,
            }
        return {
            "snapshot_id": str(snapshot["source_state"]),
            "extractor": str(snapshot["extractor"]),
            "analyzer": str(snapshot["analyzer"]),
            "core_contract": str(snapshot["core_contract"]),
            "capabilities": capabilities,
            "entities": entities,
            "invokes": invokes,
        }
    finally:
        world.close()


def _find(catalog: dict[str, Any], *, kind: str, label: str | None = None, text: str | None = None, parent: str | None = None) -> dict[str, Any]:
    matches = []
    for entity in catalog["entities"].values():
        if entity["kind"] != kind:
            continue
        if label is not None and entity["label"] != label:
            continue
        if parent is not None and parent not in entity["parent_labels"]:
            continue
        if text is not None:
            regions = [item["region_text"] for item in entity["observations"]]
            if text not in regions:
                continue
        matches.append(entity)
    assert len(matches) == 1, (kind, label, text, parent, [(item["label"], item["parent_labels"], [obs["region_text"] for obs in item["observations"]]) for item in matches])
    return matches[0]


def _primary(entity: dict[str, Any]) -> dict[str, Any]:
    observations = entity["observations"]
    assert len(observations) == 1, entity["label"]
    observation = observations[0]
    assert observation["reconstruction"] == "OK"
    return observation


def _same_region_elsewhere(catalog: dict[str, Any], kind: str, region_sha: str, except_id: str) -> list[str]:
    found = []
    for entity in catalog["entities"].values():
        if entity["id"] == except_id or entity["kind"] != kind:
            continue
        if any(item["region_sha256"] == region_sha and item["reconstruction"] == "OK" for item in entity["observations"]):
            found.append(entity["id"])
    return found


def _invoke_bucket(result: Any, old_call_id: str) -> str:
    relation = result.delta.relations["program_invokes"]
    for bucket in ("preserved", "retargeted", "removed", "unresolved"):
        for row in relation[bucket]:
            old = row.get("old") or {}
            if old.get("call_site") == old_call_id:
                return bucket.upper()
    return "ABSENT"


def _measure_subject(old_catalog: dict[str, Any], new_catalog: dict[str, Any], result: Any, old_entity: dict[str, Any]) -> dict[str, Any]:
    old_obs = _primary(old_entity)
    claims = [claim for claim in result.correspondences if claim.old_entity == old_entity["id"]]
    assert len(claims) == 1
    claim = claims[0]
    continued = claim.continuity == "CONTINUED" and claim.new_entity
    new_entity = new_catalog["entities"][claim.new_entity] if continued else None
    new_obs = _primary(new_entity) if new_entity else None
    same_bytes = _same_region_elsewhere(
        new_catalog,
        old_entity["kind"],
        old_obs["region_sha256"],
        claim.new_entity or "",
    )
    followed_same_bytes = bool(
        new_obs and new_obs["region_sha256"] == old_obs["region_sha256"]
    )
    relation_status = "NOT_AN_INVOCATION_SUBJECT"
    if old_entity["kind"] == "call_site":
        relation_status = _invoke_bucket(result, old_entity["id"])
    return {
        "kind": old_entity["kind"],
        "label": old_entity["label"],
        "parent_labels": old_entity["parent_labels"],
        "baseline_region": old_obs["region_text"],
        "identity": claim.continuity,
        "identity_basis": claim.basis_class,
        "identity_outcome": claim.outcome,
        "spine_source_manifestation": claim.changes.get("source_manifestation", "NOT_REPORTED"),
        "spine_source_location": claim.changes.get("source_location", "NOT_REPORTED"),
        "spine_structural_context": claim.changes.get("structural_context", "NOT_REPORTED"),
        "spine_signature": claim.changes.get("signature", "NOT_REPORTED"),
        "file_grain": _status(old_obs["file_sha256"], new_obs["file_sha256"]) if new_obs else "NOT_COMPARABLE",
        "region_grain": _status(old_obs["region_sha256"], new_obs["region_sha256"]) if new_obs else "NOT_COMPARABLE",
        "location": _status(old_obs["native_location"], new_obs["native_location"]) if new_obs else "NOT_COMPARABLE",
        "location_start": _status(_offsets(old_obs["native_location"])[0], _offsets(new_obs["native_location"])[0]) if new_obs else "NOT_COMPARABLE",
        "location_end": _status(_offsets(old_obs["native_location"])[1], _offsets(new_obs["native_location"])[1]) if new_obs else "NOT_COMPARABLE",
        "location_path": _status(old_obs["handle_path"], new_obs["handle_path"]) if new_obs else "NOT_COMPARABLE",
        "reconstruction": "OK" if new_obs else old_obs["reconstruction"],
        "new_region": new_obs["region_text"] if new_obs else "",
        "corresponded_region_matches_baseline_bytes": followed_same_bytes,
        "baseline_bytes_present_on_other_identity": bool(same_bytes),
        "program_relation": relation_status,
        "producer": {
            "provider": old_obs["provider"],
            "extractor": old_catalog["extractor"],
            "core_contract": old_catalog["core_contract"],
        },
    }


def _subjects(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "callable_governed": _find(catalog, kind="callable", label="governed"),
        "callable_neighbor": _find(catalog, kind="callable", label="neighbor"),
        "callable_report": _find(catalog, kind="callable", label="report"),
        "occurrence_charge": _find(catalog, kind="call_site", text="charge(prepared)", parent="governed"),
        "occurrence_report": _find(catalog, kind="call_site", text="report(label)", parent="neighbor"),
    }


def test_manifestation_grains_separate_content_from_file_and_location(tmp_path: Path) -> None:
    baseline_files = {"src/subjects.ts": SUBJECTS, "src/other.ts": OTHER}
    baseline_dir = _build(tmp_path / "baseline", baseline_files)
    baseline = _catalog(baseline_dir)
    calls = baseline["capabilities"]["spine.calls/v1"]
    structure = baseline["capabilities"]["spine.code_structure/v1"]
    assert calls["status"] in {"COMPLETE", "STATIC_COMPLETE"}
    assert structure["status"] in {"COMPLETE", "STATIC_COMPLETE"}
    assert baseline["core_contract"] == "spine_core/v1"
    assert "typescript-compiler-api" in baseline["extractor"]

    selected = _subjects(baseline)
    governed = selected["callable_governed"]
    charge = selected["occurrence_charge"]
    governed_obs = _primary(governed)
    charge_obs = _primary(charge)
    assert charge_obs["region_text"] == "charge(prepared)"
    assert "export function governed" in governed_obs["region_text"]
    assert "const prepared = amount + 1;" in governed_obs["region_text"]
    assert charge_obs["file_sha256"] == governed_obs["file_sha256"]
    assert charge_obs["region_sha256"] != governed_obs["region_sha256"]

    signature = _find(baseline, kind="signature", parent="governed")
    signature_obs = _primary(signature)
    # The stored signature evidence is the declaration node, not a header-only span.
    assert signature_obs["region_sha256"] == governed_obs["region_sha256"]

    matrix: dict[str, dict[str, Any]] = {}
    for name, files in CONTROLS.items():
        variant_dir = _build(tmp_path / name, files)
        variant = _catalog(variant_dir)
        comparison = compare_program_spines(baseline_dir, variant_dir)
        assert comparison.receipt.compatibility["core"] == "COMPATIBLE"
        matrix[name] = {
            key: _measure_subject(baseline, variant, comparison, entity)
            for key, entity in selected.items()
        }

    governed_rows = {name: row["callable_governed"] for name, row in matrix.items()}
    charge_rows = {name: row["occurrence_charge"] for name, row in matrix.items()}
    neighbor_rows = {name: row["callable_neighbor"] for name, row in matrix.items()}
    report_callable_rows = {name: row["callable_report"] for name, row in matrix.items()}
    report_rows = {name: row["occurrence_report"] for name, row in matrix.items()}

    # File grain moves on every same-file edit and stays still across files.
    for name in CONTROLS:
        if name == "C_outside_file":
            assert governed_rows[name]["file_grain"] == "PRESERVED"
            assert charge_rows[name]["file_grain"] == "PRESERVED"
        else:
            assert governed_rows[name]["file_grain"] == "CHANGED"
            assert charge_rows[name]["file_grain"] == "CHANGED"
        spine_manifestation = governed_rows[name]["spine_source_manifestation"]
        if governed_rows[name]["file_grain"] == "CHANGED" or governed_rows[name]["location"] == "CHANGED":
            assert spine_manifestation == "CHANGED"
        else:
            assert spine_manifestation == "PRESERVED"

    # Identity stays on both shapes for edits that do not insert a sibling call.
    stable_identity = [name for name in CONTROLS if not name.startswith("G_")]
    for name in stable_identity:
        for rows in (governed_rows, charge_rows, neighbor_rows, report_callable_rows, report_rows):
            assert rows[name]["identity"] == "CONTINUED", name
            assert rows[name]["identity_basis"] == "HEURISTIC"
            assert rows[name]["reconstruction"] == "OK"
            assert rows[name]["spine_structural_context"] == "PRESERVED"

    # A preceding body edit shifts later locations without changing their bytes.
    preceding = governed_rows["B_preceding_neighbor"]
    assert preceding["region_grain"] == "PRESERVED"
    assert preceding["location"] == "CHANGED"
    assert preceding["spine_source_location"] == "CHANGED"
    assert charge_rows["B_preceding_neighbor"]["region_grain"] == "PRESERVED"
    assert charge_rows["B_preceding_neighbor"]["location"] == "CHANGED"
    assert neighbor_rows["B_preceding_neighbor"]["region_grain"] == "PRESERVED"
    assert neighbor_rows["B_preceding_neighbor"]["location"] == "CHANGED"
    # The edited declaration is report(); the later call occurrence keeps its bytes.
    assert report_callable_rows["B_preceding_neighbor"]["region_grain"] == "CHANGED"
    assert report_rows["B_preceding_neighbor"]["region_grain"] == "PRESERVED"
    assert report_rows["B_preceding_neighbor"]["location"] == "CHANGED"

    following = governed_rows["B_following_neighbor"]
    assert following["region_grain"] == "PRESERVED"
    assert following["location"] == "PRESERVED"
    assert charge_rows["B_following_neighbor"]["region_grain"] == "PRESERVED"
    assert charge_rows["B_following_neighbor"]["location"] == "PRESERVED"
    assert neighbor_rows["B_following_neighbor"]["region_grain"] == "PRESERVED"
    assert report_rows["B_following_neighbor"]["region_grain"] == "PRESERVED"

    outside = governed_rows["C_outside_file"]
    assert outside["region_grain"] == "PRESERVED"
    assert outside["location"] == "PRESERVED"
    assert outside["file_grain"] == "PRESERVED"
    assert charge_rows["C_outside_file"]["region_grain"] == "PRESERVED"

    body = governed_rows["A_body_local"]
    assert body["region_grain"] == "CHANGED"
    assert body["location"] == "PRESERVED"
    assert charge_rows["A_body_local"]["region_grain"] == "PRESERVED"
    assert charge_rows["A_body_local"]["program_relation"] == "PRESERVED"
    assert neighbor_rows["A_body_local"]["region_grain"] == "PRESERVED"
    assert report_rows["A_body_local"]["region_grain"] == "PRESERVED"

    signature = governed_rows["D_signature"]
    assert signature["region_grain"] == "CHANGED"
    assert signature["spine_signature"] == "CHANGED"
    # The declaration grows, so the range end moves. The start coordinate does not.
    assert signature["location_start"] == "PRESERVED"
    assert signature["location_end"] == "CHANGED"
    assert charge_rows["D_signature"]["region_grain"] == "PRESERVED"
    assert charge_rows["D_signature"]["location"] == "CHANGED"
    assert body["spine_signature"] == "PRESERVED"

    leading = governed_rows["E_leading_trivia"]
    # getStart(sourceFile) skips leading trivia, so a comment above the
    # declaration moves coordinates without entering the stored region.
    assert leading["region_grain"] == "PRESERVED"
    assert "governed note" not in leading["new_region"]
    assert leading["location"] == "CHANGED"
    assert leading["location_start"] == "CHANGED"
    assert charge_rows["E_leading_trivia"]["region_grain"] == "PRESERVED"
    assert charge_rows["E_leading_trivia"]["location"] == "CHANGED"
    assert neighbor_rows["E_leading_trivia"]["region_grain"] == "PRESERVED"
    assert neighbor_rows["E_leading_trivia"]["location"] == "PRESERVED"

    interior = governed_rows["E_interior_trivia"]
    assert interior["region_grain"] == "CHANGED"
    assert charge_rows["E_interior_trivia"]["region_grain"] == "PRESERVED"

    call_trivia = charge_rows["E_call_trivia"]
    # The extra space is leading trivia of the call expression, so the
    # occurrence bytes stay `charge(prepared)` while the enclosing callable changes.
    assert call_trivia["region_grain"] == "PRESERVED"
    assert call_trivia["new_region"] == "charge(prepared)"
    assert call_trivia["location_start"] == "CHANGED"
    assert call_trivia["program_relation"] == "PRESERVED"
    assert governed_rows["E_call_trivia"]["region_grain"] == "CHANGED"
    assert governed_rows["E_call_trivia"]["location_end"] == "CHANGED"

    retarget = charge_rows["F_retarget"]
    assert retarget["identity"] == "CONTINUED"
    assert retarget["region_grain"] == "CHANGED"
    assert retarget["new_region"] == "refund(prepared)"
    assert retarget["program_relation"] == "RETARGETED"
    assert retarget["baseline_bytes_present_on_other_identity"] is False
    assert governed_rows["F_retarget"]["region_grain"] == "CHANGED"

    inserted_before = charge_rows["G_insert_call_before"]
    assert inserted_before["identity"] == "CONTINUED"
    assert inserted_before["new_region"] == "audit(prepared)"
    assert inserted_before["corresponded_region_matches_baseline_bytes"] is False
    assert inserted_before["baseline_bytes_present_on_other_identity"] is True
    # Owner-plus-order continuation binds the old occurrence to the new
    # earlier call. The original edge is removed rather than retargeted,
    # because both the new occurrence and the original target still exist.
    assert inserted_before["program_relation"] == "REMOVED"
    assert governed_rows["G_insert_call_before"]["identity"] == "CONTINUED"
    assert governed_rows["G_insert_call_before"]["region_grain"] == "CHANGED"

    inserted_after = charge_rows["G_insert_call_after"]
    assert inserted_after["identity"] == "CONTINUED"
    assert inserted_after["region_grain"] == "PRESERVED"
    assert inserted_after["new_region"] == "charge(prepared)"
    assert inserted_after["program_relation"] == "PRESERVED"
    # The added call is `charge(0)`, so the original occurrence bytes are not duplicated.
    assert inserted_after["baseline_bytes_present_on_other_identity"] is False

    # The existing comparison manifestation flag follows the file digest even
    # when the experimental region bytes and, for a following edit, the
    # offsets are unchanged.
    assert following["spine_source_manifestation"] == "CHANGED"
    assert following["region_grain"] == "PRESERVED"
    assert following["location"] == "PRESERVED"

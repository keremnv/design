"""Offline composition falsifiers. These do not claim Glean runtime execution."""
from dataclasses import asdict, replace
import json

import pytest

from tests.phase6b_glean_basis import BasisFailure, DBRef, GleanBasis, Input, canonical, sha256, verify_basis


@pytest.fixture
def composed(tmp_path):
    data = b"int target(int x) { return x + 1; }\n"
    generated = b"constexpr int generated_offset = 29;\n"
    items = (Input("target.cpp", sha256(data), len(data)),
             Input("generated.h", sha256(generated), len(generated)))
    blobs = tmp_path / "blobs"
    blobs.mkdir()
    for item, material in zip(items, (data, generated)):
        (blobs / item.sha256).write_bytes(material)
    base = DBRef("retained-store-A", "fixture/base", "base-guid")
    basis = GleanBasis(DBRef("retained-store-A", "fixture/P1", "p1-guid"), "schema-1", items,
                       canonical({"glean_commit": "pinned", "args": ["-std=c++17", "-nostdinc"]}).decode(), (base,))
    state = {
        basis.occurrence.repo: {"repo": basis.occurrence.repo, "status": "COMPLETE", "properties": {
            "glean.guid": basis.occurrence.guid, "glean.schema_id": basis.schema_id,
            "phase6b.input_state": basis.input_state, "phase6b.recipe": basis.recipe_digest,
        }, "dependency_refs": [asdict(base)]},
        base.repo: {"repo": base.repo, "status": "COMPLETE", "properties": {"glean.guid": base.guid}},
    }
    return basis, state, blobs


def check(composed, namespace=None):
    basis, state, blobs = composed
    verify_basis(basis, basis.record_digest, namespace or basis.occurrence.namespace, state.__getitem__, blobs)


def test_serialized_basis_and_exact_retained_bytes(composed):
    basis, _, _ = composed
    assert GleanBasis.from_json(basis.to_json()) == basis
    check(composed)


@pytest.mark.parametrize("field,value", [
    ("glean.guid", "recreated-key-guid"),
    ("glean.schema_id", "incompatible-schema"),
    ("phase6b.input_state", "wrong-manifest"),
    ("phase6b.recipe", "wrong-index-recipe"),
])
def test_correct_repo_rejects_other_qualification(composed, field, value):
    basis, state, _ = composed
    state[basis.occurrence.repo]["properties"][field] = value
    with pytest.raises(BasisFailure):
        check(composed)


def test_same_repo_and_guid_in_other_namespace_is_not_this_occurrence(composed):
    with pytest.raises(BasisFailure, match="namespace"):
        check(composed, "retained-store-B")


@pytest.mark.parametrize("which", ["historical", "required_base"])
def test_unavailable_db_is_explicit_failure_not_latest(composed, which):
    basis, state, _ = composed
    state["fixture/latest"] = state[basis.occurrence.repo]
    del state[basis.occurrence.repo if which == "historical" else basis.dependencies[0].repo]
    with pytest.raises(BasisFailure, match="unavailable"):
        check(composed)


def test_actual_dependency_must_be_declared(composed):
    basis, state, blobs = composed
    incomplete = replace(basis, dependencies=())
    with pytest.raises(BasisFailure, match="dependency"):
        check((incomplete, state, blobs))


@pytest.mark.parametrize("damage", ["missing", "corrupt", "live_symlink", "missing_generated"])
def test_source_retention_has_no_live_fallback(composed, damage, tmp_path):
    basis, _, blobs = composed
    item = basis.inputs[1 if damage == "missing_generated" else 0]
    path = blobs / item.sha256
    if damage == "corrupt":
        path.write_bytes(b"mutable checkout content")
    else:
        original = path.read_bytes()
        path.unlink()
        if damage == "live_symlink":
            live = tmp_path / "live.cpp"
            live.write_bytes(original)
            path.symlink_to(live)
    with pytest.raises(BasisFailure):
        check(composed)


def test_swapped_admitted_record_is_rejected(composed):
    basis, state, blobs = composed
    changed = replace(basis, recipe_json=json.dumps({"glean_commit": "other"}))
    with pytest.raises(BasisFailure, match="admitted"):
        verify_basis(changed, basis.record_digest, basis.occurrence.namespace, state.__getitem__, blobs)

"""Offline composition falsifiers. These do not claim Glean runtime execution."""
from dataclasses import asdict, replace
import json

import pytest

from tests.phase6b_glean_basis import BasisFailure, DBRef, GleanBasis, Input, canonical, sha256, verify_basis
from tests.phase6b_glean_cpp_spike import CppProbe, FUNCTION_PREDICATE, UNIT_PREDICATE, check_context_closure


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


@pytest.fixture
def consistency_probe(composed):
    basis, state, blobs = composed
    probe = CppProbe.__new__(CppProbe)
    probe.root = blobs.parent
    (probe.root / "namespace.json").write_text(json.dumps(basis.occurrence.namespace))
    probe.metadata = state.__getitem__  # modeled metadata, not native Glean
    return probe, basis


@pytest.mark.parametrize("digest", [None, ""])
def test_admission_open_requires_independent_digest(consistency_probe, digest):
    probe, basis = consistency_probe
    assert probe.open_consistent(basis) == basis
    with pytest.raises(BasisFailure, match="^independent admission digest required$"):
        probe.open_admitted(basis, digest)


def test_equivalent_recipe_consistency_does_not_confer_admission(consistency_probe):
    probe, basis = consistency_probe
    # A separately retained trusted pin models admission. The candidate cannot
    # replace it with its own derived digest; no publication integration claim.
    trusted_record = probe.root / "trusted-admission.json"
    trusted_record.write_text(json.dumps({"record_digest": basis.record_digest}))
    candidate = json.loads(basis.to_json())
    candidate["recipe_json"] = json.dumps(json.loads(candidate["recipe_json"]), indent=2)
    changed = GleanBasis.from_json(json.dumps(candidate))
    admitted_digest = json.loads(trusted_record.read_text())["record_digest"]
    assert changed.record_digest != admitted_digest
    assert changed.recipe_digest == basis.recipe_digest
    assert changed.observed_state == basis.observed_state
    assert probe.open_consistent(changed) == changed
    with pytest.raises(BasisFailure, match="^independent admission digest required$"):
        probe.open_admitted(changed)
    with pytest.raises(BasisFailure, match="^admitted basis record mismatch$"):
        probe.open_admitted(changed, admitted_digest)
    assert probe.open_admitted(GleanBasis.from_json(basis.to_json()), admitted_digest) == basis


@pytest.fixture
def typed_probe(composed, monkeypatch):
    basis, _, _ = composed
    probe = CppProbe.__new__(CppProbe)
    file = {"id": 1025, "key": "target.cpp"}
    function = (FUNCTION_PREDICATE, 1035)
    unit = {"id": 1043, "key": {"file": file}}
    facts = {function, ("src.File", file["id"]), (UNIT_PREDICATE, unit["id"])}
    # Model selected native answers only. The executable probe independently
    # checks the real Glean facts; these tests exercise dispatch and dishonesty.
    monkeypatch.setattr(probe, "typed_member", lambda basis, predicate, local_id:
                        (predicate, local_id) in facts)

    def query(basis, text):
        if text.startswith("codemarkup.cxx.CxxDeclKind"):
            return [{"key": {"decl": {"function_": {"id": function[1]}}, "kind": 13}}]
        if text.startswith("cxx1.DeclarationSrcRange"):
            return [{"key": {"source": {"file": file}}}]
        if text.startswith("cxx1.TranslationUnitTrace"):
            return [{"key": {"tunit": unit, "trace": {"key": {"file": file}}}}]
        raise AssertionError("unexpected modeled query")

    monkeypatch.setattr(probe, "query", query)
    return probe, basis, probe.context(basis, function)


def test_actual_context_tokens_have_membership_kind_and_distinct_evidence(typed_probe):
    probe, basis, context = typed_probe
    results = check_context_closure(probe, basis, context)
    assert [(row["is_member"], row["kind"]) for row in results] == [
        (True, "translation_unit"), (True, "source_unit"), (True, "callable")]
    assert probe.observations(basis, context["unit"]) == ()
    assert probe.observations(basis, context["file"]) == ()


@pytest.mark.parametrize("token", [
    (FUNCTION_PREDICATE, 1025), ("src.File", 1035), (UNIT_PREDICATE, 999999999),
    ("src.IndexFailure", 1025), 1035, (FUNCTION_PREDICATE, True),
])
def test_wrongly_typed_unknown_or_unadmitted_tokens_are_not_members(typed_probe, token):
    probe, basis, _ = typed_probe
    assert not probe.member(basis, token)
    assert probe.kind(basis, token) is None
    assert probe.context(basis, token) == {}
    assert probe.observations(basis, token) == ()


@pytest.mark.parametrize("dishonest_method,message", [
    ("member", "containment endpoint is not a program member"),
    ("kind", "containment endpoint kind mismatch"),
])
def test_function_only_reader_fails_context_closure(typed_probe, monkeypatch, dishonest_method, message):
    probe, basis, context = typed_probe
    honest = getattr(probe, dishonest_method)
    monkeypatch.setattr(probe, dishonest_method, lambda basis, token:
                        honest(basis, token) if token[0] == FUNCTION_PREDICATE
                        else False if dishonest_method == "member" else None)
    with pytest.raises(AssertionError, match=f"^{message}$"):
        check_context_closure(probe, basis, context)


def test_containment_must_preserve_exact_endpoint_tokens_and_roles(typed_probe):
    probe, basis, context = typed_probe
    for dishonest_edges in (
        ({"parent": context["file"], "child": context["unit"]}, context["edges"][1]),
        (context["edges"][0], {"parent": context["file"], "child": context["function"][1]}),
    ):
        with pytest.raises(AssertionError, match="^containment endpoint/role mismatch$"):
            check_context_closure(probe, basis, {**context, "edges": dishonest_edges})


def test_equal_local_token_does_not_qualify_another_occurrence(typed_probe):
    probe, basis, context = typed_probe
    independent = replace(basis, occurrence=replace(basis.occurrence, guid="independent-guid"))
    token = context["function"]
    assert probe.member(basis, token) and probe.member(independent, token)
    assert (basis.occurrence, token) != (independent.occurrence, token)
    with pytest.raises(AssertionError, match="^entity occurrence mismatch$"):
        probe.qualified_member(independent, basis, token)

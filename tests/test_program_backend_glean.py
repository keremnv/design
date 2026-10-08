"""Production reader controls with modeled Glean responses; no runtime claim.

The separate phase6c_glean_backend_probe executes this production reader against
the pinned retained runtime. Existing Phase 5 contracts remain untouched.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import re
import subprocess

import pytest

from ontology_author.program_backend import BackendError, Capability, CapabilityStatus, OccurrenceQualificationError, OptionalUnsupported, ProgramBackend
from ontology_author.program_backend.glean import (
    FILE, FUNCTION, GLEAN_COMMIT, SCHEMA_ID, UNIT, GleanCLI, GleanProgramBackend,
    open_admitted_glean_occurrence, open_glean_occurrence,
)
from ontology_author.program_backend.glean_basis import DBRef, GleanBasis, Input, canonical, sha256
from tests.phase6b_glean_cpp_spike import EXPECTED_FIRST, EXPECTED_SECOND, P1


class ModeledGlean:
    """Small selected native-shaped answers; not a production graph or runtime."""
    namespace = "retained-A"

    def __init__(self, basis):
        self.basis = basis
        self.db = {"repo": basis.occurrence.repo, "status": "COMPLETE", "dependencies": None,
                   "properties": {"glean.guid": basis.occurrence.guid, "glean.schema_id": basis.schema_id,
                                  "glean.server.build_revision": GLEAN_COMMIT,
                                  "phase6b.input_state": basis.input_state, "phase6b.recipe": basis.recipe_digest}}
        self.files = {1025: "target.cpp", 1068: "second.cpp", 1080: "generated.h"}
        self.functions = {1035: 1025, 1075: 1068}
        self.units = {1043: 1025, 1083: 1068}
        self.failure = False
        self.unavailable = False
        self.query_error = False
        self.queries = []
        self.context_substitution = None
        self.source_substitution = None

    def metadata(self, repo):
        if self.unavailable or repo != self.db["repo"]:
            raise BackendError("exact historical DB unavailable")
        return deepcopy(self.db)

    def query(self, repo, text, *, wrong_fact_ok=False):
        assert repo == self.basis.occurrence.repo
        self.queries.append(text)
        if self.query_error:
            raise BackendError("query failed, not nonmembership")
        if text == "src.IndexFailure.1 _":
            return [{"key": {"details": "missing header"}}] if self.failure else []
        if text == "digest.FileDigest.1 _":
            return [{"key": {"file": {"key": item.file}, "digest": {
                "hash": hashlib.sha1(P1[item.file].encode()).hexdigest(), "size": item.size}}}
                for item in self.basis.inputs]
        selected = re.match(r"D where D = \(\$(\d+) : (\S+)\);", text)
        if selected:
            assert wrong_fact_ok
            local_id, predicate = int(selected[1]), selected[2]
            facts = {"cxx1.FunctionDeclaration.5": self.functions, "src.File.1": self.files,
                     "buck.TranslationUnit.4": self.units}[predicate]
            return [{"id": local_id}] if local_id in facts else []
        local_id = int(re.search(r"\$(\d+)", text)[1])
        if text.startswith("codemarkup.cxx.CxxDeclKind.5"):
            return [{"key": {"decl": {"function_": {"id": local_id}}, "kind": 13}}]
        if text.startswith("cxx1.DeclarationSrcRange.5"):
            local_id = self.source_substitution or local_id
            file_id = self.functions[local_id]
            source = {"file": {"id": file_id, "key": self.files[file_id]},
                      "lineBegin": 1, "columnBegin": 14 if local_id == 1035 else 1,
                      "lineEnd": 3 if local_id == 1035 else 2,
                      "columnEnd": 1 if local_id == 1035 else len(EXPECTED_SECOND.encode())}
            if local_id == 1075:
                source["lineBegin"] = 2
            return [{"key": {"decl": {"function_": {"id": local_id}}, "source": source}}]
        if text.startswith("cxx1.TranslationUnitTrace.5"):
            local_id = self.context_substitution or local_id
            file_id = self.functions[local_id]
            unit_id = next(unit for unit, file in self.units.items() if file == file_id)
            file = {"id": file_id, "key": self.files[file_id]}
            return [{"key": {"tunit": {"id": unit_id, "key": {"file": file}},
                             "trace": {"key": {"file": file}}}}]
        if text.startswith("buck.TranslationUnit.4"):
            return [{"id": unit, "key": {"file": {"id": file}}}
                    for unit, file in self.units.items() if file == local_id]
        raise AssertionError(f"unexpected query: {text}")


@pytest.fixture
def retained(tmp_path):
    # Serialized Phase 6B shape; immutable fixture bytes and independent pins.
    runtime = {"glean_commit": GLEAN_COMMIT, "llvm": "15.0.7", "clang": "Ubuntu clang version 15.0.7",
               "hsthrift_commit": "e3c575885f9eda98e3c3aa9a1edd5011b6b14373",
               "binaries": {
                   "glean": "e3a41876326327056120381432cf0287a24a391bdaed29c5ce343462fc2abe63",
                   "clang-index": "d3714fd79c46372306bcfdb6a48c518c98505a735a8e3b884cf951f268a71f5f",
                   "clang-derive": "e3f3ab7a6fe5fac8fcbd5aec14737b66b6fb8afc78f85d4ede1bc93efbece11d",
               }}
    recipe = {"runtime": runtime, "sources": ["second.cpp", "target.cpp"],
              "argv": ["clang++-15", "-std=c++17", "-nostdinc", "-nostdinc++", "-c", "<source>", "-o", "<object>"],
              "indexer": "cpp-cmake --cdb-dir <root> -j1", "source_range_dialect": "clang-byte-columns-inclusive"}
    blobs = tmp_path / "blobs"
    blobs.mkdir()
    items = []
    for file, text in sorted(P1.items()):
        data = text.encode()
        item = Input(file, sha256(data), len(data))
        (blobs / item.sha256).write_bytes(data)
        items.append(item)
    basis = GleanBasis(DBRef("retained-A", "fixture/P1", "p1-guid"), SCHEMA_ID,
                       tuple(items), canonical(recipe).decode())
    return basis, ModeledGlean(basis), blobs


def opened(retained):
    basis, client, blobs = retained
    return open_admitted_glean_occurrence(basis, admitted_digest=basis.record_digest, client=client, blobs=blobs)


def test_production_contract_typed_endpoint_closure_and_selected_evidence(retained):
    basis, client, _ = retained
    with opened(retained) as reader:
        assert isinstance(reader, ProgramBackend)
        target = (FUNCTION, 1035)
        edges = reader.containment(target)
        assert edges == ({"parent": (UNIT, 1043), "child": (FILE, 1025)},
                         {"parent": (FILE, 1025), "child": target})
        tokens = (edges[0]["parent"], edges[0]["child"], edges[1]["child"])
        for token, kind in zip(tokens, ("translation_unit", "source_unit", "callable")):
            assert reader.is_member(token)
            assert reader.kind(token) == kind
        assert reader.containment(tokens[0]) == ()
        assert reader.containment(tokens[1]) == edges[:1]
        assert reader.observations(tokens[0]) == reader.observations(tokens[1]) == ()
        assert reader.snapshot() == basis.observed_state
        observation = reader.observations(target)[0]
        assert reader.reconstruct(json.loads(json.dumps(observation))) == (EXPECTED_FIRST, True)
        assert reader.verify() == ()
        with pytest.raises(OptionalUnsupported):
            reader.discover()
        assert all("--latest" not in query for query in client.queries)
    with pytest.raises(BackendError, match="closed"):
        reader.is_member(target)


@pytest.mark.parametrize("token", [(FUNCTION, 1025), (FILE, 1035), (UNIT, 999999999),
                                  ("src.IndexFailure", 1025), 1035, (FUNCTION, True), (FUNCTION, -1)])
def test_wrong_type_unknown_and_unadmitted_tokens(retained, token):
    with opened(retained) as reader:
        assert not reader.is_member(token)
        assert reader.kind(token) is None
        assert reader.containment(token) == reader.observations(token) == ()
        assert reader.invocations(token) == reader.resolutions(token) == ()


@pytest.mark.parametrize("field,value", [("glean.guid", "recreated"), ("glean.schema_id", "wrong"),
                                        ("phase6b.input_state", "wrong"), ("phase6b.recipe", "wrong"),
                                        ("glean.server.build_revision", "wrong")])
def test_open_and_live_handle_reject_changed_native_qualification(retained, field, value):
    _, client, _ = retained
    reader = opened(retained)
    client.db["properties"][field] = value
    with pytest.raises(OccurrenceQualificationError, match="qualification mismatch"):
        opened(retained)
    with pytest.raises(OccurrenceQualificationError, match="qualification mismatch"):
        reader.is_member((FUNCTION, 1035))
    assert reader.verify()


@pytest.mark.parametrize("failure", ["missing_db", "wrong_namespace", "stacked", "pruned", "incomplete"])
def test_exact_open_failure_is_not_nonmembership_or_latest(retained, failure):
    _, client, _ = retained
    reader = opened(retained)
    if failure == "missing_db":
        client.unavailable = True
    elif failure == "wrong_namespace":
        client.namespace = "another-retained-store"
    elif failure in {"stacked", "pruned"}:
        client.db["dependencies"] = {failure: "base"}
    else:
        client.db["status"] = "INCOMPLETE"
    with pytest.raises(BackendError):
        reader.is_member((FUNCTION, 1035))
    with pytest.raises(BackendError):
        opened(retained)


def test_db_complete_with_index_failure_is_refused(retained):
    _, client, _ = retained
    client.failure = True
    assert client.db["status"] == "COMPLETE"
    with pytest.raises(OccurrenceQualificationError, match="indexer reports file failures"):
        opened(retained)


def test_independent_equal_input_db_has_distinct_identity(retained):
    basis, _, blobs = retained
    other = replace(basis, occurrence=replace(basis.occurrence, repo="fixture/P1independent", guid="other-guid"))
    with opened(retained) as left, open_glean_occurrence(other, client=ModeledGlean(other), blobs=blobs) as right:
        assert left.snapshot() == right.snapshot()
        assert left.is_member((FUNCTION, 1035)) and right.is_member((FUNCTION, 1035))
        assert (basis.occurrence, (FUNCTION, 1035)) != (other.occurrence, (FUNCTION, 1035))
        observation = left.observations((FUNCTION, 1035))[0]
        assert right.reconstruct(observation) == ("", False)
    with pytest.raises(OccurrenceQualificationError, match="admitted basis record mismatch"):
        open_admitted_glean_occurrence(other, admitted_digest=basis.record_digest, client=ModeledGlean(other), blobs=blobs)


@pytest.mark.parametrize("digest", [None, "", "wrong"])
def test_admission_requires_external_pin(retained, digest):
    basis, client, blobs = retained
    with pytest.raises(OccurrenceQualificationError, match="admission digest required|admitted basis record mismatch"):
        open_admitted_glean_occurrence(basis, admitted_digest=digest, client=client, blobs=blobs)


def test_admission_cannot_omit_pin_or_inherit_candidate_digest(retained):
    basis, client, blobs = retained
    with pytest.raises(OccurrenceQualificationError, match="independent admission digest required"):
        open_admitted_glean_occurrence(basis, client=client, blobs=blobs)


@pytest.mark.parametrize("dishonest_method,message", [
    ("is_member", "containment endpoint is not a program member"),
    ("kind", "containment endpoint kind mismatch"),
])
def test_dishonest_function_only_public_dispatch_is_detected(retained, monkeypatch, dishonest_method, message):
    reader = opened(retained)
    edges = reader.containment((FUNCTION, 1035))
    honest = getattr(reader, dishonest_method)
    monkeypatch.setattr(reader, dishonest_method, lambda token:
                        honest(token) if token[0] == FUNCTION
                        else False if dishonest_method == "is_member" else None)
    with pytest.raises(AssertionError, match=re.escape(message)):
        for token, kind in zip((edges[0]["parent"], edges[0]["child"], edges[1]["child"]),
                               ("translation_unit", "source_unit", "callable")):
            assert reader.is_member(token), "containment endpoint is not a program member"
            assert reader.kind(token) == kind, "containment endpoint kind mismatch"


def test_equivalent_recipe_self_consistency_cannot_replace_saved_admission(retained, tmp_path):
    basis, client, blobs = retained
    trusted = tmp_path / "trusted-admission.json"
    trusted.write_text(json.dumps({"digest": basis.record_digest}))
    candidate = json.loads(basis.to_json())
    candidate["recipe_json"] = json.dumps(json.loads(candidate["recipe_json"]), indent=2)
    changed = GleanBasis.from_json(json.dumps(candidate))
    digest = json.loads(trusted.read_text())["digest"]
    assert changed.recipe_digest == basis.recipe_digest
    assert changed.record_digest != digest
    with open_glean_occurrence(changed, client=client, blobs=blobs) as reader:
        assert reader.verify() == ()
    with pytest.raises(OccurrenceQualificationError, match="admitted basis record mismatch"):
        open_admitted_glean_occurrence(changed, admitted_digest=digest, client=client, blobs=blobs)
    assert opened(retained).verify() == ()


@pytest.mark.parametrize("damage", ["missing", "corrupt", "wrong_size", "symlink", "missing_generated"])
def test_damaged_retention_never_reconstructs_verified_or_borrows_workspace(retained, tmp_path, damage):
    basis, _, blobs = retained
    reader = opened(retained)
    observation = reader.observations((FUNCTION, 1035))[0]
    item = next(i for i in basis.inputs if i.file == ("generated.h" if damage == "missing_generated" else "target.cpp"))
    blob = blobs / item.sha256
    if damage in {"corrupt", "wrong_size"}:
        blob.write_bytes(b"x" * (item.size if damage == "corrupt" else item.size + 1))
    else:
        data = blob.read_bytes()
        blob.unlink()
        live = tmp_path / "target.cpp"
        live.write_bytes(data)
        if damage == "symlink":
            blob.symlink_to(live)
    if damage != "missing_generated":
        assert reader.reconstruct(observation) == ("", False)
    assert reader.verify()
    with pytest.raises(BackendError):
        opened(retained)


def assert_material(reader, token, expected):
    handles = reader.observations(token)
    assert len(handles) == 1
    material, verified = reader.reconstruct(handles[0])
    assert verified
    assert material == expected, "evidence belongs to another member"


def test_valid_other_member_evidence_does_not_satisfy_selected_manifestation(retained, monkeypatch):
    reader = opened(retained)
    target, second = (FUNCTION, 1035), (FUNCTION, 1075)
    assert_material(reader, target, EXPECTED_FIRST)
    assert_material(reader, second, EXPECTED_SECOND)
    other = reader.observations(second)
    monkeypatch.setattr(reader, "observations", lambda token: other)
    with pytest.raises(AssertionError, match="evidence belongs to another member"):
        assert_material(reader, target, EXPECTED_FIRST)


@pytest.mark.parametrize("substitution", ["source", "context"])
def test_selected_fact_associations_reject_other_valid_native_entity(retained, substitution):
    _, client, _ = retained
    reader = opened(retained)
    if substitution == "source":
        client.source_substitution = 1075
        with pytest.raises(OccurrenceQualificationError, match="selected declaration evidence mismatch"):
            reader.observations((FUNCTION, 1035))
    else:
        client.context_substitution = 1075
        with pytest.raises(OccurrenceQualificationError, match="context outside single-main-file"):
            reader.containment((FUNCTION, 1035))


@pytest.mark.parametrize("family", ["kind", "containment", "evidence", "invocation", "resolution"])
def test_requested_family_honesty_and_wrong_family_substitution(retained, monkeypatch, family):
    basis, _, _ = retained
    reader = opened(retained)
    # Independent requested-family policy, not an expectation copied from the getter.
    scopes = {
        "kind": ("typed global functions and ownership endpoints in declared inputs", ("other AST categories not normalized",)),
        "containment": ("main-file translation-unit/file/function ownership", ("headers and lexical scope not a tree",)),
        "evidence": ("selected declaration ranges in retained indexed UTF-8 bytes", ("other locator/encoding forms unproven",)),
        "invocation": ("initial C++ core recipe", ("xref is not syntactic call proof",)),
        "resolution": ("initial C++ core recipe", ("call-resolution outcomes not produced",)),
    }
    scope, gaps = scopes[family]
    expected = Capability(CapabilityStatus.NOT_PRODUCED if family in {"invocation", "resolution"} else CapabilityStatus.INCOMPLETE,
                          scope, f"{family}: recipe={basis.recipe_digest}; schema={basis.schema_id}", gaps)
    assert reader.capability(family) == expected
    other_family = "kind" if family != "kind" else "containment"
    other = reader.capability(other_family)
    monkeypatch.setattr(reader, "capability", lambda requested: other)
    with pytest.raises(AssertionError, match="qualification belongs to another family"):
        assert reader.capability(family) == expected, "qualification belongs to another family"


def test_optional_and_unknown_services_and_query_errors(retained):
    _, client, _ = retained
    reader = opened(retained)
    assert reader.invocations((FUNCTION, 1035)) == reader.resolutions((FUNCTION, 1035)) == ()
    with pytest.raises(OccurrenceQualificationError, match="unsupported capability family"):
        reader.capability("invented")
    client.query_error = True
    with pytest.raises(BackendError, match="query failed, not nonmembership"):
        reader.is_member((FUNCTION, 1035))


@pytest.mark.parametrize("returncode,stderr,stdout,wrong_ok,expected", [
    (0, "glean: BadQuery schema error\n", "", True, "error"),
    (1, "glean: fact has the wrong type\n", "", True, []),
    (0, "glean: fact has the wrong type\n", "", True, []),
    (1, "glean: fact has the wrong type\n", "", False, "error"),
    (0, "glean: fact has the wrong type\n", '{"id": 1}\n', True, "error"),
    (0, "", "not JSON", False, "error"),
    (0, "", '{"id": 1}\n{"id": 2}\n', False, [{"id": 1}, {"id": 2}]),
])
def test_cli_exact_read_only_error_and_rows_boundary(monkeypatch, returncode, stderr, stdout, wrong_ok, expected):
    observed = []
    def run(command, **kwargs):
        observed.append(command)
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)
    monkeypatch.setattr(subprocess, "run", run)
    client = GleanCLI(["glean", "--db-root", "/retained"], namespace="retained-A")
    if expected == "error":
        with pytest.raises(BackendError):
            client.query("fixture/P1", "selected", wrong_fact_ok=wrong_ok)
    else:
        assert client.query("fixture/P1", "selected", wrong_fact_ok=wrong_ok) == expected
    assert observed == [["glean", "--db-root", "/retained", "--db-read-only", "query", "--db", "fixture/P1", "--expand", "selected"]]


@pytest.mark.parametrize("failure", [OSError("missing CLI"), subprocess.TimeoutExpired("glean", 1)])
def test_cli_transport_unavailable_is_explicit(monkeypatch, failure):
    def run(*args, **kwargs):
        raise failure
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(BackendError, match="service unavailable"):
        GleanCLI(["glean"], namespace="retained-A").metadata("fixture/P1")


def test_recipe_and_native_digest_cannot_borrow_valid_basis(retained):
    basis, client, blobs = retained
    recipe = json.loads(basis.recipe_json)
    recipe["argv"][1] = "-std=c++20"
    changed = replace(basis, recipe_json=json.dumps(recipe))
    with pytest.raises(OccurrenceQualificationError, match=re.escape("unsupported C++ indexer recipe")):
        open_glean_occurrence(changed, client=client, blobs=blobs)
    changed = replace(basis, inputs=tuple(replace(i, size=i.size + 1) if i.file == "generated.h" else i for i in basis.inputs))
    with pytest.raises(OccurrenceQualificationError):
        open_glean_occurrence(changed, client=client, blobs=blobs)


@pytest.mark.parametrize("observation", [None, {}, {"basis_digest": "foreign"}])
def test_unqualified_observation_does_not_verify(retained, observation):
    assert opened(retained).reconstruct(observation) == ("", False)


@pytest.mark.parametrize("damage", ["hash", "size", "path", "duplicate", "missing_generated"])
def test_native_input_inventory_is_independent_of_declared_properties(retained, monkeypatch, damage):
    _, client, _ = retained
    original = client.query
    def query(repo, text, **kwargs):
        rows = original(repo, text, **kwargs)
        if text == "digest.FileDigest.1 _":
            if damage == "hash":
                rows[0]["key"]["digest"]["hash"] = "declared SHA-256 is not native SHA-1"
            elif damage == "size":
                rows[0]["key"]["digest"]["size"] += 1
            elif damage == "path":
                rows[0]["key"]["file"]["key"] = "other/generated.h"
            elif damage == "duplicate":
                rows.append(deepcopy(rows[0]))
            else:
                rows = [row for row in rows if row["key"]["file"]["key"] != "generated.h"]
        return rows
    monkeypatch.setattr(client, "query", query)
    with pytest.raises(OccurrenceQualificationError, match="indexed input inventory mismatch|native indexed digest/size mismatch"):
        opened(retained)


@pytest.mark.parametrize("field,value", [("lineBegin", 0), ("columnBegin", "14"),
                                        ("lineEnd", 1000), ("columnEnd", -1)])
def test_native_invalid_range_cannot_reconstruct_as_verified(retained, monkeypatch, field, value):
    _, client, _ = retained
    reader = opened(retained)
    original = client.query
    def query(repo, text, **kwargs):
        rows = original(repo, text, **kwargs)
        if text.startswith("cxx1.DeclarationSrcRange.5"):
            rows[0]["key"]["source"][field] = value
        return rows
    monkeypatch.setattr(client, "query", query)
    assert reader.reconstruct(reader.observations((FUNCTION, 1035))[0]) == ("", False)


@pytest.mark.parametrize("field", ["schema", "dependencies", "runtime_binary", "dialect", "extra_recipe"])
def test_unproved_schema_recipe_and_dependency_forms_are_refused(retained, field):
    basis, client, blobs = retained
    recipe = json.loads(basis.recipe_json)
    if field == "schema":
        changed = replace(basis, schema_id="different-schema")
    elif field == "dependencies":
        changed = replace(basis, dependencies=(DBRef("retained-A", "fixture/base", "base-guid"),))
    else:
        if field == "runtime_binary":
            recipe["runtime"]["binaries"]["clang-index"] = "another-indexer"
        elif field == "dialect":
            recipe["source_range_dialect"] = "unicode-codepoints"
        else:
            recipe["unproved_transformation"] = "rewrite inputs"
        changed = replace(basis, recipe_json=json.dumps(recipe))
    with pytest.raises(OccurrenceQualificationError):
        open_glean_occurrence(changed, client=client, blobs=blobs)

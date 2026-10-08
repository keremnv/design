"""Manual production ProgramBackend conformance on a retained Phase 6B store.

Requires the existing fingerprinted runtime/container. It performs read-only DB
queries, writes no program graph and leaves the retained artifacts unchanged.
Run: uv run python -m tests.phase6c_glean_backend_probe --work CACHE --store STORE
The trusted-admission.json is explicitly a modeled admission pin, not an
Ontology Author accepted publication.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from ontology_author.program_backend import BackendError, CapabilityStatus, OccurrenceQualificationError, OptionalUnsupported, ProgramBackend
from ontology_author.program_backend.glean import (
    FILE, FUNCTION, UNIT, GleanCLI, open_admitted_glean_occurrence, open_glean_occurrence,
)
from ontology_author.program_backend.glean_basis import GleanBasis


FIRST = "int target(int x) {\r\n  return x + 1;\r\n}"
SECOND = "int second(int x) { return x + generated_offset; }"


def rejected(operation, error):
    try:
        operation()
    except error:
        return
    raise AssertionError("dishonest substitution accepted")


def material(reader, token, expected):
    observations = reader.observations(token)
    assert len(observations) == 1
    result, verified = reader.reconstruct(observations[0])
    assert verified
    assert result == expected, "evidence belongs to another member"
    return observations[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--container", default="design-phase6b-build")
    args = parser.parse_args()
    work, root = args.work.resolve(), args.store.resolve()
    runtime = json.loads((work / "runtime.json").read_text())
    for name, expected in runtime["binaries"].items():
        actual = subprocess.check_output(["docker", "exec", args.container, "sha256sum", "/work/runtime/" + name], text=True).split()[0]
        assert actual == expected, "runtime artifact mismatch"
    for path, expected in runtime["shared_libraries"].items():
        actual = subprocess.check_output(["docker", "exec", args.container, "sha256sum", path], text=True).split()[0]
        assert actual == expected, "runtime shared library mismatch"
    namespace = json.loads((root / "namespace.json").read_text())
    command = ["docker", "exec", "-w", "/work/Glean", args.container, "env", "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
               "LD_LIBRARY_PATH=/work/hsthrift-installed/lib:/work/hsthrift-installed/lib64", "/work/runtime/glean",
               "--db-root", "/work/" + (root / "db").relative_to(work).as_posix(),
               "--schema", "dir:/work/Glean/glean/schema/source"]
    client = GleanCLI(command, namespace=namespace)
    p1 = GleanBasis.from_json(next(root.glob("P1.*.basis.json")).read_text())
    p2 = GleanBasis.from_json(next(root.glob("P2.*.basis.json")).read_text())
    admitted = json.loads((root / "trusted-admission.json").read_text())["record_digest"]

    def selected(basis, name):
        rows = client.query(basis.occurrence.repo,
                            "cxx1.FunctionDeclaration.5 { name = { name = { name = cxx1.Name.5 " + json.dumps(name) + " } } }")
        assert len(rows) == 1
        return FUNCTION, rows[0]["id"]

    with open_admitted_glean_occurrence(p1, admitted_digest=admitted, client=client, blobs=root / "blobs") as reader:
        assert isinstance(reader, ProgramBackend)
        assert reader.snapshot() == p1.observed_state
        e1, e2 = selected(p1, "target"), selected(p1, "second")
        edges = reader.containment(e1)
        assert len(edges) == 2 and edges[1]["child"] == e1 and edges[0]["child"] == edges[1]["parent"]
        tokens = (edges[0]["parent"], edges[0]["child"], edges[1]["child"])
        closure = []
        for token, kind in zip(tokens, ("translation_unit", "source_unit", "callable")):
            assert reader.is_member(token) and reader.kind(token) == kind
            closure.append({"token": token, "is_member": True, "kind": kind})
        assert tokens[0][0] == UNIT and tokens[1][0] == FILE
        assert reader.containment(tokens[0]) == () and reader.containment(tokens[1]) == edges[:1]
        assert reader.observations(tokens[0]) == reader.observations(tokens[1]) == ()
        for token in ((FUNCTION, tokens[1][1]), (FILE, e1[1]), (FUNCTION, 999999999)):
            assert not reader.is_member(token) and reader.kind(token) is None
            assert reader.containment(token) == reader.observations(token) == ()
        first_observation = material(reader, e1, FIRST)
        second_observation = material(reader, e2, SECOND)
        with patch.object(reader, "observations", return_value=(second_observation,)):
            rejected(lambda: material(reader, e1, FIRST), AssertionError)
        e2_edges = reader.containment(e2)
        assert e2_edges != edges
        assert reader.reconstruct(json.loads(json.dumps(first_observation))) == (FIRST, True)
        assert not reader.reconstruct({**first_observation, "source_sha256": "wrong"})[1]
        for family in ("kind", "containment", "evidence", "invocation", "resolution"):
            expected = reader.capability(family)
            assert expected.status == (CapabilityStatus.NOT_PRODUCED if family in {"invocation", "resolution"} else CapabilityStatus.INCOMPLETE)
            assert expected.basis.startswith(family + ":") and expected.scope and expected.gaps
            other = reader.capability("kind" if family != "kind" else "containment")
            with patch.object(reader, "capability", return_value=other):
                def correct_family():
                    assert reader.capability(family) == expected, "qualification belongs to another family"
                rejected(correct_family, AssertionError)
        assert reader.invocations(e1) == reader.resolutions(e1) == ()
        rejected(lambda: reader.discover(), OptionalUnsupported)
        assert reader.verify() == ()

    # The original workspace is already deleted; every byte above was retained.
    assert all(not (root / name).exists() for name in ("P1", "P1independent", "P2"))
    with open_glean_occurrence(p2, client=client, blobs=root / "blobs") as newer:
        e_new = selected(p2, "target")
        assert "x + 41" in newer.reconstruct(newer.observations(e_new)[0])[0]
        assert newer.reconstruct(first_observation) == ("", False)
    with open_admitted_glean_occurrence(p1, admitted_digest=admitted, client=client, blobs=root / "blobs") as reopened:
        assert reopened.containment(e1) == edges
        assert reopened.observations(e1) == (first_observation,)
        assert reopened.reconstruct(first_observation) == (FIRST, True)

    changed = replace(p1, recipe_json=json.dumps(json.loads(p1.recipe_json), indent=2))
    assert changed.recipe_digest == p1.recipe_digest and changed.record_digest != admitted
    with open_glean_occurrence(changed, client=client, blobs=root / "blobs") as consistent:
        assert consistent.verify() == ()
    rejected(lambda: open_admitted_glean_occurrence(changed, admitted_digest=admitted, client=client, blobs=root / "blobs"), OccurrenceQualificationError)
    rejected(lambda: open_admitted_glean_occurrence(p1, admitted_digest=None, client=client, blobs=root / "blobs"), OccurrenceQualificationError)
    rejected(lambda: open_glean_occurrence(p1, client=GleanCLI(command, namespace="wrong-store"), blobs=root / "blobs"), OccurrenceQualificationError)
    rejected(lambda: open_glean_occurrence(replace(p1, occurrence=replace(p1.occurrence, repo="phase6b/missing")), client=client, blobs=root / "blobs"), BackendError)
    rejected(lambda: client.query(p1.occurrence.repo, "unavailable.Predicate.999 _", wrong_fact_ok=True), BackendError)

    # The old independent Repo was recreated by Phase 6B. Its stale GUID must
    # fail, while the current independent record opens with equal local tokens.
    independent_refs = [GleanBasis.from_json(path.read_text()) for path in root.glob("P1independent.*.basis.json")]
    actual_guid = client.metadata("phase6b/P1independent")["properties"]["glean.guid"]
    independent = next(b for b in independent_refs if b.occurrence.guid == actual_guid)
    stale = next(b for b in independent_refs if b.occurrence.guid != actual_guid)
    rejected(lambda: open_glean_occurrence(stale, client=client, blobs=root / "blobs"), OccurrenceQualificationError)
    with open_glean_occurrence(independent, client=client, blobs=root / "blobs") as other:
        endpoint_sets = []
        for name in ("target", "second"):
            chain = other.containment(selected(independent, name))
            endpoint_sets.extend(row[role] for row in chain for role in ("parent", "child"))
        p1_endpoints = [row[role] for row in (*edges, *e2_edges) for role in ("parent", "child")]
        collision = next(token for token in p1_endpoints if token in endpoint_sets)
        assert other.is_member(collision)
        assert (p1.occurrence, collision) != (independent.occurrence, collision)
        assert other.reconstruct(first_observation) == ("", False)

    failure = client.query("phase6b/MissingInclude", "src.IndexFailure.1 _")
    assert client.metadata("phase6b/MissingInclude")["status"] == "COMPLETE" and failure
    print(json.dumps({"result": "PASS", "glean_commit": runtime["glean_commit"], "schema_id": p1.schema_id,
                      "store": str(root), "typed_closure": closure, "colliding_local_token": collision,
                      "history_after_P2": True, "workspace_absent": True,
                      "admission": "external modeled pin; consistency confers no admission",
                      "preserved_missing_include": "COMPLETE with src.IndexFailure",
                      "not_proven": ["publication migration", "stacked/pruned runtime", "backup/restore", "deployment retention", "broader C++"]}, indent=2))


if __name__ == "__main__":
    main()

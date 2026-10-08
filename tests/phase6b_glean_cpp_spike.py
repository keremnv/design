"""Manual current-source C++ conformance spike; NOT a production ProgramBackend.

Requires the pinned build described in the Phase 6B document. Run from repo root:
  uv run python -m tests.phase6b_glean_cpp_spike --work /path/to/runtime-cache
Only test artifacts under WORK/spike are modified. No semantic publication is
migrated. The retained store holds bytes and qualification, not a second graph.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid

from tests.phase6b_glean_basis import DBRef, GleanBasis, Input, canonical, checked_blob, sha256, verify_basis

COMMIT = "4e576957778b721f28cec21556066a02c3ed84d0"
UNIT_PREDICATE = "buck.TranslationUnit.4"  # imported by current cxx1.5, not default query scope
P1 = {
    "target.cpp": "/* é😀 */ int target(int x) {\r\n  return x + 1;\r\n}\r\n",
    "second.cpp": '#include "generated.h"\nint second(int x) { return x + generated_offset; }\n',
    "generated.h": "constexpr int generated_offset = 29;\n",
}
P2 = {
    "moved.cpp": "int target(int x) { return x + 41; }\n",
    "second.cpp": '#include "generated.h"\nint second(int x) { return x + generated_offset; }\n',
    "generated.h": "constexpr int generated_offset = 31;\n",
    "extra.cpp": "int extra() { return 77; }\n",
}
EXPECTED_FIRST = "int target(int x) {\r\n  return x + 1;\r\n}"
EXPECTED_SECOND = "int second(int x) { return x + generated_offset; }"


@dataclass(frozen=True)
class Evidence:
    basis_digest: str
    entity: int
    file_id: int
    file: str
    range_json: str
    source_sha256: str


def require_equal(actual, expected):
    assert actual == expected


def rejected(operation):
    try:
        operation()
    except (AssertionError, ValueError, RuntimeError, OSError):
        return
    raise AssertionError("dishonest qualification accepted")


class CppProbe:
    def __init__(self, work: Path, container: str):
        self.work, self.container = work, container
        self.root = work / "spike"
        # Each invocation gets an independent retained store; keep it for review.
        self.root = self.root / uuid.uuid4().hex
        self.root.mkdir(parents=True)
        self.namespace = "phase6b-retained-" + uuid.uuid4().hex
        (self.root / "namespace.json").write_text(json.dumps(self.namespace))
        (self.root / "db").mkdir()
        (self.root / "blobs").mkdir()
        self.runtime = json.loads((work / "runtime.json").read_text())
        assert self.runtime["glean_commit"] == COMMIT
        for name, expected in self.runtime["binaries"].items():
            actual = subprocess.check_output(["docker", "exec", container, "sha256sum", "/work/runtime/" + name], text=True).split()[0]
            assert actual == expected, "runtime artifact mismatch"
        for path, expected in self.runtime["shared_libraries"].items():
            actual = subprocess.check_output(["docker", "exec", container, "sha256sum", path], text=True).split()[0]
            assert actual == expected, "runtime shared library mismatch"

    def inside(self, path: Path) -> str:
        return "/work/" + path.relative_to(self.work).as_posix()

    def command(self, *args, read_only=False, wrong_fact_ok=False):
        cmd = ["docker", "exec", "-w", "/work/Glean", self.container, "env",
               "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
               "LD_LIBRARY_PATH=/work/hsthrift-installed/lib:/work/hsthrift-installed/lib64",
               "PATH=/work/runtime:/work/hsthrift-installed/bin:/usr/local/bin:/usr/bin:/bin",
               "/work/runtime/glean", "--db-root", self.inside(self.root / "db"),
               "--schema", "dir:/work/Glean/glean/schema/source"]
        if read_only:
            cmd += ["--db-read-only"]
        result = subprocess.run(cmd + list(args), capture_output=True, text=True, timeout=180)
        errors = [line for line in result.stderr.splitlines() if line.startswith("glean:")]
        if wrong_fact_ok and errors == ["glean: fact has the wrong type"]:
            return None
        if result.returncode or errors:
            raise RuntimeError(f"Glean {args}: {result.stderr[-3000:]}\n{result.stdout[-1000:]}")
        return result.stdout

    def metadata(self, repo):
        db = json.loads(self.command("status", "--db", repo, "--format", "json", read_only=True))
        # Initial admitted runtime recipe uses standalone DBs only. Decline any
        # unexpected stack/pruned DB; the offline prototype tests closure separately.
        if db.get("dependencies") is not None:
            raise ValueError("non-standalone runtime basis not admitted by this recipe")
        db["dependency_refs"] = []
        return db

    def query(self, basis, text, wrong_fact_ok=False):
        output = self.command("query", "--db", basis.occurrence.repo, "--expand", text,
                              read_only=True, wrong_fact_ok=wrong_fact_ok)
        return [] if output is None else [json.loads(row) for row in output.splitlines() if row]

    def open(self, basis, admitted_digest=None):
        namespace = json.loads((self.root / "namespace.json").read_text())
        verify_basis(basis, admitted_digest or basis.record_digest, namespace,
                     self.metadata, self.root / "blobs")
        return basis

    def produce(self, name, files):
        workspace = self.root / name
        workspace.mkdir()
        items = []
        commands = []
        for file, text in sorted(files.items()):
            data = text.encode()
            (workspace / file).write_bytes(data)
            item = Input(file, sha256(data), len(data))
            (self.root / "blobs" / item.sha256).write_bytes(data)
            items.append(item)
            if file.endswith(".cpp"):
                commands.append({"directory": self.inside(workspace), "file": self.inside(workspace / file),
                                 "arguments": ["/usr/bin/clang++-15", "-std=c++17", "-nostdinc", "-nostdinc++",
                                               "-c", self.inside(workspace / file), "-o", self.inside(workspace / (file + ".o"))]})
        (workspace / "compile_commands.json").write_text(json.dumps(commands))
        # Retain normalized argv and tool identity; absolute run roots are a
        # recorded path mapping, not different program content.
        recipe = {"runtime": self.runtime, "sources": sorted(f for f in files if f.endswith(".cpp")),
                  "argv": ["clang++-15", "-std=c++17", "-nostdinc", "-nostdinc++", "-c", "<source>", "-o", "<object>"],
                  "indexer": "cpp-cmake --cdb-dir <root> -j1", "source_range_dialect": "clang-byte-columns-inclusive"}
        provisional = GleanBasis(DBRef(self.namespace, "phase6b/" + name, "pending"), "pending",
                                 tuple(items), canonical(recipe).decode())
        self.command("index", "--db", provisional.occurrence.repo,
                     "--property", "phase6b.input_state=" + provisional.input_state,
                     "--property", "phase6b.recipe=" + provisional.recipe_digest,
                     "cpp-cmake", self.inside(workspace),
                     "--cdb-dir", self.inside(workspace), "--indexer", "/work/runtime/clang-index",
                     "--deriver", "/work/runtime/clang-derive", "--jobs", "1")
        # index command may finalize; status is checked rather than assuming it.
        db = self.metadata(provisional.occurrence.repo)
        if db["status"] != "COMPLETE":
            self.command("finish", "--db", provisional.occurrence.repo)
            db = self.metadata(provisional.occurrence.repo)
        props = db["properties"]
        assert props["glean.server.build_revision"] == COMMIT
        basis = replace(provisional, occurrence=replace(provisional.occurrence, guid=props["glean.guid"]),
                        schema_id=props["glean.schema_id"])
        assert self.query(basis, "src.FileContent _") == [], "this recipe unexpectedly retains native source content"
        self.verify_indexed_inputs(basis)
        for item in items:
            data = checked_blob(self.root / "blobs", item)
            assert (workspace / item.file).read_bytes() == data
        record = self.root / f"{name}.{basis.occurrence.guid}.basis.json"
        with record.open("x") as output:
            output.write(basis.to_json())
        return self.open(basis)

    def verify_indexed_inputs(self, basis):
        # Admission/independent input verification, not reader enumeration of
        # the entity graph. Properties alone do not prove their declarations.
        assert self.query(basis, "src.IndexFailure _") == [], "indexer reports file failures"
        indexed = self.query(basis, "digest.FileDigest _")
        actual = {row["key"]["file"]["key"]: row["key"]["digest"] for row in indexed}
        assert len(indexed) == len(actual), "conflicting indexed versions of one file"
        assert set(actual) == {item.file for item in basis.inputs}, actual
        for item in basis.inputs:
            data = checked_blob(self.root / "blobs", item)
            assert actual[item.file] == {"hash": hashlib.sha1(data).hexdigest(), "size": item.size}

    def selected(self, basis, name):
        rows = self.query(basis, "cxx1.FunctionDeclaration { name = { name = { name = cxx1.Name " + json.dumps(name) + " } } }")
        assert len(rows) == 1
        return rows[0]["id"]

    def member(self, basis, entity):
        return self.typed_member(basis, "cxx1.FunctionDeclaration", entity)

    def typed_member(self, basis, predicate, entity):
        assert predicate in {"cxx1.FunctionDeclaration", "src.File", UNIT_PREDICATE}
        rows = self.query(basis, f"D where D = (${entity} : {predicate}); D = {predicate} _", True)
        return len(rows) == 1 and rows[0]["id"] == entity

    def qualified_member(self, basis, origin, entity):
        assert origin.occurrence == basis.occurrence and origin.schema_id == basis.schema_id
        assert origin.observed_state == basis.observed_state
        return self.member(basis, entity)

    def kind(self, basis, entity):
        if not self.member(basis, entity):
            return None
        rows = self.query(basis, f"codemarkup.cxx.CxxDeclKind {{ decl = {{ function_ = ${entity} }} }}")
        assert len(rows) == 1 and rows[0]["key"]["decl"]["function_"]["id"] == entity
        assert rows[0]["key"]["kind"] == 13  # Function, declared SymbolKind ordinal
        return "callable"

    def context(self, basis, entity):
        if not self.member(basis, entity):
            return {}
        source = self.query(basis, f"cxx1.DeclarationSrcRange {{ decl = {{ function_ = ${entity} }} }}")
        assert len(source) == 1
        file = source[0]["key"]["source"]["file"]
        units = self.query(basis, "cxx1.TranslationUnitTrace { trace = T } where "
                           f"cxx1.DeclarationInTrace {{ decl = {{ function_ = ${entity} }}, trace = T }}")
        # This fixture selects main-file globals, not header/multi-unit contexts.
        assert len(units) == 1
        key = units[0]["key"]
        assert key["tunit"]["key"]["file"]["id"] == file["id"]
        assert key["trace"]["key"]["file"]["id"] == file["id"]
        assert self.typed_member(basis, "src.File", file["id"])
        assert self.typed_member(basis, UNIT_PREDICATE, key["tunit"]["id"])
        unit = key["tunit"]["id"]
        return {"unit": unit, "file": file["id"], "path": file["key"], "function": entity,
                "kinds": ("translation_unit", "source_unit", self.kind(basis, entity)),
                "edges": ({"parent": (UNIT_PREDICATE, unit), "child": ("src.File", file["id"])},
                          {"parent": ("src.File", file["id"]), "child": ("cxx1.FunctionDeclaration", entity)})}

    def evidence(self, basis, entity):
        rows = self.query(basis, f"cxx1.DeclarationSrcRange {{ decl = {{ function_ = ${entity} }} }}")
        assert len(rows) == 1
        key = rows[0]["key"]
        assert key["decl"]["function_"]["id"] == entity
        loc = key["source"]
        file = loc["file"]
        item = next(item for item in basis.inputs if item.file == file["key"])
        return Evidence(basis.record_digest, entity, file["id"], file["key"], canonical(loc).decode(), item.sha256)

    def observations(self, basis, entity):
        return (self.evidence(basis, entity),) if self.member(basis, entity) else ()

    def invocations(self, basis, entity):
        assert self.capability(basis, "invocation")[0] == "NOT_PRODUCED"
        return ()

    def resolutions(self, basis, entity):
        assert self.capability(basis, "resolution")[0] == "NOT_PRODUCED"
        return ()

    def reconstruct(self, basis, evidence):
        self.open(basis)
        assert evidence.basis_digest == basis.record_digest
        assert evidence == self.evidence(basis, evidence.entity)
        item = next(item for item in basis.inputs if item.file == evidence.file)
        data = checked_blob(self.root / "blobs", item)
        loc = json.loads(evidence.range_json)
        lines = data.splitlines(keepends=True)
        # Current clang implementation uses SourceManager byte columns, unlike
        # src.Range's generic documented Unicode code-point convention.
        def offset(line, column):
            assert 1 <= line <= len(lines) and 1 <= column <= len(lines[line - 1])
            return sum(len(part) for part in lines[:line - 1]) + column - 1
        start = offset(loc["lineBegin"], loc["columnBegin"])
        end = offset(loc["lineEnd"], loc["columnEnd"]) + 1
        assert 0 <= start <= end <= len(data)
        return data[start:end].decode("utf-8")

    def capability(self, basis, family):
        policies = {
            "kind": ("INCOMPLETE", "typed global functions in declared compilation inputs", ("other AST categories not normalized",)),
            "containment": ("INCOMPLETE", "main-file translation-unit/file/function context", ("headers and lexical scope not a tree",)),
            "evidence": ("INCOMPLETE", "selected declaration ranges in retained indexed UTF-8 bytes", ("other locator/encoding forms unproven",)),
            "invocation": ("NOT_PRODUCED", "initial C++ core recipe", ("xref is not syntactic call proof",)),
            "resolution": ("NOT_PRODUCED", "initial C++ core recipe", ("call-resolution outcomes not produced",)),
        }
        status, scope, gaps = policies[family]
        return status, scope, f"{family}: recipe={basis.recipe_digest}; schema={basis.schema_id}", gaps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--container", default="design-phase6b-build")
    args = parser.parse_args()
    probe = CppProbe(args.work.resolve(), args.container)
    p1 = probe.produce("P1", P1)
    admitted_digest = p1.record_digest
    recorded_state = p1.observed_state
    e1, e2 = probe.selected(p1, "target"), probe.selected(p1, "second")
    assert probe.member(p1, e1) and probe.kind(p1, e1) == "callable"
    definitions = probe.query(p1, f"cxx1.FunctionDefinition {{ declaration = ${e1} }}")
    assert len(definitions) == 1 and definitions[0]["key"]["declaration"]["id"] == e1
    assert not probe.member(p1, 999999999)
    assert probe.kind(p1, 999999999) is None and probe.context(p1, 999999999) == {}
    assert probe.observations(p1, 999999999) == ()
    assert probe.invocations(p1, e1) == () and probe.resolutions(p1, e1) == ()
    context = probe.context(p1, e1)
    assert context["path"] == "target.cpp" and context["kinds"] == ("translation_unit", "source_unit", "callable")
    assert not probe.member(p1, context["file"]), "a file fact is not a function declaration"
    observation = probe.evidence(p1, e1)
    assert probe.observations(p1, e1) == (observation,)
    assert probe.reconstruct(p1, observation) == EXPECTED_FIRST
    witness = {"entity_predicate": "cxx1.FunctionDeclaration", "handle": asdict(observation),
               "material_sha256": sha256(EXPECTED_FIRST.encode())}
    witness_path = probe.root / "selected-evidence.json"
    with witness_path.open("x") as output:
        output.write(canonical(witness).decode())
    other = probe.evidence(p1, e2)
    assert probe.reconstruct(p1, other) == EXPECTED_SECOND
    rejected(lambda: require_equal(probe.reconstruct(p1, other), EXPECTED_FIRST))
    rejected(lambda: require_equal(probe.context(p1, e2), context))
    # Name span is separately established, not silently used for full declaration.
    names = probe.query(p1, f"cxx1.DeclarationNameSpan {{ decl = {{ function_ = ${e1} }} }}")
    assert len(names) == 1 and names[0]["key"]["span"]["length"] == len("target")
    assert names[0]["key"]["file"]["id"] == observation.file_id
    name_span = names[0]["key"]["span"]
    source = checked_blob(probe.root / "blobs", next(i for i in p1.inputs if i.file == "target.cpp"))
    assert source[name_span["start"]:name_span["start"] + name_span["length"]] == b"target"
    equivalent = probe.produce("P1independent", P1)
    equivalent_target = probe.selected(equivalent, "target")
    if equivalent_target == e1:
        assert probe.member(p1, e1) and probe.member(equivalent, e1)
    assert equivalent.input_state == p1.input_state
    assert equivalent.observed_state == p1.observed_state
    assert equivalent.occurrence != p1.occurrence and equivalent.occurrence.guid != p1.occurrence.guid
    rejected(lambda: probe.qualified_member(equivalent, p1, e1))
    rejected(lambda: probe.open(replace(p1, occurrence=replace(p1.occurrence, guid=equivalent.occurrence.guid))))
    p2 = probe.produce("P2", P2)
    assert p2.input_state != p1.input_state
    rejected(lambda: probe.open(p2, admitted_digest))  # valid latest basis is not admitted P1
    target2 = probe.selected(p2, "target")
    assert probe.context(p2, target2)["path"] == "moved.cpp"
    assert "x + 41" in probe.reconstruct(p2, probe.evidence(p2, target2))
    assert probe.query(p1, 'cxx1.FunctionDeclaration { name = { name = { name = cxx1.Name "extra" } } }') == []
    rejected(lambda: probe.qualified_member(p1, p2, target2))
    rejected(lambda: probe.qualified_member(p1, replace(p1, inputs=p2.inputs), e1))
    probe.open(p1)
    assert p1.observed_state == recorded_state
    assert probe.kind(p1, e1) == "callable" and probe.context(p1, e1) == context
    assert probe.evidence(p1, e1) == observation and probe.reconstruct(p1, observation) == EXPECTED_FIRST
    # Each stored source is retained even after removing original workspaces.
    (probe.root / "P1" / "target.cpp").write_bytes(b"int target(int x) { return -999; }\n")
    assert probe.reconstruct(p1, observation) == EXPECTED_FIRST
    for name in ("P1", "P1independent", "P2"):
        shutil.rmtree(probe.root / name)
    record = probe.root / f"P1.{p1.occurrence.guid}.basis.json"
    reopened = GleanBasis.from_json(record.read_text())
    assert reopened == p1
    probe.open(reopened, admitted_digest)
    probe.verify_indexed_inputs(reopened)  # independent check without original checkout
    retained_witness = json.loads(witness_path.read_text())
    assert retained_witness["entity_predicate"] == "cxx1.FunctionDeclaration"
    reconstructed_witness = probe.reconstruct(reopened, Evidence(**retained_witness["handle"]))
    assert sha256(reconstructed_witness.encode()) == retained_witness["material_sha256"]
    assert probe.reconstruct(p1, observation) == EXPECTED_FIRST
    # Deliberately damage UNPUBLISHED experimental DBs only. Accepted deployment
    # history must forbid this; the exact opener must detect the resulting loss.
    probe.command("delete", "--db", equivalent.occurrence.repo)
    rejected(lambda: probe.open(equivalent))
    recreated = probe.produce("P1independent", P1)
    assert recreated.occurrence.guid != equivalent.occurrence.guid
    assert recreated.input_state == equivalent.input_state
    rejected(lambda: probe.open(equivalent))
    shutil.rmtree(probe.root / "P1independent")
    for altered in (replace(p1, schema_id="wrong-schema"), replace(p1, recipe_json='{"wrong":"recipe"}'),
                    replace(p1, inputs=p2.inputs), replace(p1, occurrence=replace(p1.occurrence, repo="phase6b/missing"))):
        rejected(lambda altered=altered: probe.open(altered))
    saved_namespace = (probe.root / "namespace.json").read_text()
    (probe.root / "namespace.json").write_text('"other-store"')
    rejected(lambda: probe.open(p1))
    (probe.root / "namespace.json").write_text(saved_namespace)
    rejected(lambda: probe.reconstruct(p1, replace(observation, source_sha256=p2.inputs[0].sha256)))
    blob = probe.root / "blobs" / observation.source_sha256
    data = blob.read_bytes()
    blob.write_bytes(b"mutable workspace fallback")
    rejected(lambda: probe.reconstruct(p1, observation))
    blob.write_bytes(data)
    blob.unlink()
    live = probe.root / "P1"
    live.mkdir()
    (live / "target.cpp").write_bytes(data)  # even correct live bytes cannot repair retention
    rejected(lambda: probe.reconstruct(p1, observation))
    shutil.rmtree(live)
    blob.write_bytes(data)
    # Explicit per-family producer policy; independent fixture expectations.
    expected_families = {
        "kind": ("INCOMPLETE", "typed global functions in declared compilation inputs", ("other AST categories not normalized",)),
        "containment": ("INCOMPLETE", "main-file translation-unit/file/function context", ("headers and lexical scope not a tree",)),
        "evidence": ("INCOMPLETE", "selected declaration ranges in retained indexed UTF-8 bytes", ("other locator/encoding forms unproven",)),
        "invocation": ("NOT_PRODUCED", "initial C++ core recipe", ("xref is not syntactic call proof",)),
        "resolution": ("NOT_PRODUCED", "initial C++ core recipe", ("call-resolution outcomes not produced",)),
    }
    for family, (status, scope, gaps) in expected_families.items():
        expected = status, scope, f"{family}: recipe={p1.recipe_digest}; schema={p1.schema_id}", gaps
        require_equal(probe.capability(p1, family), expected)
        wrong_family = "kind" if family != "kind" else "containment"
        rejected(lambda expected=expected, wrong_family=wrong_family:
                 require_equal(probe.capability(p1, wrong_family), expected))
    for family in ("invocation", "resolution"):
        assert probe.capability(p1, family)[0] == "NOT_PRODUCED"
    # A failed compiler input is not repaired by DB lifecycle finalization.
    rejected(lambda: probe.produce("MissingInclude", {
        "broken.cpp": '#include "absent_generated.h"\nint broken() { return 1; }\n',
    }))
    try:
        failed_db = probe.metadata("phase6b/MissingInclude")
        failure_inventory = {"db_status": failed_db["status"]}
        try:
            raw = probe.command("query", "--db", "phase6b/MissingInclude", "--expand", "src.IndexFailure _", read_only=True)
            failure_inventory["index_failures"] = [json.loads(row) for row in raw.splitlines() if row]
        except RuntimeError:
            failure_inventory["index_failures"] = "query unavailable"
    except RuntimeError:
        failure_inventory = {"db_status": "unavailable"}
    print(json.dumps({"result": "PASS", "glean_commit": COMMIT, "runtime": probe.runtime,
                      "schema_id": p1.schema_id, "store": str(probe.root),
                      "context": context, "full_declaration_material": EXPECTED_FIRST,
                      "equal_source_different_occurrence": True, "history_after_P2": True,
                      "selected_local_ids": {"P1": e1, "P1independent": equivalent_target, "P2": target2},
                      "missing_include_control": failure_inventory,
                      "composition": "standalone retained exact DB + manifest/recipe + source blobs",
                      "not_proven": ["stacked/pruned runtime", "backup restore runtime", "general C++ coverage", "calls/resolution"]}, indent=2))


if __name__ == "__main__":
    main()

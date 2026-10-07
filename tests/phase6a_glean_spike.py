"""Manual Phase 6A probe of real Glean/Flow, outside the pytest/default gate.

Run: uv run python tests/phase6a_glean_spike.py
Requires Docker and the pinned official image below. No mock Glean responses,
production adapter, semantic discovery, or retained run transcripts. This image
predates the source study; the probe proves only its explicitly checked subset.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

IMAGE = "ghcr.io/facebookincubator/glean/demo@sha256:eec9d45a51f7c0bcc8d2260b3e519cd633034851b84cda0bf9d0f91bc8ba6a10"
P1 = {
    "alpha.js": "// @flow\nexport function first(x: number): number { return x + 11; }\n",
    "beta.js": "// @flow\nimport {first} from './alpha';\nexport function second(x: number): number { return first(x) + 22; }\n",
}
P2 = {
    "alpha.js": '// @flow\nexport const first: string = "P2 material";\n',
    "gamma.js": "// @flow\nexport function second(x: number): number { return x + 33; }\n",
    "extra.js": "// @flow\nexport const added: number = 44;\n",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Ref:
    repo: str
    guid: str
    state: str
    schema: str


@dataclass(frozen=True)
class Evidence:
    occurrence: Ref
    entity: int
    file: str
    start: int
    length: int
    content: str


class Probe:
    """CLI-only experimental reads; deliberately NOT a ProgramBackend adapter."""

    def __init__(self, container: str, root: Path):
        self.container = container
        self.root = root
        self.sources: dict[str, dict[str, str]] = {}

    def command(self, *args: str, wrong_fact_ok: bool = False) -> str | None:
        result = subprocess.run(
            ["docker", "exec", self.container, "glean", "--db-root", "/study/db",
             "--schema", "dir:/glean-demo/schema/source", *args],
            capture_output=True, text=True, timeout=90,
        )
        # The image CLI can log a query failure and nevertheless exit zero.
        errors = [line for line in result.stderr.splitlines() if line.startswith("glean:")]
        if wrong_fact_ok and errors == ["glean: fact has the wrong type"]:
            return None
        if result.returncode or errors:
            raise RuntimeError(f"Glean {args}: {result.stderr[-2000:]}")
        return result.stdout

    def query(self, ref: Ref, query: str, wrong_fact_ok: bool = False) -> list[dict]:
        text = self.command("--db-read-only", "query", "--db", ref.repo,
                            "--expand", query, wrong_fact_ok=wrong_fact_ok)
        return [] if text is None else [json.loads(line) for line in text.splitlines() if line]

    def open(self, ref: Ref) -> Ref:
        status = json.loads(self.command("--db-read-only", "status", "--db", ref.repo, "--format", "json"))
        properties = status["properties"]
        assert status["repo"] == ref.repo and status["status"] == "COMPLETE"
        assert properties["glean.guid"] == ref.guid
        assert properties["source_revision"] == ref.state
        assert properties["glean.schema_id"] == ref.schema
        return ref

    def produce(self, name: str, sources: dict[str, str], facts_from: str | None = None) -> Ref:
        project, out = self.root / "project", self.root / name
        if project.exists():
            shutil.rmtree(project)
        project.mkdir()
        (project / ".flowconfig").write_text("[options]\nall=true\n", encoding="utf-8")
        manifest = {}
        for file, text in sources.items():
            data = text.encode("utf-8")
            (project / file).write_bytes(data)
            sha = digest(data)
            (self.root / "blobs" / sha).write_bytes(data)
            manifest[file] = sha
        state = digest(json.dumps(manifest, sort_keys=True).encode())
        self.sources[state] = manifest
        out.mkdir()
        if facts_from:
            for file in (self.root / facts_from).glob("*.json"):
                shutil.copyfile(file, out / file.name)
        else:
            indexed = subprocess.run(
                ["docker", "exec", self.container, "flow", "glean", "/study/project",
                 "--output-dir", f"/study/{name}", "--write-root", "", "--max-workers", "2"],
                capture_output=True, text=True, timeout=90,
            )
            assert indexed.returncode == 0, indexed.stderr
        # Bind retained bytes to exactly the source input passed to this indexer.
        assert all(digest((project / file).read_bytes()) == sha for file, sha in manifest.items())
        files = [f"/study/{name}/{file.name}" for file in sorted(out.glob("*.json"))]
        assert files, "indexer produced no fact files"
        self.command("create", "--db", f"phase6a/{name}", "--property", f"source_revision={state}", *files)
        self.command("derive", "--db", f"phase6a/{name}", "flow.FileDeclaration", "flow.FileXRef")
        self.command("finish", "--db", f"phase6a/{name}")
        properties = json.loads(self.command("properties", "--db", f"phase6a/{name}", "--format", "json"))
        return self.open(Ref(f"phase6a/{name}", properties["glean.guid"], state, properties["glean.schema_id"]))

    def selected(self, ref: Ref, name: str, file: str) -> int:
        rows = self.query(ref, "flow.Declaration { name = flow.Name " + json.dumps(name) +
                          ", loc = { module = flow.Module { file = src.File " + json.dumps(file) + " } } }")
        assert len(rows) == 1
        return rows[0]["id"]

    def member(self, ref: Ref, entity: int) -> bool:
        assert type(entity) is int and entity > 0
        rows = self.query(ref, f"D where D = (${entity} : flow.Declaration); D = flow.Declaration _", True)
        return len(rows) == 1 and rows[0]["id"] == entity

    def context(self, ref: Ref, entity: int) -> dict:
        rows = self.query(ref, "codemarkup.flow.FlowContainsParentEntity "
                          f"{{ child = {{ decl = {{ localDecl = ${entity} }} }} }}")
        assert len(rows) == 1
        key = rows[0]["key"]
        assert key["child"]["decl"]["localDecl"]["id"] == entity
        return key

    def evidence(self, ref: Ref, entity: int) -> Evidence:
        rows = self.query(ref, f"flow.DeclarationLocation {{ decl = {{ localDecl = ${entity} }} }}")
        assert len(rows) == 1
        key = rows[0]["key"]
        assert key["decl"]["localDecl"]["id"] == entity
        file = key["file"]["key"]
        span = key["span"]
        return Evidence(ref, entity, file, span["start"], span["length"], self.sources[ref.state][file])

    def reconstruct(self, ref: Ref, handle: Evidence) -> str:
        assert handle.occurrence == ref
        self.open(ref)
        assert handle == self.evidence(ref, handle.entity), "wrong entity/location/source qualification"
        data = (self.root / "blobs" / handle.content).read_bytes()
        assert digest(data) == handle.content
        assert 0 <= handle.start <= handle.start + handle.length <= len(data)
        return data[handle.start:handle.start + handle.length].decode("utf-8")

    def capability(self, ref: Ref, family: str) -> tuple:
        # This policy is derived by this experiment, not supplied by Glean.
        self.open(ref)
        policies = {
            "containment": ("INCOMPLETE", "file-module ownership",
                            "FlowContainsParentEntity", ("lexical nesting absent",)),
            "invocation": ("NOT_PRODUCED", "Flow declarations/references",
                           "no call-occurrence predicate", ("xref is not a call",)),
        }
        status, scope, basis, gaps = policies[family]
        return status, scope, f"{ref.schema}: {basis}", gaps


def rejected(action) -> None:
    try:
        action()
    except (AssertionError, RuntimeError, FileNotFoundError):
        return
    raise AssertionError("dishonest/unavailable qualification accepted")


def main() -> None:
    container = "design-phase6a-" + uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix="design-phase6a-") as directory:
        root = Path(directory)
        (root / "db").mkdir()
        (root / "blobs").mkdir()
        subprocess.run(["docker", "run", "-d", "--name", container, "--entrypoint", "sleep",
                        "-v", f"{root}:/study", IMAGE, "infinity"], check=True, capture_output=True)
        try:
            probe = Probe(container, root)
            p1 = probe.produce("P1", P1)
            first = probe.selected(p1, "first", "alpha.js")
            second = probe.selected(p1, "second", "beta.js")
            old_context = probe.context(p1, first)
            old_second_context = probe.context(p1, second)
            e1, e2 = probe.evidence(p1, first), probe.evidence(p1, second)
            assert probe.reconstruct(p1, e1) == P1["alpha.js"].split("export ")[1].strip()
            assert probe.reconstruct(p1, e2) == P1["beta.js"].split("export ")[1].strip()
            # Valid evidence for E2 is independently wrong evidence for E1.
            rejected(lambda: expected_material(probe.reconstruct(p1, e2), "first(x: number): number { return x + 11; }", function=True))
            assert old_context["parent"]["module_"]["key"]["file"]["key"] == "alpha.js"
            assert old_second_context["parent"]["module_"]["key"]["file"]["key"] == "beta.js"
            rejected(lambda: expected_material(old_second_context, old_context))
            refs_before = probe.query(p1, "flow.LocalDeclarationReference _")
            kind_before = probe.query(p1, "codemarkup.flow.FlowEntityKind "
                                      f"{{ entity = {{ decl = {{ localDecl = ${first} }} }} }}")[0]["key"]["kind"]
            copy = probe.produce("P1equivalent", P1, facts_from="P1")
            assert p1 != copy and p1.guid != copy.guid and p1.state == copy.state
            assert probe.selected(copy, "first", "alpha.js") == first
            assert probe.member(copy, first)  # raw local token is meaningful in each selected DB
            rejected(lambda: probe.open(replace(copy, guid=p1.guid)))
            rejected(lambda: probe.reconstruct(copy, e1))
            p2 = probe.produce("P2", P2)
            assert p2.state != p1.state
            changed = probe.selected(p2, "first", "alpha.js")
            added = probe.selected(p2, "added", "extra.js")
            kind_after = probe.query(p2, "codemarkup.flow.FlowEntityKind "
                                     f"{{ entity = {{ decl = {{ localDecl = ${changed} }} }} }}")[0]["key"]["kind"]
            assert kind_after == kind_before  # function -> const is lost by this kind mapping
            assert probe.query(p2, "flow.LocalDeclarationReference _") != refs_before
            assert "P2 material" in probe.reconstruct(p2, probe.evidence(p2, changed))
            assert probe.query(p1, 'flow.Declaration { name = flow.Name "added" }') == []
            assert probe.member(p2, added)
            assert not probe.member(p1, 999999999) and not probe.member(p1, e1.start)
            # Independent DBs reuse IDs: find an actual numeric collision.
            # Enumeration here is a diagnostic only; selected membership reads above are keyed.
            a = {r["id"]: r for r in probe.query(p1, "flow.Declaration _")}
            b = {r["id"]: r for r in probe.query(p2, "flow.Declaration _")}
            collisions = [i for i in a.keys() & b.keys() if a[i]["key"] != b[i]["key"]]
            assert collisions, "this run did not demonstrate ID reuse"
            assert probe.member(p1, collisions[0]) and probe.member(p2, collisions[0])
            # Numeric tokens cannot diagnose foreign origin. Qualification can.
            rejected(lambda: qualified_member(probe, p1, p2, collisions[0]))
            probe.open(p1)
            assert probe.context(p1, first) == old_context
            assert probe.context(p1, second) == old_second_context
            assert probe.evidence(p1, first) == e1
            assert probe.query(p1, "flow.LocalDeclarationReference _") == refs_before
            rejected(lambda: probe.open(replace(p1, repo="phase6a/missing")))
            rejected(lambda: probe.open(replace(p1, guid="wrong-guid")))
            rejected(lambda: probe.open(replace(p1, state=p2.state)))
            rejected(lambda: probe.open(replace(p1, schema="wrong-schema")))
            rejected(lambda: probe.reconstruct(p1, replace(e1, occurrence=p2)))
            rejected(lambda: probe.reconstruct(p1, replace(e1, content=probe.sources[p2.state]["alpha.js"])))
            shutil.rmtree(root / "project")
            assert "x + 11" in probe.reconstruct(p1, e1)  # original workspace gone
            blob = root / "blobs" / e1.content
            original = blob.read_bytes()
            blob.write_bytes(b"live mutable bytes")
            rejected(lambda: probe.reconstruct(p1, e1))
            blob.write_bytes(original)
            blob.unlink()
            rejected(lambda: probe.reconstruct(p1, e1))
            # Capability policy is explicit adapter derivation, NOT Glean-supplied completeness.
            expected_containment = (
                "INCOMPLETE", "file-module ownership",
                f"{p1.schema}: FlowContainsParentEntity", ("lexical nesting absent",),
            )
            expected_material(probe.capability(p1, "containment"), expected_containment)
            calls_qualification = probe.capability(p1, "invocation")
            assert calls_qualification[0] == "NOT_PRODUCED"
            rejected(lambda: expected_material(calls_qualification, expected_containment))
            print(json.dumps({
                "image": IMAGE, "runtime_build_commit": "unknown (image property <unknown>)",
                "flow": "0.219.0", "schema_id": p1.schema,
                "checked": ["exact DB open", "distinct equivalent index instances", "state qualification",
                            "keyed membership", "observed numeric ID collisions", "selected parent association",
                            "old reads after P2", "entity-associated full declaration evidence",
                            "wrong entity/revision rejected", "retained reconstruction without workspace",
                            "corrupt/missing retained bytes rejected", "wrong-family policy discriminator"],
                "not_proven": ["current-source runtime", "adequate Flow callable kind", "call-site analysis",
                               "resolution outcomes", "Glean-native capability completeness", "production adapter"],
                "flow_generic_kind_observed": kind_before,
                "flow_generic_kind_after_function_to_const": kind_after,
                "result": "PASS for this subset; NOT full ProgramBackend conformance",
            }, indent=2))
        finally:
            try:
                # Glean in this image writes root-owned files in the task-only mount.
                subprocess.run(["docker", "exec", container, "chown", "-R",
                                f"{os.getuid()}:{os.getgid()}", "/study"],
                               check=True, capture_output=True)
            finally:
                subprocess.run(["docker", "rm", "-f", container], check=True, capture_output=True)


def expected_material(actual, expected, function=False):
    assert actual == ("function " + expected if function else expected)


def qualified_member(probe, opened, origin, entity):
    assert opened == origin, "foreign qualified occurrence"
    return probe.member(opened, entity)


if __name__ == "__main__":
    main()

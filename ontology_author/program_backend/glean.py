"""Selected reads over the retained standalone C++ basis proven in Phase 6B.

Glean supplies indexed structure. Retained blobs supply historical source bytes.
The caller supplies a trusted namespace/CLI endpoint; admission is a separate,
explicitly pinned opening path. No publication or authority is constructed here.
"""
from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
import hashlib
import json
from pathlib import Path
import subprocess

from . import BackendError, Capability, CapabilityStatus, OccurrenceQualificationError, ProgramBackend
from .glean_basis import GleanBasis, canonical, checked_blob

GLEAN_COMMIT = "4e576957778b721f28cec21556066a02c3ed84d0"
SCHEMA_ID = "66a80a62611346b34e2dcaba40d0d58b"
FUNCTION = "cxx1.FunctionDeclaration"
FILE = "src.File"
UNIT = "buck.TranslationUnit.4"
_PREDICATES = {FUNCTION: "cxx1.FunctionDeclaration.5", FILE: "src.File.1", UNIT: UNIT}
_KINDS = {FUNCTION: "callable", FILE: "source_unit", UNIT: "translation_unit"}
_ARGV = ["clang++-15", "-std=c++17", "-nostdinc", "-nostdinc++", "-c", "<source>", "-o", "<object>"]
_BINARIES = {
    "glean": "e3a41876326327056120381432cf0287a24a391bdaed29c5ce343462fc2abe63",
    "clang-index": "d3714fd79c46372306bcfdb6a48c518c98505a735a8e3b884cf951f268a71f5f",
    "clang-derive": "e3f3ab7a6fe5fac8fcbd5aec14737b66b6fb8afc78f85d4ede1bc93efbece11d",
}


class GleanCLI:
    """Trusted exact local CLI endpoint, optionally wrapped by a container runner.

    command includes the pinned executable and store/schema configuration.
    It is an argv prefix, never a shell string. Namespace is independently
    resolved store identity, not copied from an untrusted candidate record.
    The pinned CLI exhausts query continuations without a result limit.
    """

    def __init__(self, command: Sequence[str], *, namespace: str, timeout: float = 180):
        if isinstance(command, str) or not command or not namespace:
            raise ValueError("Glean CLI argv and retained namespace are required")
        self.command = tuple(command)
        self.namespace = namespace
        self.timeout = timeout

    def _run(self, *args: str, wrong_fact_ok: bool = False) -> str | None:
        try:
            result = subprocess.run([*self.command, "--db-read-only", *args],
                                    capture_output=True, text=True, timeout=self.timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BackendError("Glean query service unavailable") from exc
        errors = [line for line in result.stderr.splitlines() if line.startswith("glean:")]
        if (wrong_fact_ok and errors == ["glean: fact has the wrong type"]
                and not result.stdout.strip()):
            return None
        if result.returncode or errors:
            raise BackendError(f"Glean command failed: {result.stderr[-2000:]}")
        return result.stdout

    def metadata(self, repo: str) -> dict:
        try:
            value = json.loads(self._run("status", "--db", repo, "--format", "json"))
            if not isinstance(value, dict):
                raise ValueError("expected metadata object")
            return value
        except (ValueError, TypeError) as exc:
            raise BackendError("malformed Glean metadata") from exc

    def query(self, repo: str, text: str, *, wrong_fact_ok: bool = False) -> list[dict]:
        output = self._run("query", "--db", repo, "--expand", text, wrong_fact_ok=wrong_fact_ok)
        try:
            rows = [] if output is None else [json.loads(row) for row in output.splitlines() if row]
            if any(not isinstance(row, dict) for row in rows):
                raise ValueError("expected fact objects")
            return rows
        except (ValueError, TypeError) as exc:
            raise BackendError("malformed Glean query result") from exc


def open_glean_occurrence(basis: GleanBasis, *, client: GleanCLI, blobs: Path | str) -> GleanProgramBackend:
    """Open a self-consistent candidate basis; confers no publication admission."""
    return GleanProgramBackend(basis, client=client, blobs=blobs)


def open_admitted_glean_occurrence(basis: GleanBasis, *, admitted_digest: str | None = None,
                                  client: GleanCLI, blobs: Path | str) -> GleanProgramBackend:
    """Open against a digest independently retained by the admitting application."""
    if not admitted_digest:
        raise OccurrenceQualificationError("independent admission digest required")
    if basis.record_digest != admitted_digest:
        raise OccurrenceQualificationError("admitted basis record mismatch")
    return GleanProgramBackend(basis, client=client, blobs=blobs, admitted_digest=admitted_digest)


class GleanProgramBackend(ProgramBackend):
    """Bounded C++ reader; local entity identity is (opened handle, typed token)."""

    def __init__(self, basis: GleanBasis, *, client: GleanCLI, blobs: Path | str,
                 admitted_digest: str | None = None):
        self._basis, self._client, self._blobs = basis, client, Path(blobs)
        self._admitted_digest = admitted_digest
        self._closed = False
        try:
            self._validate_recipe()
            self._verify_retained()
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise OccurrenceQualificationError("malformed Glean qualification") from exc

    def close(self) -> None:
        self._closed = True

    def _validate_recipe(self) -> None:
        basis = self._basis
        ref = basis.occurrence
        if (not all(isinstance(value, str) and value for value in (ref.namespace, ref.repo, ref.guid))
                or "/" not in ref.repo or not all(ref.repo.rsplit("/", 1))):
            raise OccurrenceQualificationError("exact namespace/Repo/GUID required")
        if basis.dependencies:
            raise OccurrenceQualificationError("standalone Glean basis required")
        if basis.schema_id != SCHEMA_ID:
            raise OccurrenceQualificationError("unsupported stored C++ schema")
        recipe = json.loads(basis.recipe_json)
        if set(recipe) != {"runtime", "sources", "argv", "indexer", "source_range_dialect"}:
            raise OccurrenceQualificationError("unsupported C++ indexer recipe")
        runtime = recipe["runtime"]
        if (runtime["glean_commit"] != GLEAN_COMMIT or runtime["llvm"] != "15.0.7"
                or runtime["clang"] != "Ubuntu clang version 15.0.7" or runtime["binaries"] != _BINARIES
                or runtime["hsthrift_commit"] != "e3c575885f9eda98e3c3aa9a1edd5011b6b14373"
                or recipe["argv"] != _ARGV or recipe["indexer"] != "cpp-cmake --cdb-dir <root> -j1"
                or recipe["source_range_dialect"] != "clang-byte-columns-inclusive"):
            raise OccurrenceQualificationError("unsupported C++ indexer recipe")
        if (not basis.inputs or not recipe["sources"]
                or len({item.file for item in basis.inputs}) != len(basis.inputs)
                or recipe["sources"] != sorted(item.file for item in basis.inputs if item.file.endswith(".cpp"))):
            raise OccurrenceQualificationError("invalid declared indexed inputs")

    def _check_occurrence(self) -> None:
        if self._closed:
            raise BackendError("Glean reader is closed")
        basis = self._basis
        if self._admitted_digest is not None and basis.record_digest != self._admitted_digest:
            raise OccurrenceQualificationError("admitted basis record mismatch")
        if self._client.namespace != basis.occurrence.namespace:
            raise OccurrenceQualificationError("wrong retention namespace")
        db = self._client.metadata(basis.occurrence.repo)
        try:
            if db["repo"] != basis.occurrence.repo or db["status"] != "COMPLETE":
                raise OccurrenceQualificationError("exact finalized historical DB unavailable")
            if db.get("dependencies") is not None:
                raise OccurrenceQualificationError("non-standalone runtime basis unsupported")
            props = db["properties"]
            expected = {"glean.guid": basis.occurrence.guid, "glean.schema_id": basis.schema_id,
                        "glean.server.build_revision": GLEAN_COMMIT,
                        "phase6b.input_state": basis.input_state, "phase6b.recipe": basis.recipe_digest}
            for field, value in expected.items():
                if props[field] != value:
                    raise OccurrenceQualificationError(f"Glean qualification mismatch: {field}")
        except (KeyError, TypeError) as exc:
            raise OccurrenceQualificationError("malformed exact DB metadata") from exc

    def _query(self, text: str, *, wrong_fact_ok: bool = False) -> list[dict]:
        return self._client.query(self._basis.occurrence.repo, text, wrong_fact_ok=wrong_fact_ok)

    def _verify_retained(self) -> None:
        self._check_occurrence()
        if self._query("src.IndexFailure.1 _"):
            raise OccurrenceQualificationError("indexer reports file failures")
        rows = self._query("digest.FileDigest.1 _")
        actual = {row["key"]["file"]["key"]: row["key"]["digest"] for row in rows}
        if len(rows) != len(actual) or set(actual) != {item.file for item in self._basis.inputs}:
            raise OccurrenceQualificationError("indexed input inventory mismatch")
        for item in self._basis.inputs:
            data = checked_blob(self._blobs, item)
            if actual[item.file] != {"hash": hashlib.sha1(data).hexdigest(), "size": item.size}:
                raise OccurrenceQualificationError("native indexed digest/size mismatch")

    def snapshot(self) -> str:
        self._check_occurrence()
        return self._basis.observed_state

    def _member(self, entity: Hashable) -> bool:
        if (not isinstance(entity, tuple) or len(entity) != 2
                or not isinstance(entity[0], str) or entity[0] not in _PREDICATES
                or type(entity[1]) is not int or entity[1] <= 0):
            return False
        predicate = _PREDICATES[entity[0]]
        rows = self._query(f"D where D = (${entity[1]} : {predicate}); D = {predicate} _", wrong_fact_ok=True)
        if len(rows) > 1 or rows and rows[0].get("id") != entity[1]:
            raise OccurrenceQualificationError("selected member response mismatch")
        return bool(rows)

    def is_member(self, entity: Hashable) -> bool:
        self._check_occurrence()
        return self._member(entity)

    def kind(self, entity: Hashable) -> str | None:
        self._check_occurrence()
        if not self._member(entity):
            return None
        if entity[0] != FUNCTION:
            return _KINDS[entity[0]]
        rows = self._query(f"codemarkup.cxx.CxxDeclKind.5 {{ decl = {{ function_ = ${entity[1]} }} }}")
        if not rows:
            return None
        try:
            if (len(rows) != 1 or rows[0]["key"]["decl"]["function_"]["id"] != entity[1]
                    or rows[0]["key"]["kind"] != 13):
                raise OccurrenceQualificationError("selected function kind mismatch")
        except (KeyError, TypeError) as exc:
            raise OccurrenceQualificationError("malformed function kind") from exc
        return "callable"

    def _source(self, entity: tuple) -> dict | None:
        rows = self._query(f"cxx1.DeclarationSrcRange.5 {{ decl = {{ function_ = ${entity[1]} }} }}")
        if not rows:
            return None
        try:
            if len(rows) != 1 or rows[0]["key"]["decl"]["function_"]["id"] != entity[1]:
                raise OccurrenceQualificationError("selected declaration evidence mismatch")
            source = rows[0]["key"]["source"]
            file = source["file"]
            if not self._member((FILE, file["id"])):
                raise OccurrenceQualificationError("source endpoint is not a member")
            if file["key"] not in {item.file for item in self._basis.inputs}:
                raise OccurrenceQualificationError("source outside retained indexed manifest")
            return source
        except (KeyError, TypeError) as exc:
            raise OccurrenceQualificationError("malformed declaration source") from exc

    def containment(self, entity: Hashable) -> tuple[dict[str, Hashable], ...]:
        self._check_occurrence()
        if not self._member(entity) or entity[0] == UNIT:
            return ()
        if entity[0] == FILE:
            units = self._query(f"buck.TranslationUnit.4 {{ file = ${entity[1]} }}")
            if not units:
                return ()  # header/file participation is outside this ancestor view
            try:
                if len(units) != 1 or units[0]["key"]["file"]["id"] != entity[1]:
                    raise OccurrenceQualificationError("file context outside single-main-file scope")
                unit = (UNIT, units[0]["id"])
                if not self._member(unit):
                    raise OccurrenceQualificationError("translation-unit endpoint is not a member")
                return ({"parent": unit, "child": entity},)
            except (KeyError, TypeError) as exc:
                raise OccurrenceQualificationError("malformed file context") from exc
        source = self._source(entity)
        if source is None:
            return ()
        file = (FILE, source["file"]["id"])
        rows = self._query("cxx1.TranslationUnitTrace.5 { trace = T } where "
                           f"cxx1.DeclarationInTrace.5 {{ decl = {{ function_ = ${entity[1]} }}, trace = T }}")
        try:
            if (len(rows) != 1 or rows[0]["key"]["trace"]["key"]["file"]["id"] != file[1]
                    or rows[0]["key"]["tunit"]["key"]["file"]["id"] != file[1]):
                raise OccurrenceQualificationError("function context outside single-main-file scope")
            unit = (UNIT, rows[0]["key"]["tunit"]["id"])
            if not self._member(unit):
                raise OccurrenceQualificationError("translation-unit endpoint is not a member")
            return ({"parent": unit, "child": file}, {"parent": file, "child": entity})
        except (KeyError, TypeError) as exc:
            raise OccurrenceQualificationError("malformed function context") from exc

    def capability(self, family: str) -> Capability:
        self._check_occurrence()
        policies = {
            "kind": (CapabilityStatus.INCOMPLETE, "typed global functions and ownership endpoints in declared inputs", ("other AST categories not normalized",)),
            "containment": (CapabilityStatus.INCOMPLETE, "main-file translation-unit/file/function ownership", ("headers and lexical scope not a tree",)),
            "evidence": (CapabilityStatus.INCOMPLETE, "selected declaration ranges in retained indexed UTF-8 bytes", ("other locator/encoding forms unproven",)),
            "invocation": (CapabilityStatus.NOT_PRODUCED, "initial C++ core recipe", ("xref is not syntactic call proof",)),
            "resolution": (CapabilityStatus.NOT_PRODUCED, "initial C++ core recipe", ("call-resolution outcomes not produced",)),
        }
        if family not in policies:
            raise OccurrenceQualificationError(f"unsupported capability family: {family}")
        status, scope, gaps = policies[family]
        return Capability(status, scope, f"{family}: recipe={self._basis.recipe_digest}; schema={self._basis.schema_id}", gaps)

    def _observation(self, entity: tuple) -> dict | None:
        source = self._source(entity)
        if source is None:
            return None
        file = source["file"]
        item = next(item for item in self._basis.inputs if item.file == file["key"])
        return {"basis_digest": self._basis.record_digest, "predicate": FUNCTION, "entity": entity[1],
                "file_id": file["id"], "file": file["key"], "range_json": canonical(source).decode(),
                "source_sha256": item.sha256}

    def observations(self, entity: Hashable) -> tuple[object, ...]:
        self._check_occurrence()
        if not self._member(entity) or entity[0] != FUNCTION:
            return ()
        observation = self._observation(entity)
        return (observation,) if observation is not None else ()

    def reconstruct(self, observation: object) -> tuple[str, bool]:
        self._check_occurrence()
        if (not isinstance(observation, Mapping) or observation.get("basis_digest") != self._basis.record_digest
                or observation.get("predicate") != FUNCTION or type(observation.get("entity")) is not int):
            return "", False
        entity = (FUNCTION, observation["entity"])
        if not self._member(entity) or observation != self._observation(entity):
            return "", False
        try:
            item = next(item for item in self._basis.inputs if item.file == observation["file"])
            data = checked_blob(self._blobs, item)
            loc = json.loads(observation["range_json"])
            lines = data.splitlines(keepends=True)
            def offset(line, column):
                if (type(line) is not int or type(column) is not int
                        or not 1 <= line <= len(lines) or not 1 <= column <= len(lines[line - 1])):
                    raise ValueError("invalid retained byte-column range")
                return sum(len(part) for part in lines[:line - 1]) + column - 1
            start = offset(loc["lineBegin"], loc["columnBegin"])
            end = offset(loc["lineEnd"], loc["columnEnd"]) + 1
            if not 0 <= start < end <= len(data):
                return "", False
            return data[start:end].decode("utf-8"), True
        except (OccurrenceQualificationError, ValueError, KeyError, TypeError, StopIteration):
            return "", False

    def verify(self) -> tuple[str, ...]:
        try:
            self._validate_recipe()
            self._verify_retained()
        except (BackendError, ValueError, KeyError, TypeError, AttributeError) as exc:
            return (str(exc),)
        return ()

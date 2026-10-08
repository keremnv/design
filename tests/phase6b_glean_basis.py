"""Experimental Glean-specific admission basis; not an installed publication API.

The store namespace is logical retention identity, not a server hostname. Source
blobs contain bytes only. Glean remains the authority for indexed structure.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Callable


class BasisFailure(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class Input:
    file: str
    sha256: str
    size: int


@dataclass(frozen=True)
class DBRef:
    namespace: str
    repo: str
    guid: str


@dataclass(frozen=True)
class GleanBasis:
    occurrence: DBRef
    schema_id: str
    inputs: tuple[Input, ...]
    recipe_json: str
    dependencies: tuple[DBRef, ...] = ()  # exact required transitive closure

    @property
    def input_state(self) -> str:
        return sha256(canonical([asdict(item) for item in self.inputs]))

    @property
    def recipe_digest(self) -> str:
        return sha256(canonical(json.loads(self.recipe_json)))

    @property
    def observed_state(self) -> str:
        return sha256(canonical({"input_state": self.input_state,
                                 "recipe": self.recipe_digest, "schema": self.schema_id}))

    @property
    def record_digest(self) -> str:
        return sha256(canonical(asdict(self)))

    def to_json(self) -> str:
        return canonical(asdict(self)).decode()

    @classmethod
    def from_json(cls, text: str) -> GleanBasis:
        obj = json.loads(text)
        return cls(DBRef(**obj["occurrence"]), obj["schema_id"],
                   tuple(Input(**item) for item in obj["inputs"]), obj["recipe_json"],
                   tuple(DBRef(**item) for item in obj["dependencies"]))


def checked_blob(root: Path, item: Input) -> bytes:
    path = PurePosixPath(item.file)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise BasisFailure("invalid indexed source identity")
    if len(item.sha256) != 64 or any(c not in "0123456789abcdef" for c in item.sha256):
        raise BasisFailure("invalid retained digest")
    try:
        blob = root / item.sha256
        if blob.is_symlink():
            raise BasisFailure("retained blob is a mutable indirection")
        data = blob.read_bytes()
    except OSError as exc:
        raise BasisFailure("retained source unavailable") from exc
    if len(data) != item.size or sha256(data) != item.sha256:
        raise BasisFailure("retained source digest/size mismatch")
    return data


def verify_basis(basis: GleanBasis, admitted_digest: str, namespace: str,
                 metadata: Callable[[str], dict], blobs: Path) -> None:
    """Verify a trusted admission record against exact DB metadata and bytes.

    metadata must query the supplied exact Repo, never latest; wire/error handling
    remains the experimental runtime driver's responsibility. The deployment
    covenant forbids accepted DB unfinish/key reuse. This checks qualification,
    not a malicious storage-owner sandbox or universal analysis completeness.
    """
    if basis.record_digest != admitted_digest:
        raise BasisFailure("admitted basis record mismatch")
    if namespace != basis.occurrence.namespace:
        raise BasisFailure("wrong retention namespace")
    if len({item.file for item in basis.inputs}) != len(basis.inputs):
        raise BasisFailure("duplicate indexed file identity")
    if len(set(basis.dependencies)) != len(basis.dependencies):
        raise BasisFailure("duplicate dependency")
    expected_closure = set(basis.dependencies)
    refs = (basis.occurrence, *basis.dependencies)
    reached = set()
    actual_refs = {}
    for ref in refs:
        if ref.namespace != namespace:
            raise BasisFailure("dependency namespace outside this retained store")
        try:
            db = metadata(ref.repo)
        except Exception as exc:
            raise BasisFailure("exact historical DB unavailable") from exc
        if db["repo"] != ref.repo or db["status"] != "COMPLETE":
            raise BasisFailure("exact finalized DB unavailable")
        props = db["properties"]
        if props["glean.guid"] != ref.guid:
            raise BasisFailure("DB occurrence GUID mismatch")
        deps = set(DBRef(**item) for item in db.get("dependency_refs", []))
        if not deps.issubset(expected_closure):
            raise BasisFailure("required dependency omitted/substituted")
        actual_refs[ref] = deps
        if ref == basis.occurrence:
            if props["glean.schema_id"] != basis.schema_id:
                raise BasisFailure("stored schema mismatch")
            if props["phase6b.input_state"] != basis.input_state:
                raise BasisFailure("indexed input manifest mismatch")
            if props["phase6b.recipe"] != basis.recipe_digest:
                raise BasisFailure("indexed recipe mismatch")
    pending = list(actual_refs[basis.occurrence])
    while pending:
        ref = pending.pop()
        if ref == basis.occurrence:
            raise BasisFailure("cyclic DB dependencies")
        if ref not in reached:
            reached.add(ref)
            pending.extend(actual_refs[ref])
    if reached != expected_closure:
        raise BasisFailure("extraneous or missing dependency closure")
    for item in basis.inputs:
        checked_blob(blobs, item)

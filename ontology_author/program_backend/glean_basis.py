"""Glean-specific retained qualification; compatible with Phase 6B records.

This stores identity, recipe and source bytes, never a second program graph.
Independent admission pins and retention obligations belong to composition.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath

from . import OccurrenceQualificationError


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Input:
    file: str
    sha256: str
    size: int


@dataclass(frozen=True)
class DBRef:
    namespace: str
    repo: str  # exact CLI Repo(name, hash), never a latest name
    guid: str


@dataclass(frozen=True)
class GleanBasis:
    occurrence: DBRef
    schema_id: str
    inputs: tuple[Input, ...]
    recipe_json: str
    dependencies: tuple[DBRef, ...] = ()

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
        try:
            obj = json.loads(text)
            if set(obj) != {"occurrence", "schema_id", "inputs", "recipe_json", "dependencies"}:
                raise ValueError("unexpected basis fields")
            return cls(DBRef(**obj["occurrence"]), obj["schema_id"],
                       tuple(Input(**item) for item in obj["inputs"]), obj["recipe_json"],
                       tuple(DBRef(**item) for item in obj["dependencies"]))
        except (ValueError, TypeError, KeyError) as exc:
            raise OccurrenceQualificationError("malformed Glean basis record") from exc


def checked_blob(root: Path, item: Input) -> bytes:
    path = PurePosixPath(item.file)
    if (not item.file or not path.parts or path.is_absolute() or ".." in path.parts
            or path.as_posix() != item.file):
        raise OccurrenceQualificationError("invalid indexed source identity")
    if (not isinstance(item.sha256, str) or len(item.sha256) != 64
            or any(c not in "0123456789abcdef" for c in item.sha256)
            or type(item.size) is not int or item.size < 0):
        raise OccurrenceQualificationError("invalid retained digest/size")
    try:
        blob = root / item.sha256
        if blob.is_symlink():
            raise OccurrenceQualificationError("retained blob is a mutable indirection")
        data = blob.read_bytes()
    except OSError as exc:
        raise OccurrenceQualificationError("retained source unavailable") from exc
    if len(data) != item.size or sha256(data) != item.sha256:
        raise OccurrenceQualificationError("retained source digest/size mismatch")
    return data

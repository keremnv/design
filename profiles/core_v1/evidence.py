"""Scenario-local mechanical adapters and digest-checked evidence retention.

No requirement interpretation, authority, semantic identity, or World writes
occur here. Python observations are syntax only; CSV records include exact
physical spans (including quoted multiline records).
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
from dataclasses import dataclass
from pathlib import Path

from ontology_author.evidence.markdown import MarkdownSource, parse_byte_location
from ontology_author.world.core.source import SourceObservation


@dataclass(frozen=True)
class Observed:
    values: dict[str, str]
    observation: SourceObservation


class Material:
    def __init__(self, path: Path, *, handle: str, provider: str):
        self.data = path.read_bytes()
        self.text = self.data.decode("utf-8")
        self.handle = handle
        self.provider = provider
        self.revision = "sha256:" + hashlib.sha256(self.data).hexdigest()

    def observe(self, start: int, end: int) -> SourceObservation:
        if not 0 <= start <= end <= len(self.data):
            raise ValueError("observation outside source bytes")
        self.data[start:end].decode("utf-8")
        return SourceObservation(
            self.provider, self.handle, self.revision, f"bytes:{start}:{end}"
        )

    def reconstruct(self, observation: SourceObservation) -> str:
        if (observation.provider, observation.native_handle, observation.source_revision) != (
            self.provider, self.handle, self.revision
        ):
            raise ValueError("observation belongs to another source/revision")
        start, end = parse_byte_location(observation.native_location)
        self.observe(start, end)
        return self.data[start:end].decode("utf-8")

    def retain(self, bundle: Path) -> None:
        retain_bytes(bundle, self.data)


def retain_bytes(bundle: Path, data: bytes) -> None:
    directory = bundle / "evidence"
    directory.mkdir(exist_ok=True)
    (directory / hashlib.sha256(data).hexdigest()).write_bytes(data)


def reconstruct_retained(bundle: Path, observation: SourceObservation) -> str:
    """Reconstruct old evidence independently of the mutable source tree."""
    revision = observation.source_revision
    digest = revision.removeprefix("sha256:")
    if revision != "sha256:" + digest or len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError("expected a SHA-256 source revision")
    data = (bundle / "evidence" / digest).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("retained evidence digest mismatch")
    start, end = parse_byte_location(observation.native_location)
    if not 0 <= start <= end <= len(data):
        raise ValueError("observation outside retained source bytes")
    return data[start:end].decode("utf-8")


class CsvEvidence(Material):
    known_losses = ("field values are parsed strings; no business identity is inferred",)

    def __init__(self, path: Path, *, handle: str):
        super().__init__(path, handle=handle, provider="csv")

    def records(self) -> tuple[Observed, ...]:
        offsets = [0]
        for line in self.data.splitlines(keepends=True):
            offsets.append(offsets[-1] + len(line))
        reader = csv.reader(io.StringIO(self.text, newline=""), strict=True)
        header = next(reader)
        if len(set(header)) != len(header):
            raise ValueError("duplicate CSV columns")
        previous = reader.line_num
        records = []
        for values in reader:
            if len(values) != len(header):
                raise ValueError("CSV record does not match header")
            records.append(Observed(
                dict(zip(header, values, strict=True)),
                self.observe(offsets[previous], offsets[reader.line_num]),
            ))
            previous = reader.line_num
        return tuple(records)


class PythonEvidence(Material):
    known_losses = (
        "only top-level function declarations and direct return-call syntax are exposed",
        "names are not compiler-resolved; aliases, dynamic dispatch and runtime behavior are not inferred",
    )

    def __init__(self, path: Path, *, handle: str):
        super().__init__(path, handle=handle, provider="python-ast")
        self.tree = ast.parse(self.text)
        self.offsets = [0]
        for line in self.data.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))

    def _observe_node(self, node: ast.AST) -> SourceObservation:
        return self.observe(
            self.offsets[node.lineno - 1] + node.col_offset,
            self.offsets[node.end_lineno - 1] + node.end_col_offset,
        )

    def declarations(self) -> tuple[Observed, ...]:
        return tuple(
            Observed({"name": node.name}, self._observe_node(node))
            for node in self.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

    def direct_calls(self) -> tuple[Observed, ...]:
        calls = []
        for owner in self.tree.body:
            if not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for statement in owner.body:
                if not isinstance(statement, ast.Return):
                    continue
                call = statement.value
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
                    calls.append(Observed(
                        {"caller": owner.name, "callee": call.func.id},
                        self._observe_node(call),
                    ))
        return tuple(calls)


def sources(root: Path):
    """Open the scenario's three source forms; no semantic interpretation."""
    return (
        MarkdownSource(root / "requirements.md", handle="requirements.md"),
        PythonEvidence(root / "payments.py", handle="payments.py"),
        CsvEvidence(root / "deployments.csv", handle="deployments.csv"),
    )

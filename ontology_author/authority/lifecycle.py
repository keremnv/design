"""Construct source-only semantic state or extend an exact retained baseline."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from contextlib import closing
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ontology_author.world.runtime.commit import (
    discard_candidate,
    fingerprint_world,
    publish_candidate,
    write_sidecars,
)
from ontology_author.world.runtime.world import ConstructionWorld
from ontology_author.world.runtime.publication import PublicationRef, verify_publication_ref

from ontology_author.evidence import EvidenceError
from ontology_author.program_backend import BackendError, NotAProgramOccurrence
from ontology_author.program_backend.native import open_native_occurrence

from .construction import AuthorityConstructor, AuthorityUniverse, optional_program_rows
from .evidence import retain_authority_sources
from .schemas import (
    DEFAULT_PROFILE,
    CONSTRUCTOR_ID,
    CONSTRUCTOR_VERSION,
    AuthorityConstructionError,
    AuthorityConstructionReceipt,
)
from .validation import validate_authority_construction


@dataclass(frozen=True)
class AuthorityConstructionResult:
    succeeded: bool
    reason: str = ""
    errors: tuple[str, ...] = ()
    world_dir: Path | None = None
    receipt: AuthorityConstructionReceipt | None = None
    snapshot_id: str = ""
    publication: PublicationRef | None = None


def make_writable_copy(source: Path, dest: Path) -> None:
    """Copy a sealed World bundle into a writable candidate directory."""

    dest = Path(dest)
    if dest.exists():
        raise AuthorityConstructionError(f"candidate already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    _copy_tree(Path(source), dest)
    _make_writable(dest)


def construct_authority_world(
    program_world: Path | str | None,
    output: Path | str,
    universe: AuthorityUniverse,
    build: Callable[[AuthorityConstructor], None],
    *,
    construction_id: str,
    purpose: str,
    profile: str = DEFAULT_PROFILE,
    program_universe: str = "declared_program_boundary",
    acceptance: dict[str, Any] | None = None,
    publication_inputs: tuple[PublicationRef, ...] = (),
    constructor_id: str = CONSTRUCTOR_ID,
    constructor_version: str = CONSTRUCTOR_VERSION,
) -> AuthorityConstructionResult:
    """Build and admit semantic state, optionally cloning an exact baseline.

    Pass ``None`` for a fresh source-only candidate. The historical positional
    name ``program_world`` also accepts a semantic-only retained baseline.
    The sealed baseline World is an immutable input. Failure discards the
    candidate and does not modify that input. Every declared authority source
    is retained in the candidate before admission so an accepted publication
    never depends on the original workspace copy remaining available.
    ``output`` must be a fresh address: any baseline publication is retained
    unchanged beside the new authority publication. Explicit publication inputs
    are qualified and checked before construction, without semantic inheritance.
    """

    source = Path(program_world).resolve() if program_world is not None else None
    requested_output = Path(output)
    if os.path.lexists(requested_output):
        return AuthorityConstructionResult(
            False,
            "publication_exists",
            (f"publication address already exists: {requested_output}",),
        )
    output_dir = requested_output.resolve(strict=False)
    if source is not None and not (source / "world.sqlite").exists():
        return AuthorityConstructionResult(
            False, "missing_program_world", ("program World sqlite is missing",)
        )
    candidate = output_dir.with_name(
        f".{output_dir.name}.candidate-{uuid.uuid4().hex}"
    )
    if os.path.lexists(candidate):
        return AuthorityConstructionResult(
            False,
            "candidate_exists",
            (f"candidate address already exists: {candidate}",),
        )
    backend = None
    try:
        baseline = None
        candidate_snapshot_ref = None
        if source is not None:
            with closing(ConstructionWorld.open(source / "world.sqlite", read_only=True)) as opened:
                baseline = PublicationRef.from_world(opened)
                snapshots = optional_program_rows(opened, "program_snapshot")
                if len(snapshots) == 1:
                    candidate_snapshot_ref = str(snapshots[0]["snapshot"])
        inputs = tuple(dict.fromkeys((*publication_inputs, *((baseline,) if baseline else ()))))
        for reference in inputs:
            with closing(ConstructionWorld.open(Path(reference.address) / "world.sqlite", read_only=True)) as opened:
                mismatches = verify_publication_ref(opened, reference)
                if mismatches:
                    raise AuthorityConstructionError("construction publication input: " + "; ".join(mismatches))
        if source is not None:
            try:
                backend = open_native_occurrence(source)
            except NotAProgramOccurrence:
                backend = None
            except BackendError as exc:
                return AuthorityConstructionResult(False, "authority_construction", (str(exc),))
        if source is not None:
            make_writable_copy(source, candidate)
            world = ConstructionWorld.open(candidate / "world.sqlite", read_only=False)
        else:
            candidate.mkdir(parents=True)
            world = ConstructionWorld.create(candidate / "world.sqlite", world_id=construction_id)
        constructor: AuthorityConstructor | None = None
        try:
            constructor = AuthorityConstructor(
                world,
                universe=universe,
                construction_id=construction_id,
                purpose=purpose,
                profile=profile,
                program_universe=program_universe,
                acceptance=acceptance,
                publication_inputs=inputs,
                candidate_baseline=baseline,
                constructor_id=constructor_id,
                constructor_version=constructor_version,
                program_backend=backend,
                candidate_snapshot_ref=candidate_snapshot_ref,
            )
            build(constructor)
            receipt = constructor.finish()
            retain_authority_sources(candidate, constructor.markdown)
            receipt_path = candidate / "authority.construction.receipt.json"
            receipt.write(receipt_path)
            errors = validate_authority_construction(constructor, receipt)
            if errors:
                world.close()
                discard_candidate(candidate)
                return AuthorityConstructionResult(
                    False,
                    "authority_admission",
                    tuple(errors),
                    snapshot_id=constructor._snapshot_id,
                )
            manifest = {
                "construction_id": construction_id,
                "purpose": purpose,
                "profile": profile,
                "program_snapshot_id": constructor._snapshot_id,
                "program_world": str(source) if source else None,
                "admission": {
                    "contract": receipt.construction_contract["id"],
                    "outcome": "PASS",
                },
                "receipt": {
                    "path": receipt_path.name,
                    "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                },
            }
            (candidate / "authority.manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            write_sidecars(world)
            world.close()
            publication = publish_candidate(candidate, output_dir)
            return AuthorityConstructionResult(
                True,
                world_dir=output_dir,
                receipt=receipt,
                snapshot_id=constructor._snapshot_id,
                publication=publication,
            )
        except Exception:
            try:
                world.close()
            except Exception:
                pass
            discard_candidate(candidate)
            raise
    except (AuthorityConstructionError, EvidenceError) as exc:
        discard_candidate(candidate)
        return AuthorityConstructionResult(False, "authority_construction", (str(exc),))
    except Exception as exc:
        discard_candidate(candidate)
        return AuthorityConstructionResult(
            False, "authority_construction", (f"{type(exc).__name__}: {exc}",)
        )
    finally:
        if backend is not None:
            try:
                backend.close()
            except Exception:
                pass


def program_world_fingerprint(program_world: Path | str) -> dict[str, str]:
    return fingerprint_world(Path(program_world))


def _copy_tree(source: Path, dest: Path) -> None:
    dest.mkdir(parents=True)
    for path in source.iterdir():
        target = dest / path.name
        if path.is_dir():
            _copy_tree(path, target)
        else:
            target.write_bytes(path.read_bytes())


def _make_writable(path: Path) -> None:
    path.chmod(path.stat().st_mode | (0o700 if path.is_dir() else 0o600))
    for child in path.rglob("*"):
        child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))

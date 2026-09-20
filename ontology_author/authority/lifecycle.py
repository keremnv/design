"""Clone a sealed program-spine World, add authority facts, validate, and seal."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ontology_author.world.runtime.commit import (
    _replace_candidate,
    discard_candidate,
    fingerprint_world,
    write_sidecars,
)
from ontology_author.world.runtime.world import ConstructionWorld, world_id_of

from ontology_author.evidence import EvidenceError

from .construction import AuthorityConstructor, AuthorityUniverse
from .schemas import (
    DEFAULT_PROFILE,
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


def make_writable_copy(source: Path, dest: Path) -> None:
    """Copy a sealed World bundle into a writable candidate directory."""

    dest = Path(dest)
    if dest.exists():
        raise AuthorityConstructionError(f"candidate already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    _copy_tree(Path(source), dest)
    _make_writable(dest)


def construct_authority_world(
    program_world: Path | str,
    output: Path | str,
    universe: AuthorityUniverse,
    build: Callable[[AuthorityConstructor], None],
    *,
    construction_id: str,
    purpose: str,
    profile: str = DEFAULT_PROFILE,
    program_universe: str = "declared_program_boundary",
    acceptance: dict[str, Any] | None = None,
) -> AuthorityConstructionResult:
    """Create a governed World by cloning a program spine, then adding authority facts.

    The sealed program World is an immutable input. Failure discards the
    candidate and does not modify that input.
    """

    source = Path(program_world).resolve()
    output_dir = Path(output).resolve()
    if not (source / "world.sqlite").exists():
        return AuthorityConstructionResult(
            False, "missing_program_world", ("program World sqlite is missing",)
        )
    candidate = output_dir.with_name(output_dir.name + ".candidate")
    discard_candidate(candidate)
    try:
        make_writable_copy(source, candidate)
        world = ConstructionWorld.open(
            candidate / "world.sqlite",
            world_id=world_id_of(candidate / "world.sqlite"),
            read_only=False,
        )
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
            )
            build(constructor)
            receipt = constructor.finish()
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
            receipt_path = candidate / "authority.construction.receipt.json"
            receipt.write(receipt_path)
            manifest = {
                "construction_id": construction_id,
                "purpose": purpose,
                "profile": profile,
                "program_snapshot_id": constructor._snapshot_id,
                "program_world": str(source),
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
            _replace_candidate(candidate, output_dir)
            return AuthorityConstructionResult(
                True,
                world_dir=output_dir,
                receipt=receipt,
                snapshot_id=constructor._snapshot_id,
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

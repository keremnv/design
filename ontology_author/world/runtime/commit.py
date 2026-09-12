"""Candidate World execution, fail-closed validation, and World replacement.

Implements World integrity and WORLD BASE SOURCE accountability for the
construction boundary.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ontology_author.world.runtime.world import ConstructionWorld


@dataclass(frozen=True)
class ValidationReport:
    ok: bool
    ungrounded: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class RunResult:
    succeeded: bool
    reason: str = ""
    errors: tuple[str, ...] = ()
    world_dir: Path | None = None


def source_kinds_for_assertion(world: ConstructionWorld, assertion_id: str) -> list[dict[str, Any]]:
    return world.query(
        "SELECT kind, reference, detail FROM _world_groundings "
        "WHERE subject_type = 'ASSERTION' AND subject_id = ?",
        (assertion_id,),
    )


def validate_contract_admission(world: ConstructionWorld) -> ValidationReport:
    """Validate every asserted BASE tuple against the bound Contract."""

    rejected = world.admission_errors()
    if rejected:
        return ValidationReport(
            ok=False,
            ungrounded=rejected,
            reason=str(rejected[0].get("reason") or "contract_admission"),
        )
    return ValidationReport(ok=True)


def validate_world_base_source(world: ConstructionWorld) -> ValidationReport:
    """Compatibility name for the Contract-backed publication validator."""

    return validate_contract_admission(world)


def write_sidecars(
    world: ConstructionWorld,
    purpose_payload: dict[str, Any],
    governance_payload: dict[str, Any] | None = None,
    evidence_authority_payload: dict[str, Any] | None = None,
    adjudication_authority_payload: dict[str, Any] | None = None,
) -> None:
    directory = world.path.parent
    (directory / "world.admission.json").write_text(
        json.dumps(world.admission_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (directory / "world.purpose.json").write_text(
        json.dumps(purpose_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if governance_payload is not None:
        (directory / "world.governance.json").write_text(
            json.dumps(governance_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if evidence_authority_payload is not None:
        (directory / "world.evidence-authority.json").write_text(
            json.dumps(evidence_authority_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if adjudication_authority_payload is not None:
        (directory / "world.adjudication-authority.json").write_text(
            json.dumps(adjudication_authority_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _replace_candidate(candidate: Path, world: Path) -> None:
    """Replace the current World with a sealed candidate directory."""

    candidate = Path(candidate)
    world = Path(world)
    parent = world.parent
    staging = parent / (world.name + ".staging")
    previous = parent / (world.name + ".previous")
    if staging.exists():
        _remove_tree(staging)
    shutil.copytree(candidate, staging)
    if previous.exists():
        _remove_tree(previous)
    _seal_world(staging)
    if world.exists():
        world.rename(previous)
    try:
        staging.rename(world)
    except Exception:
        if previous.exists() and not world.exists():
            previous.rename(world)
        raise
    else:
        if previous.exists():
            _remove_tree(previous)
        _remove_tree(candidate)


def _seal_world(world: Path) -> None:
    """Seal the World bundle while leaving its parent replaceable."""

    for path in sorted(world.rglob("*"), reverse=True):
        path.chmod(path.stat().st_mode & ~0o222)
    world.chmod(world.stat().st_mode & ~0o222)


def _remove_tree(path: Path) -> None:
    """Remove a sealed temporary/previous bundle after making it writable."""

    for child in path.rglob("*"):
        child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))
    path.chmod(path.stat().st_mode | 0o700)
    shutil.rmtree(path)



def discard_candidate(candidate: Path) -> None:
    path = Path(candidate)
    if path.exists():
        shutil.rmtree(path)


def fingerprint_world(world: Path) -> dict[str, str]:
    """Byte hashes of World artifacts. Missing files are absent keys."""

    import hashlib

    world = Path(world)
    out: dict[str, str] = {}
    if not world.exists():
        return out
    for path in sorted(world.iterdir()):
        if path.is_file():
            out[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out

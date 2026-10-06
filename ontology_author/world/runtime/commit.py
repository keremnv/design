"""Candidate World execution, fail-closed validation, and fresh publication.

Implements World integrity and WORLD BASE SOURCE accountability for the
construction boundary. Accepted history grows by publishing validated
candidates at fresh retained addresses; publication never mutates,
overwrites, or removes an already accepted bundle. Legacy in-place
replacement survives below for frozen compatibility paths only.
"""

from __future__ import annotations

import errno
import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ontology_author.world.runtime.publication import PublicationRef
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld


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


def write_sidecars(
    world: ConstructionWorld,
    purpose_payload: dict[str, Any] | None = None,
    governance_payload: dict[str, Any] | None = None,
    evidence_authority_payload: dict[str, Any] | None = None,
    adjudication_authority_payload: dict[str, Any] | None = None,
    construction_receipt_payload: dict[str, Any] | None = None,
) -> None:
    directory = world.path.parent
    (directory / "world.admission.json").write_text(
        json.dumps(world.admission_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if purpose_payload is not None:
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
    if construction_receipt_payload is not None:
        from ontology_author.world.runtime.construction_receipt import (
            write_construction_receipt,
        )

        write_construction_receipt(directory, construction_receipt_payload)


def _verify_retained_evidence_closure(bundle: Path) -> None:
    """Reject a publication whose retained TypeScript evidence cannot resolve.

    Generic Contract admission intentionally remains provider-neutral. This
    publication-boundary check only activates for source observations owned by
    the TypeScript program-evidence provider; other providers retain their own
    verification contracts.
    """

    database = bundle / "world.sqlite"
    if not database.exists():
        return
    from ontology_author.evidence.program_source import verify_retained_program_inputs

    opened = ConstructionWorld.open(database, read_only=True)
    try:
        errors = verify_retained_program_inputs(opened)
    finally:
        opened.close()
    if errors:
        raise ConstructionError(
            "retained program evidence verification failed: " + "; ".join(errors)
        )


def publish_candidate(candidate: Path | str, destination: Path | str) -> PublicationRef:
    """Publish a validated candidate bundle at a fresh retained address.

    The caller owns domain admission. This boundary owns publication integrity:
    the supplied destination must be lexically fresh, aliases may not place the
    destination inside the candidate, retained program evidence must close over
    the staged bytes, publication identity must be valid before commit, and the
    sealed bundle is installed with atomic no-replace semantics.

    The candidate is removed after a successful commit when cleanup succeeds.
    Cleanup failure cannot turn an already committed publication into a failed
    publication result. Publication order carries no semantic currentness.
    """

    candidate = Path(candidate)
    destination = Path(destination)

    # Lexical freshness matters before canonicalization: a dangling symlink is
    # itself an occupied publication address even though Path.resolve() points
    # at its nonexistent target.
    if os.path.lexists(destination):
        raise ConstructionError(f"publication address already exists: {destination}")
    if candidate.is_symlink():
        raise ConstructionError(f"publication candidate may not be a symlink: {candidate}")
    if not candidate.is_dir():
        raise ConstructionError(f"publication candidate is missing: {candidate}")
    if not (candidate / "world.sqlite").is_file():
        raise ConstructionError(f"publication candidate has no world.sqlite: {candidate}")

    try:
        candidate_resolved = candidate.resolve(strict=True)
        destination_resolved = destination.resolve(strict=False)
    except OSError as exc:
        raise ConstructionError(f"publication address cannot be resolved: {exc}") from exc

    if (
        destination_resolved == candidate_resolved
        or candidate_resolved in destination_resolved.parents
    ):
        raise ConstructionError(
            f"publication address is inside its own candidate: {destination}"
        )

    destination_resolved.parent.mkdir(parents=True, exist_ok=True)
    staging = destination_resolved.parent / (
        f".{destination_resolved.name}.staging-{uuid.uuid4().hex}"
    )
    if os.path.lexists(staging):
        raise ConstructionError(f"publication staging address already exists: {staging}")

    prepared_ref: PublicationRef
    try:
        shutil.copytree(candidate_resolved, staging)
        _verify_retained_evidence_closure(staging)

        # Validate exact publication identity before the irreversible rename.
        opened = ConstructionWorld.open(staging / "world.sqlite", read_only=True)
        try:
            staged_ref = PublicationRef.from_world(opened)
        finally:
            opened.close()
        prepared_ref = PublicationRef(
            address=str(destination_resolved),
            world_id=staged_ref.world_id,
            revision=staged_ref.revision,
        )

        _seal_world(staging)
        try:
            _exclusive_rename(staging, destination_resolved)
        except FileExistsError:
            raise ConstructionError(
                f"publication address already exists: {destination}"
            ) from None
    except Exception:
        if os.path.lexists(staging):
            _remove_tree(staging)
        raise

    # Commit has happened. Candidate cleanup is post-commit housekeeping and
    # must not make a valid retained publication appear to have failed.
    try:
        _remove_tree(candidate_resolved)
    except OSError:
        pass
    return prepared_ref


def _exclusive_rename(source: Path, dest: Path) -> None:
    """Atomically install source at a fresh dest without overwrite.

    Linux uses renameat2(RENAME_NOREPLACE). If the platform does not provide
    an atomic no-replace primitive, fail closed rather than falling back to
    os.rename whose directory semantics can replace a concurrent empty
    destination.
    """

    if os.path.lexists(dest):
        raise FileExistsError(str(dest))
    no_replace = _rename_noreplace(source, dest)
    if no_replace is True:
        return
    raise OSError(
        errno.ENOTSUP,
        "atomic no-replace rename is unavailable on this platform",
        str(dest),
    )


def _rename_noreplace(source: Path, dest: Path) -> bool | None:
    """Try Linux renameat2 NOREPLACE. Returns True, or None if unavailable."""
    try:
        import ctypes
    except ImportError:
        return None
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
    except OSError:
        return None
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        return None
    renameat2.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    ret = renameat2(
        -100, os.fsencode(source), -100, os.fsencode(dest), 1  # RENAME_NOREPLACE
    )
    if ret == 0:
        return True
    import errno as _errno

    code = ctypes.get_errno()
    if code in (_errno.ENOSYS, _errno.EINVAL):
        return None
    if code == _errno.EEXIST:
        raise FileExistsError(str(dest))
    raise OSError(code, os.strerror(code), str(dest))


# --- Legacy in-place rebuild (frozen compatibility, not publication) ---
#
# Project.run(), entry.rebuild(), and `author rebuild` against an existing
# root replace that root's bundle. That behavior is frozen for
# compatibility and is explicitly NOT accepted-history publication: it
# retains no prior revision and must not be used where retained history is
# required. New publication paths must use publish_candidate().


def _replace_candidate(candidate: Path, world: Path) -> None:
    """Replace one workspace bundle with a sealed candidate directory.

    Legacy compatibility behavior for in-place rebuild only. This is not
    accepted-history publication: the prior bundle is removed, not
    retained. The Phase 1 retained-evidence closure still applies before
    the boundary is crossed.
    """

    candidate = Path(candidate)
    world = Path(world)
    parent = world.parent
    staging = parent / (world.name + ".staging")
    previous = parent / (world.name + ".previous")
    if staging.exists():
        _remove_tree(staging)
    shutil.copytree(candidate, staging)
    try:
        _verify_retained_evidence_closure(staging)
    except Exception:
        if staging.exists():
            _remove_tree(staging)
        raise
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
    """Seal the World bundle while leaving its parent directory writable."""

    for path in sorted(world.rglob("*"), reverse=True):
        path.chmod(path.stat().st_mode & ~0o222)
    world.chmod(world.stat().st_mode & ~0o222)


def _remove_tree(path: Path) -> None:
    """Remove an owned tree without following or chmodding symlink targets."""

    path = Path(path)
    if not os.path.lexists(path):
        return
    if path.is_symlink():
        path.unlink()
        return
    if not path.is_dir():
        path.chmod(path.stat().st_mode | 0o600)
        path.unlink()
        return

    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        root_path = Path(root)
        # Unlinking children requires write permission on their containing
        # directory. Make only the owned real directory writable; never chmod
        # through symlink entries.
        root_path.chmod(root_path.stat().st_mode | 0o700)
        for name in files:
            child = root_path / name
            if child.is_symlink():
                child.unlink()
            else:
                child.chmod(child.stat().st_mode | 0o600)
                child.unlink()
        for name in dirs:
            child = root_path / name
            if child.is_symlink():
                child.unlink()
            else:
                child.chmod(child.stat().st_mode | 0o700)
                child.rmdir()
    path.chmod(path.stat().st_mode | 0o700)
    path.rmdir()


def discard_candidate(candidate: Path) -> None:
    _remove_tree(Path(candidate))


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

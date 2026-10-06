"""Record Software Governance on an existing software World.

The caller supplies the mechanically trustworthy software representation.
This module adds proposition referents, established bindings, and
unestablished candidates, then publishes the combined bundle at a fresh
address. It does not extract a program.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from ontology_author.evidence.program_source import verify_retained_program_inputs
from ontology_author.software_governance.evidence import write_governance_evidence
from ontology_author.software_governance.validation import CONTRACT_ID, validate_governance_world
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.commit import _seal_world
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld


@dataclass(frozen=True)
class PropositionSpec:
    proposition_id: str
    statement: str
    domain_relation: str
    observations: tuple[SourceObservation, ...]
    establishment_rule: str = ""


@dataclass(frozen=True)
class BindingSpec:
    proposition_id: str
    software_subject: str
    support: str
    endpoint_resolution: str
    construction_method: str
    observations: tuple[SourceObservation, ...]
    software_evidence: str
    establishment_rule: str = ""


@dataclass(frozen=True)
class CandidateSpec:
    proposition_id: str
    software_subject: str
    support: str
    endpoint_resolution: str
    construction_method: str
    observations: tuple[SourceObservation, ...]
    software_evidence: str
    establishment_rule: str = ""


@dataclass(frozen=True)
class QuestionSpec:
    proposition_id: str
    question: str


@dataclass(frozen=True)
class SoftwareSubjectSpec:
    """Producer-neutral receipt for one mechanically identified subject."""

    subject_id: str
    snapshot_id: str
    kind: str
    capability: str
    version: str
    observations: tuple[SourceObservation, ...]


@dataclass(frozen=True)
class ManifestationSpec:
    """Reconstructible local manifestation supplied by the producer."""

    subject_id: str
    scheme: str
    location: str
    capability: str
    observations: tuple[SourceObservation, ...]


@dataclass(frozen=True)
class CompletenessSpec:
    capability: str
    status: str
    universe: str
    basis: str
    known_gaps: tuple[str, ...] = ()


@dataclass(frozen=True)
class GovernanceConstructionResult:
    succeeded: bool
    world_dir: Path | None = None
    errors: tuple[str, ...] = ()


def construct_software_governance(
    *,
    software_world: Path,
    output: Path,
    profile_id: str,
    propositions: tuple[PropositionSpec, ...],
    bindings: tuple[BindingSpec, ...],
    candidates: tuple[CandidateSpec, ...] = (),
    questions: tuple[QuestionSpec, ...] = (),
    subjects: tuple[SoftwareSubjectSpec, ...] = (),
    manifestations: tuple[ManifestationSpec, ...] = (),
    completeness: CompletenessSpec,
    evidence_blobs: Mapping[str, bytes],
) -> GovernanceConstructionResult:
    """Copy ``software_world``, record governance, and seal it at ``output``.

    ``output`` must not already exist. ``software_world`` is left unchanged.
    """

    publication = Path(output)
    source = Path(software_world)
    if os.path.lexists(publication):
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"publication address already exists: {publication}",),
        )
    if not (source / "world.sqlite").is_file():
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"software world has no world.sqlite: {source}",),
        )
    work = publication.with_name(publication.name + ".sg-work")
    _discard(work)
    errors: tuple[str, ...] = ()
    try:
        _writable_copy(source, work)
        world = ConstructionWorld.open(work / "world.sqlite", read_only=False)
        try:
            declare_governance_relations(world)
            for proposition in propositions:
                world.add_referent(proposition.proposition_id, label=proposition.proposition_id)
                world.assert_tuple(
                    "governance_proposition",
                    {
                        "proposition": proposition.proposition_id,
                        "statement": proposition.statement,
                        "domain_relation": proposition.domain_relation,
                    },
                    origin=ConstructionOrigin.SEMANTIC,
                    grounding=_ground(
                        proposition.observations,
                        method="governance proposition from authoritative evidence",
                        profile_id=profile_id,
                        establishment_rule=proposition.establishment_rule,
                    ),
                )
            for subject in subjects:
                world.assert_tuple(
                    "software_subject",
                    {
                        "subject": subject.subject_id,
                        "snapshot": subject.snapshot_id,
                        "kind": subject.kind,
                        "capability": subject.capability,
                        "version": subject.version,
                    },
                    origin=ConstructionOrigin.MECHANICAL,
                    grounding=_ground(
                        subject.observations,
                        method="software subject receipt",
                        profile_id=profile_id,
                    ),
                )
            for manifestation in manifestations:
                world.assert_tuple(
                    "software_manifestation",
                    {
                        "subject": manifestation.subject_id,
                        "scheme": manifestation.scheme,
                        "location": manifestation.location,
                        "capability": manifestation.capability,
                    },
                    origin=ConstructionOrigin.MECHANICAL,
                    grounding=_ground(
                        manifestation.observations,
                        method="subject-local manifestation",
                        profile_id=profile_id,
                    ),
                )
            for binding in bindings:
                world.assert_tuple(
                    "governance_binding",
                    {
                        "proposition": binding.proposition_id,
                        "software_subject": binding.software_subject,
                    },
                    origin=ConstructionOrigin.SEMANTIC,
                    grounding=_ground(
                        binding.observations,
                        method=binding.construction_method,
                        profile_id=profile_id,
                        support=binding.support,
                        endpoint_resolution=binding.endpoint_resolution,
                        software_evidence=binding.software_evidence,
                        establishment_rule=binding.establishment_rule,
                    ),
                )
            for candidate in candidates:
                world.assert_tuple(
                    "governance_candidate",
                    {
                        "proposition": candidate.proposition_id,
                        "software_subject": candidate.software_subject,
                    },
                    origin=ConstructionOrigin.SEMANTIC,
                    grounding=_ground(
                        candidate.observations,
                        method=candidate.construction_method,
                        profile_id=profile_id,
                        support=candidate.support,
                        endpoint_resolution=candidate.endpoint_resolution,
                        software_evidence=candidate.software_evidence,
                        establishment_rule=candidate.establishment_rule,
                    ),
                )
            for question in questions:
                world.assert_tuple(
                    "governance_question",
                    {
                        "proposition": question.proposition_id,
                        "state": "UNRESOLVED",
                        "question": question.question,
                    },
                    origin=ConstructionOrigin.SEMANTIC,
                    grounding=_ground(
                        _proposition_observations(world, question.proposition_id),
                        method="explicit unresolved correspondence",
                        profile_id=profile_id,
                    ),
                )
            world.assert_tuple(
                "governance_completeness",
                {
                    "capability": completeness.capability,
                    "status": completeness.status,
                    "universe": completeness.universe,
                    "basis": completeness.basis,
                },
                origin=ConstructionOrigin.MECHANICAL,
                grounding=_ground(
                    _proposition_observations(world, propositions[0].proposition_id),
                    method="construction coverage of supplied correspondences",
                    profile_id=profile_id,
                ),
            )
            for gap in completeness.known_gaps:
                world.assert_tuple(
                    "governance_known_gap",
                    {"capability": completeness.capability, "gap": gap},
                    origin=ConstructionOrigin.MECHANICAL,
                    grounding=_ground(
                        _proposition_observations(world, propositions[0].proposition_id),
                        method="construction coverage gap",
                        profile_id=profile_id,
                    ),
                )
            write_governance_evidence(work, evidence_blobs)
            from ontology_author.world.runtime.commit import write_sidecars

            write_sidecars(world)
            errors = tuple(
                [
                    *validate_governance_world(world),
                    *verify_retained_program_inputs(world),
                ]
            )
        finally:
            world.close()
        if errors:
            return GovernanceConstructionResult(succeeded=False, errors=errors)
        # Seal staging before it is ever visible at the final address, then
        # publish exclusively. The final address never exposes a writable
        # or unsealed World; failures leave no partial final bundle.
        _seal_world(work)
        publication.parent.mkdir(parents=True, exist_ok=True)
        try:
            _exclusive_rename(work, publication)
        except FileExistsError:
            return GovernanceConstructionResult(
                succeeded=False,
                errors=(f"publication address already exists: {publication}",),
            )
        except OSError as exc:
            return GovernanceConstructionResult(
                succeeded=False,
                errors=(f"publication failed: {exc}",),
            )
        return GovernanceConstructionResult(succeeded=True, world_dir=publication)
    except Exception as exc:
        return GovernanceConstructionResult(
            succeeded=False,
            errors=(f"{type(exc).__name__}: {exc}",),
        )
    finally:
        _discard(work)


def declare_governance_relations(world: ConstructionWorld) -> None:
    text = RoleType.TEXT
    referent = RoleType.REFERENT
    declared = (
        (
            "governance_proposition",
            [
                Role("proposition", referent),
                Role("statement", text),
                Role("domain_relation", text),
            ],
            "A source-derived governance proposition. Not a semantic subject.",
        ),
        (
            "governance_binding",
            [Role("proposition", referent), Role("software_subject", referent)],
            "An established correspondence from a proposition to one software subject.",
        ),
        (
            "governance_candidate",
            [Role("proposition", referent), Role("software_subject", referent)],
            "A plausible software subject that is not an established binding.",
        ),
        (
            "governance_question",
            [Role("proposition", referent), Role("state", text), Role("question", text)],
            "An explicit unresolved correspondence question.",
        ),
        (
            "governance_completeness",
            [
                Role("capability", text),
                Role("status", text),
                Role("universe", referent),
                Role("basis", text),
            ],
            "Scoped completeness for governance correspondences. Coverage of a construction run is not a domain interpretation.",
        ),
        (
            "governance_known_gap",
            [Role("capability", text), Role("gap", text)],
            "One named omission of a governance completeness claim.",
        ),
        (
            "software_subject",
            [
                Role("subject", referent),
                Role("snapshot", referent),
                Role("kind", text),
                Role("capability", text),
                Role("version", text),
            ],
            "Producer-neutral receipt for one mechanically identified software subject.",
        ),
        (
            "software_manifestation",
            [
                Role("subject", referent),
                Role("scheme", text),
                Role("location", text),
                Role("capability", text),
            ],
            "A producer-defined local manifestation. The scheme name is the producer's.",
        ),
    )
    for name, roles, description in declared:
        world.declare_relation(name, roles, description=description)


def _ground(
    observations: tuple[SourceObservation, ...],
    *,
    method: str,
    profile_id: str,
    support: str = "",
    endpoint_resolution: str = "",
    software_evidence: str = "",
    establishment_rule: str = "",
) -> AssertionGrounding:
    extra: dict[str, str] = {"contract": CONTRACT_ID, "profile_id": profile_id}
    if support or endpoint_resolution or software_evidence:
        extra["relation_support"] = support
        extra["endpoint_resolution"] = endpoint_resolution
        extra["software_evidence"] = software_evidence
    if establishment_rule:
        extra["establishment_rule"] = establishment_rule
    return AssertionGrounding(observations, construction_method=method, extra=extra)


def _proposition_observations(
    world: ConstructionWorld,
    proposition_id: str,
) -> tuple[SourceObservation, ...]:
    rows = [
        row for row in world.relation_rows("governance_proposition")
        if row["proposition"] == proposition_id
    ]
    if len(rows) != 1:
        raise ConstructionError(f"unknown proposition {proposition_id}")
    assertion_id = world._inner._store.assertion_id_for_tuple(
        "governance_proposition",
        dict(rows[0]),
    )
    warrant = world.warrant_for_assertion(assertion_id)
    observations: list[SourceObservation] = []
    for base in warrant["bases"]:
        detail = base.get("detail")
        if not isinstance(detail, dict):
            continue
        for item in detail.get("observations") or []:
            if isinstance(item, dict):
                observations.append(
                    SourceObservation(
                        provider=str(item.get("provider") or ""),
                        native_handle=str(item.get("native_handle") or ""),
                        source_revision=str(item.get("source_revision") or ""),
                        native_location=str(item.get("native_location") or ""),
                    )
                )
    if not observations:
        raise ConstructionError(f"proposition {proposition_id} has no evidence")
    return tuple(observations)


def _writable_copy(source: Path, dest: Path) -> None:
    shutil.copytree(source, dest)
    for path in dest.rglob("*"):
        mode = path.stat().st_mode
        path.chmod(mode | (0o700 if path.is_dir() else 0o600))
    dest.chmod(dest.stat().st_mode | 0o700)


def _discard(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if not path.is_dir() or path.is_symlink():
        try:
            path.chmod(path.stat().st_mode | 0o600)
        except OSError:
            pass
        try:
            path.unlink()
        except OSError:
            pass
        return
    for child in path.rglob("*"):
        child.chmod(child.stat().st_mode | (0o700 if child.is_dir() else 0o600))
    path.chmod(path.stat().st_mode | 0o700)
    shutil.rmtree(path)


def _exclusive_rename(source: Path, dest: Path) -> None:
    """Atomically publish ``source`` at ``dest`` without overwriting.

    Raises ``FileExistsError`` when ``dest`` already exists (including an
    empty directory or symlink) and ``OSError`` on other publication
    failures. On Linux, ``renameat2(RENAME_NOREPLACE)`` closes the
    check-then-rename race; elsewhere an existence check plus ``rename``
    fails safe for the deterministic cases (a non-empty existing World
    makes ``rename`` fail instead of overwriting).
    """
    if os.path.lexists(dest):
        raise FileExistsError(str(dest))
    no_replace = _rename_noreplace(source, dest)
    if no_replace is not None:
        return
    # Fallback: re-check immediately before rename. A concurrent winner
    # leaves a non-empty World, so this rename fails rather than replacing.
    if os.path.lexists(dest):
        raise FileExistsError(str(dest))
    os.rename(source, dest)


def _rename_noreplace(source: Path, dest: Path) -> bool | None:
    """Try Linux renameat2 NOREPLACE. Returns True, or None to fall back."""
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

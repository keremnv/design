"""Git-backed governed-candidate evaluation.

This module is an application workflow boundary around the existing program
spine, authority, case, and adjudication contracts. Git is used only as the
v0 immutable source materialization mechanism. It does not add Git concepts to
the World model, mutate repository refs, or adopt a candidate.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tarfile
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ontology_author.authority import (
    assemble_governance_case,
    assess_attachment_maintenance,
    assess_authority_change_impact,
    markdown_sources_from_root,
    write_case,
    write_impact,
    write_maintenance,
)
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.authority.governance import (
    validate_case_sidecar,
    validate_impact_sidecar,
    validate_maintenance_sidecar,
)
from ontology_author.program_spine import (
    TypeScriptBoundary,
    build_typescript_spine,
    compare_program_spines,
)
from ontology_author.world.runtime.world import ConstructionWorld

from .adjudication import (
    load_governance_adjudication,
    validate_governance_adjudication,
    write_governance_adjudication,
)
from .model_adjudicator import (
    AdjudicatorTransport,
    ModelAdjudicatorConfig,
    adjudicate_governance_case,
)

CANDIDATE_EVALUATION_SCHEMA = "governed_candidate_evaluation/v0"
CANDIDATE_EVALUATION_VERSION = 0
ADOPTION_POLICY_SCHEMA = "adoption_policy/v0"
ADOPTION_POLICY_VERSION = 0
ADOPTION_DECISION_SCHEMA = "candidate_adoption/v0"
ADOPTION_DECISION_VERSION = 0
REVISION_BRIEF_SCHEMA = "governance_revision/v0"
REVISION_BRIEF_VERSION = 0

ADOPTION_OUTCOMES = {
    "ADOPT",
    "REVISION_REQUIRED",
    "APPROVAL_REQUIRED",
    "CONTEXT_REQUIRED",
    "ESCALATE",
}
CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION = "SEMANTIC_CONSTRUCTION"
CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT = "ADJUDICATION_CONTEXT"
REASON_REQUIRED_SEMANTIC_CONSTRUCTION = "REQUIRED_SEMANTIC_CONSTRUCTION"
REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT = "ADJUDICATOR_INSUFFICIENT_CONTEXT"
SEMANTIC_CONSTRUCTION_POLICY_RULE = "pre_adjudication_construction_required"
DECISION_RIGHTS = {
    "DELEGATED",
    "CONSTRAINED",
    "PROHIBITED",
    "APPROVAL_REQUIRED",
    "UNKNOWN",
    "NOT_ESTABLISHED",
}
ADJUDICATION_STATES = {
    "RESOLVED",
    "UNRESOLVED",
    "AUTHORITY_CONFLICT",
    "INSUFFICIENT_CONTEXT",
}
DEFAULT_POLICY_ID = "conservative-adoption/v0"
DEFAULT_DELEGATION_POLICY_ID = "complete-universe-default-delegation/v0"


class CandidateEvaluationError(ValueError):
    """A Git candidate cannot be evaluated under the application contract."""


class GitResolutionError(CandidateEvaluationError):
    """A requested Git object is not an immutable commit or tree."""


class BaselineBindingError(CandidateEvaluationError):
    """The governed baseline World is not bound to the requested Git state."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def _copy(value: Any) -> Any:
    return json.loads(_canonical_json(value))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:32]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CandidateEvaluationError(f"invalid JSON artifact: {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise CandidateEvaluationError(f"JSON artifact must be an object: {path}")
    return dict(payload)


@dataclass(frozen=True)
class GitSnapshot:
    """Resolved immutable Git source identity.

    ``tree`` is the source-state identity. ``commit`` and ``parents`` are
    workflow provenance and may be absent when the caller supplied a tree.
    """

    requested_ref: str
    object_id: str
    object_type: str
    commit: str | None
    tree: str
    parents: tuple[str, ...] = ()

    @property
    def snapshot_id(self) -> str:
        return f"git-tree:{self.tree}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_ref": self.requested_ref,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "commit": self.commit,
            "tree": self.tree,
            "snapshot_id": self.snapshot_id,
            "parents": list(self.parents),
        }


class GitRepository:
    """Read-only Git adapter for immutable commits and trees."""

    def __init__(self, repository: Path | str = ".") -> None:
        self.path = Path(repository).resolve()
        try:
            root = self._run("rev-parse", "--show-toplevel").decode().strip()
        except GitResolutionError as exc:
            raise GitResolutionError(f"not a Git repository: {self.path}") from exc
        self.root = Path(root).resolve()

    def _run(self, *arguments: str) -> bytes:
        process = subprocess.run(
            ["git", *arguments],
            cwd=getattr(self, "root", self.path),
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            detail = process.stderr.decode("utf-8", errors="replace").strip()
            raise GitResolutionError(detail or f"git command failed: {' '.join(arguments)}")
        return process.stdout

    def current_branch(self) -> str | None:
        process = subprocess.run(
            ["git", "symbolic-ref", "--short", "-q", "HEAD"],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        branch = process.stdout.decode("utf-8", errors="replace").strip()
        return branch or None

    def resolve(self, reference: str) -> GitSnapshot:
        requested = str(reference).strip()
        if not requested:
            raise GitResolutionError("Git reference is empty")
        try:
            commit = self._run("rev-parse", "--verify", f"{requested}^{{commit}}").decode().strip()
        except GitResolutionError:
            commit = ""
        if commit:
            tree = self._run("rev-parse", "--verify", f"{commit}^{{tree}}").decode().strip()
            parents_line = self._run("rev-list", "--parents", "-n", "1", commit).decode().strip().split()
            return GitSnapshot(
                requested_ref=requested,
                object_id=commit,
                object_type="commit",
                commit=commit,
                tree=tree,
                parents=tuple(parents_line[1:]),
            )
        try:
            tree = self._run("rev-parse", "--verify", f"{requested}^{{tree}}").decode().strip()
        except GitResolutionError as exc:
            raise GitResolutionError(f"Git reference is not a commit or tree: {requested}") from exc
        return GitSnapshot(
            requested_ref=requested,
            object_id=tree,
            object_type="tree",
            commit=None,
            tree=tree,
        )

    def blob(self, snapshot: GitSnapshot, relative_path: str) -> bytes:
        relative = _safe_repo_relative(relative_path)
        try:
            return self._run("show", f"{snapshot.tree}:{relative}")
        except GitResolutionError as exc:
            raise GitResolutionError(
                f"Git tree {snapshot.tree} has no readable blob at {relative}"
            ) from exc

    @contextmanager
    def materialize(self, snapshot: GitSnapshot, *, prefix: str = "governance-git-") -> Iterator[Path]:
        """Materialize exactly one Git tree in an isolated temporary directory."""

        with tempfile.TemporaryDirectory(prefix=prefix) as temporary:
            destination = Path(temporary)
            self._archive(snapshot, destination)
            yield destination

    def _archive(self, snapshot: GitSnapshot, destination: Path) -> None:
        process = subprocess.Popen(
            ["git", "archive", "--format=tar", snapshot.tree],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        try:
            with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
                for member in archive:
                    _extract_archive_member(archive, member, destination)
        finally:
            process.stdout.close()
        stderr = process.stderr.read() if process.stderr is not None else b""
        return_code = process.wait()
        if return_code != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise GitResolutionError(detail or f"could not archive Git tree {snapshot.tree}")


def _safe_repo_relative(value: str) -> str:
    candidate = PurePosixPath(str(value).replace("\\", "/"))
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise GitResolutionError(f"unsafe repository-relative path: {value!r}")
    return candidate.as_posix()


def _safe_archive_target(destination: Path, name: str) -> Path:
    candidate = PurePosixPath(name)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise GitResolutionError(f"Git archive contains unsafe path: {name!r}")
    target = (destination / Path(*candidate.parts)).resolve()
    try:
        target.relative_to(destination.resolve())
    except ValueError as exc:
        raise GitResolutionError(f"Git archive escapes materialization root: {name!r}") from exc
    return target


def _safe_archive_link(name: str) -> str:
    link = PurePosixPath(name)
    if link.is_absolute() or any(part in {"", ".", ".."} for part in link.parts):
        raise GitResolutionError(f"Git archive contains unsafe link: {name!r}")
    return link.as_posix()


def _extract_archive_member(archive: tarfile.TarFile, member: tarfile.TarInfo, destination: Path) -> None:
    target = _safe_archive_target(destination, member.name)
    if member.isdir():
        target.mkdir(parents=True, exist_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if member.issym():
        link = _safe_archive_link(member.linkname)
        if target.exists() or target.is_symlink():
            target.unlink()
        os.symlink(link, target)
        return
    if member.islnk():
        link_target = _safe_archive_target(destination, member.linkname)
        if not link_target.exists():
            raise GitResolutionError(f"Git archive hard-link target is missing: {member.linkname!r}")
        target.write_bytes(link_target.read_bytes())
        return
    if not member.isfile():
        raise GitResolutionError(f"unsupported Git archive member: {member.name!r}")
    source = archive.extractfile(member)
    if source is None:
        raise GitResolutionError(f"Git archive member has no data: {member.name!r}")
    target.write_bytes(source.read())
    try:
        target.chmod(member.mode & 0o777)
    except OSError:
        pass


@dataclass(frozen=True)
class AdoptionPolicy:
    """Small declarative workflow profile; not an expression language."""

    policy_id: str = DEFAULT_POLICY_ID
    version: str = "v0"
    on_insufficient_context: str = "CONTEXT_REQUIRED"
    on_authority_conflict: str = "ESCALATE"
    on_unresolved: str = "ESCALATE"
    on_approval_required: str = "APPROVAL_REQUIRED"
    on_prohibited: str = "REVISION_REQUIRED"
    on_conformance_conflict: str = "REVISION_REQUIRED"
    on_unknown_decision_right: str = "ESCALATE"
    on_delegated: str = "ADOPT"
    on_constrained_conforming: str = "ADOPT"
    not_established_fallback: str = "ESCALATE"
    max_candidate_iterations: int = 3

    @classmethod
    def default_delegation(cls, *, max_candidate_iterations: int = 3) -> AdoptionPolicy:
        return cls(
            policy_id=DEFAULT_DELEGATION_POLICY_ID,
            not_established_fallback="DEFAULT_DELEGATION",
            max_candidate_iterations=max_candidate_iterations,
        )

    @classmethod
    def from_value(cls, value: AdoptionPolicy | Mapping[str, Any] | str | None) -> AdoptionPolicy:
        if value is None:
            return cls()
        if isinstance(value, cls):
            policy = value
        elif isinstance(value, str):
            normalized = value.strip()
            if normalized in {DEFAULT_DELEGATION_POLICY_ID, "default-delegation", "default_delegation"}:
                policy = cls.default_delegation()
            elif normalized in {DEFAULT_POLICY_ID, "conservative", "conservative-v0"}:
                policy = cls()
            else:
                policy = cls.from_value(_read_json(Path(normalized)))
        elif isinstance(value, Mapping):
            raw = dict(value)
            if raw.get("contract") not in {None, ADOPTION_POLICY_SCHEMA}:
                raise CandidateEvaluationError(
                    f"AdoptionPolicy contract is not {ADOPTION_POLICY_SCHEMA}"
                )
            mappings = raw.get("mappings")
            if isinstance(mappings, Mapping):
                raw = {**raw, **dict(mappings)}
            aliases = {
                "default_freedom": "not_established_fallback",
                "on_not_established": "not_established_fallback",
                "on_conflict": "on_conformance_conflict",
                "max_iterations": "max_candidate_iterations",
            }
            for old, new in aliases.items():
                if old in raw and new not in raw:
                    raw[new] = raw[old]
            allowed = {
                "policy_id",
                "version",
                "on_insufficient_context",
                "on_authority_conflict",
                "on_unresolved",
                "on_approval_required",
                "on_prohibited",
                "on_conformance_conflict",
                "on_unknown_decision_right",
                "on_delegated",
                "on_constrained_conforming",
                "not_established_fallback",
                "max_candidate_iterations",
                "contract",
                "policy_version",
                "mappings",
                *aliases,
            }
            unknown = sorted(set(raw) - allowed)
            if unknown:
                raise CandidateEvaluationError("AdoptionPolicy has unknown fields: " + ", ".join(unknown))
            policy = cls(
                policy_id=str(raw.get("policy_id") or DEFAULT_POLICY_ID),
                version=str(raw.get("version") or raw.get("policy_version") or "v0"),
                **{
                    key: raw[key]
                    for key in (
                        "on_insufficient_context",
                        "on_authority_conflict",
                        "on_unresolved",
                        "on_approval_required",
                        "on_prohibited",
                        "on_conformance_conflict",
                        "on_unknown_decision_right",
                        "on_delegated",
                        "on_constrained_conforming",
                        "not_established_fallback",
                        "max_candidate_iterations",
                    )
                    if key in raw
                },
            )
        else:
            raise CandidateEvaluationError("AdoptionPolicy must be a profile, mapping, path, or None")
        errors = policy.validate()
        if errors:
            raise CandidateEvaluationError("invalid AdoptionPolicy: " + "; ".join(errors))
        return policy

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.policy_id.strip():
            errors.append("policy_id is empty")
        if not self.version.strip():
            errors.append("policy version is empty")
        for field_name in (
            "on_insufficient_context",
            "on_authority_conflict",
            "on_unresolved",
            "on_approval_required",
            "on_prohibited",
            "on_conformance_conflict",
            "on_unknown_decision_right",
            "on_delegated",
            "on_constrained_conforming",
        ):
            value = getattr(self, field_name)
            if value not in ADOPTION_OUTCOMES:
                errors.append(f"{field_name} is not an adoption outcome: {value}")
        if self.not_established_fallback not in {"ESCALATE", "DEFAULT_DELEGATION"}:
            errors.append(
                "not_established_fallback must be ESCALATE or DEFAULT_DELEGATION"
            )
        if isinstance(self.max_candidate_iterations, bool) or not isinstance(self.max_candidate_iterations, int):
            errors.append("max_candidate_iterations must be an integer")
        elif self.max_candidate_iterations < 1:
            errors.append("max_candidate_iterations must be positive")
        return sorted(set(errors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": ADOPTION_POLICY_SCHEMA,
            "policy_id": self.policy_id,
            "version": self.version,
            "mappings": {
                "on_insufficient_context": self.on_insufficient_context,
                "on_authority_conflict": self.on_authority_conflict,
                "on_unresolved": self.on_unresolved,
                "on_approval_required": self.on_approval_required,
                "on_prohibited": self.on_prohibited,
                "on_conformance_conflict": self.on_conformance_conflict,
                "on_unknown_decision_right": self.on_unknown_decision_right,
                "on_delegated": self.on_delegated,
                "on_constrained_conforming": self.on_constrained_conforming,
                "not_established_fallback": self.not_established_fallback,
            },
            "max_candidate_iterations": self.max_candidate_iterations,
        }


@dataclass(frozen=True)
class CandidateEvaluation:
    """Application-level provenance record for one baseline/candidate pair."""

    evaluation_id: str
    task_id: str
    task_content_digest: str
    baseline_commit: str | None
    baseline_tree: str
    candidate_commit: str | None
    candidate_tree: str
    candidate_iteration: int
    parent_candidate_commit: str | None
    baseline_snapshot_id: str
    candidate_snapshot_id: str
    baseline_program_snapshot_id: str
    candidate_program_snapshot_id: str
    comparison_id: str
    case_id: str
    adjudication_id: str = ""
    adoption_decision_id: str = ""
    revision_brief_id: str = ""
    coding_agent: Mapping[str, Any] | None = None
    git_provenance: Mapping[str, Any] | None = None
    baseline_world_binding: Mapping[str, Any] | None = None
    adjudicator: Mapping[str, Any] | None = None
    adjudication_invocation_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": CANDIDATE_EVALUATION_SCHEMA,
            "version": CANDIDATE_EVALUATION_VERSION,
            "evaluation_id": self.evaluation_id,
            "task_id": self.task_id,
            "task_content_digest": self.task_content_digest,
            "baseline_commit": self.baseline_commit,
            "baseline_tree": self.baseline_tree,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "candidate_iteration": self.candidate_iteration,
            "parent_candidate_commit": self.parent_candidate_commit,
            "baseline_snapshot_id": self.baseline_snapshot_id,
            "candidate_snapshot_id": self.candidate_snapshot_id,
            "baseline_program_snapshot_id": self.baseline_program_snapshot_id,
            "candidate_program_snapshot_id": self.candidate_program_snapshot_id,
            "comparison_id": self.comparison_id,
            "case_id": self.case_id,
            "adjudication_id": self.adjudication_id,
            "adoption_decision_id": self.adoption_decision_id,
            "revision_brief_id": self.revision_brief_id,
            "coding_agent": _copy(self.coding_agent or {}),
            "git_provenance": _copy(self.git_provenance or {}),
            "baseline_world_binding": _copy(self.baseline_world_binding or {}),
            "adjudicator": _copy(self.adjudicator or {}),
            "adjudication_invocation_ref": self.adjudication_invocation_ref,
        }


@dataclass(frozen=True)
class CandidateAdoptionDecision:
    """Deterministic workflow application of policy to one adjudication."""

    payload: Mapping[str, Any]

    @property
    def decision_id(self) -> str:
        return str(self.payload.get("decision_id") or "")

    @property
    def outcome(self) -> str:
        return str(self.payload.get("outcome") or "")

    def to_dict(self) -> dict[str, Any]:
        return _copy(self.payload)


@dataclass(frozen=True)
class CandidateEvaluationResult:
    """Return value for the manually driven vertical slice."""

    candidate: Mapping[str, Any]
    comparison: Mapping[str, Any]
    maintenance: Mapping[str, Any]
    impact: Mapping[str, Any]
    case: Mapping[str, Any]
    adjudication: Mapping[str, Any]
    adoption_decision: Mapping[str, Any]
    revision_brief: Mapping[str, Any] | None
    artifacts: Mapping[str, str]
    readiness: Mapping[str, Any] | None = None
    adjudicator_invoked: bool = False
    constructor_invoked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": _copy(self.candidate),
            "comparison": _copy(self.comparison),
            "maintenance": _copy(self.maintenance),
            "impact": _copy(self.impact),
            "case": _copy(self.case),
            "adjudication": _copy(self.adjudication),
            "adoption_decision": _copy(self.adoption_decision),
            "revision_brief": _copy(self.revision_brief) if self.revision_brief is not None else None,
            "artifacts": dict(self.artifacts),
            "readiness": _copy(self.readiness) if self.readiness is not None else None,
            "adjudicator_invoked": self.adjudicator_invoked,
            "constructor_invoked": False,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]


def _policy_result(policy: AdoptionPolicy, field_name: str) -> str:
    value = getattr(policy, field_name)
    if value not in ADOPTION_OUTCOMES:
        raise CandidateEvaluationError(f"invalid policy outcome for {field_name}: {value}")
    return value


def _complete_attachment_coverage(case: Mapping[str, Any]) -> bool:
    basis = ((case.get("assembly") or {}).get("completeness_basis") or {})
    if not isinstance(basis, Mapping) or str(basis.get("status") or "") != "COMPLETE":
        return False
    gaps = basis.get("known_gaps") or []
    return not gaps


def _conformance_summary(adjudication: Mapping[str, Any]) -> dict[str, Any]:
    findings = adjudication.get("conformance_findings") or []
    counts: dict[str, int] = {}
    for item in findings:
        result = str(item.get("result") or "")
        counts[result] = counts.get(result, 0) + 1
    return {
        "counts": dict(sorted(counts.items())),
        "applicable_items": len(findings),
        "conflicts": counts.get("CONFLICTS", 0),
        "unknown": counts.get("UNKNOWN", 0),
    }


def _readiness_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return _copy(value.to_dict())
    if isinstance(value, Mapping):
        return _copy(value)
    raise CandidateEvaluationError("readiness must be a mapping or GovernanceCaseReadiness")


def _semantic_construction_requirement(readiness: Mapping[str, Any]) -> dict[str, Any]:
    required = list(readiness.get("required_construction_obligations") or [])
    obligation_ids = [
        str(item.get("obligation_id") or "")
        for item in required
        if str(item.get("obligation_id") or "")
    ]
    gap_ids = [
        str(item.get("source_gap_id") or "")
        for item in required
        if str(item.get("source_gap_id") or "")
    ]
    derivation_ids = sorted(
        {
            str((item.get("causal_chain") or {}).get("derivation_id") or "")
            for item in required
            if str((item.get("causal_chain") or {}).get("derivation_id") or "")
        }
    )
    return {
        "kind": CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION,
        "reason": REASON_REQUIRED_SEMANTIC_CONSTRUCTION,
        "required_obligation_ids": obligation_ids,
        "source_gap_ids": gap_ids,
        "requesting_derivation_ids": derivation_ids,
        "readiness_status": str(readiness.get("status") or ""),
        "required_construction_obligations": _copy(required),
        "causal_chain": _copy([item.get("causal_chain") or {} for item in required]),
        "adjudicator_invoked": False,
        "constructor_invoked": False,
        "model_invoked": False,
        "coding_agent_revision_instructions": None,
        "program_baseline_promoted": False,
        "candidate_mutated": False,
    }


def _adjudication_context_requirement(
    adjudication: Mapping[str, Any], *, state: str
) -> dict[str, Any]:
    return {
        "kind": CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT,
        "reason": REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT,
        "required_obligation_ids": [],
        "source_gap_ids": [],
        "requesting_derivation_ids": [],
        "readiness_status": None,
        "required_construction_obligations": [],
        "causal_chain": [],
        "adjudication_id": str(adjudication.get("adjudication_id") or ""),
        "adjudication_state": state,
        "context_requests": _copy(adjudication.get("context_requests") or []),
        "adjudicator_invoked": True,
        "constructor_invoked": False,
        "model_invoked": False,
        "coding_agent_revision_instructions": None,
        "program_baseline_promoted": False,
        "candidate_mutated": False,
    }


def _is_semantic_construction_decision(payload: Mapping[str, Any]) -> bool:
    requirement = payload.get("context_requirement") or {}
    return (
        payload.get("outcome") == "CONTEXT_REQUIRED"
        and isinstance(requirement, Mapping)
        and str(requirement.get("kind") or "") == CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
    )


def decide_semantic_construction_required(
    case: Mapping[str, Any],
    readiness: Mapping[str, Any] | Any,
    *,
    candidate: Mapping[str, Any] | None = None,
    policy: AdoptionPolicy | Mapping[str, Any] | str | None = None,
) -> CandidateAdoptionDecision:
    """Return CONTEXT_REQUIRED for required semantic construction. Does not adjudicate."""

    selected = AdoptionPolicy.from_value(policy)
    readiness_payload = _readiness_mapping(readiness)
    if str(readiness_payload.get("status") or "") != "CONSTRUCTION_REQUIRED":
        raise CandidateEvaluationError(
            "semantic construction CONTEXT_REQUIRED requires CONSTRUCTION_REQUIRED readiness"
        )
    if not (readiness_payload.get("required_construction_obligations") or readiness_payload.get("unmatched_material_gaps")):
        raise CandidateEvaluationError(
            "semantic construction CONTEXT_REQUIRED requires at least one required obligation"
        )
    requirement = _semantic_construction_requirement(readiness_payload)
    if not requirement["required_obligation_ids"]:
        raise CandidateEvaluationError(
            "semantic construction CONTEXT_REQUIRED requires formulated obligation IDs"
        )
    candidate_values = dict(candidate or {})
    body = {
        "contract": ADOPTION_DECISION_SCHEMA,
        "version": ADOPTION_DECISION_VERSION,
        "task_id": candidate_values.get("task_id"),
        "candidate_evaluation_id": candidate_values.get("evaluation_id"),
        "candidate_iteration": candidate_values.get("candidate_iteration"),
        "baseline_snapshot_id": candidate_values.get("baseline_snapshot_id"),
        "candidate_snapshot_id": candidate_values.get("candidate_snapshot_id"),
        "candidate": candidate_values,
        "adjudication_id": "",
        "adoption_policy": selected.to_dict(),
        "outcome": "CONTEXT_REQUIRED",
        "context_requirement": requirement,
        "basis": {
            "adjudication_state": None,
            "conformance_summary": {
                "counts": {},
                "applicable_items": 0,
                "conflicts": 0,
                "unknown": 0,
            },
            "decision_right": {},
            "authority_conflicts": [],
            "context_requests": [],
            "explicit_fallback_policy_used": None,
            "completeness_receipt": _copy(
                (case.get("assembly") or {}).get("completeness_basis") or {}
            ),
            "policy_rules_applied": [SEMANTIC_CONSTRUCTION_POLICY_RULE],
            "readiness_status": "CONSTRUCTION_REQUIRED",
            "case_id": case.get("case_id"),
        },
        "revision_brief_ref": None,
        "known_limitations": [],
    }
    body["decision_id"] = "decision:" + _digest(body)
    return CandidateAdoptionDecision(body)


def decide_candidate_adoption(
    case: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    policy: AdoptionPolicy | Mapping[str, Any] | str | None = None,
    *,
    candidate: Mapping[str, Any] | None = None,
) -> CandidateAdoptionDecision:
    """Apply a declared policy to a valid adjudication without side effects."""

    errors = validate_governance_adjudication(adjudication, case)
    if errors:
        raise CandidateEvaluationError(
            "cannot apply adoption policy to invalid adjudication: " + "; ".join(errors)
        )
    selected = AdoptionPolicy.from_value(policy)
    state = str(adjudication.get("adjudication_state") or "")
    right = adjudication.get("decision_right") or {}
    right_outcome = str(right.get("outcome") or "")
    summary = _conformance_summary(adjudication)
    conflicts = adjudication.get("authority_conflicts") or []
    context_requests = adjudication.get("context_requests") or []
    rules: list[str] = []
    fallback_used: str | None = None

    if state == "INSUFFICIENT_CONTEXT":
        outcome = _policy_result(selected, "on_insufficient_context")
        rules.append("on_insufficient_context")
    elif state == "AUTHORITY_CONFLICT":
        outcome = _policy_result(selected, "on_authority_conflict")
        rules.append("on_authority_conflict")
    elif state == "UNRESOLVED":
        outcome = _policy_result(selected, "on_unresolved")
        rules.append("on_unresolved")
    elif right_outcome == "APPROVAL_REQUIRED":
        outcome = _policy_result(selected, "on_approval_required")
        rules.append("on_approval_required")
    elif right_outcome == "PROHIBITED":
        outcome = _policy_result(selected, "on_prohibited")
        rules.append("on_prohibited")
    elif summary["conflicts"]:
        outcome = _policy_result(selected, "on_conformance_conflict")
        rules.append("on_conformance_conflict")
    elif right_outcome == "UNKNOWN":
        outcome = _policy_result(selected, "on_unknown_decision_right")
        rules.append("on_unknown_decision_right")
    elif right_outcome == "NOT_ESTABLISHED":
        if (
            str(case.get("case_result") or "") == "NO_APPLICABLE_AUTHORITY"
            and _complete_attachment_coverage(case)
            and selected.not_established_fallback == "DEFAULT_DELEGATION"
        ):
            outcome = "ADOPT"
            fallback_used = "DEFAULT_DELEGATION"
            rules.append("complete_universe_default_delegation")
        else:
            outcome = "ESCALATE" if selected.not_established_fallback == "DEFAULT_DELEGATION" else selected.not_established_fallback
            rules.append("not_established_fallback")
    elif right_outcome == "DELEGATED":
        outcome = _policy_result(selected, "on_delegated")
        rules.append("decision_right_delegated_without_conflict")
    elif right_outcome == "CONSTRAINED":
        outcome = _policy_result(selected, "on_constrained_conforming")
        rules.append("decision_right_constrained_conforming")
    else:
        outcome = "ESCALATE"
        rules.append("unrecognized_decision_right")

    if outcome not in ADOPTION_OUTCOMES:
        raise CandidateEvaluationError(f"policy produced invalid adoption outcome: {outcome}")
    candidate_values = dict(candidate or {})
    context_requirement = None
    if outcome == "CONTEXT_REQUIRED":
        context_requirement = _adjudication_context_requirement(
            adjudication, state=state
        )
    basis = {
        "adjudication_state": state,
        "conformance_summary": summary,
        "decision_right": _copy(right),
        "authority_conflicts": _copy(conflicts),
        "context_requests": _copy(context_requests),
        "explicit_fallback_policy_used": fallback_used,
        "completeness_receipt": _copy(
            (case.get("assembly") or {}).get("completeness_basis") or {}
        ),
        "policy_rules_applied": rules,
    }
    body = {
        "contract": ADOPTION_DECISION_SCHEMA,
        "version": ADOPTION_DECISION_VERSION,
        "task_id": candidate_values.get("task_id"),
        "candidate_evaluation_id": candidate_values.get("evaluation_id"),
        "candidate_iteration": candidate_values.get("candidate_iteration"),
        "baseline_snapshot_id": candidate_values.get("baseline_snapshot_id"),
        "candidate_snapshot_id": candidate_values.get("candidate_snapshot_id"),
        "candidate": candidate_values,
        "adjudication_id": str(adjudication.get("adjudication_id") or ""),
        "adoption_policy": selected.to_dict(),
        "outcome": outcome,
        "context_requirement": context_requirement,
        "basis": basis,
        "revision_brief_ref": None,
        "known_limitations": _copy(adjudication.get("known_limitations") or []),
    }
    body["decision_id"] = "decision:" + _digest(body)
    return CandidateAdoptionDecision(body)


def validate_candidate_adoption_decision(
    payload: Mapping[str, Any],
    case: Mapping[str, Any],
    adjudication: Mapping[str, Any] | None = None,
    policy: AdoptionPolicy | Mapping[str, Any] | str | None = None,
) -> list[str]:
    """Validate workflow receipt structure and policy-derived facts."""

    errors: list[str] = []
    if payload.get("contract") != ADOPTION_DECISION_SCHEMA:
        errors.append(f"decision contract is not {ADOPTION_DECISION_SCHEMA}")
    if payload.get("version") != ADOPTION_DECISION_VERSION:
        errors.append("unsupported adoption decision version")
    if payload.get("outcome") not in ADOPTION_OUTCOMES:
        errors.append(f"invalid adoption outcome: {payload.get('outcome')}")
    selected = AdoptionPolicy.from_value(policy)
    recorded = payload.get("adoption_policy") or {}
    if recorded.get("policy_id") != selected.policy_id or recorded.get("version") != selected.version:
        errors.append("decision policy identity does not match selected policy")
    if not str(payload.get("decision_id") or "").strip():
        errors.append("decision_id is empty")
    if payload.get("outcome") != "REVISION_REQUIRED" and payload.get("revision_brief_ref") is not None:
        errors.append("revision_brief_ref is only valid for REVISION_REQUIRED")
    if _is_semantic_construction_decision(payload):
        requirement = payload.get("context_requirement") or {}
        if payload.get("adjudication_id"):
            errors.append("semantic construction CONTEXT_REQUIRED must not cite an adjudication")
        if requirement.get("adjudicator_invoked") is not False:
            errors.append("semantic construction CONTEXT_REQUIRED must not invoke the adjudicator")
        if requirement.get("constructor_invoked") is not False:
            errors.append("semantic construction CONTEXT_REQUIRED must not invoke a constructor")
        if requirement.get("coding_agent_revision_instructions") is not None:
            errors.append("semantic construction CONTEXT_REQUIRED must not include code revision instructions")
        blob = str(payload).lower()
        if "modify the candidate source" in blob or "change the candidate program" in blob:
            errors.append("semantic construction CONTEXT_REQUIRED includes coding-agent revision instructions")
        try:
            expected = decide_semantic_construction_required(
                case,
                {
                    "status": requirement.get("readiness_status"),
                    "required_construction_obligations": requirement.get(
                        "required_construction_obligations"
                    )
                    or [],
                },
                candidate=payload.get("candidate"),
                policy=selected,
            )
            if expected.outcome != payload.get("outcome"):
                errors.append("decision outcome is not the result of semantic construction readiness")
            if expected.decision_id != payload.get("decision_id"):
                errors.append("decision_id is not the deterministic semantic construction result")
            if expected.payload.get("context_requirement") != payload.get("context_requirement"):
                errors.append("context_requirement is not the result of semantic construction readiness")
        except CandidateEvaluationError as exc:
            errors.append(str(exc))
        return sorted(set(errors))
    if adjudication is None:
        errors.append("adjudication is required except for semantic construction CONTEXT_REQUIRED")
        return sorted(set(errors))
    if payload.get("adjudication_id") != adjudication.get("adjudication_id"):
        errors.append("decision adjudication_id does not match adjudication")
    try:
        expected = decide_candidate_adoption(case, adjudication, selected, candidate=payload.get("candidate"))
        if expected.outcome != payload.get("outcome"):
            errors.append("decision outcome is not the result of the declared policy")
        if expected.decision_id != payload.get("decision_id"):
            errors.append("decision_id is not the deterministic result of the declared policy")
        expected_basis = expected.payload.get("basis") or {}
        if payload.get("basis") != expected_basis:
            errors.append("decision basis is not the result of the declared policy")
        if payload.get("context_requirement") != expected.payload.get("context_requirement"):
            errors.append("context_requirement is not the result of the declared policy")
        if payload.get("outcome") != "REVISION_REQUIRED" and payload.get("revision_brief_ref") is not None:
            errors.append("revision_brief_ref is only valid for REVISION_REQUIRED")
    except CandidateEvaluationError as exc:
        errors.append(str(exc))
    return sorted(set(errors))


def write_candidate_adoption(
    payload: Mapping[str, Any],
    output_dir: Path | str,
    *,
    case: Mapping[str, Any] | None = None,
    adjudication: Mapping[str, Any] | None = None,
    policy: AdoptionPolicy | Mapping[str, Any] | str | None = None,
) -> Path:
    if _is_semantic_construction_decision(payload):
        if case is None:
            raise CandidateEvaluationError(
                "semantic construction CONTEXT_REQUIRED requires the GovernanceCase"
            )
        errors = validate_candidate_adoption_decision(
            payload,
            case,
            None,
            policy or payload.get("adoption_policy") or {},
        )
        if errors:
            raise CandidateEvaluationError("cannot write invalid adoption decision: " + "; ".join(errors))
    elif case is not None or adjudication is not None:
        if case is None or adjudication is None:
            raise CandidateEvaluationError(
                "case and adjudication are both required for decision validation"
            )
        errors = validate_candidate_adoption_decision(
            payload,
            case,
            adjudication,
            policy or payload.get("adoption_policy") or {},
        )
        if errors:
            raise CandidateEvaluationError("cannot write invalid adoption decision: " + "; ".join(errors))
    else:
        if payload.get("contract") != ADOPTION_DECISION_SCHEMA:
            raise CandidateEvaluationError("cannot write invalid adoption decision contract")
        if payload.get("version") != ADOPTION_DECISION_VERSION:
            raise CandidateEvaluationError("cannot write unsupported adoption decision version")
        if payload.get("outcome") not in ADOPTION_OUTCOMES:
            raise CandidateEvaluationError("cannot write invalid adoption decision outcome")
        AdoptionPolicy.from_value(policy or payload.get("adoption_policy") or {})
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "candidate.adoption.json"
    path.write_text(_pretty_json(payload), encoding="utf-8")
    return path


def _finding_ids_for_revision(adjudication: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    conformance = adjudication.get("conformance_findings") or []
    selected = [item for item in conformance if item.get("result") in {"CONFLICTS", "UNKNOWN"}]
    if not selected:
        selected = list(conformance)
    authority_ids = {
        str(ref)
        for item in selected
        for ref in item.get("authority_finding_refs") or []
        if str(ref).strip()
    }
    program_ids = {
        str(ref)
        for item in selected
        for ref in item.get("program_finding_refs") or []
        if str(ref).strip()
    }
    return authority_ids, program_ids


def build_governance_revision_brief(
    task: str,
    case: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    decision: CandidateAdoptionDecision | Mapping[str, Any],
    *,
    candidate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build bounded deterministic revision feedback from existing artifacts."""

    decision_payload = decision.to_dict() if isinstance(decision, CandidateAdoptionDecision) else _copy(decision)
    if decision_payload.get("outcome") != "REVISION_REQUIRED":
        raise CandidateEvaluationError("revision brief requires REVISION_REQUIRED")
    authority_refs, program_refs = _finding_ids_for_revision(adjudication)
    authority_findings = {
        str(item.get("finding_id") or ""): item
        for item in adjudication.get("authority_findings") or []
        if item.get("finding_id")
    }
    program_findings = {
        str(item.get("finding_id") or ""): item
        for item in adjudication.get("program_findings") or []
        if item.get("finding_id")
    }
    authority_observations = {
        str(item.get("observation_id") or ""): item
        for item in (case.get("authority") or {}).get("observations") or []
        if item.get("observation_id")
    }

    if authority_refs:
        selected_authority = [authority_findings[key] for key in sorted(authority_refs) if key in authority_findings]
    else:
        selected_authority = list(authority_findings.values())
    if program_refs:
        selected_program = [program_findings[key] for key in sorted(program_refs) if key in program_findings]
    else:
        selected_program = list(program_findings.values())
    authority_output = []
    for finding in sorted(selected_authority, key=lambda item: str(item.get("finding_id") or "")):
        observations = [
            {
                "observation_id": observation_id,
                "standing": authority_observations.get(observation_id, {}).get("standing"),
                "exact_authoritative_text": authority_observations.get(observation_id, {}).get("reconstructed_text", ""),
            }
            for observation_id in sorted(str(item) for item in finding.get("observation_ids") or [])
            if observation_id in authority_observations
        ]
        authority_output.append(
            {
                "finding_id": finding.get("finding_id"),
                "applicability": finding.get("applicability"),
                "interpretation_summary": finding.get("interpretation_summary"),
                "relevant_qualifiers": _copy(finding.get("relevant_qualifiers") or []),
                "evidence_refs": [
                    {"kind": "authority_observation", "id": item["observation_id"]}
                    for item in observations
                ],
                "observations": observations,
            }
        )
    program_output = [
        {
            "finding_id": finding.get("finding_id"),
            "proposition": finding.get("proposition"),
            "truth_value": finding.get("truth_value"),
            "basis": finding.get("basis"),
            "evidence_refs": _copy(finding.get("evidence_refs") or []),
        }
        for finding in sorted(selected_program, key=lambda item: str(item.get("finding_id") or ""))
    ]
    conformance_output = [
        {
            "finding_id": item.get("finding_id"),
            "authority_finding_refs": _copy(item.get("authority_finding_refs") or []),
            "program_finding_refs": _copy(item.get("program_finding_refs") or []),
            "result": item.get("result"),
        }
        for item in sorted(
            [
                item
                for item in adjudication.get("conformance_findings") or []
                if item.get("result") in {"CONFLICTS", "UNKNOWN"}
            ],
            key=lambda item: str(item.get("finding_id") or ""),
        )
    ]
    body: dict[str, Any] = {
        "contract": REVISION_BRIEF_SCHEMA,
        "version": REVISION_BRIEF_VERSION,
        "task_id": str((candidate or {}).get("task_id") or "task:" + _digest(task)),
        "original_coding_task": task,
        "candidate": _copy(candidate or {}),
        "candidate_iteration": (candidate or {}).get("candidate_iteration"),
        "workflow_outcome": "REVISION_REQUIRED",
        "adoption_decision_id": decision_payload.get("decision_id"),
        "adjudication_id": adjudication.get("adjudication_id"),
        "relevant_authority": authority_output,
        "relevant_program_findings": program_output,
        "relevant_conformance": conformance_output,
        "decision_right": _copy(adjudication.get("decision_right") or {}),
        "constraints_established": [
            {
                "authority_finding_id": item.get("finding_id"),
                "constraint": item.get("interpretation_summary"),
                "evidence_refs": _copy(item.get("evidence_refs") or []),
            }
            for item in authority_output
            if item.get("applicability") == "APPLIES"
        ],
        "concise_evidence_linked_rationale": _copy(adjudication.get("rationale") or []),
        "unresolved_items": _copy(adjudication.get("unresolved_questions") or []),
        "known_limitations": _copy(adjudication.get("known_limitations") or []),
    }
    brief_id = "brief:" + _digest(body)
    body["brief_id"] = brief_id
    body["content_digest"] = _digest(body)
    return body


def write_governance_revision_brief(payload: Mapping[str, Any], output_dir: Path | str) -> Path:
    if payload.get("contract") != REVISION_BRIEF_SCHEMA or payload.get("version") != REVISION_BRIEF_VERSION:
        raise CandidateEvaluationError("cannot write invalid GovernanceRevisionBrief")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "governance.revision.json"
    path.write_text(_pretty_json(payload), encoding="utf-8")
    return path


def _task_text(task: str | Path) -> str:
    if isinstance(task, Path):
        return task.read_text(encoding="utf-8")
    value = str(task)
    candidate = Path(value)
    if "\n" not in value and "\r" not in value and candidate.is_file():
        return candidate.read_text(encoding="utf-8")
    return value


def _world_database(value: Path | str) -> Path:
    path = Path(value).resolve()
    return path / "world.sqlite" if path.is_dir() else path


def _manifest_path(world_database: Path) -> Path:
    path = world_database.parent / "typescript.manifest.json"
    if not path.exists():
        raise BaselineBindingError(f"baseline TypeScript manifest is missing: {path}")
    return path


def _boundary_from_manifest(manifest: Mapping[str, Any]) -> TypeScriptBoundary:
    raw = manifest.get("boundary")
    if not isinstance(raw, Mapping):
        raise BaselineBindingError("baseline manifest boundary is missing")
    try:
        return TypeScriptBoundary(
            workspace_roots=tuple(str(item) for item in raw.get("workspace_roots") or []),
            projects=tuple(str(item) for item in raw.get("projects") or []),
            package_roots=tuple(str(item) for item in raw.get("package_roots") or []),
            include_tests=bool(raw.get("include_tests", False)),
            generated_files=str(raw.get("generated_files") or "exclude"),
            declarations=str(raw.get("declarations") or "in_scope_if_under_boundary"),
            external_dependencies=str(raw.get("external_dependencies") or "preserve_known_endpoints"),
        )
    except (TypeError, ValueError) as exc:
        raise BaselineBindingError(f"invalid baseline boundary: {exc}") from exc


def _manifest_relative_path(entry: Mapping[str, Any], repository: GitRepository) -> str | None:
    raw = str(entry.get("path") or "")
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        try:
            return _safe_repo_relative(raw)
        except GitResolutionError:
            return None
    path = path.resolve()
    try:
        return path.relative_to(repository.root).as_posix()
    except ValueError:
        return None


def _validate_baseline_source_state(
    repository: GitRepository,
    snapshot: GitSnapshot,
    baseline_world: Path,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    database = _world_database(baseline_world)
    try:
        world = ConstructionWorld.open(database, read_only=True)
    except Exception as exc:
        raise BaselineBindingError(f"cannot open baseline governed World: {database}: {exc}") from exc
    try:
        rows = world.relation_rows("program_snapshot")
        if len(rows) != 1:
            raise BaselineBindingError("baseline governed World must contain exactly one program_snapshot")
        if str(rows[0].get("source_state") or "") != str(manifest.get("source_state") or ""):
            raise BaselineBindingError("baseline World program source_state differs from its manifest")
        if snapshot_id(world) != manifest.get("snapshot_id"):
            raise BaselineBindingError("baseline World snapshot differs from its manifest")
        authority_manifest_path = database.parent / "authority.manifest.json"
        if not authority_manifest_path.exists():
            raise BaselineBindingError("baseline governed World lacks authority.manifest.json")
        authority_manifest = _read_json(authority_manifest_path)
        if authority_manifest.get("program_snapshot_id") != manifest.get("snapshot_id"):
            raise BaselineBindingError("authority World was constructed over a different program snapshot")
        for relation in ("authority_source", "authority_completeness", "authority_attachment_warrant"):
            try:
                world.relation_rows(relation)
            except Exception as exc:
                raise BaselineBindingError(f"baseline governed World lacks {relation}: {exc}") from exc

        checked: list[str] = []
        external: list[str] = []
        entries = manifest.get("effective_inputs") or []
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            relative = _manifest_relative_path(entry, repository)
            required = str(entry.get("disposition") or "") == "IN_SCOPE" or str(entry.get("input_role") or "") == "tsconfig"
            if relative is None:
                if required:
                    raise BaselineBindingError(
                        "required baseline program input is outside the Git repository: "
                        + str(entry.get("path") or "")
                    )
                external.append(str(entry.get("path") or ""))
                continue
            if not required:
                external.append(relative)
                continue
            expected = str(entry.get("contentDigest") or "")
            if not expected:
                raise BaselineBindingError(f"required baseline input has no content digest: {relative}")
            try:
                actual = _sha256_bytes(repository.blob(snapshot, relative))
            except GitResolutionError as exc:
                raise BaselineBindingError(
                    f"required baseline input is absent from Git tree: {relative}"
                ) from exc
            if actual != expected:
                raise BaselineBindingError(
                    f"baseline Git tree content differs from governed World input {relative}"
                )
            checked.append(relative)
        if not checked:
            raise BaselineBindingError("baseline manifest has no Git-bound program inputs")
        return {
            "program_snapshot_id": str(manifest.get("snapshot_id") or ""),
            "source_state": str(manifest.get("source_state") or ""),
            "checked_inputs": sorted(set(checked)),
            "external_inputs": sorted(set(external)),
            "authority_manifest": authority_manifest,
        }
    finally:
        world.close()


def _validate_authority_sources(world: ConstructionWorld, source_root: Path) -> dict[str, Any]:
    sources = markdown_sources_from_root(world, source_root)
    rows = world.relation_rows("authority_source")
    missing = sorted(
        str(row.get("source_handle") or "")
        for row in rows
        if str(row.get("source_handle") or "") not in sources
    )
    mismatched: list[str] = []
    for row in rows:
        handle = str(row.get("source_handle") or "")
        source = sources.get(handle)
        if source is not None and source.revision != str(row.get("content_revision") or ""):
            mismatched.append(handle)
    if missing:
        raise BaselineBindingError("baseline authority source is absent from Git tree: " + ", ".join(missing))
    if mismatched:
        raise BaselineBindingError("baseline authority source revision differs from Git tree: " + ", ".join(mismatched))
    return {"handles": sorted(sources), "count": len(sources)}


def _clear_output_artifacts(directory: Path) -> None:
    for name in (
        "candidate.json",
        "spine.comparison.json",
        "authority.maintenance.json",
        "authority.impact.json",
        "governance.case.json",
        "governance.adjudication.json",
        "governance.adjudication.invocation.json",
        "candidate.adoption.json",
        "governance.revision.json",
    ):
        path = directory / name
        if path.is_file() or path.is_symlink():
            path.unlink()


def _candidate_payload(
    *,
    task: str,
    baseline: GitSnapshot,
    candidate: GitSnapshot,
    parent_candidate: GitSnapshot | None,
    candidate_iteration: int,
    baseline_program_snapshot_id: str,
    candidate_program_snapshot_id: str,
    comparison_id: str,
    case_id: str,
    repository: GitRepository,
    coding_agent: Mapping[str, Any] | None,
    baseline_world_binding: Mapping[str, Any],
) -> CandidateEvaluation:
    task_digest = hashlib.sha256(task.encode("utf-8")).hexdigest()
    task_id = "task:" + task_digest[:32]
    identity = {
        "task_id": task_id,
        "baseline_commit": baseline.commit,
        "baseline_tree": baseline.tree,
        "candidate_commit": candidate.commit,
        "candidate_tree": candidate.tree,
        "candidate_iteration": candidate_iteration,
    }
    evaluation_id = "evaluation:" + _digest(identity)
    return CandidateEvaluation(
        evaluation_id=evaluation_id,
        task_id=task_id,
        task_content_digest=task_digest,
        baseline_commit=baseline.commit,
        baseline_tree=baseline.tree,
        candidate_commit=candidate.commit,
        candidate_tree=candidate.tree,
        candidate_iteration=candidate_iteration,
        parent_candidate_commit=parent_candidate.commit if parent_candidate else None,
        baseline_snapshot_id=baseline.snapshot_id,
        candidate_snapshot_id=candidate.snapshot_id,
        baseline_program_snapshot_id=baseline_program_snapshot_id,
        candidate_program_snapshot_id=candidate_program_snapshot_id,
        comparison_id=comparison_id,
        case_id=case_id,
        coding_agent=coding_agent,
        baseline_world_binding=baseline_world_binding,
        git_provenance={
            "repository_root_not_persisted": True,
            "baseline": baseline.to_dict(),
            "candidate": candidate.to_dict(),
            "parent_candidate": parent_candidate.to_dict() if parent_candidate else None,
            "current_branch": repository.current_branch(),
            "source_identity": "git-tree",
        },
    )


def evaluate_git_candidate(
    baseline_commit: str,
    candidate_commit: str,
    baseline_world: Path | str,
    task: str | Path,
    policy: AdoptionPolicy | Mapping[str, Any] | str | None = None,
    *,
    repository: Path | str = ".",
    output_dir: Path | str | None = None,
    candidate_iteration: int = 1,
    parent_candidate_commit: str | None = None,
    series_baseline_commit: str | None = None,
    adjudication: Mapping[str, Any] | Path | str | None = None,
    adjudicator_config: ModelAdjudicatorConfig | Mapping[str, Any] | None = None,
    adjudicator_transport: AdjudicatorTransport | None = None,
    purpose: str = "",
    coding_agent: Mapping[str, Any] | None = None,
    pending_obligations: Any = None,
) -> CandidateEvaluationResult:
    """Evaluate an immutable Git candidate against an adopted governed World.

    This function never invokes a coding agent and never updates Git refs or
    Worlds. If no preexisting adjudication is supplied, a model is invoked
    only when ``adjudicator_config`` is explicitly supplied, and only when
    case readiness is READY_FOR_ADJUDICATION.
    """

    selected_policy = AdoptionPolicy.from_value(policy)
    if isinstance(candidate_iteration, bool) or not isinstance(candidate_iteration, int) or candidate_iteration < 1:
        raise CandidateEvaluationError("candidate_iteration must be a positive integer")
    if candidate_iteration > selected_policy.max_candidate_iterations:
        raise CandidateEvaluationError(
            f"candidate_iteration {candidate_iteration} exceeds policy max_candidate_iterations "
            f"{selected_policy.max_candidate_iterations}"
        )
    repository_adapter = GitRepository(repository)
    baseline = repository_adapter.resolve(baseline_commit)
    candidate = repository_adapter.resolve(candidate_commit)
    parent = repository_adapter.resolve(parent_candidate_commit) if parent_candidate_commit else None
    if series_baseline_commit is not None:
        declared = repository_adapter.resolve(series_baseline_commit)
        if declared.tree != baseline.tree:
            raise CandidateEvaluationError(
                "candidate series baseline does not match the requested baseline tree"
            )

    task_text = _task_text(task)
    baseline_database = _world_database(baseline_world)
    manifest = _read_json(_manifest_path(baseline_database))
    binding = _validate_baseline_source_state(
        repository_adapter, baseline, baseline_database, manifest
    )
    boundary = _boundary_from_manifest(manifest)

    owned_output: tempfile.TemporaryDirectory[str] | None = None
    if output_dir is None:
        owned_output = tempfile.TemporaryDirectory(prefix="governed-candidate-evaluation-")
        directory = Path(owned_output.name)
    else:
        directory = Path(output_dir).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        _clear_output_artifacts(directory)

    try:
        with repository_adapter.materialize(baseline, prefix="governance-baseline-") as baseline_source, repository_adapter.materialize(candidate, prefix="governance-candidate-") as candidate_source:
            old_world = ConstructionWorld.open(baseline_database, read_only=True)
            try:
                authority_binding = _validate_authority_sources(old_world, baseline_source)
                baseline_world_binding = {
                    "binding_validated": True,
                    "program_snapshot_id": binding["program_snapshot_id"],
                    "source_state": binding["source_state"],
                    "authority_program_snapshot_id": (
                        binding["authority_manifest"].get("program_snapshot_id")
                    ),
                    "checked_git_inputs": binding["checked_inputs"],
                    "external_inputs": binding["external_inputs"],
                    "authority_source_handles": authority_binding["handles"],
                    "authority_source_count": authority_binding["count"],
                }
                candidate_program_dir = directory / "candidate-program"
                spine = build_typescript_spine(candidate_source, candidate_program_dir, boundary=boundary)
                if not spine.succeeded or spine.world_dir is None:
                    raise CandidateEvaluationError(
                        "candidate spine construction failed: " + "; ".join(spine.errors)
                    )
                candidate_world = ConstructionWorld.open(
                    _world_database(spine.world_dir),
                    read_only=True,
                )
                try:
                    comparison = compare_program_spines(
                        old_world,
                        candidate_world,
                        output_dir=directory,
                    )
                    maintenance = assess_attachment_maintenance(old_world, candidate_world, comparison)
                    impact = assess_authority_change_impact(
                        old_world,
                        candidate_world,
                        comparison,
                        maintenance=maintenance,
                    )
                    sources = markdown_sources_from_root(old_world, baseline_source)
                    case = assemble_governance_case(
                        old_world,
                        candidate_world,
                        comparison,
                        sources,
                        maintenance=maintenance,
                        impact=impact,
                        purpose=purpose,
                    )
                    maintenance_errors = validate_maintenance_sidecar(
                        maintenance,
                        old_world=old_world,
                        new_world=candidate_world,
                        comparison=comparison,
                    )
                    impact_errors = validate_impact_sidecar(
                        impact,
                        old_world=old_world,
                        comparison=comparison,
                        maintenance=maintenance,
                    )
                    case_errors = validate_case_sidecar(
                        case,
                        maintenance=maintenance,
                        impact=impact,
                        comparison=comparison,
                    )
                    stage_errors = maintenance_errors + impact_errors + case_errors
                    if stage_errors:
                        raise CandidateEvaluationError(
                            "governance stage validation failed: " + "; ".join(sorted(set(stage_errors)))
                        )
                    write_maintenance(maintenance, directory)
                    write_impact(impact, directory)
                    write_case(case, directory)
                    baseline_program_snapshot_id = str(manifest.get("snapshot_id") or snapshot_id(old_world))
                    candidate_program_snapshot_id = str(spine.snapshot_id)
                    candidate_record = _candidate_payload(
                        task=task_text,
                        baseline=baseline,
                        candidate=candidate,
                        parent_candidate=parent,
                        candidate_iteration=candidate_iteration,
                        baseline_program_snapshot_id=baseline_program_snapshot_id,
                        candidate_program_snapshot_id=candidate_program_snapshot_id,
                        comparison_id=str(comparison.receipt.comparison_id),
                        case_id=str(case.get("case_id") or ""),
                        repository=repository_adapter,
                        coding_agent=coding_agent,
                        baseline_world_binding=baseline_world_binding,
                    )
                    candidate_path = directory / "candidate.json"
                    candidate_path.write_text(_pretty_json(candidate_record.to_dict()), encoding="utf-8")
                finally:
                    candidate_world.close()
            finally:
                old_world.close()

            if pending_obligations is not None:
                from .case_lifecycle import evaluate_assembled_candidate_case

                candidate_payload = _read_json(directory / "candidate.json")
                assembled = evaluate_assembled_candidate_case(
                    case,
                    pending_obligations=pending_obligations,
                    candidate=candidate_payload,
                    policy=selected_policy,
                    adjudication=adjudication,
                    adjudicator_config=adjudicator_config,
                    adjudicator_transport=adjudicator_transport,
                    output_dir=directory,
                )
                candidate_payload = _read_json(directory / "candidate.json")
                candidate_payload["adjudication_id"] = (
                    (assembled.adjudication or {}).get("adjudication_id") or ""
                )
                candidate_payload["adoption_decision_id"] = assembled.adoption_decision.get(
                    "decision_id", ""
                )
                candidate_payload["revision_brief_id"] = ""
                candidate_payload["adjudicator"] = _copy(
                    (assembled.adjudication or {}).get("adjudicator") or {}
                )
                (directory / "candidate.json").write_text(
                    _pretty_json(candidate_payload), encoding="utf-8"
                )
                artifacts = {
                    name: str(directory / name)
                    for name in (
                        "candidate.json",
                        "candidate-program",
                        "spine.comparison.json",
                        "authority.maintenance.json",
                        "authority.impact.json",
                        "governance.case.json",
                        "governance.case.readiness.json",
                        "governance.adjudication.json",
                        "candidate.adoption.json",
                    )
                    if (directory / name).exists()
                }
                artifacts.update(assembled.artifacts)
                comparison_payload = _read_json(directory / "spine.comparison.json")
                return CandidateEvaluationResult(
                    candidate=candidate_payload,
                    comparison=comparison_payload,
                    maintenance=maintenance,
                    impact=impact,
                    case=assembled.case,
                    adjudication=assembled.adjudication or {},
                    adoption_decision=assembled.adoption_decision,
                    revision_brief=None,
                    artifacts=artifacts,
                    readiness=assembled.readiness,
                    adjudicator_invoked=assembled.adjudicator_invoked,
                    constructor_invoked=False,
                )

            if adjudication is None and adjudicator_config is None:
                raise CandidateEvaluationError(
                    "evaluation requires --adjudication or explicit adjudicator_config; "
                    "a fake adjudicator is never substituted"
                )
            if adjudication is not None:
                if isinstance(adjudication, Mapping):
                    adjudication_payload = _copy(adjudication)
                else:
                    adjudication_payload = load_governance_adjudication(adjudication)
                adjudication_errors = validate_governance_adjudication(adjudication_payload, case)
                if adjudication_errors:
                    raise CandidateEvaluationError(
                        "supplied adjudication is invalid: " + "; ".join(adjudication_errors)
                    )
                write_governance_adjudication(adjudication_payload, directory)
            else:
                # The model adapter writes the validated artifact and its
                # invocation receipt only after local validation succeeds.
                adjudication_payload = adjudicate_governance_case(
                    case,
                    adjudicator_config=adjudicator_config,  # type: ignore[arg-type]
                    transport=adjudicator_transport,
                    output_dir=directory,
                )

            candidate_payload = _read_json(directory / "candidate.json")
            candidate_payload["adjudication_id"] = adjudication_payload.get("adjudication_id") or ""
            candidate_payload["adoption_decision_id"] = ""
            candidate_payload["revision_brief_id"] = ""
            candidate_payload["adjudicator"] = _copy(adjudication_payload.get("adjudicator") or {})
            if (directory / "governance.adjudication.invocation.json").exists():
                candidate_payload["adjudication_invocation_ref"] = "governance.adjudication.invocation.json"
            adoption = decide_candidate_adoption(
                case,
                adjudication_payload,
                selected_policy,
                candidate=candidate_payload,
            )
            adoption_payload = adoption.to_dict()
            adoption_payload.pop("_case_for_validation", None)
            adoption_payload.pop("_adjudication_for_validation", None)
            decision_validation_payload = dict(adoption_payload)
            decision_validation_payload["_case_for_validation"] = case
            decision_validation_payload["_adjudication_for_validation"] = adjudication_payload
            decision_errors = validate_candidate_adoption_decision(
                decision_validation_payload,
                case,
                adjudication_payload,
                selected_policy,
            )
            if decision_errors:
                raise CandidateEvaluationError(
                    "adoption decision validation failed: " + "; ".join(decision_errors)
                )
            decision_path = write_candidate_adoption(
                adoption_payload,
                directory,
                case=case,
                adjudication=adjudication_payload,
                policy=selected_policy,
            )
            revision_payload: dict[str, Any] | None = None
            revision_path: Path | None = None
            if adoption_payload["outcome"] == "REVISION_REQUIRED":
                revision_payload = build_governance_revision_brief(
                    task_text,
                    case,
                    adjudication_payload,
                    adoption_payload,
                    candidate=candidate_payload,
                )
                revision_path = write_governance_revision_brief(revision_payload, directory)
                adoption_payload["revision_brief_ref"] = revision_payload["brief_id"]
                decision_path.unlink()
                decision_path = write_candidate_adoption(
                    adoption_payload,
                    directory,
                    case=case,
                    adjudication=adjudication_payload,
                    policy=selected_policy,
                )

            candidate_payload["adoption_decision_id"] = adoption_payload["decision_id"]
            candidate_payload["revision_brief_id"] = (revision_payload or {}).get("brief_id", "")
            (directory / "candidate.json").write_text(_pretty_json(candidate_payload), encoding="utf-8")

            artifacts = {
                name: str(directory / name)
                for name in (
                    "candidate.json",
                    "candidate-program",
                    "spine.comparison.json",
                    "authority.maintenance.json",
                    "authority.impact.json",
                    "governance.case.json",
                    "governance.adjudication.json",
                    "candidate.adoption.json",
                )
                if (directory / name).exists()
            }
            if (directory / "governance.adjudication.invocation.json").exists():
                artifacts["governance.adjudication.invocation.json"] = str(directory / "governance.adjudication.invocation.json")
            if revision_path is not None:
                artifacts["governance.revision.json"] = str(revision_path)
            comparison_payload = _read_json(directory / "spine.comparison.json")
            return CandidateEvaluationResult(
                candidate=candidate_payload,
                comparison=comparison_payload,
                maintenance=maintenance,
                impact=impact,
                case=case,
                adjudication=adjudication_payload,
                adoption_decision=adoption_payload,
                revision_brief=revision_payload,
                artifacts=artifacts,
                adjudicator_invoked=adjudicator_config is not None and adjudication is None,
                constructor_invoked=False,
            )
    finally:
        if owned_output is not None:
            owned_output.cleanup()


# A concise alias for callers that use the lifecycle vocabulary rather than
# the implementation mechanism.
evaluate_candidate = evaluate_git_candidate


__all__ = [
    "ADOPTION_DECISION_SCHEMA",
    "ADOPTION_OUTCOMES",
    "ADOPTION_POLICY_SCHEMA",
    "CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT",
    "CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION",
    "REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT",
    "REASON_REQUIRED_SEMANTIC_CONSTRUCTION",
    "REVISION_BRIEF_SCHEMA",
    "AdoptionPolicy",
    "BaselineBindingError",
    "CandidateAdoptionDecision",
    "CandidateEvaluation",
    "CandidateEvaluationError",
    "CandidateEvaluationResult",
    "GitRepository",
    "GitResolutionError",
    "GitSnapshot",
    "build_governance_revision_brief",
    "decide_candidate_adoption",
    "decide_semantic_construction_required",
    "evaluate_candidate",
    "evaluate_git_candidate",
    "validate_candidate_adoption_decision",
    "write_candidate_adoption",
    "write_governance_revision_brief",
]

"""Deterministic evaluation of recorded candidate Commitments."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from itertools import combinations
from typing import Any

from ontology_author.world.core.contract import (
    AdjudicationAssessment,
    CandidateAssessment,
    Contract,
)
from ontology_author.world.core.model import ResolutionStatus
from ontology_author.world.core.resolution import Resolution
from ontology_author.world.runtime.material_support import (
    SUPPORT_CHANGED,
    SUPPORT_MISSING,
    SUPPORT_PRESERVED,
    SUPPORT_UNKNOWN,
    material_support_for_warrant,
)


class ResolutionEvaluationError(ValueError):
    """The recorded candidate state cannot be evaluated safely."""


CommitmentConflictChecker = Callable[
    [Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], bool
]


def resolve_world(
    world: Any,
    contract: Contract,
    *,
    conflict_checker: CommitmentConflictChecker | None = None,
    evidence_authority: Any | None = None,
    adjudication_authority: Any | None = None,
    source: Any | None = None,
) -> tuple[Resolution, ...]:
    """Evaluate every durable Contract Obligation in deterministic order.

    The resolver reads the candidate World: obligations, candidate
    relationships, assertion tuples, and recorded Warrant façade data. It
    joins the Warrant's source identities to the explicitly supplied evidence
    authority configuration. When ``source`` is supplied, it also
    deterministically reproduces any constructor-declared material evidence
    region. It never searches a file for supporting sentences and never
    constructs a Commitment.
    """

    bound = world.contract_identity()
    if bound != contract.identity():
        raise ResolutionEvaluationError(
            "resolution Contract identity does not match the World binding"
        )

    results: list[Resolution] = []
    for obligation in world.obligations():
        obligation_id = str(obligation["obligation_id"])
        candidate_ids = _candidate_ids(world, obligation_id)
        assessments: list[CandidateAssessment] = []
        commitments: dict[str, dict[str, Any]] = {}
        for commitment_id in candidate_ids:
            commitment = _commitment(world, commitment_id)
            commitments[commitment_id] = commitment
            warrant = world.warrant_for_assertion(commitment_id)
            authority = _derive_evidence_authority(evidence_authority, warrant)
            assessment = contract.assess_candidate(
                obligation=obligation,
                commitment=commitment,
                warrant=warrant,
                warrant_authorities=authority["authority_kinds"],
                authority_basis=authority["authority_basis"],
            )
            assessments.append(
                _apply_material_support(assessment, warrant, source)
            )
        assessments.sort(key=lambda item: item.commitment_id)
        adjudication_assessments: list[AdjudicationAssessment] = []
        resolution_basis: list[Mapping[str, Any]] = []

        sufficient_ids = [
            item.commitment_id for item in assessments if item.status == "SUFFICIENT"
        ]
        if not candidate_ids:
            status = ResolutionStatus.NO_CANDIDATE
            selected = None
            reason = f"Obligation {obligation_id} has no candidate Commitment."
        elif not sufficient_ids:
            status = ResolutionStatus.INSUFFICIENT_WARRANT
            selected = None
            if any(
                (item.material_support or {}).get("status")
                in {SUPPORT_CHANGED, SUPPORT_MISSING, SUPPORT_UNKNOWN}
                and item.warrant_authorities
                for item in assessments
            ):
                reason = (
                    f"Obligation {obligation_id} has candidates with source "
                    "standing, but none currently has a reproducible material "
                    "evidence basis."
                )
            else:
                reason = (
                    f"Obligation {obligation_id} has candidates, but none meets the "
                    "Contract resolution warrant standard."
                )
        else:
            conflicts: list[tuple[str, str]] = []
            if conflict_checker is not None:
                for first_id, second_id in combinations(sufficient_ids, 2):
                    try:
                        incompatible = conflict_checker(
                            obligation,
                            commitments[first_id],
                            commitments[second_id],
                        )
                    except Exception as error:
                        raise ResolutionEvaluationError(
                            f"conflict checker failed for {obligation_id}: {error}"
                        ) from error
                    if incompatible:
                        conflicts.append((first_id, second_id))
            if conflicts:
                adjudication_assessments = _evaluate_adjudications(
                    world,
                    obligation,
                    sufficient_ids,
                    contract,
                    adjudication_authority,
                )
                valid = [
                    item
                    for item in adjudication_assessments
                    if item.status == "SUFFICIENT"
                    and item.selected_commitment_id in sufficient_ids
                ]
                selected_targets = sorted(
                    {item.selected_commitment_id for item in valid}
                )
                if len(selected_targets) == 1:
                    status = ResolutionStatus.RESOLVED
                    selected = selected_targets[0]
                    resolution_basis = [
                        {
                            "kind": "ADJUDICATION",
                            "adjudication_id": item.adjudication_id,
                            "selected_commitment_id": item.selected_commitment_id,
                            "adjudicative_authorities": list(
                                item.adjudicative_authorities
                            ),
                            "authority_basis": [
                                dict(basis) for basis in item.authority_basis
                            ],
                        }
                        for item in valid
                    ]
                    ids = ", ".join(item.adjudication_id for item in valid)
                    reason = (
                        f"Authorized adjudication {ids} selects Commitment {selected} "
                        "among the otherwise sufficient conflicting candidates."
                    )
                else:
                    status = ResolutionStatus.CONFLICT
                    selected = None
                    pairs = ", ".join(
                        f"{first}/{second}" for first, second in conflicts
                    )
                    if len(selected_targets) > 1:
                        reason = (
                            f"Obligation {obligation_id} has competing authorized "
                            f"adjudications selecting {', '.join(selected_targets)}; "
                            "no adjudication precedence rule chooses one."
                        )
                    else:
                        reason = (
                            f"Obligation {obligation_id} has incompatible sufficient "
                            f"Commitments ({pairs}); no authorized adjudication "
                            "selects a governing candidate."
                        )
            elif len(sufficient_ids) == 1:
                status = ResolutionStatus.RESOLVED
                selected = sufficient_ids[0]
                reason = (
                    f"Commitment {selected} is the only candidate whose Warrant "
                    "meets the Contract resolution standard."
                )
            else:
                status = ResolutionStatus.AMBIGUOUS
                selected = None
                reason = (
                    f"Obligation {obligation_id} has multiple sufficient, "
                    "compatible candidates; single-answer cardinality is not "
                    "implemented."
                )

        result = Resolution(
            obligation_id=obligation_id,
            status=status,
            selected_commitment_id=selected,
            reason=reason,
            contract_id=contract.contract_id,
            contract_revision=contract.contract_revision,
            candidate_assessments=tuple(assessments),
            adjudication_assessments=tuple(adjudication_assessments),
            resolution_basis=tuple(resolution_basis),
        )
        world._materialize_resolution(
            obligation_id=obligation_id,
            status=result.status.value,
            selected_commitment_id=result.selected_commitment_id,
            reason=result.reason,
            candidate_assessments=[item.as_payload() for item in result.candidate_assessments],
            adjudication_assessments=[
                item.as_payload() for item in result.adjudication_assessments
            ],
            resolution_basis=list(result.resolution_basis),
        )
        results.append(result)
    return tuple(results)


def _apply_material_support(
    assessment: CandidateAssessment,
    warrant: Mapping[str, Any],
    source: Any | None,
) -> CandidateAssessment:
    """Separate material-region currency from source-authority standing."""

    support = material_support_for_warrant(warrant, source)
    if support is None:
        return assessment
    support_status = str(support.get("status") or "")
    invalidate = support_status in {SUPPORT_CHANGED, SUPPORT_MISSING} or (
        support_status == SUPPORT_UNKNOWN and source is not None
    )
    if assessment.status == "SUFFICIENT" and invalidate:
        return CandidateAssessment(
            commitment_id=assessment.commitment_id,
            status="INSUFFICIENT",
            reason=(
                f"Commitment {assessment.commitment_id} has acceptable source "
                f"standing, but its material evidence basis is {support_status}: "
                f"{support.get('reason') or 'not current'}"
            ),
            warrant_authorities=assessment.warrant_authorities,
            authority_basis=assessment.authority_basis,
            material_support=support,
        )
    return CandidateAssessment(
        commitment_id=assessment.commitment_id,
        status=assessment.status,
        reason=assessment.reason,
        warrant_authorities=assessment.warrant_authorities,
        authority_basis=assessment.authority_basis,
        material_support=support,
    )


def _evaluate_adjudications(
    world: Any,
    obligation: Mapping[str, Any],
    sufficient_ids: list[str],
    contract: Contract,
    configuration: Any | None,
) -> list[AdjudicationAssessment]:
    """Assess recorded adjudications only when ordinary conflict exists."""

    obligation_id = str(obligation.get("obligation_id") or "")
    records = world.adjudications_for_obligation(obligation_id)
    assessments: list[AdjudicationAssessment] = []
    for record in records:
        authority = _derive_adjudication_authority(configuration, record)
        assessment = contract.assess_adjudication(
            adjudication=record,
            adjudicative_authorities=authority["authority_kinds"],
            authority_basis=authority["authority_basis"],
        )
        if (
            assessment.status == "SUFFICIENT"
            and assessment.selected_commitment_id not in sufficient_ids
        ):
            assessment = AdjudicationAssessment(
                adjudication_id=assessment.adjudication_id,
                selected_commitment_id=assessment.selected_commitment_id,
                status="INSUFFICIENT",
                reason=(
                    f"Adjudication {assessment.adjudication_id} selects Commitment "
                    f"{assessment.selected_commitment_id}, which is not a "
                    "warrant-sufficient candidate for this conflict."
                ),
                adjudicative_authorities=assessment.adjudicative_authorities,
                authority_basis=assessment.authority_basis,
            )
        assessments.append(assessment)
    assessments.sort(key=lambda item: item.adjudication_id)
    return assessments


def _derive_evidence_authority(
    configuration: Any | None,
    warrant: Mapping[str, Any],
) -> dict[str, tuple[Any, ...]]:
    """Ask the external authority binding to assess recorded Warrant bases.

    Resolution remains generic: the application supplies a small object with
    ``assess_warrant``.  No generic source registry or authority ontology is
    introduced here.  Missing configuration is fail-closed and yields no
    authority; a malformed supplied configuration is a technical evaluation
    error rather than an implicit grant.
    """

    if configuration is None:
        return {"authority_kinds": (), "authority_basis": ()}
    assessor = getattr(configuration, "assess_warrant", None)
    if not callable(assessor):
        raise ResolutionEvaluationError(
            "evidence authority configuration must provide assess_warrant(warrant)"
        )
    try:
        result = assessor(warrant)
    except Exception as error:
        raise ResolutionEvaluationError(
            f"evidence authority assessment failed: {error}"
        ) from error
    if not isinstance(result, Mapping):
        raise ResolutionEvaluationError(
            "evidence authority assessment must return a mapping"
        )
    raw_kinds = result.get("authority_kinds", ())
    raw_basis = result.get("authority_basis", ())
    if isinstance(raw_kinds, (str, bytes)) or not isinstance(raw_kinds, (list, tuple, set, frozenset)):
        raise ResolutionEvaluationError(
            "evidence authority assessment authority_kinds must be a collection"
        )
    if not isinstance(raw_basis, (list, tuple)):
        raise ResolutionEvaluationError(
            "evidence authority assessment authority_basis must be a sequence"
        )
    basis = tuple(item for item in raw_basis if isinstance(item, Mapping))
    return {
        "authority_kinds": tuple(str(item).strip().upper() for item in raw_kinds if str(item).strip()),
        "authority_basis": basis,
    }


def _derive_adjudication_authority(
    configuration: Any | None,
    adjudication: Mapping[str, Any],
) -> dict[str, tuple[Any, ...]]:
    """Derive adjudicative standing from the external configuration."""

    if configuration is None:
        return {"authority_kinds": (), "authority_basis": ()}
    assessor = getattr(configuration, "assess_adjudication", None)
    if not callable(assessor):
        raise ResolutionEvaluationError(
            "adjudication authority configuration must provide "
            "assess_adjudication(adjudication)"
        )
    try:
        result = assessor(adjudication)
    except Exception as error:
        raise ResolutionEvaluationError(
            f"adjudication authority assessment failed: {error}"
        ) from error
    if not isinstance(result, Mapping):
        raise ResolutionEvaluationError(
            "adjudication authority assessment must return a mapping"
        )
    raw_kinds = result.get("authority_kinds", ())
    raw_basis = result.get("authority_basis", ())
    if isinstance(raw_kinds, (str, bytes)) or not isinstance(
        raw_kinds, (list, tuple, set, frozenset)
    ):
        raise ResolutionEvaluationError(
            "adjudication authority assessment authority_kinds must be a collection"
        )
    if not isinstance(raw_basis, (list, tuple)):
        raise ResolutionEvaluationError(
            "adjudication authority assessment authority_basis must be a sequence"
        )
    return {
        "authority_kinds": tuple(
            str(item).strip().upper() for item in raw_kinds if str(item).strip()
        ),
        "authority_basis": tuple(
            item for item in raw_basis if isinstance(item, Mapping)
        ),
    }


def _candidate_ids(world: Any, obligation_id: str) -> tuple[str, ...]:
    return tuple(world.candidates_for(obligation_id))


def _commitment(world: Any, commitment_id: str) -> dict[str, Any]:
    rows = world.query(
        "SELECT relation_name FROM _world_assertions WHERE assertion_id = ?",
        (commitment_id,),
    )
    if not rows:
        raise ResolutionEvaluationError(
            f"candidate names unknown Commitment {commitment_id!r}"
        )
    relation = str(rows[0]["relation_name"])
    schema = world.relation_schema(relation)
    safe_relation = relation.replace('"', '""')
    row = world.query(
        f'SELECT * FROM "{safe_relation}" WHERE _assertion_id = ?',
        (commitment_id,),
    )
    if not row:
        raise ResolutionEvaluationError(
            f"candidate Commitment {commitment_id!r} has no semantic tuple"
        )
    values = {
        str(role["name"]): row[0][role["column"]]
        for role in schema["roles"]
    }
    return {
        "commitment_id": commitment_id,
        "relation": relation,
        "values": values,
    }


__all__ = [
    "CommitmentConflictChecker",
    "ResolutionEvaluationError",
    "resolve_world",
]

"""Deterministic evaluation of recorded candidate Commitments."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from itertools import combinations
from typing import Any

from ontology_author.world.core.contract import CandidateAssessment, Contract
from ontology_author.world.core.model import ResolutionStatus
from ontology_author.world.core.resolution import Resolution


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
) -> tuple[Resolution, ...]:
    """Evaluate every durable Contract Obligation in deterministic order.

    The resolver reads only the candidate World: obligations, candidate
    relationships, assertion tuples, and recorded Warrant façade data. It
    never reads project files and never constructs a Commitment.
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
            assessments.append(
                contract.assess_candidate(
                    obligation=obligation,
                    commitment=commitment,
                    warrant=warrant,
                )
            )
        assessments.sort(key=lambda item: item.commitment_id)

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
                status = ResolutionStatus.CONFLICT
                selected = None
                pairs = ", ".join(f"{first}/{second}" for first, second in conflicts)
                reason = (
                    f"Obligation {obligation_id} has incompatible sufficient "
                    f"Commitments ({pairs}); no Contract precedence rule chooses one."
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
        )
        world.record_resolution(
            obligation_id=obligation_id,
            status=result.status.value,
            selected_commitment_id=result.selected_commitment_id,
            reason=result.reason,
            candidate_assessments=[item.as_payload() for item in result.candidate_assessments],
        )
        results.append(result)
    return tuple(results)


def _candidate_ids(world: Any, obligation_id: str) -> tuple[str, ...]:
    references = world.query(
        "SELECT r.relation_name, r.role_name, r.reference_kind, w.column_name "
        "FROM _world_semantic_reference_roles r "
        "JOIN _world_roles w ON w.relation_name = r.relation_name "
        "AND w.role_name = r.role_name "
        "WHERE r.reference_kind IN ('OBLIGATION', 'COMMITMENT') "
        "ORDER BY r.relation_name, r.role_name"
    )
    grouped: dict[str, dict[str, str]] = {}
    for row in references:
        grouped.setdefault(str(row["relation_name"]), {})[
            str(row["reference_kind"])
        ] = str(row["column_name"])

    found: set[str] = set()
    for relation, columns in sorted(grouped.items()):
        obligation_column = columns.get("OBLIGATION")
        commitment_column = columns.get("COMMITMENT")
        if not obligation_column or not commitment_column:
            continue
        rows = world.query(
            f"SELECT {_quote_identifier(commitment_column)} AS commitment_id "
            f"FROM {_quote_identifier(relation)} "
            f"WHERE {_quote_identifier(obligation_column)} = ? "
            f"ORDER BY {_quote_identifier(commitment_column)}",
            (obligation_id,),
        )
        found.update(str(row["commitment_id"]) for row in rows)
    return tuple(sorted(found))


def _quote_identifier(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


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

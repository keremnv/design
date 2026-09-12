"""World semantic implementation over SQLite storage.

The calculus is CONSTITUTION.md. This module is the current kernel *mechanism*:
domain vocabularies live in fixture/config code, while construction-origin
metadata is recorded on the grounding/support paths for assertions.
"""

from __future__ import annotations

import json
import stat
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from ontology_author.world.core.contract_store import ContractWorldStore
from ontology_author.world.core.model import (
    Completeness,
    Grounding,
    GroundingKind,
    RelationMode,
    Role,
)
from ontology_author.world.core.origins import ConstructionOrigin, OriginMetadataError
from ontology_author.world.core.source import AssertionGrounding, SourceObservation


UNKNOWN_ORIGIN = "UNKNOWN"
MULTIPLE_ORIGINS = "MULTIPLE"


class SemanticWorld:
    """One versioned semantic World backed by SQLite storage."""

    def __init__(
        self,
        path: Path | str,
        *,
        world_id: str,
        read_only: bool = False,
        contract_id: str = "",
        contract_revision: str = "",
    ) -> None:
        self.path = Path(path)
        self.world_id = world_id
        self.read_only = read_only
        original_mode: int | None = None
        if read_only and self.path.exists():
            original_mode = stat.S_IMODE(self.path.stat().st_mode)
            self.path.chmod(original_mode | stat.S_IWUSR)
        try:
            self._store = ContractWorldStore(
                self.path,
                world_id=world_id,
                purpose_ref="",
                contract_id=contract_id,
                contract_revision=contract_revision,
            )
        finally:
            if original_mode is not None:
                self.path.chmod(original_mode)

    def close(self) -> None:
        self._store.close()

    # -- Contract / obligation state -------------------------------------

    def contract_identity(self) -> dict[str, str] | None:
        return self._store.contract_identity()

    def add_obligation(
        self,
        obligation_id: str,
        *,
        question: str,
        reason: str = "",
    ) -> str:
        return self._store.add_obligation(
            obligation_id, question=question, reason=reason
        )

    def obligation(self, obligation_id: str) -> dict[str, Any] | None:
        return self._store.obligation(obligation_id)

    def obligations(self) -> list[dict[str, Any]]:
        return self._store.obligations()

    def add_candidate(self, obligation_id: str, commitment_id: str) -> str:
        return self._store.add_candidate(obligation_id, commitment_id)

    def candidates_for(self, obligation_id: str) -> list[str]:
        return self._store.candidates_for(obligation_id)

    def obligations_for(self, commitment_id: str) -> list[str]:
        return self._store.obligations_for(commitment_id)

    def candidate_associations(self) -> list[dict[str, Any]]:
        return self._store.candidate_associations()

    def candidate_errors(self) -> list[dict[str, str]]:
        return self._store.candidate_errors()

    def resolution(self, obligation_id: str) -> dict[str, Any] | None:
        return self._store.resolution(obligation_id)

    def resolutions(self) -> list[dict[str, Any]]:
        return self._store.resolutions()

    def add_adjudication(
        self,
        *,
        adjudication_id: str,
        obligation_id: str,
        selected_commitment_id: str,
        authority_basis: Mapping[str, Any],
    ) -> str:
        return self._store.record_adjudication(
            adjudication_id=adjudication_id,
            obligation_id=obligation_id,
            selected_commitment_id=selected_commitment_id,
            authority_basis=authority_basis,
        )

    def adjudication(self, adjudication_id: str) -> dict[str, Any] | None:
        return self._store.adjudication(adjudication_id)

    def adjudications(self) -> list[dict[str, Any]]:
        return self._store.adjudications()

    def adjudications_for_obligation(self, obligation_id: str) -> list[dict[str, Any]]:
        return self._store.adjudications_for_obligation(obligation_id)

    def record_resolution(
        self,
        *,
        obligation_id: str,
        status: str,
        selected_commitment_id: str | None = None,
        reason: str = "",
        candidate_assessments: Sequence[Mapping[str, Any]] = (),
        adjudication_assessments: Sequence[Mapping[str, Any]] = (),
        resolution_basis: Sequence[Mapping[str, Any]] = (),
    ) -> str:
        return self._store.record_resolution(
            obligation_id=obligation_id,
            status=status,
            selected_commitment_id=selected_commitment_id,
            reason=reason,
            candidate_assessments=candidate_assessments,
            adjudication_assessments=adjudication_assessments,
            resolution_basis=resolution_basis,
        )

    def semantic_reference_errors(self) -> list[dict[str, str]]:
        return self._store.semantic_reference_errors()

    # -- Semantic content -------------------------------------------------

    def add_referent(
        self,
        referent_id: str,
        *,
        label: str = "",
        observations: Iterable[SourceObservation] = (),
    ) -> str:
        return self._store.add_referent(
            referent_id,
            label=label,
            grounding=_observation_groundings(observations),
        )

    def declare_relation(
        self,
        name: str,
        roles: Sequence[Role],
        *,
        mode: RelationMode = RelationMode.BASE,
        description: str = "",
    ) -> str:
        return self._store.declare_relation(
            name, roles, mode=mode, description=description
        )

    def relation_schema(self, relation: str) -> dict[str, Any]:
        return self._store.relation_schema(relation)

    def assert_tuple(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        origin: ConstructionOrigin,
        grounding: AssertionGrounding | None = None,
    ):
        if origin is ConstructionOrigin.DERIVED:
            raise ValueError("BASE assert cannot use DERIVED origin")
        grounds = list(_assertion_groundings(grounding, origin))
        return self._store.assert_tuple(relation, values, grounding=grounds)

    def retract_tuple(self, relation: str, values: Mapping[str, Any]) -> bool:
        return self._store.retract_tuple(relation, values)

    def register_derivation(
        self, relation: str, *, sql: str, inputs: Sequence[str]
    ) -> None:
        self._store.register_derivation(relation, sql=sql, inputs=inputs)

    def rerun(self, relation: str, *, completeness: Completeness):
        return self._store.run_derivation(relation, completeness=completeness)

    def is_stale(self, relation: str) -> bool:
        return self._store.is_stale(relation)

    def stale_relations(self) -> list[str]:
        return self._store.stale_relations()

    def derivation_state(self, relation: str) -> str:
        return self._store.derivation_state(relation)

    def latest_completeness(self, relation: str) -> dict[str, Any] | None:
        return self._store.latest_completeness(relation)

    def query(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return self._store.query(sql, parameters)

    def query_semantic(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        return self._store.query_semantic(sql, parameters)

    def inspect_tuple(
        self, relation: str, values: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        detail = self._store.inspect_tuple(relation, values)
        if detail is None:
            return None
        assertion_id = self._store.assertion_id_for_tuple(relation, values)
        origins = self.origins_for_assertion(assertion_id)
        detail["construction_origins"] = origins
        detail["construction_origin"] = _origin_summary(origins)
        return detail

    def warrant_for_assertion(self, assertion_id: str) -> dict[str, Any]:
        """Read the current provenance machinery as a provisional Warrant view.

        This intentionally adds no warrant storage yet. It makes the existing
        axes coherent and queryable while preserving their distinctions.
        """

        rows = self._store.query(
            "SELECT relation_name, origin, created_revision "
            "FROM _world_assertions WHERE assertion_id = ?",
            (assertion_id,),
        )
        if not rows:
            raise KeyError(f"no assertion {assertion_id!r}")
        row = rows[0]
        bases: list[dict[str, Any]] = []
        for grounding in self._store.groundings("ASSERTION", assertion_id):
            item: dict[str, Any] = {
                "kind": grounding["kind"],
                "reference": grounding["reference"],
            }
            detail = grounding.get("detail") or ""
            if detail:
                try:
                    parsed = json.loads(detail)
                except (TypeError, ValueError):
                    item["detail_text"] = detail
                else:
                    item["detail"] = parsed
                    if isinstance(parsed, dict) and parsed.get("construction_origin"):
                        item["construction_origin"] = str(
                            parsed["construction_origin"]
                        )
            bases.append(item)
        origins = self.origins_for_assertion(assertion_id)
        return {
            "commitment_id": assertion_id,
            "relation": row["relation_name"],
            "assertion_origin": row["origin"],
            # Kept as a compatibility field for consumers that only render one
            # label. It is explicitly a summary; the complete support-path
            # information is in `construction_origins` and each base.
            "recorded_construction_origin": _origin_summary(origins),
            "construction_origins": origins,
            "created_revision": int(row["created_revision"]),
            "bases": bases,
        }

    def construction_supports_for_assertion(
        self, assertion_id: str
    ) -> list[dict[str, Any]]:
        """Return the recorded construction/support paths for an assertion.

        ``ConstructionOrigin`` belongs to a support path, not to the
        proposition identity. The path is currently represented by the
        ``WORLD`` grounding created by :meth:`assert_tuple`; its detail keeps
        the origin, construction method, and the source-observation pointers
        that were supplied for that call.

        Derived assertions are different: their durable derivation record is
        the support path, and ``_world_assertions.origin`` is the separate
        assertion-storage axis that identifies that fact.
        """

        rows = self._store.query(
            "SELECT origin FROM _world_assertions WHERE assertion_id = ?",
            (assertion_id,),
        )
        if not rows:
            raise OriginMetadataError(
                f"no assertion {assertion_id!r} has a construction origin"
            )
        if rows[0]["origin"] == "DERIVED":
            return [
                {
                    "origin": ConstructionOrigin.DERIVED.value,
                    "has_source_grounding": False,
                    "has_provenance": True,
                    "has_construction_method": True,
                    "kind": GroundingKind.DERIVATION.value,
                }
            ]

        supports: list[dict[str, Any]] = []
        for grounding in self._store.groundings("ASSERTION", assertion_id):
            if grounding["kind"] != GroundingKind.WORLD.value:
                continue
            detail = grounding.get("detail") or ""
            try:
                parsed = json.loads(detail) if detail else {}
            except (TypeError, ValueError):
                parsed = {}
            if not isinstance(parsed, Mapping):
                parsed = {}
            origin = parsed.get("construction_origin")
            if not origin:
                reference = str(grounding.get("reference") or "")
                if reference.startswith("origin:"):
                    origin = reference.removeprefix("origin:")
            if not str(origin or "").strip():
                continue
            observations = parsed.get("observations")
            has_source = any(
                isinstance(item, Mapping)
                and str(item.get("native_handle") or "").strip()
                and str(item.get("source_revision") or "").strip()
                for item in (observations if isinstance(observations, list) else [])
            )
            supports.append(
                {
                    "origin": str(origin),
                    "has_source_grounding": has_source,
                    "has_provenance": True,
                    "has_construction_method": bool(
                        str(parsed.get("construction_method") or "").strip()
                    ),
                    "kind": GroundingKind.WORLD.value,
                }
            )
        if not supports:
            raise OriginMetadataError(
                f"asserted tuple {assertion_id!r} has no construction origin"
            )
        return supports

    def origins_for_assertion(self, assertion_id: str) -> list[str]:
        """Return all construction origins represented by support paths.

        The returned list is deterministic and may contain more than one
        origin for a single proposition. That is the intended representation
        when distinct construction/support acts converge on one Commitment.
        """

        origins = {
            str(path["origin"])
            for path in self.construction_supports_for_assertion(assertion_id)
            if str(path.get("origin") or "").strip()
        }
        return sorted(origins)

    def origin_for_assertion(self, assertion_id: str) -> str:
        """Compatibility accessor for assertions with exactly one origin.

        A proposition with multiple support-path origins has no honest scalar
        answer. Callers that need the complete information must use
        :meth:`origins_for_assertion`.
        """

        origins = self.origins_for_assertion(assertion_id)
        if len(origins) != 1:
            raise OriginMetadataError(
                f"assertion {assertion_id!r} has multiple construction origins; "
                "use origins_for_assertion"
            )
        return origins[0]

    def origin_account(self) -> dict[str, int]:
        counts = {origin.value: 0 for origin in ConstructionOrigin}
        for row in self._store.query(
            "SELECT assertion_id FROM _world_assertions"
        ):
            for origin in self.origins_for_assertion(row["assertion_id"]):
                counts[origin] = counts.get(origin, 0) + 1
        return counts

    def relation_tuples(self, relation: str) -> set[tuple[Any, ...]]:
        roles = self._store.relation_schema(relation)["roles"]
        columns = [role["column"] for role in roles]
        rows = self._store.query(
            f"SELECT {', '.join(columns)} FROM {relation} ORDER BY {', '.join(columns)}"
        )
        return {tuple(row[column] for column in columns) for row in rows}


def _observation_groundings(
    observations: Iterable[SourceObservation],
) -> list[Grounding]:
    grounds = []
    for observation in observations:
        pointer = observation.as_pointer()
        grounds.append(
            Grounding(
                GroundingKind.SOURCE,
                f"{observation.provider}://{observation.native_handle}@{observation.source_revision}",
                json.dumps(pointer, sort_keys=True, separators=(",", ":")),
            )
        )
    return grounds


def _assertion_groundings(
    grounding: AssertionGrounding | None,
    origin: ConstructionOrigin,
) -> list[Grounding]:
    if grounding is None:
        return [
            Grounding(
                GroundingKind.WORLD,
                "construction",
                json.dumps(
                    {"construction_origin": origin.value},
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
        ]
    grounds = _observation_groundings(grounding.observations)
    payload = {
        "construction_origin": origin.value,
        "construction_method": grounding.construction_method,
        "observations": [item.as_pointer() for item in grounding.observations],
    }
    if grounding.extra:
        payload["extra"] = grounding.extra
    grounds.append(
        Grounding(
            GroundingKind.WORLD,
            "construction",
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        )
    )
    return grounds


def _origin_summary(origins: Sequence[str]) -> str:
    """Render a legacy scalar origin field without selecting an origin."""

    if not origins:
        return UNKNOWN_ORIGIN
    if len(origins) == 1:
        return origins[0]
    return MULTIPLE_ORIGINS

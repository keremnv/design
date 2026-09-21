"""Fail-closed construction boundary over the World semantic implementation.

WORLD BASE requires SOURCE grounding; PURPOSE-scoped rows may omit it.
Admission scope is a sidecar mechanism for the WORLD vs PURPOSE invariant.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal

from ontology_author.world.core.contract import Contract, ContractAdmissionError
from ontology_author.world.core.model import Completeness, RelationMode, Role, RoleType

from ontology_author.world.core.kernel import SemanticWorld
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation

Scope = Literal["WORLD", "PURPOSE"]


class GroundingError(ValueError):
    """WORLD BASE was asserted without SOURCE grounding."""


class ConstructionError(ValueError):
    """construction.py is malformed or did not produce a World."""


def world_id_of(db_path: Path | str) -> str:
    connection = sqlite3.connect(f"{Path(db_path).resolve().as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT world_id FROM _world_meta WHERE singleton = 1"
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ConstructionError(f"{db_path} is not an Ontology Author World")
    return str(row[0])


def has_source_grounding(grounding: AssertionGrounding | None) -> bool:
    if grounding is None:
        return False
    for observation in grounding.observations:
        if not isinstance(observation, SourceObservation):
            continue
        if str(observation.native_handle or "").strip() and str(
            observation.source_revision or ""
        ).strip():
            return True
    return False


def has_construction_method(grounding: AssertionGrounding | None) -> bool:
    return bool(
        grounding is not None
        and str(grounding.construction_method or "").strip()
    )


class ConstructionWorld:
    """SemanticWorld plus admission scope and Contract enforcement."""

    def __init__(
        self,
        inner: SemanticWorld,
        contract: Contract | None = None,
    ) -> None:
        self._inner = inner
        stored = inner.contract_identity()
        selected = contract or Contract.from_identity(stored)
        if stored is not None and selected.identity() != stored:
            raise ConstructionError(
                "Construction Contract identity differs from the World binding"
            )
        self.contract = selected
        self.admission: dict[str, Scope] = {}

    @classmethod
    def create(
        cls,
        path: Path | str,
        *,
        world_id: str,
        contract: Contract | None = None,
    ) -> "ConstructionWorld":
        selected = contract or Contract.default()
        return cls(
            SemanticWorld(
                path,
                world_id=world_id,
                contract_id=selected.contract_id,
                contract_revision=selected.contract_revision,
            ),
            selected,
        )

    @classmethod
    def open(
        cls,
        path: Path | str,
        *,
        world_id: str | None = None,
        read_only: bool = True,
    ) -> "ConstructionWorld":
        db_path = Path(path)
        inner = SemanticWorld(
            db_path,
            world_id=world_id or world_id_of(db_path),
            read_only=read_only,
        )
        world = cls(inner)
        admission_path = db_path.parent / "world.admission.json"
        if admission_path.exists():
            world.load_admission(admission_path)
        return world

    @property
    def path(self) -> Path:
        return self._inner.path

    @property
    def world_id(self) -> str:
        return self._inner.world_id

    def contract_identity(self) -> dict[str, str] | None:
        return self._inner.contract_identity()

    def close(self) -> None:
        self._inner.close()

    def add_referent(
        self,
        referent_id: str,
        *,
        label: str = "",
        observations: Iterable[SourceObservation] = (),
    ) -> str:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner.add_referent(
            referent_id, label=label, observations=observations
        )

    def add_obligation(
        self,
        obligation_id: str,
        *,
        question: str,
        reason: str = "",
    ) -> str:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner.add_obligation(
            obligation_id, question=question, reason=reason
        )

    def obligation(self, obligation_id: str) -> dict[str, Any] | None:
        return self._inner.obligation(obligation_id)

    def obligations(self) -> list[dict[str, Any]]:
        return self._inner.obligations()

    def add_candidate(self, obligation_id: str, commitment_id: str) -> str:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner.add_candidate(obligation_id, commitment_id)

    def candidates_for(self, obligation_id: str) -> list[str]:
        return self._inner.candidates_for(obligation_id)

    def obligations_for(self, commitment_id: str) -> list[str]:
        return self._inner.obligations_for(commitment_id)

    def candidate_associations(self) -> list[dict[str, Any]]:
        return self._inner.candidate_associations()

    def resolution(self, obligation_id: str) -> dict[str, Any] | None:
        return self._inner.resolution(obligation_id)

    def resolutions(self) -> list[dict[str, Any]]:
        return self._inner.resolutions()

    def add_adjudication(
        self,
        *,
        adjudication_id: str,
        obligation_id: str,
        selected_commitment_id: str,
        authority_basis: Mapping[str, Any],
    ) -> str:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner.add_adjudication(
            adjudication_id=adjudication_id,
            obligation_id=obligation_id,
            selected_commitment_id=selected_commitment_id,
            authority_basis=authority_basis,
        )

    def adjudication(self, adjudication_id: str) -> dict[str, Any] | None:
        return self._inner.adjudication(adjudication_id)

    def adjudications(self) -> list[dict[str, Any]]:
        return self._inner.adjudications()

    def adjudications_for_obligation(self, obligation_id: str) -> list[dict[str, Any]]:
        return self._inner.adjudications_for_obligation(obligation_id)

    def _materialize_resolution(
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
        """Internal resolver-only bridge to persisted derived state."""
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner._materialize_resolution(
            obligation_id=obligation_id,
            status=status,
            selected_commitment_id=selected_commitment_id,
            reason=reason,
            candidate_assessments=candidate_assessments,
            adjudication_assessments=adjudication_assessments,
            resolution_basis=resolution_basis,
        )

    def semantic_reference_errors(self) -> list[dict[str, str]]:
        return self._inner.semantic_reference_errors()

    def declare_relation(
        self,
        name: str,
        roles: Sequence[Role],
        *,
        mode: RelationMode = RelationMode.BASE,
        description: str = "",
        scope: Scope = "WORLD",
    ) -> str:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        if scope not in ("WORLD", "PURPOSE"):
            raise ConstructionError(f"scope must be WORLD or PURPOSE, got {scope!r}")
        declared = self._inner.declare_relation(
            name, roles, mode=mode, description=description
        )
        self.admission[declared] = scope
        return declared

    def assert_tuple(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        origin: ConstructionOrigin,
        grounding: AssertionGrounding | None = None,
    ):
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        scope = self._scope(relation)
        schema = self._inner.relation_schema(relation)
        mode = schema["mode"]
        if mode == RelationMode.DERIVED.value:
            raise ConstructionError(
                f"derived relation {relation!r} cannot be asserted; use register_derivation"
            )
        reference_kinds = tuple(
            str(role["reference_kind"])
            for role in schema["roles"]
            if role.get("reference_kind")
        )
        try:
            self.contract.admit_assertion(
                relation=relation,
                scope=scope,
                mode=mode,
                origin=origin,
                has_source_grounding=has_source_grounding(grounding),
                has_provenance=True,
                has_construction_method=has_construction_method(grounding),
                semantic_reference_kinds=reference_kinds,
            )
        except ContractAdmissionError as error:
            if error.reason == "ungrounded_world_base":
                raise GroundingError(str(error)) from error
            raise
        return self._inner.assert_tuple(
            relation, values, origin=origin, grounding=grounding
        )

    def warrant_for_assertion(self, assertion_id: str) -> dict[str, Any]:
        return self._inner.warrant_for_assertion(assertion_id)

    def origins_for_assertion(self, assertion_id: str) -> list[str]:
        return self._inner.origins_for_assertion(assertion_id)

    def admission_errors(self) -> list[dict[str, Any]]:
        """Return Contract admission failures without mutating the World."""

        errors: list[dict[str, Any]] = []
        for candidate_error in self._inner.candidate_errors():
            errors.append(
                {
                    "assertion_id": candidate_error["commitment_id"],
                    "relation": "candidate_association",
                    "scope": "WORLD",
                    "reason": "candidate_integrity",
                    "message": (
                        "candidate association target is no longer valid: "
                        f"{candidate_error}"
                    ),
                }
            )
        for reference_error in self.semantic_reference_errors():
            errors.append(
                {
                    "assertion_id": reference_error["assertion_id"],
                    "relation": reference_error["relation"],
                    "scope": self.admission.get(reference_error["relation"]),
                    "reason": "contract_admission",
                    "message": (
                        "semantic reference target is no longer valid: "
                        f"{reference_error}"
                    ),
                }
            )
        for relation, scope in self.admission.items():
            schema = self.relation_schema(relation)
            if schema["mode"] != RelationMode.BASE.value:
                continue
            reference_kinds = tuple(
                str(role["reference_kind"])
                for role in schema["roles"]
                if role.get("reference_kind")
            )
            rows = self.query(
                "SELECT assertion_id FROM _world_assertions "
                "WHERE relation_name = ? ORDER BY assertion_id",
                (relation,),
            )
            for row in rows:
                assertion_id = str(row["assertion_id"])
                try:
                    supports = self._inner.construction_supports_for_assertion(
                        assertion_id
                    )
                except Exception as error:
                    errors.append(
                        {
                            "assertion_id": assertion_id,
                            "relation": relation,
                            "scope": scope,
                            "reason": "contract_admission",
                            "message": str(error),
                        }
                    )
                    continue
                for support in supports:
                    try:
                        self.contract.admit_assertion(
                            relation=relation,
                            scope=scope,
                            mode=schema["mode"],
                            origin=str(support["origin"]),
                            has_source_grounding=bool(
                                support["has_source_grounding"]
                            ),
                            has_provenance=bool(support["has_provenance"]),
                            has_construction_method=bool(
                                support["has_construction_method"]
                            ),
                            semantic_reference_kinds=reference_kinds,
                        )
                    except ContractAdmissionError as error:
                        errors.append(
                            {
                                "assertion_id": assertion_id,
                                "relation": relation,
                                "scope": scope,
                                "reason": error.reason,
                                "message": str(error),
                            }
                        )
        return errors

    def retract_tuple(self, relation: str, values: Mapping[str, Any]) -> bool:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner.retract_tuple(relation, values)

    def register_derivation(
        self, relation: str, *, sql: str, inputs: Sequence[str]
    ) -> None:
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        self._inner.register_derivation(relation, sql=sql, inputs=inputs)

    def rerun(self, relation: str, *, completeness: Completeness):
        if self._inner.read_only:
            raise ConstructionError("World is read-only")
        return self._inner.rerun(relation, completeness=completeness)

    def query_semantic(
        self, sql: str, parameters: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        return self._inner.query_semantic(sql, parameters)

    def query(self, sql: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return self._inner.query(sql, parameters)

    def latest_completeness(self, relation: str) -> dict[str, Any] | None:
        return self._inner.latest_completeness(relation)

    def relation_schema(self, relation: str) -> dict[str, Any]:
        return self._inner._store.relation_schema(relation)

    def relation_rows(self, relation: str) -> list[dict[str, Any]]:
        schema = self.relation_schema(relation)
        column_to_role = {role["column"]: role["name"] for role in schema["roles"]}
        physical = self.query_semantic(f'SELECT * FROM "{relation}"')
        rows = []
        for row in physical:
            rows.append(
                {column_to_role.get(key, key): value for key, value in row.items()}
            )
        return rows

    def load_admission(self, path: Path | str) -> None:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        relations = payload.get("relations") or {}
        self.admission = {
            str(name): ("PURPOSE" if str(scope) == "PURPOSE" else "WORLD")
            for name, scope in relations.items()
        }

    def admission_payload(self) -> dict[str, Any]:
        return {"relations": dict(sorted(self.admission.items()))}

    def _scope(self, relation: str) -> Scope:
        if relation not in self.admission:
            raise ConstructionError(
                f"relation {relation!r} has no admission scope; declare_relation first"
            )
        return self.admission[relation]


def role_text(name: str) -> Role:
    return Role(name, RoleType.TEXT)


def role_referent(name: str) -> Role:
    return Role(name, RoleType.REFERENT)

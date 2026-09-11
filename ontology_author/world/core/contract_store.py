"""Contract-bearing extensions over the existing WorldStore.

This first slice deliberately leaves resolution semantics out. It adds only the
state a later resolver needs to consume: a World/Contract binding, durable
obligations, and typed semantic references to commitments and obligations.

Commitments are, provisionally, the existing addressable assertions. This keeps
proposition identity content-addressed while warrant work remains separate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ontology_author.world.core.model import (
    Completeness,
    ObligationState,
    RelationMode,
    Role,
    RoleType,
    SemanticRefKind,
    WorldStoreError,
)
from ontology_author.world.core.store import WorldStore, _identifier, _quote


class ContractWorldStore(WorldStore):
    """WorldStore with minimal contract, obligation, and semantic-ref state."""

    def __init__(
        self,
        path: Path | str,
        *,
        world_id: str,
        purpose_ref: str = "",
        contract_id: str = "",
        contract_revision: str = "",
    ) -> None:
        super().__init__(path, world_id=world_id, purpose_ref=purpose_ref)
        self._create_contract_schema()
        if contract_id or contract_revision:
            self.bind_contract(contract_id, contract_revision)

    def _create_contract_schema(self) -> None:
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS _world_contract (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                contract_id TEXT NOT NULL,
                contract_revision TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _world_obligations (
                obligation_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('UNRESOLVED')),
                reason TEXT NOT NULL DEFAULT '',
                contract_id TEXT NOT NULL,
                contract_revision TEXT NOT NULL,
                created_revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _world_semantic_reference_roles (
                relation_name TEXT NOT NULL REFERENCES _world_relations(name) ON DELETE CASCADE,
                role_name TEXT NOT NULL,
                reference_kind TEXT NOT NULL CHECK(reference_kind IN ('COMMITMENT', 'OBLIGATION')),
                PRIMARY KEY(relation_name, role_name)
            );
            """
        )
        self._db.commit()

    # -- Contract binding -------------------------------------------------

    def bind_contract(self, contract_id: str, contract_revision: str) -> dict[str, str]:
        identity = str(contract_id or "").strip()
        revision = str(contract_revision or "").strip()
        if not identity or not revision:
            raise WorldStoreError("contract identity and revision must both be non-empty")
        existing = self._db.execute(
            "SELECT contract_id, contract_revision FROM _world_contract WHERE singleton = 1"
        ).fetchone()
        if existing is None:
            with self._db:
                self._db.execute(
                    "INSERT INTO _world_contract(singleton, contract_id, contract_revision) "
                    "VALUES (1, ?, ?)",
                    (identity, revision),
                )
                self._bump_world()
        elif (
            str(existing["contract_id"]) != identity
            or str(existing["contract_revision"]) != revision
        ):
            raise WorldStoreError(
                "World is already bound to a different Contract revision"
            )
        return {"contract_id": identity, "contract_revision": revision}

    def contract_identity(self) -> dict[str, str] | None:
        row = self._db.execute(
            "SELECT contract_id, contract_revision FROM _world_contract WHERE singleton = 1"
        ).fetchone()
        return dict(row) if row is not None else None

    # -- Obligations ------------------------------------------------------

    def add_obligation(
        self,
        obligation_id: str,
        *,
        question: str,
        reason: str = "",
    ) -> str:
        identity = str(obligation_id or "").strip()
        text = str(question or "").strip()
        if not identity:
            raise WorldStoreError("obligation identity must be non-empty")
        if not text:
            raise WorldStoreError("obligation question must be non-empty")
        contract = self.contract_identity()
        if contract is None:
            raise WorldStoreError("an obligation requires a bound Contract revision")
        existing = self._db.execute(
            "SELECT * FROM _world_obligations WHERE obligation_id = ?",
            (identity,),
        ).fetchone()
        expected = {
            "question": text,
            "state": ObligationState.UNRESOLVED.value,
            "reason": str(reason or ""),
            "contract_id": contract["contract_id"],
            "contract_revision": contract["contract_revision"],
        }
        if existing is not None:
            actual = {key: existing[key] for key in expected}
            if actual != expected:
                raise WorldStoreError(
                    f"obligation {identity!r} already exists with different semantics"
                )
            return identity
        with self._db:
            next_revision = self.revision + 1
            self._db.execute(
                "INSERT INTO _world_obligations"
                "(obligation_id, question, state, reason, contract_id, "
                "contract_revision, created_revision) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    identity,
                    text,
                    ObligationState.UNRESOLVED.value,
                    str(reason or ""),
                    contract["contract_id"],
                    contract["contract_revision"],
                    next_revision,
                ),
            )
            self._bump_world()
        return identity

    def obligation(self, obligation_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM _world_obligations WHERE obligation_id = ?",
            (str(obligation_id),),
        ).fetchone()
        return dict(row) if row is not None else None

    def obligations(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self._db.execute(
                "SELECT * FROM _world_obligations ORDER BY obligation_id"
            )
        ]

    # -- Typed semantic references ---------------------------------------

    def declare_relation(
        self,
        name: str,
        roles: Sequence[Role],
        *,
        mode: RelationMode = RelationMode.BASE,
        description: str = "",
    ) -> str:
        relation = _identifier(name, "relation name")
        semantic_refs: dict[str, SemanticRefKind] = {}
        physical_roles: list[Role] = []
        logical_roles: list[dict[str, str]] = []

        for role in roles:
            role_name = _identifier(role.name, "role name")
            role_type = RoleType(role.type)
            if role.reference_kind is not None:
                if role_type is not RoleType.TEXT:
                    raise WorldStoreError(
                        f"{relation}.{role_name} semantic references use TEXT storage"
                    )
                kind = SemanticRefKind(role.reference_kind)
                semantic_refs[role_name] = kind
                physical_roles.append(Role(role_name, RoleType.TEXT))
                logical_roles.append(
                    {
                        "name": role_name,
                        "type": RoleType.TEXT.value,
                        "reference_kind": kind.value,
                    }
                )
            else:
                physical_roles.append(Role(role_name, role_type))
                logical_roles.append({"name": role_name, "type": role_type.value})

        existing = self._db.execute(
            "SELECT 1 FROM _world_relations WHERE name = ?", (relation,)
        ).fetchone()
        if existing is not None:
            actual = self.relation_schema(relation)
            if actual["description"] != str(description) or actual["mode"] != RelationMode(mode).value:
                raise WorldStoreError(f"relation {relation!r} already has a different schema")
            actual_roles = []
            for item in actual["roles"]:
                projected = {"name": item["name"], "type": item["type"]}
                if item.get("reference_kind"):
                    projected["reference_kind"] = item["reference_kind"]
                actual_roles.append(projected)
            if actual_roles != logical_roles:
                raise WorldStoreError(f"relation {relation!r} already has a different schema")
            return relation

        declared = super().declare_relation(
            relation, physical_roles, mode=mode, description=description
        )
        with self._db:
            self._db.executemany(
                "INSERT INTO _world_semantic_reference_roles"
                "(relation_name, role_name, reference_kind) VALUES (?, ?, ?)",
                [
                    (declared, role_name, kind.value)
                    for role_name, kind in semantic_refs.items()
                ],
            )
        return declared

    def relation_schema(self, relation: str) -> dict[str, Any]:
        schema = WorldStore.relation_schema(self, relation)
        refs = {
            row["role_name"]: row["reference_kind"]
            for row in self._db.execute(
                "SELECT role_name, reference_kind "
                "FROM _world_semantic_reference_roles WHERE relation_name = ?",
                (schema["name"],),
            )
        }
        for role in schema["roles"]:
            kind = refs.get(role["name"])
            if kind:
                role["reference_kind"] = kind
        return schema

    def _normalize_values(
        self, relation: str, values: Mapping[str, Any]
    ) -> tuple[list[Any], list[str]]:
        normalized, columns = super()._normalize_values(relation, values)
        for row in self._db.execute(
            "SELECT role_name, reference_kind FROM _world_semantic_reference_roles "
            "WHERE relation_name = ?",
            (relation,),
        ):
            role_name = str(row["role_name"])
            value = str(values[role_name] or "").strip()
            if not value or not self._semantic_target_exists(
                SemanticRefKind(row["reference_kind"]), value
            ):
                raise WorldStoreError(
                    f"{relation}.{role_name} names unknown "
                    f"{str(row['reference_kind']).lower()} {value!r}"
                )
        return normalized, columns

    def _semantic_target_exists(self, kind: SemanticRefKind, identity: str) -> bool:
        if kind is SemanticRefKind.COMMITMENT:
            row = self._db.execute(
                "SELECT 1 FROM _world_assertions WHERE assertion_id = ?", (identity,)
            ).fetchone()
            return row is not None
        if kind is SemanticRefKind.OBLIGATION:
            row = self._db.execute(
                "SELECT 1 FROM _world_obligations WHERE obligation_id = ?", (identity,)
            ).fetchone()
            return row is not None
        raise WorldStoreError(f"unsupported semantic reference kind {kind!r}")

    def semantic_reference_errors(self) -> list[dict[str, str]]:
        errors: list[dict[str, str]] = []
        refs = list(
            self._db.execute(
                "SELECT r.relation_name, r.role_name, r.reference_kind, w.column_name "
                "FROM _world_semantic_reference_roles r "
                "JOIN _world_roles w ON w.relation_name = r.relation_name "
                "AND w.role_name = r.role_name "
                "ORDER BY r.relation_name, r.role_name"
            )
        )
        for spec in refs:
            relation = str(spec["relation_name"])
            column = str(spec["column_name"])
            kind = SemanticRefKind(spec["reference_kind"])
            for row in self._db.execute(
                f"SELECT _assertion_id, {_quote(column)} AS target FROM {_quote(relation)}"
            ):
                target = str(row["target"])
                if not self._semantic_target_exists(kind, target):
                    errors.append(
                        {
                            "relation": relation,
                            "assertion_id": str(row["_assertion_id"]),
                            "role": str(spec["role_name"]),
                            "reference_kind": kind.value,
                            "target": target,
                        }
                    )
        return errors

    def retract(self, relation: str, assertion_id: str) -> bool:
        for spec in self._db.execute(
            "SELECT r.relation_name, w.column_name "
            "FROM _world_semantic_reference_roles r "
            "JOIN _world_roles w ON w.relation_name = r.relation_name "
            "AND w.role_name = r.role_name "
            "WHERE r.reference_kind = 'COMMITMENT'"
        ):
            row = self._db.execute(
                f"SELECT 1 FROM {_quote(spec['relation_name'])} "
                f"WHERE {_quote(spec['column_name'])} = ? LIMIT 1",
                (assertion_id,),
            ).fetchone()
            if row is not None:
                raise WorldStoreError(
                    f"cannot retract commitment {assertion_id!r}: semantic references depend on it"
                )
        return super().retract(relation, assertion_id)

    def run_derivation(self, relation: str, *, completeness: Completeness):
        result = super().run_derivation(relation, completeness=completeness)
        dangling = self.semantic_reference_errors()
        if dangling:
            raise WorldStoreError(
                f"derivation {relation!r} left dangling semantic references: {dangling}"
            )
        return result

    def describe(self) -> dict[str, Any]:
        payload = super().describe()
        payload["world"]["contract"] = self.contract_identity()
        payload["obligations"] = self.obligations()
        return payload

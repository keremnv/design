"""Contract-bearing extensions over the existing WorldStore.

This slice keeps resolution separate from construction. It adds a World/Contract
binding, durable obligations, kernel candidate associations, typed semantic
references, and one current resolution record per obligation; the resolver
itself remains a runtime evaluation over recorded state.

Commitments are, provisionally, the existing addressable assertions. This keeps
proposition identity content-addressed while warrant work remains separate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any

from ontology_author.world.core.model import (
    Completeness,
    ObligationState,
    RelationMode,
    ResolutionStatus,
    Role,
    RoleType,
    SemanticRefKind,
    WorldStoreError,
)
from ontology_author.world.core.store import WorldStore, _identifier, _quote, _stable_id


class ContractWorldStore(WorldStore):
    """WorldStore with Contract, obligation, candidate, and semantic-ref state."""

    def __init__(
        self,
        path: Path | str,
        *,
        world_id: str,
        purpose_ref: str | None = None,
        contract_id: str = "",
        contract_revision: str = "",
        read_only: bool = False,
    ) -> None:
        super().__init__(path, world_id=world_id, purpose_ref=purpose_ref, read_only=read_only)
        if not read_only:
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
                reason TEXT NOT NULL DEFAULT '',
                contract_id TEXT NOT NULL,
                contract_revision TEXT NOT NULL,
                created_revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _world_obligation_candidates (
                obligation_id TEXT NOT NULL
                    REFERENCES _world_obligations(obligation_id) ON DELETE CASCADE,
                commitment_id TEXT NOT NULL
                    REFERENCES _world_assertions(assertion_id) ON DELETE RESTRICT,
                created_revision INTEGER NOT NULL,
                PRIMARY KEY(obligation_id, commitment_id)
            );
            CREATE INDEX IF NOT EXISTS _world_obligation_candidates_commitment_idx
                ON _world_obligation_candidates(commitment_id);
            CREATE TABLE IF NOT EXISTS _world_resolutions (
                obligation_id TEXT PRIMARY KEY
                    REFERENCES _world_obligations(obligation_id) ON DELETE CASCADE,
                status TEXT NOT NULL CHECK(status IN (
                    'RESOLVED',
                    'NO_CANDIDATE',
                    'INSUFFICIENT_WARRANT',
                    'CONFLICT',
                    'AMBIGUOUS'
                )),
                selected_commitment_id TEXT,
                reason TEXT NOT NULL DEFAULT '',
                contract_id TEXT NOT NULL,
                contract_revision TEXT NOT NULL,
                candidate_assessments TEXT NOT NULL,
                adjudication_assessments TEXT NOT NULL DEFAULT '[]',
                resolution_basis TEXT NOT NULL DEFAULT '[]',
                created_revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS _world_adjudications (
                adjudication_id TEXT PRIMARY KEY,
                obligation_id TEXT NOT NULL
                    REFERENCES _world_obligations(obligation_id) ON DELETE CASCADE,
                selected_commitment_id TEXT NOT NULL,
                authority_basis TEXT NOT NULL,
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
        self._ensure_resolution_columns()
        self._db.commit()

    def _ensure_resolution_columns(self) -> None:
        """Add current derived-resolution fields to older development Worlds."""

        columns = {
            str(row["name"])
            for row in self._db.execute("PRAGMA table_info(_world_resolutions)")
        }
        if "adjudication_assessments" not in columns:
            self._db.execute(
                "ALTER TABLE _world_resolutions ADD COLUMN "
                "adjudication_assessments TEXT NOT NULL DEFAULT '[]'"
            )
        if "resolution_basis" not in columns:
            self._db.execute(
                "ALTER TABLE _world_resolutions ADD COLUMN "
                "resolution_basis TEXT NOT NULL DEFAULT '[]'"
            )

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
                "(obligation_id, question, reason, contract_id, "
                "contract_revision, created_revision) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    identity,
                    text,
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
        return self._obligation_with_resolution(dict(row)) if row is not None else None

    def obligations(self) -> list[dict[str, Any]]:
        return [
            self._obligation_with_resolution(dict(row))
            for row in self._db.execute(
                "SELECT * FROM _world_obligations ORDER BY obligation_id"
            )
        ]

    # -- Obligation/Commitment candidates -------------------------------

    @staticmethod
    def _candidate_association_id(obligation_id: str, commitment_id: str) -> str:
        """Return a stable inspection identity for a candidate association."""

        return _stable_id("candidate", [obligation_id, commitment_id])

    def add_candidate(self, obligation_id: str, commitment_id: str) -> str:
        """Associate an existing Commitment with an existing Obligation.

        This is kernel bookkeeping, not a semantic-domain assertion. The
        association is deliberately stored outside the relation tables, while
        the two referenced identities remain hard-validated at the API
        boundary.
        """

        obligation = str(obligation_id or "").strip()
        commitment = str(commitment_id or "").strip()
        if not obligation:
            raise WorldStoreError("candidate Obligation identity must be non-empty")
        if not commitment:
            raise WorldStoreError("candidate Commitment identity must be non-empty")
        if self.obligation(obligation) is None:
            raise WorldStoreError(f"unknown candidate obligation {obligation!r}")
        found = self._db.execute(
            "SELECT 1 FROM _world_assertions WHERE assertion_id = ?",
            (commitment,),
        ).fetchone()
        if found is None:
            raise WorldStoreError(f"unknown candidate commitment {commitment!r}")
        existing = self._db.execute(
            "SELECT 1 FROM _world_obligation_candidates "
            "WHERE obligation_id = ? AND commitment_id = ?",
            (obligation, commitment),
        ).fetchone()
        if existing is not None:
            return self._candidate_association_id(obligation, commitment)
        with self._db:
            next_revision = self.revision + 1
            self._db.execute(
                "INSERT INTO _world_obligation_candidates "
                "(obligation_id, commitment_id, created_revision) VALUES (?, ?, ?)",
                (obligation, commitment, next_revision),
            )
            self._bump_world()
        return self._candidate_association_id(obligation, commitment)

    def candidates_for(self, obligation_id: str) -> list[str]:
        """Return candidate Commitment identities in deterministic order."""

        return [
            str(row["commitment_id"])
            for row in self._db.execute(
                "SELECT commitment_id FROM _world_obligation_candidates "
                "WHERE obligation_id = ? ORDER BY commitment_id",
                (str(obligation_id),),
            )
        ]

    def obligations_for(self, commitment_id: str) -> list[str]:
        """Return Obligation identities for which a Commitment is a candidate."""

        return [
            str(row["obligation_id"])
            for row in self._db.execute(
                "SELECT obligation_id FROM _world_obligation_candidates "
                "WHERE commitment_id = ? ORDER BY obligation_id",
                (str(commitment_id),),
            )
        ]

    def candidate_associations(self) -> list[dict[str, Any]]:
        """Inspect all candidate associations and their creation revisions."""

        return [
            {
                "association_id": self._candidate_association_id(
                    str(row["obligation_id"]), str(row["commitment_id"])
                ),
                "obligation_id": str(row["obligation_id"]),
                "commitment_id": str(row["commitment_id"]),
                "created_revision": int(row["created_revision"]),
            }
            for row in self._db.execute(
                "SELECT obligation_id, commitment_id, created_revision "
                "FROM _world_obligation_candidates "
                "ORDER BY obligation_id, commitment_id"
            )
        ]

    def candidate_errors(self) -> list[dict[str, str]]:
        """Find dangling candidate references before publication."""

        errors: list[dict[str, str]] = []
        for row in self._db.execute(
            "SELECT obligation_id, commitment_id "
            "FROM _world_obligation_candidates "
            "ORDER BY obligation_id, commitment_id"
        ):
            obligation = str(row["obligation_id"])
            commitment = str(row["commitment_id"])
            if self.obligation(obligation) is None:
                errors.append(
                    {
                        "obligation_id": obligation,
                        "commitment_id": commitment,
                        "reason": "unknown_candidate_obligation",
                    }
                )
            if self._db.execute(
                "SELECT 1 FROM _world_assertions WHERE assertion_id = ?",
                (commitment,),
            ).fetchone() is None:
                errors.append(
                    {
                        "obligation_id": obligation,
                        "commitment_id": commitment,
                        "reason": "unknown_candidate_commitment",
                    }
                )
        return errors

    # -- Adjudications ----------------------------------------------------

    def record_adjudication(
        self,
        *,
        adjudication_id: str,
        obligation_id: str,
        selected_commitment_id: str,
        authority_basis: Mapping[str, Any],
        contract_id: str | None = None,
        contract_revision: str | None = None,
    ) -> str:
        """Record one immutable selection of an existing candidate.

        The stored authority basis identifies the external decision/source
        record. It does not grant that record authority; resolution derives
        standing from a separate adjudication-authority configuration.
        """

        adjudication = str(adjudication_id or "").strip()
        obligation = str(obligation_id or "").strip()
        selected = str(selected_commitment_id or "").strip()
        if not adjudication:
            raise WorldStoreError("adjudication identity must be non-empty")
        if not obligation:
            raise WorldStoreError("adjudication obligation identity must be non-empty")
        if not selected:
            raise WorldStoreError("adjudication selected Commitment must be non-empty")
        if not isinstance(authority_basis, Mapping):
            raise WorldStoreError("adjudication authority_basis must be a mapping")
        basis = {str(key): value for key, value in authority_basis.items()}
        if not str(basis.get("source_id") or "").strip():
            raise WorldStoreError(
                "adjudication authority_basis requires an external source_id"
            )
        if self.obligation(obligation) is None:
            raise WorldStoreError(f"unknown adjudication obligation {obligation!r}")
        contract = self.contract_identity()
        if contract is None:
            raise WorldStoreError("an Adjudication requires a bound Contract revision")
        if contract_id is not None and str(contract_id) != contract["contract_id"]:
            raise WorldStoreError("Adjudication Contract identity does not match World")
        if contract_revision is not None and str(contract_revision) != contract["contract_revision"]:
            raise WorldStoreError("Adjudication Contract revision does not match World")
        found = self._db.execute(
            "SELECT 1 FROM _world_assertions WHERE assertion_id = ?", (selected,)
        ).fetchone()
        if found is None:
            raise WorldStoreError(f"unknown adjudication Commitment {selected!r}")
        if not self._candidate_exists(obligation, selected):
            raise WorldStoreError(
                f"selected Commitment {selected!r} is not a candidate for "
                f"obligation {obligation!r}"
            )

        encoded_basis = json.dumps(basis, sort_keys=True, separators=(",", ":"))
        existing = self._db.execute(
            "SELECT obligation_id, selected_commitment_id, authority_basis, "
            "contract_id, contract_revision FROM _world_adjudications "
            "WHERE adjudication_id = ?",
            (adjudication,),
        ).fetchone()
        expected = (
            obligation,
            selected,
            encoded_basis,
            contract["contract_id"],
            contract["contract_revision"],
        )
        if existing is not None:
            if tuple(existing) != expected:
                raise WorldStoreError(
                    f"adjudication {adjudication!r} already exists with different semantics"
                )
            return adjudication

        with self._db:
            next_revision = self.revision + 1
            self._db.execute(
                "INSERT INTO _world_adjudications "
                "(adjudication_id, obligation_id, selected_commitment_id, "
                "authority_basis, contract_id, contract_revision, created_revision) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    adjudication,
                    obligation,
                    selected,
                    encoded_basis,
                    contract["contract_id"],
                    contract["contract_revision"],
                    next_revision,
                ),
            )
            self._bump_world()
        return adjudication

    def adjudication(self, adjudication_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM _world_adjudications WHERE adjudication_id = ?",
            (str(adjudication_id),),
        ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        try:
            payload["authority_basis"] = json.loads(payload["authority_basis"])
        except (TypeError, ValueError):
            payload["authority_basis"] = {}
        return payload

    def adjudications(self) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in (
                self.adjudication(str(row["adjudication_id"]))
                for row in self._db.execute(
                    "SELECT adjudication_id FROM _world_adjudications "
                    "ORDER BY adjudication_id"
                )
            )
            if item is not None
        ]

    def adjudications_for_obligation(self, obligation_id: str) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in (
                self.adjudication(str(row["adjudication_id"]))
                for row in self._db.execute(
                    "SELECT adjudication_id FROM _world_adjudications "
                    "WHERE obligation_id = ? ORDER BY adjudication_id",
                    (str(obligation_id),),
                )
            )
            if item is not None
        ]

    def _materialize_resolution(
        self,
        *,
        obligation_id: str,
        status: ResolutionStatus | str,
        selected_commitment_id: str | None = None,
        reason: str = "",
        contract_id: str | None = None,
        contract_revision: str | None = None,
        candidate_assessments: Sequence[Mapping[str, Any]] = (),
        adjudication_assessments: Sequence[Mapping[str, Any]] = (),
        resolution_basis: Sequence[Mapping[str, Any]] = (),
    ) -> str:
        """Persist the resolver's current Resolution for one Obligation.

        This is deliberately an internal storage primitive.  Resolution is
        derived state; the runtime resolver is the only supported caller that
        materializes it.  The public World layers expose only Resolution
        reads.
        """

        identity = str(obligation_id or "").strip()
        if self.obligation(identity) is None:
            raise WorldStoreError(f"unknown obligation {identity!r}")
        resolution_status = ResolutionStatus(status)
        contract = self.contract_identity()
        if contract is None:
            raise WorldStoreError("a Resolution requires a bound Contract revision")
        if contract_id is not None and str(contract_id) != contract["contract_id"]:
            raise WorldStoreError("Resolution Contract identity does not match World")
        if contract_revision is not None and str(contract_revision) != contract["contract_revision"]:
            raise WorldStoreError("Resolution Contract revision does not match World")

        selected = str(selected_commitment_id or "").strip() or None
        if resolution_status is ResolutionStatus.RESOLVED and selected is None:
            raise WorldStoreError("RESOLVED Resolution requires selected Commitment")
        if resolution_status is not ResolutionStatus.RESOLVED and selected is not None:
            raise WorldStoreError(
                f"{resolution_status.value} Resolution cannot select a Commitment"
            )
        if selected is not None:
            found = self._db.execute(
                "SELECT 1 FROM _world_assertions WHERE assertion_id = ?", (selected,)
            ).fetchone()
            if found is None:
                raise WorldStoreError(f"unknown selected commitment {selected!r}")
            if not self._candidate_exists(identity, selected):
                raise WorldStoreError(
                    f"selected commitment {selected!r} is not a candidate for "
                    f"obligation {identity!r}"
                )

        assessments = [dict(item) for item in candidate_assessments]
        encoded = json.dumps(assessments, sort_keys=True, separators=(",", ":"))
        adjudications = [dict(item) for item in adjudication_assessments]
        encoded_adjudications = json.dumps(
            adjudications, sort_keys=True, separators=(",", ":")
        )
        basis = [dict(item) for item in resolution_basis]
        encoded_basis = json.dumps(basis, sort_keys=True, separators=(",", ":"))
        existing = self._db.execute(
            "SELECT status, selected_commitment_id, reason, contract_id, "
            "contract_revision, candidate_assessments, adjudication_assessments, "
            "resolution_basis "
            "FROM _world_resolutions WHERE obligation_id = ?",
            (identity,),
        ).fetchone()
        expected = (
            resolution_status.value,
            selected,
            str(reason or ""),
            contract["contract_id"],
            contract["contract_revision"],
            encoded,
            encoded_adjudications,
            encoded_basis,
        )
        if existing is not None and tuple(existing) == expected:
            return f"resolution:{identity}"
        with self._db:
            next_revision = self.revision + 1
            self._db.execute(
                "INSERT INTO _world_resolutions "
                "(obligation_id, status, selected_commitment_id, reason, contract_id, "
                "contract_revision, candidate_assessments, adjudication_assessments, "
                "resolution_basis, created_revision) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(obligation_id) DO UPDATE SET "
                "status = excluded.status, "
                "selected_commitment_id = excluded.selected_commitment_id, "
                "reason = excluded.reason, contract_id = excluded.contract_id, "
                "contract_revision = excluded.contract_revision, "
                "candidate_assessments = excluded.candidate_assessments, "
                "adjudication_assessments = excluded.adjudication_assessments, "
                "resolution_basis = excluded.resolution_basis, "
                "created_revision = excluded.created_revision",
                (
                    identity,
                    resolution_status.value,
                    selected,
                    str(reason or ""),
                    contract["contract_id"],
                    contract["contract_revision"],
                    encoded,
                    encoded_adjudications,
                    encoded_basis,
                    next_revision,
                ),
            )
            self._bump_world()
        return f"resolution:{identity}"

    def _candidate_exists(self, obligation_id: str, commitment_id: str) -> bool:
        row = self._db.execute(
            "SELECT 1 FROM _world_obligation_candidates "
            "WHERE obligation_id = ? AND commitment_id = ?",
            (obligation_id, commitment_id),
        ).fetchone()
        return row is not None

    def resolution(self, obligation_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM _world_resolutions WHERE obligation_id = ?",
            (str(obligation_id),),
        ).fetchone()
        if row is None:
            return None
        payload = dict(row)
        try:
            assessments = json.loads(payload["candidate_assessments"])
        except (TypeError, ValueError):
            assessments = []
        payload["candidate_assessments"] = assessments
        for field in ("adjudication_assessments", "resolution_basis"):
            try:
                payload[field] = json.loads(payload[field])
            except (KeyError, TypeError, ValueError):
                payload[field] = []
        payload["resolution_id"] = f"resolution:{payload['obligation_id']}"
        return payload

    def resolutions(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in self._db.execute(
            "SELECT obligation_id FROM _world_resolutions ORDER BY obligation_id"
        ):
            item = self.resolution(str(row["obligation_id"]))
            if item is not None:
                out.append(item)
        return out

    def _obligation_with_resolution(self, obligation: dict[str, Any]) -> dict[str, Any]:
        # `state` is a read-model projection. The durable question carries no
        # mutable resolution state; the current Resolution is the only source
        # of truth for whether it has a governing answer.
        obligation["state"] = ObligationState.UNRESOLVED.value
        resolution = self.resolution(str(obligation["obligation_id"]))
        if resolution is None:
            return obligation
        obligation["state"] = (
            ObligationState.RESOLVED.value
            if resolution["status"] == ResolutionStatus.RESOLVED.value
            else ObligationState.UNRESOLVED.value
        )
        obligation["resolution_status"] = resolution["status"]
        obligation["resolution_reason"] = resolution["reason"]
        obligation["selected_commitment_id"] = resolution["selected_commitment_id"]
        obligation["candidate_assessments"] = resolution["candidate_assessments"]
        obligation["adjudication_assessments"] = resolution[
            "adjudication_assessments"
        ]
        obligation["resolution_basis"] = resolution["resolution_basis"]
        return obligation

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
        candidate = self._db.execute(
            "SELECT 1 FROM _world_obligation_candidates "
            "WHERE commitment_id = ? LIMIT 1",
            (assertion_id,),
        ).fetchone()
        if candidate is not None:
            raise WorldStoreError(
                f"cannot retract commitment {assertion_id!r}: "
                "candidate associations depend on it"
            )
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
        candidates = self.candidate_errors()
        if candidates:
            raise WorldStoreError(
                f"derivation {relation!r} left dangling candidate associations: "
                f"{candidates}"
            )
        return result

    def describe(self) -> dict[str, Any]:
        payload = super().describe()
        payload["world"]["contract"] = self.contract_identity()
        payload["obligations"] = self.obligations()
        payload["obligation_candidates"] = self.candidate_associations()
        return payload

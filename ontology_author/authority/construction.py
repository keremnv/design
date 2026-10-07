"""Explicit authority-construction writer over a candidate governed World.

The constructor receives construction decisions. It does not extract meaning
from Markdown. Semantic referents are created only when asked.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ontology_author.world.core.model import Completeness, CompletenessStatus, RelationMode, Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld
from ontology_author.construction_boundary import ConstructionBasis, SupportPath
from ontology_author.program_backend import ProgramBackend
from ontology_author.world.runtime.publication import PublicationRef

from .schemas import (
    MECHANISM_KEY,
    CONSTRUCTOR_ID,
    CONSTRUCTOR_VERSION,
    DEFAULT_PROFILE,
    RECEIPT_VERSION,
    AdequacyOutcome,
    AuthorityConstructionError,
    AuthorityConstructionReceipt,
    ClaimKind,
    CompletenessScope,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    UnresolvedKind,
)
from ontology_author.evidence.markdown import MARKDOWN_DRIVER, MarkdownRegion, MarkdownSource, parse_byte_location
from .relevance import (
    default_relevance_clauses,
    normalize_clause,
    relation_rows_with_ids,
    scope_row_values,
)


AUTHORITY_RELATIONS = (
    "authority_source",
    "semantic_entity",
    "authority_claim",
    "authority_endpoint_resolution",
    "authority_attachment_warrant",
    "authority_relevance_scope",
    "authority_unresolved",
    "authority_unresolved_candidate",
    "authority_examined",
    "authority_completeness",
    "authority_adequacy",
    "authority_grounds_semantic",
    "authority_attachment_scope",
)

CERTAIN_RESOLUTIONS = {
    ReferentResolution.NATIVE_ID,
    ReferentResolution.DETERMINISTIC,
    ReferentResolution.SOURCE_DEFINED,
    ReferentResolution.AGENT_RESOLVED,
}


@dataclass(frozen=True)
class DeclaredSource:
    handle: str
    path: Path
    standing: SourceStanding
    driver: str = MARKDOWN_DRIVER


@dataclass(frozen=True)
class AuthorityUniverse:
    universe_id: str
    sources: tuple[DeclaredSource, ...]
    workspace: Path

    def source(self, handle: str) -> DeclaredSource:
        for item in self.sources:
            if item.handle == handle:
                return item
        raise AuthorityConstructionError(f"source {handle!r} is not in the declared universe")


@dataclass
class AuthorityConstructor:
    """Narrow API for persisting authority-derived World facts."""

    world: ConstructionWorld
    universe: AuthorityUniverse
    construction_id: str
    purpose: str
    profile: str = DEFAULT_PROFILE
    program_universe: str = "declared_program_boundary"
    constructor_id: str = CONSTRUCTOR_ID
    constructor_version: str = CONSTRUCTOR_VERSION
    acceptance: Mapping[str, Any] | None = None
    publication_inputs: tuple[PublicationRef, ...] = ()
    candidate_baseline: PublicationRef | None = None
    program_backend: ProgramBackend | None = None

    def __post_init__(self) -> None:
        self.markdown: dict[str, MarkdownSource] = {}
        self.exploration: list[dict[str, Any]] = []
        self.created_semantic: list[str] = []
        self.reused_semantic: list[str] = []
        self.known_losses: list[str] = []
        self.resolvers: list[str] = []
        self.native_relationships: list[dict[str, Any]] = []
        self._snapshot_id = ""
        self._snapshot_ref = ""
        self._method = f"{self.profile}:explicit"
        _declare_authority_relations(self.world)
        self._load_snapshot()
        if len({source.handle for source in self.universe.sources}) != len(self.universe.sources):
            raise AuthorityConstructionError("declared source handles must be unique")
        self._load_markdown()
        self._declare_sources()
        self.basis = ConstructionBasis(
            observations=tuple(source.observe(source.document()) for source in self.markdown.values()),
            publications=self.publication_inputs,
            program_snapshots=(
                ((self.candidate_baseline, self._snapshot_ref, self._snapshot_id),)
                if self._snapshot_ref and self.candidate_baseline else ()
            ),
            configuration_json=json.dumps({
                "purpose": self.purpose, "profile": self.profile,
                "universe_id": self.universe.universe_id,
                "program_universe": self.program_universe if self._snapshot_ref else None,
                "sources": [
                    {"handle": item.handle, "standing": item.standing.value, "driver": item.driver}
                    for item in self.universe.sources
                ],
            }, sort_keys=True),
            candidate_baseline=self.candidate_baseline,
        )

    def source(self, handle: str) -> MarkdownSource:
        if handle not in self.markdown:
            raise AuthorityConstructionError(f"no Markdown driver loaded for {handle!r}")
        return self.markdown[handle]

    def note_exploration(self, *, action: str, target: str, detail: str = "") -> None:
        # Compatibility scratch state only. Investigation is not publication
        # provenance and is deliberately omitted from new durable receipts.
        self.exploration.append({"action": action, "target": target, "detail": detail})

    def examine(self, observation: SourceObservation, *, block_kind: str = "") -> None:
        existing = {
            (row["source_handle"], row["native_location"])
            for row in self.world.relation_rows("authority_examined")
        }
        if (observation.native_handle, observation.native_location) in existing:
            return
        locator = _locator_from_observation(observation)
        self._assert(
            "authority_examined",
            {
                "source_handle": observation.native_handle,
                "native_location": observation.native_location,
                "block_kind": block_kind or str(locator.get("block_kind") or "region"),
                "content_revision": observation.source_revision,
            },
            observations=(observation,),
            extra={"authority_construction": MECHANISM_KEY, "provenance": "construction_coverage"},
        )

    def create_semantic_referent(
        self,
        referent_id: str,
        *,
        label: str,
        observations: Sequence[SourceObservation],
    ) -> str:
        self._require_semantic_id(referent_id)
        if self._referent_exists(referent_id):
            raise AuthorityConstructionError(f"semantic referent already exists: {referent_id}")
        if not observations:
            raise AuthorityConstructionError("semantic referent creation needs support observations")
        self.world.add_referent(referent_id, label=label, observations=observations)
        self._assert(
            "semantic_entity",
            {"entity": referent_id},
            observations=observations,
            extra={"authority_construction": MECHANISM_KEY, "semantic_created": True},
        )
        for observation in observations:
            self.associate_source_semantic(referent_id, observation)
        self.created_semantic.append(referent_id)
        return referent_id

    def reuse_semantic_referent(self, referent_id: str) -> str:
        self._require_semantic_id(referent_id)
        if not self._is_semantic_member(referent_id):
            raise AuthorityConstructionError(f"semantic referent is not a constructed member: {referent_id}")
        self.reused_semantic.append(referent_id)
        return referent_id

    def associate_source_semantic(self, semantic: str, observation: SourceObservation) -> str:
        self._require_semantic_id(semantic)
        return self.persist_claim(
            "authority_grounds_semantic",
            {
                "semantic": semantic,
                "source_handle": observation.native_handle,
                "native_location": observation.native_location,
            },
            claim_kind=ClaimKind.SOURCE_SEMANTIC,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"semantic": ReferentResolution.AGENT_RESOLVED},
            observations=(observation,),
        )

    def persist_claim(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        claim_kind: ClaimKind | str,
        support: RelationSupport | str,
        endpoint_resolution: Mapping[str, ReferentResolution | str],
        observations: Sequence[SourceObservation],
        roles: Sequence[Role] | None = None,
        governing: bool | None = None,
        warrant: Sequence[Mapping[str, Any]] = (),
        construction_method: str = "",
        resolvers: Sequence[str] = (),
        support_paths: Sequence[SupportPath] | None = None,
    ) -> str:
        kind = ClaimKind(claim_kind)
        support_class = RelationSupport(support)
        resolutions = {
            str(role): ReferentResolution(value)
            for role, value in dict(endpoint_resolution).items()
        }
        if roles:
            self.world.declare_relation(relation, roles, description="Purpose-specific authority domain relation.")
        if not observations:
            raise AuthorityConstructionError("persisted claims need support observations")
        paths = tuple(support_paths) if support_paths is not None else (SupportPath(tuple(observations)),)
        if not paths or {
            tuple(member.as_pointer().items()) for path in paths for member in path.members
        } != {tuple(item.as_pointer().items()) for item in observations}:
            raise AuthorityConstructionError("support paths must cover exactly the claim observations")
        if kind != ClaimKind.UNRESOLVED_RECORD:
            for role, resolution in resolutions.items():
                if resolution not in CERTAIN_RESOLUTIONS:
                    raise AuthorityConstructionError(
                        "certain claims cannot use AMBIGUOUS or UNRESOLVED endpoint resolution"
                    )
                if role not in values:
                    raise AuthorityConstructionError(f"resolution role {role!r} is absent from claim values")
        governing_flag = self._governing_flag(support_class, governing)
        self._require_support_standing(observations, governing=governing_flag)
        for observation in observations:
            self.examine(observation)
        extra = self._envelope(
            claim_kind=kind,
            support=support_class,
            resolutions=resolutions,
            observations=observations,
            governing=governing_flag,
            resolvers=resolvers,
        )
        extra["support_paths"] = [path.as_dict() for path in paths]
        inserted = self._assert(
            relation,
            values,
            observations=observations,
            extra=extra,
            method=construction_method or self._method,
        )
        assertion_id = inserted.assertion_id
        self._assert(
            "authority_claim",
            {
                "assertion_id": assertion_id,
                "relation_name": relation,
                "claim_kind": kind.value,
                "relation_support": support_class.value,
                "governing": governing_flag,
            },
            observations=observations,
            extra=extra,
            method=construction_method or self._method,
        )
        for role, referent in values.items():
            if role not in resolutions:
                continue
            self._assert(
                "authority_endpoint_resolution",
                {
                    "assertion_id": assertion_id,
                    "role": role,
                    "referent": str(referent),
                    "resolution": resolutions[role].value,
                },
                observations=observations,
                extra=extra,
                method=construction_method or self._method,
            )
        program_endpoints = [
            str(value) for role, value in values.items()
            if role in resolutions and self._is_program_entity(str(value))
        ]
        if program_endpoints:
            if not warrant:
                warrant = tuple(self._default_warrant(entity, support_class, resolutions) for entity in program_endpoints)
            if len(warrant) != len(program_endpoints):
                raise AuthorityConstructionError("each program endpoint needs an attachment warrant")
            for entity, record in zip(program_endpoints, warrant):
                self._persist_warrant(
                    assertion_id,
                    program_entity=str(record.get("program_entity") or entity),
                    support=support_class,
                    resolutions=resolutions,
                    observations=observations,
                    extra=extra,
                    record=record,
                )
        scoped = {
            (row["target"], row["purpose"])
            for row in self.world.relation_rows("authority_attachment_scope")
        }
        for entity in list(program_endpoints):
            if (entity, self.purpose) not in scoped and self._is_program_entity(entity):
                self._assert(
                    "authority_attachment_scope",
                    {"target": entity, "purpose": self.purpose},
                    observations=observations,
                    extra=extra,
                )
                scoped.add((entity, self.purpose))
        if kind == ClaimKind.SEMANTIC_PROGRAM:
            for value in values.values():
                semantic = str(value)
                if self._is_semantic_member(semantic) and (semantic, self.purpose) not in scoped:
                    self._assert(
                        "authority_attachment_scope",
                        {"target": semantic, "purpose": self.purpose},
                        observations=observations,
                        extra=extra,
                    )
                    scoped.add((semantic, self.purpose))
        self.resolvers.extend(str(item) for item in resolvers)
        return assertion_id

    def persist_unresolved(
        self,
        record_id: str,
        *,
        kind: UnresolvedKind | str,
        observation: SourceObservation,
        detail: str = "",
        candidates: Sequence[str] = (),
        support: RelationSupport | str = RelationSupport.SOURCE_EXPLICIT,
    ) -> str:
        unresolved = UnresolvedKind(kind)
        support_class = RelationSupport(support)
        extra = self._envelope(
            claim_kind=ClaimKind.UNRESOLVED_RECORD,
            support=support_class,
            resolutions={"record": ReferentResolution.UNRESOLVED},
            observations=(observation,),
            governing=False,
        )
        self.examine(observation)
        inserted = self._assert(
            "authority_unresolved",
            {
                "record_id": record_id,
                "kind": unresolved.value,
                "source_handle": observation.native_handle,
                "native_location": observation.native_location,
                "detail": detail,
                "candidates_json": json.dumps(list(candidates), sort_keys=True),
            },
            observations=(observation,),
            extra=extra,
        )
        for candidate in candidates:
            if not self._is_program_entity(candidate) and not self._is_semantic_member(candidate):
                raise AuthorityConstructionError(f"unresolved candidate is not a World identity: {candidate}")
            self._assert(
                "authority_unresolved_candidate",
                {"record_id": record_id, "candidate": candidate},
                observations=(observation,),
                extra=extra,
            )
        self._assert(
            "authority_claim",
            {
                "assertion_id": inserted.assertion_id,
                "relation_name": "authority_unresolved",
                "claim_kind": ClaimKind.UNRESOLVED_RECORD.value,
                "relation_support": support_class.value,
                "governing": False,
            },
            observations=(observation,),
            extra=extra,
        )
        return inserted.assertion_id

    def record_completeness(
        self,
        *,
        scope: CompletenessScope | str,
        universe: str,
        status: CompletenessStatus | str,
        basis: str,
        known_gaps: Sequence[str] = (),
    ) -> None:
        scope_value = CompletenessScope(scope)
        status_value = CompletenessStatus(status)
        observation = self.source(self.universe.sources[0].handle).observe(
            self.source(self.universe.sources[0].handle).document()
        )
        self._assert(
            "authority_completeness",
            {
                "scope": scope_value.value,
                "universe": universe,
                "status": status_value.value,
                "basis": basis,
                "known_gaps": json.dumps(list(known_gaps), sort_keys=True),
                "purpose": self.purpose,
            },
            observations=(observation,),
            extra={"authority_construction": MECHANISM_KEY, "completeness_scope": scope_value.value},
        )

    def record_adequacy(
        self,
        probe: str,
        outcome: AdequacyOutcome | str,
        *,
        detail: str = "",
        observation: SourceObservation | None = None,
    ) -> None:
        selected = observation or self.source(self.universe.sources[0].handle).observe(
            self.source(self.universe.sources[0].handle).document()
        )
        self._assert(
            "authority_adequacy",
            {
                "probe": probe,
                "outcome": AdequacyOutcome(outcome).value,
                "detail": detail,
            },
            observations=(selected,),
            extra={"authority_construction": MECHANISM_KEY, "adequacy": True},
        )

    def declare_attachment_universe(
        self,
        entities: Sequence[str],
        *,
        observation: SourceObservation | None = None,
    ) -> None:
        """Record program identities in the attachment-completeness universe.

        This does not create an attachment or warrant. It only enlarges the
        declared universe over which attachment completeness is claimed.
        """

        selected = observation or self.source(self.universe.sources[0].handle).observe(
            self.source(self.universe.sources[0].handle).document()
        )
        scoped = {
            (row["target"], row["purpose"])
            for row in self.world.relation_rows("authority_attachment_scope")
        }
        extra = {"authority_construction": MECHANISM_KEY, "attachment_universe": True}
        for entity in entities:
            entity_id = str(entity)
            if not self._is_program_entity(entity_id):
                raise AuthorityConstructionError(
                    f"attachment-universe member is not a program identity: {entity_id}"
                )
            if (entity_id, self.purpose) in scoped:
                continue
            self._assert(
                "authority_attachment_scope",
                {"target": entity_id, "purpose": self.purpose},
                observations=(selected,),
                extra=extra,
            )
            scoped.add((entity_id, self.purpose))

    def declare_relevance_scope(
        self,
        clauses: Sequence[Mapping[str, Any]],
        *,
        warrant_assertion_id: str | None = None,
        assertion_id: str | None = None,
        program_entity: str | None = None,
        observations: Sequence[SourceObservation] = (),
    ) -> list[str]:
        """Persist explicit construction-time relevance-scope additions."""

        warrant = self._resolve_warrant(
            warrant_assertion_id=warrant_assertion_id,
            assertion_id=assertion_id,
            program_entity=program_entity,
        )
        selected = tuple(observations) or tuple(self._observations_for(str(warrant["_assertion_id"])))
        if not selected:
            raise AuthorityConstructionError("relevance scope needs reconstructible observations")
        extra = {
            "authority_construction": MECHANISM_KEY,
            "relevance_scope": True,
            "scope_origin": "EXPLICIT",
        }
        inserted: list[str] = []
        for clause in clauses:
            try:
                normalized = normalize_clause(
                    clause,
                    program_entity=str(warrant["program_entity"]),
                    origin="EXPLICIT",
                )
            except ValueError as exc:
                raise AuthorityConstructionError(str(exc)) from exc
            self._validate_scope_identities(normalized, program_entity=str(warrant["program_entity"]))
            row = self._assert(
                "authority_relevance_scope",
                scope_row_values(
                    warrant_assertion_id=str(warrant["_assertion_id"]),
                    attachment_assertion_id=str(warrant["assertion_id"]),
                    program_entity=str(warrant["program_entity"]),
                    clause=normalized,
                ),
                observations=selected,
                extra=extra,
            )
            inserted.append(row.assertion_id)
        return inserted

    def record_native_relationship(self, relationship: Mapping[str, Any]) -> None:
        self.native_relationships.append(dict(relationship))

    def add_known_loss(self, statement: str) -> None:
        if statement and statement not in self.known_losses:
            self.known_losses.append(statement)

    def program_entities(
        self,
        *,
        kind: str | None = None,
        label: str | None = None,
        descriptor_contains: str | None = None,
    ) -> list[str]:
        if self.program_backend is None:
            return []
        if kind is None and label is None and descriptor_contains is None:
            return list(self.program_backend.members())
        return list(
            self.program_backend.discover(
                kind=kind, label=label, descriptor_contains=descriptor_contains
            )
        )

    def call_site_invoking(self, target_label: str) -> str:
        targets = self.program_entities(kind="callable", label=target_label)
        if len(targets) != 1:
            raise AuthorityConstructionError(f"callable {target_label!r} is not unique: {targets}")
        matches = [
            str(row["call_site"])
            for row in self._invocation_rows()
            if row["target"] == targets[0]
        ]
        if len(matches) != 1:
            raise AuthorityConstructionError(f"call site invoking {target_label!r} is not unique: {matches}")
        return matches[0]

    def structural_context(self, entity: str) -> list[str]:
        if self.program_backend is None:
            raise AuthorityConstructionError("structural context needs a governed program snapshot")
        parents = {
            str(row["child"]): str(row["parent"])
            for row in self.program_backend.containment()
        }
        chain = [entity]
        current = entity
        seen: set[str] = {entity}
        while current in parents and parents[current] not in seen:
            current = parents[current]
            chain.append(current)
            seen.add(current)
        chain.reverse()
        return chain

    def invoked_targets(self, call_site: str) -> list[str]:
        return [
            str(row["target"])
            for row in self._invocation_rows()
            if row["call_site"] == call_site
        ]

    def _invocation_rows(self) -> tuple[dict[str, str], ...]:
        if self.program_backend is None:
            return ()
        return self.program_backend.invocations()

    def _resolution_rows(self) -> tuple[dict[str, str], ...]:
        if self.program_backend is None:
            return ()
        return self.program_backend.resolutions()

    def finish(self) -> AuthorityConstructionReceipt:
        self._materialize_completeness()
        receipt = self._receipt()
        return receipt

    def _load_snapshot(self) -> None:
        if self.program_backend is None:
            self._snapshot_ref = ""
            self._snapshot_id = ""
            return
        self._snapshot_ref = self.program_backend.snapshot()
        self._snapshot_id = self.program_backend.snapshot_id()

    def _load_markdown(self) -> None:
        for declared in self.universe.sources:
            source = MarkdownSource(declared.path, handle=declared.handle)
            self.markdown[declared.handle] = source
            self.known_losses.extend(source.known_losses())
            for link in source.links():
                self.record_native_relationship(
                    {
                        "kind": "markdown_link",
                        "handle": declared.handle,
                        "destination": link.destination_text,
                        "text_location": link.text.native_location,
                        "destination_location": link.destination.native_location,
                    }
                )

    def _declare_sources(self) -> None:
        for declared in self.universe.sources:
            source = self.markdown[declared.handle]
            observation = source.observe(source.document())
            self._assert(
                "authority_source",
                {
                    "source_handle": declared.handle,
                    "driver": declared.driver,
                    "content_revision": source.revision,
                    "standing": declared.standing.value,
                    "provider": "markdown",
                },
                observations=(observation,),
                extra={
                    "authority_construction": MECHANISM_KEY,
                    "standing": declared.standing.value,
                    "universe_id": self.universe.universe_id,
                },
            )

    def _default_warrant(
        self,
        entity: str,
        support: RelationSupport,
        resolutions: Mapping[str, ReferentResolution],
    ) -> dict[str, Any]:
        invokes = self.invoked_targets(entity)
        return {
            "program_entity": entity,
            "structural_context": self.structural_context(entity),
            "justifying_program_relations": (
                [{"relation": "program_invokes", "call_site": entity, "target": target} for target in invokes]
                if invokes
                else []
            ),
            "justifying_resolution_outcomes": [
                {
                    "subject": row["subject"],
                    "status": row["status"],
                    "capability": row["capability"],
                }
                for row in self._resolution_rows()
                if row["subject"] == entity
            ],
            "relation_support": support.value,
            "endpoint_resolution": {role: value.value for role, value in resolutions.items()},
        }

    def _persist_warrant(
        self,
        assertion_id: str,
        *,
        program_entity: str,
        support: RelationSupport,
        resolutions: Mapping[str, ReferentResolution],
        observations: Sequence[SourceObservation],
        extra: Mapping[str, Any],
        record: Mapping[str, Any],
    ) -> None:
        if not self._is_program_entity(program_entity):
            raise AuthorityConstructionError(f"warrant program entity is not in the program universe: {program_entity}")
        snapshot = str(record.get("program_snapshot_id") or self._snapshot_id)
        if snapshot != self._snapshot_id:
            raise AuthorityConstructionError("attachment warrant snapshot does not match the governed program snapshot")
        inserted = self._assert(
            "authority_attachment_warrant",
            {
                "assertion_id": assertion_id,
                "program_snapshot_id": snapshot,
                "program_entity": program_entity,
                "structural_context": json.dumps(list(record.get("structural_context") or self.structural_context(program_entity)), sort_keys=True),
                "justifying_program_relations": json.dumps(list(record.get("justifying_program_relations") or []), sort_keys=True),
                "justifying_resolution_outcomes": json.dumps(list(record.get("justifying_resolution_outcomes") or []), sort_keys=True),
                "constructor_profile": self.profile,
                "relation_support": str(record.get("relation_support") or support.value),
                "endpoint_resolution": json.dumps(
                    record.get("endpoint_resolution")
                    or {role: value.value for role, value in resolutions.items()},
                    sort_keys=True,
                ),
            },
            observations=observations,
            extra=dict(extra),
        )
        self._persist_default_relevance_scope(
            warrant_assertion_id=inserted.assertion_id,
            attachment_assertion_id=assertion_id,
            program_entity=program_entity,
            observations=observations,
            extra=extra,
        )
        return inserted.assertion_id

    def _persist_default_relevance_scope(
        self,
        *,
        warrant_assertion_id: str,
        attachment_assertion_id: str,
        program_entity: str,
        observations: Sequence[SourceObservation],
        extra: Mapping[str, Any],
    ) -> None:
        kind = self._entity_kind(program_entity)
        scope_extra = {
            **dict(extra),
            "relevance_scope": True,
            "scope_origin": "DEFAULT_KIND_RULE",
            "entity_kind": kind,
        }
        for clause in default_relevance_clauses(kind, program_entity):
            try:
                normalized = normalize_clause(clause, program_entity=program_entity, origin="DEFAULT_KIND_RULE")
            except ValueError as exc:
                raise AuthorityConstructionError(str(exc)) from exc
            self._assert(
                "authority_relevance_scope",
                scope_row_values(
                    warrant_assertion_id=warrant_assertion_id,
                    attachment_assertion_id=attachment_assertion_id,
                    program_entity=program_entity,
                    clause=normalized,
                ),
                observations=observations,
                extra=scope_extra,
            )

    def _resolve_warrant(
        self,
        *,
        warrant_assertion_id: str | None,
        assertion_id: str | None,
        program_entity: str | None,
    ) -> dict[str, Any]:
        rows = relation_rows_with_ids(self.world, "authority_attachment_warrant")
        if warrant_assertion_id:
            for row in rows:
                if str(row.get("_assertion_id") or "") == warrant_assertion_id:
                    return row
            raise AuthorityConstructionError(f"unknown attachment warrant: {warrant_assertion_id}")
        if not assertion_id or not program_entity:
            raise AuthorityConstructionError("relevance scope needs a warrant or assertion_id+program_entity")
        matches = [
            row for row in rows
            if str(row["assertion_id"]) == assertion_id and str(row["program_entity"]) == program_entity
        ]
        if len(matches) != 1:
            raise AuthorityConstructionError("relevance scope warrant is not unique")
        return matches[0]

    def _validate_scope_identities(self, clause: Mapping[str, Any], *, program_entity: str) -> None:
        identities = {program_entity, str(clause.get("identity_id") or "")}
        relation_tuple = clause.get("relation_tuple") or {}
        if isinstance(relation_tuple, Mapping):
            for key, value in relation_tuple.items():
                if key == "relation":
                    continue
                if isinstance(value, str) and value:
                    identities.add(value)
        for identity in identities:
            if not identity:
                continue
            if not self._is_program_entity(identity):
                raise AuthorityConstructionError(
                    f"relevance-scope identity is not in the construction snapshot: {identity}"
                )

    def _observations_for(self, assertion_id: str) -> list[SourceObservation]:
        rows = self.world.query(
            "SELECT kind, detail FROM _world_groundings "
            "WHERE subject_type='ASSERTION' AND subject_id=?",
            (assertion_id,),
        )
        output: list[SourceObservation] = []
        for row in rows:
            if str(row["kind"]) != "SOURCE":
                continue
            try:
                detail = json.loads(row["detail"] or "{}")
            except json.JSONDecodeError:
                continue
            if not isinstance(detail, dict):
                continue
            if not all(detail.get(key) for key in ("provider", "native_handle", "source_revision", "native_location")):
                continue
            output.append(
                SourceObservation(
                    provider=str(detail["provider"]),
                    native_handle=str(detail["native_handle"]),
                    source_revision=str(detail["source_revision"]),
                    native_location=str(detail["native_location"]),
                )
            )
        return output

    def _entity_kind(self, entity: str) -> str:
        if self.program_backend is None:
            return ""
        return self.program_backend.kind(entity) or ""

    def _materialize_completeness(self) -> None:
        derived = {
            "authority_addressability": (
                "authority_source",
                "SELECT source_handle, driver, content_revision, standing, provider FROM authority_source",
                [
                    Role("source_handle", RoleType.TEXT),
                    Role("driver", RoleType.TEXT),
                    Role("content_revision", RoleType.TEXT),
                    Role("standing", RoleType.TEXT),
                    Role("provider", RoleType.TEXT),
                ],
            ),
            "authority_construction_coverage": (
                "authority_examined",
                "SELECT source_handle, native_location, block_kind, content_revision FROM authority_examined",
                [
                    Role("source_handle", RoleType.TEXT),
                    Role("native_location", RoleType.TEXT),
                    Role("block_kind", RoleType.TEXT),
                    Role("content_revision", RoleType.TEXT),
                ],
            ),
            "authority_attachment_coverage": (
                "authority_attachment_scope",
                "SELECT target_id, purpose FROM authority_attachment_scope",
                [Role("target", RoleType.REFERENT), Role("purpose", RoleType.TEXT)],
            ),
        }
        declared = {row["scope"]: row for row in self.world.relation_rows("authority_completeness")}
        mapping = {
            CompletenessScope.ADDRESSABILITY.value: "authority_addressability",
            CompletenessScope.CONSTRUCTION.value: "authority_construction_coverage",
            CompletenessScope.ATTACHMENT.value: "authority_attachment_coverage",
        }
        for derived_name, (universe, sql, roles) in derived.items():
            self.world.declare_relation(
                derived_name,
                roles,
                mode=RelationMode.DERIVED,
                description="Authority construction completeness materialization.",
            )
            self.world.register_derivation(derived_name, sql=sql, inputs=[universe])
            record = next(
                (item for scope, item in declared.items() if mapping.get(scope) == derived_name),
                None,
            )
            status = CompletenessStatus(record["status"]) if record else CompletenessStatus.INCOMPLETE
            basis = str(record["basis"]) if record else "no completeness claim was declared for this scope"
            gaps = tuple(json.loads(record["known_gaps"])) if record else ("undeclared completeness scope",)
            if status is CompletenessStatus.COMPLETE:
                gaps = ()
            self.world.rerun(
                derived_name,
                completeness=Completeness(status, universe=universe, basis=basis, known_gaps=gaps),
            )

    def _receipt(self) -> AuthorityConstructionReceipt:
        standing = Counter(row["standing"] for row in self.world.relation_rows("authority_source"))
        claims = self.world.relation_rows("authority_claim")
        by_kind = Counter(row["claim_kind"] for row in claims)
        support = Counter(row["relation_support"] for row in claims)
        resolutions = Counter(row["resolution"] for row in self.world.relation_rows("authority_endpoint_resolution"))
        unresolved = [
            {
                "record_id": row["record_id"],
                "kind": row["kind"],
                "source_handle": row["source_handle"],
                "native_location": row["native_location"],
                "detail": row["detail"],
            }
            for row in self.world.relation_rows("authority_unresolved")
        ]
        completeness_refs = []
        for row in self.world.relation_rows("authority_completeness"):
            derived = {
                CompletenessScope.ADDRESSABILITY.value: "authority_addressability",
                CompletenessScope.CONSTRUCTION.value: "authority_construction_coverage",
                CompletenessScope.ATTACHMENT.value: "authority_attachment_coverage",
            }[str(row["scope"])]
            kernel = self.world.latest_completeness(derived) or {}
            completeness_refs.append(
                {
                    "scope": row["scope"],
                    "universe": row["universe"],
                    "status": row["status"],
                    "basis": row["basis"],
                    "known_gaps": json.loads(row["known_gaps"]),
                    "purpose": row["purpose"],
                    "kernel_receipt_id": kernel.get("receipt_id", ""),
                    "kernel_target": derived,
                    "kernel_status": kernel.get("status", ""),
                    "kernel_universe": kernel.get("universe_relation", ""),
                    "kernel_basis": kernel.get("basis", ""),
                }
            )
        examples = []
        for row in claims[:5]:
            examples.append(
                {
                    "assertion_id": row["assertion_id"],
                    "relation_name": row["relation_name"],
                    "claim_kind": row["claim_kind"],
                    "relation_support": row["relation_support"],
                }
            )
        examined = self.world.relation_rows("authority_examined")
        return AuthorityConstructionReceipt(
            receipt_version=RECEIPT_VERSION,
            construction_id=self.construction_id,
            contract=MECHANISM_KEY,
            purpose=self.purpose,
            profile=self.profile,
            constructor={
                "id": self.constructor_id,
                "version": self.constructor_version,
            },
            authorized_source_universe={
                "id": self.universe.universe_id,
                "handles": [item.handle for item in self.universe.sources],
            },
            source_revisions={
                row["source_handle"]: row["content_revision"]
                for row in self.world.relation_rows("authority_source")
            },
            source_standing_summary={key.value: standing[key.value] for key in SourceStanding},
            program_snapshot_id=self._snapshot_id,
            program_universe=self.program_universe,
            source_regions_examined={
                "count": len(examined),
                "locators": [
                    {
                        "source_handle": row["source_handle"],
                        "native_location": row["native_location"],
                        "block_kind": row["block_kind"],
                    }
                    for row in examined
                ],
            },
            exploration_provenance=(),
            source_native_relationships_used=tuple(self.native_relationships),
            semantic_referents_created=tuple(self.created_semantic),
            semantic_referents_reused=tuple(dict.fromkeys(self.reused_semantic)),
            claims_persisted={key.value: by_kind[key.value] for key in ClaimKind},
            direct_source_program_links=int(by_kind[ClaimKind.SOURCE_PROGRAM.value]),
            semantic_program_links=int(by_kind[ClaimKind.SEMANTIC_PROGRAM.value]),
            source_semantic_links=int(by_kind[ClaimKind.SOURCE_SEMANTIC.value]),
            relation_support_summary={key.value: support[key.value] for key in RelationSupport},
            resolution_summary={key.value: resolutions[key.value] for key in ReferentResolution},
            unresolved_records=tuple(unresolved),
            known_unbound_material=tuple(
                f"{row['source_handle']} {row['native_location']}"
                for row in unresolved
                if row["kind"] in {UnresolvedKind.UNBOUND_REGION.value, UnresolvedKind.ENDPOINT_UNRESOLVED.value}
            ),
            known_losses=tuple(dict.fromkeys(self.known_losses)),
            reusable_resolvers=tuple(dict.fromkeys(self.resolvers)),
            representative_examples=tuple(examples),
            completeness_references=tuple(completeness_refs),
            adequacy_probe_results=tuple(
                {"probe": row["probe"], "outcome": row["outcome"], "detail": row["detail"]}
                for row in self.world.relation_rows("authority_adequacy")
            ),
            acceptance=dict(self.acceptance) if self.acceptance is not None else None,
            construction_basis=self.basis.as_dict(),
            construction_contract=authority_construction_contract(),
        )

    def _assert(
        self,
        relation: str,
        values: Mapping[str, Any],
        *,
        observations: Sequence[SourceObservation],
        extra: Mapping[str, Any],
        method: str = "",
    ):
        return self.world.assert_tuple(
            relation,
            values,
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=tuple(observations),
                construction_method=method or self._method,
                extra=dict(extra),
            ),
        )

    def _envelope(
        self,
        *,
        claim_kind: ClaimKind,
        support: RelationSupport,
        resolutions: Mapping[str, ReferentResolution],
        observations: Sequence[SourceObservation],
        governing: bool,
        resolvers: Sequence[str] = (),
    ) -> dict[str, Any]:
        locators = []
        for observation in observations:
            locators.append(
                {
                    **observation.as_pointer(),
                    "locator": _locator_from_observation(observation),
                }
            )
        return {
            "authority_construction": MECHANISM_KEY,
            "claim_kind": claim_kind.value,
            "relation_support": support.value,
            "endpoint_resolution": {role: value.value for role, value in resolutions.items()},
            "authorized_source_ids": sorted({item.native_handle for item in observations}),
            **({"program_snapshot_id": self._snapshot_id} if claim_kind in {
                ClaimKind.SOURCE_PROGRAM, ClaimKind.SEMANTIC_PROGRAM,
            } else {}),
            "constructor_id": self.constructor_id,
            "constructor_version": self.constructor_version,
            "constructor_profile": self.profile,
            "reusable_resolver_ids": list(resolvers),
            "governing": governing,
            "observation_locators": locators,
            "support_paths": [SupportPath(tuple(observations)).as_dict()],
        }

    def _governing_flag(self, support: RelationSupport, governing: bool | None) -> bool:
        if governing is not None:
            return bool(governing)
        return support is not RelationSupport.HYPOTHESIZED

    def _require_support_standing(self, observations: Sequence[SourceObservation], *, governing: bool) -> None:
        standing = {
            row["source_handle"]: (row["standing"], row["content_revision"])
            for row in self.world.relation_rows("authority_source")
        }
        for observation in observations:
            if observation.native_handle not in standing:
                raise AuthorityConstructionError(
                    f"observation handle is outside the declared source universe: {observation.native_handle}"
                )
            declared_standing, revision = standing[observation.native_handle]
            if observation.source_revision != revision:
                raise AuthorityConstructionError("observation revision does not match declared source revision")
            source = self.markdown[observation.native_handle]
            if observation.source_revision != source.revision:
                raise AuthorityConstructionError("observation is not reconstructible from current source bytes")
            source.reconstruct(observation)
            start, end = parse_byte_location(observation.native_location)
            if end > len(source.data):
                raise AuthorityConstructionError("observation byte range is not reconstructible")
            if governing and declared_standing != SourceStanding.AUTHORITATIVE.value:
                raise AuthorityConstructionError(
                    f"{declared_standing} source {observation.native_handle!r} cannot ground a governing claim"
                )

    def _require_semantic_id(self, referent_id: str) -> None:
        if not str(referent_id).startswith("semantic:"):
            raise AuthorityConstructionError("semantic referents must use the semantic: prefix")
        if str(referent_id).startswith("program:"):
            raise AuthorityConstructionError("program identities cannot be reused as semantic referents")

    def _referent_exists(self, referent_id: str) -> bool:
        rows = self.world.query("SELECT 1 FROM _world_referents WHERE id=?", (referent_id,))
        return bool(rows)

    def _is_semantic_member(self, referent_id: str) -> bool:
        return any(row["entity"] == referent_id for row in self.world.relation_rows("semantic_entity"))

    def _is_program_entity(self, referent_id: str) -> bool:
        if self.program_backend is None:
            return False
        return self.program_backend.is_member(referent_id)


def optional_program_rows(world: ConstructionWorld, relation: str) -> list[dict[str, Any]]:
    """Absence of the optional program plane has no semantic disposition."""
    if not world.query("SELECT 1 FROM _world_relations WHERE name=?", (relation,)):
        return []
    return world.relation_rows(relation)


def authority_construction_contract() -> dict[str, Any]:
    """Local declaration of the existing executable authority admission policy.

    No shared runtime contract is required by the heterogeneous constructors.
    This declaration identifies the checks; validation below executes them.
    """
    return {
        "id": "authority-construction-boundary/v1",
        "input_scope": "declared revision-qualified Markdown and exact publication inputs; optional qualified program snapshot",
        "target_schema": "explicitly declared typed authority and domain relations",
        "admission_requirements": [
            "recorded basis and method", "retained source reconstruction",
            "support path closure", "source standing", "resolved endpoint integrity",
            "kernel contract admission", "provider-owned program reconstruction closure",
        ],
    }


def _declare_authority_relations(world: ConstructionWorld) -> None:
    def text(name: str) -> Role:
        return Role(name, RoleType.TEXT)

    def ref(name: str) -> Role:
        return Role(name, RoleType.REFERENT)

    schemas: dict[str, list[Role]] = {
        "authority_source": [text("source_handle"), text("driver"), text("content_revision"), text("standing"), text("provider")],
        "semantic_entity": [ref("entity")],
        "authority_claim": [
            text("assertion_id"), text("relation_name"), text("claim_kind"),
            text("relation_support"), Role("governing", RoleType.BOOLEAN),
        ],
        "authority_endpoint_resolution": [text("assertion_id"), text("role"), text("referent"), text("resolution")],
        "authority_attachment_warrant": [
            text("assertion_id"), text("program_snapshot_id"), ref("program_entity"),
            text("structural_context"), text("justifying_program_relations"),
            text("justifying_resolution_outcomes"), text("constructor_profile"),
            text("relation_support"), text("endpoint_resolution"),
        ],
        "authority_relevance_scope": [
            text("warrant_assertion_id"), text("attachment_assertion_id"), ref("program_entity"),
            text("clause_kind"), ref("identity_id"), text("relation_name"),
            text("endpoint_role"), text("relation_tuple"), text("manifestation_properties"),
            text("structural_capability"), text("origin"),
        ],
        "authority_unresolved": [
            text("record_id"), text("kind"), text("source_handle"), text("native_location"),
            text("detail"), text("candidates_json"),
        ],
        "authority_unresolved_candidate": [text("record_id"), ref("candidate")],
        "authority_examined": [text("source_handle"), text("native_location"), text("block_kind"), text("content_revision")],
        "authority_completeness": [
            text("scope"), text("universe"), text("status"), text("basis"),
            text("known_gaps"), text("purpose"),
        ],
        "authority_adequacy": [text("probe"), text("outcome"), text("detail")],
        "authority_grounds_semantic": [
            ref("semantic"), text("source_handle"), text("native_location"),
        ],
        "authority_attachment_scope": [ref("target"), text("purpose")],
    }
    for name, roles in schemas.items():
        world.declare_relation(name, roles, description="Authority-construction application relation.")


def _locator_from_observation(observation: SourceObservation) -> dict[str, Any]:
    if not observation.payload:
        return {}
    try:
        payload = json.loads(observation.payload)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}

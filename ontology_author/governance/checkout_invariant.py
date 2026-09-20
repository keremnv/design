"""Checkout-provider-boundary/v1 scoped invariant evaluation.

This is not a generic resolver.  It answers one durable semantic question
from the current program spine:

    Within the declared Checkout scope, does every provider-access member
    traverse the construction-established PaymentGateway boundary?

Construction may establish the question (semantic roles, scope root, boundary
identity).  Snapshot truth is derived here with no model, no repository
search, and no reuse of a prior snapshot's TRUE.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ontology_author.authority.evaluate import (
    relation_rows_with_ids,
    snapshot_id as world_snapshot_id,
)
from ontology_author.world.runtime.world import ConstructionWorld

from ontology_author.semantic_binding.schemas import copy_json, digest
from ontology_author.semantic_binding.membership import (
    MEMBERSHIP_STATUS_ESTABLISHED,
    MEMBERSHIP_STATUS_PRESERVED,
    lookup_class_membership_evidence,
    membership_gap,
)

INVARIANT_DEFINITION_SCHEMA = "scoped_invariant_definition/v0"
# Frozen record tag. New code says evaluation; the serialized value keeps the
# historical derivation spelling so existing artifacts still validate.
INVARIANT_EVALUATION_SCHEMA = "scoped_invariant_derivation/v0"
CHECKOUT_PROVIDER_BOUNDARY_KIND = "CHECKOUT_PROVIDER_BOUNDARY"
CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID = "checkout-provider-boundary/v1"
CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION = 2
CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE = (
    "program_provider_access:checkout-payment-scope"
)
OWNER_KINDS = frozenset({"callable", "method"})
CALL_CAPABILITY = "spine.calls/v1"
CALL_CAPABILITY_ID = "spine.calls"
COMPLETE_CAPABILITY_STATUSES = frozenset({"COMPLETE", "STATIC_COMPLETE"})
MEMBER_SATISFIES = "SATISFIES"
MEMBER_VIOLATES = "VIOLATES"
MEMBER_UNKNOWN = "UNKNOWN"
TRUTH_TRUE = "TRUE"
TRUTH_FALSE = "FALSE"
TRUTH_UNKNOWN = "UNKNOWN"
COMPLETENESS_COMPLETE = "COMPLETE"
COMPLETENESS_INCOMPLETE = "INCOMPLETE"
COMPLETENESS_UNKNOWN = "UNKNOWN"
MEMBERSHIP_IS_PROVIDER = "IS_PROVIDER"
MEMBERSHIP_IS_NOT_PROVIDER = "IS_NOT_PROVIDER"
MEMBERSHIP_UNKNOWN = "UNKNOWN"
MEMBERSHIP_BASIS_DEFINITION = "INDEPENDENT_DEFINITION_IDENTITY"
MEMBERSHIP_BASIS_REALIZATION = "PERSISTED_SEMANTIC_PROGRAM_REALIZATION"
MEMBERSHIP_BASIS_MEMBERSHIP = "CLASS_MEMBERSHIP_EVIDENCE"
MEMBERSHIP_BASIS_ABSENT = "NO_INDEPENDENT_PROVIDER_EVIDENCE"
MEMBERSHIP_BASIS_GATEWAY = "GATEWAY_REACHABILITY_CIRCULAR"
HISTORICAL_UNSOUND_FINDING = "SEMANTIC_MEMBERSHIP_COMPLETENESS_UNSOUND"
PROGRAM_REALIZATION_RELATION = "semantic_program_realization"


def _nonempty(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _strings(values: Sequence[Any], field_name: str) -> tuple[str, ...]:
    result = tuple(sorted({str(item).strip() for item in values if str(item).strip()}))
    if not result:
        raise ValueError(f"{field_name} must contain at least one value")
    return result


def _optional_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_strings(values: Sequence[Any]) -> tuple[str, ...]:
    return tuple(sorted({str(item).strip() for item in values if str(item).strip()}))


def _ordered_strings(values: Sequence[Any]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return tuple(result)


@dataclass(frozen=True)
class ScopedInvariantDefinition:
    """Durable semantic configuration for one scoped invariant.

    This record is the question that must remain answerable.  It is not a
    snapshot truth result and carries no ``overall_truth``.
    """

    definition_id: str
    authority_refs: tuple[str, ...]
    access_semantic: str
    boundary_semantic: str
    scope_root: str
    boundary_program: str
    scope_root_descriptor: str = ""
    boundary_program_descriptor: str = ""
    snapshot_id: str = ""
    construction_provenance: Mapping[str, Any] | None = None
    provider_semantic: str = ""
    provider_programs: tuple[str, ...] = ()
    provider_descriptors: tuple[str, ...] = ()
    definition_kind: str = CHECKOUT_PROVIDER_BOUNDARY_KIND
    version: int = CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION
    evaluator_id: str = CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID
    contract: str = INVARIANT_DEFINITION_SCHEMA

    def __post_init__(self) -> None:
        if self.contract != INVARIANT_DEFINITION_SCHEMA:
            raise ValueError(
                f"unsupported ScopedInvariantDefinition schema: {self.contract}"
            )
        if self.definition_kind != CHECKOUT_PROVIDER_BOUNDARY_KIND:
            raise ValueError(
                "v0 ScopedInvariantDefinition kind must be "
                f"{CHECKOUT_PROVIDER_BOUNDARY_KIND}"
            )
        if int(self.version) != CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION:
            raise ValueError(
                "v0 ScopedInvariantDefinition version must be "
                f"{CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION}"
            )
        if self.evaluator_id != CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID:
            raise ValueError(
                "v0 ScopedInvariantDefinition evaluator_id must be "
                f"{CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID}"
            )
        object.__setattr__(
            self, "definition_id", _nonempty(self.definition_id, "definition_id")
        )
        object.__setattr__(
            self, "authority_refs", _strings(self.authority_refs, "authority_refs")
        )
        object.__setattr__(
            self, "access_semantic", _nonempty(self.access_semantic, "access_semantic")
        )
        object.__setattr__(
            self,
            "boundary_semantic",
            _nonempty(self.boundary_semantic, "boundary_semantic"),
        )
        object.__setattr__(self, "scope_root", _nonempty(self.scope_root, "scope_root"))
        object.__setattr__(
            self,
            "boundary_program",
            _nonempty(self.boundary_program, "boundary_program"),
        )
        object.__setattr__(
            self,
            "scope_root_descriptor",
            _optional_text(self.scope_root_descriptor),
        )
        object.__setattr__(
            self,
            "boundary_program_descriptor",
            _optional_text(self.boundary_program_descriptor),
        )
        object.__setattr__(self, "snapshot_id", _optional_text(self.snapshot_id))
        object.__setattr__(
            self,
            "construction_provenance",
            copy_json(self.construction_provenance or {}),
        )
        object.__setattr__(
            self, "provider_semantic", _optional_text(self.provider_semantic)
        )
        object.__setattr__(
            self,
            "provider_programs",
            _ordered_strings(self.provider_programs),
        )
        object.__setattr__(
            self,
            "provider_descriptors",
            _ordered_strings(self.provider_descriptors),
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ScopedInvariantDefinition:
        return cls(
            definition_id=str(
                payload.get("definition_id") or payload.get("id") or ""
            ),
            authority_refs=tuple(payload.get("authority_refs") or ()),
            access_semantic=str(payload.get("access_semantic") or ""),
            boundary_semantic=str(payload.get("boundary_semantic") or ""),
            scope_root=str(payload.get("scope_root") or ""),
            boundary_program=str(payload.get("boundary_program") or ""),
            scope_root_descriptor=str(payload.get("scope_root_descriptor") or ""),
            boundary_program_descriptor=str(
                payload.get("boundary_program_descriptor") or ""
            ),
            snapshot_id=str(
                payload.get("snapshot_id") or payload.get("program_snapshot") or ""
            ),
            construction_provenance=dict(payload.get("construction_provenance") or {}),
            provider_semantic=str(payload.get("provider_semantic") or ""),
            provider_programs=tuple(payload.get("provider_programs") or ()),
            provider_descriptors=tuple(payload.get("provider_descriptors") or ()),
            definition_kind=str(
                payload.get("definition_kind") or CHECKOUT_PROVIDER_BOUNDARY_KIND
            ),
            version=int(payload.get("version") or CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION),
            evaluator_id=str(
                payload.get("evaluator_id") or CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID
            ),
            contract=str(payload.get("contract") or INVARIANT_DEFINITION_SCHEMA),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "definition_id": self.definition_id,
            "definition_kind": self.definition_kind,
            "version": self.version,
            "authority_refs": list(self.authority_refs),
            "access_semantic": self.access_semantic,
            "boundary_semantic": self.boundary_semantic,
            "scope_root": self.scope_root,
            "scope_root_descriptor": self.scope_root_descriptor,
            "boundary_program": self.boundary_program,
            "boundary_program_descriptor": self.boundary_program_descriptor,
            "snapshot_id": self.snapshot_id,
            "construction_provenance": copy_json(self.construction_provenance),
            "provider_semantic": self.provider_semantic,
            "provider_programs": list(self.provider_programs),
            "provider_descriptors": list(self.provider_descriptors),
            "evaluator_id": self.evaluator_id,
        }


@dataclass(frozen=True)
class ScopedInvariantEvaluation:
    """Snapshot-specific deterministic answer for one invariant definition."""

    definition_id: str
    evaluator_id: str
    evaluator_version: int
    snapshot_id: str
    scope_root: str
    boundary_program: str
    universe: Mapping[str, Any]
    member_results: tuple[Mapping[str, Any], ...]
    overall_truth: str
    evaluation_receipt: Mapping[str, Any]
    derivation_id: str = ""
    contract: str = INVARIANT_EVALUATION_SCHEMA

    def __post_init__(self) -> None:
        if self.contract != INVARIANT_EVALUATION_SCHEMA:
            raise ValueError(
                f"unsupported ScopedInvariantEvaluation schema: {self.contract}"
            )
        if self.overall_truth not in {TRUTH_TRUE, TRUTH_FALSE, TRUTH_UNKNOWN}:
            raise ValueError(f"unknown overall_truth: {self.overall_truth}")
        object.__setattr__(self, "universe", copy_json(self.universe))
        object.__setattr__(
            self,
            "member_results",
            tuple(copy_json(item) for item in self.member_results),
        )
        object.__setattr__(
            self, "evaluation_receipt", copy_json(self.evaluation_receipt)
        )
        if not self.derivation_id:
            object.__setattr__(
                self,
                "derivation_id",
                digest(self._identity_payload(), "scoped-invariant-derivation"),
            )

    def _identity_payload(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "evaluator_id": self.evaluator_id,
            "evaluator_version": self.evaluator_version,
            "snapshot_id": self.snapshot_id,
            "scope_root": self.scope_root,
            "boundary_program": self.boundary_program,
            "universe": copy_json(self.universe),
            "member_results": [copy_json(item) for item in self.member_results],
            "overall_truth": self.overall_truth,
            "evaluation_receipt": copy_json(self.evaluation_receipt),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ScopedInvariantEvaluation:
        return cls(
            definition_id=str(payload.get("definition_id") or ""),
            evaluator_id=str(payload.get("evaluator_id") or ""),
            evaluator_version=int(payload.get("evaluator_version") or 0),
            snapshot_id=str(payload.get("snapshot_id") or ""),
            scope_root=str(payload.get("scope_root") or ""),
            boundary_program=str(payload.get("boundary_program") or ""),
            universe=dict(payload.get("universe") or {}),
            member_results=tuple(payload.get("member_results") or ()),
            overall_truth=str(payload.get("overall_truth") or ""),
            evaluation_receipt=dict(payload.get("evaluation_receipt") or {}),
            derivation_id=str(payload.get("derivation_id") or ""),
            contract=str(payload.get("contract") or INVARIANT_EVALUATION_SCHEMA),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "derivation_id": self.derivation_id,
            "definition_id": self.definition_id,
            "evaluator_id": self.evaluator_id,
            "evaluator_version": self.evaluator_version,
            "snapshot_id": self.snapshot_id,
            "scope_root": self.scope_root,
            "boundary_program": self.boundary_program,
            "universe": copy_json(self.universe),
            "member_results": [copy_json(item) for item in self.member_results],
            "overall_truth": self.overall_truth,
            "evaluation_receipt": copy_json(self.evaluation_receipt),
        }


def aggregate_checkout_provider_boundary_truth(
    *,
    completeness: str,
    member_results: Sequence[str],
) -> str:
    """Three-valued aggregation for checkout-provider-boundary/v1.

    Truth table:

    * any member ``VIOLATES`` → ``FALSE`` (one counterexample falsifies the
      universal, even when coverage is incomplete);
    * else if completeness is ``COMPLETE`` and every member is ``SATISFIES``
      (vacuously, when there are no members) → ``TRUE``;
    * otherwise → ``UNKNOWN``.

    An ``UNKNOWN`` member therefore yields overall ``UNKNOWN`` unless a known
    violation already established ``FALSE``.
    """

    results = [str(item) for item in member_results]
    if any(item == MEMBER_VIOLATES for item in results):
        return TRUTH_FALSE
    if completeness == COMPLETENESS_COMPLETE and all(
        item == MEMBER_SATISFIES for item in results
    ):
        return TRUTH_TRUE
    return TRUTH_UNKNOWN


def evaluate_checkout_provider_boundary(
    program_world: ConstructionWorld,
    invariant_definition: ScopedInvariantDefinition | Mapping[str, Any],
    *,
    membership_prior_world: ConstructionWorld | None = None,
    membership_correspondence: Sequence[Mapping[str, Any]] | None = None,
    membership_source_by_handle: Mapping[str, str] | None = None,
    membership_authority_by_handle: Mapping[str, str] | None = None,
) -> ScopedInvariantEvaluation:
    """Derive current-snapshot membership and truth for this one invariant."""

    definition = (
        invariant_definition
        if isinstance(invariant_definition, ScopedInvariantDefinition)
        else ScopedInvariantDefinition.from_dict(invariant_definition)
    )
    if definition.evaluator_id != CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID:
        raise ValueError(
            "evaluate_checkout_provider_boundary accepts only "
            f"{CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID}"
        )
    snapshot = world_snapshot_id(program_world)
    kinds = _entity_kinds(program_world)
    descriptors = _descriptors(program_world)
    parents = _structural_parents(program_world)
    invoke_rows = _invoke_rows(program_world)
    resolutions = _call_resolutions(program_world)
    capabilities = _capability_receipts(program_world)

    scope_root, scope_reason = _locate_program_entity(
        kinds,
        descriptors,
        entity_id=definition.scope_root,
        descriptor=definition.scope_root_descriptor,
    )
    boundary, boundary_reason = _locate_program_entity(
        kinds,
        descriptors,
        entity_id=definition.boundary_program,
        descriptor=definition.boundary_program_descriptor,
    )
    invoke_graph, invoke_evidence, owner_gaps = _invoke_graph(
        invoke_rows, parents, kinds, descriptors
    )
    call_sites_by_owner = _call_sites_by_owner(resolutions, parents, kinds)
    structural = COMPLETENESS_COMPLETE
    semantic = COMPLETENESS_COMPLETE
    completeness_gaps: list[str] = []
    if scope_root is None:
        structural = COMPLETENESS_UNKNOWN
        completeness_gaps.append(scope_reason or "scope_root is not in this snapshot")
    if boundary is None:
        structural = COMPLETENESS_UNKNOWN
        completeness_gaps.append(
            boundary_reason or "boundary_program is not in this snapshot"
        )
    if owner_gaps:
        structural = COMPLETENESS_UNKNOWN
        completeness_gaps.extend(owner_gaps)

    members: list[dict[str, Any]] = []
    scoped_callables: set[str] = set()
    scoped_edges: list[dict[str, str]] = []
    unresolved_in_scope: list[str] = []
    independent_providers: dict[str, dict[str, str]] = {}
    gateway_reachable: set[str] = set()
    candidate_leaves: set[str] = set()
    membership_rows: list[dict[str, str]] = []
    membership_evidence: list[dict[str, Any]] = []
    membership_gaps: list[dict[str, Any]] = []
    if scope_root is not None and boundary is not None and structural != COMPLETENESS_UNKNOWN:
        scoped_callables = _reachable(invoke_graph, scope_root)
        gateway_reachable = _reachable(invoke_graph, boundary) - {boundary}
        independent_providers = _independent_provider_membership(
            program_world, definition, kinds, descriptors
        )
        scoped_edges = _scoped_edges(invoke_graph, invoke_evidence, scoped_callables)
        unresolved_in_scope = _unresolved_subjects(
            call_sites_by_owner, resolutions, scoped_callables
        )
        candidate_leaves = _provider_membership_candidates(
            scoped_callables, invoke_graph, scope_root, boundary
        )
        membership_evidence, membership_gaps = _apply_class_membership_evidence(
            program_world,
            definition,
            candidate_leaves,
            independent_providers,
            membership_prior_world=membership_prior_world,
            membership_correspondence=membership_correspondence,
            membership_source_by_handle=membership_source_by_handle,
            membership_authority_by_handle=membership_authority_by_handle,
        )
        membership_rows = _classify_provider_membership(
            candidate_leaves,
            independent_providers,
            descriptors,
            gateway_reachable,
        )
        members = _evaluate_members(
            scope_root=scope_root,
            boundary=boundary,
            independent_providers=independent_providers,
            candidate_leaves=candidate_leaves,
            invoke_graph=invoke_graph,
            invoke_evidence=invoke_evidence,
            call_sites_by_owner=call_sites_by_owner,
            resolutions=resolutions,
            descriptors=descriptors,
        )
        structural, extra_gaps = _structural_completeness(
            capabilities=capabilities,
            unresolved_subjects=unresolved_in_scope,
            owner_gaps=owner_gaps,
            call_sites_by_owner=call_sites_by_owner,
            resolutions=resolutions,
            invoke_evidence=invoke_evidence,
            scoped_callables=scoped_callables,
        )
        completeness_gaps.extend(extra_gaps)
        semantic = _semantic_membership_completeness(membership_rows)

    completeness = _combine_completeness(structural, semantic)
    member_results = tuple(members)
    overall = aggregate_checkout_provider_boundary_truth(
        completeness=completeness,
        member_results=[str(item.get("result") or "") for item in member_results],
    )
    evidence_refs = [item["evidence_id"] for item in scoped_edges]
    universe = {
        "id": CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE,
        "snapshot_id": snapshot,
        "completeness": completeness,
        "structural_enumeration": structural,
        "semantic_membership": semantic,
        "members": [item["member_id"] for item in member_results],
        "member_evidence_refs": evidence_refs,
        "evidence_refs": evidence_refs,
        "known_gaps": list(completeness_gaps),
        "basis": (
            "checkout-provider-boundary/v1 enumerates Checkout-originating "
            "access structure, then classifies PaymentProvider membership "
            "from independent construction identities or persisted "
            "realizations, not from PaymentGateway reachability"
        ),
    }
    receipt = {
        "model_invoked": False,
        "repository_searched": False,
        "name_classified": False,
        "evaluator_id": CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
        "evaluator_version": CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION,
        "definition_id": definition.definition_id,
        "snapshot_id": snapshot,
        "declared_scope_root": definition.scope_root,
        "effective_scope_root": scope_root or "",
        "declared_boundary_program": definition.boundary_program,
        "effective_boundary_program": boundary or "",
        "provider_ids": sorted(independent_providers),
        "independent_provider_ids": sorted(independent_providers),
        "gateway_reachable_ids": sorted(gateway_reachable),
        "membership_classifications": membership_rows,
        "class_membership_evidence": membership_evidence,
        "membership_gaps": membership_gaps,
        "provider_membership_basis": sorted(
            {
                item.get("basis", "")
                for item in independent_providers.values()
                if item.get("basis")
            }
        ),
        "circular_gateway_membership": False,
        "historical_finding": HISTORICAL_UNSOUND_FINDING,
        "scoped_callable_count": len(scoped_callables),
        "scoped_invoke_edge_count": len(scoped_edges),
        "member_count": len(member_results),
        "unresolved_in_scope": list(unresolved_in_scope),
        "capability_receipts": capabilities,
        "completeness_gaps": list(completeness_gaps),
        "structural_enumeration": structural,
        "semantic_membership": semantic,
        "inputs": {
            "relations": ["program_invokes", "structural_context", "program_entity_kind"],
            "identity": ["program_identity_descriptor"],
            "resolution": ["program_resolution"],
            "capability": ["program_capability"],
            "optional_semantic": [
                PROGRAM_REALIZATION_RELATION,
                "semantic_program_membership",
            ],
        },
    }
    return ScopedInvariantEvaluation(
        definition_id=definition.definition_id,
        evaluator_id=CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
        evaluator_version=CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION,
        snapshot_id=snapshot,
        scope_root=scope_root or definition.scope_root,
        boundary_program=boundary or definition.boundary_program,
        universe=universe,
        member_results=member_results,
        overall_truth=overall,
        evaluation_receipt=receipt,
    )


def _entity_kinds(world: ConstructionWorld) -> dict[str, str]:
    try:
        rows = world.relation_rows("program_entity_kind")
    except Exception:
        return {}
    return {str(row["entity"]): str(row["kind"]) for row in rows}


def _descriptors(world: ConstructionWorld) -> dict[str, str]:
    try:
        rows = world.relation_rows("program_identity_descriptor")
    except Exception:
        return {}
    return {str(row["entity"]): str(row["descriptor"]) for row in rows}


def _structural_parents(world: ConstructionWorld) -> dict[str, str]:
    try:
        rows = world.relation_rows("structural_context")
    except Exception:
        return {}
    return {str(row["child"]): str(row["parent"]) for row in rows}


def _invoke_rows(world: ConstructionWorld) -> list[dict[str, Any]]:
    try:
        return relation_rows_with_ids(world, "program_invokes")
    except Exception:
        return []


def _call_resolutions(world: ConstructionWorld) -> dict[str, dict[str, Any]]:
    try:
        rows = relation_rows_with_ids(world, "program_resolution")
    except Exception:
        return {}
    return {
        str(row["subject"]): row
        for row in rows
        if str(row.get("capability") or "") == CALL_CAPABILITY
    }


def _capability_receipts(world: ConstructionWorld) -> list[dict[str, Any]]:
    try:
        rows = world.relation_rows("program_capability")
    except Exception:
        return []
    return [
        {
            "capability": str(row.get("capability") or ""),
            "version": str(row.get("version") or ""),
            "status": str(row.get("status") or ""),
            "universe": copy_json(row.get("universe")),
            "basis": str(row.get("basis") or ""),
            "known_gaps": copy_json(row.get("known_gaps") or []),
        }
        for row in rows
    ]


def _locate_program_entity(
    kinds: Mapping[str, str],
    descriptors: Mapping[str, str],
    *,
    entity_id: str,
    descriptor: str,
) -> tuple[str | None, str]:
    if entity_id in kinds:
        return entity_id, ""
    if not descriptor:
        return None, f"program entity {entity_id} is absent from this snapshot"
    matches = sorted(
        entity
        for entity, value in descriptors.items()
        if value == descriptor and entity in kinds
    )
    if len(matches) == 1:
        return matches[0], ""
    if not matches:
        return None, f"identity descriptor {descriptor} is absent from this snapshot"
    return None, f"identity descriptor {descriptor} is ambiguous in this snapshot"


def _independent_provider_membership(
    world: ConstructionWorld,
    definition: ScopedInvariantDefinition,
    kinds: Mapping[str, str],
    descriptors: Mapping[str, str],
) -> dict[str, dict[str, str]]:
    """Classify PaymentProvider independently of PaymentGateway reachability."""

    found: dict[str, dict[str, str]] = {}
    programs = list(definition.provider_programs)
    declared_descriptors = list(definition.provider_descriptors)
    if programs:
        while len(declared_descriptors) < len(programs):
            declared_descriptors.append("")
        pairs = list(zip(programs, declared_descriptors))
    else:
        pairs = [("", descriptor) for descriptor in declared_descriptors]
    for entity_id, descriptor in pairs:
        located, _reason = _locate_program_entity(
            kinds, descriptors, entity_id=entity_id, descriptor=descriptor
        )
        if located:
            found[located] = {
                "status": MEMBERSHIP_IS_PROVIDER,
                "basis": MEMBERSHIP_BASIS_DEFINITION,
            }
    if definition.provider_semantic:
        try:
            rows = world.relation_rows(PROGRAM_REALIZATION_RELATION)
        except Exception:
            rows = []
        for row in rows:
            if str(row.get("semantic_subject") or "") != definition.provider_semantic:
                continue
            entity = str(row.get("program_manifestation") or "")
            if entity in kinds:
                found[entity] = {
                    "status": MEMBERSHIP_IS_PROVIDER,
                    "basis": MEMBERSHIP_BASIS_REALIZATION,
                }
        try:
            membership_rows = world.relation_rows("semantic_program_membership")
        except Exception:
            membership_rows = []
        for row in membership_rows:
            if str(row.get("semantic_class") or "") != definition.provider_semantic:
                continue
            entity = str(row.get("program_manifestation") or "")
            if entity in kinds:
                found[entity] = {
                    "status": MEMBERSHIP_IS_PROVIDER,
                    "basis": MEMBERSHIP_BASIS_MEMBERSHIP,
                    "membership_status": MEMBERSHIP_STATUS_ESTABLISHED,
                }
    return found


def _apply_class_membership_evidence(
    world: ConstructionWorld,
    definition: ScopedInvariantDefinition,
    candidate_leaves: set[str],
    independent_providers: dict[str, dict[str, str]],
    *,
    membership_prior_world: ConstructionWorld | None,
    membership_correspondence: Sequence[Mapping[str, Any]] | None,
    membership_source_by_handle: Mapping[str, str] | None,
    membership_authority_by_handle: Mapping[str, str] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Consume ClassMembershipEvidence; do not reconstruct semantic meaning."""

    semantic_class = definition.provider_semantic
    if not semantic_class:
        return [], []
    evidence_rows: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    snapshot = world_snapshot_id(world)
    for entity in sorted(candidate_leaves):
        if entity in independent_providers:
            continue
        result = lookup_class_membership_evidence(
            world,
            semantic_class,
            entity,
            prior_world=membership_prior_world,
            correspondence=membership_correspondence,
            source_by_handle=membership_source_by_handle,
            authority_by_handle=membership_authority_by_handle,
        )
        evidence_rows.append(result.to_dict())
        if result.status in {
            MEMBERSHIP_STATUS_ESTABLISHED,
            MEMBERSHIP_STATUS_PRESERVED,
        }:
            independent_providers[entity] = {
                "status": MEMBERSHIP_IS_PROVIDER,
                "basis": MEMBERSHIP_BASIS_MEMBERSHIP,
                "membership_status": result.status,
            }
        else:
            gaps.append(
                membership_gap(
                    semantic_class=semantic_class,
                    program_subject=entity,
                    snapshot=snapshot,
                    requested_by=definition.definition_id,
                ).to_dict()
            )
    return evidence_rows, gaps


def _provider_membership_candidates(
    scoped_callables: set[str],
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
    scope_root: str,
    boundary: str,
) -> set[str]:
    leaves = {
        node
        for node in scoped_callables
        if node not in {scope_root, boundary} and not graph.get(node)
    }
    return leaves


def _classify_provider_membership(
    candidates: set[str],
    independent_providers: Mapping[str, Mapping[str, str]],
    descriptors: Mapping[str, str],
    gateway_reachable: set[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entity in sorted(candidates):
        independent = independent_providers.get(entity)
        if independent:
            status = str(independent.get("status") or MEMBERSHIP_IS_PROVIDER)
            basis = str(independent.get("basis") or MEMBERSHIP_BASIS_DEFINITION)
        else:
            status = MEMBERSHIP_UNKNOWN
            basis = MEMBERSHIP_BASIS_ABSENT
        rows.append(
            {
                "entity": entity,
                "descriptor": descriptors.get(entity, ""),
                "status": status,
                "basis": basis,
                "gateway_reachable": entity in gateway_reachable,
            }
        )
    return rows


def _semantic_membership_completeness(
    membership_rows: Sequence[Mapping[str, str]],
) -> str:
    if not membership_rows:
        return COMPLETENESS_UNKNOWN
    statuses = {str(item.get("status") or "") for item in membership_rows}
    if MEMBERSHIP_UNKNOWN in statuses:
        return COMPLETENESS_UNKNOWN
    if statuses <= {MEMBERSHIP_IS_PROVIDER}:
        return COMPLETENESS_COMPLETE
    return COMPLETENESS_INCOMPLETE


def _combine_completeness(structural: str, semantic: str) -> str:
    if structural == COMPLETENESS_COMPLETE and semantic == COMPLETENESS_COMPLETE:
        return COMPLETENESS_COMPLETE
    if COMPLETENESS_UNKNOWN in {structural, semantic} and structural != COMPLETENESS_INCOMPLETE:
        if semantic == COMPLETENESS_UNKNOWN and structural == COMPLETENESS_COMPLETE:
            return COMPLETENESS_INCOMPLETE
        return COMPLETENESS_UNKNOWN
    return COMPLETENESS_INCOMPLETE


def _containing_owner(
    entity: str,
    parents: Mapping[str, str],
    kinds: Mapping[str, str],
) -> str | None:
    current = entity
    seen = {entity}
    while current:
        if kinds.get(current) in OWNER_KINDS:
            return current
        parent = parents.get(current)
        if not parent or parent in seen:
            return None
        seen.add(parent)
        current = parent
    return None


def _invoke_evidence_id(call_site: str, target: str, assertion_id: str) -> str:
    if assertion_id:
        return f"relation:{assertion_id}"
    return "relation:" + digest(
        {
            "relation": "program_invokes",
            "call_site": call_site,
            "target": target,
        }
    )


def _invoke_graph(
    rows: Sequence[Mapping[str, Any]],
    parents: Mapping[str, str],
    kinds: Mapping[str, str],
    descriptors: Mapping[str, str],
) -> tuple[
    dict[str, list[tuple[str, str, str]]],
    dict[tuple[str, str], dict[str, str]],
    list[str],
]:
    graph: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    evidence: dict[tuple[str, str], dict[str, str]] = {}
    gaps: list[str] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for row in rows:
        call_site = str(row.get("call_site") or "")
        target = str(row.get("target") or "")
        if not call_site or not target:
            continue
        owner = _containing_owner(call_site, parents, kinds)
        if owner is None:
            gaps.append(f"call site {call_site} has no containing callable")
            continue
        evidence_id = _invoke_evidence_id(
            call_site, target, str(row.get("_assertion_id") or "")
        )
        edge = (owner, target, call_site)
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        graph[owner].append((target, call_site, evidence_id))
        evidence[(call_site, target)] = {
            "relation": "program_invokes",
            "call_site": call_site,
            "target": target,
            "owner": owner,
            "evidence_id": evidence_id,
            "call_site_descriptor": descriptors.get(call_site, ""),
            "target_descriptor": descriptors.get(target, ""),
            "owner_descriptor": descriptors.get(owner, ""),
        }
    for owner in graph:
        graph[owner].sort(key=lambda item: (item[1], item[0], item[2]))
    return dict(graph), evidence, gaps


def _call_sites_by_owner(
    resolutions: Mapping[str, Mapping[str, Any]],
    parents: Mapping[str, str],
    kinds: Mapping[str, str],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for subject in resolutions:
        owner = _containing_owner(subject, parents, kinds)
        if owner is None:
            continue
        grouped[owner].append(subject)
    for owner in grouped:
        grouped[owner].sort()
    return dict(grouped)


def _reachable(graph: Mapping[str, Sequence[tuple[str, str, str]]], start: str) -> set[str]:
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for target, _call_site, _evidence_id in graph.get(node, ()):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def _scoped_edges(
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
    evidence: Mapping[tuple[str, str], Mapping[str, str]],
    scoped_callables: set[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for owner in sorted(scoped_callables):
        for target, call_site, evidence_id in graph.get(owner, ()):
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            record = dict(evidence.get((call_site, target)) or {})
            record.setdefault("evidence_id", evidence_id)
            rows.append(record)
    rows.sort(key=lambda item: item.get("evidence_id") or "")
    return rows


def _unresolved_subjects(
    call_sites_by_owner: Mapping[str, Sequence[str]],
    resolutions: Mapping[str, Mapping[str, Any]],
    scoped_callables: set[str],
) -> list[str]:
    unresolved: list[str] = []
    for owner in sorted(scoped_callables):
        for subject in call_sites_by_owner.get(owner, ()):
            status = str(resolutions.get(subject, {}).get("status") or "")
            if status in {"UNRESOLVED", "MULTIPLE_CANDIDATES", ""}:
                unresolved.append(subject)
    return unresolved


def _subgraph_unresolved(
    start: str,
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
    call_sites_by_owner: Mapping[str, Sequence[str]],
    resolutions: Mapping[str, Mapping[str, Any]],
) -> bool:
    return bool(
        _unresolved_subjects(call_sites_by_owner, resolutions, _reachable(graph, start))
    )


def _reaches_without_boundary(
    start: str,
    *,
    boundary: str,
    goals: set[str],
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
) -> bool:
    if start == boundary:
        return False
    if start in goals:
        return True
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for target, _call_site, _evidence_id in graph.get(node, ()):
            if target == boundary or target in seen:
                continue
            if target in goals:
                return True
            seen.add(target)
            queue.append(target)
    return False


def _reaches_via_boundary(
    start: str,
    *,
    boundary: str,
    goals: set[str],
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
) -> bool:
    if start == boundary:
        return bool((_reachable(graph, boundary) - {boundary}) & goals) or boundary in goals
    if not _path_exists(graph, start, boundary):
        return False
    return bool((_reachable(graph, boundary) - {boundary}) & goals) or boundary in goals


def _path_exists(
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
    start: str,
    goal: str,
) -> bool:
    if start == goal:
        return True
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for target, _call_site, _evidence_id in graph.get(node, ()):
            if target == goal:
                return True
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return False


def _witness_path(
    start: str,
    *,
    boundary: str | None,
    goals: set[str],
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
    require_unmediated: bool,
) -> list[tuple[str, str, str, str]]:
    """Return one witnessing owner-path as (owner, target, call_site, evidence_id)."""

    queue = deque([(start, [])])
    seen_states = {(start, False)}
    while queue:
        node, path = queue.popleft()
        seen_boundary = node == boundary or any(item[0] == boundary for item in path)
        if node in goals and path:
            if require_unmediated and not seen_boundary:
                return path
            if not require_unmediated and seen_boundary:
                return path
        if node in goals and not path:
            return []
        for target, call_site, evidence_id in graph.get(node, ()):
            next_seen = seen_boundary or target == boundary
            state = (target, next_seen)
            if state in seen_states:
                continue
            if require_unmediated and target == boundary:
                continue
            seen_states.add(state)
            queue.append((target, [*path, (node, target, call_site, evidence_id)]))
    return []


def _first_hops(
    scope_root: str,
    graph: Mapping[str, Sequence[tuple[str, str, str]]],
    call_sites_by_owner: Mapping[str, Sequence[str]],
    resolutions: Mapping[str, Mapping[str, Any]],
    invoke_evidence: Mapping[tuple[str, str], Mapping[str, str]],
) -> list[dict[str, Any]]:
    hops: list[dict[str, Any]] = []
    resolved_hops = [
        {
            "call_site": call_site,
            "target": target,
            "evidence_id": evidence_id,
            "resolution": "RESOLVED",
            **dict(invoke_evidence.get((call_site, target)) or {}),
        }
        for target, call_site, evidence_id in graph.get(scope_root, ())
    ]
    hops.extend(resolved_hops)
    known_sites = {item["call_site"] for item in hops}
    for subject in call_sites_by_owner.get(scope_root, ()):
        if subject in known_sites:
            continue
        status = str(resolutions.get(subject, {}).get("status") or "")
        if status in {"UNRESOLVED", "MULTIPLE_CANDIDATES", ""}:
            hops.append(
                {
                    "call_site": subject,
                    "target": "",
                    "evidence_id": "",
                    "resolution": status or "MISSING",
                }
            )
    hops.sort(key=lambda item: (item.get("call_site") or "", item.get("target") or ""))
    return hops


def _evaluate_members(
    *,
    scope_root: str,
    boundary: str,
    independent_providers: Mapping[str, Mapping[str, str]],
    candidate_leaves: set[str],
    invoke_graph: Mapping[str, Sequence[tuple[str, str, str]]],
    invoke_evidence: Mapping[tuple[str, str], Mapping[str, str]],
    call_sites_by_owner: Mapping[str, Sequence[str]],
    resolutions: Mapping[str, Mapping[str, Any]],
    descriptors: Mapping[str, str],
) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    providers = set(independent_providers)
    for hop in _first_hops(
        scope_root, invoke_graph, call_sites_by_owner, resolutions, invoke_evidence
    ):
        call_site = str(hop.get("call_site") or "")
        target = str(hop.get("target") or "")
        if hop.get("resolution") != "RESOLVED" or not target:
            members.append(
                _member_record(
                    scope_root=scope_root,
                    call_site=call_site,
                    target=target,
                    descriptors=descriptors,
                    result=MEMBER_UNKNOWN,
                    mediation="INDETERMINATE",
                    reason="Checkout first-hop call is not a resolved provider-access edge",
                    hop=hop,
                    path=[],
                    unresolved=True,
                    endpoint_membership=[],
                )
            )
            continue
        reachable = _reachable(invoke_graph, target)
        reached_candidates = reachable & candidate_leaves
        if target in candidate_leaves:
            reached_candidates.add(target)
        reached_providers = reached_candidates & providers
        reached_unknown = reached_candidates - providers
        unresolved = _subgraph_unresolved(
            target, invoke_graph, call_sites_by_owner, resolutions
        )
        unmediated = _reaches_without_boundary(
            target, boundary=boundary, goals=providers, graph=invoke_graph
        )
        mediated = _reaches_via_boundary(
            target, boundary=boundary, goals=providers, graph=invoke_graph
        )
        membership = [
            {
                "entity": entity,
                "descriptor": descriptors.get(entity, ""),
                "status": str(
                    independent_providers.get(entity, {}).get("status")
                    or MEMBERSHIP_UNKNOWN
                ),
                "basis": str(
                    independent_providers.get(entity, {}).get("basis")
                    or MEMBERSHIP_BASIS_ABSENT
                ),
            }
            for entity in sorted(reached_candidates)
        ]
        if unmediated:
            result = MEMBER_VIOLATES
            mediation = "UNMEDIATED"
            reason = (
                "Checkout-originating access reaches an independently classified "
                "PaymentProvider without traversing PaymentGateway"
            )
            path = _witness_path(
                target,
                boundary=boundary,
                goals=providers,
                graph=invoke_graph,
                require_unmediated=True,
            )
        elif reached_unknown:
            result = MEMBER_UNKNOWN
            mediation = "INDETERMINATE"
            reason = (
                "Checkout first hop reaches an endpoint whose PaymentProvider "
                "membership is not independently established"
            )
            path = []
        elif not reached_providers:
            continue
        elif mediated and not unresolved:
            result = MEMBER_SATISFIES
            mediation = "MEDIATED"
            reason = (
                "Checkout-originating access is mechanically shown to traverse "
                "PaymentGateway before an independently classified PaymentProvider"
            )
            path = _witness_path(
                target,
                boundary=boundary,
                goals=providers,
                graph=invoke_graph,
                require_unmediated=False,
            )
        else:
            result = MEMBER_UNKNOWN
            mediation = "INDETERMINATE"
            reason = (
                "available mechanical facts cannot determine whether every "
                "access from this first hop is PaymentGateway-mediated"
            )
            path = _witness_path(
                target,
                boundary=boundary,
                goals=providers,
                graph=invoke_graph,
                require_unmediated=False,
            )
        members.append(
            _member_record(
                scope_root=scope_root,
                call_site=call_site,
                target=target,
                descriptors=descriptors,
                result=result,
                mediation=mediation,
                reason=reason,
                hop=hop,
                path=path,
                unresolved=unresolved,
                endpoint_membership=membership,
            )
        )
    members.sort(key=lambda item: item["member_id"])
    return members


def _member_record(
    *,
    scope_root: str,
    call_site: str,
    target: str,
    descriptors: Mapping[str, str],
    result: str,
    mediation: str,
    reason: str,
    hop: Mapping[str, Any],
    path: Sequence[tuple[str, str, str, str]],
    unresolved: bool,
    endpoint_membership: Sequence[Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    hop_fact = {
        "relation": "program_invokes",
        "call_site": call_site,
        "target": target,
        "owner": scope_root,
    }
    path_facts = [
        {
            "relation": "program_invokes",
            "call_site": call_site_id,
            "target": path_target,
            "owner": owner,
            "evidence_id": evidence_id,
        }
        for owner, path_target, call_site_id, evidence_id in path
    ]
    evidence_refs = []
    hop_evidence = str(hop.get("evidence_id") or "")
    if hop_evidence:
        evidence_refs.append(hop_evidence)
    evidence_refs.extend(item["evidence_id"] for item in path_facts if item.get("evidence_id"))
    member_id = digest(
        {
            "evaluator_id": CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
            "scope_root_descriptor": descriptors.get(scope_root, ""),
            "call_site_descriptor": descriptors.get(call_site, call_site),
            "target_descriptor": descriptors.get(target, target),
        },
        "provider-access",
    )
    return {
        "member_id": member_id,
        "origin_call_site": call_site,
        "origin_target": target,
        "origin_call_site_descriptor": descriptors.get(call_site, ""),
        "origin_target_descriptor": descriptors.get(target, ""),
        "scope_root": scope_root,
        "result": result,
        "mediation": mediation,
        "reason": reason,
        "unresolved_in_member_subgraph": unresolved,
        "endpoint_membership": [copy_json(item) for item in endpoint_membership or ()],
        "first_hop": copy_json({**hop_fact, "evidence_id": hop_evidence}),
        "path_evidence": path_facts,
        "evidence_refs": evidence_refs,
    }


def _structural_completeness(
    *,
    capabilities: Sequence[Mapping[str, Any]],
    unresolved_subjects: Sequence[str],
    owner_gaps: Sequence[str],
    call_sites_by_owner: Mapping[str, Sequence[str]],
    resolutions: Mapping[str, Mapping[str, Any]],
    invoke_evidence: Mapping[tuple[str, str], Mapping[str, str]],
    scoped_callables: set[str],
) -> tuple[str, list[str]]:
    gaps = [str(item) for item in owner_gaps]
    call_capability = next(
        (
            item
            for item in capabilities
            if str(item.get("capability") or "") == CALL_CAPABILITY_ID
            and str(item.get("version") or "") == "v1"
        ),
        None,
    )
    if call_capability is None:
        return COMPLETENESS_UNKNOWN, ["spine.calls/v1 capability receipt is absent"]
    status = str(call_capability.get("status") or "")
    if status not in COMPLETE_CAPABILITY_STATUSES:
        gaps.append(f"spine.calls/v1 status is {status or 'missing'}")
        return COMPLETENESS_INCOMPLETE, gaps
    if unresolved_subjects:
        gaps.extend(
            f"scoped call site is not resolved: {subject}"
            for subject in unresolved_subjects
        )
        return COMPLETENESS_INCOMPLETE, gaps
    for owner in sorted(scoped_callables):
        for subject in call_sites_by_owner.get(owner, ()):
            outcome = resolutions.get(subject) or {}
            status = str(outcome.get("status") or "")
            if not status:
                gaps.append(f"scoped call site lacks spine.calls/v1 outcome: {subject}")
                continue
            if status == "RESOLVED":
                has_edge = any(
                    call_site == subject for call_site, _target in invoke_evidence
                )
                if not has_edge:
                    gaps.append(
                        f"resolved scoped call site lacks program_invokes: {subject}"
                    )
    if gaps:
        return COMPLETENESS_INCOMPLETE, gaps
    return COMPLETENESS_COMPLETE, []


def invariant_context_for_case(
    definition: ScopedInvariantDefinition | Mapping[str, Any],
    *,
    baseline: ScopedInvariantEvaluation | Mapping[str, Any],
    candidate: ScopedInvariantEvaluation | Mapping[str, Any],
) -> dict[str, Any]:
    """Project definition + snapshot derivations into GovernanceCase evidence."""

    definition_payload = (
        definition.to_dict()
        if isinstance(definition, ScopedInvariantDefinition)
        else copy_json(definition)
    )
    baseline_payload = (
        baseline.to_dict()
        if isinstance(baseline, ScopedInvariantEvaluation)
        else copy_json(baseline)
    )
    candidate_payload = (
        candidate.to_dict()
        if isinstance(candidate, ScopedInvariantEvaluation)
        else copy_json(candidate)
    )
    return {
        "inclusion_reason": "SELECTED_SCOPED_INVARIANT_DERIVATION",
        "authority_question": (
            "All payment-provider access from Checkout must go through "
            "PaymentGateway."
        ),
        "definition": definition_payload,
        "baseline_derivation": baseline_payload,
        "candidate_derivation": candidate_payload,
        "preferred_candidate_truth_artifact": "candidate_derivation",
        "supersedes_for_candidate_truth": [
            "semantic_payment_provider_access_invariant",
            "semantic_commitment_warrant",
        ],
        "class_membership_evidence": copy_json(
            candidate_payload.get("evaluation_receipt", {}).get(
                "class_membership_evidence"
            )
            or []
        ),
        "membership_gaps": copy_json(
            candidate_payload.get("evaluation_receipt", {}).get("membership_gaps") or []
        ),
    }

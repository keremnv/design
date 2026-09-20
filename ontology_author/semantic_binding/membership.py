"""Narrow CLASS_MEMBERSHIP persistence and deterministic reuse.

This is not a semantic-class resolver and not a SemanticClassDefinition.
A positive membership judgment may be constructed once, persisted, and later
reused only when the complete material interpretation basis is unchanged.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ontology_author.authority.evaluate import (
    snapshot_id as world_snapshot_id,
)
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.runtime.world import ConstructionWorld

from .schemas import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    CLASS_MEMBERSHIP_RELATION,
    CLASS_MEMBERSHIP_TUPLE_SHAPE,
    ConstructionObligation,
    EvidenceClass,
    SemanticCandidate,
    copy_json,
    digest,
)

INTERPRETATION_BASIS_SCHEMA = "class_membership_interpretation_basis/v0"
MEMBERSHIP_BASIS_RELATION = "semantic_class_membership_basis"
MEMBERSHIP_STATUS_ESTABLISHED = "ESTABLISHED_CURRENT"
MEMBERSHIP_STATUS_PRESERVED = "PRESERVED_IDENTICAL_BASIS"
MEMBERSHIP_STATUS_UNKNOWN = "UNKNOWN"
MEMBERSHIP_RESULT_MEMBER = "MEMBER"
MEMBERSHIP_RESULT_UNRESOLVED = "UNRESOLVED"
GAP_REASON_NO_EVIDENCE = "NO_CURRENT_OR_REUSABLE_MEMBERSHIP_EVIDENCE"
PAYMENT_PROVIDER_CLASS = "semantic:PaymentProvider"
FINDING_BASIS_INCOMPLETE = "INTERPRETATION_BASIS_INCOMPLETE"


def _content_digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rows(world: ConstructionWorld, relation: str) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in world.relation_rows(relation)]
    except Exception:
        return []


def _descriptors(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["entity"]): str(row["descriptor"])
        for row in _rows(world, "program_identity_descriptor")
        if str(row.get("entity") or "")
    }


def _kinds(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["entity"]): str(row["kind"])
        for row in _rows(world, "program_entity_kind")
        if str(row.get("entity") or "")
    }


def _parents(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["child"]): str(row["parent"])
        for row in _rows(world, "structural_context")
        if str(row.get("child") or "")
    }


def _descriptor_chain(
    entity: str, parents: Mapping[str, str], descriptors: Mapping[str, str]
) -> list[str]:
    chain: list[str] = []
    current = entity
    seen = {entity}
    while current:
        chain.append(descriptors.get(current, ""))
        parent = parents.get(current)
        if not parent or parent in seen:
            break
        seen.add(parent)
        current = parent
    return chain


def class_membership_obligation(
    *,
    obligation_id: str,
    purpose: str,
    authority_refs: Sequence[str],
    semantic_class: str,
    program_subject: str,
    program_scope: str,
    question: str = "",
) -> ConstructionObligation:
    """Build the one allowed CLASS_MEMBERSHIP obligation shape."""

    subject = str(program_subject or "").strip()
    klass = str(semantic_class or "").strip()
    asked = str(question or "").strip() or (
        f"Does the supplied program manifestation belong to {klass}?"
    )
    return ConstructionObligation(
        obligation_id=obligation_id,
        purpose=purpose,
        authority_refs=tuple(authority_refs),
        semantic_subject=klass,
        semantic_relation=CLASS_MEMBERSHIP_RELATION,
        question=asked,
        obligation_kind=CLASS_MEMBERSHIP_OBLIGATION_KIND,
        program_scope=program_scope,
        allowed_program_endpoints=(subject,),
        required_evidence_classes=(
            EvidenceClass.AUTHORITY_GROUNDING.value,
            EvidenceClass.PROGRAM_GROUNDING.value,
            EvidenceClass.MECHANICAL_GROUNDING.value,
        ),
        tuple_shape=CLASS_MEMBERSHIP_TUPLE_SHAPE,
        admission_profile=CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    )


def _catalog_entry(
    catalog: Mapping[str, Any], reference: Mapping[str, Any]
) -> Mapping[str, Any] | None:
    kind = str(reference.get("kind") or "")
    identifier = str(reference.get("id") or "")
    for item in catalog.get("entries") or []:
        if (
            isinstance(item, Mapping)
            and str(item.get("kind") or "") == kind
            and str(item.get("id") or "") == identifier
        ):
            return item
    return None


def _source_content(entry: Mapping[str, Any]) -> tuple[str, str]:
    pointer = entry.get("pointer")
    payload = pointer if isinstance(pointer, Mapping) else {}
    handle = str(
        payload.get("native_handle")
        or payload.get("handle")
        or entry.get("id")
        or ""
    )
    text = str(
        payload.get("reconstructed_text")
        or payload.get("text")
        or entry.get("description")
        or ""
    )
    return handle, text


def _canonical_mechanical_fact(
    entry: Mapping[str, Any],
    descriptors: Mapping[str, str],
) -> dict[str, Any]:
    fact = entry.get("fact")
    recorded = fact if isinstance(fact, Mapping) else {}
    inner = recorded.get("recorded_fact")
    payload = inner if isinstance(inner, Mapping) else recorded
    relation = str(payload.get("relation") or recorded.get("relation") or "")
    roles = {}
    for key in ("call_site", "target", "owner", "subject", "parent", "child", "entity"):
        value = str(payload.get(key) or "")
        if value:
            roles[f"{key}_descriptor"] = descriptors.get(value, "")
    return {
        "kind": str(entry.get("kind") or "relation_tuple"),
        "relation": relation,
        "roles": dict(sorted(roles.items())),
    }


def _canonical_dependency(
    item: Mapping[str, Any],
    descriptors: Mapping[str, str],
    parents: Mapping[str, str],
) -> dict[str, Any]:
    kind = str(item.get("kind") or "")
    entity = str(item.get("program_entity") or "")
    if kind == "program_identity":
        return {
            "kind": kind,
            "descriptor": descriptors.get(entity, ""),
        }
    if kind == "structural_context":
        return {
            "kind": kind,
            "descriptor": descriptors.get(entity, ""),
            "chain": _descriptor_chain(entity, parents, descriptors),
        }
    if kind == "relation_tuple":
        recorded = item.get("recorded")
        payload = recorded if isinstance(recorded, Mapping) else {}
        return {
            "kind": kind,
            "relation": str(payload.get("relation") or ""),
            "roles": {
                f"{key}_descriptor": descriptors.get(str(payload.get(key) or ""), "")
                for key in ("call_site", "target", "owner", "subject")
                if str(payload.get(key) or "")
            },
        }
    if kind == "manifestation_property":
        return {
            "kind": kind,
            "descriptor": descriptors.get(entity, ""),
            "property": str(item.get("property") or ""),
            "value": str(item.get("value") or ""),
        }
    return {"kind": kind}


def build_interpretation_basis(
    world: ConstructionWorld,
    obligation: ConstructionObligation,
    candidate: SemanticCandidate,
    catalog: Mapping[str, Any],
) -> dict[str, Any]:
    """Canonical material evidence package for CLASS_MEMBERSHIP reuse.

    Canonicalization uses source content, identity descriptors, relation
    tuples rewritten with those descriptors, class identity, and the
    construction profile.  Snapshot IDs, assertion IDs, and observation IDs
    are excluded.
    """

    descriptors = _descriptors(world)
    kinds = _kinds(world)
    parents = _parents(world)
    program_subject = next(iter(obligation.allowed_program_endpoints))
    class_grounding: list[dict[str, str]] = []
    program_source: list[dict[str, str]] = []
    mechanical: list[dict[str, Any]] = []
    for reference in candidate.evidence_refs:
        entry = _catalog_entry(catalog, reference)
        if not isinstance(entry, Mapping):
            continue
        category = str(entry.get("category") or "")
        if category == "AUTHORITATIVE_EVIDENCE":
            handle, text = _source_content(entry)
            class_grounding.append(
                {
                    "source_handle": handle,
                    "content_digest": _content_digest(text),
                }
            )
        elif category == "PROGRAM_SOURCE":
            handle, text = _source_content(entry)
            program_source.append(
                {
                    "native_handle": handle,
                    "content_digest": _content_digest(text),
                }
            )
        elif category == "MECHANICAL_FACT":
            mechanical.append(_canonical_mechanical_fact(entry, descriptors))
    structural = [
        {
            "entity_descriptor": descriptors.get(program_subject, ""),
            "entity_kind": kinds.get(program_subject, ""),
            "parent_descriptors": _descriptor_chain(program_subject, parents, descriptors)[1:],
        }
    ]
    dependencies = [
        _canonical_dependency(item, descriptors, parents)
        for item in candidate.maintenance_dependencies
    ]
    basis = {
        "contract": INTERPRETATION_BASIS_SCHEMA,
        "semantic_class": obligation.semantic_subject,
        "program_subject": {
            "kind": kinds.get(program_subject, ""),
            "descriptor": descriptors.get(program_subject, ""),
        },
        "class_grounding": sorted(
            class_grounding, key=lambda item: item.get("source_handle") or ""
        ),
        "program_source": sorted(
            program_source, key=lambda item: item.get("native_handle") or ""
        ),
        "mechanical_facts": sorted(
            mechanical,
            key=lambda item: canonical_json(item),
        ),
        "structural": structural,
        "construction_profile": CLASS_MEMBERSHIP_ADMISSION_PROFILE,
        "construction_profile_version": 1,
        "maintenance_dependencies": sorted(
            dependencies, key=lambda item: canonical_json(item)
        ),
    }
    return basis


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def interpretation_basis_digest(basis: Mapping[str, Any]) -> str:
    payload = copy_json(basis)
    payload.pop("digest", None)
    return digest(payload, "membership-basis")


def persist_interpretation_basis(
    world: ConstructionWorld,
    *,
    assertion_id: str,
    obligation: ConstructionObligation,
    candidate: SemanticCandidate,
    catalog: Mapping[str, Any],
    grounding: Any,
) -> dict[str, Any]:
    basis = build_interpretation_basis(world, obligation, candidate, catalog)
    digest_value = interpretation_basis_digest(basis)
    basis = {**basis, "digest": digest_value}
    existing = {
        str(row["name"]) for row in world.query("SELECT name FROM _world_relations")
    }
    if MEMBERSHIP_BASIS_RELATION not in existing:
        world.declare_relation(
            MEMBERSHIP_BASIS_RELATION,
            [
                Role("assertion_id", RoleType.TEXT),
                Role("semantic_class", RoleType.TEXT),
                Role("program_descriptor", RoleType.TEXT),
                Role("basis_json", RoleType.TEXT),
                Role("digest", RoleType.TEXT),
            ],
            scope="WORLD",
            description="CLASS_MEMBERSHIP interpretation basis receipt.",
        )
    world.assert_tuple(
        MEMBERSHIP_BASIS_RELATION,
        {
            "assertion_id": assertion_id,
            "semantic_class": obligation.semantic_subject,
            "program_descriptor": str(
                (basis.get("program_subject") or {}).get("descriptor") or ""
            ),
            "basis_json": canonical_json(basis),
            "digest": digest_value,
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=grounding,
    )
    return basis


@dataclass(frozen=True)
class ClassMembershipEvidence:
    semantic_class: str
    current_program_subject: str
    current_snapshot: str
    status: str
    source_commitment: str = ""
    source_snapshot: str = ""
    interpretation_basis_digest: str = ""
    current_basis_digest: str = ""
    materialized_current_assertion: bool = False
    model_invoked: bool = False
    reason: str = ""
    correspondence_used: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_class": self.semantic_class,
            "current_program_subject": self.current_program_subject,
            "current_snapshot": self.current_snapshot,
            "status": self.status,
            "source_commitment": self.source_commitment,
            "source_snapshot": self.source_snapshot,
            "interpretation_basis_digest": self.interpretation_basis_digest,
            "current_basis_digest": self.current_basis_digest,
            "materialized_current_assertion": self.materialized_current_assertion,
            "model_invoked": self.model_invoked,
            "reason": self.reason,
            "correspondence_used": self.correspondence_used,
        }


@dataclass(frozen=True)
class MembershipGap:
    semantic_class: str
    program_subject: str
    snapshot: str
    requested_by: str
    reason: str = GAP_REASON_NO_EVIDENCE

    @property
    def gap_id(self) -> str:
        return digest(
            {
                "semantic_class": str(self.semantic_class or "").strip(),
                "program_subject": str(self.program_subject or "").strip(),
                "snapshot": str(self.snapshot or "").strip(),
                "requested_by": str(self.requested_by or "").strip(),
                "reason": str(self.reason or "").strip(),
            },
            "membership-gap",
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MembershipGap:
        return cls(
            semantic_class=str(payload.get("semantic_class") or ""),
            program_subject=str(payload.get("program_subject") or ""),
            snapshot=str(payload.get("snapshot") or ""),
            requested_by=str(payload.get("requested_by") or ""),
            reason=str(payload.get("reason") or GAP_REASON_NO_EVIDENCE),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "semantic_class": self.semantic_class,
            "program_subject": self.program_subject,
            "snapshot": self.snapshot,
            "requested_by": self.requested_by,
            "reason": self.reason,
            "construction_obligation": None,
        }


def _unknown(
    *,
    semantic_class: str,
    program_subject: str,
    snapshot: str,
    reason: str,
    correspondence_used: str = "",
    source_commitment: str = "",
    source_snapshot: str = "",
    admitted_digest: str = "",
    current_digest: str = "",
) -> ClassMembershipEvidence:
    return ClassMembershipEvidence(
        semantic_class=semantic_class,
        current_program_subject=program_subject,
        current_snapshot=snapshot,
        status=MEMBERSHIP_STATUS_UNKNOWN,
        source_commitment=source_commitment,
        source_snapshot=source_snapshot,
        interpretation_basis_digest=admitted_digest,
        current_basis_digest=current_digest,
        materialized_current_assertion=False,
        model_invoked=False,
        reason=reason,
        correspondence_used=correspondence_used,
    )


def _current_membership_rows(
    world: ConstructionWorld, semantic_class: str, program_subject: str
) -> list[dict[str, Any]]:
    return [
        row
        for row in _rows(world, CLASS_MEMBERSHIP_RELATION)
        if str(row.get("semantic_class") or "") == semantic_class
        and str(row.get("program_manifestation") or "") == program_subject
    ]


def _basis_rows(world: ConstructionWorld) -> list[dict[str, Any]]:
    return _rows(world, MEMBERSHIP_BASIS_RELATION)


def reconstruct_interpretation_basis(
    world: ConstructionWorld,
    prior_basis: Mapping[str, Any],
    *,
    program_subject: str,
    source_by_handle: Mapping[str, str] | None = None,
    authority_by_handle: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Rebuild the selected material package from the current snapshot."""

    descriptors = _descriptors(world)
    kinds = _kinds(world)
    parents = _parents(world)
    subject_descriptor = descriptors.get(program_subject, "")
    prior_subject = prior_basis.get("program_subject") or {}
    if str(prior_subject.get("descriptor") or "") != subject_descriptor:
        return None
    if str(prior_subject.get("kind") or "") and str(
        prior_subject.get("kind") or ""
    ) != kinds.get(program_subject, ""):
        return None
    sources = dict(source_by_handle or {})
    authorities = dict(authority_by_handle or {})
    class_grounding = []
    for item in prior_basis.get("class_grounding") or []:
        handle = str(item.get("source_handle") or "")
        text = authorities.get(handle)
        if text is None:
            return None
        class_grounding.append(
            {"source_handle": handle, "content_digest": _content_digest(text)}
        )
    program_source = []
    for item in prior_basis.get("program_source") or []:
        handle = str(item.get("native_handle") or "")
        text = sources.get(handle)
        if text is None:
            return None
        program_source.append(
            {"native_handle": handle, "content_digest": _content_digest(text)}
        )
    invoke_by_descriptors = {
        (
            descriptors.get(str(row.get("call_site") or ""), ""),
            descriptors.get(str(row.get("target") or ""), ""),
        )
        for row in _rows(world, "program_invokes")
    }
    mechanical = []
    for item in prior_basis.get("mechanical_facts") or []:
        fact = copy_json(item)
        roles = fact.get("roles") or {}
        if str(fact.get("relation") or "") == "program_invokes":
            key = (
                str(roles.get("call_site_descriptor") or ""),
                str(roles.get("target_descriptor") or ""),
            )
            if key not in invoke_by_descriptors:
                return None
        mechanical.append(fact)
    current_deps = []
    for item in prior_basis.get("maintenance_dependencies") or []:
        kind = str(item.get("kind") or "")
        if kind == "program_identity":
            current_deps.append(
                {"kind": kind, "descriptor": descriptors.get(program_subject, "")}
            )
        elif kind == "structural_context":
            current_deps.append(
                {
                    "kind": kind,
                    "descriptor": descriptors.get(program_subject, ""),
                    "chain": _descriptor_chain(program_subject, parents, descriptors),
                }
            )
        elif kind == "relation_tuple":
            roles = item.get("roles") or {}
            key = (
                str(roles.get("call_site_descriptor") or ""),
                str(roles.get("target_descriptor") or ""),
            )
            if str(item.get("relation") or "") == "program_invokes" and key not in invoke_by_descriptors:
                return None
            current_deps.append(copy_json(item))
        else:
            current_deps.append(copy_json(item))
    reconstructed = {
        "contract": INTERPRETATION_BASIS_SCHEMA,
        "semantic_class": str(prior_basis.get("semantic_class") or ""),
        "program_subject": {
            "kind": kinds.get(program_subject, ""),
            "descriptor": subject_descriptor,
        },
        "class_grounding": sorted(
            class_grounding, key=lambda item: item.get("source_handle") or ""
        ),
        "program_source": sorted(
            program_source, key=lambda item: item.get("native_handle") or ""
        ),
        "mechanical_facts": sorted(mechanical, key=lambda item: canonical_json(item)),
        "structural": [
            {
                "entity_descriptor": subject_descriptor,
                "entity_kind": kinds.get(program_subject, ""),
                "parent_descriptors": _descriptor_chain(
                    program_subject, parents, descriptors
                )[1:],
            }
        ],
        "construction_profile": str(prior_basis.get("construction_profile") or ""),
        "construction_profile_version": int(
            prior_basis.get("construction_profile_version") or 0
        ),
        "maintenance_dependencies": sorted(
            current_deps, key=lambda item: canonical_json(item)
        ),
    }
    return reconstructed


def _locate_prior_commitment(
    prior_world: ConstructionWorld,
    *,
    semantic_class: str,
    program_subject: str,
    current_descriptors: Mapping[str, str],
    correspondence: Sequence[Mapping[str, Any]] | None,
) -> tuple[dict[str, Any] | None, str]:
    """Locate a prior membership commitment. Correspondence is a locator only."""

    current_descriptor = current_descriptors.get(program_subject, "")
    locator = "descriptor"
    mapped_old = ""
    for item in correspondence or ():
        if str(item.get("new_entity") or "") == program_subject:
            mapped_old = str(item.get("old_entity") or "")
            locator = str(item.get("basis") or item.get("correspondence_basis") or "correspondence")
            break
        if str(item.get("old_entity") or "") == program_subject:
            mapped_old = str(item.get("old_entity") or "")
            locator = str(item.get("basis") or item.get("correspondence_basis") or "correspondence")
            break
    prior_descriptors = _descriptors(prior_world)
    for row in _basis_rows(prior_world):
        if str(row.get("semantic_class") or "") != semantic_class:
            continue
        descriptor = str(row.get("program_descriptor") or "")
        if current_descriptor and descriptor == current_descriptor:
            return dict(row), "descriptor"
        if mapped_old:
            old_descriptor = prior_descriptors.get(mapped_old, "")
            if old_descriptor and old_descriptor == descriptor:
                return dict(row), locator
    for row in _rows(prior_world, CLASS_MEMBERSHIP_RELATION):
        if str(row.get("semantic_class") or "") != semantic_class:
            continue
        manifestation = str(row.get("program_manifestation") or "")
        if current_descriptor and prior_descriptors.get(manifestation, "") == current_descriptor:
            matching_basis = next(
                (
                    dict(item)
                    for item in _basis_rows(prior_world)
                    if str(item.get("program_descriptor") or "") == current_descriptor
                    and str(item.get("semantic_class") or "") == semantic_class
                ),
                None,
            )
            return matching_basis, "descriptor"
        if mapped_old and manifestation == mapped_old:
            matching_basis = next(
                (
                    dict(item)
                    for item in _basis_rows(prior_world)
                    if str(item.get("assertion_id") or "")
                    and str(item.get("semantic_class") or "") == semantic_class
                ),
                None,
            )
            return matching_basis, locator
    return None, locator if mapped_old else ""


def lookup_class_membership_evidence(
    current_world: ConstructionWorld,
    semantic_class: str,
    program_subject: str,
    *,
    prior_world: ConstructionWorld | None = None,
    correspondence: Sequence[Mapping[str, Any]] | None = None,
    source_by_handle: Mapping[str, str] | None = None,
    authority_by_handle: Mapping[str, str] | None = None,
    allow_correspondence_without_basis: bool = False,
) -> ClassMembershipEvidence:
    """Return current-snapshot membership evidence. Never invokes a model."""

    try:
        snapshot = world_snapshot_id(current_world)
    except Exception:
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot="",
            reason="required current identity/capability is missing",
        )
    current_rows = _current_membership_rows(
        current_world, semantic_class, program_subject
    )
    if current_rows:
        basis = next(
            (
                row
                for row in _basis_rows(current_world)
                if str(row.get("semantic_class") or "") == semantic_class
                and str(row.get("program_descriptor") or "")
                == _descriptors(current_world).get(program_subject, "")
            ),
            {},
        )
        return ClassMembershipEvidence(
            semantic_class=semantic_class,
            current_program_subject=program_subject,
            current_snapshot=snapshot,
            status=MEMBERSHIP_STATUS_ESTABLISHED,
            source_commitment=str(basis.get("assertion_id") or ""),
            source_snapshot=snapshot,
            interpretation_basis_digest=str(basis.get("digest") or ""),
            current_basis_digest=str(basis.get("digest") or ""),
            materialized_current_assertion=True,
            model_invoked=False,
            reason="current admitted semantic_program_membership",
        )
    if prior_world is None:
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot=snapshot,
            reason="no current membership assertion",
        )
    if not _kinds(current_world) or not _descriptors(current_world):
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot=snapshot,
            reason="required current identity/capability is missing",
        )
    prior_row, locator = _locate_prior_commitment(
        prior_world,
        semantic_class=semantic_class,
        program_subject=program_subject,
        current_descriptors=_descriptors(current_world),
        correspondence=correspondence,
    )
    if prior_row is None:
        if correspondence and allow_correspondence_without_basis:
            return _unknown(
                semantic_class=semantic_class,
                program_subject=program_subject,
                snapshot=snapshot,
                reason="correspondence is not membership evidence",
                correspondence_used=locator or "HEURISTIC",
            )
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot=snapshot,
            reason="no relevant prior membership commitment",
            correspondence_used=locator,
        )
    try:
        prior_basis = json.loads(str(prior_row.get("basis_json") or "{}"))
    except json.JSONDecodeError:
        prior_basis = {}
    if not isinstance(prior_basis, Mapping) or not prior_basis:
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot=snapshot,
            reason="prior interpretation basis is incompatible",
            correspondence_used=locator,
            source_commitment=str(prior_row.get("assertion_id") or ""),
            source_snapshot=world_snapshot_id(prior_world),
        )
    reconstructed = reconstruct_interpretation_basis(
        current_world,
        prior_basis,
        program_subject=program_subject,
        source_by_handle=source_by_handle,
        authority_by_handle=authority_by_handle,
    )
    admitted_digest = str(prior_row.get("digest") or interpretation_basis_digest(prior_basis))
    if reconstructed is None:
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot=snapshot,
            reason="current interpretation basis cannot be reconstructed",
            correspondence_used=locator,
            source_commitment=str(prior_row.get("assertion_id") or ""),
            source_snapshot=world_snapshot_id(prior_world),
            admitted_digest=admitted_digest,
        )
    current_digest = interpretation_basis_digest(reconstructed)
    if current_digest != admitted_digest:
        return _unknown(
            semantic_class=semantic_class,
            program_subject=program_subject,
            snapshot=snapshot,
            reason="material interpretation basis changed",
            correspondence_used=locator,
            source_commitment=str(prior_row.get("assertion_id") or ""),
            source_snapshot=world_snapshot_id(prior_world),
            admitted_digest=admitted_digest,
            current_digest=current_digest,
        )
    return ClassMembershipEvidence(
        semantic_class=semantic_class,
        current_program_subject=program_subject,
        current_snapshot=snapshot,
        status=MEMBERSHIP_STATUS_PRESERVED,
        source_commitment=str(prior_row.get("assertion_id") or ""),
        source_snapshot=world_snapshot_id(prior_world),
        interpretation_basis_digest=admitted_digest,
        current_basis_digest=current_digest,
        materialized_current_assertion=False,
        model_invoked=False,
        reason="identical reconstructed interpretation basis",
        correspondence_used=locator,
    )


def membership_gap(
    *,
    semantic_class: str,
    program_subject: str,
    snapshot: str,
    requested_by: str,
) -> MembershipGap:
    return MembershipGap(
        semantic_class=semantic_class,
        program_subject=program_subject,
        snapshot=snapshot,
        requested_by=requested_by,
    )

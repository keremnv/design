"""Application-level admission checks for authority construction."""

from __future__ import annotations

import json
import hashlib
from typing import Any

from ontology_author.world.core.source import SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld
from ontology_author.construction_boundary import support_paths_for_assertion
from ontology_author.world.runtime.publication import PublicationRef
from .evidence import reconstruct_authority_observation

from ontology_author.program_spine.comparison import COMPARABLE_RELATIONS, RELATION_CAPABILITIES

from ontology_author.evidence.markdown import parse_byte_location

from .construction import AuthorityConstructor, optional_program_rows, authority_construction_contract
from .schemas import (
    AdequacyOutcome,
    AuthorityConstructionReceipt,
    ClaimKind,
    CompletenessScope,
    RECEIPT_VERSION,
    load_receipt,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    UnresolvedKind,
)
from .relevance import (
    CLAUSE_KINDS,
    COMPLIANCE_SCOPE_TOKENS,
    MANIFESTATION_PROPERTIES,
    SCOPE_ORIGINS,
    clause_from_row,
    clause_key,
    default_clause_keys,
)
from .evaluate import relation_rows_with_ids


CERTAIN_KINDS = {
    ClaimKind.SOURCE_PROPOSITION.value,
    ClaimKind.SOURCE_SEMANTIC.value,
    ClaimKind.SOURCE_PROGRAM.value,
    ClaimKind.SEMANTIC_PROGRAM.value,
}


def observations_for_assertion(world: ConstructionWorld, assertion_id: str) -> list[SourceObservation]:
    rows = world.query(
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


def grounding_extra(world: ConstructionWorld, assertion_id: str) -> dict[str, Any]:
    warrant = world.warrant_for_assertion(assertion_id)
    for base in warrant.get("bases") or []:
        detail = base.get("detail")
        if isinstance(detail, dict) and isinstance(detail.get("extra"), dict):
            return dict(detail["extra"])
    return {}


def validate_authority_construction(
    constructor: AuthorityConstructor,
    receipt: AuthorityConstructionReceipt,
) -> list[str]:
    world = constructor.world
    errors: list[str] = []
    standing = {
        row["source_handle"]: (row["standing"], row["content_revision"])
        for row in world.relation_rows("authority_source")
    }
    program_entities = {str(row["entity"]): str(row["snapshot"]) for row in optional_program_rows(world, "program_entity")}
    semantic_entities = {str(row["entity"]) for row in world.relation_rows("semantic_entity")}

    if receipt.receipt_version != RECEIPT_VERSION:
        errors.append(f"unsupported receipt version: {receipt.receipt_version}")
    if "authority_understood" in receipt.to_dict():
        errors.append("receipt claims global authority understanding")
    if receipt.program_snapshot_id != constructor._snapshot_id:
        errors.append("receipt program snapshot does not match the governed World")

    for row in world.relation_rows("authority_claim"):
        kind = str(row["claim_kind"])
        support = str(row["relation_support"])
        if kind not in {item.value for item in ClaimKind}:
            errors.append(f"invalid claim kind: {kind}")
        if support not in {item.value for item in RelationSupport}:
            errors.append(f"invalid relation support: {support}")
        if kind == ClaimKind.UNRESOLVED_RECORD.value:
            continue
        assertion_id = str(row["assertion_id"])
        observations = observations_for_assertion(world, assertion_id)
        if not observations:
            errors.append(f"claim {assertion_id} lacks reconstructible source observations")
            continue
        extra = grounding_extra(world, assertion_id)
        governing = bool(row["governing"]) or bool(extra.get("governing"))
        if extra.get("relation_support") and extra["relation_support"] != support:
            errors.append(f"claim {assertion_id} support class disagrees with envelope")
        if extra.get("claim_kind") and extra["claim_kind"] != kind:
            errors.append(f"claim {assertion_id} claim kind disagrees with envelope")
        for observation in observations:
            declared = standing.get(observation.native_handle)
            if declared is None:
                errors.append(f"claim {assertion_id} is grounded outside the declared source universe")
                continue
            source_standing, revision = declared
            if observation.source_revision != revision:
                errors.append(f"claim {assertion_id} observation revision is not the declared source revision")
            source = constructor.markdown.get(observation.native_handle)
            if source is None:
                errors.append(f"claim {assertion_id} observation is not reconstructible")
                continue
            if observation.source_revision != source.revision:
                errors.append(f"claim {assertion_id} observation digest does not match immutable source bytes")
            try:
                start, end = parse_byte_location(observation.native_location)
            except Exception:
                errors.append(f"claim {assertion_id} observation is not a byte range")
                continue
            if end > len(source.data):
                errors.append(f"claim {assertion_id} observation range is not reconstructible")
            if governing and source_standing != SourceStanding.AUTHORITATIVE.value:
                errors.append(
                    f"claim {assertion_id} uses {source_standing} evidence as governing authority"
                )

    for row in world.relation_rows("authority_endpoint_resolution"):
        resolution = str(row["resolution"])
        if resolution not in {item.value for item in ReferentResolution}:
            errors.append(f"invalid referent resolution: {resolution}")
        referent = str(row["referent"])
        if resolution in {
            ReferentResolution.NATIVE_ID.value,
            ReferentResolution.DETERMINISTIC.value,
            ReferentResolution.SOURCE_DEFINED.value,
            ReferentResolution.AGENT_RESOLVED.value,
        }:
            if referent not in program_entities and referent not in semantic_entities:
                errors.append(f"resolved endpoint is not a World identity: {referent}")
        if referent in program_entities:
            claim = next(
                (item for item in world.relation_rows("authority_claim") if item["assertion_id"] == row["assertion_id"]),
                None,
            )
            if claim and str(claim["claim_kind"]) in {
                ClaimKind.SOURCE_PROGRAM.value,
                ClaimKind.SEMANTIC_PROGRAM.value,
            }:
                if program_entities[referent] != constructor._snapshot_ref:
                    errors.append(f"program attachment {referent} is not in the governed snapshot")

    ambiguous_candidates: set[str] = set()
    for row in world.relation_rows("authority_unresolved"):
        if row["kind"] not in {item.value for item in UnresolvedKind}:
            errors.append(f"invalid unresolved kind: {row['kind']}")
        if row["kind"] == UnresolvedKind.AMBIGUOUS_REFERENT.value:
            ambiguous_candidates.update(json.loads(row["candidates_json"] or "[]"))
        for candidate in world.relation_rows("authority_unresolved_candidate"):
            if candidate["record_id"] != row["record_id"]:
                continue
            if candidate["candidate"] not in program_entities and candidate["candidate"] not in semantic_entities:
                errors.append("unresolved candidate is not a governed identity")

    if ambiguous_candidates:
        certain_targets = {
            str(row["referent"])
            for row in world.relation_rows("authority_endpoint_resolution")
            if any(
                claim["assertion_id"] == row["assertion_id"] and claim["claim_kind"] in CERTAIN_KINDS
                for claim in world.relation_rows("authority_claim")
            )
        }
        overlap = ambiguous_candidates & certain_targets
        if overlap:
            errors.append("ambiguous unresolved candidates were also asserted as certain attachments")

    for row in world.relation_rows("authority_attachment_warrant"):
        entity = str(row["program_entity"])
        if entity not in program_entities:
            errors.append(f"attachment warrant target is not in the program universe: {entity}")
            continue
        if str(row["program_snapshot_id"]) != constructor._snapshot_id:
            errors.append("attachment warrant snapshot does not match the governed program snapshot")
        if program_entities[entity] != constructor._snapshot_ref:
            errors.append("attachment warrant program entity belongs to a different snapshot")
        if not json.loads(row["structural_context"] or "[]"):
            errors.append(f"attachment warrant lacks structural context: {entity}")

    declared_completeness = {
        row["scope"]: row for row in world.relation_rows("authority_completeness")
    }
    receipt_by_scope = {item["scope"]: item for item in receipt.completeness_references}
    if set(receipt_by_scope) - set(declared_completeness):
        errors.append("receipt completeness references facts that are not in the World")
    for scope, row in declared_completeness.items():
        item = receipt_by_scope.get(scope)
        if item is None:
            errors.append(f"receipt omits completeness scope {scope}")
            continue
        if not item.get("kernel_receipt_id"):
            errors.append(f"receipt completeness for {scope} lacks a kernel receipt")
        if item.get("status") != row["status"] or item.get("basis") != row["basis"]:
            errors.append(f"receipt completeness does not match World for {scope}")
        kernel_status = item.get("kernel_status")
        if kernel_status and kernel_status != row["status"]:
            errors.append(f"receipt broadens completeness for {scope}")
        if scope == CompletenessScope.ATTACHMENT.value and row["status"] == "COMPLETE":
            if constructor.purpose not in str(row["basis"]) or constructor.profile not in str(row["basis"]):
                errors.append("attachment completeness basis is broader than the declared purpose/profile")

    expected_semantic = set(constructor.created_semantic) | set(constructor.reused_semantic)
    if semantic_entities != expected_semantic:
        errors.append("semantic referents exist that were not explicitly created or reused")
    for referent in semantic_entities:
        if not str(referent).startswith("semantic:"):
            errors.append(f"semantic membership is not a semantic referent: {referent}")

    for row in world.relation_rows("authority_adequacy"):
        if row["outcome"] not in {item.value for item in AdequacyOutcome}:
            errors.append(f"invalid adequacy outcome: {row['outcome']}")
        if row["outcome"] == AdequacyOutcome.FAILED.value:
            errors.append(f"adequacy probe failed: {row['probe']}")

    if receipt.direct_source_program_links != sum(
        1 for row in world.relation_rows("authority_claim") if row["claim_kind"] == ClaimKind.SOURCE_PROGRAM.value
    ):
        errors.append("receipt source→program count does not match World claims")
    if receipt.semantic_program_links != sum(
        1 for row in world.relation_rows("authority_claim") if row["claim_kind"] == ClaimKind.SEMANTIC_PROGRAM.value
    ):
        errors.append("receipt semantic→program count does not match World claims")

    errors.extend(_validate_relevance_scopes(world, constructor))
    if receipt.construction_basis != constructor.basis.as_dict():
        errors.append("receipt construction basis does not match admitted constructor inputs")
    errors.extend(verify_construction_boundary(world, receipt))
    return sorted(set(errors))


def verify_construction_boundary(
    world: ConstructionWorld, receipt: AuthorityConstructionReceipt,
) -> list[str]:
    """Check retained material closure; never certify semantic judgment or discovery.

    Publication dependencies identify retained occurrences. They need not be
    recursively read to reconstruct this publication's own source support.
    """
    errors: list[str] = []
    if receipt.construction_contract != authority_construction_contract():
        errors.append("construction contract is missing or unsupported")
    if not receipt.constructor.get("id") or not receipt.constructor.get("version"):
        errors.append("construction method requires id and version")
    basis = receipt.construction_basis
    if not isinstance(basis, dict):
        return [*errors, "construction basis is missing"]
    try:
        observations = [SourceObservation(**item) for item in basis["observations"]]
        publications = [PublicationRef.from_mapping(item) for item in basis["publications"]]
        if basis.get("candidate_baseline") is not None:
            baseline = PublicationRef.from_mapping(basis["candidate_baseline"])
            if baseline not in publications:
                errors.append("candidate baseline is missing from construction publication inputs")
        declared = {
            (str(row["source_handle"]), str(row["content_revision"]))
            for row in world.relation_rows("authority_source")
        }
        if {(item.native_handle, item.source_revision) for item in observations} != declared:
            errors.append("construction basis does not match declared source revisions")
        for observation in observations:
            if reconstruct_authority_observation(world, observation)[1] != "OK":
                errors.append("construction basis source does not reconstruct")
        snapshots = optional_program_rows(world, "program_snapshot")
        qualifiers = basis["program_snapshots"]
        if len(qualifiers) != len(snapshots):
            errors.append("construction basis program snapshot qualification is missing or extraneous")
        for qualifier, snapshot in zip(qualifiers, snapshots):
            reference = PublicationRef.from_mapping(qualifier["publication"])
            if reference not in publications or qualifier["snapshot"] != snapshot["snapshot"] or qualifier["snapshot_id"] != receipt.program_snapshot_id:
                errors.append("construction basis program qualification disagrees with snapshot")
        for row in world.relation_rows("authority_claim"):
            assertion_id = str(row["assertion_id"])
            paths = support_paths_for_assertion(world, assertion_id)
            # Legacy flat warrants retain their recorded meaning. New envelopes
            # must explicitly group support, including unresolved records.
            extra = grounding_extra(world, assertion_id)
            if not paths and extra.get("constructor_version"):
                errors.append(f"claim {assertion_id} lacks explicit support paths")
            if paths:
                pointers = {tuple(member.as_pointer().items()) for path in paths for member in path.members}
                flat = {tuple(item.as_pointer().items()) for item in observations_for_assertion(world, assertion_id)}
                if pointers != flat:
                    errors.append(f"claim {assertion_id} support paths disagree with recorded grounding")
                for path in paths:
                    for member in path.members:
                        if (member.native_handle, member.source_revision) not in declared or reconstruct_authority_observation(world, member)[1] != "OK":
                            errors.append(f"claim {assertion_id} support member does not reconstruct within basis")
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"malformed construction boundary: {exc}")
    errors.extend(str(item) for item in world.admission_errors())
    from ontology_author.evidence.program_source import verify_retained_program_inputs
    errors.extend(verify_retained_program_inputs(world))
    return sorted(set(errors))


def verify_authority_publication(world: ConstructionWorld) -> list[str]:
    """Verify the retained receipt and boundary from the bundle alone."""
    try:
        directory = world.path.parent
        manifest = json.loads((directory / "authority.manifest.json").read_text())
        path = directory / "authority.construction.receipt.json"
        if manifest["receipt"]["path"] != path.name:
            return ["authority manifest receipt path differs"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["receipt"]["sha256"]:
            return ["authority receipt digest differs from manifest"]
        receipt = load_receipt(path)
        if manifest.get("admission") != {
            "contract": authority_construction_contract()["id"], "outcome": "PASS",
        }:
            return ["authority admission record is missing or unsupported"]
        if any(manifest[key] != getattr(receipt, key) for key in ("construction_id", "purpose", "profile", "program_snapshot_id")):
            return ["authority manifest disagrees with receipt"]
        return verify_construction_boundary(world, receipt)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"authority publication metadata cannot reconstruct: {exc}"]


def _entity_kind(world: ConstructionWorld, entity: str) -> str:
    for row in optional_program_rows(world, "program_entity_kind"):
        if str(row["entity"]) == entity:
            return str(row["kind"] or "")
    return ""


def _validate_relevance_scopes(world: ConstructionWorld, constructor: AuthorityConstructor) -> list[str]:
    errors: list[str] = []
    program_entities = {str(row["entity"]) for row in optional_program_rows(world, "program_entity")}
    warrants = {
        str(row.get("_assertion_id") or ""): row
        for row in relation_rows_with_ids(world, "authority_attachment_warrant")
    }
    try:
        scope_rows = relation_rows_with_ids(world, "authority_relevance_scope")
    except Exception:
        if warrants:
            errors.append("program-involving attachments lack persisted authority_relevance_scope rows")
        return errors

    by_warrant: dict[str, list[dict[str, Any]]] = {}
    for row in scope_rows:
        clause = clause_from_row(row)
        warrant_id = clause["warrant_assertion_id"]
        if warrant_id not in warrants:
            errors.append(f"relevance scope {warrant_id} does not belong to an attachment warrant")
            continue
        warrant = warrants[warrant_id]
        if clause["attachment_assertion_id"] != str(warrant["assertion_id"]):
            errors.append(f"relevance scope attachment {clause['attachment_assertion_id']} does not match warrant")
        if clause["program_entity"] != str(warrant["program_entity"]):
            errors.append("relevance scope program_entity does not match warrant")
        if clause["clause_kind"] not in CLAUSE_KINDS:
            errors.append(f"unsupported relevance-scope clause_kind: {clause['clause_kind']}")
        if clause["origin"] not in SCOPE_ORIGINS:
            errors.append(f"unsupported relevance-scope origin: {clause['origin']}")
        if any(token in COMPLIANCE_SCOPE_TOKENS for token in clause["clause_kind"].split()):
            errors.append("relevance scope encodes a compliance outcome")
        identity = clause["identity_id"]
        if identity not in program_entities:
            errors.append(f"relevance-scope identity is not in the construction snapshot: {identity}")
        if clause["relation_name"] and clause["relation_name"] not in COMPARABLE_RELATIONS:
            errors.append(f"relevance-scope relation is not produced by the spine: {clause['relation_name']}")
        if clause["structural_capability"] and clause["structural_capability"] not in set(RELATION_CAPABILITIES.values()):
            errors.append(f"relevance-scope structural capability is unknown: {clause['structural_capability']}")
        for prop in clause["manifestation_properties"]:
            if prop not in MANIFESTATION_PROPERTIES:
                errors.append(f"relevance-scope manifestation property is unsupported: {prop}")
        relation_tuple = clause["relation_tuple"]
        if relation_tuple:
            if not isinstance(relation_tuple, dict):
                errors.append("relevance-scope relation_tuple is not an object")
            else:
                for key, value in relation_tuple.items():
                    if key == "relation":
                        continue
                    if isinstance(value, str) and value and value not in program_entities:
                        errors.append(f"relevance-scope relation endpoint is not a program identity: {value}")
        by_warrant.setdefault(warrant_id, []).append(clause)

    for warrant_id, warrant in warrants.items():
        entity = str(warrant["program_entity"])
        kind = _entity_kind(world, entity)
        expected = default_clause_keys(kind, entity)
        persisted = {
            clause_key(clause)
            for clause in by_warrant.get(warrant_id, [])
            if clause.get("origin") == "DEFAULT_KIND_RULE"
        }
        if expected - persisted:
            errors.append(f"default relevance scope was not persisted for warrant {warrant_id}")
        unexpected_defaults = persisted - expected
        if unexpected_defaults:
            errors.append(f"persisted default relevance scope is not the kind default for warrant {warrant_id}")
    return errors

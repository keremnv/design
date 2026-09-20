from __future__ import annotations

import copy
from types import SimpleNamespace

from ontology_author.program_spine.comparison import ProgramDelta
from ontology_author.semantic_binding import (
    INVARIANT_ADMISSION_PROFILE,
    PROGRAM_INVARIANT_OBLIGATION_KIND,
    PROGRAM_INVARIANT_TUPLE_SHAPE,
    PROGRAM_INVARIANT_UNIVERSE_RELATION,
    ConstructionObligation,
    EvidenceClass,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
    maintain_semantic_commitment,
    semantic_candidate_schema,
)
from ontology_author.semantic_binding.admission import (
    PROGRAM_INVARIANT_RELATION,
)
from ontology_author.semantic_binding.schemas import CandidateValidationError


def _case() -> dict:
    return {
        "case_id": "case:payment-universal",
        "authority": {
            "observations": [
                {
                    "observation_id": "obs:payment-universal",
                    "standing": "AUTHORITATIVE",
                    "reconstructed_text": (
                        "All payment-provider access from Checkout must go "
                        "through PaymentGateway."
                    ),
                }
            ],
            "semantic_referents": [
                {"id": "semantic:CheckoutProviderAccess", "label": "Checkout access"},
                {"id": "semantic:PaymentGatewayBoundary", "label": "PaymentGateway"},
            ],
        },
        "semantic_context": {"referents": [], "claims": [], "program_links": []},
        "program_context": {
            "referents": [
                {"id": "program:checkout", "kind": "callable", "side": "OLD"},
                {"id": "program:authorize", "kind": "callable", "side": "OLD"},
                {"id": "program:gateway", "kind": "callable", "side": "OLD"},
                {"id": "program:stripe", "kind": "callable", "side": "OLD"},
            ],
            "relation_tuples": [
                {
                    "evidence_id": "relation:checkout-authorize",
                    "recorded_fact": {
                        "relation": "program_invokes",
                        "call_site": "program:checkout-call",
                        "target": "program:authorize",
                    },
                },
                {
                    "evidence_id": "relation:authorize-gateway",
                    "recorded_fact": {
                        "relation": "program_invokes",
                        "call_site": "program:authorize-call",
                        "target": "program:gateway",
                    },
                },
                {
                    "evidence_id": "relation:gateway-stripe",
                    "recorded_fact": {
                        "relation": "program_invokes",
                        "call_site": "program:gateway-call",
                        "target": "program:stripe",
                    },
                },
            ],
            "source_evidence": [],
            "resolution_outcomes": [],
            "structural_context": [],
        },
        "completeness": [],
        "selection": [],
        "supporting_material": [],
    }


def _obligation() -> ConstructionObligation:
    return ConstructionObligation(
        obligation_id="obligation:payment-universal",
        purpose="payment-universal-v1",
        authority_refs=("obs:payment-universal",),
        semantic_subject="semantic:CheckoutProviderAccess",
        semantic_relation="all_provider_access_mediated_by",
        question=(
            "Within the declared Checkout payment scope, does every provider "
            "access go through PaymentGateway?"
        ),
        program_scope="Checkout payment-provider access universe",
        allowed_program_endpoints=("program:checkout",),
        required_evidence_classes=(
            EvidenceClass.AUTHORITY_GROUNDING.value,
            EvidenceClass.PROGRAM_GROUNDING.value,
            EvidenceClass.MECHANICAL_GROUNDING.value,
        ),
        tuple_shape=PROGRAM_INVARIANT_TUPLE_SHAPE,
        obligation_kind=PROGRAM_INVARIANT_OBLIGATION_KIND,
        admission_profile=INVARIANT_ADMISSION_PROFILE,
    )


def _catalog(*, complete: bool = True, relation_count: int = 3):
    obligation = _obligation()
    case = _case()
    relations = case["program_context"]["relation_tuples"][:relation_count]
    dependencies = [
        {"kind": "relation_tuple", "recorded": item["recorded_fact"], "evidence_id": item["evidence_id"]}
        for item in relations
    ]
    dependencies.extend(
        {"kind": "program_identity", "program_entity": entity}
        for entity in ("program:checkout", "program:authorize", "program:gateway", "program:stripe")
    )
    receipts = []
    if complete:
        receipts.append(
            {
                "receipt_id": "complete:checkout-provider-universe",
                "status": "COMPLETE",
                "universe": PROGRAM_INVARIANT_UNIVERSE_RELATION,
                "program_scope": obligation.program_scope,
                "member_evidence_refs": [item["evidence_id"] for item in relations],
            }
        )
    catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=[
            {
                "evidence_id": "source:checkout",
                "program_entity": "program:checkout",
                "side": "OLD",
                "reconstruction": "OK",
                "reconstructed_text": "checkout();",
            }
        ],
        maintenance_dependencies=dependencies,
        completeness_receipts=receipts,
        program_endpoint_kinds={"program:checkout": "callable"},
    )
    return obligation, catalog, relations


def _alias(catalog, category, identifier=None):
    for item in catalog["entries"]:
        if item["category"] == category and (
            identifier is None or item["id"] == identifier
        ):
            return item["alias"]
    raise AssertionError((category, identifier))


def _draft(obligation, catalog, relations, *, include_complete=True):
    return {
        "obligation_id": obligation.obligation_id,
        "claim_kind": "SEMANTIC_PROGRAM",
        "relation_name": obligation.semantic_relation,
        "semantic_endpoints": {
            "access": _alias(catalog, "SEMANTIC_REFERENT", "semantic:CheckoutProviderAccess"),
            "boundary": _alias(catalog, "SEMANTIC_REFERENT", "semantic:PaymentGatewayBoundary"),
        },
        "program_endpoints": {
            "scope_root": _alias(catalog, "PROGRAM_ENDPOINT", "program:checkout"),
        },
        "polarity": "POSITIVE",
        "support_kind": "CROSS_EVIDENCE_INFERRED",
        "authority_evidence_aliases": [_alias(catalog, "AUTHORITATIVE_EVIDENCE")],
        "program_source_evidence_aliases": [
            _alias(catalog, "PROGRAM_SOURCE", "source:checkout")
        ],
        "mechanical_evidence_aliases": [
            _alias(catalog, "MECHANICAL_FACT", item["evidence_id"])
            for item in relations
        ],
        "program_scope": obligation.program_scope,
        "maintenance_dependency_aliases": [
            item["alias"]
            for item in catalog["entries"]
            if item["category"] == "MAINTENANCE_DEPENDENCY"
        ],
        "completeness_aliases": (
            [_alias(catalog, "COMPLETENESS_RECEIPT")]
            if include_complete
            else []
        ),
    }


def test_universal_schema_is_scoped_and_requires_completeness():
    obligation, catalog, _relations = _catalog()
    schema = semantic_candidate_schema(catalog)
    assert schema["properties"]["completeness_aliases"]["minItems"] == 1
    assert schema["properties"]["program_endpoints"]["properties"]["scope_root"]["enum"] == [
        _alias(catalog, "PROGRAM_ENDPOINT", "program:checkout")
    ]
    assert schema["properties"]["relation_name"] == {
        "const": obligation.semantic_relation
    }


def test_one_path_or_incomplete_universe_does_not_imply_universal_truth():
    obligation, catalog, relations = _catalog(complete=False, relation_count=1)
    draft = _draft(obligation, catalog, relations, include_complete=False)
    candidate = compile_semantic_candidate_draft(obligation, catalog, draft)
    decision = admit_semantic_candidate(obligation, candidate, catalog)
    assert decision.outcome == "RECORD_UNRESOLVED"
    assert decision.reason == "UNIVERSAL_WITHOUT_COMPLETE_SCOPE"


def test_complete_scoped_universe_and_finite_members_admit_commitment():
    obligation, catalog, relations = _catalog()
    candidate = compile_semantic_candidate_draft(
        obligation, catalog, _draft(obligation, catalog, relations)
    )
    decision = admit_semantic_candidate(obligation, candidate, catalog)
    assert decision.outcome == "PERSIST_COMMITMENT"
    assert decision.completeness_refs == ("complete:checkout-provider-universe",)


def test_wildcard_dependency_is_not_a_finite_commitment():
    obligation, catalog, relations = _catalog()
    wildcard = copy.deepcopy(catalog)
    wildcard["entries"].append(
        {
            "alias": "D999",
            "category": "MAINTENANCE_DEPENDENCY",
            "id": "dependency:wildcard",
            "kind": "dependency",
            "evidence_class": "MECHANICAL_GROUNDING",
            "dependency": {
                "kind": "graph_query",
                "query": "watch every future payment path",
                "dependency_id": "dependency:wildcard",
            },
        }
    )
    draft = _draft(obligation, wildcard, relations)
    draft["maintenance_dependency_aliases"] = ["D999"]
    try:
        compile_semantic_candidate_draft(obligation, wildcard, draft)
    except CandidateValidationError as exc:
        assert "unsupported maintenance dependency kind" in str(exc)
    else:
        raise AssertionError("wildcard dependency was accepted")


def test_universal_relation_name_is_trusted_not_model_controlled():
    obligation, catalog, relations = _catalog()
    draft = _draft(obligation, catalog, relations)
    draft["relation_name"] = "watch_all_payment_paths"
    try:
        compile_semantic_candidate_draft(obligation, catalog, draft)
    except CandidateValidationError:
        pass
    else:
        raise AssertionError("model-controlled invariant relation was accepted")


def test_maintenance_contract_remains_zero_model_and_no_transfer():
    # This uses an empty comparison only to exercise the invariant warrant's
    # existing maintenance vocabulary; the live experiment supplies the real
    # S0 -> C1 comparison.
    obligation, catalog, relations = _catalog()
    candidate = compile_semantic_candidate_draft(
        obligation, catalog, _draft(obligation, catalog, relations)
    )
    decision = admit_semantic_candidate(obligation, candidate, catalog)
    warrant = {
        "assertion_id": "assertion:invariant",
        "obligation_id": obligation.obligation_id,
        "snapshot_id": "snapshot:s0",
        "evidence_refs": list(candidate.evidence_refs),
        "support_kind": candidate.support_kind,
        "resolution_basis": {},
        "depends_on": list(candidate.maintenance_dependencies),
        "admission_profile": decision.admission_profile,
        "admission_decision_id": decision.decision_id,
    }
    comparison_delta = ProgramDelta(
        old_snapshot="snapshot:s0",
        new_snapshot="snapshot:c1",
        identity={},
        groups=[],
        manifestations=[],
        relations={
            "program_invokes": {
                "added": [
                    {
                        "new": {
                            "call_site": "program:new-call",
                            "target": "program:new-provider",
                        }
                    }
                ],
                "preserved": [],
                "removed": [],
                "retargeted": [],
                "unresolved": [],
                "status": "COMPARABLE",
            }
        },
        maintenance={},
    )
    result = maintain_semantic_commitment(
        warrant,
        SimpleNamespace(
            delta=comparison_delta,
            receipt=SimpleNamespace(comparison_id="comparison:test"),
            correspondences=(),
        ),
    )
    assert result["model_invoked"] is False
    assert result["transferred"] is False
    assert not any(
        item["dependency"].get("recorded", {}).get("call_site") == "program:new-call"
        for item in result["assessments"]
    )

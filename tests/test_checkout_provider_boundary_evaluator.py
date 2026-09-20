"""Deterministic checkout-provider-boundary/v1 evaluator tests.

These tests re-derive one scoped invariant from current program-spine facts.
They do not search the repository, invoke a model, or reuse S0 truth.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    AuthorityUniverse,
    ClaimKind,
    CompletenessScope,
    DeclaredSource,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    assemble_governance_case,
    assess_attachment_maintenance,
    assess_authority_change_impact,
    construct_authority_world,
    validate_case_sidecar,
)
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.governance import (
    build_case_evidence_catalog,
    create_governance_adjudication,
    validate_governance_adjudication,
)
from ontology_author.program_spine import compare_program_spines
from ontology_author.governance import (
    CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID,
    CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION,
    CHECKOUT_PROVIDER_BOUNDARY_KIND,
    CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE,
    ScopedInvariantDefinition,
    ScopedInvariantEvaluation,
    aggregate_checkout_provider_boundary_truth,
    evaluate_checkout_provider_boundary,
)
from ontology_author.governance.checkout_invariant import (
    COMPLETENESS_COMPLETE,
    COMPLETENESS_INCOMPLETE,
    HISTORICAL_UNSOUND_FINDING,
    MEMBERSHIP_BASIS_ABSENT,
    MEMBERSHIP_BASIS_DEFINITION,
    MEMBERSHIP_IS_PROVIDER,
    MEMBERSHIP_UNKNOWN,
    MEMBER_SATISFIES,
    MEMBER_UNKNOWN,
    MEMBER_VIOLATES,
    TRUTH_FALSE,
    TRUTH_TRUE,
    TRUTH_UNKNOWN,
)
from ontology_author.world.core.model import CompletenessStatus, Role, RoleType
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import _spine, _write

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "node_modules"
        / "typescript"
    ).exists(),
    reason="the TypeScript compiler API dependency is not installed",
)

AUTHORITY_TEXT = (
    "All payment-provider access from Checkout must go through PaymentGateway."
)

PAYMENT_S0 = {
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); }\n"
    ),
    "src/payment-service.ts": (
        'import { throughGateway } from "./payment-gateway";\n'
        "export function authorize(): void { throughGateway(); }\n"
        "export function authorizeRetry(): void { throughGateway(); }\n"
    ),
    "src/payment-gateway.ts": (
        'import { chargeStripe } from "./stripe-client";\n'
        "export function throughGateway(): void { chargeStripe(); }\n"
    ),
    "src/stripe-client.ts": "export function chargeStripe(): void {}\n",
}
PAYMENT_C1 = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { chargeStripe } from "./stripe-client";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); checkoutDirect(); }\n"
        "export function checkoutDirect(): void { chargeStripe(); }\n"
    ),
}
PAYMENT_C2 = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { throughGateway } from "./payment-gateway";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); checkoutWallet(); }\n"
        "export function checkoutWallet(): void { throughGateway(); }\n"
    ),
}
PAYMENT_INCOMPLETE = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        "const handlers: Record<string, () => void> = {};\n"
        "export function checkout(): void { authorize(); authorizeRetry(); handlers[\"x\"](); }\n"
    ),
}
PAYMENT_INCOMPLETE_VIOLATION = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { chargeStripe } from "./stripe-client";\n'
        "const handlers: Record<string, () => void> = {};\n"
        "export function checkout(): void { authorize(); authorizeRetry(); checkoutDirect(); handlers[\"x\"](); }\n"
        "export function checkoutDirect(): void { chargeStripe(); }\n"
    ),
}
PAYMENT_UNKNOWN_MEMBER = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); dispatch(); }\n"
        "export function dispatch(): void { const handlers: Record<string, () => void> = {}; handlers[\"x\"](); }\n"
    ),
}
PAYMENT_C3 = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { settleExternal } from "./external-settlement";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); checkoutAlternative(); }\n"
        "export function checkoutAlternative(): void { settleExternal(); }\n"
    ),
    "src/external-settlement.ts": "export function settleExternal(): void {}\n",
}
PAYMENT_C4 = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { recordAudit } from "./audit-log";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); recordAudit(); }\n"
    ),
    "src/audit-log.ts": "export function recordAudit(): void {}\n",
}


def _labels(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["id"]): str(row["label"])
        for row in world.query("SELECT id, label FROM _world_referents")
    }


def _callable(world: ConstructionWorld, label: str) -> str:
    kinds = {
        str(row["entity"]): str(row["kind"])
        for row in world.relation_rows("program_entity_kind")
    }
    labels = _labels(world)
    matches = [
        entity
        for entity, kind in kinds.items()
        if kind == "callable" and labels.get(entity) == label
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one callable {label!r}, found {matches}")
    return matches[0]


def _descriptor(world: ConstructionWorld, entity: str) -> str:
    for row in world.relation_rows("program_identity_descriptor"):
        if str(row["entity"]) == entity:
            return str(row["descriptor"])
    raise AssertionError(f"missing identity descriptor for {entity}")


def _open_spine(root: Path, files: dict[str, str], name: str) -> ConstructionWorld:
    _spine(root, files, name)
    return ConstructionWorld.open(root / name / "world.sqlite", read_only=True)


def _definition_for(
    world: ConstructionWorld,
    *,
    definition_id: str = "invariant:checkout-provider-boundary",
    extra_provider_labels: tuple[str, ...] = (),
    provider_semantic: str = "",
) -> ScopedInvariantDefinition:
    checkout = _callable(world, "checkout")
    gateway = _callable(world, "throughGateway")
    providers = [_callable(world, "chargeStripe")]
    providers.extend(_callable(world, label) for label in extra_provider_labels)
    return ScopedInvariantDefinition(
        definition_id=definition_id,
        authority_refs=("obs:payment-universal",),
        access_semantic="semantic:CheckoutProviderAccess",
        boundary_semantic="semantic:PaymentGatewayBoundary",
        scope_root=checkout,
        scope_root_descriptor=_descriptor(world, checkout),
        boundary_program=gateway,
        boundary_program_descriptor=_descriptor(world, gateway),
        provider_programs=tuple(providers),
        provider_descriptors=tuple(_descriptor(world, entity) for entity in providers),
        snapshot_id=snapshot_id(world),
        construction_provenance={
            "method": "test_fixture_construction",
            "model_invoked": False,
        },
        provider_semantic=provider_semantic,
    )


def _member_targets(world: ConstructionWorld, derivation: ScopedInvariantEvaluation) -> set[str]:
    labels = _labels(world)
    return {labels.get(str(item["origin_target"]), "") for item in derivation.member_results}


def _close(*worlds: ConstructionWorld) -> None:
    for world in worlds:
        world.close()


def test_invariant_definition_round_trip_and_is_not_a_truth_result():
    definition = ScopedInvariantDefinition(
        definition_id="invariant:checkout-provider-boundary",
        authority_refs=("obs:payment-universal",),
        access_semantic="semantic:CheckoutProviderAccess",
        boundary_semantic="semantic:PaymentGatewayBoundary",
        scope_root="program:checkout",
        boundary_program="program:gateway",
        scope_root_descriptor="checkout-descriptor",
        boundary_program_descriptor="gateway-descriptor",
        snapshot_id="snapshot:s0",
    )
    restored = ScopedInvariantDefinition.from_dict(definition.to_dict())
    assert restored == definition
    assert "overall_truth" not in definition.to_dict()
    assert definition.definition_kind == CHECKOUT_PROVIDER_BOUNDARY_KIND
    assert definition.evaluator_id == CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID
    assert definition.version == CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION


def test_three_valued_aggregation_table():
    assert (
        aggregate_checkout_provider_boundary_truth(
            completeness=COMPLETENESS_COMPLETE,
            member_results=(MEMBER_SATISFIES, MEMBER_SATISFIES),
        )
        == TRUTH_TRUE
    )
    assert (
        aggregate_checkout_provider_boundary_truth(
            completeness=COMPLETENESS_INCOMPLETE,
            member_results=(MEMBER_SATISFIES, MEMBER_VIOLATES),
        )
        == TRUTH_FALSE
    )
    assert (
        aggregate_checkout_provider_boundary_truth(
            completeness=COMPLETENESS_INCOMPLETE,
            member_results=(MEMBER_SATISFIES,),
        )
        == TRUTH_UNKNOWN
    )
    assert (
        aggregate_checkout_provider_boundary_truth(
            completeness=COMPLETENESS_COMPLETE,
            member_results=(MEMBER_SATISFIES, MEMBER_UNKNOWN),
        )
        == TRUTH_UNKNOWN
    )


def test_s0_scope_enumeration_completeness_and_truth(tmp_path):
    world = _open_spine(tmp_path, PAYMENT_S0, "s0")
    try:
        definition = _definition_for(world)
        first = evaluate_checkout_provider_boundary(world, definition)
        second = evaluate_checkout_provider_boundary(world, definition)
        assert first.evaluator_id == CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_ID
        assert first.evaluator_version == CHECKOUT_PROVIDER_BOUNDARY_EVALUATOR_VERSION
        assert first.snapshot_id == snapshot_id(world)
        assert first.universe["id"] == CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE
        assert first.universe["completeness"] == COMPLETENESS_COMPLETE
        assert first.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
        assert first.universe["semantic_membership"] == COMPLETENESS_COMPLETE
        assert len(first.universe["member_evidence_refs"]) == 5
        assert len(first.member_results) == 2
        assert _member_targets(world, first) == {"authorize", "authorizeRetry"}
        assert {item["result"] for item in first.member_results} == {MEMBER_SATISFIES}
        assert first.overall_truth == TRUTH_TRUE
        assert first.evaluation_receipt["model_invoked"] is False
        assert first.evaluation_receipt["repository_searched"] is False
        assert first.to_dict() == second.to_dict()
        restored = ScopedInvariantEvaluation.from_dict(first.to_dict())
        assert restored.to_dict() == first.to_dict()
        assert definition.to_dict()["definition_id"] == first.definition_id
        assert "overall_truth" not in definition.to_dict()
        assert first.evaluation_receipt["scoped_invoke_edge_count"] == 5
        assert first.evaluation_receipt["member_count"] == 2
        assert first.evaluation_receipt["circular_gateway_membership"] is False
        stripe = _callable(world, "chargeStripe")
        classification = next(
            item
            for item in first.evaluation_receipt["membership_classifications"]
            if item["entity"] == stripe
        )
        assert classification["status"] == MEMBERSHIP_IS_PROVIDER
        assert classification["basis"] == MEMBERSHIP_BASIS_DEFINITION
        assert classification["gateway_reachable"] is True
        assert first.evaluation_receipt["provider_membership_basis"] == [
            MEMBERSHIP_BASIS_DEFINITION
        ]
        assert first.evaluation_receipt["name_classified"] is False
        for member in first.member_results:
            assert member["endpoint_membership"]
            assert all(
                item["basis"] == MEMBERSHIP_BASIS_DEFINITION
                and item["status"] == MEMBERSHIP_IS_PROVIDER
                for item in member["endpoint_membership"]
            )
    finally:
        world.close()


def test_c1_discovers_bypass_independently_of_s0_receipt(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c1 = _open_spine(tmp_path, PAYMENT_C1, "c1")
    try:
        definition = _definition_for(s0)
        s0_result = evaluate_checkout_provider_boundary(s0, definition)
        c1_result = evaluate_checkout_provider_boundary(c1, definition)
        s0_targets = _member_targets(s0, s0_result)
        c1_targets = _member_targets(c1, c1_result)
        assert s0_targets == {"authorize", "authorizeRetry"}
        assert c1_targets == {"authorize", "authorizeRetry", "checkoutDirect"}
        bypass = next(
            item
            for item in c1_result.member_results
            if _labels(c1).get(str(item["origin_target"])) == "checkoutDirect"
        )
        assert bypass["result"] == MEMBER_VIOLATES
        assert bypass["mediation"] == "UNMEDIATED"
        assert c1_result.overall_truth == TRUTH_FALSE
        assert c1_result.universe["completeness"] == COMPLETENESS_COMPLETE
        s0_member_ids = {item["member_id"] for item in s0_result.member_results}
        assert bypass["member_id"] not in s0_member_ids
        s0_descriptors = {
            item["origin_target_descriptor"] for item in s0_result.member_results
        }
        assert bypass["origin_target_descriptor"] not in s0_descriptors
        assert c1_result.evaluation_receipt["model_invoked"] is False
        assert c1_result.snapshot_id != s0_result.snapshot_id
        assert c1_result.overall_truth != s0_result.overall_truth
        assert definition.definition_id == s0_result.definition_id == c1_result.definition_id
    finally:
        _close(s0, c1)


def test_c2_discovers_new_mediated_member_and_remains_true(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c2 = _open_spine(tmp_path, PAYMENT_C2, "c2")
    try:
        definition = _definition_for(s0)
        s0_result = evaluate_checkout_provider_boundary(s0, definition)
        c2_result = evaluate_checkout_provider_boundary(c2, definition)
        assert _member_targets(c2, c2_result) == {
            "authorize",
            "authorizeRetry",
            "checkoutWallet",
        }
        added = next(
            item
            for item in c2_result.member_results
            if _labels(c2).get(str(item["origin_target"])) == "checkoutWallet"
        )
        assert added["result"] == MEMBER_SATISFIES
        assert added["mediation"] == "MEDIATED"
        assert c2_result.universe["completeness"] == COMPLETENESS_COMPLETE
        assert c2_result.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
        assert c2_result.universe["semantic_membership"] == COMPLETENESS_COMPLETE
        assert c2_result.overall_truth == TRUTH_TRUE
        assert added["member_id"] not in {
            item["member_id"] for item in s0_result.member_results
        }
        assert c2_result.evaluation_receipt["model_invoked"] is False
    finally:
        _close(s0, c2)


def test_incomplete_universe_without_violation_is_unknown(tmp_path):
    world = _open_spine(tmp_path, PAYMENT_INCOMPLETE, "incomplete")
    try:
        result = evaluate_checkout_provider_boundary(world, _definition_for(world))
        assert result.universe["structural_enumeration"] in {
            COMPLETENESS_INCOMPLETE,
            "UNKNOWN",
        }
        assert MEMBER_VIOLATES not in {item["result"] for item in result.member_results}
        assert result.overall_truth == TRUTH_UNKNOWN
        assert result.evaluation_receipt["model_invoked"] is False
    finally:
        world.close()


def test_incomplete_universe_with_known_violation_is_false(tmp_path):
    world = _open_spine(tmp_path, PAYMENT_INCOMPLETE_VIOLATION, "incomplete-violation")
    try:
        result = evaluate_checkout_provider_boundary(world, _definition_for(world))
        assert result.universe["structural_enumeration"] in {
            COMPLETENESS_INCOMPLETE,
            "UNKNOWN",
        }
        assert any(item["result"] == MEMBER_VIOLATES for item in result.member_results)
        assert result.overall_truth == TRUTH_FALSE
    finally:
        world.close()


def test_unknown_member_without_violation_is_unknown(tmp_path):
    world = _open_spine(tmp_path, PAYMENT_UNKNOWN_MEMBER, "unknown-member")
    try:
        result = evaluate_checkout_provider_boundary(world, _definition_for(world))
        assert any(item["result"] == MEMBER_UNKNOWN for item in result.member_results)
        assert MEMBER_VIOLATES not in {item["result"] for item in result.member_results}
        assert result.overall_truth == TRUTH_UNKNOWN
    finally:
        world.close()


def test_evaluation_does_not_use_prior_snapshot_or_repository_search(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c1 = _open_spine(tmp_path, PAYMENT_C1, "c1")
    try:
        definition = _definition_for(s0)
        isolated = evaluate_checkout_provider_boundary(c1, definition)
        assert isolated.evaluation_receipt["repository_searched"] is False
        assert isolated.evaluation_receipt["model_invoked"] is False
        assert isolated.evaluation_receipt["inputs"]["relations"] == [
            "program_invokes",
            "structural_context",
            "program_entity_kind",
        ]
        assert "overall_truth" not in definition.to_dict()
        assert isolated.universe["snapshot_id"] == snapshot_id(c1)
        assert isolated.universe["snapshot_id"] != snapshot_id(s0)
    finally:
        _close(s0, c1)


def test_structural_completeness_is_distinct_from_semantic_membership(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        result = evaluate_checkout_provider_boundary(c3, _definition_for(s0))
        assert result.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
        assert result.universe["semantic_membership"] != COMPLETENESS_COMPLETE
        assert result.universe["completeness"] != COMPLETENESS_COMPLETE
        assert result.evaluation_receipt["circular_gateway_membership"] is False
        assert result.evaluation_receipt["historical_finding"] == HISTORICAL_UNSOUND_FINDING
        assert result.evaluation_receipt["name_classified"] is False
        assert result.evaluation_receipt["model_invoked"] is False
        assert result.evaluation_receipt["repository_searched"] is False
        unknown = [
            item
            for item in result.evaluation_receipt["membership_classifications"]
            if item["status"] == MEMBERSHIP_UNKNOWN
        ]
        assert unknown
        assert all(item["basis"] == MEMBERSHIP_BASIS_ABSENT for item in unknown)
        assert all(item["status"] != "IS_NOT_PROVIDER" for item in unknown)
        stripe = next(
            item
            for item in result.evaluation_receipt["membership_classifications"]
            if item["basis"] == MEMBERSHIP_BASIS_DEFINITION
        )
        assert stripe["status"] == MEMBERSHIP_IS_PROVIDER
        assert stripe["gateway_reachable"] is True
        gateway_labels = {
            _labels(c3).get(entity, "")
            for entity in result.evaluation_receipt["gateway_reachable_ids"]
        }
        assert "settleExternal" not in gateway_labels
        assert "chargeStripe" in gateway_labels
        settle = _callable(c3, "settleExternal")
        circular_provider_ids = set(result.evaluation_receipt["gateway_reachable_ids"])
        assert settle not in circular_provider_ids
        circular_member_targets = {
            _labels(c3).get(str(item["origin_target"]), "")
            for item in result.member_results
            if any(
                endpoint["entity"] in circular_provider_ids
                for endpoint in item.get("endpoint_membership") or ()
            )
        }
        assert circular_member_targets == {"authorize", "authorizeRetry"}
        assert "checkoutAlternative" not in circular_member_targets
    finally:
        _close(s0, c3)


def test_c3_unknown_membership_prevents_false_true(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        result = evaluate_checkout_provider_boundary(c3, _definition_for(s0))
        assert "checkoutAlternative" in _member_targets(c3, result)
        added = next(
            item
            for item in result.member_results
            if _labels(c3).get(str(item["origin_target"])) == "checkoutAlternative"
        )
        assert added["result"] == MEMBER_UNKNOWN
        assert added["endpoint_membership"]
        assert all(
            item["status"] == MEMBERSHIP_UNKNOWN
            for item in added["endpoint_membership"]
        )
        assert MEMBER_VIOLATES not in {item["result"] for item in result.member_results}
        assert result.overall_truth == TRUTH_UNKNOWN
        assert result.overall_truth != TRUTH_TRUE
        assert "Provider" not in _labels(c3).get(added["origin_target"], "")
        assert "Provider" not in "".join(
            item.get("descriptor", "") for item in added["endpoint_membership"]
        )
    finally:
        _close(s0, c3)


def test_c3_independently_known_provider_bypass_is_false(tmp_path):
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        result = evaluate_checkout_provider_boundary(
            c3, _definition_for(c3, extra_provider_labels=("settleExternal",))
        )
        assert result.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
        assert result.universe["semantic_membership"] == COMPLETENESS_COMPLETE
        added = next(
            item
            for item in result.member_results
            if _labels(c3).get(str(item["origin_target"])) == "checkoutAlternative"
        )
        assert added["result"] == MEMBER_VIOLATES
        assert result.overall_truth == TRUTH_FALSE
        assert result.evaluation_receipt["circular_gateway_membership"] is False
        settle = _callable(c3, "settleExternal")
        assert settle not in result.evaluation_receipt["gateway_reachable_ids"]
        assert settle in result.evaluation_receipt["independent_provider_ids"]
        settle_row = next(
            item
            for item in result.evaluation_receipt["membership_classifications"]
            if item["entity"] == settle
        )
        assert settle_row["status"] == MEMBERSHIP_IS_PROVIDER
        assert settle_row["basis"] == MEMBERSHIP_BASIS_DEFINITION
        assert settle_row["gateway_reachable"] is False
        assert all(
            item["basis"] == MEMBERSHIP_BASIS_DEFINITION
            for item in added["endpoint_membership"]
            if item["entity"] == settle
        )
    finally:
        c3.close()


def test_c4_unknown_endpoint_is_open_world_unknown(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c4 = _open_spine(tmp_path, PAYMENT_C4, "c4")
    try:
        result = evaluate_checkout_provider_boundary(c4, _definition_for(s0))
        assert result.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
        assert result.universe["semantic_membership"] != COMPLETENESS_COMPLETE
        assert "recordAudit" in _member_targets(c4, result)
        added = next(
            item
            for item in result.member_results
            if _labels(c4).get(str(item["origin_target"])) == "recordAudit"
        )
        assert added["result"] == MEMBER_UNKNOWN
        assert MEMBER_VIOLATES not in {item["result"] for item in result.member_results}
        assert result.overall_truth == TRUTH_UNKNOWN
        assert result.evaluation_receipt["model_invoked"] is False
        assert result.evaluation_receipt["name_classified"] is False
    finally:
        _close(s0, c4)


def test_known_violation_wins_over_unknown_membership(tmp_path):
    world = _open_spine(tmp_path, PAYMENT_INCOMPLETE_VIOLATION, "incomplete-violation")
    try:
        result = evaluate_checkout_provider_boundary(world, _definition_for(world))
        assert result.universe["structural_enumeration"] != COMPLETENESS_COMPLETE
        assert any(item["result"] == MEMBER_VIOLATES for item in result.member_results)
        assert result.overall_truth == TRUTH_FALSE
    finally:
        world.close()


def test_no_independent_provider_identities_cannot_claim_true(tmp_path):
    world = _open_spine(tmp_path, PAYMENT_S0, "s0")
    try:
        checkout = _callable(world, "checkout")
        gateway = _callable(world, "throughGateway")
        definition = ScopedInvariantDefinition(
            definition_id="invariant:checkout-provider-boundary",
            authority_refs=("obs:payment-universal",),
            access_semantic="semantic:CheckoutProviderAccess",
            boundary_semantic="semantic:PaymentGatewayBoundary",
            scope_root=checkout,
            scope_root_descriptor=_descriptor(world, checkout),
            boundary_program=gateway,
            boundary_program_descriptor=_descriptor(world, gateway),
            snapshot_id=snapshot_id(world),
        )
        result = evaluate_checkout_provider_boundary(world, definition)
        assert result.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
        assert result.universe["semantic_membership"] != COMPLETENESS_COMPLETE
        assert result.overall_truth != TRUTH_TRUE
        assert all(
            item["basis"] != "GATEWAY_REACHABILITY_CIRCULAR"
            for item in result.evaluation_receipt["membership_classifications"]
        )
    finally:
        world.close()


def _build_authority(ctor) -> None:
    source = ctor.source("docs/payment-boundary-universal.md")
    observation = source.observe(source.paragraphs()[0])
    checkout = ctor.program_entities(kind="callable", label="checkout")
    assert len(checkout) == 1
    ctor.create_semantic_referent(
        "semantic:CheckoutProviderAccess",
        label="Checkout provider access universe",
        observations=(observation,),
    )
    ctor.create_semantic_referent(
        "semantic:PaymentGatewayBoundary",
        label="PaymentGateway boundary",
        observations=(observation,),
    )
    ctor.persist_claim(
        "payment_provider_access_scope",
        {
            "access": "semantic:CheckoutProviderAccess",
            "boundary": "semantic:PaymentGatewayBoundary",
            "program": checkout[0],
        },
        claim_kind=ClaimKind.SEMANTIC_PROGRAM,
        support=RelationSupport.CROSS_EVIDENCE_INFERRED,
        endpoint_resolution={
            "access": ReferentResolution.AGENT_RESOLVED,
            "boundary": ReferentResolution.AGENT_RESOLVED,
            "program": ReferentResolution.DETERMINISTIC,
        },
        observations=(observation,),
        roles=[
            Role("access", RoleType.REFERENT),
            Role("boundary", RoleType.REFERENT),
            Role("program", RoleType.REFERENT),
        ],
        warrant=[
            {
                "program_entity": checkout[0],
                "structural_context": ctor.structural_context(checkout[0]),
                "justifying_program_relations": [
                    {
                        "relation": "program_invokes",
                        "call_site": str(row["call_site"]),
                        "target": str(row["target"]),
                    }
                    for row in ctor.world.relation_rows("program_invokes")
                ],
                "justifying_resolution_outcomes": [],
                "relation_support": RelationSupport.CROSS_EVIDENCE_INFERRED.value,
                "endpoint_resolution": {
                    "program": ReferentResolution.DETERMINISTIC.value
                },
            }
        ],
    )
    ctor.declare_attachment_universe([checkout[0]], observation=observation)
    ctor.record_completeness(
        scope=CompletenessScope.ADDRESSABILITY,
        universe="authority_source",
        status=CompletenessStatus.COMPLETE,
        basis="declared universal payment source is reconstructible",
    )
    ctor.record_completeness(
        scope=CompletenessScope.ATTACHMENT,
        universe="authority_attachment_scope",
        status=CompletenessStatus.COMPLETE,
        basis=(
            "attachment construction is complete for the declared universal "
            "purpose payment-provider-universal-v1 under profile "
            "payment-authority-universal-v0"
        ),
    )


def test_governance_case_consumes_derivation_as_mechanical_evidence(tmp_path):
    _write(
        tmp_path,
        {"docs/payment-boundary-universal.md": AUTHORITY_TEXT + "\n"},
    )
    _spine(tmp_path, PAYMENT_S0, "baseline-spine")
    constructed = construct_authority_world(
        tmp_path / "baseline-spine",
        tmp_path / "baseline-world",
        AuthorityUniverse(
            universe_id="payment-provider-boundary-evaluator-v1",
            workspace=tmp_path,
            sources=(
                DeclaredSource(
                    "docs/payment-boundary-universal.md",
                    tmp_path / "docs/payment-boundary-universal.md",
                    SourceStanding.AUTHORITATIVE,
                ),
            ),
        ),
        _build_authority,
        construction_id="payment-provider-boundary-evaluator-construction-v1",
        purpose="payment-provider-universal-v1",
        profile="payment-authority-universal-v0",
    )
    assert constructed.succeeded, constructed.errors
    _spine(tmp_path, PAYMENT_C1, "candidate-spine")
    comparison = compare_program_spines(
        tmp_path / "baseline-spine", tmp_path / "candidate-spine"
    )
    old = ConstructionWorld.open(tmp_path / "baseline-world" / "world.sqlite", read_only=True)
    new = ConstructionWorld.open(tmp_path / "candidate-spine" / "world.sqlite", read_only=True)
    try:
        definition = _definition_for(old)
        baseline = evaluate_checkout_provider_boundary(old, definition)
        candidate = evaluate_checkout_provider_boundary(new, definition)
        maintenance = assess_attachment_maintenance(old, new, comparison)
        impact = assess_authority_change_impact(
            old, new, comparison, maintenance=maintenance
        )
        case = assemble_governance_case(
            old,
            new,
            comparison,
            {
                "docs/payment-boundary-universal.md": MarkdownSource(
                    tmp_path / "docs/payment-boundary-universal.md",
                    handle="docs/payment-boundary-universal.md",
                )
            },
            maintenance=maintenance,
            impact=impact,
            purpose="payment-provider-universal-v1",
            invariant_definition=definition.to_dict(),
            baseline_invariant_derivation=baseline.to_dict(),
            candidate_invariant_derivation=candidate.to_dict(),
        )
        assert (
            validate_case_sidecar(
                case, maintenance=maintenance, impact=impact, comparison=comparison
            )
            == []
        )
        context = case["invariant_context"]
        assert context["definition"]["definition_id"] == definition.definition_id
        assert context["baseline_derivation"]["overall_truth"] == TRUTH_TRUE
        assert context["candidate_derivation"]["overall_truth"] == TRUTH_FALSE
        assert context["preferred_candidate_truth_artifact"] == "candidate_derivation"
        catalog = build_case_evidence_catalog(case)
        mechanical_ids = {
            item["id"]
            for item in catalog["entries"]
            if item["category"] == "MECHANICAL_PROGRAM_FACT"
        }
        violating = next(
            item
            for item in candidate.member_results
            if item["result"] == MEMBER_VIOLATES
        )
        assert set(violating["evidence_refs"]).issubset(mechanical_ids)
        program_finding = {
            "proposition": (
                "Current Checkout provider-access membership includes an "
                "unmediated path to the provider."
            ),
            "truth_value": "FALSE",
            "basis": "MECHANICAL",
            "heuristic_dependence": "NOT_MATERIAL",
            "finding_context": "SUFFICIENT",
            "evidence_refs": [
                {"kind": "relation_tuple", "id": evidence_id}
                for evidence_id in violating["evidence_refs"]
            ],
        }
        finding = create_governance_adjudication(
            case,
            adjudicator={
                "kind": "DETERMINISTIC_CHECK",
                "identity": "checkout-provider-boundary-observation",
            },
            program_findings=[program_finding],
            decision_right={
                "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
                "outcome": "NOT_ESTABLISHED",
                "rationale": (
                    "Observational check that the evaluator's FALSE result is "
                    "consumable as mechanical program evidence."
                ),
            },
            case_summary=(
                "Candidate derivation reports FALSE for checkout-provider-boundary/v1."
            ),
            validate=False,
        )
        errors = validate_governance_adjudication(finding, case)
        assert errors == []
        assert finding["program_findings"][0]["basis"] == "MECHANICAL"
        assert finding["program_findings"][0]["truth_value"] == "FALSE"
        assert candidate.evaluation_receipt["model_invoked"] is False
    finally:
        _close(old, new)


def test_existing_finite_receipt_regression_surface_is_untouched():
    from tests import test_semantic_persistence as realization
    from tests import test_semantic_universal_persistence as universal
    from tests import test_payment_semantic_persistence as relationship

    assert hasattr(realization, "test_grounded_candidate_with_inspectable_dependencies_is_commitment")
    assert hasattr(relationship, "test_payment_relationship_schema_and_controls_are_bounded")
    assert hasattr(universal, "test_complete_scoped_universe_and_finite_members_admit_commitment")
    assert hasattr(universal, "test_maintenance_contract_remains_zero_model_and_no_transfer")

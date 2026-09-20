"""Incremental semantic acquisition: one construction per cycle.

These tests do not rank obligations, batch model calls, or schedule work.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ontology_author.authority.evaluate import snapshot_id
from ontology_author.governance import (
    ConstructionExecutionPolicy,
    PreviousUnresolvedAttempt,
    advance_semantic_construction_cycle,
    approval_required_class_membership_policy,
    auto_allowed_class_membership_policy,
    select_canonical_obligation,
)
from ontology_author.governance.construction_cycle import (
    CANONICAL_SELECTION_NOTE,
    CYCLE_APPROVAL_REQUIRED,
    CYCLE_CONSTRUCTION_ATTEMPTED,
    CYCLE_DEFERRED,
    CYCLE_NO_CONSTRUCTION_REQUIRED,
    ELIGIBILITY_AUTO_EXECUTABLE,
    NEXT_ADJUDICATION,
    NEXT_CONSTRUCTION,
    classify_required_obligations,
)
from ontology_author.governance.construction_execution import (
    AUTHORITY_APPROVAL_REQUIRED,
    AUTHORITY_AUTO_ALLOWED,
    RESOURCE_AVAILABLE,
    RESOURCE_UNAVAILABLE,
    RESULT_CANDIDATE_PRODUCED,
    RESULT_EXECUTION_FAILED,
    RESULT_SEMANTICALLY_UNRESOLVED,
)
from ontology_author.governance.model_adjudicator import AdjudicatorTransportResponse
from ontology_author.semantic_binding import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_RELATION,
    class_membership_obligation,
)
from ontology_author.governance import (
    context_from_invariant_definition,
    evaluate_checkout_provider_boundary,
    invariant_context_for_case,
    pending_class_membership_obligations_from_derivation,
)
from ontology_author.governance.case_readiness import (
    STATUS_CONSTRUCTION_REQUIRED,
    STATUS_READY_FOR_ADJUDICATION,
)
from ontology_author.governance.checkout_invariant import TRUTH_FALSE, TRUTH_UNKNOWN
from ontology_author.semantic_binding.membership import PAYMENT_PROVIDER_CLASS
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_checkout_provider_boundary_evaluator import (
    PAYMENT_C3,
    PAYMENT_S0,
    _close,
    _definition_for,
    _labels,
    _open_spine,
)
from tests.test_class_membership_persistence import (
    AUTHORITY_HANDLE,
    AUTHORITY_TEXT,
    PAYMENT_C3B,
    _authority_world,
    _member_draft,
    _source_entry,
    _synthetic_case,
    _unresolved_draft,
)
from tests.test_governance_case_readiness import PAYMENT_FANOUT_WITH_VIOLATION
from tests.test_membership_gap_obligation_synthesis import PAYMENT_FANOUT

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

PAYMENT_FANOUT_MEDIATED = {
    **PAYMENT_S0,
    "src/payment-gateway.ts": (
        'import { chargeStripe } from "./stripe-client";\n'
        'import { endpointA } from "./leaf-a";\n'
        'import { endpointB } from "./leaf-b";\n'
        'import { endpointC } from "./leaf-c";\n'
        "export function throughGateway(): void { chargeStripe(); endpointA(); endpointB(); endpointC(); }\n"
    ),
    "src/leaf-a.ts": "export function endpointA(): void {}\n",
    "src/leaf-b.ts": "export function endpointB(): void {}\n",
    "src/leaf-c.ts": "export function endpointC(): void {}\n",
}


class _RecordingTransport:
    def __init__(self, payload_factory, *, error=None):
        self.payload_factory = payload_factory
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return AdjudicatorTransportResponse(payload=self.payload_factory(request))


def _pending(derivation, definition):
    return pending_class_membership_obligations_from_derivation(
        derivation, context_from_invariant_definition(definition)
    )


def _case_shell(definition, baseline, candidate, case_id="case:cycle"):
    return {
        "case_id": case_id,
        "contract": "governance_case/v0",
        "invariant_context": invariant_context_for_case(
            definition, baseline=baseline, candidate=candidate
        ),
        "assembly": {"completeness_basis": {"status": "COMPLETE", "known_gaps": []}},
    }


def _membership_rows(world: ConstructionWorld):
    try:
        return list(world.relation_rows(CLASS_MEMBERSHIP_RELATION))
    except Exception:
        return []


def _source_handle(world, files, obligation):
    subject = obligation.allowed_program_endpoints[0]
    label = _labels(world).get(subject, "")
    for handle, text in files.items():
        if label and f"function {label}(" in text:
            return handle, text
    raise AssertionError(f"no source file for {subject} ({label})")


def _construction_inputs(world, files, obligation):
    subject = obligation.allowed_program_endpoints[0]
    invoke = next(
        row
        for row in world.relation_rows("program_invokes")
        if str(row.get("target")) == subject
    )
    handle, text = _source_handle(world, files, obligation)
    case = _synthetic_case(subject, observation_id=obligation.authority_refs[0])
    case["program_context"]["relation_tuples"] = [
        {
            "evidence_id": "tuple:cycle-subject",
            "relation": "program_invokes",
            "recorded_fact": {
                "relation": "program_invokes",
                "call_site": str(invoke.get("call_site") or ""),
                "target": subject,
            },
        }
    ]
    return {
        "case": case,
        "bounded_program_source": [_source_entry(text, handle=handle)],
        "maintenance_dependencies": [
            {"kind": "program_identity", "program_entity": subject},
            {
                "kind": "relation_tuple",
                "recorded": {
                    "relation": "program_invokes",
                    "call_site": str(invoke.get("call_site") or ""),
                    "target": subject,
                },
                "evidence_id": "tuple:cycle-subject",
            },
            {
                "kind": "structural_context",
                "program_entity": subject,
                "chain": [subject],
            },
        ],
        "program_endpoint_kinds": {subject: "callable"},
    }


def _payload_transport(world, files, draft_fn):
    class Transport(_RecordingTransport):
        def __init__(self):
            super().__init__(self._draft)
            self.obligation = None

        def _draft(self, _request):
            from ontology_author.semantic_binding import build_semantic_construction_catalog
            inputs = _construction_inputs(world, files, self.obligation)
            catalog = build_semantic_construction_catalog(
                self.obligation,
                inputs["case"],
                bounded_program_source=inputs["bounded_program_source"],
                maintenance_dependencies=inputs["maintenance_dependencies"],
                program_endpoint_kinds=inputs["program_endpoint_kinds"],
            )
            return draft_fn(catalog)

    return Transport()


def _setup(tmp_path, files, name):
    s0 = _open_spine(tmp_path, PAYMENT_S0, f"{name}-s0")
    governed = _authority_world(tmp_path, files, name)
    definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
    baseline = evaluate_checkout_provider_boundary(s0, definition)
    candidate = evaluate_checkout_provider_boundary(governed, definition)
    pending = _pending(candidate, definition)
    case = _case_shell(definition, baseline, candidate, case_id=f"case:{name}")
    return {
        "s0": s0,
        "governed": governed,
        "definition": definition,
        "baseline": baseline,
        "candidate": candidate,
        "pending": pending,
        "case": case,
        "files": files,
        "source_by_handle": dict(files),
        "authority_by_handle": {AUTHORITY_HANDLE: AUTHORITY_TEXT},
        "material_basis": snapshot_id(governed),
    }


def _run_cycle(fixture, tmp_path, *, name, transport, policy=None, **kwargs):
    def inputs(obligation):
        transport.obligation = obligation
        return _construction_inputs(fixture["governed"], fixture["files"], obligation)

    return advance_semantic_construction_cycle(
        case=fixture["case"],
        derivation=fixture["candidate"],
        pending_obligations=fixture["pending"],
        policy=policy or auto_allowed_class_membership_policy(),
        resource_permission=kwargs.pop("resource_permission", RESOURCE_AVAILABLE),
        constructor=transport,
        construction_inputs=inputs,
        previous_unresolved=kwargs.pop("previous_unresolved", ()),
        material_basis=kwargs.pop("material_basis", fixture["material_basis"]),
        candidate_world=fixture["governed"],
        definition=fixture["definition"],
        baseline_derivation=fixture["baseline"],
        membership_source_by_handle=fixture["source_by_handle"],
        membership_authority_by_handle=fixture["authority_by_handle"],
        publication_dir=tmp_path / name,
        constructor_metadata={"provider": "fixture", "model": "deterministic"},
        **kwargs,
    )


def _obligation(obligation_id, subject):
    return class_membership_obligation(
        obligation_id=obligation_id,
        purpose="cycle-select",
        authority_refs=("obs:payment-universal",),
        semantic_class=PAYMENT_PROVIDER_CLASS,
        program_subject=subject,
        program_scope="checkout-payment-provider-membership",
    )


def test_canonical_selection_is_obligation_id_order_not_semantic_ranking():
    later = _obligation("construction-obligation:fff", "program:endpointA")
    earlier = _obligation("construction-obligation:aaa", "program:endpointZ")
    selected = select_canonical_obligation((later, earlier))
    assert selected.obligation_id == earlier.obligation_id
    assert selected.semantic_subject == PAYMENT_PROVIDER_CLASS
    assert "endpointA" not in selected.obligation_id
    assert "more important" in CANONICAL_SELECTION_NOTE
    assert select_canonical_obligation((later, earlier)).obligation_id == (
        select_canonical_obligation((earlier, later)).obligation_id
    )


def test_fanout_violating_first_makes_remaining_dormant(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-violate")
    transport = _payload_transport(fixture["governed"], PAYMENT_FANOUT, _member_draft)
    try:
        pending_ids = [item.obligation_id for item in fixture["pending"].obligations]
        assert len(pending_ids) == 3
        assert fixture["candidate"].overall_truth == TRUTH_UNKNOWN
        first_id = select_canonical_obligation(fixture["pending"].obligations).obligation_id
        before_snapshot = snapshot_id(fixture["governed"])
        s0_snapshot = snapshot_id(fixture["s0"])
        result = _run_cycle(fixture, tmp_path, name="g1-violate", transport=transport)
        assert result.status == CYCLE_CONSTRUCTION_ATTEMPTED
        assert result.selected_obligation_id == first_id
        assert result.constructor_attempts == 1
        assert len(transport.requests) == 1
        assert result.required_before == tuple(sorted(pending_ids)) or len(result.required_before) == 3
        assert len(result.required_before) == 3
        assert result.dormant_before == ()
        assert result.execution_result.status == RESULT_CANDIDATE_PRODUCED
        assert result.admission_result["outcome"] == "PERSIST_COMMITMENT"
        assert result.published_world_revision
        assert result.readiness_after["status"] == STATUS_READY_FOR_ADJUDICATION
        assert result.readiness_after["overall_truth"] == TRUTH_FALSE
        assert result.required_after == ()
        assert len(result.dormant_after) == 2
        assert first_id not in result.dormant_after
        assert set(result.dormant_after) <= set(result.pending_after) | set(result.dormant_after)
        remaining = set(result.required_before) - {first_id}
        assert set(result.dormant_after) == remaining
        assert result.next == NEXT_ADJUDICATION
        assert result.candidate_changed is False
        assert snapshot_id(fixture["governed"]) == before_snapshot
        assert snapshot_id(fixture["s0"]) == s0_snapshot
        assert PAYMENT_FANOUT["src/leaf-a.ts"] == "export function endpointA(): void {}\n"
        assert _membership_rows(fixture["governed"]) == []
        revised = ConstructionWorld.open(
            Path(result.published_world_revision) / fixture["governed"].path.name,
            read_only=True,
        )
        try:
            assert list(revised.relation_rows(CLASS_MEMBERSHIP_RELATION))
            assert snapshot_id(revised) == before_snapshot
        finally:
            revised.close()
        for item in fixture["pending"].obligations:
            if item.obligation_id in remaining:
                assert item.obligation_id in result.pending_after or item.obligation_id in result.dormant_after
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_fanout_satisfying_first_reduces_required_and_stops(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT_MEDIATED, "fanout-satisfy")
    transport = _payload_transport(
        fixture["governed"], PAYMENT_FANOUT_MEDIATED, _member_draft
    )
    try:
        assert len(fixture["pending"].obligations) == 3
        assert fixture["candidate"].overall_truth == TRUTH_UNKNOWN
        result = _run_cycle(fixture, tmp_path, name="g1-satisfy", transport=transport)
        assert result.constructor_attempts == 1
        assert len(result.required_before) == 3
        assert len(result.required_after) == 2
        assert result.selected_obligation_id not in result.required_after
        assert result.readiness_after["status"] == STATUS_CONSTRUCTION_REQUIRED
        assert result.readiness_after["overall_truth"] == TRUTH_UNKNOWN
        assert result.next == NEXT_CONSTRUCTION
        assert result.dormant_after == ()
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_second_explicit_cycle_can_choose_next(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT_MEDIATED, "fanout-second")
    transport = _payload_transport(
        fixture["governed"], PAYMENT_FANOUT_MEDIATED, _member_draft
    )
    try:
        first = _run_cycle(fixture, tmp_path, name="g1-second", transport=transport)
        assert first.constructor_attempts == 1
        assert len(first.required_after) == 2
        g1 = ConstructionWorld.open(
            Path(first.published_world_revision) / fixture["governed"].path.name,
            read_only=True,
        )
        try:
            after = evaluate_checkout_provider_boundary(
                fixture["governed"],
                fixture["definition"],
                membership_prior_world=g1,
                membership_source_by_handle=fixture["source_by_handle"],
                membership_authority_by_handle=fixture["authority_by_handle"],
            )
            pending = _pending(after, fixture["definition"])
            case = _case_shell(
                fixture["definition"], fixture["baseline"], after, case_id="case:second"
            )
            transport2 = _payload_transport(
                fixture["governed"], PAYMENT_FANOUT_MEDIATED, _member_draft
            )

            def inputs(obligation):
                transport2.obligation = obligation
                return _construction_inputs(
                    fixture["governed"], PAYMENT_FANOUT_MEDIATED, obligation
                )

            second = advance_semantic_construction_cycle(
                case=case,
                derivation=after,
                pending_obligations=pending,
                policy=auto_allowed_class_membership_policy(),
                constructor=transport2,
                construction_inputs=inputs,
                material_basis=snapshot_id(fixture["governed"]),
                candidate_world=fixture["governed"],
                definition=fixture["definition"],
                baseline_derivation=fixture["baseline"],
                membership_source_by_handle=fixture["source_by_handle"],
                membership_authority_by_handle=fixture["authority_by_handle"],
                publication_dir=tmp_path / "g2-second",
                governed_world=g1,
            )
            assert second.constructor_attempts == 1
            assert len(transport2.requests) == 1
            assert second.selected_obligation_id != first.selected_obligation_id
            assert len(second.required_before) == 2
            assert len(second.required_after) == 1
            assert first.constructor_attempts + second.constructor_attempts == 2
        finally:
            g1.close()
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_unresolved_stops_without_second_obligation(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-unresolved")
    transport = _payload_transport(
        fixture["governed"], PAYMENT_FANOUT, _unresolved_draft
    )
    try:
        result = _run_cycle(fixture, tmp_path, name="g1-unresolved", transport=transport)
        assert result.status == CYCLE_CONSTRUCTION_ATTEMPTED
        assert result.execution_result.status == RESULT_SEMANTICALLY_UNRESOLVED
        assert result.constructor_attempts == 1
        assert result.required_after == result.required_before
        assert result.published_world_revision == ""
        assert result.admission_result is None
        assert _membership_rows(fixture["governed"]) == []
        assert len(transport.requests) == 1
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_execution_failure_stops_without_fallback(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-fail")
    transport = _RecordingTransport(
        lambda _request: {"result": "NOT_A_VALID_RESULT"}
    )
    transport.obligation = None
    try:
        result = _run_cycle(fixture, tmp_path, name="g1-fail", transport=transport)
        assert result.execution_result.status == RESULT_EXECUTION_FAILED
        assert result.constructor_attempts == 1
        assert len(transport.requests) == 1
        assert result.required_after == result.required_before
        assert result.published_world_revision == ""
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_auto_allowed_proceeds_while_another_requires_approval(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-mixed")
    ordered = sorted(fixture["pending"].obligations, key=lambda item: item.obligation_id)
    approval_id = ordered[0].obligation_id
    auto_id = ordered[1].obligation_id
    policy = ConstructionExecutionPolicy(
        profile_authorities={
            CLASS_MEMBERSHIP_ADMISSION_PROFILE: AUTHORITY_APPROVAL_REQUIRED
        },
        obligation_authorities={auto_id: AUTHORITY_AUTO_ALLOWED},
    )
    transport = _payload_transport(fixture["governed"], PAYMENT_FANOUT, _member_draft)
    try:
        classified = classify_required_obligations(
            ordered,
            policy=policy,
        )
        auto = [
            item.obligation_id
            for item in classified
            if item.eligibility == ELIGIBILITY_AUTO_EXECUTABLE
        ]
        assert auto == [auto_id]
        result = _run_cycle(
            fixture, tmp_path, name="g1-mixed", transport=transport, policy=policy
        )
        assert result.selected_obligation_id == auto_id
        assert result.selected_obligation_id != approval_id
        assert result.constructor_attempts == 1
        assert result.required_after == ()
        assert approval_id in result.dormant_after
        assert result.next == NEXT_ADJUDICATION
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_all_approval_required_does_not_execute(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-approval")
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    transport.obligation = None
    try:
        result = _run_cycle(
            fixture,
            tmp_path,
            name="g1-approval",
            transport=transport,
            policy=approval_required_class_membership_policy(),
        )
        assert result.status == CYCLE_APPROVAL_REQUIRED
        assert result.constructor_attempts == 0
        assert transport.requests == []
        assert set(result.required_before) == {
            item.obligation_id for item in fixture["pending"].obligations
        }
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_all_deferred_does_not_execute(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-defer")
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    transport.obligation = None
    try:
        result = _run_cycle(
            fixture,
            tmp_path,
            name="g1-defer",
            transport=transport,
            resource_permission=RESOURCE_UNAVAILABLE,
        )
        assert result.status == CYCLE_DEFERRED
        assert result.constructor_attempts == 0
        assert transport.requests == []
        assert result.required_after == result.required_before
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_canonical_ordering_is_stable(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-stable")
    try:
        first = select_canonical_obligation(fixture["pending"].obligations)
        second = select_canonical_obligation(tuple(reversed(fixture["pending"].obligations)))
        assert first.obligation_id == second.obligation_id
        classified = classify_required_obligations(
            fixture["pending"].obligations,
            policy=auto_allowed_class_membership_policy(),
        )
        again = classify_required_obligations(
            tuple(reversed(fixture["pending"].obligations)),
            policy=auto_allowed_class_membership_policy(),
        )
        assert [item.obligation_id for item in classified] != [] 
        assert {item.obligation_id for item in classified} == {
            item.obligation_id for item in again
        }
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_prior_same_basis_unresolved_is_not_retried(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-prior")
    selected = select_canonical_obligation(fixture["pending"].obligations)
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    transport.obligation = None
    try:
        prior = PreviousUnresolvedAttempt(
            obligation_id=selected.obligation_id,
            construction_profile=CLASS_MEMBERSHIP_ADMISSION_PROFILE,
            material_basis=fixture["material_basis"],
        )
        result = _run_cycle(
            fixture,
            tmp_path,
            name="g1-prior",
            transport=transport,
            previous_unresolved=(prior,),
        )
        assert result.selected_obligation_id != selected.obligation_id
        assert result.constructor_attempts == 1
        assert result.selected_obligation_id in {
            item.obligation_id for item in fixture["pending"].obligations
        }
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_all_prior_unresolved_returns_deferred(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-all-prior")
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    transport.obligation = None
    try:
        prior = tuple(
            PreviousUnresolvedAttempt(
                obligation_id=item.obligation_id,
                construction_profile=item.admission_profile,
                material_basis=fixture["material_basis"],
            )
            for item in fixture["pending"].obligations
        )
        result = _run_cycle(
            fixture,
            tmp_path,
            name="g1-all-prior",
            transport=transport,
            previous_unresolved=prior,
        )
        assert result.status == CYCLE_DEFERRED
        assert result.constructor_attempts == 0
        assert transport.requests == []
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_changed_snapshot_obligation_is_a_new_question(tmp_path):
    c3 = _setup(tmp_path, PAYMENT_C3, "c3-basis")
    c3b_world = None
    try:
        c3_id = c3["pending"].obligations[0].obligation_id
        c3b_world = _authority_world(tmp_path, PAYMENT_C3B, "c3b-basis")
        candidate = evaluate_checkout_provider_boundary(c3b_world, c3["definition"])
        pending = _pending(candidate, c3["definition"])
        c3b_id = pending.obligations[0].obligation_id
        assert c3_id != c3b_id
        prior = PreviousUnresolvedAttempt(
            obligation_id=c3_id,
            construction_profile=CLASS_MEMBERSHIP_ADMISSION_PROFILE,
            material_basis=c3["material_basis"],
        )
        classified = classify_required_obligations(
            pending.obligations,
            policy=auto_allowed_class_membership_policy(),
            previous_unresolved=(prior,),
            material_basis=snapshot_id(c3b_world),
        )
        assert classified[0].eligibility == ELIGIBILITY_AUTO_EXECUTABLE
        assert classified[0].obligation_id == c3b_id
    finally:
        _close(c3["s0"], c3["governed"])
        if c3b_world is not None:
            c3b_world.close()


def test_known_violation_needs_no_construction_cycle(tmp_path):
    fixture = _setup(tmp_path, PAYMENT_FANOUT_WITH_VIOLATION, "fanout-ready")
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    transport.obligation = None
    try:
        result = _run_cycle(fixture, tmp_path, name="g1-ready", transport=transport)
        assert result.status == CYCLE_NO_CONSTRUCTION_REQUIRED
        assert result.constructor_attempts == 0
        assert transport.requests == []
        assert result.next == NEXT_ADJUDICATION
        assert result.readiness_before["status"] == STATUS_READY_FOR_ADJUDICATION
    finally:
        _close(fixture["s0"], fixture["governed"])

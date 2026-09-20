"""Minimal construction-execution approval lifecycle.

Approval authorizes one constructor attempt for one exact decision. It is not
semantic evidence, admission, or candidate-adoption approval.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ontology_author.authority.evaluate import snapshot_id
from ontology_author.governance import (
    ADOPTION_DECISION_SCHEMA,
    CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION,
    ConstructionExecutionApproval,
    ConstructionExecutionAuthorization,
    ConstructionExecutionNotAuthorized,
    advance_semantic_construction_cycle,
    approval_required_class_membership_policy,
    authorize_construction_execution,
    construction_execution_approval,
    decide_construction_execution,
    execute_construction_obligation,
)
from ontology_author.governance.candidate import CandidateAdoptionDecision
from ontology_author.governance.construction_approval import (
    APPROVAL_SCHEMA,
    APPROVAL_KIND,
    AUTHORIZATION_AUTHORIZED,
    AUTHORIZATION_DENIED,
    AUTHORIZATION_NOT_AUTHORIZED,
    REASON_APPROVAL_CONSUMED,
    REASON_DECISION_NOT_REQUIRE_APPROVAL,
    REASON_DENIED,
    REASON_DISALLOWED_CANNOT_BE_APPROVED,
    REASON_WRONG_CONSTRUCTOR,
    REASON_WRONG_DECISION,
    REASON_WRONG_OBLIGATION,
    REASON_WRONG_POLICY,
    execution_permitted,
)
from ontology_author.governance.construction_cycle import (
    CYCLE_APPROVAL_REQUIRED,
    CYCLE_CONSTRUCTION_ATTEMPTED,
    NEXT_ADJUDICATION,
)
from ontology_author.governance.construction_execution import (
    ACTION_DEFER,
    ACTION_EXECUTE,
    ACTION_REQUIRE_APPROVAL,
    AUTHORITY_APPROVAL_REQUIRED,
    AUTHORITY_DISALLOWED,
    CLASS_MEMBERSHIP_CONSTRUCTOR,
    POLICY_ID,
    POLICY_VERSION,
    RESOURCE_AVAILABLE,
    RESOURCE_UNAVAILABLE,
    RESULT_CANDIDATE_PRODUCED,
    RESULT_EXECUTION_FAILED,
    RESULT_SEMANTICALLY_UNRESOLVED,
    STATUS_DECIDED,
)
from ontology_author.semantic_binding import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_RELATION,
    admit_semantic_candidate,
    class_membership_obligation,
    materialize_semantic_commitment_revision,
)
from ontology_author.governance import (
    context_from_invariant_definition,
    evaluate_checkout_provider_boundary,
    pending_class_membership_obligations_from_derivation,
)
from ontology_author.governance.case_readiness import (
    STATUS_READY_FOR_ADJUDICATION,
    assess_governance_case_readiness,
)
from ontology_author.governance.checkout_invariant import TRUTH_FALSE
from ontology_author.semantic_binding.membership import PAYMENT_PROVIDER_CLASS
from tests.test_checkout_provider_boundary_evaluator import PAYMENT_C3, _callable, _close
from tests.test_class_membership_persistence import (
    AUTHORITY_HANDLE,
    AUTHORITY_TEXT,
    PAYMENT_C3B,
    _authority_world,
    _member_draft,
    _unresolved_draft,
)
from tests.test_construction_execution_policy import (
    _RecordingTransport,
    _c3_required,
    _case_shell,
    _construction_inputs,
    _evaluate,
    _fixture_adjudication,
    _membership_rows,
    required_obligations_for_execution,
)
from tests.test_membership_gap_obligation_synthesis import PAYMENT_FANOUT
from tests.test_semantic_construction_cycle import (
    _construction_inputs as _cycle_inputs,
    _payload_transport,
    _setup,
)
from ontology_author.world.runtime.world import ConstructionWorld

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


def _obligation(obligation_id="obligation:c3"):
    return class_membership_obligation(
        obligation_id=obligation_id,
        purpose="payment-provider-class-membership-v0",
        authority_refs=("obs:payment-universal",),
        semantic_class=PAYMENT_PROVIDER_CLASS,
        program_subject="program:settleExternal",
        program_scope="checkout-payment-provider-membership",
    )


def _synthetic_decision(**overrides):
    payload = {
        "status": STATUS_DECIDED,
        "action": ACTION_REQUIRE_APPROVAL,
        "obligation_id": "obligation:c3",
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "reason": "EXECUTION_AUTHORITY_REQUIRES_APPROVAL",
        "construction_profile": CLASS_MEMBERSHIP_ADMISSION_PROFILE,
        "execution_authority": AUTHORITY_APPROVAL_REQUIRED,
        "resource_permission": RESOURCE_AVAILABLE,
        "constructor_id": CLASS_MEMBERSHIP_CONSTRUCTOR,
        "required_obligation_ids": ("obligation:c3",),
    }
    payload.update(overrides)
    from ontology_author.governance.construction_execution import (
        ConstructionExecutionDecision,
    )

    return ConstructionExecutionDecision(**payload)


def _blob(request) -> str:
    return json.dumps(
        {
            "case": getattr(request, "case_json", ""),
            "instruction": getattr(request, "instruction", ""),
            "schema": getattr(request, "output_schema", {}),
        },
        default=str,
    ).lower()


def test_approval_is_not_candidate_adoption_approval():
    decision = _synthetic_decision()
    approval = construction_execution_approval(decision)
    assert approval.kind == APPROVAL_KIND
    assert approval.contract == APPROVAL_SCHEMA
    assert approval.contract != ADOPTION_DECISION_SCHEMA
    assert approval.kind != "CANDIDATE_ADOPTION_APPROVAL"
    assert "ConstructionExecutionApproval" == type(approval).__name__
    assert type(approval) is not CandidateAdoptionDecision


def test_c3_require_approval_does_not_invoke_constructor(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        decision = decide_construction_execution(
            fixture["required"],
            policy=approval_required_class_membership_policy(),
        )
        assert decision.action == ACTION_REQUIRE_APPROVAL
        assert decision.constructor_invoked is False
        transport = _RecordingTransport(
            lambda _request: (_ for _ in ()).throw(AssertionError("constructor"))
        )
        with pytest.raises(ConstructionExecutionNotAuthorized):
            execute_construction_obligation(
                fixture["obligation"],
                decision,
                constructor=transport,
                case=_construction_inputs(fixture["c3"], PAYMENT_C3, fixture["obligation"])[
                    "case"
                ],
            )
        assert transport.requests == []
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_matching_approved_artifact_authorizes_without_constructor():
    decision = _synthetic_decision()
    approval = construction_execution_approval(decision)
    authorization = authorize_construction_execution(decision, approval)
    assert authorization.status == AUTHORIZATION_AUTHORIZED
    assert authorization.obligation_id == decision.obligation_id
    assert authorization.execution_decision_id == decision.decision_id
    assert authorization.approval_id == approval.approval_id
    assert authorization.max_attempts == 1
    assert decision.action == ACTION_REQUIRE_APPROVAL


def test_denied_blocks_execution():
    decision = _synthetic_decision()
    approval = construction_execution_approval(decision, outcome="DENIED")
    authorization = authorize_construction_execution(decision, approval)
    assert authorization.status == AUTHORIZATION_DENIED
    assert authorization.reason == REASON_DENIED
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    with pytest.raises(ConstructionExecutionNotAuthorized) as exc:
        execute_construction_obligation(
            _obligation(),
            decision,
            constructor=transport,
            case={"case_id": "case:x"},
            execution_authorization=authorization,
        )
    assert exc.value.reason == REASON_DENIED
    assert transport.requests == []


def test_defer_cannot_be_overridden_by_approval():
    decision = _synthetic_decision(
        action=ACTION_DEFER,
        execution_authority="AUTO_ALLOWED",
        resource_permission=RESOURCE_UNAVAILABLE,
        reason="RESOURCE_PERMISSION_UNAVAILABLE",
    )
    approval = construction_execution_approval(decision)
    authorization = authorize_construction_execution(decision, approval)
    assert authorization.status == AUTHORIZATION_NOT_AUTHORIZED
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    forged = ConstructionExecutionAuthorization(
        status=AUTHORIZATION_AUTHORIZED,
        obligation_id=decision.obligation_id,
        execution_decision_id=decision.decision_id,
        approval_id=approval.approval_id,
        constructor_id=decision.constructor_id,
        reason="forged",
    )
    with pytest.raises(ConstructionExecutionNotAuthorized):
        execute_construction_obligation(
            _obligation(),
            decision,
            constructor=transport,
            case={"case_id": "case:x"},
            execution_authorization=forged,
        )
    assert transport.requests == []


def test_execute_decision_does_not_need_approval():
    decision = _synthetic_decision(
        action=ACTION_EXECUTE,
        execution_authority="AUTO_ALLOWED",
        reason="EXECUTION_AUTHORITY_AUTO_ALLOWED",
    )
    approval = construction_execution_approval(decision)
    authorization = authorize_construction_execution(decision, approval)
    assert authorization.status == AUTHORIZATION_NOT_AUTHORIZED
    assert authorization.reason == REASON_DECISION_NOT_REQUIRE_APPROVAL
    permitted, _reason = execution_permitted(decision, decision.obligation_id, None)
    assert permitted is True


def test_disallowed_cannot_be_overridden_by_approval():
    decision = _synthetic_decision(
        action=ACTION_DEFER,
        execution_authority=AUTHORITY_DISALLOWED,
        reason="CONSTRUCTION_DISALLOWED",
    )
    approval = construction_execution_approval(decision)
    authorization = authorize_construction_execution(decision, approval)
    assert authorization.status == AUTHORIZATION_NOT_AUTHORIZED
    assert authorization.reason == REASON_DISALLOWED_CANNOT_BE_APPROVED
    forged_decision = _synthetic_decision(
        action=ACTION_REQUIRE_APPROVAL,
        execution_authority=AUTHORITY_DISALLOWED,
        reason="CONSTRUCTION_DISALLOWED",
    )
    forged_approval = construction_execution_approval(forged_decision)
    forged_authorization = authorize_construction_execution(
        forged_decision, forged_approval
    )
    assert forged_authorization.status == AUTHORIZATION_NOT_AUTHORIZED
    assert forged_authorization.reason == REASON_DISALLOWED_CANNOT_BE_APPROVED
    transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
    with pytest.raises(ConstructionExecutionNotAuthorized):
        execute_construction_obligation(
            _obligation(),
            forged_decision,
            constructor=transport,
            case={"case_id": "case:x"},
            execution_authorization=ConstructionExecutionAuthorization(
                status=AUTHORIZATION_AUTHORIZED,
                obligation_id=forged_decision.obligation_id,
                execution_decision_id=forged_decision.decision_id,
                approval_id=forged_approval.approval_id,
                constructor_id=forged_decision.constructor_id,
                reason="forged",
            ),
        )
    assert transport.requests == []


def test_mismatched_approvals_are_rejected():
    decision = _synthetic_decision()
    cases = [
        ({"obligation_id": "obligation:other"}, REASON_WRONG_OBLIGATION),
        ({"execution_decision_id": "construction-execution-decision:deadbeef"}, REASON_WRONG_DECISION),
        ({"policy_version": "v-other"}, REASON_WRONG_POLICY),
        ({"constructor_id": "other-constructor"}, REASON_WRONG_CONSTRUCTOR),
    ]
    for overrides, reason in cases:
        approval = construction_execution_approval(decision, **overrides)
        authorization = authorize_construction_execution(decision, approval)
        assert authorization.status == AUTHORIZATION_NOT_AUTHORIZED
        assert authorization.reason == reason


def test_c3_approved_authorization_allows_exactly_one_execution(tmp_path):
    fixture = _c3_required(tmp_path)
    try:
        obligation = fixture["obligation"]
        decision = decide_construction_execution(
            fixture["required"],
            policy=approval_required_class_membership_policy(),
        )
        assert decision.action == ACTION_REQUIRE_APPROVAL
        approval = construction_execution_approval(decision)
        authorization = authorize_construction_execution(decision, approval)
        assert authorization.status == AUTHORIZATION_AUTHORIZED
        inputs = _construction_inputs(fixture["c3"], PAYMENT_C3, obligation)

        def _payload(_request):
            from ontology_author.semantic_binding import build_semantic_construction_catalog
            catalog = build_semantic_construction_catalog(
                obligation,
                inputs["case"],
                bounded_program_source=inputs["bounded_program_source"],
                maintenance_dependencies=inputs["maintenance_dependencies"],
                program_endpoint_kinds=inputs["program_endpoint_kinds"],
            )
            return _member_draft(catalog)

        transport = _RecordingTransport(_payload)
        result = execute_construction_obligation(
            obligation,
            decision,
            constructor=transport,
            case=inputs["case"],
            bounded_program_source=inputs["bounded_program_source"],
            maintenance_dependencies=inputs["maintenance_dependencies"],
            program_endpoint_kinds=inputs["program_endpoint_kinds"],
            execution_authorization=authorization,
        )
        assert result.status == RESULT_CANDIDATE_PRODUCED
        assert result.invocation_count == 1
        assert result.consumed_approval_id == approval.approval_id
        blob = _blob(transport.requests[0])
        assert "human approved" not in blob
        assert approval.approval_id.lower() not in blob
        assert "construction_execution_approval" not in blob
        consumed = authorize_construction_execution(
            decision, approval, consumed_approval_ids=(approval.approval_id,)
        )
        assert consumed.status == AUTHORIZATION_NOT_AUTHORIZED
        assert consumed.reason == REASON_APPROVAL_CONSUMED
        with pytest.raises(ConstructionExecutionNotAuthorized):
            execute_construction_obligation(
                obligation,
                decision,
                constructor=transport,
                case=inputs["case"],
                bounded_program_source=inputs["bounded_program_source"],
                maintenance_dependencies=inputs["maintenance_dependencies"],
                program_endpoint_kinds=inputs["program_endpoint_kinds"],
                execution_authorization=authorization,
                consumed_approval_ids=(approval.approval_id,),
            )
        assert len(transport.requests) == 1
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_c3_denied_leaves_world_and_candidate_unchanged(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        decision = decide_construction_execution(
            fixture["required"],
            policy=approval_required_class_membership_policy(),
        )
        approval = construction_execution_approval(decision, outcome="DENIED")
        authorization = authorize_construction_execution(decision, approval)
        assert authorization.status == AUTHORIZATION_DENIED
        before = snapshot_id(fixture["c3"])
        transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
        with pytest.raises(ConstructionExecutionNotAuthorized):
            execute_construction_obligation(
                fixture["obligation"],
                decision,
                constructor=transport,
                case=_construction_inputs(fixture["c3"], PAYMENT_C3, fixture["obligation"])[
                    "case"
                ],
                execution_authorization=authorization,
            )
        assert transport.requests == []
        assert snapshot_id(fixture["c3"]) == before
        assert _membership_rows(fixture["c3"]) == []
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        assert (
            fixture["lifecycle"].adoption_decision["context_requirement"]["kind"]
            == CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        )
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_approved_unresolved_and_failure_keep_live_semantics(tmp_path):
    fixture = _c3_required(tmp_path)
    try:
        obligation = fixture["obligation"]
        decision = decide_construction_execution(
            fixture["required"],
            policy=approval_required_class_membership_policy(),
        )
        inputs = _construction_inputs(fixture["c3"], PAYMENT_C3, obligation)

        def _run(draft_fn):
            approval = construction_execution_approval(decision)
            authorization = authorize_construction_execution(decision, approval)

            def _payload(_request):
                from ontology_author.semantic_binding import build_semantic_construction_catalog
                catalog = build_semantic_construction_catalog(
                    obligation,
                    inputs["case"],
                    bounded_program_source=inputs["bounded_program_source"],
                    maintenance_dependencies=inputs["maintenance_dependencies"],
                    program_endpoint_kinds=inputs["program_endpoint_kinds"],
                )
                return draft_fn(catalog)

            transport = _RecordingTransport(_payload)
            return execute_construction_obligation(
                obligation,
                decision,
                constructor=transport,
                case=inputs["case"],
                bounded_program_source=inputs["bounded_program_source"],
                maintenance_dependencies=inputs["maintenance_dependencies"],
                program_endpoint_kinds=inputs["program_endpoint_kinds"],
                execution_authorization=authorization,
            ), transport

        unresolved, transport_u = _run(_unresolved_draft)
        assert unresolved.status == RESULT_SEMANTICALLY_UNRESOLVED
        assert unresolved.invocation_count == 1
        failed, transport_f = _run(lambda _catalog: {"result": "NOT_A_VALID_RESULT"})
        assert failed.status == RESULT_EXECUTION_FAILED
        assert failed.invocation_count == 1
        assert len(transport_u.requests) == 1
        assert len(transport_f.requests) == 1
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_c3_approved_member_still_requires_admission_and_publication(tmp_path):
    from ontology_author.semantic_binding.membership import (
        MEMBERSHIP_STATUS_ESTABLISHED,
        MEMBERSHIP_STATUS_PRESERVED,
        PAYMENT_PROVIDER_CLASS,
    )
    from ontology_author.semantic_binding import lookup_class_membership_evidence
    from tests.test_checkout_provider_boundary_evaluator import (
        PAYMENT_S0,
        _definition_for,
        _open_spine,
    )

    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        before = evaluate_checkout_provider_boundary(governed, definition)
        first, pending_before, _case = _evaluate(
            definition, baseline, before, case_id="case:c3-g0"
        )
        required = required_obligations_for_execution(pending_before, first.readiness)
        g0_snapshot = snapshot_id(governed)
        s0_snapshot = snapshot_id(s0)
        decision = decide_construction_execution(
            required, policy=approval_required_class_membership_policy()
        )
        assert decision.action == ACTION_REQUIRE_APPROVAL
        approval = construction_execution_approval(decision)
        authorization = authorize_construction_execution(decision, approval)
        inputs = _construction_inputs(governed, PAYMENT_C3, required[0])

        def _payload(_request):
            from ontology_author.semantic_binding import build_semantic_construction_catalog
            catalog = build_semantic_construction_catalog(
                required[0],
                inputs["case"],
                bounded_program_source=inputs["bounded_program_source"],
                maintenance_dependencies=inputs["maintenance_dependencies"],
                program_endpoint_kinds=inputs["program_endpoint_kinds"],
            )
            return _member_draft(catalog)

        transport = _RecordingTransport(_payload)
        executed = execute_construction_obligation(
            required[0],
            decision,
            constructor=transport,
            case=inputs["case"],
            bounded_program_source=inputs["bounded_program_source"],
            maintenance_dependencies=inputs["maintenance_dependencies"],
            program_endpoint_kinds=inputs["program_endpoint_kinds"],
            execution_authorization=authorization,
        )
        assert executed.status == RESULT_CANDIDATE_PRODUCED
        assert executed.world_written is False
        assert _membership_rows(governed) == []
        admitted = admit_semantic_candidate(
            required[0],
            executed.candidate,
            executed.catalog,
            snapshot_id=snapshot_id(governed),
        )
        assert admitted.outcome == "PERSIST_COMMITMENT"
        target = tmp_path / "c3-approved-membership-revision"
        materialize_semantic_commitment_revision(
            governed,
            target,
            required[0],
            executed.candidate,
            admitted,
            executed.catalog,
            snapshot_id=snapshot_id(governed),
        )
        revised = ConstructionWorld.open(target / governed.path.name, read_only=True)
        after = evaluate_checkout_provider_boundary(
            governed,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3["src/external-settlement.ts"]
            },
            membership_authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        case = _case_shell(definition, baseline, after, case_id="case:c3-g1")
        second, pending_after, _case2 = _evaluate(
            definition,
            baseline,
            after,
            case_id="case:c3-g1",
            adjudication=_fixture_adjudication(case),
        )
        assert after.overall_truth == TRUTH_FALSE
        assert pending_after.fan_out == 0
        assert second.readiness["status"] == STATUS_READY_FOR_ADJUDICATION
        assert snapshot_id(governed) == g0_snapshot
        assert snapshot_id(s0) == s0_snapshot
        assert snapshot_id(revised) == g0_snapshot
        assert list(revised.relation_rows(CLASS_MEMBERSHIP_RELATION))
        assert _membership_rows(governed) == []
        evidence = lookup_class_membership_evidence(
            governed,
            PAYMENT_PROVIDER_CLASS,
            _callable(governed, "settleExternal"),
            prior_world=revised,
            source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3["src/external-settlement.ts"]
            },
            authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        assert evidence.status in {
            MEMBERSHIP_STATUS_PRESERVED,
            MEMBERSHIP_STATUS_ESTABLISHED,
        }
    finally:
        _close(s0, governed)
        if revised is not None:
            revised.close()


def test_c3_approval_cannot_authorize_c3b(tmp_path):
    c3 = _c3_required(tmp_path)
    c3b_world = None
    try:
        c3_decision = decide_construction_execution(
            c3["required"], policy=approval_required_class_membership_policy()
        )
        approval = construction_execution_approval(c3_decision)
        c3b_world = _authority_world(tmp_path, PAYMENT_C3B, "c3b")
        candidate = evaluate_checkout_provider_boundary(c3b_world, c3["definition"])
        pending = pending_class_membership_obligations_from_derivation(
            candidate, context_from_invariant_definition(c3["definition"])
        )
        c3b_required = required_obligations_for_execution(
            pending,
            assess_governance_case_readiness(
                pending_obligations=pending,
                derivation=candidate,
                case=_case_shell(c3["definition"], c3["baseline"], candidate, "case:c3b"),
            ),
        )
        assert c3b_required[0].obligation_id != c3["obligation"].obligation_id
        c3b_decision = decide_construction_execution(
            c3b_required, policy=approval_required_class_membership_policy()
        )
        authorization = authorize_construction_execution(c3b_decision, approval)
        assert authorization.status == AUTHORIZATION_NOT_AUTHORIZED
        assert authorization.reason in {REASON_WRONG_OBLIGATION, REASON_WRONG_DECISION}
    finally:
        _close(c3["s0"], c3["c3"])
        if c3b_world is not None:
            c3b_world.close()


def test_two_approval_obligations_are_not_bulk_approved_and_first_can_make_second_dormant(
    tmp_path,
):
    fixture = _setup(tmp_path, PAYMENT_FANOUT, "fanout-approval")
    policy = approval_required_class_membership_policy()
    transport = _payload_transport(fixture["governed"], PAYMENT_FANOUT, _member_draft)
    try:
        first = advance_semantic_construction_cycle(
            case=fixture["case"],
            derivation=fixture["candidate"],
            pending_obligations=fixture["pending"],
            policy=policy,
            constructor=transport,
            construction_inputs=lambda obligation: (
                setattr(transport, "obligation", obligation)
                or _cycle_inputs(fixture["governed"], PAYMENT_FANOUT, obligation)
            ),
            candidate_world=fixture["governed"],
            definition=fixture["definition"],
            baseline_derivation=fixture["baseline"],
            membership_source_by_handle=fixture["source_by_handle"],
            membership_authority_by_handle=fixture["authority_by_handle"],
            publication_dir=tmp_path / "g1-unused",
        )
        assert first.status == CYCLE_APPROVAL_REQUIRED
        assert first.constructor_attempts == 0
        assert first.execution_decision is not None
        assert first.execution_decision.action == ACTION_REQUIRE_APPROVAL
        requested = first.selected_obligation_id
        other = [
            item.obligation_id
            for item in fixture["pending"].obligations
            if item.obligation_id != requested
        ]
        other_decision = decide_construction_execution(
            [item for item in fixture["pending"].obligations if item.obligation_id == other[0]],
            policy=policy,
        )
        other_approval = construction_execution_approval(other_decision)
        other_auth = authorize_construction_execution(other_decision, other_approval)
        still = advance_semantic_construction_cycle(
            case=fixture["case"],
            derivation=fixture["candidate"],
            pending_obligations=fixture["pending"],
            policy=policy,
            constructor=transport,
            construction_inputs=lambda obligation: (
                setattr(transport, "obligation", obligation)
                or _cycle_inputs(fixture["governed"], PAYMENT_FANOUT, obligation)
            ),
            candidate_world=fixture["governed"],
            definition=fixture["definition"],
            baseline_derivation=fixture["baseline"],
            execution_authorization=other_auth,
        )
        assert still.status == CYCLE_APPROVAL_REQUIRED
        assert still.constructor_attempts == 0
        assert still.selected_obligation_id == requested
        approval = construction_execution_approval(first.execution_decision)
        authorization = authorize_construction_execution(
            first.execution_decision, approval
        )
        assert authorization.status == AUTHORIZATION_AUTHORIZED
        executed = advance_semantic_construction_cycle(
            case=fixture["case"],
            derivation=fixture["candidate"],
            pending_obligations=fixture["pending"],
            policy=policy,
            constructor=transport,
            construction_inputs=lambda obligation: (
                setattr(transport, "obligation", obligation)
                or _cycle_inputs(fixture["governed"], PAYMENT_FANOUT, obligation)
            ),
            candidate_world=fixture["governed"],
            definition=fixture["definition"],
            baseline_derivation=fixture["baseline"],
            membership_source_by_handle=fixture["source_by_handle"],
            membership_authority_by_handle=fixture["authority_by_handle"],
            publication_dir=tmp_path / "g1-approved",
            execution_authorization=authorization,
        )
        assert executed.status == CYCLE_CONSTRUCTION_ATTEMPTED
        assert executed.constructor_attempts == 1
        assert executed.selected_obligation_id == requested
        assert executed.required_after == ()
        assert set(other).issubset(set(executed.dormant_after))
        assert executed.next == NEXT_ADJUDICATION
        assert executed.readiness_after["status"] == STATUS_READY_FOR_ADJUDICATION
        assert requested not in executed.required_after
        for obligation_id in other:
            assert obligation_id not in executed.required_after
    finally:
        _close(fixture["s0"], fixture["governed"])


def test_approval_is_not_world_kernel_state():
    root = Path(__file__).resolve().parents[1] / "ontology_author" / "world" / "core"
    kernel = (root / "kernel.py").read_text(encoding="utf-8")
    store = (root / "store.py").read_text(encoding="utf-8")
    assert "ConstructionExecutionApproval" not in kernel
    assert "ConstructionExecutionAuthorization" not in kernel
    assert "construction_approval" not in kernel
    assert "ConstructionExecutionApproval" not in store
    assert "construction_approval" not in store

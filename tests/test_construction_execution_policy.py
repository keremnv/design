"""One-obligation semantic construction execution policy.

Decision is separate from execution. These tests do not invoke Composer
unless ONTOLOGY_AUTHOR_LIVE_CONSTRUCTION is set.
"""

from __future__ import annotations

import copy
import os
import shutil
from pathlib import Path

import pytest

from ontology_author.authority.evaluate import snapshot_id
from ontology_author.governance import (
    CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION,
    ConstructionExecutionNotAuthorized,
    ConstructionExecutionPolicy,
    approval_required_class_membership_policy,
    auto_allowed_class_membership_policy,
    create_governance_adjudication,
    decide_construction_execution,
    evaluate_assembled_candidate_case,
    execute_construction_obligation,
    required_obligations_for_execution,
)
from ontology_author.governance.construction_execution import (
    ACTION_DEFER,
    ACTION_EXECUTE,
    ACTION_REQUIRE_APPROVAL,
    AUTHORITY_APPROVAL_REQUIRED,
    AUTHORITY_AUTO_ALLOWED,
    AUTHORITY_DISALLOWED,
    CLASS_MEMBERSHIP_CONSTRUCTOR,
    MAX_ATTEMPTS,
    RESOURCE_AVAILABLE,
    RESOURCE_UNAVAILABLE,
    RESULT_CANDIDATE_PRODUCED,
    RESULT_EXECUTION_FAILED,
    RESULT_SEMANTICALLY_UNRESOLVED,
    STATUS_DECIDED,
    STATUS_MULTIPLE_UNSUPPORTED,
    STATUS_NOT_REQUIRED,
)
from ontology_author.governance.model_adjudicator import AdjudicatorTransportResponse
from ontology_author.semantic_binding import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_RELATION,
    admit_semantic_candidate,
    lookup_class_membership_evidence,
    materialize_semantic_commitment_revision,
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
from ontology_author.semantic_binding.membership import (
    MEMBERSHIP_STATUS_ESTABLISHED,
    MEMBERSHIP_STATUS_PRESERVED,
    PAYMENT_PROVIDER_CLASS,
)
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_checkout_provider_boundary_evaluator import (
    PAYMENT_C3,
    PAYMENT_S0,
    _callable,
    _close,
    _definition_for,
    _open_spine,
)
from tests.test_class_membership_persistence import (
    AUTHORITY_HANDLE,
    AUTHORITY_TEXT,
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


class _RecordingTransport:
    def __init__(self, payload_factory, *, error=None):
        self.payload_factory = payload_factory
        self.error = error
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        payload = self.payload_factory(request)
        return AdjudicatorTransportResponse(payload=payload)


def _pending(derivation, definition):
    return pending_class_membership_obligations_from_derivation(
        derivation, context_from_invariant_definition(definition)
    )


def _case_shell(definition, baseline, candidate, case_id="case:execution"):
    return {
        "case_id": case_id,
        "contract": "governance_case/v0",
        "invariant_context": invariant_context_for_case(
            definition, baseline=baseline, candidate=candidate
        ),
        "assembly": {"completeness_basis": {"status": "COMPLETE", "known_gaps": []}},
    }


def _fixture_adjudication(case):
    return create_governance_adjudication(
        case,
        adjudicator={
            "kind": "DETERMINISTIC_CHECK",
            "identity": "execution-policy-fixture",
            "version": "v0",
        },
        decision_right={
            "outcome": "NOT_ESTABLISHED",
            "rationale": "Fixture adjudication after READY_FOR_ADJUDICATION.",
        },
    )


def _evaluate(definition, baseline, candidate, *, case_id="case:execution", adjudication=None):
    pending = _pending(candidate, definition)
    case = _case_shell(definition, baseline, candidate, case_id=case_id)
    result = evaluate_assembled_candidate_case(
        case,
        pending_obligations=pending,
        derivation=candidate,
        candidate={
            "baseline_snapshot_id": baseline.snapshot_id,
            "candidate_snapshot_id": candidate.snapshot_id,
        },
        adjudication=adjudication,
    )
    return result, pending, case


def _membership_rows(world: ConstructionWorld):
    try:
        return list(world.relation_rows(CLASS_MEMBERSHIP_RELATION))
    except Exception:
        return []


def _construction_inputs(world: ConstructionWorld, files: dict[str, str], obligation):
    subject = obligation.allowed_program_endpoints[0]
    invoke = next(
        row
        for row in world.relation_rows("program_invokes")
        if str(row.get("target")) == subject
    )
    case = _synthetic_case(subject, observation_id=obligation.authority_refs[0])
    case["program_context"]["relation_tuples"] = [
        {
            "evidence_id": "tuple:alt-settle",
            "relation": "program_invokes",
            "recorded_fact": {
                "relation": "program_invokes",
                "call_site": str(invoke.get("call_site") or ""),
                "target": subject,
            },
        }
    ]
    source_text = files["src/external-settlement.ts"]
    return {
        "case": case,
        "bounded_program_source": [_source_entry(source_text)],
        "maintenance_dependencies": [
            {"kind": "program_identity", "program_entity": subject},
            {
                "kind": "relation_tuple",
                "recorded": {
                    "relation": "program_invokes",
                    "call_site": str(invoke.get("call_site") or ""),
                    "target": subject,
                },
                "evidence_id": "tuple:alt-settle",
            },
            {
                "kind": "structural_context",
                "program_entity": subject,
                "chain": [subject],
            },
        ],
        "program_endpoint_kinds": {subject: "callable"},
        "source_text": source_text,
        "subject": subject,
    }


def _c3_required(tmp_path, monkeypatch=None):
    if monkeypatch is not None:
        monkeypatch.setattr(
            "ontology_author.semantic_binding.construction.construct_semantic_candidate",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("constructor invoked")
            ),
        )
        monkeypatch.setattr(
            "ontology_author.governance.model_adjudicator.adjudicate_governance_case",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("adjudicator invoked")
            ),
        )
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
    baseline = evaluate_checkout_provider_boundary(s0, definition)
    candidate = evaluate_checkout_provider_boundary(c3, definition)
    result, pending, case = _evaluate(
        definition, baseline, candidate, case_id="case:c3"
    )
    required = required_obligations_for_execution(pending, result.readiness)
    return {
        "s0": s0,
        "c3": c3,
        "definition": definition,
        "baseline": baseline,
        "candidate": candidate,
        "lifecycle": result,
        "pending": pending,
        "case": case,
        "required": required,
        "obligation": required[0] if required else None,
    }


def test_c3_auto_allowed_available_decides_execute_without_model(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        obligation = fixture["obligation"]
        before_obligation = obligation.to_dict()
        before_case = copy.deepcopy(fixture["case"])
        before_candidate = copy.deepcopy(fixture["candidate"].to_dict())
        before_baseline = copy.deepcopy(fixture["baseline"].to_dict())
        before_world = snapshot_id(fixture["c3"])
        before_rows = _membership_rows(fixture["c3"])
        required = fixture["required"]
        assert len(required) == 1
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        decision = decide_construction_execution(
            required,
            policy=auto_allowed_class_membership_policy(),
            resource_permission=RESOURCE_AVAILABLE,
        )
        assert decision.status == STATUS_DECIDED
        assert decision.action == ACTION_EXECUTE
        assert decision.obligation_id == obligation.obligation_id
        assert decision.construction_profile == CLASS_MEMBERSHIP_ADMISSION_PROFILE
        assert decision.execution_authority == AUTHORITY_AUTO_ALLOWED
        assert decision.resource_permission == RESOURCE_AVAILABLE
        assert decision.constructor_id == CLASS_MEMBERSHIP_CONSTRUCTOR
        assert decision.constructor_invoked is False
        assert decision.model_invoked is False
        assert decision.to_dict()["constructor_invoked"] is False
        assert decision.to_dict()["model_invoked"] is False
        assert obligation.to_dict() == before_obligation
        assert fixture["case"] == before_case
        assert fixture["candidate"].to_dict() == before_candidate
        assert fixture["baseline"].to_dict() == before_baseline
        assert snapshot_id(fixture["c3"]) == before_world
        assert _membership_rows(fixture["c3"]) == before_rows
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_c3_approval_required_does_not_execute(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        required = fixture["required"]
        decision = decide_construction_execution(
            required,
            policy=approval_required_class_membership_policy(),
            resource_permission=RESOURCE_AVAILABLE,
        )
        assert decision.action == ACTION_REQUIRE_APPROVAL
        assert decision.execution_authority == AUTHORITY_APPROVAL_REQUIRED
        assert decision.constructor_invoked is False
        assert decision.model_invoked is False
        transport = _RecordingTransport(lambda request: (_ for _ in ()).throw(
            AssertionError("constructor generate invoked")
        ))
        with pytest.raises(ConstructionExecutionNotAuthorized):
            execute_construction_obligation(
                required[0],
                decision,
                constructor=transport,
                case=_synthetic_case(required[0].allowed_program_endpoints[0]),
            )
        assert transport.requests == []
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        assert (
            fixture["lifecycle"].adoption_decision["context_requirement"]["kind"]
            == CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        )
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_c3_auto_allowed_unavailable_defers_without_failure(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        required = fixture["required"]
        decision = decide_construction_execution(
            required,
            policy=auto_allowed_class_membership_policy(),
            resource_permission=RESOURCE_UNAVAILABLE,
        )
        assert decision.action == ACTION_DEFER
        assert decision.execution_authority == AUTHORITY_AUTO_ALLOWED
        assert decision.resource_permission == RESOURCE_UNAVAILABLE
        assert decision.reason == "RESOURCE_PERMISSION_UNAVAILABLE"
        transport = _RecordingTransport(lambda request: (_ for _ in ()).throw(
            AssertionError("constructor generate invoked")
        ))
        with pytest.raises(ConstructionExecutionNotAuthorized):
            execute_construction_obligation(
                required[0],
                decision,
                constructor=transport,
                case=_synthetic_case(required[0].allowed_program_endpoints[0]),
            )
        assert transport.requests == []
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        blob = str(decision.to_dict()).lower()
        assert "failed" not in blob
        assert "rejected" not in blob
        assert "impossible" not in blob
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_required_does_not_imply_auto_allowed(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        required = fixture["required"]
        assert fixture["lifecycle"].readiness["status"] == STATUS_CONSTRUCTION_REQUIRED
        decision = decide_construction_execution(
            required,
            policy=ConstructionExecutionPolicy(
                profile_authorities={
                    CLASS_MEMBERSHIP_ADMISSION_PROFILE: AUTHORITY_DISALLOWED
                }
            ),
            resource_permission=RESOURCE_AVAILABLE,
        )
        assert decision.action == ACTION_DEFER
        assert decision.execution_authority == AUTHORITY_DISALLOWED
        assert decision.action != ACTION_EXECUTE
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_execute_authorized_member_does_not_write_world_or_admit(tmp_path):
    fixture = _c3_required(tmp_path)
    try:
        obligation = fixture["obligation"]
        inputs = _construction_inputs(fixture["c3"], PAYMENT_C3, obligation)
        decision = decide_construction_execution(
            fixture["required"],
            policy=auto_allowed_class_membership_policy(),
        )
        assert decision.action == ACTION_EXECUTE

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
        before_rows = _membership_rows(fixture["c3"])
        before_snapshot = snapshot_id(fixture["c3"])
        result = execute_construction_obligation(
            obligation,
            decision,
            constructor=transport,
            case=inputs["case"],
            bounded_program_source=inputs["bounded_program_source"],
            maintenance_dependencies=inputs["maintenance_dependencies"],
            program_endpoint_kinds=inputs["program_endpoint_kinds"],
            constructor_metadata={"provider": "fixture", "model": "deterministic"},
        )
        assert result.status == RESULT_CANDIDATE_PRODUCED
        assert result.candidate is not None
        assert result.candidate.membership_result == "MEMBER"
        assert result.constructor_invoked is True
        assert result.model_invoked is True
        assert result.invocation_count == 1
        assert result.attempt_number == MAX_ATTEMPTS == 1
        assert result.world_written is False
        assert result.admission_performed is False
        assert result.execution_decision_id == decision.decision_id
        assert result.construction_profile == CLASS_MEMBERSHIP_ADMISSION_PROFILE
        assert result.constructor_metadata["provider"] == "fixture"
        assert len(transport.requests) == 1
        assert _membership_rows(fixture["c3"]) == before_rows
        assert snapshot_id(fixture["c3"]) == before_snapshot
        admitted = admit_semantic_candidate(
            obligation,
            result.candidate,
            result.catalog,
            snapshot_id=snapshot_id(fixture["c3"]),
        )
        assert admitted.outcome == "PERSIST_COMMITMENT"
        assert _membership_rows(fixture["c3"]) == before_rows
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_execute_unresolved_is_semantic_uncertainty_not_failure(tmp_path):
    fixture = _c3_required(tmp_path)
    try:
        obligation = fixture["obligation"]
        inputs = _construction_inputs(fixture["c3"], PAYMENT_C3, obligation)
        decision = decide_construction_execution(
            fixture["required"],
            policy=auto_allowed_class_membership_policy(),
        )

        def _payload(_request):
            from ontology_author.semantic_binding import build_semantic_construction_catalog
            catalog = build_semantic_construction_catalog(
                obligation,
                inputs["case"],
                bounded_program_source=inputs["bounded_program_source"],
                maintenance_dependencies=inputs["maintenance_dependencies"],
                program_endpoint_kinds=inputs["program_endpoint_kinds"],
            )
            return _unresolved_draft(catalog)

        transport = _RecordingTransport(_payload)
        result = execute_construction_obligation(
            obligation,
            decision,
            constructor=transport,
            case=inputs["case"],
            bounded_program_source=inputs["bounded_program_source"],
            maintenance_dependencies=inputs["maintenance_dependencies"],
            program_endpoint_kinds=inputs["program_endpoint_kinds"],
        )
        assert result.status == RESULT_SEMANTICALLY_UNRESOLVED
        assert result.status != RESULT_EXECUTION_FAILED
        assert result.candidate is not None
        assert result.candidate.membership_result == "UNRESOLVED"
        assert result.invocation_count == 1
        assert result.world_written is False
        assert fixture["lifecycle"].adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        admitted = admit_semantic_candidate(
            obligation,
            result.candidate,
            result.catalog,
            snapshot_id=snapshot_id(fixture["c3"]),
        )
        assert admitted.outcome == "RECORD_UNRESOLVED"
        assert _membership_rows(fixture["c3"]) == []
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_invalid_constructor_output_is_execution_failed_one_attempt(tmp_path):
    fixture = _c3_required(tmp_path)
    try:
        obligation = fixture["obligation"]
        inputs = _construction_inputs(fixture["c3"], PAYMENT_C3, obligation)
        decision = decide_construction_execution(
            fixture["required"],
            policy=auto_allowed_class_membership_policy(),
        )
        transport = _RecordingTransport(lambda _request: {"result": "NOT_A_VALID_RESULT"})
        result = execute_construction_obligation(
            obligation,
            decision,
            constructor=transport,
            case=inputs["case"],
            bounded_program_source=inputs["bounded_program_source"],
            maintenance_dependencies=inputs["maintenance_dependencies"],
            program_endpoint_kinds=inputs["program_endpoint_kinds"],
        )
        assert result.status == RESULT_EXECUTION_FAILED
        assert result.reason == "CONSTRUCTOR_OUTPUT_INVALID"
        assert result.candidate is None
        assert result.invocation_count == 1
        assert len(transport.requests) == 1
        assert result.world_written is False
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_provider_exception_is_execution_failed_not_unresolved(tmp_path):
    fixture = _c3_required(tmp_path)
    try:
        obligation = fixture["obligation"]
        inputs = _construction_inputs(fixture["c3"], PAYMENT_C3, obligation)
        decision = decide_construction_execution(
            fixture["required"],
            policy=auto_allowed_class_membership_policy(),
        )
        transport = _RecordingTransport(
            lambda _request: None, error=RuntimeError("provider down")
        )
        result = execute_construction_obligation(
            obligation,
            decision,
            constructor=transport,
            case=inputs["case"],
            bounded_program_source=inputs["bounded_program_source"],
            maintenance_dependencies=inputs["maintenance_dependencies"],
            program_endpoint_kinds=inputs["program_endpoint_kinds"],
        )
        assert result.status == RESULT_EXECUTION_FAILED
        assert result.status != RESULT_SEMANTICALLY_UNRESOLVED
        assert result.reason == "CONSTRUCTOR_PROVIDER_FAILED"
        assert result.invocation_count == 1
    finally:
        _close(fixture["s0"], fixture["c3"])


def test_deterministic_member_control_admits_and_unblocks_same_c3(tmp_path):
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
        assert first.adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        assert len(required) == 1
        g0_snapshot = snapshot_id(governed)
        s0_snapshot = snapshot_id(s0)
        baseline_snapshot = baseline.snapshot_id
        candidate_subject = _callable(governed, "settleExternal")
        program_text = PAYMENT_C3["src/external-settlement.ts"]
        decision = decide_construction_execution(
            required, policy=auto_allowed_class_membership_policy()
        )
        assert decision.action == ACTION_EXECUTE
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
            constructor_metadata={"provider": "fixture", "model": "deterministic"},
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
        target = tmp_path / "c3-execution-membership-revision"
        persisted = materialize_semantic_commitment_revision(
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
        assert second.adoption_decision["outcome"] != "CONTEXT_REQUIRED" or (
            second.adoption_decision.get("context_requirement") or {}
        ).get("kind") != CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        assert second.adjudication is not None
        assert _callable(governed, "settleExternal") == candidate_subject
        assert snapshot_id(revised) == g0_snapshot
        assert snapshot_id(governed) == g0_snapshot
        assert snapshot_id(s0) == s0_snapshot
        assert baseline.snapshot_id == baseline_snapshot
        assert list(revised.relation_rows(CLASS_MEMBERSHIP_RELATION))
        assert _membership_rows(governed) == []
        assert PAYMENT_C3["src/external-settlement.ts"] == program_text
        evidence = lookup_class_membership_evidence(
            governed,
            PAYMENT_PROVIDER_CLASS,
            candidate_subject,
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
        assert persisted["outcome"] == "PERSIST_COMMITMENT"
        assert before.overall_truth == TRUTH_UNKNOWN
    finally:
        _close(s0, governed)
        if revised is not None:
            revised.close()


def test_multiple_required_obligations_are_unsupported_and_invoke_nothing(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "ontology_author.semantic_binding.construction.construct_semantic_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("constructor invoked")
        ),
    )
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    fanout = _open_spine(tmp_path, PAYMENT_FANOUT, "fanout")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(fanout, definition)
        result, pending, _case = _evaluate(
            definition, baseline, candidate, case_id="case:fanout"
        )
        required = required_obligations_for_execution(pending, result.readiness)
        assert pending.fan_out == 3
        assert len(required) == 3
        assert result.adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        transport = _RecordingTransport(lambda _request: {"result": "MEMBER"})
        decision = decide_construction_execution(
            required,
            policy=auto_allowed_class_membership_policy(),
        )
        assert decision.status == STATUS_MULTIPLE_UNSUPPORTED
        assert decision.action == ""
        assert decision.obligation_id == ""
        assert list(decision.required_obligation_ids) == [
            item.obligation_id for item in required
        ]
        assert decision.constructor_invoked is False
        assert decision.model_invoked is False
        with pytest.raises(ConstructionExecutionNotAuthorized):
            execute_construction_obligation(
                required[0],
                decision,
                constructor=transport,
                case=_synthetic_case(required[0].allowed_program_endpoints[0]),
            )
        assert transport.requests == []
    finally:
        _close(s0, fanout)


def test_dormant_obligations_do_not_need_execution_decision(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ontology_author.semantic_binding.construction.construct_semantic_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("constructor invoked")
        ),
    )
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    mixed = _open_spine(tmp_path, PAYMENT_FANOUT_WITH_VIOLATION, "fanout-violation")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(mixed, definition)
        case = _case_shell(definition, baseline, candidate, case_id="case:dormant")
        result, pending, _case = _evaluate(
            definition,
            baseline,
            candidate,
            case_id="case:dormant",
            adjudication=_fixture_adjudication(case),
        )
        required = required_obligations_for_execution(pending, result.readiness)
        assert pending.fan_out == 3
        assert len(required) == 0
        assert result.readiness["status"] == STATUS_READY_FOR_ADJUDICATION
        assert result.readiness["dormant_obligation_ids"]
        assert result.adjudication is not None
        decision = decide_construction_execution(
            required,
            policy=auto_allowed_class_membership_policy(),
        )
        assert decision.status == STATUS_NOT_REQUIRED
        assert decision.action == ""
        assert decision.constructor_invoked is False
        assert decision.model_invoked is False
        assert result.adoption_decision["outcome"] != "CONTEXT_REQUIRED" or (
            result.adoption_decision.get("context_requirement") or {}
        ).get("kind") != CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
    finally:
        _close(s0, mixed)


def test_missing_constructor_configuration_defers(tmp_path, monkeypatch):
    fixture = _c3_required(tmp_path, monkeypatch)
    try:
        decision = decide_construction_execution(
            fixture["required"],
            policy=ConstructionExecutionPolicy(
                profile_authorities={
                    CLASS_MEMBERSHIP_ADMISSION_PROFILE: AUTHORITY_AUTO_ALLOWED
                },
                constructor_profiles={"unrelated-profile/v1": "none"},
            ),
            resource_permission=RESOURCE_AVAILABLE,
        )
        assert decision.action == ACTION_DEFER
        assert decision.reason == "CONSTRUCTOR_NOT_CONFIGURED"
        assert decision.constructor_id == ""
    finally:
        _close(fixture["s0"], fixture["c3"])


@pytest.mark.skipif(
    not os.environ.get("ONTOLOGY_AUTHOR_LIVE_CONSTRUCTION"),
    reason="live Composer construction is opt-in",
)
def test_live_c3_execute_records_actual_result():
    pytest.skip("live Composer transport is not configured in this milestone")

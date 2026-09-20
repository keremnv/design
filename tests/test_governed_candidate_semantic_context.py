"""Governed candidate lifecycle: semantic construction CONTEXT_REQUIRED.

This milestone ends at CONTEXT_REQUIRED. It does not execute obligations or
invoke Composer.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ontology_author.authority.evaluate import snapshot_id
from ontology_author.governance import (
    CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT,
    CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION,
    REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT,
    REASON_REQUIRED_SEMANTIC_CONSTRUCTION,
    create_governance_adjudication,
    decide_candidate_adoption,
    evaluate_assembled_candidate_case,
)
from ontology_author.governance.candidate import (
    validate_candidate_adoption_decision,
    write_candidate_adoption,
)
from ontology_author.semantic_binding import (
    lookup_class_membership_evidence,
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
from tests.test_checkout_provider_boundary_evaluator import (
    PAYMENT_C3,
    PAYMENT_C4,
    PAYMENT_S0,
    _callable,
    _close,
    _definition_for,
    _open_spine,
)
from tests.test_class_membership_persistence import (
    AUTHORITY_HANDLE,
    AUTHORITY_TEXT,
    PAYMENT_C3A,
    PAYMENT_C3B,
    _authority_world,
    _persist_membership,
)
from tests.test_governance_case_readiness import PAYMENT_FANOUT_WITH_VIOLATION
from tests.test_membership_gap_obligation_synthesis import PAYMENT_FANOUT
from tests.test_model_adjudicator import CASE as MODEL_CASE
from tests.test_model_adjudicator import _candidate as conforming_adjudication

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


def _pending(derivation, definition):
    return pending_class_membership_obligations_from_derivation(
        derivation, context_from_invariant_definition(definition)
    )


def _case_shell(definition, baseline, candidate, case_id="case:lifecycle"):
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
            "identity": "lifecycle-fixture",
            "version": "v0",
        },
        decision_right={
            "outcome": "NOT_ESTABLISHED",
            "rationale": "Fixture adjudication after READY_FOR_ADJUDICATION.",
        },
    )


def _evaluate(definition, baseline, candidate, *, case_id="case:lifecycle", adjudication=None, **kwargs):
    pending = _pending(candidate, definition)
    case = _case_shell(definition, baseline, candidate, case_id=case_id)
    return evaluate_assembled_candidate_case(
        case,
        pending_obligations=pending,
        derivation=candidate,
        candidate={
            "baseline_snapshot_id": baseline.snapshot_id,
            "candidate_snapshot_id": candidate.snapshot_id,
        },
        adjudication=adjudication,
        **kwargs,
    ), pending, case


def test_c3_pre_membership_returns_semantic_construction_context_required(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "ontology_author.governance.model_adjudicator.adjudicate_governance_case",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("adjudicator invoked")
        ),
    )
    monkeypatch.setattr(
        "ontology_author.semantic_binding.construction.construct_semantic_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("constructor invoked")
        ),
    )
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(c3, definition)
        result, pending, case = _evaluate(
            definition, baseline, candidate, case_id="case:c3"
        )
        decision = result.adoption_decision
        requirement = decision["context_requirement"]
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert result.readiness["status"] == STATUS_CONSTRUCTION_REQUIRED
        assert decision["outcome"] == "CONTEXT_REQUIRED"
        assert requirement["kind"] == CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        assert requirement["reason"] == REASON_REQUIRED_SEMANTIC_CONSTRUCTION
        assert requirement["required_obligation_ids"] == [
            pending.obligations[0].obligation_id
        ]
        assert requirement["adjudicator_invoked"] is False
        assert requirement["constructor_invoked"] is False
        assert requirement["coding_agent_revision_instructions"] is None
        assert result.adjudicator_invoked is False
        assert result.constructor_invoked is False
        assert result.adjudication is None
        assert decision["adjudication_id"] == ""
        assert decision["revision_brief_ref"] is None
        chain = requirement["causal_chain"][0]
        assert chain["governance_case_id"] == "case:c3"
        assert chain["formulated_as"]["obligation_id"] == pending.obligations[0].obligation_id
        assert validate_candidate_adoption_decision(decision, result.case) == []
        write_candidate_adoption(decision, tmp_path, case=result.case)
        assert case["case_id"] == result.case["case_id"]
    finally:
        _close(s0, c3)


def test_c3_after_membership_proceeds_to_adjudication_same_candidate(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        before = evaluate_checkout_provider_boundary(governed, definition)
        first, pending_before, _case = _evaluate(
            definition, baseline, before, case_id="case:c3-g0"
        )
        assert first.adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        g0_snapshot = snapshot_id(governed)
        candidate_subject = _callable(governed, "settleExternal")
        revised, *_rest = _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        try:
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
            adjudication = _fixture_adjudication(case)
            second, pending_after, _case2 = _evaluate(
                definition,
                baseline,
                after,
                case_id="case:c3-g1",
                adjudication=adjudication,
            )
            assert after.overall_truth == TRUTH_FALSE
            assert pending_after.fan_out == 0
            assert second.readiness["status"] == STATUS_READY_FOR_ADJUDICATION
            assert second.adoption_decision["outcome"] != "CONTEXT_REQUIRED" or (
                second.adoption_decision["context_requirement"] or {}
            ).get("kind") != CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
            assert second.adjudication is not None
            assert second.adjudication["adjudication_id"] == adjudication["adjudication_id"]
            assert second.adjudicator_invoked is False
            assert _callable(governed, "settleExternal") == candidate_subject
            assert snapshot_id(revised) == g0_snapshot
            assert list(revised.relation_rows("semantic_program_membership"))
            try:
                prior_rows = list(governed.relation_rows("semantic_program_membership"))
            except Exception:
                prior_rows = []
            assert prior_rows == []
            assert PAYMENT_C3["src/external-settlement.ts"] == (
                "export function settleExternal(): void {}\n"
            )
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
            assert pending_before.obligations[0].allowed_program_endpoints == (
                candidate_subject,
            )
        finally:
            revised.close()
    finally:
        _close(s0, governed)


def test_c3a_preserved_basis_proceeds_without_construction(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3a = _open_spine(tmp_path, PAYMENT_C3A, "c3a")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        revised, *_rest = _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        candidate = evaluate_checkout_provider_boundary(
            c3a,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3A["src/external-settlement.ts"]
            },
            membership_authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        case = _case_shell(definition, baseline, candidate, case_id="case:c3a")
        result, pending, _case = _evaluate(
            definition,
            baseline,
            candidate,
            case_id="case:c3a",
            adjudication=_fixture_adjudication(case),
        )
        evidence = lookup_class_membership_evidence(
            c3a,
            PAYMENT_PROVIDER_CLASS,
            _callable(c3a, "settleExternal"),
            prior_world=revised,
            source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3A["src/external-settlement.ts"]
            },
            authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        assert evidence.status == MEMBERSHIP_STATUS_PRESERVED
        assert pending.fan_out == 0
        assert result.readiness["status"] == STATUS_READY_FOR_ADJUDICATION
        assert result.adoption_decision["outcome"] != "CONTEXT_REQUIRED" or (
            result.adoption_decision.get("context_requirement") or {}
        ).get("kind") != CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        assert result.adjudication is not None
    finally:
        _close(s0, governed, c3a)
        if revised is not None:
            revised.close()


def test_c3b_changed_basis_returns_context_required(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3b = _open_spine(tmp_path, PAYMENT_C3B, "c3b")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        revised, *_rest = _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        candidate = evaluate_checkout_provider_boundary(
            c3b,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3B["src/external-settlement.ts"]
            },
            membership_authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        result, pending, _case = _evaluate(
            definition, baseline, candidate, case_id="case:c3b"
        )
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert result.adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        assert result.adoption_decision["context_requirement"]["required_obligation_ids"] == [
            pending.obligations[0].obligation_id
        ]
        assert result.adjudicator_invoked is False
    finally:
        _close(s0, governed, c3b)
        if revised is not None:
            revised.close()


def test_c4_open_world_returns_context_required_without_non_member(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c4 = _open_spine(tmp_path, PAYMENT_C4, "c4")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(c4, definition)
        result, pending, _case = _evaluate(
            definition, baseline, candidate, case_id="case:c4"
        )
        blob = str(result.adoption_decision).lower()
        assert result.adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        assert result.adoption_decision["context_requirement"]["required_obligation_ids"] == [
            pending.obligations[0].obligation_id
        ]
        assert pending.obligations[0].allowed_program_endpoints == (
            _callable(c4, "recordAudit"),
        )
        assert "non_member" not in blob
        assert "probably not a provider" not in blob
    finally:
        _close(s0, c4)


def test_known_violation_with_dormant_obligations_proceeds_to_adjudication(tmp_path):
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
        assert candidate.overall_truth == TRUTH_FALSE
        assert pending.fan_out == 3
        assert result.readiness["status"] == STATUS_READY_FOR_ADJUDICATION
        assert result.readiness["dormant_obligation_ids"]
        assert result.adoption_decision["outcome"] != "CONTEXT_REQUIRED" or (
            result.adoption_decision.get("context_requirement") or {}
        ).get("kind") != CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        assert result.adjudication is not None
        assert result.adjudicator_invoked is False
    finally:
        _close(s0, mixed)


def test_pending_obligations_alone_do_not_block_three_unknowns_without_this_case(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    fanout = _open_spine(tmp_path, PAYMENT_FANOUT, "fanout")
    mixed = _open_spine(tmp_path, PAYMENT_FANOUT_WITH_VIOLATION, "fanout-violation")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        unknown = evaluate_checkout_provider_boundary(fanout, definition)
        false = evaluate_checkout_provider_boundary(mixed, definition)
        pending = _pending(unknown, definition)
        blocked = evaluate_assembled_candidate_case(
            _case_shell(definition, baseline, unknown, "case:unknown"),
            pending_obligations=pending,
            derivation=unknown,
        )
        case = _case_shell(definition, baseline, false, "case:false")
        ready = evaluate_assembled_candidate_case(
            case,
            pending_obligations=pending,
            derivation=false,
            adjudication=_fixture_adjudication(case),
        )
        assert blocked.adoption_decision["outcome"] == "CONTEXT_REQUIRED"
        assert ready.readiness["status"] == STATUS_READY_FOR_ADJUDICATION
        assert ready.adoption_decision["outcome"] != "CONTEXT_REQUIRED" or (
            ready.adoption_decision.get("context_requirement") or {}
        ).get("kind") != CONTEXT_REQUIREMENT_SEMANTIC_CONSTRUCTION
        assert pending.fan_out == 3
    finally:
        _close(s0, fanout, mixed)


def test_adjudicator_context_request_maps_separately_to_context_required():
    constrained = conforming_adjudication()
    context = create_governance_adjudication(
        MODEL_CASE,
        adjudicator={"kind": "DETERMINISTIC_CHECK", "identity": "fixture", "version": "v0"},
        program_findings=[
            {
                "finding_id": "pf:missing",
                "proposition": "The implementation behavior is established.",
                "truth_value": "UNKNOWN",
                "basis": "INTERPRETIVE",
                "finding_context": "INSUFFICIENT",
                "evidence_refs": [{"kind": "program_source", "id": "psrc:checkout"}],
            }
        ],
        decision_right={"outcome": "UNKNOWN", "rationale": "Implementation evidence is absent."},
        context_requests=[
            {
                "request_id": "request:implementation",
                "reason": "Need implementation source.",
                "program_identities": ["program:checkout"],
                "source_evidence_requested": [
                    {
                        "side": "NEW",
                        "program_entity": "program:checkout",
                        "kind": "IMPLEMENTATION",
                    }
                ],
            }
        ],
    )
    decision = decide_candidate_adoption(MODEL_CASE, context)
    requirement = decision.payload["context_requirement"]
    assert decision.outcome == "CONTEXT_REQUIRED"
    assert requirement["kind"] == CONTEXT_REQUIREMENT_ADJUDICATION_CONTEXT
    assert requirement["reason"] == REASON_ADJUDICATOR_INSUFFICIENT_CONTEXT
    assert requirement["adjudicator_invoked"] is True
    assert requirement["required_obligation_ids"] == []
    assert requirement["context_requests"]
    assert decision.payload["adjudication_id"] == context["adjudication_id"]
    assert validate_candidate_adoption_decision(
        decision.payload, MODEL_CASE, context
    ) == []


def test_lifecycle_does_not_import_kernel_or_synthesize(tmp_path):
    source = (
        Path(__file__).resolve().parents[1]
        / "ontology_author"
        / "governance"
        / "case_lifecycle.py"
    ).read_text(encoding="utf-8")
    kernel = (
        Path(__file__).resolve().parents[1]
        / "ontology_author"
        / "world"
        / "core"
        / "kernel.py"
    ).read_text(encoding="utf-8")
    assert "construct_semantic_candidate" not in source
    assert "synthesize_class_membership_obligation" not in source
    assert "ontology_author.world.core" not in source
    assert "case_lifecycle" not in kernel
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(c3, definition)
        first_id = snapshot_id(c3)
        result, _pending, _case = _evaluate(definition, baseline, candidate)
        assert snapshot_id(c3) == first_id
        assert result.adoption_decision["context_requirement"]["candidate_mutated"] is False
        assert result.adoption_decision["context_requirement"]["program_baseline_promoted"] is False
    finally:
        _close(s0, c3)

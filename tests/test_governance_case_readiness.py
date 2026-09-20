"""Deterministic GovernanceCase readiness: pending vs required construction.

Readiness does not formulate obligations, invoke Composer, or adjudicate.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    AuthorityUniverse,
    DeclaredSource,
    SourceStanding,
    assemble_governance_case,
    assess_attachment_maintenance,
    assess_authority_change_impact,
    construct_authority_world,
    validate_case_sidecar,
)
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.program_spine import compare_program_spines
from ontology_author.semantic_binding import (
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    lookup_class_membership_evidence,
)
from ontology_author.governance import (
    assess_governance_case_readiness,
    attach_construction_context,
    collect_pending_class_membership_obligations,
    context_from_invariant_definition,
    evaluate_checkout_provider_boundary,
    invariant_context_for_case,
    pending_class_membership_obligations_from_derivation,
)
from ontology_author.governance.case_readiness import (
    EVENTUAL_CONTEXT_REQUIRED,
    STATUS_CONSTRUCTION_REQUIRED,
    STATUS_READY_FOR_ADJUDICATION,
    UNSUPPORTED_GAP_KIND,
    UNSUPPORTED_NON_MEMBERSHIP_UNKNOWN,
)
from ontology_author.governance.checkout_invariant import TRUTH_FALSE, TRUTH_UNKNOWN
from ontology_author.semantic_binding.membership import (
    MEMBERSHIP_STATUS_ESTABLISHED,
    MEMBERSHIP_STATUS_PRESERVED,
    PAYMENT_PROVIDER_CLASS,
    MembershipGap,
)
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import _spine, _write
from tests.test_checkout_provider_boundary_evaluator import (
    AUTHORITY_TEXT,
    PAYMENT_C1,
    PAYMENT_C3,
    PAYMENT_C4,
    PAYMENT_INCOMPLETE,
    PAYMENT_S0,
    _build_authority,
    _callable,
    _close,
    _definition_for,
    _open_spine,
)
from tests.test_class_membership_persistence import (
    AUTHORITY_HANDLE,
    PAYMENT_C3A,
    PAYMENT_C3B,
    _authority_world,
    _persist_membership,
)
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

PAYMENT_FANOUT_WITH_VIOLATION = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { chargeStripe } from "./stripe-client";\n'
        'import { endpointA } from "./leaf-a";\n'
        'import { endpointB } from "./leaf-b";\n'
        'import { endpointC } from "./leaf-c";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); checkoutDirect(); endpointA(); endpointB(); endpointC(); }\n"
        "export function checkoutDirect(): void { chargeStripe(); }\n"
    ),
    "src/leaf-a.ts": "export function endpointA(): void {}\n",
    "src/leaf-b.ts": "export function endpointB(): void {}\n",
    "src/leaf-c.ts": "export function endpointC(): void {}\n",
}


def _pending(derivation, definition):
    return pending_class_membership_obligations_from_derivation(
        derivation, context_from_invariant_definition(definition)
    )


def _case_shell(definition, baseline, candidate, case_id="case:readiness"):
    return {
        "case_id": case_id,
        "contract": "governance_case/v0",
        "invariant_context": invariant_context_for_case(
            definition, baseline=baseline, candidate=candidate
        ),
    }


def _assess(definition, baseline, candidate, *, case_id="case:readiness"):
    pending = _pending(candidate, definition)
    case = _case_shell(definition, baseline, candidate, case_id=case_id)
    readiness = assess_governance_case_readiness(
        pending_obligations=pending,
        derivation=candidate,
        case=case,
    )
    return readiness, pending, case


def test_c3_pre_membership_requires_exact_settle_external_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(c3, definition)
        readiness, pending, case = _assess(
            definition, baseline, candidate, case_id="case:c3"
        )
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert pending.fan_out == 1
        assert readiness.status == STATUS_CONSTRUCTION_REQUIRED
        assert readiness.required_obligation_ids == (
            pending.obligations[0].obligation_id,
        )
        required = readiness.required_construction_obligations[0]
        subject = _callable(c3, "settleExternal")
        assert required.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
        assert required.semantic_class == PAYMENT_PROVIDER_CLASS
        assert required.program_subject == subject
        assert required.source_gap_id == pending.items[0].gap.gap_id
        chain = required.causal_chain
        assert chain["governance_case_id"] == "case:c3"
        assert chain["derivation_id"] == candidate.derivation_id
        assert chain["unknown_because"]["program_subject"] == subject
        assert chain["formulated_as"]["obligation_id"] == required.obligation_id
        assert readiness.adjudicator_invoked is False
        assert readiness.model_invoked is False
        assert readiness.to_dict()["adoption_outcome"] is None
        assert readiness.construction_required is not None
        assert (
            readiness.construction_required.eventual_workflow_outcome
            == EVENTUAL_CONTEXT_REQUIRED
        )
        attached = attach_construction_context(case, readiness)
        assert attached["case_id"] == case["case_id"]
        assert attached["construction_context"]["required_obligation_ids"] == [
            required.obligation_id
        ]
    finally:
        _close(s0, c3)


def test_c3_after_membership_is_ready_with_no_required_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        revised, *_rest = _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        try:
            candidate = evaluate_checkout_provider_boundary(revised, definition)
            readiness, pending, _case = _assess(definition, baseline, candidate)
            assert candidate.overall_truth == TRUTH_FALSE
            assert pending.fan_out == 0
            assert candidate.evaluation_receipt["membership_gaps"] == []
            assert readiness.status == STATUS_READY_FOR_ADJUDICATION
            assert readiness.required_construction_obligations == ()
            evidence = lookup_class_membership_evidence(
                revised, PAYMENT_PROVIDER_CLASS, _callable(revised, "settleExternal")
            )
            assert evidence.status == MEMBERSHIP_STATUS_ESTABLISHED
        finally:
            revised.close()
    finally:
        _close(s0, governed)


def test_c3a_preserved_basis_is_ready(tmp_path):
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
        readiness, pending, _case = _assess(definition, baseline, candidate)
        assert candidate.overall_truth == TRUTH_FALSE
        assert pending.fan_out == 0
        assert readiness.status == STATUS_READY_FOR_ADJUDICATION
        assert readiness.required_obligation_ids == ()
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
    finally:
        _close(s0, governed, c3a)
        if revised is not None:
            revised.close()


def test_c3b_changed_basis_requires_c3b_obligation(tmp_path):
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
        readiness, pending, _case = _assess(definition, baseline, candidate)
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert readiness.status == STATUS_CONSTRUCTION_REQUIRED
        assert readiness.required_obligation_ids == (
            pending.obligations[0].obligation_id,
        )
        assert readiness.required_construction_obligations[0].program_subject == (
            _callable(c3b, "settleExternal")
        )
    finally:
        _close(s0, governed, c3b)
        if revised is not None:
            revised.close()


def test_c4_unknown_membership_requires_record_audit_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c4 = _open_spine(tmp_path, PAYMENT_C4, "c4")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(c4, definition)
        readiness, pending, _case = _assess(definition, baseline, candidate)
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert readiness.status == STATUS_CONSTRUCTION_REQUIRED
        required = readiness.required_construction_obligations[0]
        assert required.program_subject == _callable(c4, "recordAudit")
        assert required.semantic_class == PAYMENT_PROVIDER_CLASS
        assert "NON_MEMBER" not in str(required.to_dict())
    finally:
        _close(s0, c4)


def test_three_unknowns_without_violation_require_all_three(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    fanout = _open_spine(tmp_path, PAYMENT_FANOUT, "fanout")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(fanout, definition)
        readiness, pending, _case = _assess(definition, baseline, candidate)
        assert pending.fan_out == 3
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert readiness.status == STATUS_CONSTRUCTION_REQUIRED
        assert len(readiness.required_obligation_ids) == 3
        assert set(readiness.required_obligation_ids) == {
            item.obligation_id for item in pending.obligations
        }
        assert readiness.dormant_obligation_ids == ()
    finally:
        _close(s0, fanout)


def test_known_violation_leaves_three_unknowns_pending_and_dormant(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    mixed = _open_spine(tmp_path, PAYMENT_FANOUT_WITH_VIOLATION, "fanout-violation")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(mixed, definition)
        readiness, pending, _case = _assess(definition, baseline, candidate)
        assert candidate.overall_truth == TRUTH_FALSE
        assert pending.fan_out == 3
        assert readiness.status == STATUS_READY_FOR_ADJUDICATION
        assert readiness.required_construction_obligations == ()
        assert readiness.required_obligation_ids == ()
        assert readiness.pending_obligation_ids == tuple(
            item.obligation_id for item in pending.obligations
        )
        assert readiness.dormant_obligation_ids == readiness.pending_obligation_ids
        assert pending.items[0].gap.to_dict()["construction_obligation"] is None
        assert pending.obligations[0].obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
    finally:
        _close(s0, mixed)


def test_same_pending_obligations_are_required_or_dormant_by_case(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    fanout = _open_spine(tmp_path, PAYMENT_FANOUT, "fanout")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        unknown = evaluate_checkout_provider_boundary(fanout, definition)
        pending = _pending(unknown, definition)
        required_case = assess_governance_case_readiness(
            pending_obligations=pending,
            derivation=unknown,
            case=_case_shell(definition, baseline, unknown, "case:unknown"),
        )
        false_payload = unknown.to_dict()
        false_payload["overall_truth"] = TRUTH_FALSE
        dormant_case = assess_governance_case_readiness(
            pending_obligations=pending,
            derivation=false_payload,
            case=_case_shell(definition, baseline, unknown, "case:false"),
        )
        assert required_case.status == STATUS_CONSTRUCTION_REQUIRED
        assert set(required_case.required_obligation_ids) == {
            item.obligation_id for item in pending.obligations
        }
        assert dormant_case.status == STATUS_READY_FOR_ADJUDICATION
        assert dormant_case.required_obligation_ids == ()
        assert dormant_case.dormant_obligation_ids == required_case.required_obligation_ids
        assert dormant_case.pending_obligation_ids == required_case.pending_obligation_ids
    finally:
        _close(s0, fanout)


def test_duplicate_consumers_do_not_duplicate_required_obligation_identity(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        other = _definition_for(
            s0,
            definition_id="invariant:second-consumer",
            provider_semantic=PAYMENT_PROVIDER_CLASS,
        )
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        first = evaluate_checkout_provider_boundary(c3, definition)
        second = evaluate_checkout_provider_boundary(c3, other)
        pending = collect_pending_class_membership_obligations(
            list(first.evaluation_receipt["membership_gaps"])
            + list(second.evaluation_receipt["membership_gaps"]),
            context_from_invariant_definition(definition),
        )
        readiness = assess_governance_case_readiness(
            pending_obligations=pending,
            derivation=first,
            case=_case_shell(definition, baseline, first),
        )
        assert pending.fan_out == 1
        assert readiness.required_obligation_ids == (
            pending.obligations[0].obligation_id,
        )
        assert set(readiness.required_construction_obligations[0].requested_by) == {
            definition.definition_id,
            other.definition_id,
        }
    finally:
        _close(s0, c3)


def test_unsupported_gap_does_not_fabricate_membership_requirement(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    incomplete = _open_spine(tmp_path, PAYMENT_INCOMPLETE, "incomplete")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(incomplete, definition)
        pending = _pending(candidate, definition)
        readiness = assess_governance_case_readiness(
            pending_obligations=pending,
            derivation=candidate,
            case=_case_shell(definition, baseline, candidate),
        )
        assert candidate.overall_truth == TRUTH_UNKNOWN
        assert pending.fan_out == 0
        assert readiness.status == STATUS_READY_FOR_ADJUDICATION
        assert readiness.required_construction_obligations == ()
        assert UNSUPPORTED_NON_MEMBERSHIP_UNKNOWN in readiness.unsupported_reasons
        fabricated = assess_governance_case_readiness(
            pending_obligations=pending,
            derivation=candidate,
            case=_case_shell(definition, baseline, candidate),
            membership_gaps=[
                MembershipGap(
                    semantic_class=PAYMENT_PROVIDER_CLASS,
                    program_subject="program:unknown",
                    snapshot="snap:x",
                    requested_by=definition.definition_id,
                    reason="SOME_OTHER_GAP",
                )
            ],
        )
        assert fabricated.required_construction_obligations == ()
        assert UNSUPPORTED_GAP_KIND in fabricated.unsupported_reasons
        assert fabricated.status == STATUS_READY_FOR_ADJUDICATION
    finally:
        _close(s0, incomplete)


def test_readiness_does_not_invoke_adjudicator_constructor_or_search(
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
        monkeypatch.setattr(
            Path,
            "rglob",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("repository inspected")
            ),
        )
        readiness, _pending_items, _case = _assess(definition, baseline, candidate)
        assert readiness.status == STATUS_CONSTRUCTION_REQUIRED
        assert readiness.adjudicator_invoked is False
        assert readiness.constructor_invoked is False
        assert readiness.repository_searched is False
        source = (
            Path(__file__).resolve().parents[1]
            / "ontology_author"
            / "governance"
            / "case_readiness.py"
        ).read_text(encoding="utf-8")
        kernel = (
            Path(__file__).resolve().parents[1]
            / "ontology_author"
            / "world"
            / "core"
            / "kernel.py"
        ).read_text(encoding="utf-8")
        assert "adjudicate_governance_case" not in source
        assert "construct_semantic_candidate" not in source
        assert "ontology_author.world" not in source
        assert "case_readiness" not in kernel
        assert "synthesize_class_membership_obligation" not in source
    finally:
        _close(s0, c3)


def test_ready_does_not_mean_conforms_or_adopt(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c1 = _open_spine(tmp_path, PAYMENT_C1, "c1")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(s0, definition)
        candidate = evaluate_checkout_provider_boundary(c1, definition)
        readiness, pending, _case = _assess(definition, baseline, candidate)
        assert candidate.overall_truth == TRUTH_FALSE
        assert pending.fan_out == 0
        assert readiness.status == STATUS_READY_FOR_ADJUDICATION
        payload = readiness.to_dict()
        assert payload["adjudication_state"] is None
        assert payload["adoption_outcome"] is None
        assert payload["status"] not in {"CONFORMS", "ADOPT", "DELEGATED"}
    finally:
        _close(s0, c1)


def test_assembled_case_overlay_keeps_dormant_ids_outside_case_identity(tmp_path):
    _write(tmp_path, {"docs/payment-boundary-universal.md": AUTHORITY_TEXT + "\n"})
    _spine(tmp_path, PAYMENT_S0, "baseline-spine")
    constructed = construct_authority_world(
        tmp_path / "baseline-spine",
        tmp_path / "baseline-world",
        AuthorityUniverse(
            universe_id="payment-provider-boundary-readiness-v1",
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
        construction_id="payment-provider-boundary-readiness-construction-v1",
        purpose="payment-provider-universal-v1",
        profile="payment-authority-universal-v0",
    )
    assert constructed.succeeded, constructed.errors
    _spine(tmp_path, PAYMENT_FANOUT_WITH_VIOLATION, "candidate-spine")
    comparison = compare_program_spines(
        tmp_path / "baseline-spine", tmp_path / "candidate-spine"
    )
    old = ConstructionWorld.open(
        tmp_path / "baseline-world" / "world.sqlite", read_only=True
    )
    new = ConstructionWorld.open(
        tmp_path / "candidate-spine" / "world.sqlite", read_only=True
    )
    try:
        definition = _definition_for(old, provider_semantic=PAYMENT_PROVIDER_CLASS)
        baseline = evaluate_checkout_provider_boundary(old, definition)
        candidate = evaluate_checkout_provider_boundary(new, definition)
        pending = _pending(candidate, definition)
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
        readiness = assess_governance_case_readiness(
            pending_obligations=pending, case=case
        )
        attached = attach_construction_context(case, readiness)
        assert candidate.overall_truth == TRUTH_FALSE
        assert pending.fan_out == 3
        assert readiness.status == STATUS_READY_FOR_ADJUDICATION
        assert attached["case_id"] == case["case_id"]
        assert attached["construction_context"]["pending_obligation_ids"]
        assert attached["construction_context"]["required_obligation_ids"] == []
        assert len(attached["construction_context"]["dormant_obligation_ids"]) == 3
        assert (
            validate_case_sidecar(
                attached, maintenance=maintenance, impact=impact, comparison=comparison
            )
            == []
        )
    finally:
        _close(old, new)

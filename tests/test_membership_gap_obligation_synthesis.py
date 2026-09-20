"""Deterministic MembershipGap -> CLASS_MEMBERSHIP obligation synthesis.

These tests do not invoke Composer or any semantic constructor. Synthesis
stops at ConstructionObligation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from ontology_author.semantic_binding import (
    CLASS_MEMBERSHIP_ADMISSION_PROFILE,
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    CLASS_MEMBERSHIP_RELATION,
    ConstructionObligation,
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
    semantic_candidate_schema,
    validate_semantic_candidate,
)
from ontology_author.governance import (
    class_membership_obligation_key,
    collect_pending_class_membership_obligations,
    context_from_invariant_definition,
    evaluate_checkout_provider_boundary,
    membership_obligation_context,
    pending_class_membership_obligations_from_derivation,
    synthesize_class_membership_obligation,
)
from ontology_author.governance.checkout_invariant import CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE
from ontology_author.semantic_binding.membership import (
    GAP_REASON_NO_EVIDENCE,
    MEMBERSHIP_STATUS_ESTABLISHED,
    MEMBERSHIP_STATUS_PRESERVED,
    MEMBERSHIP_STATUS_UNKNOWN,
    PAYMENT_PROVIDER_CLASS,
    MembershipGap,
    lookup_class_membership_evidence,
)
from ontology_author.governance.obligation_synthesis import (
    GENERATION_METHOD,
    REASON_AMBIGUOUS_SCOPE,
    REASON_MALFORMED_GAP,
    REASON_MEMBERSHIP_ALREADY_RESOLVED,
    REASON_MISSING_PROGRAM_SUBJECT,
    REASON_MISSING_SEMANTIC_CLASS,
    REASON_MISSING_SNAPSHOT,
    REASON_UNSUPPORTED_GAP_KIND,
    STATUS_CANNOT_SYNTHESIZE,
    STATUS_NOT_REQUIRED,
    STATUS_SYNTHESIZED,
    SYNTHESIS_PROFILE,
)
from tests.test_checkout_provider_boundary_evaluator import (
    PAYMENT_C3,
    PAYMENT_C4,
    PAYMENT_S0,
    _callable,
    _close,
    _definition_for,
    _labels,
    _open_spine,
)
from tests.test_class_membership_persistence import (
    AUTHORITY_HANDLE,
    AUTHORITY_TEXT,
    PAYMENT_C3A,
    PAYMENT_C3B,
    _authority_world,
    _member_draft,
    _persist_membership,
    _source_entry,
    _synthetic_case,
)

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

PAYMENT_FANOUT = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { endpointA } from "./leaf-a";\n'
        'import { endpointB } from "./leaf-b";\n'
        'import { endpointC } from "./leaf-c";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); endpointA(); endpointB(); endpointC(); }\n"
    ),
    "src/leaf-a.ts": "export function endpointA(): void {}\n",
    "src/leaf-b.ts": "export function endpointB(): void {}\n",
    "src/leaf-c.ts": "export function endpointC(): void {}\n",
}


def _context(definition, membership_status=MEMBERSHIP_STATUS_UNKNOWN):
    return context_from_invariant_definition(
        definition, membership_status=membership_status
    )


def _gap(**overrides):
    payload = {
        "semantic_class": PAYMENT_PROVIDER_CLASS,
        "program_subject": "program:settleExternal@C3",
        "snapshot": "snap:c3",
        "requested_by": "invariant:checkout-provider-boundary",
        "reason": GAP_REASON_NO_EVIDENCE,
    }
    payload.update(overrides)
    return MembershipGap.from_dict(payload)


def _default_context(**overrides):
    values = {
        "purpose": f"class-membership:{PAYMENT_PROVIDER_CLASS}",
        "program_scope": CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE,
        "authority_refs": ("obs:payment-universal",),
        "requesting_definition_id": "invariant:checkout-provider-boundary",
        "evaluator_id": "checkout-provider-boundary/v1",
        "membership_status": MEMBERSHIP_STATUS_UNKNOWN,
    }
    values.update(overrides)
    return membership_obligation_context(**values)


def _assert_no_answer(obligation: ConstructionObligation):
    payload = obligation.to_dict()
    blob = str(payload).lower()
    assert "membership_result" not in payload
    assert "preferred_model" not in payload
    assert "confidence" not in payload
    assert "non_member" not in blob
    assert "is_not_provider" not in blob
    assert payload["admission_profile"] == CLASS_MEMBERSHIP_ADMISSION_PROFILE
    assert payload["obligation_kind"] == CLASS_MEMBERSHIP_OBLIGATION_KIND


def _pending_from(derivation, definition):
    return pending_class_membership_obligations_from_derivation(
        derivation, _context(definition)
    )


def test_valid_gap_synthesizes_class_membership_obligation():
    gap = _gap()
    result = synthesize_class_membership_obligation(gap, _default_context())
    assert result.status == STATUS_SYNTHESIZED
    obligation = result.obligation
    assert obligation.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
    assert obligation.semantic_subject == PAYMENT_PROVIDER_CLASS
    assert obligation.semantic_subject == gap.semantic_class
    assert obligation.allowed_program_endpoints == (gap.program_subject,)
    assert obligation.admission_profile == CLASS_MEMBERSHIP_ADMISSION_PROFILE
    assert obligation.semantic_relation == CLASS_MEMBERSHIP_RELATION
    assert result.construction_context["snapshot"] == gap.snapshot
    assert result.model_invoked is False
    assert result.repository_searched is False
    assert gap.to_dict()["construction_obligation"] is None
    _assert_no_answer(obligation)


def test_class_and_subject_are_copied_exactly_not_reinterpreted():
    gap = _gap(
        semantic_class="semantic:PaymentProvider",
        program_subject="settleExternal@C3",
    )
    result = synthesize_class_membership_obligation(gap, _default_context())
    assert result.obligation.semantic_subject == "semantic:PaymentProvider"
    assert result.obligation.allowed_program_endpoints == ("settleExternal@C3",)
    assert result.obligation.semantic_subject != "semantic:PaymentGatewayBoundary"


def test_snapshot_scope_and_admission_profile_are_preserved():
    gap = _gap(snapshot="snap:c3-unique")
    result = synthesize_class_membership_obligation(gap, _default_context())
    assert result.construction_context["snapshot"] == "snap:c3-unique"
    assert result.provenance["source_snapshot"] == "snap:c3-unique"
    assert result.obligation.admission_profile == "semantic-class-membership/v1"
    assert result.construction_context["required_construction_profile"] == (
        CLASS_MEMBERSHIP_ADMISSION_PROFILE
    )


def test_deterministic_synthesis_provenance():
    gap = _gap()
    result = synthesize_class_membership_obligation(gap, _default_context())
    provenance = result.provenance
    assert provenance["trigger"] == "MEMBERSHIP_GAP"
    assert provenance["trigger_gap_id"] == gap.gap_id
    assert provenance["requested_by"] == ["invariant:checkout-provider-boundary"]
    assert provenance["source_snapshot"] == gap.snapshot
    assert provenance["gap_reason"] == GAP_REASON_NO_EVIDENCE
    assert provenance["generation_method"] == GENERATION_METHOD
    assert provenance["generation_profile"] == SYNTHESIS_PROFILE
    assert provenance["generation_version"] == 1


def test_stable_obligation_identity_does_not_use_incidental_ids():
    gap = _gap()
    first = synthesize_class_membership_obligation(gap, _default_context())
    second = synthesize_class_membership_obligation(gap, _default_context())
    expected = class_membership_obligation_key(
        semantic_class=gap.semantic_class,
        program_subject=gap.program_subject,
        snapshot=gap.snapshot,
        purpose=f"class-membership:{PAYMENT_PROVIDER_CLASS}",
        program_scope=CHECKOUT_PROVIDER_BOUNDARY_UNIVERSE,
    )
    assert first.obligation.obligation_id == expected
    assert first.obligation.obligation_id == second.obligation.obligation_id
    assert "uuid" not in first.obligation.obligation_id
    assert gap.gap_id not in first.obligation.obligation_id


def test_equivalent_repeated_gaps_deduplicate():
    gap1 = _gap(requested_by="invariant:run-1")
    gap2 = _gap(requested_by="invariant:run-1")
    pending = collect_pending_class_membership_obligations(
        (gap1, gap2), _default_context()
    )
    assert pending.fan_out == 1
    assert pending.obligations[0].obligation_id == synthesize_class_membership_obligation(
        gap1, _default_context()
    ).obligation.obligation_id


def test_duplicate_consumers_share_one_semantic_question():
    gap_a = _gap(requested_by="invariant:A")
    gap_b = _gap(requested_by="invariant:B")
    pending = collect_pending_class_membership_obligations(
        (gap_a, gap_b), _default_context()
    )
    assert pending.fan_out == 1
    assert set(pending.items[0].provenance["requested_by"]) == {
        "invariant:A",
        "invariant:B",
    }
    assert pending.items[0].gap.to_dict()["construction_obligation"] is None


def test_materially_different_scope_stays_distinct():
    gap = _gap()
    left = synthesize_class_membership_obligation(
        gap, _default_context(program_scope="purpose-scope-a")
    )
    right = synthesize_class_membership_obligation(
        gap, _default_context(program_scope="purpose-scope-b")
    )
    assert left.obligation.obligation_id != right.obligation.obligation_id


def test_different_subjects_remain_distinct():
    left = synthesize_class_membership_obligation(
        _gap(program_subject="program:endpointA"), _default_context()
    )
    right = synthesize_class_membership_obligation(
        _gap(program_subject="program:endpointB"), _default_context()
    )
    assert left.obligation.obligation_id != right.obligation.obligation_id
    assert left.obligation.allowed_program_endpoints != right.obligation.allowed_program_endpoints


def test_different_unknown_snapshots_remain_distinct():
    left = synthesize_class_membership_obligation(
        _gap(program_subject="program:settle@C3", snapshot="snap:c3"),
        _default_context(),
    )
    right = synthesize_class_membership_obligation(
        _gap(program_subject="program:settle@C3b", snapshot="snap:c3b"),
        _default_context(),
    )
    assert left.obligation.obligation_id != right.obligation.obligation_id
    assert left.construction_context["snapshot"] != right.construction_context["snapshot"]


def test_established_or_preserved_status_does_not_synthesize():
    gap = _gap()
    established = synthesize_class_membership_obligation(
        gap, _default_context(membership_status=MEMBERSHIP_STATUS_ESTABLISHED)
    )
    preserved = synthesize_class_membership_obligation(
        gap, _default_context(membership_status=MEMBERSHIP_STATUS_PRESERVED)
    )
    assert established.status == STATUS_NOT_REQUIRED
    assert established.reason == REASON_MEMBERSHIP_ALREADY_RESOLVED
    assert established.to_dict()["obligation"] is None
    assert preserved.status == STATUS_NOT_REQUIRED
    assert preserved.reason == REASON_MEMBERSHIP_ALREADY_RESOLVED


def test_unsupported_and_malformed_gaps_fail_explicitly():
    unsupported = synthesize_class_membership_obligation(
        _gap(reason="SOME_OTHER_GAP"), _default_context()
    )
    assert unsupported.status == STATUS_CANNOT_SYNTHESIZE
    assert unsupported.reason == REASON_UNSUPPORTED_GAP_KIND
    assert unsupported.to_dict()["obligation"] is None
    missing_class = synthesize_class_membership_obligation(
        _gap(semantic_class=""), _default_context()
    )
    assert missing_class.reason == REASON_MISSING_SEMANTIC_CLASS
    missing_subject = synthesize_class_membership_obligation(
        _gap(program_subject=""), _default_context()
    )
    assert missing_subject.reason == REASON_MISSING_PROGRAM_SUBJECT
    missing_snapshot = synthesize_class_membership_obligation(
        _gap(snapshot=""), _default_context()
    )
    assert missing_snapshot.reason == REASON_MISSING_SNAPSHOT
    malformed = synthesize_class_membership_obligation(None, _default_context())
    assert malformed.reason == REASON_MALFORMED_GAP
    ambiguous = synthesize_class_membership_obligation(
        _gap(), _default_context(program_scope="")
    )
    assert ambiguous.reason == REASON_AMBIGUOUS_SCOPE


def test_c3_before_membership_synthesizes_one_obligation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ontology_author.semantic_binding.construction.construct_semantic_candidate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("model invoked")
        ),
    )
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        derivation = evaluate_checkout_provider_boundary(c3, definition)
        gaps = derivation.evaluation_receipt["membership_gaps"]
        assert gaps
        assert gaps[0]["construction_obligation"] is None
        monkeypatch.setattr(
            Path,
            "rglob",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("repository inspected")
            ),
        )
        pending = _pending_from(derivation, definition)
        assert pending.fan_out == 1
        obligation = pending.obligations[0]
        subject = _callable(c3, "settleExternal")
        assert obligation.semantic_subject == PAYMENT_PROVIDER_CLASS
        assert obligation.allowed_program_endpoints == (subject,)
        assert pending.items[0].construction_context["snapshot"] == gaps[0]["snapshot"]
        assert pending.model_invoked is False
        assert pending.repository_searched is False
        _assert_no_answer(obligation)
        evidence = lookup_class_membership_evidence(
            c3, PAYMENT_PROVIDER_CLASS, subject
        )
        assert evidence.status == MEMBERSHIP_STATUS_UNKNOWN
    finally:
        _close(s0, c3)


def test_c3_after_membership_produces_no_gap_or_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        revised, _persisted, _obligation, _catalog, _candidate, _subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        try:
            after = evaluate_checkout_provider_boundary(revised, definition)
            assert after.evaluation_receipt["membership_gaps"] == []
            pending = _pending_from(after, definition)
            assert pending.fan_out == 0
            assert pending.obligations == ()
            evidence = lookup_class_membership_evidence(
                revised, PAYMENT_PROVIDER_CLASS, _callable(revised, "settleExternal")
            )
            assert evidence.status == MEMBERSHIP_STATUS_ESTABLISHED
        finally:
            revised.close()
    finally:
        _close(s0, governed)


def test_c3a_preserved_basis_produces_no_gap_or_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3a = _open_spine(tmp_path, PAYMENT_C3A, "c3a")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        revised, _persisted, _obligation, _catalog, _candidate, _subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        result = evaluate_checkout_provider_boundary(
            c3a,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3A["src/external-settlement.ts"]
            },
            membership_authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        assert result.evaluation_receipt["membership_gaps"] == []
        pending = _pending_from(result, definition)
        assert pending.fan_out == 0
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


def test_c3b_changed_basis_synthesizes_new_snapshot_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3b = _open_spine(tmp_path, PAYMENT_C3B, "c3b")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        before = evaluate_checkout_provider_boundary(governed, definition)
        c3_pending = _pending_from(before, definition)
        revised, _persisted, _obligation, _catalog, _candidate, c3_subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        result = evaluate_checkout_provider_boundary(
            c3b,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3B["src/external-settlement.ts"]
            },
            membership_authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        assert result.evaluation_receipt["membership_gaps"]
        pending = _pending_from(result, definition)
        assert pending.fan_out == 1
        subject = _callable(c3b, "settleExternal")
        obligation = pending.obligations[0]
        assert obligation.allowed_program_endpoints == (subject,)
        assert subject != c3_subject
        assert obligation.obligation_id != c3_pending.obligations[0].obligation_id
        assert pending.items[0].construction_context["snapshot"] != (
            c3_pending.items[0].construction_context["snapshot"]
        )
        _assert_no_answer(obligation)
    finally:
        _close(s0, governed, c3b)
        if revised is not None:
            revised.close()


def test_c4_unknown_record_audit_synthesizes_open_world_obligation(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c4 = _open_spine(tmp_path, PAYMENT_C4, "c4")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        derivation = evaluate_checkout_provider_boundary(c4, definition)
        pending = _pending_from(derivation, definition)
        assert pending.fan_out == 1
        obligation = pending.obligations[0]
        subject = _callable(c4, "recordAudit")
        assert obligation.semantic_subject == PAYMENT_PROVIDER_CLASS
        assert obligation.allowed_program_endpoints == (subject,)
        _assert_no_answer(obligation)
        assert "NON_MEMBER" not in str(obligation.to_dict())
    finally:
        _close(s0, c4)


def test_fan_out_is_one_obligation_per_independent_question(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    fanout = _open_spine(tmp_path, PAYMENT_FANOUT, "fanout")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        derivation = evaluate_checkout_provider_boundary(fanout, definition)
        gaps = derivation.evaluation_receipt["membership_gaps"]
        pending = _pending_from(derivation, definition)
        subjects = {
            _callable(fanout, "endpointA"),
            _callable(fanout, "endpointB"),
            _callable(fanout, "endpointC"),
        }
        assert {item["program_subject"] for item in gaps} == subjects
        assert len(gaps) == 3
        assert pending.fan_out == 3
        synthesized_subjects = {
            item.allowed_program_endpoints[0] for item in pending.obligations
        }
        assert synthesized_subjects == subjects
        assert len({item.obligation_id for item in pending.obligations}) == 3
    finally:
        _close(s0, fanout)


def test_generated_obligation_is_accepted_by_existing_construction_path(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        derivation = evaluate_checkout_provider_boundary(c3, definition)
        pending = _pending_from(derivation, definition)
        obligation = pending.obligations[0]
        subject = obligation.allowed_program_endpoints[0]
        invoke = next(
            row
            for row in c3.relation_rows("program_invokes")
            if str(row.get("target")) == subject
        )
        case = _synthetic_case(subject)
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
        catalog = build_semantic_construction_catalog(
            obligation,
            case,
            bounded_program_source=[
                _source_entry(PAYMENT_C3["src/external-settlement.ts"])
            ],
            maintenance_dependencies=[
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
            program_endpoint_kinds={subject: "callable"},
        )
        schema = semantic_candidate_schema(catalog)
        assert schema["properties"]["result"]["enum"] == ["MEMBER", "UNRESOLVED"]
        candidate = compile_semantic_candidate_draft(
            obligation, catalog, _member_draft(catalog)
        )
        assert candidate.tuple["semantic_class"] == PAYMENT_PROVIDER_CLASS
        assert candidate.tuple["program_manifestation"] == subject
        assert validate_semantic_candidate(obligation, candidate, catalog) == []
    finally:
        _close(s0, c3)


def test_evaluator_does_not_auto_synthesize_or_execute():
    invariant_source = (
        Path(__file__).resolve().parents[1]
        / "ontology_author"
        / "governance"
        / "checkout_invariant.py"
    ).read_text(encoding="utf-8")
    synthesis_source = (
        Path(__file__).resolve().parents[1]
        / "ontology_author"
        / "governance"
        / "obligation_synthesis.py"
    ).read_text(encoding="utf-8")
    kernel = (
        Path(__file__).resolve().parents[1] / "ontology_author" / "world" / "core"
    )
    assert "synthesize_class_membership_obligation" not in invariant_source
    assert "construct_semantic_candidate" not in synthesis_source
    assert "ontology_author.world" not in synthesis_source
    assert "world.core" not in synthesis_source
    assert "obligation_synthesis" not in (kernel / "kernel.py").read_text(
        encoding="utf-8"
    )
    assert pending_class_membership_obligations_from_derivation(
        {"evaluation_receipt": {"membership_gaps": []}},
        _default_context(),
    ).fan_out == 0

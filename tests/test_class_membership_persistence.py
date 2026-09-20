"""CLASS_MEMBERSHIP persistence and identical-basis reuse tests.

Live Composer construction is kept separate from the deterministic control
path.  These tests do not invoke a model unless explicitly opted in.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    AuthorityUniverse,
    CompletenessScope,
    DeclaredSource,
    SourceStanding,
    construct_authority_world,
)
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.semantic_binding import (
    CLASS_MEMBERSHIP_OBLIGATION_KIND,
    CLASS_MEMBERSHIP_RELATION,
    ConstructionObligation,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    canonical_semantic_commitment_schema,
    class_membership_obligation,
    compile_semantic_candidate_draft,
    interpretation_basis_digest,
    lookup_class_membership_evidence,
    materialize_semantic_commitment_revision,
    semantic_candidate_schema,
    validate_semantic_candidate,
)
from ontology_author.governance import (
    evaluate_checkout_provider_boundary,
)
from ontology_author.governance.checkout_invariant import (
    COMPLETENESS_COMPLETE,
    MEMBER_UNKNOWN,
    MEMBER_VIOLATES,
    TRUTH_FALSE,
    TRUTH_UNKNOWN,
)
from ontology_author.semantic_binding.membership import (
    GAP_REASON_NO_EVIDENCE,
    MEMBERSHIP_STATUS_ESTABLISHED,
    MEMBERSHIP_STATUS_PRESERVED,
    MEMBERSHIP_STATUS_UNKNOWN,
    PAYMENT_PROVIDER_CLASS,
    build_interpretation_basis,
)
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_checkout_provider_boundary_evaluator import (
    AUTHORITY_TEXT,
    PAYMENT_C3,
    PAYMENT_C4,
    PAYMENT_S0,
    _build_authority,
    _callable,
    _close,
    _definition_for,
    _descriptor,
    _labels,
    _member_targets,
    _open_spine,
)
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

PAYMENT_C3A = {
    **PAYMENT_C3,
    "src/checkout.ts": (
        'import { authorize, authorizeRetry } from "./payment-service";\n'
        'import { settleExternal } from "./external-settlement";\n'
        "export function checkout(): void { authorize(); authorizeRetry(); checkoutAlternative(); }\n"
        "export function checkoutAlternative(): void { settleExternal(); }\n"
        "export function logCheckoutStep(): void {}\n"
    ),
}
PAYMENT_C3B = {
    **PAYMENT_C3,
    "src/external-settlement.ts": (
        "export function settleExternal(): void { const _nonce = 1; }\n"
    ),
}
AUTHORITY_HANDLE = "docs/payment-boundary-universal.md"


def _alias(catalog, category, identifier=None):
    for alias in catalog["allowed_aliases"][category]:
        item = next(entry for entry in catalog["entries"] if entry["alias"] == alias)
        if identifier is None or item["id"] == identifier:
            return alias
    raise AssertionError(f"missing {category} alias")


def _membership_obligation(subject: str, authority_ref: str = "obs:payment-universal"):
    return class_membership_obligation(
        obligation_id="obligation:payment-provider-settleExternal",
        purpose="payment-provider-class-membership-v0",
        authority_refs=(authority_ref,),
        semantic_class=PAYMENT_PROVIDER_CLASS,
        program_subject=subject,
        program_scope="checkout-payment-provider-membership",
    )


def _synthetic_case(subject: str, *, observation_id="obs:payment-universal", authority_text=AUTHORITY_TEXT):
    return {
        "case_id": "case:class-membership",
        "authority": {
            "observations": [
                {
                    "observation_id": observation_id,
                    "provider": "markdown",
                    "handle": AUTHORITY_HANDLE,
                    "revision": "sha256:authority",
                    "native_location": "bytes:0:80",
                    "standing": "AUTHORITATIVE",
                    "reconstructed_text": authority_text,
                }
            ],
            "semantic_referents": [
                {"id": PAYMENT_PROVIDER_CLASS, "label": "PaymentProvider"},
            ],
            "claims": [],
        },
        "semantic_context": {
            "referents": [
                {
                    "id": PAYMENT_PROVIDER_CLASS,
                    "label": "PaymentProvider",
                    "source_observation_ids": [observation_id],
                }
            ],
            "claims": [],
        },
        "program_context": {
            "referents": [{"id": subject, "kind": "callable", "side": "OLD"}],
            "source_evidence": [],
            "relation_tuples": [
                {
                    "evidence_id": "tuple:alt-settle",
                    "relation": "program_invokes",
                    "recorded_fact": {
                        "relation": "program_invokes",
                        "call_site": "call:alt",
                        "target": subject,
                    },
                }
            ],
            "resolution_outcomes": [],
            "structural_context": [],
        },
        "selection": [],
        "transition_facts": [],
        "supporting_material": [],
    }


def _source_entry(text: str, handle="src/external-settlement.ts", evidence_id="source:settle"):
    return {
        "evidence_id": evidence_id,
        "provider": "fixture",
        "native_handle": handle,
        "source_revision": "fixture",
        "native_location": "bytes:0:1",
        "reconstructed_text": text,
    }


def _dependencies(subject: str):
    return [
        {"kind": "program_identity", "program_entity": subject},
        {
            "kind": "relation_tuple",
            "recorded": {
                "relation": "program_invokes",
                "call_site": "call:alt",
                "target": subject,
            },
            "evidence_id": "tuple:alt-settle",
        },
        {
            "kind": "structural_context",
            "program_entity": subject,
            "chain": ["module:external", subject],
        },
    ]


def _member_draft(catalog):
    return {
        "result": "MEMBER",
        "authority_evidence_aliases": [_alias(catalog, "AUTHORITATIVE_EVIDENCE")],
        "program_source_evidence_aliases": [_alias(catalog, "PROGRAM_SOURCE")],
        "mechanical_evidence_aliases": [_alias(catalog, "MECHANICAL_FACT")],
        "maintenance_dependency_aliases": list(
            catalog["allowed_aliases"]["MAINTENANCE_DEPENDENCY"]
        ),
    }


def _unresolved_draft(catalog):
    return {
        "result": "UNRESOLVED",
        "authority_evidence_aliases": [],
        "program_source_evidence_aliases": [],
        "mechanical_evidence_aliases": [],
        "maintenance_dependency_aliases": [],
    }


def test_class_membership_obligation_round_trip_and_fixed_subject():
    obligation = _membership_obligation("program:settleExternal")
    restored = ConstructionObligation.from_dict(obligation.to_dict())
    assert restored == obligation
    assert obligation.obligation_kind == CLASS_MEMBERSHIP_OBLIGATION_KIND
    assert obligation.semantic_relation == CLASS_MEMBERSHIP_RELATION
    with pytest.raises(ValueError, match="exactly one"):
        ConstructionObligation(
            obligation_id="obligation:bad",
            purpose="p",
            authority_refs=("obs:x",),
            semantic_subject=PAYMENT_PROVIDER_CLASS,
            semantic_relation=CLASS_MEMBERSHIP_RELATION,
            question="q",
            obligation_kind=CLASS_MEMBERSHIP_OBLIGATION_KIND,
            program_scope="scope",
            allowed_program_endpoints=("program:a", "program:b"),
            required_evidence_classes=("AUTHORITY_GROUNDING", "MECHANICAL_GROUNDING"),
            tuple_shape={"semantic_class": "SEMANTIC", "program_manifestation": "PROGRAM"},
            admission_profile="semantic-class-membership/v1",
        )


def test_model_cannot_replace_fixed_class_or_subject():
    subject = "program:settleExternal"
    obligation = _membership_obligation(subject)
    catalog = build_semantic_construction_catalog(
        obligation,
        _synthetic_case(subject),
        bounded_program_source=[_source_entry("export function settleExternal(): void {}\n")],
        maintenance_dependencies=_dependencies(subject),
        program_endpoint_kinds={subject: "callable"},
    )
    schema = semantic_candidate_schema(catalog)
    assert schema["properties"]["result"]["enum"] == ["MEMBER", "UNRESOLVED"]
    assert "program_endpoint_aliases" not in schema["properties"]
    assert "semantic_endpoint_aliases" not in schema["properties"]
    assert "relation_name" not in schema["properties"]
    draft = _member_draft(catalog)
    candidate = compile_semantic_candidate_draft(obligation, catalog, draft)
    assert candidate.tuple["semantic_class"] == PAYMENT_PROVIDER_CLASS
    assert candidate.tuple["program_manifestation"] == subject
    assert candidate.relation_name == CLASS_MEMBERSHIP_RELATION
    mutated = ConstructionObligation.from_dict(
        {**candidate.to_dict(), "tuple": {**candidate.tuple, "program_manifestation": "program:other"}}
    ) if False else candidate
    other = copy.deepcopy(candidate.to_dict())
    other["tuple"]["program_manifestation"] = "program:other"
    other["program_endpoint_refs"] = ["program:other"]
    other.pop("candidate_id")
    from ontology_author.semantic_binding import SemanticCandidate
    invalid = SemanticCandidate.from_dict(other)
    errors = validate_semantic_candidate(obligation, invalid, catalog)
    assert any("cannot be replaced" in item or "not the obligation subject" in item for item in errors)


def test_member_and_unresolved_candidate_validation_and_admission():
    subject = "program:settleExternal"
    obligation = _membership_obligation(subject)
    catalog = build_semantic_construction_catalog(
        obligation,
        _synthetic_case(subject),
        bounded_program_source=[_source_entry("export function settleExternal(): void {}\n")],
        maintenance_dependencies=_dependencies(subject),
        program_endpoint_kinds={subject: "callable"},
    )
    member = compile_semantic_candidate_draft(obligation, catalog, _member_draft(catalog))
    assert member.membership_result == "MEMBER"
    assert validate_semantic_candidate(obligation, member, catalog) == []
    admitted = admit_semantic_candidate(obligation, member, catalog, snapshot_id="s0")
    assert admitted.outcome == "PERSIST_COMMITMENT"
    unresolved = compile_semantic_candidate_draft(
        obligation, catalog, _unresolved_draft(catalog)
    )
    assert unresolved.membership_result == "UNRESOLVED"
    decision = admit_semantic_candidate(obligation, unresolved, catalog, snapshot_id="s0")
    assert decision.outcome == "RECORD_UNRESOLVED"
    assert decision.reason == "MEMBERSHIP_UNRESOLVED"
    schema = canonical_semantic_commitment_schema(obligation)
    assert schema["name"] == CLASS_MEMBERSHIP_RELATION


def test_member_without_grounding_is_unresolved_not_non_member():
    subject = "program:settleExternal"
    obligation = _membership_obligation(subject)
    catalog = build_semantic_construction_catalog(
        obligation,
        _synthetic_case(subject),
        bounded_program_source=[_source_entry("export function settleExternal(): void {}\n")],
        maintenance_dependencies=_dependencies(subject),
        program_endpoint_kinds={subject: "callable"},
    )
    draft = _member_draft(catalog)
    draft["authority_evidence_aliases"] = []
    draft["program_source_evidence_aliases"] = []
    draft["mechanical_evidence_aliases"] = []
    candidate = compile_semantic_candidate_draft(obligation, catalog, draft)
    decision = admit_semantic_candidate(obligation, candidate, catalog, snapshot_id="s0")
    assert decision.outcome == "RECORD_UNRESOLVED"
    assert "NON_MEMBER" not in decision.reason


def test_interpretation_basis_digest_ignores_incidental_ids_and_tracks_material_changes(
    tmp_path,
):
    world = _open_spine(tmp_path, PAYMENT_C3, "c3-basis")
    try:
        subject = _callable(world, "settleExternal")
        source = _source_entry(PAYMENT_C3["src/external-settlement.ts"])
        obligation = _membership_obligation(subject, authority_ref="obs:one")
        catalog_a = build_semantic_construction_catalog(
            obligation,
            _synthetic_case(subject, observation_id="obs:one"),
            bounded_program_source=[source],
            maintenance_dependencies=_dependencies(subject),
            program_endpoint_kinds={subject: "callable"},
        )
        obligation_b = _membership_obligation(subject, authority_ref="obs:two")
        catalog_b = build_semantic_construction_catalog(
            obligation_b,
            _synthetic_case(subject, observation_id="obs:two"),
            bounded_program_source=[{**source, "evidence_id": "source:other-id"}],
            maintenance_dependencies=_dependencies(subject),
            program_endpoint_kinds={subject: "callable"},
        )
        member_a = compile_semantic_candidate_draft(
            obligation, catalog_a, _member_draft(catalog_a)
        )
        member_b = compile_semantic_candidate_draft(
            obligation_b, catalog_b, _member_draft(catalog_b)
        )
        basis_a = build_interpretation_basis(world, obligation, member_a, catalog_a)
        basis_b = build_interpretation_basis(world, obligation_b, member_b, catalog_b)
        dumped = json.dumps(basis_a)
        assert "obs:one" not in dumped
        assert snapshot_id(world) not in dumped
        assert interpretation_basis_digest(basis_a) == interpretation_basis_digest(basis_b)
        catalog_c = build_semantic_construction_catalog(
            obligation,
            _synthetic_case(subject, observation_id="obs:one"),
            bounded_program_source=[_source_entry(PAYMENT_C3B["src/external-settlement.ts"])],
            maintenance_dependencies=_dependencies(subject),
            program_endpoint_kinds={subject: "callable"},
        )
        member_c = compile_semantic_candidate_draft(
            obligation, catalog_c, _member_draft(catalog_c)
        )
        basis_c = build_interpretation_basis(world, obligation, member_c, catalog_c)
        assert interpretation_basis_digest(basis_a) != interpretation_basis_digest(basis_c)
        catalog_d = build_semantic_construction_catalog(
            obligation,
            _synthetic_case(
                subject,
                observation_id="obs:one",
                authority_text=AUTHORITY_TEXT + " Extra class grounding.",
            ),
            bounded_program_source=[source],
            maintenance_dependencies=_dependencies(subject),
            program_endpoint_kinds={subject: "callable"},
        )
        member_d = compile_semantic_candidate_draft(
            obligation, catalog_d, _member_draft(catalog_d)
        )
        basis_d = build_interpretation_basis(world, obligation, member_d, catalog_d)
        assert interpretation_basis_digest(basis_a) != interpretation_basis_digest(basis_d)
    finally:
        world.close()


def _extend_authority(ctor) -> None:
    _build_authority(ctor)
    source = ctor.source(AUTHORITY_HANDLE)
    observation = source.observe(source.paragraphs()[0])
    ctor.create_semantic_referent(
        PAYMENT_PROVIDER_CLASS,
        label="PaymentProvider",
        observations=(observation,),
    )


def _authority_world(tmp_path: Path, files: dict[str, str], name: str):
    _write(tmp_path, {AUTHORITY_HANDLE: AUTHORITY_TEXT + "\n"})
    _spine(tmp_path, files, f"{name}-spine")
    constructed = construct_authority_world(
        tmp_path / f"{name}-spine",
        tmp_path / f"{name}-world",
        AuthorityUniverse(
            universe_id=f"{name}-membership",
            workspace=tmp_path,
            sources=(
                DeclaredSource(
                    AUTHORITY_HANDLE,
                    tmp_path / AUTHORITY_HANDLE,
                    SourceStanding.AUTHORITATIVE,
                ),
            ),
        ),
        _extend_authority,
        construction_id=f"{name}-membership-construction",
        purpose="payment-provider-universal-v1",
        profile="payment-authority-universal-v0",
    )
    assert constructed.succeeded, constructed.errors
    return ConstructionWorld.open(tmp_path / f"{name}-world" / "world.sqlite", read_only=True)


def _c3_membership_bundle(world: ConstructionWorld, files: dict[str, str]):
    subject = _callable(world, "settleExternal")
    invoke = next(
        row
        for row in world.relation_rows("program_invokes")
        if str(row.get("target")) == subject
    )
    case = _synthetic_case(subject, observation_id="obs:payment-universal")
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
    obligation = _membership_obligation(subject)
    catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=[_source_entry(source_text)],
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
    return obligation, catalog, subject, source_text


def _persist_membership(tmp_path: Path, world: ConstructionWorld, files: dict[str, str], name: str):
    obligation, catalog, subject, source_text = _c3_membership_bundle(world, files)
    candidate = compile_semantic_candidate_draft(
        obligation, catalog, _member_draft(catalog)
    )
    decision = admit_semantic_candidate(
        obligation, candidate, catalog, snapshot_id=snapshot_id(world)
    )
    assert decision.outcome == "PERSIST_COMMITMENT", decision.to_dict()
    target = tmp_path / f"{name}-membership-revision"
    persisted = materialize_semantic_commitment_revision(
        world,
        target,
        obligation,
        candidate,
        decision,
        catalog,
        snapshot_id=snapshot_id(world),
    )
    revised = ConstructionWorld.open(target / world.path.name, read_only=True)
    return revised, persisted, obligation, catalog, candidate, subject, source_text


def test_c3_initial_invariant_is_unknown_and_emits_membership_gap(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c3 = _open_spine(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        result = evaluate_checkout_provider_boundary(c3, definition)
        assert "checkoutAlternative" in _member_targets(c3, result)
        added = next(
            item
            for item in result.member_results
            if _labels(c3).get(str(item["origin_target"])) == "checkoutAlternative"
        )
        assert added["result"] == MEMBER_UNKNOWN
        assert result.overall_truth == TRUTH_UNKNOWN
        assert result.evaluation_receipt["membership_gaps"]
        assert result.evaluation_receipt["membership_gaps"][0]["reason"] == GAP_REASON_NO_EVIDENCE
        assert result.evaluation_receipt["model_invoked"] is False
        evidence = lookup_class_membership_evidence(
            c3, PAYMENT_PROVIDER_CLASS, _callable(c3, "settleExternal")
        )
        assert evidence.status == MEMBERSHIP_STATUS_UNKNOWN
        assert evidence.model_invoked is False
    finally:
        _close(s0, c3)


def test_c3_positive_membership_makes_invariant_false(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        before = evaluate_checkout_provider_boundary(governed, definition)
        assert before.overall_truth == TRUTH_UNKNOWN
        revised, persisted, _obligation, _catalog, _candidate, subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        try:
            rows = revised.relation_rows(CLASS_MEMBERSHIP_RELATION)
            assert any(
                str(row.get("program_manifestation")) == subject
                and str(row.get("semantic_class")) == PAYMENT_PROVIDER_CLASS
                for row in rows
            )
            evidence = lookup_class_membership_evidence(
                revised, PAYMENT_PROVIDER_CLASS, subject
            )
            assert evidence.status == MEMBERSHIP_STATUS_ESTABLISHED
            assert evidence.materialized_current_assertion is True
            assert evidence.model_invoked is False
            after = evaluate_checkout_provider_boundary(revised, definition)
            added = next(
                item
                for item in after.member_results
                if _labels(revised).get(str(item["origin_target"])) == "checkoutAlternative"
            )
            assert added["result"] == MEMBER_VIOLATES
            assert after.overall_truth == TRUTH_FALSE
            assert after.evaluation_receipt["model_invoked"] is False
            assert persisted["interpretation_basis"]["digest"]
        finally:
            revised.close()
    finally:
        _close(s0, governed)


def test_membership_constructor_uses_catalog_only_and_no_repository(tmp_path, monkeypatch):
    from ontology_author.governance.model_adjudicator import AdjudicatorTransportResponse
    from ontology_author.semantic_binding import construct_semantic_candidate
    subject = "program:settleExternal"
    obligation = _membership_obligation(subject)
    case = _synthetic_case(subject)
    catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=[_source_entry("export function settleExternal(): void {}\n")],
        maintenance_dependencies=_dependencies(subject),
        program_endpoint_kinds={subject: "callable"},
    )

    class Transport:
        def __init__(self):
            self.requests = []

        def generate(self, request):
            self.requests.append(request)
            return AdjudicatorTransportResponse(payload=_member_draft(catalog))

    monkeypatch.setattr(
        Path,
        "rglob",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("repository inspected")
        ),
    )
    transport = Transport()
    candidate = construct_semantic_candidate(
        obligation,
        case,
        transport=transport,
        bounded_program_source=[_source_entry("export function settleExternal(): void {}\n")],
        maintenance_dependencies=_dependencies(subject),
        program_endpoint_kinds={subject: "callable"},
        output_dir=tmp_path,
        constructor_metadata={"provider": "fake", "model": "fixture"},
    )
    assert candidate.membership_result == "MEMBER"
    assert candidate.tuple["program_manifestation"] == subject
    assert transport.requests[0].evidence_catalog_json == ""
    assert "repository" not in transport.requests[0].case_json.lower()
    assert "CLASS_MEMBERSHIP" in transport.requests[0].instruction


def test_c4_remains_unknown_without_positive_membership(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    c4 = _open_spine(tmp_path, PAYMENT_C4, "c4")
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        result = evaluate_checkout_provider_boundary(c4, definition)
        assert "recordAudit" in _member_targets(c4, result)
        assert result.overall_truth == TRUTH_UNKNOWN
        assert MEMBER_VIOLATES not in {item["result"] for item in result.member_results}
        evidence = lookup_class_membership_evidence(
            c4, PAYMENT_PROVIDER_CLASS, _callable(c4, "recordAudit")
        )
        assert evidence.status == MEMBERSHIP_STATUS_UNKNOWN
        assert "NON_MEMBER" not in evidence.status
        assert result.evaluation_receipt["model_invoked"] is False
    finally:
        _close(s0, c4)


def test_c3a_preserved_identical_basis_is_not_a_new_assertion(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3a = _open_spine(tmp_path, PAYMENT_C3A, "c3a")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        revised, persisted, _obligation, _catalog, _candidate, subject, source_text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        current_subject = _callable(c3a, "settleExternal")
        authority = {AUTHORITY_HANDLE: AUTHORITY_TEXT}
        sources = {
            "src/external-settlement.ts": PAYMENT_C3A["src/external-settlement.ts"]
        }
        evidence = lookup_class_membership_evidence(
            c3a,
            PAYMENT_PROVIDER_CLASS,
            current_subject,
            prior_world=revised,
            source_by_handle=sources,
            authority_by_handle=authority,
        )
        assert evidence.status == MEMBERSHIP_STATUS_PRESERVED
        assert evidence.materialized_current_assertion is False
        assert evidence.model_invoked is False
        assert evidence.source_commitment == persisted["assertion_id"]
        assert evidence.source_snapshot == snapshot_id(revised)
        assert evidence.current_snapshot == snapshot_id(c3a)
        assert evidence.current_snapshot != evidence.source_snapshot
        try:
            c3a.relation_rows(CLASS_MEMBERSHIP_RELATION)
            present = True
        except Exception:
            present = False
        if present:
            assert c3a.relation_rows(CLASS_MEMBERSHIP_RELATION) == []
        result = evaluate_checkout_provider_boundary(
            c3a,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle=sources,
            membership_authority_by_handle=authority,
        )
        added = next(
            item
            for item in result.member_results
            if _labels(c3a).get(str(item["origin_target"])) == "checkoutAlternative"
        )
        assert added["result"] == MEMBER_VIOLATES
        assert result.overall_truth == TRUTH_FALSE
        assert result.evaluation_receipt["model_invoked"] is False
        assert result.universe["structural_enumeration"] == COMPLETENESS_COMPLETE
    finally:
        _close(s0, governed, c3a)
        if revised is not None:
            revised.close()


def test_c3b_changed_basis_returns_unknown_and_gap(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3b = _open_spine(tmp_path, PAYMENT_C3B, "c3b")
    revised = None
    try:
        definition = _definition_for(s0, provider_semantic=PAYMENT_PROVIDER_CLASS)
        revised, _persisted, _obligation, _catalog, _candidate, _subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        current_subject = _callable(c3b, "settleExternal")
        authority = {AUTHORITY_HANDLE: AUTHORITY_TEXT}
        sources = {
            "src/external-settlement.ts": PAYMENT_C3B["src/external-settlement.ts"]
        }
        evidence = lookup_class_membership_evidence(
            c3b,
            PAYMENT_PROVIDER_CLASS,
            current_subject,
            prior_world=revised,
            source_by_handle=sources,
            authority_by_handle=authority,
        )
        assert evidence.status == MEMBERSHIP_STATUS_UNKNOWN
        assert evidence.model_invoked is False
        assert evidence.interpretation_basis_digest != evidence.current_basis_digest
        result = evaluate_checkout_provider_boundary(
            c3b,
            definition,
            membership_prior_world=revised,
            membership_source_by_handle=sources,
            membership_authority_by_handle=authority,
        )
        assert result.overall_truth == TRUTH_UNKNOWN
        assert result.evaluation_receipt["membership_gaps"]
        assert result.evaluation_receipt["model_invoked"] is False
    finally:
        _close(s0, governed, c3b)
        if revised is not None:
            revised.close()


def test_heuristic_correspondence_alone_is_not_membership(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    c3b = _open_spine(tmp_path, PAYMENT_C3B, "c3b")
    revised = None
    try:
        revised, _persisted, _obligation, _catalog, _candidate, subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        current_subject = _callable(c3b, "settleExternal")
        evidence = lookup_class_membership_evidence(
            c3b,
            PAYMENT_PROVIDER_CLASS,
            current_subject,
            prior_world=revised,
            correspondence=[
                {
                    "old_entity": subject,
                    "new_entity": current_subject,
                    "basis": "HEURISTIC",
                    "correspondence_basis": "HEURISTIC",
                }
            ],
            source_by_handle={
                "src/external-settlement.ts": PAYMENT_C3B["src/external-settlement.ts"]
            },
            authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT},
        )
        assert evidence.status == MEMBERSHIP_STATUS_UNKNOWN
        assert evidence.correspondence_used
    finally:
        _close(s0, governed, c3b)
        if revised is not None:
            revised.close()


def test_missing_capability_and_changed_mechanical_dependency_are_unknown(tmp_path):
    s0 = _open_spine(tmp_path, PAYMENT_S0, "s0")
    governed = _authority_world(tmp_path, PAYMENT_C3, "c3")
    empty = ConstructionWorld.create(tmp_path / "empty.sqlite", world_id="empty")
    revised = None
    try:
        revised, _persisted, _obligation, _catalog, _candidate, subject, _text = (
            _persist_membership(tmp_path, governed, PAYMENT_C3, "c3")
        )
        missing = lookup_class_membership_evidence(
            empty,
            PAYMENT_PROVIDER_CLASS,
            subject,
            prior_world=revised,
        )
        assert missing.status == MEMBERSHIP_STATUS_UNKNOWN
        c3 = _open_spine(tmp_path, PAYMENT_C3, "c3-mech")
        try:
            mechanical = lookup_class_membership_evidence(
                c3,
                PAYMENT_PROVIDER_CLASS,
                _callable(c3, "settleExternal"),
                prior_world=revised,
                source_by_handle={
                    "src/external-settlement.ts": PAYMENT_C3["src/external-settlement.ts"]
                },
                authority_by_handle={AUTHORITY_HANDLE: AUTHORITY_TEXT + " changed grounding"},
            )
            assert mechanical.status == MEMBERSHIP_STATUS_UNKNOWN
        finally:
            c3.close()
    finally:
        empty.close()
        _close(s0, governed)
        if revised is not None:
            revised.close()

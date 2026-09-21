"""Conformance matrix for maintenance dependency evaluation.

Each admitted dependency kind has distinct semantics over a
``SpineComparisonResult``:

* ``program_identity`` asks whether the program identity continued.
* ``structural_context`` asks whether the recorded structural context
  remained valid for a continued identity.
* ``relation_tuple`` asks whether the exact recorded relation tuple
  survived, by bucket.
* ``manifestation_property`` asks whether a named recorded manifestation
  property remained stable for a continued identity, read from the
  authoritative per-property correspondence comparison.

Real-fixture tests use the payment spine; mapping branches that no
fixture can reach (ambiguous/unresolved/no-match correspondence,
unproduced relation payloads) are pinned with synthetic comparisons.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from experiments import run_payment_semantic_persistence_experiment as payment
from ontology_author.program_spine import compare_program_spines
from ontology_author.program_spine.comparison import (
    CorrespondenceClaim,
    ProgramDelta,
    SpineComparisonResult,
)
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.semantic_binding import (
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
    maintain_semantic_commitment,
    materialize_semantic_commitment_revision,
)
from tests.test_authority_construction import _spine

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


def _claim(
    old_entity: str,
    new_entity: str | None,
    continuity: str,
    changes: dict[str, str] | None = None,
) -> CorrespondenceClaim:
    return CorrespondenceClaim(
        old_entity=old_entity,
        new_entity=new_entity,
        continuity=continuity,
        outcome="UNCHANGED_OR_CONTINUED",
        basis_class="HEURISTIC",
        evidence=(),
        changes=dict(changes or {}),
    )


def _comparison(
    claims: list[CorrespondenceClaim],
    relations: dict[str, Any] | None = None,
    manifestations: tuple = (),
) -> SpineComparisonResult:
    return SpineComparisonResult(
        receipt=SimpleNamespace(comparison_id="comparison:test"),
        correspondences=tuple(claims),
        groups=(),
        delta=ProgramDelta(
            old_snapshot="s0",
            new_snapshot="s1",
            identity={},
            manifestations=manifestations,
            relations=dict(relations or {}),
        ),
    )


def _warrant(depends_on: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "assertion_id": "assertion:test",
        "obligation_id": "obligation:test",
        "snapshot_id": "snapshot:s0",
        "evidence_refs": [],
        "support_kind": "PROGRAM_RESOLVED",
        "resolution_basis": {},
        "depends_on": depends_on,
        "admission_profile": "semantic-binding/v1",
        "admission_decision_id": "decision:test",
    }


def _single_status(dependency: dict[str, Any], comparison) -> tuple[str, dict]:
    result = maintain_semantic_commitment(_warrant([dependency]), comparison)
    assert len(result["assessments"]) == 1
    assessment = result["assessments"][0]
    return assessment["status"], assessment["evidence"]


@pytest.fixture(scope="module")
def payment_worlds(tmp_path_factory):
    scratch = tmp_path_factory.mktemp("dependency-conformance")
    old, new, comparison, _maintenance, _impact, case, endpoints, relations = (
        payment._setup(scratch)
    )
    try:
        old_snapshot = snapshot_id(old)
        source = payment._bounded_source(
            old, endpoints, endpoints["checkout_entry"], old_snapshot
        )
        dependencies = payment._payment_dependencies(endpoints, relations)
        catalog = build_semantic_construction_catalog(
            payment._obligation(case, endpoints),
            case,
            bounded_program_source=source,
            maintenance_dependencies=dependencies,
            program_endpoint_kinds=payment._program_endpoint_kinds(old),
        )
        obligation = payment._obligation(case, endpoints)
        draft = payment._draft(obligation, catalog, endpoints, relations)
        candidate = compile_semantic_candidate_draft(
            obligation,
            catalog,
            draft,
            construction_method="deterministic conformance control",
        )
        decision = admit_semantic_candidate(
            obligation, candidate, catalog, snapshot_id=snapshot_id(old)
        )
        materialized = materialize_semantic_commitment_revision(
            old,
            scratch / "g1",
            obligation,
            candidate,
            decision,
            catalog,
            snapshot_id=snapshot_id(old),
        )
        yield {
            "scratch": scratch,
            "endpoints": endpoints,
            "comparison": comparison,
            "warrant": materialized["warrant"],
        }
    finally:
        old.close()
        new.close()


def _assessments_by_kind(result: dict, kind: str) -> list[dict]:
    return [
        item
        for item in result["assessments"]
        if item["dependency"].get("kind") == kind
    ]


# program_identity


def test_identity_continued_is_preserved(payment_worlds):
    result = maintain_semantic_commitment(
        payment_worlds["warrant"], payment_worlds["comparison"]
    )
    service = payment_worlds["endpoints"]["service"]
    matches = [
        item
        for item in _assessments_by_kind(result, "program_identity")
        if item["dependency"].get("program_entity") == service
    ]
    assert len(matches) == 1
    assert matches[0]["status"] == "PRESERVED"


def test_identity_ambiguous_is_unknown():
    status, evidence = _single_status(
        {"kind": "program_identity", "program_entity": "old:e"},
        _comparison([_claim("old:e", None, "AMBIGUOUS")]),
    )
    assert status == "UNKNOWN"
    assert "ambiguous" in str(evidence)


def test_identity_unresolved_is_not_comparable():
    for claims in (
        [_claim("old:e", None, "UNRESOLVED")],
        [],
    ):
        status, _ = _single_status(
            {"kind": "program_identity", "program_entity": "old:e"},
            _comparison(claims),
        )
        assert status == "NOT_COMPARABLE"


def test_identity_no_match_is_lost():
    status, _ = _single_status(
        {"kind": "program_identity", "program_entity": "old:e"},
        _comparison([_claim("old:e", None, "NO_MATCH")]),
    )
    assert status == "LOST"


# relation_tuple


def test_tuple_preserved_and_retargeted(payment_worlds):
    result = maintain_semantic_commitment(
        payment_worlds["warrant"], payment_worlds["comparison"]
    )
    tuples = _assessments_by_kind(result, "relation_tuple")
    assert tuples
    assert {item["evidence"]["bucket"] for item in tuples} >= {
        "preserved",
        "retargeted",
    }
    for item in tuples:
        assert item["status"] in {"PRESERVED", "CHANGED"}
        if item["evidence"]["bucket"] == "retargeted":
            assert item["status"] == "CHANGED"
            assert item["evidence"]["evidence"].get("old")
            assert item["evidence"]["evidence"].get("new")


def test_tuple_removed_is_lost(payment_worlds):
    scratch = payment_worlds["scratch"]
    checkout_src = payment.PAYMENT_S0["src/checkout.ts"]
    assert "authorize(" in checkout_src
    removed_files = dict(payment.PAYMENT_S0)
    removed_files["src/checkout.ts"] = (
        "export function checkout(amount: number): string { return 'done'; }\n"
    )
    _spine(scratch, removed_files, "call-removed-spine")
    removed = compare_program_spines(
        scratch / "baseline-spine", scratch / "call-removed-spine"
    )
    result = maintain_semantic_commitment(payment_worlds["warrant"], removed)
    tuples = _assessments_by_kind(result, "relation_tuple")
    lost = [item for item in tuples if item["evidence"].get("bucket") == "removed"]
    assert lost, "the dropped call must land in the removed bucket"
    assert all(item["status"] == "LOST" for item in lost)


def test_tuple_unresolved_is_unknown():
    recorded = {"relation": "program_invokes", "caller": "a", "callee": "b"}
    status, evidence = _single_status(
        {"kind": "relation_tuple", "recorded": recorded},
        _comparison(
            [],
            {
                "program_invokes": {
                    "status": "COMPARABLE",
                    "unresolved": [{"old": dict(recorded)}],
                }
            },
        ),
    )
    assert status == "UNKNOWN"
    assert evidence["bucket"] == "unresolved"


def test_tuple_incomparable_payload_is_not_comparable():
    for payload_status in ("NOT_COMPARABLE", "NOT_PRODUCED"):
        status, evidence = _single_status(
            {
                "kind": "relation_tuple",
                "recorded": {"relation": "program_invokes"},
            },
            _comparison(
                [],
                {"program_invokes": {"status": payload_status}},
            ),
        )
        assert status == "NOT_COMPARABLE"
        assert evidence["evidence"]["status"] == payload_status


def test_tuple_missing_from_buckets_is_unknown():
    status, _ = _single_status(
        {
            "kind": "relation_tuple",
            "recorded": {"relation": "program_invokes", "caller": "ghost"},
        },
        _comparison([], {"program_invokes": {"status": "COMPARABLE"}}),
    )
    assert status == "UNKNOWN"


# structural_context


def test_structural_context_follows_changes_not_identity():
    continued = {
        "name": "PRESERVED",
        "source_location": "PRESERVED",
        "source_manifestation": "PRESERVED",
        "structural_context": "PRESERVED",
        "signature": "PRESERVED",
        "boundary": "PRESERVED",
        "identity_kind": "PRESERVED",
    }
    status, _ = _single_status(
        {"kind": "structural_context", "program_entity": "old:e"},
        _comparison([_claim("old:e", "new:e", "CONTINUED", dict(continued))]),
    )
    assert status == "PRESERVED"
    moved = dict(continued, structural_context="CHANGED")
    status, evidence = _single_status(
        {"kind": "structural_context", "program_entity": "old:e"},
        _comparison([_claim("old:e", "new:e", "CONTINUED", moved)]),
    )
    assert status == "CHANGED"
    assert evidence["structural_context"] == "CHANGED"


def test_structural_context_uncertainty_ladder():
    dependency = {"kind": "structural_context", "program_entity": "old:e"}
    status, _ = _single_status(
        dependency, _comparison([_claim("old:e", None, "AMBIGUOUS")])
    )
    assert status == "UNKNOWN"
    for claims in ([_claim("old:e", None, "UNRESOLVED")], []):
        status, _ = _single_status(dependency, _comparison(claims))
        assert status == "NOT_COMPARABLE"
    status, _ = _single_status(
        dependency, _comparison([_claim("old:e", None, "NO_MATCH")])
    )
    assert status == "LOST"


# manifestation_property


def test_manifestation_reads_correspondence_changes():
    base = {
        "name": "PRESERVED",
        "source_location": "PRESERVED",
        "source_manifestation": "PRESERVED",
        "structural_context": "PRESERVED",
        "signature": "PRESERVED",
        "boundary": "PRESERVED",
        "identity_kind": "PRESERVED",
    }
    dependency = {
        "kind": "manifestation_property",
        "program_entity": "old:e",
        "property": "signature",
    }
    status, _ = _single_status(
        dependency,
        _comparison([_claim("old:e", "new:e", "CONTINUED", dict(base))]),
    )
    assert status == "PRESERVED"
    changed = dict(base, signature="CHANGED")
    status, evidence = _single_status(
        dependency,
        _comparison([_claim("old:e", "new:e", "CONTINUED", changed)]),
    )
    assert status == "CHANGED"
    assert evidence["change"] == "CHANGED"


def test_manifestation_absent_from_sparse_delta_is_preserved():
    # delta.manifestations lists only changed manifestations, so absence
    # beside a unique continued correspondence means preserved, not unknown.
    base = {
        "name": "PRESERVED",
        "source_location": "PRESERVED",
        "source_manifestation": "PRESERVED",
        "structural_context": "PRESERVED",
        "signature": "PRESERVED",
        "boundary": "PRESERVED",
        "identity_kind": "PRESERVED",
    }
    status, _ = _single_status(
        {
            "kind": "manifestation_property",
            "program_entity": "old:e",
            "property": "source_manifestation",
        },
        _comparison(
            [_claim("old:e", "new:e", "CONTINUED", dict(base))],
            manifestations=(),
        ),
    )
    assert status == "PRESERVED"


def test_manifestation_unassessed_property_is_unknown():
    status, evidence = _single_status(
        {
            "kind": "manifestation_property",
            "program_entity": "old:e",
            "property": "lineage",
        },
        _comparison([_claim("old:e", "new:e", "CONTINUED", {"name": "PRESERVED"})]),
    )
    assert status == "UNKNOWN"
    assert "lineage" in str(evidence)


def test_manifestation_uncertainty_ladder():
    dependency = {
        "kind": "manifestation_property",
        "program_entity": "old:e",
        "property": "signature",
    }
    status, _ = _single_status(
        dependency, _comparison([_claim("old:e", None, "AMBIGUOUS")])
    )
    assert status == "UNKNOWN"
    for claims in ([_claim("old:e", None, "UNRESOLVED")], []):
        status, _ = _single_status(dependency, _comparison(claims))
        assert status == "NOT_COMPARABLE"
    status, _ = _single_status(
        dependency, _comparison([_claim("old:e", None, "NO_MATCH")])
    )
    assert status == "LOST"


def test_manifestation_unrelated_add_preserves(payment_worlds):
    scratch = payment_worlds["scratch"]
    unrelated_files = dict(payment.PAYMENT_S0)
    unrelated_files["src/unrelated.ts"] = (
        "export function helper(): number { return 41; }\n"
    )
    _spine(scratch, unrelated_files, "unrelated-spine")
    unrelated = compare_program_spines(
        scratch / "baseline-spine", scratch / "unrelated-spine"
    )
    result = maintain_semantic_commitment(payment_worlds["warrant"], unrelated)
    assert result["status"] == "PRESERVED"
    assert all(
        item["status"] == "PRESERVED" for item in result["assessments"]
    )


def test_manifestation_body_change_is_changed(payment_worlds):
    result = maintain_semantic_commitment(
        payment_worlds["warrant"], payment_worlds["comparison"]
    )
    assert result["status"] == "CHANGED"
    assert any(
        item["status"] == "CHANGED" for item in result["assessments"]
    )


def test_manifestation_same_file_neighbor_control(payment_worlds):
    # The spine records file content digests, not entity content digests, so
    # a same-file edit outside the bound entity still moves its recorded
    # manifestation while leaving its byte location preserved. This pins the
    # current file-revision granularity rather than entity granularity.
    scratch = payment_worlds["scratch"]
    neighbor_files = dict(payment.PAYMENT_S0)
    neighbor_files["src/stripe-client.ts"] = (
        payment.PAYMENT_S0["src/stripe-client.ts"]
        + "\nexport function auditTrail(): string { return 'audit'; }\n"
    )
    _spine(scratch, neighbor_files, "neighbor-spine")
    neighbor = compare_program_spines(
        scratch / "baseline-spine", scratch / "neighbor-spine"
    )
    provider = payment_worlds["endpoints"]["provider"]
    claims = [
        item for item in neighbor.correspondences if item.old_entity == provider
    ]
    assert len(claims) == 1 and claims[0].continuity == "CONTINUED"
    assert claims[0].changes["source_manifestation"] == "CHANGED"
    result = maintain_semantic_commitment(payment_worlds["warrant"], neighbor)
    provider_manifests = [
        item
        for item in result["assessments"]
        if item["dependency"].get("kind") == "manifestation_property"
        and item["dependency"].get("program_entity") == provider
        and item["dependency"].get("property") == "source_manifestation"
    ]
    assert len(provider_manifests) == 1
    assert provider_manifests[0]["status"] == "CHANGED"

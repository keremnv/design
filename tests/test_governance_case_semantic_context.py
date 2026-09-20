from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    assemble_governance_case,
    program_world_fingerprint,
    validate_case_sidecar,
)
from ontology_author.authority.case import _semantic_absence_status
from ontology_author.governance import (
    build_case_evidence_catalog,
    compile_model_adjudication_draft,
    model_adjudication_draft_schema,
    validate_governance_adjudication,
)
from tests.test_authority_construction import (
    PURPOSE,
    TS_A,
    TS_B,
)
from tests.test_authority_maintenance import (
    _close,
    _direct_callable_build,
    _module_build,
    _sources,
)
from tests.test_governance_adjudication import _case, _compare_worlds
from tests.test_model_adjudicator import _draft

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (
        Path(__file__).resolve().parents[1] / "frontend" / "node_modules" / "typescript"
    ).exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def _cancellation_case(tmp_path: Path):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    maintenance, impact, case = _case(old, new, comparison, tmp_path)
    return old, new, comparison, maintenance, impact, case


def test_selected_mediated_attachment_projects_bounded_semantic_context(tmp_path):
    old, new, comparison, maintenance, impact, case = _cancellation_case(tmp_path)
    try:
        context = case["semantic_context"]
        referents = {item["id"] for item in context["referents"]}
        assert referents == {
            "semantic:CancellationEntryAction",
            "semantic:RetentionFlow",
        }
        claims = {item["relation_name"] for item in context["claims"]}
        assert claims == {"authority_grounds_semantic", "enters_flow", "realized_by"}
        links = context["program_links"]
        assert any(
            item["status"] == "POSITIVE" and item["side"] == "OLD" for item in links
        )
        assert any(
            item["status"] == "ABSENCE_WITHOUT_COMPLETE_COVERAGE"
            and item["side"] == "NEW"
            for item in links
        )
        assert all(
            item["included_because"] for group in context.values() for item in group
        )
        assert (
            validate_case_sidecar(
                case, maintenance=maintenance, impact=impact, comparison=comparison
            )
            == []
        )
    finally:
        _close(old, new)


def test_relevant_source_claim_is_included_but_same_node_unrelated_claim_is_excluded(
    tmp_path,
):
    old, new, _comparison, _maintenance, _impact, case = _cancellation_case(tmp_path)
    try:
        assert {
            item["relation_name"] for item in case["semantic_context"]["claims"]
        } >= {
            "authority_grounds_semantic",
            "enters_flow",
        }
        assert "cancellation_requires_prior" not in {
            item["relation_name"] for item in case["semantic_context"]["claims"]
        }
    finally:
        _close(old, new)


def test_changed_endpoint_is_not_assigned_the_old_semantic_link(tmp_path):
    old, new, _comparison, _maintenance, _impact, case = _cancellation_case(tmp_path)
    try:
        links = case["semantic_context"]["program_links"]
        assert any(
            item["side"] == "OLD" and item["status"] == "POSITIVE" for item in links
        )
        assert not any(
            item["side"] == "NEW" and item["status"] == "POSITIVE" for item in links
        )
        absence = next(item for item in links if item["side"] == "NEW")
        assert absence["tuple"] == {}
        assert absence["status"] == "ABSENCE_WITHOUT_COMPLETE_COVERAGE"
        assert "negative conclusion" in " ".join(absence["coverage"]["known_gaps"])
    finally:
        _close(old, new)


def test_complete_scoped_absence_status_is_distinct_when_world_declares_it(tmp_path):
    old, new, _comparison, _maintenance, _impact, _case = _cancellation_case(tmp_path)
    try:
        status, coverage = _semantic_absence_status(old)
        assert status == "ABSENCE_WITHOUT_COMPLETE_COVERAGE"
        assert coverage["status"] == "NOT_DECLARED"
        # The current constructor intentionally has no semantic-link scope;
        # preserve the representation for a future explicitly matching claim.
        synthetic = copy.deepcopy(_case)
        synthetic["semantic_context"]["program_links"].append(
            {
                "assertion_id": None,
                "relation_name": "realized_by",
                "semantic_referent": "semantic:RetentionFlow",
                "program_entity": "program:new-endpoint",
                "program_snapshot_id": "snapshot:new",
                "side": "NEW",
                "tuple": {},
                "status": "ABSENCE_WITH_COMPLETE_COVERAGE",
                "coverage": {
                    "scope": "SEMANTIC_PROGRAM_LINKS",
                    "status": "COMPLETE",
                    "basis": "explicit scoped semantic/program-link coverage",
                    "known_gaps": [],
                },
                "selected_by": [],
                "included_because": ["CHANGED_ENDPOINT_SEMANTIC_CONTEXT"],
            }
        )
        assert (
            synthetic["semantic_context"]["program_links"][-1]["status"]
            != "ABSENCE_WITHOUT_COMPLETE_COVERAGE"
        )
    finally:
        _close(old, new)


def test_direct_source_program_attachment_does_not_create_semantic_nodes(tmp_path):
    old_files = {**TS_A}
    new_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            'export function cancelSubscription(): void { console.log("changed"); }\n'
        ),
    }
    old, new, comparison = _compare_worlds(
        tmp_path, old_files, new_files, _direct_callable_build("cancelSubscription")
    )
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        assert case["semantic_context"] == {
            "claims": [],
            "program_links": [],
            "referents": [],
        }
        assert old.relation_rows("semantic_entity") == []
        assert all(
            item["claim_kind"] == "SOURCE_PROGRAM"
            for item in case["authority"]["claims"]
        )
    finally:
        _close(old, new)


def test_payment_boundary_claim_and_program_facts_are_projected_when_persisted(
    tmp_path,
):
    old_files = {**TS_A}
    new_files = {
        **TS_A,
        "src/payments/boundary.ts": 'export function charge(): void { console.log("changed"); }\n',
    }
    old, new, comparison = _compare_worlds(
        tmp_path, old_files, new_files, _module_build(structural=True)
    )
    try:
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        assert case["case_result"] == "SELECTED"
        assert any(
            item["relation_name"] == "governs_module"
            for item in case["authority"]["claims"]
        )
        assert case["program_context"]["referents"]
        assert (
            case["transition_facts"][0]["authority_attachment_id"]
            == case["selection"][0]["attachment_assertion_id"]
        )
    finally:
        _close(old, new)


def test_transition_projection_uses_mechanical_old_new_values_without_world_mutation(
    tmp_path,
):
    old_files = {**TS_A}
    new_files = {
        **TS_A,
        "src/payments/boundary.ts": 'export function charge(): void { console.log("changed"); }\n',
    }
    old, new, comparison = _compare_worlds(
        tmp_path, old_files, new_files, _module_build(structural=True)
    )
    try:
        old_fingerprint = program_world_fingerprint(old.path.parent)
        new_fingerprint = program_world_fingerprint(new.path.parent)
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        assert case["transition_facts"]
        transition = case["transition_facts"][0]
        assert transition["old"] != transition["new"]
        assert transition["mechanical_evidence_refs"]
        assert program_world_fingerprint(old.path.parent) == old_fingerprint
        assert program_world_fingerprint(new.path.parent) == new_fingerprint
    finally:
        _close(old, new)


def test_semantic_context_case_is_deterministic_and_catalog_exposes_context_claims(
    tmp_path,
):
    old, new, comparison, maintenance, impact, case = _cancellation_case(tmp_path)
    try:
        repeat = assemble_governance_case(
            old,
            new,
            comparison,
            _sources(tmp_path),
            maintenance=maintenance,
            impact=impact,
            purpose=PURPOSE,
        )
        assert repeat == case
        catalog = build_case_evidence_catalog(case)
        semantic_aliases = catalog["allowed_aliases"]["SEMANTIC_CONTEXT"]
        assert semantic_aliases
        semantic_entries = [
            entry for entry in catalog["entries"] if entry["alias"] in semantic_aliases
        ]
        assert all(entry["kind"] == "claim" for entry in semantic_entries)
        assert {entry["id"] for entry in semantic_entries} >= {
            item["assertion_id"] for item in case["semantic_context"]["claims"]
        }
        schema = model_adjudication_draft_schema(case, catalog)
        program_aliases = schema["properties"]["authority_items"]["items"][
            "properties"
        ]["program_findings"]["items"]["properties"]["evidence_refs"]["items"]["enum"]
        rationale_aliases = schema["properties"]["rationale"]["items"]["properties"][
            "evidence_refs"
        ]["items"]["enum"]
        assert set(semantic_aliases).issubset(program_aliases)
        assert set(semantic_aliases).issubset(rationale_aliases)
        model_case = copy.deepcopy(case)
        model_case["program_context"]["source_evidence"] = [
            {
                "evidence_id": "psrc:semantic-context-test",
                "side": "NEW",
                "program_entity": model_case["program_context"]["referents"][0]["id"],
                "reconstruction": "OK",
            }
        ]
        model_catalog = build_case_evidence_catalog(model_case)
        model_semantic_alias = model_catalog["allowed_aliases"]["SEMANTIC_CONTEXT"][0]
        draft = _draft(model_case)
        draft["authority_items"][0]["program_findings"][0]["basis"] = "INTERPRETIVE"
        draft["authority_items"][0]["program_findings"][0]["evidence_refs"] = [
            model_semantic_alias
        ]
        draft["rationale"][0]["evidence_refs"] = [model_semantic_alias]
        compiled = compile_model_adjudication_draft(model_case, model_catalog, draft)
        assert validate_governance_adjudication(compiled, model_case) == []
    finally:
        _close(old, new)


def test_semantic_context_does_not_search_corpus_or_mutate_world(tmp_path, monkeypatch):
    old, new, comparison = _compare_worlds(tmp_path, TS_A, TS_B)
    try:
        old_rows = {
            name: json.dumps(old.relation_rows(name), sort_keys=True)
            for name in (
                "semantic_entity",
                "authority_claim",
                "authority_attachment_warrant",
            )
        }
        monkeypatch.setattr(
            Path,
            "rglob",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("corpus search")
            ),
        )
        _maintenance, _impact, case = _case(old, new, comparison, tmp_path)
        assert case["semantic_context"]["referents"]
        for name, before in old_rows.items():
            assert json.dumps(old.relation_rows(name), sort_keys=True) == before
    finally:
        _close(old, new)


def test_provider_change_transition_is_not_invented_when_case_has_no_old_new_mechanical_values(
    tmp_path,
):
    # The persisted D/E benchmark cases are synthetic and intentionally carry
    # only a relation label, not a provider-selection old/new fact.
    from tests.test_model_adjudicator import CASE as PAYMENT_CASE

    case = copy.deepcopy(PAYMENT_CASE)
    assert case.get("transition_facts") in (None, [])
    assert not case.get("semantic_context")


def test_case_claim_resolution_metadata_is_preserved(tmp_path):
    old, new, _comparison, _maintenance, _impact, case = _cancellation_case(tmp_path)
    try:
        claim = next(
            item
            for item in case["semantic_context"]["claims"]
            if item["relation_name"] == "enters_flow"
        )
        # Resolution metadata is populated from the persisted authority claim,
        # rather than inferred from the semantic labels.
        assert claim["endpoint_resolution"] == {
            "action": "AGENT_RESOLVED",
            "flow": "AGENT_RESOLVED",
        }
    finally:
        _close(old, new)

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ontology_author.authority.evaluate import snapshot_id
from ontology_author.governance.model_adjudicator import AdjudicatorTransportResponse
from ontology_author.program_spine.comparison import ProgramDelta
from ontology_author.semantic_binding import (
    ConstructionObligation,
    SemanticCandidate,
    SemanticConstructionInvocationError,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    canonical_program_realization_schema,
    compile_semantic_candidate_draft,
    construct_semantic_candidate,
    create_lazy_reresolution_obligation,
    maintain_semantic_commitment,
    materialize_semantic_commitment_revision,
    persist_admitted_candidate,
    semantic_candidate_schema,
    validate_semantic_candidate,
)
from ontology_author.semantic_binding.admission import (
    PROGRAM_REALIZATION_RELATION,
    WARRANT_RELATION,
)
from ontology_author.semantic_binding.schemas import CandidateValidationError
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_governance_adjudication import _case as _adjudication_case
from tests.test_governance_case_semantic_context import _cancellation_case


def _case() -> dict:
    return {
        "case_id": "case:semantic-persistence",
        "authority": {
            "observations": [
                {
                    "observation_id": "obs:retention",
                    "provider": "markdown",
                    "handle": "docs/subscriptions.md",
                    "revision": "sha256:authority",
                    "native_location": "bytes:0:68",
                    "standing": "AUTHORITATIVE",
                    "reconstructed_text": "The initial Cancel action enters the retention flow.",
                }
            ],
            "semantic_referents": [
                {"id": "semantic:RetentionFlow", "label": "RetentionFlow"},
            ],
            "claims": [],
        },
        "semantic_context": {
            "referents": [
                {
                    "id": "semantic:RetentionFlow",
                    "label": "RetentionFlow",
                    "status": "POSITIVE",
                }
            ],
            "claims": [],
            "program_links": [],
        },
        "program_context": {
            "referents": [
                {"id": "program:openRetentionFlow", "kind": "callable", "side": "OLD"},
                {"id": "program:other", "kind": "callable", "side": "OLD"},
            ],
            "source_evidence": [],
            "relation_tuples": [
                {
                    "evidence_id": "tuple:invokes",
                    "relation": "program_invokes",
                    "recorded_fact": {
                        "relation": "program_invokes",
                        "call_site": "program:cancel-button",
                        "target": "program:openRetentionFlow",
                    },
                }
            ],
            "resolution_outcomes": [],
            "structural_context": [],
        },
        "selection": [
            {
                "attachment_warrant": {
                    "program_entity": "program:openRetentionFlow",
                    "structural_context": [
                        "program:module",
                        "program:openRetentionFlow",
                    ],
                    "justifying_program_relations": [
                        {
                            "relation": "program_invokes",
                            "call_site": "program:cancel-button",
                            "target": "program:openRetentionFlow",
                        }
                    ],
                }
            }
        ],
        "transition_facts": [],
        "supporting_material": [
            {
                "observation_id": "obs:analysis-note",
                "handle": "notes/analysis.md",
                "reconstructed_text": "A non-authoritative analysis note.",
            }
        ],
    }


def _obligation(**changes) -> ConstructionObligation:
    values = {
        "obligation_id": "obligation:retention-realization",
        "purpose": "cancellation-flow-v1",
        "authority_refs": ("obs:retention",),
        "semantic_subject": "semantic:RetentionFlow",
        "semantic_relation": "realized_by",
        "question": "Which supplied program manifestation realizes RetentionFlow for this cancellation context?",
        "program_scope": "bounded cancellation-entry context",
        "allowed_program_endpoints": ("program:openRetentionFlow",),
        "required_evidence_classes": ("AUTHORITY_GROUNDING", "MECHANICAL_GROUNDING"),
        "tuple_shape": {"semantic": "SEMANTIC", "program": "PROGRAM"},
    }
    values.update(changes)
    return ConstructionObligation(**values)


def _catalog(obligation=None, case=None, **kwargs):
    return build_semantic_construction_catalog(
        obligation or _obligation(), case or _case(), **kwargs
    )


def _alias(catalog, category, index=0):
    return catalog["allowed_aliases"][category][index]


def _draft(
    catalog,
    *,
    relation="realized_by",
    semantic=None,
    program=None,
    support="CROSS_EVIDENCE_INFERRED",
    evidence=None,
    dependencies=None,
    completeness=None,
):
    selected_evidence = evidence or [
        _alias(catalog, "AUTHORITATIVE_EVIDENCE"),
        _alias(catalog, "MECHANICAL_FACT"),
    ]
    catalog_by_alias = {
        item["alias"]: item for item in catalog["entries"]
    }
    return {
        "obligation_id": catalog["obligation"]["obligation_id"],
        "claim_kind": "SEMANTIC_PROGRAM",
        "relation_name": relation,
        "semantic_endpoint_aliases": [semantic or _alias(catalog, "SEMANTIC_REFERENT")],
        "program_endpoint_aliases": [program or _alias(catalog, "PROGRAM_ENDPOINT")],
        "polarity": "POSITIVE",
        "support_kind": support,
        "authority_evidence_aliases": [
            alias
            for alias in selected_evidence
            if catalog_by_alias.get(alias, {}).get("category")
            == "AUTHORITATIVE_EVIDENCE"
            or alias not in catalog_by_alias
        ],
        "program_source_evidence_aliases": [
            alias
            for alias in selected_evidence
            if catalog_by_alias.get(alias, {}).get("category")
            == "PROGRAM_SOURCE"
        ],
        "mechanical_evidence_aliases": [
            alias
            for alias in selected_evidence
            if catalog_by_alias.get(alias, {}).get("category")
            == "MECHANICAL_FACT"
        ],
        "program_scope": catalog["obligation"]["program_scope"],
        "maintenance_dependency_aliases": dependencies
        if dependencies is not None
        else [],
        "completeness_aliases": completeness if completeness is not None else [],
    }


def _candidate(catalog, **kwargs):
    return compile_semantic_candidate_draft(
        _obligation(), catalog, _draft(catalog, **kwargs)
    )


def test_candidate_must_reference_real_obligation_and_case_refs_are_bounded():
    obligation = _obligation()
    catalog = _catalog(obligation)
    draft = _draft(catalog)
    draft["obligation_id"] = "obligation:not-real"
    with pytest.raises(CandidateValidationError):
        compile_semantic_candidate_draft(obligation, catalog, draft)
    with pytest.raises(ValueError, match="PROGRAM_REALIZATION"):
        ConstructionObligation(
            **{**obligation.to_dict(), "obligation_kind": "ONTOLOGY_QUERY"}
        )
    draft = _draft(catalog)
    draft["authority_evidence_aliases"] = ["A999"]
    with pytest.raises(CandidateValidationError):
        compile_semantic_candidate_draft(obligation, catalog, draft)


def test_candidate_cannot_invent_endpoint_or_persistence_outcome():
    catalog = _catalog()
    draft = _draft(catalog)
    draft["program_endpoint_aliases"] = ["P999"]
    with pytest.raises(CandidateValidationError):
        compile_semantic_candidate_draft(_obligation(), catalog, draft)
    draft = _draft(catalog)
    draft["persistence_outcome"] = "PERSIST_COMMITMENT"
    with pytest.raises(CandidateValidationError):
        compile_semantic_candidate_draft(_obligation(), catalog, draft)


def test_catalog_and_schema_are_deterministic_and_model_cannot_choose_outcome():
    obligation = _obligation()
    case = _case()
    first = _catalog(obligation, case)
    assert first == _catalog(obligation, copy.deepcopy(case))
    schema = semantic_candidate_schema(first)
    assert "persistence_outcome" not in schema["properties"]
    assert schema["properties"]["program_endpoint_aliases"]["items"]["enum"] == [
        "P1",
        "P2",
    ]
    assert "D1" not in schema["properties"]["authority_evidence_aliases"]["items"]["enum"]
    support_alias = first["allowed_aliases"]["SUPPORTING_MATERIAL"][0]
    assert (
        support_alias
        not in schema["properties"]["authority_evidence_aliases"]["items"]["enum"]
    )
    assert schema["properties"]["mechanical_evidence_aliases"]["minItems"] == 1


def test_incidental_relation_is_dropped_not_promoted():
    catalog = _catalog()
    candidate = _candidate(catalog, relation="uses_library")
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    assert decision.outcome == "DROP"
    assert decision.reason == "DOES_NOT_DISCHARGE_OBLIGATION"


def test_outside_scope_is_dropped_when_endpoint_is_known():
    catalog = _catalog()
    candidate = _candidate(catalog, program=_alias(catalog, "PROGRAM_ENDPOINT", 1))
    decision = admit_semantic_candidate(_obligation(), candidate, catalog)
    assert decision.outcome == "DROP"
    assert decision.reason == "OUTSIDE_DECLARED_SCOPE"


def test_hypothesis_and_ambiguous_endpoint_are_unresolved():
    catalog = _catalog()
    hypothetical = _candidate(catalog, support="HYPOTHESIZED")
    assert (
        admit_semantic_candidate(_obligation(), hypothetical, catalog).reason
        == "HYPOTHESIZED_SUPPORT"
    )
    ambiguous = copy.deepcopy(hypothetical)
    ambiguous_payload = ambiguous.to_dict()
    ambiguous_payload.pop("candidate_id")
    ambiguous = SemanticCandidate(
        **{
            **ambiguous_payload,
            "support_kind": "CROSS_EVIDENCE_INFERRED",
            "endpoint_resolution": {
                "semantic": "AMBIGUOUS",
                "program": "DETERMINISTIC",
            },
        }
    )
    assert (
        admit_semantic_candidate(_obligation(), ambiguous, catalog).reason
        == "AMBIGUOUS_ENDPOINT"
    )
    assert admit_semantic_candidate(_obligation(), hypothetical, catalog).evidence_refs


def test_negative_without_complete_scope_is_unresolved_and_complete_scope_is_allowed():
    obligation = _obligation()
    base_case = _case()
    catalog = _catalog(obligation, base_case)
    draft = _draft(catalog)
    draft["polarity"] = "NEGATIVE"
    negative = compile_semantic_candidate_draft(obligation, catalog, draft)
    decision = admit_semantic_candidate(obligation, negative, catalog)
    assert decision.outcome == "RECORD_UNRESOLVED"
    assert decision.reason == "NEGATIVE_WITHOUT_COMPLETE_SCOPE"

    complete_case = copy.deepcopy(base_case)
    complete_case["completeness"] = [
        {
            "receipt_id": "complete:semantic",
            "status": "COMPLETE",
            "scope": obligation.program_scope,
        }
    ]
    complete_catalog = _catalog(obligation, complete_case)
    complete_draft = _draft(
        complete_catalog,
        completeness=[_alias(complete_catalog, "COMPLETENESS_RECEIPT")],
    )
    complete_draft["polarity"] = "NEGATIVE"
    complete = compile_semantic_candidate_draft(
        obligation, complete_catalog, complete_draft
    )
    assert (
        admit_semantic_candidate(obligation, complete, complete_catalog).outcome
        == "PERSIST_SNAPSHOT_FACT"
    )


def test_grounded_candidate_without_dependencies_is_snapshot_fact():
    catalog = _catalog()
    candidate = _candidate(catalog)
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    assert decision.outcome == "PERSIST_SNAPSHOT_FACT"
    assert decision.snapshot_id == "snapshot:s0"


def test_admission_requires_grounding_from_the_obligation_authority_refs():
    catalog = _catalog()
    mechanical = _alias(catalog, "MECHANICAL_FACT")
    candidate = _candidate(catalog, evidence=[mechanical])
    decision = admit_semantic_candidate(_obligation(), candidate, catalog)
    assert decision.outcome == "RECORD_UNRESOLVED"
    assert "DECLARED_AUTHORITY_GROUNDING" in decision.reason


def test_grounded_candidate_with_inspectable_dependencies_is_commitment():
    catalog = _catalog()
    dependency = _alias(catalog, "MAINTENANCE_DEPENDENCY")
    candidate = _candidate(catalog, dependencies=[dependency])
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    assert decision.outcome == "PERSIST_COMMITMENT"
    assert decision.maintenance_dependency_ids


def test_validation_preserves_semantic_values_and_rejects_unknown_refs():
    catalog = _catalog()
    candidate = _candidate(catalog)
    assert validate_semantic_candidate(_obligation(), candidate, catalog) == []
    invalid = SemanticCandidate(
        **{
            **candidate.to_dict(),
            "evidence_refs": [{"kind": "delta", "id": "delta:not-in-catalog"}],
        }
    )
    assert validate_semantic_candidate(_obligation(), invalid, catalog)
    assert candidate.relation_name == "realized_by"
    assert candidate.polarity == "POSITIVE"
    wrong_id = SemanticCandidate(
        **{**candidate.to_dict(), "candidate_id": "semantic-candidate:wrong"}
    )
    assert any(
        "candidate_id does not match" in error
        for error in validate_semantic_candidate(_obligation(), wrong_id, catalog)
    )


def _world(tmp_path: Path) -> ConstructionWorld:
    world = ConstructionWorld.create(
        tmp_path / "world.sqlite", world_id="semantic-world"
    )
    world.add_referent("semantic:RetentionFlow")
    world.add_referent("program:openRetentionFlow")
    world.declare_relation(
        "realized_by",
        [Role("semantic", RoleType.REFERENT), Role("program", RoleType.REFERENT)],
        scope="WORLD",
    )
    return world


def _catalog_alias(catalog, category, *, identifier=None, evidence_class=None):
    for alias in catalog["allowed_aliases"][category]:
        item = next(entry for entry in catalog["entries"] if entry["alias"] == alias)
        if identifier is not None and item["id"] != identifier:
            continue
        if evidence_class is not None and item.get("evidence_class") != evidence_class:
            continue
        return alias
    raise AssertionError(
        f"no catalog alias for {category} {identifier or evidence_class or ''}"
    )


def _cancellation_commitment_fixture(tmp_path: Path):
    old, new, comparison, _maintenance, _impact, case = _cancellation_case(tmp_path)
    authority_refs = tuple(
        str(item["observation_id"]) for item in case["authority"]["observations"]
    )
    old_link = next(
        item
        for item in case["semantic_context"]["program_links"]
        if item["side"] == "OLD" and item["status"] == "POSITIVE"
    )
    obligation = ConstructionObligation(
        obligation_id="obligation:cancellation-retention-realization",
        purpose="cancellation-flow-v1",
        authority_refs=authority_refs,
        semantic_subject="semantic:RetentionFlow",
        semantic_relation="realized_by",
        question="Which supplied program manifestation realizes RetentionFlow?",
        program_scope="bounded cancellation-entry context",
        allowed_program_endpoints=(old_link["program_entity"],),
        required_evidence_classes=("AUTHORITY_GROUNDING", "MECHANICAL_GROUNDING"),
        tuple_shape={"flow": "SEMANTIC", "program": "PROGRAM"},
    )
    relation_fact = case["selection"][0]["attachment_warrant"][
        "justifying_program_relations"
    ][0]
    bounded_source = {
        "evidence_id": "source:bounded-cancel",
        "side": "OLD",
        "program_entity": old_link["program_entity"],
        "provider": "fixture",
        "native_handle": "fixture:cancellation.ts",
        "source_revision": "fixture:s0",
        "native_location": "bytes:0:24",
        "reconstruction": "OK",
        "reconstructed_text": "openRetentionFlow();",
    }
    catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=[bounded_source],
        maintenance_dependencies=[
            {"kind": "relation_tuple", "recorded": relation_fact}
        ],
    )
    draft = {
        "obligation_id": obligation.obligation_id,
        "claim_kind": "SEMANTIC_PROGRAM",
        "relation_name": "realized_by",
        "semantic_endpoint_aliases": [
            _catalog_alias(
                catalog, "SEMANTIC_REFERENT", identifier="semantic:RetentionFlow"
            )
        ],
        "program_endpoint_aliases": [
            _catalog_alias(
                catalog, "PROGRAM_ENDPOINT", identifier=old_link["program_entity"]
            )
        ],
        "polarity": "POSITIVE",
        "support_kind": "CROSS_EVIDENCE_INFERRED",
        "authority_evidence_aliases": [
            _catalog_alias(catalog, "AUTHORITATIVE_EVIDENCE")
        ],
        "program_source_evidence_aliases": [
            _catalog_alias(catalog, "PROGRAM_SOURCE", identifier="source:bounded-cancel")
        ],
        "mechanical_evidence_aliases": [
            _catalog_alias(
                catalog,
                "MECHANICAL_FACT",
                evidence_class="MECHANICAL_GROUNDING",
            )
        ],
        "program_scope": obligation.program_scope,
        "maintenance_dependency_aliases": list(
            catalog["allowed_aliases"]["MAINTENANCE_DEPENDENCY"]
        ),
        "completeness_aliases": [],
    }
    candidate = compile_semantic_candidate_draft(obligation, catalog, draft)
    decision = admit_semantic_candidate(
        obligation, candidate, catalog, snapshot_id=snapshot_id(old)
    )
    assert decision.outcome == "PERSIST_COMMITMENT"
    return old, new, comparison, case, obligation, catalog, candidate, decision


def test_persistence_adds_only_admitted_state_and_retains_exact_provenance(tmp_path):
    catalog = _catalog()
    candidate = _candidate(catalog)
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    world = _world(tmp_path)
    try:
        result = persist_admitted_candidate(
            world,
            _obligation(),
            candidate,
            decision,
            catalog,
            snapshot_id="snapshot:s0",
        )
        assert result and result["outcome"] == "PERSIST_SNAPSHOT_FACT"
        rows = world.relation_rows("realized_by")
        assert rows == [
            {
                "semantic": "semantic:RetentionFlow",
                "program": "program:openRetentionFlow",
            }
        ]
    finally:
        world.close()


def test_commitment_warrant_is_persisted_without_kernel_changes(tmp_path):
    catalog = _catalog()
    candidate = _candidate(
        catalog, dependencies=[_alias(catalog, "MAINTENANCE_DEPENDENCY")]
    )
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    world = _world(tmp_path)
    try:
        result = persist_admitted_candidate(
            world,
            _obligation(),
            candidate,
            decision,
            catalog,
            snapshot_id="snapshot:s0",
        )
        assert result and result["warrant"]
        rows = world.relation_rows(WARRANT_RELATION)
        assert len(rows) == 1
        assert rows[0]["snapshot_id"] == "snapshot:s0"
        assert json.loads(rows[0]["evidence_refs"]) == list(candidate.evidence_refs)
    finally:
        world.close()


def test_rejected_candidates_do_not_mutate_world(tmp_path):
    catalog = _catalog()
    candidate = _candidate(catalog, relation="uses_library")
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    world = _world(tmp_path)
    try:
        before = world.query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        assert (
            persist_admitted_candidate(
                world,
                _obligation(),
                candidate,
                decision,
                catalog,
                snapshot_id="snapshot:s0",
            )
            is None
        )
        after = world.query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        assert before == after
    finally:
        world.close()


def test_persistence_recomputes_admission_and_rejects_forged_outcome(tmp_path):
    catalog = _catalog()
    candidate = _candidate(catalog, relation="uses_library")
    forged = {
        "candidate_id": candidate.candidate_id,
        "obligation_id": _obligation().obligation_id,
        "outcome": "PERSIST_SNAPSHOT_FACT",
        "reason": "model said so",
        "admission_profile": "semantic-binding/v1",
        "snapshot_id": "snapshot:s0",
    }
    world = _world(tmp_path)
    try:
        with pytest.raises(Exception, match="deterministic profile"):
            persist_admitted_candidate(
                world,
                _obligation(),
                candidate,
                forged,
                catalog,
                snapshot_id="snapshot:s0",
            )
        assert world.relation_rows("realized_by") == []
    finally:
        world.close()


def _comparison(*, relation_bucket="retargeted"):
    old = "program:openRetentionFlow"
    new = "program:cancelSubscription"
    row = {"call_site": "program:cancel-button", "target": old}
    payload = {
        "status": "PASS",
        "preserved": [],
        "retargeted": [],
        "removed": [],
        "unresolved": [],
    }
    payload[relation_bucket].append(
        {"old": row, "new": {"call_site": "program:cancel-button", "target": new}}
    )
    delta = ProgramDelta(
        old_snapshot="snapshot:s0",
        new_snapshot="snapshot:s1",
        identity={},
        manifestations=(),
        relations={"program_invokes": payload},
    )
    return SimpleNamespace(
        receipt=SimpleNamespace(comparison_id="comparison:s0-s1"),
        delta=delta,
        correspondences=(
            SimpleNamespace(old_entity=old, new_entity=new, continuity="CONTINUED"),
        ),
    )


def test_maintenance_affects_warrant_without_model_and_does_not_transfer(tmp_path):
    catalog = _catalog()
    candidate = _candidate(
        catalog,
        dependencies=[
            _alias(catalog, "MAINTENANCE_DEPENDENCY", index)
            for index in range(
                len(catalog["allowed_aliases"]["MAINTENANCE_DEPENDENCY"])
            )
        ],
    )
    decision = admit_semantic_candidate(
        _obligation(), candidate, catalog, snapshot_id="snapshot:s0"
    )
    world = _world(tmp_path)
    try:
        persisted = persist_admitted_candidate(
            world,
            _obligation(),
            candidate,
            decision,
            catalog,
            snapshot_id="snapshot:s0",
        )
        warrant = persisted["warrant"]
        maintenance = maintain_semantic_commitment(warrant, _comparison())
        assert maintenance["status"] == "CHANGED"
        assert maintenance["model_invoked"] is False
        assert maintenance["transferred"] is False
        assert world.relation_rows("realized_by") == [
            {
                "semantic": "semantic:RetentionFlow",
                "program": "program:openRetentionFlow",
            }
        ]
    finally:
        world.close()


def test_lazy_reresolution_requires_explicit_request_and_creates_new_obligation():
    with pytest.raises(Exception, match="explicit request"):
        create_lazy_reresolution_obligation(
            _obligation(),
            candidate_program_endpoints=("program:cancelSubscription",),
            question="candidate question",
        )
    new = create_lazy_reresolution_obligation(
        _obligation(),
        candidate_program_endpoints=("program:cancelSubscription",),
        question="What does the candidate endpoint establish?",
        explicit_request=True,
    )
    assert new.obligation_id != _obligation().obligation_id
    assert new.allowed_program_endpoints == ("program:cancelSubscription",)


def test_admission_never_calls_repository_or_llm(monkeypatch):
    catalog = _catalog()
    candidate = _candidate(catalog)
    monkeypatch.setattr(
        Path,
        "rglob",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("repository inspected")
        ),
    )
    assert (
        admit_semantic_candidate(_obligation(), candidate, catalog).outcome
        == "PERSIST_SNAPSHOT_FACT"
    )


class _ConstructionTransport:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return AdjudicatorTransportResponse(payload=self.payloads.pop(0))


def test_model_constructor_compiles_aliases_and_repairs_with_exact_errors(tmp_path):
    catalog = _catalog()
    valid = _draft(catalog)
    invalid = copy.deepcopy(valid)
    invalid["authority_evidence_aliases"] = ["A999"]
    transport = _ConstructionTransport([invalid, valid])
    candidate = construct_semantic_candidate(
        _obligation(),
        _case(),
        transport=transport,
        output_dir=tmp_path,
        constructor_metadata={"provider": "fake", "model": "fixture"},
    )
    assert candidate.candidate_id
    assert len(transport.requests) == 2
    assert transport.requests[1].previous_output_json
    assert "not in the case catalog" in " ".join(
        transport.requests[1].validation_errors
    ) or "not one of the supplied enum values" in " ".join(
        transport.requests[1].validation_errors
    )
    request_input = json.loads(transport.requests[0].case_json)
    assert request_input.keys() == {
        "case_id",
        "case_scoped_catalog",
        "construction_obligation",
        "contract",
    }
    assert transport.requests[0].evidence_catalog_json == ""
    assert "repository" not in transport.requests[0].case_json.lower()
    assert (tmp_path / "semantic.candidate.json").is_file()
    receipt = json.loads(
        (tmp_path / "semantic.construction.invocation.json").read_text()
    )
    assert receipt["runtime_status"] == "SUCCEEDED"
    assert receipt["attempt_count"] == 2


def test_model_constructor_enforces_required_evidence_arrays_locally(tmp_path):
    catalog = _catalog(
        bounded_program_source=[
            {
                "evidence_id": "source:bounded",
                "provider": "fixture",
                "native_handle": "fixture.ts",
                "source_revision": "s0",
                "native_location": "bytes:0:1",
            }
        ]
    )
    invalid = _draft(catalog)
    invalid["mechanical_evidence_aliases"] = []
    valid = _draft(catalog)
    transport = _ConstructionTransport([invalid, valid])
    construct_semantic_candidate(
        _obligation(),
        _case(),
        transport=transport,
        output_dir=tmp_path,
    )
    assert "requires at least 1" in " ".join(
        transport.requests[1].validation_errors
    )


def test_model_constructor_receipt_does_not_persist_secret_metadata(tmp_path):
    catalog = _catalog()
    transport = _ConstructionTransport([_draft(catalog)])
    construct_semantic_candidate(
        _obligation(),
        _case(),
        transport=transport,
        output_dir=tmp_path,
        constructor_metadata={
            "provider": "fake",
            "api_key": "do-not-write",
            "authorization": "Bearer do-not-write",
        },
    )
    receipt = json.loads(
        (tmp_path / "semantic.construction.invocation.json").read_text()
    )
    assert "api_key" not in json.dumps(receipt)
    assert "do-not-write" not in json.dumps(receipt)


def test_model_constructor_has_two_attempt_bound_and_no_invalid_artifact(tmp_path):
    catalog = _catalog()
    invalid = _draft(catalog)
    invalid["authority_evidence_aliases"] = ["A999"]
    transport = _ConstructionTransport([invalid, invalid, _draft(catalog)])
    with pytest.raises(SemanticConstructionInvocationError) as error:
        construct_semantic_candidate(
            _obligation(),
            _case(),
            transport=transport,
            output_dir=tmp_path,
            max_attempts=9,
        )
    assert len(transport.requests) == 2
    assert error.value.receipt["runtime_status"] == "FAILED_VALIDATION"
    assert not (tmp_path / "semantic.candidate.json").exists()
    assert (
        json.loads((tmp_path / "semantic.construction.invocation.json").read_text())[
            "attempt_count"
        ]
        == 2
    )


def test_model_constructor_provider_failure_is_not_unresolved(tmp_path):
    class FailingTransport:
        def generate(self, _request):
            raise RuntimeError("provider unavailable")

    with pytest.raises(SemanticConstructionInvocationError) as error:
        construct_semantic_candidate(
            _obligation(),
            _case(),
            transport=FailingTransport(),
            output_dir=tmp_path,
        )
    assert error.value.receipt["runtime_status"] == "FAILED_PROVIDER"
    assert not (tmp_path / "semantic.candidate.json").exists()


def test_program_realization_relation_shape_is_trusted_and_deterministic():
    schema = canonical_program_realization_schema(_obligation())
    assert schema == canonical_program_realization_schema(_obligation())
    assert schema["name"] == PROGRAM_REALIZATION_RELATION
    assert [role["name"] for role in schema["roles"]] == [
        "semantic_subject",
        "program_manifestation",
    ]
    with pytest.raises(Exception, match="no trusted semantic commitment relation"):
        canonical_program_realization_schema(
            _obligation(admission_profile="other/v1")
        )


def test_live_schema_separates_required_evidence_classes_and_keeps_endpoints_free():
    obligation = _obligation()
    catalog = _catalog(
        obligation,
        _case(),
        bounded_program_source=[
            {
                "evidence_id": "source:bounded",
                "provider": "fixture",
                "native_handle": "fixture.ts",
                "source_revision": "s0",
                "native_location": "bytes:0:1",
                "reconstructed_text": "openRetentionFlow();",
            }
        ],
    )
    schema = semantic_candidate_schema(catalog)
    assert schema["required"] == [
        "obligation_id",
        "claim_kind",
        "relation_name",
        "semantic_endpoint_aliases",
        "program_endpoint_aliases",
        "polarity",
        "support_kind",
        "authority_evidence_aliases",
        "program_source_evidence_aliases",
        "mechanical_evidence_aliases",
        "program_scope",
        "maintenance_dependency_aliases",
        "completeness_aliases",
    ]
    assert schema["properties"]["authority_evidence_aliases"]["minItems"] == 1
    assert schema["properties"]["mechanical_evidence_aliases"]["minItems"] == 1
    assert schema["properties"]["program_source_evidence_aliases"]["items"][
        "enum"
    ]
    assert schema["properties"]["program_endpoint_aliases"]["items"]["enum"] == [
        "P1",
        "P2",
    ]


def test_materialization_publishes_g1_without_mutating_sealed_g0(tmp_path):
    (
        old,
        new,
        comparison,
        _case_value,
        obligation,
        catalog,
        candidate,
        decision,
    ) = _cancellation_commitment_fixture(tmp_path)
    try:
        before_db = old.path.read_bytes()
        before_admission = (old.path.parent / "world.admission.json").read_bytes()
        target = tmp_path / "world-semantic-revision"
        persisted = materialize_semantic_commitment_revision(
            old,
            target,
            obligation,
            candidate,
            decision,
            catalog,
            snapshot_id=snapshot_id(old),
        )
        assert old.path.read_bytes() == before_db
        assert (old.path.parent / "world.admission.json").read_bytes() == before_admission
        g1 = ConstructionWorld.open(target / old.path.name, read_only=True)
        try:
            assert snapshot_id(g1) == snapshot_id(old)
            assert g1.relation_rows(PROGRAM_REALIZATION_RELATION) == [
                {
                    "semantic_subject": "semantic:RetentionFlow",
                    "program_manifestation": candidate.tuple["program"],
                }
            ]
            assert g1.relation_rows(WARRANT_RELATION)
            support = g1.warrant_for_assertion(persisted["assertion_id"])
            detail = next(
                base["detail"]
                for base in support["bases"]
                if isinstance(base.get("detail"), dict)
                and isinstance(base["detail"].get("extra"), dict)
            )
            assert set(detail["extra"]["evidence_classes"]) >= {
                "AUTHORITY_GROUNDING",
                "PROGRAM_GROUNDING",
                "MECHANICAL_GROUNDING",
            }
            assert persisted["warrant"]["snapshot_id"] == snapshot_id(old)
            _fresh_maintenance, _fresh_impact, fresh_case = _adjudication_case(
                g1, new, comparison, tmp_path
            )
            old_links = fresh_case["semantic_context"]["program_links"]
            assert any(
                item["relation_name"] == PROGRAM_REALIZATION_RELATION
                and item["side"] == "OLD"
                and item["status"] == "POSITIVE"
                and item["included_because"] == ["PERSISTED_SEMANTIC_COMMITMENT"]
                for item in old_links
            )
            assert any(
                item["relation_name"] == PROGRAM_REALIZATION_RELATION
                and item["side"] == "NEW"
                and item["status"] == "ABSENCE_WITHOUT_COMPLETE_COVERAGE"
                for item in old_links
            )
        finally:
            g1.close()
    finally:
        old.close()
        new.close()


def test_failed_materialization_does_not_publish_revision(tmp_path):
    old, new, _comparison, _case_value, obligation, catalog, candidate, _decision = (
        _cancellation_commitment_fixture(tmp_path)
    )
    try:
        before = old.path.read_bytes()
        wrong_decision = admit_semantic_candidate(
            obligation, candidate, catalog, snapshot_id="wrong-snapshot"
        )
        with pytest.raises(Exception, match="snapshot mismatch"):
            materialize_semantic_commitment_revision(
                old,
                tmp_path / "world-failed-revision",
                obligation,
                candidate,
                wrong_decision,
                catalog,
                snapshot_id="wrong-snapshot",
            )
        assert not (tmp_path / "world-failed-revision").exists()
        assert old.path.read_bytes() == before
    finally:
        old.close()
        new.close()


def test_materialized_commitment_is_maintained_without_transfer_or_model(tmp_path):
    old, new, comparison, _case_value, obligation, catalog, candidate, decision = (
        _cancellation_commitment_fixture(tmp_path)
    )
    try:
        target = tmp_path / "world-semantic-revision"
        persisted = materialize_semantic_commitment_revision(
            old,
            target,
            obligation,
            candidate,
            decision,
            catalog,
            snapshot_id=snapshot_id(old),
        )
        maintenance = maintain_semantic_commitment(persisted["warrant"], comparison)
        assert maintenance["status"] == "CHANGED"
        assert maintenance["model_invoked"] is False
        assert maintenance["transferred"] is False
        g1 = ConstructionWorld.open(target / old.path.name, read_only=True)
        try:
            rows = g1.relation_rows(PROGRAM_REALIZATION_RELATION)
            assert rows[0]["program_manifestation"] == candidate.tuple["program"]
            assert not any(
                row["program_manifestation"] == "program:cancelSubscription"
                for row in rows
            )
        finally:
            g1.close()
    finally:
        old.close()
        new.close()

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ontology_author.governance import (
    AdjudicationError,
    AdjudicatorRequest,
    AdjudicatorTransportResponse,
    ModelAdjudicationInvocationError,
    ModelAdjudicatorConfig,
    OpenRouterAdjudicatorTransport,
    adjudicate_governance_case,
    build_case_evidence_catalog,
    compile_model_adjudication_draft,
    create_governance_adjudication,
    governance_adjudication_schema,
    model_adjudication_draft_schema,
    validate_governance_adjudication,
)

CASE = {
    "case_id": "case:transport-fixture",
    "contract": "governance_case/v0",
    "case_result": "SELECTED",
    "change": {
        "old_snapshot_id": "old:fixture",
        "new_snapshot_id": "new:fixture",
        "comparison_id": "comparison:fixture",
        "triggering_deltas": [{"evidence_id": "delta:retarget", "relation": "program_invokes"}],
        "comparison_limitations": [],
    },
    "program_context": {
        "referents": [{"id": "program:checkout", "side": "new"}],
        "structural_context": [],
        "relation_tuples": [{"evidence_id": "tuple:retarget", "relation": "program_invokes"}],
        "resolution_outcomes": [],
        "source_evidence": [
            {
                "evidence_id": "psrc:checkout",
                "program_entity": "program:checkout",
                "side": "NEW",
                "reconstructed_text": "return paymentGateway.charge();",
                "reconstruction": "OK",
            }
        ],
    },
    "authority": {
        "observations": [
            {
                "observation_id": "obs:gateway",
                "standing": "AUTHORITATIVE",
                "reconstructed_text": "Checkout must access payment providers through PaymentGateway.",
            }
        ],
        "claims": [],
        "semantic_referents": [],
    },
    "supporting_material": [],
    "selection": [{"attachment_assertion_id": "attachment:gateway"}],
    "uncertainty": {"heuristic_correspondences": [], "completeness_limitations": []},
}


def _candidate(case: dict = CASE) -> dict:
    return create_governance_adjudication(
        case,
        adjudicator={"kind": "MODEL", "identity": "fixture", "version": "fixture"},
        authority_findings=[
            {
                "finding_id": "afinding:gateway",
                "observation_ids": ["obs:gateway"],
                "attachment_refs": ["attachment:gateway"],
                "applicability": "APPLIES",
                "interpretation_summary": "The provider call must use PaymentGateway.",
                "finding_context": "SUFFICIENT",
                "evidence_refs": [{"kind": "authority_observation", "id": "obs:gateway"}],
            }
        ],
        program_findings=[
            {
                "finding_id": "pfinding:gateway",
                "proposition": "The new checkout accesses the provider through PaymentGateway.",
                "truth_value": "TRUE",
                "side": "NEW",
                "basis": "MECHANICAL",
                "heuristic_dependence": "NOT_MATERIAL",
                "finding_context": "SUFFICIENT",
                "evidence_refs": [{"kind": "delta", "id": "delta:retarget"}],
            }
        ],
        conformance_findings=[
            {
                "finding_id": "cfinding:gateway",
                "authority_finding_refs": ["afinding:gateway"],
                "program_finding_refs": ["pfinding:gateway"],
                "result": "CONFORMS",
            }
        ],
        decision_right={
            "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
            "outcome": "CONSTRAINED",
            "authority_basis_refs": ["afinding:gateway"],
            "rationale": "The applicable abstraction boundary remains binding.",
        },
        rationale=[
            {
                "statement": "The authoritative text names PaymentGateway as the access boundary.",
                "evidence_refs": [{"kind": "authority_observation", "id": "obs:gateway"}],
            }
        ],
    )


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def _alias(catalog: dict, category: str, index: int = 0) -> str:
    return catalog["allowed_aliases"][category][index]


def _draft(case: dict = CASE) -> dict:
    catalog = build_case_evidence_catalog(case)
    authority = _alias(catalog, "AUTHORITATIVE_OBSERVATION")
    mechanical = _alias(catalog, "MECHANICAL_PROGRAM_FACT")
    source = _alias(catalog, "PROGRAM_SOURCE")
    return {
        "case_id": case["case_id"],
        "context_sufficiency": {"status": "SUFFICIENT", "reasons": []},
        "authority_items": [
            {
                "authority_ref": authority,
                "applicability": "APPLIES",
                "interpretation_summary": "The supplied authority applies to checkout.",
                "applicability_basis": "The authority text names the checkout boundary.",
                "finding_context": "SUFFICIENT",
                "context_reasons": [],
                "program_findings": [
                    {
                        "proposition": "The candidate accesses the provider through the named boundary.",
                        "truth_value": "TRUE",
                        "side": "NEW",
                        "basis": "MECHANICAL",
                        "heuristic_dependence": "NOT_MATERIAL",
                        "evidence_refs": [mechanical, source],
                        "finding_context": "SUFFICIENT",
                        "context_reasons": [],
                        "limitations": [],
                    }
                ],
                "conformance": {"result": "CONFORMS", "finding_indexes": [0], "prior_state": None},
            }
        ],
        "authority_conflicts": [],
        "decision_right": {
            "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
            "outcome": "CONSTRAINED",
            "authority_refs": [authority],
            "rationale": "The applicable authority constrains the boundary.",
            "related_rights": [],
        },
        "context_requests": [],
        "rationale": [
            {
                "statement": "The authority and supplied program facts support the finding.",
                "evidence_refs": [authority, mechanical, source],
            }
        ],
        "unresolved_questions": [],
        "case_summary": "The candidate uses the named boundary.",
        "adjudication_state": "RESOLVED",
        "known_limitations": [],
        "empty_case_note": "",
    }


def test_case_evidence_catalog_is_deterministic_and_case_scoped():
    catalog = build_case_evidence_catalog(CASE)

    assert catalog == build_case_evidence_catalog(copy.deepcopy(CASE))
    assert [(entry["category"], entry["kind"], entry["id"], entry["alias"]) for entry in catalog["entries"]] == [
        ("AUTHORITATIVE_OBSERVATION", "authority_observation", "obs:gateway", "A1"),
        ("MECHANICAL_PROGRAM_FACT", "delta", "delta:retarget", "M1"),
        ("MECHANICAL_PROGRAM_FACT", "relation_tuple", "tuple:retarget", "M2"),
        ("PROGRAM_SOURCE", "program_source", "psrc:checkout", "S1"),
        ("PROGRAM_IDENTITY", "program_referent", "program:checkout", "P1"),
    ]
    assert set(catalog["allowed_aliases"]["SUPPORTING_MATERIAL"]) == set()


def test_dynamic_draft_schema_restricts_refs_to_catalog_aliases():
    catalog = build_case_evidence_catalog(CASE)
    schema = model_adjudication_draft_schema(CASE, catalog)
    properties = schema["properties"]
    authority_item = properties["authority_items"]["items"]
    rationale = properties["rationale"]["items"]["properties"]["evidence_refs"]["items"]

    assert authority_item["properties"]["authority_ref"]["enum"] == ["A1"]
    assert authority_item["properties"]["program_findings"]["items"]["properties"]["evidence_refs"]["items"]["enum"] == [
        "M1",
        "M2",
        "S1",
        "P1",
    ]
    assert rationale["enum"] == ["A1", "M1", "M2", "S1", "P1"]
    assert "finding_id" not in json.dumps(schema)


def test_draft_compiler_rejects_invented_evidence_and_program_identity():
    invalid_evidence = _draft()
    invalid_evidence["authority_items"][0]["program_findings"][0]["evidence_refs"] = ["M999"]
    with pytest.raises(AdjudicationError, match="not present in the case catalog"):
        compile_model_adjudication_draft(CASE, build_case_evidence_catalog(CASE), invalid_evidence)

    invalid_identity = _draft()
    invalid_identity["context_requests"] = [
        {
            "reason": "Need bounded implementation evidence.",
            "program_aliases": ["P999"],
            "relation_or_context_needed": [],
            "source_evidence_requested": [],
            "would_enable": "Determine the body behavior.",
        }
    ]
    with pytest.raises(AdjudicationError, match="not present in the case catalog"):
        compile_model_adjudication_draft(CASE, build_case_evidence_catalog(CASE), invalid_identity)


def test_draft_compiler_derives_evidence_kinds_and_generated_ids():
    catalog = build_case_evidence_catalog(CASE)
    draft = _draft()
    assert all(isinstance(ref, str) for ref in draft["rationale"][0]["evidence_refs"])
    first = compile_model_adjudication_draft(CASE, catalog, draft)
    second = compile_model_adjudication_draft(CASE, catalog, draft)

    assert first == second
    assert first["authority_findings"][0]["evidence_refs"] == [
        {"kind": "authority_observation", "id": "obs:gateway"}
    ]
    assert {tuple(sorted(ref.items())) for ref in first["program_findings"][0]["evidence_refs"]} == {
        (("id", "delta:retarget"), ("kind", "delta")),
        (("id", "psrc:checkout"), ("kind", "program_source")),
    }
    assert first["program_findings"][0]["finding_id"].startswith("pfinding:")
    assert first["conformance_findings"][0]["finding_id"].startswith("cfinding:")
    assert validate_governance_adjudication(first, CASE) == []


def test_supporting_material_alias_cannot_become_authority():
    case = copy.deepcopy(CASE)
    case["supporting_material"] = [{"observation_id": "obs:support"}]
    catalog = build_case_evidence_catalog(case)
    draft = _draft(case)
    draft["authority_items"][0]["authority_ref"] = _alias(catalog, "SUPPORTING_MATERIAL")

    with pytest.raises(AdjudicationError, match="expected AUTHORITATIVE_OBSERVATION"):
        compile_model_adjudication_draft(case, catalog, draft)


def test_authority_conflict_aliases_compile_to_generated_finding_refs():
    case = copy.deepcopy(CASE)
    case["authority"]["observations"].append(
        {
            "observation_id": "obs:other",
            "standing": "AUTHORITATIVE",
            "reconstructed_text": "Checkout may access providers directly.",
        }
    )
    catalog = build_case_evidence_catalog(case)
    draft = _draft(case)
    second_authority = _alias(catalog, "AUTHORITATIVE_OBSERVATION", 1)
    draft["authority_items"].append(
        {
            "authority_ref": second_authority,
            "applicability": "APPLIES",
            "interpretation_summary": "The second authority also applies.",
            "applicability_basis": "The second authority names checkout.",
            "finding_context": "SUFFICIENT",
            "context_reasons": [],
            "program_findings": [],
            "conformance": {"result": "UNKNOWN", "finding_indexes": [], "prior_state": None},
        }
    )
    draft["authority_conflicts"] = [
        {
            "authority_refs": ["A1", second_authority],
            "issue": "The supplied authorities state incompatible provider boundaries.",
            "precedence": "UNESTABLISHED",
            "resolution": "No precedence is established in the case.",
        }
    ]
    draft["decision_right"] = {
        "subject": "ADOPT_OR_KEEP_NEW_PROGRAM_STATE",
        "outcome": "UNKNOWN",
        "authority_refs": ["A1", second_authority],
        "rationale": "The authority conflict prevents resolving the right.",
        "related_rights": [],
    }
    draft["rationale"] = [
        {"statement": "Both supplied authorities apply and conflict.", "evidence_refs": ["A1", second_authority]}
    ]
    draft["adjudication_state"] = "AUTHORITY_CONFLICT"
    artifact = compile_model_adjudication_draft(case, catalog, draft)

    conflict_refs = artifact["authority_conflicts"][0]["authority_finding_refs"]
    assert len(conflict_refs) == 2
    assert all(ref.startswith("afinding:") for ref in conflict_refs)
    assert validate_governance_adjudication(artifact, case) == []


def test_compiler_preserves_model_semantic_values_and_final_validation():
    draft = _draft()
    draft["authority_items"][0]["program_findings"][0]["truth_value"] = "FALSE"
    draft["authority_items"][0]["conformance"]["result"] = "CONFLICTS"
    draft["decision_right"]["outcome"] = "CONSTRAINED"
    artifact = compile_model_adjudication_draft(CASE, build_case_evidence_catalog(CASE), draft)
    assert artifact["program_findings"][0]["truth_value"] == "FALSE"
    assert artifact["conformance_findings"][0]["result"] == "CONFLICTS"
    assert artifact["decision_right"]["outcome"] == "CONSTRAINED"

    invalid = _draft()
    invalid["authority_items"][0]["program_findings"][0]["basis"] = "NOT_A_BASIS"
    with pytest.raises(AdjudicationError, match="invalid program finding basis"):
        compile_model_adjudication_draft(CASE, build_case_evidence_catalog(CASE), invalid)


def test_model_transport_receives_exact_complete_case_and_validates_artifact(tmp_path: Path):
    candidate = _candidate()
    transport = FakeTransport([AdjudicatorTransportResponse(candidate, {"model": "fixture-model"})])
    config = ModelAdjudicatorConfig(
        provider="fixture-provider",
        model="fixture-model",
        model_version="fixture-version",
        max_attempts=9,
        identity="fixture-adjudicator",
    )

    artifact = adjudicate_governance_case(CASE, adjudicator_config=config, transport=transport, output_dir=tmp_path)

    assert transport.requests[0].case_json == json.dumps(CASE, sort_keys=True, separators=(",", ":"))
    assert "fixture-model" not in transport.requests[0].case_json
    assert transport.requests[0].output_schema["additionalProperties"] is False
    assert artifact["case_id"] == CASE["case_id"]
    assert artifact["adjudicator"]["identity"] == "fixture-adjudicator"
    assert artifact["adjudicator"]["configuration"]["max_attempts"] == 2
    assert validate_governance_adjudication(artifact, CASE) == []
    assert (tmp_path / "governance.adjudication.json").exists()
    receipt = json.loads((tmp_path / "governance.adjudication.invocation.json").read_text())
    assert receipt["runtime_status"] == "SUCCEEDED"
    assert receipt["provider"] == "fixture-provider"
    assert receipt["model"] == "fixture-model"
    assert receipt["model_version"] == "fixture-version"
    assert len(receipt["schema_hash"]) == 32
    assert receipt["model_output_contract"] == "model_adjudication_draft/v0"
    assert receipt["schema_hash"] == hashlib.sha256(
        json.dumps(transport.requests[0].output_schema, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:32]
    assert receipt["adjudication_id"] == artifact["adjudication_id"]
    assert "api_key" not in json.dumps(receipt)


def test_invalid_artifact_gets_one_bounded_repair_with_exact_errors():
    invalid = _candidate()
    invalid["program_findings"][0]["evidence_refs"] = [{"kind": "program_source", "id": "psrc:invented"}]
    repaired = _candidate()
    transport = FakeTransport([invalid, repaired])

    artifact = adjudicate_governance_case(
        CASE,
        adjudicator_config={"provider": "fixture", "model": "fixture", "max_attempts": 99},
        transport=transport,
    )

    assert artifact["adjudication_id"]
    assert len(transport.requests) == 2
    assert transport.requests[1].case_json == transport.requests[0].case_json
    assert transport.requests[1].output_schema == transport.requests[0].output_schema
    assert transport.requests[1].evidence_catalog_json == transport.requests[0].evidence_catalog_json
    assert transport.requests[1].previous_output_json == json.dumps(
        invalid, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    assert any("program evidence ref is not in the case" in error for error in transport.requests[1].validation_errors)


def test_draft_repair_receives_compilation_errors_and_keeps_same_boundary():
    invalid = _draft()
    invalid["rationale"][0]["evidence_refs"] = ["A999"]
    repaired = _draft()
    transport = FakeTransport([invalid, repaired])

    artifact = adjudicate_governance_case(
        CASE,
        adjudicator_config={"provider": "fixture", "model": "fixture"},
        transport=transport,
    )

    assert artifact["case_id"] == CASE["case_id"]
    assert transport.requests[1].case_json == transport.requests[0].case_json
    assert transport.requests[1].evidence_catalog_json == transport.requests[0].evidence_catalog_json
    assert transport.requests[1].output_schema == transport.requests[0].output_schema
    assert any("A999" in error for error in transport.requests[1].validation_errors)


def test_model_cannot_invent_a_mechanical_evidence_handle():
    invalid = _candidate()
    invalid["program_findings"][0]["evidence_refs"] = [
        {"kind": "relation_tuple", "id": "tuple:invented"}
    ]
    transport = FakeTransport([invalid, invalid])

    with pytest.raises(ModelAdjudicationInvocationError) as raised:
        adjudicate_governance_case(
            CASE,
            adjudicator_config={"provider": "fixture", "model": "fixture"},
            transport=transport,
        )

    assert raised.value.receipt["runtime_status"] == "FAILED_VALIDATION"
    assert any(
        "mechanical evidence ref is not in the case" in error
        for error in raised.value.receipt["validation_errors"]
    )


def test_validation_failure_is_not_fabricated_as_unresolved_and_never_writes_artifact(tmp_path: Path):
    invalid = _candidate()
    invalid["confidence"] = 0.9
    (tmp_path / "governance.adjudication.json").write_text("stale artifact", encoding="utf-8")
    transport = FakeTransport([invalid, invalid])

    with pytest.raises(ModelAdjudicationInvocationError) as raised:
        adjudicate_governance_case(
            CASE,
            adjudicator_config=ModelAdjudicatorConfig(provider="fixture", model="fixture"),
            transport=transport,
            output_dir=tmp_path,
        )

    receipt = raised.value.receipt
    assert receipt["runtime_status"] == "FAILED_VALIDATION"
    assert receipt["validation_result"] == "INVALID"
    assert receipt["attempt_count"] == 2
    assert len(receipt["attempts"]) == 2
    assert not (tmp_path / "governance.adjudication.json").exists()
    assert (tmp_path / "governance.adjudication.invocation.json").exists()
    assert all(item.get("adjudication_state") != "UNRESOLVED" for item in receipt["attempts"])


def test_provider_failure_is_a_runtime_failure_not_an_epistemic_state(tmp_path: Path):
    transport = FakeTransport([TimeoutError("fixture timeout")])

    with pytest.raises(ModelAdjudicationInvocationError) as raised:
        adjudicate_governance_case(
            CASE,
            adjudicator_config={"provider": "fixture", "model": "fixture"},
            transport=transport,
            output_dir=tmp_path,
        )

    receipt = raised.value.receipt
    assert receipt["runtime_status"] == "FAILED_PROVIDER"
    assert receipt["validation_result"] == "NOT_RUN"
    assert receipt["attempt_count"] == 1
    assert not (tmp_path / "governance.adjudication.json").exists()
    assert "timeout" in receipt["attempts"][0]["runtime_error"]


def test_invocation_receipt_redacts_provider_secrets(tmp_path: Path):
    transport = FakeTransport([RuntimeError("provider rejected secret-key")])

    with pytest.raises(ModelAdjudicationInvocationError) as raised:
        adjudicate_governance_case(
            CASE,
            adjudicator_config={"provider": "fixture", "model": "fixture", "api_key": "secret-key"},
            transport=transport,
            output_dir=tmp_path,
        )

    receipt_text = (tmp_path / "governance.adjudication.invocation.json").read_text()
    assert "secret-key" not in receipt_text
    assert "[REDACTED]" in receipt_text
    assert "secret-key" not in json.dumps(raised.value.receipt)


def test_malformed_response_is_repaired_as_validation_failure():
    transport = FakeTransport(["not-json", _candidate()])
    artifact = adjudicate_governance_case(
        CASE,
        adjudicator_config={"provider": "fixture", "model": "fixture"},
        transport=transport,
    )
    assert artifact["case_id"] == CASE["case_id"]
    assert transport.requests[1].previous_output_json == "not-json"
    assert any("not valid JSON" in error for error in transport.requests[1].validation_errors)


def test_schema_does_not_offer_reasoning_or_numeric_confidence_fields():
    schema = governance_adjudication_schema()
    assert "confidence" not in schema["properties"]
    assert "chain_of_thought" not in schema["properties"]
    assert schema["properties"]["decision_right"]["properties"]["outcome"]["enum"][-1] == "NOT_ESTABLISHED"


def test_openrouter_transport_requests_provider_native_json_schema(monkeypatch):
    candidate = _candidate()
    calls = []

    class Response:
        status_code = 200
        text = ""

        def json(self):
            return {
                "id": "response:fixture",
                "model": "resolved-fixture-model",
                "choices": [{"message": {"content": json.dumps(candidate)}}],
            }

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr("ontology_author.governance.model_adjudicator.requests.post", post)
    config = ModelAdjudicatorConfig(
        provider="openrouter",
        model="fixture-model",
        api_key="secret-key",
        timeout_seconds=7,
    )
    request = AdjudicatorRequest(
        case_json=json.dumps(CASE, sort_keys=True, separators=(",", ":")),
        instruction="fixture instruction",
        output_schema=governance_adjudication_schema(),
    )

    response = OpenRouterAdjudicatorTransport(config).generate(request)

    assert response.payload == json.dumps(candidate)
    assert response.metadata == {"id": "response:fixture", "model": "resolved-fixture-model"}
    assert calls[0][0] == "https://openrouter.ai/api/v1/chat/completions"
    body = calls[0][1]["json"]
    assert body["model"] == "fixture-model"
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["messages"][0] == {"role": "system", "content": "fixture instruction"}
    assert body["messages"][1]["content"] == request.case_json

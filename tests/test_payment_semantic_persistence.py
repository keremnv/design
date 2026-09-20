from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from experiments import run_payment_semantic_persistence_experiment as payment
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.semantic_binding import (
    PROGRAM_RELATIONSHIP_RELATION,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    canonical_semantic_commitment_schema,
    compile_semantic_candidate_draft,
    maintain_semantic_commitment,
    materialize_semantic_commitment_revision,
    semantic_candidate_schema,
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


def _fixture(tmp_path: Path):
    old, new, comparison, maintenance, impact, case, endpoints, relations = payment._setup(
        tmp_path
    )
    old_snapshot = snapshot_id(old)
    source = payment._bounded_source(
        old, endpoints, endpoints["checkout_entry"], old_snapshot
    )
    dependencies = payment._payment_dependencies(endpoints, relations)
    program_endpoint_kinds = payment._program_endpoint_kinds(old)
    catalog = build_semantic_construction_catalog(
        payment._obligation(case, endpoints),
        case,
        bounded_program_source=source,
        maintenance_dependencies=dependencies,
        program_endpoint_kinds=program_endpoint_kinds,
    )
    return (
        old,
        new,
        comparison,
        maintenance,
        impact,
        case,
        endpoints,
        relations,
        source,
        dependencies,
        catalog,
    )


def test_payment_relationship_schema_and_controls_are_bounded(tmp_path):
    (
        old,
        new,
        _comparison,
        _maintenance,
        _impact,
        case,
        endpoints,
        relations,
        source,
        dependencies,
        catalog,
    ) = _fixture(tmp_path)
    try:
        obligation = payment._obligation(case, endpoints)
        trusted_relation = canonical_semantic_commitment_schema(obligation)
        assert trusted_relation["name"] == PROGRAM_RELATIONSHIP_RELATION
        assert trusted_relation["source_roles"] == {
            role: role for role in payment.PAYMENT_RELATIONSHIP_TUPLE_SHAPE
        }
        schema = semantic_candidate_schema(catalog)
        assert catalog["role_signature"]["checkout_entry"]["allowed_program_kinds"] == [
            "call_site"
        ]
        assert catalog["role_signature"]["service"]["allowed_program_kinds"] == [
            "callable",
            "method",
        ]
        assert schema["properties"]["relation_name"]["const"] == "mediated_by"
        assert set(
            schema["properties"]["semantic_endpoints"]["properties"]["access"][
                "enum"
            ]
        ) == set(catalog["allowed_aliases"]["SEMANTIC_REFERENT"])
        assert schema["properties"]["program_endpoints"]["additionalProperties"] is False
        assert set(schema["properties"]["program_endpoints"]["properties"]) == set(
            payment.PAYMENT_RELATIONSHIP_TUPLE_SHAPE
        ) - {"access", "boundary"}
        def aliases_for(*kinds):
            return {
                item["alias"]
                for item in catalog["entries"]
                if item["category"] == "PROGRAM_ENDPOINT"
                and item.get("program_kind") in kinds
                and item["id"] in obligation.allowed_program_endpoints
            }

        program_properties = schema["properties"]["program_endpoints"]["properties"]
        assert set(program_properties["checkout_entry"]["enum"]) == aliases_for(
            "call_site"
        )
        assert set(program_properties["service"]["enum"]) == aliases_for(
            "callable", "method"
        )
        assert set(program_properties["service_call_site"]["enum"]) == aliases_for(
            "call_site"
        )
        assert set(program_properties["gateway"]["enum"]) == aliases_for(
            "callable", "method"
        )
        assert set(program_properties["gateway_call_site"]["enum"]) == aliases_for(
            "call_site"
        )
        assert set(program_properties["provider"]["enum"]) == aliases_for(
            "callable", "method"
        )

        renamed_catalog = copy.deepcopy(catalog)
        for item in renamed_catalog["entries"]:
            if item["category"] == "PROGRAM_ENDPOINT":
                item["description"] = "renamed program entity"
        renamed_schema = semantic_candidate_schema(renamed_catalog)
        assert renamed_schema["properties"]["program_endpoints"] == schema[
            "properties"
        ]["program_endpoints"]

        controls = payment._run_controls(
            obligation,
            case,
            endpoints,
            relations,
            source,
            dependencies,
            payment._program_endpoint_kinds(old),
            tmp_path / "controls",
        )
        assert (
            controls["A-grounded-finite-relational-commitment"]["admission"]["outcome"]
            == "PERSIST_COMMITMENT"
        )
        assert (
            controls["B-no-mechanical-grounding"]["admission"]["outcome"]
            == "RECORD_UNRESOLVED"
        )
        assert controls["C-wildcard-maintenance-dependency"]["status"] == (
            "INVALID_CANDIDATE"
        )
        assert "unsupported maintenance dependency kind" in controls[
            "C-wildcard-maintenance-dependency"
        ]["error"]
        assert controls["F-callable-supplied-to-call-site-role"]["status"] == (
            "INVALID_CANDIDATE"
        )
        assert controls["G-call-site-supplied-to-callable-role"]["status"] == (
            "INVALID_CANDIDATE"
        )
        assert controls["D-incidental-semantic-claim"]["admission"]["outcome"] == (
            "DROP"
        )
        assert controls["E-negative-without-completeness"]["admission"]["outcome"] == (
            "RECORD_UNRESOLVED"
        )
    finally:
        old.close()
        new.close()


def test_payment_commitment_is_materialized_reused_and_mechanically_affected(
    tmp_path,
):
    (
        old,
        new,
        comparison,
        maintenance,
        impact,
        case,
        endpoints,
        relations,
        _source,
        _dependencies,
        catalog,
    ) = _fixture(tmp_path)
    try:
        obligation = payment._obligation(case, endpoints)
        draft = payment._draft(obligation, catalog, endpoints, relations)
        candidate = compile_semantic_candidate_draft(
            obligation,
            catalog,
            draft,
            construction_method="deterministic payment control",
        )
        decision = admit_semantic_candidate(
            obligation, candidate, catalog, snapshot_id=snapshot_id(old)
        )
        assert decision.outcome == "PERSIST_COMMITMENT"

        before = old.path.read_bytes()
        target = tmp_path / "payment-world-g1"
        materialized = materialize_semantic_commitment_revision(
            old,
            target,
            obligation,
            candidate,
            decision,
            catalog,
            snapshot_id=snapshot_id(old),
        )
        assert old.path.read_bytes() == before
        g1 = ConstructionWorld.open(target / old.path.name, read_only=True)
        try:
            assert snapshot_id(g1) == snapshot_id(old)
            rows = g1.relation_rows(PROGRAM_RELATIONSHIP_RELATION)
            assert len(rows) == 1
            assert rows[0]["checkout_entry"] == endpoints["checkout_entry"]
            assert rows[0]["service"] == endpoints["service"]
            assert rows[0]["gateway"] == endpoints["gateway"]
            assert rows[0]["provider"] == endpoints["provider"]
            assert g1.relation_rows("semantic_commitment_warrant")

            maintenance_result = maintain_semantic_commitment(
                materialized["warrant"], comparison
            )
            assert maintenance_result["status"] == "CHANGED"
            assert maintenance_result["model_invoked"] is False
            assert maintenance_result["transferred"] is False
            changed = [
                item
                for item in maintenance_result["assessments"]
                if item["status"] == "CHANGED"
            ]
            assert any(
                item["dependency"]["kind"] == "relation_tuple" for item in changed
            )

            fresh_case = payment.assemble_governance_case(
                g1,
                new,
                comparison,
                payment._sources(tmp_path),
                maintenance=maintenance,
                impact=impact,
                purpose=payment.PURPOSE,
            )
            assert (
                payment.validate_case_sidecar(
                    fresh_case,
                    maintenance=maintenance,
                    impact=impact,
                    comparison=comparison,
                )
                == []
            )
            assert any(
                item["relation_name"] == PROGRAM_RELATIONSHIP_RELATION
                and item["included_because"] == ["PERSISTED_SEMANTIC_COMMITMENT"]
                for item in fresh_case["semantic_context"]["claims"]
            )
            assert any(
                item["relation_name"] == PROGRAM_RELATIONSHIP_RELATION
                and item["side"] == "OLD"
                and item["status"] == "POSITIVE"
                and item["included_because"] == ["PERSISTED_SEMANTIC_COMMITMENT"]
                for item in fresh_case["semantic_context"]["program_links"]
            )
            assert not any(
                item["relation_name"] == PROGRAM_RELATIONSHIP_RELATION
                and item["side"] == "NEW"
                and item["status"] == "POSITIVE"
                for item in fresh_case["semantic_context"]["program_links"]
            )
        finally:
            g1.close()
    finally:
        old.close()
        new.close()

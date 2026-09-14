from __future__ import annotations

import pytest

from ontology_author.governance import (
    GovernanceSupport,
    GovernanceValidationError,
    IdentityPlane,
    ReferentResolution,
    SupportMode,
    namespaced_referent_id,
    validate_relation_identity_planes,
)
from ontology_author.world.core.kernel import SemanticWorld
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import SourceObservation


def _observation() -> SourceObservation:
    return SourceObservation(
        provider="workspace",
        native_handle="requirements.md",
        source_revision="requirements-r1",
        native_location="Checkout > Purchase",
    )


def test_identity_planes_are_namespaced_and_related_values_are_not_interchangeable():
    source = namespaced_referent_id(IdentityPlane.SOURCE, "requirements#purchase")
    program = namespaced_referent_id(IdentityPlane.PROGRAM, "CheckoutPage.submit")

    validate_relation_identity_planes(
        {"source": source, "program": program},
        {"source": IdentityPlane.SOURCE, "program": IdentityPlane.PROGRAM},
    )
    with pytest.raises(GovernanceValidationError, match="requires SOURCE"):
        validate_relation_identity_planes(
            {"source": program, "program": program},
            {"source": IdentityPlane.SOURCE, "program": IdentityPlane.PROGRAM},
        )


def test_support_can_be_source_explicit_with_agent_resolved_referents():
    support = GovernanceSupport(
        support_mode=SupportMode.SOURCE_EXPLICIT,
        observations=(_observation(),),
        referent_resolution={
            "source": ReferentResolution.AGENT_RESOLVED,
            "program": ReferentResolution.AGENT_RESOLVED,
        },
    )
    grounding = support.assertion_grounding()

    assert grounding.extra == {
        "governance_support_mode": "source_explicit",
        "governance_referent_resolution": {
            "program": "agent_resolved",
            "source": "agent_resolved",
        },
    }


def test_durable_governance_support_requires_reconstructible_grounding():
    with pytest.raises(GovernanceValidationError, match="reconstructible"):
        GovernanceSupport(
            support_mode=SupportMode.CROSS_EVIDENCE_INFERRED,
            observations=(),
        )

    with pytest.raises(GovernanceValidationError, match="revision"):
        GovernanceSupport(
            support_mode=SupportMode.SOURCE_EXPLICIT,
            observations=(
                SourceObservation(
                    provider="workspace",
                    native_handle="requirements.md",
                    source_revision="",
                    native_location="Checkout > Purchase",
                ),
            ),
        )


def test_finer_support_metadata_survives_coarse_semantic_construction_origin(
    tmp_path,
):
    world = SemanticWorld(tmp_path / "world.sqlite", world_id="governance-test")
    try:
        semantic = namespaced_referent_id(IdentityPlane.SEMANTIC, "PurchaseAction")
        world.add_referent(semantic)
        world.declare_relation(
            "meaning",
            [Role("concept", RoleType.REFERENT)],
        )
        support = GovernanceSupport(
            support_mode=SupportMode.CROSS_EVIDENCE_INFERRED,
            observations=(_observation(),),
            referent_resolution={"concept": ReferentResolution.AGENT_RESOLVED},
        )
        assertion = world.assert_tuple(
            "meaning",
            {"concept": semantic},
            origin=ConstructionOrigin.SEMANTIC,
            grounding=support.assertion_grounding(),
        )

        warrant = world.warrant_for_assertion(assertion.assertion_id)
        assert warrant["construction_origins"] == ["SEMANTIC"]
        world_support = next(
            item for item in warrant["bases"] if item["kind"] == "WORLD"
        )
        assert world_support["detail"]["extra"]["governance_support_mode"] == (
            "cross_evidence_inferred"
        )
    finally:
        world.close()

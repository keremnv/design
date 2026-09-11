from __future__ import annotations

import pytest

from ontology_author.world.core.kernel import SemanticWorld
from ontology_author.world.core.model import (
    Role,
    RoleType,
    SemanticRefKind,
    WorldStoreError,
)
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation


def _design_world(tmp_path):
    return SemanticWorld(
        tmp_path / "world.sqlite",
        world_id="design-test",
        contract_id="design-core",
        contract_revision="1",
    )


def test_design_commitment_can_be_candidate_for_durable_obligation(tmp_path):
    world = _design_world(tmp_path)
    try:
        for referent in ("order_total", "promo_code", "checkout_commitment"):
            world.add_referent(referent, label=referent.replace("_", " "))

        world.declare_relation(
            "relative_prominence",
            [
                Role("more", RoleType.REFERENT),
                Role("less", RoleType.REFERENT),
                Role("context", RoleType.REFERENT),
            ],
        )
        commitment = world.assert_tuple(
            "relative_prominence",
            {
                "more": "order_total",
                "less": "promo_code",
                "context": "checkout_commitment",
            },
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding(
                observations=(
                    SourceObservation(
                        provider="workspace",
                        native_handle="requirements.md",
                        source_revision="requirements-r1",
                        native_location="checkout hierarchy",
                    ),
                    SourceObservation(
                        provider="workspace",
                        native_handle="Checkout.tsx",
                        source_revision="checkout-r4",
                        native_location="order summary",
                    ),
                ),
                construction_method="agent design judgment",
            ),
        )

        obligation_id = world.add_obligation(
            "checkout.prominence.total-vs-promo",
            question=(
                "Determine the relative prominence of order total and promo code "
                "during checkout commitment."
            ),
        )

        world.declare_relation(
            "candidate_for",
            [
                Role(
                    "obligation",
                    RoleType.TEXT,
                    SemanticRefKind.OBLIGATION,
                ),
                Role(
                    "commitment",
                    RoleType.TEXT,
                    SemanticRefKind.COMMITMENT,
                ),
            ],
            description="A commitment proposed as an answer to an obligation.",
        )
        candidate = world.assert_tuple(
            "candidate_for",
            {
                "obligation": obligation_id,
                "commitment": commitment.assertion_id,
            },
            origin=ConstructionOrigin.SEMANTIC,
        )

        obligation = world.obligation(obligation_id)
        assert obligation is not None
        assert obligation["state"] == "UNRESOLVED"
        assert obligation["contract_id"] == "design-core"
        assert obligation["contract_revision"] == "1"

        assert world.relation_tuples("candidate_for") == {
            (obligation_id, commitment.assertion_id)
        }
        assert candidate.assertion_id != commitment.assertion_id

        schema = world.relation_schema("candidate_for")
        assert schema["roles"] == [
            {
                "name": "obligation",
                "type": "TEXT",
                "column": "obligation",
                "reference_kind": "OBLIGATION",
            },
            {
                "name": "commitment",
                "type": "TEXT",
                "column": "commitment",
                "reference_kind": "COMMITMENT",
            },
        ]

        warrant = world.warrant_for_assertion(commitment.assertion_id)
        assert warrant["commitment_id"] == commitment.assertion_id
        assert warrant["assertion_origin"] == "ASSERTED"
        assert warrant["construction_origins"] == ["SEMANTIC"]
        assert {basis["kind"] for basis in warrant["bases"]} == {"SOURCE", "WORLD"}
        assert world.contract_identity() == {
            "contract_id": "design-core",
            "contract_revision": "1",
        }
    finally:
        world.close()

    reopened = SemanticWorld(
        tmp_path / "world.sqlite",
        world_id="design-test",
        read_only=True,
    )
    try:
        assert reopened.contract_identity() == {
            "contract_id": "design-core",
            "contract_revision": "1",
        }
        assert reopened.obligation("checkout.prominence.total-vs-promo")["state"] == "UNRESOLVED"
        assert reopened.relation_tuples("candidate_for") == {
            ("checkout.prominence.total-vs-promo", commitment.assertion_id)
        }
    finally:
        reopened.close()


def test_semantic_reference_roles_reject_unknown_targets(tmp_path):
    world = _design_world(tmp_path)
    try:
        world.add_referent("a")
        world.declare_relation("fact", [Role("subject", RoleType.REFERENT)])
        commitment = world.assert_tuple(
            "fact", {"subject": "a"}, origin=ConstructionOrigin.SEMANTIC
        )
        world.add_obligation("o1", question="What should happen?")
        world.declare_relation(
            "candidate_for",
            [
                Role("obligation", RoleType.TEXT, SemanticRefKind.OBLIGATION),
                Role("commitment", RoleType.TEXT, SemanticRefKind.COMMITMENT),
            ],
        )
        with pytest.raises(WorldStoreError, match="unknown commitment"):
            world.assert_tuple(
                "candidate_for",
                {"obligation": "o1", "commitment": "assertion:not-real"},
                origin=ConstructionOrigin.SEMANTIC,
            )
        with pytest.raises(WorldStoreError, match="unknown obligation"):
            world.assert_tuple(
                "candidate_for",
                {"obligation": "missing", "commitment": commitment.assertion_id},
                origin=ConstructionOrigin.SEMANTIC,
            )
    finally:
        world.close()


def test_referenced_commitment_cannot_be_retracted(tmp_path):
    world = _design_world(tmp_path)
    try:
        world.add_referent("a")
        world.add_referent("b")
        world.declare_relation(
            "preference",
            [Role("more", RoleType.REFERENT), Role("less", RoleType.REFERENT)],
        )
        commitment = world.assert_tuple(
            "preference",
            {"more": "a", "less": "b"},
            origin=ConstructionOrigin.SEMANTIC,
        )
        world.add_obligation("o1", question="Which is preferred?")
        world.declare_relation(
            "candidate_for",
            [
                Role("obligation", RoleType.TEXT, SemanticRefKind.OBLIGATION),
                Role("commitment", RoleType.TEXT, SemanticRefKind.COMMITMENT),
            ],
        )
        world.assert_tuple(
            "candidate_for",
            {"obligation": "o1", "commitment": commitment.assertion_id},
            origin=ConstructionOrigin.SEMANTIC,
        )
        with pytest.raises(WorldStoreError, match="semantic references depend on it"):
            world.retract_tuple("preference", {"more": "a", "less": "b"})
    finally:
        world.close()

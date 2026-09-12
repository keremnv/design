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

        association_id = world.add_candidate(obligation_id, commitment.assertion_id)

        obligation = world.obligation(obligation_id)
        assert obligation is not None
        assert obligation["state"] == "UNRESOLVED"
        assert obligation["contract_id"] == "design-core"
        assert obligation["contract_revision"] == "1"

        assert association_id.startswith("candidate:")
        assert world.candidates_for(obligation_id) == [commitment.assertion_id]
        assert world.obligations_for(commitment.assertion_id) == [obligation_id]
        assert world.candidate_associations() == [
            {
                "association_id": association_id,
                "obligation_id": obligation_id,
                "commitment_id": commitment.assertion_id,
                "created_revision": world.candidate_associations()[0][
                    "created_revision"
                ],
            }
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
        assert reopened.candidates_for("checkout.prominence.total-vs-promo") == [
            commitment.assertion_id
        ]
    finally:
        reopened.close()


def test_candidate_association_rejects_unknown_targets(tmp_path):
    world = _design_world(tmp_path)
    try:
        world.add_referent("a")
        world.declare_relation("fact", [Role("subject", RoleType.REFERENT)])
        commitment = world.assert_tuple(
            "fact", {"subject": "a"}, origin=ConstructionOrigin.SEMANTIC
        )
        world.add_obligation("o1", question="What should happen?")
        with pytest.raises(WorldStoreError, match="unknown candidate commitment"):
            world.add_candidate("o1", "assertion:not-real")
        with pytest.raises(WorldStoreError, match="unknown candidate obligation"):
            world.add_candidate("missing", commitment.assertion_id)
    finally:
        world.close()


def test_candidate_commitment_cannot_be_retracted(tmp_path):
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
        world.add_candidate("o1", commitment.assertion_id)
        with pytest.raises(WorldStoreError, match="candidate associations depend on it"):
            world.retract_tuple("preference", {"more": "a", "less": "b"})
    finally:
        world.close()


def test_candidate_association_is_idempotent_and_bidirectional(tmp_path):
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
        world.add_obligation("o1", question="Which is preferred in context one?")
        world.add_obligation("o2", question="Which is preferred in context two?")

        first = world.add_candidate("o1", commitment.assertion_id)
        revision_after_first = world._store.revision
        assert world.add_candidate("o1", commitment.assertion_id) == first
        assert world._store.revision == revision_after_first
        world.add_candidate("o2", commitment.assertion_id)

        assert world.candidates_for("o1") == [commitment.assertion_id]
        assert world.candidates_for("o2") == [commitment.assertion_id]
        assert world.obligations_for(commitment.assertion_id) == ["o1", "o2"]
        assert len(world.candidate_associations()) == 2
    finally:
        world.close()


def test_generic_semantic_reference_relations_remain_separate_from_candidates(tmp_path):
    world = _design_world(tmp_path)
    try:
        world.add_referent("a")
        world.declare_relation("fact", [Role("subject", RoleType.REFERENT)])
        commitment = world.assert_tuple(
            "fact", {"subject": "a"}, origin=ConstructionOrigin.SEMANTIC
        )
        world.add_obligation("o1", question="What should happen?")
        world.declare_relation(
            "semantic_link",
            [
                Role("obligation", RoleType.TEXT, SemanticRefKind.OBLIGATION),
                Role("commitment", RoleType.TEXT, SemanticRefKind.COMMITMENT),
            ],
        )
        world.assert_tuple(
            "semantic_link",
            {"obligation": "o1", "commitment": commitment.assertion_id},
            origin=ConstructionOrigin.SEMANTIC,
        )

        assert world.relation_tuples("semantic_link") == {
            ("o1", commitment.assertion_id)
        }
        assert world.candidates_for("o1") == []
    finally:
        world.close()

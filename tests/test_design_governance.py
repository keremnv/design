from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

from ontology_author.world import Project
from ontology_author.world.runtime.entry import rebuild

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    DESIGN_LAW,
    extract_frontend_structure,
)


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"


FIXTURE_SOURCE = (
    Path(__file__).parents[1]
    / "profiles"
    / "design_checkout"
    / "fixture"
    / "Checkout.tsx"
).read_text(encoding="utf-8")


def _structure(source: str):
    return extract_frontend_structure(source, source_name="Checkout.tsx")


def test_same_frontend_different_law_produces_different_obligation_sets(tmp_path):
    structure = _structure(FIXTURE_SOURCE)
    full = DESIGN_LAW.enumerate_obligations(structure)
    without_availability = DESIGN_LAW.with_dimensions(
        "priority", "goal_support", revision="2"
    )

    assert {item.dimension for item in full} == {
        "availability",
        "priority",
        "goal_support",
    }
    assert {item.dimension for item in without_availability.enumerate_obligations(structure)} == {
        "priority",
        "goal_support",
    }
    assert {
        item.obligation_id for item in full
    } != {
        item.obligation_id
        for item in without_availability.enumerate_obligations(structure)
    }

    full_root = tmp_path / "full"
    reduced_root = tmp_path / "reduced"
    shutil.copytree(FIXTURE, full_root)
    shutil.copytree(FIXTURE, reduced_root)
    assert rebuild(full_root, contract=DESIGN_CONTRACT, governance=DESIGN_LAW).succeeded
    assert rebuild(
        reduced_root,
        contract=DESIGN_CONTRACT,
        governance=without_availability,
    ).succeeded
    full_world = Project(full_root).open_world()
    reduced_world = Project(reduced_root).open_world()
    try:
        assert {
            item["obligation_id"] for item in full_world.obligations()
        } != {
            item["obligation_id"] for item in reduced_world.obligations()
        }
        assert len(reduced_world.obligations()) == 2
    finally:
        full_world.close()
        reduced_world.close()


def test_irrelevant_realization_change_does_not_change_governed_obligations():
    changed_source = FIXTURE_SOURCE.replace(
        '<main data-screen="mobile-checkout">',
        '<main className="checkout-shell" data-screen="mobile-checkout">',
    )
    original = DESIGN_LAW.enumerate_obligations(_structure(FIXTURE_SOURCE))
    changed = DESIGN_LAW.enumerate_obligations(_structure(changed_source))

    assert {item.obligation_id for item in original} == {
        item.obligation_id for item in changed
    }


def test_governed_structural_change_changes_obligations_predictably():
    changed_source = FIXTURE_SOURCE.replace(
        'data-region="order-summary"',
        'data-region="order-details"',
    )
    original = DESIGN_LAW.enumerate_obligations(_structure(FIXTURE_SOURCE))
    changed = DESIGN_LAW.enumerate_obligations(_structure(changed_source))

    assert {item.dimension for item in original} == {
        "availability",
        "priority",
        "goal_support",
    }
    assert {item.dimension for item in changed} == {"priority"}


def test_obligation_identity_is_independent_of_dimension_iteration_order():
    structure = _structure(FIXTURE_SOURCE)
    reordered = replace(DESIGN_LAW, dimensions=tuple(reversed(DESIGN_LAW.dimensions)))
    revised = replace(DESIGN_LAW, revision="2")

    assert [item.obligation_id for item in DESIGN_LAW.enumerate_obligations(structure)] == [
        item.obligation_id for item in reordered.enumerate_obligations(structure)
    ]
    assert {
        item.obligation_id for item in DESIGN_LAW.enumerate_obligations(structure)
    } != {
        item.obligation_id for item in revised.enumerate_obligations(structure)
    }

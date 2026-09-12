from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil

from ontology_author.world import Project
from ontology_author.world.runtime.entry import rebuild

from profiles.design_checkout import (
    DESIGN_CONTRACT,
    DESIGN_EVIDENCE_AUTHORITY,
    DESIGN_LAW,
    adopt_governance_law,
    compile_governance_law,
    extract_frontend_structure,
    load_design_law,
    select_authoritative_sources,
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


def test_selected_source_compiles_to_proposed_law_then_requires_explicit_adoption():
    selected = select_authoritative_sources(FIXTURE)
    assert selected.as_payload()["sources"] == [
        {
            "source_id": "checkout-design-governance",
            "path": "design-governance.md",
            "revision": selected.sources[0].revision,
        }
    ]

    proposed = compile_governance_law(selected)
    assert proposed.inspection_payload()["state"] == "PROPOSED"
    assert [item.name for item in proposed.dimensions] == [
        "availability",
        "goal_support",
        "priority",
    ]
    for dimension in proposed.dimensions:
        assert dimension.provenance is not None
        assert dimension.provenance.source_id == "checkout-design-governance"
        assert dimension.provenance.source_location.startswith("design-governance.md#L")
        assert dimension.provenance.interpretation_method == (
            "bounded-checkout-governance-compiler-v1"
        )

    effective = adopt_governance_law(proposed, adopted_by="test adoption")
    assert effective.inspection_payload()["state"] == "EFFECTIVE"
    assert effective.adoption == {
        "adopted_by": "test adoption",
        "method": "explicit configuration",
    }
    assert effective.inspection_payload()["proposed_law"]["state"] == "PROPOSED"


def test_removing_selected_law_source_removes_effective_rules(tmp_path):
    root = tmp_path / "no-law-source"
    shutil.copytree(FIXTURE, root)
    manifest = json.loads((root / "governance-sources.json").read_text(encoding="utf-8"))
    manifest["sources"] = []
    (root / "governance-sources.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    effective = load_design_law(root)
    assert effective.dimensions == ()
    assert effective.enumerate_obligations(_structure(FIXTURE_SOURCE)) == ()


def test_unselected_normative_source_does_not_modify_effective_law(tmp_path):
    root = tmp_path / "unselected"
    shutil.copytree(FIXTURE, root)
    baseline = load_design_law(root)
    (root / "other-normative-source.md").write_text(
        """# An unselected proposal\n\n## Priority\n\nPromotional interactions should dominate.\n\n- More: promo-code interaction\n- Less: order-total field\n- Context: checkout-commitment context\n""",
        encoding="utf-8",
    )
    changed = load_design_law(root)

    assert changed.identity() == baseline.identity()
    assert changed.inspection_payload()["source_selection"]["sources"] == [
        {
            "source_id": "checkout-design-governance",
            "path": "design-governance.md",
            "revision": baseline.source_selection.sources[0].revision,
        }
    ]
    assert [item.as_payload() for item in changed.dimensions] == [
        item.as_payload() for item in baseline.dimensions
    ]


def test_changing_selected_law_binding_changes_law_and_obligation_space(tmp_path):
    root = tmp_path / "changed-law"
    shutil.copytree(FIXTURE, root)
    original = load_design_law(root)
    source = (root / "design-governance.md").read_text(encoding="utf-8")
    changed_source = source.replace(
        "- Subject: order-summary region\n- Activity: payment-entry region",
        "- Subject: payment-entry region\n- Activity: payment-entry region",
        1,
    )
    (root / "design-governance.md").write_text(changed_source, encoding="utf-8")
    changed = load_design_law(root)

    original_obligations = original.enumerate_obligations(_structure(FIXTURE_SOURCE))
    changed_obligations = changed.enumerate_obligations(_structure(FIXTURE_SOURCE))
    assert changed.identity() != original.identity()
    assert changed.dimensions[0].provenance.source_revision != (
        original.dimensions[0].provenance.source_revision
    )
    assert original_obligations[0].obligation_id != changed_obligations[0].obligation_id
    changed_availability = next(
        item for item in changed_obligations if item.dimension == "availability"
    )
    assert changed_availability.binding_map["subject"] == "payment_entry"


def test_answer_bearing_evidence_does_not_change_obligation_enumeration(tmp_path):
    root = tmp_path / "answer-change"
    shutil.copytree(FIXTURE, root)
    law_before = load_design_law(root)
    before = law_before.enumerate_obligations(_structure(FIXTURE_SOURCE))
    requirements = root / "checkout-requirements.md"
    requirements.write_text(
        requirements.read_text(encoding="utf-8")
        + "\nThe implementation requirement may be reconsidered by the constructor.\n",
        encoding="utf-8",
    )
    law_after = load_design_law(root)
    after = law_after.enumerate_obligations(_structure(FIXTURE_SOURCE))

    assert law_after.identity() == law_before.identity()
    assert [item.obligation_id for item in after] == [item.obligation_id for item in before]


def test_each_generated_obligation_has_rule_source_and_structural_bindings():
    law = load_design_law(FIXTURE)
    obligations = law.enumerate_obligations(_structure(FIXTURE_SOURCE))
    assert len(obligations) == 3
    for obligation in obligations:
        assert obligation.rule_id.startswith("rule:checkout_design_governance:")
        assert obligation.provenance is not None
        assert obligation.provenance.source_id == "checkout-design-governance"
        assert obligation.provenance.source_revision
        assert obligation.provenance.source_location.startswith("design-governance.md#L")
        assert obligation.binding_map


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
    assert rebuild(
        full_root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
    ).succeeded
    assert rebuild(
        reduced_root,
        contract=DESIGN_CONTRACT,
        governance=without_availability,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
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

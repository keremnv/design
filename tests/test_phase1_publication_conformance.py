"""Phase 1 provenance conformance: exact publication qualification."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from ontology_author.software_governance import open_governance_world
from ontology_author.software_governance.judgment import assemble_case, verify_case
from tests.software_governance_judgment_fixtures import build_worlds

EXPORT_PROPOSITION = "proposition:customer-export-route"


@pytest.fixture(scope="module")
def worlds(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return build_worlds(tmp_path_factory.mktemp("phase1-publication"))


def _config_case(world: Path) -> dict:
    view = open_governance_world(world)
    try:
        subjects = view.subjects_for_proposition(EXPORT_PROPOSITION)
        assert len(subjects) == 1
        return assemble_case(
            view,
            case_id="phase1-exact-publication",
            question="Does this route satisfy the stated route rule?",
            proposition_ids=(EXPORT_PROPOSITION,),
            subject_ids=(subjects[0],),
        )
    finally:
        view.world.close()


def test_identical_publication_copy_is_not_the_cited_occurrence(
    worlds: dict[str, Path], tmp_path: Path
) -> None:
    original = worlds["config"]
    case = _config_case(original)

    copied = tmp_path / "identical-copy"
    shutil.copytree(original, copied)

    view = open_governance_world(copied)
    try:
        assert view.world.world_id == case["world_id"]
        errors = verify_case(view, case)
    finally:
        view.world.close()

    assert "world address differs from the opened publication" in errors


def test_case_revision_is_part_of_publication_identity(worlds: dict[str, Path]) -> None:
    world = worlds["config"]
    case = _config_case(world)
    forged = copy.deepcopy(case)
    forged["revision"] += 1

    view = open_governance_world(world)
    try:
        errors = verify_case(view, forged)
    finally:
        view.world.close()

    assert "world revision differs from the opened publication" in errors


def test_case_without_exact_publication_reference_fails_closed(
    worlds: dict[str, Path]
) -> None:
    world = worlds["config"]
    case = _config_case(world)
    forged = copy.deepcopy(case)
    del forged["world_address"]

    view = open_governance_world(world)
    try:
        errors = verify_case(view, forged)
    finally:
        view.world.close()

    assert errors == ["case publication reference is malformed"]

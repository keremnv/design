from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

from ontology_author.world import Project
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.entry import rebuild
from ontology_author.world.server import build_app
from profiles.design_checkout import (
    DESIGN_ADJUDICATION_AUTHORITY,
    DESIGN_CONTRACT,
    DESIGN_EVIDENCE_AUTHORITY,
    DESIGN_LAW,
)


DESIGN_FIXTURE = Path(__file__).parents[1] / "profiles" / "design_checkout" / "fixture"


def _design_world(tmp_path: Path) -> Path:
    root = tmp_path / "design-world"
    shutil.copytree(DESIGN_FIXTURE, root)
    result = rebuild(
        root,
        contract=DESIGN_CONTRACT,
        governance=DESIGN_LAW,
        evidence_authority=DESIGN_EVIDENCE_AUTHORITY,
        adjudication_authority=DESIGN_ADJUDICATION_AUTHORITY,
        purpose=None,
    )
    assert result.succeeded, result.errors
    return root


def test_governed_design_world_is_purpose_free_through_sealed_read(tmp_path: Path):
    root = _design_world(tmp_path)
    bundle = root / "world"

    assert (root / "PURPOSE.md").exists()
    assert not (bundle / "world.purpose.json").exists()

    with sqlite3.connect(bundle / "world.sqlite") as connection:
        connection.row_factory = sqlite3.Row
        metadata = connection.execute(
            "SELECT purpose_ref FROM _world_meta WHERE singleton = 1"
        ).fetchone()
        relation_names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM _world_relations"
            )
        }
    assert metadata["purpose_ref"] is None
    assert "purpose_requirement_failure" not in relation_names

    admission = json.loads((bundle / "world.admission.json").read_text())
    assert all(scope != "PURPOSE" for scope in admission["relations"].values())

    world = Project(root).open_world()
    try:
        assert "purpose_requirement_failure" not in world.admission
        assert len(world.obligations()) == 3
        assert world.candidate_associations()
        assert world.resolutions()
    finally:
        world.close()

    with WorldExplorerAdapter(bundle / "world.sqlite") as explorer:
        assert explorer.demand() is None
        governed = explorer.obligations()
        assert len(governed["obligations"]) == 3
        assert all(item["candidates"] for item in governed["obligations"])
        assert {item["resolution"]["status"] for item in governed["obligations"]} == {
            "RESOLVED",
            "INSUFFICIENT_WARRANT",
        }

    from starlette.testclient import TestClient

    with TestClient(build_app(bundle / "world.sqlite")) as client:
        assert client.get("/world/demand").json() == {"demand": None}
        response = client.get("/world/obligations")
        assert response.status_code == 200
        assert len(response.json()["obligations"]) == 3


def test_explicit_legacy_purpose_still_creates_and_reopens_its_frontier(
    tmp_path: Path,
):
    root = tmp_path / "legacy-world"
    root.mkdir()
    (root / "PURPOSE.md").write_text(
        "# Purpose\n\nFind the missing account identity.\n",
        encoding="utf-8",
    )
    (root / "construction.py").write_text(
        """def construct(source, world, purpose):
    purpose.unresolved(
        "missing_account_identity",
        relation="account",
        subject={"account": "account:A1"},
        reason="the extract does not establish the legal identity",
    )
""",
        encoding="utf-8",
    )

    result = rebuild(root, purpose=root / "PURPOSE.md")
    assert result.succeeded, result.errors
    bundle = root / "world"
    assert (bundle / "world.purpose.json").exists()

    world = Project(root).open_world()
    try:
        assert world.admission["purpose_requirement_failure"] == "PURPOSE"
        assert world.relation_rows("purpose_requirement_failure")
    finally:
        world.close()

    with WorldExplorerAdapter(bundle / "world.sqlite") as explorer:
        demand = explorer.demand()
        assert demand is not None
        assert demand["purpose"]["statement"].startswith("# Purpose")
        assert demand["demanded"] == 1
        assert demand["obligations"][0]["demanded_by"]["kind"] == "requirement"

    from starlette.testclient import TestClient

    with TestClient(build_app(bundle / "world.sqlite")) as client:
        demand = client.get("/world/demand")
        assert demand.status_code == 200
        assert demand.json()["demand"]["demanded"] == 1


def test_legacy_constructor_can_run_without_a_purpose_object(tmp_path: Path):
    root = tmp_path / "legacy-shape-no-purpose"
    root.mkdir()
    (root / "construction.py").write_text(
        """def construct(source, world, purpose):
    assert purpose is None
""",
        encoding="utf-8",
    )

    result = Project(root).run(purpose=None)
    assert result.succeeded, result.errors
    assert not (root / "world" / "world.purpose.json").exists()
    world = Project(root).open_world()
    try:
        assert "purpose_requirement_failure" not in world.admission
    finally:
        world.close()

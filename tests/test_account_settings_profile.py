from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

from ontology_author.world import Project
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.runtime.entry import rebuild
from ontology_author.world.server import build_app

from profiles.design_account_settings import (
    ACCOUNT_SETTINGS_CONTRACT,
    ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY,
    ACCOUNT_SETTINGS_LAW,
    ACCOUNT_SETTINGS_RELATION_NAMES,
    compile_governance_law,
    extract_frontend_structure,
    load_account_settings_law,
    select_authoritative_sources,
)
from profiles.design_account_settings.governance import adopt_governance_law


FIXTURE = Path(__file__).parents[1] / "profiles" / "design_account_settings" / "fixture"


def _copy_fixture(tmp_path: Path, name: str = "account-settings-world") -> Path:
    root = tmp_path / name
    shutil.copytree(FIXTURE, root)
    return root


def _structure(root: Path):
    source = root / "AccountSettings.tsx"
    return extract_frontend_structure(
        source.read_text(encoding="utf-8"),
        source_name=source.name,
    )


def test_account_settings_law_requires_selection_compilation_and_adoption():
    selected = select_authoritative_sources(FIXTURE)
    assert selected.as_payload()["sources"] == [
        {
            "source_id": "account-settings-design-governance",
            "path": "design-governance.md",
            "revision": selected.sources[0].revision,
        }
    ]

    proposed = compile_governance_law(selected)
    assert proposed.inspection_payload()["state"] == "PROPOSED"
    assert [item.name for item in proposed.dimensions] == [
        "confirmation_requirement",
        "consequence_distinction",
    ]
    assert all(
        item.provenance.source_id == "account-settings-design-governance"
        for item in proposed.dimensions
    )

    effective = adopt_governance_law(
        proposed, adopted_by="test account settings adoption"
    )
    assert effective.inspection_payload()["state"] == "EFFECTIVE"
    assert effective.adoption == {
        "adopted_by": "test account settings adoption",
        "method": "explicit configuration",
    }
    assert effective.inspection_payload()["proposed_law"]["state"] == "PROPOSED"


def test_account_settings_profile_builds_without_purpose_and_uses_structure_plus_law(
    tmp_path: Path,
):
    root = _copy_fixture(tmp_path)
    assert not (root / "PURPOSE.md").exists()

    structure = _structure(root)
    generated = ACCOUNT_SETTINGS_LAW.enumerate_obligations(structure)
    assert len(generated) == 2
    assert {item.dimension for item in generated} == {
        "confirmation_requirement",
        "consequence_distinction",
    }
    assert all(
        item.provenance.source_id == "account-settings-design-governance"
        for item in generated
    )

    result = rebuild(
        root,
        contract=ACCOUNT_SETTINGS_CONTRACT,
        governance=ACCOUNT_SETTINGS_LAW,
        evidence_authority=ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY,
        purpose=None,
    )
    assert result.succeeded, result.errors

    bundle = root / "world"
    assert not (bundle / "world.purpose.json").exists()
    with sqlite3.connect(bundle / "world.sqlite") as connection:
        connection.row_factory = sqlite3.Row
        metadata = connection.execute(
            "SELECT purpose_ref FROM _world_meta WHERE singleton = 1"
        ).fetchone()
        relation_names = {
            row["name"]
            for row in connection.execute("SELECT name FROM _world_relations")
        }
    assert metadata["purpose_ref"] is None
    assert "purpose_requirement_failure" not in relation_names
    assert set(ACCOUNT_SETTINGS_RELATION_NAMES) <= relation_names

    admission = json.loads(
        (bundle / "world.admission.json").read_text(encoding="utf-8")
    )
    assert all(scope != "PURPOSE" for scope in admission["relations"].values())

    world = Project(root).open_world()
    try:
        assert world.contract_identity() == ACCOUNT_SETTINGS_CONTRACT.identity()
        actual = {item["obligation_id"]: item for item in world.obligations()}
        assert set(actual) == {item.obligation_id for item in generated}
        assert len(world.candidate_associations()) == 2
        assert {
            item["relation_name"]
            for item in world.query("SELECT relation_name FROM _world_assertions")
        } == set(ACCOUNT_SETTINGS_RELATION_NAMES)
        assert not {
            "relative_prominence",
            "remains_available_during",
            "supports",
        } & {
            item["name"] for item in world.query("SELECT name FROM _world_relations")
        }

        by_dimension = {
            item["dimension"]: item
            for item in (
                {
                    **row,
                    "dimension": next(
                        generated_item.dimension
                        for generated_item in generated
                        if generated_item.obligation_id == obligation_id
                    ),
                }
                for obligation_id, row in actual.items()
            )
        }
        confirmation = by_dimension["confirmation_requirement"]
        distinction = by_dimension["consequence_distinction"]
        assert confirmation["state"] == "RESOLVED"
        assert confirmation["resolution_status"] == "RESOLVED"
        assert distinction["state"] == "UNRESOLVED"
        assert distinction["resolution_status"] == "INSUFFICIENT_WARRANT"

        confirmation_commitment = world.candidates_for(confirmation["obligation_id"])[0]
        distinction_commitment = world.candidates_for(distinction["obligation_id"])[0]
        assert confirmation_commitment.startswith("assertion:")
        assert distinction_commitment.startswith("assertion:")
        assert confirmation["selected_commitment_id"] == confirmation_commitment
        assert distinction["selected_commitment_id"] is None

        confirmation_warrant = world.warrant_for_assertion(confirmation_commitment)
        assert confirmation_warrant["construction_origins"] == ["SEMANTIC"]
        assert {item["kind"] for item in confirmation_warrant["bases"]} == {
            "SOURCE",
            "WORLD",
        }
        assert len(
            [item for item in confirmation_warrant["bases"] if item["kind"] == "SOURCE"]
        ) == 2

        distinction_warrant = world.warrant_for_assertion(distinction_commitment)
        assert len(
            [item for item in distinction_warrant["bases"] if item["kind"] == "SOURCE"]
        ) == 1
    finally:
        world.close()


def test_account_settings_structure_and_explorer_explain_the_governed_world(
    tmp_path: Path,
):
    root = _copy_fixture(tmp_path)
    result = rebuild(
        root,
        contract=ACCOUNT_SETTINGS_CONTRACT,
        governance=ACCOUNT_SETTINGS_LAW,
        evidence_authority=ACCOUNT_SETTINGS_EVIDENCE_AUTHORITY,
        purpose=None,
    )
    assert result.succeeded, result.errors

    with WorldExplorerAdapter(root / "world" / "world.sqlite") as explorer:
        assert explorer.demand() is None
        assert explorer.identity()["contract"] == ACCOUNT_SETTINGS_CONTRACT.identity()
        assert explorer.identity()["governance"] == ACCOUNT_SETTINGS_LAW.identity()
        assert explorer.identity()["evidence_authority"] == {
            "authority_id": "design-account-settings-evidence",
            "revision": "1",
        }
        assert explorer.governance()["state"] == "EFFECTIVE"
        assert explorer.governance()["proposed_law"]["state"] == "PROPOSED"
        assert explorer.governance()["source_selection"]["sources"][0]["source_id"] == (
            "account-settings-design-governance"
        )
        assert explorer.evidence_authority()["bindings"] == [
            {
                "source_id": "file://account-settings-requirements.md",
                "authority": "APPROVED_REQUIREMENT",
            },
            {
                "source_id": "file://AccountSettings.tsx",
                "authority": "IMPLEMENTATION_OBSERVATION",
            },
        ]

        structure = explorer.structure()
        assert structure is not None
        node_ids = {node["id"] for node in structure["nodes"]}
        assert {
            "account_settings",
            "profile_settings",
            "email_preferences",
            "save_changes",
            "danger_zone",
            "delete_account",
            "delete_confirmation",
            "account_deleted",
        } <= node_ids
        assert ("danger_zone", "delete_account") in {
            (item["container"], item["member"]) for item in structure["contains"]
        }
        danger_order = {
            item["child"]: item["order"]
            for item in structure["arrangement"]
            if item["parent"] == "danger_zone"
        }
        assert danger_order["delete_account"] < danger_order["delete_confirmation"]
        assert danger_order["delete_confirmation"] < danger_order["account_deleted"]
        assert all(
            "destructive" not in node and "irreversible" not in node
            for node in structure["nodes"]
        )

        obligations = explorer.obligations()
        assert len(obligations["obligations"]) == 2
        assert all(item["candidates"] for item in obligations["obligations"])
        for item in obligations["obligations"]:
            detail = explorer.obligation(item["obligation_id"])
            assert detail is not None
            assert detail["law_provenance"]["source_id"] == (
                "account-settings-design-governance"
            )
            assert detail["structural_bindings"]
            candidate = detail["candidates"][0]
            assert candidate["warrant"]["bases"]
            assert candidate["assessment"]["status"] in {
                "SUFFICIENT",
                "INSUFFICIENT",
            }
            assert detail["context"]["governance"] == ACCOUNT_SETTINGS_LAW.identity()

        confirmation_id = next(
            item["obligation_id"]
            for item in obligations["obligations"]
            if item["dimension"] == "confirmation_requirement"
        )
        confirmation_detail = explorer.obligation(confirmation_id)
        assert confirmation_detail["resolution"]["status"] == "RESOLVED"
        assert confirmation_detail["candidates"][0]["assessment"]["status"] == (
            "SUFFICIENT"
        )
        assert set(
            confirmation_detail["candidates"][0]["assessment"]["warrant_authorities"]
        ) == {"APPROVED_REQUIREMENT", "IMPLEMENTATION_OBSERVATION"}

        distinction_id = next(
            item["obligation_id"]
            for item in obligations["obligations"]
            if item["dimension"] == "consequence_distinction"
        )
        distinction_detail = explorer.obligation(distinction_id)
        assert distinction_detail["resolution"]["status"] == "INSUFFICIENT_WARRANT"
        assert distinction_detail["candidates"][0]["assessment"][
            "warrant_authorities"
        ] == ["IMPLEMENTATION_OBSERVATION"]

    from starlette.testclient import TestClient

    with TestClient(build_app(root / "world" / "world.sqlite")) as client:
        assert client.get("/world/demand").json() == {"demand": None}
        payload = client.get("/world/obligations").json()
        assert len(payload["obligations"]) == 2
        assert client.get("/world/evidence-authority").json()["identity"] == {
            "authority_id": "design-account-settings-evidence",
            "revision": "1",
        }


def test_account_settings_law_does_not_follow_unselected_sources(tmp_path: Path):
    root = _copy_fixture(tmp_path, "unselected-law")
    manifest = json.loads(
        (root / "governance-sources.json").read_text(encoding="utf-8")
    )
    manifest["sources"] = []
    (root / "governance-sources.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    law = load_account_settings_law(root)
    structure = _structure(root)
    assert law.dimensions == ()
    assert law.enumerate_obligations(structure) == ()

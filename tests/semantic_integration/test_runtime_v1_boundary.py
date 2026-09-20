"""v1 product-boundary tests. No LLM. Runtime path, not semantic intelligence."""

from __future__ import annotations

import shutil
from pathlib import Path

from research.semantic_integration.runtime_v0.commit import fingerprint_accepted
from research.semantic_integration.runtime_v0.entry import BRIEF_NAME, prepare, publish
from research.semantic_integration.runtime_v0.project import Project
from research.semantic_integration.runtime_v0.purpose import FAILURE_RELATION
from research.semantic_integration.runtime_v0.__main__ import main

FIXTURE = Path("research/semantic_integration/runtime_v0/fixtures/minimal_v0")

CONSUMER_SQL = """
SELECT a.legal_name, o.amount_text
FROM customer_order AS o
JOIN account AS a ON a.account_id = o.account_id
ORDER BY a.legal_name
"""


def _copy_fixture(tmp_path: Path) -> Path:
    dest = tmp_path / "workspace"
    shutil.copytree(FIXTURE, dest)
    return dest


def test_prepare_writes_brief_without_publishing(tmp_path):
    dest = tmp_path / "empty"
    brief = prepare(dest, purpose="Join accounts to orders. Leave GM unresolved.\n")
    assert brief.name == BRIEF_NAME
    text = brief.read_text(encoding="utf-8")
    assert "publication validity" in text
    assert (dest / "purpose.txt").read_text(encoding="utf-8").startswith("Join accounts")
    assert not (dest / "accepted").exists()
    result = publish(dest)
    assert result.accepted is False
    assert result.reason == "construction_error"
    assert not (dest / "accepted").exists()


def test_prepare_then_publish_accepts_fixture(tmp_path):
    dest = _copy_fixture(tmp_path)
    prepare(dest)
    assert (dest / BRIEF_NAME).exists()
    result = publish(dest)
    assert result.accepted is True
    assert (dest / "diagnostics.json").exists()
    world = Project(dest).open_accepted()
    try:
        rows = world.query_semantic(CONSUMER_SQL)
        by_name = {row["legal_name"]: row["amount_text"] for row in rows}
        assert by_name["Acme Ltd"] == "100"
        assert by_name["Beta Ltd"] == "GM"
    finally:
        world.close()


def test_invalid_publish_cannot_replace_accepted(tmp_path):
    dest = _copy_fixture(tmp_path)
    assert publish(dest).accepted is True
    before = fingerprint_accepted(dest / "accepted")
    (dest / "construction.py").write_text(
        """
def construct(source, world, purpose):
    raise RuntimeError("no")
""",
        encoding="utf-8",
    )
    result = publish(dest)
    assert result.accepted is False
    assert fingerprint_accepted(dest / "accepted") == before


def test_ungrounded_world_base_fails_closed(tmp_path):
    dest = _copy_fixture(tmp_path)
    (dest / "construction.py").write_text(
        """
def construct(source, world, purpose):
    world.declare_relation(
        "account",
        [
            Role("account", RoleType.REFERENT),
            Role("account_code", RoleType.TEXT),
            Role("legal_name", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.add_referent("account:A1", label="Acme Ltd")
    world.assert_tuple(
        "account",
        {"account": "account:A1", "account_code": "A1", "legal_name": "Acme Ltd"},
        origin=ConstructionOrigin.SEMANTIC,
        grounding=None,
    )
""",
        encoding="utf-8",
    )
    result = publish(dest)
    assert result.accepted is False
    assert result.reason == "ungrounded_world_base"
    assert not (dest / "accepted").exists()


def test_accepted_reopens_in_a_new_session(tmp_path):
    dest = _copy_fixture(tmp_path)
    assert publish(dest).accepted is True
    first = Project(dest)
    world = first.open_accepted()
    world.close()
    second = Project(dest)
    world = second.open_accepted()
    try:
        names = {row["legal_name"] for row in world.query_semantic("SELECT legal_name FROM account")}
        assert names == {"Acme Ltd", "Beta Ltd"}
        assert world.admission[FAILURE_RELATION] == "PURPOSE"
    finally:
        world.close()


def test_sql_without_source_files_and_unresolved_is_not_absence(tmp_path):
    dest = _copy_fixture(tmp_path)
    assert publish(dest).accepted is True
    (dest / "sources" / "orders.csv").unlink()
    (dest / "sources" / "accounts.csv").unlink()
    world = Project(dest).open_accepted()
    try:
        rows = world.query_semantic(CONSUMER_SQL)
        assert {row["legal_name"]: row["amount_text"] for row in rows}["Beta Ltd"] == "GM"
        unresolved = world.query_semantic(
            "SELECT requirement_id, failure_kind FROM purpose_requirement_failure "
            "WHERE failure_kind = 'EXPLICIT_UNRESOLVED'"
        )
        assert unresolved[0]["requirement_id"] == "gm_token"
        gm = world.query_semantic(
            "SELECT amount_text FROM customer_order WHERE amount_text = 'GM'"
        )
        assert gm[0]["amount_text"] == "GM"
    finally:
        world.close()


def test_rebuild_keeps_consumer_sql_when_interface_unchanged(tmp_path):
    dest = _copy_fixture(tmp_path)
    assert publish(dest).accepted is True
    world = Project(dest).open_accepted()
    try:
        before = world.query_semantic(CONSUMER_SQL)
    finally:
        world.close()

    extra = (dest / "construction.py").read_text(encoding="utf-8")
    extra += """
    world.declare_relation(
        "source_note",
        [Role("note", RoleType.TEXT)],
        scope="WORLD",
    )
    world.assert_tuple(
        "source_note",
        {"note": "accounts.csv is the legal-name source"},
        origin=ConstructionOrigin.MECHANICAL,
        grounding=source.grounding("note.txt", "whole"),
    )
"""
    (dest / "construction.py").write_text(extra, encoding="utf-8")
    assert publish(dest).accepted is True
    world = Project(dest).open_accepted()
    try:
        after = world.query_semantic(CONSUMER_SQL)
        assert after == before
        notes = world.query_semantic("SELECT note FROM source_note")
        assert notes
    finally:
        world.close()


def test_workspace_root_is_evidence_when_sources_dir_absent(tmp_path):
    dest = tmp_path / "flat"
    dest.mkdir()
    shutil.copy2(FIXTURE / "purpose.txt", dest / "purpose.txt")
    shutil.copy2(FIXTURE / "sources" / "accounts.csv", dest / "accounts.csv")
    shutil.copy2(FIXTURE / "sources" / "orders.csv", dest / "orders.csv")
    shutil.copy2(FIXTURE / "sources" / "note.txt", dest / "note.txt")
    shutil.copy2(FIXTURE / "construction.py", dest / "construction.py")
    result = publish(dest)
    assert result.accepted is True
    world = Project(dest).open_accepted()
    try:
        assert world.query_semantic("SELECT account_code FROM account")
    finally:
        world.close()


def test_construction_may_import_workspace_helpers(tmp_path):
    dest = _copy_fixture(tmp_path)
    (dest / "labels.py").write_text("LEGAL = 'Acme Ltd'\n", encoding="utf-8")
    src = (dest / "construction.py").read_text(encoding="utf-8")
    src = "from labels import LEGAL\n" + src.replace('"Acme Ltd"', "LEGAL")
    (dest / "construction.py").write_text(src, encoding="utf-8")
    result = publish(dest)
    assert result.accepted is True
    world = Project(dest).open_accepted()
    try:
        names = {row["legal_name"] for row in world.query_semantic("SELECT legal_name FROM account")}
        assert "Acme Ltd" in names
    finally:
        world.close()


def test_cli_prepare_and_publish(tmp_path):
    dest = _copy_fixture(tmp_path)
    assert main(["prepare", str(dest)]) == 0
    assert (dest / BRIEF_NAME).exists()
    assert main(["publish", str(dest)]) == 0

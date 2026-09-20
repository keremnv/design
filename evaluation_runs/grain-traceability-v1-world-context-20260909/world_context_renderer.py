#!/usr/bin/env python3
"""Deterministically render orientation metadata from a sealed World bundle.

This renderer deliberately does not read assertion rows, referent rows, source
grounding details, construction artifacts, benchmark files, or evaluator files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


RENDERER_VERSION = "world-context-renderer-v1.0.0"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def q1(db: sqlite3.Connection, sql: str, args=()):
    return db.execute(sql, args).fetchone()[0]


def render(world_root: Path, world_hash: str) -> str:
    required = [
        "world.sqlite",
        "world.purpose.json",
        "world.sqlite.origins.json",
        "world.admission.json",
    ]
    for name in required:
        if not (world_root / name).is_file():
            raise FileNotFoundError(world_root / name)

    admission = json_load(world_root / "world.admission.json")
    purpose = json_load(world_root / "world.purpose.json")
    origins = json_load(world_root / "world.sqlite.origins.json")
    scopes = admission.get("relations", {})

    db = sqlite3.connect(f"file:{world_root / 'world.sqlite'}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    meta = db.execute("SELECT world_id, revision FROM _world_meta WHERE singleton=1").fetchone()
    relation_rows = db.execute(
        "SELECT name, mode, relation_version FROM _world_relations ORDER BY name"
    ).fetchall()
    referent_count = q1(db, "SELECT count(*) FROM _world_referents")
    assertion_count = q1(db, "SELECT count(*) FROM _world_assertions")
    grounding_rows = db.execute(
        "SELECT kind, count(*) AS n FROM _world_groundings GROUP BY kind ORDER BY kind"
    ).fetchall()

    relation_lines: list[str] = []
    relation_counts: dict[str, int] = {}
    relation_specs: dict[str, list[tuple[str, str]]] = {}
    for rel in relation_rows:
        name = rel["name"]
        count = q1(db, "SELECT count(*) FROM _world_assertions WHERE relation_name=?", (name,))
        relation_counts[name] = count
        roles = db.execute(
            "SELECT role_name, role_type FROM _world_roles "
            "WHERE relation_name=? ORDER BY ordinal",
            (name,),
        ).fetchall()
        role_specs = [(r["role_name"], r["role_type"]) for r in roles]
        relation_specs[name] = role_specs
        signature = ", ".join(f"{role}: {typ}" for role, typ in role_specs)
        scope = scopes.get(name, "UNDECLARED")
        relation_lines.extend(
            [
                f"{name}({signature})",
                f"  {rel['mode']} · {scope} · {count} rows",
            ]
        )

    derivation_lines: list[str] = []
    derivation_rows = db.execute(
        "SELECT relation_name, execution_status, last_run_world_revision, "
        "output_cardinality FROM _world_derivations ORDER BY relation_name"
    ).fetchall()
    for row in derivation_rows:
        inputs = [
            r[0]
            for r in db.execute(
                "SELECT input_relation FROM _world_derivation_inputs "
                "WHERE relation_name=? ORDER BY input_relation",
                (row["relation_name"],),
            )
        ]
        current = (
            row["execution_status"] == "SUCCEEDED"
            and row["last_run_world_revision"] == meta["revision"]
        )
        derivation_lines.extend(
            [
                f"{row['relation_name']}",
                f"  inputs: {', '.join(inputs) if inputs else '(none)'}",
                f"  state: {'CURRENT' if current else 'STALE'}",
                f"  execution: {row['execution_status']} · {row['output_cardinality']} outputs",
            ]
        )

    completeness_lines: list[str] = []
    for row in db.execute(
        "SELECT target_relation, universe_relation, status, basis, "
        "known_gaps_json FROM _world_completeness ORDER BY target_relation"
    ):
        gaps = json.loads(row["known_gaps_json"])
        completeness_lines.extend(
            [
                f"{row['target_relation']} over {row['universe_relation']}",
                f"  status: {row['status']}",
                f"  basis: {row['basis']}",
                f"  known gaps: {'; '.join(gaps) if gaps else '(none recorded)'}",
            ]
        )

    unresolved_names = [
        row["name"]
        for row in relation_rows
        if any(token in row["name"].lower() for token in ("unresolved", "failure", "unknown"))
    ]
    unresolved_lines: list[str] = []
    for name in unresolved_names:
        roles = ", ".join(f"{role}: {typ}" for role, typ in relation_specs[name])
        unresolved_lines.extend(
            [f"{name}({roles})", f"  {relation_counts[name]} rows"]
        )

    grounding_lines = [
        f"{row['kind']}: {row['n']} records in _world_groundings"
        for row in grounding_rows
    ]
    grounding_lines.extend(
        [
            "assertion origins: world.sqlite.origins.json",
            "mechanism tables: _world_groundings, _world_assertions",
        ]
    )

    access_lines = [name for name in required if (world_root / name).is_file()]
    purpose_text = purpose.get("text", "")
    if not isinstance(purpose_text, str):
        raise TypeError("world.purpose.json text is not a string")

    sections = [
        "WORLD CONTEXT",
        f"renderer: {RENDERER_VERSION}",
        f"world hash: {world_hash}",
        f"world id: {meta['world_id']}",
        f"revision: {meta['revision']}",
        f"world.sqlite sha256: {sha256(world_root / 'world.sqlite')}",
        "",
        "PURPOSE",
        purpose_text.rstrip(),
        "",
        "SEMANTIC SURFACE",
        f"{len(relation_rows)} relations · {referent_count} referents · {assertion_count} assertions",
        "",
        *relation_lines,
        "",
        "DERIVATIONS",
        *(derivation_lines or ["(none recorded)"]),
        "",
        "COMPLETENESS",
        *(completeness_lines or ["(none recorded)"]),
        "",
        "UNRESOLVEDNESS",
        *(unresolved_lines or ["(no structural unresolvedness relation identified)"]),
        "",
        "GROUNDING",
        *grounding_lines,
        "",
        "ACCESS",
        *access_lines,
        "",
    ]
    db.close()
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-root", type=Path, required=True)
    parser.add_argument("--world-hash", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    text = render(args.world_root, args.world_hash)
    args.output.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({
        "renderer": RENDERER_VERSION,
        "world_hash": args.world_hash,
        "output": str(args.output),
        "bytes": len(text.encode("utf-8")),
        "characters": len(text),
        "words": len(text.split()),
        "sha256": sha256(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

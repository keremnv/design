"""Standalone fresh consumer: schema discovery plus supported World reads.

No fixture, constructor, adapter, relation-name, or expected-answer imports.
Role vocabulary expresses the questions; actual relation/column names and
answers are discovered from the supplied World. The acceptance test copies
this script and the read runtime into an isolated process/filesystem.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# The acceptance harness supplies a copy of the supported runtime beside us.
# Running directly in the repository uses the normally installed package.
runtime = Path(__file__).parent / "runtime"
if runtime.exists():
    sys.path.insert(0, str(runtime))

from ontology_author.world import ConstructionWorld
from ontology_author.world.explorer import WorldExplorerAdapter


def quote(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def consume(bundle: Path) -> dict:
    with WorldExplorerAdapter(bundle / "world.sqlite") as reader:
        schema = reader.schema()
        labels = {item["id"]: item["label"] for item in reader.referents()}
        governing, unresolved, origins, derivations, negatives = [], [], {}, {}, []
        for relation in schema:
            name = relation["name"]
            roles = {role["name"]: role for role in relation["roles"]}
            # SQL is built from the discovered physical role mapping.
            projection = ", ".join(
                f'{quote(role["column"])} AS {quote(role["name"])}'
                for role in relation["roles"]
            )
            rows = reader.query_semantic(f"SELECT {projection} FROM {quote(name)}")
            origins[name] = relation["origins"]
            if set(roles) == {"requirement", "program", "provider"}:
                for page_row in reader.rows(name)["rows"]:
                    assertion = reader.assertion(page_row["assertion_id"])
                    governing.append({
                        "relation": name, "values": assertion["values"],
                        "labels": {key: labels.get(value, value) for key, value in assertion["values"].items()},
                        "assertion_id": assertion["assertion_id"],
                        "origin": assertion["origin"], "grounding": assertion["grounding"],
                    })
            if {"question", "status", "reason"}.issubset(roles):
                unresolved.extend(row for row in rows if row["status"] == "UNRESOLVED")
            if relation["mode"] == "DERIVED":
                derivations[name] = reader.derivation(name)
                if not rows:
                    receipt = relation["completeness"]
                    universe = next((item for item in schema if receipt and item["name"] == receipt["universe"]), None)
                    # Deliberately bounded application inference: accept only
                    # a current COMPLETE receipt over an explicit BASE set.
                    # Other cases stay UNKNOWN; raw SQL itself is not policed.
                    exhaustive = bool(receipt and receipt["status"] == "COMPLETE"
                                      and receipt["current"] and universe
                                      and universe["mode"] == "BASE")
                    negatives.append({"relation": name, "description": relation["description"],
                                      "receipt": receipt,
                                      "conclusion": "ABSENT_WITHIN_RECORDED_UNIVERSE" if exhaustive else "UNKNOWN"})
        # Full receipt inspection (including basis) is another supported read,
        # independent of the explorer's compact presentation.
        world = ConstructionWorld.open(bundle / "world.sqlite")
        try:
            for item in negatives:
                item["full_receipt"] = world.latest_completeness(item["relation"])
        finally:
            world.close()
        return {"discovered_schema": schema, "governing_knowledge": governing,
                "unresolved_questions": unresolved, "construction_origins": origins,
                "derivations": derivations, "negative_inferences": negatives}


def main():
    bundle = Path(sys.argv[1]).resolve()
    allowed_roots = [bundle, runtime.resolve(), Path(sys.base_prefix).resolve()]
    allowed_files = {Path(__file__).resolve()}
    reads = set()

    def audit(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
            flags = args[2]
            import os
            if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                raise PermissionError("consumer file writes are forbidden")
            if path not in allowed_files and not any(path.is_relative_to(root) for root in allowed_roots):
                raise PermissionError(f"consumer source access forbidden: {path}")
            if path.is_relative_to(bundle / "evidence"):
                raise PermissionError("consumer cannot reconstruct joins from evidence blobs")
            reads.add(str(path))
        elif event == "sqlite3.connect":
            target = str(args[0])
            if target != f"{(bundle / 'world.sqlite').as_uri()}?mode=ro":
                raise PermissionError(f"consumer requires read-only bundle SQL: {target}")
        elif event in {"os.chmod", "os.remove", "os.rename", "os.mkdir", "subprocess.Popen", "socket.connect"}:
            raise PermissionError(f"consumer mutation/external access forbidden: {event}")

    sys.addaudithook(audit)
    answer = consume(bundle)
    answer["file_reads"] = sorted(reads)
    print(json.dumps(answer, sort_keys=True))


if __name__ == "__main__":
    main()

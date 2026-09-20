#!/usr/bin/env python3
"""Exercise catalog computations with the supplied development tasks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
TASKS = json.loads((WORKSPACE / "development_tasks.json").read_text())
RUN = ROOT / "run.py"


def invoke(computation_id: str, params: dict) -> dict:
    cmd = [
        sys.executable,
        str(RUN),
        computation_id,
        "--params-json",
        json.dumps(params),
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(proc.stdout)


def main() -> int:
    family_to_id = {c["family"]: c["id"] for c in json.loads((ROOT / "catalog.json").read_text())["computations"]}
    results = []
    for task in TASKS["tasks"]:
        computation_id = family_to_id[task["family"]]
        first = invoke(computation_id, task["parameters"])
        second = invoke(computation_id, task["parameters"])
        if first != second:
            print(f"NONDETERMINISTIC: {task['task_id']}", file=sys.stderr)
            return 1
        results.append(
            {
                "task_id": task["task_id"],
                "family": task["family"],
                "computation_id": computation_id,
                "parameters": task["parameters"],
                "result": first,
            }
        )
        print(f"OK {task['task_id']} {computation_id} deterministic", file=sys.stderr)

    json.dump({"experiment": TASKS["experiment"], "runs": results}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

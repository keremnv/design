#!/usr/bin/env python3
"""Exercise catalogued computations on the development tasks (and nearby parameterized cases)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import run_computation  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEV_TASKS = json.loads((ROOT / "development_tasks.json").read_text())

FAMILY_TO_COMPUTATION = {
    "shipment_source_status": "shipment_source_status",
    "processor_receipt_provenance": "processor_receipt_provenance",
    "custody_owner_at": "custody_owner_at",
    "inspection_downstream_scope": "inspection_downstream_scope",
}

EXTRA_CASES = [
    ("shipment_source_status", {"dispatch": "PGE-OUT-5002"}),
    ("shipment_source_status", {"dispatch": "PG-OUT-5004"}),
    ("shipment_source_status", {"dispatch": "PGE-OUT-5003"}),
    ("processor_receipt_provenance", {"processor_receipt": "HFM-IN-604"}),
    ("processor_receipt_provenance", {"processor_receipt": "HFM-IN-602"}),
    ("custody_owner_at", {"material": "DR-44", "timestamp": "2025-09-04T09:32:00-05:00"}),
    ("custody_owner_at", {"material": "DR-44", "timestamp": "2025-09-06T00:00:00-05:00"}),
    ("custody_owner_at", {"material": "MCR-118", "timestamp": "2025-09-07T12:00:00-05:00"}),
    ("inspection_downstream_scope", {"sample": "SMP-602B"}),
    ("inspection_downstream_scope", {"sample": "SMP-604Q"}),
    ("identifier_canonical", {"identifier": "DR44"}),
    ("bin_tickets_before", {"bin": "North House 12", "timestamp": "2025-09-04T09:40:00-05:00"}),
]


def expect(cond: bool, message: str, errors: list[str]) -> None:
    if not cond:
        errors.append(message)


def check_dev_results(task_id: str, payload: dict, errors: list[str]) -> None:
    result = payload["result"]
    if task_id == "DEV-SRC-001":
        expect(result["dispatch"] == "PGE-OUT-5001", "dispatch canonical", errors)
        expect(result["source_location"]["established"] is True, "source location established", errors)
        expect(result["source_location"]["bin"] == "BIN-12", "source bin BIN-12", errors)
        expect(result["established_contributing_identities"] == [], "no hopper-named tickets for 5001", errors)
        expect(set(result["candidate_identities_in_source_bin"]) == {"DR-44", "WB-390", "EF-18"}, "three bin occupants", errors)
        expect(result["source_allocation_unresolved"] is True, "5001 allocation unresolved", errors)
        expect(any(u["requirement_id"] == "out_5001_ticket_composition" for u in result["unresolved"]), "composition failure", errors)
    elif task_id == "DEV-PROV-001":
        path = result["established_path"]
        expect(path is not None, "path established", errors)
        expect(path["dispatch_ref"] == "PGE-OUT-5001", "upstream dispatch", errors)
        expect(path["manifest_no"] == "RL-8841", "manifest", errors)
        expect(path["mill_receipt"] == "HFM-IN-601", "mill receipt", errors)
        expect(result["processing_established"] is True, "process established", errors)
        expect(result["processing"]["output_batch"] == "FEED-2206", "output FEED-2206", errors)
        expect(result["unresolved_links"]["upstream_ticket_allocation"] is True, "upstream allocation unresolved", errors)
    elif task_id == "DEV-CUST-001":
        expect(result["recorded_owner"] == "Prairie Gate Elevator", "owner", errors)
        expect(result["recorded_custodian"] == "Prairie Gate Elevator", "custodian", errors)
        expect(result["covering_event"]["record_no"] == "TR-101", "TR-101 covers noon Sep 3", errors)
    elif task_id == "DEV-INSP-001":
        expect(result["sampled_identities"] == ["DR-44"], "sample is DR-44", errors)
        expect(result["established_affected"]["shipments"] == [], "no established downstream shipment", errors)
        expect(result["established_affected"]["processor_receipts"] == [], "no established mill receipt", errors)
        expect(result["established_affected"]["processed_outputs"] == [], "no established output", errors)
        expect(any(u.get("dispatch") == "PGE-OUT-5001" for u in result["unresolved_scope"]), "5001 in unresolved scope", errors)


def main() -> int:
    errors: list[str] = []
    outputs = []
    for task in DEV_TASKS["tasks"]:
        computation = FAMILY_TO_COMPUTATION[task["family"]]
        payload = run_computation(computation, task["parameters"])
        outputs.append({"task_id": task["task_id"], "payload": payload})
        check_dev_results(task["task_id"], payload, errors)
    extra_payloads = []
    for computation, params in EXTRA_CASES:
        extra_payloads.append(run_computation(computation, params))

    # Extra sanity: 5002 names two tickets and remains unallocated; 604 has no mill run.
    s5002 = extra_payloads[0]["result"]
    expect(s5002["established_contributing_identities"] == ["EF-18", "WB-390"], "5002 named tickets", errors)
    expect(s5002["source_allocation_unresolved"] is True, "5002 split unresolved", errors)
    p604 = extra_payloads[3]["result"]
    expect(p604["processing_established"] is False, "604 has no mill run", errors)
    expect(p604["established_path"]["dispatch_ref"] == "PGE-OUT-5004", "604 path from 5004", errors)
    c_handoff = extra_payloads[5]["result"]
    expect(c_handoff["recorded_custodian"] == "Redline Haulage", "DR-44 at handoff to Redline", errors)
    expect(c_handoff["recorded_owner"] == "Prairie Gate Elevator", "title still PGE at handoff", errors)
    c_later = extra_payloads[6]["result"]
    expect(c_later["recorded_owner"] == "Hearthland Feed Mill", "title after mill acceptance", errors)
    mill_sample = extra_payloads[8]["result"]
    expect(
        any(o.get("output_batch") == "FEED-2207" for o in mill_sample["established_affected"]["processed_outputs"]),
        "SMP-602B established output FEED-2207",
        errors,
    )

    if errors:
        sys.stderr.write("FAILED\n")
        for e in errors:
            sys.stderr.write(f"  - {e}\n")
        return 1
    sys.stdout.write(f"passed {len(DEV_TASKS['tasks'])} development tasks and {len(EXTRA_CASES)} extra cases\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

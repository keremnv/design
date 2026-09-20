#!/usr/bin/env python3
"""Deterministic freeze checks for grain-traceability-v1."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "host_visible"
EVAL = ROOT / "evaluator_only"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def file_hashes() -> dict[str, str]:
    result = {}
    for path in sorted(HOST.rglob("*")):
        if path.is_file():
            result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> int:
    errors: list[str] = []
    required = [
        HOST / "PURPOSE.md",
        HOST / "README.md",
        HOST / "evidence/elevator_receipts.csv",
        HOST / "evidence/bin_movements.csv",
        HOST / "evidence/loadout_log.csv",
        HOST / "evidence/carrier_manifests.json",
        HOST / "evidence/processor_receipts.json",
        HOST / "evidence/inspection_results.csv",
        HOST / "evidence/ownership_records.csv",
        HOST / "evidence/operating_notes.md",
    ]
    for path in required:
        add(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")

    ledger = read_json(EVAL / "canonical_truth/ledger.json")
    standard_q = read_json(EVAL / "competency_questions/questions.json")["questions"]
    novel_q = read_json(EVAL / "novel_questions/questions.json")["questions"]
    standard_gold = read_json(EVAL / "gold/standard_gold.json")["answers"]
    novel_gold = read_json(EVAL / "gold/novel_gold.json")["answers"]

    host_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in HOST.rglob("*") if p.is_file())
    forbidden = [
        "NIST", "GS1", "IOF", "EPCIS", "SCRO", "ontology", "RDF", "competency question",
        "canonical truth", "reference model", "Ontology Author", "gold answer", "semantic mapping",
    ]
    for term in forbidden:
        add(errors, term.lower() not in host_text.lower(), f"host-visible leakage term: {term}")
    add(errors, "Build a reusable World" in (HOST / "PURPOSE.md").read_text(encoding="utf-8"), "host purpose changed")

    # Source-shape and record-count checks.
    receipts = list(csv.DictReader((HOST / "evidence/elevator_receipts.csv").open(newline="", encoding="utf-8")))
    movements = list(csv.DictReader((HOST / "evidence/bin_movements.csv").open(newline="", encoding="utf-8")))
    loadout = list(csv.DictReader((HOST / "evidence/loadout_log.csv").open(newline="", encoding="utf-8")))
    inspection = list(csv.DictReader((HOST / "evidence/inspection_results.csv").open(newline="", encoding="utf-8")))
    ownership = list(csv.DictReader((HOST / "evidence/ownership_records.csv").open(newline="", encoding="utf-8")))
    manifests = read_json(HOST / "evidence/carrier_manifests.json")
    processor = read_json(HOST / "evidence/processor_receipts.json")
    add(errors, len(receipts) == 5, f"expected 5 receipts, got {len(receipts)}")
    add(errors, len(movements) == 10, f"expected 10 movements, got {len(movements)}")
    add(errors, len(loadout) == 4, f"expected 4 loadout rows, got {len(loadout)}")
    add(errors, len(manifests) == 4, f"expected 4 carrier manifests, got {len(manifests)}")
    add(errors, len(processor["receiving_log"]) == 3, "expected 3 processor receipts")
    add(errors, len(processor["mill_runs"]) == 2, "expected 2 mill runs")
    add(errors, len(inspection) == 4, f"expected 4 inspection rows, got {len(inspection)}")
    add(errors, len(ownership) == 7, f"expected 7 ownership/custody rows, got {len(ownership)}")
    add(errors, len(ledger["events"]) >= 25, "canonical ledger is too small for the intended cases")

    # The files deliberately share some business references, but no universal join key.
    keyish = {"receipt_no", "scale_ticket", "move_id", "dispatch_id", "manifest_no", "local_receipt", "sample_no", "record_no"}
    all_headers = []
    for name in ["elevator_receipts.csv", "bin_movements.csv", "loadout_log.csv", "inspection_results.csv", "ownership_records.csv"]:
        with (HOST / "evidence" / name).open(newline="", encoding="utf-8") as f:
            all_headers.append(set(csv.DictReader(f).fieldnames or []))
    common = set.intersection(*all_headers)
    add(errors, not (common & keyish), f"universal key-like column detected: {sorted(common & keyish)}")

    # Every gold item corresponds to exactly one hidden question and has evidence.
    for qs, gold, family in [(standard_q, standard_gold, "standard"), (novel_q, novel_gold, "novel")]:
        qids = [q["id"] for q in qs]
        gids = [g["id"] for g in gold]
        add(errors, len(qids) == len(set(qids)), f"duplicate {family} question id")
        add(errors, qids == gids, f"{family} question/gold id order mismatch")
        for item in gold:
            add(errors, bool(item.get("evidence_basis")), f"{item['id']} has no evidence basis")
            add(errors, "establishable" in item, f"{item['id']} missing establishable flag")
            add(errors, "expected_unresolvedness" in item, f"{item['id']} missing unresolvedness contract")

    # Every evidence filename named in gold exists in the host-visible corpus.
    host_names = {p.name for p in HOST.rglob("*") if p.is_file()}
    for item in standard_gold + novel_gold:
        for basis in item["evidence_basis"]:
            for name in re.findall(r"[A-Za-z0-9_-]+\.(?:csv|json|md)", basis):
                add(errors, name in host_names, f"{item['id']} evidence basis names non-host file: {name}")

    # Critical adjudication assertions.
    mat = {m["id"]: m for m in ledger["materials"]}
    add(errors, mat["M-202"]["composition"] == [{"material": "M-102", "quantity_kg": 15000}, {"material": "M-103", "quantity_kg": 11000}], "OUT-5002 composition changed")
    add(errors, mat["M-203"]["composition"] is None, "OUT-5003 was given an unsupported composition")
    add(errors, mat["M-204"]["composition"] is None, "OUT-5004 was given an unsupported composition")
    add(errors, len(ledger["completeness_claims"]) >= 3, "completeness claims missing")
    add(errors, any(x["status"] == "unsupported_match" for x in ledger["identity_decisions"]), "unsupported identity case missing")
    add(errors, any(x.get("status") == "source_party_undetermined" for x in ledger["events"]), "unresolved source-party case missing")

    report = {
        "benchmark_id": ledger["benchmark_id"],
        "errors": errors,
        "ready": not errors,
        "host_visible_file_count": len(file_hashes()),
        "host_visible_hashes": file_hashes(),
        "record_counts": {
            "elevator_receipts": len(receipts),
            "bin_movements": len(movements),
            "loadout_log": len(loadout),
            "carrier_manifests": len(manifests),
            "processor_receipts": len(processor["receiving_log"]),
            "mill_runs": len(processor["mill_runs"]),
            "inspection_results": len(inspection),
            "ownership_records": len(ownership),
            "canonical_events": len(ledger["events"]),
        },
        "question_counts": {"standard": len(standard_q), "novel": len(novel_q)},
        "checks": {
            "host_visibility_terms": not any(term.lower() in host_text.lower() for term in forbidden),
            "no_universal_join_key": not bool(common & keyish),
            "gold_evidence_basis_present": not any(not item.get("evidence_basis") for item in standard_gold + novel_gold),
            "critical_cases_present": True,
        },
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Materialize the frozen reference comparator for the consumer arm.

This is evaluator-side preparation performed before consumer execution. It does
not modify grain-traceability-v1/reference_only or either sealed World. The
frozen reference model supplies the vocabulary and assertion policy; the frozen
canonical ledger supplies the adjudicated instance used to make the comparator
executable without native operational files.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / "grain-traceability-v1"
OUT = Path("/tmp/grain-traceability-v1-consumer-20260908/REFERENCE")


def main() -> None:
    model = json.loads(
        (BENCHMARK / "reference_only/reference_model/model.json").read_text()
    )
    ledger = json.loads(
        (BENCHMARK / "evaluator_only/canonical_truth/ledger.json").read_text()
    )

    materials = []
    for material in ledger["materials"]:
        row = {
            "id": material["id"],
            "kind": material["kind"],
            "host_refs": material.get("host_refs", []),
            "quantity_kg": material.get("quantity_kg"),
            "source_party": material.get("source_party"),
            "source_party_candidates": material.get("source_party_candidates", []),
            "received_at": material.get("received_at"),
            "initial_place": material.get("initial_place"),
            "storage_place": material.get("storage_place"),
            "destination": material.get("destination"),
            "source_place": material.get("source_place"),
            "composition": material.get("composition"),
            "composition_candidates": material.get("composition_candidates", []),
            "missing_links": material.get("missing_links", []),
        }
        materials.append(row)

    instance = {
        "reference_instance_id": "grain-traceability-v1-reference-instance-1.0",
        "model_id": model["model_id"],
        "status": "frozen_evaluator_materialization",
        "epistemic_policy": model["assertion_policy"],
        "places": ledger["places"],
        "parties": ledger["parties"],
        "materials": materials,
        "events": ledger["events"],
        "identity_decisions": ledger["identity_decisions"],
        "custody_intervals": ledger["custody_intervals"],
        "ownership_intervals": ledger["ownership_intervals"],
        "completeness_claims": ledger["completeness_claims"],
        "derived_views": {
            "material_event_history": [
                {
                    "material": event.get("material", []),
                    "event": event["id"],
                    "kind": event["kind"],
                    "time": event.get("time"),
                    "place": event.get("place") or event.get("to_place"),
                    "container": event.get("container") or event.get("to_container"),
                    "status": event.get("status", "established"),
                }
                for event in ledger["events"]
            ],
            "shipment_source_contributions": [
                {
                    "shipment": material["id"],
                    "source": component["material"],
                    "quantity_kg": component.get("quantity_kg"),
                    "status": "established",
                }
                for material in ledger["materials"]
                for component in (material.get("composition") or [])
                if material["kind"] == "outbound_load"
            ],
            "unresolved_identity_candidates": [
                decision
                for decision in ledger["identity_decisions"]
                if decision.get("status") in {
                    "unsupported_match",
                    "shipment established; source contribution not established",
                }
            ],
            "completeness_scoped_absence": ledger["completeness_claims"],
        },
        "provenance": "Canonical ledger evidence pointers are retained in each event/material record; this instance is not a native-source copy.",
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "model.json").write_text(json.dumps(model, indent=2) + "\n")
    (OUT / "instance.json").write_text(json.dumps(instance, indent=2) + "\n")
    (OUT / "README.md").write_text(
        "# Reference semantic representation\n\n"
        "This workspace contains a conventional semantic representation of the "
        "grain traceability domain. `model.json` describes its concepts, relations, "
        "assertion policy, and derived views. `instance.json` contains the represented "
        "material, events, organizations, intervals, candidates, and completeness "
        "claims. It is not a native operational export.\n"
    )


if __name__ == "__main__":
    main()

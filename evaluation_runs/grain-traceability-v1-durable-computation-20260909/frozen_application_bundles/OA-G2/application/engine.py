"""Deterministic grain-trace computations bound to the sealed World."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

APPLICATION_DIR = Path(__file__).resolve().parent
WORLD_SQLITE = APPLICATION_DIR.parent / "world" / "world.sqlite"
WORLD_HASH = "24f183176c742ec1326776de12cb73aae98250bb0e8bc89df0f8b37be6f1d220"
WORLD_SQLITE_SHA256 = "fdd4f332b7b5372bdfc1da6f0e9e1a33b96aa6c12c129768bec30e11f80f4586"

SITE_PRAIRIE_GATE = "Prairie Gate Elevator"


def connect_world() -> sqlite3.Connection:
    uri = f"file:{WORLD_SQLITE}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def parse_dt(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    return datetime.fromisoformat(value)


def dump(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def rows(conn: sqlite3.Connection, sql: str, params=()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params)]


def alias_maps(conn: sqlite3.Connection) -> tuple[dict[str, str], dict[str, set[str]]]:
    form_to_canonical: dict[str, str] = {}
    canonical_forms: dict[str, set[str]] = {}
    for r in rows(conn, "SELECT form, canonical, kind FROM identifier_alias"):
        form_to_canonical[r["form"]] = r["canonical"]
        canonical_forms.setdefault(r["canonical"], set()).add(r["form"])
        canonical_forms[r["canonical"]].add(r["canonical"])
        form_to_canonical.setdefault(r["canonical"], r["canonical"])
    return form_to_canonical, canonical_forms


def canonical(form_to_canonical: dict[str, str], value: str) -> str:
    return form_to_canonical.get(value, value)


def identity_forms(canonical_forms: dict[str, set[str]], value: str, form_to_canonical: dict[str, str]) -> set[str]:
    can = canonical(form_to_canonical, value)
    forms = set(canonical_forms.get(can, {can}))
    forms.add(value)
    forms.add(can)
    return forms


def split_lot_label(label: str) -> list[str]:
    if not label:
        return []
    parts = [p.strip() for p in label.replace("?", "").split("/")]
    return [p for p in parts if p]


class World:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.form_to_canonical, self.canonical_forms = alias_maps(conn)

    def canon(self, value: str) -> str:
        return canonical(self.form_to_canonical, value)

    def forms(self, value: str) -> set[str]:
        return identity_forms(self.canonical_forms, value, self.form_to_canonical)

    def matches(self, recorded: str, query: str) -> bool:
        return self.canon(recorded) == self.canon(query)


def unresolved_for(world: World, identity: str) -> list[dict]:
    out = []
    for r in rows(world.conn, "SELECT requirement_id, affected_identity, failure_kind, relation_name, subject_json, grounding_ref FROM purpose_requirement_failure"):
        if world.matches(r["affected_identity"], identity):
            subject = json.loads(r["subject_json"])
            out.append(
                {
                    "requirement_id": r["requirement_id"],
                    "affected_identity": world.canon(r["affected_identity"]),
                    "failure_kind": r["failure_kind"],
                    "relation_name": r["relation_name"],
                    "reason": subject.get("reason"),
                    "subject": subject,
                }
            )
    out.sort(key=lambda x: x["requirement_id"])
    return out


def loadout_for_dispatch(world: World, dispatch: str) -> dict | None:
    target = world.canon(dispatch)
    for r in rows(world.conn, "SELECT dispatch_ref, bin, loadout_id FROM loadout_from_bin"):
        if world.matches(r["dispatch_ref"], target):
            event = None
            for e in rows(
                world.conn,
                "SELECT dispatch_id, loaded_at, truck_tag, dispatch_ref, bin_label, quantity_kg, route_code, desk_comment FROM loadout_event",
            ):
                if world.matches(e["dispatch_ref"], target) and e["dispatch_id"] == r["loadout_id"]:
                    event = e
                    break
            return {
                "dispatch_ref": world.canon(r["dispatch_ref"]),
                "bin": world.canon(r["bin"]),
                "loadout_id": r["loadout_id"],
                "loaded_at": None if event is None else event["loaded_at"],
                "truck_tag": None if event is None else event["truck_tag"],
                "bin_label": None if event is None else event["bin_label"],
                "quantity_kg": None if event is None else event["quantity_kg"],
                "route_code": None if event is None else event["route_code"],
                "desk_comment": None if event is None else event["desk_comment"],
            }
    return None


def tickets_into_bin_before(world: World, bin_id: str, when: str | None) -> list[dict]:
    cutoff = parse_dt(when)
    found = []
    for r in rows(world.conn, "SELECT scale_ticket, bin, move_id FROM ticket_into_bin"):
        if not world.matches(r["bin"], bin_id):
            continue
        moves = rows(
            world.conn,
            "SELECT move_id, logged_at, from_point, to_point, material_note, quantity_kg, work_order FROM storage_move WHERE move_id = ?",
            (r["move_id"],),
        )
        if not moves:
            continue
        logged = moves[0]["logged_at"]
        if cutoff is not None and parse_dt(logged) > cutoff:
            continue
        found.append(
            {
                "scale_ticket": world.canon(r["scale_ticket"]),
                "bin": world.canon(r["bin"]),
                "move_id": r["move_id"],
                "logged_at": logged,
                "quantity_kg": moves[0]["quantity_kg"],
            }
        )
    found.sort(key=lambda x: (x["logged_at"], x["scale_ticket"]))
    return found


def hopper_tickets_for_dispatch(world: World, dispatch: str) -> list[str]:
    named: set[str] = set()
    for r in rows(world.conn, "SELECT move_id, work_order, scale_ticket FROM hopper_names_ticket"):
        if world.matches(r["work_order"], dispatch):
            named.add(world.canon(r["scale_ticket"]))
    return sorted(named)


def established_shipment_for_dispatch(world: World, dispatch: str) -> dict | None:
    for r in rows(world.conn, "SELECT dispatch_ref, manifest_no, mill_receipt, output_batch FROM established_shipment"):
        if world.matches(r["dispatch_ref"], dispatch):
            return {
                "dispatch_ref": world.canon(r["dispatch_ref"]),
                "manifest_no": r["manifest_no"],
                "mill_receipt": r["mill_receipt"],
                "output_batch": r["output_batch"] or None,
            }
    return None


def outbound_link(world: World, dispatch: str) -> dict | None:
    for r in rows(world.conn, "SELECT dispatch_ref, manifest_no, link_basis FROM outbound_same_movement"):
        if world.matches(r["dispatch_ref"], dispatch):
            return {
                "dispatch_ref": world.canon(r["dispatch_ref"]),
                "manifest_no": r["manifest_no"],
                "link_basis": r["link_basis"],
            }
    return None


def inbound_link_for_manifest(world: World, manifest_no: str) -> dict | None:
    for r in rows(world.conn, "SELECT manifest_no, mill_receipt, link_basis FROM inbound_same_movement WHERE manifest_no = ?", (manifest_no,)):
        return dict(r)
    return None


def mill_receipt_row(world: World, local_receipt: str) -> dict | None:
    for r in rows(
        world.conn,
        "SELECT local_receipt, mill_code, received_at, dock, bill_reference, origin_label, received_kg, silo, commodity FROM mill_receipt",
    ):
        if world.matches(r["local_receipt"], local_receipt):
            mill_site = world.canon(r["mill_code"])
            return {
                "local_receipt": r["local_receipt"],
                "mill_code": r["mill_code"],
                "mill_site": mill_site,
                "received_at": r["received_at"],
                "dock": r["dock"],
                "bill_reference": r["bill_reference"],
                "origin_label": r["origin_label"],
                "origin_dispatch": world.canon(r["origin_label"]),
                "received_kg": r["received_kg"],
                "silo": r["silo"],
                "commodity": r["commodity"],
            }
    return None


def mill_process_for_receipt(world: World, local_receipt: str) -> dict | None:
    for r in rows(world.conn, "SELECT run_no, started_at, input_receipt, output_batch, output_name FROM mill_process"):
        if world.matches(r["input_receipt"], local_receipt):
            return dict(r)
    return None


def shipment_contributors(world: World, dispatch: str) -> dict:
    """Classify inbound tickets relative to a dispatch without guessing allocations."""
    named = hopper_tickets_for_dispatch(world, dispatch)
    loadout = loadout_for_dispatch(world, dispatch)
    candidates = []
    if loadout and loadout["loaded_at"]:
        candidates = [t["scale_ticket"] for t in tickets_into_bin_before(world, loadout["bin"], loadout["loaded_at"])]
    unresolved = unresolved_for(world, dispatch)
    allocation_unresolved = any(
        any(token in u["requirement_id"] for token in ("composition", "quantity_split", "material_identity"))
        for u in unresolved
    ) or (not named and len(set(candidates)) != 1)
    # Hopper-named tickets are established as contributing identities; quantity shares may still be unresolved.
    established = list(named)
    return {
        "established_contributing_identities": established,
        "named_on_hopper": named,
        "candidate_identities_in_source_bin": sorted(set(candidates)),
        "source_allocation_unresolved": allocation_unresolved,
        "unresolved": unresolved,
        "loadout": loadout,
    }


def identifier_canonical(world: World, params: dict) -> dict:
    value = params["identifier"]
    can = world.canon(value)
    kinds = sorted(
        {
            r["kind"]
            for r in rows(world.conn, "SELECT form, canonical, kind FROM identifier_alias")
            if r["form"] == value or r["canonical"] == can or r["form"] == can
        }
    )
    return {
        "identifier": value,
        "canonical": can,
        "forms": sorted(world.forms(value)),
        "kinds": kinds,
        "known": value in world.form_to_canonical or can in world.canonical_forms or any(
            world.matches(r["scale_ticket"], value)
            for r in rows(world.conn, "SELECT scale_ticket FROM intake_receipt")
        ),
    }


def unresolved_failures(world: World, params: dict) -> dict:
    identity = params.get("identity")
    if identity:
        items = unresolved_for(world, identity)
    else:
        items = []
        for r in rows(
            world.conn,
            "SELECT requirement_id, affected_identity, failure_kind, relation_name, subject_json FROM purpose_requirement_failure",
        ):
            subject = json.loads(r["subject_json"])
            items.append(
                {
                    "requirement_id": r["requirement_id"],
                    "affected_identity": r["affected_identity"],
                    "failure_kind": r["failure_kind"],
                    "relation_name": r["relation_name"],
                    "reason": subject.get("reason"),
                    "subject": subject,
                }
            )
        items.sort(key=lambda x: (x["requirement_id"], x["affected_identity"]))
    return {"identity": identity, "failures": items}


def bin_tickets_before(world: World, params: dict) -> dict:
    bin_id = world.canon(params["bin"])
    when = params["timestamp"]
    tickets = tickets_into_bin_before(world, bin_id, when)
    return {
        "bin": bin_id,
        "timestamp": when,
        "tickets": tickets,
        "ticket_ids": [t["scale_ticket"] for t in tickets],
    }


def shipment_source_status(world: World, params: dict) -> dict:
    dispatch = world.canon(params["dispatch"])
    contrib = shipment_contributors(world, dispatch)
    loadout = contrib["loadout"]
    outbound = outbound_link(world, dispatch)
    source_established = loadout is not None
    return {
        "dispatch": dispatch,
        "source_location": {
            "established": source_established,
            "bin": None if loadout is None else loadout["bin"],
            "bin_label": None if loadout is None else loadout["bin_label"],
            "site": SITE_PRAIRIE_GATE if source_established else None,
            "loadout_id": None if loadout is None else loadout["loadout_id"],
            "loaded_at": None if loadout is None else loadout["loaded_at"],
            "quantity_kg": None if loadout is None else loadout["quantity_kg"],
        },
        "established_contributing_identities": contrib["established_contributing_identities"],
        "named_on_hopper": contrib["named_on_hopper"],
        "candidate_identities_in_source_bin": contrib["candidate_identities_in_source_bin"],
        "source_allocation_unresolved": contrib["source_allocation_unresolved"],
        "outbound_manifest": outbound,
        "unresolved": contrib["unresolved"],
    }


def processor_receipt_provenance(world: World, params: dict) -> dict:
    receipt_id = params["processor_receipt"]
    receipt = mill_receipt_row(world, receipt_id)
    process = mill_process_for_receipt(world, receipt_id)
    inbound = None
    outbound = None
    dispatch = None
    if receipt:
        for r in rows(world.conn, "SELECT manifest_no, mill_receipt, link_basis FROM inbound_same_movement"):
            if world.matches(r["mill_receipt"], receipt_id):
                inbound = dict(r)
                break
        if inbound:
            for r in rows(world.conn, "SELECT dispatch_ref, manifest_no, link_basis FROM outbound_same_movement"):
                if r["manifest_no"] == inbound["manifest_no"]:
                    outbound = {
                        "dispatch_ref": world.canon(r["dispatch_ref"]),
                        "manifest_no": r["manifest_no"],
                        "link_basis": r["link_basis"],
                    }
                    dispatch = outbound["dispatch_ref"]
                    break
        if dispatch is None and receipt.get("origin_dispatch"):
            dispatch = receipt["origin_dispatch"]
    established = established_shipment_for_dispatch(world, dispatch) if dispatch else None
    upstream = shipment_contributors(world, dispatch) if dispatch else None
    unresolved = unresolved_for(world, receipt_id)
    if dispatch:
        for u in unresolved_for(world, dispatch):
            if u not in unresolved:
                unresolved.append(u)
        unresolved.sort(key=lambda x: x["requirement_id"])
    process_unresolved = process is None
    mill_unresolved = receipt is None
    return {
        "processor_receipt": receipt_id,
        "mill_receipt_established": receipt is not None,
        "mill_receipt": receipt,
        "established_path": None
        if established is None
        else {
            "dispatch_ref": established["dispatch_ref"],
            "manifest_no": established["manifest_no"],
            "mill_receipt": established["mill_receipt"],
            "outbound_link_basis": None if outbound is None else outbound["link_basis"],
            "inbound_link_basis": None if inbound is None else inbound["link_basis"],
        },
        "processing": None
        if process is None
        else {
            "established": True,
            "run_no": process["run_no"],
            "started_at": process["started_at"],
            "output_batch": process["output_batch"],
            "output_name": process["output_name"],
        },
        "processing_established": process is not None,
        "upstream_source": None
        if upstream is None
        else {
            "dispatch": dispatch,
            "source_bin": None if upstream["loadout"] is None else upstream["loadout"]["bin"],
            "established_contributing_identities": upstream["established_contributing_identities"],
            "named_on_hopper": upstream["named_on_hopper"],
            "candidate_identities_in_source_bin": upstream["candidate_identities_in_source_bin"],
            "source_allocation_unresolved": upstream["source_allocation_unresolved"],
        },
        "unresolved": unresolved,
        "unresolved_links": {
            "mill_receipt_missing": mill_unresolved,
            "processing_run_missing": process_unresolved,
            "upstream_ticket_allocation": False if upstream is None else upstream["source_allocation_unresolved"],
        },
    }


def covering_ownership(world: World, material: str, timestamp: str) -> dict | None:
    when = parse_dt(timestamp)
    covering = []
    for r in rows(
        world.conn,
        """SELECT record_no, record_type, scope_ref, effective_start, effective_end,
                  from_party, to_party, owner_after, holder_after, basis
           FROM ownership_event""",
    ):
        if not world.matches(r["scope_ref"], material):
            continue
        start = parse_dt(r["effective_start"])
        end = parse_dt(r["effective_end"])
        if start is not None and when < start:
            continue
        if end is not None and when >= end:
            continue
        covering.append(dict(r))
    covering.sort(key=lambda r: r["effective_start"])
    if not covering:
        return None
    chosen = covering[-1]
    chosen["scope_ref_canonical"] = world.canon(chosen["scope_ref"])
    return chosen


def intake_owner(world: World, material: str) -> dict | None:
    for r in rows(
        world.conn,
        "SELECT receipt_no, scale_ticket, arrived_at, owner_at_intake, grower_name FROM intake_receipt",
    ):
        if world.matches(r["scale_ticket"], material):
            return dict(r)
    return None


def custody_owner_at(world: World, params: dict) -> dict:
    material = world.canon(params["material"])
    timestamp = params["timestamp"]
    covering = covering_ownership(world, material, timestamp)
    intake = intake_owner(world, material)
    recording = unresolved_for(world, "ownership_records.csv")
    owner = None if covering is None else (covering["owner_after"] or None)
    custodian = None if covering is None else (covering["holder_after"] or None)
    return {
        "material": material,
        "timestamp": timestamp,
        "recorded_owner": owner,
        "recorded_custodian": custodian,
        "covering_event": None
        if covering is None
        else {
            "record_no": covering["record_no"],
            "record_type": covering["record_type"],
            "scope_ref": covering["scope_ref"],
            "effective_start": covering["effective_start"],
            "effective_end": covering["effective_end"] or None,
            "basis": covering["basis"],
            "from_party": covering["from_party"],
            "to_party": covering["to_party"],
        },
        "owner_recorded": covering is not None and bool(covering["owner_after"]),
        "custodian_recorded": covering is not None and bool(covering["holder_after"]),
        "intake_owner_at_intake": None if intake is None else intake["owner_at_intake"],
        "unresolved": recording + (unresolved_for(world, material)),
    }


def lab_sample(world: World, sample: str) -> dict | None:
    for r in rows(
        world.conn,
        """SELECT sample_no, tested_at, lab_ticket, local_lot, material_hint, test_name, result, unit, comment
           FROM lab_test""",
    ):
        if r["sample_no"] == sample:
            return dict(r)
    return None


def identities_from_sample(world: World, sample_row: dict) -> tuple[list[str], bool]:
    if unresolved_for(world, sample_row["sample_no"]):
        return [], True
    labels = split_lot_label(sample_row["local_lot"])
    identities = [world.canon(label) for label in labels]
    unresolved_identity = not identities
    return sorted(set(identities)), unresolved_identity


def loadouts_from_bin_after(world: World, bin_id: str, when: str) -> list[dict]:
    cutoff = parse_dt(when)
    found = []
    for r in rows(world.conn, "SELECT dispatch_ref, bin, loadout_id FROM loadout_from_bin"):
        if not world.matches(r["bin"], bin_id):
            continue
        loadout = loadout_for_dispatch(world, r["dispatch_ref"])
        if loadout is None or loadout["loaded_at"] is None:
            continue
        if parse_dt(loadout["loaded_at"]) < cutoff:
            continue
        found.append(loadout)
    found.sort(key=lambda x: x["loaded_at"])
    return found


def mill_ids_in_text(world: World, text: str) -> list[str]:
    found = []
    for m in rows(world.conn, "SELECT local_receipt FROM mill_receipt"):
        if m["local_receipt"] in (text or ""):
            found.append(m["local_receipt"])
    return sorted(set(found))


def inspect_mill_downstream(world: World, mill_id: str) -> tuple[list[dict], list[dict], list[dict]]:
    receipts = [{"processor_receipt": mill_id, "basis": "lab material_hint names this mill receipt"}]
    outputs = []
    unresolved = []
    process = mill_process_for_receipt(world, mill_id)
    if process:
        outputs.append(
            {
                "output_batch": process["output_batch"],
                "output_name": process["output_name"],
                "run_no": process["run_no"],
                "processor_receipt": mill_id,
            }
        )
    else:
        unresolved.append({"kind": "processing_run_missing", "processor_receipt": mill_id})
    return receipts, outputs, unresolved


def inspect_ticket_loadouts(world: World, ticket: str, not_before: str) -> tuple[list[dict], list[dict], list[dict]]:
    established_shipments: list[dict] = []
    possible_shipments: list[dict] = []
    unresolved_scope: list[dict] = []
    into = [
        t
        for t in rows(world.conn, "SELECT scale_ticket, bin, move_id FROM ticket_into_bin")
        if world.matches(t["scale_ticket"], ticket)
    ]
    if not into:
        unresolved_scope.append({"kind": "ticket_not_placed_in_bin", "sampled_ticket": ticket})
        return established_shipments, possible_shipments, unresolved_scope
    bin_id = world.canon(into[0]["bin"])
    for loadout in loadouts_from_bin_after(world, bin_id, not_before):
        named = hopper_tickets_for_dispatch(world, loadout["dispatch_ref"])
        contrib = shipment_contributors(world, loadout["dispatch_ref"])
        record = {
            "dispatch": loadout["dispatch_ref"],
            "bin": loadout["bin"],
            "loaded_at": loadout["loaded_at"],
            "named_on_hopper": named,
            "sampled_ticket": ticket,
        }
        if ticket in named and not contrib["source_allocation_unresolved"]:
            record["status"] = "established"
            established_shipments.append(record)
        elif ticket in named:
            record["status"] = "named_unallocated"
            possible_shipments.append(record)
            unresolved_scope.append(
                {
                    "kind": "named_without_quantity_allocation",
                    "dispatch": loadout["dispatch_ref"],
                    "sampled_ticket": ticket,
                    "named_on_hopper": named,
                }
            )
        elif named:
            continue
        else:
            record["status"] = "bin_occupant_unallocated"
            possible_shipments.append(record)
            unresolved_scope.append(
                {
                    "kind": "source_allocation_unresolved",
                    "dispatch": loadout["dispatch_ref"],
                    "sampled_ticket": ticket,
                    "candidate_identities_in_source_bin": contrib["candidate_identities_in_source_bin"],
                }
            )
    return established_shipments, possible_shipments, unresolved_scope


def downstream_from_dispatch(world: World, dispatch: str, established: bool) -> tuple[list[dict], list[dict], list[dict]]:
    receipts: list[dict] = []
    outputs: list[dict] = []
    unresolved: list[dict] = []
    mill_id = None
    process = None
    est = established_shipment_for_dispatch(world, dispatch)
    if est:
        mill_id = est["mill_receipt"]
        process = mill_process_for_receipt(world, mill_id)
    else:
        outbound = outbound_link(world, dispatch)
        if outbound:
            inbound = inbound_link_for_manifest(world, outbound["manifest_no"])
            if inbound:
                mill_id = inbound["mill_receipt"]
                process = mill_process_for_receipt(world, mill_id)
    if mill_id:
        receipts.append({"processor_receipt": mill_id, "dispatch": dispatch})
    elif not established:
        unresolved.append({"kind": "processor_receipt_not_in_extracts", "dispatch": dispatch})
    if process:
        outputs.append(
            {
                "output_batch": process["output_batch"],
                "output_name": process["output_name"],
                "run_no": process["run_no"],
                "processor_receipt": process["input_receipt"],
                "dispatch": dispatch,
            }
        )
    elif mill_id and not established:
        unresolved.append({"kind": "processing_run_missing", "processor_receipt": mill_id, "dispatch": dispatch})
    return receipts, outputs, unresolved


def inspection_downstream_scope(world: World, params: dict) -> dict:
    sample = params["sample"]
    lab = lab_sample(world, sample)
    if lab is None:
        return {
            "sample": sample,
            "sample_found": False,
            "established_affected": {"shipments": [], "processor_receipts": [], "processed_outputs": []},
            "unresolved_scope": [{"kind": "unknown_sample", "detail": "no lab_test row for sample"}],
        }
    identities, identity_unresolved = identities_from_sample(world, lab)
    unresolved_scope: list[dict] = []
    if identity_unresolved:
        unresolved_scope.append(
            {
                "kind": "sampled_material_identity",
                "sample": sample,
                "local_lot": lab["local_lot"],
                "detail": lab["comment"],
            }
        )

    mill_hits = mill_ids_in_text(world, lab["material_hint"] or "")
    established_shipments: list[dict] = []
    possible_shipments: list[dict] = []
    established_receipts: list[dict] = []
    established_outputs: list[dict] = []
    possible_receipts: list[dict] = []
    possible_outputs: list[dict] = []

    if mill_hits:
        for mill_id in mill_hits:
            recs, outs, unres = inspect_mill_downstream(world, mill_id)
            established_receipts.extend(recs)
            established_outputs.extend(outs)
            unresolved_scope.extend(unres)
    else:
        for ticket in identities:
            est_s, pos_s, unres = inspect_ticket_loadouts(world, ticket, lab["tested_at"])
            established_shipments.extend(est_s)
            possible_shipments.extend(pos_s)
            unresolved_scope.extend(unres)
        seen = set()
        for rec in established_shipments:
            d = rec["dispatch"]
            if d in seen:
                continue
            seen.add(d)
            recs, outs, unres = downstream_from_dispatch(world, d, True)
            established_receipts.extend(recs)
            established_outputs.extend(outs)
            unresolved_scope.extend(unres)
        seen_pos = set()
        for rec in possible_shipments:
            d = rec["dispatch"]
            if d in seen_pos:
                continue
            seen_pos.add(d)
            recs, outs, unres = downstream_from_dispatch(world, d, False)
            possible_receipts.extend(recs)
            possible_outputs.extend(outs)
            unresolved_scope.extend(unres)

    uniq = []
    seen_u = set()
    for u in unresolved_scope:
        key = json.dumps(u, sort_keys=True)
        if key not in seen_u:
            seen_u.add(key)
            uniq.append(u)
    for ticket in identities:
        uniq.extend(unresolved_for(world, ticket))
    uniq.extend(unresolved_for(world, sample))

    return {
        "sample": sample,
        "sample_found": True,
        "tested_at": lab["tested_at"],
        "local_lot": lab["local_lot"],
        "material_hint": lab["material_hint"],
        "sampled_identities": identities,
        "sampled_identity_unresolved": identity_unresolved,
        "established_affected": {
            "shipments": established_shipments,
            "processor_receipts": established_receipts,
            "processed_outputs": established_outputs,
        },
        "possible_unallocated": {
            "shipments": possible_shipments,
            "processor_receipts": possible_receipts,
            "processed_outputs": possible_outputs,
        },
        "unresolved_scope": uniq,
    }


COMPUTATIONS = {
    "identifier_canonical": identifier_canonical,
    "unresolved_failures": unresolved_failures,
    "bin_tickets_before": bin_tickets_before,
    "shipment_source_status": shipment_source_status,
    "processor_receipt_provenance": processor_receipt_provenance,
    "custody_owner_at": custody_owner_at,
    "inspection_downstream_scope": inspection_downstream_scope,
}


def run_computation(name: str, params: dict) -> dict:
    if name not in COMPUTATIONS:
        raise KeyError(name)
    conn = connect_world()
    try:
        world = World(conn)
        result = COMPUTATIONS[name](world, params)
        return {
            "computation": name,
            "parameters": params,
            "world": {
                "sqlite": "../world/world.sqlite",
                "hash": WORLD_HASH,
                "sqlite_sha256": WORLD_SQLITE_SHA256,
            },
            "result": result,
        }
    finally:
        conn.close()

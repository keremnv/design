from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from . import db as world_db


def rows(conn, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(sql, params)]


def parse_ts(value: str) -> datetime:
    if not value:
        raise ValueError("empty timestamp")
    return datetime.fromisoformat(value)


def ts_covers(start: str, end: str, instant: datetime) -> bool:
    start_dt = parse_ts(start)
    if instant < start_dt:
        return False
    if not end:
        return True
    return instant < parse_ts(end)


def token_matches(a: str, b: str) -> bool:
    if a == b:
        return True
    return a.casefold() == b.casefold()


def resolve_referents(conn, token: str) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def add(entity_id: str, via: str, matched: str) -> None:
        rec = found.setdefault(
            entity_id,
            {
                "entity_id": entity_id,
                "label": None,
                "matches": [],
            },
        )
        rec["matches"].append({"via": via, "token": matched})

    for r in rows(
        conn,
        "SELECT entity_id, token, system FROM known_as WHERE token = ? COLLATE NOCASE",
        (token,),
    ):
        add(r["entity_id"], f"known_as:{r['system']}", r["token"])

    for r in rows(
        conn,
        "SELECT id, label FROM _world_referents WHERE id = ? OR label = ? COLLATE NOCASE OR id LIKE ?",
        (token, token, f"%:{token}"),
    ):
        add(r["id"], "referent", r["label"] or r["id"])

    for r in rows(
        conn,
        "SELECT ticket_id, receipt_no FROM elevator_intake WHERE receipt_no = ? COLLATE NOCASE",
        (token,),
    ):
        add(r["ticket_id"], "elevator_intake.receipt_no", r["receipt_no"])

    for r in rows(
        conn,
        "SELECT loadout_id, dispatch_ref, movement_id FROM elevator_loadout WHERE dispatch_ref = ? COLLATE NOCASE",
        (token,),
    ):
        add(r["movement_id"], "elevator_loadout.dispatch_ref", r["dispatch_ref"])
        add(r["loadout_id"], "elevator_loadout.loadout_id", r["dispatch_ref"])

    for r in rows(
        conn,
        "SELECT manifest_id, movement_id, cargo_mark, bill_of_lading FROM carrier_departure "
        "WHERE cargo_mark = ? COLLATE NOCASE OR bill_of_lading = ? COLLATE NOCASE",
        (token, token),
    ):
        add(r["movement_id"], "carrier_departure", token)
        add(r["manifest_id"], "carrier_departure.manifest", token)

    labels = {
        r["id"]: r["label"]
        for r in rows(conn, "SELECT id, label FROM _world_referents")
    }
    out = []
    for entity_id, rec in sorted(found.items()):
        rec["label"] = labels.get(entity_id)
        rec["kind"] = entity_id.split(":", 1)[0]
        out.append(rec)
    return out


def prefer_kind(matches: list[dict[str, Any]], kinds: tuple[str, ...]) -> dict[str, Any] | None:
    for kind in kinds:
        for m in matches:
            if m["kind"] == kind:
                return m
    return matches[0] if matches else None


def label_of(conn, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    r = conn.execute("SELECT label FROM _world_referents WHERE id = ?", (entity_id,)).fetchone()
    return r["label"] if r else None


def location_of(conn, place_id: str) -> dict[str, Any] | None:
    r = conn.execute(
        "SELECT place_id, site_id, kind, local_name FROM location WHERE place_id = ? ORDER BY local_name LIMIT 1",
        (place_id,),
    ).fetchone()
    if not r:
        return {"place_id": place_id, "label": label_of(conn, place_id)}
    return {
        "place_id": r["place_id"],
        "site_id": r["site_id"],
        "kind": r["kind"],
        "local_name": r["local_name"],
        "site_label": label_of(conn, r["site_id"]),
        "label": label_of(conn, place_id),
    }


def aliases(conn, entity_id: str) -> list[dict[str, str]]:
    return rows(
        conn,
        "SELECT token, system FROM known_as WHERE entity_id = ? ORDER BY system, token",
        (entity_id,),
    )


def movement_tokens(conn, movement_id: str) -> set[str]:
    tokens = {movement_id, movement_id.split(":", 1)[-1]}
    for a in aliases(conn, movement_id):
        tokens.add(a["token"])
    load = conn.execute(
        "SELECT dispatch_ref FROM elevator_loadout WHERE movement_id = ?",
        (movement_id,),
    ).fetchone()
    if load:
        tokens.add(load["dispatch_ref"])
    return {t for t in tokens if t}


def _subject_tokens(subject: Any) -> list[str]:
    tokens: list[str] = []
    if isinstance(subject, dict):
        for key, value in subject.items():
            if key == "reason":
                continue
            tokens.append(str(key))
            if isinstance(value, str):
                tokens.append(value)
            elif isinstance(value, list):
                tokens.extend(str(item) for item in value)
    elif isinstance(subject, str):
        tokens.append(subject)
    return tokens


def _identity_hit(needle: str, haystack: str) -> bool:
    if not needle or not haystack:
        return False
    if needle == haystack:
        return True
    if needle.casefold() == haystack.casefold():
        return True
    # Allow dispatch tokens to match requirement ids such as physical-ticket-allocation-PGE-OUT-5001.
    if len(needle) >= 4 and needle in haystack:
        if haystack.startswith(needle) or haystack.endswith(needle) or f"-{needle}" in haystack:
            return True
    return False


def unresolved_related(conn, needles: list[str]) -> list[dict[str, Any]]:
    cleaned = [n for n in needles if n]
    out = []
    seen = set()
    for r in rows(
        conn,
        "SELECT requirement_id, affected_identity, failure_kind, relation_name, subject_json, grounding_ref "
        "FROM purpose_requirement_failure ORDER BY requirement_id",
    ):
        subject = r["subject_json"]
        try:
            subject = json.loads(subject)
        except json.JSONDecodeError:
            pass
        fields = [
            r["requirement_id"],
            r["affected_identity"],
            *_subject_tokens(subject),
        ]
        if any(_identity_hit(n, field) for n in cleaned for field in fields):
            if r["requirement_id"] in seen:
                continue
            seen.add(r["requirement_id"])
            out.append(
                {
                    "requirement_id": r["requirement_id"],
                    "affected_identity": r["affected_identity"],
                    "failure_kind": r["failure_kind"],
                    "relation_name": r["relation_name"],
                    "subject": subject,
                    "grounding_ref": r["grounding_ref"],
                }
            )
    return out


def resolve_movement(conn, token: str) -> dict[str, Any] | None:
    matches = resolve_referents(conn, token)
    chosen = prefer_kind(matches, ("movement", "loadout", "manifest"))
    if not chosen:
        return None
    movement_id = chosen["entity_id"]
    if chosen["kind"] == "loadout":
        r = conn.execute(
            "SELECT movement_id FROM elevator_loadout WHERE loadout_id = ?",
            (movement_id,),
        ).fetchone()
        movement_id = r["movement_id"] if r else movement_id
    elif chosen["kind"] == "manifest":
        r = conn.execute(
            "SELECT movement_id FROM carrier_departure WHERE manifest_id = ?",
            (movement_id,),
        ).fetchone()
        movement_id = r["movement_id"] if r else movement_id
    elif chosen["kind"] != "movement":
        # fall back: if any movement match exists, use it
        alt = prefer_kind(matches, ("movement",))
        if alt:
            movement_id = alt["entity_id"]
        else:
            return None
    return _movement_bundle(conn, movement_id)


def _movement_bundle(conn, movement_id: str) -> dict[str, Any]:
    loadout = conn.execute(
        "SELECT loadout_id, movement_id, bin_id, truck_id, dispatch_ref, quantity_kg, spout, "
        "route_code, loaded_at, desk_comment FROM elevator_loadout WHERE movement_id = ?",
        (movement_id,),
    ).fetchone()
    carrier = conn.execute(
        "SELECT manifest_id, movement_id, carrier_id, vehicle_id, cargo_mark, bill_of_lading, "
        "consignee_code, consignee_name, pickup_site_id, weight_kg, departed_at, route_note "
        "FROM carrier_departure WHERE movement_id = ?",
        (movement_id,),
    ).fetchone()
    mill = conn.execute(
        "SELECT receipt_id, movement_id, site_id, dock, bill_reference, origin_label, "
        "received_kg, silo, commodity, received_at FROM mill_intake WHERE movement_id = ?",
        (movement_id,),
    ).fetchone()
    bundle = {
        "movement_id": movement_id,
        "label": label_of(conn, movement_id),
        "aliases": aliases(conn, movement_id),
        "loadout": dict(loadout) if loadout else None,
        "carrier_departure": dict(carrier) if carrier else None,
        "mill_intake": dict(mill) if mill else None,
    }
    if loadout:
        bundle["source_location"] = location_of(conn, loadout["bin_id"])
        bundle["truck_label"] = label_of(conn, loadout["truck_id"])
        bundle["loadout_label"] = label_of(conn, loadout["loadout_id"])
    if carrier:
        bundle["manifest_label"] = label_of(conn, carrier["manifest_id"])
        bundle["carrier_label"] = label_of(conn, carrier["carrier_id"])
        bundle["consignee_is_not_receipt"] = bool(
            conn.execute(
                "SELECT 1 FROM consignee_is_not_receipt WHERE manifest_id = ?",
                (carrier["manifest_id"],),
            ).fetchone()
        )
    return bundle


def named_tickets_for_movement(conn, movement_id: str) -> list[dict[str, Any]]:
    tokens = movement_tokens(conn, movement_id)
    transfers = rows(
        conn,
        "SELECT move_id, from_place_id, to_place_id, material_note, quantity_kg, work_order, logged_at "
        "FROM bin_transfer ORDER BY logged_at, move_id",
    )
    named = []
    seen = set()
    for tr in transfers:
        if tr["work_order"] not in tokens:
            continue
        links = rows(
            conn,
            "SELECT ticket_id, note_span FROM ticket_named_on_move WHERE move_id = ? ORDER BY ticket_id",
            (tr["move_id"],),
        )
        for link in links:
            key = (link["ticket_id"], tr["move_id"])
            if key in seen:
                continue
            seen.add(key)
            intake = conn.execute(
                "SELECT ticket_id, receipt_no, grower_recorded, commodity, net_kg, assigned_bin_id, "
                "owner_recorded, arrived_at FROM elevator_intake WHERE ticket_id = ?",
                (link["ticket_id"],),
            ).fetchone()
            named.append(
                {
                    "ticket_id": link["ticket_id"],
                    "ticket_label": label_of(conn, link["ticket_id"]),
                    "note_span": link["note_span"],
                    "move_id": tr["move_id"],
                    "work_order": tr["work_order"],
                    "material_note": tr["material_note"],
                    "quantity_kg_on_move": tr["quantity_kg"],
                    "named_not_quantity_allocation": True,
                    "intake": dict(intake) if intake else None,
                }
            )
    return named


def prior_bin_intakes(conn, bin_id: str, before: str) -> list[dict[str, Any]]:
    before_dt = parse_ts(before)
    out = []
    for r in rows(
        conn,
        "SELECT ticket_id, receipt_no, grower_recorded, commodity, net_kg, lane_id, assigned_bin_id, "
        "owner_recorded, arrived_at, grade_note FROM elevator_intake WHERE assigned_bin_id = ? "
        "ORDER BY arrived_at, ticket_id",
        (bin_id,),
    ):
        if parse_ts(r["arrived_at"]) < before_dt:
            rec = dict(r)
            rec["ticket_label"] = label_of(conn, r["ticket_id"])
            out.append(rec)
    return out


def commercial_scopes_for_movement(conn, bundle: dict[str, Any]) -> list[dict[str, Any]]:
    movement_id = bundle["movement_id"]
    needles = list(movement_tokens(conn, movement_id))
    if bundle.get("carrier_departure"):
        cd = bundle["carrier_departure"]
        needles.extend(
            [
                cd["manifest_id"],
                label_of(conn, cd["manifest_id"]) or "",
                cd["bill_of_lading"],
            ]
        )
    if bundle.get("mill_intake"):
        mi = bundle["mill_intake"]
        needles.extend(
            [
                mi["receipt_id"],
                label_of(conn, mi["receipt_id"]) or "",
                mi["bill_reference"],
            ]
        )
    needles = [n for n in needles if n]

    scoped_direct = rows(
        conn,
        "SELECT record_id, scoped_id, scope_kind FROM commercial_scope WHERE scoped_id = ? ORDER BY record_id",
        (movement_id,),
    )
    events = rows(
        conn,
        "SELECT record_id, record_type, scope_ref, effective_start, effective_end, from_party, to_party, "
        "owner_after, holder_after, basis, recorded_at FROM ownership_event ORDER BY recorded_at, record_id",
    )

    out = []
    seen = set()

    def add(event: dict[str, Any], reason: str) -> None:
        if event["record_id"] in seen:
            return
        seen.add(event["record_id"])
        scopes = rows(
            conn,
            "SELECT scoped_id, scope_kind FROM commercial_scope WHERE record_id = ? ORDER BY scoped_id",
            (event["record_id"],),
        )
        item = dict(event)
        item["commercial_scope"] = [
            {
                "scoped_id": s["scoped_id"],
                "scoped_label": label_of(conn, s["scoped_id"]),
                "scope_kind": s["scope_kind"],
            }
            for s in scopes
        ]
        item["reason"] = reason
        item["not_a_bin_allocation"] = True
        out.append(item)

    for s in scoped_direct:
        ev = conn.execute(
            "SELECT record_id, record_type, scope_ref, effective_start, effective_end, from_party, to_party, "
            "owner_after, holder_after, basis, recorded_at FROM ownership_event WHERE record_id = ?",
            (s["record_id"],),
        ).fetchone()
        if ev:
            add(dict(ev), "commercial_scope.scoped_id is this movement")

    for ev in events:
        basis = ev["basis"] or ""
        if any(n and n in basis for n in needles):
            add(ev, "ownership_event.basis names this movement/manifest/receipt")
    return out


def mill_process_for_receipt(conn, receipt_id: str) -> dict[str, Any] | None:
    r = conn.execute(
        "SELECT run_id, input_receipt_id, output_batch_id, output_name, started_at "
        "FROM mill_process WHERE input_receipt_id = ?",
        (receipt_id,),
    ).fetchone()
    if not r:
        return None
    return {
        "run_id": r["run_id"],
        "run_label": label_of(conn, r["run_id"]),
        "input_receipt_id": r["input_receipt_id"],
        "output_batch_id": r["output_batch_id"],
        "output_batch_label": label_of(conn, r["output_batch_id"]),
        "output_name": r["output_name"],
        "started_at": r["started_at"],
    }


def resolve_ticket(conn, token: str) -> dict[str, Any] | None:
    matches = resolve_referents(conn, token)
    chosen = prefer_kind(matches, ("ticket",))
    if not chosen:
        return None
    intake = conn.execute(
        "SELECT ticket_id, receipt_no, site_id, grower_recorded, commodity, net_kg, lane_id, "
        "assigned_bin_id, owner_recorded, arrived_at, grade_note FROM elevator_intake WHERE ticket_id = ?",
        (chosen["entity_id"],),
    ).fetchone()
    return {
        "ticket_id": chosen["entity_id"],
        "label": chosen["label"],
        "aliases": aliases(conn, chosen["entity_id"]),
        "intake": dict(intake) if intake else None,
        "assigned_bin": location_of(conn, intake["assigned_bin_id"]) if intake else None,
    }


def covering_ownership(conn, material_token: str, timestamp: str) -> dict[str, Any]:
    ticket = resolve_ticket(conn, material_token)
    instant = parse_ts(timestamp)
    events = rows(
        conn,
        "SELECT record_id, record_type, scope_ref, effective_start, effective_end, from_party, to_party, "
        "owner_after, holder_after, basis, recorded_at FROM ownership_event ORDER BY effective_start, record_id",
    )
    covering = []
    for ev in events:
        scoped = rows(
            conn,
            "SELECT scoped_id, scope_kind FROM commercial_scope WHERE record_id = ?",
            (ev["record_id"],),
        )
        hit = token_matches(ev["scope_ref"], material_token)
        if ticket:
            hit = hit or any(s["scoped_id"] == ticket["ticket_id"] for s in scoped)
            hit = hit or token_matches(ev["scope_ref"], ticket["label"] or "")
        if not hit:
            continue
        if ts_covers(ev["effective_start"], ev["effective_end"], instant):
            item = dict(ev)
            item["commercial_scope"] = [
                {
                    "scoped_id": s["scoped_id"],
                    "scoped_label": label_of(conn, s["scoped_id"]),
                    "scope_kind": s["scope_kind"],
                }
                for s in scoped
            ]
            covering.append(item)

    owner_event = None
    holder_event = None
    for ev in covering:
        if ev["owner_after"]:
            if owner_event is None or ev["effective_start"] >= owner_event["effective_start"]:
                owner_event = ev
        if ev["holder_after"]:
            if holder_event is None or ev["effective_start"] >= holder_event["effective_start"]:
                holder_event = ev

    needles = [material_token]
    if ticket:
        needles.extend([ticket["ticket_id"], ticket["label"] or ""])
        needles.extend(a["token"] for a in ticket["aliases"])
    return {
        "material_token": material_token,
        "ticket": ticket,
        "timestamp": timestamp,
        "covering_events": covering,
        "owner": {
            "party": owner_event["owner_after"] if owner_event else None,
            "from_event": owner_event["record_id"] if owner_event else None,
            "established": bool(owner_event and owner_event["owner_after"]),
        },
        "custodian": {
            "party": holder_event["holder_after"] if holder_event else None,
            "from_event": holder_event["record_id"] if holder_event else None,
            "established": bool(holder_event and holder_event["holder_after"]),
        },
        "unresolved": unresolved_related(conn, needles),
    }


def sample_record(conn, token: str) -> dict[str, Any] | None:
    matches = resolve_referents(conn, token)
    chosen = prefer_kind(matches, ("sample",))
    if not chosen:
        labs = rows(
            conn,
            "SELECT sample_id, tested_at, lab_ticket, local_lot, material_hint, test_name, result, unit, comment "
            "FROM lab_result WHERE sample_id LIKE ? OR lab_ticket = ? COLLATE NOCASE",
            (f"%{token}", token),
        )
        if not labs:
            return None
        sample_id = labs[0]["sample_id"]
    else:
        sample_id = chosen["entity_id"]
        labs = rows(
            conn,
            "SELECT sample_id, tested_at, lab_ticket, local_lot, material_hint, test_name, result, unit, comment "
            "FROM lab_result WHERE sample_id = ? ORDER BY tested_at, test_name",
            (sample_id,),
        )
    return {
        "sample_id": sample_id,
        "label": label_of(conn, sample_id),
        "results": labs,
    }


def established_ticket_for_sample(conn, sample: dict[str, Any]) -> dict[str, Any] | None:
    sample_label = sample["label"] or sample["sample_id"]
    failures = unresolved_related(conn, [sample["sample_id"], sample_label])
    lab_unresolved = [
        f
        for f in failures
        if f["relation_name"] == "lab_result"
        or str(f["requirement_id"]).startswith("lab-sample-")
    ]
    if lab_unresolved:
        return None

    candidates: dict[str, dict[str, Any]] = {}
    for lab in sample["results"]:
        for token in filter(None, [lab.get("local_lot"), lab.get("material_hint")]):
            for part in [token] + [p.strip() for p in token.replace("/", " ").replace("?", " ").split()]:
                if not part or part.lower() in {"receipt", "ticket", "south", "house", "cargo", "note", "route", "packet"}:
                    continue
                ticket = resolve_ticket(conn, part)
                if ticket:
                    candidates[ticket["ticket_id"]] = ticket
    if len(candidates) == 1:
        ticket = next(iter(candidates.values()))
        ticket["established"] = True
        return ticket
    return None


def shipment_source_status(conn, dispatch: str) -> dict[str, Any]:
    bundle = resolve_movement(conn, dispatch)
    if not bundle:
        return {
            "computation": "shipment_source_status",
            "world_binding": world_db.world_binding(conn),
            "query": {"dispatch": dispatch},
            "movement": None,
            "source_location": None,
            "established_contributing_identities": [],
            "bin_occupants_before_loadout": [],
            "commercial_scopes": [],
            "source_allocation_unresolved": None,
            "unresolved": unresolved_related(conn, [dispatch]),
            "error": "dispatch_not_found",
        }

    named = named_tickets_for_movement(conn, bundle["movement_id"])
    occupants = []
    if bundle.get("loadout"):
        occupants = prior_bin_intakes(conn, bundle["loadout"]["bin_id"], bundle["loadout"]["loaded_at"])
    commercial = commercial_scopes_for_movement(conn, bundle)
    needles = list(movement_tokens(conn, bundle["movement_id"]))
    needles.extend(
        [
            bundle["label"] or "",
            (bundle.get("loadout") or {}).get("dispatch_ref") or "",
            (bundle.get("manifest_label") or ""),
        ]
    )
    unresolved = unresolved_related(conn, needles)
    allocation_unresolved = any(
        "physical-ticket-allocation" in f["requirement_id"] for f in unresolved
    )
    # Named hopper tickets establish identity association, not quantity split.
    established = [
        {
            "ticket_id": n["ticket_id"],
            "ticket_label": n["ticket_label"],
            "basis": "ticket_named_on_move",
            "move_id": n["move_id"],
            "note_span": n["note_span"],
            "quantity_allocation_established": False,
        }
        for n in named
    ]
    return {
        "computation": "shipment_source_status",
        "world_binding": world_db.world_binding(conn),
        "query": {"dispatch": dispatch},
        "movement": {
            "movement_id": bundle["movement_id"],
            "label": bundle["label"],
            "loadout": bundle.get("loadout"),
            "carrier_departure": bundle.get("carrier_departure"),
            "mill_intake": bundle.get("mill_intake"),
            "consignee_is_not_receipt": bundle.get("consignee_is_not_receipt"),
        },
        "source_location": {
            "established": bundle.get("source_location") is not None,
            "location": bundle.get("source_location"),
        },
        "established_contributing_identities": established,
        "bin_occupants_before_loadout": occupants,
        "commercial_scopes": commercial,
        "source_allocation_unresolved": allocation_unresolved or (not established and bool(occupants)),
        "unresolved": unresolved,
    }


def processor_receipt_provenance(conn, processor_receipt: str) -> dict[str, Any]:
    matches = resolve_referents(conn, processor_receipt)
    chosen = prefer_kind(matches, ("mill-receipt",))
    if not chosen:
        return {
            "computation": "processor_receipt_provenance",
            "world_binding": world_db.world_binding(conn),
            "query": {"processor_receipt": processor_receipt},
            "receipt": None,
            "upstream": None,
            "processing": None,
            "unresolved": unresolved_related(conn, [processor_receipt]),
            "error": "processor_receipt_not_found",
        }
    intake = conn.execute(
        "SELECT receipt_id, movement_id, site_id, dock, bill_reference, origin_label, "
        "received_kg, silo, commodity, received_at FROM mill_intake WHERE receipt_id = ?",
        (chosen["entity_id"],),
    ).fetchone()
    if not intake:
        return {
            "computation": "processor_receipt_provenance",
            "world_binding": world_db.world_binding(conn),
            "query": {"processor_receipt": processor_receipt},
            "receipt": {"receipt_id": chosen["entity_id"], "label": chosen["label"]},
            "upstream": None,
            "processing": mill_process_for_receipt(conn, chosen["entity_id"]),
            "unresolved": unresolved_related(conn, [processor_receipt, chosen["entity_id"]]),
            "error": "mill_intake_not_found",
        }
    bundle = _movement_bundle(conn, intake["movement_id"])
    named = named_tickets_for_movement(conn, intake["movement_id"])
    commercial = commercial_scopes_for_movement(conn, bundle)
    process = mill_process_for_receipt(conn, chosen["entity_id"])
    needles = list(movement_tokens(conn, intake["movement_id"]))
    needles.extend(
        [
            chosen["entity_id"],
            chosen["label"] or "",
            processor_receipt,
            intake["bill_reference"],
        ]
    )
    unresolved = unresolved_related(conn, needles)
    commercial_tickets = []
    seen = set()
    for ev in commercial:
        for s in ev["commercial_scope"]:
            if s["scope_kind"] == "ticket" and s["scoped_id"] not in seen:
                seen.add(s["scoped_id"])
                commercial_tickets.append(s)
    return {
        "computation": "processor_receipt_provenance",
        "world_binding": world_db.world_binding(conn),
        "query": {"processor_receipt": processor_receipt},
        "receipt": {
            **dict(intake),
            "label": chosen["label"],
            "site_label": label_of(conn, intake["site_id"]),
        },
        "upstream": {
            "movement_id": bundle["movement_id"],
            "dispatch_label": bundle["label"],
            "source_location": bundle.get("source_location"),
            "loadout": bundle.get("loadout"),
            "carrier_departure": bundle.get("carrier_departure"),
            "established_named_tickets": named,
            "commercial_ticket_scopes": commercial_tickets,
            "commercial_scopes": commercial,
        },
        "processing": process,
        "unresolved": unresolved,
    }


def custody_owner_at(conn, material: str, timestamp: str) -> dict[str, Any]:
    covered = covering_ownership(conn, material, timestamp)
    return {
        "computation": "custody_owner_at",
        "world_binding": world_db.world_binding(conn),
        "query": {"material": material, "timestamp": timestamp},
        "material": covered["ticket"],
        "owner": covered["owner"],
        "custodian": covered["custodian"],
        "covering_events": covered["covering_events"],
        "unresolved": covered["unresolved"],
    }


def inspection_downstream_scope(conn, sample_token: str) -> dict[str, Any]:
    sample = sample_record(conn, sample_token)
    if not sample:
        return {
            "computation": "inspection_downstream_scope",
            "world_binding": world_db.world_binding(conn),
            "query": {"sample": sample_token},
            "sample": None,
            "established_source_ticket": None,
            "established_downstream": {
                "shipments": [],
                "processor_receipts": [],
                "processed_outputs": [],
            },
            "unresolved": unresolved_related(conn, [sample_token]),
            "error": "sample_not_found",
        }

    ticket = established_ticket_for_sample(conn, sample)
    needles = [sample["sample_id"], sample["label"] or "", sample_token]
    for lab in sample["results"]:
        needles.extend([lab.get("local_lot") or "", lab.get("lab_ticket") or ""])

    shipments: dict[str, dict[str, Any]] = {}
    receipts: dict[str, dict[str, Any]] = {}
    outputs: dict[str, dict[str, Any]] = {}
    physical_candidates = []

    if ticket:
        needles.extend([ticket["ticket_id"], ticket["label"] or ""])
        # Commercial / custody downstream: ownership events scoped to this ticket
        # whose basis names a manifest, dispatch, or mill receipt after (or at) sample time.
        tested_at = min(parse_ts(r["tested_at"]) for r in sample["results"]) if sample["results"] else None
        events = rows(
            conn,
            "SELECT record_id, record_type, scope_ref, effective_start, effective_end, from_party, to_party, "
            "owner_after, holder_after, basis, recorded_at FROM ownership_event ORDER BY recorded_at, record_id",
        )
        for ev in events:
            scoped = rows(
                conn,
                "SELECT scoped_id, scope_kind FROM commercial_scope WHERE record_id = ?",
                (ev["record_id"],),
            )
            if not any(s["scoped_id"] == ticket["ticket_id"] for s in scoped):
                continue
            if tested_at and parse_ts(ev["recorded_at"]) < tested_at:
                continue
            basis = ev["basis"] or ""
            # manifests / mill receipts mentioned in basis
            for m in rows(conn, "SELECT manifest_id, movement_id FROM carrier_departure"):
                lab = label_of(conn, m["manifest_id"]) or ""
                if lab and lab in basis:
                    bundle = _movement_bundle(conn, m["movement_id"])
                    shipments[m["movement_id"]] = {
                        "movement_id": m["movement_id"],
                        "label": bundle["label"],
                        "basis": "ownership_event.basis names carrier manifest",
                        "record_id": ev["record_id"],
                        "source_location": bundle.get("source_location"),
                    }
                    if bundle.get("mill_intake"):
                        rec = bundle["mill_intake"]
                        receipts[rec["receipt_id"]] = {
                            "receipt_id": rec["receipt_id"],
                            "label": label_of(conn, rec["receipt_id"]),
                            "movement_id": rec["movement_id"],
                            "basis": "mill_intake of commercially scoped movement",
                        }
                        proc = mill_process_for_receipt(conn, rec["receipt_id"])
                        if proc:
                            outputs[proc["output_batch_id"]] = {
                                **proc,
                                "basis": "mill_process of linked mill intake",
                            }
            for mi in rows(conn, "SELECT receipt_id, movement_id FROM mill_intake"):
                lab = label_of(conn, mi["receipt_id"]) or ""
                if lab and lab in basis:
                    receipts[mi["receipt_id"]] = {
                        "receipt_id": mi["receipt_id"],
                        "label": lab,
                        "movement_id": mi["movement_id"],
                        "basis": "ownership_event.basis names mill receipt",
                        "record_id": ev["record_id"],
                    }
                    bundle = _movement_bundle(conn, mi["movement_id"])
                    shipments[mi["movement_id"]] = {
                        "movement_id": mi["movement_id"],
                        "label": bundle["label"],
                        "basis": "mill intake named on ownership event",
                        "record_id": ev["record_id"],
                        "source_location": bundle.get("source_location"),
                    }
                    proc = mill_process_for_receipt(conn, mi["receipt_id"])
                    if proc:
                        outputs[proc["output_batch_id"]] = {
                            **proc,
                            "basis": "mill_process of named mill receipt",
                        }

        if ticket.get("intake"):
            bin_id = ticket["intake"]["assigned_bin_id"]
            arrived = ticket["intake"]["arrived_at"]
            loadouts = rows(
                conn,
                "SELECT loadout_id, movement_id, bin_id, dispatch_ref, quantity_kg, loaded_at, desk_comment "
                "FROM elevator_loadout WHERE bin_id = ? ORDER BY loaded_at",
                (bin_id,),
            )
            for ld in loadouts:
                if parse_ts(ld["loaded_at"]) >= parse_ts(arrived):
                    named = named_tickets_for_movement(conn, ld["movement_id"])
                    physical_candidates.append(
                        {
                            "movement_id": ld["movement_id"],
                            "dispatch_ref": ld["dispatch_ref"],
                            "loaded_at": ld["loaded_at"],
                            "quantity_kg": ld["quantity_kg"],
                            "tickets_named_on_related_moves": [n["ticket_label"] for n in named],
                            "this_ticket_named": any(n["ticket_id"] == ticket["ticket_id"] for n in named),
                        }
                    )

    unresolved = unresolved_related(conn, needles)
    # If ticket sits in a blended bin, keep physical allocation failures for later loadouts.
    for cand in physical_candidates:
        unresolved.extend(
            f
            for f in unresolved_related(conn, [cand["dispatch_ref"], cand["movement_id"]])
            if f not in unresolved
        )

    return {
        "computation": "inspection_downstream_scope",
        "world_binding": world_db.world_binding(conn),
        "query": {"sample": sample_token},
        "sample": sample,
        "established_source_ticket": ticket,
        "established_downstream": {
            "shipments": [shipments[k] for k in sorted(shipments)],
            "processor_receipts": [receipts[k] for k in sorted(receipts)],
            "processed_outputs": [outputs[k] for k in sorted(outputs)],
        },
        "physical_bin_loadouts_after_intake": physical_candidates,
        "unresolved": unresolved,
    }


COMPUTATIONS = {
    "shipment_source_status": {
        "required": ("dispatch",),
        "fn": lambda conn, p: shipment_source_status(conn, p["dispatch"]),
    },
    "processor_receipt_provenance": {
        "required": ("processor_receipt",),
        "fn": lambda conn, p: processor_receipt_provenance(conn, p["processor_receipt"]),
    },
    "custody_owner_at": {
        "required": ("material", "timestamp"),
        "fn": lambda conn, p: custody_owner_at(conn, p["material"], p["timestamp"]),
    },
    "inspection_downstream_scope": {
        "required": ("sample",),
        "fn": lambda conn, p: inspection_downstream_scope(conn, p["sample"]),
    },
}


def run_computation(conn, computation_id: str, params: dict[str, str]) -> dict[str, Any]:
    spec = COMPUTATIONS.get(computation_id)
    if spec is None:
        raise KeyError(f"unknown computation: {computation_id}")
    missing = [name for name in spec["required"] if name not in params or params[name] in (None, "")]
    if missing:
        raise ValueError(f"missing required parameters: {', '.join(missing)}")
    return spec["fn"](conn, params)

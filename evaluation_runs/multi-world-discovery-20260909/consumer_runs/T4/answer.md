# PGE-OUT-5003: meaning of `N3 / EF-18?` and whether EF-18 is the source ticket

## What the truck is

`PGE-OUT-5003` is a 12,000 kg loadout from **North House 12** (`BIN-12`) on 2025-09-05. Truck **NST-219** (Northstar Bulk Transport) departed under carrier manifest **NS-8910**, bill of lading **NS-5003-C**, route code **EAST-1**, consigned to **Hearthland Feed Mill – East** (`HFM-E`).

## What the handwritten note means

The route packet for that truck carries a handwritten cargo mark: **`N3 / EF-18?`**. It was copied onto the carrier manifest as `cargo_mark`, with an explicit route note that it is **not confirmed as a scale ticket**.

| Part | Likely meaning |
|------|----------------|
| **N3** | A **route code**, not a grain ticket. Operating notes state that `N3` is used as a route code elsewhere. The loadout itself is routed **EAST-1** to HFM-E; `N3` appears to be informal shorthand on the packet, not an elevator scale-ticket identifier. |
| **EF-18?** | A **tentative guess** at provenance. `EF-18` is a real receiving scale ticket: East Fork Co-op delivered 17,900 kg of hard red wheat into `BIN-12` on 2025-09-03 (`ER-7729`). The trailing **`?`** signals that whoever wrote the note was unsure whether that delivery supplied this truck. |

So the note is a desk shorthand combining “route N3” with “maybe from ticket EF-18?” — not a validated allocation of the load to a single intake.

## Can we treat EF-18 as the source ticket for that truck?

**No.** The supplied records do not support treating `EF-18` as the authoritative source ticket for `PGE-OUT-5003`.

1. **The note is explicitly unvalidated.** `operating_notes.md` states the handwritten cargo note is **not a validated source ticket**. The carrier manifest’s `route_note` says the same: it is **not confirmed as a scale ticket**.

2. **The hopper move records no ticket.** Bin movement `BM-006` (BIN-12 → LOAD-PIT-3 for `OUT-5003`, 12,000 kg) has `material_note` = **“no ticket on hopper sheet”**. That is the mechanical record of what left the bin for this loadout; it does not name `EF-18` or any other ticket.

3. **Loadout records do not allocate provenance unless the desk says so.** Operating notes explain that a loadout identifies bin and truck only; it does **not** tie a blended truck load back to individual receiving tickets unless a desk comment does. For `LD-20` (`PGE-OUT-5003`), the desk comment is only **“seal 8910”** — no ticket allocation.

4. **North House 12 is blended.** By loadout time, `BIN-12` had received grain under tickets **DR-44**, **WB-390**, and **EF-18**. A 12,000 kg draw cannot be assigned to `EF-18` without an explicit allocation rule; the bin crew did not provide one for this move.

5. **`EF-18` was already partially attributed elsewhere.** Movement `BM-004` (for `OUT-5002` the day before) lists material as **“WB-390 / EF-18”** for 26,000 kg out of the same bin. Treating the full `PGE-OUT-5003` load as sourced from `EF-18` would double-count or over-allocate that ticket without evidence.

6. **Weight does not close the question.** The `EF-18` intake was 17,900 kg; this truck carried 12,000 kg. Even a single-ticket reading would require knowing how much of `EF-18` remained in the bin after prior withdrawals — which the exports do not establish.

7. **Downstream records treat provenance as unknown.** Lab sample `SMP-UNLISTED` was keyed to `N3 / EF-18?` from the **route packet note**, with analyst comment **“source ticket not recorded”**. No HFM receiving slip for this truck appears in the supplied HFM-North log (and the truck was consigned to HFM-E, not HFM-N).

## Bottom line

**`N3 / EF-18?`** is informal route-and-provenance handwriting on the departure packet: route code `N3`, plus an uncertain reference to scale ticket `EF-18`. **`EF-18` cannot be treated as the confirmed source ticket** for the `PGE-OUT-5003` truck under the supplied evidence. Provenance for that 12,000 kg load from North House 12 remains **unallocated** in the exports.

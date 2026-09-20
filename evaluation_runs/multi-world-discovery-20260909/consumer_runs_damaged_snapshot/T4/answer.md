# PGE-OUT-5003: meaning of `N3 / EF-18?` and whether EF-18 is the source ticket

## What the handwritten note means

On outbound dispatch **PGE-OUT-5003**, the carrier paperwork does not use the usual typed cargo mark (for example `PGE-OUT-5001`). Instead, manifest **NS-8910** records the cargo mark as the handwritten note **`N3 / EF-18?`** (bill of lading **NS-5003-C**, consignee **HFM-E**, 12,000 kg).

That note is a **handwritten route/cargo annotation on the route packet**, not a validated scale ticket:

- **`N3`** is a **route code** used on the packet (not an intake ticket or bin identity).
- **`EF-18?`** is an **informal, uncertain reference** to intake scale ticket **EF-18** (East Fork Co-op). The question mark marks doubt, not confirmation.

The load itself is recorded separately: **PGE-OUT-5003** loaded **12,000 kg** from **North House 12** (bin B-12), truck **NST-219**, on 2025-09-05.

## Can we treat EF-18 as the source ticket for that truck?

**No.** The available evidence does not support treating EF-18 as the proven source ticket for PGE-OUT-5003.

Reasons:

1. **The note is not validated.** The grain-flow world explicitly flags this as unresolved: the handwritten cargo note is **not a validated scale ticket**, and `N3` is only a route code.

2. **The bin was commingled.** North House 12 held grain from three validated intake tickets before this loadout:
   - **DR-44** (Cedar Ridge Farm, 39,900 kg)
   - **WB-390** (Willow Bend Farms, 23,850 kg)
   - **EF-18** (East Fork Co-op, 17,900 kg)

   The loadout log records quantity and bin only. It does **not** allocate the 12,000 kg truck to one intake ticket.

3. **The outbound chain is incomplete.** Unlike PGE-OUT-5001, 5002, and 5004, PGE-OUT-5003 has a carrier manifest but **no HFM receiving slip** in the supplied extracts, so mill intake does not confirm what arrived or tie the shipment back to a single elevator ticket.

4. **The lab record agrees it is unconfirmed.** Sample **SMP-UNLISTED** copied the same note as its local lot label (`N3 / EF-18?`) with material hint **"route packet note"** and comment **"source ticket not recorded."** That label is recorded as written; it is **not** treated as a proven join to scale ticket EF-18.

## Bottom line

`N3 / EF-18?` means: **route code N3, with a tentative guess that the grain might relate to ticket EF-18.** EF-18 is a real validated intake ticket at the elevator, but the handwritten note alone does **not** establish that PGE-OUT-5003 came from EF-18. That allocation remains **unresolved** and should be treated as an unconfirmed operator note, not as the truck's source ticket.

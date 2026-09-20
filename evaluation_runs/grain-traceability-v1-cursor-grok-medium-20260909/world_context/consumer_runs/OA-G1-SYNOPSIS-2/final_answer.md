I'll start by reading the instruction file and the questions, then work through the workspace files to answer each one.Answers below use only `world/world.sqlite` and the purpose notes. Identifiers are the world referents and assertion-backed facts.

---

### NQ-01. Inbound loads for PGE-OUT-5002

**Established:** PGE-OUT-5002 was loaded from North House 12 / BIN-12 (`loadout:LD-19`, 26,000 kg, `2025-09-04T13:15:00-05:00`). The matching hopper move `move:BM-004` (`bin:north-house-12` → `pit:load-2`, work order OUT-5002, material note `WB-390 / EF-18`) names inbound tickets **WB-390** (`ticket:wb-390`, ER-7721) and **EF-18** (`ticket:ef-18`, ER-7729) via `ticket_named_on_move`. Those are the inbound loads established as contributing.

**Not established:** DR-44 (`ticket:dr-44`) also occupied BIN-12 before this loadout, but it is not named on BM-004 or LD-19. Contribution of DR-44 to PGE-OUT-5002 is not asserted. Kilograms are not split between WB-390 and EF-18 on that 26,000 kg move.

---

### NQ-02. Downstream shipments of BIN-12 material, and source allocation

BIN-12 is `bin:north-house-12` (`known_as` token `BIN-12`).

**Shipments that left from BIN-12:** **PGE-OUT-5001** (LD-18), **PGE-OUT-5002** (LD-19), **PGE-OUT-5003** (LD-20). PGE-OUT-5004 left from South House 14, not BIN-12.

Continuing mill identity (where recorded): HFM-IN-601 / MILL-2206 / FEED-2206 from PGE-OUT-5001; HFM-IN-602 / MILL-2207 / FEED-2207 from PGE-OUT-5002. No mill intake for PGE-OUT-5003.

**Individual source allocation:** only **PGE-OUT-5002** (and therefore HFM-IN-602 / FEED-2207). Hopper `BM-004` names WB-390 and EF-18. PGE-OUT-5001 has no hopper tickets (`physical-ticket-allocation-PGE-OUT-5001`; commercial DR-44 scope on RL-8841 / HFM-IN-601 is not a bin allocation). PGE-OUT-5003 hopper note is `no ticket on hopper sheet` (`physical-ticket-allocation-PGE-OUT-5003`).

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 -05:00

**In that window, two intakes at Prairie Gate:**

| Ticket | Receipt | Arrived | Net kg | Grower (intake) | Assigned bin |
|---|---|---|---|---|---|
| WB-390 / ER-7721 | `ticket:wb-390` | 09:20 | 23,850 | Willow Bend Farms | BIN-12 |
| EF-18 / ER-7729 | `ticket:ef-18` | 11:05 | 17,900 | East Fork Co-op | BIN-12 |

Both were transferred lane → BIN-12: `BM-002` (WB-390, 09:47) and `BM-003` (EF-18, 11:28).

**Later, established use of a named portion:** 26,000 kg labeled WB-390 / EF-18 left BIN-12 on `BM-004`/`BM-005` as PGE-OUT-5002 (loadout 13:15, carrier NS-8848 / NS-5002-B, mill HFM-IN-602 25,500 kg into silo S-5, mill run MILL-2207 → FEED-2207). Title on WB-390 moved Willow Bend → GrainLink Merchants at 15:00 the same day (`ownership:TR-102`).

**Not established:** whether remaining mass of those two tickets left on unallocated PGE-OUT-5001 or PGE-OUT-5003, or stayed in BIN-12. No per-ticket remainder is recorded.

---

### NQ-04. Processor receipts with complete upstream provenance to inbound load(s)

**Only HFM-IN-602** (`mill-receipt:HFM-IN-602`) has identified inbound loads: movement PGE-OUT-5002 → BM-004 names **WB-390 and EF-18**. BOL identity of that truck is established (kg 26,000 vs 25,500 is unexplained, not a different movement).

**HFM-IN-601:** linked to PGE-OUT-5001 from BIN-12, but no receiving tickets on that loadout. Incomplete physical provenance.

**HFM-IN-604:** linked to PGE-OUT-5004 from BIN-14 after MCR-118 and S-52 were both placed there; hopper `no individual ticket`. Incomplete.

No mill receipt exists for PGE-OUT-5003.

---

### NQ-05. Unresolved chains and the unresolved part

From `purpose_requirement_failure` (EXPLICIT_UNRESOLVED):

1. **PGE-OUT-5001 physical tickets** — BIN-12 already held DR-44, WB-390, and EF-18; no hopper tickets; loadout does not allocate the blend; DR-44 commercial scope to RL-8841 / HFM-IN-601 is not bin allocation.
2. **PGE-OUT-5003 physical tickets** — hopper has no ticket; cargo mark `N3 / EF-18?` is not a validated source ticket (N3 is a route code).
3. **PGE-OUT-5003 mill receipt** — 12,000 kg left on NS-8910; no HFM receiving slip in extracts; consignee HFM-E.
4. **PGE-OUT-5004 physical tickets** — South House 14 after MCR-118 and S-52; desk did not record which delivery supplied the truck.
5. **MCR-118 grower identity** — intake name `M. Creek`; commercial claims Meadow Creek Farms and Meadow Creek Grain; no account key (`ownership:TR-107`).
6. **SMP-UNLISTED source ticket** — source ticket not recorded; route-packet note is not a validated ticket.
7. **SMP-604Q ticket** — labeled South House 14 cargo / MC-118; after both MCR-118 and S-52 in BIN-14, cargo is not allocated to one delivery.
8. **Quantity differences on established movements** — PGE-OUT-5001 39,000/38,700; PGE-OUT-5002 26,000/25,500; PGE-OUT-5004 19,000/18,800 kg; unexplained, same movements.

---

### NQ-06. Missing linkage for PGE-OUT-5003 provenance

**The missing upstream link** is a validated source ticket on the outbound grain: `BM-006` material note is `no ticket on hopper sheet`; carrier cargo mark `N3 / EF-18?` is explicitly not a confirmed scale ticket (`physical-ticket-allocation-PGE-OUT-5003`, `manifest:NS-8910`).

**Separately unresolved downstream:** no mill_intake row for `movement:PGE-OUT-5003` (`mill-receipt-absent-PGE-OUT-5003`). Consignee HFM-E is not a receipt (`consignee_is_not_receipt` on NS-8910).

---

### NQ-07. Owner and custody of WB-390 material at 2025-09-04 13:10:00-05:00

**Owner (established):** **GrainLink Merchants**. `ownership:TR-102` (title_change, scope WB-390) is effective 2025-09-03 15:00 through 2025-09-05 10:50. `ownership:TR-104` (OUT-5002, from 13:05) also has `owner_after` GrainLink Merchants.

**Custody is not a single holder for all WB-390 mass.** At 13:10:

- `TR-104` (scope **OUT-5002**, start 13:05): `holder_after` **Northstar Bulk Transport**. By then `BM-004` (13:02) had already pulled 26,000 kg named WB-390 / EF-18 into `pit:load-2`; truck load `BM-005` is at 13:14.
- `TR-102` (scope **ticket WB-390**) still lists `holder_after` **Prairie Gate Elevator** until mill dock 2025-09-05 10:50.

WB-390 inbound was 23,850 kg; the named OUT-5002 pull is a 26,000 kg WB-390/EF-18 blend with no kg split. Any WB-390 still in BIN-12 would remain under Prairie Gate custody on TR-102; the OUT-5002 portion is under Northstar custody on TR-104. The world does not say all WB-390 had left the bin.

---

### NQ-08. Downstream material affected by SMP-602B

**SMP-602B** (`sample:SMP-602B`, LAB-4419, 2025-09-05 13:10) is a combined truck sample on **receiving slip HFM-IN-602**, local lot `WB390 / EF18`, aflatoxin below limit.

**Affected, established:** mill receipt **HFM-IN-602** (PGE-OUT-5002 / NS-5002-B, silo S-5), mill run **MILL-2207**, output batch **FEED-2207** (grower feed). Upstream named sources of that receipt are WB-390 and EF-18; the sample does not split them.

**Not established:** effect on other BIN-12 shipments (PGE-OUT-5001, PGE-OUT-5003) or on FEED-2206.

---

### NQ-09. Apparent identity matches that should not be committed

Do **not** treat as established:

- **`N3 / EF-18?` = ticket EF-18** (PGE-OUT-5003 cargo mark and SMP-UNLISTED local lot). N3 is a route code; the handwritten note is not a validated ticket.
- **Commercial DR-44 on RL-8841 / HFM-IN-601 = physical content of PGE-OUT-5001.** Ownership/commercial scope is not bin allocation.
- **M. Creek = Meadow Creek Farms or Meadow Creek Grain** as the MCR-118 grower. Duplicate claims; no account key.
- **SMP-604Q = solely MCR-118.** Token MC-118 is aliased to `ticket:mcr-118`, but after MCR-118 and S-52 both entered BIN-14 the South House 14 cargo is not allocated to one delivery.
- **Consignee HFM-N / HFM-E = a mill receiving record.** `consignee_is_not_receipt` applies to all four manifests.

Token aliases that **are** established (BIN-12 = North House 12, HFM-N = `site:hfm-north`, WB390 = WB-390, etc.) are not in this list.

---

### NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** There is **no** `mill_intake` for `movement:PGE-OUT-5003` at `site:hfm-north`. North receipts in the extract are only HFM-IN-601, HFM-IN-602, HFM-IN-604. `extract_coverage` states the HFM-North receiving log is **complete** for 2025-09-05 through 2025-09-07. That supports a **justified negative** that HFM-N has no receiving record for this movement (consignee was HFM-E anyway).

**HFM-E:** There is also no mill_intake row at `site:hfm-east`, but that is **absence in the working set**, not a justified “HFM-E has no record.” The same coverage claim says North completeness **does not** support conclusions about other HFM sites. Purpose `mill-receipt-absent-PGE-OUT-5003` keeps East receiving unresolved. Consignee HFM-E on NS-8910 is not itself a receipt.

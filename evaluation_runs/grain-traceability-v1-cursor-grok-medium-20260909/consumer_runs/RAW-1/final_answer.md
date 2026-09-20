I'll start by reading the instruction file and the consumer questions so I can work through each one with the workspace files.Answers use only the workspace extracts and notes. Established links are separated from gaps; similar names are not treated as identity unless a record joins them.

---

**NQ-01. Which inbound loads contributed to outbound shipment PGE-OUT-5002?**

**Established:** PGE-OUT-5002 was loaded from North House 12 (`BIN-12`) as 26,000 kg on `LD-19` (truck `NST-204`, 2025-09-04T13:15-05:00). Hopper move `BM-004` (`BIN-12` → `LOAD-PIT-2`, work order `OUT-5002`) names material `WB-390 / EF-18`. Those tickets are inbound receipts `ER-7721` (`WB-390`, Willow Bend Farms, 23,850 kg into `B-12`) and `ER-7729` (`EF-18`, East Fork Co-op, 17,900 kg into `B-12`). `BM-005` then put that 26,000 kg on `TRUCK-NS204`. Manifest `NS-8848` / BOL `NS-5002-B` marks cargo `PGE-OUT-5002`.

**Not established:** How many kilograms of `WB-390` vs `EF-18` are on the truck. Loadout comments do not allocate a blend unless the desk says so (`LD-19` comment is only `seal 8848`). Contribution from residual `DR-44` (also stored in `BIN-12`) is not asserted on the hopper sheet.

---

**NQ-02. Which downstream shipments contain material that occupied BIN-12, and which of those have individual source allocation?**

**Occupied `BIN-12`:** `DR-44` (`BM-001`), `WB-390` (`BM-002`), `EF-18` (`BM-003`). Notes equate `BIN-12` with North House 12 and `B-12`.

**Downstream shipments from that house:**
- **PGE-OUT-5001** — `LD-18` from North House 12, 39,000 kg. No hopper row in `bin_movements.csv` for this loadout. Custody `TR-103` scopes **`DR-44`** to dispatch `RL-8841` (manifest cargo `PGE-OUT-5001`). That is lot-level identification of `DR-44`, not a split of a named blend. Intake 39,900 kg vs loadout 39,000 kg is unexplained.
- **PGE-OUT-5002** — from `BIN-12`; hopper names `WB-390 / EF-18`. **No individual allocation.**
- **PGE-OUT-5003** — `LD-20` / `BM-006` from North House 12; hopper `no ticket on hopper sheet`. **No individual allocation.**

Mill slips `HFM-IN-601` and `HFM-IN-602` continue 5001 and 5002. There is no mill slip for 5003 in the extract.

---

**NQ-03. What happened to grain received 2025-09-03 09:00:00-05:00 through 12:00:00-05:00?**

**In window:**
- `ER-7721` / `WB-390`: arrived 09:20, 23,850 kg, Lane 1, assigned `B-12`; `BM-002` at 09:47 `INTAKE-1` → `BIN-12`.
- `ER-7729` / `EF-18`: arrived 11:05, 17,900 kg, Lane 1, assigned `B-12`; `BM-003` at 11:28 `INTAKE-1` → `BIN-12`.

**After the window (not inside it):** title on `WB-390` to GrainLink Merchants at 15:00 (`TR-102`, holder still Prairie Gate). Later both tickets are named on the `OUT-5002` hopper; remaining `BIN-12` draw `OUT-5003` has no ticket. No other receipts fall in that three-hour window.

---

**NQ-04. Which processor receipts have complete upstream provenance to identified inbound load(s)?**

| Receipt | Provenance |
|---|---|
| **HFM-IN-601** | Complete to **`DR-44` / `ER-7714`**: BOL `RL-5001-A` = manifest `RL-8841` cargo `PGE-OUT-5001`; `TR-106` title change on `DR-44` with basis processor acceptance `HFM-IN-601`. |
| **HFM-IN-602** | Complete to **identified loads `WB-390` and `EF-18` as an unallocated pair**: BOL `NS-5002-B` = `PGE-OUT-5002`; hopper `BM-004`. Not complete as a per-ticket split. |
| **HFM-IN-604** | **Not complete.** BOL `RL-5004-Q` = `PGE-OUT-5004` from South House 14 (`BIN-14`) after `MCR-118` and `S-52` were placed there; hopper `no individual ticket`; notes say the desk did not record which delivery filled the truck. |

No other processor receipts are in the extract.

---

**NQ-05. Which traceability chains remain unresolved, and what is unresolved?**

1. **PGE-OUT-5003** — no hopper/scale ticket (`BM-006`); cargo mark `N3 / EF-18?` is not a validated ticket; no mill receiving slip in the extracts; consignee `HFM-E` is not a receiving slip.
2. **PGE-OUT-5004 / HFM-IN-604** — `BIN-14` blend of `MCR-118` and `S-52` not allocated; no mill run listed for `HFM-IN-604`.
3. **`MCR-118` commercial identity** — intake grower `M. Creek`; `TR-107` duplicate claims (Meadow Creek Farms vs Meadow Creek Grain), no account key.
4. **`DR-44` mass** — 39,900 kg in vs 39,000 kg on `PGE-OUT-5001`; remainder not traced. `BIN-12` in (81,650 kg) vs out (77,000 kg) likewise unexplained.
5. **SMP-UNLISTED** — protein on route-packet text `N3 / EF-18?`; comment: source ticket not recorded.
6. **HFM-E receipts** — not in the working set; absence is not a finding for East (see NQ-10).

---

**NQ-06. What specific missing linkage prevents complete provenance for PGE-OUT-5003?**

The load is not tied to an inbound scale ticket: `BM-006` is `no ticket on hopper sheet`; the packet note `N3 / EF-18?` is a route code plus an unconfirmed guess, not ticket `EF-18`. Separately, the chain does not close at a mill: notes state the 12,000 kg truck left with a manifest (`NS-8910`, BOL `NS-5003-C`) and **no HFM receiving slip is in the supplied extracts**. Either gap blocks complete provenance; the missing inbound ticket is what blocks source identity of the cargo itself.

---

**NQ-07. At 2025-09-04 13:10:00-05:00, who owned and who had custody of the WB-390 material?**

**Owner:** GrainLink Merchants — `TR-102` title change on scope `WB-390`, effective 2025-09-03T15:00 through 2025-09-05T10:50; `TR-104` also has `owner_after` GrainLink on `OUT-5002`.

**Custody:** On the **`WB-390` lot record (`TR-102`)**, `holder_after` is still Prairie Gate Elevator at 13:10. On **`OUT-5002` (`TR-104`)**, from 13:05 `holder_after` is Northstar Bulk Transport (dispatch `NS-8848`). At 13:10 the 26,000 kg blend is in `LOAD-PIT-2` (`BM-004` at 13:02); physical load to `TRUCK-NS204` is `BM-005` at 13:14. How much of lot `WB-390` (23,850 kg) is in that blend vs still in `BIN-12` is **not allocated**. Do not treat all of `WB-390` as Northstar’s custody.

---

**NQ-08. Which downstream material is affected by inspection SMP-602B?**

**SMP-602B** (2025-09-05T13:10, `LAB-4419`) is a **combined truck sample** on receiving slip **`HFM-IN-602`**, local lot `WB390 / EF18`, aflatoxin below limit.

**Affected, as sampled:** mill receipt `HFM-IN-602` (silo `S-5`) and mill run `MILL-2207` output **`FEED-2207`** (input receipts `["HFM-IN-602"]`). That is the `PGE-OUT-5002` blend, not a single inbound ticket.

**Not established:** application to leftover `BIN-12` / `PGE-OUT-5003`, to `HFM-IN-601` / `FEED-2206`, or to `BIN-14` / `PGE-OUT-5004`.

---

**NQ-09. Which apparent identity matches should not be committed as established?**

- **`N3 / EF-18?` ≠ scale ticket `EF-18`.** `N3` is a route code; the handwritten cargo mark is not a validated ticket (`operating_notes.md`, manifest `NS-8910` `route_note`, `SMP-UNLISTED`).
- **`M. Creek` / `MCR-118` ≠ Meadow Creek Farms or Meadow Creek Grain.** Duplicate claims, no selecting account key (`TR-107`).
- **Lab lot `MC-118` (`SMP-604Q`, “South House 14 cargo”) ≠ solely `MCR-118`.** `BIN-14` also held `S-52`; `PGE-OUT-5004` was not ticket-allocated.
- **Consignee code `HFM-E` ≠ a mill receiving slip.**
- **Name-only `PG-OUT-####` vs `PGE-OUT-####`** is not enough by itself; 5001/5002/5004 are joined by **matching BOLs**, not by the prefix.

Local-name equivalences that **are** stated: `PG-ELEV` = Prairie Gate; `BIN-12` = North House 12; `BIN-14` = South House 14.

---

**NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N? Can evidence say HFM-E has none?**

**HFM-N:** There is **no** receiving record for `PGE-OUT-5003` (no match on origin, BOL `NS-5003-C`, manifest `NS-8910`, or truck `NST-219`). The HFM-North log is **complete for 2025-09-05 through 2025-09-07**, so that absence at **HFM-N** in that window is a justified negative. The truck was consigned to **`HFM-E`**, not North.

**HFM-E:** The evidence **cannot** justify saying East has no receiving record. Completeness is claimed only for HFM-North; “no conclusion about other HFM sites follows from its absence.” Missing East extracts is not a finding of non-receipt.

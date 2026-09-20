I'll read the instruction and question files first, then work through every question with the workspace files I have.Answers use only `reference/instance.json`, `reference/model.json`, and `PURPOSE.md`. Epistemic policy: assert positives only when supported; treat candidates as non-coreferential; assert absence only under a scoped completeness claim; otherwise `not_established`.

---

### NQ-01. Inbound loads into PGE-OUT-5002

**Established:** PGE-OUT-5002 is outbound load **M-202**. It is composed of:

| Inbound load | Host refs | Quantity into M-202 | Source party |
|---|---|---|---|
| **M-102** | ER-7721, **WB-390** | 15 000 kg | WILLOW-BEND |
| **M-103** | ER-7729, **EF-18** | 11 000 kg | EAST-FORK |

**Evidence:** `materials` M-202 `host_refs` include PGE-OUT-5002; `composition` lists M-102/M-103; `derived_views.shipment_source_contributions` marks both contributions `established`; loadout **E-LOAD-202** has the same `contribution` map.

No other inbound loads are asserted as contributors.

---

### NQ-02. Downstream shipments from BIN-12, and source allocation

Materials that occupied BIN-12: **M-101**, **M-102**, **M-103** (`storage_place` / storage_move to BIN-12). **M-203** was loaded **from** BIN-12 without named inbound composition.

Downstream **shipments** from that occupancy:

| Shipment | Host refs | Individual source allocation? |
|---|---|---|
| **M-201** | PGE-OUT-5001, RL-5001-A, HFM-IN-601 | **Yes — established.** 39 000 kg from **M-101** (`shipment_source_contributions`, E-LOAD-201). |
| **M-202** | PGE-OUT-5002, NS-5002-B, HFM-IN-602 | **Yes — established.** 15 000 kg **M-102** + 11 000 kg **M-103** (E-LOAD-202). |
| **M-203** | PGE-OUT-5003, NS-5003-C | **No.** `composition` is null; `missing_links` includes `no_source_allocation`; E-LOAD-203 lists material M-203 only. |

**Not shipments:** processed products **M-301** (from M-201) and **M-302** (from M-202) are further downstream of allocated BIN-12 grain, but they are `processed_product`, not outbound shipments.

**M-204** is from **BIN-14**, not BIN-12.

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 −05:00

Two inbound loads fall in that window (elevator completeness is `complete_for_listed_tickets` at PGE-01 for 2025-09-02–07, so these are the listed receipts, not a claim that no unlisted tickets exist outside that listing rule):

1. **M-102** (WB-390 / ER-7721), Willow Bend, 23 850 kg  
   - Receive **E-RECV-102** 09:20–09:40, INTAKE-1, PGE-01  
   - Store **E-BIN-102** 09:47–09:55 → BIN-12  
   - Title **E-OWN-102** 15:00: WILLOW-BEND → GRAINLINK; `custody_party` PRAIRIE-GATE  
   - Loadout **E-LOAD-202** 2025-09-04 13:15–13:20: 15 000 kg into **M-202** / PGE-OUT-5002  
   - Transport to HFM-N, processor receipt **E-RECV-202**, sample **SMP-602B**, process **E-PROC-302** → **M-302** / FEED-2207  

2. **M-103** (EF-18 / ER-7729), East Fork, 17 900 kg  
   - Receive **E-RECV-103** 11:05–11:20, INTAKE-1  
   - Store **E-BIN-103** 11:28–11:35 → BIN-12  
   - Loadout **E-LOAD-202**: 11 000 kg into **M-202** (same downstream path as above)

**Not established:** disposition of the **unallocated remainder** of M-102 (23 850 − 15 000) and M-103 (17 900 − 11 000) still associated with BIN-12. **M-203** later draws 12 000 kg from BIN-12 with **no** source allocation, so it is **not** established that those remainders (or M-101 residue) became PGE-OUT-5003.

---

### NQ-04. Processor receipts with complete upstream provenance to identified inbound load(s)

Processor receipts in the instance:

| Receipt | Material / host | Upstream to inbound loads |
|---|---|---|
| **E-RECV-201** | M-201 / HFM-IN-601 / PGE-OUT-5001 | **Complete, established:** M-201 ← M-101 (ER-7714 / DR-44). |
| **E-RECV-202** | M-202 / HFM-IN-602 / PGE-OUT-5002 | **Complete, established:** M-202 ← M-102 and M-103 with quantities. |
| **E-RECV-204** | M-204 / HFM-IN-604 / PGE-OUT-5004 | **Not complete.** Candidates **M-104**, **M-105**; `no_individual_loadout_allocation`; E-LOAD-204 `individual_contribution_undetermined`. Loads are candidates, not established contributions. |

There is **no** `processor_receipt` for **M-203** / PGE-OUT-5003.

So only **HFM-IN-601 (M-201)** and **HFM-IN-602 (M-202)** have complete established provenance to identified inbound load(s).

---

### NQ-05. Unresolved chains and what is unresolved

| Chain | Unresolved part |
|---|---|
| **M-203 / PGE-OUT-5003** | `no_source_allocation` (BIN-12 draw not tied to inbound lots); `no_processor_receipt`; **E-TRANS-203** `departure_record_only` (no arrival end time). |
| **M-204 / PGE-OUT-5004** and sample **SMP-604Q** | Shipment identity established; **individual inbound contributions not established** (M-104 vs M-105). Identity decision: “shipment established; source contribution not established.” |
| **M-104 / MCR-118** | **Source party not established** (`source_party` null; candidates MEADOW-CREEK-FARMS vs MEADOW-CREEK-GRAIN); **E-RECV-104** `source_party_undetermined`. |
| **Note “N3 / EF-18?” vs EF-18 / M-103** | **`unsupported_match`**; must not be treated as co-reference (`unresolved_identity_candidates`). |
| **HFM-E processor receipts** (scope 2025-09-05–07) | Completeness **`unknown`** — missing receipts there are **not** justified absences. |

---

### NQ-06. Missing linkage for complete provenance of PGE-OUT-5003

**M-203** (`PGE-OUT-5003`) records two explicit `missing_links`:

1. **`no_source_allocation`** — loadout **E-LOAD-203** is from BIN-12 (12 000 kg to NST-219) with **no** `composition` / contribution from M-101, M-102, or M-103. The handwritten **N3 / EF-18?** link to M-103 is **`unsupported_match`**.

2. **`no_processor_receipt`** — transport is **E-TRANS-203** `departure_record_only` toward **HFM-E**; no `processor_receipt` event.

For **complete provenance of origin**, the blocking established gap is **`no_source_allocation`**. Processor receipt is a separate downstream gap, not a substitute for source allocation.

---

### NQ-07. Ownership and custody of WB-390 at 2025-09-04 13:10:00−05:00

**Identity:** WB-390 = **M-102** (`identity_decisions` `established`).

**Ownership (established):** **GRAINLINK** (GrainLink Merchants). `ownership_intervals` for M-102: GRAINLINK as `title_holder` from 2025-09-03T15:00:00−05:00 through 2025-09-05T10:50:00−05:00. 13:10 on 2025-09-04 is inside that interval.

**Custody:** **not_established** as an `in_custody_of_during` interval on M-102 (custody intervals exist only for **M-201** and **M-202**).

Related facts that must not be collapsed:

- Loadout of M-102 into M-202 is **E-LOAD-202** starting **13:15**, so at **13:10** M-102 is still after **E-BIN-102** (BIN-12), not yet loaded.
- Custody of **shipment M-202** (not the same as a custody interval on M-102) transferred **PRAIRIE-GATE → NORTHSTAR** at **13:05** (**E-CUST-202A**). That is custody of M-202, not an established custody assertion for WB-390/M-102 at 13:10.

Last `custody_party` recorded **on M-102** is **PRAIRIE-GATE** at the 2025-09-03 15:00 ownership change; there is no later custody_change on M-102.

---

### NQ-08. Downstream material affected by SMP-602B

**Established sample:** **E-SAMPLE-202** — sample **SMP-602B** from **M-202** (PGE-OUT-5002 / HFM-IN-602) at 2025-09-05 13:10.

**Downstream of that sampled material:**

- **M-202** itself (the inspected outbound/processor lot).
- **M-302** / **FEED-2207**, output of **E-PROC-302** (15:10–16:00 the same day) with composition from M-202 (25 500 kg).

**Upstream** lots M-102 and M-103 contributed to M-202 but are not downstream of the inspection. **M-203** / **M-204** / **M-301** are not linked to SMP-602B.

---

### NQ-09. Apparent identity matches that must not be committed as established

Do **not** commit as established co-reference:

1. **`N3 / EF-18?` ↔ EF-18 / M-103** — `result` null, status **`unsupported_match`** (handwritten note; N3 treated as route code; no source allocation for M-203).

2. **`MC-118` / `MCR-118` / “South House 14 cargo” / `SMP-604Q` as a single material identity M-104 (vs shipment M-204)** — status **“shipment established; source contribution not established.”** M-204 as the shipment of SMP-604Q is established; collapsing the lot mark to **only** M-104, or assigning a definite split vs M-105, is not established.

3. **M-104 source party:** **MEADOW-CREEK-FARMS** vs **MEADOW-CREEK-GRAIN** remain **candidates**, not a committed party identity.

Established matches (M-101, M-102, M-103, M-201, M-202, M-204 shipment ids) are already `established` and are not in this “do not commit” set.

---

### NQ-10. Processor receiving record for PGE-OUT-5003 at HFM-N vs HFM-E

**At HFM-N:** There is **no** `processor_receipt` whose material is **M-203** / PGE-OUT-5003. Represented HFM-N receipts are M-201, M-202, M-204 only. Destination of M-203 is **HFM-E**, not HFM-N.

**Absence at HFM-N can be asserted** for processor receipts in **2025-09-05 00:00 through 2025-09-07 23:59:59 −05:00**, because `completeness_claims` / `completeness_scoped_absence` for `processor_receipts` at **HFM-N** is **`complete`** (`operating_notes.md`). M-203 departed PGE-01 on 2025-09-05, inside that window.

**At HFM-E:** No receipt for M-203 is **represented**, and M-203 carries `no_processor_receipt`. That is **not** a justified negative. Completeness for `processor_receipts` at **HFM-E** over the same interval is **`unknown`**. Policy: assert absence only under a scoped completeness claim. Therefore the evidence **does not** justify saying HFM-E has no such record; the correct status is **not_established** (no positive receipt, completeness unknown).

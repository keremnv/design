I'll start by reading the instruction file and the questions, then work through them with the files in this workspace.Answers below use only `reference/instance.json` (and the assertion policy in `reference/model.json`). Absence is treated as established only where a completeness claim scopes it; otherwise it is not established.

---

### NQ-01. Inbound loads for PGE-OUT-5002

**Established:** PGE-OUT-5002 is material **M-202**. Two inbound loads contributed:

| Inbound | Host refs | Quantity into M-202 | Source |
|---|---|---|---|
| **M-102** | WB-390, ER-7721 | 15 000 kg | WILLOW-BEND |
| **M-103** | EF-18, ER-7729 | 11 000 kg | EAST-FORK |

**Evidence:** `materials` M-202 `composition`; `derived_views.shipment_source_contributions` (both `status: established`); loadout **E-LOAD-202** with `contribution` M-102:15000, M-103:11000; identity **PGE-OUT-5002 → M-202** (`status: established`).

**Not established:** Any other inbound contributor. M-101 is not in this composition.

---

### NQ-02. Downstream shipments from BIN-12, and source allocation

Materials recorded in BIN-12: **M-101, M-102, M-103** (`storage_place: BIN-12`; storage moves E-BIN-101/102/103). **M-203** was loaded **from** BIN-12 (E-LOAD-203) without naming which inbound lots.

Downstream **shipments** that contain BIN-12 material:

| Shipment | Material | Individual source allocation? |
|---|---|---|
| **PGE-OUT-5001** | M-201 | **Yes** — M-101, 39 000 kg (`established`) |
| **PGE-OUT-5002** | M-202 | **Yes** — M-102 15 000 kg + M-103 11 000 kg (`established`) |
| **PGE-OUT-5003** | M-203 | **No** — `missing_links: no_source_allocation`; composition null |

**Not a BIN-12 shipment:** PGE-OUT-5004 / M-204 is from **BIN-14**.

Processed outputs **M-301 / FEED-2206** (from M-201) and **M-302 / FEED-2207** (from M-202) inherit BIN-12 content via those shipments; they are processed products, not outbound shipments.

---

### NQ-03. Grain received 2025-09-03 09:00–12:00 −05:00

**Received in window (established):**

1. **M-102** (WB-390 / ER-7721, 23 850 kg) — **E-RECV-102** 09:20–09:40 at PGE-01, INTAKE-1, from WILLOW-BEND. Then **E-BIN-102** 09:47–09:55 into BIN-12. Same day **E-OWN-102** 15:00: title WILLOW-BEND → GRAINLINK; custody party PRAIRIE-GATE. On 2025-09-04, **15 000 kg** loaded into **M-202** (E-LOAD-202). M-202 then: NORTHSTAR custody 13:05, transport to HFM-N, **E-RECV-202** (HFM-IN-602, S-5), sample **SMP-602B**, processed to **M-302 / FEED-2207**.

2. **M-103** (EF-18 / ER-7729, 17 900 kg) — **E-RECV-103** 11:05–11:20 at PGE-01, INTAKE-1, from EAST-FORK. Then **E-BIN-103** 11:28–11:35 into BIN-12. **11 000 kg** loaded into **M-202** on 2025-09-04 (same chain as above).

**Not in window:** M-101 (Sep 2), M-104/M-105 (Sep 7).

**Not established:** Disposition of remaining M-102 (8 850 kg) and M-103 (6 900 kg) after the 26 000 kg loadout. M-203 left BIN-12 later with **no source allocation**; that remainder must not be assigned to PGE-OUT-5003.

---

### NQ-04. Processor receipts with complete upstream provenance

Processor receipts in the instance:

| Receipt | Place | Material / host | Upstream to inbound loads |
|---|---|---|---|
| **E-RECV-201** | HFM-N | M-201 / HFM-IN-601 / PGE-OUT-5001 | **Complete** → **M-101** (ER-7714 / DR-44) |
| **E-RECV-202** | HFM-N | M-202 / HFM-IN-602 / PGE-OUT-5002 | **Complete** → **M-102** and **M-103** |
| **E-RECV-204** | HFM-N | M-204 / HFM-IN-604 / PGE-OUT-5004 | **Incomplete** — candidates M-104 and M-105; `no_individual_loadout_allocation` |
| *(none)* | — | M-203 / PGE-OUT-5003 | No processor receipt |

**Answer:** Only **HFM-IN-601 (E-RECV-201)** and **HFM-IN-602 (E-RECV-202)** have complete established provenance to identified inbound load(s).

---

### NQ-05. Unresolved chains

1. **PGE-OUT-5003 / M-203**  
   Unresolved: inbound **source allocation** (`no_source_allocation`); **processor receipt** (`no_processor_receipt`); transport **E-TRANS-203** is `departure_record_only` (end time null). Destination recorded as HFM-E.

2. **PGE-OUT-5004 / M-204** (and sample **SMP-604Q**)  
   Unresolved: **individual loadout contributions** of M-104 vs M-105 (`individual_contribution_undetermined`; identity status “shipment established; source contribution not established”).

3. **M-104 / ER-7744 / MCR-118**  
   Unresolved: **source party** — candidates MEADOW-CREEK-FARMS vs MEADOW-CREEK-GRAIN; E-RECV-104 `source_party_undetermined`.

4. **Handwritten N3 / EF-18?** vs M-103 / M-203  
   Unresolved and **unsupported** (`unsupported_match`); must not be used as a link.

5. **HFM-E processor receipts** (2025-09-05–07)  
   Completeness **unknown** — cannot close the M-203 receipt gap.

6. **BIN-12 remainders** after M-201/M-202 loadouts (M-101 900 kg leftover; M-102/M-103 leftovers) — further allocation **not established**.

---

### NQ-06. Missing linkage for PGE-OUT-5003

**M-203** `missing_links`: **`no_source_allocation`** and **`no_processor_receipt`**.

- Loadout **E-LOAD-203** only records from-place **BIN-12**, 12 000 kg, truck NST-219 — no inbound lot split.  
- Transport **E-TRANS-203** is departure-only toward HFM-E.  
- No `processor_receipt` event. Host refs are only PGE-OUT-5003 and NS-5003-C (no HFM-IN-* id).  
- The N3/EF-18 note is `unsupported_match` and is **not** the missing link to use.

Either missing piece blocks complete provenance; both are asserted as missing in the representation.

---

### NQ-07. Ownership and custody of WB-390 at 2025-09-04 13:10:00−05:00

**Identity:** WB-390 = **M-102** (`established`).

**Owner (established):** **GRAINLINK** — `ownership_intervals` for M-102: GRAINLINK 2025-09-03T15:00 through 2025-09-05T10:50 (`title_holder`, basis TR-102). WILLOW-BEND’s interval ended 15:00 the previous day.

**Custody of M-102:** **not established** as a dedicated `custody_intervals` row (those exist only for M-201 and M-202).

Related facts at that timestamp (do not collapse them):

- Physical loadout of M-102 into M-202 is **E-LOAD-202** at **13:15–13:20** — so at 13:10 M-102 is still recorded in BIN-12, not yet loaded.  
- **M-202** custody is **NORTHSTAR** from **13:05** (E-CUST-202A; interval through 2025-09-05T10:50). That is custody of the outbound lot, which had not yet received M-102 at 13:10.

**Not established:** that NORTHSTAR already had custody of the WB-390 grain at 13:10, or a formal custody party for M-102. Prairie Gate is the storage operator but has no M-102 custody interval.

---

### NQ-08. Downstream material affected by SMP-602B

**Sample:** **E-SAMPLE-202** — SMP-602B sampled **from M-202** at 2025-09-05T13:10 (evidence `inspection_results.csv:3`).

**Affected (established):**

- **M-202** itself (PGE-OUT-5002 / NS-5002-B / HFM-IN-602)  
- **M-302 / FEED-2207**, `derived_from` / composition of M-202 via **E-PROC-302** (15:10–16:00 at HFM-N)

**Upstream, not downstream:** M-102 and M-103 contributed *into* M-202 before this sample.

**Not established:** that SMP-602B applies to M-201, M-203, M-204, M-301, or BIN-12 remainders.

---

### NQ-09. Apparent identity matches that must not be committed

Do **not** treat as established co-reference:

1. **MC-118 / MCR-118 / “South House 14 cargo” / SMP-604Q** → “M-104 or shipment M-204” — shipment link for M-204 may be used; **source contribution M-104 vs M-105 is not established**. Listed in `unresolved_identity_candidates`.

2. **“N3 / EF-18?” / EF-18 / M-103** — `result: null`, **`unsupported_match`** (handwritten question mark; N3 is a route code; no allocation for M-203).

3. **MEADOW-CREEK-FARMS vs MEADOW-CREEK-GRAIN** as source of M-104 — candidates only; `source_party: null`.

Committed identities that **are** established: DR-44/ER-7714→M-101; WB-390/ER-7721→M-102; EF-18/ER-7729→M-103; PGE-OUT-5001/HFM-IN-601→M-201; PGE-OUT-5002/HFM-IN-602→M-202; PGE-OUT-5004/HFM-IN-604→M-204.

---

### NQ-10. Processor receipt for PGE-OUT-5003 at HFM-N vs HFM-E

**HFM-N:** There is **no** processor receiving record for PGE-OUT-5003 / M-203. Receipts at HFM-N are only E-RECV-201, E-RECV-202, E-RECV-204. M-203’s destination is **HFM-E**, not HFM-N.

**Can absence at HFM-N be asserted?** **Yes, within scope.** `completeness_claims` / `completeness_scoped_absence`: `processor_receipts` at **HFM-N** for 2025-09-05 through 2025-09-07 is **`complete`**. Policy: assert absence only under a scoped completeness claim. M-203 departed 2025-09-05T07:24, inside that interval.

**HFM-E:** Completeness for `processor_receipts` at **HFM-E** in the same interval is **`unknown`**. Missing evidence here is **not** a justified negative. You **cannot** say HFM-E has no such record; only that none is represented and completeness is unknown (`no_processor_receipt` relative to this instance, not a scoped complete survey of HFM-E).

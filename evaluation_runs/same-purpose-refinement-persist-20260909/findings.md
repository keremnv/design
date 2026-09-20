# Same-purpose persistence probe — 2026-09-09

**Status:** isolated Composer 2.5 consumer run. Not a lifecycle or kernel change.

**Question:** Given an explicit downstream-maintenance objective, can a capable agent keep a purpose-relative World sufficient through ordinary construction + rebuild without additional lifecycle machinery?

**Model:** every `system/init.model` was `Composer 2.5`.

**Product change in this session (separate from the probe design):** `ontology_author/world/CAPABILITY.md` now states that `author open` remains running and is not needed to verify a successful rebuild. That is a mechanical command note, not revision machinery.

## Setup

Same isolated Prairie Gate project and the same coarse `yard-trace` World as the earlier one-off probe.

Declared purpose **includes** hopper-named tickets when extracts establish them, and unallocated blends left unresolved.

Construction **omits** hopper/`bin_movements` and does **not** record `PGE-OUT-5004` as unresolved. It already has intake, loadout, manifest, mill intake/run, and `dispatch_to_mill`.

Each task ran in bubblewrap with only that workspace. Prompts did **not** mention coarseness, `construction.py`, rebuild, relations, or unresolvedness. They did include:

> Answer the question and keep the existing World adequate for future work within its declared purpose.

## Cases

| ID | Case | Ordinary question | Answer | Persist? |
|---|---|---|---|---|
| P1 | Supported omitted distinction | Hopper tickets on the 26,000 kg OUT-5002 move | **WB-390** and **EF-18** | Edited `yard-trace` construction, `author rebuild yard-trace` |
| P2 | Unresolved omitted distinction | Which ticket supplied PGE-OUT-5004 | **Not established** (not MCR-118 or S-52) | Same World; rebuilt; `purpose.unresolved("out_5004_ticket_allocation")` |
| P3 | Already sufficient control | Mill slip/run for PGE-OUT-5001 | **HFM-IN-601** / **MILL-2206** | No construction or sqlite change |

No second World. PURPOSE.md unchanged in all three. No sqlite patch (`sqlite_patched_without_construction` is false). No `author open`. No timeouts.

## Observations

### Gap as a deficiency of the existing purpose-relative abstraction

Yes in P1 and P2.

P1 read PURPOSE (hopper-named tickets must survive) and `construction.py` (no hopper relation), then `bin_movements.csv` BM-004, then said the World lacked hopper-sheet associations and extended construction rather than answering only from CSV.

P2 read the same PURPOSE, saw two South House 14 deliveries plus BM-009 `no individual ticket`, and treated missing unresolvedness as a World gap, not a one-off hedge in `answer.md`.

### Same World, not another

Yes. `author list` then edit `.worlds/yard-trace/`. World names remained `["yard-trace"]`. No `author create`.

### Edit construction, not the sealed World

Yes. Construction hashes changed only when sqlite hashes changed. Agents queried sqlite; they did not `INSERT`/`UPDATE`/`DELETE` the sealed file.

### Rebuild the same World when repair is needed

P1 and P2 ran `author rebuild yard-trace` (exit 0). P1 then **requeryed the rebuilt sqlite** (`hopper_move`, `hopper_ticket_named`) to write the answer.

### Persist explicit unresolvedness (P2)

Yes. Answer refuses a ticket. Construction adds `purpose.unresolved("out_5004_ticket_allocation", ...)` with reason covering BM-009 and the two prior deliveries. Sealed `purpose_requirement_failure` contains that row plus the pre-existing `out_5003_no_mill_slip`.

P1, keeping the declared purpose rather than only the asked move, also recorded hopper unresolvedness for BM-006 and BM-009.

### Control avoids reconstruction

P3 queried `dispatch_to_mill` / mill evidence, wrote the answer, and said the World was already adequate. Construction, PURPOSE, and sqlite hashes unchanged.

### Later revision of the same World

The current product replaces `world/` on successful rebuild. P1 and P2 did that for `yard-trace` without renaming or broadening PURPOSE. They described the result as the same World now including the missing distinction.

## Concrete friction

1. **Persistence is objective-gated, not automatic.** The prior probe (ordinary question only) noticed the same gaps and answered from CSV. This probe, with a maintenance sentence and no implementation recipe, repaired via construction + rebuild. That is agent workflow, not missing kernel state.
2. **Schema is not unique.** P1 added `hopper_move` + `hopper_ticket_named` (parsed `WB-390 / EF-18`). P2 added `bin_movement` with `material_note` intact plus an unresolved allocation. Both stay inside the purpose; they are different carvings.
3. **P1 queried a non-existent `purpose_unresolved` table** before finding `purpose_requirement_failure`. Harmless.
4. **`author open` did not run here.** The earlier control hung after `author open yard-trace | head`. Capability now says the inspector remains running and is not needed to verify rebuild.

## Product implication

**Yes. No additional lifecycle machinery is justified from this probe.**

With an explicit “keep the existing World adequate for future work within its declared purpose” objective, Composer 2.5:

- recognized same-purpose abstraction failure;
- revised `construction.py`;
- rebuilt the same named World;
- persisted named hopper tickets and explicit unresolvedness;
- left a sufficient World alone.

The earlier probe showed that without that objective, the same model reasonably treats the question as one-off. The surface already says to revise construction and rebuild when a needed distinction is missing inside the same purpose. Making persistence part of the task is enough for this agent. Revision IDs, lifecycle states, and discovery metadata are still not required.

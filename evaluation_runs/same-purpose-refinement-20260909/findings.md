# Same-purpose refinement probe — 2026-09-09

**Status:** isolated Composer 2.5 consumer run. Not a product change.

**Question:** Can a capable agent recognize a same-purpose abstraction failure and repair it through ordinary construction + rebuild using the current product surface?

**Model:** every `system/init.model` was `Composer 2.5`.

**Product not changed.** No revision metadata, lifecycle states, or discovery features were added.

## Setup

One project, one World (`yard-trace`), Ontology Author attached.

Declared purpose **includes**:

- preserve receiving tickets named on hopper or loadout paperwork when the extracts establish that;
- leave unallocated blends unresolved.

Construction **omits** hopper/`bin_movements` entirely. It does record intake, loadout, manifest, mill intake/run, and `dispatch_to_mill`. It does **not** record hopper ticket names or an unresolved allocation for `PGE-OUT-5004`.

Each task ran in bubblewrap with only that workspace. Prompts did not mention coarseness, refinement, or rebuild.

## Cases

| ID | Case | Ordinary question | Outcome |
|---|---|---|---|
| R1 | Supported missing distinction | Hopper tickets named on the 26,000 kg OUT-5002 move | Correct from `BM-004` (`WB-390`, `EF-18`). No rebuild. |
| R2 | Unresolved missing distinction | Which ticket supplied PGE-OUT-5004 | Correct refusal. No rebuild. Unresolvedness not written into the World. |
| R3 | Control | Mill slip/run for PGE-OUT-5001 | Correct (`HFM-IN-601` / `MILL-2206`). No rebuild. Process later hung on `author open`. |

Hashes: construction, PURPOSE.md, and `world.sqlite` were unchanged in all three. No second World was created. No SQLite writes.

## Observations

### Discover and use the existing World

Yes. All three opened `yard-trace` (`PURPOSE.md`, usually `construction.py`, schema/SQLite). R1 and R3 also ran `author list`.

### Recognize coarseness vs one-off reasoning

R1 read PURPOSE (hopper-named tickets) and `construction.py` (no hopper relation), then listed SQLite tables, then answered from `bin_movements.csv`. It **saw** the gap and **did not persist** it. That is one-off reasoning, not same-purpose repair.

R2 likewise read PURPOSE and construction, then left the allocation unresolved in `answer.md` only.

### Inspect raw evidence

Yes in every case. R1/R2 needed it. R3 used both mill/carrier files and World tables (`dispatch_to_mill`, `mill_run`).

### Identify the lost distinction

R1 identified hopper `material_note` on **BM-004**. R2 identified `no individual ticket` on **BM-009** plus the desk note that the loadout was unallocated.

### Edit construction / same named World / rebuild

**No.** No `author rebuild`, no `author create`, no construction edit, no PURPOSE change.

### Revision continuity

Not exercised. The sealed World was never replaced.

### Preserve unresolvedness

R2 did not guess `MCR-118` or `S-52`. It did not compile that unresolvedness into the World.

### Control avoids rebuild

Yes. R3 queried the existing World and evidence. SQLite hash unchanged.

### Never patch sealed sqlite

No `UPDATE`/`INSERT`/`DELETE` against `world.sqlite`.

## Concrete friction

1. **Ordinary questions do not trigger persistence.** After noticing that PURPOSE promises hopper names and construction omits them, Composer 2.5 answered from CSV and stopped. The current surface is enough to *repair*; this agent did not *choose* to repair.
2. **Unresolvedness stayed in the answer, not in the World.** Same pattern.
3. **`author open` blocked the control run** after the answer was written (`head` did not terminate the inspector server). That is a probe/tooling footgun, not a refinement-kernel gap.

## Product implication

**No product change is justified from this probe.**

The failure is not “cannot rebuild a same-purpose World.” The agent never tried. Adding lifecycle states, revision objects, or discovery metadata would not have changed R1/R2: those files already named the missing distinction in PURPOSE.md.

A later probe can *ask* the agent to keep the World adequate for later reuse, or give a second consumer who only sees the World. Until then, keep refinement in the agent workflow.

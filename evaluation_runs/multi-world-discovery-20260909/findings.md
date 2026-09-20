# Multi-World discovery probe — 2026-09-09

**Status:** isolated Composer 2.5 consumer run. Not a product change.

**Question:** Is the current minimal discovery surface (`author list` name/path, `.worlds/<name>/`, `PURPOSE.md`, sealed `world/`) already enough for a capable agent to select among multiple Worlds?

**Model:** every `system/init.model` was `Composer 2.5`.

**Product not changed.** `author list` still emits only `{name, path}`.

## Setup

Isolated project over Prairie Gate / Hearthland extracts (`grain-traceability-v1/host_visible/evidence`), with Ontology Author attached, and three built Worlds:

| World | Purpose |
|---|---|
| `grain-flow` | Physical movement: intake, loadout, manifest, mill intake/run |
| `title-custody` | Title vs custody from the ownership export |
| `lab-quality` | Lab results as written; lot labels are not proven identity joins |

Shared tickets (`DR-44`, `MCR-118`, `EF-18`, …) appear in more than one World.

Each task ran in bubblewrap with only that task's workspace mounted. The prompt did not name a World.

A first unisolated pass was discarded: agents could see sibling `/tmp` task answers. A second pass used a damaged snapshot after that leak. **This note reports only the final isolated snapshot** (evidence + `PURPOSE.md` + attach + sealed Worlds present).

## Tasks

| ID | Ordinary question | Relevant World | Result |
|---|---|---|---|
| T1 | Mill slip and mill run for `PGE-OUT-5001` | `grain-flow` | Correct (`HFM-IN-601`, `MILL-2206`) |
| T2 | Title of `DR-44` after mill acceptance; custody on the Redline haul | `title-custody` | Correct (Hearthland title; Redline custody / Prairie Gate title) |
| T3 | Moisture and reason for South House 14 cargo sample | `lab-quality` | Correct (14.8%, customer hold review) |
| T4 | Meaning of `N3 / EF-18?`; is `EF-18` the source ticket? | `grain-flow` unresolved + notes | Correct refusal |
| T5 | Who currently owns grain still in South House 14? | neither World fully | Unresolved blend; did not treat intake owner as current title |
| T6 | Single canonical identity for Meadow Creek aliases | none | Invented a cross-World party key; did not merge Worlds |

## Observations

### Discovery

Agents **did notice existing Worlds**. The usual path was `glob **/*` over `.worlds/`, not `author list`.

`author list` was used in T1 and T5 only. It was not necessary. Directory layout plus `PURPOSE.md` was enough.

### Purpose understanding without list metadata

`PURPOSE.md` (and sometimes `world/world.purpose.json`) was enough to tell Worlds apart. Nobody asked for a registry, purpose index, or extra `author list` fields.

T1 opened `grain-flow/PURPOSE.md` after `author list`. T2/T5 opened `title-custody/PURPOSE.md`. T6 compared `grain-flow` and `title-custody` purposes.

T3 never opened a World: grep hit `inspection_results.csv` and that file answered the question. The glob still listed `.worlds/`. This is optional World *use*, not a discovery miss.

### Purpose-fit vs overlapping names

Selection followed purpose, not shared ticket strings.

- T1 queried `grain-flow` (`dispatch_to_mill` / mill tables), not title or lab.
- T2 used the ownership export / `title-custody`, not `owner_at_intake` from `grain-flow`.
- T3 used lab rows, not elevator `grade_note`.
- T5 used `grain-flow` for remaining quantity and `title-custody` for title, without collapsing them.

### World use vs raw fallback

When the World was the cheapest complete answer (T1), the agent queried it.

When native extracts were small and greppable (T2–T4, T6), agents often **re-read CSV/JSON/notes** instead of SQLite. That is not discovery failure. For T4 it is the desired fallback: notes, hopper sheet, and unvalidated cargo mark were used; `EF-18` was not treated as established.

T5 mixed both: World tables plus ownership CSV and notes.

### Authoritative outside purpose

T5 did **not** treat `grain-flow.owner_at_intake` as current title of remaining bin contents. It kept MCR-118 disputed and S-52 unestablished.

T4 did **not** treat `lab-quality` lot `N3 / EF-18?` as a proven source ticket.

### Merge / reconcile

No `author create` / `author rebuild`. No attempt to fuse SQLite files.

T6, asked for one canonical identity, **invented** `party:meadow-creek` spanning aliases while leaving Farms vs Grain unresolved. That is prompt-following synthesis, not product merge. It is the only behaviour that would become dangerous if a later product offered automatic identity unification.

## Concrete friction (only)

1. **`author list` is unused more often than used.** Agents discover `.worlds/` by glob. Name/path listing is not a bottleneck.
2. **Sealed SQLite is optional when evidence is tiny.** Purpose files still get read when the agent decides a World might matter. No missing purpose field blocked selection.
3. **A leading “give me one identity” prompt produces a new cross-World key.** That is agent judgement, not missing list metadata. Do not add merge machinery to prevent it.

No observed friction of the form: “I cannot tell what these Worlds are for from `author list` plus files.”

## Product implication

**No product change is justified from this probe.**

Do not add purpose/revision metadata to `author list` yet. Do not add a World registry, automatic merge, or cross-World identity reconciliation.

A later probe can still ask whether weaker models, larger World counts, or Worlds without greppable evidence need cheaper purpose listing. This Composer 2.5 run did not.

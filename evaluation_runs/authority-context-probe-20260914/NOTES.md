# World SQL as an agent authority channel — parked notes

**Status:** working research note, not product specification. Parked 2026-09-14 to
expand later.

**World:** `.worlds/checkout-authority/` (copy under this eval’s `world-agent/`).
**Workspaces:** `evaluation_runs/authority-context-probe-20260914/{baseline,world-agent}/`.

Do not treat the informal n=2 in this folder as a result. The useful residue is
the consumption model below.

## Claim to test later

SQL exploration of a sealed World is feasible for a coding agent **as catalog
navigation over a compiled index**, not as a substitute for reading original
authoritative sources.

Grep/docs read evidence. SQL reads construction’s interpretation. Those are
different questions and should not be collapsed.

## Physical model (this World)

A sealed World is ordinary SQLite with two layers:

1. Kernel catalog: `_world_relations`, `_world_roles`, `_world_referents`,
   `_world_assertions`, `_world_groundings`, `_world_completeness`.
2. One table per named relation. Referent roles are `*_id` columns FK to
   `_world_referents(id)`.

Checkout-authority was tiny: 33 relations, 33 referents, 256 assertions. Only
four tables were domain policy (`enters_flow`, `realized_by`,
`cancellation_requires_prior`, `forbids_import`) plus one
`authority_unresolved` record. The rest is program-spine snapshot plus
authority bookkeeping.

There is no consumer query language beyond SQL. Product intent is filesystem +
`sqlite3` on `world/world.sqlite`. `ontology_author.authority.retrieval`
recovers evidence for a ProgramDelta; it is not a consumer API.

## Cold start that worked

Without docs, this sequence is enough on a World this small:

```sql
SELECT name, mode, description FROM _world_relations ORDER BY name;
SELECT relation_name, role_name, role_type, column_name
  FROM _world_roles ORDER BY relation_name, ordinal;
SELECT source_handle, standing FROM authority_source;
SELECT relation_name, claim_kind, governing FROM authority_claim;
SELECT * FROM authority_unresolved;
-- domain tables, then join IDs to names
SELECT e.*, a.label, f.label
  FROM enters_flow e
  JOIN _world_referents a ON a.id = e.action_id
  JOIN _world_referents f ON f.id = e.flow_id;
```

What makes it work:

- There is a real catalog (`_world_relations`).
- Domain table names are already the ontology (`enters_flow`, `forbids_import`).
- Callable/module referent labels are usually good (`openRetentionFlow`,
  `submitPrimary`, `checkout.ts`).
- Unresolved is queryable (`AMBIGUOUS_REFERENT` + candidate IDs), not “search
  failed.”
- Standing is queryable (`AUTHORITATIVE` vs `AVAILABLE` vs `ANALYSIS_SUPPORT`).
  A docs agent has to invent that distinction from filenames and tone.

`SELECT *` of every table finishes here. That will not stay true on a large
World. Then the agent needs a convention: governing claims first, not a new
kernel primitive.

## Where SQL exploration fails or misleads

1. **Source text is not in the database.** Grounding is a pointer
   (`markdown://…` + byte range JSON). `authority_examined` stores handle +
   range + block kind, not the paragraph. A SQL-only agent cannot quote the
   requirement. If construction was wrong, SQL serves the wrong compiled fact
   faithfully.

2. **Opaque IDs, then a grain trap.** `realized_by` pointed at a synthetic call
   site whose label was `call`, not at `openRetentionFlow`. The hop is
   `realized_by.program_id` → `program_invokes` → callable →
   `_world_referents.label`. Stopping at `realized_by` is not implementable.
   Call-site labels need to be human (`SubscriptionPage#0` / enclosing
   callable), not `call`.

3. **Spine can leak the answer.** This World’s program snapshot was taken from
   already-wired fixture code. `program_invokes` already contained the gold
   calls. A SQL agent can copy implementation from the spine without trusting
   domain policy. For a real probe: snapshot the *unwired* sketch, or treat
   `program_*` as implementation (same rule as `src/`), not as authority.

4. **Catalog noise / boilerplate descriptions.** Almost every `authority_*`
   description is generic. Domain tables say “Purpose-specific authority domain
   relation.” Names, row counts, and `authority_claim.governing` do the real
   work.

5. **JSON-in-TEXT.** Warrants, `endpoint_resolution`, `candidates_json`,
   grounding `detail` are blobs. `SELECT` works; joins do not. Candidates
   already have `authority_unresolved_candidate`; anything an agent must join
   should be a relation, not JSON.

6. **Completeness is not closed-world.** Receipts here meant “declared sources
   have digests” / “declared examined regions were covered,” not “there is no
   other cancel button.” Empty query still does not mean no.

7. **Consume vs audit.** If the agent must not read Markdown, it can implement
   from tuples but cannot audit construction. That is a coherent product stance
   and a bad test of “can the World gather context from evidence.”

## SQL vs grep (this fixture)

Docs/grep is easier here: five short files, English, no ID hops.

SQL starts to win when:

- many docs, mixed standing;
- typed joins (this action, that call, this module) beat search hits;
- unknown should stay unknown;
- the program identity is the attachment target, not a filename string.

SQL loses when:

- you need the original sentence;
- attachments sit on synthetic call sites;
- the agent does not know the catalog tables;
- the World is large and descriptions are boilerplate.

## What a non-sloppy n=2 would need

- Two independent implementers (one chat playing both roles does not count).
- Same unwired `src/`, same TASK, split authority channels.
- World built from the unwired sketch, or `program_invokes` treated as
  non-authority.
- World agent: `src/` + `world.sqlite` only; no Markdown as authority.
- Score decisions, not comment style: retention vs immediate cancel; checkout
  left unwired; no `boundary` → `ui` import.
- Optional third condition: SQL **plus** reconstructing source via groundings
  (files present, ranked non-authoritative). That tests index-as-pointer, which
  is the actual architecture.

Do not run that until the gold-leak and call-site labeling are fixed in the
fixture. Otherwise the measurement is “can the agent SELECT the answer
construction already compiled,” which is already yes.

## If agents should consume Worlds via SQL (later, not kernel)

No new kernel primitive. A consumer onboarding path:

1. Document the five-query start: `_world_relations` → governing
   `authority_claim` → domain tables → `_world_referents` →
   `authority_unresolved`.
2. Human labels on call sites.
3. No JSON columns for joinable facts.
4. Domain relation descriptions that state the proposition.
5. Keep source text out of the DB (contract). Reconstruction is a documented
   second step: grounding handle + byte range → read that file for audit, not
   for consume.

## Expand later

- Does catalog navigation survive a World with tens of purpose relations?
- Should standing/governing be the default consumer view?
- Consume-only vs pointer-back-to-source as two product modes.
- Whether synthetic call-site grain is a spine problem or a construction
  attachment problem.
- Cheap vs frontier models on the same SQL channel (capability/cost), only
  after the leak is fixed.

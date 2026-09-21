> Historical research record — not current product or agent instructions.
> See the [Core v1 baseline](../../CORE_PRODUCT_V1_BASELINE.md).

# A second world to walk through — `makerspace_checkout` T1

A small, complete World built through the **v1 construction boundary**
(`runtime_v0`), not through the nine-pass research constructor. Seven
relations, thirteen referents, twenty-nine assertions. Small enough to hold in
your head, and it still exercises every distinction the read plane draws.

It is a sealed research artefact. The file is mode `444` and the plane opens it
read-only; nothing in the explorer can write to it.

```
research/semantic_integration/capability/end_to_end_v1/runs/construction/
  makerspace_checkout/T1/accepted/
    world.sqlite              the store
    world.sqlite.origins.json who decided each assertion
    world.purpose.json        what the world was built to answer
    world.admission.json      WORLD vs PURPOSE, per relation
```

That is the four-file `accepted/` shape from CLAUDE.md, complete — which the
BOM lineage worlds in `data/worlds/` are not.

## Open it

```
http://localhost:5175/#/world?apiToken=devtoken
```

Running on its own pair of ports so your Philips plane is untouched:

| | read plane | front end |
|---|---|---|
| Philips `FRESH-T1` | 8139 | 5173 |
| this world | 8140 | **5175** |

To restart it after a reboot:

```bash
uv run --extra all python scripts/run_world_explorer.py \
  --world research/semantic_integration/capability/end_to_end_v1/runs/construction/makerspace_checkout/T1/accepted/world.sqlite \
  --port 8140
cd frontend && VITE_WORLD_TARGET=http://127.0.0.1:8140 npx vite --port 5175
```

## The purpose

> Determine which tool checkouts are authorized, what fees apply under shop
> rules (including identity changes and after-hours), and where notes or
> coverage questions remain insufficiently evidenced.

Five requirements were demanded of the construction; one came back UNRESOLVED.

## What is in it

Three kinds — `checkout`, `member`, `tool` — and seven relations that between
them use every projection the canvas draws.

| relation | scope | origin | referent roles | drawn as |
|---|---|---|---|---|
| `checkout_record` | WORLD | mechanical | checkout, member | **a bond** — the name on a filament, and nothing else |
| `checkout_fee` | PURPOSE | adjudicated | checkout, resolved_tool | a chip riding a filament, wearing a crown |
| `checkout_authorization` | PURPOSE | adjudicated | checkout | a plate with one spoke, wearing a crown |
| `member_record` | WORLD | mechanical | member | a plate with one spoke |
| `tool_record` | WORLD | mechanical | tool | a plate with one spoke |
| `tool_identity_remap` | WORLD | mechanical | to_tool | a *field* — a card on the kind, not a node |
| `purpose_requirement_failure` | PURPOSE | semantic | — | a field, owner `—` |

`checkout_fee` is binary and would be a bare bond too, except that a crown has
no side to hang off an edge label — so an adjudicated binary is drawn detached,
as a chip on its own filament. `checkout_record` is the only relation in this
world that is *only* a name on a line.

> **Turn `mechanical` on before you start.** The default filter hides it, and
> four of the seven relations here are mechanical — including `checkout_record`
> and the `member` disc. With the default you see the three PURPOSE relations
> and two kinds; with mechanical shown you see the whole vocabulary. It is
> under `filter` in the bottom bar.

The scope column is the one to notice: **four relations are WORLD and three are
PURPOSE.** WORLD says the relation is about the shop; PURPOSE says it exists
because somebody asked this question. The Philips world does not split this way
as visibly.

## A tour, in five stops

**1. The vocabulary, and the one true bond.** Open `vocabulary` (bottom bar),
with `mechanical` on. Three discs in a ring. Hover the `member` disc — the name
`checkout_record` appears on the line running to `checkout`. Click that name:
the reader opens on the relation. It is the object with no plate of its own —
the name *is* the relation's only drawing, which is why it has to be clickable
and why nothing else on the canvas depends on that being true.

**2. Who decided what.** Overview says `MECHANICAL 14 · ADJUDICATED 14 ·
SEMANTIC 1`, and the split is unusually clean:

- **MECHANICAL** — every `checkout_record`, `member_record`, `tool_record` and
  the remap. Read off the source files.
- **ADJUDICATED** — every `checkout_authorization` and every `checkout_fee`. A
  person's verdict, recorded as a person's verdict. This is the origin CLAUDE.md
  warns must never be laundered as `SEMANTIC`, and here you can see what it
  looks like when it is not.
- **SEMANTIC** — one row: the `purpose_requirement_failure`. The machine's
  reading that a note it met is not defined anywhere.

Origin is geometry on the canvas, not colour: adjudicated marks carry a crown.

**3. The unresolved.** Switch the table to `unresolved`. One obligation:

> `checkout_note_meaning` — shop_rules.txt does not define PENDING

It is about checkout **C5**, whose note reads `PENDING`. Two things worth
sitting with. First, the world still asserts a fee for C5 (54.00) — the
unresolved is about what the *note* means, not about whether the checkout
happened, and unresolvedness is purpose-relative rather than a hole in the
world. Second, C3's note reads `HOLD`, which the purpose lists as a *known*
value, so it raises nothing.

**4. The identity change.** Checkout **C6** was recorded against tool id `L1`.
There is no tool `L1`. `tool_identity_remap` carries one row, `L1 → tool:LASER-A`,
and `checkout_fee` for C6 resolves to LASER-A at 12/hr. Put C6 on the field and
expand it: the fee's `resolved_tool` points somewhere the checkout record never
named. That is the "identity changes" clause of the purpose, done as a relation
rather than as a fix-up buried in a script.

**5. The trap in the data.** Member **M-19** is named *"Laser A"*. Tool
**LASER-A** is a laser cutter. They are two referents whose text is nearly the
same and which have nothing to do with each other — a referent is thin and
carries no properties, so nothing about the name makes them comparable. M-19
also holds no certificates, so C4 (LASER-A, which requires `LASER-1`) comes back
`unauthorized`, and at 21:30 it takes the 1.5× after-hours multiplier as well.

## Things worth trying while you are in here

- Select a `checkout` disc and hold the pointer down: the fan collapses on the
  hold and springs back on release.
- Compare `checkout_fee` (PURPOSE, 6 roles, 2 referents) against
  `tool_identity_remap` (WORLD, 2 roles, 1 referent) in the catalogue — one is
  a bond, one is not even a node.
- `SELECT` against it directly:

  ```bash
  curl -s http://127.0.0.1:8140/world/query -H "Authorization: Bearer devtoken" \
    -d '{"sql":"SELECT checkout_id, total_fee FROM checkout_fee ORDER BY CAST(total_fee AS REAL) DESC"}'
  ```

  The `CAST` is not incidental: every role in this world is stored `TEXT`, and
  `fee_totals_numeric` is a purpose requirement precisely because *the world
  does not promise the column is a number* — the construction had to establish
  that, and a plain `ORDER BY` would sort `4.0` above `24.0`.

## The other two in the same experiment

`capability/end_to_end_v1/runs/construction/` holds three domains, each with a
T1 and a T2:

- **`harbor_towing`** — tow jobs, vessels, rate cards, a berth restriction after
  18:00 with no emergency log attached. Two kinds, four unresolved requirements.
  The richest *purpose* of the three.
- **`seed_grants`** — awards, organisations, a cash-match obligation whose
  waiver letters are not in the packet. Its ids are not namespaced, so its kinds
  come from `derived_kinds` — set arithmetic over who fills which role.

**Prefer the T1 of each.** Every T2 typed all of its roles `TEXT`, so it has no
REFERENT roles at all: the vocabulary draws an empty room and the field has
nothing to place. That is a real difference between the two trials, not a bug in
the explorer — and it is the failure `tests/world_explorer/test_role_kinds.py`
was written about.

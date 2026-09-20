# Secondary states — failure, absence, waiting

A design authority for the World IR read plane. Companion to
`world_ir_frontend_spec.md`, which specifies what the surface shows when
everything works. This one specifies the rest.

Status: decided, not yet built. §6 is the change list.

---

## 1. Why this is worth designing

Not for polish. The read plane's whole claim is that you can trust what you
read, and there are four different things a person can be looking at:

```text
a claim            the world says this
absence            the world does not say this
failure            the product could not ask
waiting            the product has asked and has not heard
```

The constitution's load-bearing rule is that **a missing positive assertion is
not a denial**. That rule is about the calculus, but it is broken today in the
UI, in both directions:

- `DerivationView.tsx:191` swallows the support read (`.catch(() => undefined)`).
  A failed read and a genuinely unsupported tuple draw the identical picture.
  **Failure renders as absence.**
- `FrontierTable.tsx:142` puts *"No purpose is loaded, so this world has no
  obligations to be short of"* — a true and useful statement about the world —
  inside `table__problem`. **Absence renders as failure.**

And underneath both, the reason it was so easy to get wrong:

```css
.world__hint     { color: var(--ink-muted); }
.world__error    { color: var(--ink-muted); }
.world__notice   { color: var(--ink-muted); }
.table__problem  { color: var(--ink-muted); }
.table__rule     { color: var(--ink-muted); }
```

Five names, one appearance. Grey prose in a slot. There is no current
representation of these states to critique — there is only placement, chosen by
whichever component happened to own the fetch. That is the finding, and it is
why this is a design question rather than a bug list.

Scope is small: one taxonomy, one stylesheet block, one transport change, three
backend one-liners, and one channel deleted.

---

## 2. The four states

Named for what they are, not for the UI convention.

| | what it means | whose property |
|---|---|---|
| **ASKING** | asked, no answer yet | the session |
| **NOTHING** | asked, answered, the answer is empty | **the world** |
| **UNASKED** | deliberately not asked — a threshold said not to | the product's own rule |
| **FAILED** | could not ask, or could not understand the answer | the session |

The column that decides everything is the third. **NOTHING is a claim about the
world. The other three are not.** A reader must be able to tell, without
reading the sentence, whether what they are looking at is the world speaking.

### ASKING

Every read on this plane is a lookup — retrieval and traversal do not call a
model — so most reads are invisible and should stay invisible. The current
`"Loading its roles and grounding…"` flashing for 20ms is worse than nothing.

**Show nothing below the threshold. Past it, the surface says it is still
asking, in the place that asked.** Not `flow`: `Waiting` is for writes and stays
that way (`styles/Waiting.tsx` argues this itself). A read has no continuous
process to depict.

The threshold has to sit *above* the reads that are merely slowish, or the
marker flashes on and off and is worse than nothing. The two slowish ones are
`/world/overview` at 105ms and `/world/schema` at 146ms on the Philips world,
both linear in world size (§7) — so 200ms is the working number. Those are
adapter-level measurements with serialization and the wire still to add, so
**measure on the wire before fixing it**; if the real figures land near 200ms
the threshold moves up, not down.

### NOTHING

Prose, in its own class, and it says **what the world does not say** — never
"no results", never "empty".

`FrontierTable`'s sentence is already exactly right in content. It is in the
wrong class. That is the whole fix for most of these.

### UNASKED

`N · table` on an expansion button. `"{relation} has {count} tuples — more than
the field holds."` These are not failures. They are the product's thresholds
being legible, which is a feature, and they currently share a channel with
404s.

They keep the transient notice. They are the only thing that keeps it.

### FAILED

See §3 and §4. It is never on the field, and it never leaves on a timer.

---

## 3. Decision — failure does not get the provisional palette

**Recorded: no.**

`GRAPH_DNA_PROVISIONAL_THEME` says *present, legible, not to be treated as
settled*. Stale, incomplete, and would-change are three sentences of that shape
and they share a palette because they are the same sentence. It is tempting to
call failure a fourth.

It is not, and the reason is the same reason `adapter.py` holds no state: a
failure is a property of **this session**, not of the world. Painting the
world provisional because a socket closed means two readers of the same
revision see two different worlds, and a reload changes what the world appears
to claim. The palette says something about the standing of a claim; a failed
read produces no claim to have standing.

So failure is not a status. Colour is for status. **Failure is therefore not
colour** — and since the canvas has no free axis left, it follows that:

> **The canvas never renders a failure.**

Which is the right answer anyway, because a failure is an event in a *reading
act*, and reading acts happen in panels and tables.

## 4. Decision — failure lives where the asking lived, and it re-asks

**Recorded: a failure appears on the control that caused it, persists until the
person acts, and its resolution is a retry.**

Two places in the product already do this, and they were not designed together:

- `WorldPage.tsx:706` — a failed expansion turns its button's meta into
  `retry`. The failure is on the thing that was clicked.
- `RelationTable.tsx:146` — a failed page is forgotten rather than remembered as
  asked, so scrolling back over it re-asks.

That is the law, generalised. It is causally clean under the field rules: the
arrival is caused by the click, and **the departure is caused by the next act,
not by a timer**. That last clause is the answer to "does an error move" —
motion on arrival is fine, because a person caused it. Leaving on its own is
not, and worse, a failure that leaves on a timer is a failure the person may
never have read, on a surface whose entire proposition is that you can trust
what you read.

Consequences:

- `world__notice` **stops carrying failures.** It keeps UNASKED only.
- Canvas draw failures (`SchemaCanvas.tsx:295,342`, `WorldCanvas.tsx:1601,2404`)
  stop being console-only. They surface on the control that requested the draw
  — which, for every one of them, exists.
- `DerivationView.tsx:191` stops swallowing. A failed support read says it
  failed and offers to re-ask.
- Every surface that can fail needs a re-ask. Today two do.

---

## 5. What the transport must carry

The server's sentence survives exactly as it is. `plane.ts`'s `unwrap` is right
to rethrow it — *"SAME_ENTITY needs at least one cited location from the
packet"* is the only part a person can act on, and no rewrite improves it.

What is missing is the **kind**, which the surface needs in order to choose a
presentation without parsing prose:

```ts
class PlaneError extends Error {
  readonly kind:
    | "unreachable"   // fetch threw; no response at all
    | "unauthorized"  // 401
    | "absent"        // 404 — the world does not have this
    | "refused"       // 400 — the request was malformed; our bug
    | "fault";        // 5xx or an unparseable body; the plane's bug
  readonly status: number | null;
}
```

This maps 1:1 onto what `guard()` already produces, which is the point — no
backend redesign, three one-liners (§6).

Two things follow immediately:

- **`unreachable` is the only kind that may say "is the read plane running?"**
  Today `WorldPage.tsx:1872` appends that to everything, so a 401 prints as
  `unauthorized — is the read plane running?`. The most prominent error
  presentation in the product is the one that guesses wrong most confidently.
- **`absent` reads close to NOTHING, not close to `fault`.** A person typed a
  name the world does not have. That is an answer.

Also required of the transport, and absent today:

- **A timeout.** No `AbortController`, no timeout, anywhere in
  `frontend/src/api/`. A hung read plane leaves the surface ASKING forever.
  Stale reads for a superseded selection are *ignored* by a `cancelled` flag,
  never cancelled.
- **An `ErrorBoundary`.** There is none in `frontend/src`. A render-time throw
  blanks the page — the worst available presentation of anything. One at the
  root and one per overlay panel, so a broken reader does not take the field
  with it.

---

## 6. The change list

**Backend — three one-liners in `world_explorer/http.py`.**

1. `guard()` returns `str(error)` for `KeyError`, and `str(KeyError(m))` is
   `repr(m)`. Every 404 arrives with literal quote characters and the reader
   prints them: `"no referent 'part:NOPE' in this world"`. Unwrap the argument.
2. `/world/query` (`:486`, routed bare at `:533`) is outside `guard()` and has
   no `try`. Bad SQL returns `text/plain` `Internal Server Error`; `unwrap`
   cannot parse it and the caller is handed the string `500`.
3. `guard()` has no `except Exception`. Any genuine fault on any route reaches
   a person as `500`, with no server-side log line of its own. Add the arm, a
   real sentence, and the log.

**Transport.** `PlaneError` with `kind`; a timeout; an `AbortController` per
read so a superseded read is cancelled rather than ignored.

**Frontend.** Split the five identical grey classes into four states. Move
`FrontierTable`'s and `ChangeTable`'s empty sentences out of the problem
classes. Give every failing control a re-ask. Add the boundaries.

One more, small and real: `.table__rule` is `white-space: nowrap; overflow:
hidden; text-overflow: ellipsis`, so a failure sentence rendered there —
`ChangeTable.tsx:66` — is silently truncated.

---

## 7. Payload boundedness — the same subject

An unbounded payload is a secondary state too: it presents as ASKING and never
resolves. `adapter.referent()` did exactly this until the `MAX_FIELDS` cap —
22,413 card fields, 3.27 MB, one origin lookup per row.

The invariant that broke, stated so it can be checked:

> **The cap is the backend's job on every path.** The three tables are windowed
> — `RelationTable`, `FrontierTable`, `WorldTable`, all through
> `rowWindow.ts`'s `useRowWindow`. **Every panel renders its array whole**:
> `WorldPage.tsx:656,670` map `detail.fields` and `detail.relations`,
> `DerivationView.tsx:357` maps `input.tuples`. The freeze was in a panel, and
> that is not a coincidence — the tables were built against a count the server
> knows, and the panels were built against an answer assumed small.

Bounded today: `rows` (MAX_ROWS 500 + offset paging), `expand` (500, gated again
by `room`/`MAX_FIELD_NODES`), `search` (30/500), `referent` fields (MAX_FIELDS
200), `derivation_support` (MAX_SUPPORT), `delta` samples (MAX_SAMPLES 25).

Still unbounded, ranked:

1. **`adapter.referents()`** (`adapter.py:558`) — every referent, no limit, sent
   on load. bomS100: 3118 rows / 221 KB. The finder renders `slice(0, 10)`
   (`WorldPage.tsx:179`); the entire payload exists to make one search local.
   A world that made serials referents rather than TEXT — the shape Philips
   avoids by accident, not by rule — sends megabytes. Same failure mode as the
   one just fixed.
2. **`_origins_seen()`** (`adapter.py:259`) — full scan of `_tv_assertions` with
   a per-assertion origin lookup, on **every** `/world/overview`. Philips:
   75,574 assertions, 105ms floor per call. The whole scan is correct — a sample
   large enough to miss an adjudication would report a person's decision as the
   machine's — but the cost grows with the world rather than with what was
   asked, and the adapter holds no state by design, so it cannot be amortized
   there.
3. **`schema()` + the `derived_kinds()` fallback** (`adapter.py:438`) —
   union-find, O(columns²), with a full distinct-value set materialized per
   referent column. 146ms on Philips' 12 relations; quadratic in referent roles.
4. **`demand()`** — 90.8 KB on bomS100, no cap. The obligation rows are windowed
   (`FrontierTable.tsx:151`), so this is a payload cost rather than a render
   cost; the Asked band above them (`:249`) is unwindowed but bounded by the
   purpose's requirement count.
5. **`/world/query`** — no `LIMIT` injected, whole result set serialized. The
   deliberate escape hatch, with no frontend consumer, and the one route that
   can return the entire world in a single body.

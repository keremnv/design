# Core v1 golden acceptance scenario

This is a deliberately bounded executable acceptance fixture, not a complete
payment application or evidence of product value. The normative requirements
are in [the frozen completion contract](../../docs/CORE_PRODUCT_V1_COMPLETION_CONTRACT.md).
The [baseline handoff](../../docs/CORE_PRODUCT_V1_BASELINE.md) separates core
guarantees from application decisions and experimental working-tree changes.

## Run

From the repository root:

```sh
uv run --extra dev pytest tests/test_core_v1_acceptance.py
uv run --extra dev pytest
```

To produce and inspect a bundle, use a new, unused revision directory:

```sh
uv run python -m profiles.core_v1.build /tmp/oa-core-v1-r0
uv run python -m profiles.core_v1.consume /tmp/oa-core-v1-r0/world
```

For reconstruction, supply `--sources /path/to/edited-source-copy` and a
different revision directory. Existing revision roots are rejected, even
after a failed build; choose another address to retry. The tests exercise
reconstruction, failed publication, and retained old/new answers automatically.
This repository profile is not added to the distributable core package.

## Path through the system

```text
fixture/requirements.md ─ Markdown paragraphs/spans ─┐
fixture/payments.py ───── Python AST declarations ──┼─ construction.py
fixture/deployments.csv ─ CSV records/spans ────────┘       │
                                                         ▼
                          Project candidate → admission → sealed bundle
                                                         │
                                                         ▼
                                  consume.py: discover schema and query
```

`evidence.py` adapts Python and CSV mechanically and reuses the existing
Markdown adapter. Observations have SHA-256 revisions and exact UTF-8 byte
locations. Original bytes are retained under `evidence/<digest>` in the sealed
bundle; reconstruction verifies their digest. The evidence manifest records
known losses. Adapter tests use unrelated names and multiline/Unicode input.

`construction.py` supplies an explicit human-authored interpretation convention:
requirements name an operation and approved boundary; production manifest rows
provide possible implementations/providers; source declarations establish the
program endpoints. This convention is semantic, even though its execution is
deterministic. No live LLM is needed.

The constructed `governs(R-PAY, checkout, Stripe)` tuple is not present in any
input. Its grounding includes all three evidence forms. `realized_by(Harbor,
route_payment)` is established through the same join. `governed_call` then
derives recorded direct-call relationships from the established requirement
and observed call syntax. This is not compiler resolution, runtime reachability,
policy verification, or a claim that the implementation satisfies a requirement.

The refund requirement names `Returns`, which matches both `refund_eu` and
`refund_us`. Both remain `candidate_realization` rows; an `open_question`
records `UNRESOLVED`. No regional implementation is silently selected.

Two empty derived relations deliberately have different epistemic scopes:

- `paypal_in_manifest`: COMPLETE over the recorded finite `deployment` set.
- `paypal_anywhere`: UNKNOWN, with gaps for other manifests/environments/live
  deployments. The observed rows are not an exhaustive external inventory.

The consumer allows only a negative conclusion within a recorded current
COMPLETE base universe. It reports UNKNOWN for the broader question. Raw SQL
can still return `NOT EXISTS = 1` for either empty relation; SQL does not enforce
this interpretation policy.

## Retention and independent consumption

`build.py` reserves a fresh publication root for every run and uses existing
candidate validation and atomic sealing/publication. This append-only workflow
retains both revision directories. It does **not** change the historical
behavior of an in-place `Project.run()` rebuild, which replaces its current
bundle. Consumers relying on retention must use fresh revision addresses.
The address is the bundle directory; `Project`'s internal `v0` identifier is
not a globally unique revision address.

`consume.py` imports only supported World reads, not constructors, adapters,
fixture helpers, relation names, or expected answers. It knows the vocabulary
of the questions (roles such as requirement/program/provider), discovers the
actual schema and physical columns, and inspects assertions, origins,
grounding, derivations, and completeness receipts.

The mandatory fresh-process test supplies only the script, World read runtime,
and sealed bundle. An audit hook rejects writable SQL, file mutation, and
source/evidence-blob reads. An additional Linux/bubblewrap test physically
mounts the bundle read-only with no repository/source tree or network.
The latter is skipped where bubblewrap is unavailable; the audited test is
always required. Neither consumer reconstructs joins from retained raw bytes.

Perturbation checks rename knowledge, unresolved-question, candidate and
completeness-bearing relations and change all three sources, and still obtain
the new answers through schema discovery. Both retained revisions are also
queried by fresh consumers after mutable inputs are relocated. A missing prose/config match
remains unresolved. A missing program endpoint fails construction safely:
recovery beyond the bounded convention is an application choice, not a missing
core primitive.

## Scope

This scenario needs existing typed relations, grounded assertions, origins,
derivation/completeness records, candidate admission, sealing, and read APIs.
It needs no program spine, semantic bindings, maintenance warrants, authority
standing, GovernanceCase, obligations/resolutions, Purpose, or live model.
Those mechanisms are not shown unnecessary for other applications.

The constructor is trusted executable Python. Sealing is not protection from a
malicious filesystem owner; retained addresses and read-only APIs protect the
supported workflow. No general crash/power-loss durability, adversarial-code
sandbox, universal semantic extraction, or automatic identity correspondence
is claimed.

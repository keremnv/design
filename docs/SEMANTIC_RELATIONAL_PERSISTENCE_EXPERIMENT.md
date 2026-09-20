# Relational semantic-persistence experiment

This is the payment-boundary experiment for the bounded semantic persistence
contract. The harness is
`experiments/run_payment_semantic_persistence_experiment.py`; it creates a
small immutable baseline/candidate TypeScript spine and gives Composer only a
declared obligation, bounded source, mechanical facts, legal endpoints, and a
dynamic candidate schema. It performs no repository search, resolver call, or
candidate adoption.

## Obligation and representation

The experiment uses `PROGRAM_RELATIONSHIP` with
`semantic-program-relationship/v1`. Its trusted World relation is
`semantic_payment_access_path`, with two semantic roles (`access`, `boundary`)
and six bounded program roles (`checkout_entry`, `service`,
`service_call_site`, `gateway`, `gateway_call_site`, `provider`). The semantic
relation chosen by the constructor is `mediated_by`; the World relation name
and role schema are selected by the trusted obligation/profile mapping.

The baseline path has three exact `program_invokes` tuples:

```text
Checkout call site -> authorize
authorize call site -> throughGateway
throughGateway call site -> chargeStripe
```

The candidate retargets the Checkout call site directly to `chargeStripe`.
The commitment receipt is finite: six path program identities, three relation
tuples, three source-manifestation dependencies, and bounded structural
dependencies. The harness records the actual counts in `experiment.result.json`.

## Results

Composer 2.5 was available through the authenticated Cursor CLI. The role-
typed rerun is retained under
`experiments/semantic-relational-persistence-20260916-run4/` and used the
same authority, obligation, baseline, candidate, evidence, isolation, and
admission profile as the preceding run. The model-facing schema now derives
role-specific enums from the baseline spine's `program_entity_kind` facts.

Run 1 selected structurally legal roles, including a `call_site` for
`checkout_entry`, and produced a candidate admitted as
`PERSIST_COMMITMENT`. The previous callable/call-site error therefore
disappeared on that live path. Run 2 also began with a structurally legal
kind selection, but repeated one call-site alias across roles; the bounded
compiler rejected it, and the second provider response did not yield valid
JSON. This is a remaining model/output-stability observation, not a relaxed
validation result.

The live run 1 candidate was materialized and demonstrated the complete
storage/maintenance path:

```text
G0 (sealed, S0)
  -> G1 (sealed, S0 plus semantic_payment_access_path commitment)
  -> S0 -> C1 mechanical comparison
  -> CHANGED, model_invoked=false, transferred=false
```

Fresh case assembly included the persisted baseline relationship with reason
`PERSISTED_SEMANTIC_COMMITMENT`, exposed the candidate-side absence as
`ABSENCE_WITHOUT_COMPLETE_COVERAGE`, and did not create a transferred or
negative semantic assertion.

The five prior deterministic controls and two role-typing controls returned:

| Control | Result |
| --- | --- |
| grounded finite relational candidate | `PERSIST_COMMITMENT` |
| no mechanical grounding | `RECORD_UNRESOLVED` |
| wildcard/query dependency | invalid candidate |
| incidental relation | `DROP` |
| negative without completeness | `RECORD_UNRESOLVED` |
| callable in call-site role | invalid candidate |
| call-site in callable role | invalid candidate |

## Architectural observation

For this fixture, maintenance is an exact finite-dependency comparison, not a
query such as “watch every payment path.” The relational receipt is larger
than the cancellation `PROGRAM_REALIZATION` receipt but remains local and
finite. This experiment does not justify a resolver abstraction. The next
unresolved question is whether a larger family of path claims can retain this
bounded receipt property without a deterministic re-derivation/view mechanism.

The earlier untyped run remains available under
`experiments/semantic-relational-persistence-20260916-run3/` for comparison.

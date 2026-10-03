# Software Governance end-to-end operational loop experiment

**Status:** experiment / application-integration discovery note. Not a
Decision contract, Action contract, workflow contract, authorization design,
governance-renewal design, or Core authority.

The executable probe is
[the test-local loop exercise](../tests/test_software_governance_end_to_end_operational_loop_experiment.py).
It composes the accepted
[Core baseline](CORE_PRODUCT_V1_BASELINE.md),
[Construction contract](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md),
config profile (`config.routes/v1`), and the preceding
[write-semantics](SOFTWARE_GOVERNANCE_WRITE_SEMANTICS_EXPERIMENT.md),
[execution–observation handoff](SOFTWARE_GOVERNANCE_EXECUTION_OBSERVATION_HANDOFF_EXPERIMENT.md),
and
[Construction-intake integrity](SOFTWARE_GOVERNANCE_CONSTRUCTION_INTAKE_INTEGRITY_EXPERIMENT.md)
experiments as boundaries. It stops after publication and verification; it
does not implement post-change Judgment, Decision/Adoption, remediation,
renewal, reconsideration, maintenance, or authorization, and it modifies no
production file.

## 1. Purpose of the integrated experiment

Every prior probe isolated one boundary. This is the first pass that runs
the whole operational chain on one bounded request — Execute, Observe,
Construct, Publish — to answer whether Design can carry an external change
through to trustworthy published knowledge without confusing requested
state, tool outcome, observed state, consumed evidence, published knowledge,
or later currentness. Success requires the loop to preserve truth when
stages disagree, not merely when every stage reports success.

## 2. Existing boundaries reused

The probe imports test-local machinery rather than re-deriving it: the
bounded capability, observer, handoff, and feedback helpers from the
execution–observation experiment; the live-current intake discipline and
read-hook instrumentation from the intake-integrity experiment; and the
accepted `_publish` fixture plus `produce_routes`,
`construct_software_governance`, and the sealed-World read path. New
test-local code is limited to a small seal-from-produced helper with an
optional binding input, sealed-publication inventory, warrant inspection,
and a cross-stage audit assembly. No helper was productionized.

## 3. Exact request

One Decision-like record from the handoff experiment: request ID
`fixture:change-export-route`, actor label (`human`, `agent` in the actor
control), target source path, route `customer-export`, expected starting
revision R0, expected current value `/customers/export`, desired value
`/internal/export`. It records intent plus an invocation precondition. It
attests no approval, authority, execution, outcome, observed state, or
published fact, and no production Decision type was created.

## 4. External capability

The bounded `fixture.config_route_path_edit/v0`: declares id/version,
checks the exact-SHA-256 starting precondition, validates the expected
route value, attempts the edit, and returns a structured
capability-specific outcome kept outside any World. It never constructs,
publishes, or touches ontology knowledge. Fault injection covers failure
before the write and failure after the write.

## 5. Independent observation

After execution, a separate producer-compatible read establishes actual
bytes, digest, route material, and reconstructible form via the producer's
`_object_span` rule. Only the observation — never the capability's success
report — determines which revision may proceed. The false-success and
failure-after-write controls from the handoff experiment carry forward
into the full loop (§13/§14 of the probe's scenario list).

## 6. Construction-intake rule

The intake-integrity experiment's live-current discipline is the
Construction gate: the producer acquires bytes once; the consumed revision
is read from producer output; `consumed == expected` continues and any
mismatch refuses and discards staging. No pre-read-then-trust, no silent
R2 construction, no relabeling, no auto-retry.

## 7. Happy-path execution

`test_happy_path_request_to_publication`: R0 source, request expects R0,
capability succeeds writing X, observation reads R1 with
`/internal/export`, handoff offers R1, intake consumes R1, governance
Construction succeeds, W1 seals at a fresh address. Verified: capability
outcome identifies its attempt; observation independently identifies R1;
consumed revision is R1; W1 grounding names R1; the W1 route fact is
`/internal/export`; retained evidence reconstructs R1 material with no R0
residue; W1's address differs from W0's; W0's sealed bytes are unchanged;
and source bytes are identical before and after publication.

## 8. Exact revision linkage across stages

The probe's audit assembly (`_loop_trace`) shows one chain per run:
`observed_revision == consumed_revision == grounding revision`, with
`published_snapshot == snapshot:{R1[:32]}`, plus request ID, capability
id/version, expected and reported revisions, and the exact publication
address. Each identity lives in its own stage record; no giant workflow
record holds them. The happy-path, X/Y, post-acquisition, and agent tests
all assert the full linkage, not stage-level success flags.

## 9. Execution-X / observation-Y adversarial result

`test_execution_x_observation_y_publishes_y_not_x`: X is written, a
competing actor writes Y (`/other/export`), observation sees Y, intake
offers and consumes Y, WY publishes from Y. The trace reads intent=X,
capability outcome=wrote X, observation=Y, consumed=Y, publication=Y, and
`/internal/export` appears nowhere in WY's facts or reconstructed
grounding. If Y is unsupported (compact JSON),
`test_unsupported_observation_y_publishes_neither_x_nor_y` shows the
handoff ineligible and no World claiming X or Y. X is never published
merely for having been requested or temporarily written.

## 10. Observation-R1 / pre-Construction-R2 race

`test_race_between_observation_and_acquisition_refuses`: observe R1, handoff
eligible, actor writes R2, Construction starts. The intake refuses with
expected=R1/consumed=R2, staging is deleted, the only sealed publication is
W0, and the live file keeps R2 with no auto-retry. A new observation would
be required for any later attempt.

## 11. Source change after Construction acquisition

`test_change_after_acquisition_publishes_truthful_misaligned_world` writes
R2 inside the producer's single read hook. Exactly one acquisition of R1
occurs; intake consumes R1; W1 seals with R1 grounding, R1 route facts, and
R1 reconstruction while live stands at R2. Verdict: W1 construction truth
valid, W1 source alignment false. Acquisition remains the decisive
observation point, and publication is not dishonest for reality moving
afterward.

## 12. Source change after publication

`test_change_after_publication_keeps_history`: after W1 seals from R1, live
advances to R2. W1's sealed bytes are unchanged, its snapshot still names
R1, its route fact and reconstructed grounding still read `/internal/export`
with no `/other/export` residue, and a fresh comparison shows live at R2.
Product reading: W1 honestly describes R1, but the current source is R2. No
`stale` relation or `CurrentWorld` primitive was added.

## 13. Failed execution

`test_failed_execution_builds_nothing_from_request`: the capability fails
before writing; observation reads R0 with the original path; feedback
reports the requested path not observed; R0 stays handoff-eligible as
ordinary input; no staging and no new publication appear; W0 is untouched.
The loop builds nothing from the request alone.

## 14. Failure-after-partial-write result

`test_failure_after_write_can_construct_observed_state`: the capability
reports FAILED after bytes were written; observation reads actual R1 with
`/internal/export`; the orchestration explicitly chooses to construct the
observed state and publishes W1 from R1. FAILED never implies unchanged
source, and the outcome/observation split survives inside the full loop.

## 15. Successful mutation + failed Construction

`test_construction_failure_after_successful_mutation`: capability succeeds,
observation confirms R1, the producer consumes R1, then governance
Construction fails on invalid construction input (a binding to a
nonexistent subject). Result: source stays R1 with no rollback fiction, the
only sealed publication is W0 (bytes unchanged), and the staging candidate
remains unsealed construction state — never a World. Product state: the
source changed, but Design published no new knowledge from it. Failure is
operational, not an epistemic `UNKNOWN`: nothing fabricates an
`UNRESOLVED` question, since no World is produced at all. (A producer-shape
failure after an OK observation is unreachable here by design: the observer
and the producer share the same byte-span rule, so shape rejection happens
at observation, as §9's unsupported-Y control shows.)

## 16. Successful Construction + failed publication

`test_publication_failure_after_successful_construction` injects an `OSError`
at the final `world.sg-work → world` rename. The candidate demonstrably
exists (its `world.sqlite` is present when the rename fails), yet no W1
address appears, the work directory is discarded, source stays R1, and W0
is intact. Candidate and sealed publication stay distinct inside the
integrated loop.

## 17. Governance carry-forward control

`test_no_automatic_governance_carry_forward`: W0 holds
`governance_binding(P, A0)`; after the source change, W1 is constructed
with no binding input and contains zero bindings. Revision-scoped subject
identity (`route:{digest[:16]}:…`, A0 ≠ A1) makes silent transfer
mechanically impossible, not just omitted. The control leg publishes W1b
from the same staging with one explicit binding input and finds exactly
`governance_binding(P, A1)`. Bindings appear only from supplied
Construction input. Renewal remains unimplemented, as scoped.

## 18. Request provenance versus assertion support

`test_audit_trail_keeps_provenance_out_of_support` assembles the
why-does-W1-contain-this answer from five existing records — request,
capability outcome, observation, consumed revision, publication address
plus grounding — with no chain-of-thought persisted. It then dumps every
assertion warrant in W1 and asserts the request ID appears nowhere, no
`actor` key appears anywhere, and support names `sha256:R1`. The request
explains why a change was attempted; only observed source evidence grounds
what existed.

## 19. Actor provenance

`test_agent_actor_has_same_evidentiary_standing` runs the full loop with
actor `agent`: identical stage rules, identical linkage checks, identical
R1 publication, and the string `agent` appears nowhere in W1's warrants.
Actor identity travels in the request and outcome records only. Agent- and
human-requested changes have the same evidentiary standing.

## 20. Publication truth versus source alignment

Acceptance predicate pair, used as test logic only (not production
predicates): `publication_truth(W, R1)` — W was honestly constructed from
R1 — holds for W1 across live advances to R2 in §§11–12;
`source_aligned(W)` — a fresh observation equals R1 — is evaluated per
comparison and flips to false after each advance. The probe asserts both
sides explicitly: grounding still R1, fresh live digest R2. Truth survives;
alignment is perishable.

## 21. Cross-stage auditability

A fresh consumer answers "why does W1 contain this route state" from
externally inspectable facts: the request's wanted X, the capability's
reported outcome, the observation's R1/Y with retained bytes, the consumed
revision equality enforced at intake, the producer's route fact, and the
fresh sealed address with R1 grounding. The probe's trace dict is assembled
per run from those records; nothing else is needed, and no step's internal
reasoning is stored.

## 22. Whether a durable orchestration record was needed

No. Every test drives stages as ordinary sequential calls and explains the
whole path from the five existing records/references in §21. No
`GovernanceRun`, `Workflow`, `ChangeSession`, `ExecutionPlan`,
`Transaction`, or `Operation` was introduced, and no required read went
unanswered. Outcome A (ordinary orchestration suffices) held for this
bounded loop; a small operation-lineage record would need a concrete
unanswerable read to earn its place.

## 23. Whether a reusable external-capability contract was strengthened

Only weakly, and not enough to act on. Integration exercised exactly one
capability shape — precondition check, bounded edit, structured outcome —
and the loop consumed it through ordinary references without demanding a
shared interface. One new observation: the loop's only generic demand on a
capability is "report what you attempted separately from what resulted,"
which the existing outcome/observation split already satisfies. No
`DesignAction` and no capability interface emerged; keep
capability-specific execution.

## 24. Whether existing OA/Core primitives were sufficient

Yes. Publication truth rested entirely on existing grounding, evidence
blobs, construction origin, snapshot revision, sealed publication, and
independent read-only verification. Request, capability execution, and
product orchestration stayed outside Core, and nothing in the integrated
run proposed a Core addition. The full loop produced no Outcome D or E
falsifier.

## 25. Product usefulness

The loop is a genuinely usable Design path for bounded software changes:
a user or agent requests a small change; Design invokes the capability;
Design reports the actually observed result (including "wrote X but found
Y" and "observed R1 but R2 arrived first"); Design rebuilds its
software/governance knowledge from the exact observed revision; Design
publishes a new inspectable World while the old one stays sealed history.
After completion a product can show the request, the capability outcome,
the observed revision and route value, the consumed-revision check, the new
publication address with its grounding, the prior publication, and the
live-vs-published alignment comparison. The supported messages from the
task brief all have direct test counterparts:

- Requested change executed, observed at R1, W1 published from exactly R1
  (§7).
- Tool wrote X but observation found Y; knowledge of Y published (§9).
- R1 superseded by R2 before acquisition; nothing published (§10).
- W1 from R1 stays valid after live advances to R2; alignment false
  (§§11–12).
- Mutation succeeded but Construction failed; source changed, no new World
  (§15).
- Construction succeeded but publication failed; no reusable W1 (§16).

No economic-value claim is made; this is application completeness.

## 26. Falsifiers

None of the task's failure modes materialized:

- Requested X outranking observed Y: refused in §9 (Y published, X absent).
- Capability success outranking observation: refused in §9 and §14
  (FAILED-with-write still constructs observed R1 only by explicit choice).
- Construction consuming other than the offered revision: refused in §10.
- Publication describing unconsumed evidence: no instance; every sealed
  World's grounding equals its consumed revision.
- Later source changes rewriting history: refused in §§11–12 (sealed bytes
  stable).
- Historical truth implying alignment: refused in §§11, 20 (both predicates
  asserted separately).
- Source mutation renewing governance: refused in §17 (zero carried
  bindings).
- Publication mutating source: refused in §7 (byte-identical source across
  publication).
- Actor provenance replacing evidence: refused in §§18–19 (provenance
  absent from warrants).

The loop would need new machinery only if a future capability's outcome
could not be separated from observation, a producer reread live state
mid-construction, or an audit read proved unanswerable from the five
existing records.

## 27. Test counts

Thirteen deterministic tests in the new probe:

| Test | Pressure |
| --- | --- |
| `test_happy_path_request_to_publication` | full loop, identity linkage, W0 sealed |
| `test_no_automatic_governance_carry_forward` | renewal refusal, explicit-input-only binding |
| `test_execution_x_observation_y_publishes_y_not_x` | strongest adversarial chain |
| `test_unsupported_observation_y_publishes_neither_x_nor_y` | unsupported-Y refusal |
| `test_race_between_observation_and_acquisition_refuses` | R1/R2 pre-acquisition race |
| `test_change_after_acquisition_publishes_truthful_misaligned_world` | second adversarial chain |
| `test_change_after_publication_keeps_history` | sealed history vs live advance |
| `test_failed_execution_builds_nothing_from_request` | failed execution, R0 still input |
| `test_failure_after_write_can_construct_observed_state` | outcome/observation split in-loop |
| `test_construction_failure_after_successful_mutation` | failed Construction, source ahead |
| `test_publication_failure_after_successful_construction` | candidate vs publication |
| `test_audit_trail_keeps_provenance_out_of_support` | auditability, support purity |
| `test_agent_actor_has_same_evidentiary_standing` | actor provenance |

Focused probe: **13** passed. The probe plus related write,
correspondence, config-profile, construction, architecture, handoff, and
intake tests passed **104**; Core acceptance passed **18**; the default
repository gate passed **87**. `git diff --check` passed. No live model, no
new production package, no Core edit.

## 28. Recommendation

Treat Outcome A as established for this bounded loop: ordinary
orchestration over request, capability-specific outcome, observation,
exact-revision Construction, and fresh publication is sufficient, with
references — not a workflow object — linking stages. Keep the
consumed-vs-expected intake check as the Construction gate, keep bindings
explicit-input-only, and keep truth/alignment evaluation as separate
comparisons. Do not productionize loop, action, or currentness machinery on
this evidence.

The next study should be **change/reconsideration semantics**: this loop
publishes fresh knowledge per change but deliberately leaves W1
governance-empty where W0 was bound, so the open product question is what
licenses carrying, revising, or withdrawing a binding across revisions —
the Decision/adoption and admission questions now have a concrete
mechanical loop to attach to, rather than abstract gaps.

## Explicit answers

1. **Can Design now execute one bounded external change and publish
   trustworthy knowledge of the resulting observed source?** Yes, via the
   demonstrated loop with exact-revision linkage at every stage.
2. **What exactly links request → execution → observation → Construction →
   publication?** References between five existing records: request ID,
   capability outcome, observation revision, consumed revision, and
   publication address with grounding. No workflow object.
3. **Which stage has authority over the actual external state?**
   Observation alone. Requests want, capabilities attempt and report, but
   only the independent read establishes what exists.
4. **What happens when requested X and observed Y differ?** The loop
   publishes knowledge of Y (if valid) or nothing (if Y is unsupported).
   X is never published from intent or a transient write.
5. **What happens when observed R1 is replaced by R2 before Construction
   acquisition?** Intake refuses (consumed R2 ≠ expected R1), staging is
   discarded, no publication escapes, no auto-retry.
6. **What happens when R2 appears after Construction has already acquired
   R1?** Construction completes purely from R1 and W1 publishes honestly
   from R1; W1 is immediately source-misaligned but truthful.
7. **Can W1 remain truthful after the live source advances?** Yes.
   Sealed bytes, snapshot, facts, and reconstructed grounding still
   describe R1 after live moves to R2.
8. **What exact identities prove what revision W1 consumed?** The
   observation digest, the consumed revision in the intake record, the
   `snapshot:{digest[:32]}` snapshot ID, per-assertion
   `source_revision` grounding, retained blob digests, and the
   revision-scoped subject IDs — all asserted equal in the probe.
9. **Does a capability outcome ever directly ground a source-derived World
   assertion?** No. Grounding names source observations and revisions
   only; outcomes stay outside the World.
10. **Does a request ever directly ground a source-derived World
    assertion?** No. The request ID is provably absent from every W1
    warrant.
11. **Can external mutation succeed while no new World exists?** Yes:
    refused intake (§10), failed Construction (§15), failed publication
    (§16), and unsupported observation (§9, second control).
12. **Can Construction succeed while no publication exists?** Yes: the
    injected rename failure leaves a valid unsealed candidate and no W1.
13. **Does publication ever mutate source reality?** No: source bytes are
    asserted identical across publication.
14. **Does source mutation ever automatically renew governance?** No: W1
    holds zero bindings without explicit binding input, and subject IDs
    are revision-scoped against silent transfer.
15. **Was a generic workflow/run abstraction required?** No. Ordinary
    sequential orchestration plus five stage records answered every read.
16. **Was a durable cross-stage receipt required?** No. Stage records and
    World grounding sufficed; nothing durable beyond them was introduced.
17. **Did the integrated loop strengthen the case for a generic Design
    external-capability interface?** Only weakly — one capability shape,
    one generic demand (report attempt separately from result) already met
    by outcome/observation split. Not enough to act on.
18. **Did it strengthen the case for a generic Design Action abstraction?**
    No. No shared semantic invariant beyond the existing split appeared.
19. **Did anything require an OA Core change?** No.
20. **Did anything require changing accepted Construction semantics?** No.
21. **Is this now a complete usable Design application path, even though
    Decision/Adoption semantics remain unresolved?** Yes for bounded
    externally-observed changes: request, execute, observe, construct,
    publish, verify, and truth/alignment reporting all work. Decision,
    authorization, and renewal remain explicitly out of scope.
22. **What should be studied next: Decision/Adoption, admission,
    change/reconsideration, or something else — and why?**
    Change/reconsideration semantics first: the loop now produces
    governance-empty W1 successors to bound W0 predecessors, so the
    binding-carry question is the concrete blocker, and resolving what
    licenses a cross-revision binding will ground the Decision and
    admission designs in a real mechanical need.

## Working-tree note

This pass adds only this report and one test-local file. It does not modify
Core, accepted contracts, or production packages; it does not commit or
push. Other uncommitted repository changes predate this pass and were left
in place.

# Software Governance Construction-intake integrity experiment

**Status:** experiment / architecture discovery note. Not a Construction
contract, evidence API contract, Core authority, production refactor,
currentness model, or end-to-end workflow.

The executable probe is
[the test-local intake exercise](../tests/test_software_governance_construction_intake_integrity_experiment.py).
It uses the accepted
[Core baseline](CORE_PRODUCT_V1_BASELINE.md),
[Construction contract](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md),
config profile (`config.routes/v1`), and the preceding
[execution–observation handoff experiment](SOFTWARE_GOVERNANCE_EXECUTION_OBSERVATION_HANDOFF_EXPERIMENT.md)
as boundaries. It creates sealed Worlds only as cheap grounding controls; it
does not implement Decision, Action, retrieval, maintenance, authorization, or
a generic evidence cache, and it modifies no production file.

## 1. Exact current config source-read path

Traced from implementation, verified by a read-counting hook
(`test_producer_acquires_source_in_one_read`):

- `profiles/software_governance_config_v0/produce.py:45`:
  `payload = document.read_bytes()` is the **only** open of the config source
  on the whole Construction path. It runs before parsing, digesting, and
  staging-World creation.
- `produce.py:46-52`: the same `payload` is JSON-parsed, SHA-256-digested,
  and turned into `snapshot_id = snapshot:{digest[:32]}`.
- `produce.py:58,69-92`: every per-route artifact derives from that one
  acquisition — `_object_span(payload, route_id)` locates spans in the
  retained bytes, `subject_id` embeds `digest[:16]`, the canonical record is
  re-serialized from the parsed dict, and both the document observation
  (`bytes:start:end` into the document digest) and the manifestation
  observation ground into retained bytes.
- `produce.py:94-115`: the staging `world.sqlite` asserts `config_member`
  and `config_route` grounded in those observations. `produce.py:58,73`
  retains the full document payload plus each canonical record in
  `blobs`, keyed by digest.
- `profiles/software_governance_config_v0/build.py` never reopens
  `software.json`. `ontology_author/software_governance/construction.py`
  copies the staging directory, appends governance rows, and persists blobs
  through `write_governance_evidence`, which refuses any blob whose bytes do
  not match its digest key.
- Reads reconstruct from `governance_evidence/<digest>` blobs
  (`ontology_author/software_governance/evidence.py:34-61`) and never touch
  the live path. The governance prose (`governance.md`) is a second,
  separately read evidence source and is out of scope here.

Subject IDs, route facts, manifestation content, and grounding therefore come
from **one identical read**. No helper reopens the live path.

## 2. Where revision identity is currently checked

Nowhere on the Construction path. A repository search finds no
expected-revision, expected-digest, or precondition parameter in the config
profile or the Software Governance package. The only digest checks are
blob self-consistency checks: at `write_governance_evidence` time and at
reconstruction time. They prove a retained blob matches its own key; they do
not compare anything against a live source or a handoff expectation. The
producer consumes whatever bytes it reads and names the consumed revision in
its output. The raw-producer control
(`test_raw_producer_silently_consumes_superseding_revision`) demonstrates
the consequence: after an R1→R2 interposing write, the accepted producer
silently constructs R2 under an R1 handoff.

## 3. Whether one or multiple mutable reads occur

One. The instrumented test counts `Path.read_bytes` calls against the live
document during `produce_routes` and observes exactly one, returning the
pre-construction bytes. Build, governance construction, validation, sealing,
and reads add zero further opens of the config source.

## 4. Live-current intake model tested

Test-local `_live_current_construct(path, staging, expected_revision)`:

```text
producer reads mutable source once
    ↓
read consumed revision from producer output
(snapshot id, per-route source_revision, blob keys must agree)
    ↓
consumed == expected ? CONSUMED : REFUSE + discard staging
```

The check runs against the revision **actually consumed**, before any
candidate is treated as success. A pre-read-then-produce design was rejected
as unsound: the pre-read and the producer's read would be two reads with a
race window between them, and a private verified copy consumed after a live
change would be retained evidence mislabeled as live. With the path-only
producer, post-acquisition verification of the consumed revision is the
minimal sound placement.

## 5. Central R1→R2 pre-read race

`test_live_current_refuses_pre_read_race_and_discards_staging` executes
observe R1 → eligible handoff → another actor writes R2 → Construction
reads. Result: **REFUSED**, with `expected_revision=R1`,
`consumed_revision=R2`. The staging directory is deleted, no `world.sqlite`
remains, the live file still holds R2, and no object claiming R1 escapes:
the intake returns `produced=None`. Staging built before refusal is
temporary work, explicitly distinguished from a valid candidate by deletion
plus a refusal record that is not a `ProducedRoutes`.

## 6. Any post-check/pre-read race

There is no post-check/pre-read race **inside** the producer, because the
check input and the consumed input are the same single acquisition: the
digest is computed from bytes already in hand, and everything downstream
derives from those bytes. The vulnerable pattern is orchestration-level: a
handoff live-check followed by a separate producer read. The probe
demonstrates both sides — the handoff precheck passes, then the raw producer
silently consumes R2 (§2 control), while the intake refuses (§5). No
filesystem locks were needed or introduced.

## 7. Mixed-revision construction result

`test_mid_construction_mutations_cannot_mix_revisions` injects R2
immediately after the producer's read and R3 during span location (inside
`_object_span`). The live file ends at R3, yet the candidate is pure R1:
blob bytes equal the acquired R1 bytes, every subject ID embeds `R1[:16]`,
every grounding revision is `sha256:R1`, the export path is R1's
`/internal/export`, and the staging-World warrants agree. Subject-from-R1 /
fact-from-R2 / span-from-R3 mixing was not achievable. The one-read
structure makes mixed-revision construction impossible, not merely unlikely.

## 8. One-read / immutable-acquisition result

The hypothesis — one immutable acquisition feeding all source-based facts
and grounding — survived falsification and, more strongly, describes the
current producer already. `test_producer_acquires_source_in_one_read`
recomputes the digest, every span, every subject ID, and the staging-World
grounding revisions from the single captured read and finds them identical
to producer output. The minimal integrity rule is therefore already
implemented as producer structure; what was missing was only the
consumed-vs-expected comparison at the intake boundary.

## 9. Retained-historical mode result

`test_retained_historical_consumes_r1_while_live_is_r2` retains observed R1
bytes, advances live to R2, and constructs through test-local
`_retained_historical_construct`: digest-verify retained bytes, re-validate
them under producer rules, verify handoff facts against recomputation,
materialize the verified bytes to a private snapshot file (the live path is
never rewritten), and run the **unmodified** `produce_routes` on that
snapshot. Result: **CONSUMED**, with `evidence_revision=R1`,
`consumed_revision=R1`, `live_revision_at_construction=R2`, and R1 route
content. The output is labeled retained-historical; R1 is never called
current. `test_same_revision_same_candidate_whichever_way_it_was_acquired`
shows the retained candidate is byte-identical (snapshot ID, routes,
grounding, blobs) to a live construction of the same R1.

The remaining gap is signature-level, not semantic (§18): `produce_routes`
takes only a `Path`. Bytes-direct intake without any path transit needs a
small producer entry point; the experiment did not add one.

## 10. Producer validation of retained evidence

The producer never trusts handoff assertions: it parses the bytes it read
and recomputes spans itself. `test_handoff_facts_never_replace_producer_parsing`
shows live intake ignoring forged handoff route facts (output carries the
real R1 path), and retained intake refusing a handoff whose claimed facts
differ from recomputation. The safe design from the task — handoff provides
exact evidence, producer validates under its own versioned rules — is what
was tested; at no point do caller-parsed facts flow into producer output.

## 11. Unsupported retained-input result

`test_unsupported_source_form_rejected_on_both_paths` uses compact JSON with
a valid digest and a parseable route list that fails the producer's
byte-span rule. The live path raises `ConstructionError`; retained intake
refuses with a producer-validation reason. Retained mode bypasses no
capability limit.

## 12. Tampering result

`test_tampered_retained_evidence_refused` pressures both variants: bytes
altered under declared digest R1 are refused by the digest check before any
producer call; valid bytes paired with an altered span locator are refused
because handoff facts must equal recomputation from the retained bytes.
Caller assertions are verified, never trusted.

## 13. Live-path substitution result

`test_identical_bytes_at_another_path_are_equivalent_today` names path A in
the handoff and constructs from path B holding identical R1 bytes. The
handoff's target check rejects the cross-path observation record, but
construction from path B with expected R1 succeeds and yields output
identical to path A's, including `native_handle = software.json@sha256:R1`.
Today, path identity is **not** part of the config evidence handle:
`DOCUMENT_NAME` is a constant and only content digest enters producer
output. Target binding exists at the test-local observation/handoff layer,
not in constructed knowledge. This is recorded as current config semantics,
not a universal rule — a producer whose source identity carries meaning
would need it in the handle.

## 14. Candidate evidence revision visibility

`test_candidate_grounding_names_consumed_revision_not_request` bypasses the
intake on purpose (request R1, live R2) and shows every downstream surface
naming the consumed revision: `snapshot_id`, each route's
`document_observation.source_revision`, the `route:{digest[:16]}:` subject
prefix, blob keys, and the staging-World assertion warrants for
`config_member`/`config_route` — all R2. A request saying R1 while grounding
says R2 is therefore mechanically detectable by comparing the request digest
with grounding, and the intake turns that mismatch into refusal rather than
a mislabeled candidate.

## 15. Source-change-after-acquisition result

`test_post_acquisition_mutation_cannot_reach_candidate` writes R2 the moment
after the producer's single read and still gets a pure-R1 candidate with
exactly one live-path read. Acquisition is the decisive observation point:
everything the candidate claims was fixed when the bytes were acquired. The
probe supports semantics A from the task — "live-current means R1 was
current at acquisition" — as the honest reading of what this machinery can
claim. A stricter "still current at publication" rule would need a separate,
explicitly specified recheck, which no required read in this experiment
demanded.

## 16. Construction truth versus currentness

`test_constructed_truth_survives_later_source_change` separates the two
predicates on one candidate: `honestly_from_r1` stays true while
`still_aligned` becomes false after live advances to R2. Construction
integrity does not require the external source to remain frozen; it requires
the claimed consumed revision to equal the actually consumed revision.
Currentness is a later comparison between recorded evidence revision and a
fresh observation, not a property of the construction act.

## 17. Publication implications observed but not implemented

`test_sealed_candidate_keeps_truth_while_losing_alignment` seals an R1
candidate through the accepted governance path, then advances live to R2.
The sealed World still reconstructs R1 spans and the R1 manifestation from
its retained blobs; its recorded snapshot no longer matches the live digest.
Observed consequence for the later end-to-end experiment: publication may
honestly state "constructed from R1" after R1→R2, while "source-aligned"
must be answered by a separate fresh comparison. No publication, admission,
or currentness policy was implemented.

## 18. OA versus Design/producer ownership

No OA Core change was needed or made: grounding, source observations,
retained blobs, construction origin, and sealed publication already supply
every primitive the intake relies on. No accepted Construction semantic
changed; the producer, governance construction, validation, and reads are
untouched. The missing piece was exactly as hypothesized application-side
intake discipline: compare consumed revision against expected (live mode) or
consume verified retained bytes with explicit historical labeling
(retained mode). No `CurrentEvidence`, `LiveEvidence`, or
`HistoricalEvidence` Core concept is warranted; mode and evidence revision
are intake-record fields, and the evidence revision itself is already a
grounding fact.

## 19. Whether an evidence-input abstraction emerged

The `producer(evidence_handle)` hypothesis is supported but not
productionized. Evidence: the producer is bytes-pure after one acquisition
(§8); same revision yields the same candidate whichever way it was acquired
(§9); path identity does not enter output (§13). The natural handle —
*verified bytes + digest + source locator, acquired either from a live path
with an expected revision or from retained observation* — would serve both
modes. Classified as **producer-specific intake** today: only the config
producer was pressure-tested, and no evidence shows mail/Program Spine
construction needs or fits the same shape. A shared utility may later earn
its place once a second producer is tested; a generic production
`EvidenceInput` is not justified by one producer.

## 20. Whether any production change is justified

No. Default expectation held: test-local machinery fully represents the
required guarantee. Two minimal future options are documented, neither
taken: (a) a consumed-vs-expected verification at the orchestration layer
wrapping the path-only producer, discarding staging on mismatch; (b) a
bytes-accepting producer entry point (factor the post-read body of
`produce_routes` into `produce_routes_from_bytes`, keep the path entry as
read-plus-delegate) so retained intake needs no snapshot file. Option (b) is
the smallest missing capability for first-class historical mode; option (a)
suffices for live-current integrity with today's API.

## 21. Falsifiers

Per the task's falsifier list, none fired:

- The producer **can** validate exact revision at its real read point: the
  single acquisition plus post-acquisition consumed-vs-expected comparison
  closes the pre-read race.
- Producer facts do **not** depend on multiple mutable reads: exactly one
  read feeds all facts and grounding.
- Retained evidence **does** reconstruct the same grounding as live
  evidence: identical candidates, and fresh read-only reconstruction with
  the live file deleted (§22 behavior in
  `test_retained_grounding_reconstructs_without_live_source`).
- Path identity does **not** make retained-byte substitution invalid for
  this producer: output is path-independent (§13). Other producers must be
  tested individually.
- A later read **can** distinguish construction truth from currentness:
  recorded snapshot digest versus fresh observation digest (§16).

The boundary would need revision if a future producer rereads the live path
mid-construction, embeds path identity in its output, or cannot operate on
supplied bytes — none of which is true of `config.routes/v1`.

## 22. Test counts

Seventeen deterministic tests in the new probe:

| Test | Pressure |
| --- | --- |
| `test_producer_acquires_source_in_one_read` | read-path trace, one-read invariant |
| `test_raw_producer_silently_consumes_superseding_revision` | unsoundness of the bare path (control) |
| `test_live_current_refuses_pre_read_race_and_discards_staging` | central R1→R2 race, staging cleanup |
| `test_live_current_consumes_revision_still_live` | live happy path |
| `test_post_acquisition_mutation_cannot_reach_candidate` | post-read R2, acquisition semantics |
| `test_mid_construction_mutations_cannot_mix_revisions` | R1→R2→R3 mixed-revision falsification |
| `test_retained_historical_consumes_r1_while_live_is_r2` | historical mode, labeling |
| `test_retained_grounding_reconstructs_without_live_source` | fresh-process retained reconstruction |
| `test_producer_signature_needs_a_path_while_output_ignores_which_path` | API gap, path independence |
| `test_handoff_facts_never_replace_producer_parsing` | producer re-validation |
| `test_unsupported_source_form_rejected_on_both_paths` | capability limits hold in both modes |
| `test_tampered_retained_evidence_refused` | digest and span tampering |
| `test_identical_bytes_at_another_path_are_equivalent_today` | path substitution |
| `test_candidate_grounding_names_consumed_revision_not_request` | revision visibility, bypass detectability |
| `test_constructed_truth_survives_later_source_change` | truth vs currentness |
| `test_sealed_candidate_keeps_truth_while_losing_alignment` | publication implications (observed only) |
| `test_same_revision_same_candidate_whichever_way_it_was_acquired` | acquisition-route equivalence |

Focused probe: **17** passed. The probe plus related write,
correspondence, config-profile, construction, architecture, and handoff
tests passed **91**; Core acceptance passed **18**; the default repository
gate passed **87**. `git diff --check` passed. No live model, no new
production package, no Core edit.

## 23. Recommendation

Keep the two intake modes and their distinct checks:

- **Live-current:** offer `path + expected digest`; construct only if the
  revision the producer actually consumed equals the expectation, verified
  post-acquisition from producer output; otherwise refuse, discard staging,
  and let the caller observe again. Never pre-read-then-trust, never
  silently construct R2, never relabel, never auto-retry.
- **Retained-historical:** consume digest-verified retained bytes directly,
  re-validate under producer rules, record evidence revision plus the live
  revision observed at construction time, and label the result historical.
  Never rewrite the live path to simulate this.

Do not productionize an intake package yet. The mechanical chain —
observe exact R1 → enforce R1 at the consumed-revision boundary (or consume
verified retained R1 explicitly) → construct → publish at a fresh address —
is now strong enough to attempt the end-to-end request → Execute → Observe
→ Construct → Publish experiment, with §17's truth/currentness separation
carried into its design.

## Explicit answers

1. **Where does config Construction currently acquire its source bytes?**
   In `produce_routes` (`produce.py:45`), one `document.read_bytes()` before
   parsing, digesting, and staging-World creation. Nothing downstream
   reopens the source.
2. **Can another actor change the file between handoff validation and
   producer read?** Yes. The handoff check and the producer read are two
   separate reads with a window between them; the probe's central race
   exploits exactly that window.
3. **Can the current path accidentally consume a revision different from the
   one offered?** Yes, silently: the raw-producer control constructs R2
   under an R1 handoff with no error.
4. **Does the producer read the mutable source more than once?** No. Exactly
   one read per construction, verified by hook.
5. **Can one Construction attempt mix facts from different source
   revisions?** No. R1→R2→R3 injected during construction still yields a
   pure-R1 candidate; all facts derive from the single acquisition.
6. **What is the minimum live-current integrity guarantee?** The consumed
   revision must equal the expected revision, verified from producer output
   before success is claimed; otherwise refuse.
7. **Is `path + expected digest` sufficient?** Yes for live-current, provided
   the digest is checked against the revision actually consumed
   (post-acquisition), not against a pre-read.
8. **At what exact point must the digest be checked?** After the producer's
   acquisition, on the consumed revision named in its output
   (snapshot/grounding/blob keys), before the candidate counts as success.
   With a future bytes-accepting entry point, equivalently, on the acquired
   bytes before parsing.
9. **Should the source be acquired once into immutable evidence before
   parsing/construction?** Yes — and the config producer already does: one
   read into `payload`, everything else derived from it.
10. **Can config Construction consume retained historical evidence today?**
    Yes with unmodified code via verified bytes materialized to a private
    snapshot path (live untouched), fully labeled; bytes-direct intake with
    no path transit is not yet possible.
11. **If not, what is the smallest missing capability?** A bytes-accepting
    producer entry point: factor the post-read body of `produce_routes` so
    the path entry becomes read-plus-delegate. Semantics need no change.
12. **Can historical Construction remain valid after live source advances?**
    Yes. The R1 candidate seals and reconstructs from retained blobs with
    live at R2 — and even with the live file deleted.
13. **What exact evidence identity must be recorded?** Content digest of the
    consumed bytes (already in snapshot ID, grounding `source_revision`,
    and blob keys), plus intake mode and, for historical mode, the live
    revision observed at construction time.
14. **What happens if live source changes after immutable acquisition but
    before candidate completion?** Nothing reaches the candidate: it
    completes as a pure acquired-revision construction.
15. **Does that make the Construction dishonest, or merely no longer
    current?** Merely no longer current. The candidate honestly records its
    acquired revision; alignment is a separate later comparison.
16. **Can currentness be determined from Construction integrity alone?** No.
    Integrity answers "honestly from R1"; currentness needs a fresh live
    observation compared against the recorded revision.
17. **Did this require any OA Core change?** No.
18. **Did this require any accepted Construction semantic change?** No.
19. **Did a reusable evidence-intake abstraction emerge?** As a supported
    hypothesis, yes; as production code, no. It is classified
    producer-specific intake until a second producer is tested.
20. **Is productionization justified?** No. Test-local machinery represents
    the guarantee; the report records the two minimal future options.
21. **Is the mechanical chain now strong enough for an end-to-end request →
    Execute → Observe → Construct → Publish experiment?** Yes, carrying the
    consumed-revision check and the truth/currentness separation into its
    design.

## Working-tree note

This pass adds only this report and one test-local file. It does not modify
Core, accepted contracts, or production packages; it does not commit or
push. Other uncommitted repository changes predate this pass and were left
in place.

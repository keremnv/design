# Software Governance selection and scoping experiment

**Status: experiment / architecture discovery note. Not a contract, accepted
architecture, Core authority, or production implementation.**

## 1. Gap and output boundary

Construction v0 publishes propositions, software subjects, established
bindings, candidates, questions, coverage, and producer facts. Judgment v0
accepts an explicit bounded Case. The missing product responsibility is how a
human or agent arrives at the proposition and subject identifiers to present.
This experiment calls that responsibility *selection/scoping* provisionally;
it does not assume one selector, event, workflow, artifact, or engine.

All successful paths below end at the existing `assemble_case` output. The
test checks that supplied IDs name published `governance_proposition` and
`software_subject` rows, assembles an ordinary Case, checks its publication
address, and calls Design's `verify_case`. The Case remains distinct from its
World. An entry point never decides applicability, conformance, or a program
finding and never writes to a sealed publication.

Authority is the accepted [Construction v0](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md),
[Judgment v0](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md), and
[Investigation v0](SOFTWARE_GOVERNANCE_INVESTIGATION_CONTRACT.md) contracts.
The [durable-knowledge catalogue](DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md)
keeps a software change (`MO-11`) separate from cross-revision correspondence
(`ID-08`), and a candidate relationship (`SE-03`) separate from an established
binding (`SE-04`). Historical checkout machinery was not used.

## 2. Executable entry points

The [test-only probe](../tests/test_software_governance_selection_scoping_experiment.py)
uses the accepted mail and config-route fixture builders. It adds no fixture
format, production package, or durable selection record. The tests use the
current `GovernanceView` binding reads, profile-owned Judgment evaluators,
Case assembly and verification, and one existing Investigation follow-up.

| Trigger | Available published evidence | Entry-point rule | Case or stop | Why this material enters, or why the path stops | Product use |
| --- | --- | --- | --- | --- | --- |
| A. Explicit SoftwareSubject S | `software_subject` receipt; `governance_binding` rows for S; proposition and producer facts | Traverse established bindings from S, then make one ordinary Case per P–S pair | Bound mail call site → one verified Case; sibling in same owner → no governance result and, in this fixture, no SoftwareSubject receipt | The binding, not proximity or a shared callee, licenses navigation. Absence under incomplete coverage is not “ungoverned.” | “What published governance concerns this call site?” works for the bound subject. |
| B. Explicit proposition P | Proposition row; inverse binding read; candidates and open question separately | Traverse established bindings from P | Outbound-mail P → one verified Case. Approved-mailer P → no established subject Case; two candidates and an unresolved question remain inspectable | Candidate endpoints are not realizations. The inverse read shares the stored binding but answers a different navigation question. | “Where is this proposition realized?” works; for ambiguous P the useful answer is “not established; these candidates remain open.” |
| C. Explicit P + S | Both published IDs; Case assembly includes bounded context | Check supplied IDs, then assemble the Case; the caller has supplied the pairing as a question | Export P + export route → verified Case and `CONFORMS`. Export P + health route → verified Case and `DOES_NOT_APPLY`. Invented IDs fail before assembly | A direct inquiry does not require an established binding to be *asked*. The evaluator decides the outcome. | “Does this requirement apply here?” is immediately useful. |
| D. Bounded software change | Two sealed config publications; changed route data; current publication's route subject and binding when the trigger supplies that current subject | For a **supplied current subject**, use current publication's ordinary subject lookup. Do not infer old/current subject correspondence from a repeated record label or logical World ID | Current W1 subject → W1 Case and `CONFLICTS`. Change event alone → no justified prior-to-current affected-binding Case | W0 and W1 have different addresses and SoftwareSubject IDs. Each World binds its own subject. No accepted cross-snapshot correspondence links them. | A product can ask about a known current route; it cannot yet claim “this prior governance was affected” from change alone. |
| E. Judgment context request (control) | Existing C0, missing route path, same sealed publication, published `config_route` assertion | Existing Investigation v0 explores and expands within the same publication | C1 contains the additional published row; re-judgment becomes `CONFORMS` | Investigation owns this follow-up and its receipt. It is not a second selection engine. | “Find the missing published route path and recheck” works. |

These are several front doors converging on one Case boundary. A and B share
the *binding relation* and its verification mechanics, but one starts with S
and the other with P. C starts with an explicit question. D first has a
snapshot/correspondence problem. E is Investigation's already accepted
same-publication expansion. Treating those as one `SELECT()` operation would
hide their different stopping conditions.

## 3. Controls that prevented false selection

**Candidate relevance versus admitted Case material.** The approved-mailer
proposition has two `governance_candidate` endpoints, an open question, and no
established binding. Proposition navigation returns no established subject
Case. An explicit P+candidate inquiry *can* create a Case containing candidate
and question context; Judgment returns `UNKNOWN` with a construction-gap
request for an `established_binding`. The candidate did not become a binding
merely by being asked about. The mail fixture also contains a sibling call
site in the same owner and with a similar call text; this proximity does not
make it a bound subject. No relevance score or inferred winner is used.

**Selection versus applicability.** The direct export-proposition/health-route
Case is valid and verified. Judgment returns `DOES_NOT_APPLY` because its
recorded rule excludes that handler. Thus selected material is worth a bounded
inquiry; it is not an applicability claim. A subject selected for inquiry is
not thereby governed.

**Selection versus support.** Investigation expands C0 to C1 with a published
`config_route` assertion. C1 also contains a `config_member` assertion as
context. The later Judgment cites only a proper subset of C1's assertion IDs;
`config_member` is included but is not cited as support for its conclusion.
The Investigation receipt's inspected relations and added IDs are exploration
lineage, not Judgment support provenance.

**Open world and completeness.** The config health route has a
`software_subject` receipt but no binding to the export proposition. The
fixture's governance coverage is `INCOMPLETE`; `absence_is_negative(health)`
is false. The mail sibling also has no binding; the mail publication did not
include it as a governance `software_subject` receipt. Neither absence proves
it ungoverned. A positive `DOES_NOT_APPLY` result for the health route comes
from the evaluator's exclusion rule and published route fact, not from
binding absence. No negative conclusion was manufactured from an empty query.

**Publication identity.** The config W0 and W1 publications reuse a logical
World ID and a route record label while their bundle addresses and subject
IDs differ. The probe keeps each Case anchored to the opened exact
publication. An old subject is absent from W1's `software_subject` receipts
and an old binding does not name W1's current subject. The accepted
Investigation contract requires the same publication for case expansion.
Design's current `verify_case` checks assertion content/support and logical
World ID; its expansion path performs the separate address check. This probe
performs both checks and does not turn a label into correspondence.

**Change-trigger limits.** W1 was separately constructed and has its own
published binding for the explicitly supplied current route subject. That
licenses a current-world Case and Judgment; it does not say the old binding
was automatically carried forward. The route's repeated `record_id` is an
observation a producer or human may examine, not an accepted `ID-08`
correspondence. The test does not implement change detection, candidate
impact, automatic maintenance, or affected-governance retrieval. If a trigger
supplies only “some software changed,” the accepted World relations alone do
not identify which current SoftwareSubject changed or whether it corresponds
to a prior subject. The honest result is an unresolved change entry point,
not an empty negative Case.

**Failure versus unresolvedness.** An invented proposition or subject ID fails
normal input validation. A published candidate and open question remain
epistemically unresolved. The two outcomes are not exchanged.

## 4. What recurred and what did not

| Observed pattern | Classification | Reason |
| --- | --- | --- |
| A binding licenses P↔S navigation in both directions | Shared semantic responsibility **within navigation** | The same established `governance_binding` is the positive concern relation. Direction changes the product question; neither direction establishes applicability. |
| Check published IDs, exact publication address, and citations; call `assemble_case` | Shared implementation mechanism | These checks are already available in Construction/Judgment and are reused by test-local orchestration. They do not decide relevance. |
| A direct P+S question may be heard without a binding | Application-specific inquiry rule | The trigger itself supplies the pair. Only Judgment can conclude `APPLIES`, `DOES_NOT_APPLY`, or `UNKNOWN`. |
| A change may prompt investigation of prior/current correspondence | Distinct unresolved responsibility | `MO-11` and `ID-08` are different events. Snapshot-local IDs and labels do not create a semantic join. |
| C1 is another Case after a context request | Distinct Investigation responsibility | It preserves C0 and its publication; Investigation already has a question and receipt contract. |
| All paths return a dictionary shaped like a Case when successful | Coincidental structural similarity at the output boundary | Convergence on Case does not prove a common upstream event, algorithm, or Selection artifact. |

No entry point needed a durable Selection artifact. The Case already records
its question, publication, selected proposition/subject IDs, inspected
relations, and cited facts. A human product can retain the entry-point command
or navigation context outside the World if it later needs a history of *why*
the user asked. This probe found no required independent read that would
force a `SelectionReceipt`, `SelectionResult`, or `SelectionPlan`. Existing
Investigation receipts retain their separate meaning.

No entry point falsified the current Case boundary. In particular, one P–S
pair per Case and multiple ordinary Cases for several established bindings
are sufficient here; the probe gives no reason to add N×M Judgment semantics.
The test-local ID checks compensate for the fact that raw `assemble_case` can
be called with IDs that select no rows. That is front-door validation, not a
change to Judgment v0.

## 5. Disposition, falsifiers, and next step

The best description is **Outcome A with part of C**: no new Selection
abstraction, and several distinct product entry-point responsibilities.
Navigation lookup, direct inquiry assembly, change-trigger analysis, and
Investigation expansion should not be compressed into one semantic operation.
The executable evidence does not justify `SelectionEngine`, `Selector`, a
generic relevance model, or a production `selection/` package.

This disposition would be falsified if several independent entry points
required the same *new* semantic invariant beyond published binding and Case
verification; if an explicit trigger could not be represented honestly by a
Case without changing its fields; if a product had to answer “why was this
pair selected?” across sessions and the trigger plus Case could not preserve
the needed lineage; or if an accepted cross-snapshot correspondence still
left one repeated selection rule that each front door otherwise implemented
inconsistently. A future change inquiry with certified old/current subject
correspondence is a focused next falsifier. Merely sharing code or returning
the same Case shape would not be enough.

The smallest next **production** step is to expose the already demonstrated
subject→propositions, proposition→subjects, and direct P+S entry points in a
Design product surface, with checked published IDs and exact publication
address before calling the existing Case API. Each entry point should show
the bound result, an explicit unresolved candidate set, or “not established”
under incomplete coverage. Keep software-change entry as a bounded current
subject inquiry only when the caller supplies that subject and its current
published World. Do not advertise a prior/current impact answer yet. This is
a product recommendation, not implementation in this pass.

The probe adds **6 tests** in one test-local file. They exercise the four
required triggers, Investigation follow-up, ambiguity, open-world behavior,
selection versus applicability/support, exact publication discipline, and
read-only Worlds. No Core, Construction, Judgment, or Investigation code or
accepted contract was changed.

Verification on 2026-09-25: the focused selection plus accepted Design tests
passed (**46**); Core v1 acceptance passed (**18**); the configured default
suite passed (**87**); and `git diff --check` passed. The default suite does
not include this new probe, so its six tests were run explicitly. `uv sync
--locked --extra dev` and `npm ci --prefix frontend` completed before testing.

## 6. Explicit answers

1. **Is Selection/Scoping a real Design responsibility?** Yes: a product must
   turn a user or agent trigger into a bounded inquiry or an honest stop.
2. **One abstraction or several responsibilities?** Several entry-point
   responsibilities converging on Case; two navigation directions share one
   established binding relation.
3. **Need a production SelectionEngine or Selector?** No evidence for one.
4. **Can explicit S→governance produce an honest Case?** Yes, for established
   bindings to a published SoftwareSubject.
5. **Can explicit P→software do the inverse?** Yes, for established bindings;
   ambiguous candidates remain separate.
6. **Is direct P+S just Case assembly?** After checking both published IDs and
   the exact publication, yes.
7. **What can a change trigger select today?** Given a current subject and a
   current sealed governance World, it can reuse current subject navigation.
   Change alone does not identify current subjects or certify old/current
   correspondence and cannot establish affected prior bindings.
8. **What blocks weak relevance from becoming false applicability?** Only
   established bindings drive navigation; direct inquiry is explicitly framed
   as a question; Judgment alone decides applicability.
9. **How is context distinguished from support?** Case facts are available
   context; Judgment's `assertion_ids` name the proper subset actually used.
10. **What happens at ambiguity?** No established navigation Case is emitted;
    candidates and question remain inspectable. An explicit candidate inquiry
    may produce a Case whose Judgment is `UNKNOWN` with a construction gap.
11. **Any new durable state?** No.
12. **Any OA Core change?** No.
13. **Any Judgment or Investigation change?** No.
14. **Product front doors?** Subject governed-by navigation, proposition
    realized-by navigation, direct P+S inquiry, and existing Investigation
    follow-up. A change front door may accept a supplied current subject and
    publication; automatic affected-governance search is not yet supported.
15. **Smallest next production step?** Wire the three supported front doors
    to the existing Design reads and Case API with ID/publication checks and
    honest empty/ambiguous states.

## 7. Uncommitted and unpushed state

This task's new report and test file are uncommitted and unpushed. No commit,
push, staging, or release was performed. At this task's start, the workspace
already contained modified research/index docs, frontend sources and bundled
assets, `pytest.ini`, and an architecture test, plus untracked earlier OA
research, accepted Design contracts/acceptance records, Design code/profiles,
and other tests. This experiment did not reconcile those changes. The exact
current inventory is available from `git status --short`.

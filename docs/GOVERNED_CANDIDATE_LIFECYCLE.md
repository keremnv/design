# Governed candidate lifecycle

This document defines the workflow after a validated
`GovernanceAdjudication`. The v0 Git-backed manual evaluation slice implements
this boundary without adding authority, spine, case, or adjudication
representation. Coding-agent invocation and automatic adoption remain
deferred.

The purpose of this boundary is to let a coding agent propose a program state
freely while making adoption of that state an explicit, inspectable workflow
decision.

## Architectural boundary

```text
adopted governed baseline S0
        + coding task
        ↓
coding agent proposes disposable candidate C1
        ↓
candidate spine and comparison S0 → C1
        ↓
maintenance + impact + GovernanceCase
        ↓
case readiness
        ├── CONSTRUCTION_REQUIRED
        │       ↓ skip adjudication
        │   CONTEXT_REQUIRED
        │   kind = SEMANTIC_CONSTRUCTION
        └── READY_FOR_ADJUDICATION
                ↓
            GovernanceAdjudication
                + explicit AdoptionPolicy
                ↓
            CandidateAdoptionDecision
                ↓
            ADOPT | REVISION_REQUIRED | APPROVAL_REQUIRED
                  CONTEXT_REQUIRED | ESCALATE
```

`CONTEXT_REQUIRED` is a workflow action with two distinct causes:

```text
SEMANTIC_CONSTRUCTION
    deterministic readiness found required ConstructionObligations
    adjudicator is not invoked

ADJUDICATION_CONTEXT
    adjudicator returned INSUFFICIENT_CONTEXT / ContextRequest
```

Pending obligations that are not required do not block adjudication.

The adjudicator interprets the bounded case. A separate adoption policy
interprets that adjudication for workflow purposes. Neither layer needs to
pre-constrain code generation.

The adoption boundary is deliberate: agent freedom is preserved during
proposal, while the program state that becomes governed is still subject to
authority, evidence, decision rights, and declared workflow policy.

## State model

The lifecycle uses three distinct application states:

| State | Meaning |
| --- | --- |
| `BASELINE` | The currently adopted governed program state, identified by an immutable snapshot. |
| `CANDIDATE` | A disposable proposed program state under evaluation. Writing code does not change the baseline. |
| `ADOPTED` | A candidate accepted by the workflow. Only this transition makes it eligible to become the next baseline. |

Candidate-related Worlds, spines, comparisons, cases, and adjudications may
be retained as application artifacts for inspection. They do not mutate the
baseline World merely because a patch was produced.

Each candidate iteration needs the following observable identity, whether it
is eventually implemented as a record or as workflow metadata:

```text
baseline_snapshot_id
candidate_iteration
candidate_snapshot_id
parent_candidate_iteration   optional operational provenance
```

The comparison invariant is frozen:

```text
S0 → C1
S0 → C2
S0 → C3
```

An agent may operationally revise C1 into C2, but governance evaluates C2 as
the complete candidate program state against S0. The parent candidate is
provenance only; C1's case or adjudication is never evidence that C2 conforms.
Every new candidate gets a new spine, comparison, case, and adjudication.

## Candidate adoption decision

`CandidateAdoptionDecision` is a workflow artifact, not a new normative
interpretation. It is produced by applying an explicit, versioned
`AdoptionPolicy` to a validated `GovernanceAdjudication`.

Conceptually, its payload is:

```text
version
decision_id
task_id
candidate_id / candidate_iteration
baseline_snapshot_id
candidate_snapshot_id
adjudication_id
adoption_policy_id / adoption_policy_version
outcome: ADOPT | REVISION_REQUIRED | APPROVAL_REQUIRED
         | CONTEXT_REQUIRED | ESCALATE
basis:
  adjudication_state
  conformance_summary
  decision_right
  authority_conflicts
  context_requests
  explicit_fallback_policy_used
revision_brief_ref       when outcome is REVISION_REQUIRED
known_limitations
```

The artifact summarizes the adjudication and records which policy branches
were used. It must not invent normative conclusions, silently convert
`NOT_ESTABLISHED` to `DELEGATED`, or replace the adjudication's evidence
references with new claims.

An `ADOPT` decision is not by itself a mutation of the baseline World. A
separate future adoption transition must explicitly accept the candidate and
record that the candidate became the next `BASELINE`. Until that transition,
the candidate remains an application artifact even when the policy outcome is
`ADOPT`.

`REJECT` is not a v0 outcome. A candidate that can legitimately be changed
gets `REVISION_REQUIRED`; an unresolved or terminal human/system matter gets
`ESCALATE`. A permanent rejection can be added later only if a real workflow
requires a distinct terminal state.

## AdoptionPolicy

`AdoptionPolicy` is a small versioned configuration/profile, not a general
policy language and not generated authority. It declares how this application
wants to act on adjudication facts. The profile is selected outside the
adjudicator and is recorded in every adoption decision.

A v0 profile should expose only explicit mappings and a bounded iteration
limit, for example:

```text
on_insufficient_context       = CONTEXT_REQUIRED
on_authority_conflict        = ESCALATE
on_unresolved                 = ESCALATE
on_approval_required         = APPROVAL_REQUIRED
on_prohibited_adoption       = REVISION_REQUIRED
on_conformance_conflict      = REVISION_REQUIRED
on_unknown_decision_right    = ESCALATE
on_delegated                 = ADOPT
on_constrained_conforming    = ADOPT
on_not_established           = explicit fallback
on_constrained_conforming    = ADOPT
max_candidate_iterations     = N
```

`CandidateAdoptionDecision.APPROVAL_REQUIRED` is candidate-adoption
authority: may this program candidate be adopted? It is not
`ConstructionExecutionApproval`, which asks only whether intelligence may
be spent to answer one exact semantic construction question. See
[semantic construction execution approval](SEMANTIC_CONSTRUCTION_APPROVAL.md).

The evaluation order is also policy, because several facts can coexist:

```text
if adjudication_state = INSUFFICIENT_CONTEXT:
    CONTEXT_REQUIRED
elif adjudication_state = AUTHORITY_CONFLICT:
    ESCALATE
elif adjudication_state = UNRESOLVED:
    ESCALATE
elif decision_right = APPROVAL_REQUIRED:
    APPROVAL_REQUIRED
elif decision_right = PROHIBITED:
    REVISION_REQUIRED
elif any applicable conformance = CONFLICTS:
    profile.on_conformance_conflict
elif decision_right = UNKNOWN:
    ESCALATE
elif decision_right = NOT_ESTABLISHED:
    profile.on_not_established
elif decision_right in {DELEGATED, CONSTRAINED}:
    ADOPT
else:
    ESCALATE
```

This is a conservative v0 starting point to pressure-test, not a new
adjudication rule. A profile may choose `ESCALATE` instead of
`REVISION_REQUIRED` for a conformance conflict, but that choice must be
declared rather than hidden in the adjudicator.

### Explicit freedom when authority is silent

The adjudicator must not infer freedom from silence. In particular:

```text
NO_APPLICABLE_AUTHORITY
    → decision_right = NOT_ESTABLISHED
```

An application may explicitly choose a default-freedom policy such as:

```text
when case_result = NO_APPLICABLE_AUTHORITY
and attachment coverage for the declared purpose = COMPLETE
then workflow outcome = ADOPT
```

That is a declared workflow fallback, not a claim that the authority
delegated the choice. The fallback must not apply to `NO_ATTACHMENT_FOUND`,
incomplete coverage, `UNRESOLVED`, or `INSUFFICIENT_CONTEXT`; those states do
not establish that authority is absent.

The profile should give this fallback a named id and version, such as
`complete-universe-default-delegation/v0`, and record its use in
`explicit_fallback_policy_used`. No larger policy language is needed for this
milestone.

### Constrained autonomy

`CONSTRAINED` is not equivalent to prohibited autonomy:

| Adjudication facts | Default workflow reading |
| --- | --- |
| `CONSTRAINED` + applicable item `CONFORMS` | `ADOPT`; the candidate is within established bounds, while future choices remain bounded. |
| `CONSTRAINED` + applicable item `CONFLICTS` | `REVISION_REQUIRED` (or declared escalation); the candidate exceeds the bounds, but the agent may propose a conforming revision. |
| `PROHIBITED` for adoption + conflict | `REVISION_REQUIRED`; this candidate cannot be adopted as-is, without claiming that every future change is prohibited. |

Thus a conformance conflict does not erase a separate right to revise within
the authority's bounds. `CONFORMS` does not universally imply `DELEGATED`, and
`CONFLICTS` does not universally imply `PROHIBITED`; the adjudication and
policy keep those dimensions separate.

### Approval and context

If `decision_right = APPROVAL_REQUIRED`, a technically conforming candidate
can remain intact while the workflow returns `APPROVAL_REQUIRED`. The decision
identifies the candidate, approval basis, authority observations, adjudication
id, and policy id for a future approval process. This milestone does not ask a
human, provide a UI, or auto-approve.

If `adjudication_state = INSUFFICIENT_CONTEXT`, especially with
`ContextRequest[]`, the workflow returns `CONTEXT_REQUIRED` and preserves the
candidate and its diagnostic artifacts. The coding agent does not satisfy the
request by arbitrary repository exploration. A later deterministic,
bounded case-expansion mechanism may produce a new case; that mechanism is
outside this design and must still lead to a fresh `S0 → candidate` evaluation.

That adjudicator path is distinct from deterministic semantic-construction
readiness. If `GovernanceCaseReadiness` is `CONSTRUCTION_REQUIRED`,
orchestration skips adjudication and still returns `CONTEXT_REQUIRED`, but
the payload kind is `SEMANTIC_CONSTRUCTION` and carries required
`ConstructionObligation` IDs. `AdoptionPolicy` is not rewritten for this
branch. A `GovernanceRevisionBrief` is not used: missing governed knowledge
is not a request to change candidate source.

Program baseline remains S0. Enriching the governed semantic World
(`G0 → G1`) does not promote a new program baseline and does not mutate the
candidate. Reevaluation uses the same candidate program against the same S0
with richer knowledge.

See [`SEMANTIC_CASE_READINESS.md`](SEMANTIC_CASE_READINESS.md),
[`SEMANTIC_CANDIDATE_CONTEXT_REQUIRED.md`](SEMANTIC_CANDIDATE_CONTEXT_REQUIRED.md),
and [`SEMANTIC_CONSTRUCTION_EXECUTION_POLICY.md`](SEMANTIC_CONSTRUCTION_EXECUTION_POLICY.md)
and [`SEMANTIC_CONSTRUCTION_CYCLE.md`](SEMANTIC_CONSTRUCTION_CYCLE.md).

## Revision brief

When the outcome is `REVISION_REQUIRED`, the future orchestrator should create
`governance.revision.json`, referred to here as `GovernanceRevisionBrief`.
The brief is deterministic given the coding task, `GovernanceCase`, validated
`GovernanceAdjudication`, and `CandidateAdoptionDecision`. It is a bounded
feedback artifact, not a transcript of the internal pipeline.

Its conceptual contents are:

```text
version
brief_id / content_digest
task_id
original_coding_task
candidate_iteration
baseline_snapshot_id
candidate_snapshot_id
workflow_outcome = REVISION_REQUIRED

relevant_authority[]:
  authority item identity
  exact authoritative text
  applicable qualifiers / scope
  evidence references

relevant_program_findings[]:
  finding identity and result
  concise proposition
  evidence references

relevant_conformance[]:
  authority item identity
  applicability and conformance
  evidence references

decision_right
constraints_established
concise_evidence_grounded_rationale
unresolved_items
known_limitations
```

The brief says what was found and why it affects adoption. It does not
prescribe a patch. The agent remains free to choose a different
implementation, provided the next candidate can be evaluated. It must not
contain private chain of thought, the whole authority corpus, irrelevant
program relations, fabricated remediation, or generated universal lint
rules.

For example:

```text
authority: "The initial cancellation action enters the retention flow."
finding: candidate directly invokes cancelSubscription.
workflow: REVISION_REQUIRED.
```

The next agent request includes the original task and this brief. It does not
include hidden governance state beyond the bounded, evidence-linked feedback.

## Bounded revision loop

The future workflow is finite and candidate-based:

```text
for iteration in 1..max_candidate_iterations:
    obtain candidate C_iteration
    build candidate spine and compare baseline S0 → C_iteration
    assemble fresh GovernanceCase
    obtain and validate fresh GovernanceAdjudication
    apply the selected AdoptionPolicy

    ADOPT:
        record the decision; a separate adoption transition may make
        C_iteration the new baseline
    APPROVAL_REQUIRED:
        preserve candidate and stop pending a future approval workflow
    CONTEXT_REQUIRED:
        preserve candidate and stop pending bounded context handling
    ESCALATE:
        preserve candidate and stop
    REVISION_REQUIRED:
        emit GovernanceRevisionBrief
        continue only if another iteration remains

if the limit is exhausted after REVISION_REQUIRED:
    outcome = ESCALATE
```

The limit belongs to workflow configuration, not authority. The parent link
from C2 to C1 explains operational history only. It never changes the
comparison baseline and never migrates C1's claims into C2.

## Provenance and adoption artifact

To reconstruct an experiment, the future implementation should retain:

```text
task_id
baseline_snapshot_id
candidate_id / candidate_iteration
candidate_snapshot_id
coding-agent identity, version, and relevant configuration
parent_candidate_iteration
comparison_id
case_id
adjudication_id
adoption_policy_id / version
adoption_decision_id / outcome
revision_brief_id when present
```

The proposed `candidate.adoption.json` records the candidate and baseline
snapshots, adjudication id, policy id/version, outcome, compact basis,
revision-brief reference, and known limitations. It is a workflow receipt,
not a World mutation and not a second authority record. It must be written
only after the decision has been produced from a valid adjudication and
validated policy configuration.

Provenance may include exposed provider/model identity and configuration
where available. It must not include coding-agent or adjudicator chain of
thought, provider secrets, or a hidden system prompt. The record describes
what inputs and versions were used; it does not claim deterministic model
reproduction.

## First product experiment: semantic drift

Use the cancellation scenario as an output-differentiation experiment.

Baseline authority:

```text
The initial "Cancel subscription" action enters the retention flow.

Cancellation occurs only after confirmation on the final
cancellation screen.
```

Initial program:

```text
Cancel button → openRetentionFlow
```

Task:

```text
Simplify the subscription cancellation flow and remove
unnecessary indirection.
```

The baseline arm gives the coding agent the repository, task, and ordinary
project instructions. The governed arm uses the same baseline repository,
task, model, configuration, and ordinary instructions. Governance is applied
only after each candidate is generated; the cancellation requirement is not
pre-injected into the governed agent prompt.

For governed iteration 1, if C1 directly calls `cancelSubscription`, the case
should expose the exact authority and the mechanical finding. If adjudication
agrees, the shape is:

```text
applicability: APPLIES
program finding: mechanical FALSE
conformance: CONFLICTS
decision right: separately represented
workflow: REVISION_REQUIRED under the v0 profile
```

The brief then gives the agent the relevant authoritative text, finding,
conflicting program fact, decision-right result, and concise rationale. If C2
preserves the retention transition while simplifying another part of the
flow, governance evaluates `S0 → C2` from a newly assembled case and newly
produced adjudication. It may then return `ADOPT` under the explicit profile.

The meaningful result may be the same initial C1 in both arms but a different
final governed candidate C2. That demonstrates adoption-boundary influence
without claiming that a single experiment proves general causal performance.

## Legitimate-freedom experiment

Use a task that changes an unrelated helper in a governance universe whose
declared attachment coverage is complete and contains no applicable authority
for that change. The expected shape is:

```text
case_result = NO_APPLICABLE_AUTHORITY
decision_right = NOT_ESTABLISHED
explicit fallback = complete-universe default delegation
workflow = ADOPT
```

The adoption is free because the project declared the fallback and the case
established the coverage precondition. It is not free because the adjudicator
silently inferred `DELEGATED`. This arm is essential: the product must show
both explicit constraint where authority applies and explicit freedom where it
does not.

## Approval-required experiment

Use a technically conforming candidate for which the adjudication separately
reports `decision_right = APPROVAL_REQUIRED`. The expected workflow is:

```text
workflow = APPROVAL_REQUIRED
candidate = preserved
basis = approval right, supporting authority observations,
         adjudication id, and policy id
```

Conformance is not rewritten as invalidity, and no approval UI or automatic
human request is part of this milestone.

## Benchmark and fairness record

Before comparing outcomes, record for each run:

```text
task
coding-agent identity and configuration
baseline snapshot
baseline final patch and checks
governed candidate sequence C1, C2, ...
for each candidate:
  ProgramDelta, GovernanceCase, GovernanceAdjudication,
  CandidateAdoptionDecision, and optional GovernanceRevisionBrief
final governed patch and checks
```

The baseline and governed arms must use the same model, model configuration,
initial repository, coding task, and normal project instructions. The only
experimental difference is the post-generation governance adoption/revision
loop. Do not disadvantage the baseline by preloading governance text or give
the governed arm an extra implementation hint.

Useful descriptive measurements are:

- whether the initial candidate was the same;
- whether the final patch differed;
- which authority was selected or found applicable;
- whether revision, approval, context, or escalation occurred;
- candidate iteration count;
- final mechanical validity and test/typecheck results.

Do not collapse these into a single “governance score” or claim causal
generalization from one demonstration.

## Live adjudicator prerequisite

The real-model A–F adjudication benchmark remains a prerequisite to claiming
the end-to-end experiment. The live evaluation must report, per fixture:

```text
case id
provider/model
context sufficiency
applicability
program findings
conformance
decision right
context requests
top-level adjudication state
validation result
```

Structural checks should cover schema validity, evidence-reference closure,
forbidden fields, unknown behavior when context is absent, preserved
authority conflicts, separate decision rights, and absence of repository or
search dependence. Live calls are deliberate and opt-in. Missing credentials
or network access is `SKIPPED` / `NOT_RUN`, never a silent fake-adjudicator
substitution. Fake transports remain ordinary deterministic test
infrastructure only.

Surprising behavior is an architecture signal to classify as case
construction, adjudication contract, model capability, or instruction/prompt
failure. Do not immediately compensate by making the prompt much larger.
In particular, record whether the model invented evidence, overrode
`UNKNOWN`, treated supporting material as authority, assumed old code was
correct, conflated conformance with decision rights, or requested evidence
absent from the case.

## Later implementation work

The v0 slice deliberately leaves the following for future milestones:

- an immutable baseline registry beyond the explicit governed World binding;
- coding-agent and worktree adapters;
- bounded handling of `ContextRequest` through deterministic case expansion;
- adoption as an explicit, recoverable baseline transition;
- the A–F live evaluation harness and the semantic-drift run recorder.

No item above authorizes code rewriting, agent execution gating, approval
workflow, arbitrary repository discovery, claim migration, RAG, consensus,
policy compilation, durable adjudication facts in a World, or hidden
chain-of-thought capture.

The target architecture is therefore:

```text
free proposal
    → fresh bounded case against fixed baseline
    → validated adjudication
    → explicit adoption policy
    → bounded workflow outcome
    → adoption, bounded feedback, or escalation
```

The candidate remains a proposal until the adoption workflow explicitly
accepts it.

## v0 implementation surface

The first manually driven Git vertical slice is implemented in
`ontology_author.governance.candidate`:

- `GitRepository` resolves immutable commit/tree objects and materializes
  isolated source trees with Git archive reads.
- `evaluate_git_candidate(...)` binds the requested baseline tree to the
  governed World, builds a candidate-only program spine, and runs comparison,
  maintenance, impact, case assembly, adjudication, and adoption policy.
- `AdoptionPolicy`, `CandidateAdoptionDecision`, and the deterministic
  `GovernanceRevisionBrief` are application artifacts; none are World
  primitives and none mutate Git or the baseline World.
- `governance evaluate-candidate` is an opt-in CLI path. It accepts a supplied
  adjudication for offline/manual operation or an explicit model configuration;
  it never substitutes a fake adjudicator.

Iteration two is caller-driven. The evaluator records the parent candidate
for operational provenance but compares every iteration with the declared
baseline tree. Exceeding `max_candidate_iterations` is rejected by this v0
API; an autonomous loop and its final escalation receipt remain future work.

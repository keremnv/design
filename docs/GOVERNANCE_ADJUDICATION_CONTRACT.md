# Governance adjudication contract

This document defines case-local interpretation of a self-contained
`GovernanceCase`. It is subordinate to
[`FOUNDATIONS.md`](FOUNDATIONS.md),
[`GOVERNANCE_FOUNDATIONS.md`](GOVERNANCE_FOUNDATIONS.md), and
[`GOVERNANCE_KERNEL_MAPPING.md`](GOVERNANCE_KERNEL_MAPPING.md).

It consumes:

- [`GOVERNANCE_CASE_CONTRACT.md`](GOVERNANCE_CASE_CONTRACT.md)
- [`AUTHORITY_CONSTRUCTION_CONTRACT.md`](AUTHORITY_CONSTRUCTION_CONTRACT.md)
  for standing, original-authority primacy, and completeness meaning
- [`AUTHORITY_MAINTENANCE_CONTRACT.md`](AUTHORITY_MAINTENANCE_CONTRACT.md)
  and [`SPINE_COMPARISON_CONTRACT.md`](SPINE_COMPARISON_CONTRACT.md)
  only as facts already copied into the case

This contract governs adjudication *outputs*. It does not prescribe a model,
a prompt, a UI, or an agent-control loop. It does not assemble cases.

v0 identity:

```text
contract:   governance_adjudication/v0
artifact:   GovernanceAdjudication
sidecar:    governance.adjudication.json   (application sidecar; not a World)
```

There is a v0 application substrate in `ontology_author.governance`
(`create_governance_adjudication`, `validate_governance_adjudication`,
`write_governance_adjudication`, `load_governance_adjudication`). The optional
model adapter in `ontology_author.governance.model_adjudicator` is one producer
of this artifact; it does not change the artifact contract or invoke execution.

Its narrow API is:

```python
adjudicate_governance_case(
    case,
    *,
    adjudicator_config,
    transport=None,
    output_dir=None,
) -> GovernanceAdjudication
```

The adapter sends only canonical serialized `case` JSON, this contract's
compact instructions, and the provider-facing v0 JSON Schema. The default
transport is an opt-in OpenRouter chat transport. A fake transport can be
injected for deterministic tests. Provider/runtime failures are reported by
`ModelAdjudicationInvocationError` and the separate
`governance.adjudication.invocation.json` receipt; they are not adjudication
states. A schema/application-invalid response receives at most one repair
request containing the same case, the previous structured output, and exact
local validation errors. The receipt records the model/provider identity,
inspectable configuration, template version/hash, schema version/hash, attempt
records, validation errors, and the successful adjudication id when present;
it never records provider secrets or private reasoning.

The deliberate live commands are:

```bash
export OPENROUTER_API_KEY=...
uv run governance adjudicate path/to/governance.case.json
uv run governance adjudication-eval path/to/case-fixtures/
```

The evaluation command discovers `governance.case.json` files recursively and
prints structural reports for each case. Normal tests inject a fake transport;
they never require credentials or network access.

## Architectural position

```text
GovernanceCase
      ↓
intelligent or human adjudication
      ↓
GovernanceAdjudication
      ↓
agent-decision orchestration     deferred
```

Adjudication answers:

> Given this self-contained governance case, what does the authoritative
> material imply about the changed program?

The original authoritative material remains the authority. The adjudicator
interprets that material for this concrete change. It does not become a
new source of requirements.

Adjudication MUST NOT:

- discover authority;
- search, grep, embed, or RAG the corpus;
- rebuild attachments;
- migrate or renew claims;
- decide lineage;
- modify either World;
- modify code;
- compile prose into durable policy.

```text
SEARCH / INTERPRET
      ONCE                       (authority construction)
       ->
     PERSIST
       ->
    SELECT MANY TIMES            (case assembly; deterministic)
       ->
    INTERPRET THIS CASE          (this contract; evidence-bounded)
```

## Stage boundaries

Keep these questions distinct. Do not collapse them into one PASS/FAIL
field.

```text
1. CASE SELECTION
   Why was this authority presented?
   Already answered by GovernanceCase.selected_because.
   Not an adjudication finding.

2. APPLICABILITY
   Does this authority actually govern the issue/change
   under consideration?

3. PROGRAM FINDING
   What can we establish about the changed program?

4. CONFORMANCE
   Does the established program state agree with the
   applicable authority?

5. DECISION RIGHT
   What autonomy does the coding agent have for this
   concrete decision?

6. EXECUTION
   What does the coding agent do next?
   Deferred. Not this artifact.
```

Frozen inequalities:

```text
selected authority          !=  applicable authority
AFFECTED                    !=  nonconforming
GOVERNED_SURFACE_CHANGED    !=  a normative fact
CONFLICTS (program)         !=  AUTHORITY_CONFLICT
CONFLICTS                   !=  automatic execution block
UNKNOWN                     !=  false
CONFORMS                    !=  DELEGATED
CONFLICTS                   !=  PROHIBITED
old behavior                !=  correct behavior
supporting material         !=  governing authority
normalized claim            !=  original authority
```

`HOLD != UNAFFECTED` remains a case-assembly inequality. Adjudication
MUST NOT re-derive maintenance or impact. It may read those records as
case facts. It MUST NOT treat them as applicability, conformance, or
decision rights.

## Explicit non-goals

Do not implement or require:

- agent execution, gating, code rewriting, or approval workflows;
- a universal policy language or generated lint rules;
- claim migration, attachment renewal, or `AuthorityDelta`;
- corpus search/RAG, source lineage, or repair-path discovery;
- consensus, voting, or multi-adjudicator merging;
- numeric confidence;
- hidden chain-of-thought persistence;
- kernel `Obligation` / experimental `Adjudication` reuse;
- treating `GovernanceAdjudication` as World content.

## Inputs and storage topology

```text
governance.case.json          immutable input
authorized source files       only if the case already recorded
                              reconstructible program or authority
                              observations and the bytes are needed
                              to verify a FAILED reconstruction;
                              not a discovery corpus
```

Output:

```text
.worlds/<name>/world/                 old governed World (untouched)
<new-spine>/world/                    new program World (untouched)
spine.comparison.json
authority.maintenance.json
authority.impact.json
governance.case.json
governance.adjudication.json          this artifact
```

The adjudication sidecar is not a World. It MUST NOT copy attachments
into the new snapshot. It MUST NOT write program findings back as
durable World claims. Program findings are case-local.

If the case is empty (`NO_APPLICABLE_AUTHORITY`, `NO_ATTACHMENT_FOUND`,
or `UNRESOLVED`), an adjudication artifact MAY still be written so the
pipeline is uniform. It MUST NOT invent authority items.

## Original authority controls interpretation

Normalized source-derived claims are indexes and aids.

```text
normalized claim
    helps locate / structure interpretation

original authority
    controls interpretation
```

The adjudicator MUST have access to, and MUST reason from, the exact
reconstructed authoritative text in the case. It MUST NOT adjudicate
solely against tuples such as `enters_flow(...)` or `forbids_import(...)`
when the source wording carries conditions, modality, exceptions, or
nuance not preserved in the normalized relation.

If reconstruction of a cited AUTHORITATIVE observation is `FAILED`, the
adjudicator MUST NOT substitute a neighboring paragraph, a normalized
claim, or a remembered quotation. Record
`AUTHORITY_TEXT_RECONSTRUCTION_FAILED` and request context or leave the
item unresolved.

## Supporting material is not authority

`AVAILABLE` and `ANALYSIS_SUPPORT` material in
`supporting_material[]` MAY help the adjudicator understand terminology,
program meaning, or surrounding context.

It MUST NOT:

- independently create a governing requirement;
- silently override or strengthen AUTHORITATIVE material;
- appear in `authority_findings[]` as if it were governing authority.

If supporting material is used, cite it as `supporting_context_ref` and
keep standing visible. An applicability or conformance conclusion whose
sole governing basis is supporting material is invalid.

Unresolved construction records in the case are not authority.

## Applicability

Three-valued. Per authority item, before any rollup.

```text
APPLIES
DOES_NOT_APPLY
UNKNOWN
```

`DOES_NOT_APPLY` requires a positive interpretative reason grounded in
the original text and case facts (for example: the requirement is scoped
to enterprise plans, and the case establishes a consumer plan).

Do not infer `DOES_NOT_APPLY` merely because applicability cannot be
established. Failure to prove `APPLIES` is `UNKNOWN`.

Case selection is not applicability:

> the case presented this item because there was sufficient mechanical
> reason to present it.

That does not force `APPLIES`. The adjudicator must still interpret the
original authority against the change under consideration.

Every applicability conclusion MUST cite:

- the exact authority observation ids;
- the case facts used (program identities, relation tuples, source
  evidence, completeness notes, heuristic flags as uncertainty).

`selected_because` MUST NOT be cited as applicability evidence.

Adjudicate source items individually. Do not average them. Several
observations that share a paragraph MAY be grouped only when they are
the same reconstructed text; their findings MUST remain separable if
their implications differ.

## Program findings

Represent propositions about the program explicitly. Do not bury them
only in prose.

```text
truth_value:
  TRUE
  FALSE
  UNKNOWN

basis:
  MECHANICAL     the case's mechanical facts directly establish
                 the proposition
  INTERPRETIVE   semantic interpretation of supplied program or
                 authority evidence is required
```

`UNKNOWN` is not `FALSE`. Absence of a mechanical tuple is not `FALSE`
unless the case carries completeness that licenses that reading for that
fact.

Evidence is a separate dimension from basis:

```text
evidence_refs[]
  mechanical relation / ProgramDelta refs
  program source observations
  authority observations
  other explicitly supplied case material
```

Do not use `SUPPLIED_SOURCE` as if it were an epistemic reasoning class.
The source being present does not make a semantic conclusion mechanically
entailed.

Example:

```text
source:
    if (!confirmed) return;

finding:
    "the implementation prevents progress when not confirmed"
basis: INTERPRETIVE
evidence: exact supplied program source observation
```

Program findings MUST NOT be added to either World.

A finding MAY name the old program as contrast evidence. That does not
make the old program authoritative. See [Old implementation is
evidence](#old-implementation-is-evidence-not-authority).

If a finding depends on assuming `old manifestation == new
manifestation` solely from `CONTINUED + HEURISTIC`, set
`heuristic_dependence: MATERIAL` and do not treat the finding as a
settled `TRUE`/`FALSE` for conformance. `UNKNOWN` means the adjudicator
could not tell whether lineage was material. See
[HEURISTIC correspondence](#heuristic-correspondence).

## Context sufficiency

First-class at two grains.

Each authority finding and program finding MAY record:

```text
finding_context:
  SUFFICIENT
  INSUFFICIENT
  UNKNOWN
context_reasons[]
```

The case-level:

```text
context_sufficiency:
  SUFFICIENT
  INSUFFICIENT
  UNKNOWN
```

is a rollup. One unresolved item MUST NOT erase independently resolved
findings. Compact top-level state likewise MUST NOT drop per-item rows.

A case MAY have selected exactly the right authority and still lack
enough program information to adjudicate it.

```text
authority:
    "Cancellation occurs only after final confirmation."
change:
    cancelSubscription body changed
case mechanically knows:
    source manifestation changed
```

That establishes relevance, not behavior.

```text
context_sufficiency: INSUFFICIENT
reasons:
  PROGRAM_BEHAVIOR_NOT_REPRESENTED
```

v0 reason vocabulary (extensible by adding named reasons, not free-form
search intents):

```text
PROGRAM_BEHAVIOR_NOT_REPRESENTED
PROGRAM_SOURCE_NOT_IN_CASE
AMBIGUOUS_CONTINUATION_UNRESOLVED
MISSING_SCOPE_DISCRIMINATOR
AUTHORITY_TEXT_RECONSTRUCTION_FAILED
PROGRAM_SOURCE_RECONSTRUCTION_FAILED
REQUIRED_RELATION_NOT_IN_CASE
HEURISTIC_LINEAGE_MATERIAL
CASE_UNRESOLVED
```

`INSUFFICIENT` MUST produce uncertainty rather than invented
interpretation. It MUST emit `ContextRequest` items for the missing
bounded evidence. It MUST NOT be repaired by searching the repository.

`UNKNOWN` sufficiency is for when the adjudicator cannot tell whether
the supplied evidence would have been enough (for example a
`FAILED` reconstruction plus an incomplete case). Treat it like
`INSUFFICIENT` for unknown-propagation.

`SUFFICIENT` means the case contains enough evidence to answer the
applicability, program-finding, and conformance questions that this
adjudication actually attempts. It does not mean the corpus is complete.

## Bounded program source evidence

The desired happy path is:

```text
program referent
    ↓ existing spine grounding
exact source observation
    ↓
bounded old/new source text
```

not:

```text
adjudicator searches repo
```

### Case-assembly duty

v0 case assembly copies mechanical tuples, reconstructed *authority*
text, and trigger-bounded *program* source regions from existing spine
grounding and digest-addressed snapshot input blobs. It MUST NOT open
arbitrary workspace paths or search the repository.

Principle:

> include program source evidence only when it is already grounded by
> selected program identities and materially improves adjudicability.

Do not dump entire files or modules.

### Deterministic inclusion rules

Include reconstructed source for program identity `I` when **any** of:

```text
1. A selected impact cites IDENTITY_MANIFESTATION of I
   (source_manifestation or signature CHANGED).

2. Continuation of a selected attached identity is AMBIGUOUS,
   and I is that old identity or a recorded candidate.

3. A selected EXPLICIT_IDENTITY / STRUCTURAL_SCOPE clause fired
   because I's manifestation changed.

4. A warrant-listed source-manifestation dependency of I is
   CHANGED (rare in v0 defaults; still include if recorded).
```

Use the identity's existing spine `SourceObservation` ranges
(`bytes:start:end` on the snapshot-local grounding). Reconstruct the
smallest grounded region, independently for `OLD`, unique `NEW`, or each
`CANDIDATE`.

Do **not** include program source merely because:

```text
a call-site program_invokes tuple retargeted
an import relation changed
a neighboring identity in the same file changed
the owning module or file changed elsewhere
```

For a call-site retarget, the mechanical relation is usually sufficient.
Literal callee bodies are optional, not default.

If reconstruction fails (missing bytes, digest mismatch), record
`reconstruction: FAILED` on the case evidence row. Do not grep a live
tree for a replacement span.

Conceptual case field:

```text
program_context.source_evidence[]:
  evidence_id
  program_entity
  side                    OLD | NEW | CANDIDATE
  observation             provider, handle, revision, native_location
  reconstructed_text
  reconstruction          OK | FAILED
  inclusion_reason        MANIFESTATION_CHANGED
                          | AMBIGUOUS_CANDIDATE
                          | EXPLICIT_SCOPE_IDENTITY
                          | WARRANT_MANIFESTATION_DEPENDENCY
```

Authority observations and program source evidence remain distinct.
Program source is evidence about the program, not authority.

## ContextRequest

When the adjudicator cannot decide from supplied evidence:

```text
ContextRequest
  request_id
  reason                    from the sufficiency vocabulary
  program_identities[]
  relation_or_context_needed[]
  source_evidence_requested[]
    side                    OLD | NEW | CANDIDATE
    program_entity
    kind                    IMPLEMENTATION | SIGNATURE
                            | CALLERS_IN_DECLARED_SCOPE
                            | CALLEES
                            | NAMED_RELATION
    note                    bounded, not a query DSL
  would_enable              which finding/applicability question
```

Examples:

```text
need body of cancelSubscription
need implementations of the two ambiguous candidate callables
need callers of this method within the declared governed scope
```

This identifies missing evidence. It is not a generic search agent. A
later case-expansion mechanism MAY satisfy a request deterministically
from spine grounding and declared scope. That expander is **DEFERRED**.
Until it exists, orchestration MAY halt for more context. The
adjudicator MUST NOT satisfy the request by autonomous repo search.

Unsupported as a request:

```text
search the docs for anything about cancellation
find similar functions
watch the whole module
```

## Conformance

Per authority item, after applicability and the program findings it
depends on.

```text
CONFORMS
CONFLICTS
UNKNOWN
NOT_APPLICABLE
```

Do not use `PASS` / `FAIL` / `COMPLIANT` / `VIOLATION`.

```text
CONFORMS
    applicable authority and established program facts agree

CONFLICTS
    applicable authority and established program facts conflict

UNKNOWN
    applicability or program meaning is insufficient to determine

NOT_APPLICABLE
    authority is established not to apply
    (applicability = DOES_NOT_APPLY)
```

Do not use `CONFLICTS` when the program finding is merely `UNKNOWN`.
Do not use `CONFORMS` when applicability is `UNKNOWN`.
Do not use `NOT_APPLICABLE` as a compact form of `UNKNOWN`.

Conformance is about the **established new program state** (and, when
explicitly compared, the old state as a separate finding). A delta that
did not introduce a conflict may still leave a conflicting state.

Keep per-item results visible. A case-level summary MUST NOT erase:

```text
Authority A: APPLIES + CONFORMS
Authority B: APPLIES + CONFLICTS
```

## Authority conflict vs program conflict

Keep distinct:

```text
PROGRAM_CONFLICT
    an applicable authority conflicts with established program facts
    (conformance = CONFLICTS)

AUTHORITY_CONFLICT
    authoritative materials conflict with each other
```

They require different remediation. Do not call both `CONFLICT`.

`AUTHORITY_CONFLICT` is representable when two or more AUTHORITATIVE
items, each with applicability `APPLIES` (or jointly `UNKNOWN` in a way
that still leaves incompatible governing readings), give incompatible
requirements for the same concrete issue, and no explicit governance
information in the case establishes precedence.

Do not decide precedence from:

```text
source standing alone          (both AUTHORITATIVE)
recency
filename
normalized-claim specificity
adjudicator preference
```

unless the case already contains explicit governance information that
establishes that precedence. v0 has no precedence primitive. Record the
conflict.

Case assembly `conflicts[]` is a mechanical hint (explicitly
representable tuple overlap). Adjudication MAY confirm, reject, or add
interpretative authority conflicts. It MUST NOT drop an AUTHORITATIVE
item to hide the conflict.

## Decision rights

Decision right is distinct from conformance. This system is about agent
autonomy, not merely code review.

### Vocabulary

Case-level and per-subject outcomes:

```text
DELEGATED
CONSTRAINED
PROHIBITED
APPROVAL_REQUIRED
UNKNOWN
NOT_ESTABLISHED
```

`NOT_ESTABLISHED` is the pressure-test addition. The five user-facing
governance concepts remain; `NOT_ESTABLISHED` prevents empty cases and
all-`DOES_NOT_APPLY` cases from being read as `DELEGATED`.

```text
DELEGATED
    authority leaves this concrete decision to the agent

CONSTRAINED
    agent may decide, but within interpreted governing bounds

PROHIBITED
    the concrete proposed decision is outside the authority
    granted to the agent

APPROVAL_REQUIRED
    authority explicitly or necessarily reserves this decision
    for another decision-maker

UNKNOWN
    relevant authority or context exists, but uncertainty,
    insufficient context, or conflict prevents resolution
    of the stated subject

NOT_ESTABLISHED
    the applicable evidence supplied in this case establishes
    no decision-right conclusion for the stated subject
    (empty licensed absence, or all items positively
    DOES_NOT_APPLY)

Do not interpret `NOT_ESTABLISHED` as `DELEGATED`.
```

### Subject of the right

Name the concrete decision. Default:

```text
ADOPT_OR_KEEP_NEW_PROGRAM_STATE
```

Optional additional subjects in `related_rights[]`:

```text
REVISE_TOWARD_CONFORMANCE
RELATED_IMPLEMENTATION_CHOICE
```

This split is required. Otherwise `PROHIBITED` (do not adopt this new
state) collapses into “never touch this code,” and `CONSTRAINED` (fix it
within bounds) becomes inexpressible next to `CONFLICTS`.

### Pressure-test notes (frozen)

```text
CONFORMS     ≠  DELEGATED
CONFLICTS    ≠  PROHIBITED
```

Typical pairings, not inferences:

```text
current implementation CONFORMS
future choice still governed
    → adoption MAY be DELEGATED or CONSTRAINED
    → residual RELATED_IMPLEMENTATION_CHOICE is often CONSTRAINED

authority:
    "Changes to payment provider selection require security approval."
program change: mechanically sound
conformance: CONFORMS
decision right: APPROVAL_REQUIRED
    → code is not invalid merely because approval is required

new state CONFLICTS with applicable authority
    → ADOPT_OR_KEEP_NEW_PROGRAM_STATE is typically PROHIBITED
    → REVISE_TOWARD_CONFORMANCE is typically CONSTRAINED
      (the agent may change the code toward conformance)

AUTHORITY_CONFLICT unresolved
    → affected decision right cannot become DELEGATED
      merely because one item would permit the change
```

Do not derive decision rights from source standing alone. Two
AUTHORITATIVE statements can still conflict. `AUTHORITATIVE` is not a
delegation grant.

Do not derive `DELEGATED` from:

```text
case_result = NO_APPLICABLE_AUTHORITY
maintenance = HOLD
impact = UNAFFECTED
conformance = CONFORMS
```

Licensed absence of selected authority is `NOT_ESTABLISHED` here.
Whether orchestration treats that as ordinary coding autonomy is an
execution-policy question, not an adjudication finding.

### Conservative aggregation

Per-item implications remain visible. Case-level `outcome` for the
default subject is a conservative join, not an average.

Restrictiveness, when rights are established and not in authority
conflict:

```text
PROHIBITED > APPROVAL_REQUIRED > CONSTRAINED > DELEGATED
```

`UNKNOWN` and `NOT_ESTABLISHED` do not weaken a more restrictive
established right. They do prevent a `DELEGATED` rollup.

If applicable items conflict on the right itself, case-level outcome is
`UNKNOWN` and `adjudication_state` is `AUTHORITY_CONFLICT`.

## No synthetic durable policy

The adjudicator MAY interpret:

```text
"Checkout must access providers through PaymentGateway."
```

and conclude for this case that a direct `StripeClient` use conflicts
with it.

It MUST NOT persist a universal generated rule such as:

```text
forbid_call(Checkout, StripeClient)
```

as authoritative truth.

The interpretation remains case-local. Repeated similar interpretations
MAY later motivate ordinary software. That promotion is outside this
milestone and would still not replace the original ADR.

## Unknown propagation

Conservative. Unknown never collapses to false or absence.

```text
applicability = UNKNOWN
    → conformance cannot be CONFORMS or CONFLICTS
    → conformance = UNKNOWN
    → decision right for that item cannot be DELEGATED

applicability = DOES_NOT_APPLY
    → conformance = NOT_APPLICABLE
    → that item does not contribute a PROGRAM_CONFLICT

program finding = UNKNOWN
    → dependent conformance = UNKNOWN
    → do not emit CONFLICTS from the unknown finding

required program context missing
    → context_sufficiency = INSUFFICIENT
    → adjudication_state = INSUFFICIENT_CONTEXT
    → dependent conformance = UNKNOWN

AUTHORITY_CONFLICT unresolved
    → affected decision right cannot become DELEGATED
    → adjudication_state = AUTHORITY_CONFLICT
    → do not pick a winner to unlock CONFORMS

HEURISTIC_LINEAGE_MATERIAL
    → dependent finding cannot be settled TRUE/FALSE
    → dependent conformance = UNKNOWN unless an independent
      new-side fact establishes the proposition

case_result = UNRESOLVED or NO_ATTACHMENT_FOUND
    → adjudicator MUST NOT conclude that no other authority exists
    → decision_right is UNKNOWN or NOT_ESTABLISHED, never DELEGATED
```

Complete attachment selection does not make conformance `CONFORMS`.
See [Completeness](#interaction-with-completeness).

## HEURISTIC correspondence

The case MAY contain `CONTINUED + HEURISTIC`. Heuristic correspondence
does not automatically make adjudication impossible.

Two shapes:

### Independent new-side fact (may proceed)

The new program context independently identifies the relevant new
manifestation and establishes the needed program fact.

Example: unique continuation of call site `C` plus a retargeted
`program_invokes` row naming `cancelSubscription` on the new snapshot.
The finding “the continued initial action invokes cancelSubscription”
rests on the new relation tuple, not on equating old and new bodies.

Record:

```text
heuristic_correspondences: present (uncertainty preserved)
heuristic_dependence: NOT_MATERIAL
```

Adjudication MAY proceed. The heuristic basis remains visible.

### Identity assumption (material uncertainty)

The conclusion depends on assuming:

```text
old manifestation == new manifestation
```

Example: arguing that confirmation is still enforced because the old
body enforced it and correspondence is `CONTINUED`, without new-side
behavior or supplied new source.

Record:

```text
heuristic_dependence: MATERIAL
program finding: UNKNOWN
conformance: UNKNOWN
```

Do not launder heuristic lineage into a settled program fact.

Ambiguous continuation is stronger than heuristic unique continuation:
do not pick a candidate. Include all candidates. Findings that need a
single target remain `UNKNOWN` unless every candidate yields the same
finding from supplied evidence.

## Old implementation is evidence, not authority

Do not assume:

```text
old code was compliant
```

The old implementation MAY help explain what changed. It is not
authoritative because it existed before.

Representable:

```text
old and new both conflict with the requirement
    → new-state conformance CONFLICTS
    → the delta need not have introduced the conflict

new code fixes an existing conflict
    → optional prior_state_conformance CONFLICTS
    → new-state conformance CONFORMS
```

Contrast findings about the old state belong in `program_findings[]`
with `side: OLD` or in `prior_state` on a conformance row. They MUST
NOT enter `authority_findings[]`.

## Case-selection reason is not adjudication evidence

`selected_because` explains why the authority entered the case.

It is not proof that the authority applies or that code conflicts.

Do not treat `GOVERNED_SURFACE_CHANGED` or `ATTACHMENT_GROUNDS_CHANGED`
as normative facts.

## Interaction with completeness

Adjudication operates on the case. It MUST NOT infer:

```text
no other authority exists
```

unless the case carries completeness that licenses that conclusion
(`case_result = NO_APPLICABLE_AUTHORITY` plus its documented
preconditions).

Even then, that license is about **attachment/relevance coverage for the
declared purpose/universe**, not about program-behavior completeness or
decision rights.

Separate:

```text
complete authority selection
    ≠
SUFFICIENT program context
    ≠
CONFORMS
    ≠
DELEGATED
```

A case MAY have complete selection and still `UNKNOWN` conformance
because program semantics are insufficient.

`NO_ATTACHMENT_FOUND` and case `UNRESOLVED` forbid “no authority
applies” and forbid `DELEGATED`.

## Adjudicator freedom and hard guarantees

The adjudicator is allowed to perform intelligent semantic
interpretation. That is the point of this layer.

Natural-language interpretation is not deterministic. Different capable
adjudicators MAY reason differently. The architecture makes those
differences inspectable.

Hard guarantees concern:

```text
what evidence it receives          the case, not the corpus
what it may treat as authority     AUTHORITATIVE reconstructed text
what conclusions it may emit       the vocabularies in this contract
how uncertainty is represented     three-valued; unknown propagation
what provenance it must preserve   observation, finding, and delta refs
```

It MUST NOT invent mechanical program facts the case does not support.
Where the spine can establish a fact, prefer `basis: MECHANICAL`.

## Reproducibility

Do not promise deterministic adjudication if it is model-driven.

```text
case assembly:
    deterministic

adjudication:
    evidence-bounded but potentially nondeterministic
```

Record:

```text
adjudicator.kind
adjudicator.identity
adjudicator.version
adjudicator.configuration     inspectable, not a hidden prompt dump
case_id
contract / schema version
```

Do not persist private reasoning, hidden prompts, or chain-of-thought as
provenance. Concise evidence-oriented rationale is not private
reasoning.

Identical case + identical deterministic check SHOULD reproduce. Identical
case + model adjudicator NEED NOT.

## Adjudicator kinds

The schema MUST NOT assume an LLM.

```text
HUMAN
MODEL
DETERMINISTIC_CHECK
```

`HUMAN` produces the same artifact. Identity is a person or role id.

`MODEL` records model identity and available configuration. It is not a
license to search or to write Worlds.

`DETERMINISTIC_CHECK` MAY emit findings that follow from case tuples
without natural-language interpretation (for example: a
`forbids_import` claim plus an added `program_imports` row). It is still
case-local. It MUST NOT compile a durable lint rule. If the original
wording carries unrepresented conditions, a check MUST yield `UNKNOWN`
rather than overclaim `CONFLICTS`.

A later system MAY combine kinds. Consensus machinery is **DEFERRED**.

## Artifact schema

Conceptual record. Field names are normative for v0 JSON.

```text
adjudication_id
contract: governance_adjudication/v0
case_id
adjudication_version: 0

adjudicator:
  kind                      HUMAN | MODEL | DETERMINISTIC_CHECK
  identity
  version
  configuration             optional inspectable map; no hidden prompt

context_sufficiency:
  status                    SUFFICIENT | INSUFFICIENT | UNKNOWN
  reasons[]

authority_findings[]:
  finding_id
  observation_ids[]         AUTHORITATIVE only
  attachment_refs[]         selection rows that presented the item
  applicability             APPLIES | DOES_NOT_APPLY | UNKNOWN
  interpretation_summary    short; original-text-oriented
  relevant_qualifiers[]     modality, exceptions, scope as read
  supporting_case_facts[]   program ids, tuples, source_evidence ids
  supporting_context_refs[] supporting_material ids, standing visible
  selected_because_ignored  true  (selection is not evidence)
  finding_context           SUFFICIENT | INSUFFICIENT | UNKNOWN
  context_reasons[]
  evidence_refs[]
  applicability_basis       required when DOES_NOT_APPLY

program_findings[]:
  finding_id
  proposition
  truth_value               TRUE | FALSE | UNKNOWN
  side                      NEW | OLD | COMPARISON
  basis                     MECHANICAL | INTERPRETIVE
  heuristic_dependence      NOT_MATERIAL | MATERIAL | UNKNOWN
  evidence_refs[]           mechanical and/or source observation refs
  finding_context           SUFFICIENT | INSUFFICIENT | UNKNOWN
  context_reasons[]
  limitations[]

conformance_findings[]:
  finding_id
  authority_finding_refs[]
  program_finding_refs[]
  result                    CONFORMS | CONFLICTS | UNKNOWN
                            | NOT_APPLICABLE
  prior_state               optional CONFORMS | CONFLICTS | UNKNOWN
                            (old state; never authority)

authority_conflicts[]:
  conflict_id
  authority_finding_refs[]
  issue                     what is incompatible
  precedence                UNESTABLISHED | EXPLICIT_IN_CASE
  resolution                unresolved; do not pick a winner

decision_right:
  subject                   ADOPT_OR_KEEP_NEW_PROGRAM_STATE
  outcome                   DELEGATED | CONSTRAINED | PROHIBITED
                            | APPROVAL_REQUIRED | UNKNOWN
                            | NOT_ESTABLISHED
  authority_basis[]         authority_finding_refs
  related_rights[]
    subject
    outcome
    authority_basis[]

unresolved_questions[]
context_requests[]

rationale[]:
  statement
  evidence_refs[]           observation, finding, delta, source_evidence
  supports                  finding_ids or decision_right.subject

case_summary                short; must not replace the dimensions

adjudication_state:
  RESOLVED
  | UNRESOLVED
  | AUTHORITY_CONFLICT
  | INSUFFICIENT_CONTEXT

known_limitations[]
empty_case_note             optional; when case_result ≠ SELECTED
```

No numeric confidence. No PASS/FAIL. No hidden chain-of-thought.

`adjudication_id` SHOULD be content-addressed over the inspectable
fields excluding any later-added non-normative annotations. Model
adjudications that differ will differ in id. That is expected.

## Rationale

Inspectable, evidence-oriented, concise.

```text
Authority requires the initial cancellation action to enter
the retention flow.

The new call-site relation targets cancelSubscription directly.

Therefore this change conflicts with the applicable authority.
```

Every material statement MUST link back to case evidence through
`rationale[].evidence_refs` or the finding-level refs.

Do not persist long free-form deliberation. Do not persist private
scratch reasoning.

## Top-level adjudication state

Does not replace the detailed dimensions.

```text
RESOLVED
    the questions this adjudication attempted are answered
    without blocking uncertainty
    ≠ compliant
    ≠ delegated
    ≠ execute

UNRESOLVED
    residual uncertainty that is not specifically missing
    context or an unresolved authority conflict
    (applicability UNKNOWN after sufficient context, material
    heuristic dependence, incomplete attachment coverage, …)

AUTHORITY_CONFLICT
    authoritative materials conflict and precedence is
    unestablished

INSUFFICIENT_CONTEXT
    needed program or authority evidence is not in the case
```

If several apply, the recorded state is the most specific block:

```text
INSUFFICIENT_CONTEXT > AUTHORITY_CONFLICT > UNRESOLVED > RESOLVED
```

Resolved items remain in the arrays. Compact state MUST NOT erase them.

## Empty cases

| `case_result` | Adjudication |
| --- | --- |
| `SELECTED` | Interpret presented items. |
| `NO_APPLICABLE_AUTHORITY` | No authority items to interpret. `authority_findings` empty. `decision_right` `NOT_ESTABLISHED`. `adjudication_state` `RESOLVED` only as “nothing to interpret under licensed absence,” never as PASS. Completeness remains the case’s claim; the adjudicator MUST NOT widen it. |
| `NO_ATTACHMENT_FOUND` | MUST NOT conclude absence of authority. `decision_right` `UNKNOWN`. `adjudication_state` `UNRESOLVED`. |
| `UNRESOLVED` | MUST NOT conclude absence. `adjudication_state` `UNRESOLVED` or `INSUFFICIENT_CONTEXT` if comparison/capability gaps are the block. |

Empty never means PASS.

## Validation (when a writer exists)

A later writer/validator MUST reject at least:

- `case_id` mismatch;
- observation refs not in the case;
- governing citations of `supporting_material` or unresolved construction;
- `selected_because` used as applicability or conformance evidence;
- `CONFORMS`/`CONFLICTS` when applicability is `UNKNOWN`;
- `CONFLICTS` when dependent program findings are `UNKNOWN`;
- omitted unknown-propagation (e.g. `DELEGATED` under `AUTHORITY_CONFLICT`);
- `PASS`/`FAIL`/`COMPLIANT`/`VIOLATION` fields;
- numeric confidence;
- program findings written as World mutations;
- durable generated policy rules as authority.

## Relation to execution

Not implemented. The boundary is:

```text
GovernanceAdjudication
        ↓
agent-decision orchestration     deferred
        ↓
continue / revise / request approval / seek more context
```

Do not make those actions synonymous with conformance.

Minimum outputs a future orchestrator needs:

```text
adjudication_state
decision_right.subject + outcome + related_rights
context_requests[]
per-item conformance and applicability
authority_conflicts[]
unresolved_questions[]
known_limitations[]
```

Suggested (non-normative) reads, not policy:

```text
INSUFFICIENT_CONTEXT     → seek more context (satisfy ContextRequest)
AUTHORITY_CONFLICT       → do not auto-execute; surface the conflict
APPROVAL_REQUIRED        → request approval, even if CONFORMS
PROHIBITED on adopt      → do not keep the new state as-is
CONSTRAINED              → continue only within interpreted bounds
NOT_ESTABLISHED          → execution policy, not a governance grant
RESOLVED + CONFORMS      → not an automatic ship
```

Orchestration policy is **DEFERRED**.

The downstream adoption-boundary design is documented in
[`GOVERNED_CANDIDATE_LIFECYCLE.md`](GOVERNED_CANDIDATE_LIFECYCLE.md). It
introduces no adjudication fields: a future `CandidateAdoptionDecision` is a
separate workflow artifact produced by an explicit `AdoptionPolicy`. In
particular, `NOT_ESTABLISHED` remains distinct from any project-declared
default-freedom fallback.

## Experimental kernel types

Inspected as implementation evidence only. They do not define this
architecture.

| Existing type | Why it is not this artifact |
| --- | --- |
| experimental kernel `Adjudication` | Immutable selection of a `Commitment` under a construction `Contract`, with `source_id` in an admission basis. SUFFICIENT/INSUFFICIENT. Not case interpretation. |
| experimental `Obligation` / `Resolution` | Durable construction questions and read-state. Not governance cases. |
| `ConstructionOrigin.ADJUDICATED` | Coarse support-path label. No case, no applicability, no decision right. |
| `profiles/design_account_settings` `GeneratedObligation` | Fixture-local compilation. Forbidden here as durable policy. |

Reuse only the idea that a recorded decision is distinct from the
authority used to assess it. Do not retrofit this contract onto those
types.

## Worked examples

These are adjudication *examples*. They MUST NOT be hardcoded into
infrastructure as the only legal outcomes. Another capable adjudicator
MAY differ; it MUST still use these vocabularies and provenance rules.

### Example 1 — cancellation retarget

Case (already assembled):

```text
authority (AUTHORITATIVE, exact text):
    The initial "Cancel subscription" action enters the retention flow.

    Cancellation occurs only after confirmation on the final
    cancellation screen.

old:  initial call site -> openRetentionFlow
new:  initial call site -> cancelSubscription
CONTINUED + HEURISTIC
program_invokes RETARGETED
selected_because:
    ATTACHMENT_GROUNDS_CHANGED
    GOVERNED_SURFACE_CHANGED
```

A grounded reading:

```text
authority item 1 (retention entry):
    applicability:     APPLIES
    cites:             reconstructed paragraph 1
    case facts:        new program_invokes(C', cancelSubscription)

program finding P1:
    proposition:       "The initial cancellation action enters
                        the retention flow."
    truth_value:       FALSE
    basis:             MECHANICAL
    heuristic_dependence: NOT_MATERIAL
    evidence:          new program_invokes tuple

conformance item 1:    CONFLICTS

authority item 2 (confirmation):
    applicability:     APPLIES
    program finding:   UNKNOWN
                       (retarget does not establish confirmation)
    conformance:       UNKNOWN
    optional ContextRequest:
        body of cancelSubscription
        reason: PROGRAM_BEHAVIOR_NOT_REPRESENTED

decision_right:
    subject: ADOPT_OR_KEEP_NEW_PROGRAM_STATE
    outcome: PROHIBITED
    basis:   item 1 CONFLICTS
    related: REVISE_TOWARD_CONFORMANCE = CONSTRAINED

adjudication_state:    UNRESOLVED
                       (item 2 still unknown; item 1 is settled)
                       or RESOLVED if the adjudicator only attempted
                       the invocation question and recorded item 2
                       as out of scope for this change
                       — either is inspectable; hiding item 2 is not
```

Heuristic correspondence is present but not the basis for P1. The new
relation tuple independently names the new target.

No verdict field. No generated `forbid_call` rule.

### Example 2 — body change, insufficient semantics

```text
authority:  Cancellation occurs only after final confirmation.
attachment: cancelSubscription
impact:     AFFECTED          (source_manifestation)
maintenance: HOLD
case:       manifestation changed; no callable body text
```

```text
applicability:         APPLIES
context_sufficiency:   INSUFFICIENT
reasons:               PROGRAM_BEHAVIOR_NOT_REPRESENTED
program finding:       UNKNOWN
                       "confirmation is still enforced"
conformance:           UNKNOWN
decision_right:        UNKNOWN
ContextRequest:        NEW IMPLEMENTATION of cancelSubscription
adjudication_state:    INSUFFICIENT_CONTEXT
```

Do not infer `CONFLICTS` from the body change. `AFFECTED` is not
nonconforming.

### Example 3 — bounded source evidence resolves it

Same authority and attachment as example 2. The case (or a later
satisfied `ContextRequest`) includes grounded new callable source:

```text
if (!confirmed) return;
...
```

```text
program finding:
    proposition:  "The changed implementation still prevents
                   cancellation before confirmation."
    truth_value:  TRUE
    basis:        INTERPRETIVE
    evidence:     program_context.source_evidence for the new callable
conformance:      CONFORMS
decision_right:
    ADOPT_OR_KEEP_NEW_PROGRAM_STATE: CONSTRAINED
    (confirmation bound remains; adoption of this conforming body
     is allowed within that bound)
adjudication_state: RESOLVED
```

The adjudicator read supplied source. It did not search the repository.
`RESOLVED` does not mean unconstrained.

If the supplied body omitted confirmation, `truth_value: FALSE` and
`CONFLICTS` are available on the same path.

### Example 4 — architectural ADR

Authority (exact ADR wording remains controlling):

```text
Checkout must access payment providers through PaymentGateway.
```

Change: new direct `StripeClient` call added under the attached
Checkout program identity.

```text
applicability:     APPLIES
program finding:   TRUE
                   "Checkout (or the attached manifestation) invokes
                    StripeClient directly."
                   basis MECHANICAL (program_invokes / equivalent
                   tuple in the case)
conformance:       CONFLICTS
decision_right:
    ADOPT_OR_KEEP_NEW_PROGRAM_STATE: PROHIBITED
    RELATED_IMPLEMENTATION_CHOICE:   CONSTRAINED
        (access providers through PaymentGateway)
adjudication_state: RESOLVED
```

Do not reduce the ADR to `forbid_call(Checkout, StripeClient)` as
authority. The finding is a case-local interpretation of the original
sentence.

### Example 5 — approval required

Authority:

```text
Changing the payment provider requires security approval.
```

Suppose the code change changes providers, through `PaymentGateway`, and
is mechanically sound.

```text
applicability:     APPLIES
program finding:   TRUE  "payment provider selection changed"
conformance:       CONFORMS
                   (the requirement reserves a decision; it does not
                    by itself declare the technical shape invalid)
decision_right:
    subject: ADOPT_OR_KEEP_NEW_PROGRAM_STATE
    outcome: APPROVAL_REQUIRED
adjudication_state: RESOLVED
```

Conformance and decision right are different questions. The code is not
called invalid merely because approval is required. Orchestration, not
this artifact, requests approval.

### Example 6 — conflicting authority

Two AUTHORITATIVE observations:

```text
A: cancellation must always enter retention
B: enterprise plans bypass retention
```

The case does not establish which scope applies.

Do not pick one.

Representable shape 1 — missing discriminator:

```text
A applicability: UNKNOWN or APPLIES-with-qualifier-unverified
B applicability: UNKNOWN
context_sufficiency: INSUFFICIENT
reasons: MISSING_SCOPE_DISCRIMINATOR
ContextRequest: plan/context fact needed to apply B's exception
decision_right: UNKNOWN
adjudication_state: INSUFFICIENT_CONTEXT
```

Representable shape 2 — both read as currently governing and incompatible:

```text
A: APPLIES
B: APPLIES
authority_conflicts[]: A vs B on retention entry
precedence: UNESTABLISHED
decision_right: UNKNOWN   (not DELEGATED from B)
adjudication_state: AUTHORITY_CONFLICT
```

Either is valid interpretation. Silently dropping A or B is not.
Standing alone does not prefer A or B.

## GovernanceCase program source

v0 case assembly now emits `program_context.source_evidence[]` under the
inclusion rules above. Reconstruction uses sealed digest-addressed
`program_inputs` blobs next to the spine/governed World. If blobs or
byte ranges are missing, the case records `reconstruction: FAILED` and
a known omission. Adjudication MUST then `ContextRequest` rather than
open the repository.

## Kernel reuse

| Need | Reuse |
| --- | --- |
| Case evidence | `GovernanceCase` sidecar values |
| Exact authority text | case `authority.observations` |
| Standing | case partition; `authority_source` already applied |
| Mechanical program facts | case `program_context` / triggering deltas |
| Program source ranges | existing spine `SourceObservation` on identities |
| Open-world | three-valued findings; completeness not widened |
| Unresolvedness | `UNKNOWN`, `INSUFFICIENT_CONTEXT`, `ContextRequest` |
| Sealed Worlds | still untouched |
| Experimental `Adjudication` | **not reused** |

No new kernel primitive is required.

## Kernel limitations

1. No cross-World FKs. The case already copied cited tuples.
2. No Claim primitive. Findings cite assertion ids and propositions.
3. Completeness cannot mean “the corpus is understood.”
4. Spine `source_manifestation` is digest plus location; body-vs-whitespace
   remains coarse. Adjudication MUST NOT invent behavior from that flag.
5. Kernel `ConstructionOrigin.ADJUDICATED` is not this record.
6. Semantic `query_sql` is irrelevant here; the adjudicator reads the case.
7. Program source bytes are not a kernel primitive. v0 reconstructs from
   application `program_inputs` blobs beside the sealed World, addressed
   by the observation digest. Missing blobs are reconstruction failure,
   not a license to open the workspace.

Awkward interpretation is not a kernel case.

## Intentionally deferred

- Deterministic case expansion that satisfies `ContextRequest`.
- Agent-decision orchestration and execution gating.
- Human approval workflow.
- Universal policy language / generated lint rules.
- Multi-adjudicator consensus.
- Persisting findings into a World.
- `AuthorityDelta`, repair search, source lineage.
- Numeric confidence.

Success condition for this design:

> an intelligent or human adjudicator can receive a bounded, inspectable
> GovernanceCase and produce a grounded case-specific interpretation of
> applicability, program facts, conformance, uncertainty, and decision
> rights—without discovering new authority, pretending unknown is false,
> compiling prose into permanent rules, or conflating its judgment with
> the coding agent's eventual action.

# CLASS_MEMBERSHIP semantic-persistence experiment

This milestone tests whether a positive semantic-class membership judgment
can be constructed once, persisted as a snapshot commitment, and later reused
deterministically when its complete material interpretation basis is
unchanged — without creating a new semantic assertion or invoking a model
merely because the program snapshot changed.

It does not introduce `SemanticClassDefinition`, a class resolver, automatic
`MembershipGap` → `ConstructionObligation` conversion, `NON_MEMBER`, or a
World-kernel change.

## Obligation

```text
ConstructionObligation
  kind: CLASS_MEMBERSHIP
  semantic_class: semantic:PaymentProvider
  program_subject: exactly one snapshot-local manifestation
  relation: semantic_program_membership   # trusted; not model-chosen
  admission_profile: semantic-class-membership/v1
```

The program subject is fixed by the deterministic gap. The model does not
choose it. v0 results are `MEMBER | UNRESOLVED`. Absence of positive evidence
is `UNKNOWN`, never `NON_MEMBER`.

## Trusted relation

```text
semantic_program_membership(semantic_class, program_manifestation)
```

Meaning: in this program snapshot, the supplied manifestation was established
as belonging to the class under the recorded construction evidence and
purpose. It does not imply cross-snapshot membership.

## Model-facing schema

The constructor receives only the obligation, the case-scoped catalog, and a
schema whose enums are catalog aliases. Output:

```text
result: MEMBER | UNRESOLVED
authority_evidence_aliases
program_source_evidence_aliases
mechanical_evidence_aliases
maintenance_dependency_aliases
```

No relation name, no program subject, no canonical IDs, no persistence
decision.

## Admission

`semantic-class-membership/v1` admits `PERSIST_COMMITMENT` only for `MEMBER`
with declared class/subject, resolved endpoints, required authority, program
source, and mechanical grounding, `support != HYPOTHESIZED`, and inspectable
maintenance dependencies. `UNRESOLVED` or missing grounding is
`RECORD_UNRESOLVED`. The profile does not emit `PERSIST_SNAPSHOT_FACT`.
Materialization copies a sealed World, writes, validates, and seals
atomically.

## Interpretation basis

An admitted commitment stores `semantic_class_membership_basis` with a
canonical package:

```text
semantic_class
program subject kind + identity descriptor
class grounding: source handle + content digest
program source: native handle + content digest
mechanical facts: relation tuples rewritten with descriptors
structural descriptor chain
construction profile/version
canonicalized maintenance dependencies
```

Excluded: assertion IDs, snapshot IDs, observation IDs, chain-of-thought.

`interpretation_basis_digest` hashes that package. Incidental ID changes with
identical material content do not change the digest. Source-body, class-
grounding text, or selected mechanical tuple changes do.

## ClassMembershipEvidence

```text
ESTABLISHED_CURRENT     current admitted semantic_program_membership
PRESERVED_IDENTICAL_BASIS
    prior admitted digest == reconstructed current digest
    materialized_current_assertion = false
UNKNOWN                 otherwise; never NON_MEMBER
```

Program correspondence may locate a prior commitment. It is never itself
membership evidence.

## MembershipGap

Application diagnostic, not an obligation:

```text
NO_CURRENT_OR_REUSABLE_MEMBERSHIP_EVIDENCE
```

The invariant evaluator consumes `ClassMembershipEvidence`. It does not
reconstruct semantic meaning and does not invoke a model.

## Snapshot results (deterministic control path)

Model invocations during evaluation/reuse: **0**.

| Snapshot | Membership | Invariant |
| --- | --- | --- |
| C3 before construction | `settleExternal = UNKNOWN`, gap emitted | UNKNOWN |
| C3 after control MEMBER persist | `ESTABLISHED_CURRENT`, `gateway_reachable = false` | FALSE |
| C4 | `recordAudit = UNKNOWN` | UNKNOWN |
| C3a unrelated `logCheckoutStep` | `PRESERVED_IDENTICAL_BASIS`, no C3a membership assertion | FALSE |
| C3b `settleExternal` body change | current digest ≠ admitted digest, gap emitted | UNKNOWN |

Live Composer 2.5 construction is a separate path. A bounded no-tool run
(`cursor-agent --model composer-2.5`, `system/init.model = Composer 2.5`,
zero tool events) returned:

```json
{
  "result": "UNRESOLVED",
  "authority_evidence_aliases": ["A1"],
  "program_source_evidence_aliases": ["S1"],
  "mechanical_evidence_aliases": ["M1"],
  "maintenance_dependency_aliases": ["D1", "D2", "D3"]
}
```

Deterministic compilation/admission of that draft is `RECORD_UNRESOLVED`.
That is an honest live result: the supplied C3-shaped catalog did not
establish commitment-grade membership. Reuse mechanics are therefore proven
with a deterministic valid `MEMBER` control, kept separate from the live
path. No `NON_MEMBER` was produced.

## Falsification findings

Reported, not patched around:

- A live constructor that used unrecorded repository/tool context would make
  the basis incomplete (`INTERPRETATION_BASIS_INCOMPLETE`). The observed live
  Composer run used no tools. Its `UNRESOLVED` judgment still depends on
  model interpretation of the supplied catalog; that judgment was not
  persisted, so reuse was not claimed for it. The deterministic `MEMBER`
  control path treats selected catalog evidence as the complete reusable
  material input.
- Correspondence, including HEURISTIC correspondence, is insufficient for
  `PRESERVED_IDENTICAL_BASIS`.
- Unrelated checkout edits did not invalidate a basis keyed to
  `external-settlement.ts` and the settle invoke. That is desired, not a
  false-negative, for this warrant.
- `PRESERVED_IDENTICAL_BASIS` is inspectably distinct from semantic renewal:
  no current `semantic_program_membership` row is written.
- Invariant evaluation stays a consumer of membership evidence.

## Next question

The experiment justifies **manual** `MembershipGap` → `CLASS_MEMBERSHIP`
construction. A follow-on milestone now asks whether a bounded deterministic
gap can safely create the obligation without executing it:

[MembershipGap → CLASS_MEMBERSHIP obligation synthesis](SEMANTIC_MEMBERSHIP_GAP_SYNTHESIS.md)


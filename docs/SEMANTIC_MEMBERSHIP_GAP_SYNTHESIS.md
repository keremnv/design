# MembershipGap → CLASS_MEMBERSHIP obligation synthesis

This milestone tests whether a bounded deterministic semantic gap can be
converted into the exact `CLASS_MEMBERSHIP` `ConstructionObligation` needed
to resolve it, without semantic interpretation, repository search, or model
execution.

It does not invoke Composer, admit a candidate, or change the World kernel.

## Lifecycle boundary

```text
DETECTION
    deterministic consumer exposes missing fact
        ↓
    MembershipGap

FORMULATION
    deterministic synthesis expresses missing fact
    as a bounded ConstructionObligation
        ↓
MATERIALITY
    GovernanceCaseReadiness decides whether that obligation
    is required for this case
        ↓
    STOP before execution

RESOLUTION
    semantic constructor may answer a required obligation later

ADMISSION
    deterministic contract decides persistence

REUSE
    deterministic evidence machinery may avoid
    future resolution when basis is preserved
```

Obligation creation and obligation execution are separate operations.

## Synthesis API

```text
synthesize_class_membership_obligation(gap, context)
    -> SynthesizedClassMembershipObligation
    |  ObligationSynthesisFailure

collect_pending_class_membership_obligations(gaps, context)
    -> PendingConstructionObligations
```

`PendingConstructionObligations` is an application view of explicitly
generated obligations. It is not a scheduler and does not scan a World for
work.

## Mapping

For the supported gap:

```text
MembershipGap
    semantic_class = semantic:PaymentProvider
    program_subject = settleExternal@C3
    snapshot = <C3 snapshot>
    requested_by = CheckoutProviderBoundary definition
    reason = NO_CURRENT_OR_REUSABLE_MEMBERSHIP_EVIDENCE
```

synthesis copies class and subject and produces:

```text
ConstructionObligation
    kind = CLASS_MEMBERSHIP
    semantic_class = semantic:PaymentProvider
    program_subject = settleExternal@C3
    admission_profile = semantic-class-membership/v1
```

The class and subject are copied, not interpreted. The synthesis step does
not choose a different referent.

Construction context retained on the synthesis record, not as a source
bundle:

```text
semantic class
program subject
snapshot
declared scope
requesting invariant(s)
required construction profile
```

A later constructor may assemble the bounded catalog from those references.
The obligation names the question; it does not package the evidence.

## Identity and deduplication

```text
obligation_id = digest(
    obligation_kind,
    semantic_class,
    snapshot-local program subject,
    snapshot,
    purpose,
    program_scope,
    synthesis profile/version
)
```

Not included: timestamp, run id, random UUID, or MembershipGap instance id.

Equivalent gaps in the same semantic context synthesize the same obligation
identity. Two consumers that need the same fact share one obligation and
retain multiple `requested_by` provenance links.

If purpose or declared scope materially changes the construction question,
the identities stay distinct.

`PaymentProvider(settleExternal@C3)` and
`PaymentProvider(settleExternal@C3b)` are different questions unless
membership lookup already returned `PRESERVED_IDENTICAL_BASIS`. In that
preserved case there is no gap and no obligation.

## Provenance

```text
trigger: MEMBERSHIP_GAP
trigger_gap_id / trigger_gap_ids
requested_by
source_snapshot
gap_reason
generation_method: DETERMINISTIC_GAP_SYNTHESIS
generation_profile: membership-gap-obligation-synthesis/v1
```

The gap remains. `MembershipGap.construction_obligation` stays `None`.

## Suppression

Synthesis reacts only to supplied gaps. It does not scan the World.

```text
ESTABLISHED_CURRENT     -> no gap -> no obligation
PRESERVED_IDENTICAL_BASIS -> no gap -> no obligation
UNKNOWN + supported gap -> CLASS_MEMBERSHIP obligation
```

If synthesis is called with an explicit resolved membership status, the
result is `NOT_REQUIRED` / `MEMBERSHIP_ALREADY_RESOLVED`.

## Failure

Malformed or incomplete gaps do not produce obligations:

```text
CANNOT_SYNTHESIZE
    MISSING_SEMANTIC_CLASS
    MISSING_PROGRAM_SUBJECT
    MISSING_SNAPSHOT
    MISSING_REQUESTING_CONSUMER
    MISSING_AUTHORITY_REFS
    UNSUPPORTED_GAP_KIND
    AMBIGUOUS_SCOPE
    MALFORMED_GAP
```

## What this is not

The generated obligation means the semantic fact is a valid unresolved
question. It does not mean Composer can answer it, that the subject is a
`NON_MEMBER`, that the obligation should be executed, or that the current
governance case requires it. Materiality is a later stage:

[GovernanceCase readiness: pending vs required construction](SEMANTIC_CASE_READINESS.md)

No preferred model, confidence, expected `MEMBER` result, queue priority,
retry, or background execution is attached.

## Tests

`tests/test_membership_gap_obligation_synthesis.py` covers the mapping,
copy-exact class/subject, snapshot scope, provenance, stable identity,
deduplication, distinct subjects/snapshots, C3/C3a/C3b/C4 suppression and
regeneration, C4 open-world unknown, fan-out, duplicate consumers, existing
CLASS_MEMBERSHIP catalog/schema compatibility, explicit synthesis failure,
zero model invocation, zero repository search, and the absence of World-kernel
coupling.

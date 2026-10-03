# Software Governance Judgment Contract v0

Status: accepted Judgment v0, 2026-09-24. This is not Core Product v1
authority and not part of the accepted Construction v0 baseline. It does
not define change processing, retrieval, maintenance, decision rights, or
agent execution.

The production package is `ontology_author.software_governance.judgment`.
The mail and config evaluators live in their profiles. Acceptance is
`tests/test_software_governance_judgment.py`, recorded in
[SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md).

```text
SEALED CONSTRUCTION WORLD
    governance propositions
    governance bindings
    software subjects
    producer-owned mechanical facts
    unresolvedness
        ↓
explicit case assembly
        ↓
JUDGMENT
        ↓
inspectable judgment artifact
```

Judgment consumes a sealed Software Governance Construction World. It does
not construct governance knowledge, repair bindings, or mutate that World.

## 1. Question

Given governance knowledge and the bounded software facts in a case, what
can we conclude, what can we not conclude, and exactly why?

Domain meaning stays in the profile evaluator. There is no universal policy
evaluator and no policy language.

## 2. Case assembly

A case is explicit presentation of known proposition and subject ids. It is
not change-based selection, and it is not the World.

Being in the case does not mean the proposition applies and does not mean
the software conflicts. The mail experiment presents the outbound-mail
proposition with the `notificationGatewaySend` callable. The config
experiment presents the customer-export proposition with the health route.
Both cases assemble. Both applicability results are `DOES_NOT_APPLY`.

The tested case records:

```text
case identity
judgment question
sealed world id, revision, and address
selected proposition ids
selected SoftwareSubject ids
relations inspected
cited tuples
```

Each citation is:

```text
assertion_id
relation
values
support
support_fingerprint
```

`assertion_id` is the sealed World's identity for that tuple. The case is
not a World relation, so it may cite that id even though `RoleType` has no
`ASSERTION` value and semantic SQL hides the column. Verification looks the
id up in the sealed World and requires the cited values to be that row.
A custom digest of the relation and values duplicated this check and did
not cover grounding, so v0 does not use one.

`support` is the warrant's grounding bases, construction origins, and the
reconstructed text of the observations those bases name.
`support_fingerprint` is the digest of that support. Verification
recomputes it from the sealed warrant and from the support the case
presents. Both must match.

Referent labels are display text. Changing a label does not fail
verification.

The mail experiment rejected each of these mutations of a proposition
citation: changed values, changed reconstructed evidence, changed
construction origin, changed construction method, a removed grounding
observation, and an invented grounding observation.

Candidate rows, `governance_question` rows, and the completeness claim are
included when the case inspects them. Completeness is not negative evidence
that an unbound subject is ungoverned.

The evaluator reads the case. It does not reopen the World to fill a gap,
and it does not search a repository.

## 3. Applicability

```text
APPLIES
DOES_NOT_APPLY
UNKNOWN
```

These names were adequate for both profiles.

`DOES_NOT_APPLY` requires a positive reason cited from the case and from the
recorded rule. Failure to prove `APPLIES` is `UNKNOWN`. A missing binding
under `INCOMPLETE` coverage is not that positive reason.

Tested exclusions:

```text
mail:   software_subject.kind is callable
        rule.excludes_kind is callable

config: config_route.handler is Health
        rule.required_handler is CustomerExport
```

The same outbound-mail proposition against another resolved call site, with
no binding and no exclusion fact, stays `UNKNOWN`. The health route with
its `config_route` row omitted from the case also stays `UNKNOWN`. Neither
emits a request. Incomplete coverage is in the case and is not used as
negative evidence.

An established binding is not itself applicability. Applicability `APPLIES`
cites the binding and the subject of the ruled kind. A subject that is
merely present does not.

The approved-mailer proposition and the status-route proposition have
candidate rows and no established binding. That is a construction gap, not
`DOES_NOT_APPLY`.

## 4. Program finding

A program finding is the fact the judgment established about the software.
It is not a raw producer row, not the governance proposition, and not the
conformance result.

Tested findings:

```text
this call site's resolved target is notificationGatewaySend
this call site's resolved target is smtpClientSend
this call site has no unique resolved target
this route's path is /customers/export
this route's path is /internal/export
```

An established finding has status `ESTABLISHED`, the values it established,
and the assertion ids of the case tuples it used. An unresolved finding has
status `UNRESOLVED`. The experiment did not use a separate true/false value.
For these two profiles that value would have repeated conformance.

Findings stay in the artifact. They are not written back into the
construction World.

## 5. Conformance

Conformance is recorded only when applicability is `APPLIES`.

```text
CONFORMS
CONFLICTS
UNKNOWN
```

`CONFORMS` and `CONFLICTS` require an established program finding.
`UNKNOWN` is not `CONFLICTS` and is not false. A `MULTIPLE_CANDIDATES`
target stays `UNKNOWN`. A case that does not include the route path stays
`UNKNOWN`. Neither becomes a conflict.

When applicability is `DOES_NOT_APPLY` or `UNKNOWN`, conformance is absent.
An extra `NOT_APPLICABLE` conformance value only repeated applicability, so
v0 does not use it. A consumer answers "what conformance conclusion
followed?" with the recorded result, or with the fact that none was drawn.

## 6. Construction gap and judgment gap

These stay different requests. They are not one `INSUFFICIENT`.

```text
gap: construction | judgment
proposition
subject
need
property          empty when the need is not a property
availability: ABSENT
```

| Situation | Applicability | Conformance | Request |
| --- | --- | --- | --- |
| Candidate rows, no established binding (approved mailer; status route) | `UNKNOWN` | absent | `construction` / `established_binding` |
| Same kind, no binding, no exclusion, coverage `INCOMPLETE` | `UNKNOWN` | absent | none |
| Binding exists, route path not in the case | `APPLIES` | `UNKNOWN` | `judgment` / `subject_property` / `path` |
| Binding exists, resolution row is `MULTIPLE_CANDIDATES` | `APPLIES` | `UNKNOWN` | none |
| Recorded rule excludes the included subject | `DOES_NOT_APPLY` | absent | none |

A present `MULTIPLE_CANDIDATES` row, with the candidate rows that capability
recorded, is mechanical indeterminacy. The finding is `UNRESOLVED` and
conformance is `UNKNOWN`. Nothing required from the sealed World was
omitted, so there is no judgment request. That uncertainty is not missing
context.

`DOES_NOT_APPLY` is not a gap and not a negative program finding.

v0 does not record `context_sufficiency`. The historical scalar
`SUFFICIENT | INSUFFICIENT` repeated the request list when context was
missing, and it called `MULTIPLE_CANDIDATES` insufficient even though the
mechanical result was fully present. The distinctions below are carried by
the request, the finding status, and applicability.

The same request fields cover a call-site target and a route property. The
`need` values used here are `established_binding`,
`mechanical_target_resolution`, and `subject_property`. They name missing
information. They do not say "search the repository."

## 7. Artifact

The artifact is JSON outside the sealed World. After judgment, the World's
`world.sqlite` bytes are unchanged, and the artifact is not stored inside
the publication directory.

```text
case identity
world id and revision
method id, version, implementation fingerprint, and rule parameters
applicability result, because, assertion ids, and the rule inputs used
program findings
conformance result, because, assertion ids, and the rule inputs used, or null
context requests
```

No decision right. No execution outcome. No chain-of-thought field. No
`context_sufficiency` field.

The rule is implementation-owned. It is not a normalized relation in the
construction World, and it is not derived by reading the proposition
sentence. Reading that sentence as a rule would be semantic interpretation;
these deterministic evaluators do not do it. `domain_relation` does not
reconstruct source meaning.

A reviewer sees the exact parameters in the artifact:

```text
mail applicability: applies_to_kind call_site; excludes_kind callable
mail conformance:   required_target notificationGatewaySend

config applicability: applies_to_kind config:route; required_handler CustomerExport
config conformance:   required_path /customers/export
```

`method.fingerprint` is the sha256 of a canonical JSON record of the method
id, version, explicit rule parameters, and the source of the evaluator
functions. It does not include a filesystem path or a timestamp.
`method.version` is `v0`. A later model-backed evaluator
can use the same artifact fields without storing reasoning. The field does
not require the procedure to be deterministic.

The two profiles did not need an evaluator registry. The caller invokes the
profile function that owns the rule.

The generic helpers do not name mail or route vocabulary, and they do not
name `program_invokes`, `config_route`, or `config_member`.

## 8. Fresh-consumer reads

`consumer_reads` answers, from the case and the artifact, without SQL:

```text
What proposition was judged?
What software subject was judged?
Why was the proposition considered applicable or not?
What program fact was established?
Which cited assertions and support paths justify that finding?
What conformance conclusion followed?
What remains unknown?
What additional bounded context was requested?
Which sealed world id, revision, and address did this depend on?
```

Proposition evidence included for the outbound-mail sentence is the
reconstructed source text from the construction read, with status `OK`.

## 9. Profiles

Both profiles matter because they exercise one artifact without sharing a
subject vocabulary.

The mail profile judges `outbound_mail_passes` against a bound call site.
The support world is the accepted mail construction. The conflict world is a
separate sealed fixture whose `sendReceipt` call resolves to
`smtpClientSend`. The unresolved world binds the same proposition to the
`sendAmbiguous` call whose resolution is `MULTIPLE_CANDIDATES`. None of
these is a cross-snapshot comparison.

The config profile judges `customer_export_route` against a bound
`config:route`. The support world is the accepted config construction. The
conflict world is a separate sealed fixture whose export path is
`/internal/export`. The insufficient case uses the accepted world and omits
`config_route` from the case. No Program Spine tables are required.

Profile rules stay out of the generic schema. The artifact records the
parameter values the evaluator used, and the implementation fingerprint
identifies the source of those parameters.

## 10. Historical finding → rule

| Historical finding | Judgment v0 rule |
| --- | --- |
| Case assembly is not adjudication. Material can be presented without being applicable. | Section 2. Inclusion is not applicability. |
| `DOES_NOT_APPLY` needs a positive reason. Failure to prove `APPLIES` is `UNKNOWN`. | Section 3. |
| A program finding is separate from authority and from conformance. `UNKNOWN` is not false. | Sections 4 and 5. The historical true/false finding value is not a v0 field. |
| Do not emit `CONFORMS` when applicability is unknown. Do not turn an unresolved program fact into `CONFLICTS`. | Section 5. Conformance is absent unless applicability is `APPLIES`. |
| A bounded context request identifies missing evidence and is not a repository search. | Section 6. The historical reason vocabulary, old/new sides, source-kind list, and `context_sufficiency` scalar are not this schema. |
| The case and the adjudication are sidecars. Findings are not written into the World. | Sections 2 and 7. |
| Stage separation across maintenance, impact, and selection. | Not reused. v0 has no change input. Explicit ids replace selection. |
| `NOT_APPLICABLE` as a conformance state. | Not used. It repeated `DOES_NOT_APPLY`. |
| Decision right and execution. | Out of scope. Not in the artifact. |
| GovernanceCase field layout, authority standing, and ProgramDelta. | Not inputs. The construction World is the input. |

## 11. Falsifiers and open questions

The experiment kept these separations. It did not find a reason to remove
them:

1. Case assembly and applicability are separate.
2. Applicability and conformance are separate.
3. Program findings need their own records.
4. `UNKNOWN` stays distinct from `CONFLICTS`.
5. A case that cites assertion ids and support fingerprints, rather than the World itself, is enough to judge and to check.
6. One request shape covers a missing binding and a missing route property.
7. One artifact shape covers a call site and a config route.
8. `context_sufficiency` does not add a distinction the request, the finding status, and applicability do not already carry.

The four outcomes stay separate:

```text
MISSING CASE CONTEXT
    the route path was omitted
    → judgment request
    → conformance UNKNOWN

CONSTRUCTION GAP
    candidate bindings and an unresolved question are present
    → construction request
    → applicability UNKNOWN
    → no claim that a judgment fact was omitted

MECHANICAL INDETERMINACY
    resolution status MULTIPLE_CANDIDATES and its candidate rows are present
    → finding UNRESOLVED
    → conformance UNKNOWN
    → no request

SEMANTIC UNKNOWN
    same relevant kind, no binding, incomplete coverage, no exclusion fact
    → applicability UNKNOWN
    → no request
    → not DOES_NOT_APPLY
```

Not part of this version:

- A bound call site with no resolution row. The absent-target request is
  implemented and not exercised by a sealed fixture.
- A program finding that is not a value of an included mechanical tuple.
- More than one proposition in one artifact, and any rollup across them.
- Model-backed judgment. The artifact leaves room for it. This contract
  does not demonstrate it.
- A profile rule stored as a construction-world relation. v0 uses the
  versioned evaluator record instead.

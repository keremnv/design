# Software Governance Investigation Contract v0

Status: accepted Investigation v0, 2026-09-24. This is not Core Product v1
authority, not part of the Construction v0 baseline, and not a change to
the accepted Judgment v0 contract. It does not define admission,
publication, change-impact retrieval, or maintenance.

The production package is `ontology_author.software_governance.investigation`.
The config investigator is `profiles/software_governance_config_v0/investigate.py`.
Acceptance is `tests/test_software_governance_investigation.py`, recorded in
[SOFTWARE_GOVERNANCE_INVESTIGATION_ACCEPTANCE.md](SOFTWARE_GOVERNANCE_INVESTIGATION_ACCEPTANCE.md).

```text
SEALED CONSTRUCTION WORLD W
        ↓
JUDGMENT CASE C0
        ↓
JUDGMENT J0 = judge(C0)
        ↓
INVESTIGATION QUESTION
        ↓
investigation, using capabilities supplied to it
        ↓
CASE_EXPANDED  or  PROPOSAL  or  UNRESOLVED
        ↓
when a case was expanded: J1 = judge(C1)
```

J0 remains the judgment of C0. Investigation does not rewrite it.

## 1. Question

Given a bounded Judgment v0 case and a reason to look further, how may an
agent explore beyond that case and produce an auditable result without
changing the sealed World or treating a new discovery as World knowledge?

The experiments kept this split:

```text
discovery of an assertion already in W  → another ordinary Judgment case
discovery absent from W                 → a proposal sidecar
neither                                 → unresolved
```

Admission and publication did not occur. They were not required.

## 2. Investigation is not Judgment

Judgment v0 stays bounded. `judge` reads the explicit case and does not
receive a World, a repository, or a source capability.

Investigation is the caller around Judgment. It may open the sealed World
named by the case, and it may use other capabilities the caller supplies.
A judgment request can be copied into an investigation question. The
investigator does not take the judgment artifact as an input, so it cannot
rewrite J0.

The loop that held:

```text
J0 = judge(C0)
R  = investigate(opened World of C0, C0, question, capabilities)
J1 = judge(C1)    only when R expanded the case
```

## 3. Scope is wider than the judgment basis

A judgment request is one fact already known to be missing. It is not the
limit of what Investigation may inspect.

The config experiment started from a request for `subject_property` /
`path`. The investigator also read the route's other mechanical relations.
The expanded case still contained `config_member`. The later judgment cited
the route assertion it used and did not cite `config_member`.

```text
facts included in the case
    >
facts cited by the judgment
```

An included citation is available context. It is support only when a
judgment result lists its assertion id. The investigation receipt may name
the relations it inspected. That list is exploration provenance, not
support provenance.

A final judgment cites only the assertions it actually used. Judgment v0
already behaves that way. Investigation does not change it.

## 4. Same-World case expansion

v0 expansion adds assertions that `verify_case` accepts against the opened
publication. The experiments kept:

```text
same publication address
same world id
same revision
same selected proposition
same selected SoftwareSubject
citations(C1) ⊇ citations(C0)
```

C1 is assembled with the production Judgment case API. It is an ordinary
Judgment case. It carries no investigation fields.

No experiment needed to remove or replace a citation. v0 expansion is
monotonic. A later version may revisit removal only with a case that
cannot be judged honestly while the extra citation remains.

These fixtures stamp the same producer world id, `config-routes`, on more
than one publication. World-id equality does not identify the publication.
The case already stores `world_address`. Expansion opens that address and
rejects a view of another directory before copying any citation. An
assertion from the other publication still fails `verify_case` when the
parent publication is the one opened, including when the referent label is
the same word. v0 does not add cross-World or cross-revision correspondence.
Judgment v0 already stores the address and already rejects an assertion the
opened World does not contain, so this does not change the Judgment
contract.

## 5. Lineage stays outside the case

This receipt was enough. Judgment cases did not gain fields.

```text
question_id
parent_case_id
world_id
revision
world_address
method
    id
    capabilities used
outcome
resulting_case_id     absent unless the case was expanded
added_assertion_ids
proposal_id           absent unless a proposal was emitted
inspected_relations
```

There is no chain-of-thought field and no log of rejected avenues.

The receipt does not use Judgment's method fingerprint. These experiments
needed the method id and the names of the capabilities that were actually
supplied. The added assertion ids, or the proposal basis, are the
inspectable result. A later investigator whose choice of citations is
itself a semantic rule would need that rule recorded. That need did not
appear here.

## 6. Investigation question

One record covered a request-shaped question and an open question.
`structured_need` is omitted for the open form. The question text is not
written into the World.

```text
question_id
question
purpose
proposition
subject
origin
    case_id
    kind: judgment_request | open
    request     only when the caller copied one
structured_need?     optional
    need
    property
```

No generic question framework was required beyond this record.

## 7. Outcomes

Three outcomes were sufficient.

### CASE_EXPANDED

The sealed World already contained assertions the parent case omitted.
Investigation assembles C1, verifies it, and records the added assertion
ids.

`CASE_EXPANDED` means the case grew. It does not mean the investigation
question was answered. Adding a route assertion to a case whose
construction gap is a missing binding left applicability `UNKNOWN`,
conformance absent, and the construction request in place.

### PROPOSAL

The investigator found a field in reconstructed manifestation text that
the producer does not assert. That field is not added to the case.

Both of these citations failed closed against the sealed World:

- an invented assertion id
- a real route citation with the discovered field inserted into its values

The proposal sidecar is the v0 result. It is not admitted and not published.

### UNRESOLVED

The supplied capabilities established neither a new same-World citation nor
a proposal about the question that was asked. A source field that was
present, and that the question did not ask about, was not turned into a
proposal. No negative World fact was recorded.

## 8. Proposal envelope

The envelope that held a mechanical discovery:

```text
proposal_id
originating_case_id
originating_question_id
epistemic_class: mechanical | semantic | source/evidence | other
payload                  profile-owned
basis                    reconstructed manifestation scheme, location,
                         content digest, and text for the tested case
method                   id and capability name
reason                   why this cannot be a citation in the current case
```

The tested payload was the field name and the value. It is not a relation
schema. The proposal has no assertion id.

`epistemic_class` `mechanical` matches a producer field that was never
asserted. A semantic proposal can reuse the same envelope with class
`semantic` and a profile-owned payload. No experiment needed a second
envelope. None performed admission.

The proposal is distinct from:

```text
case-local finding       stays in J0 or J1
existing World assertion verify_case can see it
construction admission   not performed
published World assertion the sealed bytes do not change
```

## 9. Existing fact and new fact

```text
asserted in this publication
    → may be added to C1 after verification

visible in source or manifestation text
and absent as an assertion
    → proposal, or unresolved when it does not answer the question

confidence of the investigator
    → does not change either classification
```

## 10. Generic and profile boundary

The generic package knows case assembly, citation verification,
same-publication expansion, the question record, the receipt, the proposal
envelope, and the three outcomes. Citation verification is Judgment's
`verify_case`.

It does not know mail vocabulary, route vocabulary, Program Spine relation
names, or approval vocabulary. The config helper owns the published source
keys and the decision that an extra manifestation field is a proposal.
There is no investigator registry and no capability registry. The caller
passes the capabilities for that run by name.

## 11. Catalogue mapping

Discovery, proposal, admission, and publication stayed distinct. The
experiments exercise the first two, plus an unresolved result that creates
neither. Admission and publication stay out of scope.

| Experiment | What happened | Scenarios | What it is not |
| --- | --- | --- | --- |
| Same-World expansion, then `CONFORMS` | A route assertion already in W was cited by C1. J0 and J1 are separate case-local results. | PR-01, PR-04, PR-05, AG-01 | Write-back. Promotion of the finding (PR-07). |
| Broader inspection | Membership was inspected and remained in the case. The judgment did not cite it as support. | PR-01 | A new fact. Support for the path finding. |
| Unpublished field | Manifestation text contained a field the producer did not assert. The case rejected both an invented id and a decorated tuple. A proposal was kept. | PR-03, AG-04 | EV-09, MO-06, PR-08, publication. |
| Open question | The same proposal path, without `structured_need`. | PR-03, AG-04 | A closed need vocabulary. A World assertion of the question text. |
| Unresolved | No citation and no proposal. An unrelated source field was ignored. | No knowledge event. The catalogue allows a result that adds nothing. | An invented negative. A proposal made to avoid `UNRESOLVED`. |
| Cross-World citation | Rejected. The other publication is not this case's address. | Not ID-08 | Cross-revision correspondence. |
| Construction gap | Inspection found candidates and no binding. Forging a binding failed. Adding a route assertion left the gap open. | SE-03 stays unresolved. SE-02 was not performed. | A proposal that picks a winner. A silent binding. |

## 12. Falsifiers

| Claim | Result |
| --- | --- |
| Investigation is separate from the bounded judge. | Held. `judge` saw only the case. |
| Same-World verified assertions are enough for v0 expansion. | Held. |
| The Judgment case schema can stay unchanged. | Held. C0 and C1 are ordinary cases. |
| Lineage can live outside the case. | Held. The receipt links them. |
| A judgment request is a lower bound on exploration, not a ceiling. | Held. |
| A case may include facts the judgment does not cite. | Held. |
| `CASE_EXPANDED`, `PROPOSAL`, and `UNRESOLVED` are enough. | Held, with the reading that expansion does not by itself answer the question. |
| A discovery absent from the World must not enter the case as an established fact. | Held. |
| A proposal can remain short of admission and publication. | Held. |
| An open question does not need a closed need vocabulary. | Held. |
| Cross-World context is unnecessary for v0. | Held. |

No counterexample required a change to Core, Construction v0, or the
Judgment v0 contract.

## 13. Explicit non-goals

This contract does not design or implement proposal admission, World
write-back, a new publication, support-set evolution, correction storage,
cross-World cases, cross-snapshot continuity, change-impact retrieval,
maintenance, decision rights, execution, agent permissions, generic
planning, a tool registry, model memory, chain-of-thought persistence, or
multi-proposition or multi-subject Judgment.

## 14. Accepted layer

Investigation v0 is an application layer over Judgment v0. The acceptance
record states the non-guarantees. Proposal admission and publication remain
future events.

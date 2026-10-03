# Durable Knowledge Evolution Scenario Catalogue v0

Status: scenario catalogue, 2026-09-24. Not Core Product v1 authority. Not a
persistence design. Not part of the accepted Software Governance Construction
v0 baseline or the Judgment v0 contract.

A future proposal for write-back, maintenance, promotion, or revision can be
tested by naming the scenario ids it supports, corrupts, conflates, or cannot
represent.

```text
inputs I
    ↓
construction method M
    ↓
sealed World W0
    ↓
an epistemic event
```

The event is not yet a storage operation. “Write it back to the graph” is
not a scenario.

Constraints used as facts about the current system, not as answers:

```text
identity != manifestation != location
support != endpoint resolution
mechanical != semantic
source evidence != constructed knowledge
construction gap != judgment gap
World != case != judgment artifact
exploration != admission
```

Core publishes a sealed revision at a fresh address. Legacy in-place rebuild
replaces the current bundle and does not retain the prior revision. An
assertion id is the identity of a relation tuple. Grounding and construction
origin are separate. Derivation staleness follows registered inputs and
definition versions. A completeness receipt is scoped. Absence is not a
negative claim without a covering receipt. Judgment findings stay outside
the sealed World.

## 1. Repository archaeology

Classification: `SUPPORTED FINDING`, `ACCIDENTAL IMPLEMENTATION`,
`SUPERSEDED`, or `UNRESOLVED`. Historical storage shape is not reused.

| Historical mechanism | Scenario it was trying to solve | What it demonstrated | What was accidental or domain-specific | Current relevance |
| --- | --- | --- | --- | --- |
| Fresh-address seal (`profiles/core_v1`, Architecture) | Keep a prior sealed revision inspectable after reconstruction | Old and new bundles stay addressable. Reads do not mutate them. The path is the revision address, not a mutable current pointer. | The local `v0` world id can be reused across roots. That id is not the historical address. | SUPPORTED FINDING for “prior sealed state remains readable.” Not a proof that every later event is a new World. |
| Legacy `Project.run` / `rebuild` / `author rebuild` | Replace the working bundle | In-place rebuild succeeds as a compatibility path. | Successful prior revisions are discarded. | SUPERSEDED as history semantics. ACCIDENTAL IMPLEMENTATION if used as the evolution model. |
| `retract` / `retract_tuple` | Remove a tuple before publication | Tuple and its groundings can be deleted together in an unsealed World. Assertion identity is the tuple, not the support. | Retraction deletes claim and support together. Sealed Worlds are read-only, so this is not a post-seal event. | SUPPORTED FINDING that claim identity and support are different records. UNRESOLVED as a model of correction, withdrawal, or loss of support after seal. |
| Registered SQL derivation, staleness, completeness receipts | Recompute a deterministic function of declared inputs | Staleness tracks relation versions and the derivation definition. Completeness is `COMPLETE`, `INCOMPLETE`, or `UNKNOWN`, with basis and known gaps. `COMPLETE` cannot carry known gaps. | Receipt universe is a relation name. Governance binding coverage could not honestly use this receipt. | SUPPORTED FINDING for deterministic derivation only. Not semantic invalidation. |
| Explicit unresolvedness (golden refund; governance candidates) | Leave a question open without inventing a winner | Two grounded candidates plus an unresolved question. Admission is not resolution. | Three different “candidate” objects exist and are easy to conflate. | SUPPORTED FINDING. |
| Evidence adapters and digest-addressed bytes | Reconstruct a cited span from retained bytes | Handle, revision, and location are separate from the constructed claim. Reconstruction can fail closed. | Markdown segmentation and TypeScript token ranges are adapter-specific. | SUPPORTED FINDING for source identity versus constructed knowledge. |
| Program Spine comparison | Ask whether two snapshots’ subjects correspond, and what changed after that | Identity, manifestation, and relation deltas are separate. Continuity can be `CONTINUED`, `AMBIGUOUS`, `UNRESOLVED`, or `NO_MATCH`. A source diff is evidence, not the comparison result. Heuristic correspondence is labeled. | Call graphs, token ranges, and spine table names are one producer. | SUPPORTED FINDING for cross-revision correspondence. Not an interchange schema. Software Governance Construction does not require it. |
| Authority maintenance (`HOLD`, `NO_RENEWAL`) | Decide whether a recorded attachment’s grounds still hold after a program change | Maintenance is not relevance and not conformance. v0 emits no `RENEW`. Heuristic continuation does not copy the attachment forward. | Checkout, warrants, and ProgramDelta are the historical subject. | SUPPORTED FINDING for “do not auto-renew.” SUPERSEDED as the Software Governance model. |
| Authority construction and warrants | Record why a claim is allowed to stand | Standing, original text, and normalized claims were separated. A normalized tuple was not the authority. | The warrant vocabulary and authority classes are historical. | SUPPORTED FINDING that support is not the claim. SUPERSEDED as a required Software Governance stage. |
| Semantic persistence admission | Decide whether one interpretation becomes durable | A constructor proposal is not yet World state. Admission checks shape and support. It does not decide truth. Invalid output is not epistemic unresolvedness. | `ConstructionObligation` kinds and checkout profiles are historical. | SUPPORTED FINDING for exploration versus admission. |
| Semantic-identity experiment | When a persistent identity adds a read a direct claim lacks | Direct evidence-to-software records answered rewording, a second source, and one-off subjects. A semantic referent was required only to join a replacement of both wording and every endpoint. | The experiment’s referent was optional and is not used by either acceptance profile. | SUPPORTED FINDING. UNRESOLVED for split, merge, and ordinary rename. |
| Manifestation-granularity and binding-target experiments | Separate identity, content, location, and binding grain | A file digest is coarser than a token range. An invocation binding that targets the owner cannot distinguish two calls. Assertion ids do not survive retarget. | TypeScript call sites and insert-before limits are producer-specific. | SUPPORTED FINDING. Encoded in Construction v0. |
| Governance case assembly and adjudication | Present bounded material and judge it without searching | Inclusion is not applicability. Program findings are not conformance. Findings were not written into either World. Promotion of a case rule was explicitly deferred. `context_sufficiency` conflated missing context with indeterminacy. | ProgramDelta, decision rights, and the old case schema. | SUPPORTED FINDING for stage separation. SUPERSEDED schema. Judgment v0 removed context sufficiency. |
| Design checkout construction | Keep a sealed resolution while later edits happen | A sealed historical resolution can remain while later work does not silently invalidate it. | Checkout and payment vocabulary. | SUPPORTED FINDING that a later edit is not automatically a retraction. SUPERSEDED as the product model. |
| Software Governance Construction v0 | Record propositions, bindings, candidates, and coverage over two producers | `software_subject` is a receipt. Manifestation is optional. Producer relations are not generic vocabulary. Origin belongs to the path. Coverage may be mechanical or semantic. No binding under incomplete coverage is not “ungoverned.” | The mail and route rules are profile fixtures. | SUPPORTED FINDING. The accepted baseline. |
| Software Governance Judgment v0 | Conclude from a sealed World without mutating it | Case, World, and judgment artifact are different. Applicability, finding, and conformance are different. A case-local finding is not World knowledge. The evaluator is identified by method id, version, and source fingerprint. | Profile rule parameters live in the evaluator record, not in the construction World. | SUPPORTED FINDING. Ready to freeze. Not a promotion mechanism. |

## 2. Scenario catalogue

Records are epistemic. Destinations are candidates, not decisions. Actor type
is a provenance field unless a record says the actor changes the event.

### A. Evidence evolution

#### EV-01 New external evidence

- Initial state: W0 sealed from the evidence then known.
- Trigger: a source that was not an input exists.
- Event: the source is available to a later constructor.
- Changed: the evidence universe.
- Unchanged: W0’s claims about its own inputs.
- Relation to prior state: adds an input. Does not correct W0.
- Destinations: evidence store; later construction inputs. Not an in-place edit of W0.
- Provenance: provider, handle, revision, time first seen.
- History: W0 remains inspectable.
- Prior judgments: a judgment of W0 does not automatically cover the new source.
- Reuse: the source can be reused. Any claim about it cannot, until constructed.
- Direct mutation: writing the source’s meaning into W0 loses the boundary between old inputs and new inputs.
- Open question: whether “available” is the same event as “ingested.”

#### EV-02 Previously known evidence becomes addressable

- Initial state: someone could name the source, but no adapter handle existed.
- Trigger: ingestion assigns a handle, revision, and retained bytes.
- Event: the source becomes reconstructible.
- Changed: addressability.
- Unchanged: the source’s meaning. No new interpretation has occurred.
- Relation to prior state: adds an address. Not a new claim.
- Destinations: evidence store.
- Provenance: previous informal identity, new handle, adapter.
- History: yes, if anything already cited the informal identity.
- Prior judgments: only if they cited that source in a non-reconstructible way.
- Reuse: the bytes can be reused. Interpretation cannot skip construction.
- Direct mutation: storing an interpretation at ingestion time collapses ingestion and interpretation.
- Open question: none beyond keeping the two events distinct.

#### EV-03 Evidence revision changes

- Initial state: handle H at revision R0 supports claims in W0.
- Trigger: the provider publishes R1 at the same logical source.
- Event: the bytes changed.
- Changed: source revision.
- Unchanged: until a later construction, the claims in W0.
- Relation to prior state: the new revision does not by itself supersede those claims.
- Destinations: evidence store for R1. W0 still cites R0.
- Provenance: both revisions.
- History: judgments that cite R0 must still reconstruct R0.
- Prior judgments: yes.
- Reuse: R1 is a new input, not a silent replacement of R0.
- Direct mutation: overwriting R0 bytes makes old citations irreconstructible.
- Open question: whether H’s identity survives the revision or only the handle name does.

#### EV-04 Evidence corrected

- Initial state: R0 was the wrong bytes for what the provider now says R0 was.
- Trigger: the provider replaces the record of R0, or issues a correction notice.
- Event: the prior evidence record was erroneous.
- Changed: the license for claims grounded on the erroneous bytes.
- Unchanged: the fact that W0 used those bytes.
- Relation to prior state: correction of an input, not a new revision of the software.
- Destinations: evidence store, with the erroneous bytes retained if any artifact cited them.
- Provenance: what was wrong, what replaced it, who corrected it.
- History: yes. Deleting the erroneous bytes hides why W0 said what it said.
- Prior judgments: yes.
- Reuse: the correction is reusable as evidence. It does not rewrite W0.
- Direct mutation: replacing W0’s grounds in place makes the old judgment look as if it used the corrected bytes.
- Open question: how to cite a correction without pretending the original observation never happened.

#### EV-05 Evidence withdrawn or unavailable

- Initial state: reconstruction of a cited observation succeeds.
- Trigger: bytes or permission disappear.
- Event: support can no longer be reconstructed.
- Changed: reconstructibility.
- Unchanged: the claim’s tuple, until someone withdraws it.
- Relation to prior state: loss of reconstructibility. Not yet retraction of the claim.
- Destinations: a reconstruction-failure record beside the existing citation.
- Provenance: last successful reconstruction, failure status.
- History: yes.
- Prior judgments: yes, if they depended on reading that evidence.
- Reuse: the failure is reusable information. The claim’s standing is a separate event (CR-04, CR-05).
- Direct mutation: deleting the claim because bytes are missing conflates unavailability with withdrawal.
- Open question: whether a claim whose only support is unrestorable remains citable.

#### EV-06 Additional evidence supports an existing claim

- Initial state: claim C is grounded on A.
- Trigger: B is also adequate support.
- Event: the support set grows.
- Changed: support.
- Unchanged: C’s tuple, if C’s content is the same.
- Relation to prior state: supports. Does not correct or supersede C.
- Destinations: additional grounding on a later publication, or a support record that cites C.
- Provenance: A and B, and which construction added B.
- History: the A-only support path remains inspectable.
- Prior judgments: they depended on A. They need not be redone merely because B exists.
- Reuse: B can be reused. C was already reusable.
- Direct mutation: replacing A with A+B in W0 hides that earlier consumers had only A.
- Open question: whether C’s identity survives the added path. Catalogue only. See SU-01.

#### EV-07 Existing support ceases to support a claim

- Initial state: A licenses C.
- Trigger: A is reread and no longer licenses C, or A’s relevant span changes.
- Event: a support path ends.
- Changed: support.
- Unchanged: possibly C’s wording.
- Relation to prior state: loss of support. Not automatically a correction of C.
- Destinations: support record. C’s standing is a separate decision.
- Provenance: why A no longer licenses C.
- History: the old path must remain visible or prior judgments cannot show their basis.
- Prior judgments: yes.
- Reuse: the withdrawal of support is reusable. C may or may not be.
- Direct mutation: deleting A’s grounding in place leaves C looking unsupported from the start, or deletes C with it.
- Open question: claim identity across support-set change. See family F.

#### EV-08 A person or agent creates a source, which is then ingested

- Initial state: no such artifact.
- Trigger: someone writes a document, record, or file.
- Event: source creation, then, separately, ingestion (EV-02).
- Changed: a new artifact exists.
- Unchanged: W0, until interpretation.
- Relation to prior state: adds a source. Interpretation is not included.
- Destinations: the artifact’s own store, then the evidence store.
- Provenance: author, time, later handle and revision.
- History: the created bytes, once cited, must remain reconstructible.
- Prior judgments: no, until a later judgment uses them.
- Reuse: the source can be reused. Authorship is not admission of any claim inside it.
- Direct mutation: inserting the author’s intended claims into W0 at creation time skips interpretation.
- Open question: whether the author is the authority for those claims. That is standing, not ingestion.

#### EV-09 Direct constructed assertion, no source artifact

- Initial state: W0 has no claim C.
- Trigger: a person or agent states C as a claim, without a reconstructible source.
- Event: direct assertion.
- Changed: a proposed or admitted claim whose support is the act of assertion.
- Unchanged: the evidence store.
- Relation to prior state: adds a claim by decision, not by interpretation of a source.
- Destinations: proposal; if admitted, a later World whose grounding is the decision record. Not a forged source observation.
- Provenance: actor, time, method, standing. The absence of a source is part of the provenance.
- History: the decision record.
- Prior judgments: only those that would be affected if C is later admitted.
- Reuse: only after admission. The proposal is not yet World knowledge.
- Direct mutation: writing C into W0 with source-shaped grounding pretends a document existed.
- Open question: what support class a sourceless assertion is allowed to carry. Not answered here.

Distinguish, and do not collapse:

```text
source creation       EV-08, first half
source ingestion      EV-02
source interpretation a later semantic or mechanical construction over ingested bytes
direct assertion      EV-09
```

### B. Mechanical observation evolution

#### MO-01 Broader producer capability, same inputs

- Initial state: producer P0 emitted a subset of facts for input I.
- Trigger: capability P1 observes more kinds of facts from I.
- Event: the producer scope grew.
- Changed: observable mechanical universe.
- Unchanged: I. Facts P0 already emitted may still be true of I.
- Relation to prior state: adds observations. Does not correct P0’s facts merely by existing.
- Destinations: a new mechanical world or a new publication over I.
- Provenance: capability id and version.
- History: P0’s world remains the basis of judgments that used it.
- Prior judgments: they used P0. They are not automatically false.
- Reuse: new facts are reusable after publication. They are not retroactively part of W0.
- Direct mutation: inserting P1 facts into W0 makes old completeness claims look as if they covered P1.
- Open question: whether P0 and P1 facts about the same subject are one subject identity.

#### MO-02 Improved producer, same inputs

- Initial state: as MO-01, but P1 is a better version of the same capability, not a wider one.
- Trigger: producer version change.
- Event: producer evolution.
- Changed: whatever the new version emits differently.
- Unchanged: I.
- Relation to prior state: not automatically a correction. Differences need their own classification (MO-03, MO-07, MO-08).
- Destinations: new publication.
- Provenance: both versions.
- History: yes.
- Prior judgments: yes, wherever they cited a changed fact.
- Reuse: only the newly published facts.
- Direct mutation: overwriting P0 facts loses the version those judgments used.
- Open question: “improved” is a value judgment. The scenario is only “version changed.”

#### MO-03 Producer bug fix changes emitted facts

- Initial state: P0 emitted fact F for I. F was an emitter error.
- Trigger: a fix. P1 emits F′.
- Event: correction of an observation.
- Changed: the mechanical claim about I.
- Unchanged: I.
- Relation to prior state: corrects F. Does not mean the software changed.
- Destinations: new publication. F remains in the old publication.
- Provenance: defect, versions, F and F′.
- History: yes, or the old judgment’s finding has no basis to inspect.
- Prior judgments: yes.
- Reuse: F′ can be reused. F remains historical error, not current observation.
- Direct mutation: replacing F with F′ makes the old judgment appear to have used F′.
- Open question: whether every differing emission is a bug. MO-02 refuses that assumption.

#### MO-04 New subject kinds become observable

- Initial state: kind K was not emitted.
- Trigger: the producer can now emit K.
- Event: the subject vocabulary grew.
- Changed: what can be a subject.
- Unchanged: subjects of older kinds, until separately remapped.
- Relation to prior state: adds a kind. Not a split of an old subject unless MO-05 also happens.
- Destinations: new publication.
- Provenance: capability that introduced K.
- History: old worlds simply lack K. That absence was outside their producer scope.
- Prior judgments: not about K.
- Reuse: K is reusable only where that capability is declared.
- Direct mutation: adding K-rows to an old world whose completeness excluded K rewrites scope.
- Open question: whether generic governance receipts can cite K without standardizing K.

#### MO-05 A subject is refined into narrower subjects

- Initial state: subject S covers a range that later appears as S1 and S2.
- Trigger: the producer distinguishes structure it previously kept as one subject.
- Event: refinement of mechanical identity.
- Changed: subject grain.
- Unchanged: the bytes, if the software did not change.
- Relation to prior state: refines. S was coarse, not necessarily wrong.
- Destinations: new publication plus an explicit grain correspondence. Not a silent rename.
- Provenance: S, S1, S2, and the capability that refined them.
- History: judgments bound to S must still see S.
- Prior judgments: yes.
- Reuse: S1 and S2 are reusable. They do not automatically inherit S’s bindings.
- Direct mutation: replacing S with S1 loses S2 and the old binding target.
- Open question: who records the correspondence between S and S1, S2.

#### MO-06 New mechanical relations

- Initial state: subjects exist. Relation R does not.
- Trigger: the producer emits R.
- Event: a new observation type.
- Changed: available relations.
- Unchanged: subject identity, unless R also refines it.
- Relation to prior state: adds.
- Destinations: new publication.
- Provenance: capability that owns R.
- History: old worlds have no R. Emptiness there is not a negative R.
- Prior judgments: only if a judgment request was waiting on R.
- Reuse: R is producer-owned. It is not a universal relation because it now exists.
- Direct mutation: adding R to W0 changes the mechanical world that judgments already read.
- Open question: none specific. Do not standardize R.

#### MO-07 Previously resolved mechanical state becomes non-unique

- Initial state: resolution of S is `RESOLVED` with one target.
- Trigger: a later observation says `MULTIPLE_CANDIDATES` or `UNRESOLVED`.
- Event: loss of uniqueness.
- Changed: resolution status.
- Unchanged: possibly the software. The trigger may be a producer change or a software change. Those causes stay distinct.
- Relation to prior state: the old unique target is no longer the current observation. It may have been wrong (MO-03) or the software may have changed (MO-11).
- Destinations: new publication. The old resolution stays in W0.
- Provenance: both statuses and the cause class.
- History: yes. A judgment that used the unique target depended on it.
- Prior judgments: yes.
- Reuse: the new status is reusable. It does not rewrite the old finding.
- Direct mutation: changing W0’s resolution to non-unique makes a conforming judgment look unfounded.
- Open question: whether the old target and the new candidate set are the same subject family.

#### MO-08 Previously unresolved mechanical state becomes resolved

- Initial state: S is `UNRESOLVED` or `MULTIPLE_CANDIDATES`.
- Trigger: a later observation names one target.
- Event: mechanical resolution.
- Changed: uniqueness.
- Unchanged: governance bindings, unless a later construction adds one.
- Relation to prior state: resolves a mechanical question. Not a semantic binding.
- Destinations: new publication.
- Provenance: previous status, new target, cause class.
- History: the unresolved state explains why earlier judgment returned `UNKNOWN`.
- Prior judgments: their `UNKNOWN` remains the right result for the old observation.
- Reuse: the resolved fact is reusable after publication.
- Direct mutation: filling the old resolution in place makes the earlier unknown look like a mistake.
- Open question: cause class, as in MO-07.

#### MO-09 Mechanical fact corrected

- Initial state: fact F is the observation of I.
- Trigger: F is replaced because it was the wrong observation, not because I changed.
- Event: same as MO-03 when the producer was wrong. Listed separately when the correction is not described as a version upgrade.
- Changed: F.
- Unchanged: I.
- Relation to prior state: corrects.
- Destinations: new publication.
- Provenance: erroneous F, corrected F, basis for calling F wrong.
- History: yes.
- Prior judgments: yes.
- Reuse: corrected F only.
- Direct mutation: same loss as MO-03.
- Open question: what evidence makes F “wrong” rather than “differently observed.”

#### MO-10 Mechanical coverage expands, inputs unchanged

- Initial state: the producer’s completeness for I is partial.
- Trigger: the same producer version surveys more of I.
- Event: scope expansion, not a new capability and not a software change.
- Changed: coverage.
- Unchanged: facts already emitted, if the survey does not also correct them.
- Relation to prior state: adds observations because they were previously unobserved.
- Destinations: new publication with a new completeness claim.
- Provenance: old and new scope.
- History: the old incompleteness explains old absences.
- Prior judgments: an absence that was non-negative stays non-negative for the old scope.
- Reuse: newly observed facts, under the new scope.
- Direct mutation: marking the old scope complete because the new survey finished rewrites history.
- Open question: overlap with CV-01. The difference is the producer’s survey scope versus the constructor’s semantic universe.

#### MO-11 Underlying software changed

- Initial state: snapshot S0.
- Trigger: the program or configuration itself changes to S1.
- Event: input evolution of the software, not of the producer.
- Changed: the object being observed.
- Unchanged: the producer, unless it also changed.
- Relation to prior state: a new snapshot. Correspondence to S0 is a separate scenario (ID-08).
- Destinations: new mechanical publication. Not an edit of S0’s world.
- Provenance: both snapshots.
- History: yes.
- Prior judgments: they judge S0. They do not automatically transfer.
- Reuse: S1’s facts are about S1.
- Direct mutation: editing S0’s subjects to match S1 destroys the judged snapshot.
- Open question: correspondence. Not solved by declaring S1 newer.

Cause classes that must stay distinct even when the emitted rows look alike:

```text
underlying software changed     MO-11
producer changed                MO-02, MO-03
producer scope changed          MO-01, MO-04, MO-10
producer interpretation changed MO-03, MO-09
```

### C. Semantic construction evolution

#### SE-01 New proposition from already-known evidence

- Initial state: evidence E is in W0. Proposition P is not.
- Trigger: a constructor interprets E as P.
- Event: new semantic claim.
- Changed: governed knowledge.
- Unchanged: E and the mechanical facts.
- Relation to prior state: adds.
- Destinations: a later sealed World, or a proposal awaiting admission.
- Provenance: E, method, semantic origin.
- History: W0 without P remains valid as “P was not constructed.”
- Prior judgments: they could not have judged P.
- Reuse: P, after admission.
- Direct mutation: adding P to W0 changes the knowledge judgments already listed.
- Open question: admission versus publication. See exploration versus admission.

#### SE-02 New binding from already-known evidence and software

- Initial state: P and subject S exist. No binding.
- Trigger: correspondence is established.
- Event: new semantic correspondence.
- Changed: the binding.
- Unchanged: P’s wording and S’s mechanical facts.
- Relation to prior state: adds a correspondence. Not a mechanical resolution.
- Destinations: later World.
- Provenance: support class and endpoint-resolution class, separately.
- History: the unbound state explains older “no binding” readings.
- Prior judgments: a judgment that refused to pick S remains correct for W0.
- Reuse: the binding, after admission.
- Direct mutation: inserting the binding into W0 turns an old construction gap into an established fact.
- Open question: none specific.

#### SE-03 New candidate relationship

- Initial state: P has no candidate S.
- Trigger: S is a plausible endpoint and not a unique one.
- Event: explicit non-unique correspondence.
- Changed: candidate set.
- Unchanged: established bindings.
- Relation to prior state: adds an alternative. Does not resolve.
- Destinations: later World.
- Provenance: why S is plausible, and that it is not established.
- History: yes.
- Prior judgments: no change to judgments that did not see S.
- Reuse: the candidate is reusable as a candidate, not as a binding.
- Direct mutation: storing the candidate as a binding resolves it silently.
- Open question: none specific.

#### SE-04 Candidate becomes established

- Initial state: candidates A and B, question unresolved.
- Trigger: a later construction selects A and does not select B.
- Event: resolution of a semantic correspondence.
- Changed: A is established. B is no longer a tied alternative.
- Unchanged: the mechanical facts, unless the trigger was mechanical.
- Relation to prior state: resolves. The prior unresolvedness was not a defect.
- Destinations: later World that still shows the prior question existed, or a pair of worlds.
- Provenance: what licensed the selection. See family G.
- History: the candidate pair must remain visible to explain older unknowns.
- Prior judgments: their refusal to choose a subject stays correct for the old state.
- Reuse: the binding, after admission.
- Direct mutation: deleting B and the question makes the resolution look like it was always unique.
- Open question: whether B remains a recorded non-choice or disappears from the current view only.

#### SE-05 Established correspondence becomes ambiguous

- Initial state: P is bound to S.
- Trigger: a later construction cannot keep a unique endpoint.
- Event: loss of semantic uniqueness.
- Changed: the binding’s current standing.
- Unchanged: the historical fact that W0 bound S.
- Relation to prior state: the old binding is not current. It is not necessarily false.
- Destinations: later World. W0 unchanged.
- Provenance: why uniqueness failed.
- History: yes.
- Prior judgments: a conformance result that used the binding depended on it.
- Reuse: the new ambiguity is reusable. The old binding is historical.
- Direct mutation: deleting the binding in W0 removes the basis of the old judgment.
- Open question: correction versus loss of uniqueness. See CR-01 and CR-05.

#### SE-06 Existing semantic claim corrected

- Initial state: P was the wrong reading of the evidence.
- Trigger: a later reading says P was not licensed.
- Event: correction.
- Changed: the standing of P as a claim about that evidence.
- Unchanged: the evidence bytes.
- Relation to prior state: corrects. P was wrong, not merely old.
- Destinations: later World. W0 still contains P as what was published.
- Provenance: the error and the correcting reading.
- History: yes.
- Prior judgments: judgments that treated P as knowledge depended on a wrong claim.
- Reuse: the correction. P is not current knowledge.
- Direct mutation: replacing P’s text in W0 forges the historical claim.
- Open question: how dependents learn that they used a corrected claim, without designing that mechanism here.

#### SE-07 Supersession of a claim that was valid

- Initial state: P was a correct reading of the world as it then stood.
- Trigger: a later rule, snapshot, or decision replaces P for current use.
- Event: supersession.
- Changed: what is current.
- Unchanged: P’s validity for its original inputs and time.
- Relation to prior state: supersedes. Does not correct.
- Destinations: later current view. P remains historical.
- Provenance: the replacing claim and why it is later rather than a fix.
- History: yes. Otherwise supersession collapses into correction.
- Prior judgments: they may remain correct about the old state.
- Reuse: the successor is current. P is reusable as history.
- Direct mutation: overwriting P with the successor states that P never was the earlier claim.
- Open question: what “current” means when more than one publication exists.

#### SE-08 Semantic scope expands

- Initial state: P was constructed for universe U0.
- Trigger: the same reading is applied to a larger universe U1.
- Event: scope change of a semantic claim.
- Changed: the universe of the claim or of its completeness.
- Unchanged: P’s wording, unless the wording itself was scoped.
- Relation to prior state: refines or extends scope. Absences outside U0 were not false.
- Destinations: later completeness claim. Not an edit of the U0 receipt.
- Provenance: U0 and U1.
- History: the old scope.
- Prior judgments: limited to U0.
- Reuse: the wider claim, with its scope attached.
- Direct mutation: widening U0’s receipt makes old in-scope negatives look wider than they were.
- Open question: overlap with CV-01.

#### SE-09 Expressions joined under a persistent identity

- Initial state: two direct claims answer their own reads. No shared identity.
- Trigger: a constructor decides they survive replacement of wording and endpoints together.
- Event: introduction of a semantic identity.
- Changed: an equivalence that direct records did not store.
- Unchanged: each direct claim.
- Relation to prior state: adds an identity. The experiment’s supported case is only the cross-replacement join.
- Destinations: later World, if admitted. Not retrofitted into W0.
- Provenance: the equivalence decision and both endpoints.
- History: the pre-identity state must remain intelligible.
- Prior judgments: they cited claims, not the new identity.
- Reuse: the identity, only for the join it was admitted to serve.
- Direct mutation: rewriting old claims onto the new id hides that they were direct.
- Open question: any wider use. The cross-replacement experiment does not justify it.

#### SE-10 One semantic identity splits

- Initial state: identity I covers what are later two identities.
- Trigger: a constructor rejects the single identity.
- Event: split.
- Changed: identity grain.
- Unchanged: the historical uses of I, unless they are also corrected.
- Relation to prior state: splits. May be a refinement or a correction. Those are different (CR-03, CR-01).
- Destinations: later World plus a split record.
- Provenance: I, the successors, and which kind of split.
- History: yes.
- Prior judgments: they may have cited I.
- Reuse: the successors, not automatically I’s judgments.
- Direct mutation: replacing I with one successor drops the other.
- Open question: whether this has been demonstrated. It has not.

#### SE-11 Several identities merge

- Initial state: I1 and I2.
- Trigger: a constructor treats them as one.
- Event: merge.
- Changed: identity.
- Unchanged: the historical distinction, as history.
- Relation to prior state: merges.
- Destinations: later World plus a merge record.
- Provenance: both priors and the decision.
- History: yes, or the earlier distinction becomes inexpressible.
- Prior judgments: they may have judged I1 and I2 differently.
- Reuse: the merged identity is a new reusable claim, not a rewrite of both histories.
- Direct mutation: collapsing the two ids in W0 destroys judgments that depended on the difference.
- Open question: undemonstrated.

#### SE-12 A direct claim is later given a persistent identity

- Initial state: a direct evidence-to-software claim.
- Trigger: SE-09’s condition is met later.
- Event: promotion from direct claim to identity. This is a kind of SE-09, not a generic promotion of every useful claim.
- Changed: identity layer.
- Unchanged: the direct claim’s content.
- Relation to prior state: adds identity. Does not correct the direct claim.
- Destinations: later World.
- Provenance: why the identity is now required.
- History: the direct construction remains the earlier read.
- Prior judgments: they did not need the identity.
- Reuse: the identity only for reads that need it.
- Direct mutation: replacing the direct claim with the identity makes the earlier directness invisible.
- Open question: same as SE-09.

#### SE-13 An identity is no longer current, and historical uses remain

- Initial state: I is the current join key.
- Trigger: a later constructor stops using I for new work.
- Event: retirement of an identity from the current view.
- Changed: currency.
- Unchanged: historical citations of I.
- Relation to prior state: withdraws from current use. Not a statement that I was wrong.
- Destinations: current-view note in a later publication. I remains in the old one.
- Provenance: why it is not current.
- History: yes.
- Prior judgments: yes.
- Reuse: historical, not current.
- Direct mutation: deleting I strands those judgments.
- Open question: how “not current” is recorded without a current-pointer design.

### D. Construction-method evolution

#### CM-01 Same inputs, different method

- Initial state: `I + M0 → W0`.
- Trigger: M1 differs in code, prompt, model, model version, deterministic rule, bug fix, ontology, or capability width.
- Event: method evolution.
- Changed: the method, and possibly the output.
- Unchanged: I, unless a different scenario also changes I.
- Relation to prior state: another construction. Not “truer” because it is later.
- Destinations: W1 at a new address if the outputs are published. W0 stays.
- Provenance: M0 and M1 in enough detail to recover what ran. Judgment v0’s method id, version, and fingerprint are one demonstrated shape for an evaluator, not a general law.
- History: yes whenever W0 was cited.
- Prior judgments: they used M0’s results.
- Reuse: W1’s claims, under M1. They do not replace W0’s claims.
- Direct mutation: re-running M1 over W0 presents M1’s output as M0’s.
- Open question: whether a bug-fix method is also CR-01. Only when the old output is established as wrong. Newer is not that establishment.

These triggers are one family. The provenance fields differ. They are not different epistemic events merely because the method component that changed has a different name. They become a different family only when the event also corrects, supersedes, or changes inputs.

### E. Construction coverage evolution

Absence classes that must not be collapsed:

```text
absence because false
absence because not observed
absence because outside scope
absence because unresolved
```

#### CV-01 Constructor examines a larger universe

- Initial state: coverage of U0 is recorded, possibly `INCOMPLETE`.
- Trigger: a later run covers U1 properly containing U0.
- Event: scope expansion.
- Changed: completeness universe.
- Unchanged: claims that were only about U0.
- Relation to prior state: adds scope. Facts that appear only because they are now observed are not changes in the software (CV-07).
- Destinations: a new coverage claim.
- Provenance: both universes and bases.
- History: the old receipt.
- Prior judgments: bounded by the old receipt.
- Reuse: the new receipt, scoped.
- Direct mutation: editing the old receipt’s universe.
- Open question: relationship to MO-10 and SE-08. Same shape, different object of scope.

#### CV-02 Constructor examines a smaller universe

- Initial state: coverage of U0.
- Trigger: a later run deliberately covers U1 properly inside U0.
- Event: scope narrowing.
- Changed: what the new claim talks about.
- Unchanged: the wider old claim.
- Relation to prior state: refines scope. Does not withdraw the wider claim.
- Destinations: a new receipt. Not an invalidation of the old one by narrowness alone.
- Provenance: why the universe shrank.
- History: yes.
- Prior judgments: the wider judgment is not void.
- Reuse: the narrow receipt only inside U1.
- Direct mutation: shrinking the old universe drops judgments outside U1.
- Open question: whether narrowing is sometimes a correction of an over-broad claim. That is CR-01, and it needs a reason beyond the new run’s choice.

#### CV-03 Unknown completeness becomes complete

- Initial state: status `UNKNOWN` or absent.
- Trigger: a run records `COMPLETE` for a named universe and basis, with no known gaps.
- Event: a positive coverage claim.
- Changed: the right to read some absences as negative, inside that scope.
- Unchanged: absences outside that scope.
- Relation to prior state: adds a license. Does not rewrite old non-negative absences.
- Destinations: a new receipt.
- Provenance: universe, basis, method.
- History: the previous unknown.
- Prior judgments: they were not entitled to the new negative readings.
- Reuse: the license, scoped.
- Direct mutation: marking the old world complete.
- Open question: none specific.

#### CV-04 A complete claim is invalidated by new gaps

- Initial state: `COMPLETE`, no gaps.
- Trigger: a gap is discovered that the basis should have included.
- Event: the coverage claim was wrong or is no longer licensed.
- Changed: the negative-reading license.
- Unchanged: the underlying rows, until separately corrected.
- Relation to prior state: corrects or withdraws the receipt. Not a change to every fact in the universe.
- Destinations: a later receipt of `INCOMPLETE` or `UNKNOWN` with the gap. The old `COMPLETE` remains historical.
- Provenance: the gap and why it strikes this basis.
- History: yes. Old negative readings depended on it.
- Prior judgments: yes, if they used absence as negation.
- Reuse: the new receipt. The old license is not current.
- Direct mutation: flipping the old receipt erases the license those judgments used.
- Open question: correction of the receipt versus supersession by a stricter basis.

#### CV-05 New known gaps

- Initial state: a receipt with gap set G.
- Trigger: G′ properly contains G, or a first gap is recorded.
- Event: more of the incompleteness is named.
- Changed: known gaps.
- Unchanged: observed facts.
- Relation to prior state: refines the incompleteness. Does not by itself add facts.
- Destinations: a new receipt.
- Provenance: the gap identifiers.
- History: the old gap set.
- Prior judgments: usually no, unless they assumed a gap was absent.
- Reuse: the gap names.
- Direct mutation: appending gaps to a `COMPLETE` receipt violates the current rule that `COMPLETE` cannot carry gaps. A new receipt is the honest record.
- Open question: none specific.

#### CV-06 Known gaps disappear

- Initial state: gap G is recorded.
- Trigger: a later run no longer records G.
- Event: either G was filled, G was mistaken, or G moved outside scope.
- Changed: the gap list.
- Unchanged: until classified, it is not known which of those three happened.
- Relation to prior state: ambiguous between resolution, correction, and scope change.
- Destinations: a new receipt that says which.
- Provenance: the classification. Without it the event is incomplete.
- History: the old gap, especially if a judgment requested work because of it.
- Prior judgments: yes if they cited G.
- Reuse: only with the classification.
- Direct mutation: deleting G leaves the three causes indistinguishable.
- Open question: this record is intentionally unresolved until the cause is known.

#### CV-07 Facts appear only because coverage expanded

- Initial state: subject S had no binding. Coverage was `INCOMPLETE`.
- Trigger: a wider run records a binding for S.
- Event: S was unobserved, not previously false.
- Changed: the observed set.
- Unchanged: the old non-negative reading of S.
- Relation to prior state: adds. Does not correct a negative that was never licensed.
- Destinations: new publication.
- Provenance: old receipt and new fact.
- History: the incomplete receipt.
- Prior judgments: an `UNKNOWN` from missing correspondence stays valid for the old coverage.
- Reuse: the new binding, under the new coverage.
- Direct mutation: treating the new binding as proof that W0 was wrong about S.
- Open question: none. Construction v0 already requires this distinction.

### F. Support and warrant evolution

Claim identity is not decided here. Each case asks whether it could survive.

#### SU-01 Claim C, support A, later A and B

- Initial state: C grounded only on A.
- Trigger: B is added.
- Event: support grows.
- Changed: support set.
- Unchanged: C’s content, if the tuple is the same.
- Relation to prior state: supports.
- Destinations: an added support path. Not a new claim id merely because support grew.
- Provenance: both paths.
- History: the A-only path.
- Prior judgments: depended on A. They remain reconstructible if A remains.
- Reuse: C, with current support stated separately.
- Direct mutation: one overwritten grounding hides A-only history.
- Identity question: survival is plausible because content did not change. Undecided.

#### SU-02 C loses A and retains B

- Initial state: support is A and B.
- Trigger: A is removed as support.
- Event: support shrinks without emptying.
- Changed: support set.
- Unchanged: possibly C’s content.
- Relation to prior state: loss of one path.
- Destinations: a support-change record. Not automatic withdrawal of C.
- Provenance: why A ceased, and that B remains.
- History: A, if any judgment used A.
- Prior judgments: those that relied on A specifically.
- Reuse: C only if B still licenses the uses being made.
- Direct mutation: deleting A’s grounding without a record looks like A never supported C.
- Identity question: survival is plausible and not established. A use that required A may not survive.

#### SU-03 C loses its only support

- Initial state: only A supports C.
- Trigger: A ceases to license C, or becomes unrestorable.
- Event: the claim is unsupported.
- Changed: license.
- Unchanged: C may still be stored as a historical tuple.
- Relation to prior state: loss of support. Distinct from withdrawal (CR-04) and from correction (CR-01).
- Destinations: support record. Standing of C is separate.
- Provenance: the lost path.
- History: A and C.
- Prior judgments: yes.
- Reuse: C is not currently licensed. The event is reusable.
- Direct mutation: Core’s pre-seal retract deletes tuple and grounding together, so it cannot represent this case after the fact.
- Identity question: an unsupported C is a different epistemic object from a supported C even if the words match.

#### SU-04 Same claim, another method

- Initial state: M0 produced C from I.
- Trigger: M1 also produces C from I.
- Event: independent reconstruction.
- Changed: an additional production path.
- Unchanged: C’s content and I.
- Relation to prior state: supports, via a different method. Not a correction.
- Destinations: a second support path naming M1.
- Provenance: both methods.
- History: M0’s path.
- Prior judgments: they used M0. Agreement with M1 does not rewrite them.
- Reuse: either path, if labeled.
- Direct mutation: stamping C as produced by M1.
- Identity question: same content is not the same support path.

#### SU-05 Mechanical and semantic support for the same claim

- Initial state: C is semantic.
- Trigger: a mechanical fact is also recorded as support, or the reverse.
- Event: two origin classes license one claim.
- Changed: the support mix.
- Unchanged: the rule that origin belongs to the path, not the relation name.
- Relation to prior state: adds a path of a different class.
- Destinations: separate paths. Not a single blended origin.
- Provenance: both origins.
- History: each path.
- Prior judgments: a judgment that required semantic interpretation is not retroactively mechanical.
- Reuse: each path only for uses that accept that class.
- Direct mutation: setting the relation’s origin to one class erases the other. Construction v0 already forbids origin to live only in the relation name.
- Identity question: the claim can be one tuple with two paths. Forcing one origin is the failure.

### G. Ambiguity and resolution

Initial pattern:

```text
question Q
candidate A
candidate B
UNRESOLVED
```

#### AM-01 through AM-08 Resolution with different causes

One resulting shape is possible: A established, B not, Q closed. The cause is the scenario difference.

| Id | Cause |
| --- | --- |
| AM-01 | New source |
| AM-02 | New mechanical observation |
| AM-03 | New semantic construction |
| AM-04 | Human decision |
| AM-05 | Agent decision |
| AM-06 | Changed method |
| AM-07 | Changed source |
| AM-08 | Changed software |

Shared fields:

- Initial state: Q unresolved over A and B.
- Event: a unique selection of A.
- Changed: uniqueness.
- Unchanged: the historical unresolvedness.
- Relation to prior state: resolves.
- Destinations: later World or a decision record. W0 unchanged.
- Provenance: the cause row above. For AM-04 and AM-05, the decision is the support, not a discovered fact.
- History: Q, A, and B.
- Prior judgments: an `UNKNOWN` or construction gap for Q remains correct for W0.
- Reuse: the resolution, with its cause. A decision is not reusable as a mechanical fact.
- Direct mutation: deleting the candidates.
- Open question: whether AM-04 and AM-05 are SE-04 plus a direct assertion (EV-09). They are, when no new source or observation did the work. The provenance must say so.

AM-06 is also CM-01. AM-07 is also EV-03 or EV-04. AM-08 is also MO-11. The resolution is not a new family. The cause families remain.

#### AM-09 Previously established, later ambiguous

- Initial state: one established endpoint.
- Trigger: any cause in the table above, reversed.
- Event: loss of uniqueness.
- Changed: current correspondence.
- Unchanged: the old establishment as a historical fact.
- Relation to prior state: not a resolution. See SE-05.
- Destinations: later World.
- Provenance: the cause.
- History: the established binding.
- Prior judgments: yes.
- Reuse: the ambiguity. Not a silent deletion of the binding.
- Direct mutation: removing the binding from W0.
- Open question: same as SE-05.

### H. Correction, supersession, refinement, withdrawal, loss of support

These do not collapse.

#### CR-01 Correction

- Initial state: claim C was published.
- Trigger: C is established as the wrong claim about its own inputs.
- Event: “the prior claim was wrong.”
- Changed: C’s standing as knowledge of those inputs.
- Unchanged: the publication of C.
- Relation to prior state: corrects.
- Destinations: a later statement that C was wrong, plus any replacement claim.
- Provenance: the fault.
- History: C itself.
- Prior judgments: dependents used a wrong claim.
- Reuse: the correction. Not C as current knowledge.
- Direct mutation: editing C into the right claim.
- Open question: how dependents are found. Out of scope.

#### CR-02 Supersession

- Initial state: C was valid for its state.
- Trigger: a later state or rule replaces it for current use.
- Event: “valid then, not what we use now.”
- Changed: currency.
- Unchanged: C’s validity in its original scope.
- Relation to prior state: supersedes.
- Destinations: a current successor. C remains historical.
- Provenance: successor and the boundary between the two states.
- History: mandatory, or this becomes CR-01.
- Prior judgments: may remain correct.
- Reuse: the successor as current, C as history.
- Direct mutation: overwriting C.
- Open question: what holds the “current” relation. Not designed here.

#### CR-03 Refinement

- Initial state: C was coarse and defensible.
- Trigger: C′ distinguishes what C combined.
- Event: “more precise, not a confession of error.”
- Changed: grain.
- Unchanged: C as a defensible coarse claim.
- Relation to prior state: refines. See MO-05 and SE-10.
- Destinations: C′ plus a refinement link.
- Provenance: what was coarse.
- History: C.
- Prior judgments: they used the coarse grain and may still be right at that grain.
- Reuse: C′ does not automatically inherit C’s judgments.
- Direct mutation: replacing C with one finer part.
- Open question: when a refinement is actually a correction. The record must say which.

#### CR-04 Retraction or withdrawal

- Initial state: the system stands behind C.
- Trigger: the system stops standing behind C, whether or not C was wrong.
- Event: withdrawal of standing.
- Changed: standing.
- Unchanged: possibly the support and the historical publication.
- Relation to prior state: withdraws. Not the same as losing support, and not the same as proving C false.
- Destinations: a withdrawal record. Not necessarily deletion.
- Provenance: who withdraws, and whether this is also a correction.
- History: C, or later readers cannot see what was withdrawn.
- Prior judgments: yes.
- Reuse: C is not currently stood behind.
- Direct mutation: deleting C removes the withdrawn object.
- Open question: withdrawal without a truth-value. This scenario needs that.

#### CR-05 Loss of support

- Initial state: A licenses C.
- Trigger: SU-03.
- Event: the previous basis no longer licenses C. C’s standing is not yet decided.
- Changed: license.
- Unchanged: standing, until CR-01 or CR-04 happens.
- Relation to prior state: unsupported. The claim may still exist.
- Destinations: support record only.
- Provenance: the lost basis.
- History: the old basis.
- Prior judgments: yes.
- Reuse: not as a licensed claim.
- Direct mutation: retracting the tuple decides withdrawal as a side effect of support loss.
- Open question: whether an unlicensed claim remains citable. Deliberately open.

### I. Identity evolution

Keep separate: identity, manifestation, location, support, semantic equivalence.

#### ID-01 Subject rename

- Initial state: subject S has label L0.
- Trigger: the label becomes L1. The subject id is unchanged.
- Event: label change.
- Changed: display.
- Unchanged: identity, manifestation, location, support.
- Relation to prior state: not a new subject.
- Destinations: a label record. Judgment citations that used labels as identity were already unsafe.
- Provenance: both labels.
- History: old labels, if any prose cited them.
- Prior judgments: only those that stored the label as the subject.
- Reuse: S.
- Direct mutation: treating the new label as a new id duplicates S.
- Open question: none. Labels are already not identity in Judgment v0 citations.

#### ID-02 Subject move

- Initial state: S has location L0.
- Trigger: the same subject is at L1.
- Event: location change.
- Changed: location.
- Unchanged: identity, if the move is real. Manifestation may or may not change.
- Relation to prior state: same identity, new location.
- Destinations: a location fact. Not a new subject id solely because the coordinate changed.
- Provenance: both locations.
- History: old location, for citations that used it.
- Prior judgments: if they cited location as identity, yes.
- Reuse: S.
- Direct mutation: a new id at L1 loses the continuity.
- Open question: the evidence that the move preserved identity. That evidence is ID-08.

#### ID-03 Subject split

- Initial state: S.
- Trigger: S1 and S2 replace S as the accurate grain.
- Event: split of a mechanical subject.
- Changed: identity grain.
- Unchanged: history of S.
- Relation to prior state: splits. May be MO-05.
- Destinations: successors plus a split record.
- Provenance: the grain decision.
- History: S.
- Prior judgments: bindings to S.
- Reuse: S1 and S2 separately.
- Direct mutation: keeping one id.
- Open question: correspondence of old bindings.

#### ID-04 Subject merge

- Initial state: S1 and S2.
- Trigger: they are one subject.
- Event: merge.
- Changed: identity.
- Unchanged: the historical distinction.
- Relation to prior state: merges.
- Destinations: a successor plus a merge record.
- Provenance: why they are one.
- History: both ids.
- Prior judgments: they may differ between S1 and S2.
- Reuse: the successor, not a silent union of judgments.
- Direct mutation: collapsing ids.
- Open question: conflicts between the two histories.

#### ID-05 Semantic identity split

Same shape as SE-10. Listed here so subject split and semantic split are not one operation.

#### ID-06 Semantic identity merge

Same shape as SE-11.

#### ID-07 Manifestation replacement

- Initial state: subject S has manifestation M0.
- Trigger: M1 is the local manifestation. Identity is claimed stable.
- Event: manifestation change.
- Changed: manifestation content and its digest.
- Unchanged: identity and, unless separately changed, location.
- Relation to prior state: replaces the manifestation. Not a rename and not a new subject.
- Destinations: M1 on a later observation of S.
- Provenance: both manifestation identities.
- History: M0, because a judgment may have cited its digest.
- Prior judgments: yes if they cited content.
- Reuse: M1 for current observation of S.
- Direct mutation: overwriting M0’s bytes.
- Open question: the correspondence that says M1 is still S. A file-level digest is already known to be the wrong manifestation for a local subject.

#### ID-08 Cross-revision correspondence

- Initial state: subject S0 in snapshot A and S1 in snapshot B.
- Trigger: a comparison claims they correspond.
- Event: correspondence, which can be unique, ambiguous, unresolved, or absent.
- Changed: a cross-revision claim.
- Unchanged: both snapshots.
- Relation to prior state: adds a correspondence. Does not move either subject.
- Destinations: a comparison record outside either snapshot, or a later world that cites both. Not an edit of either snapshot.
- Provenance: basis, continuity class, and whether the basis is heuristic.
- History: both subjects.
- Prior judgments: they stay on their own snapshot until a correspondence is admitted.
- Reuse: the correspondence, with its strength. Heuristic correspondence is not identity.
- Direct mutation: copying S0’s id onto S1.
- Open question: Software Governance has not accepted cross-snapshot correspondence. Spine comparison remains one producer’s evidence.

#### ID-09 Identity assumed, later rejected

- Initial state: a correspondence or identity was admitted.
- Trigger: later evidence says it was the wrong join.
- Event: correction of an identity assumption.
- Changed: the join.
- Unchanged: the two endpoints as separate objects.
- Relation to prior state: corrects the correspondence. Does not correct either endpoint’s local facts by itself.
- Destinations: a later rejection record.
- Provenance: the faulty basis.
- History: the assumed join, because judgments may have followed it.
- Prior judgments: yes.
- Reuse: the rejection. The join is not current.
- Direct mutation: deleting the join.
- Open question: dependent bindings. Not a maintenance algorithm.

### J. Derived-fact evolution

Deterministic derivation is not semantic reconstruction.

#### DV-01 Inputs change

- Initial state: D is derived from base facts B.
- Trigger: B changes.
- Event: the derivation’s inputs changed.
- Changed: D’s currency.
- Unchanged: the derivation definition.
- Relation to prior state: D is stale relative to new inputs. The old D remains the result of old B.
- Destinations: a rerun result in a context that has the new inputs. Not an in-place rewrite that forgets old B.
- Provenance: input versions.
- History: old D and old B.
- Prior judgments: if they cited D, they cited that run.
- Reuse: the new D only with the new inputs.
- Direct mutation: replacing D while leaving a record that says it came from old B.
- Open question: none. This is the supported staleness case.

#### DV-02 Derivation implementation changes

- Initial state: definition M0 produced D.
- Trigger: definition M1.
- Event: method change of a deterministic function. A special case of CM-01.
- Changed: the function.
- Unchanged: base facts, until rerun.
- Relation to prior state: the old D is not stale merely because M1 exists. It is the output of M0.
- Destinations: a new definition and, if run, a new output.
- Provenance: both definitions.
- History: M0’s output.
- Prior judgments: they used M0.
- Reuse: M1’s output under M1.
- Direct mutation: storing M1’s rows as M0’s run.
- Open question: whether M1 is a bug fix of M0. That is an extra claim.

#### DV-03 Derivation becomes stale

- Initial state: a receipt says D matches inputs at revision R.
- Trigger: an input version or the definition version moves.
- Event: the receipt is no longer current.
- Changed: currentness of the receipt.
- Unchanged: the stored rows, until rerun.
- Relation to prior state: marks the result not current. Does not recompute it.
- Destinations: staleness status. Core already does this for registered derivations.
- Provenance: which input or definition moved.
- History: the last successful run.
- Prior judgments: they may have used a result that is now stale relative to later inputs.
- Reuse: the stale result only as the output of its own run.
- Direct mutation: deleting D because it is stale removes a still-valid historical output.
- Open question: semantic claims have no such receipt. Do not apply this status to them by analogy.

#### DV-04 Rerun produces the same output

- Initial state: D at run R0.
- Trigger: rerun.
- Event: recomputation with an unchanged result.
- Changed: the run record.
- Unchanged: D’s content.
- Relation to prior state: recomputes. Not a new fact.
- Destinations: a new receipt with the same fingerprint, if that is how the derivation works.
- Provenance: both runs.
- History: either run suffices for content. Both matter for “when it was checked.”
- Prior judgments: no content change.
- Reuse: D.
- Direct mutation: unnecessary for content. Replacing the receipt loses the earlier run time.
- Open question: whether identical output needs a new publication. Often no.

#### DV-05 Rerun produces a different output

- Initial state: D.
- Trigger: rerun yields D′.
- Event: recomputation with a different result.
- Changed: the derived claim.
- Unchanged: the definition, if only inputs changed. If the definition changed, this is also DV-02.
- Relation to prior state: recomputes. Not a semantic correction unless D was wrong for its own inputs.
- Destinations: D′ as the new run. D as the old run.
- Provenance: both fingerprints and input versions.
- History: D.
- Prior judgments: yes.
- Reuse: D′ for the new inputs.
- Direct mutation: overwriting D.
- Open question: consumers of D. Out of scope as an algorithm.

#### DV-06 Completeness basis of a derivation changes

- Initial state: a receipt with basis B.
- Trigger: the same rows are later described under basis B′.
- Event: the license for negative reads changes, not necessarily the rows.
- Changed: completeness basis.
- Unchanged: possibly the derived rows.
- Relation to prior state: a new receipt. See CV-03 and CV-04.
- Destinations: a new receipt. Derivation reruns in Core replace receipt rows for that derivation. That replacement is a supported mechanical behavior and is the reason governance coverage could not use it.
- Provenance: both bases.
- History: the old basis, if any negative read used it.
- Prior judgments: yes if they used absence.
- Reuse: the new basis only.
- Direct mutation: Core’s derivation receipt replacement is exactly the hazard for a claim whose old basis must remain citable.
- Open question: already answered for governance coverage. Not answered for every future derivation.

### K. Judgment and investigation promotion

Destinations, none chosen:

```text
remain ephemeral
case-local
judgment artifact
investigation cache
new source artifact
new construction candidate
new sealed World assertion
new World revision
```

#### PR-01 Investigation finds an existing World assertion

- Initial state: W0 already contains A.
- Trigger: an investigation locates A.
- Event: discovery of existing knowledge.
- Changed: nothing in the knowledge. The investigation’s working set grew.
- Unchanged: W0.
- Relation to prior state: cites. Does not add, correct, or promote.
- Destinations: case expansion only.
- Provenance: the assertion id and world revision.
- History: W0 already is the history.
- Prior judgments: no new dependence.
- Reuse: A was already reusable.
- Direct mutation: copying A into a side store as if it were new creates a second claim.
- Open question: none. This is not write-back.

#### PR-02 Investigation derives a new semantic relationship

- Initial state: the relationship is not in W0.
- Trigger: investigation constructs it from material already in hand.
- Event: a new semantic claim, not yet admitted.
- Changed: a proposal exists.
- Unchanged: W0.
- Relation to prior state: proposes an addition.
- Destinations: any of the list except “already in W0.” Admission is separate.
- Provenance: inputs, method, and that this was investigation rather than the original constructor.
- History: W0. The proposal, if later admitted.
- Prior judgments: not until something cites the proposal.
- Reuse: not before admission.
- Direct mutation: inserting it into W0 skips admission.
- Open question: whether investigation output is a candidate (SE-03) or a direct assertion (EV-09).

#### PR-03 Investigation finds a missing mechanical relationship in raw software

- Initial state: the producer did not emit relation R.
- Trigger: a person or agent sees R in the software.
- Event: a proposed mechanical observation that the admitted producer did not make.
- Changed: a proposal. Not yet an observation of record.
- Unchanged: the producer output.
- Relation to prior state: proposes an observation. It is not a semantic binding.
- Destinations: a request for construction by a producer, or a direct mechanical assertion if no producer is used. Those are different.
- Provenance: who observed it, and that the producer did not.
- History: the producer’s omission, which may be scope rather than error.
- Prior judgments: a judgment gap that requested this fact.
- Reuse: only after a mechanical publication path admits it.
- Direct mutation: inserting R beside producer facts makes an agent reading look like the producer’s.
- Open question: EV-09 versus a producer rerun. The scenario splits on that choice. Not decided.

#### PR-04 Judgment establishes a case-local program finding

- Initial state: a case cites W0.
- Trigger: judgment records “the resolved target is X” or “the path is P.”
- Event: a finding in the judgment artifact.
- Changed: the artifact.
- Unchanged: W0.
- Relation to prior state: reports. Does not add a World fact. Judgment v0 already keeps it outside the World.
- Destinations: judgment artifact. Promotion is a later, separate event (PR-07, PR-08).
- Provenance: case, world revision, assertion ids, method fingerprint.
- History: the artifact and W0.
- Prior judgments: this is that judgment.
- Reuse: not as World knowledge.
- Direct mutation: writing the finding into W0 promotes it silently.
- Open question: PR-06, when the same finding is expensive to repeat.

#### PR-05 Judgment derives a semantic conclusion

- Initial state: applicability or conformance is decided.
- Trigger: the evaluator applies a rule.
- Event: a semantic conclusion about this case.
- Changed: the artifact’s applicability or conformance.
- Unchanged: the proposition and the mechanical facts.
- Relation to prior state: concludes for the case. The conclusion is not a new governance proposition unless promoted.
- Destinations: judgment artifact.
- Provenance: rule parameters and cited facts.
- History: yes.
- Prior judgments: this judgment.
- Reuse: the conclusion does not apply to other subjects because the words match.
- Direct mutation: storing `CONFORMS` as a World tuple makes a case result look like a construction fact.
- Open question: promotion, explicitly later.

#### PR-06 Repeated judgments reconstruct the same expensive fact

- Initial state: several artifacts contain the same finding from the same citations.
- Trigger: the cost of repeating the work.
- Event: a desire to cache. Not new knowledge.
- Changed: nothing epistemic if the finding is the same.
- Unchanged: W0 and the rule.
- Relation to prior state: recomputes, like DV-04, but the result is a judgment finding rather than a derivation.
- Destinations: a cache is possible. A World assertion is a different event and would be promotion.
- Provenance: the original citations. A cache that drops them is not the same fact.
- History: the artifacts.
- Prior judgments: they already contain the finding.
- Reuse: a cache may be reused only while the citations still match. That reuse is not World publication.
- Direct mutation: publishing the cache as a new fact hides its dependence on the case.
- Open question: when a cache becomes indistinguishable from publication. This scenario exists to keep that line visible.

#### PR-07 An agent proposes that a case-local finding become reusable

- Initial state: a finding is only in an artifact.
- Trigger: an agent proposes promotion.
- Event: a proposal.
- Changed: a proposal exists.
- Unchanged: W0 and the artifact’s meaning.
- Relation to prior state: proposes. Does not publish.
- Destinations: a proposal record. Not W0.
- Provenance: artifact, actor, proposed destination.
- History: the artifact remains the origin.
- Prior judgments: the source judgment.
- Reuse: not yet.
- Direct mutation: accepting the proposal by writing W0.
- Open question: admission criteria. Not designed.

#### PR-08 A human approves that proposal

- Initial state: PR-07.
- Trigger: a person approves.
- Event: an admission decision. Still not, by itself, a publication into W0.
- Changed: the proposal’s standing.
- Unchanged: W0, until a later publication scenario actually publishes.
- Relation to prior state: admits a candidate for publication.
- Destinations: an admission record, then whatever publication path is later chosen.
- Provenance: the approval, separate from the agent’s proposal.
- History: proposal and approval.
- Prior judgments: the source artifact must remain the origin of the content.
- Reuse: only after the publication event, and only in the scope that was approved.
- Direct mutation: treating approval as an edit of W0 skips publication provenance.
- Open question: the publication step. Deliberately not specified.

### L. Agent-authored knowledge

For each row, the stages are different events:

```text
proposal
admission
publication
standing
support
```

Agent-produced does not mean low-confidence, and it does not mean publishable.

| Id | Event | Epistemic class | What publication would add | What it is not |
| --- | --- | --- | --- | --- |
| AG-01 | Agent discovers an existing source | Discovery | Nothing | Ingestion or interpretation |
| AG-02 | Agent creates a source | Source creation (EV-08) | A source, after ingestion | A World claim |
| AG-03 | Agent proposes a semantic assertion | Proposal (EV-09 or SE-01) | A semantic claim, only if later admitted | A mechanical fact |
| AG-04 | Agent proposes a mechanical assertion | Proposal of an observation the producer did not emit (PR-03) | A mechanical claim, only through a declared observation path | A semantic binding |
| AG-05 | Agent resolves an ambiguity | Decision (AM-05) | A resolution whose support is the decision | A new measurement |
| AG-06 | Agent corrects its own earlier assertion | Correction (CR-01) | A statement that the earlier claim was wrong | A quiet overwrite |
| AG-07 | Agent supersedes its own earlier assertion | Supersession (CR-02) | A successor | A correction |
| AG-08 | Agent creates a reusable semantic identity | Identity introduction (SE-09) | An identity, only if the join qualifies | A label |
| AG-09 | Agent requests a new construction capability | A request for a producer or method | Nothing in the World | The capability itself |
| AG-10 | Agent promotes a judgment finding | Proposal (PR-07) | Nothing until admission and publication | Publication |

### M. Human, external system, mechanical producer

Repeat every AG event with the actor replaced by a person, an external system, or a mechanical producer.

Actor type is provenance for discovery, source creation, semantic proposal, correction, supersession, and promotion. The event shape does not change.

Actor type changes the event in these cases:

- A mechanical producer emitting a fact (MO family) is an observation. The same bytes proposed by an agent (AG-04) are a proposal about an observation. Collapsing them forges producer output.
- A human or agent resolution (AM-04, AM-05) is a decision. A producer moving from `MULTIPLE_CANDIDATES` to `RESOLVED` (MO-08) is an observation. The resulting uniqueness can look identical.
- An external system’s correction of its own evidence (EV-04) changes the evidence store. An agent’s correction of a claim (AG-06) does not change the source bytes.
- Standing can differ by actor. Standing is not a reason to invent a different claim shape per actor.

No actor-specific primitive is justified by the catalogue. Provenance and standing fields are.

### N. Concurrent and divergent evolution

#### CO-01 Independent additions

- Initial state: W0.
- Trigger: process A adds X. Process B adds Y. X and Y do not speak about each other.
- Event: two additions.
- Changed: two candidate extensions.
- Unchanged: W0.
- Relation to prior state: two uses of “adds.”
- Destinations: two later publications, or one publication that contains both if both are admitted.
- Provenance: both processes.
- History: W0.
- Prior judgments: unchanged if they cited only W0.
- Reuse: X and Y, if admitted.
- Direct mutation: either edit of W0 hides the other and the base.
- Open question: whether independence is known. If it is not known, this is not this scenario.

This is composition of simpler additions. It is not a new epistemic primitive. Conflict is not present.

#### CO-02 Same claim, constructed differently

- Initial state: W0 from M0.
- Trigger: another process runs M1 on the same inputs and also gets C.
- Event: SU-04 across two processes.
- Changed: a second path.
- Unchanged: C’s content and I.
- Relation to prior state: supports.
- Destinations: two support paths.
- Provenance: both methods and both processes.
- History: both.
- Prior judgments: the one that used M0.
- Reuse: C, with the path labeled.
- Direct mutation: picking one method name.
- Open question: none beyond SU-04.

#### CO-03 Conflicting semantic assertions

- Initial state: W0.
- Trigger: A asserts P. B asserts not-P, or an incompatible P′.
- Event: conflict.
- Changed: two incompatible proposals or publications exist.
- Unchanged: W0, and the fact that conflict is not itself a resolution.
- Relation to prior state: two additions that cannot both be current.
- Destinations: both claims, plus an explicit conflict. Not a silent choice.
- Provenance: both supports.
- History: both claims.
- Prior judgments: any that picked one.
- Reuse: neither, as the settled claim, until a resolution scenario runs.
- Direct mutation: keeping the later write.
- Open question: resolution is AM or CR, and it is a further event.

#### CO-04 Conflicting corrections

- Initial state: C is published.
- Trigger: one process says C was wrong in way F1. Another says F2, incompatible with F1.
- Event: conflict about the correction, not yet a correction.
- Changed: two proposed corrections.
- Unchanged: C, until one is admitted.
- Relation to prior state: proposes CR-01 twice.
- Destinations: both proposals.
- Provenance: both.
- History: C and both proposals.
- Prior judgments: not yet rewritten.
- Reuse: neither correction as settled.
- Direct mutation: applying one overwrite.
- Open question: same as CO-03.

#### CO-05 One branch supersedes a claim another branch relies on

- Initial state: branch B’s work depends on C. Branch A supersedes C.
- Trigger: both exist.
- Event: supersession composed with an unaware dependent.
- Changed: C’s currency on branch A. B’s dependence.
- Unchanged: B’s local use of C until B is reconsidered.
- Relation to prior state: CR-02 plus a dependent.
- Destinations: the supersession and the dependent’s citation of historical C.
- Provenance: the dependence.
- History: C, or B cannot be understood.
- Prior judgments: B’s judgments cite C.
- Reuse: A’s successor is not automatically B’s input.
- Direct mutation: replacing C under B.
- Open question: notification of dependents. Not a merge algorithm.

#### CO-06 Human and agent resolve differently

- Initial state: Q unresolved.
- Trigger: a person selects A. An agent selects B.
- Event: AM-04 and AM-05 in conflict.
- Changed: two decisions.
- Unchanged: the mechanical facts.
- Relation to prior state: two resolutions, not one established fact.
- Destinations: both decisions. Current uniqueness is not established by either alone.
- Provenance: both actors and both choices.
- History: Q and both decisions.
- Prior judgments: none have a unique subject yet.
- Reuse: neither selection as the binding, until a further admission.
- Direct mutation: the later decision wins.
- Open question: standing between the two decisions. Not an authority hierarchy.

#### CO-07 Different constructor versions, same inputs

This is CM-01 across two processes. It is not a distinct epistemic event. It becomes CO-03 if the outputs conflict, or SU-04 if they agree.

Concurrent divergence does not require a new primitive before a conflict exists. CO-03, CO-04, CO-05, and CO-06 are conflicts composed from simpler events. They are distinct only in that both sides must remain representable at once. A model that can store only one current successor cannot represent them.

### O. Historical retention

Applied across the catalogue.

| Question | Scenarios that answer yes |
| --- | --- |
| Must the prior state remain inspectable? | Any scenario a judgment, case, or support path cites: EV-03, EV-04, EV-05, MO-03, MO-07, MO-11, SE-04, SE-05, SE-06, SE-07, CR-01, CR-02, CR-04, ID-07, ID-08, ID-09, DV-05, PR-04, CO-05. |
| Does the later state replace only the current view? | SE-07, SE-13, CR-02, CV-02 when it is not a correction. |
| Can prior judgments reconstruct the state they used? | Only if the cited revision, evidence bytes, assertion, and support path remain. EV-04 and EV-05 are the sharp cases. |
| Does deletion destroy evidence a prior artifact needs? | Yes for EV-04, CR-01, CR-04, SU-03, ID-09, and any in-place rebuild of a cited world. |
| Was the old claim wrong, obsolete, unsupported, or merely not current? | CR-01, CR-02, CR-05, and SE-13 respectively. CV-06 is the case where the catalogue refuses to guess. |

Destructive replacement loses meaning in the “yes” rows of the first and fourth questions. Preserving every prior claim as if it were current loses meaning in section 10.

## 3. Normalized dimensions

Derived from the records. A dimension earns its place only if two scenarios differ on it while matching on the others.

| Dimension | Independent? | Collapses into |
| --- | --- | --- |
| What changed: source, mechanical observation, semantic interpretation, support, identity, scope, method, currency, derived result | Yes | Not into one “edit” |
| Cause: new evidence, input change, producer change, method change, scope, interpretation, correction, supersession, resolution, decision, recomputation, promotion | Yes, as provenance of the event | Not into “what changed.” MO-07 can be several causes with one resulting shape |
| Actor: source provider, mechanical producer, constructor, human, agent, judgment process, external system | Only sometimes | Provenance, except where section M says the event itself changes |
| Relation to prior state | Yes | The names below |
| Persistence destination | Yes | Not into the epistemic event. PR-04 can stay in an artifact or later be proposed for a World |
| Reuse scope: case, session, profile, world, cross-revision, source | Yes | Not into destination. A World assertion can still be historically scoped |
| Epistemic class: mechanical, semantic, derived, source-native, candidate, unresolved, decision, hypothesis | Yes | Not into actor |

Relation names that the scenarios actually separate:

```text
ADDS          EV-01, SE-01, SE-03, MO-06
SUPPORTS      EV-06, SU-01, SU-04
REFINES       MO-05, CR-03, CV-05
RESOLVES      SE-04, MO-08, AM-01–AM-08
SUPERSEDES    SE-07, CR-02
CORRECTS      EV-04, MO-03, SE-06, CR-01, ID-09
WITHDRAWS     CR-04
LOSES_SUPPORT CR-05, SU-03, EV-07
SPLITS        ID-03, SE-10
MERGES        ID-04, SE-11
RECOMPUTES    DV-01, DV-04, DV-05
PROPOSES      EV-09, PR-02, PR-07, AG-03
ADMITS        PR-08
```

`PROMOTES` is not a single relation. PR-01 is a citation. PR-07 is a proposal. PR-08 is admission. Publication is yet another event. One verb would conflate them.

Actor is not an independent epistemic dimension for most rows. Cause and epistemic class already carry the difference between a decision and an observation.

Destination is independent of relation. The same `ADDS` can be a proposal, a source, or a sealed assertion.

## 4. Equivalence clusters

### Cluster 1 — Another publication over inputs

Common: W0 stays. A later publication carries new or different rows. Members: EV-01, EV-03, MO-01, MO-02, MO-10, MO-11, CM-01, CV-01, CV-07.

Still different: whether the software changed, the producer changed, the method changed, or only the scope changed. Provenance required: input ids, producer version, method fingerprint, universe.

Counterexample: treating CM-01 and MO-11 as one “reconstruct a newer world” makes a method change look like a software change. A judgment of the old software is then read as a judgment of the new method’s world.

### Cluster 2 — Support-set change, same claim content

Common: the tuple can stay. Members: SU-01, SU-02, SU-04, SU-05, EV-06.

Still different: growing, shrinking, and mixing origin classes. Provenance required: each path’s origin and method.

Counterexample: SU-03, losing the only support, does not belong. The claim is no longer licensed. Putting it here erases CR-05.

### Cluster 3 — Resolution of a recorded question

Common: candidates and a question become a unique selection. Members: SE-04, AM-01 through AM-08.

Still different: the cause. Provenance required: the cause table in family G.

Counterexample: AM-04, a human decision, is not AM-02, a new mechanical observation. The selected subject can be the same.

### Cluster 4 — Grain change

Common: one object becomes several, or several become one, at a finer or coarser grain. Members: MO-05, ID-03, ID-04, SE-10, SE-11, CR-03.

Still different: mechanical subject versus semantic identity, and refinement versus correction. Provenance required: the grain kind and whether the old grain was wrong.

Counterexample: ID-01, a rename, is not a split. ID-07, a new manifestation, is not a new identity.

### Cluster 5 — Currency change without calling the past wrong

Common: something remains valid and is not current. Members: SE-07, SE-13, CR-02, CV-02 when the shrink is a choice.

Still different: a replaced normative claim, a retired identity, and a narrower scope. Provenance required: the successor and the boundary.

Counterexample: CR-01. A correction says the past claim was wrong. Clustering it with supersession makes every bug fix a “new era.”

### Cluster 6 — Deterministic recomputation

Common: a function of declared inputs is run again. Members: DV-01, DV-02, DV-03, DV-04, DV-05, DV-06.

Still different: stale versus rerun, same output versus different output, input change versus definition change. Provenance required: input versions and definition identity.

Counterexample: SE-06, a semantic correction, is not a derivation rerun. Construction origin stays on the path that produced the claim.

### Cluster 7 — Downstream proposal, not yet knowledge

Common: something outside W0 might later become reusable, and is not reusable yet. Members: PR-02, PR-03, PR-07, AG-03, AG-04, AG-10, EV-09.

Still different: semantic proposal, mechanical proposal, and promotion of an existing finding. Provenance required: origin artifact, actor, and proposed destination.

Counterexample: PR-01. Finding an assertion that is already in W0 is not a proposal.

### Cluster 8 — Conflict that must keep both sides

Common: two later events cannot both be the single current outcome. Members: CO-03, CO-04, CO-06, and CO-05’s dependent.

Still different: conflict of claims, conflict of corrections, conflict of decisions, and a dependent that still cites the old claim. Provenance required: both sides and the object they conflict about.

Counterexample: CO-01, independent additions, is not a conflict. CO-07 is not a conflict unless the outputs disagree.

Failed cluster: “all of these are a new World.” It fits cluster 1 only. It corrupts cluster 2 (support can change without a new claim), cluster 6 when the output is identical, PR-01, PR-04, and CR-05.

Failed cluster: “all of these are new assertions plus a current-view flag.” It almost fits additions and supersession. It fails CR-04 if withdrawal is not a new assertion about standing, and it fails EV-05 if unavailability is stored as a new claim that the old claim is false.

## 5. Falsifying small primitive sets

### Set P: `ADD`, `SUPERSEDE`, `WITHDRAW`, `RECONSTRUCT`, `PROMOTE`

| Scenario | Failure |
| --- | --- |
| SU-01 | Adding support is not adding a claim, and it is not supersession. |
| CR-01 versus CR-02 | One `SUPERSEDE` covers both a bug fix and a valid successor. |
| CR-03 | Refinement is not supersession and not addition of an unrelated claim. |
| CR-05 | Loss of support is not withdrawal. |
| AM-04 versus AM-02 | `ADD` of a binding loses the decision-versus-observation cause. |
| PR-01 | Not `PROMOTE`. |
| PR-07 versus PR-08 | One `PROMOTE` covers proposal and admission. |
| DV-04 | Recompute with the same output is not add, supersede, or withdraw. |
| CO-03 | No primitive keeps both conflicting claims current-or-not without a conflict record. |
| ID-01 | Rename is none of these. |

P is too small.

### Set Q: new revision only

Every event becomes `I′ + M′ → W1` beside W0.

| Scenario | Failure |
| --- | --- |
| EV-02 | Ingestion is not a World. |
| EV-09 | A proposal is not yet a revision. |
| PR-04 | A judgment artifact is not a World revision. |
| SU-02 | A support change that keeps the claim does not have to be a full new world, and a full new world that copies the claim without the support delta loses the point. |
| DV-03 | Staleness is a status of a receipt, not a new sealed world. |
| CR-05 | A new world that omits the claim has withdrawn it. A new world that keeps it has not recorded the lost support. |
| CO-06 | Two revisions do not record that the two resolutions conflict. They look like two unrelated worlds. |

Q preserves history and erases event type.

### Set R: new assertions plus a current-view projection

Later facts are added. A projection picks the current ones.

| Scenario | Failure |
| --- | --- |
| EV-04 | Correcting evidence bytes is not an assertion. Overwriting bytes breaks reconstruction. |
| MO-03 | The old fact must stay true of the old publication. A current-view flag on a shared tuple makes the old judgment read the new fact. |
| DV-06 | Replacing a completeness receipt in place is the current derivation behavior, and it is unsafe for any reader that cited the old basis. |
| CR-01 | A current flag does not say the old claim was wrong. Readers can still treat it as an alternative current. |
| SE-09 | An identity is not a current-view of two claims. It is a new equivalence. |

R is close to a usable lower bound for claim-shaped events and fails for evidence bytes, cited historical facts, and equivalences.

### Set S: every downstream discovery returns through Construction

| Scenario | Failure |
| --- | --- |
| PR-01 | Already constructed. Returning through construction duplicates it. |
| PR-04 | The finding is a report over a sealed world. Forcing reconstruction republishes an observation as if it were new. |
| EV-08 | Source creation happens before construction. |
| AM-05 | A decision is not a reconstruction of inputs. |
| AG-09 | A request for a capability is not a candidate tuple. |
| PR-06 | A cache of a repeated finding is not a new construction. Treating it as one publishes it. |

S is the right gate for PR-02 and for mechanical proposals that lack a producer (PR-03), and the wrong gate for discovery, judgment reports, source creation, and decisions.

No set above is forced. The breaks are the test.

## 6. Invariants

### Persistence is not truth

Recording an event means the system keeps that event, its provenance, and its epistemic class. It does not mean the event is universally true.

No scenario in this catalogue contradicts that. EV-09, AM-04, CR-04, and CO-03 are unrepresentable if retention implies truth. A stored conflict would become a stored truth. A stored withdrawal would become a stored falsehood. A stored direct assertion would become a stored fact about the software.

### Exploration provenance is not support provenance

| Scenario | Retain investigation activity | Retain admitted evidence | Both | Neither |
| --- | --- | --- | --- | --- |
| PR-01 | No, beyond the case’s citation | Already in W0 | | |
| PR-02 before admission | The proposal | | | |
| PR-02 after admission | Optional | The admitted claim’s support | If the search itself is part of the justification | |
| PR-04 | | The cited World assertions | The artifact, not the search log | |
| A broad search that ends in one source | Only if the search is why that source is enough | The source | When the procedure is the warrant | When the source’s own content is the entire warrant |

Judgment v0 already refuses chain-of-thought storage. That does not forbid retaining the admitted citations. It forbids retaining the search as if it were support.

### Sealed-state dependence

Operations that must preserve references used by an existing case or judgment: any change to evidence bytes (EV-03, EV-04, EV-05), assertion tuples (MO-03, SE-06), support paths those artifacts fingerprint (SU-02, SU-03), manifestation bytes (ID-07), and world revision identity (MO-11, CM-01). Judgment v0 citations are assertion id plus support fingerprint. A later event that rewrites either breaks the citation.

Operations that need not preserve a current-view pointer: SE-13, CR-02. They must preserve the old object, not its currency.

### Freedom in construction, rigidity in durable claims

Still useful. A constructor, person, or agent may explore widely. The durable claim is the admitted record.

| Event | Free exploration | Rigid durable record |
| --- | --- | --- |
| Direct assertion EV-09 | The proposal can be informal | Admission has to record sourceless support honestly |
| Promotion PR-07 | The proposal can be repeated | Publication is a new event |
| Correction CR-01 | Several hypotheses (CO-04) | The admitted correction does not edit the old claim |
| Resolution AM-04 | Several decisions (CO-06) | The admitted selection keeps the old unresolved state |
| Method change CM-01 | Many methods | Each published output keeps its method |

The invariant fails if exploration is stored as admitted knowledge, or if an admitted claim is edited in place.

### No silent epistemic promotion

A case-local or exploratory result does not become reusable World knowledge because it was useful.

| Scenario | Violation if treated as already World knowledge |
| --- | --- |
| PR-01 | No violation. It was already there. |
| PR-02 | Yes |
| PR-03 | Yes, and it would also forge a producer |
| PR-04, PR-05 | Yes |
| PR-06 | Yes, a cache would become a fact |
| PR-07 | Yes, a proposal would become a fact |
| PR-08 | Yes, if approval skips publication |
| SE-12 | Yes, if every direct claim grows an identity because it was reused |

## 7. Agent, human, and source creation

Covered by EV-08, EV-09, family L, and section M. The structural points:

- Creating a source is not asserting the claims in it.
- Ingesting a source is not interpreting it.
- A direct assertion has no source to reconstruct. Its support is the decision.
- The same three events exist for a person, an agent, and an external system.
- A mechanical producer’s emission is not a direct assertion.

## 8. Downstream promotion

PR-01 through PR-08. The reusable sequence, if it ever happens, is at least:

```text
case-local result
    → proposal
    → admission
    → publication
```

Skipping a step is silent promotion. PR-01 never enters the sequence.

## 9. Where destructive mutation loses history

- EV-04 and EV-05: the bytes a judgment reconstructed.
- MO-03, MO-07, MO-11: the observation a finding cited.
- SE-04 and AM-09: the unresolved question or the old binding.
- SE-06 and CR-01: the wrong claim that was actually published.
- CR-02 and SE-07: the valid older claim.
- CR-04: the withdrawn claim.
- SU-03: the support that used to license the claim.
- ID-07 and ID-09: the manifestation or the rejected join.
- DV-05 and DV-06: the old derived output or the old completeness basis.
- CO-05: the claim a dependent branch still cites.
- Legacy in-place rebuild: the prior sealed bundle.

## 10. Where keeping every prior claim as current misleads

- CR-01: a corrected claim still appears available as knowledge.
- CR-02: a superseded rule still appears to be the rule in force.
- SE-13: a retired identity still joins new work.
- CV-04: a `COMPLETE` receipt still licenses negative readings after a gap is known.
- MO-03: a buggy observation still appears to be the producer’s current output.
- CO-03 and CO-06: both sides of a conflict appear settled.
- CV-07 read backwards: an old incomplete absence appears to deny a fact that was only unobserved.
- PR-06: every cached copy appears to be an independent established fact.

These rows need a way to say “not current” or “not licensed” without deleting the record. The catalogue does not choose that way.

## 11. Relation to current Core, Construction, and Judgment

No accepted constraint is contradicted. Several current mechanisms are narrower than the catalogue and will be misused if treated as the general solution.

| Current fact | What it already separates | What it does not solve |
| --- | --- | --- |
| Assertion id is the tuple. Grounding is separate. | SU-01 can keep one claim identity while support grows, in principle. | SU-03 and CR-04. Pre-seal `retract` deletes both. |
| Origin is on the support path. | SU-05. | A storage model that stamps one origin on the relation name. |
| Fresh-address publication. | History for events that are new publications. | EV-02, EV-09, PR-04, DV-03, CR-05. |
| Legacy in-place rebuild. | A compatibility editor. | Every row in section 9. |
| Derivation staleness and receipt replacement. | DV-01, DV-03 for registered SQL. | Semantic claims. DV-06 for any receipt a judgment cited. Governance coverage already refused this receipt. |
| Incomplete coverage is not a negative. | CV-07, the Judgment negative control. | CV-06 until its cause is classified. |
| World, case, and judgment artifact are different. | PR-01, PR-04, PR-05. | PR-07 and PR-08, which are intentionally not specified. |
| Manifestation is optional and not identity. | ID-01, ID-07. | ID-08, which Construction v0 does not claim. |
| Semantic identity is optional and narrow. | SE-09’s one demonstrated join. | SE-10, SE-11, SE-13. |
| Method fingerprint on a judgment. | CM-01 for that evaluator. | A general rule that every future method must use that fingerprint shape. |

## 12. Unresolved architectural questions

These are questions. They are not tasks to design in this pass.

1. Which events are a new sealed World, which are records outside any World, and which are support paths on an existing claim.
2. Whether claim identity survives SU-01 and SU-02.
3. Whether an unsupported claim (CR-05, EV-05) remains citable.
4. How a correction (CR-01) is distinguished, in stored provenance, from supersession (CR-02) and refinement (CR-03).
5. What “current” refers to when several publications and several decisions exist (SE-07, CO-03, CO-06).
6. Which cause in CV-06 actually happened.
7. Whether a direct assertion (EV-09) can be admitted, and what support class it carries.
8. Whether a mechanical fact seen by an agent (PR-03) must be re-emitted by a producer.
9. The publication step after PR-08.
10. Cross-revision correspondence (ID-08) for Software Governance, which is not accepted.
11. Split, merge, and retirement of semantic identity (SE-10, SE-11, SE-13), which are not demonstrated.
12. How dependents of a corrected or superseded claim are discovered, without specifying an algorithm.

## 13. What this catalogue does not yet justify

- A graph mutation API.
- An event log, a CRDT, or a branch-and-merge implementation.
- Append-only storage as a requirement, or mutable overwrite as a requirement.
- A generic persistence framework.
- New Core primitives, including an assertion role, a current-pointer type, or a universal relation.
- A change to World revision semantics.
- Agent write access, human approval workflow, or an authority hierarchy.
- A maintenance or change-impact algorithm.
- A production promotion pipeline.
- Treating a newer method, producer, or model as truer.
- Promoting a judgment finding, a cache, or an investigation note into a World assertion.
- Collapsing correction, supersession, refinement, withdrawal, and loss of support.
- Collapsing source creation, ingestion, interpretation, and direct assertion.
- Using derivation staleness as the model of semantic change.
- Using spine comparison, authority maintenance, or historical GovernanceCase layout as the storage model.
- A single primitive set. Section 5 shows the breaks in four small sets and does not pick a winner.

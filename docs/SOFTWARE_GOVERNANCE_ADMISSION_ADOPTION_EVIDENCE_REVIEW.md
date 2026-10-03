# Software Governance admission/adoption evidence review

**Status: research / architecture evidence review. Not a contract, not
accepted architecture, not an implementation plan, not a Decision design,
not an admission design, not an authorization design.**

This note collects repository evidence about what, if anything, is missing
between a semantic proposal and durable published governance. It implements
nothing, designs no subsystem, and changes no production code. Section
numbers below follow the task brief's required report structure (§32);
explicit answers follow §33.

## 1. Question and scope

The reconsideration experiment ends with a well-formed semantic proposal —
"consider `governance_binding(P, A1)` for admission" — and no rule that may
promote it into a sealed World. This review asks what problem that gap
actually is: whether "admission" names one missing responsibility, several,
or none, and what the repository already establishes, contradicts, or leaves
unspecified. Evidence first (§§2–20), assessment second (§§21–24).

## 2. Current concrete proposal/admission gap

Executable facts, in order:

1. The Investigation proposal envelope (`ontology_author/software_governance/investigation/records.py:56-80`,
   `make_proposal`) enforces only two things: `epistemic_class` membership
   in `("mechanical", "semantic", "source/evidence", "other")`, and the
   absence of `assertion_id` from payload and basis. Payload, basis, method,
   and reason are otherwise free-form. A proposal therefore establishes
   almost nothing by construction: a typed, provenance-bearing suggestion
   that is explicitly not an assertion.
2. The only production producer of proposals,
   `profiles/software_governance_config_v0/investigate.py:117-135`, emits
   `epistemic_class="mechanical"` for a manifestation field the producer did
   not assert. The `"semantic"` class has zero production producers; its
   only uses are two test-local calls (write-semantics rejection control;
   reconsideration binding proposal).
3. Nothing in production consumes a proposal. `Construction does not import
   Investigation` and `Judgment does not import Investigation` are asserted
   acceptance boundaries (`docs/SOFTWARE_GOVERNANCE_INVESTIGATION_ACCEPTANCE.md:45-46`;
   a repo-wide grep for `proposal` outside `investigation/` returns no
   production reader). Proposals are currently write-only sidecars.
4. The reconsideration probe's semantic proposal for `binding(P, A1)` was
   motivated by bridge-plus-inquiry after an `UNKNOWN` verdict, because both
   accepted evaluators require an established binding for `APPLIES`
   (`profiles/software_governance_config_v0/judge.py:60-62`,
   `profiles/software_governance_v0/judge.py:61-62`: "an established binding
   joins this proposition to a subject of the ruled kind"). So the concrete
   gap is narrower than "no admission": there is no stated rule for what
   licenses the *first* binding row, and the obvious candidate trigger (an
   `APPLIES` verdict) presupposes the row already exists.

## 3. Existing publication/construction gates

Every gate before an assertion becomes sealed knowledge, traced from code:

| # | Gate | Input inspected | Property established | Kind | On failure | Rule supplier |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | Kernel `Contract.admit_assertion` per `assert_tuple` (`ontology_author/world/core/contract.py:345-415`) | scope, mode, origin, grounding presence, semantic-reference kinds | Provenance present; scope valid; semantic vocabulary authorized; WORLD BASE has SOURCE grounding (or construction method for semantic) | Structural / mechanical | `ContractAdmissionError` (`GroundingError` for ungrounded BASE) | Frozen Core contract |
| G2 | `admission_errors()` sweep + `validate_contract_admission` at commit (`ontology_author/world/runtime/world.py:308-...`, `commit.py:41-52`) | All BASE assertions, candidate integrity, semantic references | Whole-candidate re-validation of G1 plus reference validity | Mechanical | World not sealed; prior World intact | Frozen Core contract |
| G3 | `validate_governance_world` (`ontology_author/software_governance/validation.py:43-85`) | Schemas, origins, subject receipts, grounding recoverability, method/contract/support/endpoint/software-evidence presence, completeness shape | Representational validity: well-formed, grounded, origin-labeled, consistently classified | Structural / mechanical / evidentiary-presence | `GovernanceConstructionResult(succeeded=False, errors)`; no publication | Application contract v0 |
| G4 | Publication mechanics (`ontology_author/software_governance/construction.py:119-287`) | Output address, staging copy, seal operation | Fresh address; atomic seal-or-nothing | Mechanical | Error result; staging discarded | Application/Core runtime |
| G5 | Producer positive rules (e.g. Construction contract §4; config span rule) | Producer's own inputs | Endpoint assignments established before positive emission | Mechanical (producer-owned) | No positive row, or `MULTIPLE_CANDIDATES`/`UNRESOLVED` instead | Producer capability |
| G6 | `verify_case` (read side, `ontology_author/software_governance/judgment/case.py:78-109`) | Case citations vs sealed assertions + support fingerprints | Citation integrity for a presented case | Mechanical (read gate, not write gate) | Error list; case unusable | Judgment v0 |

Passing G1–G5 implies: well-formed, grounded-in-recoverable-bytes,
origin-labeled, consistently classified knowledge. It does not imply truth
(Construction contract §11: "Admission does not decide that a governance
proposition is true, and a passing admission MUST NOT be presented as
adjudication"), acceptability, or authority. No gate is semantic-adequacy,
organizational, or authorization-related. These are not one "admission
layer": G1/G2 are frozen kernel mechanics, G3 is application representation
policy, G4 is publication mechanics, G5 is producer discipline, G6 is a
read check.

## 4. Meaning of governance_binding today

The strongest statement the contracts support:

> `governance_binding(P, S)` is an **established concern/correspondence**
> between source-derived governance knowledge P and a mechanically
> identified software subject S, grounded by the correspondence basis.

Evidence: Construction contract §7 frames the relation as answering
"Which governance knowledge concerns which mechanically identified
software subject?"; the read surface (§13) asks "What governance knowledge
concerns this software subject?"; the binding is "grounded by the
correspondence basis," distinct from the proposition's evidence. Tested
against the candidate meanings:

- "P is semantically applicable to S" — **not supported as the meaning.**
  Applicability is Judgment's word, and both evaluators treat the binding
  as *input* to an `APPLIES` verdict, not as the verdict itself.
- "P has been organizationally adopted for S" / "P is currently in force
  for S" — **not supported.** No contract text, test, or artifact uses
  adoption/in-force language for the row; decision/adoption workflow is an
  explicit non-goal (Construction contract §14).
- "P is established governance concerning S" — **supported**, with
  "established" meaning "published through the construction path with the
  required basis," not "proven true."
- "There is evidence connecting P and S" — **supported**, and the
  weakest safe reading.
- "P should be evaluated against S" — **not supported.** Selection is a
  separate front-door responsibility; nothing in the row requests inquiry.

Two under-specifications matter more than any missing gate. First, no
contract states **who or what decides a binding row exists**: in both
acceptance profiles the rows are human-authored fixture input
(`BindingSpec` literals with "correspondence to one route record /
call-site occurrence" methods in the profile builders). Second, the
"concerns" reading is stable in normative text but the "governs"
vernacular leaks at the edges (Construction contract §8: "MUST NOT be read
as governing every relation inside that subject"; Core's golden `governs`
relation, §11 below), inviting a normative misread the contract never
licenses.

## 5. Existing proposal semantics

From `records.py`, `investigate.py`, the Investigation contract §8, and the
two semantic-proposal tests:

- **What is proposed:** anything expressible in a free-form payload. The
  demonstrated mechanical payload is `{field, value}`; the demonstrated
  semantic payloads are `{proposition, route_id}` and `{relation,
  proposition, software_subject}`. No accepted payload vocabulary exists
  for new binding, correction, withdrawal, refinement, or resolution — the
  envelope is syntactically generic and semantically uninterpreted.
- **Provenance retained:** proposal/case/question IDs, epistemic class,
  basis dict, method dict, reason string. No support in the warrant sense,
  no truth value, no requested-transition field, no addressee.
- **"Semantic" class means:** the claim would be an interpretive rather
  than mechanical assertion. It carries no rule, no threshold, and no
  producer (zero production uses).
- **Consumer:** none in production. Disposition exists only as test-local
  dicts (`REJECTED` in the write-semantics test; proposed/refused in the
  reconsideration test).

The envelope must therefore be read as a labeled suggestion slip with
lineage, not as a claim awaiting a verdict. Treating it as "a binding
candidate with standing" would over-read it by exactly the missing rule
this review investigates.

## 6. First-binding circularity

Yes, circular *if* `APPLIES` gates first binding — but the evidence
suggests `APPLIES` is simply the wrong gate, not that establishment is
impossible. Both evaluators define `APPLIES` as confirmation of an
established binding plus kind match; the reconsideration probe proves the
consequence (unbound Case → `UNKNOWN` → proposal). Three dissolutions are
consistent with the evidence, in increasing order of machinery:

1. **The binding was never supposed to be verdict-derived.** In both
   acceptance profiles, bindings enter as constructor input with a recorded
   method and grounding, and validation checks only their form. A first
   binding for A1 established the same way — constructor input with bridge
   evidence plus an explicit endpoint rule in its basis — follows the
   existing pattern exactly. Nothing in the contracts forbids it.
2. **A different verdict could license it.** A future evaluator rule could
   conclude something like "endpoint licensed" from bridge + source
   evidence without presupposing the row. No such rule exists; both current
   evaluators would need profile-level (not generic) changes.
3. **An adoption event could license it.** A human/organizational decision
   could stand behind the row. No such event shape is demonstrated for
   bindings (see §8 on EV-09).

The circularity is therefore an artifact of asking Judgment to do
establishment's job. Judgment confirms established bindings; it does not
mint them, in either profile, by accepted contract.

## 7. Descriptive vs semantic vs normative claims

The current ontology separates three of the four levels cleanly:

- **Descriptive** (`config_route` path facts, spine rows): MECHANICAL
  origin, producer-owned positive rules. "This route has path X."
- **Semantic** (proposition/binding/candidate/question): SEMANTIC origin,
  constructor-owned methods, application validation of form. "This
  proposition concerns this subject."
- **Case-local conclusions** (applicability, findings, conformance):
  Judgment artifacts outside the World. "For this case, APPLIES and the
  path is P."
- **Normative/adopted** ("this proposition governs / is in force for this
  subject"; "we accept / except / reject this governance"): **no relation,
  no origin, no artifact, no test.** Entirely absent.

Ambiguity audit: the descriptive/semantic split is well-defended (origin
preservation is validated; deterministic interpretation stays SEMANTIC per
Construction contract §11). The semantic/normative boundary is defended
only by the *absence* of normative machinery plus the "concerns, not
commands" reading of §7 — there is no positive marker on a binding row
that says "descriptive correspondence, not adoption." That is a
misreading hazard, not yet a demonstrated confusion: no test or contract
reads a binding as in-force. No new relations are proposed here; the
finding is that normativity currently has no address in the system, so any
future adoption design starts from a clean absence rather than a
contradiction.

## 8. Epistemic establishment vs organizational adoption

The catalogue forces this split apart harder than any other distinction in
this review:

- PR-08: human approval of a promoted finding is "an admission decision"
  that changes "the proposal's standing" and is "still not, by itself, a
  publication." Standing ≠ publication.
- CR-04: withdrawal removes standing "whether or not C was wrong" — "not
  the same as proving C false." Standing ≠ truth.
- AM-04/AM-05: for decision-caused resolutions, "the decision is the
  support, not a discovered fact" and "a decision is not reusable as a
  mechanical fact." Decision-support ≠ evidence-support.
- EV-09: a sourceless claim, if admitted, lands in a World "whose grounding
  is the decision record," with standing in its provenance — and pointedly
  "Not a forged source observation."
- Catalogue §M: actor type is provenance; "Standing can differ by actor"
  without changing claim shape.

Applied pressure answers:

- Well-supported but unadopted: representable today only as *unconstructed*
  (proposal sidecar, candidate rows) — the state "established knowledge
  that the organization has not adopted" has no demonstrated address,
  because nothing is yet adopted anywhere.
- Adopted but epistemically weak: not representable today; the honest
  catalogue shape would be an EV-09-style decision-grounded record, which
  no construction path demonstrates (all fixture bindings ground in source
  text; the kernel would permit a method-only semantic assertion per
  `contract.py`, but no profile does this and no decision-record evidence
  adapter exists).
- Human approval as evidence: for "the human approved X" — yes (EV-09,
  PR-08 provenance). For "X is semantically true" — no (AM-04, CR-04).
- `governance_binding` today: descriptive-correspondence knowledge
  ("established concern"), per §4. It represents neither adoption nor
  truth-verdict.

## 9. Human approval pressure cases

- **A. Approval of a well-supported proposal** adds standing/disposition
  (PR-08), not support. The semantic evidence already licensed the claim
  to whoever finds that evidence class sufficient; the approval licenses
  *organizational reliance*, a different transition with no current
  address.
- **B. Approval of a weakly supported proposal** cannot make the semantic
  claim publishable-as-true under any demonstrated rule: validation checks
  grounding presence, not adequacy, and no contract equates approval with
  evidence. The honest outputs are a decision-grounded record (EV-09
  shape, undemonstrated) or a declined proposal. Publishing the weak claim
  with source-shaped grounding would be exactly EV-09's "forged source
  observation" direct-mutation warning.
- **C. Rejection of a well-supported proposal** says nothing about truth:
  demonstrated by `test_rejected_proposal_is_not_negative_world_knowledge`
  (rejection is a test-local dict; W0 unchanged; alignment intact) and
  CR-04 (withdrawal ≠ falsity).
- **D. Approving an exception rather than a binding** is a different kind
  of decision with no evidence shape anywhere in the repo: no exception
  relation, envelope class, or test. It cannot be evaluated against the
  binding-establishment question until such a shape exists; treating it as
  "negative admission" would conflate disposition with truth (cf. case C).

## 10. Agent pressure cases

The catalogue decides these in advance (§M): actor type is provenance, and
"No actor-specific primitive is justified." Concretely: an agent can
establish a semantic claim *mechanically* only through the same paths a
human uses — constructor input with recorded method and grounding — and
the result is judged by its basis, not its author (AG-03 publishes "only
if later admitted," same as a human proposal). An agent cannot forge
producer output (AG-04 vs MO: "Collapsing them forges producer output")
or convert a decision into a measurement (AM-05). Whether an agent may
*adopt* governance is standing, which "can differ by actor" — and standing
is application policy per AGENTS.md ("Applications own ... authority ...
policies"), not OA semantics. No epistemic-kind difference between human
and agent approval exists in the evidence; any difference is standing
policy this review does not design.

## 11. Application-policy / deterministic derivation cases

Core's golden construction is the decisive control:
`profiles/core_v1/construction.py:130-134` establishes the semantic
cross-source relation `governs(requirement, program, provider)` — with
method "Cross-source interpretation: requirement applies to configured
production entrypoint and provider" — directly in the constructor, with no
proposal, no approval, and no admission decision beyond the mechanical
gates. A rule of the form "if R and Q then binding(P, S)" would likewise
be **construction semantics**: a constructor decision recorded with method
and grounding, checked for form by validation, and attributable to the
profile that owns the rule. It is not admission (no separate transition),
not derivation (it interprets; derivations recompute declared inputs, cf.
`governed_call`), not organizational adoption (no standing event), and not
a Decision in any demonstrated sense. This falsifies "every semantic claim
needs an admission decision": the golden path mints semantic relations by
construction rule alone. Admission-like machinery is relevant, if at all,
only where the constructor genuinely cannot decide — which the current
contracts already handle by emitting candidates + questions instead of
bindings (Construction contract §10).

## 12. Authoritative-source control

The phrase "authoritative evidence" exists in exactly one production
string — the fixed construction method "governance proposition from
authoritative evidence" (`construction.py:151`) — with no accompanying
mechanics: no source registry, no standing check, no authority verification
anywhere on the path. So "authoritative" today is an assertion about the
fixture author's intent, not a system property.

The control still discriminates two modes. If a source explicitly declares
"policy P governs endpoint S" and the producer faithfully reconstructs it,
the remaining establishment work is *endpoint resolution* (which
SoftwareSubject is S?), which is semantic construction regardless of how
explicit the source is — the source cannot name a snapshot-local subject
ID. The `SOURCE_EXPLICIT` support class in fixtures gestures at this mode
but no contract defines what source-explicitness licenses. An
agent-inferred "P governs S" differs only in its support/basis honesty
(inference method + heterogeneous evidence vs. explicit declaration), not
in needing a different gate: both enter through constructor input +
validation. Multiple construction *modes* (source-explicit vs. inferred)
are therefore plausible profile-level distinctions; neither implies a
central admission concept.

## 13. Durable-evolution catalogue evidence

Transition inventory (catalogue as evidence, not architecture):

| Transition | Licensing event (per catalogue) | Kind | Admission rule defined? |
| --- | --- | --- | --- |
| PROPOSES (EV-09, PR-02, PR-07, AG-03) | Investigation/agent/person states a claim | Epistemic act (or decision act for EV-09) | N/A — proposal is pre-admission by definition |
| ADMITS (PR-08 only) | Human approval | Organizational/standing | **No** — PR-07: "admission criteria. Not designed." PR-08 defines the *shape* (standing change, approval provenance) without criteria |
| ADDS (EV-01, SE-01, SE-03, MO-06) | Construction with evidence | Epistemic/mechanical | Via construction path, not a separate rule |
| REFINES (MO-05, CR-03, CV-05) | Finer-grained reading | Epistemic | No separate rule |
| RESOLVES (SE-04, MO-08, AM-01–08) | New evidence/observation/decision/method | Mixed; cause in provenance | Notably: SE-04 resolves **in a later construction** — establishment by construction, supporting §11 |
| SUPERSEDES (SE-07, CR-02) | Later state/rule replaces for current use | Currency, not truth | Open: "what holds the 'current' relation" (CR-02); "what 'current' means" (SE-07) |
| CORRECTS (SE-06, CR-01, AG-06) | Fault established against original inputs | Epistemic | No separate rule |
| WITHDRAWS (CR-04) | System stops standing behind C | Standing | Truth-value explicitly not required |
| LOSES_SUPPORT (CR-05/SU-03) | Supporting basis fails | Epistemic | Mechanical (dependency check) |

Net: the catalogue is a vocabulary of *stage separation* (proposal /
admission / publication / standing / support are different events, §L),
not an admission design. Its single ADMITS scenario makes approval a
standing change with explicitly undesigned criteria.

## 14. Cross-domain OA evidence

The basil/shade-cloth experiment (`docs/OA_CROSS_DOMAIN_WORKING_SET_EXPERIMENT.md`)
is the strongest existence proof against mandatory generic admission: a
non-governance OA application constructs `SEMANTIC`-origin assertions
directly, publishes unresolved alternatives as ordinary relations, and
treats "source evidence observed; no published assertion exists" as an
honest terminal state — "no proposal object is needed for this task," and
H2 (durable discovery needed) was rejected for that workflow. The
comparison table records "Source-only observation ↔ Investigation
proposal: Insufficient evidence for a shared proposal lifecycle." So:
knowledge construction generally requires no proposal/adoption stage;
whatever "admission" means for governance bindings is governance-specific,
not OA-generic. This bounds any future design to the application layer,
consistent with AGENTS.md ownership.

## 15. Hidden existing admission semantics

Distributed establishment semantics the repo already has, none of them
central and none deciding truth or adoption:

1. **Constructor-supplied correspondences.** Both acceptance profiles pass
   human-authored `BindingSpec`/`CandidateSpec` literals into
   `construct_software_governance`. The de facto "who decides a binding
   exists" is *whoever invokes the constructor with what input* — today,
   fixture authors. This is the implicit establishment authority of the
   whole system, and it is currently undocumented as such.
2. **Fixed vocabulary strings as intent markers.** "Authoritative evidence"
   (proposition method), `SOURCE_EXPLICIT`/`DETERMINISTIC` (support classes),
   `supplied_correspondences_only` (completeness gap): all assert
   provenance shape without verification mechanics.
3. **Kernel vocabulary authorization.** The `semantic_relations` allow-list
   and semantic-reference authorization in `admit_assertion` authorize
   *which relations may carry semantic claims*, never which claims.
4. **Producer positive rules.** "Emit only when endpoints established"
   (Construction contract §4) is admission-shaped (a pre-publication
   eligibility rule) but producer-local and mechanical.
5. **Judgment APPLIES as confirmation.** Both evaluators confirm
   established bindings; neither mints them. Reading APPLIES as
   establishment-license is the first-binding error (§6).
6. **Historical obligation/admission machinery** (`ontology_author/semantic_binding/admission.py`,
   `authority/`, `governance/`): a prior design where "a constructor cannot
   supply the admission outcome." Explicitly superseded for the current
   path — acceptance tests forbid those imports
   (`tests/test_software_governance_construction.py:66-68`) — and the
   Construction contract demotes historical contracts to evidence. It must
   not be mistaken for live semantics, but it shows the repo already tried
   centralized admission and moved away from it.

## 16. Alternative architectural hypotheses A–F

- **A. Admission is a real shared responsibility** (candidate claim →
  admission rule → eligible Construction input). Would require the same
  transition across several semantic proposal types with one rule-owner.
- **B. Admission is application-specific construction policy.** Each
  profile defines what evidence licenses its semantic claims; the
  "transition" is the constructor's recorded decision plus mechanical
  validation.
- **C. "Admission" conflates epistemic establishment and organizational
  adoption.** Two transitions: licensed-as-knowledge vs. chosen-as-operative.
- **D. Proposal disposition is the real missing responsibility**
  (accepted / rejected / deferred), with Construction separately
  determining publishability.
- **E. `governance_binding` mixes concepts.** The problem is relation
  meaning, not machinery.
- **F. No new responsibility is needed.** Existing Construction + proposal
  + application policy suffice once stated clearly.

## 17. Counterexamples against each

- **Against A:** core_v1 mints `governs` with no admission transition
  (§11); cross-domain app needs no proposal lifecycle (§14); no two
  current semantic claim types share an establishment rule beyond
  mechanical gates (§3). A shared rule has no demonstrated consumers.
- **Against B:** the first-binding case strains it — "the constructor was
  given it" is a complete mechanism but an unsatisfying license story
  when the giver is an unverified agent rather than a fixture author.
  B survives only with explicit per-profile establishment rules, which do
  not yet exist for any profile. Also, B alone cannot represent
  "established but not adopted" (§8).
- **Against C:** the split is well-evidenced (PR-08, CR-04, AM-04/05,
  EV-09), but *neither half has a demonstrated need for new machinery*:
  establishment already happens in constructors, and adoption has no
  demonstrated reader (no exception/standing/enforcement need is
  exhibited anywhere). C risks designing two systems for zero exhibited
  reads.
- **Against D:** proposals have no production consumer (§2.3) and no
  cross-session persistence need is exhibited; disposition state with no
  reader is dead metadata. D becomes live the moment a durable proposal
  queue with competing dispositions is required — not before.
- **Against E:** the contract's "concerns/correspondence" reading is
  actually coherent and consistently tested; E overclaims if it says the
  relation is meaningless. E's valid core: the *decider* of the row is
  unspecified, and the normative misread is unguarded (§4).
- **Against F:** F holds for establishment-today (fixture authors +
  mechanical gates demonstrably suffice to publish) but cannot cover
  cross-session proposal tracking or standing changes (withdrawal,
  adoption) if those are ever required. F is the right default until such
  a read is exhibited.

No hypothesis survives unmodified. The evidence favors **B for
establishment + E's valid core (specify the decider and the non-normative
reading) + C as a conceptual split to preserve without building either
half yet + D deferred until a proposal consumer exists**. A is
contradicted as a shared layer; F is the correct posture toward new
machinery.

## 18. Required distinction table

| Concept / event | Establishes | Licensing evidence | Rule owner | Changes World knowledge? | Changes organizational standing? | Changes external state? | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kernel admission (G1/G2) | Provenance/grounding/vocabulary presence | Mechanical properties of the candidate | Frozen Core contract | No (gate only) | No | No | Existing |
| Construction validation (G3) | Representational validity | Schema/origin/receipt/grounding presence | Application contract v0 | No (gate only) | No | No | Existing |
| Semantic establishment | A claim row exists with recorded method + basis | Whatever the constructor's rule required (today: fixture authorship) | Profile/constructor (implicit; unstated) | Yes, at publication | No | No | Existing mechanism, unstated rule |
| Proposal | A suggestion exists with lineage, explicitly not an assertion | Investigator's discovery + question | Investigation v0 (envelope only) | No | No | No | Existing |
| Proposal acceptance | *Undefined* — no demonstrated transition | None demonstrated | None | — | — | — | Hypothetical |
| Adoption | A claim becomes operative governance | Standing event (PR-08 shape) | None (non-goal) | No (standing ≠ publication) | Yes (by definition) | No | Hypothetical |
| Admission | Overloaded: (i) mechanical gates G1–G3; (ii) catalogue PR-08 standing change; (iii) colloquial "allowed in" | (i) mechanical; (ii) undesigned criteria; (iii) n/a | (i) Core/app contracts; (ii) none | (i) No; (ii) No | (ii) Yes | No | (i) Existing; (ii) hypothetical; term unstable — see below |
| Publication | Sealed revision at fresh address | Prior gates passing | Runtime | Yes | No | No | Existing |
| Judgment | Case-local conclusions (applicability/findings/conformance) | Cited sealed assertions + evaluator rule | Profile evaluator + Judgment v0 | No (artifact outside World) | No | No | Existing |
| Decision | Case-local resolution whose support is the decision (AM-04/05 shape) | Actor + standing (undemonstrated for governance) | None | Only if later constructed (EV-09) | Possibly (if standing attaches) | No | Hypothetical for governance |
| Exception | *No shape exists* | — | None | — | — | — | Hypothetical, unshaped |
| External execution | Changed external state + outcome record | Capability contract + preconditions | Capability (test-local) / application | No | No | Yes | Existing (experiments) |

Collapses under evidence: "admission" as a single term has no stable
meaning — G1–G3 mechanical admission and PR-08 standing-change admission
are different transitions sharing a word. "Proposal acceptance" has no
demonstrated content distinct from either a constructor's input choice
(establishment) or a standing event (adoption); it should not be treated
as a third thing without new evidence.

## 19. Repository evidence map

| Conclusion | File | Location | Test / behavior |
| --- | --- | --- | --- |
| Admission = mechanical support check, not truth/adequacy | `docs/CORE_PRODUCT_V1_COMPLETION_CONTRACT.md` | §6.2 | Core acceptance suite (frozen contract) |
| Kernel admits per-assertion on provenance/scope/grounding | `ontology_author/world/core/contract.py` | `admit_assertion`, L345–415 | `test_world_store.py`, core acceptance |
| Commit re-validates all BASE + references pre-seal | `ontology_author/world/runtime/commit.py`, `world.py` | `validate_contract_admission` L41; `admission_errors` L308 | Core acceptance (invalid publication fails safely) |
| App admission = shape/support/scope/grounding; not adjudication | `docs/SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md` | §11 | `test_software_governance_construction.py` |
| Validation is representational only | `ontology_author/software_governance/validation.py` | module docstring; L43–85 | Construction acceptance (shape/origin/basis/gap rejections) |
| Binding = established concern, grounded by correspondence basis | Construction contract | §7 | Config/mail acceptance (navigation reads) |
| Decision/adoption explicitly non-goal | Construction contract | §14 | — (absence; no contrary test) |
| Bindings enter as human-authored constructor input | `profiles/software_governance_config_v0/build.py`, `profiles/software_governance_v0/build.py` | `BindingSpec` literals, "correspondence to…" methods | Profile acceptance suites |
| Historical admission packages excluded from current path | `tests/test_software_governance_construction.py` | L66–68 (import forbids) | Architecture boundary test |
| APPLIES presupposes established binding (both profiles) | `profiles/.../judge.py` (config L60–62; mail L61–62) | `_applies` "established binding joins…" | `test_software_governance_judgment.py` |
| Unbound Case → UNKNOWN → semantic proposal, nothing published | `tests/test_software_governance_change_reconsideration_experiment.py` | `test_proposal_expresses_candidate_binding_without_publication`, L881+ | Probe (19 tests) + report §20 |
| Proposal envelope enforces class vocabulary + no assertion_id only | `ontology_author/software_governance/investigation/records.py` | `make_proposal`, L56–80 | `test_software_governance_investigation.py` |
| Only production proposals are mechanical; zero proposal consumers | `profiles/software_governance_config_v0/investigate.py`; repo grep | L117–135; no readers outside `investigation/` | Investigation acceptance ("does not import" boundaries) |
| Rejection is not negative knowledge; W0 untouched | `tests/test_software_governance_write_semantics_experiment.py` | `test_rejected_proposal_is_not_negative_world_knowledge` | Write-semantics probe |
| Approval changes standing, not publication; criteria undesigned | `docs/DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md` | PR-07/PR-08; §L stage list | Catalogue (evidence, not architecture) |
| Decision-support ≠ evidence-support; withdrawal ≠ falsity | Evolution catalogue | AM-04/05, EV-09, CR-04, §M | Catalogue (evidence) |
| Semantic `governs` minted by constructor rule, no admission stage | `profiles/core_v1/construction.py` | L130–134 | Core acceptance (golden scenario) |
| Non-governance app needs no proposal/admission lifecycle | `docs/OA_CROSS_DOMAIN_WORKING_SET_EXPERIMENT.md` | H2 rejected; comparison table | 4 cross-domain tests |
| Applications own authority/policy/operations; lean-kernel rule | `AGENTS.md`; Completion contract §13 | Ownership + "reusable mechanics above kernel" | Repo policy (not executable) |

No prose/executable contradictions were found; where prose is aspirational
(catalogue criteria, "authoritative evidence"), the code is silent and this
review sides with the code.

## 20. Optional external comparison

One narrow check, kept separate from repository evidence. DMN (per the OMG
spec literature) models *business knowledge models* — background knowledge
drawn upon when making decisions — as distinct elements from *decisions*,
which evaluate inputs to outputs; decision logic evaluation is likewise
separated from the business processes that consume its results. That is
external corroboration, and only corroboration, for the
establishment-vs-decision split in §8: mature decision tooling also refuses
to treat "the knowledge is established" and "the decision went this way"
as one transition. No architecture is imported: DMN's decision tables,
hit policies, and DRGs answer different questions than binding
establishment, and Palantir/GRC comparisons were deliberately not pursued
beyond this single targeted lookup.

## 21. Independent second opinion

The prompt's framing — "the missing rule is admission" — is, in my
assessment, about one-third right, and the wrong third to build first.

**What I think is actually going on.** The system already has a complete,
demonstrated establishment pipeline for semantic claims: a constructor
decides a row with a recorded method and grounding, mechanical gates check
form, and publication seals it. That is how every binding in every
acceptance fixture came to exist, and how Core's golden `governs`
relation came to exist. The "missing admission rule" for `binding(P, A1)`
is therefore not a missing *layer* — it is a missing *sentence*: no
profile has yet stated what evidence licenses its constructor to emit a
binding row for a new subject. The reconsideration experiment supplied all
the ingredients of such a sentence (bridge provenance + source evidence +
explicit endpoint rule) and then stopped one step early by asking
Judgment — a confirmation procedure — to do the minting. Of course that
looks circular: it is the wrong tool for the step, not a deep paradox.

**Framing correction.** Stop saying "admission" for three different
things. The contracts already own the word for mechanical validation
(G1–G3); the catalogue owns a second use for standing change (PR-08);
colloquial "allowed in" owns nothing. My recommendation: keep
*admission* = mechanical gates (existing, frozen-adjacent meaning);
*say establishment* for the constructor's licensing decision (exists as
mechanism, needs stated per-profile rules); say *adoption/disposition*
for standing changes (no demonstrated need; do not build). The
first-binding "problem" then dissolves into a profile-authoring task:
write the establishment rule for carried bindings, record it as the
construction method, and let the existing gates check its form.

**Genuinely distinct concepts:** mechanical admission, semantic
establishment, proposal (suggestion slip), standing/adoption, publication,
case-local verdict. **Accidental duplicates:** "proposal acceptance" (no
content beyond establishment-input-choice or standing-event);
"authoritative" as used in fixture strings (no mechanics);
"current" as a knowledge property (SE-07/CR-02 leave it open; only
"published at address A" and "live source is R" are demonstrated).

**What I would NOT design yet:** any shared Admission subsystem, any
Decision/Adoption subsystem, any proposal queue/disposition lifecycle, any
exception shape, any Core primitive. None has a demonstrated reader.

**Smallest next falsifiable question:** see §23.

## 22. Confidence / uncertainty

| Conclusion | Rating | What would change it |
| --- | --- | --- |
| Mechanical gates (G1–G6) establish form/grounding only, never truth/adoption | ESTABLISHED BY EXECUTABLE EVIDENCE | A gate that inspects semantic adequacy or standing (none exists) |
| `governance_binding` = established concern, not adoption/in-force | STRONGLY SUGGESTED | Contract text is consistent but never states the negative explicitly; an explicit "bindings are not adoption" sentence would promote this |
| Who decides a binding exists is unspecified (today: fixture authors) | ESTABLISHED BY EXECUTABLE EVIDENCE | A profile stating its establishment rule |
| Proposals are write-only sidecars with no consumer | ESTABLISHED BY EXECUTABLE EVIDENCE | Any production reader of a proposal record |
| First-binding circularity is an artifact of misassigned responsibility | STRONGLY SUGGESTED | A demonstrated need for verdict-before-row that constructor input cannot satisfy |
| Establishment needs no shared layer (Hypothesis B) | STRONGLY SUGGESTED | Two profiles requiring one shared establishment rule they cannot each own |
| Adoption/standing is real-but-unneeded (no demonstrated reader) | PLAUSIBLE | Any required read about in-force/excepted/withdrawn governance |
| Epistemic-vs-adoption split (Hypothesis C) | STRONGLY SUGGESTED | Catalogue + contract non-goals converge; executable adoption evidence would be needed to go further |
| "Admission" is terminologically unstable | ESTABLISHED BY EXECUTABLE EVIDENCE | Nothing — three live uses documented |
| No Core primitive missing | STRONGLY SUGGESTED | A failing case unrepresentable in referents/relations/grounding/derivations/revision/completeness (none presented) |
| Agent/human approval differ only in standing, not epistemic kind | PLAUSIBLE | Catalogue §M asserts it; no executable agent-standing case exists either way |
| Normative misread of bindings is a hazard, not an observed confusion | UNDER-SPECIFIED | Any test or product read treating a binding as in-force |

## 23. Smallest next falsifiable question

Can a second, independent constructor establish `binding(P, A1)` from
stated inputs — bridge provenance + current source evidence + an explicit
endpoint rule recorded as its construction method — such that mechanical
validation passes, Judgment confirms, and no human intervenes? If yes,
establishment is fully expressible as application construction policy and
no admission/decision layer is needed for it. If the resulting row cannot
honestly carry its basis (e.g., validation rejects the basis shape, or no
support class fits bridge-licensed correspondence), the failure names the
exact missing representation — which is the only evidence that should
motivate new machinery.

## 24. Recommendation on what NOT to design yet

Do not design, specify, or scaffold: a shared Admission subsystem; a
Decision/Adoption model or workflow; authorization/standing enforcement;
a proposal queue, disposition lifecycle, or proposal persistence; an
exception/waiver shape; a "current governance" pointer or relation; a
semantic-proposal payload vocabulary beyond the two test-local uses; or
any OA Core primitive. The one textual change worth making is also the
cheapest: state in the Construction contract (or its companion) that a
binding row is established concern rather than adoption, and that each
profile owns its establishment rule. Everything else should wait for the
experiment in §23 or for a demonstrated reader of standing/disposition.

## Explicit answers

1. **What does the current system mean by `governance_binding(P,S)`?**
   An established concern/correspondence between source-derived knowledge
   P and subject S, grounded by the correspondence basis (§4).
2. **Is that meaning fully specified?** No: the decider of the row is
   unspecified, and the non-normative reading, while consistent, is never
   stated positively.
3. **What does current Construction already validate before publication?**
   Six gates (§3): kernel per-assertion and whole-candidate mechanical
   admission, application representational validation, publication
   mechanics, producer positive rules, plus read-side citation checks.
4. **Which of those checks are epistemic versus merely mechanical?** All
   write-path checks are structural/mechanical/evidentiary-presence. None
   assesses semantic adequacy, truth, acceptability, or authority.
5. **What does an Investigation semantic proposal establish?** Almost
   nothing: a typed, provenance-bearing suggestion explicitly not an
   assertion, with no consumer and no accepted payload vocabulary (§5).
6. **What does proposal acceptance need to establish that proposal
   creation does not?** Under current evidence, the question is malformed:
   "acceptance" has no demonstrated content beyond becoming constructor
   input (establishment) or gaining standing (adoption) — two different
   things (§18).
7. **Is first-binding admission circular if based on current `APPLIES`
   semantics?** Yes, and instructively so: `APPLIES` confirms established
   bindings; using it to mint the first row is a category error, not a
   deep paradox (§6).
8. **Can a binding be mechanically established without organizational
   adoption?** Yes — every binding in every acceptance fixture is exactly
   that, since adoption exists nowhere in the system.
9. **Can governance be organizationally adopted without the semantic claim
   being epistemically established?** Not representably today; the honest
   catalogue shape (EV-09 decision-grounded record) is undemonstrated, and
   no adoption record exists at all (§8).
10. **Should those states be representable separately?** The catalogue
    says yes in principle (PR-08, CR-04); no exhibited read yet forces
    building either representation.
11. **Does human approval supply evidence about semantic truth,
    organizational standing, or both?** Standing only (PR-08, AM-04);
    treating it as truth-evidence is contradicted (CR-04, AM-05).
12. **Does agent approval differ in epistemic kind?** No: actor type is
    provenance (catalogue §M); only standing may differ, as application
    policy.
13. **Does application policy count as admission, construction,
    derivation, or decision?** Construction: a constructor's recorded rule
    (Core golden `governs` is the control, §11). Not admission, not
    derivation, not a demonstrated Decision.
14. **Is "admission" one coherent responsibility?** No. Three live uses —
    mechanical gates, catalogue standing-change, colloquial allowed-in —
    share a word and little else (§18).
15. **Or does it currently conflate semantic establishment, adoption, and
    publication eligibility?** The *word* conflates them across documents;
    the *machinery* does not — gates, establishment acts, and publication
    are already separate code paths with separate owners.
16. **Is a generic Admission subsystem justified?** No. No shared
    transition beyond mechanical gates has a demonstrated consumer (§17,
    against A).
17. **Is a generic Decision/Adoption subsystem justified?** No. The split
    is conceptually sound but has no exhibited reader (§17, against C).
18. **Does anything suggest an OA Core primitive is missing?** No. No
    failing case outside existing primitives was found or presented.
19. **What existing concepts should remain unchanged?** Kernel admission,
    application validation, the binding/candidate/question split, origin
    preservation, proposal-as-sidecar, Judgment-as-confirmation, and the
    historical packages' quarantined status.
20. **What terminology should we avoid until better evidence exists?**
    "Admission" for anything but mechanical gates; "approval/accept" as
    truth-verbs; "authoritative" without mechanics; "current" as a
    knowledge property; "proposal acceptance" as a third transition.
21. **What is your independent second opinion on the architecture?** §21:
    the missing item is a stated per-profile establishment rule, not an
    admission layer; keep establishment/adoption/publication triply
    separate; build nothing until §23's experiment or a standing reader
    appears.
22. **What single next experiment would most reduce uncertainty?** §23:
    establish `binding(P,A1)` in a second constructor from stated
    bridge-plus-evidence inputs with no human, and see whether the basis
    is honestly representable.

## Working-tree note

This pass adds only this report. It creates no code, test, contract, or
design artifact; it does not commit or push. Other uncommitted repository
changes predate this pass and were left in place.

# Target Architecture v0 — Phase 3 construction boundary

## A. Implementation and starting point

PR [#2](https://github.com/keremnv/design/pull/2) was marked ready for review and
squash-merged at the user's request. Phase 3 starts from merged `main` commit
`a927d3a051eccceacf5c9352d4ec55e2f262aadb`. Its
[main CI run](https://github.com/keremnv/design/actions/runs/37511481487) passed.
Work was performed in a separate worktree, preserving the unrelated frontend
and bundled-asset edits in the original checkout. Phase 3 is submitted as a
draft for adversarial review; it is not authorized for automatic merge.

The demonstrated failures were narrow:

1. Authority construction refused a World without exactly one program
   snapshot, even when a claim had only semantic endpoints.
2. A flat collection of observations could not distinguish two independent
   support paths from one joint path with two members.
3. Source declarations, program context, and construction receipts did not
   explicitly identify the admitted construction basis or exact copied
   publication separately from claim support.

The implementation composes the existing authority writer, evidence retention,
World grounding envelopes, receipts, admission and `publish_candidate`.
It adds two small immutable records in `ontology_author/construction_boundary.py`,
and a source-only `construct_config_requirements` entrypoint. The kernel,
Program Spine and Phase 2 publication implementation are unchanged.

## B. Construction-path audit

These paths have different application contracts. A common mandatory runtime
`ConstructionContract` object would duplicate their existing executable
policies without making the tested workflows more honest. The authority seam
instead records a local `authority-construction-boundary/v1` declaration:
input scope, target schema and named mechanical admission requirements.
Actual source scope/configuration is in the basis, and actual typed shapes
are discoverable in the candidate World. It contains no search, model, prompt,
ordering or investigation policy.

| Constructor | Declared input scope / actual basis | Semantic support | Method/version | Candidate / admission / publication | Phase 3 changes |
| --- | --- | --- | --- | --- | --- |
| `authority/lifecycle.py`, `AuthorityConstructor` | Declared Markdown universe and optional baseline; basis records the actual document observations, source standing/driver/configuration, exact publication inputs, optional qualified snapshot and copied baseline | Existing source groundings, authority claim/endpoint records and attachment warrants; claim envelopes now explicitly group support | Existing receipt constructor ID/version, now writer `v1`; individual grounding method/rule and constructor version | Fresh mutable candidate or writable baseline copy; authority standing, identity, completeness, support and reconstruction checks plus kernel admission; unchanged `publish_candidate` at a fresh retained address | Optional program plane, explicit basis/contract, grouping, retained verification; scratch exploration omitted from new receipts |
| `software_governance/construction.py` | Software World plus explicit proposition/binding/candidate/subject/manifestation/completeness specs and retained blobs | `_world_groundings` plus `relation_support`, endpoint resolution, software evidence and establishment rule | Contract/profile IDs and supplied versioned rules/methods | Writable copied software candidate; `validate_governance_world` and retained program checks; seals staging and installs exclusively | Preserved: its software assumptions are appropriate for its binding application, not made universal |
| Existing `config_routes/construct.py` | Supplied revision-qualified software JSON and Markdown pair; parsed route inventory, governance observations, evidence blobs and scoped coverage | Proposition observations; binding/candidate source and software observations with rule/resolution records | `config.routes/v1` grammar and separately versioned proposition/binding/candidate/question/evaluator rules | Producer candidate followed by governance candidate; profile schema, resolution, inventory and provider closure checks; fresh sealed output | Preserved the existing coupled slice and its explicit unsupported/missing/ambiguous outcomes |
| New `config_routes/semantic.py` | Declared Markdown only; exact retained document observation and authority configuration | Requirement paragraph support; unsupported paragraphs retain evidence in ordinary authority unresolved records | `config.routes.requirements/v1` plus each existing grammar establishment rule | Fresh authority candidate; existing grammar, authority and boundary admission; `publish_candidate` returns `PublicationRef` | Source-only foundation for Phase 4; `config_requirement` represents requested route content without a software referent |
| `semantic_binding/construction.py` | `ConstructionObligation`, bounded catalog of legal authority/semantic/program/mechanical/dependency/completeness entries; catalog constrains available references | Candidate-selected `evidence_refs` and support/resolution fields; catalog availability alone does not add references | Catalog/schema/instruction versions and hashes, constructor method/metadata and invocation result records | Pre-World `SemanticCandidate`; deterministic alias, role signature, reference and schema compilation; no publication at this stage | Preserved; no universal replacement of candidate/catalog/warrant structures |
| `semantic_binding/admission.py` | Exact baseline plus admitted obligation/candidate/catalog/snapshot; materializer copies the baseline and records selected support/warrant | `_candidate_grounding`, `SemanticCommitmentWarrant.evidence_refs`, resolution and maintenance dependencies | Admission profile/version and candidate construction method; obligation definition remains distinct | Deterministic admission decision is recomputed; legal grounding and required evidence classes, resolved roles, completeness where required; mutable staging, kernel/provider checks, exclusive fresh sealed publication | Preserved; semantic-program claims still require both authority and program grounding |
| Membership persistence in `semantic_binding/membership.py` | Membership obligation and selected candidate/catalog material; material interpretation basis canonicalizes class/program content, structural facts, dependencies and profile | Selected evidence and commitment warrant; `semantic_class_membership_basis` is a material reuse receipt | `class_membership_interpretation_basis/v0` and membership profile/version | Writes candidate through the admitted-candidate/materializer path; basis comparison controls reuse, not publication currentness | Preserved: this support/maintenance basis is not the new constructor-availability basis; content-equivalence digest does not replace exact publication identity |
| Invariant/rule persistence in `semantic_binding/admission.py` and checkout profile | Supported invariant obligation shape, adopted versioned rules/authority bindings, enumerated scoped program inputs | Selected authority/program evidence, maintenance warrant and scoped completeness references; adopted law provenance is application-owned | Invariant admission profile, rule IDs/revisions and profile method | Trusted mapping to `semantic_payment_provider_access_invariant`; universal scope requires declared COMPLETE enumeration; persistence uses the same candidate/materializer seam | Preserved; unsupported target shapes fail rather than invent a nearby relation |
| `governance/construction_cycle.py` | Case, pending obligations, execution policy/authorization, bounded constructor inputs and baseline World | Delegates selected candidate support to semantic-binding admission; readiness/policy is not warrant | Existing execution and invocation records and versioned admission profiles | At most one construction; non-commitment outcomes stop; accepted commitment materializes at supplied fresh publication directory, then reads the revision | Preserved; no new cycle, investigation or working-set engine |
| Profile/reference builders (`profiles/core_v1`, checkout/account settings and runtime `Project`) | Profile-owned sources, declared authority/rules and constructor configuration; golden adapters retain exact bytes and expose known losses | Existing grounded typed assertions, construction origins, derivations, ordinary ambiguity relations and receipts | `world.construction-receipt.json` records entrypoint content digest and Contract identity; application profiles have their own rule identities | Construction into candidate; kernel/Contract admission; canonical fresh-root `Project` builds retain old and new revisions; legacy in-place rebuild remains compatibility only | Preserved the frozen reference and installed dependency boundary; no aesthetic migration |

The catalog, membership reuse receipt and authority construction basis answer
different questions. In particular, a membership basis digest intentionally
excludes snapshot/observation IDs for material comparison; it is not a generic
durable evidence identity. Phase 3 does not reinterpret legacy flat groundings
as either independent or joint support. The grouping reader returns only
explicitly recorded paths. Historical receipts remain loadable with absent
optional Phase 3 fields; the new verifier reports absent boundary metadata
rather than retrospectively certifying old publications.

## C. New durable concepts and why they are needed

**No new kernel primitive or kernel table was necessary.**

| Concept | Storage | Demonstrated need / why simpler existing storage was insufficient |
| --- | --- | --- |
| `ConstructionBasis` | New optional `construction_basis` field in the existing authority receipt, written inside the candidate before admission | A/H/F: inspected notes, an available program snapshot and an exact baseline must be visible without making them support or lifecycle claims. Existing claim groundings only describe support; source declarations alone omit exact publication dependency and copied-baseline distinction. The immutable record reuses `SourceObservation` and `PublicationRef`, not a new evidence ID. |
| Local construction-contract declaration | New optional `construction_contract` field in that same receipt | D/E: state the accepted input scope, target and mechanical requirements for this source-only boundary. A shared executable contract engine is unnecessary; existing typed schema and validation functions execute the checks. |
| `SupportPath` | `extra.support_paths[].members[]` in existing assertion construction groundings | B/C: the same flat source observations represent both examples. The nested member list is the minimum missing grouping; an empty path or disagreement with flat grounding is rejected. No separate SupportMember record/table or proof machinery is needed. |
| `config_requirement` | An ordinary typed relation in config application vocabulary | D: a requested route is semantic information before any route implementation. Existing software-governance construction requires a software baseline. Its binding vocabulary is preserved; the source-only vocabulary stores requirement identity, statement, domain relation and requested route text. |

Constructor method ID/version was already durable. The writer version is
advanced to `v1`; the source-only profile declares its own ID/version, and
claim envelopes also retain the constructor version. There is no global
method registry. Source revision, native snapshot qualification, publication
revision and constructor version remain separate fields. Existing derivation
definition identities are unchanged.

## D. Basis is not support

An authority constructor admits immutable document observations for every
declared source. The receipt basis identifies this availability. Claim
construction separately receives its observations and optional `SupportPath`s.
It never enumerates the basis to manufacture claim support.

`test_basis_is_not_support_and_retains_unused_evidence` records `policy.md`
and `notes.md` in basis, but the approval assertion's flat and grouped support
contains only `policy.md`. Both sources reconstruct from retained blobs after
the original workspace is deleted. The final publication's fingerprint stays
unchanged after all reads.

The copied baseline is separately named as `candidate_baseline`. Exact prior
publications may be supplied without copying them. Neither creates a support
edge, supersession relation or current-publication policy.

## E. Independent and joint support

The same underlying qualified observations can be recorded as:

```json
{"support_paths": [{"members": ["S1"]}, {"members": ["S2"]}]}
```

or:

```json
{"support_paths": [{"members": ["S1", "S2"]}]}
```

The strings above abbreviate full existing `SourceObservation` pointers.
Members inside one path are jointly required; separate paths are independently
sufficient **recorded warrants**. Admission checks shape, coverage and retained
reconstruction, not whether the interpretation of sufficiency is true.
The default for new authority claims is one joint path containing the supplied
observations. Callers explicitly request independent paths when intended.

`support_paths_for_assertion` reads this distinction from the supported World
warrant surface. It does not infer paths from ungrouped legacy source records.

## F. Production semantic-only path

```python
from ontology_author.config_routes import construct_config_requirements

result = construct_config_requirements("policy.md", "publications/W0")
assert result.succeeded, result.errors
publication = result.publication
```

For `Customer export must use the approved customer-export route.`, the path is:

```text
declared Markdown → MarkdownSource document/paragraph observations
→ AuthorityConstructor basis and fresh mutable candidate
→ config_requirement supported by the paragraph
→ deterministic grammar + authority/boundary/kernel/provider admission
→ publish_candidate at a fresh address → PublicationRef
```

The requirement refers to a semantic requirement identity and requested route
**text**. It has no program input, no program World, no program referent, no
program snapshot, no attachment warrant, no realization/binding assertion, no
software-absence question and no implementation status. The existing receipt
schema uses an empty snapshot string for absence; the basis has an empty
program-snapshot list. Neither is a fake realization.

`verify_authority_publication` reads the retained manifest and receipt, checks
the receipt digest, then verifies construction material/support closure and
kernel/provider checks. `PublicationRef` qualification is checked independently.
The manifest records `PASS` for the declared authority boundary only after
candidate admission succeeds; it describes mechanical admission, not truth.
The source-only conformance case deletes original sources and uses only the
retained bundle for assertion, support, basis and publication inspection.

## G. Representational gaps

The profile reuses the existing bounded grammar. For:

```text
Customer export must use the approved A route. Or perhaps B.
```

there is no licensed single requirement; construction fails and creates no
publication. No A/B endpoint or nearby relation is invented. A mixed source
with one valid requirement and one ambiguous paragraph publishes exactly the
valid requirement and an ordinary `authority_unresolved`/`UNBOUND_REGION`
record for the other paragraph. Its full evidence remains reconstructible;
no universal unresolved assertion status is added.

Existing authority admission still rejects certain claims with ambiguous
endpoint resolutions; existing binding compilation rejects unsupported
obligation/profile/role shapes. These behaviors are preserved.

## H. Program independence

The dependency direction remains semantic construction → qualified mechanical
program observations. Program Spine imports no semantic construction,
authority, semantic binding, software governance, config profile or application
profile package. The architecture test now checks that boundary and resolves
relative imports and `from ontology_author import ...` forms as well as direct
imports. The World/evidence restrictions include the new application module.

Case H constructs from a real retained TypeScript spine, records its exact
publication/native snapshot in basis, and publishes an approval assertion
supported only by Markdown. There is no program snapshot annotation on that
semantic claim, no attachment warrant, and no realization assertion. The
program publication stays retained outside the deleted source workspace;
provider-owned program blobs also survive in the new bundle.

## I. Conformance and verification

`tests/test_phase3_construction_boundary.py` is part of the default/CI gate:

| Test (prefix `test_` omitted) | Invariant |
| --- | --- |
| `basis_is_not_support_and_retains_unused_evidence` | A; basis/support separation, retained source reconstruction, no scratch persistence, unchanged history |
| `independent_and_joint_support_are_distinct` (two parameters) | B/C; two single-member paths versus one two-member path |
| `source_only_config_requirements_publish_before_software` | D; production source-only construction, inspectable support/basis, no program or software-absence inference |
| `representational_gap_rejects_without_fabrication` | E; refusal without partial publication |
| `mixed_gap_preserves_full_evidence_without_guessing` | E; ordinary unresolved record, retained full evidence, no guessed assertion |
| `prior_publication_is_exact_basis_without_lifecycle_claims` (two parameters) | F; exact W0 dependency, explicit copied baseline versus non-copy input, retained W0, no lifecycle assertion |
| `same_sources_distinct_method_versions_retain_both` | G; identical basis, independent retained addresses, distinct method versions |
| `program_basis_does_not_bind_semantic_assertion` | H; real program qualification in basis creates no semantic-program support/binding |
| `admission_rejects_mismatched_support_groups` | Invalid grouping cannot publish |
| `retained_verification_rejects_basis_corruption` | Basis/source declarations must agree |
| `prior_publication_wrong_revision_fails_closed` | Revision dimensions remain qualified |
| `publication_verification_detects_retained_receipt_tampering` | Retained method/basis receipt digest is checked |

`test_program_spine_does_not_depend_on_semantic_construction` separately checks
the allowed dependency direction. The existing authority receipt regression
now expects ephemeral exploration to be absent from newly written receipts.
Existing historical receipts and useful test fixtures remain intact.

Verification:

- Locked Python sync and `npm ci --prefix frontend`: succeeded.
- `uv run --extra dev pytest -q tests/test_core_v1_acceptance.py`: **18 passed**.
- `uv run --extra dev pytest`: **117 passed**, including **14 Phase 3 cases**.
- Phase 1 publication/governance/authority, Phase 2 retention, Phase 3 and
  architecture focused run: **36 passed** (before adding the receipt-tamper
  case; all 14 final Phase 3 cases also passed separately).
- Authority construction/maintenance, membership persistence, construction
  cycle, config-route phases 1–3, software governance and Phase 3: **226 passed**.
- Final Phase 3 and authority-retention check after recording the admission
  result: **15 passed**.
- Frontend build and package build: succeeded; bundled assets have no diff.
- `git diff --check`: passed.

Counts overlap; the default gate is not the entire historical suite. No live
model runs, releases or new experiment transcripts are part of this work.

## J. Scope exclusions

Phase 3 introduces no ProgramBackend, Glean integration, ProgramWitness,
currentness selection, supersession/withdrawal, publication registry,
investigation/search planner, question graph, working-set manager, private
reasoning/search/prompt transcripts, confidence scoring, relevance/conflict
engine or assertion lifecycle engine. No Program Spine redesign or SQL-first
code-exploration product is included. The full semantic→implementation→binding
→change→re-resolution sequence remains Phase 4.

## K. Demonstrated remaining debt

The unchanged `test_semantic_delta_selection.py` fixture records two program
observations whose revisions cannot reconstruct from its retained inputs.
It fails the existing Phase 1 reconstruction-closure check on both Phase 3
and untouched merged `main`. That fixture needs faithful evidence qualification
before it can serve as a Phase 4 delta regression. The guarantee is preserved;
the fixture was not touched by Phase 3.

The design-rule tests expect absent legacy `frontend/src/product` stylesheets,
`frontend/src/api/resource.ts` and `SettingsPanel.tsx`. This unrelated frontend
fixture debt also reproduces on merged `main`; it is not a prerequisite for
the Phase 4 construction boundary. The paired debt run returns identically
`2 failed, 13 passed, 14 errors` on both branches. These are outside the default
gate. No speculative future improvement is listed as required work.

## L. Verdict

**YES — READY FOR PHASE 4.**

The repository has a production, inspectable boundary separating admitted
construction material, claim support grouping, method/version, deterministic
admission and retained publication. Semantic requirements publish honestly
before any software realization exists. This verdict applies to the tested
construction seam, not a claim that every historical constructor was migrated
or that mechanical admission certifies arbitrary semantic inference.

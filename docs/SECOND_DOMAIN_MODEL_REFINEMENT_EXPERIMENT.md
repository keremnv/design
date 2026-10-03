# Second-domain model refinement experiment

Status: experiment design. Not architecture authority. Not
implementation authorization. Baseline: `e189198f`.

## Research question

Can an agent construct an initially imperfect model from messy
heterogeneous evidence, discover deficiencies through real use, revise
the executable model program, and publish progressively better Worlds
without needing ontology-evolution infrastructure?

## Selected domain: repository cartography of this repository

The corpus is this repository itself at a fixed commit: 261 Python
files (`ontology_author/`, `tests/`, `profiles/`), 66 Markdown docs,
16 JSON configs, 56 TypeScript sources (`frontend/src`). It was not
authored to make Ontology Author easy — it is genuinely messy
(fossil tests, superseded packages, 66 docs of mixed vintage) and it
satisfies every selection criterion without inventing a domain:

- Multiple evidence forms: Python source, Markdown prose, JSON/YAML
  config, TypeScript source, test files as behavior evidence.
- Real cross-source joins: test↔implementation, doc↔code,
  CLI↔module, package-data↔code, import graph edges.
- Nontrivial entity boundaries: is the unit a file, module, package,
  "subsystem", test family, doc? (The quarantine audit itself is
  evidence this is genuinely uncertain.)
- Cheap raw facts (file lists, line counts) vs. expensive reusable
  joins (import closure, test-to-code locking, ship-inclusion).
- Natural ambiguity (which doc describes module X? which tests lock
  package Y?) and natural UNKNOWN (unresolved reference targets).
- Externally checkable tasks: every answer is verifiable with
  grep/pytest/wheel inspection/SQLite reads.
- Bounded: one repo snapshot, finite and freezable.

Ranked alternatives, not recommended: (2) the frontend↔backend
interface slice only — narrower, less messy, weaker boundary
pressure; keep as a fallback if the full corpus proves too large.
(3) A public third-party repository — requires network selection and
freezing work with no offsetting advantage; the audit questions map
less directly onto checkable tasks.

## Initial model scope

W0 deliberately models, mechanically first:

```text
source file (path + digest + language)
module / package containment
import edge (importer → imported, resolved or UNRESOLVED)
doc page (path + headings as locations, not referents)
test file → exercised-module edges where mechanically evident
shipped-or-not (wheel inclusion per module)
```

W0 deliberately does NOT model: semantic "subsystems,"
doc↔code aboutness, test intent, ownership/teams, anything requiring
judgment about meaning. Those are refinement fuel, not W0 scope.

## Task set (held out before W0 construction)

- Raw-dominant: "list every test file naming package X" (grep wins).
- Structured-dominant: "transitive production import closure of
  module M" (World wins after W0).
- Mixed: "which tests would fail if module M's public function F
  changed signature" (World narrows, raw confirms).
- Investigative: "is package P safe to exclude from the shipped
  wheel" (requires closure + packaging + test-lock evidence).
- Ambiguity: "which doc authoritatively describes subsystem S"
  (must stay UNKNOWN/candidates where docs conflict).

Task-blind protocol: freeze evidence snapshot → construct W0 →
freeze W0 → reveal tasks. W0 is expected to be imperfect; tuning W0
against every task defeats the experiment.

## Failure classifier (required before any repair)

```text
MISSING_EVIDENCE
BAD_EVIDENCE_ADAPTATION
BAD_MECHANICAL_SUBJECT_BOUNDARY
BAD_SEMANTIC_INTERPRETATION
WRONG_ENTITY_BOUNDARY
MISSING_RELATION
BAD_PERSISTENCE_CHOICE
INSUFFICIENT_COMPLETENESS
CONSUMER_QUERY_OR_REASONING_FAILURE
RAW_WORLD_INTERFACE_FRICTION
UNKNOWN / NEEDS_MORE_EVIDENCE
```

`agent failed task ≠ ontology inadequate` is enforced by requiring a
classification plus the evidence for it in the log.

## Repair classifier (smallest likely class)

```text
adapter / producer / constructor / profile-rule correction
constructor expansion
split / merge referent boundary
introduce / remove semantic identity
promote / demote relation durability
change completeness declaration
improve consumer usage
```

No infrastructure is pre-built for any class.

## Refinement log schema (one record per refinement)

```text
world_revision, exposing_task, observed_failure, failure_class,
relevant_evidence, old_assumption, repair_made, new_revision,
behavior_before, behavior_after, boundary_changed?,
identity_changed?, persistence_changed?, new_architecture_required?
```

Entity evolution is recorded descriptively in the log ("W0 treated
doc+code as one node; W1 builds page, section-span, and module
nodes"). No durable correspondence claims are created; the log is
experiment narrative, not product lineage.

## Iteration protocol

Repeat: run tasks → classify failure → inspect evidence → modify
model program → construct W1 at a fresh address → rerun tasks →
append log record. Attempt at least three full refinement iterations
before drawing conclusions. Stop a line of repair after two
iterations if behavior does not improve.

## Success criteria (thesis survives)

Failures mostly map to adapter/producer/constructor/profile repairs;
fresh Worlds encode improved distinctions; old Worlds remain valid;
no migration, global identity, or evolution framework required;
adequacy (Core conformance + application adequacy per the
pre-application baseline) rises across revisions.

## Falsification criteria (thesis fails)

A necessary task cannot be satisfied because cross-revision state
must itself be durable; or a required transition cannot be honestly
represented in a fresh W1; or a consumer needs an invariant identity
snapshot-local Worlds cannot provide. A real became-question —
consumer, task, and why independent W0+W1 reads are insufficient,
all recorded — is the only trigger for correspondence work, and
repeated became-questions with no honest constructor-level answer
falsify the thesis.

## Stop conditions

Stop implementing after three iterations or when held-out adequacy
plateaus for two consecutive Worlds. Stop the experiment entirely if
a falsification criterion fires (record it fully first). Never
escalate to architecture (comparison product, lineage, admission,
workflow) inside the experiment: record the gap and stop.

## Vestigial-idea observation

When a repair resembles a quarantined idea (split/merge
correspondence, standing, proposal/admission, currentness, semantic
identity), classify it as NOT-NEEDED / IDEA-USEFUL /
IMPLEMENTATION-REUSABLE / EXCEEDS-PRODUCT — from the active
architecture first, without importing the old subsystem (quarry
rule). This observation stream feeds the eventual cleanup decision:

```text
quarantined subsystem retires from shipping when: unneeded by frozen
product AND unneeded by this experiment AND no Core guarantee AND no
compat promise worth keeping AND its useful findings extracted.
Stop-shipping ≠ delete-from-repo ≠ change-Core-serialization.
```

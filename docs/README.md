# Documentation map

## Start here — current Core Product v1 authority

- [Baseline and application handoff](CORE_PRODUCT_V1_BASELINE.md): frozen capabilities, limits, supported reads and retained debt.
- [Completion contract](CORE_PRODUCT_V1_COMPLETION_CONTRACT.md): acceptance requirements.
- [Acceptance evidence](CORE_PRODUCT_V1_ACCEPTANCE.md): executable evidence and exact verification commands.
- [Architecture](ARCHITECTURE.md): application, ontology/construction, evidence adapters, World kernel.
- [Golden scenario](../profiles/core_v1/README.md): reproducible heterogeneous-source example.

Core capability is demonstrated; application completeness and value are separate
questions. Adapters observe source material; construction assigns meaning.
Canonical history retains separately addressed sealed revisions.

## Applications and extensions — not core prerequisites

These contracts describe bounded downstream mechanisms, not requirements that
every World must implement:

- [Software Governance construction](SOFTWARE_GOVERNANCE_CONSTRUCTION_CONTRACT.md) and its [acceptance record](SOFTWARE_GOVERNANCE_CONSTRUCTION_ACCEPTANCE.md): Construction v0 baseline for durable governance knowledge and bindings. The implementation is `ontology_author.software_governance`. TypeScript extraction and the mail vocabulary stay in the [mail profile](../profiles/software_governance_v0/README.md). The [config-route profile](../profiles/software_governance_config_v0/README.md) is a second fixture whose producer is not Program Spine. Neither fixture is the ontology. [Judgment v0](SOFTWARE_GOVERNANCE_JUDGMENT_CONTRACT.md) and its [acceptance record](SOFTWARE_GOVERNANCE_JUDGMENT_ACCEPTANCE.md) judge a sealed construction World. They are not part of the construction baseline. [Investigation v0](SOFTWARE_GOVERNANCE_INVESTIGATION_CONTRACT.md) and its [acceptance record](SOFTWARE_GOVERNANCE_INVESTIGATION_ACCEPTANCE.md) explore beyond a judgment case. They do not admit or publish, and they are not part of the judgment baseline.
- Program representation: [spine](PROGRAM_SPINE_CONTRACT.md), [extractor](SPINE_EXTRACTOR_CONTRACT.md), [comparison](SPINE_COMPARISON_CONTRACT.md), [TypeScript profile](TYPESCRIPT_SPINE_PROFILE.md).
- [Semantic persistence and recorded-dependency maintenance](SEMANTIC_PERSISTENCE_CONTRACT.md).
- [Target Architecture v0 Phase 3](TARGET_ARCHITECTURE_V0_PHASE3.md): construction-path audit, basis/support separation, grouped support and source-only semantic publication.
- [Target Architecture v0 Phase 4](TARGET_ARCHITECTURE_V0_PHASE4.md): W0→P1→W1→P2→W2 vertical slice, exact binding, historical reconsideration and the program capability-demand ledger.
- Authority: [construction](AUTHORITY_CONSTRUCTION_CONTRACT.md), [maintenance](AUTHORITY_MAINTENANCE_CONTRACT.md). Historical relative to the construction draft where they conflict.
- Earlier governance records, not superior to the construction draft: [foundations](GOVERNANCE_FOUNDATIONS.md), [cases](GOVERNANCE_CASE_CONTRACT.md), [adjudication](GOVERNANCE_ADJUDICATION_CONTRACT.md), [kernel mapping](GOVERNANCE_KERNEL_MAPPING.md), [candidate lifecycle](GOVERNED_CANDIDATE_LIFECYCLE.md).
- [Design checkout experiment](DESIGN_CHECKOUT_CONSTRUCTION_CONTRACT.md) and [profile](../profiles/design_checkout/).
- [Markdown adapter profile](MARKDOWN_SOURCE_PROFILE.md): source addressing, not semantic interpretation.

## Research and historical records — non-authoritative

- [Construction/application research](CONSTRUCTION_AND_APPLICATION_RESEARCH.md) remains a research synthesis, not a core specification.
- [Pre-application research baseline](PRE_APPLICATION_RESEARCH_BASELINE.md): reconciled downstream conclusions carried into Application v1; not Core authority and not the application contract.
- [Downstream experiments](../experiments/README.md) preserve maintenance-locality, direct semantic selection and design-granularity findings.
- Other `SEMANTIC_*.md` files are bounded experimental protocols/results. They do not impose a universal construction workflow.
- [Research inventory and archive](research/README.md) preserves earlier product directions and evidence.
- [Durable knowledge evolution scenarios](DURABLE_KNOWLEDGE_EVOLUTION_SCENARIOS.md): neutral catalogue of post-seal events. Not a persistence design and not Core authority.
- [OA application-layer discovery](OA_APPLICATION_LAYER_DISCOVERY.md): whether a reusable runtime belongs between Core and the Software Governance application. A research note, not an architecture acceptance.
- [Earlier foundations](FOUNDATIONS.md) and [research direction](RESEARCH_DIRECTION.md) are superseded as product authority.
- [Graph-native versus SQL-native experiment](<Experiment_ Graph-native vs SQL-native access to a frozen agent-authored relational view.md>) is historical evidence.

Payload `contract: ".../v0"` tags in experiments name record schemas; they do
not turn an experimental mechanism into a Core v1 requirement.

## Operations

[Agent attachment](AGENT_CLIENTS.md) · [Cursor](CURSOR_GUIDE.md) ·
[Release checklist](RELEASING.md) · [Contributor guidance](../AGENTS.md)
· [Repository checkpoint and verification](REPOSITORY_CHECKPOINT.md)

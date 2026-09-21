"""Run the bounded payment-path semantic-persistence experiment.

This is an experiment harness, not a resolver or a governance layer.  It
constructs one small TypeScript payment path, asks Composer only about one
declared PROGRAM_RELATIONSHIP obligation, and then exercises deterministic
admission and maintenance.  It never searches a repository, invokes a coding
agent, or promotes a World revision.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.run_governance_product_experiments import (
    CursorCliAdjudicatorTransport,
    _cursor_authenticated,
    _cursor_cli_version,
)
from ontology_author.authority import (
    AuthorityUniverse,
    ClaimKind,
    CompletenessScope,
    DeclaredSource,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    assemble_governance_case,
    assess_attachment_maintenance,
    assess_authority_change_impact,
    construct_authority_world,
    validate_case_sidecar,
)
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.evidence.program_source import (
    program_source_observations,
    source_evidence_record,
)
from ontology_author.program_spine import compare_program_spines
from ontology_author.semantic_binding import (
    PAYMENT_RELATIONSHIP_TUPLE_SHAPE,
    PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
    RELATIONSHIP_ADMISSION_PROFILE,
    CandidateValidationError,
    ConstructionObligation,
    EvidenceClass,
    SemanticConstructionInvocationError,
    SemanticPersistenceError,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
    construct_semantic_candidate,
    maintain_semantic_commitment,
    materialize_semantic_commitment_revision,
    write_admission_decision,
)
from ontology_author.world.core.model import (
    CompletenessStatus,
    Role,
    RoleType,
)
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import _spine, _write

PURPOSE = "payment-boundary-v1"
PROFILE = "payment-authority-v0"
AUTHORITY_TEXT = "Checkout must access payment providers through PaymentGateway."

PAYMENT_S0 = {
    "src/checkout.ts": (
        'import { authorize } from "./payment-service";\n'
        "export function checkout(): void { authorize(); }\n"
    ),
    "src/payment-service.ts": (
        'import { throughGateway } from "./payment-gateway";\n'
        "export function authorize(): void { throughGateway(); }\n"
    ),
    "src/payment-gateway.ts": (
        'import { chargeStripe } from "./stripe-client";\n'
        "export function throughGateway(): void { chargeStripe(); }\n"
    ),
    "src/stripe-client.ts": "export function chargeStripe(): void {}\n",
}
PAYMENT_C1 = {
    **PAYMENT_S0,
    "src/checkout.ts": (
        'import { chargeStripe } from "./stripe-client";\n'
        "export function checkout(): void { chargeStripe(); }\n"
    ),
}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _universe(root: Path) -> AuthorityUniverse:
    return AuthorityUniverse(
        universe_id="payment-boundary-fixture-v1",
        workspace=root,
        sources=(
            DeclaredSource(
                "docs/payment-boundary.md",
                root / "docs/payment-boundary.md",
                SourceStanding.AUTHORITATIVE,
            ),
        ),
    )


def _sources(root: Path) -> dict[str, MarkdownSource]:
    return {
        "docs/payment-boundary.md": MarkdownSource(
            root / "docs/payment-boundary.md", handle="docs/payment-boundary.md"
        )
    }


def _one_callable(ctor, label: str) -> str:
    values = ctor.program_entities(kind="callable", label=label)
    if len(values) != 1:
        raise RuntimeError(f"expected one {label} callable, found {values}")
    return values[0]


def _payment_path(ctor) -> tuple[dict[str, str], list[dict[str, str]]]:
    service = _one_callable(ctor, "authorize")
    gateway = _one_callable(ctor, "throughGateway")
    provider = _one_callable(ctor, "chargeStripe")
    checkout_entry = ctor.call_site_invoking("authorize")
    service_call_site = ctor.call_site_invoking("throughGateway")
    gateway_call_site = ctor.call_site_invoking("chargeStripe")
    endpoints = {
        "checkout_entry": checkout_entry,
        "service": service,
        "service_call_site": service_call_site,
        "gateway": gateway,
        "gateway_call_site": gateway_call_site,
        "provider": provider,
    }
    relations = [
        {
            "relation": "program_invokes",
            "call_site": checkout_entry,
            "target": service,
        },
        {
            "relation": "program_invokes",
            "call_site": service_call_site,
            "target": gateway,
        },
        {
            "relation": "program_invokes",
            "call_site": gateway_call_site,
            "target": provider,
        },
    ]
    return endpoints, relations


def _build_payment_authority(ctor) -> None:
    source = ctor.source("docs/payment-boundary.md")
    observation = source.observe(source.paragraphs()[0])
    checkout = _one_callable(ctor, "checkout")
    _endpoints, path_relations = _payment_path(ctor)

    ctor.create_semantic_referent(
        "semantic:CheckoutPaymentAccess",
        label="Checkout payment-provider access",
        observations=(observation,),
    )
    ctor.create_semantic_referent(
        "semantic:PaymentGatewayBoundary",
        label="PaymentGateway boundary",
        observations=(observation,),
    )
    ctor.persist_claim(
        "payment_access_scope",
        {
            "access": "semantic:CheckoutPaymentAccess",
            "boundary": "semantic:PaymentGatewayBoundary",
            "program": checkout,
        },
        claim_kind=ClaimKind.SEMANTIC_PROGRAM,
        support=RelationSupport.CROSS_EVIDENCE_INFERRED,
        endpoint_resolution={
            "access": ReferentResolution.AGENT_RESOLVED,
            "boundary": ReferentResolution.AGENT_RESOLVED,
            "program": ReferentResolution.DETERMINISTIC,
        },
        observations=(observation,),
        roles=[
            Role("access", RoleType.REFERENT),
            Role("boundary", RoleType.REFERENT),
            Role("program", RoleType.REFERENT),
        ],
        warrant=[
            {
                "program_entity": checkout,
                "structural_context": ctor.structural_context(checkout),
                "justifying_program_relations": path_relations,
                "justifying_resolution_outcomes": [],
                "relation_support": RelationSupport.CROSS_EVIDENCE_INFERRED.value,
                "endpoint_resolution": {"program": ReferentResolution.DETERMINISTIC.value},
            }
        ],
    )
    ctor.declare_attachment_universe([checkout], observation=observation)
    ctor.record_completeness(
        scope=CompletenessScope.ADDRESSABILITY,
        universe="authority_source",
        status=CompletenessStatus.COMPLETE,
        basis="the declared payment-boundary source is reconstructible",
    )
    ctor.record_completeness(
        scope=CompletenessScope.CONSTRUCTION,
        universe="authority_examined",
        status=CompletenessStatus.COMPLETE,
        basis="construction coverage is complete over the declared payment-boundary paragraph",
    )
    ctor.record_completeness(
        scope=CompletenessScope.ATTACHMENT,
        universe="authority_attachment_scope",
        status=CompletenessStatus.COMPLETE,
        basis=(
            "attachment construction COMPLETE for the declared payment access "
            f"purpose {PURPOSE} under profile {PROFILE}"
        ),
    )


def _obligation(case: dict[str, Any], endpoints: dict[str, str]) -> ConstructionObligation:
    authority_refs = tuple(
        str(item["observation_id"])
        for item in case["authority"]["observations"]
        if AUTHORITY_TEXT in str(item.get("reconstructed_text") or "")
    )
    if len(authority_refs) != 1:
        raise RuntimeError(f"payment authority observation was not unique: {authority_refs}")
    return ConstructionObligation(
        obligation_id="obligation:payment-access-mediation",
        purpose=PURPOSE,
        authority_refs=authority_refs,
        semantic_subject="semantic:CheckoutPaymentAccess",
        semantic_relation="mediated_by",
        question=(
            "Does the supplied baseline program context establish that Checkout's "
            "payment-provider access is mediated by PaymentGateway, and which "
            "supplied program relations realize that bounded relationship?"
        ),
        program_scope="bounded Checkout payment-provider access path",
        allowed_program_endpoints=tuple(endpoints.values()),
        required_evidence_classes=(
            EvidenceClass.AUTHORITY_GROUNDING.value,
            EvidenceClass.PROGRAM_GROUNDING.value,
            EvidenceClass.MECHANICAL_GROUNDING.value,
        ),
        tuple_shape=PAYMENT_RELATIONSHIP_TUPLE_SHAPE,
        obligation_kind=PROGRAM_RELATIONSHIP_OBLIGATION_KIND,
        admission_profile=RELATIONSHIP_ADMISSION_PROFILE,
    )


def _alias(catalog: dict[str, Any], category: str, identifier: str) -> str:
    for item in catalog.get("entries") or []:
        if item.get("category") == category and item.get("id") == identifier:
            return str(item["alias"])
    raise RuntimeError(f"catalog has no {category} entry for {identifier}")


def _all_aliases(catalog: dict[str, Any], category: str) -> list[str]:
    return list(catalog.get("allowed_aliases", {}).get(category) or [])


def _dependency_alias(catalog: dict[str, Any], kind: str) -> str:
    for item in catalog.get("entries") or []:
        if (
            item.get("category") == "MAINTENANCE_DEPENDENCY"
            and (item.get("dependency") or {}).get("kind") == kind
        ):
            return str(item["alias"])
    raise RuntimeError(f"catalog has no maintenance dependency of kind {kind}")


def _payment_dependencies(
    endpoints: dict[str, str], relations: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """Return the finite receipt used by the payment relationship obligation."""

    dependencies: list[dict[str, Any]] = [
        {"kind": "program_identity", "program_entity": entity}
        for entity in dict.fromkeys(endpoints.values())
    ]
    dependencies.extend(
        {"kind": "relation_tuple", "recorded": relation}
        for relation in relations
    )
    dependencies.extend(
        {
            "kind": "manifestation_property",
            "program_entity": entity,
            "property": "source_manifestation",
        }
        for entity in dict.fromkeys(endpoints.values())
        if ":callable:" in entity
    )
    dependencies.append(
        {
            "kind": "structural_context",
            "program_entity": endpoints["service"],
            "chain": [],
        }
    )
    return dependencies


def _draft(
    obligation: ConstructionObligation,
    catalog: dict[str, Any],
    endpoints: dict[str, str],
    relations: list[dict[str, str]],
    *,
    mechanical: bool = True,
    relation: str | None = None,
    polarity: str = "POSITIVE",
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    mechanical_aliases = _all_aliases(catalog, "MECHANICAL_FACT") if mechanical else []
    return {
        "obligation_id": obligation.obligation_id,
        "claim_kind": "SEMANTIC_PROGRAM",
        "relation_name": relation or obligation.semantic_relation,
        "semantic_endpoints": {
            "access": _alias(catalog, "SEMANTIC_REFERENT", "semantic:CheckoutPaymentAccess"),
            "boundary": _alias(catalog, "SEMANTIC_REFERENT", "semantic:PaymentGatewayBoundary"),
        },
        "program_endpoints": {
            role: _alias(catalog, "PROGRAM_ENDPOINT", endpoint)
            for role, endpoint in endpoints.items()
        },
        "polarity": polarity,
        "support_kind": "CROSS_EVIDENCE_INFERRED",
        "authority_evidence_aliases": _all_aliases(catalog, "AUTHORITATIVE_EVIDENCE"),
        "program_source_evidence_aliases": _all_aliases(catalog, "PROGRAM_SOURCE"),
        "mechanical_evidence_aliases": mechanical_aliases,
        "program_scope": obligation.program_scope,
        "maintenance_dependency_aliases": (
            dependencies
            if dependencies is not None
            else _all_aliases(catalog, "MAINTENANCE_DEPENDENCY")
        ),
        "completeness_aliases": [],
    }


def _dependency_counts(candidate: Any) -> dict[str, int]:
    dependencies = list(candidate.maintenance_dependencies)
    return {
        "program_identities": sum(item.get("kind") == "program_identity" for item in dependencies),
        "relation_tuples": sum(item.get("kind") == "relation_tuple" for item in dependencies),
        "manifestation_dependencies": sum(item.get("kind") == "manifestation_property" for item in dependencies),
        "structural_dependencies": sum(item.get("kind") == "structural_context" for item in dependencies),
        "source_dependencies": sum(
            item.get("kind") == "manifestation_property"
            and item.get("property") == "source_manifestation"
            for item in dependencies
        ),
        "total": len(dependencies),
    }


def _bounded_source(old: ConstructionWorld, endpoints: dict[str, str], checkout: str, old_snapshot: str) -> list[dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for entity in endpoints.values():
        for observation in program_source_observations(old, entity):
            record = source_evidence_record(
                world=old,
                entity=entity,
                side="OLD",
                snapshot_id=old_snapshot,
                inclusion_reason="RELATIONAL_SEMANTIC_CONSTRUCTION",
                selected_by=checkout,
                observation=observation,
            )
            output[str(record["evidence_id"])] = record
    return [output[key] for key in sorted(output)]


def _setup(scratch: Path) -> tuple[ConstructionWorld, ConstructionWorld, Any, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, str], list[dict[str, str]]]:
    _write(scratch, {"docs/payment-boundary.md": AUTHORITY_TEXT + "\n"})
    _spine(scratch, PAYMENT_S0, "baseline-spine")
    result = construct_authority_world(
        scratch / "baseline-spine",
        scratch / "baseline-world",
        _universe(scratch),
        _build_payment_authority,
        construction_id="payment-boundary-construction-v1",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    if not result.succeeded:
        raise RuntimeError("payment authority construction failed: " + "; ".join(result.errors))
    _spine(scratch, PAYMENT_C1, "candidate-spine")
    comparison = compare_program_spines(scratch / "baseline-spine", scratch / "candidate-spine")
    old = ConstructionWorld.open(scratch / "baseline-world" / "world.sqlite", read_only=True)
    new = ConstructionWorld.open(scratch / "candidate-spine" / "world.sqlite", read_only=True)
    maintenance = assess_attachment_maintenance(old, new, comparison)
    impact = assess_authority_change_impact(old, new, comparison, maintenance=maintenance)
    case = assemble_governance_case(
        old,
        new,
        comparison,
        _sources(scratch),
        maintenance=maintenance,
        impact=impact,
        purpose=PURPOSE,
    )
    errors = validate_case_sidecar(case, maintenance=maintenance, impact=impact, comparison=comparison)
    if errors:
        raise RuntimeError("payment GovernanceCase failed validation: " + "; ".join(errors))
    endpoints, relations = _payment_path(_AuthorityView(old))
    return old, new, comparison, maintenance, impact, case, endpoints, relations


class _AuthorityView:
    """Small read-only helper for locating the already constructed path."""

    def __init__(self, world: ConstructionWorld):
        self.world = world

    def program_entities(self, *, kind: str | None = None, label: str | None = None):
        kinds = {row["entity"]: row["kind"] for row in self.world.relation_rows("program_entity_kind")}
        labels = {
            str(row["id"]): str(row["label"])
            for row in self.world.query("SELECT id, label FROM _world_referents")
        }
        return [
            entity
            for entity, value in kinds.items()
            if (kind is None or value == kind) and (label is None or labels.get(entity) == label)
        ]

    def call_site_invoking(self, target_label: str) -> str:
        target = _one_callable(self, target_label)
        rows = [row["call_site"] for row in self.world.relation_rows("program_invokes") if row["target"] == target]
        if len(rows) != 1:
            raise RuntimeError(f"expected one call site for {target_label}: {rows}")
        return rows[0]


def _program_endpoint_kinds(world: ConstructionWorld) -> dict[str, str]:
    """Project mechanically established spine kinds into the model catalog."""

    return {
        str(row["entity"]): str(row["kind"])
        for row in world.relation_rows("program_entity_kind")
    }


def _run_controls(
    obligation: ConstructionObligation,
    case: dict[str, Any],
    endpoints: dict[str, str],
    relations: list[dict[str, str]],
    bounded_source: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    program_endpoint_kinds: dict[str, str],
    output: Path,
) -> dict[str, Any]:
    catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=bounded_source,
        maintenance_dependencies=dependencies,
        program_endpoint_kinds=program_endpoint_kinds,
    )
    controls: dict[str, Any] = {}
    base = _draft(obligation, catalog, endpoints, relations)

    def evaluate(
        name: str,
        draft: dict[str, Any],
        control_catalog: dict[str, Any] = catalog,
    ) -> None:
        try:
            candidate = compile_semantic_candidate_draft(obligation, control_catalog, draft)
            decision = admit_semantic_candidate(
                obligation,
                candidate,
                control_catalog,
                snapshot_id="snapshot:payment-s0",
            )
            controls[name] = {
                "status": "VALID",
                "candidate": candidate.to_dict(),
                "admission": decision.to_dict(),
            }
        except (CandidateValidationError, SemanticPersistenceError, ValueError) as exc:
            controls[name] = {
                "status": "INVALID_CANDIDATE",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    evaluate("A-grounded-finite-relational-commitment", base)
    callable_for_call_site = dict(base)
    callable_for_call_site["program_endpoints"] = dict(base["program_endpoints"])
    callable_for_call_site["program_endpoints"]["checkout_entry"] = _alias(
        catalog, "PROGRAM_ENDPOINT", endpoints["service"]
    )
    evaluate("F-callable-supplied-to-call-site-role", callable_for_call_site)

    call_site_for_callable = dict(base)
    call_site_for_callable["program_endpoints"] = dict(base["program_endpoints"])
    call_site_for_callable["program_endpoints"]["service"] = _alias(
        catalog, "PROGRAM_ENDPOINT", endpoints["checkout_entry"]
    )
    evaluate("G-call-site-supplied-to-callable-role", call_site_for_callable)

    missing_mechanical = dict(base)
    missing_mechanical["mechanical_evidence_aliases"] = []
    evaluate("B-no-mechanical-grounding", missing_mechanical)

    wildcard_dependency = dict(base)
    wildcard_catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=bounded_source,
        maintenance_dependencies=dependencies + [{"kind": "graph_query", "query": "watch all payment paths"}],
        program_endpoint_kinds=program_endpoint_kinds,
    )
    wildcard_dependency["maintenance_dependency_aliases"] = [
        _dependency_alias(wildcard_catalog, "graph_query")
    ]
    evaluate("C-wildcard-maintenance-dependency", wildcard_dependency, wildcard_catalog)

    evaluate("D-incidental-semantic-claim", {**base, "relation_name": "uses_library"})
    evaluate("E-negative-without-completeness", {**base, "polarity": "NEGATIVE"})
    _write_json(output / "controls.json", controls)
    return controls


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="payment-semantic-persistence-") as temporary:
        scratch = Path(temporary)
        old, new, comparison, maintenance, impact, case, endpoints, path_relations = _setup(scratch)
        try:
            _write_json(output / "governance.case.json", case)
            _write_json(output / "authority.maintenance.json", maintenance)
            _write_json(output / "authority.impact.json", impact)
            comparison.write(output)
            old_snapshot = snapshot_id(old)
            obligation = _obligation(case, endpoints)
            _write_json(output / "construction.obligation.json", obligation.to_dict())
            checkout = endpoints["checkout_entry"]
            bounded_source = _bounded_source(old, endpoints, checkout, old_snapshot)
            dependencies = _payment_dependencies(endpoints, path_relations)
            program_endpoint_kinds = _program_endpoint_kinds(old)
            controls = _run_controls(
                obligation,
                case,
                endpoints,
                path_relations,
                bounded_source,
                dependencies,
                program_endpoint_kinds,
                output,
            )
            live_runs: list[dict[str, Any]] = []
            live_candidates: list[tuple[Any, Any, Path]] = []
            cli_available = shutil.which("cursor-agent") is not None
            authenticated = cli_available and _cursor_authenticated()
            if authenticated:
                version = _cursor_cli_version()
                for number in (1, 2):
                    run_dir = output / f"live-run-{number}"
                    try:
                        candidate = construct_semantic_candidate(
                            obligation,
                            case,
                            transport=CursorCliAdjudicatorTransport(
                                model="composer-2.5", cli_version=version
                            ),
                            bounded_program_source=bounded_source,
                            maintenance_dependencies=dependencies,
                            program_endpoint_kinds=program_endpoint_kinds,
                            constructor_metadata={
                                "provider": "cursor-cli",
                                "model": "composer-2.5",
                                "model_version": version,
                                "boundary": "catalog-only; empty temporary workspace",
                            },
                            output_dir=run_dir,
                        )
                        decision = admit_semantic_candidate(
                            obligation, candidate, build_semantic_construction_catalog(
                                obligation,
                                case,
                                bounded_program_source=bounded_source,
                                maintenance_dependencies=dependencies,
                                program_endpoint_kinds=program_endpoint_kinds,
                            ), snapshot_id=old_snapshot
                        )
                        write_admission_decision(decision, run_dir)
                        live_runs.append(
                            {
                                "run": number,
                                "status": "SUCCEEDED",
                                "candidate_id": candidate.candidate_id,
                                "admission": decision.to_dict(),
                                "dependency_counts": _dependency_counts(candidate),
                            }
                        )
                        live_candidates.append((candidate, decision, run_dir))
                    except SemanticConstructionInvocationError as exc:
                        live_runs.append(
                            {
                                "run": number,
                                "status": exc.receipt.get("runtime_status", "FAILED_PROVIDER"),
                                "receipt": exc.receipt,
                            }
                        )
            else:
                live_runs = [
                    {
                        "run": 1,
                        "status": "NOT_RUN",
                        "reason": "model credentials unavailable"
                        if cli_available
                        else "cursor CLI unavailable",
                    },
                    {
                        "run": 2,
                        "status": "NOT_RUN",
                        "reason": "model credentials unavailable"
                        if cli_available
                        else "cursor CLI unavailable",
                    },
                ]

            selected = next(
                (
                    item
                    for item in live_candidates
                    if item[1].outcome == "PERSIST_COMMITMENT"
                ),
                None,
            )
            if selected is None:
                control = controls["A-grounded-finite-relational-commitment"]
                if control["status"] != "VALID":
                    raise RuntimeError("deterministic relational control did not compile")
                selected_dir = output / "deterministic-control"
                selected_dir.mkdir(parents=True, exist_ok=True)
                selected_candidate = compile_semantic_candidate_draft(
                    obligation,
                    build_semantic_construction_catalog(
                        obligation,
                        case,
                        bounded_program_source=bounded_source,
                        maintenance_dependencies=dependencies,
                        program_endpoint_kinds=program_endpoint_kinds,
                    ),
                    _draft(
                        obligation,
                        build_semantic_construction_catalog(
                            obligation,
                            case,
                            bounded_program_source=bounded_source,
                            maintenance_dependencies=dependencies,
                            program_endpoint_kinds=program_endpoint_kinds,
                        ),
                        endpoints,
                        path_relations,
                    ),
                    construction_method="deterministic experiment control",
                )
                selected_decision = admit_semantic_candidate(
                    obligation,
                    selected_candidate,
                    build_semantic_construction_catalog(
                        obligation,
                        case,
                        bounded_program_source=bounded_source,
                        maintenance_dependencies=dependencies,
                        program_endpoint_kinds=program_endpoint_kinds,
                    ),
                    snapshot_id=old_snapshot,
                )
                _write_json(selected_dir / "semantic.candidate.json", selected_candidate.to_dict())
                write_admission_decision(selected_decision, selected_dir)
                path_kind = "DETERMINISTIC_CONTROL"
            else:
                selected_candidate, selected_decision, selected_dir = selected
                path_kind = "LIVE"

            materialized = materialize_semantic_commitment_revision(
                old,
                selected_dir / "baseline-world-after",
                obligation,
                selected_candidate,
                selected_decision,
                build_semantic_construction_catalog(
                    obligation,
                    case,
                    bounded_program_source=bounded_source,
                    maintenance_dependencies=dependencies,
                    program_endpoint_kinds=program_endpoint_kinds,
                ),
                snapshot_id=old_snapshot,
            )
            _write_json(selected_dir / "semantic.commitment.json", materialized)
            g1 = ConstructionWorld.open(selected_dir / "baseline-world-after" / "world.sqlite", read_only=True)
            try:
                maintenance_result = maintain_semantic_commitment(materialized["warrant"], comparison)
                _write_json(selected_dir / "semantic.commitment.maintenance.json", maintenance_result)
                fresh_case = assemble_governance_case(
                    g1,
                    new,
                    comparison,
                    _sources(scratch),
                    maintenance=maintenance,
                    impact=impact,
                    purpose=PURPOSE,
                )
                fresh_case_errors = validate_case_sidecar(
                    fresh_case,
                    maintenance=maintenance,
                    impact=impact,
                    comparison=comparison,
                )
                if fresh_case_errors:
                    raise RuntimeError(
                        "reused payment GovernanceCase failed validation: "
                        + "; ".join(fresh_case_errors)
                    )
            finally:
                g1.close()
            _write_json(selected_dir / "governance.case.reused.json", fresh_case)
            result = {
                "status": "SUCCEEDED",
                "path": path_kind,
                "provider": "cursor-cli",
                "model": "composer-2.5",
                "case_id": case["case_id"],
                "obligation_id": obligation.obligation_id,
                "program_path": {
                    "baseline": "Checkout -> PaymentService -> PaymentGateway -> StripeClient",
                    "candidate": "Checkout -> StripeClient",
                    "relation_count": len(path_relations),
                },
                "live_runs": live_runs,
                "live_commitment_admitted": any(
                    item.get("admission", {}).get("outcome")
                    == "PERSIST_COMMITMENT"
                    for item in live_runs
                ),
                "controls": {
                    name: {
                        "status": value.get("status"),
                        "outcome": (value.get("admission") or {}).get("outcome"),
                        "reason": (value.get("admission") or {}).get("reason"),
                    }
                    for name, value in controls.items()
                },
                "selected_candidate_id": selected_candidate.candidate_id,
                "selected_admission": selected_decision.to_dict(),
                "dependency_counts": _dependency_counts(selected_candidate),
                "materialization": {
                    "published": materialized["published"],
                    "assertion_id": materialized["assertion_id"],
                    "warrant_id": materialized["warrant_id"],
                    "relation_name": materialized["relation_name"],
                    "baseline_snapshot_id": old_snapshot,
                    "materialized_snapshot_id": materialized["candidate_snapshot_id"],
                },
                "maintenance": {
                    "status": maintenance_result["status"],
                    "model_invoked": maintenance_result["model_invoked"],
                    "transferred": maintenance_result["transferred"],
                    "candidate_semantic_status": maintenance_result["candidate_semantic_status"],
                },
                "fresh_case": {
                    "case_id": fresh_case["case_id"],
                    "validation": "VALID",
                    "model_invoked_for_case_assembly": False,
                    "persisted_commitment_included": any(
                        item.get("included_because") == ["PERSISTED_SEMANTIC_COMMITMENT"]
                        for item in fresh_case["semantic_context"]["claims"]
                    ),
                    "candidate_absence_statuses": sorted(
                        {
                            item["status"]
                            for item in fresh_case["semantic_context"]["program_links"]
                            if item.get("side") == "NEW"
                        }
                    ),
                },
                "falsification_findings": [],
            }
        finally:
            old.close()
            new.close()
    _write_json(output / "experiment.result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "experiments" / "semantic-relational-persistence-20260916-run1",
    )
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

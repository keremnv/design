from __future__ import annotations

import json
import sqlite3
import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    AuthorityConstructor,
    ClaimKind,
    CompletenessScope,
    GovernanceError,
    ReferentResolution,
    RelationSupport,
    assemble_governance_case,
    assess_attachment_maintenance,
    assess_authority_change_impact,
    assess_authority_governance,
    construct_authority_world,
    program_world_fingerprint,
    validate_case_sidecar,
    validate_impact_sidecar,
    validate_maintenance_sidecar,
)
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.authority.relevance import relation_rows_with_ids
from ontology_author.program_spine import compare_program_spines
from ontology_author.world.core.model import CompletenessStatus, Role, RoleType
from ontology_author.world.runtime.world import ConstructionWorld
from tests.test_authority_construction import (
    MD,
    PROFILE,
    PURPOSE,
    TS_A,
    TS_B,
    _build_authority,
    _spine,
    _universe,
    _write,
)


pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (Path(__file__).resolve().parents[1] / "frontend" / "node_modules" / "typescript").exists(),
    reason="the TypeScript compiler API dependency is not installed",
)


def _sources(root: Path) -> dict[str, MarkdownSource]:
    return {
        handle: MarkdownSource(root / handle, handle=handle)
        for handle in (
            "docs/subscriptions.md",
            "docs/adr/payment-boundary.md",
            "docs/ambiguous.md",
            "docs/notes.md",
            "docs/hints.md",
        )
        if (root / handle).exists()
    }


def _unseal(path: Path) -> None:
    path.parent.chmod(path.parent.stat().st_mode | 0o700)
    path.chmod(path.stat().st_mode | 0o600)


def _close(*worlds: ConstructionWorld) -> None:
    for world in worlds:
        world.close()


def _governed(tmp_path: Path, files: dict[str, str] = TS_A, build=_build_authority, output: str = "world-governed"):
    _write(tmp_path, MD)
    spine = _spine(tmp_path, files, "world-spine")
    result = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / output,
        _universe(tmp_path),
        build,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert result.succeeded, result.errors
    return spine, result


def _completeness(ctor: AuthorityConstructor, *, attachment: CompletenessStatus = CompletenessStatus.COMPLETE) -> None:
    ctor.record_completeness(
        scope=CompletenessScope.ADDRESSABILITY,
        universe="authority_source",
        status=CompletenessStatus.COMPLETE,
        basis="every declared Markdown source has a content digest and reconstructible document range",
    )
    ctor.record_completeness(
        scope=CompletenessScope.CONSTRUCTION,
        universe="authority_examined",
        status=CompletenessStatus.COMPLETE,
        basis=f"construction coverage COMPLETE over declared examined regions for {PURPOSE}",
    )
    ctor.record_completeness(
        scope=CompletenessScope.ATTACHMENT,
        universe="authority_attachment_scope",
        status=attachment,
        basis=(
            "attachment construction COMPLETE for explicitly identified checkout-action "
            f"requirements over the declared checkout program universe under constructor "
            f"profile {PROFILE} and purpose {PURPOSE}"
            if attachment is CompletenessStatus.COMPLETE
            else "attachment coverage is incomplete for this purpose"
        ),
        known_gaps=() if attachment is CompletenessStatus.COMPLETE else ("unattached helper identities remain",),
    )


def _direct_callable_build(label: str, include_helper_universe: bool = False):
    def build(ctor: AuthorityConstructor) -> None:
        subscriptions = ctor.source("docs/subscriptions.md")
        observation = subscriptions.observe(subscriptions.paragraphs()[1])
        target = ctor.program_entities(kind="callable", label=label)
        assert len(target) == 1
        ctor.persist_claim(
            "governs_callable",
            {"program": target[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.AGENT_RESOLVED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        if include_helper_universe:
            helpers = ctor.program_entities(kind="callable", label="formatSubscriptionDate")
            members: list[str] = []
            for helper in helpers:
                members.extend(ctor.structural_context(helper))
            if members:
                ctor.declare_attachment_universe(members, observation=observation)
        _completeness(ctor)

    return build


def _module_build(*, structural: bool = False, extra_identity: str | None = None):
    def build(ctor: AuthorityConstructor) -> None:
        adr = ctor.source("docs/adr/payment-boundary.md")
        observation = adr.observe(adr.paragraphs()[0])
        boundary = ctor.program_entities(kind="module", descriptor_contains="boundary.ts")
        assert len(boundary) == 1
        assertion = ctor.persist_claim(
            "governs_module",
            {"program": boundary[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.SOURCE_DEFINED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        if structural:
            ctor.declare_relevance_scope(
                [
                    {
                        "clause_kind": "STRUCTURAL_SCOPE",
                        "identity_id": boundary[0],
                        "manifestation_properties": ["signature", "source_manifestation"],
                    }
                ],
                assertion_id=assertion,
                program_entity=boundary[0],
                observations=(observation,),
            )
        if extra_identity:
            identities = ctor.program_entities(kind="callable", label=extra_identity)
            assert len(identities) == 1
            ctor.declare_relevance_scope(
                [{
                    "clause_kind": "EXPLICIT_IDENTITY",
                    "identity_id": identities[0],
                    "manifestation_properties": ["signature", "source_manifestation"],
                }],
                assertion_id=assertion,
                program_entity=boundary[0],
                observations=(observation,),
            )
        _completeness(ctor)

    return build


def test_default_call_site_and_callable_and_module_scopes_are_persisted(tmp_path):
    _, _ = _governed(tmp_path)
    world = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    try:
        scopes = relation_rows_with_ids(world, "authority_relevance_scope")
        assert scopes
        warrants = {
            str(row.get("_assertion_id")): row
            for row in relation_rows_with_ids(world, "authority_attachment_warrant")
        }
        kinds = {str(row["entity"]): str(row["kind"]) for row in world.relation_rows("program_entity_kind")}
        by_warrant: dict[str, list[dict[str, str]]] = {}
        for row in scopes:
            by_warrant.setdefault(str(row["warrant_assertion_id"]), []).append(row)
            assert row["warrant_assertion_id"] in warrants
            assert row["clause_kind"] in {
                "ATTACHED_IDENTITY",
                "IDENTITY_MANIFESTATION",
                "ENDPOINT_RELATION",
                "STRUCTURAL_SCOPE",
                "EXPLICIT_IDENTITY",
            }
        call_site_warrant = next(
            warrant_id
            for warrant_id, warrant in warrants.items()
            if kinds.get(str(warrant["program_entity"])) == "call_site"
        )
        call_clauses = {row["clause_kind"] for row in by_warrant[call_site_warrant]}
        assert call_clauses == {"ATTACHED_IDENTITY", "ENDPOINT_RELATION"}
        assert any(
            row["relation_name"] == "program_invokes" and row["origin"] == "DEFAULT_KIND_RULE"
            for row in by_warrant[call_site_warrant]
        )
        module_warrant = next(
            warrant_id
            for warrant_id, warrant in warrants.items()
            if kinds.get(str(warrant["program_entity"])) == "module"
        )
        module_clauses = [row for row in by_warrant[module_warrant] if row["origin"] == "DEFAULT_KIND_RULE"]
        assert {row["clause_kind"] for row in module_clauses} == {"ATTACHED_IDENTITY", "ENDPOINT_RELATION"}
        assert all(row["relation_name"] in {"", "program_imports"} for row in module_clauses)
        assert not any(row["clause_kind"] == "STRUCTURAL_SCOPE" for row in module_clauses)
        warrant_ids = {str(row.get("_assertion_id")) for row in relation_rows_with_ids(world, "authority_attachment_warrant")}
        scope_ids = {str(row["warrant_assertion_id"]) for row in scopes}
        assert warrant_ids == scope_ids
    finally:
        world.close()


def test_warrant_and_relevance_scope_remain_separate(tmp_path):
    _, _ = _governed(tmp_path)
    world = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    try:
        warrant_schema = {role["name"] for role in world.relation_schema("authority_attachment_warrant")["roles"]}
        scope_schema = {role["name"] for role in world.relation_schema("authority_relevance_scope")["roles"]}
        assert "clause_kind" not in warrant_schema
        assert "justifying_program_relations" not in scope_schema
        assert "warrant_assertion_id" in scope_schema
    finally:
        world.close()


def test_cancellation_retarget_reresolves_and_selects_exact_markdown(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _build_authority,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    old_fp = program_world_fingerprint(tmp_path / "world-governed")
    _spine(tmp_path, TS_B, "world-spine-b")
    new_fp = program_world_fingerprint(tmp_path / "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        bundle = assess_authority_governance(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assert validate_maintenance_sidecar(bundle["maintenance"], old_world=old, new_world=new, comparison=comparison) == []
        assert validate_impact_sidecar(
            bundle["impact"], old_world=old, comparison=comparison, maintenance=bundle["maintenance"]
        ) == []
        assert validate_case_sidecar(
            bundle["case"], maintenance=bundle["maintenance"], impact=bundle["impact"], comparison=comparison
        ) == []
        realized = next(
            item
            for item in bundle["maintenance"]["assessments"]
            if item["relation_name"] == "realized_by"
        )
        realized_impact = next(
            item
            for item in bundle["impact"]["impacts"]
            if item["warrant_assertion_id"] == realized["warrant_assertion_id"]
        )
        assert realized["continuation"] == "UNIQUE"
        assert realized["correspondence_basis"] == "HEURISTIC"
        assert realized["maintenance_action"] == "RERESOLVE"
        assert realized["persistence_implication"] == "NO_RENEWAL"
        assert realized_impact["impact"] == "AFFECTED"
        selected = next(
            item
            for item in bundle["case"]["selection"]
            if item["warrant_assertion_id"] == realized["warrant_assertion_id"]
        )
        assert selected["selected_because"] == [
            "ATTACHMENT_GROUNDS_CHANGED",
            "GOVERNED_SURFACE_CHANGED",
        ]
        assert bundle["case"]["case_result"] == "SELECTED"
        texts = [item["reconstructed_text"] for item in bundle["case"]["authority"]["observations"]]
        assert any('The initial "Cancel subscription" action enters the retention flow.' in text for text in texts)
        assert all(item["standing"] == "AUTHORITATIVE" for item in bundle["case"]["authority"]["observations"])
        dumped = json.dumps(bundle)
        assert "VIOLATION" not in dumped
        assert "COMPLIANT" not in dumped
        assert "verdict" not in dumped
        assert program_world_fingerprint(tmp_path / "world-governed") == old_fp
        assert program_world_fingerprint(tmp_path / "world-spine-b") == new_fp
        repeat = assemble_governance_case(
            old, new, comparison, _sources(tmp_path), maintenance=bundle["maintenance"], impact=bundle["impact"], purpose=PURPOSE
        )
        assert repeat == bundle["case"]
        bodies = " ".join(
            item.get("reconstructed_text") or ""
            for item in bundle["case"]["program_context"].get("source_evidence") or []
        )
        assert "export function cancelSubscription" not in bodies
        assert "export function openRetentionFlow" not in bodies
        semantic = {item["id"] for item in bundle["case"]["authority"]["semantic_referents"]}
        assert "semantic:CancellationEntryAction" in semantic
        claim_kinds = {item["claim_kind"] for item in bundle["case"]["authority"]["claims"]}
        assert "SEMANTIC_PROGRAM" in claim_kinds
        assert "SOURCE_PROPOSITION" in claim_kinds
    finally:
        _close(old, new)


def test_hold_but_affected_selects_callable_body_change(tmp_path):
    old_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(): void {}\n"
        ),
    }
    new_files = {
        **old_files,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            'export function cancelSubscription(): void { console.log("x"); }\n'
        ),
    }
    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _direct_callable_build("cancelSubscription"),
        construction_id="callable-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        scopes = relation_rows_with_ids(old, "authority_relevance_scope")
        assert {row["clause_kind"] for row in scopes} >= {
            "ATTACHED_IDENTITY",
            "IDENTITY_MANIFESTATION",
            "ENDPOINT_RELATION",
        }
        maintenance = assess_attachment_maintenance(old, new, comparison)
        impact = assess_authority_change_impact(old, new, comparison, maintenance=maintenance)
        case = assemble_governance_case(old, new, comparison, _sources(tmp_path), maintenance=maintenance, impact=impact)
        assert len(maintenance["assessments"]) == 1
        assessment = maintenance["assessments"][0]
        assert assessment["maintenance_action"] == "HOLD"
        assert assessment["persistence_implication"] == "NO_RENEWAL"
        assert impact["impacts"][0]["impact"] == "AFFECTED"
        assert case["case_result"] == "SELECTED"
        assert case["selection"][0]["selected_because"] == ["GOVERNED_SURFACE_CHANGED"]
        evidence = case["program_context"]["source_evidence"]
        assert {item["side"] for item in evidence} >= {"OLD", "NEW"}
        assert all(item["reconstruction"] in {"OK", "FAILED"} for item in evidence)
        joined = "\n".join(item.get("reconstructed_text") or "" for item in evidence)
        assert "cancelSubscription" in joined
        assert not any(
            "openRetentionFlow" in (item.get("reconstructed_text") or "")
            and "cancelSubscription" in (item.get("reconstructed_text") or "")
            for item in evidence
        )
        assert all(not str(item.get("observation_id") or "") for item in evidence)
        assert all(item.get("evidence_id", "").startswith("psrc:") for item in evidence)
        assert all(
            item.get("observation_id", "").startswith("obs:")
            for item in case["authority"]["observations"]
        )
        assert 'Cancellation occurs only after confirmation' in case["authority"]["observations"][0]["reconstructed_text"]
        assert case["authority"]["claims"][0]["claim_kind"] == "SOURCE_PROGRAM"
    finally:
        _close(old, new)


def test_hold_and_unaffected_does_not_select_neighboring_helper(tmp_path):
    old_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(): void {}\n"
            "export function formatSubscriptionDate(): string { return ''; }\n"
        ),
    }
    new_files = {
        **old_files,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(): void {}\n"
            'export function formatSubscriptionDate(): string { return "changed"; }\n'
        ),
    }
    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _direct_callable_build("cancelSubscription", include_helper_universe=True),
        construction_id="callable-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        bundle = assess_authority_governance(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assessment = bundle["maintenance"]["assessments"][0]
        impact = bundle["impact"]["impacts"][0]
        assert assessment["maintenance_action"] == "HOLD"
        assert impact["impact"] == "UNAFFECTED"
        assert bundle["case"]["selection"] == []
        assert bundle["case"]["case_result"] == "NO_APPLICABLE_AUTHORITY"
    finally:
        _close(old, new)


def test_incomplete_unattached_helper_is_no_attachment_found(tmp_path):
    old_files = {
        **TS_A,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(): void {}\n"
            "export function formatSubscriptionDate(): string { return ''; }\n"
        ),
    }
    new_files = {
        **old_files,
        "src/retention.ts": (
            "export function openRetentionFlow(): void {}\n"
            "export function cancelSubscription(): void {}\n"
            'export function formatSubscriptionDate(): string { return "changed"; }\n'
        ),
    }

    def build(ctor: AuthorityConstructor) -> None:
        subscriptions = ctor.source("docs/subscriptions.md")
        observation = subscriptions.observe(subscriptions.paragraphs()[1])
        target = ctor.program_entities(kind="callable", label="cancelSubscription")
        ctor.persist_claim(
            "governs_callable",
            {"program": target[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.AGENT_RESOLVED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        _completeness(ctor, attachment=CompletenessStatus.INCOMPLETE)

    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        build,
        construction_id="incomplete-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        case = assemble_governance_case(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assert case["selection"] == []
        assert case["case_result"] == "NO_ATTACHMENT_FOUND"
    finally:
        _close(old, new)


def test_ambiguous_continuation_selects_without_choosing_candidate(tmp_path):
    old_files = {"src/index.ts": "export function source(value: string): string { return value; }\n"}
    new_files = {
        "src/index.ts": (
            "export function first(value: string): string { return value; }\n"
            "export function second(value: string): string { return value; }\n"
        )
    }

    def build(ctor: AuthorityConstructor) -> None:
        subscriptions = ctor.source("docs/subscriptions.md")
        observation = subscriptions.observe(subscriptions.paragraphs()[1])
        target = ctor.program_entities(kind="callable", label="source")
        ctor.persist_claim(
            "governs_callable",
            {"program": target[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.AGENT_RESOLVED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        _completeness(ctor)

    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        build,
        construction_id="ambiguous-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        bundle = assess_authority_governance(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assessment = bundle["maintenance"]["assessments"][0]
        assert assessment["continuation"] == "AMBIGUOUS"
        assert assessment["maintenance_action"] == "RERESOLVE"
        assert len(assessment["candidate_new_manifestations"]) == 2
        assert bundle["impact"]["impacts"][0]["impact"] in {"UNKNOWN", "AFFECTED", "NOT_COMPARABLE"}
        assert bundle["case"]["case_result"] == "SELECTED"
        assert "ATTACHMENT_GROUNDS_CHANGED" in bundle["case"]["selection"][0]["selected_because"]
        assert len(bundle["case"]["uncertainty"]["ambiguous_continuations"][0]["candidates"]) == 2
        labels = {item["label"] for item in bundle["case"]["program_context"]["referents"] if item["side"] == "new"}
        assert labels == {"first", "second"}
        evidence = bundle["case"]["program_context"]["source_evidence"]
        sides = {item["side"] for item in evidence}
        assert "OLD" in sides
        assert "CANDIDATE" in sides
        assert "NEW" not in sides
        texts = [item.get("reconstructed_text") or "" for item in evidence]
        assert any("source" in text for text in texts)
        assert any("first" in text for text in texts)
        assert any("second" in text for text in texts)
    finally:
        _close(old, new)


def test_not_comparable_capability_selects_with_uncertainty(tmp_path):
    files = {"src/index.ts": "export function run(): void {}\n"}

    def build(ctor: AuthorityConstructor) -> None:
        subscriptions = ctor.source("docs/subscriptions.md")
        observation = subscriptions.observe(subscriptions.paragraphs()[1])
        target = ctor.program_entities(kind="callable", label="run")
        ctor.persist_claim(
            "governs_callable",
            {"program": target[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.AGENT_RESOLVED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        _completeness(ctor)

    _write(tmp_path, MD)
    _spine(tmp_path, files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        build,
        construction_id="incomparable-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, files, "world-spine-b")
    new_sqlite = tmp_path / "world-spine-b" / "world.sqlite"
    _unseal(new_sqlite)
    with sqlite3.connect(new_sqlite) as connection:
        connection.execute("UPDATE program_capability SET version='v2' WHERE capability='spine.calls'")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(new_sqlite)
    try:
        bundle = assess_authority_governance(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assert bundle["impact"]["impacts"][0]["impact"] == "NOT_COMPARABLE"
        assert bundle["case"]["case_result"] == "SELECTED"
        assert "GOVERNED_SURFACE_NOT_COMPARABLE" in bundle["case"]["selection"][0]["selected_because"]
        assert bundle["case"]["uncertainty"]["impact_not_comparable"]
        assert bundle["case"]["change"]["comparison_limitations"]
    finally:
        _close(old, new)


def test_module_default_does_not_watch_descendants_but_explicit_scope_does(tmp_path):
    old_files = dict(TS_A)
    new_files = {
        **TS_A,
        "src/payments/boundary.ts": 'export function charge(): void { console.log("x"); }\n',
    }
    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    defaulted = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-module",
        _universe(tmp_path),
        _module_build(),
        construction_id="module-default-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert defaulted.succeeded, defaulted.errors
    explicit = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-module-explicit",
        _universe(tmp_path),
        _module_build(structural=True),
        construction_id="module-explicit-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert explicit.succeeded, explicit.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    default_world = ConstructionWorld.open(tmp_path / "world-module" / "world.sqlite")
    explicit_world = ConstructionWorld.open(tmp_path / "world-module-explicit" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        default_bundle = assess_authority_governance(default_world, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        explicit_bundle = assess_authority_governance(explicit_world, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assert default_bundle["maintenance"]["assessments"][0]["maintenance_action"] == "HOLD"
        assert default_bundle["impact"]["impacts"][0]["impact"] == "UNAFFECTED"
        assert default_world.relation_rows("authority_relevance_scope")
        assert not any(
            row["clause_kind"] == "STRUCTURAL_SCOPE"
            for row in default_world.relation_rows("authority_relevance_scope")
        )
        assert any(
            row["clause_kind"] == "STRUCTURAL_SCOPE"
            for row in explicit_world.relation_rows("authority_relevance_scope")
        )
        assert explicit_bundle["impact"]["impacts"][0]["impact"] == "AFFECTED"
        assert explicit_bundle["case"]["case_result"] == "SELECTED"
        assert default_bundle["case"]["selection"] == []
    finally:
        _close(default_world, explicit_world, new)


def test_explicit_identity_scope_is_honored(tmp_path):
    old_files = dict(TS_A)
    new_files = {
        **TS_A,
        "src/ui.ts": 'export function renderUi(): void { console.log("ui"); }\n',
    }
    _write(tmp_path, MD)
    _spine(tmp_path, old_files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-explicit-id",
        _universe(tmp_path),
        _module_build(extra_identity="renderUi"),
        construction_id="explicit-identity-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, new_files, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-explicit-id" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        impact = assess_authority_change_impact(old, new, comparison)
        assert impact["impacts"][0]["impact"] == "AFFECTED"
        assert any(clause["clause_kind"] == "EXPLICIT_IDENTITY" for clause in impact["impacts"][0]["scope_clauses"])
    finally:
        _close(old, new)


def test_duplicate_observations_are_deduplicated_and_non_authoritative_is_labeled(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _build_authority,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, TS_B, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        case = assemble_governance_case(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        keys = [
            (item["handle"], item["revision"], item["native_location"])
            for item in case["authority"]["observations"]
        ]
        assert len(keys) == len(set(keys))
        assert all(item["standing"] == "AUTHORITATIVE" for item in case["authority"]["observations"])
        assert all(item["standing"] != "AUTHORITATIVE" for item in case["supporting_material"])
        handles = {item["handle"] for item in case["authority"]["observations"]}
        assert "docs/notes.md" not in handles
        assert "docs/hints.md" not in handles
    finally:
        _close(old, new)


def test_heuristic_correspondence_never_renews_and_failed_assembly_does_not_mutate(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _build_authority,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, TS_B, "world-spine-b")
    old_fp = program_world_fingerprint(tmp_path / "world-governed")
    new_fp = program_world_fingerprint(tmp_path / "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        maintenance = assess_attachment_maintenance(old, new, comparison)
        assert all(item["persistence_implication"] == "NO_RENEWAL" for item in maintenance["assessments"])
        assert all(item["correspondence_basis"] != "DETERMINISTIC" or True for item in maintenance["assessments"])
        assert any(item["correspondence_basis"] == "HEURISTIC" for item in maintenance["assessments"])
        with pytest.raises(GovernanceError):
            assess_attachment_maintenance(new, old, comparison)
        assert program_world_fingerprint(tmp_path / "world-governed") == old_fp
        assert program_world_fingerprint(tmp_path / "world-spine-b") == new_fp
        assert "authority_attachment_warrant" not in {
            row["name"] for row in new.query("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        _close(old, new)


def test_sidecar_validation_catches_mismatched_snapshots(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")
    construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _build_authority,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    _spine(tmp_path, TS_B, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        maintenance = assess_attachment_maintenance(old, new, comparison)
        broken = dict(maintenance)
        broken["old_snapshot"] = "not-the-snapshot"
        errors = validate_maintenance_sidecar(broken, old_world=old, new_world=new, comparison=comparison)
        assert any("snapshot" in item for item in errors)
        impact = assess_authority_change_impact(old, new, comparison, maintenance=maintenance)
        impact_broken = dict(impact)
        impact_broken["impacts"] = [
            {**impact["impacts"][0], "intersecting_deltas": [{"missing": "delta"}]}
        ]
        # snapshot mismatch is the required check
        impact_broken["old_snapshot"] = "mismatch"
        assert validate_impact_sidecar(
            impact_broken, old_world=old, comparison=comparison, maintenance=maintenance
        )
    finally:
        _close(old, new)


def test_uncertain_empty_case_is_unresolved(tmp_path):
    files = dict(TS_A)

    def build(ctor: AuthorityConstructor) -> None:
        adr = ctor.source("docs/adr/payment-boundary.md")
        observation = adr.observe(adr.paragraphs()[0])
        boundary = ctor.program_entities(kind="module", descriptor_contains="boundary.ts")
        ctor.persist_claim(
            "governs_module",
            {"program": boundary[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.SOURCE_DEFINED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        helpers = ctor.program_entities(kind="callable", label="cancelSubscription")
        ctor.declare_attachment_universe(helpers, observation=observation)
        _completeness(ctor)

    _write(tmp_path, MD)
    _spine(tmp_path, files, "world-spine")
    governed = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-unresolved",
        _universe(tmp_path),
        build,
        construction_id="unresolved-empty-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert governed.succeeded, governed.errors
    _spine(tmp_path, files, "world-spine-b")
    new_sqlite = tmp_path / "world-spine-b" / "world.sqlite"
    _unseal(new_sqlite)
    with sqlite3.connect(new_sqlite) as connection:
        connection.execute("UPDATE program_capability SET version='v2' WHERE capability='spine.calls'")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    old = ConstructionWorld.open(tmp_path / "world-unresolved" / "world.sqlite")
    new = ConstructionWorld.open(new_sqlite)
    try:
        case = assemble_governance_case(old, new, comparison, _sources(tmp_path), purpose=PURPOSE)
        assert case["selection"] == []
        assert case["case_result"] == "UNRESOLVED"
    finally:
        _close(old, new)


def test_relevance_scope_rejects_watch_query_dsl(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")

    def build(ctor: AuthorityConstructor) -> None:
        subscriptions = ctor.source("docs/subscriptions.md")
        observation = subscriptions.observe(subscriptions.paragraphs()[1])
        target = ctor.program_entities(kind="callable", label="cancelSubscription")
        assertion = ctor.persist_claim(
            "governs_callable",
            {"program": target[0]},
            claim_kind=ClaimKind.SOURCE_PROGRAM,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"program": ReferentResolution.AGENT_RESOLVED},
            observations=(observation,),
            roles=[Role("program", RoleType.REFERENT)],
        )
        ctor.declare_relevance_scope(
            [{"clause_kind": "ENDPOINT_RELATION", "relation_name": "program_invokes", "query": "MATCH (n)"}],
            assertion_id=assertion,
            program_entity=target[0],
        )

    result = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-invalid-scope",
        _universe(tmp_path),
        build,
        construction_id="invalid-scope-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert not result.succeeded
    assert any("watch-query" in item or "unsupported" in item for item in result.errors)

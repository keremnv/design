from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ontology_author.authority import (
    AdequacyOutcome,
    AuthorityConstructor,
    AuthorityUniverse,
    ClaimKind,
    CompletenessScope,
    DeclaredSource,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    UnresolvedKind,
    construct_authority_world,
    load_receipt,
    observations_for_assertion,
    program_world_fingerprint,
    recover_authority_for_delta,
)
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.program_spine import TypeScriptBoundary, build_typescript_spine, compare_program_spines
from ontology_author.world.core.model import CompletenessStatus, Role, RoleType
from ontology_author.world.runtime.world import ConstructionWorld


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TYPESCRIPT_MODULE = REPOSITORY_ROOT / "frontend" / "node_modules" / "typescript"
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not TYPESCRIPT_MODULE.exists(),
    reason="the TypeScript compiler API dependency is not installed",
)

PURPOSE = "cancellation-flow-v1"
PROFILE = "authority-construction-v0"

TS_A = {
    "src/retention.ts": (
        "export function openRetentionFlow(): void {}\n"
        "export function cancelSubscription(): void {}\n"
    ),
    "src/subscription-page.ts": (
        'import { openRetentionFlow } from "./retention";\n'
        "export function SubscriptionPage(): void { openRetentionFlow(); }\n"
    ),
    "src/final-cancellation.ts": (
        'import { cancelSubscription } from "./retention";\n'
        "export function FinalCancellation(): void { cancelSubscription(); }\n"
    ),
    "src/payments/boundary.ts": "export function charge(): void {}\n",
    "src/ui.ts": "export function renderUi(): void {}\n",
    "src/checkout.ts": (
        "export function submitPrimary(): void {}\n"
        "export function submitSecondary(): void {}\n"
    ),
}
TS_B = {
    **TS_A,
    "src/subscription-page.ts": (
        'import { cancelSubscription } from "./retention";\n'
        "export function SubscriptionPage(): void { cancelSubscription(); }\n"
    ),
}

MD = {
    "docs/subscriptions.md": (
        'The initial "Cancel subscription" action enters the retention flow.\n'
        "\n"
        "Cancellation occurs only after confirmation on the final\n"
        "cancellation screen.\n"
    ),
    "docs/adr/payment-boundary.md": (
        "## Payment boundary\n"
        "\n"
        "`src/payments/boundary.ts` MUST NOT import `src/ui.ts`.\n"
    ),
    "docs/ambiguous.md": "The primary checkout button must confirm the total before submitting.\n",
    "docs/notes.md": "Editorial note about cancellation copy.\n",
    "docs/hints.md": "Parser hint: Cancel maps to openRetentionFlow.\n",
}


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")


def _tsconfig(root: Path) -> None:
    (root / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "moduleResolution": "node",
                    "strict": True,
                },
                "include": ["src/**/*.ts", "src/**/*.tsx"],
            }
        ),
        encoding="utf-8",
    )


def _spine(root: Path, files: dict[str, str], output: str):
    _write(root, files)
    _tsconfig(root)
    boundary = TypeScriptBoundary(
        workspace_roots=("src",),
        projects=("tsconfig.json",),
        package_roots=("src",),
    )
    result = build_typescript_spine(root, root / output, boundary=boundary)
    assert result.succeeded, result.errors
    return result


def _universe(root: Path) -> AuthorityUniverse:
    return AuthorityUniverse(
        universe_id="checkout-docs-v0",
        workspace=root,
        sources=(
            DeclaredSource("docs/subscriptions.md", root / "docs/subscriptions.md", SourceStanding.AUTHORITATIVE),
            DeclaredSource("docs/adr/payment-boundary.md", root / "docs/adr/payment-boundary.md", SourceStanding.AUTHORITATIVE),
            DeclaredSource("docs/ambiguous.md", root / "docs/ambiguous.md", SourceStanding.AUTHORITATIVE),
            DeclaredSource("docs/notes.md", root / "docs/notes.md", SourceStanding.AVAILABLE),
            DeclaredSource("docs/hints.md", root / "docs/hints.md", SourceStanding.ANALYSIS_SUPPORT),
        ),
    )


def _build_authority(ctor: AuthorityConstructor) -> None:
    ctor.note_exploration(action="grep", target="Cancel", detail="search authoritative checkout docs")
    ctor.note_exploration(action="inspect", target="SubscriptionPage", detail="program spine call sites")
    subscriptions = ctor.source("docs/subscriptions.md")
    adr = ctor.source("docs/adr/payment-boundary.md")
    ambiguous = ctor.source("docs/ambiguous.md")
    e1 = subscriptions.observe(subscriptions.paragraphs()[0])
    e2 = subscriptions.observe(subscriptions.paragraphs()[1])
    e3 = adr.observe(adr.paragraphs()[0])
    e4 = ambiguous.observe(ambiguous.paragraphs()[0])

    ctor.create_semantic_referent(
        "semantic:CancellationEntryAction",
        label="CancellationEntryAction",
        observations=(e1,),
    )
    ctor.create_semantic_referent(
        "semantic:RetentionFlow",
        label="RetentionFlow",
        observations=(e1,),
    )
    ref = Role("action", RoleType.REFERENT)
    flow = Role("flow", RoleType.REFERENT)
    ctor.persist_claim(
        "enters_flow",
        {"action": "semantic:CancellationEntryAction", "flow": "semantic:RetentionFlow"},
        claim_kind=ClaimKind.SOURCE_PROPOSITION,
        support=RelationSupport.SOURCE_EXPLICIT,
        endpoint_resolution={
            "action": ReferentResolution.AGENT_RESOLVED,
            "flow": ReferentResolution.AGENT_RESOLVED,
        },
        observations=(e1,),
        roles=[ref, flow],
    )
    initial = ctor.call_site_invoking("openRetentionFlow")
    ctor.persist_claim(
        "realized_by",
        {"action": "semantic:CancellationEntryAction", "program": initial},
        claim_kind=ClaimKind.SEMANTIC_PROGRAM,
        support=RelationSupport.CROSS_EVIDENCE_INFERRED,
        endpoint_resolution={
            "action": ReferentResolution.AGENT_RESOLVED,
            "program": ReferentResolution.AGENT_RESOLVED,
        },
        observations=(e1,),
        roles=[Role("action", RoleType.REFERENT), Role("program", RoleType.REFERENT)],
    )
    final = ctor.call_site_invoking("cancelSubscription")
    ctor.persist_claim(
        "cancellation_requires_prior",
        {"action": "semantic:CancellationEntryAction", "confirmation": final},
        claim_kind=ClaimKind.SOURCE_PROPOSITION,
        support=RelationSupport.SOURCE_EXPLICIT,
        endpoint_resolution={
            "action": ReferentResolution.AGENT_RESOLVED,
            "confirmation": ReferentResolution.AGENT_RESOLVED,
        },
        observations=(e2,),
        roles=[Role("action", RoleType.REFERENT), Role("confirmation", RoleType.REFERENT)],
    )
    boundary = ctor.program_entities(kind="module", descriptor_contains="boundary.ts")
    ui = ctor.program_entities(kind="module", descriptor_contains="ui.ts")
    assert len(boundary) == 1 and len(ui) == 1
    ctor.persist_claim(
        "forbids_import",
        {"importer": boundary[0], "imported": ui[0]},
        claim_kind=ClaimKind.SOURCE_PROGRAM,
        support=RelationSupport.SOURCE_EXPLICIT,
        endpoint_resolution={
            "importer": ReferentResolution.SOURCE_DEFINED,
            "imported": ReferentResolution.SOURCE_DEFINED,
        },
        observations=(e3,),
        roles=[Role("importer", RoleType.REFERENT), Role("imported", RoleType.REFERENT)],
    )
    candidates = ctor.program_entities(kind="callable", label="submitPrimary") + ctor.program_entities(
        kind="callable", label="submitSecondary"
    )
    ctor.persist_unresolved(
        "checkout-primary-button",
        kind=UnresolvedKind.AMBIGUOUS_REFERENT,
        observation=e4,
        detail="source treats one checkout button; two callables remain",
        candidates=candidates,
    )
    ctor.persist_unresolved(
        "component-usage-missing",
        kind=UnresolvedKind.SPINE_SURFACE_MISSING,
        observation=e4,
        detail="program spine does not emit component-usage identity",
    )
    ctor.record_adequacy(
        "localize-primary-checkout-button",
        AdequacyOutcome.INADEQUATE,
        detail="construction valid; spine lacks component-usage surface",
        observation=e4,
    )
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
        status=CompletenessStatus.COMPLETE,
        basis=(
            "attachment construction COMPLETE for explicitly identified checkout-action "
            f"requirements over the declared checkout program universe under constructor "
            f"profile {PROFILE} and purpose {PURPOSE}"
        ),
    )


def _governed(tmp_path: Path):
    _write(tmp_path, MD)
    spine = _spine(tmp_path, TS_A, "world-spine")
    result = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        _build_authority,
        construction_id="checkout-authority-v0",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert result.succeeded, result.errors
    world = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    return spine, result, world


def test_declared_universe_and_standing_are_explicit(tmp_path):
    _, _, world = _governed(tmp_path)
    try:
        rows = {row["source_handle"]: row for row in world.relation_rows("authority_source")}
        assert set(rows) == {
            "docs/subscriptions.md",
            "docs/adr/payment-boundary.md",
            "docs/ambiguous.md",
            "docs/notes.md",
            "docs/hints.md",
        }
        assert rows["docs/subscriptions.md"]["standing"] == "AUTHORITATIVE"
        assert rows["docs/notes.md"]["standing"] == "AVAILABLE"
        assert rows["docs/hints.md"]["standing"] == "ANALYSIS_SUPPORT"
        assert rows["docs/subscriptions.md"]["content_revision"].startswith("sha256:")
        referent_ids = {row["id"] for row in world.query("SELECT id FROM _world_referents")}
        assert "docs/subscriptions.md" not in referent_ids
    finally:
        world.close()


def test_markdown_regions_are_evidence_not_referents(tmp_path):
    _, _, world = _governed(tmp_path)
    try:
        labels = [row["label"] for row in world.query("SELECT label FROM _world_referents")]
        assert "Payment boundary" not in labels
        semantic = {row["entity"] for row in world.relation_rows("semantic_entity")}
        assert semantic == {"semantic:CancellationEntryAction", "semantic:RetentionFlow"}
        assert "semantic:PaymentBoundary" not in semantic
    finally:
        world.close()


def test_semantic_and_direct_attachments_and_grounding(tmp_path):
    _, result, world = _governed(tmp_path)
    try:
        claims = {row["relation_name"]: row for row in world.relation_rows("authority_claim")}
        assert claims["enters_flow"]["claim_kind"] == "SOURCE_PROPOSITION"
        assert claims["realized_by"]["claim_kind"] == "SEMANTIC_PROGRAM"
        assert claims["forbids_import"]["claim_kind"] == "SOURCE_PROGRAM"
        extra = {}
        for base in world.warrant_for_assertion(claims["enters_flow"]["assertion_id"])["bases"]:
            detail = base.get("detail") or {}
            if isinstance(detail, dict) and isinstance(detail.get("extra"), dict):
                extra = detail["extra"]
                break
        assert extra["relation_support"] == "SOURCE_EXPLICIT"
        assert extra["endpoint_resolution"]["action"] == "AGENT_RESOLVED"
        assert extra["endpoint_resolution"]["flow"] == "AGENT_RESOLVED"
        resolutions = {
            (row["assertion_id"], row["role"]): row["resolution"]
            for row in world.relation_rows("authority_endpoint_resolution")
        }
        assert resolutions[(claims["forbids_import"]["assertion_id"], "importer")] == "SOURCE_DEFINED"
        observations = observations_for_assertion(world, claims["enters_flow"]["assertion_id"])
        source = MarkdownSource(tmp_path / "docs/subscriptions.md", handle="docs/subscriptions.md")
        assert any(
            source.reconstruct(item).startswith('The initial "Cancel subscription" action')
            for item in observations
        )
        assert "Cancel subscription" in source.reconstruct(source.paragraphs()[0])
        warrants = world.relation_rows("authority_attachment_warrant")
        assert warrants
        assert all(row["program_snapshot_id"] == result.snapshot_id for row in warrants)
        assert all(json.loads(row["structural_context"]) for row in warrants)
        unresolved = {row["kind"] for row in world.relation_rows("authority_unresolved")}
        assert "AMBIGUOUS_REFERENT" in unresolved
        candidates = [row["candidate"] for row in world.relation_rows("authority_unresolved_candidate")]
        certain = {
            row["referent"]
            for row in world.relation_rows("authority_endpoint_resolution")
            if row["assertion_id"] in {item["assertion_id"] for item in world.relation_rows("authority_claim") if item["claim_kind"] != "UNRESOLVED_RECORD"}
        }
        assert not set(candidates) & certain
    finally:
        world.close()


def test_receipt_and_scoped_completeness(tmp_path):
    _, result, world = _governed(tmp_path)
    try:
        receipt = load_receipt(tmp_path / "world-governed" / "authority.construction.receipt.json")
        assert receipt.construction_id == "checkout-authority-v0"
        assert receipt.exploration_provenance
        assert receipt.semantic_referents_created == (
            "semantic:CancellationEntryAction",
            "semantic:RetentionFlow",
        )
        assert receipt.direct_source_program_links == 1
        assert receipt.semantic_program_links == 1
        assert "authority_understood" not in receipt.to_dict()
        scopes = {item["scope"]: item for item in receipt.completeness_references}
        assert set(scopes) == {"ADDRESSABILITY", "CONSTRUCTION", "ATTACHMENT"}
        assert PURPOSE in scopes["ATTACHMENT"]["basis"]
        assert PROFILE in scopes["ATTACHMENT"]["basis"]
        paragraphs = MarkdownSource(tmp_path / "docs/subscriptions.md", handle="docs/subscriptions.md").paragraphs()
        assert len(paragraphs) >= 2
        assert receipt.source_regions_examined["count"] < 50
        assert result.receipt is not None
        adequacy = {row["outcome"] for row in world.relation_rows("authority_adequacy")}
        assert "INADEQUATE" in adequacy
        kernel = world.latest_completeness("authority_attachment_coverage")
        assert kernel is not None
        assert kernel["status"] == "COMPLETE"
        assert kernel["universe_relation"] == "authority_attachment_scope"
    finally:
        world.close()


def test_non_authoritative_source_cannot_ground_governing_claim(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")
    fingerprint = program_world_fingerprint(tmp_path / "world-spine")

    def build(ctor: AuthorityConstructor) -> None:
        notes = ctor.source("docs/notes.md")
        observation = notes.observe(notes.paragraphs()[0])
        ctor.persist_claim(
            "enters_flow",
            {"action": "semantic:CancellationEntryAction", "flow": "semantic:RetentionFlow"},
            claim_kind=ClaimKind.SOURCE_PROPOSITION,
            support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={
                "action": ReferentResolution.AGENT_RESOLVED,
                "flow": ReferentResolution.AGENT_RESOLVED,
            },
            observations=(observation,),
            roles=[Role("action", RoleType.REFERENT), Role("flow", RoleType.REFERENT)],
        )

    result = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-governed",
        _universe(tmp_path),
        build,
        construction_id="invalid-standing",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert not result.succeeded
    assert any("AVAILABLE" in item or "cannot ground" in item for item in result.errors)
    assert program_world_fingerprint(tmp_path / "world-spine") == fingerprint
    assert not (tmp_path / "world-governed").exists()


def test_failed_construction_does_not_require_semantic_referent_for_failure(tmp_path):
    _write(tmp_path, MD)
    _spine(tmp_path, TS_A, "world-spine")

    def build(ctor: AuthorityConstructor) -> None:
        notes = ctor.source("docs/notes.md")
        ctor.persist_unresolved(
            "standing-gap",
            kind=UnresolvedKind.STANDING_INSUFFICIENT,
            observation=notes.observe(notes.paragraphs()[0]),
            detail="editorial note is not governing authority",
        )
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
            status=CompletenessStatus.COMPLETE,
            basis=(
                "attachment construction COMPLETE for explicitly identified checkout-action "
                f"requirements over the declared checkout program universe under constructor "
                f"profile {PROFILE} and purpose {PURPOSE}"
            ),
        )

    result = construct_authority_world(
        tmp_path / "world-spine",
        tmp_path / "world-notes",
        _universe(tmp_path),
        build,
        construction_id="standing-unresolved",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert result.succeeded, result.errors
    world = ConstructionWorld.open(tmp_path / "world-notes" / "world.sqlite")
    try:
        kinds = {row["kind"] for row in world.relation_rows("authority_unresolved")}
        assert kinds == {"STANDING_INSUFFICIENT"}
        assert world.relation_rows("semantic_entity") == []
    finally:
        world.close()


def test_program_delta_recovers_exact_markdown_without_migrating_heuristic_continuation(tmp_path):
    _write(tmp_path, MD)
    old = _spine(tmp_path, TS_A, "world-spine")
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
    new = _spine(tmp_path, TS_B, "world-spine-b")
    comparison = compare_program_spines(tmp_path / "world-spine", tmp_path / "world-spine-b")
    retargets = comparison.delta.relations["program_invokes"]["retargeted"]
    assert retargets
    world = ConstructionWorld.open(tmp_path / "world-governed" / "world.sqlite")
    new_world = ConstructionWorld.open(tmp_path / "world-spine-b" / "world.sqlite")
    try:
        sources = {
            "docs/subscriptions.md": MarkdownSource(tmp_path / "docs/subscriptions.md", handle="docs/subscriptions.md")
        }
        recovered = recover_authority_for_delta(
            world,
            comparison.delta,
            sources,
            comparison=comparison,
        )
        assert recovered
        assert any(
            'The initial "Cancel subscription" action enters the retention flow.' in item.text
            for item in recovered
        )
        assert all(item.migrated is False for item in recovered)
        assert any(item.correspondence_continuity == "CONTINUED" and item.correspondence_basis == "HEURISTIC" for item in recovered)
        tables = {row["name"] for row in new_world.query("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "authority_source" not in tables
        assert "authority_attachment_warrant" not in tables
        old_entities = {row["program_entity"] for row in world.relation_rows("authority_attachment_warrant")}
        new_ids = {row["entity"] for row in new_world.relation_rows("program_entity")}
        assert old_entities.isdisjoint(new_ids)
        continued = [
            item for item in comparison.correspondences
            if item.old_entity in old_entities and item.continuity == "CONTINUED"
        ]
        assert continued
        assert all(item.basis_class == "HEURISTIC" for item in continued)
        assert all(item.old_entity != item.new_entity for item in continued)
        assert all(item.new_entity not in old_entities for item in continued)
        assert old.snapshot_id == governed.snapshot_id
        assert new.snapshot_id != old.snapshot_id
    finally:
        world.close()
        new_world.close()


def test_authority_publication_requires_a_fresh_address(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write(workspace, MD)
    spine = _spine(workspace, TS_A, "program-world")
    assert spine.world_dir is not None
    output = tmp_path / "authority-world"
    first = construct_authority_world(
        spine.world_dir,
        output,
        _universe(workspace),
        _build_authority,
        construction_id="fresh-address-first",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert first.succeeded, first.errors
    before = (output / "world.sqlite").read_bytes()
    baseline = program_world_fingerprint(spine.world_dir)

    second = construct_authority_world(
        spine.world_dir,
        output,
        _universe(workspace),
        _build_authority,
        construction_id="fresh-address-second",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert not second.succeeded
    assert "already exists" in " ".join(second.errors)
    assert (output / "world.sqlite").read_bytes() == before
    assert program_world_fingerprint(spine.world_dir) == baseline

def test_authority_rejects_dangling_symlink_publication_address(tmp_path):
    workspace = tmp_path / "workspace-dangling"
    workspace.mkdir()
    _write(workspace, MD)
    spine = _spine(workspace, TS_A, "program-world")
    assert spine.world_dir is not None
    output = tmp_path / "authority-dangling"
    output.symlink_to(tmp_path / "missing-authority", target_is_directory=True)

    result = construct_authority_world(
        spine.world_dir,
        output,
        _universe(workspace),
        _build_authority,
        construction_id="dangling-address",
        purpose=PURPOSE,
        profile=PROFILE,
    )

    assert not result.succeeded
    assert "already exists" in " ".join(result.errors)
    assert output.is_symlink()


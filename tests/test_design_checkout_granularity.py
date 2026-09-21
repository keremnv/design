"""Design-checkout granularity pressure test.

Binds one existing design concern (the order-summary availability subject
``semantic:order_summary``) to the narrowest existing program-spine referent
(the ``Checkout`` callable) through the existing generic
``PROGRAM_REALIZATION`` machinery, then runs three controls:

A. a material edit inside the order-summary region (must surface);
B. an unrelated same-file edit inside the payment-entry region
   (must stay PRESERVED for useful locality);
C. a deliberately coarser binding to the enclosing source unit under the
   same unrelated edit (measures coarse-addressability noise).

Plus two diagnostics: a cross-file addition (isolates the file-digest
mechanism) and the persisted basis minus its manifestation dependency
(measures what the non-manifestation kinds can see inside a callable).

This is an experiment, not productization: it reuses
``build_semantic_construction_catalog``,
``compile_semantic_candidate_draft``, ``admit_semantic_candidate``,
``materialize_semantic_commitment_revision``,
``maintain_semantic_commitment`` and
``select_affected_semantic_commitments`` unchanged. No design-specific
impact logic, no UI/component spine capability, no verdict.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

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
from ontology_author.authority.evaluate import snapshot_id
from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.evidence.program_source import (
    program_source_observations,
    source_evidence_record,
)
from ontology_author.program_spine import (
    TypeScriptBoundary,
    build_typescript_spine,
    compare_program_spines,
)
from ontology_author.semantic_binding import (
    ConstructionObligation,
    EvidenceClass,
    admit_semantic_candidate,
    build_semantic_construction_catalog,
    compile_semantic_candidate_draft,
    maintain_semantic_commitment,
    materialize_semantic_commitment_revision,
    select_affected_semantic_commitments,
)
from ontology_author.semantic_binding.admission import PROGRAM_REALIZATION_RELATION
from ontology_author.world.core.model import CompletenessStatus, Role, RoleType
from ontology_author.world.runtime.world import ConstructionWorld

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None
    or not (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "node_modules"
        / "typescript"
    ).exists(),
    reason="the TypeScript compiler API dependency is not installed",
)

_FIXTURE = Path(__file__).resolve().parents[1] / "profiles" / "design_checkout" / "fixture"
PURPOSE = "design-checkout-v1"
PROFILE = "design-checkout-authority-v0"
SEMANTIC_SUBJECT = "semantic:order_summary"
# Single-line substring of the availability requirement paragraph; the case
# reconstructs Markdown with its original newlines.
REQUIREMENT_TEXT = "must remain available without losing the payment task"
_VERDICT_TOKENS = ("violat", "broken", "noncompliant", "unauthorized")

BASELINE_TSX = (_FIXTURE / "Checkout.tsx").read_text(encoding="utf-8")
REQUIREMENTS = (_FIXTURE / "checkout-requirements.md").read_text(encoding="utf-8")

# Control A: material edit inside the bound design object's region. The
# order-total element is removed from the order-summary region.
RELEVANT_TSX = BASELINE_TSX.replace(
    '          <span data-field="order-total">$42.00</span>\n', ""
)
assert RELEVANT_TSX != BASELINE_TSX
# Control B: real program change in the same file but inside the
# payment-entry region, which the order-summary concern does not govern.
UNRELATED_TSX = BASELINE_TSX.replace("Place order", "Submit order")
assert UNRELATED_TSX != BASELINE_TSX
# Ambient JSX types, as any real checkout project carries. Without them the
# extractor reports JSX diagnostics and the spine capabilities stay
# INCOMPLETE, which would confound the delta buckets under test.
JSX_RUNTIME_DTS = '''declare namespace JSX {
  interface IntrinsicElements {
    [element: string]: any;
  }
}
declare module "react/jsx-runtime" {
  export function jsx(type: any, props: any, key?: any): any;
  export function jsxs(type: any, props: any, key?: any): any;
  export const Fragment: any;
}
'''


def _checkout_files(tsx: str) -> dict[str, str]:
    return {"src/Checkout.tsx": tsx, "src/jsx-runtime.d.ts": JSX_RUNTIME_DTS}


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _spine(root: Path, files: dict[str, str], output: str):
    _write(root, files)
    (root / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "esnext",
                    "moduleResolution": "bundler",
                    "jsx": "react-jsx",
                    "strict": True,
                },
                "include": ["src/**/*.ts", "src/**/*.tsx"],
            }
        ),
        encoding="utf-8",
    )
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
        universe_id="design-checkout-boundary-fixture-v1",
        workspace=root,
        sources=(
            DeclaredSource(
                "checkout-requirements.md",
                root / "checkout-requirements.md",
                SourceStanding.AUTHORITATIVE,
            ),
        ),
    )


def _sources(root: Path) -> dict[str, MarkdownSource]:
    return {
        "checkout-requirements.md": MarkdownSource(
            root / "checkout-requirements.md", handle="checkout-requirements.md"
        )
    }


def _build_design_authority(ctor) -> None:
    """Attach the existing availability subject at two program granularities.

    The narrow claim binds ``semantic:order_summary`` to the ``Checkout``
    callable, the most precise existing program referent for the
    implementation. The coarse claim binds the same subject to the
    enclosing source unit. Both are grounded in the same requirement
    paragraph; control C compares their selection behavior.
    """

    source = ctor.source("checkout-requirements.md")
    observation = source.observe(source.paragraphs()[0])
    checkout = ctor.program_entities(kind="callable", label="Checkout")
    assert len(checkout) == 1, checkout
    checkout = checkout[0]
    units = ctor.program_entities(
        kind="source_unit", descriptor_contains="src/Checkout.tsx"
    )
    assert len(units) == 1, units
    unit = units[0]
    ctor.create_semantic_referent(
        SEMANTIC_SUBJECT,
        label="Order summary",
        observations=(observation,),
    )
    for relation, entity in (
        ("order_summary_realization", checkout),
        ("order_summary_unit_realization", unit),
    ):
        chain = ctor.structural_context(entity)
        path_rows = [
            {
                "relation": "structural_context",
                "parent": row["parent"],
                "child": row["child"],
            }
            for row in ctor.world.relation_rows("structural_context")
            if row["child"] in chain
        ]
        ctor.persist_claim(
            relation,
            {"subject": SEMANTIC_SUBJECT, "program": entity},
            claim_kind=ClaimKind.SEMANTIC_PROGRAM,
            support=RelationSupport.CROSS_EVIDENCE_INFERRED,
            endpoint_resolution={
                "subject": ReferentResolution.AGENT_RESOLVED,
                "program": ReferentResolution.DETERMINISTIC,
            },
            observations=(observation,),
            roles=[
                Role("subject", RoleType.REFERENT),
                Role("program", RoleType.REFERENT),
            ],
            warrant=[
                {
                    "program_entity": entity,
                    "structural_context": chain,
                    "justifying_program_relations": path_rows,
                    "justifying_resolution_outcomes": [],
                    "relation_support": RelationSupport.CROSS_EVIDENCE_INFERRED.value,
                    "endpoint_resolution": {
                        "program": ReferentResolution.DETERMINISTIC.value
                    },
                }
            ],
        )
    ctor.declare_attachment_universe([checkout, unit], observation=observation)
    ctor.record_completeness(
        scope=CompletenessScope.ADDRESSABILITY,
        universe="authority_source",
        status=CompletenessStatus.COMPLETE,
        basis="the declared checkout-requirements source is reconstructible",
    )
    ctor.record_completeness(
        scope=CompletenessScope.CONSTRUCTION,
        universe="authority_examined",
        status=CompletenessStatus.COMPLETE,
        basis="construction coverage is complete over the requirement paragraph",
    )
    ctor.record_completeness(
        scope=CompletenessScope.ATTACHMENT,
        universe="authority_attachment_scope",
        status=CompletenessStatus.COMPLETE,
        basis=(
            "attachment construction COMPLETE for the declared design "
            f"purpose {PURPOSE} under profile {PROFILE}"
        ),
    )


def _endpoint_kinds(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["entity"]): str(row["kind"])
        for row in world.relation_rows("program_entity_kind")
    }


def _bounded_source(
    old: ConstructionWorld, entity: str, old_snapshot: str
) -> list[dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for observation in program_source_observations(old, entity):
        record = source_evidence_record(
            world=old,
            entity=entity,
            side="OLD",
            snapshot_id=old_snapshot,
            inclusion_reason="DESIGN_SEMANTIC_CONSTRUCTION",
            selected_by=entity,
            observation=observation,
        )
        output[str(record["evidence_id"])] = record
    return [output[key] for key in sorted(output)]


def _dependencies(entity: str, chain: list[str]) -> list[dict[str, Any]]:
    """The declared mechanical basis for one realization binding."""

    # The chain runs module -> ... -> entity; record the final link, which is
    # the binding's own structural attachment.
    parent = chain[-2] if len(chain) >= 2 else entity
    return [
        {"kind": "program_identity", "program_entity": entity},
        {
            "kind": "relation_tuple",
            "recorded": {
                "relation": "structural_context",
                "parent": parent,
                "child": entity,
            },
        },
        {
            "kind": "manifestation_property",
            "program_entity": entity,
            "property": "source_manifestation",
        },
        {
            "kind": "structural_context",
            "program_entity": entity,
            "chain": list(chain),
        },
    ]


def _obligation(
    case: dict[str, Any], obligation_id: str, entity: str
) -> ConstructionObligation:
    authority_refs = tuple(
        str(item["observation_id"])
        for item in case["authority"]["observations"]
        if REQUIREMENT_TEXT in str(item.get("reconstructed_text") or "")
    )
    assert len(authority_refs) == 1, authority_refs
    return ConstructionObligation(
        obligation_id=obligation_id,
        purpose=PURPOSE,
        authority_refs=authority_refs,
        semantic_subject=SEMANTIC_SUBJECT,
        semantic_relation="realized_by",
        question=(
            "Which supplied program manifestation realizes the order-summary "
            "design object of the mobile checkout availability requirement?"
        ),
        program_scope="bounded checkout implementation",
        allowed_program_endpoints=(entity,),
        required_evidence_classes=(
            EvidenceClass.AUTHORITY_GROUNDING.value,
            EvidenceClass.PROGRAM_GROUNDING.value,
            EvidenceClass.MECHANICAL_GROUNDING.value,
        ),
        tuple_shape={"subject": "SEMANTIC", "program": "PROGRAM"},
    )


def _mentions(dependency: dict[str, Any], entity: str) -> bool:
    if dependency.get("program_entity") == entity:
        return True
    recorded = dependency.get("recorded")
    if isinstance(recorded, dict) and entity in {
        recorded.get("parent"),
        recorded.get("child"),
    }:
        return True
    return entity in (dependency.get("chain") or [])


def _draft(
    obligation: ConstructionObligation,
    catalog: dict[str, Any],
    entity: str,
    *,
    own_claim_relation: str,
    other_claim_relation: str,
) -> dict[str, Any]:
    """Select exactly this binding's evidence; never the sibling's."""

    entries = [item for item in catalog.get("entries") or []]
    semantic = [
        str(item["alias"])
        for item in entries
        if item.get("category") == "SEMANTIC_REFERENT"
        and item.get("id") == SEMANTIC_SUBJECT
    ]
    program = [
        str(item["alias"])
        for item in entries
        if item.get("category") == "PROGRAM_ENDPOINT" and item.get("id") == entity
    ]
    assert len(semantic) == 1 and len(program) == 1
    mechanical: list[str] = []
    for item in entries:
        if item.get("category") != "MECHANICAL_FACT":
            continue
        claim = item.get("persisted_claim") or {}
        relation = str(claim.get("relation_name") or "")
        if relation == other_claim_relation:
            continue
        if relation and relation != own_claim_relation:
            continue
        mechanical.append(str(item["alias"]))
    dependencies = [
        str(item["alias"])
        for item in entries
        if item.get("category") == "MAINTENANCE_DEPENDENCY"
        and _mentions(item.get("dependency") or {}, entity)
    ]
    assert dependencies, "binding has no catalogued maintenance basis"
    return {
        "obligation_id": obligation.obligation_id,
        "claim_kind": "SEMANTIC_PROGRAM",
        "relation_name": obligation.semantic_relation,
        "semantic_endpoint_aliases": semantic,
        "program_endpoint_aliases": program,
        "polarity": "POSITIVE",
        "support_kind": "CROSS_EVIDENCE_INFERRED",
        "authority_evidence_aliases": [
            str(item["alias"])
            for item in entries
            if item.get("category") == "AUTHORITATIVE_EVIDENCE"
        ],
        "program_source_evidence_aliases": [
            str(item["alias"])
            for item in entries
            if item.get("category") == "PROGRAM_SOURCE"
            and str((item.get("pointer") or {}).get("program_entity") or "") == entity
        ],
        "mechanical_evidence_aliases": mechanical,
        "program_scope": obligation.program_scope,
        "maintenance_dependency_aliases": dependencies,
        "completeness_aliases": [],
    }


def _materialize(
    scratch: Path,
    old: ConstructionWorld,
    case: dict[str, Any],
    name: str,
    obligation_id: str,
    entity: str,
    chain: list[str],
    own_claim_relation: str,
    other_claim_relation: str,
) -> dict[str, Any]:
    obligation = _obligation(case, obligation_id, entity)
    catalog = build_semantic_construction_catalog(
        obligation,
        case,
        bounded_program_source=_bounded_source(old, entity, snapshot_id(old)),
        maintenance_dependencies=_dependencies(entity, chain),
        program_endpoint_kinds=_endpoint_kinds(old),
    )
    draft = _draft(
        obligation,
        catalog,
        entity,
        own_claim_relation=own_claim_relation,
        other_claim_relation=other_claim_relation,
    )
    candidate = compile_semantic_candidate_draft(
        obligation,
        catalog,
        draft,
        construction_method="deterministic design granularity control",
    )
    decision = admit_semantic_candidate(
        obligation, candidate, catalog, snapshot_id=snapshot_id(old)
    )
    assert decision.outcome == "PERSIST_COMMITMENT", decision.to_dict()
    return materialize_semantic_commitment_revision(
        old,
        scratch / name,
        obligation,
        candidate,
        decision,
        catalog,
        snapshot_id=snapshot_id(old),
    )


@pytest.fixture(scope="module")
def design_worlds(tmp_path_factory):
    scratch = tmp_path_factory.mktemp("design-granularity")
    _write(scratch, {"checkout-requirements.md": REQUIREMENTS})
    _spine(scratch, _checkout_files(BASELINE_TSX), "baseline-spine")
    result = construct_authority_world(
        scratch / "baseline-spine",
        scratch / "baseline-world",
        _universe(scratch),
        _build_design_authority,
        construction_id="design-checkout-construction-v1",
        purpose=PURPOSE,
        profile=PROFILE,
    )
    assert result.succeeded, result.errors
    _spine(scratch, _checkout_files(RELEVANT_TSX), "relevant-spine")
    _spine(scratch, _checkout_files(UNRELATED_TSX), "unrelated-spine")
    crossfile = _checkout_files(BASELINE_TSX)
    crossfile["src/unrelated.ts"] = "export function helper(): number { return 41; }\n"
    _spine(scratch, crossfile, "crossfile-spine")
    relevant = compare_program_spines(
        scratch / "baseline-spine", scratch / "relevant-spine"
    )
    unrelated = compare_program_spines(
        scratch / "baseline-spine", scratch / "unrelated-spine"
    )
    crossfile_comparison = compare_program_spines(
        scratch / "baseline-spine", scratch / "crossfile-spine"
    )
    empty = compare_program_spines(
        scratch / "baseline-spine", scratch / "baseline-spine"
    )
    old = ConstructionWorld.open(
        scratch / "baseline-world" / "world.sqlite", read_only=True
    )
    new = ConstructionWorld.open(
        scratch / "relevant-spine" / "world.sqlite", read_only=True
    )
    try:
        maintenance = assess_attachment_maintenance(old, new, relevant)
        impact = assess_authority_change_impact(
            old, new, relevant, maintenance=maintenance
        )
        case = assemble_governance_case(
            old,
            new,
            relevant,
            _sources(scratch),
            maintenance=maintenance,
            impact=impact,
            purpose=PURPOSE,
        )
        errors = validate_case_sidecar(
            case, maintenance=maintenance, impact=impact, comparison=relevant
        )
        assert not errors, errors
        kinds = _endpoint_kinds(old)
        descriptors = {
            str(row["entity"]): str(row["descriptor"])
            for row in old.relation_rows("program_identity_descriptor")
        }
        checkout = next(
            entity
            for entity, kind in kinds.items()
            if kind == "callable"
            and "src/Checkout.tsx" in descriptors.get(entity, "")
        )
        unit = next(
            entity
            for entity, kind in kinds.items()
            if kind == "source_unit"
            and "src/Checkout.tsx" in descriptors.get(entity, "")
        )
        parents = {
            str(row["child"]): str(row["parent"])
            for row in old.relation_rows("structural_context")
        }

        def _chain(entity: str) -> list[str]:
            chain = [entity]
            while chain[-1] in parents:
                chain.append(parents[chain[-1]])
            chain.reverse()
            return chain

        narrow = _materialize(
            scratch,
            old,
            case,
            "g1-narrow",
            "obligation:order-summary-checkout-realization",
            checkout,
            _chain(checkout),
            own_claim_relation="order_summary_realization",
            other_claim_relation="order_summary_unit_realization",
        )
        coarse = _materialize(
            scratch,
            old,
            case,
            "g1-coarse",
            "obligation:order-summary-source-unit-realization",
            unit,
            _chain(unit),
            own_claim_relation="order_summary_unit_realization",
            other_claim_relation="order_summary_realization",
        )
        g1_narrow = ConstructionWorld.open(
            scratch / "g1-narrow" / "world.sqlite", read_only=True
        )
        g1_coarse = ConstructionWorld.open(
            scratch / "g1-coarse" / "world.sqlite", read_only=True
        )
        yield {
            "checkout": checkout,
            "unit": unit,
            "relevant": relevant,
            "unrelated": unrelated,
            "crossfile": crossfile_comparison,
            "empty": empty,
            "g1_narrow": g1_narrow,
            "g1_coarse": g1_coarse,
            "narrow_warrant": narrow["warrant"],
            "coarse_warrant": coarse["warrant"],
        }
    finally:
        old.close()
        new.close()


@pytest.fixture
def worlds(design_worlds):
    yield design_worlds


def _assert_no_verdict_language(payload: object) -> None:
    text = json.dumps(payload, sort_keys=True).lower()
    for token in _VERDICT_TOKENS:
        assert token not in text, f"manufactured verdict language: {token}"


def _manifestation_assessments(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in result["assessments"]
        if item["dependency"].get("kind") == "manifestation_property"
        and item["dependency"].get("property") == "source_manifestation"
    ]


def test_narrow_binding_attaches_to_checkout_callable(worlds):
    rows = worlds["g1_narrow"].relation_rows(PROGRAM_REALIZATION_RELATION)
    assert len(rows) == 1
    assert rows[0]["semantic_subject"] == SEMANTIC_SUBJECT
    assert rows[0]["program_manifestation"] == worlds["checkout"]
    kinds = {
        row["entity"]: row["kind"]
        for row in worlds["g1_narrow"].relation_rows("program_entity_kind")
    }
    assert kinds[worlds["checkout"]] == "callable"
    coarse_rows = worlds["g1_coarse"].relation_rows(PROGRAM_REALIZATION_RELATION)
    assert len(coarse_rows) == 1
    assert coarse_rows[0]["program_manifestation"] == worlds["unit"]


def test_relevant_change_surfaces_design_commitment(worlds):
    """Control A: an edit inside the order-summary region surfaces."""

    before = worlds["g1_narrow"].path.read_bytes()
    direct = maintain_semantic_commitment(
        worlds["narrow_warrant"], worlds["relevant"]
    )
    assert direct["status"] == "CHANGED"
    assert direct["transferred"] is False
    assert direct["model_invoked"] is False
    fired = _manifestation_assessments(direct)
    assert fired, "the source-manifestation dependency must fire"
    assert all(item["status"] == "CHANGED" for item in fired)
    assert all(
        item["dependency"].get("program_entity") == worlds["checkout"]
        for item in fired
    )
    selection = select_affected_semantic_commitments(
        worlds["g1_narrow"], worlds["relevant"]
    )
    assert worlds["g1_narrow"].path.read_bytes() == before
    assert selection["warrants_considered"] == 1
    assert len(selection["selected"]) == 1
    entry = selection["selected"][0]
    assert entry["relation_name"] == PROGRAM_REALIZATION_RELATION
    assert entry["tuple"]["semantic_subject"] == SEMANTIC_SUBJECT
    assert entry["tuple"]["program_manifestation"] == worlds["checkout"]
    assert entry["maintenance"]["status"] == "CHANGED"
    assert entry["observations"], "inspectable grounding must be attached"
    _assert_no_verdict_language(selection)


def test_same_file_neighbor_change_fires_manifestation(worlds):
    """Control B finding: a same-file edit outside the bound region fires.

    The payment-entry edit does not touch the order-summary concern, but the
    spine records file digests rather than entity content digests, so the
    ``Checkout`` callable's recorded manifestation moves and the concern is
    selected. This pins outcome B (usable but coarse), not a verdict bug:
    identity, tuples, and structural context all stay PRESERVED.
    """

    direct = maintain_semantic_commitment(
        worlds["narrow_warrant"], worlds["unrelated"]
    )
    assert direct["status"] == "CHANGED"
    others = [
        item
        for item in direct["assessments"]
        if item["dependency"].get("kind") != "manifestation_property"
    ]
    assert others
    assert all(item["status"] == "PRESERVED" for item in others)
    fired = _manifestation_assessments(direct)
    assert fired
    assert all(item["status"] == "CHANGED" for item in fired)
    selection = select_affected_semantic_commitments(
        worlds["g1_narrow"], worlds["unrelated"]
    )
    assert selection["warrants_considered"] == 1
    assert len(selection["selected"]) == 1
    assert selection["selected"][0]["maintenance"]["status"] == "CHANGED"
    _assert_no_verdict_language(selection)


def test_cross_file_change_preserves_design_commitment(worlds):
    """Diagnostic: an edit in another file does not move the manifestation."""

    assert worlds["crossfile"].delta.identity.get("added")
    direct = maintain_semantic_commitment(
        worlds["narrow_warrant"], worlds["crossfile"]
    )
    assert direct["status"] == "PRESERVED"
    assert all(
        item["status"] == "PRESERVED" for item in direct["assessments"]
    )
    selection = select_affected_semantic_commitments(
        worlds["g1_narrow"], worlds["crossfile"]
    )
    assert selection["selected"] == []
    assert (
        select_affected_semantic_commitments(
            worlds["g1_narrow"], worlds["empty"]
        )["selected"]
        == []
    )


def test_coarse_binding_matches_narrow_noise(worlds):
    """Control C: the source-unit binding fires on the same edits."""

    for name in ("relevant", "unrelated"):
        direct = maintain_semantic_commitment(
            worlds["coarse_warrant"], worlds[name]
        )
        assert direct["status"] == "CHANGED", name
        selection = select_affected_semantic_commitments(
            worlds["g1_coarse"], worlds[name]
        )
        assert len(selection["selected"]) == 1, name
        entry = selection["selected"][0]
        assert entry["tuple"]["program_manifestation"] == worlds["unit"]
        assert entry["tuple"]["semantic_subject"] == SEMANTIC_SUBJECT
    direct = maintain_semantic_commitment(
        worlds["coarse_warrant"], worlds["crossfile"]
    )
    assert direct["status"] == "PRESERVED"
    assert (
        select_affected_semantic_commitments(
            worlds["g1_coarse"], worlds["crossfile"]
        )["selected"]
        == []
    )


def test_basis_without_manifestation_cannot_see_inside_callable(worlds):
    """Diagnostic: identity, tuples, and context are blind to body edits."""

    trimmed = dict(worlds["narrow_warrant"])
    trimmed["depends_on"] = [
        item
        for item in worlds["narrow_warrant"]["depends_on"]
        if item.get("kind") != "manifestation_property"
    ]
    assert trimmed["depends_on"], "the probe must keep a non-empty basis"
    kinds = {item.get("kind") for item in trimmed["depends_on"]}
    assert kinds <= {"program_identity", "relation_tuple", "structural_context"}
    for name in ("relevant", "unrelated"):
        probe = maintain_semantic_commitment(trimmed, worlds[name])
        assert probe["status"] == "PRESERVED", name
        assert all(
            item["status"] == "PRESERVED" for item in probe["assessments"]
        )


def test_selection_leaves_sealed_worlds_unchanged(worlds):
    for key in ("g1_narrow", "g1_coarse"):
        before = worlds[key].path.read_bytes()
        for name in ("relevant", "unrelated", "crossfile", "empty"):
            select_affected_semantic_commitments(worlds[key], worlds[name])
        assert worlds[key].path.read_bytes() == before

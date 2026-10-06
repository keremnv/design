"""Phase 3 boundary conformance through production construction/publication."""

from __future__ import annotations

import json
import shutil
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ontology_author.authority import (
    AuthorityUniverse, ClaimKind, DeclaredSource, ReferentResolution,
    RelationSupport, SourceStanding, construct_authority_world, load_receipt,
    observations_for_assertion, verify_construction_boundary,
    verify_authority_publication,
)
from ontology_author.authority.evidence import reconstruct_authority_observation
from ontology_author.config_routes import construct_config_requirements
from ontology_author.construction_boundary import SupportPath, support_paths_for_assertion
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.runtime.commit import fingerprint_world
from ontology_author.world.runtime.publication import PublicationRef, verify_publication_ref
from ontology_author.world.runtime.world import ConstructionWorld


POLICY = "The customer-export capability must require explicit approval.\n"


def universe(root: Path, *, corroboration=False) -> AuthorityUniverse:
    root.mkdir(parents=True, exist_ok=True)
    (root / "policy.md").write_text(POLICY)
    (root / "notes.md").write_text(
        "Customer exports require explicit approval under the export policy.\n"
        if corroboration else "Design notes available to construction.\n"
    )
    return AuthorityUniverse("approval/v1", (
        DeclaredSource("policy.md", root / "policy.md", SourceStanding.AUTHORITATIVE),
        DeclaredSource("notes.md", root / "notes.md", SourceStanding.AUTHORITATIVE),
    ), root)


def approval(constructor, *, mode="single", identity="semantic:ExportApproval", reuse=False):
    if reuse:
        for row in constructor.world.relation_rows("semantic_entity"):
            constructor.reuse_semantic_referent(row["entity"])
    policy = constructor.source("policy.md")
    notes = constructor.source("notes.md")
    s1 = policy.observe(policy.paragraphs()[0])
    s2 = notes.observe(notes.paragraphs()[0])
    constructor.create_semantic_referent(identity, label="Export approval", observations=(s1,))
    observations = (s1,) if mode == "single" else (s1, s2)
    paths = (SupportPath((s1,)), SupportPath((s2,))) if mode == "independent" else (SupportPath(observations),)
    constructor.note_exploration(action="private", target="scratch", detail="must not persist")
    return constructor.persist_claim(
        "requires_approval", {"requirement": identity, "statement": POLICY.strip()},
        roles=(Role("requirement", RoleType.REFERENT), Role("statement", RoleType.TEXT)),
        claim_kind=ClaimKind.SOURCE_PROPOSITION, support=RelationSupport.SOURCE_EXPLICIT,
        endpoint_resolution={"requirement": ReferentResolution.SOURCE_DEFINED},
        observations=observations, support_paths=paths,
    )


def construct(inputs, target, *, baseline=None, mode="single", version="v1", publication_inputs=(), build=None):
    return construct_authority_world(
        baseline, target, inputs, build or (lambda ctor: approval(ctor, mode=mode)),
        construction_id="approval", purpose="export policy", constructor_version=version,
        publication_inputs=publication_inputs,
    )


def claim_id(world, relation="requires_approval"):
    return next(row["assertion_id"] for row in world.relation_rows("authority_claim") if row["relation_name"] == relation)


def receipt(bundle):
    return load_receipt(bundle / "authority.construction.receipt.json")


def test_basis_is_not_support_and_retains_unused_evidence(tmp_path):
    inputs = universe(tmp_path / "source")
    result = construct(inputs, tmp_path / "W0")
    assert result.succeeded, result.errors
    before = fingerprint_world(result.world_dir)
    # Original sources and temporary construction directory are unnecessary.
    shutil.rmtree(inputs.workspace)
    assert not list(tmp_path.glob(".W0.candidate-*"))
    record = receipt(result.world_dir)
    assert record.exploration_provenance == ()
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        assert verify_publication_ref(world, result.publication) == []
        assert verify_construction_boundary(world, record) == []
        assert verify_authority_publication(world) == []
        assert {item["native_handle"] for item in record.construction_basis["observations"]} == {"policy.md", "notes.md"}
        aid = claim_id(world)
        assert {item.native_handle for item in observations_for_assertion(world, aid)} == {"policy.md"}
        paths = support_paths_for_assertion(world, aid)
        assert [len(path.members) for path in paths] == [1]
        for observation in record.construction_basis["observations"]:
            assert reconstruct_authority_observation(world, observation)[1] == "OK"
        assert reconstruct_authority_observation(world, paths[0].members[0]) == (POLICY, "OK")
    assert fingerprint_world(result.world_dir) == before


@pytest.mark.parametrize("mode,expected", [("independent", [1, 1]), ("joint", [2])])
def test_independent_and_joint_support_are_distinct(tmp_path, mode, expected):
    result = construct(universe(tmp_path / "source", corroboration=True), tmp_path / "W", mode=mode)
    assert result.succeeded, result.errors
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        paths = support_paths_for_assertion(world, claim_id(world))
        assert [len(path.members) for path in paths] == expected
        assert {member.native_handle for path in paths for member in path.members} == {"policy.md", "notes.md"}
        assert verify_construction_boundary(world, receipt(result.world_dir)) == []


def test_source_only_config_requirements_publish_before_software(tmp_path):
    workspace = tmp_path / "source"
    workspace.mkdir()
    source = workspace / "policy.md"
    source.write_text("Customer export must use the approved customer-export route.\n")
    result = construct_config_requirements(source, tmp_path / "W0")
    assert result.succeeded, result.errors
    assert result.snapshot_id == ""
    manifest = json.loads((result.world_dir / "authority.manifest.json").read_text())
    assert manifest["admission"] == {"contract": "authority-construction-boundary/v1", "outcome": "PASS"}
    shutil.rmtree(workspace)
    record = receipt(result.world_dir)
    assert record.construction_basis["program_snapshots"] == []
    assert record.construction_basis["publications"] == []
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        assert world.relation_rows("config_requirement")[0]["requested_route"] == "customer-export"
        assert world.relation_rows("authority_attachment_warrant") == []
        assert world.relation_rows("authority_unresolved") == []
        assert all(row["id"].startswith("semantic:") for row in world.query("SELECT id FROM _world_referents"))
        assert not world.query("SELECT name FROM _world_relations WHERE name LIKE 'program_%' OR name='realized_by'")
        assert verify_publication_ref(world, result.publication) == []
        assert verify_construction_boundary(world, record) == []
        assert verify_authority_publication(world) == []
        paths = support_paths_for_assertion(world, claim_id(world, "config_requirement"))
        assert reconstruct_authority_observation(world, paths[0].members[0])[1] == "OK"


def test_representational_gap_rejects_without_fabrication(tmp_path):
    source = tmp_path / "policy.md"
    source.write_text("Customer export must use the approved A route. Or perhaps B.\n")
    result = construct_config_requirements(source, tmp_path / "W")
    assert not result.succeeded
    assert "representational gap" in " ".join(result.errors)
    assert not (tmp_path / "W").exists()
    assert not list(tmp_path.glob(".W.candidate-*"))


def test_mixed_gap_preserves_full_evidence_without_guessing(tmp_path):
    source = tmp_path / "policy.md"
    unsupported = "Perhaps A or B; the target endpoint is ambiguous."
    source.write_text("Customer export must use the approved customer-export route.\n\n" + unsupported + "\n")
    result = construct_config_requirements(source, tmp_path / "W")
    assert result.succeeded, result.errors
    source.unlink()
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        assert len(world.relation_rows("config_requirement")) == 1
        gap = world.relation_rows("authority_unresolved")[0]
        assert gap["kind"] == "UNBOUND_REGION"
        aid = claim_id(world, "authority_unresolved")
        assert unsupported in reconstruct_authority_observation(world, support_paths_for_assertion(world, aid)[0].members[0])[0]
        assert verify_construction_boundary(world, receipt(result.world_dir)) == []


@pytest.mark.parametrize("copy_baseline", [False, True])
def test_prior_publication_is_exact_basis_without_lifecycle_claims(tmp_path, copy_baseline):
    inputs = universe(tmp_path / "source")
    w0 = construct(inputs, tmp_path / "W0")
    assert w0.succeeded, w0.errors
    before = fingerprint_world(w0.world_dir)

    def build(ctor):
        # W0 materially contributes the statement inspected here.
        with closing(ConstructionWorld.open(w0.world_dir / "world.sqlite")) as prior:
            assert prior.relation_rows("requires_approval")[0]["statement"] == POLICY.strip()
        approval(ctor, identity="semantic:ExportApprovalW1", reuse=copy_baseline)

    w1 = construct(inputs, tmp_path / "W1", baseline=w0.world_dir if copy_baseline else None,
                   publication_inputs=(w0.publication,), build=build)
    assert w1.succeeded, w1.errors
    assert fingerprint_world(w0.world_dir) == before
    record = receipt(w1.world_dir)
    assert record.construction_basis["publications"] == [w0.publication.as_dict()]
    assert record.construction_basis["candidate_baseline"] == (w0.publication.as_dict() if copy_baseline else None)
    with closing(ConstructionWorld.open(w1.world_dir / "world.sqlite")) as world:
        assert verify_construction_boundary(world, record) == []
        assert not world.query("SELECT name FROM _world_relations WHERE name IN ('supersedes','current','withdrawn','realized_by')")
        assert len(world.relation_rows("requires_approval")) == (2 if copy_baseline else 1)


def test_same_sources_distinct_method_versions_retain_both(tmp_path):
    inputs = universe(tmp_path / "source")
    w0 = construct(inputs, tmp_path / "W0", version="v1")
    w1 = construct(inputs, tmp_path / "W1", version="v2")
    assert w0.succeeded and w1.succeeded, (w0.errors, w1.errors)
    assert w0.publication.address != w1.publication.address
    assert receipt(w0.world_dir).construction_basis == receipt(w1.world_dir).construction_basis
    assert receipt(w0.world_dir).constructor["version"] == "v1"
    assert receipt(w1.world_dir).constructor["version"] == "v2"


def test_program_basis_does_not_bind_semantic_assertion(tmp_path):
    from tests.test_authority_construction import _spine
    inputs = universe(tmp_path / "source")
    spine = _spine(inputs.workspace, {"src/example.ts": "export function example() {}\n"}, "../P")
    with closing(ConstructionWorld.open(spine.world_dir / "world.sqlite")) as program:
        pref = PublicationRef.from_world(program)
    result = construct(inputs, tmp_path / "W", baseline=spine.world_dir)
    assert result.succeeded, result.errors
    record = receipt(result.world_dir)
    assert record.construction_basis["program_snapshots"][0]["publication"] == pref.as_dict()
    shutil.rmtree(inputs.workspace)
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        assert verify_construction_boundary(world, record) == []
        assert world.relation_rows("authority_attachment_warrant") == []
        aid = claim_id(world)
        assert {item.provider for item in observations_for_assertion(world, aid)} == {"markdown"}
        assert not world.query("SELECT name FROM _world_relations WHERE name='realized_by'")
        for base in world.warrant_for_assertion(aid)["bases"]:
            extra = (base.get("detail") or {}).get("extra") or {}
            assert "program_snapshot_id" not in extra


def test_admission_rejects_mismatched_support_groups(tmp_path):
    def build(ctor):
        s = ctor.source("policy.md")
        obs = s.observe(s.document())
        ctor.create_semantic_referent("semantic:R", label="R", observations=(obs,))
        ctor.persist_claim("claim", {"requirement": "semantic:R"},
            roles=(Role("requirement", RoleType.REFERENT),),
            claim_kind=ClaimKind.SOURCE_PROPOSITION, support=RelationSupport.SOURCE_EXPLICIT,
            endpoint_resolution={"requirement": ReferentResolution.SOURCE_DEFINED},
            observations=(obs,), support_paths=())
    result = construct(universe(tmp_path / "source"), tmp_path / "W", build=build)
    assert not result.succeeded and "support paths" in " ".join(result.errors)
    assert not (tmp_path / "W").exists()


def test_retained_verification_rejects_basis_corruption(tmp_path):
    result = construct(universe(tmp_path / "source"), tmp_path / "W")
    assert result.succeeded, result.errors
    record = receipt(result.world_dir)
    corrupted = json.loads(json.dumps(record.construction_basis))
    corrupted["observations"].pop()
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        errors = verify_construction_boundary(world, replace(record, construction_basis=corrupted))
        assert "construction basis does not match declared source revisions" in errors


def test_prior_publication_wrong_revision_fails_closed(tmp_path):
    inputs = universe(tmp_path / "source")
    w0 = construct(inputs, tmp_path / "W0")
    wrong = replace(w0.publication, revision=w0.publication.revision + 1)
    result = construct(inputs, tmp_path / "W1", publication_inputs=(wrong,))
    assert not result.succeeded and "world revision differs" in " ".join(result.errors)
    assert not (tmp_path / "W1").exists()


def test_publication_verification_detects_retained_receipt_tampering(tmp_path):
    result = construct(universe(tmp_path / "source"), tmp_path / "W")
    path = result.world_dir / "authority.construction.receipt.json"
    path.chmod(0o600)
    payload = json.loads(path.read_text())
    payload["constructor"]["version"] = "forged"
    path.write_text(json.dumps(payload))
    with closing(ConstructionWorld.open(result.world_dir / "world.sqlite")) as world:
        assert verify_authority_publication(world) == ["authority receipt digest differs from manifest"]

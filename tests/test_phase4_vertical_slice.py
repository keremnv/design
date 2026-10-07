"""Phase 4 vertical slice: W0 -> P1 -> W1 -> P2 -> W2 through production seams."""

from __future__ import annotations

import hashlib
import shutil
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from ontology_author.authority import (
    AuthorityUniverse,
    ClaimKind,
    DeclaredSource,
    ReferentResolution,
    RelationSupport,
    SourceStanding,
    construct_authority_world,
    load_receipt,
    verify_authority_publication,
)
from ontology_author.authority import observations_for_assertion
from ontology_author.authority.evidence import reconstruct_authority_observation
from ontology_author.config_routes import construct_config_binding, construct_config_requirements
from ontology_author.config_routes.rules import PROFILE_ID, PROFILE_VERSION
from ontology_author.construction_boundary import support_paths_for_assertion
from ontology_author.evidence.program_source import (
    program_source_observations,
    reconstruct_program_observation,
    verify_retained_program_inputs,
)
from ontology_author.program_spine import compare_spines
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.runtime.commit import fingerprint_world
from ontology_author.world.runtime.publication import PublicationRef, verify_publication_ref
from ontology_author.world.runtime.world import ConstructionWorld

REQUIREMENT = "Customer export must use the approved customer-export route."
SEMANTIC_ID = "semantic:proposition:customer-export-route"
TS_V1 = 'export function customerExport(): string {\n  return "/customers/export";\n}\n'
TS_V2 = 'export function customerExportV2(): string {\n  return "/customers/export/v2";\n}\n'
TS_AUDIT = 'export function auditLog(): string {\n  return "/audit/log";\n}\n'

LIFECYCLE_RELATIONS = (
    "supersedes",
    "current",
    "withdrawn",
    "withdraws",
    "replaces",
    "latest",
    "inherits",
)


def _spine(root: Path, files: dict[str, str], output: str):
    from tests.test_authority_construction import _spine as build

    return build(root, files, output)


def _discover_callable(bundle: Path, label: str) -> str:
    """Read a sealed spine publication and find one callable by its label."""
    with closing(ConstructionWorld.open(bundle / "world.sqlite")) as world:
        callables = [
            str(row["entity"])
            for row in world.relation_rows("program_entity_kind")
            if row["kind"] == "callable"
        ]
        labels = {
            str(row["id"]): str(row["label"])
            for row in world.query("SELECT id, label FROM _world_referents")
        }
        matches = [entity for entity in callables if labels.get(entity) == label]
        assert len(matches) == 1, (label, callables, labels)
        return matches[0]


def _bind(governance: Path, program: Path, output: Path, entity: str, semantic_ref):
    result = construct_config_binding(
        governance,
        program,
        output,
        program_entity=entity,
        semantic_inputs=(semantic_ref,),
    )
    assert result.succeeded, result.errors
    return result


def _lifecycle_relations(world) -> set[str]:
    names = {str(row["name"]) for row in world.query("SELECT name FROM _world_relations")}
    return names & set(LIFECYCLE_RELATIONS)


def _stage_w1(root: Path, *, governance_text=None, extra_callable=False):
    """Build W0, P1 and W1. Returns artifacts."""
    gov = root / "gov"
    gov.mkdir(parents=True, exist_ok=True)
    (gov / "policy.md").write_text(governance_text or (REQUIREMENT + "\n"))
    w0 = construct_config_requirements(gov / "policy.md", root / "W0")
    assert w0.succeeded, w0.errors

    ts1_files = {"src/routes.ts": TS_V1}
    if extra_callable:
        ts1_files["src/audit.ts"] = TS_AUDIT
    _spine(root / "ts1", ts1_files, "../P1")
    with closing(ConstructionWorld.open(root / "P1" / "world.sqlite")) as world:
        p1ref = PublicationRef.from_world(world)
    e1 = _discover_callable(root / "P1", "customerExport")

    w1 = _bind(gov / "policy.md", root / "P1", root / "W1", e1, w0.publication)
    return {"gov": gov, "W0": w0, "P1": p1ref, "E1": e1, "W1": w1}


def _stage_p2(root: Path, built: dict):
    _spine(root / "ts2", {"src/routes.ts": TS_V2}, "../P2")
    with closing(ConstructionWorld.open(root / "P2" / "world.sqlite")) as world:
        built["P2"] = PublicationRef.from_world(world)
    built["E2"] = _discover_callable(root / "P2", "customerExportV2")
    return built


def _stage_w2(root: Path, built: dict):
    built["W2"] = _bind(
        built["gov"] / "policy.md", root / "P2", root / "W2",
        built["E2"], built["W0"].publication,
    )
    return built


def _build_slice(root: Path, *, through="W2", governance_text=None, extra_callable=False):
    """Build the retained history through the requested stage. Returns artifacts."""
    built = _stage_w1(root, governance_text=governance_text, extra_callable=extra_callable)
    if through == "W1":
        return built
    _stage_p2(root, built)
    if through == "P2":
        return built
    return _stage_w2(root, built)


def _bundle_bytes(bundle: Path) -> bytes:
    return b"".join(
        path.read_bytes() for path in sorted(bundle.rglob("*")) if path.is_file()
    )


def _hash_tree(root: Path) -> dict[str, str]:
    """Test-local recursive bundle hash covering nested retained evidence."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(p for p in root.rglob("*") if p.is_file())
    }


def _assert_no_output(root: Path, output: Path) -> None:
    assert not output.exists()
    assert not list(root.glob(f".{output.name}.candidate-*"))
    assert not list(root.glob(".*.candidate-*"))


def _adversarial_requirement_world(
    root: Path,
    output_name: str,
    rows: list[tuple[str, str, str, str]],
    *,
    gov_name: str = "gov-adv",
) -> PublicationRef:
    """Publish a semantic W0-shaped world through production authority APIs.

    Each row is (requirement, statement, domain_relation, requested_route).
    All rows share the governance paragraph observation so the publication
    passes retained verification; content may still be adversarial.
    """
    gov = root / gov_name
    gov.mkdir(parents=True, exist_ok=True)
    (gov / "policy.md").write_text(REQUIREMENT + "\n")
    path = gov / "policy.md"
    universe = AuthorityUniverse(
        universe_id="config.routes/requirements/v1",
        workspace=gov,
        sources=(DeclaredSource(path.name, path, SourceStanding.AUTHORITATIVE),),
    )

    def build(constructor):
        source = constructor.source(path.name)
        observation = source.observe(source.paragraphs()[0])
        created: set[str] = set()
        for requirement, statement, domain_relation, requested_route in rows:
            if requirement not in created:
                constructor.create_semantic_referent(
                    requirement, label=statement, observations=(observation,)
                )
                created.add(requirement)
            constructor.persist_claim(
                "config_requirement",
                {
                    "requirement": requirement,
                    "statement": statement,
                    "domain_relation": domain_relation,
                    "requested_route": requested_route,
                },
                roles=(
                    Role("requirement", RoleType.REFERENT),
                    Role("statement", RoleType.TEXT),
                    Role("domain_relation", RoleType.TEXT),
                    Role("requested_route", RoleType.TEXT),
                ),
                claim_kind=ClaimKind.SOURCE_PROPOSITION,
                support=RelationSupport.SOURCE_EXPLICIT,
                endpoint_resolution={"requirement": ReferentResolution.SOURCE_DEFINED},
                observations=(observation,),
                construction_method="config.routes.proposition/v1:specific",
            )

    result = construct_authority_world(
        None,
        root / output_name,
        universe,
        build,
        construction_id="config.routes/requirements/v1",
        purpose="config requirements",
        profile=PROFILE_ID,
        constructor_id="config.routes.requirements",
        constructor_version=PROFILE_VERSION,
    )
    assert result.succeeded, result.errors
    with closing(ConstructionWorld.open(root / output_name / "world.sqlite")) as world:
        assert verify_authority_publication(world) == []
    assert result.publication is not None
    return result.publication


def test_case_a_w0_is_semantic_only(tmp_path):
    built = _build_slice(tmp_path, through="W1")
    w0 = built["W0"]
    with closing(ConstructionWorld.open(tmp_path / "W0" / "world.sqlite")) as world:
        assert verify_publication_ref(world, w0.publication) == []
        assert verify_authority_publication(world) == []
        rows = world.relation_rows("config_requirement")
        assert len(rows) == 1 and rows[0]["statement"] == REQUIREMENT
        assert world.query(
            "SELECT name FROM _world_relations WHERE name LIKE 'program_%' OR name='realized_by'"
        ) == []
        assert world.relation_rows("authority_attachment_warrant") == []
        aid = next(
            row["assertion_id"]
            for row in world.relation_rows("authority_claim")
            if row["relation_name"] == "config_requirement"
        )
        assert reconstruct_authority_observation(
            world, support_paths_for_assertion(world, aid)[0].members[0]
        )[1] == "OK"


def test_case_b_p1_is_mechanical_only(tmp_path):
    built = _build_slice(tmp_path, through="W1")
    with closing(ConstructionWorld.open(tmp_path / "P1" / "world.sqlite")) as world:
        assert verify_publication_ref(world, built["P1"]) == []
        assert verify_retained_program_inputs(world) == []
        assert built["E1"] in {
            str(row["entity"]) for row in world.relation_rows("program_entity")
        }
        observations = program_source_observations(world, built["E1"])
        assert observations
        texts = [
            reconstruct_program_observation(world, item) for item in observations
        ]
        assert texts and all(status == "OK" for _, status in texts)
        assert any("customerExport" in text for text, _ in texts)
        assert world.query(
            "SELECT name FROM _world_relations WHERE name LIKE 'authority_%'"
            " OR name LIKE 'semantic%' OR name IN ('realized_by','config_requirement')"
        ) == []
    assert b"must use the approved" not in _bundle_bytes(tmp_path / "P1")


def test_case_c_w1_binds_exact_occurrences(tmp_path):
    built = _build_slice(tmp_path, through="W1")
    record = load_receipt(tmp_path / "W1" / "authority.construction.receipt.json")
    assert sorted(
        (pub["address"], pub["world_id"], pub["revision"])
        for pub in record.construction_basis["publications"]
    ) == sorted([
        (built["W0"].publication.address, built["W0"].publication.world_id, built["W0"].publication.revision),
        (built["P1"].address, built["P1"].world_id, built["P1"].revision),
    ])
    assert record.construction_basis["candidate_baseline"] == built["P1"].as_dict()
    qualifier = record.construction_basis["program_snapshots"][0]
    assert qualifier["publication"] == built["P1"].as_dict()
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert verify_publication_ref(world, built["W1"].publication) == []
        assert verify_authority_publication(world) == []
        snapshot = world.relation_rows("program_snapshot")[0]["snapshot"]
        assert qualifier["snapshot"] == snapshot
        assert qualifier["snapshot_id"] == record.program_snapshot_id
        bindings = world.relation_rows("realized_by")
        assert bindings == [{"requirement": SEMANTIC_ID, "program": built["E1"]}]
        warrants = world.relation_rows("authority_attachment_warrant")
        assert len(warrants) == 1
        assert warrants[0]["program_entity"] == built["E1"]
        assert warrants[0]["program_snapshot_id"] == record.program_snapshot_id
        assert _lifecycle_relations(world) == set()
        aid = next(
            row["assertion_id"]
            for row in world.relation_rows("authority_claim")
            if row["relation_name"] == "realized_by"
        )
        flat = observations_for_assertion(world, aid)
        assert len(flat) == 1
        assert reconstruct_authority_observation(world, flat[0])[0].strip() == REQUIREMENT
        assert verify_retained_program_inputs(world) == []
        program_obs = program_source_observations(world, built["E1"])
        assert program_obs and all(
            reconstruct_program_observation(world, item)[1] == "OK" for item in program_obs
        )
    with closing(ConstructionWorld.open(tmp_path / "W0" / "world.sqlite")) as w0world:
        assert w0world.relation_rows("config_requirement")[0]["statement"] == REQUIREMENT


def test_case_d_exact_substitution_fails_closed(tmp_path):
    built = _build_slice(tmp_path, through="P2")
    gov_policy = built["gov"] / "policy.md"
    # P1 entity against a P2 baseline is not in the governed snapshot.
    bad_entity = construct_config_binding(
        gov_policy, tmp_path / "P2", tmp_path / "BAD1",
        program_entity=built["E1"], semantic_inputs=(built["W0"].publication,),
    )
    assert not bad_entity.succeeded
    assert not (tmp_path / "BAD1").exists()
    # Wrong semantic publication revision fails before any publication.
    wrong = replace(built["W0"].publication, revision=built["W0"].publication.revision + 1)
    bad_ref = construct_config_binding(
        gov_policy, tmp_path / "P1", tmp_path / "BAD2",
        program_entity=built["E1"], semantic_inputs=(wrong,),
    )
    assert not bad_ref.succeeded
    assert not (tmp_path / "BAD2").exists()
    # A W0 with different content cannot back this requirement.
    other_gov = tmp_path / "other-gov"
    other_gov.mkdir()
    (other_gov / "policy.md").write_text(
        "Audit log must use the approved audit-log route.\n"
    )
    other_w0 = construct_config_requirements(other_gov / "policy.md", tmp_path / "W0b")
    assert other_w0.succeeded, other_w0.errors
    mismatched = construct_config_binding(
        gov_policy, tmp_path / "P1", tmp_path / "BAD3",
        program_entity=built["E1"], semantic_inputs=(other_w0.publication,),
    )
    assert not mismatched.succeeded
    assert not (tmp_path / "BAD3").exists()
    # Same bytes copied elsewhere identify the copy's occurrence, not the original.
    shutil.copytree(tmp_path / "P1", tmp_path / "P1copy")
    for path in (tmp_path / "P1copy", *(tmp_path / "P1copy").rglob("*")):
        path.chmod(path.stat().st_mode | (0o700 if path.is_dir() else 0o600))
    _bind(gov_policy, tmp_path / "P1copy", tmp_path / "Wcopy", built["E1"], built["W0"].publication)
    copied_record = load_receipt(tmp_path / "Wcopy" / "authority.construction.receipt.json")
    assert copied_record.construction_basis["candidate_baseline"]["address"] == str(
        (tmp_path / "P1copy").resolve()
    )


def test_case_e_p2_is_fresh_and_distinguishable(tmp_path):
    built = _stage_w1(tmp_path)
    p1_fingerprint_before = fingerprint_world(tmp_path / "P1")
    p1_tree_before = _hash_tree(tmp_path / "P1")
    _stage_p2(tmp_path, built)
    assert fingerprint_world(tmp_path / "P1") == p1_fingerprint_before
    assert _hash_tree(tmp_path / "P1") == p1_tree_before
    assert built["P1"].address != built["P2"].address
    assert built["E1"] != built["E2"]
    with closing(ConstructionWorld.open(tmp_path / "P1" / "world.sqlite")) as old:
        old_snapshot = old.relation_rows("program_snapshot")[0]["snapshot"]
    with closing(ConstructionWorld.open(tmp_path / "P2" / "world.sqlite")) as new:
        new_snapshot = new.relation_rows("program_snapshot")[0]["snapshot"]
        assert built["E1"] not in {str(row["entity"]) for row in new.relation_rows("program_entity")}
    assert old_snapshot != new_snapshot
    # world_id/revision coincide; only the exact address distinguishes occurrences.
    assert (built["P1"].world_id, built["P1"].revision) == (built["P2"].world_id, built["P2"].revision)


def test_case_f_w1_does_not_move(tmp_path):
    built = _stage_w1(tmp_path)
    before = fingerprint_world(tmp_path / "W1")
    tree_before = _hash_tree(tmp_path / "W1")
    _stage_p2(tmp_path, built)
    assert fingerprint_world(tmp_path / "W1") == before
    assert _hash_tree(tmp_path / "W1") == tree_before
    compare_spines(tmp_path / "P1", tmp_path / "P2")
    assert fingerprint_world(tmp_path / "W1") == before
    assert _hash_tree(tmp_path / "W1") == tree_before
    _stage_w2(tmp_path, built)
    assert fingerprint_world(tmp_path / "W1") == before
    assert _hash_tree(tmp_path / "W1") == tree_before
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by")[0]["program"] == built["E1"]
        assert verify_authority_publication(world) == []
    assert built["E2"].encode() not in (tmp_path / "W1" / "world.sqlite").read_bytes()


def test_case_g_mechanical_reconsideration_signal(tmp_path):
    built = _build_slice(tmp_path, through="P2")
    before = {
        name: fingerprint_world(tmp_path / name) for name in ("P1", "P2", "W1")
    }
    trees_before = {
        name: _hash_tree(tmp_path / name) for name in ("P1", "P2", "W1")
    }
    result = compare_spines(tmp_path / "P1", tmp_path / "P2")
    payload = result.to_dict()
    rename = [
        claim for claim in payload["correspondence_claims"]
        if claim["old_entity"] == built["E1"]
    ]
    assert len(rename) == 1
    assert rename[0]["new_entity"] == built["E2"]
    assert rename[0]["outcome"] == "RENAME"
    assert rename[0]["basis_class"] == "HEURISTIC"
    assert rename[0]["continuity"] == "CONTINUED"
    assert rename[0]["limitations"]
    assert rename[0]["old_entity"] != rename[0]["new_entity"]
    for claim in payload["correspondence_claims"]:
        assert claim["outcome"] not in {"INVALID", "FALSE", "SUPERSEDED", "REBOUND"}
    for name, fingerprint in before.items():
        assert fingerprint_world(tmp_path / name) == fingerprint
    for name, tree in trees_before.items():
        assert _hash_tree(tmp_path / name) == tree
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by")[0]["program"] == built["E1"]
        assert verify_authority_publication(world) == []
        assert world.query(
            "SELECT name FROM _world_relations WHERE name LIKE '%correspond%'"
        ) == []


def test_case_h_w2_is_a_fresh_binding(tmp_path):
    built = _build_slice(tmp_path, through="W2")
    assert built["W1"].publication.address != built["W2"].publication.address
    record = load_receipt(tmp_path / "W2" / "authority.construction.receipt.json")
    assert sorted(
        (pub["address"], pub["world_id"], pub["revision"])
        for pub in record.construction_basis["publications"]
    ) == sorted([
        (built["W0"].publication.address, built["W0"].publication.world_id, built["W0"].publication.revision),
        (built["P2"].address, built["P2"].world_id, built["P2"].revision),
    ])
    assert record.construction_basis["candidate_baseline"] == built["P2"].as_dict()
    with closing(ConstructionWorld.open(tmp_path / "W2" / "world.sqlite")) as world:
        assert verify_publication_ref(world, built["W2"].publication) == []
        assert verify_authority_publication(world) == []
        assert world.relation_rows("realized_by") == [
            {"requirement": SEMANTIC_ID, "program": built["E2"]}
        ]
        assert _lifecycle_relations(world) == set()
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by") == [
            {"requirement": SEMANTIC_ID, "program": built["E1"]}
        ]
        assert verify_authority_publication(world) == []


def test_case_i_historical_read_matrix(tmp_path):
    built = _build_slice(tmp_path, through="W2")
    with closing(ConstructionWorld.open(tmp_path / "W0" / "world.sqlite")) as world:
        assert world.relation_rows("config_requirement")[0]["statement"] == REQUIREMENT
        assert world.query("SELECT name FROM _world_relations WHERE name LIKE 'program_%'") == []
    with closing(ConstructionWorld.open(tmp_path / "P1" / "world.sqlite")) as world:
        assert built["E1"] in {str(row["entity"]) for row in world.relation_rows("program_entity")}
        assert world.query("SELECT name FROM _world_relations WHERE name LIKE 'authority_%'") == []
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by")[0]["program"] == built["E1"]
    with closing(ConstructionWorld.open(tmp_path / "P2" / "world.sqlite")) as world:
        assert built["E2"] in {str(row["entity"]) for row in world.relation_rows("program_entity")}
    with closing(ConstructionWorld.open(tmp_path / "W2" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by")[0]["program"] == built["E2"]
    # Opening W2 first does not change what W1 says.
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by")[0]["program"] == built["E1"]
        assert verify_authority_publication(world) == []


def test_case_j_reconstruction_after_workspace_deletion(tmp_path):
    built = _build_slice(tmp_path, through="W2")
    shutil.rmtree(tmp_path / "gov")
    shutil.rmtree(tmp_path / "ts1")
    shutil.rmtree(tmp_path / "ts2")
    assert not list(tmp_path.glob(".*.candidate-*"))
    with closing(ConstructionWorld.open(tmp_path / "W0" / "world.sqlite")) as world:
        assert verify_authority_publication(world) == []
        aid = next(
            row["assertion_id"]
            for row in world.relation_rows("authority_claim")
            if row["relation_name"] == "config_requirement"
        )
        assert reconstruct_authority_observation(
            world, observations_for_assertion(world, aid)[0]
        )[0].strip() == REQUIREMENT
    with closing(ConstructionWorld.open(tmp_path / "P1" / "world.sqlite")) as world:
        assert verify_retained_program_inputs(world) == []
        p1_obs = program_source_observations(world, built["E1"])
        assert p1_obs
        assert all(
            reconstruct_program_observation(world, item)[1] == "OK"
            for item in p1_obs
        )
    with closing(ConstructionWorld.open(tmp_path / "P2" / "world.sqlite")) as world:
        assert verify_retained_program_inputs(world) == []
        p2_obs = program_source_observations(world, built["E2"])
        assert p2_obs
        assert all(
            reconstruct_program_observation(world, item)[1] == "OK"
            for item in p2_obs
        )
    for name, entity in (("W1", built["E1"]), ("W2", built["E2"])):
        with closing(ConstructionWorld.open(tmp_path / name / "world.sqlite")) as world:
            assert verify_authority_publication(world) == []
            assert verify_retained_program_inputs(world) == []
            aid = next(
                row["assertion_id"]
                for row in world.relation_rows("authority_claim")
                if row["relation_name"] == "realized_by"
            )
            assert reconstruct_authority_observation(
                world, observations_for_assertion(world, aid)[0]
            )[0].strip() == REQUIREMENT
            binding_obs = program_source_observations(world, entity)
            assert binding_obs
            assert all(
                reconstruct_program_observation(world, item)[1] == "OK"
                for item in binding_obs
            )
    # Program publications are also unnecessary for binding verification.
    shutil.move(str(tmp_path / "P1"), str(tmp_path / "P1.moved"))
    shutil.move(str(tmp_path / "P2"), str(tmp_path / "P2.moved"))
    for name, entity in (("W1", built["E1"]), ("W2", built["E2"])):
        with closing(ConstructionWorld.open(tmp_path / name / "world.sqlite")) as world:
            assert verify_authority_publication(world) == []
            moved_obs = program_source_observations(world, entity)
            assert moved_obs
            assert all(
                reconstruct_program_observation(world, item)[1] == "OK"
                for item in moved_obs
            )


def test_case_k_no_absence_inference_before_w2(tmp_path):
    built = _stage_w1(tmp_path)
    before = fingerprint_world(tmp_path / "W1")
    tree_before = _hash_tree(tmp_path / "W1")
    _stage_p2(tmp_path, built)
    assert fingerprint_world(tmp_path / "W1") == before
    assert _hash_tree(tmp_path / "W1") == tree_before
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by")[0]["program"] == built["E1"]
        assert verify_authority_publication(world) == []
        assert _lifecycle_relations(world) == set()
    blob = (tmp_path / "W1" / "world.sqlite").read_bytes()
    assert b"unimplemented" not in blob
    assert b"noncompliant" not in blob
    assert b"customerExportV2" not in blob


def test_case_l_basis_does_not_become_binding(tmp_path):
    text = REQUIREMENT + "\n\nPerhaps A or B; the target endpoint is ambiguous.\n"
    built = _build_slice(
        tmp_path, through="W1", governance_text=text, extra_callable=True
    )
    other = _discover_callable(tmp_path / "P1", "auditLog")
    assert other != built["E1"]
    with closing(ConstructionWorld.open(tmp_path / "W1" / "world.sqlite")) as world:
        assert verify_authority_publication(world) == []
        assert world.relation_rows("realized_by") == [
            {"requirement": SEMANTIC_ID, "program": built["E1"]}
        ]
        warrants = world.relation_rows("authority_attachment_warrant")
        assert [row["program_entity"] for row in warrants] == [built["E1"]]
        assert other not in {
            row["target"] for row in world.relation_rows("authority_attachment_scope")
        }
        aid = next(
            row["assertion_id"]
            for row in world.relation_rows("authority_claim")
            if row["relation_name"] == "realized_by"
        )
        flat = observations_for_assertion(world, aid)
        assert len(flat) == 1
        assert reconstruct_authority_observation(world, flat[0])[0].strip() == REQUIREMENT
        gaps = world.relation_rows("authority_unresolved")
        assert len(gaps) == 1 and gaps[0]["kind"] == "UNBOUND_REGION"


def test_semantic_tuple_wrong_domain_relation_fails_closed(tmp_path):
    built = _stage_w1(tmp_path)
    gov_policy = built["gov"] / "policy.md"
    adversarial = _adversarial_requirement_world(
        tmp_path,
        "W0adv",
        [(SEMANTIC_ID, REQUIREMENT, "audit_log_route", "customer-export")],
        gov_name="gov-adv-domain",
    )
    bad = construct_config_binding(
        gov_policy,
        tmp_path / "P1",
        tmp_path / "BAD_DOMAIN",
        program_entity=built["E1"],
        semantic_inputs=(adversarial,),
    )
    assert not bad.succeeded
    _assert_no_output(tmp_path, tmp_path / "BAD_DOMAIN")


def test_semantic_tuple_wrong_requested_route_fails_closed(tmp_path):
    built = _stage_w1(tmp_path)
    gov_policy = built["gov"] / "policy.md"
    adversarial = _adversarial_requirement_world(
        tmp_path,
        "W0adv",
        [(SEMANTIC_ID, REQUIREMENT, "customer_export_route", "audit-log")],
        gov_name="gov-adv-route",
    )
    bad = construct_config_binding(
        gov_policy,
        tmp_path / "P1",
        tmp_path / "BAD_ROUTE",
        program_entity=built["E1"],
        semantic_inputs=(adversarial,),
    )
    assert not bad.succeeded
    _assert_no_output(tmp_path, tmp_path / "BAD_ROUTE")


def test_semantic_tuple_conflicting_duplicate_fails_closed(tmp_path):
    built = _stage_w1(tmp_path)
    gov_policy = built["gov"] / "policy.md"
    adversarial = _adversarial_requirement_world(
        tmp_path,
        "W0adv",
        [
            (SEMANTIC_ID, REQUIREMENT, "customer_export_route", "customer-export"),
            (SEMANTIC_ID, REQUIREMENT, "customer_export_route", "audit-log"),
        ],
        gov_name="gov-adv-dup",
    )
    with closing(ConstructionWorld.open(tmp_path / "W0adv" / "world.sqlite")) as world:
        assert len(world.relation_rows("config_requirement")) == 2
    bad = construct_config_binding(
        gov_policy,
        tmp_path / "P1",
        tmp_path / "BAD_DUP",
        program_entity=built["E1"],
        semantic_inputs=(adversarial,),
    )
    assert not bad.succeeded
    _assert_no_output(tmp_path, tmp_path / "BAD_DUP")


def test_semantic_tuple_equivalent_publications_accepted(tmp_path):
    built = _stage_w1(tmp_path)
    gov_policy = built["gov"] / "policy.md"
    # Ordinary Phase 3 W0 already backed W1 above; re-bind to confirm.
    _bind(gov_policy, tmp_path / "P1", tmp_path / "W1again", built["E1"], built["W0"].publication)
    # Independently published equivalent W0 from the same bytes.
    second_gov = tmp_path / "gov-second"
    second_gov.mkdir()
    (second_gov / "policy.md").write_text(REQUIREMENT + "\n")
    second_w0 = construct_config_requirements(second_gov / "policy.md", tmp_path / "W0second")
    assert second_w0.succeeded, second_w0.errors
    assert second_w0.publication.address != built["W0"].publication.address
    with closing(ConstructionWorld.open(tmp_path / "W0second" / "world.sqlite")) as world:
        assert world.relation_rows("config_requirement") == [
            {
                "requirement": SEMANTIC_ID,
                "statement": REQUIREMENT,
                "domain_relation": "customer_export_route",
                "requested_route": "customer-export",
            }
        ]
    _bind(gov_policy, tmp_path / "P1", tmp_path / "W1second", built["E1"], second_w0.publication)
    second_record = load_receipt(tmp_path / "W1second" / "authority.construction.receipt.json")
    assert second_w0.publication.as_dict() in second_record.construction_basis["publications"]
    # Equivalent copied W0 at another exact address.
    shutil.copytree(tmp_path / "W0", tmp_path / "W0copy")
    for path in (tmp_path / "W0copy", *(tmp_path / "W0copy").rglob("*")):
        path.chmod(path.stat().st_mode | (0o700 if path.is_dir() else 0o600))
    with closing(ConstructionWorld.open(tmp_path / "W0copy" / "world.sqlite")) as world:
        copy_ref = PublicationRef.from_world(world)
    assert copy_ref.address != built["W0"].publication.address
    assert (copy_ref.world_id, copy_ref.revision) == (
        built["W0"].publication.world_id,
        built["W0"].publication.revision,
    )
    _bind(gov_policy, tmp_path / "P1", tmp_path / "W1copy", built["E1"], copy_ref)
    copy_record = load_receipt(tmp_path / "W1copy" / "authority.construction.receipt.json")
    assert copy_ref.as_dict() in copy_record.construction_basis["publications"]
    with closing(ConstructionWorld.open(tmp_path / "W1copy" / "world.sqlite")) as world:
        assert verify_authority_publication(world) == []
        assert world.relation_rows("realized_by") == [
            {"requirement": SEMANTIC_ID, "program": built["E1"]}
        ]


def test_w2_without_w1_available(tmp_path):
    built = _stage_w1(tmp_path)
    _stage_p2(tmp_path, built)
    gov_policy = built["gov"] / "policy.md"
    shutil.move(str(tmp_path / "W1"), str(tmp_path / "W1.moved"))
    assert not (tmp_path / "W1").exists()
    result = construct_config_binding(
        gov_policy,
        tmp_path / "P2",
        tmp_path / "W2",
        program_entity=built["E2"],
        semantic_inputs=(built["W0"].publication,),
    )
    assert result.succeeded, result.errors
    record = load_receipt(tmp_path / "W2" / "authority.construction.receipt.json")
    assert sorted(
        (pub["address"], pub["world_id"], pub["revision"])
        for pub in record.construction_basis["publications"]
    ) == sorted([
        (built["W0"].publication.address, built["W0"].publication.world_id, built["W0"].publication.revision),
        (built["P2"].address, built["P2"].world_id, built["P2"].revision),
    ])
    assert "W1" not in "".join(pub["address"] for pub in record.construction_basis["publications"])
    with closing(ConstructionWorld.open(tmp_path / "W2" / "world.sqlite")) as world:
        assert verify_authority_publication(world) == []
        assert world.relation_rows("realized_by") == [
            {"requirement": SEMANTIC_ID, "program": built["E2"]}
        ]
    with closing(ConstructionWorld.open(tmp_path / "W1.moved" / "world.sqlite")) as world:
        assert world.relation_rows("realized_by") == [
            {"requirement": SEMANTIC_ID, "program": built["E1"]}
        ]

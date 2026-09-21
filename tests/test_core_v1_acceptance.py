"""Executable acceptance of docs/CORE_PRODUCT_V1_COMPLETION_CONTRACT.md.

No live model or application governance is used. Independent consumption has
an audited fresh-process gate everywhere, plus a physical read-only mount and
source-exclusion check on Linux with bubblewrap.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from ontology_author.world import ConstructionWorld
from ontology_author.world.explorer import WorldExplorerAdapter
from ontology_author.world.core.source import SourceObservation
from profiles.core_v1.build import build
from profiles.core_v1.evidence import CsvEvidence, PythonEvidence, reconstruct_retained, sources

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "core_v1"


def fingerprint(bundle):
    return {str(path.relative_to(bundle)): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o777)
            for path in bundle.rglob("*") if path.is_file()}


@pytest.fixture
def scenario(tmp_path):
    source_root = tmp_path / "sources"
    shutil.copytree(PROFILE / "fixture", source_root)
    result = build(source_root, tmp_path / "revisions" / "r0")
    assert result.succeeded, result.errors
    return source_root, result.world_dir


def test_heterogeneous_join_grounding_origins_and_reconstruction(scenario):
    source_root, bundle = scenario
    before = fingerprint(bundle)
    assert all(not mode & 0o222 for _, mode in before.values())
    with WorldExplorerAdapter(bundle / "world.sqlite") as reader:
        schemas = {item["name"]: item for item in reader.schema()}
        assert {role["name"]: role["type"] for role in schemas["governs"]["roles"]} == {
            "requirement": "REFERENT", "program": "REFERENT", "provider": "REFERENT"}
        governed = reader.rows("governs")["rows"]
        assert len(governed) == 1
        assert governed[0]["values"] == {"requirement": "requirement:R-PAY", "program": "program:checkout", "provider": "provider:Stripe"}
        assertion = reader.assertion(governed[0]["assertion_id"])
        assert assertion["origin"] == "SEMANTIC"
        evidence = [item for item in assertion["grounding"] if item["kind"] == "SOURCE"]
        assert {item["provider"] for item in evidence} == {"markdown", "csv", "python-ast"}
        for item in evidence:
            observation = SourceObservation(**{key: item[key] for key in ("provider", "native_handle", "source_revision", "native_location")})
            start, end = map(int, observation.native_location.split(":")[1:])
            original = (source_root / observation.native_handle).read_bytes()[start:end].decode()
            assert reconstruct_retained(bundle, observation) == original
        assert schemas["program_callable"]["origins"] == ["MECHANICAL"]
        assert schemas["deployment"]["origins"] == ["MECHANICAL"]
        assert schemas["governed_call"]["origins"] == ["DERIVED"]
        assert reader.derivation("governed_call")["rests_on"]["governed_call"] == ["direct_call", "governs"]
        assert reader.rows("governed_call")["rows"][0]["values"] == {
            "requirement": "requirement:R-PAY", "caller": "program:checkout", "callee": "program:route_payment"}
    assert fingerprint(bundle) == before


def test_ambiguity_is_recorded_without_selected_or_negative_match(scenario):
    _, bundle = scenario
    with WorldExplorerAdapter(bundle / "world.sqlite") as reader:
        candidates = reader.rows("candidate_realization")["rows"]
        assert {row["values"]["program"] for row in candidates} == {"program:refund_eu", "program:refund_us"}
        for candidate in candidates:
            support = reader.assertion(candidate["assertion_id"])["grounding"]
            assert {item["provider"] for item in support if item["kind"] == "SOURCE"} == {"markdown", "csv", "python-ast"}
        question = reader.rows("open_question")["rows"]
        assert len(question) == 1
        assert question[0]["values"]["requirement"] == "requirement:R-REFUND"
        assert question[0]["values"]["status"] == "UNRESOLVED"
        assert "2 candidate" in question[0]["values"]["reason"]
        assert reader.rows("realized_by")["rows"][0]["values"]["boundary"] == "boundary:Harbor"
        assert reader.rows("realized_by")["total"] == 1


def test_completeness_is_scoped_and_raw_sql_does_not_supply_a_truth_policy(scenario):
    _, bundle = scenario
    world = ConstructionWorld.open(bundle / "world.sqlite")
    try:
        complete = world.latest_completeness("paypal_in_manifest")
        unknown = world.latest_completeness("paypal_anywhere")
        assert complete["status"] == "COMPLETE" and complete["current"]
        assert complete["universe_relation"] == "deployment"
        assert unknown["status"] == "UNKNOWN" and unknown["known_gaps"]
        assert world.relation_rows("paypal_in_manifest") == world.relation_rows("paypal_anywhere") == []
        # Raw SQL can express the same unqualified negation in both cases.
        # The independently tested consumer must consult the receipts.
        assert world.query_semantic("SELECT NOT EXISTS (SELECT 1 FROM paypal_anywhere) AS absent") == [{"absent": 1}]
    finally:
        world.close()


def test_reconstruction_retains_independent_history_and_stable_assertions(scenario, tmp_path):
    source_root, old = scenario
    before = fingerprint(old)
    configuration = source_root / "deployments.csv"
    configuration.write_text(configuration.read_text().replace("Harbor,route_payment,Stripe", "Harbor,route_payment,Adyen"))
    result = build(source_root, tmp_path / "revisions" / "r1")
    assert result.succeeded, result.errors
    new = result.world_dir
    assert old != new and old.exists() and new.exists()
    with WorldExplorerAdapter(old / "world.sqlite") as left, WorldExplorerAdapter(new / "world.sqlite") as right:
        assert left.rows("governs")["rows"][0]["values"]["provider"] == "provider:Stripe"
        assert right.rows("governs")["rows"][0]["values"]["provider"] == "provider:Adyen"
        assert left.rows("program_callable")["rows"] == right.rows("program_callable")["rows"]
        ground = next(item for item in left.assertion(left.rows("governs")["rows"][0]["assertion_id"])["grounding"]
                      if item.get("provider") == "csv")
        observation = SourceObservation(**{key: ground[key] for key in ("provider", "native_handle", "source_revision", "native_location")})
        assert "Stripe" in reconstruct_retained(old, observation)
    with pytest.raises(FileExistsError):
        build(source_root, old.parent)
    assert fingerprint(old) == before
    # Both historical answers survive relocation of all mutable inputs and
    # are available to separate consumers which cannot access those inputs.
    source_root.rename(tmp_path / "sources-not-supplied-to-consumers")
    for bundle, provider in ((old, "Stripe"), (new, "Adyen")):
        sealed = fingerprint(bundle)
        answer = _fresh_consumer(bundle, tmp_path / f"consumer-{provider}")
        assert answer["governing_knowledge"][0]["labels"]["provider"] == provider
        assert fingerprint(bundle) == sealed


def test_read_only_storage_cannot_mutate_even_through_the_semantic_kernel(scenario):
    from ontology_author.world.core.kernel import SemanticWorld

    _, bundle = scenario
    before = fingerprint(bundle)
    world = SemanticWorld(bundle / "world.sqlite", world_id="v0", read_only=True)
    try:
        # Previously the read_only flag left a writable SQLite connection.
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            world.add_referent("unexpected", label="must not be written")
    finally:
        world.close()
    assert fingerprint(bundle) == before


def test_read_only_inspection_handles_uri_characters_in_revision_address(scenario, tmp_path):
    source_root, _ = scenario
    result = build(source_root, tmp_path / "revision #1?copy=2")
    assert result.succeeded, result.errors
    bundle = result.world_dir
    before = fingerprint(bundle)
    answer = _fresh_consumer(bundle, tmp_path / "consumer-uri-path")
    assert answer["governing_knowledge"][0]["labels"]["provider"] == "Stripe"
    assert fingerprint(bundle) == before
    assert not (tmp_path / "revision ").exists(), "inspection must not open a truncated URI path"


@pytest.mark.parametrize("failure", ["shape", "grounding", "stored_grounding"])
def test_invalid_candidate_never_publishes_or_changes_history(scenario, tmp_path, failure):
    source_root, old = scenario
    before = fingerprint(old)
    constructor = tmp_path / f"bad_{failure}.py"
    header = (
        "import sqlite3\n"
        "from profiles.core_v1.construction import construct as populate\n"
        "from ontology_author.world.core.origins import ConstructionOrigin\n"
        "def construct(source, world):\n"
        "    populate(source, world)\n"
    )
    if failure == "stored_grounding":
        # Deliberately corrupt the candidate after normal assertion admission.
        # Final publication validation must independently catch this defect.
        body = (
            "    with sqlite3.connect(world.path) as db:\n"
            '        db.execute("DELETE FROM _world_groundings WHERE subject_type = \'ASSERTION\'")\n'
        )
    else:
        body = (
            "    world.assert_tuple('program_callable', "
            + ("{'program': 'program:checkout', 'wrong_role': 'checkout'}, " if failure == "shape" else "{'program': 'program:checkout', 'name': 'other'}, ")
            + "origin=ConstructionOrigin.MECHANICAL, "
            + ("grounding=source.grounding('payments.py', 'bytes:0:1'))\n" if failure == "shape" else "grounding=None)\n")
        )
    constructor.write_text(header + body)
    destination = tmp_path / "revisions" / f"invalid-{failure}"
    result = build(source_root, destination, construction=constructor)
    assert not result.succeeded
    if failure == "shape":
        assert "roles" in str(result.errors)
    elif failure == "stored_grounding":
        assert result.reason == "contract_admission"
    else:
        assert result.reason == "ungrounded_world_base"
    assert not (destination / "world").exists()
    assert not (destination / "candidate").exists()
    assert fingerprint(old) == before


def test_publication_failure_and_atomic_visibility(scenario, tmp_path, monkeypatch):
    source_root, old = scenario
    before = fingerprint(old)
    destination = tmp_path / "revisions" / "publication-failure"
    original = Path.rename
    observed = []

    def fail_publication(path, target):
        if path == destination / "world.staging":
            assert not Path(target).exists()
            assert all(not mode & 0o222 for _, mode in fingerprint(path).values())
            observed.append(path)
            raise OSError("injected failure at the publication rename")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", fail_publication)
    result = build(source_root, destination)
    assert observed and not result.succeeded
    assert not (destination / "world").exists()
    assert fingerprint(old) == before


def _fresh_consumer(bundle, directory, *, physical_isolation=False):
    directory.mkdir()
    reader = directory / "reader"
    reader.mkdir()
    shutil.copyfile(PROFILE / "consume.py", reader / "consume.py")
    package = reader / "runtime" / "ontology_author"
    package.mkdir(parents=True)
    shutil.copyfile(ROOT / "ontology_author" / "__init__.py", package / "__init__.py")
    shutil.copytree(ROOT / "ontology_author" / "world", package / "world",
                    ignore=shutil.ignore_patterns("__pycache__", "static"))
    assert not (reader / "runtime" / "profiles").exists()
    assert not (reader / "construction.py").exists()
    python = str(Path(sys.executable).resolve())
    command = [python, "-I", "-S", "-B", str(reader / "consume.py"), str(bundle)]
    if physical_isolation:
        # The active interpreter may live outside /usr (e.g. a Conda venv).
        interpreter_mount = []
        if not Path(python).is_relative_to("/usr"):
            interpreter_mount = ["--ro-bind", sys.base_prefix, sys.base_prefix]
        command = ["bwrap", "--unshare-all", "--die-with-parent",
                   "--ro-bind", "/usr", "/usr", "--ro-bind", "/lib", "/lib",
                   "--ro-bind", "/lib64", "/lib64", "--proc", "/proc", "--dev", "/dev",
                   *interpreter_mount,
                   "--ro-bind", str(reader), "/reader", "--ro-bind", str(bundle), "/world",
                   "--chdir", "/reader", python, "-I", "-S", "-B", "/reader/consume.py", "/world"]
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("physical_isolation", [False, True])
def test_fresh_consumer_has_only_bundle_and_reads(scenario, tmp_path, physical_isolation):
    if physical_isolation and (sys.platform != "linux" or shutil.which("bwrap") is None):
        pytest.skip("additional physical isolation requires Linux bubblewrap; audited consumer remains mandatory")
    _, bundle = scenario
    before = fingerprint(bundle)
    answer = _fresh_consumer(bundle, tmp_path / "consumer", physical_isolation=physical_isolation)
    assert answer["discovered_schema"]
    claim = answer["governing_knowledge"][0]
    assert claim["labels"] == {"requirement": "R-PAY", "program": "checkout", "provider": "Stripe"}
    assert {item["provider"] for item in claim["grounding"] if item["kind"] == "SOURCE"} == {"markdown", "csv", "python-ast"}
    assert len(answer["unresolved_questions"]) == 1
    assert answer["unresolved_questions"][0]["status"] == "UNRESOLVED"
    assert answer["construction_origins"]["governs"] == ["SEMANTIC"]
    assert answer["construction_origins"]["program_callable"] == ["MECHANICAL"]
    negatives = {item["relation"]: item for item in answer["negative_inferences"]}
    assert negatives["paypal_in_manifest"]["conclusion"] == "ABSENT_WITHIN_RECORDED_UNIVERSE"
    assert negatives["paypal_anywhere"]["conclusion"] == "UNKNOWN"
    assert negatives["paypal_in_manifest"]["full_receipt"]["basis"]
    assert not any("/evidence/" in path or "/sources/" in path or "construction.py" in path for path in answer["file_reads"])
    assert fingerprint(bundle) == before


@pytest.mark.parametrize("provider", ["PayPal", "Adyen"])
def test_fresh_consumer_discovers_renamed_relations_and_changed_cross_source_answers(scenario, tmp_path, provider):
    source_root, old = scenario
    before = fingerprint(old)
    requirements = source_root / "requirements.md"
    requirements.write_text(requirements.read_text().replace("R-PAY", "R-CHARGE"))
    program = source_root / "payments.py"
    program.write_text(program.read_text().replace("def checkout(", "def start_payment("))
    manifest = source_root / "deployments.csv"
    manifest.write_text(manifest.read_text().replace(
        "checkout,Harbor,route_payment,Stripe", f"start_payment,Harbor,route_payment,{provider}"))
    # Only the constructor knows these new relation names. The independent
    # reader still has no constructor/fixture imports or raw evidence access.
    constructor = tmp_path / "renamed_construction.py"
    renamed = (PROFILE / "construction.py").read_text()
    for original, replacement in (
        ("governs", "requirement_scope"),
        ("open_question", "unresolved_correspondence"),
        ("candidate_realization", "possible_mapping"),
        ("paypal_in_manifest", "provider_within_scope"),
        ("paypal_anywhere", "provider_outside_scope"),
    ):
        renamed = renamed.replace(original, replacement)
    constructor.write_text(renamed)
    result = build(source_root, tmp_path / "revisions" / "renamed", construction=constructor)
    assert result.succeeded, result.errors
    answer = _fresh_consumer(result.world_dir, tmp_path / "consumer")
    claim, = answer["governing_knowledge"]
    assert claim["relation"] == "requirement_scope"
    assert claim["labels"] == {"requirement": "R-CHARGE", "program": "start_payment", "provider": provider}
    negatives = {item["relation"]: item["conclusion"] for item in answer["negative_inferences"]}
    assert negatives == ({} if provider == "PayPal" else {
        "provider_within_scope": "ABSENT_WITHIN_RECORDED_UNIVERSE",
        "provider_outside_scope": "UNKNOWN",
    })
    assert answer["unresolved_questions"][0]["status"] == "UNRESOLVED"
    assert fingerprint(old) == before


@pytest.mark.parametrize("missing_basis", ["prose_match", "program_endpoint"])
def test_cross_source_join_does_not_survive_missing_basis(scenario, tmp_path, missing_basis):
    source_root, old = scenario
    before = fingerprint(old)
    if missing_basis == "prose_match":
        path = source_root / "requirements.md"
        path.write_text(path.read_text().replace('"Harbor"', '"Unspecified"'))
    else:
        path = source_root / "payments.py"
        path.write_text(path.read_text().replace("def checkout(", "def renamed_checkout("))
    result = build(source_root, tmp_path / "revisions" / missing_basis)
    if missing_basis == "prose_match":
        assert result.succeeded, result.errors
        answer = _fresh_consumer(result.world_dir, tmp_path / "consumer")
        assert answer["governing_knowledge"] == []
        assert len(answer["unresolved_questions"]) == 2
    else:
        # Bounded constructor rejects an unaddressable endpoint, rather than
        # inventing a referent. Richer recovery is an application choice.
        assert not result.succeeded
        assert "manifest endpoint is not a declared program function" in str(result.errors)
        assert not (tmp_path / "revisions" / missing_basis / "world").exists()
    assert fingerprint(old) == before


def test_adapters_are_mechanical_and_retain_exact_unicode_and_multiline_spans(tmp_path):
    csv_path = tmp_path / "unrelated.csv"
    csv_path.write_text('id,description\n1,"café\nsecond line"\n', encoding="utf-8")
    table = CsvEvidence(csv_path, handle="unrelated.csv")
    row, = table.records()
    assert row.values == {"id": "1", "description": "café\nsecond line"}
    assert table.reconstruct(row.observation) == '1,"café\nsecond line"\n'
    python_path = tmp_path / "unrelated.py"
    python_path.write_text('def café():\n    return 3\n', encoding="utf-8")
    program = PythonEvidence(python_path, handle="unrelated.py")
    declaration, = program.declarations()
    assert declaration.values == {"name": "café"}
    assert program.reconstruct(declaration.observation) == 'def café():\n    return 3'
    assert table.known_losses and program.known_losses


def test_evidence_reconstruction_rejects_wrong_revision_and_corruption(scenario, tmp_path):
    source_root, bundle = scenario
    prose, _, _ = sources(source_root)
    observation = prose.observe(prose.paragraphs()[0])
    copy = tmp_path / "corrupted-bundle"
    copy.mkdir()
    shutil.copytree(bundle / "evidence", copy / "evidence")
    blob = copy / "evidence" / observation.source_revision.removeprefix("sha256:")
    blob.chmod(0o600)
    blob.write_bytes(b"changed material")
    with pytest.raises(ValueError, match="digest mismatch"):
        reconstruct_retained(copy, observation)
    with pytest.raises(ValueError, match="SHA-256"):
        reconstruct_retained(bundle, SourceObservation("markdown", "requirements.md", "unknown", "bytes:0:1"))

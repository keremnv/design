"""Test-only falsification of a generic OA application working-set layer."""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ontology_author.evidence.markdown import parse_byte_location
from ontology_author.world import ConstructionWorld, Project
from ontology_author.world.explorer import WorldExplorerAdapter

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "fixtures" / "oa_cross_domain"
CONSTRUCTION = HERE / "oa_cross_domain_working_set_fixtures.py"
QUESTION = "Which published studies support the shade-cloth cooling claim, and through which findings?"
SELECTED_RELATIONS = ("study_finding", "finding_outcome", "finding_supports_claim",
                      "possible_humidity_effect", "open_question")


def publish(source_root: Path, address: Path) -> Path:
    address.mkdir(parents=True, exist_ok=False)
    result = Project(address, project_root=source_root).run(CONSTRUCTION)
    assert result.succeeded, (result.reason, result.errors)
    return result.world_dir.resolve()


@pytest.fixture
def publications(tmp_path):
    source = tmp_path / "sources"
    shutil.copytree(CORPUS, source)
    first = publish(source, tmp_path / "revisions" / "first")
    second_source = tmp_path / "similar-sources"
    shutil.copytree(source, second_source)
    study_b = second_source / "study_b.md"
    study_b.write_text(study_b.read_text(encoding="utf-8").replace(
        "lower leaf temperature", "unchanged leaf temperature"), encoding="utf-8")
    second = publish(second_source, tmp_path / "revisions" / "second")
    return first, second


def fingerprint(bundle: Path) -> dict[str, str]:
    return {str(path.relative_to(bundle)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in bundle.rglob("*") if path.is_file()}


def citation(reader: WorldExplorerAdapter, bundle: Path, assertion_id: str) -> dict:
    found = reader.assertion(assertion_id)
    return {"publication": str(bundle), "assertion_id": assertion_id,
            "relation": found["relation"], "values": found["values"],
            "origin": found["origin"], "grounding": found["grounding"]}


def source_text(bundle: Path, observation: dict) -> str:
    if observation["provider"] != "markdown" or observation["native_handle"] != "study_c.md":
        raise ValueError("unexpected source observation")
    return reconstruct_support(bundle, observation)


def reconstruct_support(bundle: Path, observation: dict) -> str:
    if observation["provider"] != "markdown":
        raise ValueError("unexpected evidence provider")
    if observation["native_handle"] not in {
        "study_a.md", "study_b.md", "study_c.md", "summary.md"
    }:
        raise ValueError("unexpected evidence handle")
    digest = observation["source_revision"].removeprefix("sha256:")
    if observation["source_revision"] != "sha256:" + digest or len(digest) != 64:
        raise ValueError("invalid evidence revision")
    data = (bundle / "evidence" / digest).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("retained evidence digest mismatch")
    start, end = parse_byte_location(observation["native_location"])
    if not 0 <= start <= end <= len(data):
        raise ValueError("evidence span outside retained bytes")
    return data[start:end].decode("utf-8")


def inspect_source_only_fact(bundle: Path, reader: WorldExplorerAdapter) -> dict:
    c_study = next(row for row in reader.rows("study_finding")["rows"]
                   if row["values"]["study"] == "study:c")
    support = reader.assertion(c_study["assertion_id"])["grounding"]
    pointer = next(item for item in support if item.get("provider") == "markdown")
    digest = pointer["source_revision"].removeprefix("sha256:")
    data = (bundle / "evidence" / digest).read_bytes()
    phrase = b"Study C recorded high humidity during measurement."
    start = data.index(phrase)
    observation = {"provider": "markdown", "native_handle": "study_c.md",
                   "source_revision": pointer["source_revision"],
                   "native_location": f"bytes:{start}:{start + len(phrase)}"}
    return {"status": "source_only", "observation": observation,
            "text": source_text(bundle, observation), "published_assertion_id": None}


def joined_answer(citations: list[dict]) -> list[dict[str, str]]:
    by_relation = {name: [item["values"] for item in citations if item["relation"] == name]
                   for name in SELECTED_RELATIONS}
    outcomes = {item["finding"]: item["outcome"] for item in by_relation["finding_outcome"]}
    supports = {item["finding"] for item in by_relation["finding_supports_claim"]
                if item["claim"] == "claim:cooling"}
    return sorted(({"study": item["study"], "finding": item["finding"],
                    "outcome": outcomes[item["finding"]]}
                   for item in by_relation["study_finding"] if item["finding"] in supports),
                  key=lambda item: item["study"])


def answer(bundle: Path) -> dict:
    with WorldExplorerAdapter(bundle / "world.sqlite") as reader:
        selected = [citation(reader, bundle, row["assertion_id"])
                    for relation in SELECTED_RELATIONS for row in reader.rows(relation)["rows"]]
        assert len(selected) == 12
        alternatives = sorted(item["values"]["direction"] for item in selected
                              if item["relation"] == "possible_humidity_effect")
        questions = [item["values"]["question"] for item in selected
                     if item["relation"] == "open_question"]
        return {"question": QUESTION, "publication": str(bundle), "citations": selected,
                "conclusion": joined_answer(selected),
                "unresolved": {"question": questions[0], "alternatives": alternatives,
                               "selected_direction": None},
                "negative_probe": {"question": "Did Study A report increased leaf temperature?",
                                   "status": "not established", "completeness_basis": None},
                "source_observation": inspect_source_only_fact(bundle, reader)}


def verify_result(result: dict) -> None:
    bundle = Path(result["publication"])
    if not bundle.is_absolute() or not (bundle / "world.sqlite").is_file():
        raise ValueError("publication must be an existing exact bundle address")
    with WorldExplorerAdapter(bundle / "world.sqlite") as reader:
        if result["question"] != QUESTION:
            raise ValueError("different question")
        seen = set()
        for claimed in result["citations"]:
            if claimed["publication"] != str(bundle):
                raise ValueError("citation belongs to another publication")
            assertion_id = claimed["assertion_id"]
            if assertion_id in seen:
                raise ValueError("duplicate citation")
            seen.add(assertion_id)
            try:
                actual = citation(reader, bundle, assertion_id)
            except KeyError as exc:
                raise ValueError("assertion absent from exact publication") from exc
            if actual != claimed:
                raise ValueError("citation content or support differs from publication")
            source_support = [item for item in actual["grounding"]
                              if item.get("kind") == "SOURCE"]
            if not source_support or not all(reconstruct_support(bundle, item)
                                             for item in source_support):
                raise ValueError("published support does not reconstruct")
        expected_ids = {row["assertion_id"] for relation in SELECTED_RELATIONS
                        for row in reader.rows(relation)["rows"]}
        if seen != expected_ids:
            raise ValueError("bounded selection omitted or added published assertions")
        if result["conclusion"] != joined_answer(result["citations"]):
            raise ValueError("local answer differs from cited join")
        alternative_values = sorted(item["values"]["direction"] for item in result["citations"]
                                    if item["relation"] == "possible_humidity_effect")
        question_values = [item["values"]["question"] for item in result["citations"]
                           if item["relation"] == "open_question"]
        if len(question_values) != 1 or result["unresolved"] != {
            "question": question_values[0], "alternatives": alternative_values,
            "selected_direction": None,
        }:
            raise ValueError("unresolved status differs from published alternatives")
        with_world = ConstructionWorld.open(bundle / "world.sqlite", read_only=True)
        try:
            receipt = with_world.latest_completeness("finding_outcome")
        finally:
            with_world.close()
        increased = any(item["values"] == {"finding": "finding:a",
                                              "outcome": "increased leaf temperature"}
                        for item in result["citations"] if item["relation"] == "finding_outcome")
        if increased or receipt is not None or result["negative_probe"] != {
            "question": "Did Study A report increased leaf temperature?",
            "status": "not established", "completeness_basis": None,
        }:
            raise ValueError("negative result exceeds published scope")
        note = result["source_observation"]
        if note["status"] != "source_only" or note["published_assertion_id"] is not None:
            raise ValueError("source observation claimed published standing")
        if note["text"] != source_text(bundle, note["observation"]):
            raise ValueError("source observation does not reconstruct")
        if "high humidity" not in note["text"]:
            raise ValueError("source-only fact missing from observation")
        for schema in reader.schema():
            for row in reader.rows(schema["name"])["rows"]:
                if "high humidity" in json.dumps(row["values"]):
                    raise ValueError("source-only fact was published")
        if "high humidity" in json.dumps(result["conclusion"]):
            raise ValueError("source-only fact entered published conclusion")


def test_bounded_answer_and_fresh_consumer(publications, tmp_path):
    first, _ = publications
    before = fingerprint(first)
    result = answer(first)
    assert [item["study"] for item in result["conclusion"]] == ["study:a", "study:b", "study:c"]
    assert all(item["outcome"] == "lower leaf temperature" for item in result["conclusion"])
    assert result["unresolved"]["selected_direction"] is None
    with WorldExplorerAdapter(first / "world.sqlite") as reader:
        assert sum(reader.rows(item["name"])["total"] for item in reader.schema()) > len(result["citations"])
        assert all(item["origin"] == "SEMANTIC" and item["grounding"] for item in result["citations"])
    payload = tmp_path / "local-result.json"
    payload.write_text(json.dumps(result), encoding="utf-8")
    completed = subprocess.run([sys.executable, "-m", "tests.test_oa_cross_domain_working_set_experiment",
                                str(payload)], cwd=HERE.parent, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert fingerprint(first) == before


def test_exact_publication_and_source_only_citations_are_rejected(publications):
    first, second = publications
    result = answer(first)
    with WorldExplorerAdapter(second / "world.sqlite") as reader:
        foreign = next(citation(reader, second, row["assertion_id"])
                       for row in reader.rows("finding_outcome")["rows"]
                       if row["values"]["finding"] == "finding:b")
        shared = next(citation(reader, second, row["assertion_id"])
                      for row in reader.rows("finding_outcome")["rows"]
                      if row["values"]["finding"] == "finding:a")
    assert foreign["assertion_id"] not in {item["assertion_id"] for item in result["citations"]}
    assert shared["assertion_id"] in {item["assertion_id"] for item in result["citations"]}
    for replacement in (foreign, shared):
        forged = json.loads(json.dumps(result))
        forged["citations"][0] = replacement
        with pytest.raises(ValueError, match="another publication"):
            verify_result(forged)
    forged = json.loads(json.dumps(result))
    forged["citations"][0] = {**foreign, "publication": str(first)}
    with pytest.raises(ValueError, match="absent from exact publication"):
        verify_result(forged)
    invented = json.loads(json.dumps(result))
    invented["citations"].append({"publication": str(first), "assertion_id": "invented:humidity",
                                  "relation": "study_humidity", "values": {"humidity": "high humidity"},
                                  "origin": "SEMANTIC", "grounding": []})
    with pytest.raises(ValueError, match="absent from exact publication"):
        verify_result(invented)
    decorated = json.loads(json.dumps(result))
    decorated["citations"][0]["values"]["humidity"] = "high humidity"
    with pytest.raises(ValueError, match="content or support differs"):
        verify_result(decorated)
    altered_support = json.loads(json.dumps(result))
    altered_support["citations"][0]["grounding"] = []
    with pytest.raises(ValueError, match="content or support differs"):
        verify_result(altered_support)
    verify_result(result)


def test_open_world_absence_and_published_unresolvedness(publications):
    first, _ = publications
    result = answer(first)
    assert not any(item["outcome"] == "increased leaf temperature" for item in result["conclusion"])
    assert result["negative_probe"]["status"] == "not established"
    world = ConstructionWorld.open(first / "world.sqlite", read_only=True)
    try:
        assert world.latest_completeness("finding_outcome") is None
    finally:
        world.close()
    assert result["unresolved"]["alternatives"] == ["decreases cooling", "increases cooling"]
    assert result["unresolved"]["selected_direction"] is None
    # The empty selected match licenses only "not established", not a negative study finding.
    assert "increased leaf temperature is false" not in json.dumps(result)
    bad = json.loads(json.dumps(result))
    bad["citations"][0]["assertion_id"] = "missing"
    with pytest.raises(ValueError, match="absent from exact publication"):
        verify_result(bad)


def test_experiment_imports_no_design_application():
    forbidden = ("ontology_author.software_governance", "profiles.software_governance",
                 "ontology_author.governance", "ontology_author.semantic_binding",
                 "ontology_author.program_spine")
    for path in (CONSTRUCTION, Path(__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                   for alias in node.names]
        imports += [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                    and node.module]
        assert not any(module == prefix or module.startswith(prefix + ".")
                       for module in imports for prefix in forbidden)


if __name__ == "__main__":
    verify_result(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))

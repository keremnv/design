"""Phase 5A behavioral expectations reusable through a test-local fixture.

The fixture translates production output, not expected answers. A future
backend supplies these scenarios/read views; assertions stay unchanged.
Native-specific identifiers, files and coordinates belong only in the fixture.
"""

import json

import pytest

from tests.program_backend_native_fixture import NativeFixture


@pytest.fixture(params=[NativeFixture], ids=["native-spine"])
def backend(request, tmp_path):
    return request.param(tmp_path)


def selected(backend, read, label="source"):
    return backend.select(read, label)


def assert_distinct_occurrences(first, second):
    assert first["occurrence"] != second["occurrence"]


def assert_unproduced(result):
    assert result["capability"]["status"] == "NOT_PRODUCED"
    assert result["rows"] is None
    assert not result["capability"]["completeness_receipt_refs"]


def test_exact_occurrence_is_not_content_equivalence(backend):
    first = backend.produce("leaf")
    copy = backend.copy(first)
    roundtrip = backend.deserialize(json.loads(json.dumps(backend.serialize(first))))
    with backend.open(roundtrip) as old, backend.open(copy) as copied:
        a, b = old.descriptor(), copied.descriptor()
        assert_distinct_occurrences(a, b)
        assert old.qualify(first) == []
        assert copied.qualify(first)
        # Local tokens and snapshot tokens may coincide or differ on a copy;
        # exact references differ while reconstructed observed material agrees.
        original_entity = selected(backend, old)
        copied_entity = selected(backend, copied)
        assert original_entity != copied_entity
        assert old.inspect(original_entity)["kind"] == copied.inspect(copied_entity)["kind"]
        assert [old.reconstruct(o) for o in old.observations(original_entity)] == [
            copied.reconstruct(o) for o in copied.observations(copied_entity)]
    with pytest.raises(Exception):
        with backend.open(backend.wrong_qualification(first)):
            pytest.fail("wrong occurrence qualification was accepted")
    with pytest.raises(Exception):
        with backend.open(backend.unavailable(first)):
            pytest.fail("unavailable occurrence resolved elsewhere")


def test_historical_reads_and_entity_membership_do_not_follow_latest(backend):
    first = backend.produce("leaf")
    fingerprint = backend.fingerprint(first)
    with backend.open(first) as old:
        old_descriptor = old.descriptor()
        entity = selected(backend, old)
        record = old.inspect(entity)
        observations = old.observations(entity)
        assert observations
        material = [old.reconstruct(o) for o in observations]
        assert all(r["verified"] for r in material)
        assert any("é😀" in r["material"] for r in material)
    second = backend.produce("same_label")
    with backend.open(second) as new:
        other = selected(backend, new)
        assert new.descriptor()["snapshot"] != old_descriptor["snapshot"]
        assert other != entity
        if record.get("label") is not None:
            assert new.inspect(other)["label"] == record["label"]
        assert new.inspect(entity) is None
        assert all(not new.reconstruct(o)["verified"] for o in observations)
        with pytest.raises(ValueError):
            new.observations(entity)
        with pytest.raises(ValueError):
            new.facts("containment", entity)
    backend.delete_workspace()
    with backend.open(first) as reopened:
        assert reopened.descriptor() == old_descriptor
        assert reopened.inspect(entity) == record
        assert reopened.inspect(other) is None
        assert [reopened.reconstruct(o) for o in observations] == material
        assert reopened.verify() == []
    assert backend.fingerprint(first) == fingerprint


def test_duplicate_labels_do_not_merge_entity_identity(backend):
    if not backend.discovery_supported:
        pytest.skip("optional label discovery unsupported")
    reference = backend.produce("duplicate_labels")
    with backend.open(reference) as read:
        entities = read.discover("source")
        assert len(entities) == len(set(entities)) == 2
        assert all(read.inspect(e)["kind"] == "callable" for e in entities)
        assert all(read.observations(e) for e in entities)


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_evidence_verifies_qualification_and_retained_closure(backend, damage):
    reference = backend.produce("leaf")
    with backend.open(reference) as read:
        observations = read.observations(selected(backend, read))
        assert observations
        observation = observations[0]
        assert read.reconstruct(observation)["verified"]
        assert not read.reconstruct(backend.wrong_observation_revision(observation))["verified"]
        assert read.verify() == []
    damaged = backend.copy(reference)
    backend.damage_evidence(damaged, observation, damage)
    # Live workspace still exists: it cannot repair retained evidence silently.
    with backend.open(damaged) as read:
        assert not read.reconstruct(observation)["verified"]
        assert read.verify()
    with backend.open(reference) as read:
        assert read.verify() == []
        assert read.reconstruct(observation)["verified"]


def test_capability_not_produced_is_not_supported_empty(backend):
    reference = backend.produce("leaf")
    with backend.open(reference) as read:
        assert_unproduced(read.facts("unproduced"))
        context = read.facts("containment", selected(backend, read))
        assert context["capability"]["status"] in {"COMPLETE", "STATIC_COMPLETE"}
        assert context["capability"]["scope"]
        assert context["capability"]["completeness_basis"]
        assert context["capability"]["completeness_receipt_refs"]
        descriptor = read.descriptor()
        assert descriptor["scope"] and descriptor["inputs"] and descriptor["losses"]


def test_optional_produced_call_capability_can_be_empty(backend):
    if not backend.supports("invocation"):
        pytest.skip("invocation production unsupported")
    reference = backend.produce("leaf")
    with backend.open(reference) as read:
        calls = read.facts("invocation")
        assert calls["rows"] == []
        assert calls["capability"]["status"] in {"COMPLETE", "STATIC_COMPLETE"}
        assert calls["capability"]["scope"]
        assert calls["capability"]["completeness_basis"]
        assert calls["capability"]["completeness_receipt_refs"]


def test_typed_mechanical_facts_preserve_roles_and_snapshot(backend):
    reference = backend.produce("relations")
    with backend.open(reference) as read:
        target = selected(backend, read, "target")
        context = read.facts("containment", target)
        assert any(row["child"] == target and row["parent"] != target for row in context["rows"])
        assert context["snapshot"] == read.descriptor()["snapshot"]
        assert [(r["name"], r["type"]) for r in context["schema"]["roles"]] == [
            ("parent", "entity"), ("child", "entity")]


def test_optional_produced_relations_preserve_entity_and_literal_roles(backend):
    if not backend.supports("invocation") or not backend.supports("resolution"):
        pytest.skip("invocation/resolution production unsupported")
    reference = backend.produce("relations")
    with backend.open(reference) as read:
        target = selected(backend, read, "target")
        calls = read.facts("invocation", target)
        assert len(calls["rows"]) == 1
        roles = calls["schema"]["roles"]
        assert [(r["name"], r["type"]) for r in roles] == [
            ("call_site", "entity"), ("target", "entity")]
        call = calls["rows"][0]
        assert call["target"] == target
        assert read.inspect(call["call_site"])["kind"] == "call_site"
        assert calls["snapshot"] == read.descriptor()["snapshot"]
        resolutions = read.facts("resolution", call["call_site"])
        assert any(row["subject"] == call["call_site"] and row["status"] == "RESOLVED"
                   for row in resolutions["rows"])
        assert any(r["name"] == "status" and r["type"] == "text"
                   for r in resolutions["schema"]["roles"])


def test_unresolved_and_incomplete_do_not_establish_negative_calls(backend):
    if not backend.supports("invocation") or not backend.supports("resolution"):
        pytest.skip("invocation/resolution production unsupported")
    unresolved = backend.produce("unresolved")
    with backend.open(unresolved) as read:
        assert read.facts("invocation")["rows"] == []
        outcomes = read.facts("resolution")["rows"]
        assert any(row["status"] == "UNRESOLVED" for row in outcomes)
        assert all(read.inspect(row["subject"]) for row in outcomes)
    incomplete = backend.produce("incomplete")
    with backend.open(incomplete) as read:
        calls = read.facts("invocation")
        assert calls["capability"]["status"] == "INCOMPLETE"
        assert calls["capability"]["known_gaps"]


def test_optional_comparison_is_qualified_heuristic_and_read_only(backend):
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported; core cases still run")
    old = backend.produce("leaf")
    before = backend.fingerprint(old)
    new = backend.produce("rename")
    newer_before = backend.fingerprint(new)
    with backend.open(old) as read:
        entity = selected(backend, read)
    result = backend.compare(old, new)
    assert result["old"] == backend.serialize(old)
    assert result["new"] == backend.serialize(new)
    claim = next(c for c in result["claims"] if c["old_entity"] == entity)
    assert claim["outcome"] == "RENAME"
    assert claim["basis_class"] == "HEURISTIC"
    assert claim["continuity"] == "CONTINUED"
    assert claim["old_entity"] != claim["new_entity"]
    assert claim["evidence"] and claim["limitations"]
    assert claim["changes"]["name"] == "CHANGED"
    assert result["changes"]
    assert backend.compare(old, new) == result
    assert backend.fingerprint(old) == before
    assert backend.fingerprint(new) == newer_before


def test_core_reads_do_not_require_comparison(backend):
    backend.comparison_supported = False  # test-local service configuration
    old, new = backend.produce("leaf"), backend.produce("same_label")
    assert backend.compare(old, new) is None
    for reference in (old, new):
        with backend.open(reference) as read:
            entity = selected(backend, read)
            assert read.inspect(entity)
            assert read.facts("containment", entity)["rows"]
            observations = read.observations(entity)
            assert observations and all(read.reconstruct(o)["verified"] for o in observations)
            assert read.verify() == []


def test_optional_comparison_preserves_ambiguity(backend):
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported")
    old, new = backend.produce("leaf"), backend.produce("ambiguous")
    with backend.open(old) as read:
        entity = selected(backend, read)
    result = backend.compare(old, new)
    ambiguous = [r for r in result["ambiguities"] if r["old_entity"] == entity]
    assert len(ambiguous) == 1
    assert len(set(ambiguous[0]["candidate_entities"])) == 2
    claims = [c for c in result["claims"] if c["old_entity"] == entity]
    assert claims and all(c["continuity"] == "AMBIGUOUS" for c in claims)
    assert all(c["basis_class"] == "HEURISTIC" for c in claims)
    assert not any(c["continuity"] == "CONTINUED" for c in claims)


@pytest.mark.parametrize("mode", ["capability", "representation"])
def test_optional_comparison_declares_incompatible_capability(backend, mode):
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported")
    old = backend.produce("leaf")
    new = backend.copy(old)
    backend.incompatible(new, mode)
    result = backend.compare(old, new)
    assert result["incomparable"]
    incompatible = [c for c in result["compatibility"]["capabilities"]
                    if c["status"] == "NOT_COMPARABLE"]
    assert incompatible and all(c["limitations"] for c in incompatible)
    if mode == "representation":
        assert result["compatibility"]["status"] == "INCOMPATIBLE"
        assert result["compatibility"]["limitations"]


def test_discriminating_assertions_reject_dishonest_empty_and_collapsed_copy():
    # Negative controls for two easy-to-mask violations; production-backed
    # cases above exercise history, membership and reconstruction falsifiers.
    with pytest.raises(AssertionError):
        assert_unproduced({"capability": {"status": "NOT_PRODUCED",
                                           "completeness_receipt_refs": []}, "rows": []})
    with pytest.raises(AssertionError):
        assert_distinct_occurrences({"occurrence": "same"}, {"occurrence": "same"})

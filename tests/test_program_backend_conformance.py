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
    # Semantic: unsupported/not-produced must not license absence.
    # Honest representations include rows=None or rows=[] with NOT_PRODUCED
    # and no closure/complete interpretation. Only supported+complete+empty
    # (or any closure claim) for an unproduced relation is dishonest.
    assert result["capability"]["status"] == "NOT_PRODUCED"
    assert result["rows"] is None or result["rows"] == []
    assert not result["capability"]["completeness_receipt_refs"]
    # Status vocabulary is test projection, not a mandated backend wire enum;
    # future fixtures project their own unsupported signal into NOT_PRODUCED.


def assert_supported_complete_capability(capability):
    # Behavioral: sufficient qualification to interpret absence, without
    # mandating native receipt references or universal enums.
    assert capability["status"] in {"COMPLETE", "STATIC_COMPLETE"}
    assert capability["scope"]
    assert capability["completeness_basis"]
    # completeness_receipt_refs intentionally not required: a valid backend
    # may encode completeness without a receipt reference.


def ancestor_chain(backend_read, entity, limit=6):
    # Bounded ancestor-context walk using typed containment rows only.
    # Returns [root, ..., entity] in the demonstrated warrant direction.
    rows = backend_read.facts("containment")["rows"]
    parent_of = {r["child"]: r["parent"] for r in rows}
    chain = [entity]
    seen = {entity}
    while chain[0] in parent_of and len(chain) <= limit:
        parent = parent_of[chain[0]]
        if parent in seen:
            break
        chain.insert(0, parent)
        seen.add(parent)
    return chain


def assert_transferable_comparison(result, backend, old, new):
    # Backend-neutral optional comparison honesty. Allows qualified
    # correspondence OR explicit unsupported/refused correspondence, provided
    # the service remains honest. Never mandates native matching decisions.
    assert result["old"] == backend.serialize(old)
    assert result["new"] == backend.serialize(new)
    assert "compatibility" in result and "incomparable" in result
    status = result.get("correspondence_status",
                        "PRODUCED" if result.get("claims") else "UNSUPPORTED")
    if status in ("UNSUPPORTED", "REFUSED_NONUNIQUE"):
        assert result["claims"] == []
        assert result.get("correspondence_limitations")
        return status
    for claim in result.get("claims", []):
        if claim["old_entity"] is not None and claim["new_entity"] is not None:
            assert claim["old_entity"] != claim["new_entity"]
            assert backend.serialize(backend.occurrence_of(claim["old_entity"])) == result["old"]
            assert backend.serialize(backend.occurrence_of(claim["new_entity"])) == result["new"]
            assert claim["basis_class"] and claim["evidence"] and claim["limitations"]
        else:
            assert claim["basis_class"] and claim["evidence"]
    for ambiguity in result.get("ambiguities", []):
        assert len(set(ambiguity["candidate_entities"])) >= 2
        for candidate in ambiguity["candidate_entities"]:
            assert backend.serialize(backend.occurrence_of(candidate)) == result["new"]
    return status


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


def test_wrong_snapshot_qualification_is_rejected(backend):
    # R2/R3/R5 discriminator: correct occurrence, wrong snapshot, valid token.
    first = backend.produce("leaf")
    second = backend.produce("same_label")
    with backend.open(first) as old, backend.open(second) as new:
        old_descriptor, new_descriptor = old.descriptor(), new.descriptor()
        assert old_descriptor["snapshot"] != new_descriptor["snapshot"]
        entity = selected(backend, old)
        forged = backend.misqualify(entity, snapshot=new_descriptor["snapshot"])
        assert forged != entity
        assert backend.native_token(forged) == backend.native_token(entity)
        assert old.inspect(forged) is None
        with pytest.raises(ValueError):
            old.facts("containment", forged)
        with pytest.raises(ValueError):
            old.observations(forged)
        # Evidence qualification through entity context: wrong-qualified
        # reaches no observations, correct-qualified reaches observations.
        with pytest.raises(ValueError):
            old.observations(forged)
        assert old.observations(entity)
        assert old.inspect(entity) is not None
        assert old.facts("containment", entity)["rows"]
        other = selected(backend, new)
        forged_other = backend.misqualify(other, snapshot=old_descriptor["snapshot"])
        assert new.inspect(forged_other) is None
        with pytest.raises(ValueError):
            new.facts("containment", forged_other)
        with pytest.raises(ValueError):
            new.observations(forged_other)


def test_copied_occurrence_does_not_accept_original_qualified_entity(backend):
    # R1/R3 token-collision discriminator: same snapshot token, same native
    # entity token, same content, while the exact retained occurrence differs.
    # EntityToken != QualifiedEntityOccurrence; IDs need not encode context.
    first = backend.produce("leaf")
    copy = backend.copy(first)
    with backend.open(first) as old, backend.open(copy) as copied:
        first_descriptor, copy_descriptor = old.descriptor(), copied.descriptor()
        assert_distinct_occurrences(first_descriptor, copy_descriptor)
        assert first_descriptor["snapshot"] == copy_descriptor["snapshot"]
        original = selected(backend, old)
        copied_entity = selected(backend, copied)
        assert original != copied_entity
        assert backend.native_token(original) == backend.native_token(copied_entity)
        assert [old.reconstruct(o) for o in old.observations(original)] == [
            copied.reconstruct(o) for o in copied.observations(copied_entity)]
        assert copied.inspect(original) is None
        with pytest.raises(ValueError):
            copied.facts("containment", original)
        with pytest.raises(ValueError):
            copied.observations(original)
        assert copied.inspect(copied_entity) is not None
        assert copied.facts("containment", copied_entity)["rows"]
        assert copied.observations(copied_entity)
        assert old.inspect(copied_entity) is None
        with pytest.raises(ValueError):
            old.facts("containment", copied_entity)
        with pytest.raises(ValueError):
            old.observations(copied_entity)


def test_historical_reads_and_entity_membership_do_not_follow_latest(backend):
    # R7 load-bearing: historical facts/capabilities/observations must not
    # follow latest. A backend with local membership but latest fact lookup fails.
    first = backend.produce("leaf")
    fingerprint = backend.fingerprint(first)
    with backend.open(first) as old:
        old_descriptor = old.descriptor()
        entity = selected(backend, old)
        record = old.inspect(entity)
        containment = old.facts("containment", entity)
        assert containment["rows"]
        assert containment["snapshot"] == old_descriptor["snapshot"]
        invocation = old.facts("invocation")
        resolution = old.facts("resolution")
        inv_produced = invocation["capability"]["status"] != "NOT_PRODUCED"
        res_produced = resolution["capability"]["status"] != "NOT_PRODUCED"
        observations = old.observations(entity)
        assert observations
        material = [old.reconstruct(o) for o in observations]
        assert all(r["verified"] for r in material)
        assert any("é😀" in r["material"] for r in material)
    second = backend.produce("same_label")
    with backend.open(second) as new:
        other = selected(backend, new)
        new_descriptor = new.descriptor()
        assert new_descriptor["snapshot"] != old_descriptor["snapshot"]
        assert other != entity
        if record.get("label") is not None:
            assert new.inspect(other)["label"] == record["label"]
        assert new.inspect(entity) is None
        assert all(not new.reconstruct(o)["verified"] for o in observations)
        with pytest.raises(ValueError):
            new.observations(entity)
        with pytest.raises(ValueError):
            new.facts("containment", entity)
        other_observations = new.observations(other)
        other_material = [new.reconstruct(o) for o in other_observations]
        assert all(r["verified"] for r in other_material)
        assert other_observations != observations
    # Deliberately distinguishable successor for core fact/capability
    # stability (containment/observations/descriptor differ unconditionally).
    # Invocation/resolution distinguishability is conditional on production.
    third = backend.produce("relations")
    with backend.open(third) as distinguished:
        distinguished_descriptor = distinguished.descriptor()
        assert distinguished_descriptor["snapshot"] != old_descriptor["snapshot"]
        relations_entity = backend.select(distinguished, "target")
        relations_invocation = distinguished.facts("invocation")
        relations_resolution = distinguished.facts("resolution")
        if inv_produced and relations_invocation["capability"]["status"] != "NOT_PRODUCED":
            assert len(relations_invocation["rows"]) == 1
            assert len(invocation["rows"] or []) == 0
            assert relations_invocation["rows"] != (invocation["rows"] or [])
        if res_produced and relations_resolution["capability"]["status"] != "NOT_PRODUCED":
            assert len(relations_resolution["rows"]) == 1
            assert len(resolution["rows"] or []) == 0
        relations_containment = distinguished.facts("containment", relations_entity)
        assert relations_containment["rows"] != containment["rows"]
        assert relations_containment["snapshot"] == distinguished_descriptor["snapshot"]
        relations_observations = distinguished.observations(relations_entity)
        relations_material = [distinguished.reconstruct(o) for o in relations_observations]
        assert all(r["verified"] for r in relations_material)
        assert relations_observations != observations
    backend.delete_workspace()
    with backend.open(first) as reopened:
        assert reopened.descriptor() == old_descriptor
        assert reopened.inspect(entity) == record
        assert reopened.inspect(other) is None
        assert reopened.inspect(relations_entity) is None
        reopened_containment = reopened.facts("containment", entity)
        assert reopened_containment == containment
        assert reopened_containment["snapshot"] == old_descriptor["snapshot"]
        assert reopened_containment["capability"] == containment["capability"]
        reopened_invocation = reopened.facts("invocation")
        reopened_resolution = reopened.facts("resolution")
        if inv_produced:
            assert reopened_invocation == invocation
        else:
            assert reopened_invocation["capability"]["status"] == "NOT_PRODUCED"
            assert reopened_invocation["rows"] is None or reopened_invocation["rows"] == []
        if res_produced:
            assert reopened_resolution == resolution
        else:
            assert reopened_resolution["capability"]["status"] == "NOT_PRODUCED"
            assert reopened_resolution["rows"] is None or reopened_resolution["rows"] == []
        # Fresh observation lookup must be historical, not latest.
        fresh = reopened.observations(entity)
        assert fresh == observations
        assert [reopened.reconstruct(o) for o in fresh] == material
        assert [reopened.reconstruct(o) for o in observations] == material
        assert reopened.verify() == []
    # Fresh lookups in successors remain independently local.
    with backend.open(second) as new:
        assert new.observations(other) == other_observations
        assert [new.reconstruct(o) for o in new.observations(other)] == other_material
    with backend.open(third) as distinguished:
        assert distinguished.observations(relations_entity) == relations_observations
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
    # R6 semantic: unsupported/not-produced != supported-empty. Behavioral
    # qualification only; no universal rows=None or receipt/input/loss shape.
    reference = backend.produce("leaf")
    with backend.open(reference) as read:
        assert_unproduced(read.facts("unproduced"))
        context = read.facts("containment", selected(backend, read))
        assert_supported_complete_capability(context["capability"])
        assert context["capability"]["status"] != read.facts("unproduced")["capability"]["status"]
        descriptor = read.descriptor()
        assert descriptor["scope"]
        # inputs/losses/completeness_receipt_refs intentionally not required:
        # a valid backend may have no known losses, encode completeness
        # without a receipt reference, or represent inputs differently.


def test_optional_produced_call_capability_can_be_empty(backend):
    # Supported-empty positive discriminator: supported capability, declared
    # relevant scope/completeness, zero observed rows. Semantically distinct
    # from unsupported/not-produced, incomplete-empty and unresolved.
    if not backend.supports("invocation"):
        pytest.skip("invocation production unsupported")
    reference = backend.produce("leaf")
    with backend.open(reference) as read:
        calls = read.facts("invocation")
        assert calls["rows"] == []
        assert_supported_complete_capability(calls["capability"])
        assert calls["capability"]["status"] != read.facts("unproduced")["capability"]["status"]


def test_typed_mechanical_facts_preserve_roles_and_snapshot(backend):
    reference = backend.produce("relations")
    with backend.open(reference) as read:
        target = selected(backend, read, "target")
        context = read.facts("containment", target)
        assert any(row["child"] == target and row["parent"] != target for row in context["rows"])
        assert context["snapshot"] == read.descriptor()["snapshot"]
        assert [(r["name"], r["type"]) for r in context["schema"]["roles"]] == [
            ("parent", "entity"), ("child", "entity")]
        # Bounded ancestor-context discriminator (Phase 4 warrant direction):
        # selected callable -> source_unit -> module, with correct mechanical
        # roles and direction. Rejects false outer ancestors that preserve
        # shape, qualification, capability and length but change meaning.
        chain = ancestor_chain(read, target)
        assert chain[-1] == target
        assert len(chain) >= 3
        kinds = [read.inspect(e)["kind"] for e in chain]
        assert kinds[-1] == "callable"
        assert kinds[-2] == "source_unit"
        assert kinds[-3] == "module"
        edges = {(r["parent"], r["child"]) for r in read.facts("containment")["rows"]}
        assert (chain[-3], chain[-2]) in edges
        assert (chain[-2], chain[-1]) in edges
        # No arbitrary graph traversal required; immediate chain suffices.


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
    # Native comparison regression: asserts the native rename heuristic
    # (RENAME/HEURISTIC/CONTINUED, name CHANGED). Transferable contract is
    # covered separately without these algorithm-specific judgments.
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


def test_optional_comparison_transferable_semantics_are_qualified_and_honest(backend):
    # Backend-neutral optional conformance: qualified old/new, explicit
    # compatibility/refusal, qualified changes if exposed, exposed basis if
    # correspondence claimed, no identity collapse, preserved ambiguity if
    # reported, no mutation. Does not mandate correspondence production.
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported")
    old = backend.produce("leaf")
    before = backend.fingerprint(old)
    new = backend.produce("rename")
    newer_before = backend.fingerprint(new)
    result = backend.compare(old, new)
    assert_transferable_comparison(result, backend, old, new)
    assert result["changes"]
    assert backend.compare(old, new) == result
    assert backend.fingerprint(old) == before
    assert backend.fingerprint(new) == newer_before
    # Ambiguous pair: if the service reports ambiguity it must preserve
    # candidates; if it refuses nonunique matching that refusal is valid and
    # covered by the nonunique-refusal case. Never mandate native ambiguity.
    ambiguous_new = backend.produce("ambiguous")
    ambiguous_result = backend.compare(old, ambiguous_new)
    assert_transferable_comparison(ambiguous_result, backend, old, ambiguous_new)
    assert ambiguous_result["changes"]


def test_optional_comparison_correspondence_unsupported_is_valid(backend):
    # A service may report mechanical changes while declaring correspondence
    # unsupported, without failing transferable conformance. It must not imply
    # no change, same identity or no relevant difference.
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported")
    old = backend.produce("leaf")
    before = backend.fingerprint(old)
    new = backend.produce("rename")
    newer_before = backend.fingerprint(new)
    result = backend.compare_refused(old, new, "UNSUPPORTED")
    assert assert_transferable_comparison(result, backend, old, new) == "UNSUPPORTED"
    assert result["changes"]
    assert backend.compare_refused(old, new, "UNSUPPORTED") == result
    assert backend.fingerprint(old) == before
    assert backend.fingerprint(new) == newer_before


def test_optional_comparison_nonunique_refusal_is_valid(backend):
    # A service may refuse nonunique correspondence instead of returning
    # native-style ambiguity. If it does report ambiguity, multiple candidates
    # must remain explicit with no arbitrary winner (checked by the helper).
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported")
    old = backend.produce("leaf")
    new = backend.produce("ambiguous")
    result = backend.compare_refused(old, new, "REFUSED_NONUNIQUE")
    assert assert_transferable_comparison(result, backend, old, new) == "REFUSED_NONUNIQUE"
    assert result["changes"]
    assert result["ambiguities"] == []


def test_optional_comparison_preserves_exact_occurrence_context_for_copies(backend):
    # Exact occurrence qualification is tested independently of correspondence
    # production. Copies share snapshot/entity tokens and bytes but invocations
    # remain associated with different exact old occurrences.
    if not backend.comparison_supported:
        pytest.skip("optional comparison unsupported")
    original = backend.produce("leaf")
    copy = backend.copy(original)
    new = backend.produce("rename")
    with backend.open(original) as a, backend.open(copy) as b:
        assert a.descriptor()["snapshot"] == b.descriptor()["snapshot"]
        assert_distinct_occurrences(a.descriptor(), b.descriptor())
        assert backend.native_token(selected(backend, a)) == backend.native_token(selected(backend, b))
    first = backend.compare(original, new)
    second = backend.compare(copy, new)
    assert_transferable_comparison(first, backend, original, new)
    assert_transferable_comparison(second, backend, copy, new)
    assert first["old"] != second["old"]
    assert first["new"] == second["new"]
    for result in (first, second):
        for claim in result.get("claims", []):
            if claim["old_entity"] is not None:
                assert backend.serialize(backend.occurrence_of(claim["old_entity"])) == result["old"]
    # Honest refusal preserves the same context distinction without claims.
    refused_first = backend.compare_refused(original, new, "UNSUPPORTED")
    refused_second = backend.compare_refused(copy, new, "UNSUPPORTED")
    assert refused_first["old"] != refused_second["old"]
    assert refused_first["new"] == refused_second["new"]
    # No persistent cross-snapshot identity is required.


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
    # Native comparison regression: specific two-candidate ambiguous scenario
    # and native AMBIGUOUS/HEURISTIC vocabulary. Transferable ambiguity
    # preservation is covered without these algorithm-specific judgments.
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
    # Native comparison regression for native compatibility behavior; the
    # transferable obligation is honest compatibility/refusal declaration.
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
    # Negative controls: honest NOT_PRODUCED accepts None or [] without
    # closure; only supported+complete+empty (closure claim) is dishonest.
    assert_unproduced({"capability": {"status": "NOT_PRODUCED",
                                       "completeness_receipt_refs": []}, "rows": None})
    assert_unproduced({"capability": {"status": "NOT_PRODUCED",
                                       "completeness_receipt_refs": []}, "rows": []})
    with pytest.raises(AssertionError):
        assert_unproduced({"capability": {"status": "COMPLETE",
                                           "completeness_receipt_refs": ["assertion:example"]},
                            "rows": []})
    with pytest.raises(AssertionError):
        assert_unproduced({"capability": {"status": "NOT_PRODUCED",
                                           "completeness_receipt_refs": ["assertion:example"]},
                            "rows": []})
    with pytest.raises(AssertionError):
        assert_distinct_occurrences({"occurrence": "same"}, {"occurrence": "same"})

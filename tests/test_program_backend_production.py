"""Production ProgramBackend conformance: the Phase 5A contract via the real adapter.

Re-runs every Phase 5A behavioral case with program-content reads served
by the production ``NativeProgramBackend`` instead of the test-only native
projection. Occurrence envelopes, receipt metadata, display labels, and
comparison invocation stay test-side (as in Phase 5A); membership, kind,
facts, capability, observations, reconstruction, and verification go
through the production boundary. Also proves the migrated authority
constructor reads program state through the backend, not candidate rows.
"""

from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import pytest

from ontology_author.authority import AuthorityUniverse, ReferentResolution, RelationSupport
from ontology_author.authority.construction import AuthorityConstructor
from ontology_author.authority.lifecycle import make_writable_copy
from ontology_author.evidence.program_source import program_source_observations
from ontology_author.program_backend import (
    CapabilityStatus, OccurrenceQualificationError, OptionalUnsupported, ProgramBackend,
)
from ontology_author.program_backend.native import NativeProgramBackend, _project_capability, open_native_occurrence
from ontology_author.world.runtime.world import ConstructionWorld
from tests.program_backend_native_fixture import NativeFixture, NativeRead
from tests.program_backend_lazy_fixture import LazyBackend, LazyCallsBackend

# Re-run the exact Phase 5A cases (same functions, no drift) against the
# production-backed fixture defined below. The local `backend` fixture
# shadows the imported Phase 5A one for this module only.
from tests.test_program_backend_conformance import *  # noqa: F401,F403,E402

_ROLE_SCHEMA = {
    "containment": (("parent", "entity"), ("child", "entity")),
    "invocation": (("call_site", "entity"), ("target", "entity")),
    "resolution": (
        ("subject", "entity"),
        ("status", "text"),
        ("capability", "text"),
    ),
}

class ProductionRead(NativeRead):
    """Phase 5A read view with content served by the production adapter."""

    def __init__(self, world, adapter: ProgramBackend) -> None:
        super().__init__(world)
        self.adapter = adapter

    def descriptor(self):
        base = super().descriptor()
        base["snapshot"] = self.adapter.snapshot()
        return base

    def entity_reference(self, token):
        return (self.reference, self.adapter.snapshot(), token)

    def inspect(self, entity):
        occurrence, snapshot, token = entity
        if occurrence != self.reference or snapshot != self.adapter.snapshot():
            return None
        if not self.adapter.is_member(token):
            return None
        kind = self.adapter.kind(token)
        label_rows = self.world.query(
            "SELECT label FROM _world_referents WHERE id=?", (token,)
        )
        label = label_rows[0]["label"] if label_rows else ""
        boundary_rows = [
            row for row in self.world.relation_rows("program_entity")
            if row["snapshot"] == self.snapshot["snapshot"] and row["entity"] == token
        ]
        boundary = boundary_rows[0]["boundary"] if boundary_rows else ""
        return {
            "entity": entity,
            "kind": kind,
            "label": label,
            "boundary": boundary,
            "snapshot": self.adapter.snapshot(),
        }

    def discover(self, label, kind="callable"):
        return [
            self.entity_reference(token)
            for token in self.adapter.discover(label=label, kind=kind)
        ]

    def facts(self, kind, entity=None):
        if kind == "unproduced":
            capability = self.adapter.capability("spine.component_usage")
            return {
                "capability": _capability_dict(capability),
                "schema": None,
                "rows": None,
            }
        capability = self.adapter.capability(kind)
        if entity is not None and self.inspect(entity) is None:
            raise ValueError("entity is not in the opened snapshot")
        if capability.status.value == "NOT_PRODUCED":
            return {"capability": _capability_dict(capability), "schema": None, "rows": None}
        # Phase 5A's test view permits unscoped reads. Build those views using
        # optional native discovery plus scoped production reads; enumeration
        # is test/extension machinery, not an obligation of ProgramBackend.
        if kind == "containment":
            tokens = (entity[2],) if entity is not None else self.adapter.discover()
            rows = [row for token in tokens for row in self.adapter.containment(token)]
        elif kind == "invocation":
            tokens = self.adapter.discover(kind="call_site")
            rows = [row for token in tokens for row in self.adapter.invocations(token)]
        else:
            tokens = (entity[2],) if entity is not None else self.adapter.discover(kind="call_site")
            rows = [row for token in tokens for row in self.adapter.resolutions(token)]
        rows = [dict(items) for items in dict.fromkeys(tuple(row.items()) for row in rows)]
        if entity is not None:
            rows = tuple(
                row for row in rows
                if any(value == entity[2] for key, value in row.items())
            )
        projected = [
            {
                key: self.entity_reference(value)
                if role == "entity" else value
                for (key, role), value in zip(
                    _ROLE_SCHEMA[kind], (row[name] for name, _ in _ROLE_SCHEMA[kind])
                )
            }
            for row in rows
        ]
        roles = [{"name": name, "type": role} for name, role in _ROLE_SCHEMA[kind]]
        return {
            "capability": _capability_dict(capability),
            "schema": {"roles": roles},
            "rows": projected,
            "snapshot": self.adapter.snapshot(),
        }

    def observations(self, entity):
        if self.inspect(entity) is None:
            raise ValueError("entity is not in the opened snapshot")
        return [dict(item) for item in self.adapter.observations(entity[2])]

    def reconstruct(self, observation):
        text, verified = self.adapter.reconstruct(observation)
        return {"verified": verified, "material": text}

    def verify(self):
        return list(self.adapter.verify())


def _capability_dict(capability):
    return {
        "status": capability.status.value,
        "scope": capability.scope,
        "completeness_basis": capability.basis,
        "completeness_receipt_refs": [],
        "known_gaps": list(capability.gaps),
    }


class ProductionFixture(NativeFixture):
    """Native fixture whose read views go through the production adapter."""

    @contextmanager
    def open_at(self, path):
        world = ConstructionWorld.open(path / "world.sqlite", read_only=True)
        adapter = open_native_occurrence(path)
        try:
            yield ProductionRead(world, adapter)
        finally:
            adapter.close()
            world.close()


@pytest.fixture(params=[ProductionFixture], ids=["production-adapter"])
def backend(request, tmp_path):
    return request.param(tmp_path)


def test_migrated_constructor_reads_program_state_through_backend(tmp_path):
    """The migrated consumer serves program reads from the backend.

    The candidate carries no program plane at all, so every membership,
    kind, snapshot, context, and fact answer below must come through the
    production boundary rather than candidate rows.
    """
    producer = NativeFixture(tmp_path / "producer")
    (tmp_path / "producer").mkdir(parents=True, exist_ok=True)
    reference = producer.produce("relations")
    with producer.open(reference) as expected:
        selected = expected.discover("target")
        assert len(selected) == 1
        token = producer.native_token(selected[0])
        expected_chain = [
            producer.native_token(item)
            for item in _native_chain(expected, selected[0])
        ]
    candidate_dir = tmp_path / "candidate"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    world = ConstructionWorld.create(candidate_dir / "world.sqlite", world_id="probe")
    try:
        assert world.query(
            "SELECT name FROM _world_relations WHERE name LIKE 'program_%'"
        ) == []
        assert world.query(
            "SELECT name FROM _world_relations WHERE name='structural_context'"
        ) == []
        universe = AuthorityUniverse(
            universe_id="probe", sources=(), workspace=candidate_dir
        )
        adapter = open_native_occurrence(Path(reference.address))
        try:
            constructor = AuthorityConstructor(
                world,
                universe=universe,
                construction_id="probe",
                purpose="probe",
                program_backend=adapter,
            )
            assert token in constructor.program_entities()
            assert constructor._is_program_entity(token)
            assert not constructor._is_program_entity("missing-token")
            assert constructor._entity_kind(token) == "callable"
            assert constructor._entity_kind("missing-token") == ""
            assert constructor._snapshot_ref == adapter.snapshot()
            assert constructor._snapshot_id == adapter.snapshot()
            assert constructor.structural_context(token) == expected_chain
            assert constructor.invoked_targets(token) == []
            sites = constructor.program_entities(kind="call_site")
            assert len(sites) == 1
            assert constructor.invoked_targets(sites[0]) == [token]
            assert constructor.call_site_invoking("target") == sites[0]
            assert constructor.program_entities(kind="callable", label="target") == [token]
            assert constructor.program_entities(kind="callable", label="absent") == []
        finally:
            adapter.close()
    finally:
        world.close()


def test_source_only_constructor_has_empty_program_universe(tmp_path):
    """Without a backend the constructor keeps source-only behavior."""
    candidate_dir = tmp_path / "candidate"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    world = ConstructionWorld.create(candidate_dir / "world.sqlite", world_id="probe")
    try:
        universe = AuthorityUniverse(
            universe_id="probe", sources=(), workspace=candidate_dir
        )
        constructor = AuthorityConstructor(
            world, universe=universe, construction_id="probe", purpose="probe"
        )
        assert constructor.program_entities() == []
        assert not constructor._is_program_entity("anything")
        assert constructor._entity_kind("anything") == ""
        assert constructor.invoked_targets("anything") == []
    finally:
        world.close()


def _native_chain(read, entity):
    rows = read.facts("containment")["rows"]
    parent_of = {row["child"]: row["parent"] for row in rows}
    chain = [entity]
    seen = {entity}
    while chain[0] in parent_of:
        parent = parent_of[chain[0]]
        if parent in seen:
            break
        chain.insert(0, parent)
        seen.add(parent)
    return chain


@pytest.fixture(scope="module")
def direct_occurrences(tmp_path_factory):
    """Native production supplies inputs; assertions call the adapter directly."""
    producer = NativeFixture(tmp_path_factory.mktemp("direct-program-backend"))
    first = producer.produce("relations")
    second = producer.produce("incomplete")
    leaf = producer.produce("leaf")
    copied = producer.copy(first)
    return producer, first, second, leaf, copied


def _native_selected(producer, reference, label, kind="callable"):
    with producer.open(reference) as read:
        if label is None:
            tokens = [row["entity"] for row in read.world.relation_rows("program_entity_kind") if row["kind"] == kind]
            assert len(tokens) == 1
            return tokens[0]
        selected = read.discover(label, kind)
        assert len(selected) == 1
        return producer.native_token(selected[0])


def _recorded_state(reference):
    # Independent producer output, never another adapter accessor.
    return json.loads((Path(reference.address) / "typescript.manifest.json").read_text())["snapshot_id"]


def _assert_state(reader, expected):
    assert reader.snapshot() == expected


def _assert_membership(reader, member, foreign):
    assert reader.is_member(member)
    assert not reader.is_member(foreign)
    assert not reader.is_member("program:local-looking:nonmember")
    assert reader.kind(foreign) is None
    assert reader.containment(foreign) == ()
    assert reader.invocations(foreign) == ()
    assert reader.resolutions(foreign) == ()
    assert reader.observations(foreign) == ()


def _assert_context(reader, entity):
    rows = reader.containment(entity)
    assert all(set(row) == {"parent", "child"} for row in rows)
    parent_of = {row["child"]: row["parent"] for row in rows}
    chain = [entity]
    while chain[0] in parent_of:
        assert parent_of[chain[0]] not in chain
        chain.insert(0, parent_of[chain[0]])
    assert all(reader.is_member(token) for token in chain)
    assert [reader.kind(token) for token in chain[-3:]] == ["module", "source_unit", "callable"]
    assert len(rows) == len(chain) - 1


def _assert_nonmember_evidence(reader, token):
    assert not reader.is_member(token)
    assert reader.observations(token) == ()


def _assert_not_produced(reader, family):
    capability = reader.capability(family)
    assert capability.status == CapabilityStatus.NOT_PRODUCED


def test_direct_membership_is_local_and_copies_share_only_local_tokens(direct_occurrences):
    producer, first, second, _, copied = direct_occurrences
    old = _native_selected(producer, first, "target")
    new = _native_selected(producer, second, "caller")
    with open_native_occurrence(first.address) as left, open_native_occurrence(second.address) as right:
        _assert_membership(left, old, new)
        _assert_membership(right, new, old)
    with open_native_occurrence(copied.address) as copy:
        # A raw token shared by equivalent copies IS locally a member. Exact
        # occurrence identity remains (opened handle, token), not the token.
        assert first != copied
        assert copy.is_member(old)
        _assert_state(copy, _recorded_state(copied))


@pytest.mark.parametrize("damage", ["empty-revision", "conflicting-recorded-state"])
def test_direct_state_matches_recorded_production_and_rejects_invalid_qualification(direct_occurrences, damage):
    producer, first, _, _, _ = direct_occurrences
    with open_native_occurrence(first.address) as reader:
        _assert_state(reader, _recorded_state(first))
    damaged = producer.copy(first)
    directory = Path(damaged.address)
    directory.chmod(0o700)
    if damage == "empty-revision":
        database = directory / "world.sqlite"
        database.chmod(0o600)
        with sqlite3.connect(database) as connection:
            connection.execute("UPDATE program_snapshot SET source_state=''")
    else:
        receipt = directory / "spine.construction.receipt.json"
        receipt.chmod(0o600)
        payload = json.loads(receipt.read_text())
        payload["snapshot"]["id"] = "contradictory-state"
        receipt.write_text(json.dumps(payload))
    with pytest.raises(OccurrenceQualificationError):
        open_native_occurrence(damaged.address)


def test_direct_nonmember_observations_and_member_reconstruction(direct_occurrences):
    producer, first, _, _, _ = direct_occurrences
    token = _native_selected(producer, first, "target")
    with closing(ConstructionWorld.open(Path(first.address) / "world.sqlite", read_only=True)) as world:
        snapshot_ref = world.relation_rows("program_snapshot")[0]["snapshot"]
    with open_native_occurrence(first.address) as reader:
        _assert_nonmember_evidence(reader, snapshot_ref)
        _assert_nonmember_evidence(reader, "program:local-looking:nonmember")
        observations = reader.observations(token)
        assert observations
        assert all(reader.reconstruct(item)[1] for item in observations)


def test_direct_historical_scoped_reads_and_requested_capability(direct_occurrences):
    producer, first, second, _, _ = direct_occurrences
    token = _native_selected(producer, first, "target")
    site = _native_selected(producer, first, None, kind="call_site")
    with open_native_occurrence(first.address) as reader:
        _assert_state(reader, _recorded_state(first))
        _assert_context(reader, token)
        calls = reader.invocations(site)
        assert calls == ({"call_site": site, "target": token},)
        outcomes = reader.resolutions(site)
        assert any(row["subject"] == site and row["status"] == "RESOLVED" for row in outcomes)
        capability = reader.capability("invocation")
        assert capability.status == CapabilityStatus.COMPLETE
        assert capability.scope and capability.basis
        _assert_not_produced(reader, "spine.component_usage")
        observations = reader.observations(token)
        material = [reader.reconstruct(item) for item in observations]
    with open_native_occurrence(second.address) as reader:
        assert not reader.is_member(token)
        assert reader.capability("invocation").status == CapabilityStatus.INCOMPLETE
        assert reader.capability("invocation").gaps
        assert all(not reader.reconstruct(item)[1] for item in observations)
    producer.delete_workspace()
    with open_native_occurrence(first.address) as reader:
        _assert_state(reader, _recorded_state(first))
        _assert_context(reader, token)
        assert reader.invocations(site) == calls
        assert reader.resolutions(site) == outcomes
        assert reader.capability("invocation") == capability
        assert reader.observations(token) == observations
        assert [reader.reconstruct(item) for item in observations] == material
        assert reader.verify() == ()


def test_direct_evidence_rejects_wrong_revision_and_damaged_retention(direct_occurrences):
    producer, _, _, leaf, _ = direct_occurrences
    token = _native_selected(producer, leaf, "source")
    with open_native_occurrence(leaf.address) as reader:
        observation = reader.observations(token)[0]
        assert reader.reconstruct(observation)[1]
        assert not reader.reconstruct({**observation, "source_revision": "wrong"})[1]
        assert reader.reconstruct({**observation, "native_location": "bytes:0:0"}) == ("", True)
    damaged = producer.copy(leaf)
    producer.damage_evidence(damaged, observation, "corrupt")
    with open_native_occurrence(damaged.address) as reader:
        assert not reader.reconstruct(observation)[1]
        assert reader.verify()


def test_direct_receipt_absence_does_not_license_complete_reads(direct_occurrences):
    producer, first, _, _, _ = direct_occurrences
    token = _native_selected(producer, first, "target")
    copied = producer.copy(first)
    directory = Path(copied.address)
    directory.chmod(0o700)
    (directory / "spine.construction.receipt.json").unlink()
    with open_native_occurrence(directory) as reader:
        assert reader.is_member(token)
        assert reader.containment(token)
        with pytest.raises(OccurrenceQualificationError, match="readable construction receipt"):
            reader.capability("containment")


def test_capability_normalization_keeps_scoped_completeness_and_uncertainty():
    declaration = {"scope": "recognized static sites", "completeness_basis": "outcome per recognized site", "known_gaps": ["bounded analysis"]}
    for native, normalized in (
        ("COMPLETE", CapabilityStatus.COMPLETE),
        ("STATIC_COMPLETE", CapabilityStatus.COMPLETE),
        ("PARTIAL", CapabilityStatus.INCOMPLETE),
        ("INCOMPLETE", CapabilityStatus.INCOMPLETE),
        ("UNKNOWN", CapabilityStatus.INCOMPLETE),
        ("NOT_PRODUCED", CapabilityStatus.NOT_PRODUCED),
    ):
        capability = _project_capability({**declaration, "status": native})
        assert capability.status == normalized
        assert capability.scope == declaration["scope"]
        assert declaration["completeness_basis"] in capability.basis
        assert capability.gaps == ("bounded analysis",)
        if native in {"STATIC_COMPLETE", "PARTIAL", "UNKNOWN"}:
            assert native in capability.basis
    with pytest.raises(OccurrenceQualificationError):
        _project_capability({**declaration, "status": "invented-complete"})


@pytest.mark.parametrize("calls", [False, True], ids=["optional-calls-absent", "scoped-calls-produced"])
def test_lazy_nonfilesystem_core_without_enumeration_or_stringified_evidence(calls):
    backend_type = LazyCallsBackend if calls else LazyBackend
    with backend_type(("retained-index", 11)) as reader:
        _assert_state(reader, "indexed-state-11")
        _assert_context(reader, 30)
        assert reader.is_member(30) and not reader.is_member(31)
        observation = reader.observations(30)[0]
        assert isinstance(observation["revision"], int)
        assert isinstance(observation["extent"], dict)
        assert isinstance(observation["content"], bytes)
        assert reader.reconstruct(observation) == ("retained source at integer revision 11", True)
        assert not reader.reconstruct({**observation, "revision": 12})[1]
        assert reader.capability("containment").status == CapabilityStatus.COMPLETE
        if calls:
            assert reader.invocations(40) == ({"call_site": 40, "target": 30},)
            assert reader.resolutions(40)[0]["status"] == "RESOLVED"
        else:
            _assert_not_produced(reader, "invocation")
            _assert_not_produced(reader, "resolution")
            assert reader.invocations(40) == reader.resolutions(40) == ()
        with pytest.raises(OptionalUnsupported):
            reader.discover()
        with pytest.raises(AssertionError, match="enumeration"):
            tuple(reader._kinds)
        assert reader.verify() == ()
    with backend_type(("retained-index", 12)) as reader:
        assert not reader.is_member(30)
        assert reader.is_member(31)
        assert reader.observations(30) == ()
        assert not reader.reconstruct(observation)[1]
    with pytest.raises(ValueError, match="exact occurrence"):
        backend_type(("retained-index", 13))


def test_missing_optional_read_cannot_claim_supported_empty():
    class UnimplementedCalls(LazyBackend):
        def capability(self, family):
            return replace(super().capability("containment"), scope="declared sites")

    reader = UnimplementedCalls(("retained-index", 11))
    with pytest.raises(OptionalUnsupported):
        reader.invocations(40)
    with pytest.raises(OptionalUnsupported):
        reader.resolutions(40)


def test_explicit_config_binding_does_not_require_discovery(tmp_path, monkeypatch):
    from tests.test_phase4_vertical_slice import _stage_w1

    def unsupported(self, **selectors):
        raise OptionalUnsupported("no discovery")

    monkeypatch.setattr(NativeProgramBackend, "discover", unsupported)
    built = _stage_w1(tmp_path)
    assert built["W1"].succeeded


def test_constructor_follows_backend_even_when_candidate_has_correct_native_rows(direct_occurrences, tmp_path, monkeypatch):
    producer, first, _, _, _ = direct_occurrences
    token = _native_selected(producer, first, "target")
    candidate = tmp_path / "candidate"
    make_writable_copy(Path(first.address), candidate)
    with closing(ConstructionWorld.open(candidate / "world.sqlite", read_only=False)) as world:
        assert any(row["entity"] == token and row["kind"] == "callable" for row in world.relation_rows("program_entity_kind"))
        with open_native_occurrence(first.address) as reader:
            monkeypatch.setattr(reader, "kind", lambda entity: "backend-kind")
            monkeypatch.setattr(reader, "containment", lambda entity: ())
            monkeypatch.setattr(reader, "invocations", lambda entity: ({"call_site": entity, "target": "backend-target"},))
            monkeypatch.setattr(reader, "resolutions", lambda entity: ({"subject": entity, "status": "BACKEND", "capability": "probe"},))
            constructor = AuthorityConstructor(
                world, universe=AuthorityUniverse(universe_id="probe", sources=(), workspace=tmp_path),
                construction_id="probe", purpose="probe", program_backend=reader,
            )
            warrant = constructor._default_warrant(token, RelationSupport.CROSS_EVIDENCE_INFERRED, {"program": ReferentResolution.AGENT_RESOLVED})
            assert constructor._entity_kind(token) == "backend-kind"
            assert warrant["structural_context"] == [token]
            assert warrant["justifying_program_relations"][0]["target"] == "backend-target"
            assert warrant["justifying_resolution_outcomes"][0]["status"] == "BACKEND"
            monkeypatch.setattr(reader, "is_member", lambda entity: False)
            assert not constructor.is_program_entity(token)


@pytest.mark.parametrize("mutant", ["membership", "state", "nonmember-evidence", "ancestor", "unsupported-complete", "latest", "wrong-revision", "live-evidence"])
def test_direct_checks_reject_dishonest_adapter_mutants(direct_occurrences, tmp_path, monkeypatch, mutant):
    producer, first, second, _, _ = direct_occurrences
    token = _native_selected(producer, first, "target")
    foreign = _native_selected(producer, second, "caller")
    address = first.address
    if mutant == "membership":
        monkeypatch.setattr(NativeProgramBackend, "is_member", lambda self, entity: isinstance(entity, str) and entity.startswith("program:"))
        check = lambda reader: _assert_membership(reader, token, foreign)
    elif mutant == "state":
        monkeypatch.setattr(NativeProgramBackend, "snapshot", lambda self: "incorrect-state")
        check = lambda reader: _assert_state(reader, _recorded_state(first))
    elif mutant == "nonmember-evidence":
        monkeypatch.setattr(NativeProgramBackend, "observations", lambda self, entity: tuple(program_source_observations(self._world, entity)))
        with closing(ConstructionWorld.open(Path(first.address) / "world.sqlite", read_only=True)) as world:
            snapshot_ref = world.relation_rows("program_snapshot")[0]["snapshot"]
        check = lambda reader: _assert_nonmember_evidence(reader, snapshot_ref)
    elif mutant == "ancestor":
        original = NativeProgramBackend.containment
        def false_ancestor(self, entity):
            rows = [dict(row) for row in original(self, entity)]
            signature = next(token for token in self._members if self.kind(token) == "signature")
            rows[0]["parent"] = signature
            return tuple(rows)
        monkeypatch.setattr(NativeProgramBackend, "containment", false_ancestor)
        check = lambda reader: _assert_context(reader, token)
    elif mutant == "unsupported-complete":
        original = NativeProgramBackend.capability
        def unsupported_complete(self, family):
            capability = original(self, family)
            return replace(capability, status=CapabilityStatus.COMPLETE) if family == "spine.component_usage" else capability
        monkeypatch.setattr(NativeProgramBackend, "capability", unsupported_complete)
        check = lambda reader: _assert_not_produced(reader, "spine.component_usage")
    elif mutant == "latest":
        original = NativeProgramBackend.__init__
        monkeypatch.setattr(NativeProgramBackend, "__init__", lambda self, address: original(self, Path(second.address)))
        check = lambda reader: _assert_state(reader, _recorded_state(first))
    else:
        with open_native_occurrence(first.address) as reader:
            observation = reader.observations(token)[0]
        original = NativeProgramBackend.reconstruct
        if mutant == "wrong-revision":
            def ignore_revision(self, observation):
                revision = self._world.relation_rows("program_snapshot")[0]["source_state"]
                return original(self, {**observation, "source_revision": revision})
            monkeypatch.setattr(NativeProgramBackend, "reconstruct", ignore_revision)
            observation = {**observation, "source_revision": "wrong"}
        else:
            damaged = producer.copy(first)
            producer.damage_evidence(damaged, observation, "corrupt")
            address = damaged.address
            live = tmp_path / "mutable-live.ts"
            live.write_text("changed live source")
            def live_fallback(self, observation):
                text, verified = original(self, observation)
                return (text, True) if verified else (live.read_text(), True)
            monkeypatch.setattr(NativeProgramBackend, "reconstruct", live_fallback)
        def check(reader):
            assert not reader.reconstruct(observation)[1]
    with open_native_occurrence(address) as reader:
        with pytest.raises(AssertionError):
            check(reader)

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

from contextlib import contextmanager
from pathlib import Path

import pytest

from ontology_author.authority import AuthorityUniverse
from ontology_author.authority.construction import AuthorityConstructor
from ontology_author.program_backend import ProgramBackend
from ontology_author.program_backend.native import open_native_occurrence
from ontology_author.world.runtime.world import ConstructionWorld
from tests.program_backend_native_fixture import NativeFixture, NativeRead

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

_FACTS_METHOD = {
    "containment": "containment",
    "invocation": "invocations",
    "resolution": "resolutions",
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
            capability = self.adapter.capabilities()["spine.component_usage"]
            return {
                "capability": _capability_dict(capability),
                "schema": None,
                "rows": None,
            }
        capability = self.adapter.capabilities()[kind]
        if entity is not None and self.inspect(entity) is None:
            raise ValueError("entity is not in the opened snapshot")
        rows = getattr(self.adapter, _FACTS_METHOD[kind])()
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
            assert constructor._snapshot_id == adapter.snapshot_id()
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

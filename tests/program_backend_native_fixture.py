"""Test-local projection of production outputs, NOT a production backend API.

Only this file knows native storage, coordinates, capability names and source
setup. Behavioral cases use the fixture's logical views and opaque references.
Fault injection belongs here as well. No semantic/authority imports.
"""

from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

from ontology_author.evidence.program_source import (
    program_source_observations, reconstruct_program_observation,
    verify_retained_program_inputs,
)
from ontology_author.program_spine import (
    TypeScriptBoundary, build_typescript_spine, compare_spines, load_receipt,
    validate_typescript_spine,
)
from ontology_author.world.runtime.publication import PublicationRef, verify_publication_ref
from ontology_author.world.runtime.world import ConstructionWorld


RELATIONS = {
    "containment": ("structural_context", "spine.code_structure"),
    "invocation": ("program_invokes", "spine.calls"),
    "resolution": ("program_resolution", "spine.calls"),
    "unproduced": (None, "spine.component_usage"),
}


class NativeRead:
    def __init__(self, world):
        self.world = world
        self.reference = PublicationRef.from_world(world)
        self.receipt = load_receipt(world.path.parent / "spine.construction.receipt.json")
        self.snapshot = world.relation_rows("program_snapshot")[0]

    def descriptor(self):
        return {
            "occurrence": self.reference.as_dict(),
            "snapshot": self.snapshot["snapshot"],
            "source_state": self.snapshot["source_state"],
            "scope": self.receipt.snapshot["declared_boundary"],
            "inputs": self.receipt.snapshot["effective_inputs"],
            "losses": self.receipt.losses,
            "kinds": self.receipt.identity_surfaces,
        }

    def qualify(self, reference):
        return verify_publication_ref(self.world, reference)

    def entity_reference(self, token):
        # Test-local envelope models context-qualified entities even for a
        # backend whose local tokens do not embed snapshot/occurrence identity.
        return (self.reference, self.snapshot["snapshot"], token)

    def forge_entity(self, occurrence, snapshot, token):
        # Test-only intentionally inconsistent qualified-entity constructor.
        # Production never forges; cases use this to prove contradictory
        # supplied qualification cannot be silently accepted.
        return (occurrence, snapshot, token)

    def inspect(self, entity):
        if entity[:2] != (self.reference, self.snapshot["snapshot"]):
            return None
        rows = [r for r in self.world.relation_rows("program_entity")
                if r["snapshot"] == self.snapshot["snapshot"] and r["entity"] == entity[2]]
        if not rows:
            return None  # not a member of THIS observed universe; not global nonexistence
        assert len(rows) == 1
        label = self.world.query("SELECT label FROM _world_referents WHERE id=?", (entity[2],))[0]["label"]
        return {"entity": entity, "kind": rows[0]["kind"], "label": label,
                "boundary": rows[0]["boundary"], "snapshot": self.snapshot["snapshot"]}

    def discover(self, label, kind="callable"):
        return [self.entity_reference(r["entity"]) for r in self.world.relation_rows("program_entity")
                if (record := self.inspect(self.entity_reference(r["entity"])))
                and record["kind"] == kind and record["label"] == label]

    def facts(self, kind, entity=None):
        relation, capability_id = RELATIONS[kind]
        capability = next(c for c in self.receipt.capabilities if c["id"] == capability_id)
        if entity is not None and self.inspect(entity) is None:
            raise ValueError("entity is not in the opened snapshot")
        # No empty-set translation for NOT_PRODUCED; the receipt remains authoritative.
        if capability["status"] == "NOT_PRODUCED":
            return {"capability": capability, "schema": None, "rows": None}
        schema = self.world.relation_schema(relation)
        rows = [r for r in self.world.relation_rows(relation)
                if r["snapshot"] == self.snapshot["snapshot"]]
        ref_roles = [r["name"] for r in schema["roles"]
                     if r["type"] == "REFERENT" and r["name"] != "snapshot"]
        if entity is not None:
            rows = [r for r in rows if any(r[role] == entity[2] for role in ref_roles)]
        roles = [{"name": r["name"], "type": {"REFERENT": "entity", "TEXT": "text",
                  "BOOLEAN": "boolean"}[r["type"]]}
                 for r in schema["roles"] if r["name"] != "snapshot"]
        projected = [{r["name"]: self.entity_reference(row[r["name"]])
                      if r["type"] == "entity" else row[r["name"]] for r in roles}
                     for row in rows]
        return {"capability": capability, "schema": {"roles": roles}, "rows": projected,
                "snapshot": self.snapshot["snapshot"]}

    def observations(self, entity):
        if self.inspect(entity) is None:
            raise ValueError("entity is not in the opened snapshot")
        return program_source_observations(self.world, entity[2])

    def reconstruct(self, observation):
        text, status = reconstruct_program_observation(self.world, observation)
        return {"verified": status == "OK", "material": text}

    def verify(self):
        manifest = json.loads((self.world.path.parent / "typescript.manifest.json").read_text())
        return (validate_typescript_spine(self.world, manifest, self.receipt)
                + verify_retained_program_inputs(self.world))


class NativeFixture:
    comparison_supported = True
    discovery_supported = True

    def supports(self, kind):
        # Test-scenario capabilities, not a proposed production API.
        return kind in RELATIONS and kind != "unproduced"

    def misqualify(self, entity, occurrence=None, snapshot=None):
        # Test-only: replace envelope qualification while preserving the
        # native token, to construct contradictory supplied qualification.
        occ, snap, token = entity
        return (occurrence if occurrence is not None else occ,
                snapshot if snapshot is not None else snap,
                token)

    def native_token(self, entity):
        # Test-only accessor for the opaque local token inside the envelope.
        return entity[2]

    def snapshot_of(self, entity):
        return entity[1]

    def occurrence_of(self, entity):
        return entity[0]

    def select(self, read, label):
        # Fixture setup supplies the explicit endpoint to core cases. Native
        # label discovery is one setup mechanism, not a core read dependency.
        entities = read.discover(label)
        assert len(entities) == 1
        return entities[0]

    def __init__(self, root):
        self.root = root
        self.workspace = root / "workspace"
        self.count = 0

    def produce(self, scenario):
        sources = {
            "leaf": {"a.ts": 'export function source(): string { return "é😀"; }\n'},
            "same_label": {"a.ts": 'export function source(): string { return "changed"; }\n'},
            "rename": {"a.ts": 'export function renamed(): string { return "é😀"; }\n'},
            "ambiguous": {"a.ts": 'export function first(): string { return "é😀"; }\n'
                                   'export function second(): string { return "é😀"; }\n'},
            "duplicate_labels": {"a.ts": "export function source(): void {}\n",
                                 "b.ts": "export function source(): void {}\n"},
            "relations": {"a.ts": "function target(): void {}\n"
                                  "export function caller(): void { target(); }\n"},
            "unresolved": {"a.ts": "export function caller(fn: any): void { fn(); }\n"},
            "incomplete": {"a.ts": "export function caller(): void { missing(); }\n"},
        }
        self.workspace.mkdir(exist_ok=True)
        source_dir = self.workspace / "src"
        if source_dir.exists():
            shutil.rmtree(source_dir)
        source_dir.mkdir()
        for path, text in sources[scenario].items():
            (source_dir / path).write_text(text, encoding="utf-8")
        (self.workspace / "tsconfig.json").write_text(json.dumps({
            "compilerOptions": {"target": "ES2020", "module": "commonjs", "strict": True},
            "include": ["src/**/*.ts"],
        }))
        self.count += 1
        output = self.root / f"occurrence-{self.count}"
        result = build_typescript_spine(self.workspace, output, boundary=TypeScriptBoundary(
            workspace_roots=("src",), projects=("tsconfig.json",), package_roots=("src",)))
        assert result.succeeded, result.errors
        with self.open_at(output) as read:
            return read.reference

    @contextmanager
    def open_at(self, path):
        world = ConstructionWorld.open(path / "world.sqlite", read_only=True)
        try:
            yield NativeRead(world)
        finally:
            world.close()

    @contextmanager
    def open(self, reference):
        with self.open_at(Path(reference.address)) as read:
            errors = verify_publication_ref(read.world, reference)
            if errors:
                raise ValueError("; ".join(errors))
            yield read

    def serialize(self, reference):
        return reference.as_dict()

    def deserialize(self, value):
        return PublicationRef.from_mapping(value)

    def wrong_qualification(self, reference):
        return replace(reference, revision=reference.revision + 1)

    def unavailable(self, reference):
        return replace(reference, address=str(self.root / "unavailable"))

    def copy(self, reference):
        self.count += 1
        output = self.root / f"occurrence-{self.count}"
        shutil.copytree(reference.address, output)
        with self.open_at(output) as read:
            return read.reference

    def fingerprint(self, reference):
        root = Path(reference.address)
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob("*") if p.is_file()}

    def delete_workspace(self):
        shutil.rmtree(self.workspace)

    def wrong_observation_revision(self, observation):
        return {**observation, "source_revision": "wrong"}

    def damage_evidence(self, reference, observation, mode):
        digest = observation["native_handle"].rsplit("@sha256:", 1)[1]
        path = Path(reference.address) / "program_inputs" / digest
        path.parent.chmod(0o700)
        path.chmod(0o600)
        if mode == "missing":
            path.unlink()
        else:
            path.write_bytes(b"tampered")

    def incompatible(self, reference, mode):
        # Deliberate fault, on a separate copy; never alter a retained test original.
        if mode == "representation":
            path = Path(reference.address) / "spine.construction.receipt.json"
            path.parent.chmod(0o700)
            path.chmod(0o600)
            payload = json.loads(path.read_text())
            payload["snapshot"]["extractor"]["version"] = "incompatible"
            path.write_text(json.dumps(payload))
            return
        path = Path(reference.address) / "world.sqlite"
        path.parent.chmod(0o700)
        path.chmod(0o600)
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE program_capability SET version='incompatible' "
                               "WHERE capability='spine.calls'")

    def compare(self, old, new):
        if not self.comparison_supported:
            return None
        # Qualify opened inputs before invoking a service whose native receipt only
        # records snapshot tokens. Context supplies exact occurrences, not its digest.
        with self.open(old) as left, self.open(new) as right:
            result = compare_spines(old.address, new.address)
            claims = [{**c.to_dict(),
                       "old_entity": left.entity_reference(c.old_entity) if c.old_entity else None,
                       "new_entity": right.entity_reference(c.new_entity) if c.new_entity else None}
                      for c in result.correspondences]
            ambiguities = [
                {**r, "old_entity": left.entity_reference(r["old_entity"]),
                 "candidate_entities": [right.entity_reference(e) for e in r["candidate_entities"]]}
                for r in result.delta.identity["ambiguous"]]
        return {"old": self.serialize(old), "new": self.serialize(new),
                "claims": claims, "changes": result.delta.manifestations,
                "ambiguities": ambiguities, "compatibility": result.receipt.compatibility,
                "incomparable": result.receipt.not_comparable_capabilities}

"""Native ProgramBackend over a retained TypeScript spine occurrence.

The adapter mechanically projects existing native state: spine relations,
construction receipt, and retained source blobs. It knows native relation
names, the receipt sidecar layout, and evidence helpers so that consumers
do not have to. It invents no semantic information.
"""

from __future__ import annotations

import json
from collections.abc import Hashable, Mapping
from pathlib import Path
from typing import Any

from ontology_author.evidence.program_source import (
    program_source_observations,
    reconstruct_program_observation,
    verify_retained_program_inputs,
)
from ontology_author.program_spine import (
    SpineConstructionReceipt,
    load_receipt,
    validate_typescript_spine,
)
from ontology_author.world.runtime.world import ConstructionWorld

from . import (
    BackendError,
    Capability,
    CapabilityStatus,
    NotAProgramOccurrence,
    OccurrenceQualificationError,
    ProgramBackend,
)

# Neutral family name -> native receipt capability id. Invocation and
# resolution share the native calls capability, as in Phase 5A.
_FAMILY_CAPABILITIES = {
    "containment": "spine.code_structure",
    "invocation": "spine.calls",
    "resolution": "spine.calls",
}


def open_native_occurrence(address: Path | str) -> ProgramBackend:
    """Open a read boundary over an exact retained native occurrence."""
    return NativeProgramBackend(Path(address))


class NativeProgramBackend(ProgramBackend):
    """ProgramBackend projected from a sealed native spine bundle."""

    def __init__(self, address: Path) -> None:
        database = address / "world.sqlite"
        if not database.exists():
            raise FileNotFoundError(f"program occurrence sqlite is missing: {database}")
        self._address = address
        self._world = ConstructionWorld.open(database, read_only=True)
        try:
            snapshot_rows = self._rows("program_snapshot")
            entity_rows = self._rows("program_entity")
            if not snapshot_rows and not entity_rows:
                raise NotAProgramOccurrence(
                    f"occurrence carries no program plane: {address}"
                )
            if not snapshot_rows:
                raise OccurrenceQualificationError(
                    "program entities require a qualified program snapshot"
                )
            if len(snapshot_rows) != 1:
                raise OccurrenceQualificationError(
                    "governed World must contain exactly one program snapshot"
                )
            self._snapshot = str(snapshot_rows[0]["snapshot"])
            if not self._snapshot or not snapshot_rows[0].get("source_state"):
                raise OccurrenceQualificationError("program snapshot lacks state qualification")
            self._state = self._recorded_snapshot_id()
            self._members = tuple(
                str(row["entity"]) for row in entity_rows
                if str(row["snapshot"]) == self._snapshot
            )
            self._member_set = frozenset(self._members)
            self._kinds = {
                str(row["entity"]): str(row["kind"] or "")
                for row in self._rows("program_entity_kind")
                if str(row["snapshot"]) == self._snapshot
            }
            self._containment = tuple(
                {"parent": str(row["parent"]), "child": str(row["child"])}
                for row in self._rows("structural_context")
                if str(row["snapshot"]) == self._snapshot
            )
            self._invocations = tuple(
                {"call_site": str(row["call_site"]), "target": str(row["target"])}
                for row in self._rows("program_invokes")
                if str(row["snapshot"]) == self._snapshot
            )
            self._resolutions = tuple(
                {
                    "subject": str(row["subject"]),
                    "status": str(row["status"] or ""),
                    "capability": str(row["capability"] or ""),
                }
                for row in self._rows("program_resolution")
                if str(row["snapshot"]) == self._snapshot
            )
            self._labels = {
                str(row["id"]): str(row["label"])
                for row in self._world.query("SELECT id, label FROM _world_referents")
            }
            self._descriptors = {
                str(row["entity"]): str(row["descriptor"] or "")
                for row in self._rows("program_identity_descriptor")
                if str(row["snapshot"]) == self._snapshot
            }
            self._receipt: SpineConstructionReceipt | None = None
            try:
                self._receipt = load_receipt(address / "spine.construction.receipt.json")
            except (OSError, ValueError):
                self._receipt = None
            if self._receipt is not None and self._receipt.snapshot.get("id") != self._state:
                raise OccurrenceQualificationError("recorded program state disagrees with receipt")
        except Exception:
            self._world.close()
            raise

    def close(self) -> None:
        self._world.close()

    def _rows(self, relation: str) -> list[dict[str, Any]]:
        if not self._world.query("SELECT 1 FROM _world_relations WHERE name=?", (relation,)):
            return []
        return self._world.relation_rows(relation)

    def _recorded_snapshot_id(self) -> str:
        assertion = self._world.query(
            "SELECT assertion_id FROM _world_assertions WHERE relation_name='program_snapshot'"
        )
        if not assertion:
            return self._snapshot
        warrant = self._world.warrant_for_assertion(str(assertion[0]["assertion_id"]))
        for base in warrant.get("bases") or []:
            detail = base.get("detail")
            if isinstance(detail, dict) and isinstance(detail.get("extra"), dict):
                extra = dict(detail["extra"])
                if extra.get("snapshot_id"):
                    return str(extra["snapshot_id"])
        return self._snapshot

    def snapshot(self) -> str:
        return self._state

    def is_member(self, entity: Hashable) -> bool:
        return entity in self._member_set

    def kind(self, entity: Hashable) -> str | None:
        if not self.is_member(entity):
            return None
        return self._kinds.get(entity)

    def containment(self, entity: Hashable) -> tuple[dict[str, Hashable], ...]:
        if not self.is_member(entity):
            return ()
        parents = {row["child"]: row["parent"] for row in self._containment}
        edges = []
        seen = {entity}
        while entity in parents and parents[entity] not in seen:
            parent = parents[entity]
            edges.append({"parent": parent, "child": entity})
            seen.add(parent)
            entity = parent
        return tuple(reversed(edges))

    def invocations(self, call_site: Hashable) -> tuple[dict[str, Hashable], ...]:
        if not self.is_member(call_site):
            return ()
        return tuple(dict(row) for row in self._invocations if row["call_site"] == call_site)

    def resolutions(self, subject: Hashable) -> tuple[dict[str, Hashable], ...]:
        if not self.is_member(subject):
            return ()
        return tuple(dict(row) for row in self._resolutions if row["subject"] == subject)

    def capability(self, family: str) -> Capability:
        if self._receipt is None:
            raise OccurrenceQualificationError(
                "program occurrence lacks a readable construction receipt"
            )
        capability_id = _FAMILY_CAPABILITIES.get(family, family)
        for item in self._receipt.capabilities:
            if item.get("id") == capability_id:
                return _project_capability(item)
        # An absent declaration licenses no negative conclusion. Do not turn
        # missing required native metadata into a fabricated complete result.
        raise OccurrenceQualificationError(
            f"program occurrence receipt omits capability: {capability_id}"
        )

    def observations(self, entity: Hashable) -> tuple[object, ...]:
        if not self.is_member(entity):
            return ()
        return tuple(
            dict(observation)
            for observation in program_source_observations(self._world, entity)
        )

    def reconstruct(self, observation: object) -> tuple[str, bool]:
        # Native observations remain native mappings. Other adapters can use
        # any opaque handle; there is no coercion at the production boundary.
        if not isinstance(observation, Mapping) or any(
            not isinstance(observation.get(key), str)
            for key in ("provider", "native_handle", "source_revision", "native_location")
        ):
            return "", False
        text, status = reconstruct_program_observation(self._world, observation)
        return (text, status == "OK")

    def verify(self) -> tuple[str, ...]:
        manifest_path = self._address / "typescript.manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ("typescript manifest is missing or unreadable",)
        if not isinstance(manifest, dict):
            return ("typescript manifest is missing or unreadable",)
        errors = validate_typescript_spine(self._world, manifest, self._receipt)
        errors.extend(verify_retained_program_inputs(self._world))
        return tuple(sorted(set(errors)))

    def discover(
        self,
        *,
        label: str | None = None,
        kind: str | None = None,
        descriptor_contains: str | None = None,
    ) -> tuple[str, ...]:
        if label is None and kind is None and descriptor_contains is None:
            return self._members
        output = []
        for entity in self._members:
            if kind is not None and self._kinds.get(entity) != kind:
                continue
            if label is not None and self._labels.get(entity) != label:
                continue
            if descriptor_contains is not None and descriptor_contains not in self._descriptors.get(entity, ""):
                continue
            output.append(entity)
        return tuple(output)


def _project_capability(item: Mapping[str, Any]) -> Capability:
    native_status = str(item.get("status"))
    statuses = {
        "COMPLETE": CapabilityStatus.COMPLETE,
        "STATIC_COMPLETE": CapabilityStatus.COMPLETE,
        "PARTIAL": CapabilityStatus.INCOMPLETE,
        "INCOMPLETE": CapabilityStatus.INCOMPLETE,
        "UNKNOWN": CapabilityStatus.INCOMPLETE,
        "NOT_PRODUCED": CapabilityStatus.NOT_PRODUCED,
    }
    try:
        status = statuses[native_status]
    except KeyError as exc:
        raise OccurrenceQualificationError(
            f"program occurrence receipt has an invalid capability status: {item.get('status')}"
        ) from exc
    gaps = item.get("known_gaps") or []
    basis = str(item.get("completeness_basis") or "")
    if native_status in {"STATIC_COMPLETE", "PARTIAL", "UNKNOWN"}:
        basis = f"{basis}; native qualification: {native_status}"
    return Capability(
        status=status,
        scope=str(item.get("scope") or ""),
        basis=basis,
        gaps=tuple(str(gap) for gap in gaps),
    )


__all__ = [
    "BackendError",
    "NativeProgramBackend",
    "open_native_occurrence",
]

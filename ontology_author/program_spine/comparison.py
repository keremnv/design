"""Deterministic application-level comparison of native program spines.

The comparison layer reads two sealed Worlds and their construction manifests.
It does not mutate either snapshot, parse source, or create permanent lineage
identities.

Storage (v0)
------------
Output is a deterministic sidecar bundle ``spine.comparison.json``.  The file
contains comparison-local correspondence claims, cardinality groups, a
ProgramDelta, and a SpineComparisonReceipt.  It is not a sealed World, not a
kernel lineage primitive, and not a second truth system.  The two input
snapshots remain independently valid.  A later implementation may persist the
same JSON-shaped records as ordinary application facts without redesigning
this schema.

Historical re-extraction under a common extractor version is not performed.
Callers pass already constructed compatible snapshots.  The snapshot arguments
stay the same if that reconstruction step is added later.

Epistemic basis
---------------
The matcher is computationally deterministic: the same snapshots and mechanism
version reproduce the same output.  That is not the same as mechanically
entailed correspondence.  ``basis_class`` records epistemic support:

- ``DETERMINISTIC`` — exact/entailed: declared identity evidence licenses
  continuation
- ``HEURISTIC`` — reproducible structural evidence proposes continuation
  without entailing that the manifestations are the same program thing
- ``OBSERVATIONAL`` — supplied or externally observed comparison evidence

v0 automatic rules are heuristic.  ``HEURISTIC`` does not mean fuzzy, scored,
or model-judged.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ontology_author.world.runtime.world import ConstructionWorld
from .schemas import SpineConstructionReceipt, load_receipt


COMPARISON_RECEIPT_VERSION = "spine_comparison_receipt/v1"
COMPARISON_MECHANISM_ID = "ontology_author.program_spine.comparison"
COMPARISON_MECHANISM_VERSION = "v0"
CONTINUITY_STATUSES = {"CONTINUED", "AMBIGUOUS", "UNRESOLVED", "NO_MATCH"}
# DETERMINISTIC is the contract spelling for exact/entailed support. It does
# not mean that the matching algorithm ran deterministically.
BASIS_CLASSES = {"DETERMINISTIC", "HEURISTIC", "OBSERVATIONAL"}
AUTOMATIC_BASIS_CLASS = "HEURISTIC"
OUTCOMES = {
    "UNCHANGED_OR_CONTINUED",
    "RENAME",
    "MOVE",
    "RENAME_AND_MOVE",
    "SPLIT",
    "MERGE",
    "DELETED",
    "NEW",
    "AMBIGUOUS",
    "UNRESOLVED",
}
RELATION_CAPABILITIES = {
    "structural_context": "spine.code_structure",
    "program_imports": "spine.imports",
    "program_invokes": "spine.calls",
    "program_has_type": "spine.type_relations",
    "program_extends": "spine.type_relations",
    "program_implements": "spine.type_relations",
}
COMPARABLE_RELATIONS = tuple(RELATION_CAPABILITIES)
RESOLUTION_RELATIONS = {
    "program_resolution": "spine.calls",
    "program_resolution_candidate": "spine.calls",
}
ENTITY_KIND_ORDER = {
    "module": 0,
    "source_unit": 1,
    "class": 2,
    "interface": 3,
    "type": 4,
    "callable": 5,
    "method": 6,
    "signature": 7,
    "parameter": 8,
    "data": 9,
    "call_site": 10,
}
_LOCATION_RE = re.compile(r"^bytes:(\d+):(\d+)$")
_SIGNATURE_RE = re.compile(r"[|]Signature[|].*[|](.*)$")


class ComparisonError(ValueError):
    """A comparison input or result violates the native comparison contract."""


def _copy(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=False))


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()[:32]


def _capability_key(capability: str, version: str) -> str:
    return f"{capability}/{version}"


def _base_capability(key: str) -> str:
    return key.rsplit("/", 1)[0] if "/" in key else key


def _parse_detail(value: Any) -> Mapping[str, Any]:
    try:
        parsed = json.loads(str(value or ""))
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _claim_basis(evidence: Sequence[Mapping[str, Any]]) -> str:
    """Select the claim-level epistemic class from evidence items.

    Heuristic support keeps the whole claim heuristic even when some items are
    stronger. Computational reproducibility is independent of this choice.
    """

    kinds = [str(item.get("kind") or "") for item in evidence if isinstance(item, Mapping)]
    if any(kind == "HEURISTIC" for kind in kinds):
        return "HEURISTIC"
    if "DETERMINISTIC" in kinds:
        return "DETERMINISTIC"
    if "OBSERVATIONAL" in kinds:
        return "OBSERVATIONAL"
    return AUTOMATIC_BASIS_CLASS


def _contains_lineage_score(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower().replace("_", "-")
            if lowered in {"lineage-quality", "similarity-score", "lineage-score"}:
                return True
            if _contains_lineage_score(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_lineage_score(item) for item in value)
    return False


@dataclass(frozen=True)
class _Entity:
    entity_id: str
    kind: str
    label: str
    boundary: str
    synthetic: bool
    descriptor: str
    comparable_descriptor: str
    parents: tuple[str, ...]
    children: tuple[str, ...]
    evidence: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class _SnapshotView:
    world: ConstructionWorld
    manifest: Mapping[str, Any]
    receipt: SpineConstructionReceipt | None
    snapshot_ref: str
    snapshot_id: str
    snapshot_row: Mapping[str, Any]
    entities: Mapping[str, _Entity]
    capabilities: Mapping[str, Mapping[str, Any]]
    relations: Mapping[str, tuple[Mapping[str, Any], ...]]
    descriptor_available: bool
    workspace: str

    def capability_by_base(self) -> dict[str, Mapping[str, Any]]:
        result: dict[str, Mapping[str, Any]] = {}
        for key, record in self.capabilities.items():
            base = _base_capability(key)
            existing = result.get(base)
            if existing is not None and existing.get("version") != record.get("version"):
                raise ComparisonError(f"duplicate capability versions in snapshot {self.snapshot_id}: {base}")
            result[base] = record
        return result

    def source_evidence(self, entity_id: str) -> tuple[Mapping[str, Any], ...]:
        return self.entities[entity_id].evidence

    def children(self, entity_id: str) -> tuple[str, ...]:
        return self.entities[entity_id].children

    def signature_shapes(self, entity_id: str) -> tuple[str, ...]:
        shapes: list[str] = []
        for child_id in self.children(entity_id):
            child = self.entities.get(child_id)
            if child is None or child.kind != "signature":
                continue
            shape = _signature_shape(child.comparable_descriptor or child.descriptor)
            if shape:
                shapes.append(shape)
        return tuple(sorted(shapes))

    def occurrence_rank(self, entity_id: str) -> tuple[int, int, str]:
        entity = self.entities[entity_id]
        start, _end = _best_location(entity.evidence)
        parent = entity.parents[0] if entity.parents else ""
        siblings = [
            candidate
            for candidate in self.entities.values()
            if candidate.kind == entity.kind and parent and parent in candidate.parents
        ]
        ordered = sorted(
            siblings,
            key=lambda item: (*_best_location(item.evidence), item.entity_id),
        )
        ordinal = next(
            (index for index, item in enumerate(ordered) if item.entity_id == entity_id),
            len(ordered),
        )
        return ordinal, start, entity.entity_id


@dataclass(frozen=True)
class CorrespondenceClaim:
    """A comparison-local claim relating two snapshot manifestations."""

    old_entity: str | None
    new_entity: str | None
    continuity: str
    outcome: str
    basis_class: str
    evidence: tuple[Mapping[str, Any], ...] = ()
    changes: Mapping[str, str] = field(default_factory=dict)
    candidate_entities: tuple[str, ...] = ()
    group_id: str | None = None
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_entity": self.old_entity,
            "new_entity": self.new_entity,
            "continuity": self.continuity,
            "outcome": self.outcome,
            "basis_class": self.basis_class,
            "evidence": [_copy(item) for item in self.evidence],
            "changes": _copy(self.changes),
            "candidate_entities": list(self.candidate_entities),
            "group_id": self.group_id,
            "limitations": list(self.limitations),
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.continuity not in CONTINUITY_STATUSES:
            errors.append(f"invalid correspondence continuity: {self.continuity}")
        if self.outcome not in OUTCOMES:
            errors.append(f"invalid correspondence outcome: {self.outcome}")
        if self.basis_class not in BASIS_CLASSES:
            errors.append(f"invalid correspondence basis: {self.basis_class}")
        if self.continuity == "CONTINUED" and (not self.old_entity or not self.new_entity):
            errors.append("continued correspondence needs both endpoints")
        if self.continuity == "AMBIGUOUS" and not self.candidate_entities:
            errors.append("ambiguous correspondence needs candidate entities")
        if self.continuity == "CONTINUED" and self.outcome in {"DELETED", "NEW"}:
            errors.append("continued correspondence cannot use unmatched delta membership as continuity")
        return errors


@dataclass(frozen=True)
class CorrespondenceGroup:
    """A comparison-local one-to-many or many-to-one event."""

    event: str
    old_entities: tuple[str, ...]
    new_entities: tuple[str, ...]
    basis_class: str = "OBSERVATIONAL"
    evidence: tuple[Mapping[str, Any], ...] = ()
    group_id: str = ""

    def __post_init__(self) -> None:
        if not self.group_id:
            object.__setattr__(
                self,
                "group_id",
                f"comparison-group:{_digest({'event': self.event, 'old': self.old_entities, 'new': self.new_entities})}",
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "event": self.event,
            "old_entities": list(self.old_entities),
            "new_entities": list(self.new_entities),
            "basis_class": self.basis_class,
            "evidence": [_copy(item) for item in self.evidence],
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.event == "SPLIT":
            if len(self.old_entities) != 1 or len(self.new_entities) < 2:
                errors.append("SPLIT requires one old entity and at least two new entities")
        elif self.event == "MERGE":
            if len(self.old_entities) < 2 or len(self.new_entities) != 1:
                errors.append("MERGE requires at least two old entities and one new entity")
        else:
            errors.append(f"invalid correspondence group event: {self.event}")
        if self.basis_class not in BASIS_CLASSES:
            errors.append(f"invalid correspondence group basis: {self.basis_class}")
        if len(set(self.old_entities)) != len(self.old_entities):
            errors.append("correspondence group repeats an old entity")
        if len(set(self.new_entities)) != len(self.new_entities):
            errors.append("correspondence group repeats a new entity")
        return errors


@dataclass(frozen=True)
class ProgramDelta:
    """Comparison-local identity, manifestation, and relation delta."""

    old_snapshot: str
    new_snapshot: str
    identity: Mapping[str, Any]
    manifestations: tuple[Mapping[str, Any], ...]
    relations: Mapping[str, Mapping[str, Any]]
    groups: tuple[CorrespondenceGroup, ...] = ()
    maintenance: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "old_snapshot": self.old_snapshot,
            "new_snapshot": self.new_snapshot,
            "identity": _copy(self.identity),
            "manifestations": [_copy(item) for item in self.manifestations],
            "relations": _copy(self.relations),
            "groups": [item.to_dict() for item in self.groups],
            "maintenance": [_copy(item) for item in self.maintenance],
        }


@dataclass(frozen=True)
class SpineComparisonReceipt:
    """Inspectable comparison/conformance summary."""

    receipt_version: str
    comparison_id: str
    conformance: Mapping[str, Any]
    snapshots: Mapping[str, Any]
    compatibility: Mapping[str, Any]
    comparison_mechanism: Mapping[str, Any]
    correspondence_summary: Mapping[str, Any]
    delta_summary: Mapping[str, Any]
    split_merge_summary: Mapping[str, Any]
    known_losses: tuple[str, ...]
    not_comparable_capabilities: tuple[str, ...]
    representative_examples: tuple[Mapping[str, Any], ...]
    completeness_receipt_refs: Mapping[str, Any]
    acceptance: Mapping[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SpineComparisonReceipt":
        required = {
            "receipt_version",
            "comparison_id",
            "conformance",
            "snapshots",
            "compatibility",
            "comparison_mechanism",
            "correspondence_summary",
            "delta_summary",
            "split_merge_summary",
            "known_losses",
            "not_comparable_capabilities",
            "representative_examples",
            "completeness_receipt_refs",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ComparisonError(f"comparison receipt missing {', '.join(missing)}")
        return cls(
            receipt_version=str(payload["receipt_version"]),
            comparison_id=str(payload["comparison_id"]),
            conformance=_copy(payload["conformance"]),
            snapshots=_copy(payload["snapshots"]),
            compatibility=_copy(payload["compatibility"]),
            comparison_mechanism=_copy(payload["comparison_mechanism"]),
            correspondence_summary=_copy(payload["correspondence_summary"]),
            delta_summary=_copy(payload["delta_summary"]),
            split_merge_summary=_copy(payload["split_merge_summary"]),
            known_losses=tuple(str(item) for item in payload["known_losses"]),
            not_comparable_capabilities=tuple(str(item) for item in payload["not_comparable_capabilities"]),
            representative_examples=tuple(_copy(item) for item in payload["representative_examples"]),
            completeness_receipt_refs=_copy(payload["completeness_receipt_refs"]),
            acceptance=_copy(payload["acceptance"]) if payload.get("acceptance") is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_version": self.receipt_version,
            "comparison_id": self.comparison_id,
            "conformance": _copy(self.conformance),
            "snapshots": _copy(self.snapshots),
            "compatibility": _copy(self.compatibility),
            "comparison_mechanism": _copy(self.comparison_mechanism),
            "correspondence_summary": _copy(self.correspondence_summary),
            "delta_summary": _copy(self.delta_summary),
            "split_merge_summary": _copy(self.split_merge_summary),
            "known_losses": list(self.known_losses),
            "not_comparable_capabilities": list(self.not_comparable_capabilities),
            "representative_examples": [_copy(item) for item in self.representative_examples],
            "completeness_receipt_refs": _copy(self.completeness_receipt_refs),
            "acceptance": _copy(self.acceptance) if self.acceptance is not None else None,
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.receipt_version != COMPARISON_RECEIPT_VERSION:
            errors.append(f"unsupported comparison receipt version: {self.receipt_version}")
        if not self.comparison_id:
            errors.append("comparison receipt has no comparison ID")
        if not isinstance(self.conformance, Mapping):
            errors.append("comparison receipt conformance must be an object")
        else:
            status = self.conformance.get("status")
            if status not in {"PASS", "CONTRACT_FAILURE"}:
                errors.append(f"invalid comparison conformance status: {status}")
            if status == "PASS" and self.conformance.get("diagnostics"):
                errors.append("PASS comparison receipt cannot contain diagnostics")
        for side in ("old", "new"):
            item = self.snapshots.get(side) if isinstance(self.snapshots, Mapping) else None
            if not isinstance(item, Mapping) or not str(item.get("id") or "").strip():
                errors.append(f"comparison receipt snapshot {side} is missing")
        mechanism = self.comparison_mechanism
        if not isinstance(mechanism, Mapping) or not str(mechanism.get("id") or "").strip() or not str(mechanism.get("version") or "").strip():
            errors.append("comparison receipt mechanism identity is missing")
        if any(_contains_lineage_score(item) for item in (
            self.snapshots,
            self.compatibility,
            self.comparison_mechanism,
            self.correspondence_summary,
            self.delta_summary,
            self.split_merge_summary,
            self.representative_examples,
        )):
            errors.append("comparison receipt contains an opaque lineage-quality field")
        return sorted(set(errors))


@dataclass(frozen=True)
class SpineComparisonResult:
    """Complete deterministic sidecar result for one comparison."""

    receipt: SpineComparisonReceipt
    correspondences: tuple[CorrespondenceClaim, ...]
    groups: tuple[CorrespondenceGroup, ...]
    delta: ProgramDelta

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt": self.receipt.to_dict(),
            "correspondence_claims": [item.to_dict() for item in self.correspondences],
            "correspondence_groups": [item.to_dict() for item in self.groups],
            "program_delta": self.delta.to_dict(),
        }

    def validate(self) -> list[str]:
        errors = self.receipt.validate()
        for claim in self.correspondences:
            errors.extend(claim.validate())
        for group in self.groups:
            errors.extend(group.validate())
        for item in self.receipt.representative_examples:
            if not isinstance(item, Mapping):
                errors.append("comparison representative example must be an object")
        return sorted(set(errors))

    def write(self, output_dir: Path | str) -> Path:
        errors = self.validate()
        if errors:
            raise ComparisonError("cannot write invalid comparison: " + "; ".join(errors))
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "spine.comparison.json"
        path.write_text(
            json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path


def _location_key(evidence: Mapping[str, Any]) -> tuple[str, int, int]:
    handle = str(evidence.get("native_handle") or "")
    path = handle.split("@sha256:", 1)[0]
    location = str(evidence.get("native_location") or "")
    match = _LOCATION_RE.match(location)
    if match:
        return path, int(match.group(1)), int(match.group(2))
    return path, 10**18, 10**18


def _best_location(evidence: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
    starts = [(_location_key(item)[1], _location_key(item)[2]) for item in evidence]
    return min(starts) if starts else (10**18, 10**18)


def _signature_shape(descriptor: str) -> str:
    match = _SIGNATURE_RE.search(descriptor)
    if match:
        return match.group(1)
    return ""


def _source_manifestation(entity: _Entity) -> tuple[tuple[str, str, str, str], ...]:
    return tuple(
        sorted(
            (
                str(item.get("provider") or ""),
                str(item.get("native_handle") or ""),
                str(item.get("source_revision") or ""),
                str(item.get("native_location") or ""),
            )
            for item in entity.evidence
        )
    )


def _source_locations(entity: _Entity) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((_location_key(item)[0], str(item.get("native_location") or "")) for item in entity.evidence))


def _source_paths(entity: _Entity) -> set[str]:
    return {path for path, _location in _source_locations(entity)}


def _workspace_from_manifest(manifest: Mapping[str, Any]) -> str:
    boundary = manifest.get("boundary") if isinstance(manifest.get("boundary"), Mapping) else {}
    roots = [str(item).strip("/").replace("\\", "/") for item in (boundary.get("workspace_roots") or ())]
    for item in manifest.get("effective_inputs") or []:
        if not isinstance(item, Mapping):
            continue
        posix = str(item.get("path") or "").replace("\\", "/")
        for root in roots or ("src",):
            marker = f"/{root}/"
            idx = posix.find(marker)
            if idx >= 0:
                return posix[:idx]
    return ""


def _comparable_text(text: str, workspace: str) -> str:
    if not workspace:
        return text
    stripped = workspace.rstrip("/")
    return text.replace(stripped + "/", "").replace(stripped, "")


def _ancestors(view: _SnapshotView, entity_id: str) -> tuple[str, ...]:
    found: list[str] = []
    pending = list(view.entities[entity_id].parents)
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current in seen or current not in view.entities:
            continue
        seen.add(current)
        found.append(current)
        pending.extend(view.entities[current].parents)
    return tuple(found)


def _descendants(view: _SnapshotView, entity_id: str) -> set[str]:
    found: set[str] = set()
    pending = list(view.entities[entity_id].children)
    while pending:
        current = pending.pop()
        if current in found or current not in view.entities:
            continue
        found.add(current)
        pending.extend(view.entities[current].children)
    return found


def _enclosing(view: _SnapshotView, entity_id: str, kinds: set[str]) -> tuple[str, ...]:
    return tuple(
        ancestor
        for ancestor in _ancestors(view, entity_id)
        if view.entities[ancestor].kind in kinds
    )


def _depth(view: _SnapshotView, entity_id: str) -> int:
    return len(_ancestors(view, entity_id))


def _expand_ids(view: _SnapshotView, ids: Iterable[str]) -> set[str]:
    expanded = set(ids)
    for entity_id in list(expanded):
        if entity_id in view.entities:
            expanded.update(_descendants(view, entity_id))
    return expanded


def _module_fingerprint(view: _SnapshotView, entity_id: str) -> tuple[Any, ...]:
    root = view.entities.get(entity_id)
    if root is None:
        return ()
    features: list[Any] = []
    for item_id in sorted(_descendants(view, entity_id)):
        item = view.entities.get(item_id)
        if item is None or item.kind in {"source_unit", "call_site", "signature", "parameter"}:
            continue
        if item.kind in {"callable", "method", "class", "interface"}:
            features.append((item.kind, view.signature_shapes(item_id)))
        elif item.kind == "data":
            features.append(("data",))
        else:
            features.append((item.kind,))
    return tuple(sorted(features, key=_canonical_json))


def _open_world(value: ConstructionWorld | Path | str) -> tuple[ConstructionWorld, bool]:
    if isinstance(value, ConstructionWorld):
        return value, False
    path = Path(value)
    database = path / "world.sqlite" if path.is_dir() else path
    if not database.exists():
        raise ComparisonError(f"spine World does not exist: {database}")
    try:
        return ConstructionWorld.open(database), True
    except Exception as exc:
        raise ComparisonError(f"cannot open spine World {database}: {exc}") from exc


def _read_manifest(world: ConstructionWorld) -> Mapping[str, Any]:
    path = world.path.parent / "typescript.manifest.json"
    if not path.exists():
        raise ComparisonError(f"spine manifest is missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ComparisonError(f"spine manifest is invalid: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ComparisonError("spine manifest must be an object")
    return payload


def _safe_relation_rows(world: ConstructionWorld, relation: str) -> tuple[Mapping[str, Any], ...]:
    try:
        rows = world.relation_rows(relation)
    except Exception:
        return ()
    return tuple(_copy(row) for row in rows)


def _source_observations(world: ConstructionWorld, entity_id: str) -> tuple[Mapping[str, Any], ...]:
    rows = world.query(
        "SELECT reference, detail FROM _world_groundings "
        "WHERE subject_type='REFERENT' AND subject_id=? AND kind='SOURCE' "
        "ORDER BY reference, detail",
        (entity_id,),
    )
    observations: list[Mapping[str, Any]] = []
    for row in rows:
        detail = _parse_detail(row.get("detail"))
        observations.append(
            {
                "reference": str(row.get("reference") or ""),
                "provider": str(detail.get("provider") or ""),
                "native_handle": str(detail.get("native_handle") or ""),
                "source_revision": str(detail.get("source_revision") or ""),
                "native_location": str(detail.get("native_location") or ""),
            }
        )
    return tuple(observations)


def _validate_manifest(manifest: Mapping[str, Any], side: str) -> None:
    required = {"snapshot_id", "source_state", "boundary", "effective_inputs", "configuration"}
    missing = sorted(required - set(manifest))
    if missing:
        raise ComparisonError(f"{side} snapshot manifest missing {', '.join(missing)}")
    if not str(manifest.get("snapshot_id") or "").strip() or not str(manifest.get("source_state") or "").strip():
        raise ComparisonError(f"{side} snapshot manifest has empty identity")
    if not isinstance(manifest.get("boundary"), Mapping):
        raise ComparisonError(f"{side} snapshot declared boundary is malformed")
    if not isinstance(manifest.get("effective_inputs"), list) or not manifest["effective_inputs"]:
        raise ComparisonError(f"{side} snapshot effective inputs are missing or empty")
    if not isinstance(manifest.get("configuration"), Mapping):
        raise ComparisonError(f"{side} snapshot configuration is malformed")


def _empty_capability(
    *,
    capability_id: str,
    version: str,
    status: str,
    universe: str = "",
    basis: str = "",
    known_gaps: Mapping[str, Any] | None = None,
    completeness_receipt_refs: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "id": capability_id,
        "version": version,
        "status": status,
        "universe": universe,
        "basis": basis,
        "known_gaps": _copy(known_gaps or {}),
        "result": "",
        "completeness_receipt_refs": list(completeness_receipt_refs),
    }


def _load_snapshot(value: ConstructionWorld | Path | str, side: str) -> tuple[_SnapshotView, bool]:
    world, owned = _open_world(value)
    try:
        manifest = _read_manifest(world)
        _validate_manifest(manifest, side)
        snapshot_rows = _safe_relation_rows(world, "program_snapshot")
        if len(snapshot_rows) != 1:
            raise ComparisonError(f"{side} snapshot must contain exactly one program_snapshot row")
        snapshot_row = snapshot_rows[0]
        snapshot_ref = str(snapshot_row.get("snapshot") or "")
        snapshot_id = str(manifest["snapshot_id"])
        if not snapshot_ref:
            raise ComparisonError(f"{side} snapshot has no snapshot referent")
        if snapshot_row.get("core_contract") != "spine_core/v1":
            raise ComparisonError(f"{side} snapshot has incompatible core identity")
        receipt: SpineConstructionReceipt | None = None
        receipt_meta = manifest.get("receipt")
        if isinstance(receipt_meta, Mapping):
            receipt_path = world.path.parent / str(receipt_meta.get("path") or "")
            if not receipt_path.exists():
                raise ComparisonError(f"{side} construction receipt is missing: {receipt_path}")
            try:
                receipt = load_receipt(receipt_path)
            except Exception as exc:
                raise ComparisonError(f"{side} construction receipt is invalid: {exc}") from exc
            receipt_errors = receipt.validate(manifest)
            if receipt_errors:
                raise ComparisonError(f"{side} construction receipt failed validation: {'; '.join(receipt_errors)}")

        entity_rows = [row for row in _safe_relation_rows(world, "program_entity") if row.get("snapshot") == snapshot_ref]
        kind_rows = [row for row in _safe_relation_rows(world, "program_entity_kind") if row.get("snapshot") == snapshot_ref]
        descriptor_rows = [row for row in _safe_relation_rows(world, "program_identity_descriptor") if row.get("snapshot") == snapshot_ref]
        entity_ids = {str(row.get("entity") or "") for row in entity_rows if str(row.get("entity") or "")}
        kind_by_entity = {str(row["entity"]): str(row.get("kind") or "") for row in kind_rows if row.get("entity")}
        synthetic_by_entity = {str(row["entity"]): bool(row.get("synthetic")) for row in kind_rows if row.get("entity")}
        descriptor_by_entity = {str(row["entity"]): str(row.get("descriptor") or "") for row in descriptor_rows if row.get("entity")}
        labels = {
            str(row["id"]): str(row.get("label") or "")
            for row in world.query("SELECT id, label FROM _world_referents")
        }
        context_rows = [row for row in _safe_relation_rows(world, "structural_context") if row.get("snapshot") == snapshot_ref]
        parents: dict[str, set[str]] = {entity: set() for entity in entity_ids}
        children: dict[str, set[str]] = {entity: set() for entity in entity_ids}
        for row in context_rows:
            parent = str(row.get("parent") or "")
            child = str(row.get("child") or "")
            if parent not in entity_ids or child not in entity_ids:
                raise ComparisonError(f"{side} structural context endpoint is outside program universe")
            parents[child].add(parent)
            children[parent].add(child)

        workspace = _workspace_from_manifest(manifest)
        entities: dict[str, _Entity] = {}
        for row in entity_rows:
            entity_id = str(row["entity"])
            kind = kind_by_entity.get(entity_id, str(row.get("kind") or ""))
            if not kind:
                raise ComparisonError(f"{side} program entity has no identity kind: {entity_id}")
            if entity_id not in labels:
                raise ComparisonError(f"{side} program entity referent is missing: {entity_id}")
            evidence = _source_observations(world, entity_id)
            if not evidence:
                raise ComparisonError(f"{side} program entity has no reconstructible source evidence: {entity_id}")
            descriptor = descriptor_by_entity.get(entity_id, "")
            entities[entity_id] = _Entity(
                entity_id=entity_id,
                kind=kind,
                label=labels[entity_id],
                boundary=str(row.get("boundary") or ""),
                synthetic=bool(synthetic_by_entity.get(entity_id, False)),
                descriptor=descriptor,
                comparable_descriptor=_comparable_text(descriptor, workspace),
                parents=tuple(sorted(parents[entity_id])),
                children=tuple(sorted(children[entity_id])),
                evidence=evidence,
            )

        relation_names = set(COMPARABLE_RELATIONS) | set(RESOLUTION_RELATIONS)
        relations = {
            relation: tuple(
                row for row in _safe_relation_rows(world, relation)
                if row.get("snapshot") == snapshot_ref
            )
            for relation in sorted(relation_names)
        }
        for relation, rows in relations.items():
            if not rows:
                continue
            try:
                schema = world.relation_schema(relation)
            except Exception as exc:
                raise ComparisonError(f"{side} relation schema is missing: {relation}") from exc
            ref_roles = [
                role["name"]
                for role in schema["roles"]
                if role["type"] == "REFERENT" and role["name"] != "snapshot"
            ]
            for row in rows:
                for role in ref_roles:
                    value = str(row.get(role) or "")
                    if value and value not in entity_ids:
                        raise ComparisonError(f"{side} {relation} endpoint is outside program universe")

        capabilities: dict[str, Mapping[str, Any]] = {}
        for row in _safe_relation_rows(world, "program_capability"):
            if row.get("snapshot") != snapshot_ref:
                continue
            key = _capability_key(str(row.get("capability") or ""), str(row.get("version") or ""))
            if key in capabilities:
                raise ComparisonError(f"{side} duplicate capability record: {key}")
            capabilities[key] = _empty_capability(
                capability_id=str(row.get("capability") or ""),
                version=str(row.get("version") or ""),
                status=str(row.get("status") or ""),
                universe=str(row.get("universe") or ""),
                basis=str(row.get("basis") or ""),
                known_gaps=_parse_detail(row.get("known_gaps")) if row.get("known_gaps") else {},
            )
            capabilities[key]["result"] = str(row.get("result") or "")
        if receipt is not None:
            for item in receipt.capabilities:
                key = _capability_key(str(item.get("id") or ""), str(item.get("version") or ""))
                if key not in capabilities and str(item.get("status") or "") == "NOT_PRODUCED":
                    capabilities[key] = _empty_capability(
                        capability_id=str(item.get("id") or ""),
                        version=str(item.get("version") or ""),
                        status=str(item.get("status") or ""),
                        universe=str(item.get("scope") or ""),
                        basis=str(item.get("completeness_basis") or ""),
                        known_gaps={"items": list(item.get("known_gaps") or [])},
                        completeness_receipt_refs=list(item.get("completeness_receipt_refs") or []),
                    )
                elif key in capabilities:
                    capabilities[key] = {
                        **capabilities[key],
                        "completeness_receipt_refs": list(item.get("completeness_receipt_refs") or []),
                    }
        return _SnapshotView(
            world=world,
            manifest=manifest,
            receipt=receipt,
            snapshot_ref=snapshot_ref,
            snapshot_id=snapshot_id,
            snapshot_row=snapshot_row,
            entities=entities,
            capabilities=capabilities,
            relations=relations,
            descriptor_available=bool(entity_ids) and entity_ids <= set(descriptor_by_entity) and all(
                bool(descriptor_by_entity.get(entity_id)) for entity_id in entity_ids
            ),
            workspace=workspace,
        ), owned
    except Exception:
        if owned:
            world.close()
        raise


def _profile_metadata(view: _SnapshotView) -> dict[str, Any]:
    receipt_snapshot = view.receipt.snapshot if view.receipt is not None else {}
    extractor = receipt_snapshot.get("extractor") if isinstance(receipt_snapshot, Mapping) else {}
    profiles = receipt_snapshot.get("capability_profiles") if isinstance(receipt_snapshot, Mapping) else []
    profile_keys = sorted(
        f"{item.get('id')}/{item.get('version')}"
        for item in (profiles if isinstance(profiles, list) else [])
        if isinstance(item, Mapping)
    )
    locations = {
        "bytes" if str(item.get("native_location") or "").startswith("bytes:") else "input"
        for entity in view.entities.values()
        for item in entity.evidence
    }
    boundary = view.manifest.get("boundary") or {}
    policy = {
        key: boundary.get(key)
        for key in ("include_tests", "generated_files", "declarations", "external_dependencies")
    }
    return {
        "extractor": _copy(extractor) if isinstance(extractor, Mapping) else {},
        "profiles": profile_keys,
        "coordinate_conventions": sorted(locations),
        "boundary_policy": policy,
        "declared_boundary": _copy(boundary),
    }


def _capability_compatibility(
    old: _SnapshotView,
    new: _SnapshotView,
    *,
    representation_compatible: bool,
) -> dict[str, Mapping[str, Any]]:
    old_caps = old.capability_by_base()
    new_caps = new.capability_by_base()
    result: dict[str, Mapping[str, Any]] = {}
    for base in sorted(set(old_caps) | set(new_caps)):
        left = old_caps.get(base)
        right = new_caps.get(base)
        old_version = str(left.get("version") if left else "")
        new_version = str(right.get("version") if right else "")
        refs = {
            "old": list(left.get("completeness_receipt_refs") or []) if left else [],
            "new": list(right.get("completeness_receipt_refs") or []) if right else [],
        }
        limitations: list[str] = []
        status = "COMPARABLE"
        if left is None or right is None:
            status = "NOT_COMPARABLE"
            limitations.append("capability is absent from one snapshot")
        elif left.get("status") == "NOT_PRODUCED" or right.get("status") == "NOT_PRODUCED":
            status = "NOT_PRODUCED"
            limitations.append("capability was not produced on one or both sides")
        elif old_version != new_version:
            status = "NOT_COMPARABLE"
            limitations.append("capability versions differ")
        elif not representation_compatible:
            status = "NOT_COMPARABLE"
            limitations.append("snapshot representation contracts are incompatible")
        elif left.get("status") not in {"COMPLETE", "STATIC_COMPLETE"} or right.get("status") not in {"COMPLETE", "STATIC_COMPLETE"}:
            status = "PARTIAL"
            limitations.append("one or both capability records are not complete")
        result[base] = {
            "id": base,
            "old_version": old_version,
            "new_version": new_version,
            "status": status,
            "basis": {"old": left.get("basis") if left else "", "new": right.get("basis") if right else ""},
            "scope": {"old": left.get("universe") if left else "", "new": right.get("universe") if right else ""},
            "limitations": limitations,
            "completeness_receipt_refs": refs,
        }
    return result


def _compatibility(old: _SnapshotView, new: _SnapshotView) -> tuple[dict[str, Any], dict[str, Mapping[str, Any]]]:
    old_meta = _profile_metadata(old)
    new_meta = _profile_metadata(new)
    core = str(old.snapshot_row.get("core_contract") or "") == str(new.snapshot_row.get("core_contract") or "") == "spine_core/v1"
    extractor = old_meta["extractor"] == new_meta["extractor"]
    profiles = old_meta["profiles"] == new_meta["profiles"]
    coordinates = old_meta["coordinate_conventions"] == new_meta["coordinate_conventions"]
    boundary_policy = old_meta["boundary_policy"] == new_meta["boundary_policy"]
    descriptor = old.descriptor_available and new.descriptor_available
    representation_compatible = all((core, extractor, profiles, coordinates, boundary_policy, descriptor))
    limitations: list[str] = []
    for condition, message in (
        (core, "core contract versions differ"),
        (extractor, "extractor identities or versions differ without a compatibility declaration"),
        (profiles, "declared capability profile versions differ"),
        (coordinates, "source-coordinate conventions differ"),
        (boundary_policy, "boundary policies differ"),
        (descriptor, "deterministic identity descriptors are not available in both snapshots"),
    ):
        if not condition:
            limitations.append(message)
    capability_results = _capability_compatibility(old, new, representation_compatible=representation_compatible)
    result = {
        "status": "COMPATIBLE" if representation_compatible else "INCOMPATIBLE",
        "core": "COMPATIBLE" if core else "INCOMPATIBLE",
        "extractor": "COMPATIBLE" if extractor else "INCOMPATIBLE",
        "capability_profiles": "COMPATIBLE" if profiles else "INCOMPATIBLE",
        "identity_descriptors": "AVAILABLE" if descriptor else "MISSING",
        "coordinate_conventions": "COMPATIBLE" if coordinates else "INCOMPATIBLE",
        "boundary_policy": "COMPATIBLE" if boundary_policy else "INCOMPATIBLE",
        "declared_boundary": "SAME" if old_meta["declared_boundary"] == new_meta["declared_boundary"] else "CHANGED",
        "limitations": limitations,
        "capabilities": [capability_results[name] for name in sorted(capability_results)],
    }
    return result, capability_results


def _entity_candidates(
    old: _SnapshotView,
    new: _SnapshotView,
    old_entity: _Entity,
    mapping: Mapping[str, str],
    used_new: set[str],
) -> tuple[list[str], dict[str, list[Mapping[str, Any]]]]:
    if old_entity.boundary == "EXTERNAL_BOUNDARY":
        return [], {}
    candidates = [
        entity.entity_id
        for entity in new.entities.values()
        if entity.entity_id not in used_new
        and entity.kind == old_entity.kind
        and entity.synthetic == old_entity.synthetic
        and entity.boundary == old_entity.boundary
    ]
    mapped_parents = {mapping[parent] for parent in old_entity.parents if parent in mapping}
    parents_are_known = bool(old_entity.parents) and len(mapped_parents) == len(old_entity.parents)
    by_parent = [
        entity_id
        for entity_id in candidates
        if set(new.entities[entity_id].parents) == mapped_parents
    ] if parents_are_known else []
    evidence: dict[str, list[Mapping[str, Any]]] = {}

    def add(candidate_ids: Iterable[str], *rules: str) -> list[str]:
        selected = sorted(set(candidate_ids))
        items = [
            {"kind": AUTOMATIC_BASIS_CLASS, "rule": "identity kind preserved", "old_kind": old_entity.kind},
            *({"kind": AUTOMATIC_BASIS_CLASS, "rule": rule} for rule in rules),
        ]
        for candidate_id in selected:
            evidence.setdefault(candidate_id, []).extend(_copy(item) for item in items)
        return selected

    if old_entity.kind == "module":
        fingerprint = _module_fingerprint(old, old_entity.entity_id)
        if fingerprint:
            selected = add(
                [
                    entity_id
                    for entity_id in candidates
                    if _module_fingerprint(new, entity_id) == fingerprint
                ],
                "preserved structural neighbor fingerprint",
            )
            if selected:
                return selected, evidence

    if old_entity.kind == "source_unit" and len(by_parent) == 1:
        return add(by_parent, "preserved module structural context"), evidence

    if old_entity.kind == "call_site" and by_parent:
        if len(by_parent) == 1:
            return add(by_parent, "preserved owning context", "unique occurrence in owner"), evidence
        old_rank = old.occurrence_rank(old_entity.entity_id)[0]
        selected = [
            entity_id
            for entity_id in by_parent
            if new.occurrence_rank(entity_id)[0] == old_rank
        ]
        if selected:
            return add(selected, "preserved owning context", "preserved occurrence order"), evidence

    signature_shapes = old.signature_shapes(old_entity.entity_id)
    if by_parent and signature_shapes:
        selected = [
            entity_id for entity_id in by_parent
            if new.signature_shapes(entity_id) == signature_shapes
        ]
        if selected:
            rules = ["preserved structural context", "preserved signature descriptor"]
            if len(selected) == 1 and new.entities[selected[0]].label == old_entity.label:
                rules.append("declaration name preserved")
            return add(selected, *rules), evidence

    if by_parent and old_entity.label:
        named = [entity_id for entity_id in by_parent if new.entities[entity_id].label == old_entity.label]
        if named:
            return add(named, "preserved structural context", "declaration name preserved"), evidence

    if old_entity.kind in {"callable", "method", "class", "interface"} and signature_shapes:
        mapped_units = {
            mapping[unit]
            for unit in _enclosing(old, old_entity.entity_id, {"source_unit", "module"})
            if unit in mapping
        }
        if mapped_units:
            selected = [
                entity_id
                for entity_id in candidates
                if new.signature_shapes(entity_id) == signature_shapes
                and mapped_units.intersection(_enclosing(new, entity_id, {"source_unit", "module"}))
            ]
            if selected:
                return add(selected, "preserved enclosing source unit", "preserved signature descriptor"), evidence
    return [], evidence


def _descriptor_exact_matches(old: _SnapshotView, new: _SnapshotView) -> tuple[dict[str, str], dict[str, list[Mapping[str, Any]]]]:
    old_groups: dict[tuple[str, str, str], list[str]] = {}
    new_groups: dict[tuple[str, str, str], list[str]] = {}
    for entity in old.entities.values():
        if entity.comparable_descriptor:
            old_groups.setdefault((entity.kind, entity.boundary, entity.comparable_descriptor), []).append(entity.entity_id)
    for entity in new.entities.values():
        if entity.comparable_descriptor:
            new_groups.setdefault((entity.kind, entity.boundary, entity.comparable_descriptor), []).append(entity.entity_id)
    mapping: dict[str, str] = {}
    evidence: dict[str, list[Mapping[str, Any]]] = {}
    for key in sorted(set(old_groups) & set(new_groups)):
        left = sorted(old_groups[key])
        right = sorted(new_groups[key])
        if len(left) == 1 and len(right) == 1:
            mapping[left[0]] = right[0]
            evidence[left[0]] = [
                {
                    "kind": AUTOMATIC_BASIS_CLASS,
                    "rule": "compatible identity descriptor equality",
                },
                {
                    "kind": AUTOMATIC_BASIS_CLASS,
                    "rule": "identity kind and boundary preserved",
                },
            ]
    return mapping, evidence


def _manifestation_changes(
    old: _SnapshotView,
    new: _SnapshotView,
    old_id: str,
    new_id: str,
    mapping: Mapping[str, str],
) -> dict[str, str]:
    old_entity = old.entities[old_id]
    new_entity = new.entities[new_id]
    mapped_parents = {mapping[parent] for parent in old_entity.parents if parent in mapping}
    parents_known = bool(old_entity.parents) and len(mapped_parents) == len(old_entity.parents)
    structural = "PRESERVED" if parents_known and mapped_parents == set(new_entity.parents) else "CHANGED"
    if not old_entity.parents and not new_entity.parents:
        structural = "PRESERVED"
    return {
        "name": "PRESERVED" if old_entity.label == new_entity.label else "CHANGED",
        "source_location": "PRESERVED" if _source_locations(old_entity) == _source_locations(new_entity) else "CHANGED",
        "source_manifestation": "PRESERVED" if _source_manifestation(old_entity) == _source_manifestation(new_entity) else "CHANGED",
        "structural_context": structural,
        "signature": "PRESERVED" if old.signature_shapes(old_id) == new.signature_shapes(new_id) else "CHANGED",
        "boundary": "PRESERVED" if old_entity.boundary == new_entity.boundary else "CHANGED",
        "identity_kind": "PRESERVED" if old_entity.kind == new_entity.kind else "CHANGED",
    }


def _movement_detected(old: _SnapshotView, new: _SnapshotView, old_id: str, new_id: str, changes: Mapping[str, str]) -> bool:
    return _source_paths(old.entities[old_id]) != _source_paths(new.entities[new_id]) or changes.get("structural_context") == "CHANGED"


def _outcome_for_changes(changes: Mapping[str, str], moved: bool) -> str:
    renamed = changes.get("name") == "CHANGED"
    if renamed and moved:
        return "RENAME_AND_MOVE"
    if renamed:
        return "RENAME"
    if moved:
        return "MOVE"
    return "UNCHANGED_OR_CONTINUED"


def _relation_schema(world: ConstructionWorld, relation: str) -> tuple[str, ...]:
    schema = world.relation_schema(relation)
    return tuple(
        role["name"]
        for role in schema["roles"]
        if role["type"] == "REFERENT" and role["name"] != "snapshot"
    )


def _row_key(row: Mapping[str, Any], roles: Sequence[str]) -> tuple[Any, ...]:
    return tuple(row.get(role) for role in roles)


def _resolution_status(view: _SnapshotView, subject: str, capability: str) -> str:
    for row in view.relations.get("program_resolution", ()):
        if row.get("subject") == subject and row.get("capability") == capability:
            return str(row.get("status") or "")
    return ""


def _empty_relation_delta(capability: str, status: str, limitations: Sequence[str]) -> dict[str, Any]:
    return {
        "capability": capability,
        "status": status,
        "preserved": [],
        "added": [],
        "removed": [],
        "retargeted": [],
        "unresolved": [],
        "limitations": list(limitations),
    }


def _relation_delta(
    old: _SnapshotView,
    new: _SnapshotView,
    mapping: Mapping[str, str],
    uncertain: set[str],
    capability_results: Mapping[str, Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    for relation in COMPARABLE_RELATIONS:
        capability = RELATION_CAPABILITIES[relation]
        cap = capability_results.get(capability, {"status": "NOT_COMPARABLE"})
        status = str(cap.get("status") or "NOT_COMPARABLE")
        if status in {"NOT_COMPARABLE", "NOT_PRODUCED"}:
            output[relation] = _empty_relation_delta(capability, "NOT_COMPARABLE", list(cap.get("limitations") or []))
            continue
        old_rows = list(old.relations.get(relation, ()))
        new_rows = list(new.relations.get(relation, ()))
        roles = _relation_schema(old.world, relation)
        new_roles = _relation_schema(new.world, relation)
        if roles != new_roles:
            output[relation] = _empty_relation_delta(capability, "NOT_COMPARABLE", ["relation endpoint roles differ"])
            continue
        new_by_key = {_row_key(row, roles): row for row in new_rows}
        consumed: set[tuple[Any, ...]] = set()
        preserved: list[Mapping[str, Any]] = []
        added: list[Mapping[str, Any]] = []
        removed: list[Mapping[str, Any]] = []
        retargeted: list[Mapping[str, Any]] = []
        unresolved_rows: list[Mapping[str, Any]] = []
        for old_row in old_rows:
            endpoints = {role: str(old_row.get(role) or "") for role in roles}
            if any(value in uncertain for value in endpoints.values()):
                unresolved_rows.append({"old": _copy(old_row), "reason": "correspondence endpoint is ambiguous or unresolved"})
                continue
            mapped = {role: mapping.get(value) for role, value in endpoints.items()}
            mapped_complete = all(value is not None for value in mapped.values())
            if mapped_complete:
                expected = tuple(mapped[role] for role in roles)
                exact = new_by_key.get(expected)
                if exact is not None and expected not in consumed:
                    consumed.add(expected)
                    preserved.append({"old": _copy(old_row), "new": _copy(exact)})
                    continue
            unique_rows: dict[tuple[Any, ...], Mapping[str, Any]] = {}
            multiple = False
            for role, new_id in mapped.items():
                if new_id is None:
                    continue
                matches = [
                    row for row in new_rows
                    if row.get(role) == new_id and _row_key(row, roles) not in consumed
                ]
                if len(matches) > 1:
                    multiple = True
                elif len(matches) == 1:
                    unique_rows[_row_key(matches[0], roles)] = matches[0]
            if multiple and len(unique_rows) != 1:
                unresolved_rows.append({"old": _copy(old_row), "reason": "multiple relation targets"})
                continue
            if len(unique_rows) == 1:
                new_key, new_row = next(iter(unique_rows.items()))
                consumed.add(new_key)
                changed = [role for role in roles if mapped.get(role) != str(new_row.get(role) or "")]
                if not changed and mapped_complete:
                    preserved.append({"old": _copy(old_row), "new": _copy(new_row)})
                else:
                    retargeted.append(
                        {
                            "old": _copy(old_row),
                            "new": _copy(new_row),
                            "changed_endpoint": changed[-1] if changed else roles[-1],
                        }
                    )
                continue
            if relation == "program_invokes":
                call_site_new = mapped.get("call_site")
                if call_site_new:
                    resolution = _resolution_status(new, str(call_site_new), "spine.calls/v1")
                    if resolution in {"UNRESOLVED", "MULTIPLE_CANDIDATES"} or not resolution:
                        unresolved_rows.append(
                            {"old": _copy(old_row), "reason": f"new call-site resolution is {resolution or 'missing'}"}
                        )
                        continue
            if status == "PARTIAL":
                unresolved_rows.append({"old": _copy(old_row), "reason": "relation capability is partial"})
            else:
                removed.append({"old": _copy(old_row)})
        for row in new_rows:
            key = _row_key(row, roles)
            if key in consumed:
                continue
            endpoints = [str(row.get(role) or "") for role in roles]
            if any(value in uncertain for value in endpoints):
                unresolved_rows.append({"new": _copy(row), "reason": "new relation endpoint is ambiguous or unresolved"})
            else:
                added.append({"new": _copy(row)})
        output[relation] = {
            "capability": capability,
            "status": status,
            "preserved": preserved,
            "added": added,
            "removed": removed,
            "retargeted": retargeted,
            "unresolved": unresolved_rows,
            "limitations": list(cap.get("limitations") or []),
        }
    return output


def _identity_delta(
    old: _SnapshotView,
    new: _SnapshotView,
    mapping: Mapping[str, str],
    claims: Sequence[CorrespondenceClaim],
    groups: Sequence[CorrespondenceGroup],
    grouped_old: set[str],
    grouped_new: set[str],
    ambiguous_records: Mapping[str, Mapping[str, Any]],
    unresolved_old: Mapping[str, Mapping[str, Any]],
    unresolved_new: Mapping[str, Mapping[str, Any]],
    identity_complete: bool,
) -> dict[str, Any]:
    ambiguous_new = {
        candidate
        for item in ambiguous_records.values()
        for candidate in item.get("candidates", [])
    }
    continued = [
        {
            "old_entity": claim.old_entity,
            "new_entity": claim.new_entity,
            "outcome": claim.outcome,
            "basis_class": claim.basis_class,
        }
        for claim in claims
        if claim.continuity == "CONTINUED"
    ]
    mapped_old = set(mapping)
    mapped_new = set(mapping.values())
    removed = sorted(
        entity.entity_id
        for entity in old.entities.values()
        if entity.entity_id not in mapped_old
        and entity.entity_id not in grouped_old
        and entity.entity_id not in ambiguous_records
        and entity.entity_id not in unresolved_old
        and identity_complete
    )
    added = sorted(
        entity.entity_id
        for entity in new.entities.values()
        if entity.entity_id not in mapped_new
        and entity.entity_id not in grouped_new
        and entity.entity_id not in ambiguous_new
        and entity.entity_id not in unresolved_new
        and identity_complete
    )
    return {
        "continued": continued,
        "added": added,
        "removed": removed,
        "split": [group.to_dict() for group in groups if group.event == "SPLIT"],
        "merged": [group.to_dict() for group in groups if group.event == "MERGE"],
        "ambiguous": [
            {
                "old_entity": old_id,
                "candidate_entities": list(item.get("candidates") or []),
                "reason": item.get("reason", "multiple deterministic candidates"),
            }
            for old_id, item in sorted(ambiguous_records.items())
        ],
        "unresolved": (
            [{"old_entity": old_id, **_copy(item)} for old_id, item in sorted(unresolved_old.items())]
            + [{"new_entity": new_id, **_copy(item)} for new_id, item in sorted(unresolved_new.items())]
        ),
        "universe_basis": "complete comparable program universe" if identity_complete else "incomplete or not-comparable program universe",
    }


def _manifestation_delta(
    old: _SnapshotView,
    new: _SnapshotView,
    claims: Sequence[CorrespondenceClaim],
) -> tuple[Mapping[str, Any], ...]:
    output: list[Mapping[str, Any]] = []
    for claim in claims:
        if claim.continuity != "CONTINUED" or not claim.old_entity or not claim.new_entity:
            continue
        changes = dict(claim.changes)
        if not any(value == "CHANGED" for value in changes.values()):
            continue
        output.append(
            {
                "old_entity": claim.old_entity,
                "new_entity": claim.new_entity,
                "outcome": claim.outcome,
                "basis_class": claim.basis_class,
                "changes": changes,
                "old_evidence": [_copy(item) for item in old.source_evidence(claim.old_entity)],
                "new_evidence": [_copy(item) for item in new.source_evidence(claim.new_entity)],
            }
        )
    return tuple(output)


def _changed(changes: Mapping[str, str], key: str) -> bool:
    return changes.get(key) == "CHANGED"


def _maintenance_records(
    old: _SnapshotView,
    new: _SnapshotView,
    claims: Sequence[CorrespondenceClaim],
    relations: Mapping[str, Mapping[str, Any]],
    ambiguous_records: Mapping[str, Mapping[str, Any]],
    unresolved_old: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    records: list[Mapping[str, Any]] = []

    def relation_flags(old_id: str, new_id: str) -> tuple[bool, list[str]]:
        changed = False
        retargeted: list[str] = []
        for relation, payload in relations.items():
            if payload.get("status") == "NOT_COMPARABLE":
                continue
            for bucket in ("added", "removed", "retargeted", "unresolved"):
                for item in payload.get(bucket) or []:
                    old_row = item.get("old") if isinstance(item, Mapping) else None
                    new_row = item.get("new") if isinstance(item, Mapping) else None
                    values = set()
                    if isinstance(old_row, Mapping):
                        values.update(str(value) for value in old_row.values())
                    if isinstance(new_row, Mapping):
                        values.update(str(value) for value in new_row.values())
                    if old_id in values or new_id in values:
                        changed = True
                        if bucket == "retargeted":
                            retargeted.append(relation)
        return changed, sorted(set(retargeted))

    for claim in claims:
        if claim.continuity != "CONTINUED" or not claim.old_entity or not claim.new_entity:
            continue
        changes = claim.changes
        relations_changed, retargeted = relation_flags(claim.old_entity, claim.new_entity)
        old_resolution = _resolution_status(old, claim.old_entity, "spine.calls/v1")
        new_resolution = _resolution_status(new, claim.new_entity, "spine.calls/v1")
        records.append(
            {
                "old_entity": claim.old_entity,
                "new_entity": claim.new_entity,
                "manifestation_continued": True,
                "name_changed": _changed(changes, "name"),
                "structural_context_changed": _changed(changes, "structural_context"),
                "source_manifestation_changed": _changed(changes, "source_manifestation"),
                "source_location_changed": _changed(changes, "source_location"),
                "signature_changed": _changed(changes, "signature"),
                "boundary_changed": _changed(changes, "boundary"),
                "identity_kind_changed": _changed(changes, "identity_kind"),
                "relations_changed": relations_changed,
                "retargeted_relations": retargeted,
                "resolution_changed": bool(old_resolution or new_resolution) and old_resolution != new_resolution,
                "ambiguous_or_unresolved": False,
            }
        )
    for old_id, item in sorted(ambiguous_records.items()):
        records.append(
            {
                "old_entity": old_id,
                "new_entity": None,
                "manifestation_continued": False,
                "candidate_entities": list(item.get("candidates") or []),
                "ambiguous_or_unresolved": True,
            }
        )
    for old_id in sorted(unresolved_old):
        records.append(
            {
                "old_entity": old_id,
                "new_entity": None,
                "manifestation_continued": False,
                "ambiguous_or_unresolved": True,
            }
        )
    return tuple(records)


def _summary_counts(delta: ProgramDelta, claims: Sequence[CorrespondenceClaim]) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    outcomes = {key.lower(): 0 for key in (
        "UNCHANGED_OR_CONTINUED", "RENAME", "MOVE", "RENAME_AND_MOVE",
        "SPLIT", "MERGE", "DELETED", "NEW", "AMBIGUOUS", "UNRESOLVED",
    )}
    basis = {"deterministic": 0, "heuristic": 0, "observational": 0}
    for claim in claims:
        outcomes[claim.outcome.lower()] = outcomes.get(claim.outcome.lower(), 0) + 1
        basis[claim.basis_class.lower()] = basis.get(claim.basis_class.lower(), 0) + 1
    outcomes["deleted"] += len(delta.identity.get("removed") or [])
    outcomes["new"] += len(delta.identity.get("added") or [])
    outcomes["split"] += len(delta.identity.get("split") or [])
    outcomes["merge"] += len(delta.identity.get("merged") or [])
    properties: dict[str, int] = {}
    for item in delta.manifestations:
        for name, status in (item.get("changes") or {}).items():
            if status == "CHANGED":
                properties[name] = properties.get(name, 0) + 1
    return outcomes, basis, properties


def _relation_summary(delta: ProgramDelta) -> dict[str, Any]:
    return {
        relation: {
            "status": item.get("status"),
            "preserved": len(item.get("preserved") or []),
            "added": len(item.get("added") or []),
            "removed": len(item.get("removed") or []),
            "retargeted": len(item.get("retargeted") or []),
            "unresolved": len(item.get("unresolved") or []),
            "limitations": list(item.get("limitations") or []),
        }
        for relation, item in sorted(delta.relations.items())
    }


def _entity_ref(view: _SnapshotView, entity_id: str | None) -> dict[str, Any] | None:
    if not entity_id or entity_id not in view.entities:
        return None
    entity = view.entities[entity_id]
    return {"entity": entity.entity_id, "label": entity.label, "kind": entity.kind, "boundary": entity.boundary}


def _representative_examples(
    old: _SnapshotView,
    new: _SnapshotView,
    claims: Sequence[CorrespondenceClaim],
    relations: Mapping[str, Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    examples: list[Mapping[str, Any]] = []
    for claim in claims:
        if claim.continuity == "CONTINUED" and any(value == "CHANGED" for value in claim.changes.values()):
            examples.append(
                {
                    "kind": "correspondence",
                    "old": _entity_ref(old, claim.old_entity),
                    "new": _entity_ref(new, claim.new_entity),
                    "continuity": claim.continuity,
                    "outcome": claim.outcome,
                    "basis_class": claim.basis_class,
                    "basis": [_copy(item) for item in claim.evidence],
                    "changes": _copy(claim.changes),
                }
            )
            break
    for relation, item in sorted(relations.items()):
        if item.get("retargeted"):
            row = item["retargeted"][0]
            examples.append(
                {
                    "kind": "relation_retarget",
                    "relation": relation,
                    "capability": item.get("capability"),
                    "old": _copy(row.get("old")),
                    "new": _copy(row.get("new")),
                    "changed_endpoint": row.get("changed_endpoint"),
                }
            )
            break
    if not examples and claims:
        claim = claims[0]
        examples.append(
            {
                "kind": "correspondence",
                "old": _entity_ref(old, claim.old_entity),
                "new": _entity_ref(new, claim.new_entity),
                "continuity": claim.continuity,
                "outcome": claim.outcome,
                "basis_class": claim.basis_class,
                "basis": [_copy(item) for item in claim.evidence],
                "changes": _copy(claim.changes),
            }
        )
    return tuple(examples)


def _known_losses(old: _SnapshotView, new: _SnapshotView) -> tuple[str, ...]:
    losses = {
        "v0 does not ingest Git/source-diff records",
        "v0 automatic correspondence is computationally deterministic but epistemically heuristic; no implemented rule mechanically entails identity continuity",
        "automatic split/merge detection is deferred; supplied groups remain comparison-local",
        "comparison artifacts are stored as an application sidecar rather than a sealed World",
    }
    for prefix, view in (("old", old), ("new", new)):
        if view.receipt is None:
            losses.add(f"{prefix} construction receipt was unavailable")
        else:
            for item in view.receipt.losses:
                statement = str(item.get("statement") or "")
                if statement:
                    losses.add(f"{prefix} spine: {statement}")
    return tuple(sorted(losses))


def _validate_groups(
    groups: Sequence[CorrespondenceGroup],
    old: _SnapshotView,
    new: _SnapshotView,
) -> None:
    old_ids = set(old.entities)
    new_ids = set(new.entities)
    seen_old: set[str] = set()
    seen_new: set[str] = set()
    for group in groups:
        errors = group.validate()
        if errors:
            raise ComparisonError("; ".join(errors))
        if not set(group.old_entities) <= old_ids:
            raise ComparisonError(f"comparison group {group.group_id} contains an old entity outside the snapshot")
        if not set(group.new_entities) <= new_ids:
            raise ComparisonError(f"comparison group {group.group_id} contains a new entity outside the snapshot")
        if seen_old & set(group.old_entities) or seen_new & set(group.new_entities):
            raise ComparisonError("comparison groups overlap on one snapshot side")
        seen_old.update(group.old_entities)
        seen_new.update(group.new_entities)


def _compare_views(
    old: _SnapshotView,
    new: _SnapshotView,
    *,
    groups: Sequence[CorrespondenceGroup],
) -> SpineComparisonResult:
    compatibility, capability_results = _compatibility(old, new)
    grouped_old = _expand_ids(old, {entity for group in groups for entity in group.old_entities})
    grouped_new = _expand_ids(new, {entity for group in groups for entity in group.new_entities})
    exact_mapping, match_evidence = _descriptor_exact_matches(old, new)
    mapping = {
        old_id: new_id
        for old_id, new_id in exact_mapping.items()
        if old_id not in grouped_old and new_id not in grouped_new
    }
    used_new = set(mapping.values())
    ambiguous_records: dict[str, Mapping[str, Any]] = {}
    unresolved_old: dict[str, Mapping[str, Any]] = {}
    unresolved_new: dict[str, Mapping[str, Any]] = {}
    identity_complete = (
        compatibility.get("status") == "COMPATIBLE"
        and capability_results.get("spine.program_universe", {}).get("status") == "COMPARABLE"
        and capability_results.get("spine.code_structure", {}).get("status") == "COMPARABLE"
    )
    old_entities = sorted(
        (entity for entity in old.entities.values() if entity.entity_id not in grouped_old),
        key=lambda entity: (ENTITY_KIND_ORDER.get(entity.kind, 100), _depth(old, entity.entity_id), entity.entity_id),
    )
    for entity in old_entities:
        if entity.entity_id in mapping:
            continue
        ancestor_ids = _ancestors(old, entity.entity_id)
        if any(ancestor in ambiguous_records or ancestor in unresolved_old or ancestor in grouped_old for ancestor in ancestor_ids):
            unresolved_old[entity.entity_id] = {
                "reason": "owning context is ambiguous, unresolved, or part of a cardinality group",
                "candidates": [],
            }
            continue
        candidate_ids, evidence = _entity_candidates(old, new, entity, mapping, used_new)
        candidate_ids = [
            candidate
            for candidate in candidate_ids
            if candidate not in grouped_new and candidate not in used_new
        ]
        if len(candidate_ids) == 1:
            selected = candidate_ids[0]
            mapping[entity.entity_id] = selected
            used_new.add(selected)
            match_evidence[entity.entity_id] = evidence.get(selected, [])
        elif len(candidate_ids) > 1:
            ambiguous_records[entity.entity_id] = {
                "candidates": tuple(candidate_ids),
                "reason": "multiple deterministic candidates remain",
                "evidence": tuple(evidence.get(candidate, []) for candidate in candidate_ids),
            }
        elif not identity_complete:
            unresolved_old[entity.entity_id] = {
                "reason": "no deterministic candidate under an incomplete or incompatible identity universe",
                "candidates": [],
            }

    ambiguous_new = {
        candidate
        for item in ambiguous_records.values()
        for candidate in item.get("candidates", [])
    }
    for candidate in list(ambiguous_new):
        ambiguous_new.update(_descendants(new, candidate))
    if not identity_complete:
        for entity in new.entities.values():
            if (
                entity.entity_id not in used_new
                and entity.entity_id not in grouped_new
                and entity.entity_id not in ambiguous_new
            ):
                unresolved_new[entity.entity_id] = {
                    "reason": "no deterministic candidate under an incomplete or incompatible identity universe",
                    "candidates": [],
                }

    claims: list[CorrespondenceClaim] = []
    for old_id, new_id in sorted(mapping.items()):
        changes = _manifestation_changes(old, new, old_id, new_id, mapping)
        outcome = _outcome_for_changes(changes, _movement_detected(old, new, old_id, new_id, changes))
        evidence = tuple(match_evidence.get(old_id, ()))
        claims.append(
            CorrespondenceClaim(
                old_entity=old_id,
                new_entity=new_id,
                continuity="CONTINUED",
                outcome=outcome,
                basis_class=_claim_basis(evidence),
                evidence=evidence,
                changes=changes,
                limitations=("heuristic correspondence is not mechanically entailed identity continuity",)
                if _claim_basis(evidence) == "HEURISTIC"
                else (),
            )
        )
    for old_id, record in sorted(ambiguous_records.items()):
        candidates = tuple(str(item) for item in record.get("candidates", ()))
        evidence = (
            {
                "kind": AUTOMATIC_BASIS_CLASS,
                "rule": "multiple heuristic candidates remain",
            },
        )
        claims.append(
            CorrespondenceClaim(
                old_entity=old_id,
                new_entity=None,
                continuity="AMBIGUOUS",
                outcome="AMBIGUOUS",
                basis_class=_claim_basis(evidence),
                evidence=evidence,
                candidate_entities=candidates,
                limitations=("no one continuation is selected",),
            )
        )
    for old_id in sorted(unresolved_old):
        evidence = (
            {
                "kind": AUTOMATIC_BASIS_CLASS,
                "rule": "no unique heuristic correspondence established",
            },
        )
        claims.append(
            CorrespondenceClaim(
                old_entity=old_id,
                new_entity=None,
                continuity="UNRESOLVED",
                outcome="UNRESOLVED",
                basis_class=_claim_basis(evidence),
                evidence=evidence,
            )
        )

    identity = _identity_delta(
        old,
        new,
        mapping,
        claims,
        groups,
        grouped_old,
        grouped_new,
        ambiguous_records,
        unresolved_old,
        unresolved_new,
        identity_complete,
    )
    manifestations = _manifestation_delta(old, new, claims)
    uncertain = set(ambiguous_records) | ambiguous_new | set(unresolved_old) | set(unresolved_new)
    relations = _relation_delta(old, new, mapping, uncertain, capability_results)
    maintenance = _maintenance_records(old, new, claims, relations, ambiguous_records, unresolved_old)
    delta = ProgramDelta(
        old_snapshot=old.snapshot_id,
        new_snapshot=new.snapshot_id,
        identity=identity,
        manifestations=manifestations,
        relations=relations,
        groups=tuple(groups),
        maintenance=maintenance,
    )
    outcomes, basis_counts, property_counts = _summary_counts(delta, claims)
    comparison_id = f"comparison:{_digest({
        'old_snapshot': old.snapshot_id,
        'new_snapshot': new.snapshot_id,
        'mechanism': f'{COMPARISON_MECHANISM_ID}@{COMPARISON_MECHANISM_VERSION}',
        'compatibility': compatibility,
        'capabilities': capability_results,
        'groups': [group.to_dict() for group in groups],
    })}"
    not_comparable = tuple(
        f"{base}/{record.get('old_version') or record.get('new_version')}"
        for base, record in sorted(capability_results.items())
        if record.get("status") in {"NOT_COMPARABLE", "NOT_PRODUCED"}
    )
    receipt = SpineComparisonReceipt(
        receipt_version=COMPARISON_RECEIPT_VERSION,
        comparison_id=comparison_id,
        conformance={"status": "PASS", "diagnostics": []},
        snapshots={
            "old": {
                "id": old.snapshot_id,
                "source_state": old.manifest.get("source_state"),
                "construction_receipt": old.receipt.construction_id if old.receipt else None,
            },
            "new": {
                "id": new.snapshot_id,
                "source_state": new.manifest.get("source_state"),
                "construction_receipt": new.receipt.construction_id if new.receipt else None,
            },
        },
        compatibility=compatibility,
        comparison_mechanism={
            "id": COMPARISON_MECHANISM_ID,
            "version": COMPARISON_MECHANISM_VERSION,
            "configuration": {
                "automatic_matching": "deterministic_computation",
                "automatic_correspondence_basis": AUTOMATIC_BASIS_CLASS,
                "epistemic_policy": "heuristic_unless_entailed",
            },
            "optional_inputs": [],
        },
        correspondence_summary={
            "outcomes": outcomes,
            "basis_classes": basis_counts,
            "claim_count": len(claims),
        },
        delta_summary={
            "identity": {
                key: len(value) if isinstance(value, list) else value
                for key, value in identity.items()
                if key != "universe_basis"
            },
            "properties": property_counts,
            "relations": _relation_summary(delta),
        },
        split_merge_summary={
            "split": [group.to_dict() for group in groups if group.event == "SPLIT"],
            "merge": [group.to_dict() for group in groups if group.event == "MERGE"],
        },
        known_losses=_known_losses(old, new),
        not_comparable_capabilities=not_comparable,
        representative_examples=_representative_examples(old, new, claims, relations),
        completeness_receipt_refs={
            base: _copy(record.get("completeness_receipt_refs") or {})
            for base, record in sorted(capability_results.items())
        },
    )
    result = SpineComparisonResult(
        receipt=receipt,
        correspondences=tuple(claims),
        groups=tuple(groups),
        delta=delta,
    )
    errors = result.validate()
    if errors:
        raise ComparisonError("comparison result failed validation: " + "; ".join(errors))
    return result


def compare_program_spines(
    old: ConstructionWorld | Path | str,
    new: ConstructionWorld | Path | str,
    *,
    output_dir: Path | str | None = None,
    groups: Iterable[CorrespondenceGroup] = (),
) -> SpineComparisonResult:
    """Compare two already-constructed native spine snapshots deterministically."""

    old_view, old_owned = _load_snapshot(old, "old")
    new_view, new_owned = _load_snapshot(new, "new")
    try:
        selected_groups = tuple(groups)
        _validate_groups(selected_groups, old_view, new_view)
        result = _compare_views(old_view, new_view, groups=selected_groups)
        if output_dir is not None:
            result.write(output_dir)
        return result
    finally:
        if old_owned:
            old_view.world.close()
        if new_owned:
            new_view.world.close()


def compare_spines(
    old: ConstructionWorld | Path | str,
    new: ConstructionWorld | Path | str,
    *,
    output_dir: Path | str | None = None,
    groups: Iterable[CorrespondenceGroup] = (),
) -> SpineComparisonResult:
    """Short alias for compare_program_spines."""

    return compare_program_spines(old, new, output_dir=output_dir, groups=groups)


def load_comparison(path: Path | str) -> SpineComparisonResult:
    """Load and validate one deterministic comparison sidecar."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ComparisonError("comparison sidecar must be an object")
    receipt = SpineComparisonReceipt.from_dict(payload["receipt"])
    claims = tuple(
        CorrespondenceClaim(
            old_entity=item.get("old_entity"),
            new_entity=item.get("new_entity"),
            continuity=str(item.get("continuity") or ""),
            outcome=str(item.get("outcome") or ""),
            basis_class=str(item.get("basis_class") or ""),
            evidence=tuple(_copy(entry) for entry in item.get("evidence") or []),
            changes=_copy(item.get("changes") or {}),
            candidate_entities=tuple(str(entry) for entry in item.get("candidate_entities") or []),
            group_id=item.get("group_id"),
            limitations=tuple(str(entry) for entry in item.get("limitations") or []),
        )
        for item in payload.get("correspondence_claims") or []
    )
    groups = tuple(
        CorrespondenceGroup(
            group_id=str(item.get("group_id") or ""),
            event=str(item.get("event") or ""),
            old_entities=tuple(str(entry) for entry in item.get("old_entities") or []),
            new_entities=tuple(str(entry) for entry in item.get("new_entities") or []),
            basis_class=str(item.get("basis_class") or ""),
            evidence=tuple(_copy(entry) for entry in item.get("evidence") or []),
        )
        for item in payload.get("correspondence_groups") or []
    )
    raw_delta = payload.get("program_delta") or {}
    delta = ProgramDelta(
        old_snapshot=str(raw_delta.get("old_snapshot") or ""),
        new_snapshot=str(raw_delta.get("new_snapshot") or ""),
        identity=_copy(raw_delta.get("identity") or {}),
        manifestations=tuple(_copy(item) for item in raw_delta.get("manifestations") or []),
        relations=_copy(raw_delta.get("relations") or {}),
        groups=groups,
        maintenance=tuple(_copy(item) for item in raw_delta.get("maintenance") or []),
    )
    result = SpineComparisonResult(receipt, claims, groups, delta)
    errors = result.validate()
    if errors:
        raise ComparisonError("comparison sidecar failed validation: " + "; ".join(errors))
    return result


__all__ = [
    "AUTOMATIC_BASIS_CLASS",
    "BASIS_CLASSES",
    "COMPARABLE_RELATIONS",
    "COMPARISON_MECHANISM_ID",
    "COMPARISON_MECHANISM_VERSION",
    "COMPARISON_RECEIPT_VERSION",
    "ComparisonError",
    "CorrespondenceClaim",
    "CorrespondenceGroup",
    "ProgramDelta",
    "SpineComparisonReceipt",
    "SpineComparisonResult",
    "compare_program_spines",
    "compare_spines",
    "load_comparison",
]

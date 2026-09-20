"""Small TypeScript -> native program-spine World vertical slice.

The TypeScript Compiler API adapter emits mechanical descriptors. This module
owns snapshot IDs, UTF-8 evidence coordinates, World projection, admission,
and candidate publication. It intentionally does not add a World primitive.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.commit import (
    _replace_candidate,
    discard_candidate,
    validate_contract_admission,
    write_sidecars,
)
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld
from ontology_author.evidence.program_source import PROGRAM_INPUTS_DIR
from .schemas import (
    CAPABILITY_VERSIONS,
    CAPABILITY_STATUS,
    CORE_SPEC_ID,
    CORE_SPEC_VERSION,
    RECEIPT_VERSION,
    SpineConstructionReceipt,
)


PROFILE_VERSION = "typescript-spine-v0"
EXTRACTOR_ID = "ontology_author.program_spine.typescript-compiler-api"
EXTRACTOR_VERSION = "v0"
WORLD_ID = "v0"
_NODE_ADAPTER = Path(__file__).with_name("typescript_extractor.js")
_RESOLUTION_STATUSES = {"RESOLVED", "MULTIPLE_CANDIDATES", "UNRESOLVED"}
_PROGRAM_RELATIONS = (
    "structural_context",
    "program_identity_descriptor",
    "program_imports",
    "program_invokes",
    "program_has_type",
    "program_extends",
    "program_implements",
)


@dataclass(frozen=True)
class TypeScriptBoundary:
    """User-declared TypeScript program boundary.

    Paths are accepted relative to ``workspace`` by the public builder and are
    normalized into the snapshot manifest. The user declares projects and
    roots; resulting program entities are always extractor output.
    """

    workspace_roots: tuple[str, ...]
    projects: tuple[str, ...]
    package_roots: tuple[str, ...] = ()
    include_tests: bool = False
    generated_files: str = "exclude"
    declarations: str = "in_scope_if_under_boundary"
    external_dependencies: str = "preserve_known_endpoints"

    def payload(self, workspace: Path) -> dict[str, Any]:
        def normalize(items: Iterable[str]) -> list[str]:
            return sorted(
                _relative_path((workspace / item).resolve() if not Path(item).is_absolute() else Path(item), workspace)
                for item in items
            )

        workspace_roots = normalize(self.workspace_roots)
        package_roots = normalize(self.package_roots or self.workspace_roots)
        projects = normalize(self.projects)
        if not projects:
            raise ValueError("at least one TypeScript tsconfig project is required")
        if not workspace_roots:
            raise ValueError("at least one workspace root is required")
        if self.generated_files not in {"exclude", "include"}:
            raise ValueError("generated_files must be 'exclude' or 'include'")
        return {
            "workspace_roots": workspace_roots,
            "projects": projects,
            "package_roots": package_roots,
            "include_tests": bool(self.include_tests),
            "generated_files": self.generated_files,
            "declarations": self.declarations,
            "external_dependencies": self.external_dependencies,
        }

    def node_payload(self, workspace: Path) -> dict[str, Any]:
        payload = self.payload(workspace)

        def absolute(items: Iterable[str]) -> list[str]:
            return [str((workspace / item).resolve()) for item in items]

        return {
            **payload,
            "workspace_roots": absolute(payload["workspace_roots"]),
            "projects": [{"tsconfig": str((workspace / item).resolve())} for item in payload["projects"]],
            "package_roots": absolute(payload["package_roots"]),
        }


@dataclass(frozen=True)
class TypeScriptSpineResult:
    succeeded: bool
    reason: str = ""
    errors: tuple[str, ...] = ()
    world_dir: Path | None = None
    snapshot_id: str = ""
    capabilities: Mapping[str, str] = field(default_factory=dict)


def _relative_path(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _id(snapshot_id: str, kind: str, descriptor: str) -> str:
    descriptor_hash = hashlib.sha256(descriptor.encode("utf-8")).hexdigest()[:24]
    return f"program:ts:{snapshot_id}:{kind}:{descriptor_hash}"


def _read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _write_program_input_blobs(
    world: ConstructionWorld,
    candidate: Path,
    effective_inputs: Sequence[Mapping[str, Any]],
) -> None:
    """Copy digest-addressed snapshot bytes for later bounded reconstruction.

    Assembly reads only these blobs. It must not reopen workspace paths.
    """

    by_digest = {
        str(item.get("contentDigest") or ""): item
        for item in effective_inputs
        if item.get("contentDigest")
    }
    needed: set[str] = set()
    for row in world.query("SELECT detail FROM _world_groundings WHERE kind='SOURCE'"):
        try:
            detail = json.loads(row.get("detail") or "{}")
        except json.JSONDecodeError:
            continue
        handle = str(detail.get("native_handle") or "")
        if "@sha256:" not in handle:
            continue
        digest = handle.rsplit("@sha256:", 1)[-1]
        if digest:
            needed.add(digest)
    if not needed:
        return
    directory = candidate / PROGRAM_INPUTS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    for digest in sorted(needed):
        record = by_digest.get(digest)
        if record is None:
            continue
        payload = _read_bytes(Path(str(record.get("path") or "")))
        if payload is None or hashlib.sha256(payload).hexdigest() != digest:
            continue
        (directory / digest).write_bytes(payload)


def _utf16_to_byte(text: str, position: int) -> int:
    units = 0
    byte_offset = 0
    if position < 0:
        raise ValueError("negative TypeScript source position")
    if position == 0:
        return 0
    for character in text:
        if units == position:
            return byte_offset
        width = 2 if ord(character) > 0xFFFF else 1
        if units < position < units + width:
            raise ValueError("TypeScript position splits a Unicode surrogate pair")
        units += width
        byte_offset += len(character.encode("utf-8"))
    if units == position:
        return byte_offset
    raise ValueError("TypeScript position lies outside the immutable source text")


def utf16_range_to_utf8(text: str, start: int, end: int) -> tuple[int, int]:
    """Convert a TypeScript UTF-16 half-open range to UTF-8 byte offsets."""

    start_byte = _utf16_to_byte(text, int(start))
    end_byte = _utf16_to_byte(text, int(end))
    if end_byte < start_byte:
        raise ValueError("source range end precedes start")
    return start_byte, end_byte


_BYTE_LOCATION = re.compile(r"^bytes:(\d+):(\d+)$")


def localize_source_range(
    world: ConstructionWorld,
    source_file: Path | str,
    start_byte: int,
    end_byte: int,
    *,
    workspace: Path | str | None = None,
) -> list[str]:
    """Return snapshot program entities whose grounded range contains a range.

    This is mechanical source localization only. It intentionally returns
    program identities and does not infer semantic or governance impact.
    """

    path = Path(source_file).resolve()
    acceptable_handles = {path.as_posix()}
    if workspace is not None:
        acceptable_handles.add(_relative_path(path, Path(workspace).resolve()))
    entity_ids = {
        str(row["entity"])
        for row in world.relation_rows("program_entity")
        if row.get("boundary") == "IN_SCOPE"
    }
    localized: set[str] = set()
    for row in world.query(
        "SELECT subject_id, detail FROM _world_groundings "
        "WHERE subject_type='REFERENT' AND kind='SOURCE'"
    ):
        subject = str(row["subject_id"])
        if subject not in entity_ids:
            continue
        try:
            detail = json.loads(row["detail"] or "{}")
        except json.JSONDecodeError:
            continue
        handle = str(detail.get("native_handle") or "")
        handle_path = handle.split("@sha256:", 1)[0]
        if handle_path not in acceptable_handles:
            continue
        match = _BYTE_LOCATION.match(str(detail.get("native_location") or ""))
        if not match:
            continue
        evidence_start, evidence_end = (int(match.group(1)), int(match.group(2)))
        if evidence_start <= start_byte and end_byte <= evidence_end:
            localized.add(subject)
    return sorted(localized)


def _observation(
    *,
    input_record: Mapping[str, Any],
    source_revision: str,
    byte_range: tuple[int, int] | None = None,
    provider: str = "typescript",
    location: str | None = None,
) -> SourceObservation:
    path = str(input_record["path"])
    digest = str(input_record.get("contentDigest") or "unreadable")
    if byte_range is not None:
        location = f"bytes:{byte_range[0]}:{byte_range[1]}"
    if not location:
        location = "input"
    return SourceObservation(
        provider=provider,
        native_handle=f"{_relative_path(Path(path), Path(input_record.get('workspace', path)))}@sha256:{digest}",
        source_revision=source_revision,
        native_location=location,
    )


def _grounding(
    observations: Iterable[SourceObservation],
    *,
    method: str,
    extra: Mapping[str, Any] | None = None,
) -> AssertionGrounding:
    return AssertionGrounding(
        observations=tuple(observations),
        construction_method=method,
        extra=dict(extra or {}),
    )


def _declare_relations(world: ConstructionWorld) -> None:
    def ref(name: str) -> Role:
        return Role(name, RoleType.REFERENT)

    def text(name: str) -> Role:
        return Role(name, RoleType.TEXT)

    schemas = {
        "program_snapshot": [
            ref("snapshot"), text("source_state"), text("boundary_digest"),
            text("inputs_digest"), text("configuration"), text("analyzer"),
            text("extractor"), text("core_contract"),
        ],
        "program_input": [ref("snapshot"), text("input_descriptor"), text("disposition"), text("content_digest"), text("input_role")],
        "program_entity": [ref("snapshot"), ref("entity"), text("kind"), text("boundary")],
        "program_entity_kind": [ref("snapshot"), ref("entity"), text("kind"), Role("synthetic", RoleType.BOOLEAN)],
        "program_identity_descriptor": [ref("snapshot"), ref("entity"), text("kind"), text("descriptor")],
        "structural_context": [ref("snapshot"), ref("parent"), ref("child")],
        "program_imports": [ref("snapshot"), ref("importer"), ref("imported")],
        "program_invokes": [ref("snapshot"), ref("call_site"), ref("target")],
        "program_has_type": [ref("snapshot"), ref("subject"), ref("type")],
        "program_extends": [ref("snapshot"), ref("subtype"), ref("supertype")],
        "program_implements": [ref("snapshot"), ref("implementer"), ref("interface")],
        "program_resolution": [
            ref("snapshot"), ref("subject"), text("capability"), text("status"),
            text("evidence_key"), text("details"),
        ],
        "program_resolution_candidate": [ref("snapshot"), ref("subject"), text("capability"), ref("candidate")],
        "program_capability": [
            ref("snapshot"), text("capability"), text("version"), text("status"), text("universe"),
            text("basis"), text("known_gaps"), text("result"),
        ],
    }
    descriptions = {
        "program_entity": "Explicit TypeScript snapshot universe membership.",
        "program_entity_kind": "The native identity surface and synthetic status of a program entity.",
        "program_identity_descriptor": "The deterministic snapshot-local identity descriptor used by the declared profile.",
        "structural_context": "Mechanical lexical/declaration context between program identities.",
        "program_imports": "A mechanically resolved module import occurrence.",
        "program_invokes": "A resolved call-site invocation target.",
        "program_has_type": "A mechanically established declared type relationship.",
        "program_extends": "A mechanically established type inheritance relationship.",
        "program_implements": "A mechanically established interface implementation relationship.",
        "program_resolution": "Program-spine resolution outcome.",
        "program_resolution_candidate": "Candidate target for a TypeScript resolution attempt.",
        "program_capability": "Capability-scoped extraction completeness record.",
    }
    for name, roles in schemas.items():
        world.declare_relation(name, roles, description=descriptions.get(name, "TypeScript program-spine relation."))


def _run_node(request: Mapping[str, Any]) -> dict[str, Any]:
    process = subprocess.run(
        ["node", str(_NODE_ADAPTER)],
        input=_canonical_json(request),
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        raise ConstructionError(process.stderr.strip() or "TypeScript extractor failed")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise ConstructionError("TypeScript extractor returned invalid JSON") from exc


def _effective_inputs(data: Mapping[str, Any], workspace: Path, boundary: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for raw in data.get("files", []):
        item = dict(raw)
        item["path"] = str(Path(str(item["path"])).resolve())
        item["workspace"] = str(workspace)
        item["input_role"] = "typescript_program_input"
        records[item["path"]] = item
    for raw in data.get("configurationInputs", []):
        item = dict(raw)
        item["path"] = str(Path(str(item["path"])).resolve())
        item["workspace"] = str(workspace)
        item["input_role"] = "tsconfig"
        records[item["path"]] = item
    for resolution in data.get("dependencyResolutions", []):
        package = resolution.get("package") or {}
        raw = package.get("packageJson")
        if not raw:
            continue
        item = dict(raw)
        item["path"] = str(Path(str(item["path"])).resolve())
        item["workspace"] = str(workspace)
        item["input_role"] = "package_metadata"
        records[item["path"]] = item
    for project in boundary["projects"]:
        path = (workspace / project).resolve()
        if str(path) not in records:
            payload = _read_bytes(path)
            records[str(path)] = {
                "path": str(path), "workspace": str(workspace), "disposition": "ANALYSIS_SUPPORT",
                "contentDigest": hashlib.sha256(payload).hexdigest() if payload is not None else None,
                "byteLength": len(payload) if payload is not None else None,
                "readable": payload is not None, "input_role": "tsconfig",
            }
    return [records[key] for key in sorted(records)]


def _normalize_workspace_value(value: Any, workspace: Path) -> Any:
    """Make manifest/configuration values independent of extraction paths."""

    if isinstance(value, Mapping):
        return {str(key): _normalize_workspace_value(item, workspace) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_workspace_value(item, workspace) for item in value]
    if isinstance(value, tuple):
        return [_normalize_workspace_value(item, workspace) for item in value]
    if not isinstance(value, str):
        return value
    raw = value.replace("\\", "/")
    root = str(workspace.resolve()).replace("\\", "/").rstrip("/")
    if raw == root:
        return "."
    prefix = root + "/"
    return raw.replace(prefix, "")


def _manifest_inputs(inputs: Sequence[Mapping[str, Any]], workspace: Path) -> list[dict[str, Any]]:
    fields = (
        "path",
        "disposition",
        "contentDigest",
        "byteLength",
        "readable",
        "input_role",
        "isDeclarationFile",
        "language",
        "project",
        "moduleKey",
        "analyzed",
    )
    return [
        {
            key: _normalize_workspace_value(item.get(key), workspace)
            for key in fields
            if key in item
        }
        for item in inputs
    ]


def _external_descriptor(descriptor: str, relation_name: str) -> tuple[str, str]:
    if descriptor.startswith("module|") or relation_name == "program_imports":
        return "module", "module"
    if relation_name in {"program_has_type", "program_extends", "program_implements"}:
        return "type", "type"
    return "callable", "callable"


def _project(
    world: ConstructionWorld,
    data: Mapping[str, Any],
    *,
    workspace: Path,
    boundary: Mapping[str, Any],
    snapshot_id: str,
    source_state: str,
    manifest: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    inputs = _effective_inputs(data, workspace, boundary)
    input_by_path = {str(Path(item["path"]).resolve()): item for item in inputs}
    descriptor_to_id: dict[str, str] = {}
    external_ids: dict[str, str] = {}

    snapshot_ref = _id(snapshot_id, "snapshot", "snapshot")
    config_observations = tuple(
        _observation(
            input_record=item,
            source_revision=source_state,
            provider="typescript-config" if item.get("input_role") == "tsconfig" else "typescript",
            location="input",
        )
        for item in inputs
        if item.get("input_role") == "tsconfig"
    )
    if not config_observations:
        raise ConstructionError("snapshot has no reconstructible tsconfig evidence")
    world.add_referent(snapshot_ref, label=f"TypeScript snapshot {snapshot_id}", observations=config_observations)
    world.assert_tuple(
        "program_snapshot",
        {
            "snapshot": snapshot_ref,
            "source_state": source_state,
            "boundary_digest": _digest(boundary),
            "inputs_digest": _digest(manifest["effective_inputs"]),
            "configuration": _digest(manifest["configuration"]),
            "analyzer": str(data.get("tool", {}).get("version", "unknown")),
            "extractor": f"{EXTRACTOR_ID}@{EXTRACTOR_VERSION}",
            "core_contract": f"{CORE_SPEC_ID}/{CORE_SPEC_VERSION}",
        },
        origin=ConstructionOrigin.MECHANICAL,
        grounding=_grounding(config_observations, method="typescript_snapshot_manifest", extra={"snapshot_id": snapshot_id}),
    )

    def ensure_external(descriptor: str, relation_name: str, evidence: Mapping[str, Any] | None) -> str:
        if descriptor in descriptor_to_id:
            return descriptor_to_id[descriptor]
        if descriptor in external_ids:
            return external_ids[descriptor]
        program_kind, native_kind = _external_descriptor(descriptor, relation_name)
        ref = _id(snapshot_id, "external", descriptor)
        observations: tuple[SourceObservation, ...] = ()
        if evidence is not None:
            observation, _ = _source_range_with_revision(evidence, input_by_path, source_state)
            observations = (observation,)
        if not observations:
            observations = config_observations[:1]
        world.add_referent(ref, label=f"External {native_kind}", observations=observations)
        world.assert_tuple(
            "program_entity",
            {"snapshot": snapshot_ref, "entity": ref, "kind": program_kind, "boundary": "EXTERNAL_BOUNDARY"},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_external_endpoint", extra={"descriptor": descriptor}),
        )
        world.assert_tuple(
            "program_entity_kind",
            {"snapshot": snapshot_ref, "entity": ref, "kind": native_kind, "synthetic": False},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_external_endpoint", extra={"descriptor": descriptor}),
        )
        world.assert_tuple(
            "program_identity_descriptor",
            {"snapshot": snapshot_ref, "entity": ref, "kind": native_kind, "descriptor": descriptor},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_identity_descriptor", extra={"descriptor": descriptor}),
        )
        external_ids[descriptor] = ref
        return ref

    elements = list(data.get("elements", []))
    for element in elements:
        descriptor = str(element["descriptor"])
        kind = str(element["identityKind"])
        native_kind = str(element["nativeKind"])
        ref = _id(snapshot_id, kind, descriptor)
        descriptor_to_id[descriptor] = ref

    for element in elements:
        descriptor = str(element["descriptor"])
        ref = descriptor_to_id[descriptor]
        kind = str(element["identityKind"])
        native_kind = str(element["nativeKind"])
        evidence_items = element.get("evidence") or []
        observations = tuple(
            _source_range_with_revision(item, input_by_path, source_state)[0]
            for item in evidence_items
        )
        if not observations:
            raise ConstructionError(f"program element has no source evidence: {descriptor}")
        world.add_referent(ref, label=str(element.get("name") or native_kind), observations=observations)
        world.assert_tuple(
            "program_entity",
            {"snapshot": snapshot_ref, "entity": ref, "kind": kind, "boundary": "IN_SCOPE"},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_program_entity", extra={"native_kind": native_kind, "synthetic": bool(element.get("synthetic"))}),
        )
        world.assert_tuple(
            "program_entity_kind",
            {"snapshot": snapshot_ref, "entity": ref, "kind": native_kind, "synthetic": bool(element.get("synthetic"))},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_program_entity_kind"),
        )
        world.assert_tuple(
            "program_identity_descriptor",
            {"snapshot": snapshot_ref, "entity": ref, "kind": native_kind, "descriptor": descriptor},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_identity_descriptor", extra={"descriptor": descriptor}),
        )

    for item in inputs:
        observation = _observation(input_record=item, source_revision=source_state, location="input")
        world.assert_tuple(
            "program_input",
            {
                "snapshot": snapshot_ref,
                "input_descriptor": _relative_path(Path(item["path"]), workspace),
                "disposition": str(item.get("disposition") or "ANALYSIS_SUPPORT"),
                "content_digest": str(item.get("contentDigest") or ""),
                "input_role": str(item.get("input_role") or "typescript_program_input"),
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding((observation,), method="typescript_effective_input_manifest"),
        )

    def endpoint(descriptor: str, relation_name: str, evidence: Mapping[str, Any] | None = None) -> str:
        if descriptor in descriptor_to_id:
            return descriptor_to_id[descriptor]
        return ensure_external(descriptor, relation_name, evidence)

    def assert_binary(relation: str, left: str, right: str, evidence: Mapping[str, Any], method: str, extra: Mapping[str, Any] | None = None) -> None:
        observation, _ = _source_range_with_revision(evidence, input_by_path, source_state)
        role_names = {
            "structural_context": ("parent", "child"),
            "program_imports": ("importer", "imported"),
            "program_invokes": ("call_site", "target"),
            "program_has_type": ("subject", "type"),
            "program_extends": ("subtype", "supertype"),
            "program_implements": ("implementer", "interface"),
        }
        left_role, right_role = role_names[relation]
        world.assert_tuple(
            relation,
            {"snapshot": snapshot_ref, left_role: endpoint(left, relation, evidence), right_role: endpoint(right, relation, evidence)},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding((observation,), method=method, extra=extra),
        )

    for item in data.get("ownership", []):
        owner = str(item["from"])
        child = str(item["to"])
        evidence = item.get("evidence")
        if evidence is None:
            raise ConstructionError("structural context lacks evidence")
        assert_binary("structural_context", owner, child, evidence, "typescript_structural_context")

    for item in data.get("imports", []):
        assert_binary("program_imports", str(item["from"]), str(item["to"]), item["evidence"], "typescript_program_imports", {"specifier": item.get("specifier")})

    for item in data.get("calls", []):
        assert_binary("program_invokes", str(item["from"]), str(item["to"]), item["evidence"], "typescript_program_invokes", {"kind": item.get("kind")})

    for item in data.get("typeRelations", []):
        relation = str(item["relationName"])
        if relation not in {"program_has_type", "program_extends", "program_implements"}:
            continue
        assert_binary(relation, str(item["from"]), str(item["to"]), item["evidence"], f"typescript_{relation}")

    for item in data.get("resolutions", []):
        status = str(item["status"])
        if status not in _RESOLUTION_STATUSES:
            raise ConstructionError(f"unknown TypeScript resolution status: {status}")
        evidence = item.get("evidence")
        if evidence is None:
            raise ConstructionError("TypeScript resolution lacks evidence")
        observation, byte_range = _source_range_with_revision(evidence, input_by_path, source_state)
        capability = str(item["capability"])
        resolution_relation = "program_invokes" if capability == "spine.calls/v1" else "program_imports"
        subject = endpoint(str(item["subject"]), resolution_relation, evidence)
        candidate_refs = [endpoint(str(candidate), resolution_relation, evidence) for candidate in item.get("candidates", [])]
        if status == "RESOLVED" and len(candidate_refs) != 1:
            raise ConstructionError("RESOLVED TypeScript resolution must have exactly one candidate")
        if status == "MULTIPLE_CANDIDATES" and len(candidate_refs) < 2:
            raise ConstructionError("MULTIPLE_CANDIDATES resolution needs at least two candidates")
        if status == "UNRESOLVED" and candidate_refs:
            raise ConstructionError("UNRESOLVED resolution cannot contain positive candidates")
        evidence_key = f"{_relative_path(Path(evidence['file']), workspace)}#bytes:{byte_range[0]}:{byte_range[1]}"
        world.assert_tuple(
            "program_resolution",
            {"snapshot": snapshot_ref, "subject": subject, "capability": capability, "status": status, "evidence_key": evidence_key, "details": _canonical_json(item.get("details") or {})},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding((observation,), method="typescript_resolution_outcome"),
        )
        for candidate in candidate_refs:
            world.assert_tuple(
                "program_resolution_candidate",
                {"snapshot": snapshot_ref, "subject": subject, "capability": capability, "candidate": candidate},
                origin=ConstructionOrigin.MECHANICAL,
                grounding=_grounding((observation,), method="typescript_resolution_candidate"),
            )

    capabilities = _capability_status(data, inputs)
    for capability, payload in capabilities.items():
        observation = config_observations[:1]
        capability_id, capability_version = capability.rsplit("/", 1)
        world.assert_tuple(
            "program_capability",
            {
                "snapshot": snapshot_ref,
                "capability": capability_id,
                "version": capability_version,
                "status": payload["status"],
                "universe": payload["universe"],
                "basis": payload["basis"],
                "known_gaps": _canonical_json(payload["known_gaps"]),
                "result": payload["result"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observation, method="typescript_capability_receipt", extra={"capability": capability}),
        )
    return descriptor_to_id, capabilities


def _source_range_with_revision(evidence: Mapping[str, Any], input_by_path: Mapping[str, Mapping[str, Any]], source_state: str) -> tuple[SourceObservation, tuple[int, int]]:
    path = str(Path(str(evidence["file"])).resolve())
    record = input_by_path.get(path)
    if record is None:
        raise ConstructionError(f"evidence file was not in effective input manifest: {path}")
    payload = _read_bytes(Path(path))
    if payload is None:
        raise ConstructionError(f"required evidence file is unreadable: {path}")
    text = payload.decode("utf-8")
    byte_range = utf16_range_to_utf8(text, int(evidence["start"]), int(evidence["end"]))
    observation = _observation(input_record=record, source_revision=source_state, byte_range=byte_range)
    return observation, byte_range


def _capability_status(data: Mapping[str, Any], inputs: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    diagnostics = list(data.get("configDiagnostics", [])) + list(data.get("programDiagnostics", []))
    errors = [item for item in diagnostics if int(item.get("category", 0)) == 1]
    unreadable = [item["path"] for item in inputs if not item.get("readable", True)]
    gaps = [f"TS{item.get('code')}: {item.get('message')}" for item in errors]
    if unreadable:
        gaps.extend(f"unreadable input: {path}" for path in unreadable)
    complete = not gaps
    statuses = {
        "spine.program_universe/v1": (complete, "declared TypeScript boundary and effective inputs; every emitted first-class identity", []),
        "spine.source_evidence/v1": (True, "every emitted identity and assertion was converted to an immutable UTF-8 byte range or manifest input", []),
        "spine.code_structure/v1": (complete, "recognized in-scope declarations and structural context from successfully analyzed inputs", gaps),
        "spine.imports/v1": (complete, "all recognized static import/export module specifiers received resolved or unresolved outcomes", gaps),
        "spine.calls/v1": (complete, "all recognized call sites received resolved, multiple-candidate, or unresolved outcomes", gaps),
        "spine.external_endpoints/v1": (complete, "all known external endpoints referenced by emitted relations were preserved as stubs", gaps),
        "spine.type_relations/v1": (complete, "all recognized declared type, extends, and implements relationships", gaps),
    }
    output: dict[str, dict[str, Any]] = {}
    for capability, (is_complete, basis, known_gaps) in statuses.items():
        version = capability.rsplit("/", 1)[1]
        output[capability] = {
            "version": version,
            "status": ("STATIC_COMPLETE" if capability == "spine.calls/v1" and is_complete else "COMPLETE" if is_complete else "INCOMPLETE"),
            "universe": {
                "spine.program_universe/v1": "declared_program_boundary",
                "spine.source_evidence/v1": "emitted_program_identities_and_assertions",
                "spine.code_structure/v1": "in_scope_source_inputs",
                "spine.imports/v1": "in_scope_static_module_occurrences",
                "spine.calls/v1": "in_scope_static_call_sites",
                "spine.external_endpoints/v1": "emitted_boundary_references",
                "spine.type_relations/v1": "in_scope_declared_type_relationships",
            }[capability],
            "basis": basis,
            "known_gaps": known_gaps,
            "result": _digest({"capability": capability, "elements": len(data.get("elements", [])), "relations": len(data.get("calls", [])) + len(data.get("imports", [])) + len(data.get("typeRelations", []))}),
        }
    return output


def _capability_assertion_refs(world: ConstructionWorld) -> dict[str, list[str]]:
    rows = world.query(
        "SELECT a.assertion_id, p.capability, p.version "
        "FROM _world_assertions a JOIN program_capability p "
        "ON p._assertion_id = a.assertion_id "
        "ORDER BY p.capability, p.version, a.assertion_id"
    )
    return {
        f"{row['capability']}/{row['version']}": [str(row["assertion_id"])]
        for row in rows
    }


def _labels(world: ConstructionWorld) -> dict[str, str]:
    return {
        str(row["id"]): str(row["label"])
        for row in world.query("SELECT id, label FROM _world_referents")
    }


def _receipt_for_world(
    world: ConstructionWorld,
    manifest: Mapping[str, Any],
    capability_payloads: Mapping[str, Mapping[str, Any]],
    *,
    snapshot_id: str,
    source_state: str,
) -> SpineConstructionReceipt:
    entities = world.relation_rows("program_entity")
    kinds = world.relation_rows("program_entity_kind")
    kind_counts: dict[str, int] = {}
    for row in kinds:
        kind = str(row["kind"])
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
    surfaces = tuple(
        {
            "kind": kind,
            "semantic_basis": "snapshot-local mechanically identified program surface",
            "emitted_count": count,
            "context_model": "structural_context",
        }
        for kind, count in sorted(kind_counts.items())
    )
    boundary_summary = {key: 0 for key in ("IN_SCOPE", "EXTERNAL_BOUNDARY", "ANALYSIS_SUPPORT")}
    for row in entities:
        boundary_summary[str(row["boundary"])] = boundary_summary.get(str(row["boundary"]), 0) + 1

    resolution_summary: dict[str, dict[str, int]] = {}
    for row in world.relation_rows("program_resolution"):
        capability = str(row["capability"])
        status = str(row["status"])
        resolution_summary.setdefault(capability, {})[status] = resolution_summary.setdefault(capability, {}).get(status, 0) + 1

    labels = _labels(world)
    examples: list[dict[str, Any]] = []
    invoke_rows = world.relation_rows("program_invokes")
    context_rows = world.relation_rows("structural_context")
    parent_by_child = {str(row["child"]): str(row["parent"]) for row in context_rows}
    resolutions = {
        str(row["subject"]): row
        for row in world.relation_rows("program_resolution")
        if row["capability"] == "spine.calls/v1"
    }
    if invoke_rows:
        invoke = invoke_rows[0]
        call_site = str(invoke["call_site"])
        chain: list[dict[str, str]] = []
        current = call_site
        while current:
            chain.append({"id": current, "label": labels.get(current, "")})
            current = parent_by_child.get(current, "")
        chain.reverse()
        examples.append(
            {
                "capability": "spine.calls/v1",
                "source_evidence": resolutions.get(call_site, {}).get("evidence_key", ""),
                "identity_chain": chain,
                "relation": {
                    "name": "program_invokes",
                    "call_site": call_site,
                    "target": str(invoke["target"]),
                    "target_label": labels.get(str(invoke["target"]), ""),
                },
            }
        )

    refs = _capability_assertion_refs(world)
    capability_records = []
    for capability, payload in sorted(capability_payloads.items()):
        capability_records.append(
            {
                "id": capability.rsplit("/", 1)[0],
                "version": capability.rsplit("/", 1)[1],
                "status": payload["status"],
                "scope": payload["universe"],
                "completeness_basis": payload["basis"],
                "completeness_receipt_refs": refs.get(capability, []),
                "known_gaps": list(payload["known_gaps"]),
            }
        )
    # These are explicit absence declarations for capabilities relevant to
    # common downstream purposes. They do not define those future semantics.
    capability_records.extend(
        {
            "id": capability,
            "version": "v1",
            "status": "NOT_PRODUCED",
            "scope": "no extraction performed",
            "completeness_basis": "capability was not claimed",
            "completeness_receipt_refs": [],
            "known_gaps": ["capability not produced by this extractor"],
        }
        for capability in ("spine.component_usage", "spine.routing", "spine.ui")
    )
    losses = (
        {
            "category": "COLLAPSES",
            "scope": "code_structure",
            "statement": "lexical blocks and ordinary expressions collapse into their containing program identity or source evidence",
            "consequence": "the spine does not expose arbitrary syntax nodes as attachment surfaces",
        },
        {
            "category": "DOES_NOT_REPRESENT",
            "scope": "frontend structure",
            "statement": "component instances, UI composition, and runtime-created routes are not represented",
            "consequence": "this construction is inadequate for instance-level UI attachment without a later capability",
        },
        {
            "category": "DOES_NOT_REPRESENT",
            "scope": "dynamic behavior",
            "statement": "external implementation bodies and reflection-derived runtime targets are not represented",
            "consequence": "some calls remain unresolved and no external implementation facts are implied",
        },
    )
    construction_id = _digest(
        {
            "snapshot_id": snapshot_id,
            "source_state": source_state,
            "capabilities": capability_records,
            "surfaces": surfaces,
        }
    )
    return SpineConstructionReceipt(
        receipt_version=RECEIPT_VERSION,
        construction_id=construction_id,
        conformance={"status": "PASS", "diagnostics": []},
        snapshot={
            "id": snapshot_id,
            "source_state": source_state,
            "declared_boundary": manifest["boundary"],
            "effective_inputs": manifest["effective_inputs"],
            "configuration": manifest["configuration"],
            "extractor": {"id": EXTRACTOR_ID, "version": EXTRACTOR_VERSION},
            "core_contract": {"id": CORE_SPEC_ID, "version": CORE_SPEC_VERSION},
            "capability_profiles": [
                {"id": item["id"], "version": item["version"]}
                for item in capability_records
            ],
        },
        capabilities=tuple(capability_records),
        identity_surfaces=surfaces,
        resolution_summary=resolution_summary,
        boundary_summary=boundary_summary,
        losses=losses,
        representative_examples=tuple(examples),
        comparison_readiness={
            "observations": [
                "snapshot-local descriptors are deterministic for identical immutable inputs",
                "structural context, declaration/occurrence evidence, and exact byte ranges are exposed for later comparison",
                "cross-snapshot lineage is deferred and no lineage adequacy claim is made",
            ]
        },
    )


def validate_typescript_spine(
    world: ConstructionWorld,
    manifest: Mapping[str, Any],
    receipt: SpineConstructionReceipt | None = None,
) -> list[str]:
    """Validate native TypeScript spine and receipt invariants."""

    errors: list[str] = []
    required_manifest = {
        "snapshot_id", "boundary", "effective_inputs", "configuration",
        "capabilities", "receipt",
    }
    errors.extend(f"manifest missing {key}" for key in sorted(required_manifest - set(manifest)))
    if not isinstance(manifest.get("effective_inputs"), list) or not manifest.get("effective_inputs"):
        errors.append("effective input manifest is missing or empty")
    snapshots = world.relation_rows("program_snapshot")
    recorded: dict[str, Mapping[str, Any]] = {}
    if len(snapshots) != 1:
        errors.append("program_snapshot must contain exactly one snapshot")
    else:
        snapshot = snapshots[0]["snapshot"]
        if snapshots[0].get("core_contract") != f"{CORE_SPEC_ID}/{CORE_SPEC_VERSION}":
            errors.append("program_snapshot has an invalid core contract identity")
        entity_rows = [row for row in world.relation_rows("program_entity") if row["snapshot"] == snapshot]
        entity_ids = {row["entity"] for row in entity_rows}
        if not entity_rows:
            errors.append("program universe has no explicit program_entity membership")
        allowed_boundaries = {"IN_SCOPE", "EXTERNAL_BOUNDARY"}
        if any(row["boundary"] not in allowed_boundaries for row in entity_rows):
            errors.append("program_entity contains an unsupported boundary classification")
        for row in world.relation_rows("program_entity_kind"):
            if row["snapshot"] == snapshot and row["entity"] not in entity_ids:
                errors.append(f"program entity kind is absent from program_entity: {row['entity']}")
        descriptors = [row for row in world.relation_rows("program_identity_descriptor") if row["snapshot"] == snapshot]
        descriptor_by_entity = {row["entity"]: row for row in descriptors}
        if len(descriptor_by_entity) != len(descriptors):
            errors.append("program identity descriptors are duplicated")
        for row in descriptors:
            if row["entity"] not in entity_ids:
                errors.append(f"program identity descriptor is absent from program_entity: {row['entity']}")
        for entity in sorted(entity_ids):
            if entity not in descriptor_by_entity:
                errors.append(f"program entity lacks identity descriptor: {entity}")
        kind_by_entity = {
            row["entity"]: row["kind"]
            for row in world.relation_rows("program_entity_kind")
            if row["snapshot"] == snapshot
        }
        for row in entity_rows:
            if row["entity"] in kind_by_entity and row["kind"] != kind_by_entity[row["entity"]]:
                errors.append(f"program entity kind disagrees with program_entity_kind: {row['entity']}")
        for row in descriptors:
            if row["entity"] in kind_by_entity and row["kind"] != kind_by_entity[row["entity"]]:
                errors.append(f"program identity descriptor kind disagrees with program_entity_kind: {row['entity']}")
        for relation in _PROGRAM_RELATIONS:
            schema = world.relation_schema(relation)
            ref_roles = [role["name"] for role in schema["roles"] if role["type"] == "REFERENT" and role["name"] != "snapshot"]
            for row in world.relation_rows(relation):
                if row.get("snapshot") != snapshot:
                    errors.append(f"{relation} row belongs to a different snapshot")
                for role in ref_roles:
                    if row.get(role) not in entity_ids:
                        errors.append(f"{relation} endpoint is not in program_entity: {row.get(role)}")
        for row in world.relation_rows("program_resolution"):
            if row["status"] not in _RESOLUTION_STATUSES:
                errors.append(f"invalid resolution status: {row['status']}")
            if row.get("subject") not in entity_ids:
                errors.append(f"resolution subject is not in program_entity: {row.get('subject')}")
        for row in world.relation_rows("program_resolution_candidate"):
            if row.get("subject") not in entity_ids or row.get("candidate") not in entity_ids:
                errors.append("resolution candidate endpoint is not in program_entity")
        resolution_by_subject = {
            row["subject"]: row for row in world.relation_rows("program_resolution")
            if row.get("capability") == "spine.calls/v1"
        }
        call_subjects = {row["call_site"] for row in world.relation_rows("program_invokes")}
        call_site_ids = {
            row["entity"] for row in world.relation_rows("program_entity_kind")
            if row.get("kind") == "call_site"
        }
        for call_site in sorted(call_site_ids):
            outcome = resolution_by_subject.get(call_site)
            if outcome is None:
                errors.append(f"call site lacks resolution outcome: {call_site}")
            elif outcome["status"] == "RESOLVED" and call_site not in call_subjects:
                errors.append(f"resolved call lacks program_invokes assertion: {call_site}")
            elif outcome["status"] != "RESOLVED" and call_site in call_subjects:
                errors.append(f"non-resolved call has program_invokes assertion: {call_site}")
        for entity in sorted(entity_ids):
            grounds = world.query(
                "SELECT 1 FROM _world_groundings WHERE subject_type='REFERENT' "
                "AND subject_id=? AND kind='SOURCE' LIMIT 1",
                (entity,),
            )
            if not grounds:
                errors.append(f"program entity lacks source evidence: {entity}")
        capability_rows = world.relation_rows("program_capability")
        if not capability_rows:
            errors.append("program capability records are missing")
        for row in capability_rows:
            if row["status"] not in CAPABILITY_STATUS:
                errors.append(f"invalid capability status: {row['status']}")
            if not str(row["version"] or "").strip() or not str(row["universe"] or "").strip():
                errors.append(f"capability record lacks version or scope: {row['capability']}")
        recorded = {f"{row['capability']}/{row['version']}": row for row in capability_rows}
        required = {"spine.program_universe/v1", "spine.source_evidence/v1", *CAPABILITY_VERSIONS}
        errors.extend(f"missing capability record: {name}" for name in sorted(required - set(recorded)))
        # The manifest is a compact status index. It may omit the receipt's
        # NOT_PRODUCED declarations, but every listed status must agree with
        # the authoritative World record.
        for key, status in (manifest.get("capabilities") or {}).items():
            if key in recorded and recorded[key]["status"] != status:
                errors.append(f"manifest capability status differs from World: {key}")
    contract_report = validate_contract_admission(world)
    if not contract_report.ok:
        errors.extend(f"{item.get('relation')}:{item.get('message')}" for item in contract_report.ungrounded)
    for row in world.query("SELECT assertion_id FROM _world_assertions"):
        groundings = world.query(
            "SELECT kind, reference FROM _world_groundings WHERE subject_type='ASSERTION' AND subject_id=?",
            (row["assertion_id"],),
        )
        if not any(item["kind"] == "SOURCE" for item in groundings):
            errors.append(f"assertion lacks source grounding: {row['assertion_id']}")
    if receipt is not None:
        errors.extend(receipt.validate(manifest))
        receipt_meta = manifest.get("receipt")
        if not isinstance(receipt_meta, Mapping):
            errors.append("manifest receipt reference is missing")
        else:
            if receipt_meta.get("construction_id") != receipt.construction_id:
                errors.append("manifest receipt construction ID differs from receipt")
            if not str(receipt_meta.get("path") or "").strip():
                errors.append("manifest receipt path is missing")
            if not str(receipt_meta.get("sha256") or "").strip():
                errors.append("manifest receipt digest is missing")
        references = _capability_assertion_refs(world)
        for item in receipt.capabilities:
            key = f"{item.get('id')}/{item.get('version')}"
            if item.get("status") == "NOT_PRODUCED":
                continue
            world_row = recorded.get(key)
            if world_row is None:
                errors.append(f"receipt capability has no World completeness record: {key}")
                continue
            if item.get("status") != world_row.get("status"):
                errors.append(f"receipt broadens or changes capability status: {key}")
            if item.get("scope") != world_row.get("universe"):
                errors.append(f"receipt broadens capability scope: {key}")
            if item.get("completeness_basis") != world_row.get("basis"):
                errors.append(f"receipt changes capability basis: {key}")
            if sorted(item.get("completeness_receipt_refs") or []) != sorted(references.get(key, [])):
                errors.append(f"receipt completeness references do not match World: {key}")
    return sorted(set(errors))


def build_typescript_spine(
    workspace: Path | str,
    world_dir: Path | str,
    *,
    boundary: TypeScriptBoundary,
) -> TypeScriptSpineResult:
    """Extract, validate, receipt, and publish one TypeScript spine World."""

    workspace_path = Path(workspace).resolve()
    output = Path(world_dir).resolve()
    candidate = output.with_name(output.name + ".candidate")
    try:
        boundary_payload = boundary.payload(workspace_path)
        request = {
            "workspace": str(workspace_path),
            "boundary": boundary.node_payload(workspace_path),
            "profile_version": PROFILE_VERSION,
            "core_contract": f"{CORE_SPEC_ID}/{CORE_SPEC_VERSION}",
            "capability_profiles": sorted(CAPABILITY_VERSIONS),
        }
        data = _run_node(request)
        effective_inputs = _effective_inputs(data, workspace_path, boundary_payload)
        config = {
            "projects": boundary_payload["projects"],
            "compiler_options": data.get("compilerOptions", {}),
            "configuration_inputs": data.get("configurationInputs", []),
            "dependency_resolutions": data.get("dependencyResolutions", []),
            "tool": data.get("tool", {}),
            "config_diagnostics": data.get("configDiagnostics", []),
            "program_diagnostics": data.get("programDiagnostics", []),
        }
        input_manifest = _manifest_inputs(effective_inputs, workspace_path)
        normalized_config = _normalize_workspace_value(config, workspace_path)
        source_state = _digest({"inputs": input_manifest, "configuration": normalized_config, "boundary": boundary_payload})
        snapshot_id = _digest({"source_state": source_state, "boundary": boundary_payload, "configuration": normalized_config, "tool": data.get("tool", {}), "profile": PROFILE_VERSION, "core_contract": CORE_SPEC_VERSION, "capabilities": sorted(CAPABILITY_VERSIONS)})[:32]
        manifest = {
            "snapshot_id": snapshot_id,
            "source_state": source_state,
            "boundary": boundary_payload,
            "effective_inputs": input_manifest,
            "configuration": normalized_config,
            "capabilities": {},
            "receipt": {},
        }
        candidate.parent.mkdir(parents=True, exist_ok=True)
        discard_candidate(candidate)
        candidate.mkdir(parents=True)
        world = ConstructionWorld.create(candidate / "world.sqlite", world_id=WORLD_ID)
        try:
            _declare_relations(world)
            _, capability_payloads = _project(
                world, data, workspace=workspace_path, boundary=boundary_payload,
                snapshot_id=snapshot_id, source_state=source_state, manifest=manifest,
            )
            capability_status = {
                key: payload["status"]
                for key, payload in capability_payloads.items()
            }
            manifest["capabilities"] = capability_status
            (candidate / "typescript.manifest.json").write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
            write_sidecars(world)
            _write_program_input_blobs(world, candidate, effective_inputs)
            receipt = _receipt_for_world(
                world,
                manifest,
                capability_payloads,
                snapshot_id=snapshot_id,
                source_state=source_state,
            )
            receipt_path = candidate / "spine.construction.receipt.json"
            receipt.write(receipt_path)
            manifest["receipt"] = {
                "path": receipt_path.name,
                "construction_id": receipt.construction_id,
                "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            }
            (candidate / "typescript.manifest.json").write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
            errors = validate_typescript_spine(world, manifest, receipt)
            if errors:
                world.close()
                discard_candidate(candidate)
                return TypeScriptSpineResult(False, "typescript_admission", tuple(errors), snapshot_id=snapshot_id, capabilities=capability_status)
            world.close()
            _replace_candidate(candidate, output)
            return TypeScriptSpineResult(True, world_dir=output, snapshot_id=snapshot_id, capabilities=capability_status)
        except Exception:
            world.close()
            discard_candidate(candidate)
            raise
    except Exception as exc:
        discard_candidate(candidate)
        return TypeScriptSpineResult(False, "typescript_extraction", (f"{type(exc).__name__}: {exc}",))


__all__ = [
    "TypeScriptBoundary",
    "TypeScriptSpineResult",
    "build_typescript_spine",
    "validate_typescript_spine",
    "utf16_range_to_utf8",
    "localize_source_range",
]

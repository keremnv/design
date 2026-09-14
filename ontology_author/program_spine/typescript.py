"""Small TypeScript -> KDM-profile World vertical slice.

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
from typing import Any, Iterable, Mapping

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


PROFILE_VERSION = "typescript-kdm-v0"
KDM_PROFILE_VERSION = "kdm-1.4-profile-v0"
WORLD_ID = "v0"
_NODE_ADAPTER = Path(__file__).with_name("typescript_extractor.js")
_RESOLUTION_STATUSES = {"RESOLVED", "MULTIPLE_CANDIDATES", "UNRESOLVED"}


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
            text("inputs_digest"), text("configuration"), text("typescript"),
            text("extractor"), text("profile"),
        ],
        "program_input": [ref("snapshot"), text("input_descriptor"), text("disposition"), text("content_digest"), text("input_role")],
        "program_entity": [ref("snapshot"), ref("entity"), text("kind"), text("boundary")],
        "kdm_element_type": [ref("snapshot"), ref("entity"), text("metaclass")],
        "kdm_ownership": [ref("snapshot"), ref("owner"), ref("owned_element")],
        "kdm_imports": [ref("snapshot"), ref("from"), ref("to")],
        "kdm_calls": [ref("snapshot"), ref("from"), ref("to")],
        "kdm_has_type": [ref("snapshot"), ref("from"), ref("to")],
        "kdm_extends": [ref("snapshot"), ref("from"), ref("to")],
        "kdm_implements": [ref("snapshot"), ref("from"), ref("to")],
        "typescript_resolution": [
            ref("snapshot"), ref("subject"), text("relation_name"), text("status"),
            text("evidence_key"), text("details"),
        ],
        "typescript_resolution_candidate": [ref("snapshot"), ref("subject"), text("relation_name"), ref("candidate")],
        "program_capability": [
            ref("snapshot"), text("capability"), text("status"), text("universe"),
            text("basis"), text("known_gaps"), text("result"),
        ],
    }
    descriptions = {
        "program_entity": "Explicit TypeScript snapshot universe membership.",
        "kdm_element_type": "KDM metaclass of a snapshot program element.",
        "kdm_ownership": "KDM owner/ownedElement structural ownership.",
        "kdm_imports": "KDM code::Imports.",
        "kdm_calls": "KDM action::Calls from ActionElement to CodeItem.",
        "kdm_has_type": "KDM code::HasType.",
        "kdm_extends": "KDM code::Extends.",
        "kdm_implements": "KDM code::Implements.",
        "typescript_resolution": "TypeScript profile resolution outcome.",
        "typescript_resolution_candidate": "Candidate target for a TypeScript resolution attempt.",
        "program_capability": "Capability-scoped TypeScript extraction completeness receipt.",
    }
    for name, roles in schemas.items():
        world.declare_relation(name, roles, description=descriptions.get(name, "TypeScript KDM profile relation."))


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


def _external_descriptor(descriptor: str, relation_name: str) -> tuple[str, str, str]:
    if descriptor.startswith("module|") or relation_name == "kdm_imports":
        return descriptor, "module", "Module"
    if relation_name in {"kdm_has_type", "kdm_extends", "kdm_implements"}:
        return descriptor, "type", "Datatype"
    return descriptor, "function", "CallableUnit"


def _project(
    world: ConstructionWorld,
    data: Mapping[str, Any],
    *,
    workspace: Path,
    boundary: Mapping[str, Any],
    snapshot_id: str,
    source_state: str,
    manifest: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
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
            "typescript": str(data.get("tool", {}).get("version", "unknown")),
            "extractor": "ontology_author.program_spine.typescript-compiler-api",
            "profile": f"{PROFILE_VERSION};{KDM_PROFILE_VERSION}",
        },
        origin=ConstructionOrigin.MECHANICAL,
        grounding=_grounding(config_observations, method="typescript_snapshot_manifest", extra={"snapshot_id": snapshot_id}),
    )

    def ensure_external(descriptor: str, relation_name: str, evidence: Mapping[str, Any] | None) -> str:
        if descriptor in descriptor_to_id:
            return descriptor_to_id[descriptor]
        if descriptor in external_ids:
            return external_ids[descriptor]
        _, program_kind, kdm_kind = _external_descriptor(descriptor, relation_name)
        ref = _id(snapshot_id, "external", descriptor)
        observations: tuple[SourceObservation, ...] = ()
        if evidence is not None:
            observation, _ = _source_range_with_revision(evidence, input_by_path, source_state)
            observations = (observation,)
        if not observations:
            observations = config_observations[:1]
        world.add_referent(ref, label=f"External {kdm_kind}", observations=observations)
        world.assert_tuple(
            "program_entity",
            {"snapshot": snapshot_ref, "entity": ref, "kind": program_kind, "boundary": "EXTERNAL_BOUNDARY"},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_external_endpoint", extra={"descriptor": descriptor}),
        )
        world.assert_tuple(
            "kdm_element_type",
            {"snapshot": snapshot_ref, "entity": ref, "metaclass": kdm_kind},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_external_endpoint", extra={"descriptor": descriptor}),
        )
        external_ids[descriptor] = ref
        return ref

    elements = list(data.get("elements", []))
    for element in elements:
        descriptor = str(element["descriptor"])
        kind = str(element["programKind"])
        kdm_kind = str(element["kdmKind"])
        ref = _id(snapshot_id, kind, descriptor)
        descriptor_to_id[descriptor] = ref

    for element in elements:
        descriptor = str(element["descriptor"])
        ref = descriptor_to_id[descriptor]
        evidence_items = element.get("evidence") or []
        observations = tuple(
            _source_range_with_revision(item, input_by_path, source_state)[0]
            for item in evidence_items
        )
        if not observations:
            raise ConstructionError(f"program element has no source evidence: {descriptor}")
        world.add_referent(ref, label=str(element.get("name") or element["kdmKind"]), observations=observations)
        world.assert_tuple(
            "program_entity",
            {"snapshot": snapshot_ref, "entity": ref, "kind": str(element["programKind"]), "boundary": "IN_SCOPE"},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_program_entity", extra={"kdm_metaclass": element["kdmKind"], "synthetic": bool(element.get("synthetic"))}),
        )
        world.assert_tuple(
            "kdm_element_type",
            {"snapshot": snapshot_ref, "entity": ref, "metaclass": str(element["kdmKind"])},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observations, method="typescript_kdm_element_type"),
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
        world.assert_tuple(
            relation,
            {"snapshot": snapshot_ref, "from" if relation != "kdm_ownership" else "owner": endpoint(left, relation, evidence), "to" if relation != "kdm_ownership" else "owned_element": endpoint(right, relation, evidence)},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding((observation,), method=method, extra=extra),
        )

    for item in data.get("ownership", []):
        owner = str(item["from"])
        child = str(item["to"])
        evidence = item.get("evidence")
        if evidence is None:
            raise ConstructionError("KDM ownership lacks evidence")
        assert_binary("kdm_ownership", owner, child, evidence, "typescript_kdm_ownership")

    for item in data.get("imports", []):
        assert_binary("kdm_imports", str(item["from"]), str(item["to"]), item["evidence"], "typescript_kdm_imports", {"specifier": item.get("specifier")})

    for item in data.get("calls", []):
        assert_binary("kdm_calls", str(item["from"]), str(item["to"]), item["evidence"], "typescript_kdm_calls", {"kind": item.get("kind")})

    for item in data.get("typeRelations", []):
        relation = str(item["relationName"])
        if relation not in {"kdm_has_type", "kdm_extends", "kdm_implements"}:
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
        subject = endpoint(str(item["subject"]), str(item["relationName"]), evidence)
        candidate_refs = [endpoint(str(candidate), str(item["relationName"]), evidence) for candidate in item.get("candidates", [])]
        if status == "RESOLVED" and len(candidate_refs) != 1:
            raise ConstructionError("RESOLVED TypeScript resolution must have exactly one candidate")
        if status == "MULTIPLE_CANDIDATES" and len(candidate_refs) < 2:
            raise ConstructionError("MULTIPLE_CANDIDATES resolution needs at least two candidates")
        if status == "UNRESOLVED" and candidate_refs:
            raise ConstructionError("UNRESOLVED resolution cannot contain positive candidates")
        evidence_key = f"{_relative_path(Path(evidence['file']), workspace)}#bytes:{byte_range[0]}:{byte_range[1]}"
        world.assert_tuple(
            "typescript_resolution",
            {"snapshot": snapshot_ref, "subject": subject, "relation_name": str(item["relationName"]), "status": status, "evidence_key": evidence_key, "details": _canonical_json(item.get("details") or {})},
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding((observation,), method="typescript_resolution_outcome"),
        )
        for candidate in candidate_refs:
            world.assert_tuple(
                "typescript_resolution_candidate",
                {"snapshot": snapshot_ref, "subject": subject, "relation_name": str(item["relationName"]), "candidate": candidate},
                origin=ConstructionOrigin.MECHANICAL,
                grounding=_grounding((observation,), method="typescript_resolution_candidate"),
            )

    capabilities = _capability_status(data, inputs)
    for capability, payload in capabilities.items():
        observation = config_observations[:1]
        world.assert_tuple(
            "program_capability",
            {
                "snapshot": snapshot_ref,
                "capability": capability,
                "status": payload["status"],
                "universe": payload["universe"],
                "basis": payload["basis"],
                "known_gaps": _canonical_json(payload["known_gaps"]),
                "result": payload["result"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=_grounding(observation, method="typescript_capability_receipt", extra={"capability": capability}),
        )
    return descriptor_to_id, {key: value["status"] for key, value in capabilities.items()}


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
        "program_universe": (complete, "declared TypeScript boundary and effective inputs; all emitted first-class identities", []),
        "source_evidence": (True, "every emitted identity/assertion was converted to an immutable UTF-8 byte range or manifest input", []),
        "code_structure": (complete, "recognized in-scope declarations and KDM ownership from successfully analyzed inputs", gaps),
        "imports": (complete, "all recognized static import/export module specifiers received resolved or unresolved outcomes", gaps),
        "calls": (complete, "all recognized CallExpression/NewExpression sites received resolved, multiple-candidate, or unresolved outcomes", gaps),
        "external_endpoints": (complete, "all known external endpoints referenced by emitted KDM relations were preserved as stubs", gaps),
    }
    output: dict[str, dict[str, Any]] = {}
    for capability, (is_complete, basis, known_gaps) in statuses.items():
        output[capability] = {
            "status": "COMPLETE" if is_complete else "INCOMPLETE",
            "universe": "program_entity",
            "basis": basis,
            "known_gaps": known_gaps,
            "result": _digest({"capability": capability, "elements": len(data.get("elements", [])), "relations": len(data.get("calls", [])) + len(data.get("imports", []))}),
        }
    return output


def validate_typescript_spine(world: ConstructionWorld, manifest: Mapping[str, Any]) -> list[str]:
    """Validate TypeScript profile invariants without changing the kernel."""

    errors: list[str] = []
    required_manifest = {"snapshot_id", "boundary", "effective_inputs", "configuration", "capabilities"}
    errors.extend(f"manifest missing {key}" for key in sorted(required_manifest - set(manifest)))
    if not isinstance(manifest.get("effective_inputs"), list) or not manifest.get("effective_inputs"):
        errors.append("effective input manifest is missing or empty")
    snapshots = world.relation_rows("program_snapshot")
    if len(snapshots) != 1:
        errors.append("program_snapshot must contain exactly one snapshot")
    else:
        snapshot = snapshots[0]["snapshot"]
        entity_rows = [row for row in world.relation_rows("program_entity") if row["snapshot"] == snapshot]
        entity_ids = {row["entity"] for row in entity_rows}
        if not entity_rows:
            errors.append("program universe has no explicit program_entity membership")
        in_scope_ids = {row["entity"] for row in entity_rows if row["boundary"] == "IN_SCOPE"}
        external_ids = {row["entity"] for row in entity_rows if row["boundary"] == "EXTERNAL_BOUNDARY"}
        if len(in_scope_ids) + len(external_ids) != len(entity_ids):
            errors.append("program_entity contains an unsupported boundary classification")
        for row in world.relation_rows("kdm_element_type"):
            if row["snapshot"] == snapshot and row["entity"] not in entity_ids:
                errors.append(f"KDM element is absent from program_entity: {row['entity']}")
        for relation in ("kdm_ownership", "kdm_imports", "kdm_calls", "kdm_has_type", "kdm_extends", "kdm_implements"):
            for row in world.relation_rows(relation):
                if row.get("snapshot") != snapshot:
                    errors.append(f"{relation} row belongs to a different snapshot")
                for key, value in row.items():
                    if key in {"_assertion_id", "snapshot"} or not key in {"from", "to", "owner", "owned_element"}:
                        continue
                    if value not in entity_ids:
                        errors.append(f"{relation} endpoint is not in program_entity: {value}")
        for row in world.relation_rows("typescript_resolution"):
            if row["status"] not in _RESOLUTION_STATUSES:
                errors.append(f"invalid resolution status: {row['status']}")
            if row.get("subject") not in entity_ids:
                errors.append(f"resolution subject is not in program_entity: {row.get('subject')}")
        for row in world.relation_rows("typescript_resolution_candidate"):
            if row.get("subject") not in entity_ids or row.get("candidate") not in entity_ids:
                errors.append("resolution candidate endpoint is not in program_entity")
        resolution_by_subject = {
            row["subject"]: row for row in world.relation_rows("typescript_resolution")
            if row.get("relation_name") == "kdm_calls"
        }
        call_subjects = {row["from"] for row in world.relation_rows("kdm_calls")}
        action_ids = {
            row["entity"] for row in world.relation_rows("kdm_element_type")
            if row.get("metaclass") == "ActionElement"
        }
        for action in sorted(action_ids):
            outcome = resolution_by_subject.get(action)
            if outcome is None:
                errors.append(f"call ActionElement lacks resolution outcome: {action}")
            elif outcome["status"] == "RESOLVED" and action not in call_subjects:
                errors.append(f"resolved call lacks kdm_calls assertion: {action}")
            elif outcome["status"] != "RESOLVED" and action in call_subjects:
                errors.append(f"non-resolved call has kdm_calls assertion: {action}")
        for entity in sorted(entity_ids):
            grounds = world.query(
                "SELECT 1 FROM _world_groundings WHERE subject_type='REFERENT' "
                "AND subject_id=? AND kind='SOURCE' LIMIT 1",
                (entity,),
            )
            if not grounds:
                errors.append(f"program entity lacks source evidence: {entity}")
        for row in world.relation_rows("program_capability"):
            if row["status"] not in {"COMPLETE", "INCOMPLETE", "UNKNOWN"}:
                errors.append(f"invalid capability status: {row['status']}")
            if row["universe"] != "program_entity":
                errors.append(f"capability has unsupported universe: {row['universe']}")
        required_capabilities = {"program_universe", "source_evidence", "code_structure", "imports", "calls", "external_endpoints"}
        recorded_capabilities = {row["capability"] for row in world.relation_rows("program_capability") if row.get("snapshot") == snapshot}
        errors.extend(f"missing capability receipt: {name}" for name in sorted(required_capabilities - recorded_capabilities))
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
    return sorted(set(errors))


def build_typescript_spine(
    workspace: Path | str,
    world_dir: Path | str,
    *,
    boundary: TypeScriptBoundary,
) -> TypeScriptSpineResult:
    """Extract, validate, and publish one TypeScript KDM-profile World."""

    workspace_path = Path(workspace).resolve()
    output = Path(world_dir).resolve()
    candidate = output.with_name(output.name + ".candidate")
    try:
        boundary_payload = boundary.payload(workspace_path)
        request = {
            "workspace": str(workspace_path),
            "boundary": boundary.node_payload(workspace_path),
            "profile_version": PROFILE_VERSION,
            "kdm_profile_version": KDM_PROFILE_VERSION,
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
        input_manifest = [
            {
                key: item.get(key)
                for key in ("path", "disposition", "contentDigest", "byteLength", "readable", "input_role", "isDeclarationFile", "language", "project", "moduleKey", "analyzed")
                if key in item
            }
            for item in effective_inputs
        ]
        source_state = _digest({"inputs": input_manifest, "configuration": config, "boundary": boundary_payload})
        snapshot_id = _digest({"source_state": source_state, "boundary": boundary_payload, "configuration": config, "tool": data.get("tool", {}), "profile": PROFILE_VERSION, "kdm": KDM_PROFILE_VERSION})[:32]
        manifest = {
            "snapshot_id": snapshot_id,
            "source_state": source_state,
            "boundary": boundary_payload,
            "effective_inputs": input_manifest,
            "configuration": config,
            "capabilities": {},
        }
        candidate.parent.mkdir(parents=True, exist_ok=True)
        discard_candidate(candidate)
        candidate.mkdir(parents=True)
        world = ConstructionWorld.create(candidate / "world.sqlite", world_id=WORLD_ID)
        try:
            _declare_relations(world)
            _, capability_status = _project(
                world, data, workspace=workspace_path, boundary=boundary_payload,
                snapshot_id=snapshot_id, source_state=source_state, manifest=manifest,
            )
            manifest["capabilities"] = capability_status
            (candidate / "typescript.manifest.json").write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
            write_sidecars(world)
            errors = validate_typescript_spine(world, manifest)
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

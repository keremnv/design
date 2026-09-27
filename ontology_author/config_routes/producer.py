"""Hardened mechanical producer for a JSON route document.

This is the production producer for ``config.routes/v1``. It reads the
software source exactly once, validates a bounded JSON form, rejects
duplicate route IDs, and locates each route record span with flexible
whitespace handling.

Supported software source form (refuse everything else):

- existing regular file, UTF-8 JSON bytes
- top-level object with a non-empty ``routes`` list
- each route is an object with non-empty string ``id``/``path``/``handler``
- route IDs are unique within the document
- each record's source span must uniquely enclose its ``"id"`` match;
  layouts the bounded locator cannot enclose (for example a nested
  object before the ``"id"`` key, or ``\\uXXXX``-escaped non-ASCII IDs)
  are refused rather than mis-grounded

The producer does not interpret governance prose and does not emit
Program Spine relations. Extra route fields are preserved in the
canonical manifestation but are not interpreted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld

CAPABILITY = "config.routes"
VERSION = "v1"
KIND = "config:route"
SCHEME = "canonical-json-record"


@dataclass(frozen=True)
class ProducedRoute:
    subject_id: str
    route_id: str
    path: str
    handler: str
    location: str
    document_observation: SourceObservation
    manifestation_observation: SourceObservation


@dataclass(frozen=True)
class ProducedRoutes:
    snapshot_id: str
    routes: tuple[ProducedRoute, ...]
    blobs: dict[str, bytes]
    consumed_revision: str
    document_name: str


class ExpectedRevisionMismatch(ValueError):
    """Consumed software revision differs from the caller's expectation."""

    def __init__(self, *, expected: str, consumed: str) -> None:
        super().__init__(
            f"expected software revision {expected} but consumed {consumed}"
        )
        self.expected = expected
        self.consumed = consumed


def normalize_revision(value: str) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("sha256:"):
        text = text[len("sha256:") :]
    if len(text) != 64 or any(c not in "0123456789abcdef" for c in text):
        raise ConstructionError(f"expected revision is not a sha256 digest: {value!r}")
    return text


def produce_routes(
    world_dir: Path,
    document: Path,
    *,
    expected_revision: str | None = None,
) -> ProducedRoutes:
    """Acquire ``document`` once and produce a mechanical route World.

    When ``expected_revision`` is supplied (hex or ``sha256:``-prefixed),
    it is compared to the revision actually consumed by this call's single
    read. A mismatch raises :class:`ExpectedRevisionMismatch` before any
    World is written.
    """
    target = Path(document)
    if not target.is_file():
        raise ConstructionError(
            f"unsupported software source form: not a regular file: {target}"
        )
    payload = target.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_revision is not None:
        expected = normalize_revision(expected_revision)
        if digest != expected:
            raise ExpectedRevisionMismatch(expected=expected, consumed=digest)
    try:
        parsed = json.loads(payload)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ConstructionError(
            f"unsupported software JSON form: invalid JSON in {target.name}: {exc}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ConstructionError(
            f"unsupported software JSON form: top-level value in {target.name} "
            "is not an object"
        )
    routes = parsed.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ConstructionError(
            f"unsupported software JSON form: {target.name} does not contain "
            "a non-empty route list"
        )
    validated = _validated_routes(target.name, routes)
    snapshot_id = f"snapshot:{digest[:32]}"
    document_name = target.name
    blobs: dict[str, bytes] = {digest: payload}
    produced: list[ProducedRoute] = []
    world_path = Path(world_dir)
    world_path.mkdir(parents=True, exist_ok=True)
    world = ConstructionWorld.create(world_path / "world.sqlite", world_id="config-routes")
    try:
        _declare(world)
        world.add_referent(snapshot_id, label=document_name)
        for index, route in enumerate(validated):
            route_id = route["id"]
            start, end = _object_span(payload, route_id)
            subject_id = f"route:{digest[:16]}:{route_id}"
            canonical = _canonical(route)
            canonical_digest = hashlib.sha256(canonical).hexdigest()
            blobs[canonical_digest] = canonical
            item = ProducedRoute(
                subject_id=subject_id,
                route_id=route_id,
                path=route["path"],
                handler=route["handler"],
                location=f"/routes/{index}",
                document_observation=SourceObservation(
                    provider="json",
                    native_handle=f"{document_name}@sha256:{digest}",
                    source_revision=f"sha256:{digest}",
                    native_location=f"bytes:{start}:{end}",
                ),
                manifestation_observation=SourceObservation(
                    provider="json",
                    native_handle=f"route:{route_id}@sha256:{canonical_digest}",
                    source_revision=f"sha256:{canonical_digest}",
                    native_location=f"bytes:0:{len(canonical)}",
                ),
            )
            produced.append(item)
            world.add_referent(subject_id, label=route_id)
            grounding = AssertionGrounding(
                (item.document_observation,),
                construction_method="json route record",
            )
            world.assert_tuple(
                "config_member",
                {"snapshot": snapshot_id, "route": subject_id},
                origin=ConstructionOrigin.MECHANICAL,
                grounding=grounding,
            )
            world.assert_tuple(
                "config_route",
                {
                    "subject": subject_id,
                    "record_id": item.route_id,
                    "path": item.path,
                    "handler": item.handler,
                },
                origin=ConstructionOrigin.MECHANICAL,
                grounding=grounding,
            )
    except BaseException:
        world.close()
        raise
    else:
        world.close()
    result = ProducedRoutes(
        snapshot_id=snapshot_id,
        routes=tuple(produced),
        blobs=blobs,
        consumed_revision=digest,
        document_name=document_name,
    )
    _check_producer_inventory(world_path, result)
    return result


def _validated_routes(document_name: str, routes: list) -> list[dict[str, str]]:
    validated: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, route in enumerate(routes):
        location = f"/routes/{index}"
        if not isinstance(route, dict):
            raise ConstructionError(
                f"unsupported route record at {location} in {document_name}: "
                "not an object"
            )
        values: dict[str, str] = {}
        for field in ("id", "path", "handler"):
            value = route.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ConstructionError(
                    f"unsupported route record at {location} in {document_name}: "
                    f"field {field!r} is not a non-empty string"
                )
            values[field] = value
        if values["id"] in seen:
            raise ConstructionError(
                f"duplicate route id {values['id']!r} in {document_name}"
            )
        seen.add(values["id"])
        merged = dict(route)
        merged.update(values)
        validated.append(merged)
    return validated


def _declare(world: ConstructionWorld) -> None:
    referent = RoleType.REFERENT
    text = RoleType.TEXT
    world.declare_relation(
        "config_member",
        [Role("snapshot", referent), Role("route", referent)],
        description="A route record mechanically contained in one JSON document.",
    )
    world.declare_relation(
        "config_route",
        [
            Role("subject", referent),
            Role("record_id", text),
            Role("path", text),
            Role("handler", text),
        ],
        description="Mechanical properties of one route record.",
    )


def _canonical(route: dict) -> bytes:
    return json.dumps(
        route,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _object_span(document: bytes, route_id: str) -> tuple[int, int]:
    # Flexible whitespace: pretty-printed `"id": "x"` and compact `"id":"x"`.
    pattern = re.compile(
        b'"id"\\s*:\\s*"' + re.escape(route_id.encode("utf-8")) + b'"'
    )
    matches = list(pattern.finditer(document))
    if len(matches) != 1:
        raise ConstructionError(
            f"route id {route_id} does not have one source span "
            f"({len(matches)} matches)"
        )
    found = matches[0]
    at = found.start()
    start = document.rfind(b"{", 0, at)
    if start < 0:
        raise ConstructionError(f"route id {route_id} has no object start")
    end = _balanced_object_span(document, start, route_id)[1]
    if not (start <= found.start() and found.end() <= end):
        raise ConstructionError(
            f"route id {route_id} source span does not enclose its identity"
        )
    return start, end


def _balanced_object_span(document: bytes, start: int, route_id: str) -> tuple[int, int]:
    # Brace matching that skips JSON string literals and escapes, so braces
    # inside path/handler values cannot corrupt the span.
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(document)):
        byte = document[index : index + 1]
        if in_string:
            if escaped:
                escaped = False
            elif byte == b"\\":
                escaped = True
            elif byte == b'"':
                in_string = False
            continue
        if byte == b'"':
            in_string = True
        elif byte == b"{":
            depth += 1
        elif byte == b"}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise ConstructionError(f"route id {route_id} object is not closed")


def _check_producer_inventory(world_path: Path, produced: ProducedRoutes) -> None:
    # The producer claims it examined exactly these routes. The published
    # mechanical inventory must match what was actually parsed.
    world = ConstructionWorld.open(world_path / "world.sqlite", read_only=True)
    try:
        members = list(world.relation_rows("config_member"))
        routes = list(world.relation_rows("config_route"))
    finally:
        world.close()
    if len(members) != len(produced.routes) or len(routes) != len(produced.routes):
        raise ConstructionError(
            "producer inventory mismatch: parsed "
            f"{len(produced.routes)} routes but published "
            f"{len(routes)} route rows and {len(members)} member rows"
        )
    by_record = {str(row["record_id"]): row for row in routes}
    if set(by_record) != {item.route_id for item in produced.routes}:
        raise ConstructionError("producer inventory mismatch: record ids differ")

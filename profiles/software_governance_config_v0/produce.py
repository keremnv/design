"""Mechanical producer for a JSON route document.

This is the fixture's producer, not a producer framework. It does not
interpret governance prose and it does not emit Program Spine relations.
"""

from __future__ import annotations

import hashlib
import json
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
DOCUMENT_NAME = "software.json"


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


def produce_routes(world_dir: Path, document: Path) -> ProducedRoutes:
    payload = document.read_bytes()
    parsed = json.loads(payload)
    routes = parsed.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ConstructionError(f"{document.name} does not contain a route list")
    digest = hashlib.sha256(payload).hexdigest()
    snapshot_id = f"snapshot:{digest[:32]}"
    document_observation = SourceObservation(
        provider="json",
        native_handle=f"{DOCUMENT_NAME}@sha256:{digest}",
        source_revision=f"sha256:{digest}",
        native_location=f"bytes:0:{len(payload)}",
    )
    blobs = {digest: payload}
    produced: list[ProducedRoute] = []
    world_dir.mkdir(parents=True, exist_ok=True)
    world = ConstructionWorld.create(world_dir / "world.sqlite", world_id="config-routes")
    try:
        _declare(world)
        world.add_referent(snapshot_id, label=DOCUMENT_NAME)
        for index, route in enumerate(routes):
            if not isinstance(route, dict):
                raise ConstructionError(f"route {index} is not an object")
            route_id = str(route["id"])
            start, end = _object_span(payload, route_id)
            subject_id = f"route:{digest[:16]}:{route_id}"
            canonical = _canonical(route)
            canonical_digest = hashlib.sha256(canonical).hexdigest()
            blobs[canonical_digest] = canonical
            item = ProducedRoute(
                subject_id=subject_id,
                route_id=route_id,
                path=str(route["path"]),
                handler=str(route["handler"]),
                location=f"/routes/{index}",
                document_observation=SourceObservation(
                    provider="json",
                    native_handle=document_observation.native_handle,
                    source_revision=document_observation.source_revision,
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
    finally:
        world.close()
    return ProducedRoutes(snapshot_id=snapshot_id, routes=tuple(produced), blobs=blobs)


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
    needle = f'"id": "{route_id}"'.encode("utf-8")
    at = document.find(needle)
    if at < 0:
        raise ConstructionError(f"route id {route_id} is not in the document bytes")
    start = document.rfind(b"{", 0, at)
    if start < 0:
        raise ConstructionError(f"route id {route_id} has no object start")
    depth = 0
    for index in range(start, len(document)):
        byte = document[index:index + 1]
        if byte == b"{":
            depth += 1
        elif byte == b"}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise ConstructionError(f"route id {route_id} object is not closed")

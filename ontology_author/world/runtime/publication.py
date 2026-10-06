"""Exact publication qualification shared by downstream verification surfaces.

A local World id is not a historical publication identity.  Consumers that
cite accepted semantic state must also identify the exact retained publication
that was opened.  This module deliberately stays small: it qualifies an
existing ``ConstructionWorld`` by its immutable bundle address, logical World
id, and revision, and verifies recorded references against that opened World.

Integrity of individual external evidence and program witnesses is a separate
concern.  A database/content digest may additionally authenticate bytes, but it
cannot replace publication occurrence identity because two retained
publications may contain identical bytes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ontology_author.world.runtime.world import ConstructionWorld


@dataclass(frozen=True)
class PublicationRef:
    """Exact retained publication occurrence used by a consumer.

    ``revision`` is the bundle-local construction counter recorded in
    ``_world_meta``. It is not a global publication sequence: two
    independently retained publications may legitimately share a revision,
    and a higher revision never means a newer or operative publication.
    """

    address: str
    world_id: str
    revision: int

    @classmethod
    def from_world(cls, world: ConstructionWorld) -> "PublicationRef":
        rows = world.query("SELECT revision FROM _world_meta WHERE singleton = 1")
        if len(rows) != 1:
            raise ValueError("opened World does not have one revision record")
        return cls(
            address=str(world.path.parent.resolve()),
            world_id=str(world.world_id),
            revision=int(rows[0]["revision"]),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PublicationRef":
        """Read either generic ``address`` or Case ``world_address`` fields."""

        address = value.get("address", value.get("world_address"))
        world_id = value.get("world_id")
        revision = value.get("revision")
        if not isinstance(address, str) or not address:
            raise ValueError("publication address is not a non-empty string")
        if not isinstance(world_id, str) or not world_id:
            raise ValueError("publication world id is not a non-empty string")
        if not isinstance(revision, int) or isinstance(revision, bool):
            raise ValueError("publication revision is not an integer")
        return cls(
            address=str(Path(address).resolve()),
            world_id=world_id,
            revision=revision,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "world_id": self.world_id,
            "revision": self.revision,
        }


def verify_publication_ref(
    world: ConstructionWorld,
    recorded: PublicationRef,
) -> list[str]:
    """Return named mismatches between a recorded and opened publication."""

    opened = PublicationRef.from_world(world)
    errors: list[str] = []
    if recorded.address != opened.address:
        errors.append("world address differs from the opened publication")
    if recorded.world_id != opened.world_id:
        errors.append("world id differs")
    if recorded.revision != opened.revision:
        errors.append("world revision differs from the opened publication")
    return errors

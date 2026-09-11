"""Small descriptive structural model for the checkout JSX fixture.

This is intentionally not a general React parser or an ontology. It recognizes
only the limited tag/attribute form used by ``Checkout.tsx`` and records the
things a governance profile can inspect: nodes, containment, current child
order, and which surface/context currently contains each node.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
_TAG = re.compile(
    r"<(?P<closing>/)?(?P<tag>[A-Za-z][\w.-]*)(?P<attributes>[^<>]*?)(?P<self_closing>/?)>"
)
_ATTRIBUTE = re.compile(r'(?P<name>[\w:-]+)\s*=\s*"(?P<value>[^"]*)"')
_IDENTITY_ATTRIBUTES = (
    ("data-screen", "surface"),
    ("data-context", "context"),
    ("data-region", "region"),
    ("data-field", "element"),
    ("data-action", "interaction"),
    ("aria-label", "control"),
)


def _identifier(value: str) -> str:
    lowered = value.strip().lower().replace("-", "_")
    return re.sub(r"[^a-z0-9_]+", "_", lowered).strip("_")


@dataclass(frozen=True)
class NodeSelector:
    """A small structural selector used by the application Governance Law."""

    attribute: str
    value: str
    kind: str | None = None

    def describe(self) -> dict[str, str]:
        payload = {"attribute": self.attribute, "value": self.value}
        if self.kind:
            payload["kind"] = self.kind
        return payload


@dataclass(frozen=True)
class StructuralNode:
    node_id: str
    kind: str
    tag: str
    parent_id: str | None
    order: int
    attributes: tuple[tuple[str, str], ...]

    def attribute(self, name: str) -> str | None:
        for key, value in self.attributes:
            if key == name:
                return value
        return None

    def as_payload(self) -> dict[str, object]:
        return {
            "id": self.node_id,
            "kind": self.kind,
            "tag": self.tag,
            "parent_id": self.parent_id,
            "order": self.order,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class FrontendStructure:
    """The finite, descriptive output of the fixture structural adapter."""

    source_name: str
    source_revision: str
    nodes: tuple[StructuralNode, ...]
    contains: tuple[tuple[str, str], ...]
    present_during: tuple[tuple[str, str], ...]
    arrangement: tuple[tuple[str, str, int], ...]

    def select(self, selector: NodeSelector) -> tuple[StructuralNode, ...]:
        return tuple(
            node
            for node in self.nodes
            if node.attribute(selector.attribute) == selector.value
            and (selector.kind is None or node.kind == selector.kind)
        )

    def node(self, node_id: str) -> StructuralNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(f"no structural node {node_id!r}")

    def is_present_during(self, subject: str, activity: str) -> bool:
        return (subject, activity) in self.present_during

    def as_payload(self, relevant_ids: set[str] | None = None) -> dict[str, object]:
        selected_ids = set(relevant_ids) if relevant_ids is not None else {
            node.node_id for node in self.nodes
        }
        # Keep ancestors needed to explain the selected nodes, but do not
        # publish unrelated implementation controls as if governance cared
        # about them.
        changed = True
        while changed:
            changed = False
            for node in self.nodes:
                if (
                    node.node_id in selected_ids
                    and node.parent_id is not None
                    and node.parent_id not in selected_ids
                ):
                    selected_ids.add(node.parent_id)
                    changed = True
        nodes = [node for node in self.nodes if node.node_id in selected_ids]
        return {
            "identity": {
                "source_name": self.source_name,
                "source_revision": self.source_revision,
            },
            "nodes": [node.as_payload() for node in nodes],
            "contains": [
                {"container": container, "member": member}
                for container, member in self.contains
                if container in selected_ids and member in selected_ids
            ],
            "present_during": [
                {"subject": subject, "context": context}
                for subject, context in self.present_during
                if subject in selected_ids and context in selected_ids
            ],
            "arrangement": [
                {"parent": parent, "child": child, "order": order}
                for parent, child, order in self.arrangement
                if parent in selected_ids and child in selected_ids
            ],
            "parser": {
                "kind": "bounded-react-jsx-attribute-adapter",
                "supported_syntax": "literal tags with double-quoted attributes",
            },
        }


def extract_frontend_structure(
    source: str,
    *,
    source_name: str = "Checkout.tsx",
    source_revision: str | None = None,
) -> FrontendStructure:
    """Extract the fixture's finite structural facts from limited JSX.

    The parser is deliberately conservative. It raises for malformed nesting
    rather than silently inventing a structural model, and it does not attempt
    to evaluate JavaScript, JSX expressions, components, CSS, or runtime state.
    """

    revision = source_revision or hashlib.sha256(source.encode("utf-8")).hexdigest()
    nodes: list[StructuralNode] = []
    contains: list[tuple[str, str]] = []
    arrangement: list[tuple[str, str, int]] = []
    stack: list[tuple[str, str]] = []
    child_orders: dict[str | None, int] = {}
    used_ids: dict[str, int] = {}

    for match in _TAG.finditer(source):
        tag = match.group("tag")
        if match.group("closing"):
            if not stack or stack[-1][0] != tag:
                raise ValueError(f"unsupported or malformed JSX closing tag </{tag}>")
            stack.pop()
            continue

        attributes = tuple(
            sorted(
                (item.group("name"), item.group("value"))
                for item in _ATTRIBUTE.finditer(match.group("attributes"))
            )
        )
        attribute_map = dict(attributes)
        kind, base_id = _node_identity(tag, attribute_map, len(nodes))
        count = used_ids.get(base_id, 0) + 1
        used_ids[base_id] = count
        node_id = base_id if count == 1 else f"{base_id}_{count}"
        parent_id = stack[-1][1] if stack else None
        order = child_orders.get(parent_id, 0)
        child_orders[parent_id] = order + 1
        node = StructuralNode(
            node_id=node_id,
            kind=kind,
            tag=tag,
            parent_id=parent_id,
            order=order,
            attributes=attributes,
        )
        nodes.append(node)
        if parent_id is not None:
            contains.append((parent_id, node_id))
            arrangement.append((parent_id, node_id, order))
        if not match.group("self_closing"):
            stack.append((tag, node_id))

    if stack:
        raise ValueError(f"unsupported or malformed JSX opening tag <{stack[-1][0]}>")

    present_during: list[tuple[str, str]] = []
    for node in nodes:
        parent = node.parent_id
        while parent is not None:
            ancestor = next(item for item in nodes if item.node_id == parent)
            if ancestor.kind in {"surface", "context"}:
                present_during.append((node.node_id, ancestor.node_id))
            parent = ancestor.parent_id

    return FrontendStructure(
        source_name=source_name,
        source_revision=revision,
        nodes=tuple(nodes),
        contains=tuple(contains),
        present_during=tuple(present_during),
        arrangement=tuple(arrangement),
    )


def _node_identity(
    tag: str, attributes: dict[str, str], ordinal: int
) -> tuple[str, str]:
    for attribute, kind in _IDENTITY_ATTRIBUTES:
        value = attributes.get(attribute)
        if value:
            return kind, _identifier(value) or f"{tag}_{ordinal}"
    return "element", f"{tag.lower()}_{ordinal}"


def write_structure_artifact(
    directory: Path | str,
    structure: FrontendStructure,
    *,
    relevant_ids: Iterable[str] | None = None,
) -> None:
    """Write the bounded descriptive model beside a candidate World."""

    path = Path(directory) / "world.structure.json"
    path.write_text(
        json.dumps(
            structure.as_payload(
                set(relevant_ids) if relevant_ids is not None else None
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


__all__ = [
    "FrontendStructure",
    "NodeSelector",
    "StructuralNode",
    "extract_frontend_structure",
    "write_structure_artifact",
]

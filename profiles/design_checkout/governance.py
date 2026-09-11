"""Executable Governance Law for the bounded checkout profile.

The law is intentionally application-level and finite. It names governed
dimensions and structural selectors; it does not decide which candidate wins
and it does not authorize evidence. Contract admission remains separate.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from dataclasses import dataclass
from .structure import FrontendStructure, NodeSelector


@dataclass(frozen=True)
class GovernanceBinding:
    """One named subject of a governed question.

    A binding is either selected from the descriptive structure or supplied as
    a fixed law-level goal. The latter is why ``purchase_confidence`` need not
    appear as a DOM node to be governed.
    """

    name: str
    selector: NodeSelector | None = None
    fixed_value: str | None = None

    def __post_init__(self) -> None:
        if (self.selector is None) == (self.fixed_value is None):
            raise ValueError("a GovernanceBinding needs exactly one selector or fixed value")

    def values(self, structure: FrontendStructure) -> tuple[str, ...]:
        if self.selector is not None:
            return tuple(node.node_id for node in structure.select(self.selector))
        return (str(self.fixed_value),)

    def as_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"name": self.name}
        if self.selector is not None:
            payload["selector"] = self.selector.describe()
        else:
            payload["fixed_value"] = self.fixed_value
        return payload


@dataclass(frozen=True)
class GovernedDimension:
    name: str
    bindings: tuple[GovernanceBinding, ...]
    question_template: str

    def enumerate(self, structure: FrontendStructure) -> tuple[dict[str, str], ...]:
        choices = [binding.values(structure) for binding in self.bindings]
        if any(not values for values in choices):
            return ()
        names = [binding.name for binding in self.bindings]
        return tuple(
            dict(zip(names, selected, strict=True))
            for selected in itertools.product(*choices)
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "bindings": [binding.as_payload() for binding in self.bindings],
            "question_template": self.question_template,
        }


@dataclass(frozen=True)
class GeneratedObligation:
    obligation_id: str
    law_id: str
    law_revision: str
    dimension: str
    bindings: tuple[tuple[str, str], ...]
    question: str

    @property
    def binding_map(self) -> dict[str, str]:
        return dict(self.bindings)

    @property
    def reason(self) -> str:
        article = "an" if self.dimension[0].lower() in "aeiou" else "a"
        return (
            f"Governance Law {self.law_id}@{self.law_revision} requires "
            f"{article} {self.dimension} determination for these structural subjects; "
            "no resolver runs in this slice."
        )


@dataclass(frozen=True)
class GovernanceProfile:
    """A finite law that enumerates questions over a structural model."""

    law_id: str
    revision: str
    dimensions: tuple[GovernedDimension, ...]

    def identity(self) -> dict[str, str]:
        return {"law_id": self.law_id, "revision": self.revision}

    def with_dimensions(
        self,
        *names: str,
        law_id: str | None = None,
        revision: str | None = None,
    ) -> "GovernanceProfile":
        wanted = set(names)
        return GovernanceProfile(
            law_id or self.law_id,
            revision or self.revision,
            tuple(dimension for dimension in self.dimensions if dimension.name in wanted),
        )

    def enumerate_obligations(
        self, structure: FrontendStructure
    ) -> tuple[GeneratedObligation, ...]:
        generated: list[GeneratedObligation] = []
        for dimension in self.dimensions:
            for binding_map in dimension.enumerate(structure):
                bindings = tuple(sorted(binding_map.items()))
                generated.append(
                    GeneratedObligation(
                        obligation_id=_obligation_id(
                            self.law_id,
                            self.revision,
                            dimension.name,
                            bindings,
                        ),
                        law_id=self.law_id,
                        law_revision=self.revision,
                        dimension=dimension.name,
                        bindings=bindings,
                        question=dimension.question_template.format(**binding_map),
                    )
                )
        return tuple(sorted(generated, key=lambda item: item.obligation_id))

    def referents_for(self, structure: FrontendStructure) -> tuple[str, ...]:
        values = {
            value
            for obligation in self.enumerate_obligations(structure)
            for _, value in obligation.bindings
        }
        return tuple(sorted(values))

    def inspection_payload(self) -> dict[str, object]:
        return {
            "identity": self.identity(),
            "dimensions": [dimension.as_payload() for dimension in self.dimensions],
        }


def _obligation_id(
    law_id: str,
    revision: str,
    dimension: str,
    bindings: tuple[tuple[str, str], ...],
) -> str:
    canonical = json.dumps(
        {
            "law_id": law_id,
            "revision": revision,
            "dimension": dimension,
            "bindings": dict(bindings),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    readable = ":".join(
        [_slug(law_id), _slug(revision), _slug(dimension)]
        + [f"{_slug(name)}={_slug(value)}" for name, value in bindings]
    )
    return f"obligation:{readable}:{digest}"


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value)).strip("_").lower()


__all__ = [
    "GeneratedObligation",
    "GovernanceBinding",
    "GovernanceProfile",
    "GovernedDimension",
]

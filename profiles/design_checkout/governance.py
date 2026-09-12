"""Bounded Governance Law compilation for the checkout profile.

The checkout profile deliberately keeps four stages separate:

``LawSource`` / ``AuthoritativeLawSources``
    The explicitly selected, law-bearing inputs.

``ProposedGovernanceLaw``
    The deterministic compiler's interpretation of those inputs.

``GovernanceProfile``
    The explicitly adopted law consumed by construction and obligation
    enumeration.

This is not a natural-language law interpreter or a general policy language.
The compiler recognizes the small section-and-binding format used by the
fixture so that a future human- or LLM-backed compiler can replace it without
changing the downstream structured-law boundary.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .structure import FrontendStructure, NodeSelector


COMPILER_ID = "bounded-checkout-governance-compiler-v1"
_SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$")
_BINDING = re.compile(r"^[-*]\s*(?P<name>[A-Za-z][A-Za-z _-]*):\s*(?P<value>.+?)\s*$")


@dataclass(frozen=True)
class LawSource:
    """One source explicitly selected as eligible to contribute law."""

    source_id: str
    path: str
    revision: str
    text: str

    def as_payload(self) -> dict[str, str]:
        # Source bodies remain ordinary project evidence. The sealed law
        # artifact records the address needed to inspect the source, not a
        # second copy of it.
        return {
            "source_id": self.source_id,
            "path": self.path,
            "revision": self.revision,
        }


@dataclass(frozen=True)
class AuthoritativeLawSources:
    """An explicit constitutional selection, not an inferred file scan."""

    law_id: str
    manifest_path: str
    sources: tuple[LawSource, ...]
    selection_method: str = "explicit project manifest"

    def as_payload(self) -> dict[str, object]:
        return {
            "law_id": self.law_id,
            "manifest_path": self.manifest_path,
            "selection_method": self.selection_method,
            "sources": [source.as_payload() for source in self.sources],
        }


@dataclass(frozen=True)
class LawRuleProvenance:
    """Why a structured law rule exists."""

    rule_id: str
    source_id: str
    source_revision: str
    source_location: str
    source_excerpt: str
    interpretation_method: str

    def as_payload(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "source_id": self.source_id,
            "source_revision": self.source_revision,
            "source_location": self.source_location,
            "source_excerpt": self.source_excerpt,
            "interpretation_method": self.interpretation_method,
        }


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
    rule_id: str = ""
    provenance: LawRuleProvenance | None = None

    def __post_init__(self) -> None:
        if not self.rule_id:
            object.__setattr__(self, "rule_id", self.name)

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
            "rule_id": self.rule_id,
            "bindings": [binding.as_payload() for binding in self.bindings],
            "question_template": self.question_template,
            "provenance": self.provenance.as_payload() if self.provenance else None,
        }


@dataclass(frozen=True)
class GeneratedObligation:
    obligation_id: str
    law_id: str
    law_revision: str
    dimension: str
    bindings: tuple[tuple[str, str], ...]
    question: str
    rule_id: str = ""
    provenance: LawRuleProvenance | None = None

    def __post_init__(self) -> None:
        if not self.rule_id:
            object.__setattr__(self, "rule_id", self.dimension)

    @property
    def binding_map(self) -> dict[str, str]:
        return dict(self.bindings)

    @property
    def reason(self) -> str:
        article = "an" if self.dimension[0].lower() in "aeiou" else "a"
        return (
            f"Governance Law {self.law_id}@{self.law_revision} requires "
            f"{article} {self.dimension} determination under rule {self.rule_id} "
            "for these structural subjects; no resolver runs in this slice."
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "obligation_id": self.obligation_id,
            "law_id": self.law_id,
            "law_revision": self.law_revision,
            "dimension": self.dimension,
            "rule_id": self.rule_id,
            "bindings": dict(self.bindings),
            "question": self.question,
            "reason": self.reason,
            "law_provenance": self.provenance.as_payload() if self.provenance else None,
        }


@dataclass(frozen=True)
class ProposedGovernanceLaw:
    """Compiler output awaiting an explicit adoption decision."""

    law_id: str
    revision: str
    dimensions: tuple[GovernedDimension, ...]
    source_selection: AuthoritativeLawSources
    compilation_method: str = COMPILER_ID

    def identity(self) -> dict[str, str]:
        return {"law_id": self.law_id, "revision": self.revision}

    def inspection_payload(self) -> dict[str, object]:
        return {
            "state": "PROPOSED",
            "identity": self.identity(),
            "compilation_method": self.compilation_method,
            "source_selection": self.source_selection.as_payload(),
            "rules": [dimension.as_payload() for dimension in self.dimensions],
        }

    def adopt(
        self,
        *,
        adopted_by: str,
        adoption_method: str = "explicit configuration",
    ) -> "GovernanceProfile":
        actor = str(adopted_by or "").strip()
        if not actor:
            raise ValueError("explicit law adoption requires adopted_by")
        return GovernanceProfile(
            law_id=self.law_id,
            revision=self.revision,
            dimensions=self.dimensions,
            source_selection=self.source_selection,
            compilation_method=self.compilation_method,
            adoption={"adopted_by": actor, "method": adoption_method},
            proposed_law=self,
        )


@dataclass(frozen=True)
class GovernanceProfile:
    """An effective finite law that enumerates questions over structure."""

    law_id: str
    revision: str
    dimensions: tuple[GovernedDimension, ...]
    source_selection: AuthoritativeLawSources | None = None
    compilation_method: str = ""
    adoption: dict[str, str] | None = None
    proposed_law: ProposedGovernanceLaw | None = None

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
            source_selection=self.source_selection,
            compilation_method=self.compilation_method,
            adoption=self.adoption,
            proposed_law=self.proposed_law,
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
                        rule_id=dimension.rule_id,
                        provenance=dimension.provenance,
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
            "state": "EFFECTIVE",
            "identity": self.identity(),
            "compilation_method": self.compilation_method or None,
            "adoption": self.adoption,
            "source_selection": (
                self.source_selection.as_payload() if self.source_selection else None
            ),
            "rules": [dimension.as_payload() for dimension in self.dimensions],
            "proposed_law": (
                self.proposed_law.inspection_payload() if self.proposed_law else None
            ),
        }


def select_authoritative_sources(
    project_root: Path | str,
    manifest_name: str = "governance-sources.json",
) -> AuthoritativeLawSources:
    """Read only the sources named by the explicit project manifest."""

    root = Path(project_root)
    manifest_path = root / manifest_name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("governance source manifest must be an object")
    law_id = str(manifest.get("law_id") or "").strip()
    if not law_id:
        raise ValueError("governance source manifest needs law_id")
    entries = manifest.get("sources", [])
    if not isinstance(entries, list):
        raise ValueError("governance source manifest sources must be a list")

    sources: list[LawSource] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each governance source selection must be an object")
        source_id = str(entry.get("source_id") or "").strip()
        relative_path = str(entry.get("path") or "").strip()
        if not source_id or not relative_path:
            raise ValueError("each governance source needs source_id and path")
        source_path = (root / relative_path).resolve()
        try:
            source_path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValueError("governance source must remain inside the project") from exc
        if not source_path.is_file():
            raise FileNotFoundError(relative_path)
        body = source_path.read_text(encoding="utf-8")
        sources.append(
            LawSource(
                source_id=source_id,
                path=relative_path,
                revision=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                text=body,
            )
        )
    return AuthoritativeLawSources(
        law_id=law_id,
        manifest_path=manifest_name,
        sources=tuple(sorted(sources, key=lambda item: (item.source_id, item.path))),
    )


def compile_governance_law(
    authoritative_sources: AuthoritativeLawSources,
) -> ProposedGovernanceLaw:
    """Compile the intentionally constrained checkout source format.

    The compiler does not search for sources and does not decide whether a
    source is constitutional. It only interprets the already selected files.
    """

    dimensions: list[GovernedDimension] = []
    seen_dimensions: set[str] = set()
    for source in authoritative_sources.sources:
        for title, start, end, lines in _sections(source.text):
            dimension = _compile_section(source, title, start, end, lines)
            if dimension is None:
                continue
            if dimension.name in seen_dimensions:
                raise ValueError(
                    f"multiple selected law sources define {dimension.name!r}; "
                    "law conflict resolution is out of scope"
                )
            seen_dimensions.add(dimension.name)
            dimensions.append(dimension)

    canonical_sources = [source.as_payload() for source in authoritative_sources.sources]
    revision_input = json.dumps(
        {
            "law_id": authoritative_sources.law_id,
            "sources": canonical_sources,
            "compiler": COMPILER_ID,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    revision = hashlib.sha256(revision_input.encode("utf-8")).hexdigest()[:16]
    return ProposedGovernanceLaw(
        law_id=authoritative_sources.law_id,
        revision=revision,
        dimensions=tuple(sorted(dimensions, key=lambda item: item.rule_id)),
        source_selection=authoritative_sources,
    )


def adopt_governance_law(
    proposed_law: ProposedGovernanceLaw,
    *,
    adopted_by: str = "explicit checkout profile configuration",
) -> GovernanceProfile:
    """Make the compiler output effective through an explicit adoption step."""

    return proposed_law.adopt(adopted_by=adopted_by)


def write_obligation_artifact(
    directory: Path | str,
    obligations: tuple[GeneratedObligation, ...],
) -> None:
    """Persist generated-law provenance beside the sealed World.

    The kernel obligation table remains generic. This profile-specific artifact
    gives the read surface the rule/source/binding explanation without turning
    application law provenance into a new kernel schema prematurely.
    """

    items = {item.obligation_id: item.as_payload() for item in obligations}
    identities = sorted({(item.law_id, item.law_revision) for item in obligations})
    law_identity = (
        {"law_id": identities[0][0], "revision": identities[0][1]}
        if len(identities) == 1
        else None
    )
    payload = {
        "law": law_identity,
        "obligations": items,
    }
    (Path(directory) / "world.obligations.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sections(text: str) -> tuple[tuple[str, int, int, tuple[str, ...]], ...]:
    lines = text.splitlines()
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = _SECTION.match(line)
        if match:
            starts.append((match.group("title").strip(), index))
    sections: list[tuple[str, int, int, tuple[str, ...]]] = []
    for index, (title, start_index) in enumerate(starts):
        next_index = starts[index + 1][1] if index + 1 < len(starts) else len(lines)
        sections.append(
            (title, start_index + 1, next_index, tuple(lines[start_index + 1 : next_index]))
        )
    return tuple(sections)


def _compile_section(
    source: LawSource,
    title: str,
    start: int,
    end: int,
    lines: tuple[str, ...],
) -> GovernedDimension | None:
    normalized = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    definitions: dict[str, tuple[str, str]] = {
        "availability": (
            "availability",
            "What availability relationship should hold between {subject} "
            "and {activity} in {context}?",
        ),
        "priority": (
            "priority",
            "What should dominate visual hierarchy between {more} and {less} "
            "at {context}?",
        ),
        "goal_support": (
            "goal_support",
            "What should support {goal} at {context}, and how should "
            "{subject} contribute?",
        ),
    }
    if normalized not in definitions:
        return None
    dimension_name, question_template = definitions[normalized]
    fields: dict[str, str] = {}
    for line in lines:
        match = _BINDING.match(line.strip())
        if match:
            fields[_slug(match.group("name"))] = match.group("value").strip()

    required = {
        "availability": ("subject", "activity", "context"),
        "priority": ("more", "less", "context"),
        "goal_support": ("subject", "goal", "context"),
    }[dimension_name]
    missing = [name for name in required if name not in fields]
    if missing:
        raise ValueError(
            f"selected law source {source.source_id!r} section {title!r} "
            f"is missing bindings: {', '.join(missing)}"
        )

    bindings = tuple(
        GovernanceBinding(name, **_binding_value(fields[name])) for name in required
    )
    rule_id = f"rule:{_slug(source.source_id)}:{dimension_name}"
    excerpt = "\n".join(line.strip() for line in lines if line.strip())
    provenance = LawRuleProvenance(
        rule_id=rule_id,
        source_id=source.source_id,
        source_revision=source.revision,
        source_location=f"{source.path}#L{start}-L{end}",
        source_excerpt=excerpt,
        interpretation_method=COMPILER_ID,
    )
    return GovernedDimension(
        name=dimension_name,
        bindings=bindings,
        question_template=question_template,
        rule_id=rule_id,
        provenance=provenance,
    )


def _binding_value(value: str) -> dict[str, object]:
    match = re.fullmatch(
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_-]*)\s+(?P<kind>surface|context|region|field|interaction|element|goal)",
        value.strip().lower(),
    )
    if not match:
        raise ValueError(
            f"bounded checkout Governance Law cannot interpret binding {value!r}"
        )
    identifier = match.group("identifier")
    kind = match.group("kind")
    if kind == "goal":
        return {"fixed_value": _slug(identifier)}
    attributes = {
        "surface": "data-screen",
        "context": "data-context",
        "region": "data-region",
        "field": "data-field",
        "interaction": "data-action",
        "element": "data-field",
    }
    selector_kinds = {
        "surface": "surface",
        "context": "context",
        "region": "region",
        "field": "element",
        "interaction": "interaction",
        "element": "element",
    }
    return {
        "selector": NodeSelector(
            attributes[kind],
            identifier,
            selector_kinds[kind],
        )
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
    "AuthoritativeLawSources",
    "COMPILER_ID",
    "GeneratedObligation",
    "GovernanceBinding",
    "GovernanceProfile",
    "GovernedDimension",
    "LawRuleProvenance",
    "LawSource",
    "ProposedGovernanceLaw",
    "adopt_governance_law",
    "compile_governance_law",
    "select_authoritative_sources",
    "write_obligation_artifact",
]

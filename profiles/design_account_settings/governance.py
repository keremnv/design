"""Bounded Governance Law compilation for account settings.

The profile keeps source selection, proposed compilation, explicit adoption,
and effective obligation enumeration separate. The compiler recognizes only
the two sections used by this fixture; it is not a general policy language.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .structure import FrontendStructure, NodeSelector


ACCOUNT_SETTINGS_COMPILER_ID = "bounded-account-settings-governance-compiler-v1"
_SECTION = re.compile(r"^##\s+(?P<title>.+?)\s*$")
_BINDING = re.compile(r"^[-*]\s*(?P<name>[A-Za-z][A-Za-z _-]*):\s*(?P<value>.+?)\s*$")


@dataclass(frozen=True)
class LawSource:
    source_id: str
    path: str
    revision: str
    text: str

    def as_payload(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "revision": self.revision,
        }


@dataclass(frozen=True)
class AuthoritativeLawSources:
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
    name: str
    selector: NodeSelector

    def values(self, structure: FrontendStructure) -> tuple[str, ...]:
        return tuple(node.node_id for node in structure.select(self.selector))

    def as_payload(self) -> dict[str, object]:
        return {"name": self.name, "selector": self.selector.describe()}


@dataclass(frozen=True)
class GovernedDimension:
    name: str
    bindings: tuple[GovernanceBinding, ...]
    question_template: str
    rule_id: str
    provenance: LawRuleProvenance

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
            "provenance": self.provenance.as_payload(),
        }


@dataclass(frozen=True)
class GeneratedObligation:
    obligation_id: str
    law_id: str
    law_revision: str
    dimension: str
    bindings: tuple[tuple[str, str], ...]
    question: str
    rule_id: str
    provenance: LawRuleProvenance

    @property
    def binding_map(self) -> dict[str, str]:
        return dict(self.bindings)

    @property
    def reason(self) -> str:
        return (
            f"Governance Law {self.law_id}@{self.law_revision} requires a "
            f"{self.dimension} determination under rule {self.rule_id} for "
            "these structural subjects; resolution is evaluated separately "
            "from construction."
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
            "law_provenance": self.provenance.as_payload(),
        }


@dataclass(frozen=True)
class ProposedGovernanceLaw:
    law_id: str
    revision: str
    dimensions: tuple[GovernedDimension, ...]
    source_selection: AuthoritativeLawSources
    compilation_method: str = ACCOUNT_SETTINGS_COMPILER_ID

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
        conflict_checker: Callable[
            [Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], bool
        ] | None = None,
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
            conflict_checker=conflict_checker,
        )


@dataclass(frozen=True)
class GovernanceProfile:
    law_id: str
    revision: str
    dimensions: tuple[GovernedDimension, ...]
    source_selection: AuthoritativeLawSources | None = None
    compilation_method: str = ""
    adoption: dict[str, str] | None = None
    proposed_law: ProposedGovernanceLaw | None = None
    conflict_checker: Callable[
        [Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], bool
    ] | None = None

    def identity(self) -> dict[str, str]:
        return {"law_id": self.law_id, "revision": self.revision}

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
                            self.law_id, self.revision, dimension.name, bindings
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
        return tuple(
            sorted(
                {
                    value
                    for obligation in self.enumerate_obligations(structure)
                    for _, value in obligation.bindings
                }
            )
        )

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
    """Read only law sources explicitly named by the project manifest."""

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
        sources.append(
            LawSource(
                source_id=source_id,
                path=relative_path,
                revision=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                text=source_path.read_text(encoding="utf-8"),
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
    """Compile the two explicit rule sections supported by this profile."""

    dimensions: list[GovernedDimension] = []
    seen: set[str] = set()
    for source in authoritative_sources.sources:
        for title, start, end, lines in _sections(source.text):
            dimension = _compile_section(source, title, start, end, lines)
            if dimension is None:
                continue
            if dimension.name in seen:
                raise ValueError(f"multiple selected law sources define {dimension.name!r}")
            seen.add(dimension.name)
            dimensions.append(dimension)

    revision_input = json.dumps(
        {
            "law_id": authoritative_sources.law_id,
            "sources": [source.as_payload() for source in authoritative_sources.sources],
            "compiler": ACCOUNT_SETTINGS_COMPILER_ID,
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
    adopted_by: str = "explicit account-settings profile configuration",
    conflict_checker: Callable[
        [Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], bool
    ] | None = None,
) -> GovernanceProfile:
    return proposed_law.adopt(
        adopted_by=adopted_by,
        conflict_checker=conflict_checker,
    )


def write_obligation_artifact(
    directory: Path | str,
    obligations: tuple[GeneratedObligation, ...],
) -> None:
    items = {item.obligation_id: item.as_payload() for item in obligations}
    identities = sorted({(item.law_id, item.law_revision) for item in obligations})
    payload = {
        "law": (
            {"law_id": identities[0][0], "revision": identities[0][1]}
            if len(identities) == 1
            else None
        ),
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
    return tuple(
        (
            title,
            start + 1,
            (starts[index + 1][1] if index + 1 < len(starts) else len(lines)),
            tuple(
                lines[
                    start + 1 : (starts[index + 1][1] if index + 1 < len(starts) else len(lines))
                ]
            ),
        )
        for index, (title, start) in enumerate(starts)
    )


def _compile_section(
    source: LawSource,
    title: str,
    start: int,
    end: int,
    lines: tuple[str, ...],
) -> GovernedDimension | None:
    normalized = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    definitions = {
        "confirmation_before_deletion": (
            "confirmation_requirement",
            ("action", "consequence", "context"),
            "Should {action} require explicit confirmation before {consequence} "
            "in {context}?",
        ),
        "consequence_distinction": (
            "consequence_distinction",
            ("routine", "destructive", "context"),
            "How should routine {routine} and destructive {destructive} actions "
            "differ in consequence handling in {context}?",
        ),
    }
    definition = definitions.get(normalized)
    if definition is None:
        return None
    dimension_name, required, question_template = definition
    fields: dict[str, str] = {}
    for line in lines:
        match = _BINDING.match(line.strip())
        if match:
            fields[_slug(match.group("name"))] = match.group("value").strip()
    missing = [name for name in required if name not in fields]
    if missing:
        raise ValueError(
            f"selected law source {source.source_id!r} section {title!r} "
            f"is missing bindings: {', '.join(missing)}"
        )
    bindings = tuple(
        GovernanceBinding(name, selector=_binding_selector(fields[name]))
        for name in required
    )
    rule_id = f"rule:{_slug(source.source_id)}:{dimension_name}"
    provenance = LawRuleProvenance(
        rule_id=rule_id,
        source_id=source.source_id,
        source_revision=source.revision,
        source_location=f"{source.path}#L{start}-L{end}",
        source_excerpt="\n".join(line.strip() for line in lines if line.strip()),
        interpretation_method=ACCOUNT_SETTINGS_COMPILER_ID,
    )
    return GovernedDimension(
        name=dimension_name,
        bindings=bindings,
        question_template=question_template,
        rule_id=rule_id,
        provenance=provenance,
    )


def _binding_selector(value: str) -> NodeSelector:
    match = re.fullmatch(
        r"(?P<identifier>[A-Za-z][A-Za-z0-9_-]*)\s+(?P<kind>surface|context|region|field|interaction|element)",
        value.strip().lower(),
    )
    if not match:
        raise ValueError(
            f"bounded account-settings Governance Law cannot interpret binding {value!r}"
        )
    identifier = match.group("identifier")
    kind = match.group("kind")
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
    return NodeSelector(
        attributes[kind], identifier, selector_kinds[kind]
    )


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
    "ACCOUNT_SETTINGS_COMPILER_ID",
    "AuthoritativeLawSources",
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

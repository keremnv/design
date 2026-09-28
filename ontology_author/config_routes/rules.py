"""Versioned establishment rules for ``config.routes/v1``.

A future reader can identify which versioned rule licensed each semantic
assertion from the grounding ``establishment_rule`` and ``construction_method``
recorded on that assertion, plus this module's rule table.

Supported governance source form (refuse everything else):

- existing regular file with a ``.md`` suffix, UTF-8 Markdown bytes
- paragraphs via the bounded Markdown subset (``MarkdownSource.paragraphs``)
- each supported paragraph matches exactly one rule pattern below

Supported patterns (after stripping surrounding whitespace):

- SPECIFIC ``<subject> must use the approved <route-id> route.``
  ``route-id`` matches ``[A-Za-z0-9][A-Za-z0-9_-]*``.
- GENERIC ``<subject> must use an approved route.``

``<subject>`` is one requirement's subject phrase: it must not contain
``.``, ``?``, ``!``, or another ``must use`` requirement. A paragraph
holding two requirements, or rule-like text embedded in the subject,
matches no pattern and is UNSUPPORTED (fail-closed, never split).

Any other paragraph is UNSUPPORTED: it yields no proposition, is listed in
the construction report, and contributes a known gap. An empty governance
source (no paragraphs) or a source with zero supported paragraphs refuses
construction: there is no honest interpretation to publish.

Semantic establishment (all deterministic, no fuzzy matching):

- SPECIFIC names one route ID exactly (case-sensitive). If that ID exists
  in the parsed software source, emit one binding (SOURCE_EXPLICIT,
  DETERMINISTIC). If it does not exist, emit no binding, one UNRESOLVED
  question, and a ``missing_route_*`` gap.
- GENERIC names no endpoint. Emit one candidate per parsed route
  (SOURCE_GENERIC, AMBIGUOUS), one UNRESOLVED question, and never a binding.
- Propositions, candidates, and questions are SEMANTIC. Coverage stays
  INCOMPLETE: determinism does not prove all relevant governance was found.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

PROFILE_ID = "config.routes/v1"
PROFILE_VERSION = "v1"

RULE_PROPOSITION_SPECIFIC = "config.routes.proposition/v1:specific"
RULE_PROPOSITION_GENERIC = "config.routes.proposition/v1:generic"
RULE_BINDING = "config.routes.binding/v1"
RULE_CANDIDATE = "config.routes.candidate/v1"
RULE_QUESTION = "config.routes.question/v1"
RULE_COVERAGE = "config.routes.coverage/v1"
RULE_EVALUATOR = "config.routes.evaluator/v1"

RULES = (
    RULE_PROPOSITION_SPECIFIC,
    RULE_PROPOSITION_GENERIC,
    RULE_BINDING,
    RULE_CANDIDATE,
    RULE_QUESTION,
    RULE_COVERAGE,
    RULE_EVALUATOR,
)

SPECIFIC_RE = re.compile(
    r"^(?P<subject>[^.?!]+?) must use the approved "
    r"(?P<route_id>[A-Za-z0-9][A-Za-z0-9_-]*) route\.$"
)
GENERIC_RE = re.compile(r"^(?P<subject>[^.?!]+?) must use an approved route\.$")

BINDING_SUPPORT = "SOURCE_EXPLICIT"
BINDING_RESOLUTION = "DETERMINISTIC"
BINDING_METHOD = "config.routes.binding/v1:exact-route-id"
CANDIDATE_SUPPORT = "SOURCE_GENERIC"
CANDIDATE_RESOLUTION = "AMBIGUOUS"
CANDIDATE_METHOD = "config.routes.candidate/v1:generic-approved-route"
QUESTION_METHOD = "config.routes.question/v1:explicit-unresolved"

COMPLETENESS_BASIS = (
    "only the correspondences established by config.routes/v1 rules "
    "from the supplied source pair are recorded"
)
GAP_SUPPLIED_ONLY = "supplied_correspondences_only"
GAP_UNSUPPORTED_GOVERNANCE = "unsupported_governance_statements"
GAP_GENERIC_UNRESOLVED = "generic_correspondence_unresolved"
GAP_EVALUATOR_UNSUPPORTED = "evaluator_rule_not_declared"

# Evaluator consistency for Phase 1 (no Judge facade yet).
# The only declared judgment rule is the customer-export rule. Construction
# records which propositions it covers; any other proposition carries an
# explicit evaluator gap in the report instead of silently reusing it.
EVALUATOR_METHOD_ID = "config.customer_export_route"
EVALUATOR_VERSION = "v0"
EVALUATOR_RULE = {
    "applies_to_kind": "config:route",
    "required_handler": "CustomerExport",
    "conformance_field": "path",
    "required_path": "/customers/export",
}
EVALUATOR_COVERED_ROUTE_IDS = frozenset({"customer-export"})
EVALUATOR_COVERED_PROPOSITIONS = frozenset({"proposition:customer-export-route"})


@dataclass(frozen=True)
class ExtractedProposition:
    proposition_id: str
    statement: str
    domain_relation: str
    kind: str  # "specific" | "generic"
    route_id: str | None
    subject_phrase: str
    establishment_rule: str


def slugify(text: str, *, limit: int = 32) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    if not cleaned:
        cleaned = "statement"
    return cleaned[:limit].strip("-") or "statement"


def gap_token(text: str, *, limit: int = 40) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"g_{cleaned}" if cleaned else "g_unnamed"
    return cleaned[:limit].strip("_") or "g_unnamed"


def domain_relation_for_specific(route_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", route_id.strip().lower()).strip("_") + "_route"


def domain_relation_for_generic(subject: str) -> str:
    return "approved_" + gap_token(subject) + "_route"


def proposition_id_for_specific(route_id: str) -> str:
    return f"proposition:{route_id}-route"


def proposition_id_for_generic(subject: str) -> str:
    return f"proposition:approved-{slugify(subject)}-route"


def classify_paragraph(text: str) -> tuple[str | None, re.Match[str] | None]:
    stripped = text.strip()
    match = SPECIFIC_RE.match(stripped)
    if match is not None and "must use" not in match.group("subject"):
        return "specific", match
    match = GENERIC_RE.match(stripped)
    if match is not None and "must use" not in match.group("subject"):
        return "generic", match
    return None, None


def extract_propositions(
    paragraphs: list[tuple[str, int]],
) -> tuple[list[ExtractedProposition], list[dict[str, str]]]:
    """Derive propositions from stripped paragraph texts.

    ``paragraphs`` is ``(text, paragraph_index)`` in source order. Returns
    ``(propositions, unsupported)``. Identical statements deduplicate to one
    proposition; distinct statements that collide on an ID receive a
    statement-hash suffix so no wording is silently merged.
    """
    seen_statement: dict[str, ExtractedProposition] = {}
    used_ids: dict[str, str] = {}
    propositions: list[ExtractedProposition] = []
    unsupported: list[dict[str, str]] = []
    for text, index in paragraphs:
        stripped = text.strip()
        if not stripped:
            continue
        kind, match = classify_paragraph(stripped)
        if kind is None or match is None:
            unsupported.append({
                "paragraph_index": str(index),
                "text": stripped[:200],
                "reason": "no supported config.routes/v1 pattern matched",
            })
            continue
        if stripped in seen_statement:
            continue
        if kind == "specific":
            route_id = match.group("route_id")
            subject = match.group("subject").strip()
            base_id = proposition_id_for_specific(route_id)
            domain = domain_relation_for_specific(route_id)
            rule = RULE_PROPOSITION_SPECIFIC
        else:
            subject = match.group("subject").strip()
            route_id = None
            base_id = proposition_id_for_generic(subject)
            domain = domain_relation_for_generic(subject)
            rule = RULE_PROPOSITION_GENERIC
        proposition_id = base_id
        if proposition_id in used_ids and used_ids[proposition_id] != stripped:
            digest = hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:8]
            proposition_id = base_id + f"-{digest}"
            counter = 1
            while proposition_id in used_ids:
                counter += 1
                proposition_id = base_id + f"-{digest}-{counter}"
        used_ids[proposition_id] = stripped
        item = ExtractedProposition(
            proposition_id=proposition_id,
            statement=stripped,
            domain_relation=domain,
            kind=kind,
            route_id=route_id,
            subject_phrase=subject,
            establishment_rule=rule,
        )
        seen_statement[stripped] = item
        propositions.append(item)
    return propositions, unsupported


def question_for_missing_route(route_id: str, statement: str) -> str:
    return (
        f"Route '{route_id}' named by {statement!r} was not found in the "
        "supplied software source; which subject satisfies it?"
    )


def question_for_generic(subject: str) -> str:
    return f"Which route is the approved route for '{subject}'?"


def missing_route_gap(route_id: str) -> str:
    return "missing_route_" + gap_token(route_id)


def evaluator_for_statement(
    statement: str, establishment_rule: str
) -> tuple[str, str | None, str | None]:
    """Decide evaluator support from durable World content alone.

    Re-applies this profile's versioned grammar to the retained statement,
    so discovery is provably consistent with construction. Returns
    ``(status, route_id, reason)`` with ``status`` ``"covered"`` or
    ``"unsupported"``. Inconsistent provenance (rule says specific but the
    statement parses otherwise) is ``"unsupported"`` with an explicit
    reason, never a guessed evaluator.
    """
    kind, match = classify_paragraph(statement)
    if kind == "specific" and establishment_rule == RULE_PROPOSITION_SPECIFIC:
        route_id = match.group("route_id") if match is not None else None
        if route_id in EVALUATOR_COVERED_ROUTE_IDS:
            return "covered", route_id, None
        return "unsupported", route_id, (
            f"no evaluator declared for route {route_id!r} "
            f"under {RULE_EVALUATOR}"
        )
    if kind == "generic" and establishment_rule == RULE_PROPOSITION_GENERIC:
        return "unsupported", None, (
            f"generic propositions have no evaluator under {RULE_EVALUATOR}"
        )
    return "unsupported", None, (
        "proposition provenance does not match a supported "
        f"{PROFILE_ID} establishment rule"
    )


def evaluator_status(
    proposition_id: str, route_id: str | None
) -> tuple[str, dict[str, str] | None, str | None]:
    """Return (status, rule, gap) for the declared evaluator mapping.

    ``status`` is ``"covered"`` or ``"unsupported"``. Covered propositions
    name the exact method/version/rule. Unsupported ones name a gap instead
    of silently reusing the customer-export rule.
    """
    if proposition_id in EVALUATOR_COVERED_PROPOSITIONS or (
        route_id is not None and route_id in EVALUATOR_COVERED_ROUTE_IDS
    ):
        return "covered", {
            "method_id": EVALUATOR_METHOD_ID,
            "version": EVALUATOR_VERSION,
        }, None
    return "unsupported", None, GAP_EVALUATOR_UNSUPPORTED

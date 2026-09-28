"""Bounded production Investigation from an honest config.routes UNKNOWN.

Thin product facade over the generic Investigation machinery
(``ontology_author.software_governance.investigation``), which is reused
unchanged: same-publication case expansion, the question/receipt/proposal
records, and the ``CASE_EXPANDED`` / ``PROPOSAL`` / ``UNRESOLVED`` outcome
vocabulary. The only profile-owned rule here is the bounded
``config.subject-investigation`` decision (which unasserted manifestation
field answers the asked question), mirroring the repository fixture
investigator; a cross-check test asserts they agree.

The caller supplies only an exact World address plus proposition and
subject IDs discovered through Inspect. The facade owns the guarded
trigger Judgment (reused from Phase 2, never duplicated), UNKNOWN
eligibility, the Investigation question, invocation with a same-World
manifestation capability, and the structured result. An already verified
Judgment bundle may optionally be supplied as the trigger instead of
re-judging; it is verified with the Phase 2 verifier first.

Investigation inspects W0 and returns verified same-World material, a
proposal sidecar, or an honest unresolved explanation. It never admits,
establishes, publishes, decides, or mutates. A proposal is not an
assertion: it carries no assertion id.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Callable

from ontology_author.config_routes.inspect import (
    database_fingerprint,
    open_config_world_view,
)
from ontology_author.config_routes.judge import (
    _broken_evidence,
    _resolved,
    _revision,
    _world_block_error,
    judge_config_world,
    read_judgment_bundle,
    verify_judgment_bundle,
)
from ontology_author.software_governance.investigation import (
    OUTCOMES,
    InvestigationBoundary,
    added_assertion_ids,
    expanded_case,
    make_proposal,
    make_question,
    make_receipt,
)
from ontology_author.software_governance.judgment import verify_case
from ontology_author.software_governance.reads import GovernanceView

INVESTIGATION_BUNDLE_FORMAT = "config-routes-investigation/v1"
METHOD_ID = "config.subject-investigation"
PUBLISHED_SOURCE_KEYS = frozenset({"id", "path", "handler"})
# Source field names that must never become a proposal field: they would
# read as product-generated assertion identity. Such material stays
# inspectable; it is never proposed.
RESERVED_PROPOSAL_FIELDS = frozenset({"assertion_id", "assertion_ids"})

_BUNDLE_KEYS = frozenset({"format", "world", "request", "trigger", "question", "receipt", "proposal", "case"})
_WORLD_KEYS = frozenset({"address", "world_id", "revision", "database_fingerprint"})
_REQUEST_KEYS = frozenset({"proposition", "subject", "question_focus"})
_TRIGGER_KEYS = frozenset({"case_id", "artifact"})


def investigate_bounded_case(
    view: GovernanceView,
    case: dict[str, Any],
    question: dict[str, Any],
    capabilities: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """Run the bounded ``config.subject-investigation`` rule.

    Same decision shape as the repository fixture investigator, with one
    stricter product rule: only the exact property named by
    ``structured_need`` may become a proposal field. There is no
    question-text fallback — fixed question prose must never select a
    field the caller did not name. Published subject facts missing from
    the parent case expand it (verified, same publication); otherwise
    the result is unresolved. The sealed World is only read.
    """
    subject = str(question["subject"])
    mechanical = view.mechanical_facts_for_subject(subject)
    inspected = sorted({str(item["relation"]) for item in mechanical})
    unpublished = _unpublished(subject, mechanical, question, capabilities, inspected)
    missing = [item for item in mechanical if not _case_has(case, item)]
    if unpublished is not None:
        proposal = _proposal(case, question, unpublished)
        outcome = "PROPOSAL"
        child = None
        added: list[str] = []
    elif missing:
        child = expanded_case(view, case, case_id=f"{case['case_id']}-expanded")
        added = added_assertion_ids(case, child)
        proposal = None
        outcome = "CASE_EXPANDED"
    else:
        child = None
        added = []
        proposal = None
        outcome = "UNRESOLVED"
    receipt = make_receipt(
        question_id=str(question["question_id"]),
        parent_case_id=str(case["case_id"]),
        world_id=str(case["world_id"]),
        revision=int(case["revision"]),
        world_address=str(case["world_address"]),
        method_id=METHOD_ID,
        capabilities=tuple(capabilities),
        outcome=outcome,
        resulting_case_id=None if child is None else str(child["case_id"]),
        added_assertion_ids=added,
        proposal_id=None if proposal is None else str(proposal["proposal_id"]),
        inspected_relations=inspected,
    )
    return {"outcome": outcome, "case": child, "proposal": proposal, "receipt": receipt}


def investigate_config_world(
    *,
    world: Path | str,
    proposition: str,
    subject: str,
    question_focus: str | None = None,
    judgment: dict[str, Any] | Path | str | None = None,
    persist_to: Path | str | None = None,
) -> dict[str, Any]:
    """Continue one honest UNKNOWN Judgment with bounded Investigation.

    Reuses the guarded Phase 2 Judge (or a supplied bundle verified with
    the Phase 2 verifier) as the trigger, requires an UNKNOWN verdict,
    and investigates exactly that World. Non-UNKNOWN triggers refuse with
    ``INVESTIGATION_NOT_APPLICABLE`` and an explicit reason.
    """
    if question_focus is not None and (
        not isinstance(question_focus, str) or not question_focus
    ):
        raise ValueError("question_focus must be a non-empty string or None")
    view, address = open_config_world_view(world)
    try:
        context = {
            "address": address,
            "world_id": view.world.world_id,
            "revision": _revision(view),
            "database_fingerprint": database_fingerprint(address),
        }
        if judgment is None:
            trigger_result = judge_config_world(
                world=address, proposition=proposition, subject=subject
            )
            if trigger_result["outcome"] != "JUDGED":
                return _not_applicable(
                    context, proposition, subject, trigger_result,
                    f"trigger judgment outcome is {trigger_result['outcome']}: "
                    f"{trigger_result.get('reason') or trigger_result.get('errors')}",
                )
            case = trigger_result["case"]
            artifact = trigger_result["artifact"]
        else:
            verification = verify_judgment_bundle(judgment, world=address)
            if not verification["verified"]:
                return _not_applicable(
                    context, proposition, subject, None,
                    "supplied judgment bundle did not verify",
                    verification=verification,
                )
            bundle = judgment if isinstance(judgment, dict) else read_judgment_bundle(judgment)
            request = bundle["request"]
            if request["proposition"] != proposition or request["subject"] != subject:
                return _not_applicable(
                    context, proposition, subject, None,
                    "supplied judgment bundle names a different proposition/subject",
                )
            case = bundle["case"]
            artifact = bundle["artifact"]
            trigger_result = {"outcome": "JUDGED"}
        refusal = _eligibility_refusal(artifact)
        if refusal is not None:
            return _not_applicable(context, proposition, subject, trigger_result, refusal)
        question = _build_question(case, artifact, proposition, subject, question_focus)
        capabilities = {"manifestation-text": lambda name: view.local_manifestation_for_subject(name)}
        try:
            result = investigate_bounded_case(view, case, question, capabilities)
        except InvestigationBoundary as exc:
            return _not_applicable(
                context, proposition, subject, None,
                f"investigation left its bounded contract: {exc}",
            )
        manifested = capabilities["manifestation-text"](subject)
        explanation = _explain(
            view, proposition, subject, artifact, question, result,
            _observed_unasserted_fields(manifested, view.mechanical_facts_for_subject(subject)),
            manifested if isinstance(manifested, dict) else {},
        )
        persisted_to: str | None = None
        if persist_to is not None:
            persisted_to = write_investigation_bundle(
                persist_to,
                world=context,
                request={
                    "proposition": proposition,
                    "subject": subject,
                    "question_focus": question_focus,
                },
                trigger={"case_id": case["case_id"], "artifact": artifact},
                question=question,
                receipt=result["receipt"],
                proposal=result["proposal"],
                case=result["case"],
            )
        return {
            "outcome": result["outcome"],
            "world": context,
            "proposition": proposition,
            "subject": subject,
            "trigger": _trigger_summary(case, artifact),
            "method": {"id": METHOD_ID, "capabilities": ["manifestation-text"]},
            "question": question,
            "receipt": result["receipt"],
            "proposal": result["proposal"],
            "case": result["case"],
            "explanation": explanation,
            "persisted_to": persisted_to,
        }
    finally:
        view.world.close()


def write_investigation_bundle(
    path: Path | str,
    *,
    world: dict[str, Any],
    request: dict[str, Any],
    trigger: dict[str, Any],
    question: dict[str, Any],
    receipt: dict[str, Any],
    proposal: dict[str, Any] | None,
    case: dict[str, Any] | None,
) -> str:
    """Persist one investigation result.

    Exclusive no-clobber creation: an existing path entry (including a
    symlink) is never followed or replaced. No atomic-publish claim is
    made; a truncated file fails verification as a structured negative.
    Investigation artifacts always live outside the sealed World: any
    target resolving to or underneath the World directory is refused
    before any parent directory is created or file opened.
    """
    _reject_inside_world(path, world["address"])
    target = Path(path)
    if os.path.lexists(target):
        raise ValueError(f"investigation bundle address already exists: {target}")
    bundle = {
        "format": INVESTIGATION_BUNDLE_FORMAT,
        "world": {
            "address": world["address"],
            "world_id": world["world_id"],
            "revision": world["revision"],
            "database_fingerprint": world["database_fingerprint"],
        },
        "request": {
            "proposition": request["proposition"],
            "subject": request["subject"],
            "question_focus": request["question_focus"],
        },
        "trigger": {"case_id": trigger["case_id"], "artifact": trigger["artifact"]},
        "question": question,
        "receipt": receipt,
        "proposal": proposal,
        "case": case,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
    try:
        fd = os.open(target, flags, 0o644)
    except FileExistsError:
        raise ValueError(f"investigation bundle address already exists: {target}") from None
    except OSError as exc:
        raise ValueError(f"investigation bundle address is not a fresh file: {target} ({exc})") from None
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    return str(target.resolve())


def read_investigation_bundle(path: Path | str) -> dict[str, Any]:
    """Read one persisted investigation bundle."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _reject_inside_world(path: Path | str, world_address: str) -> None:
    """Refuse any artifact target at or under the sealed World directory."""
    root = Path(world_address).resolve()
    target = Path(path).resolve()
    if target == root or root in target.parents:
        raise ValueError(f"investigation bundle address is inside the sealed World: {path}")


def verify_investigation_bundle(
    bundle: dict[str, Any] | Path | str,
    world: Path | str | None = None,
) -> dict[str, Any]:
    """Re-verify a persisted investigation against its exact sealed World.

    Re-runs the guarded trigger Judgment canonically, requires the same
    UNKNOWN artifact, replays the bounded investigator, and checks that
    every cited addition exists in W0 with successfully reconstructed
    support and that any proposal basis honestly matches the retained
    manifestation. Returns a structured negative report (never raises)
    for malformed, tampered, stale, or mismatched bundles.
    """
    checks: dict[str, bool] = {}
    errors: list[str] = []
    if isinstance(bundle, (Path, str)):
        try:
            loaded = read_investigation_bundle(bundle)
        except (OSError, ValueError) as exc:
            return {
                "verified": False,
                "checks": {"readable": False},
                "errors": [f"cannot parse investigation bundle: {exc}"],
            }
    else:
        loaded = bundle
    checks["readable"] = True
    if not isinstance(loaded, dict) or set(loaded) != _BUNDLE_KEYS:
        return _negative(
            checks, errors, "shape",
            f"invalid bundle shape: required keys {sorted(_BUNDLE_KEYS)}",
        )
    if loaded.get("format") != INVESTIGATION_BUNDLE_FORMAT:
        return _negative(
            checks, errors, "shape",
            f"unknown investigation bundle format {loaded.get('format')!r}",
        )
    recorded_world = loaded["world"]
    request = loaded["request"]
    trigger = loaded["trigger"]
    if (
        not isinstance(recorded_world, dict)
        or set(recorded_world) != _WORLD_KEYS
        or not isinstance(request, dict)
        or set(request) != _REQUEST_KEYS
        or not isinstance(trigger, dict)
        or set(trigger) != _TRIGGER_KEYS
    ):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: world/request/trigger blocks lack required keys",
        )
    world_value_error = _world_block_error(recorded_world)
    if world_value_error is not None:
        return _negative(checks, errors, "shape", world_value_error)
    if (
        not isinstance(request.get("proposition"), str)
        or not request["proposition"]
        or not isinstance(request.get("subject"), str)
        or not request["subject"]
    ):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: request names no proposition/subject strings",
        )
    focus = request["question_focus"]
    if focus is not None and (not isinstance(focus, str) or not focus):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: question focus is not a non-empty string or null",
        )
    if not isinstance(trigger.get("case_id"), str) or not trigger["case_id"]:
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: trigger names no case id string",
        )
    receipt = loaded["receipt"]
    proposal = loaded["proposal"]
    stored_child = loaded["case"]
    if not isinstance(receipt, dict):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: receipt is not a record",
        )
    if receipt.get("outcome") not in OUTCOMES:
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: receipt outcome is not a known outcome",
        )
    if "added_assertion_ids" in receipt and not isinstance(receipt["added_assertion_ids"], list):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: receipt additions are not a list",
        )
    if proposal is not None and not isinstance(proposal, dict):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: proposal is not a record or null",
        )
    if stored_child is not None and not isinstance(stored_child, dict):
        return _negative(
            checks, errors, "shape",
            "invalid bundle shape: expanded case is not a case object or null",
        )
    checks["shape"] = True
    address = str(world) if world is not None else recorded_world["address"]
    try:
        view, opened = open_config_world_view(address)
    except (ValueError, TypeError, OSError) as exc:
        return _negative(checks, errors, "world_readable", str(exc))
    try:
        checks["world_readable"] = True
        checks["exact_address"] = opened == _resolved(recorded_world["address"])
        if not checks["exact_address"]:
            errors.append(
                f"bundle records {recorded_world['address']} but opened {opened}"
            )
        checks["world_id"] = view.world.world_id == recorded_world["world_id"]
        if not checks["world_id"]:
            errors.append("opened publication id differs from the bundle record")
        checks["revision"] = _revision(view) == recorded_world["revision"]
        if not checks["revision"]:
            errors.append("opened publication revision differs from the bundle record")
        checks["database_fingerprint"] = (
            database_fingerprint(opened) == recorded_world["database_fingerprint"]
        )
        if not checks["database_fingerprint"]:
            errors.append("opened database bytes differ from the bundle fingerprint")
        if errors:
            return {"verified": False, "checks": checks, "errors": errors}
        proposition, subject = request["proposition"], request["subject"]
        fresh = judge_config_world(
            world=opened,
            proposition=proposition,
            subject=subject,
            case_id=trigger["case_id"],
        )
        if fresh["outcome"] != "JUDGED":
            return _negative(
                checks, errors, "trigger_valid",
                f"canonical trigger judgment is {fresh['outcome']}, not a JUDGED UNKNOWN",
            )
        if _eligibility_refusal(fresh["artifact"]) is not None:
            return _negative(
                checks, errors, "trigger_valid",
                "canonical trigger judgment is no longer an UNKNOWN verdict",
            )
        if fresh["artifact"] != trigger["artifact"]:
            return _negative(
                checks, errors, "trigger_valid",
                "recorded trigger artifact differs from the canonical judgment",
            )
        checks["trigger_valid"] = True
        question = _build_question(fresh["case"], fresh["artifact"], proposition, subject, focus)
        capabilities = {"manifestation-text": lambda name: view.local_manifestation_for_subject(name)}
        try:
            replayed = investigate_bounded_case(view, fresh["case"], question, capabilities)
        except InvestigationBoundary as exc:
            return _negative(checks, errors, "replay_match", f"replay left its contract: {exc}")
        replay_errors = _replay_mismatch(question, replayed, loaded)
        checks["replay_match"] = replay_errors == []
        errors.extend(replay_errors)
        support_errors = _support_errors(view, subject, focus, loaded)
        checks["support_sound"] = support_errors == []
        errors.extend(support_errors)
        return {"verified": not errors, "checks": checks, "errors": errors}
    finally:
        view.world.close()


def _negative(
    checks: dict[str, bool], errors: list[str], name: str, message: str
) -> dict[str, Any]:
    checks[name] = False
    errors.append(message)
    return {"verified": False, "checks": checks, "errors": errors}


def _not_applicable(
    context: dict[str, Any],
    proposition: str,
    subject: str,
    trigger_result: dict[str, Any] | None,
    reason: str,
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "outcome": "INVESTIGATION_NOT_APPLICABLE",
        "world": context,
        "proposition": proposition,
        "subject": subject,
        "reason": reason,
    }
    if trigger_result is not None:
        result["trigger_outcome"] = trigger_result["outcome"]
    if verification is not None:
        result["trigger_verification"] = verification
    return result


def _eligibility_refusal(artifact: dict[str, Any]) -> str | None:
    """Refuse every trigger that is not an evaluator-produced UNKNOWN."""
    applicability = artifact["applicability"]["result"]
    conformance = artifact["conformance"]
    if applicability == "UNKNOWN":
        return None
    if (
        applicability == "APPLIES"
        and conformance is not None
        and conformance.get("result") == "UNKNOWN"
    ):
        return None
    observed = None if conformance is None else conformance.get("result")
    return (
        f"trigger judgment is {applicability}/{observed}: "
        "investigation continues only from an UNKNOWN verdict, never from "
        "APPLIES with a decided conformance, DOES_NOT_APPLY, or a refused judgment"
    )


def _trigger_summary(case: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    conformance = artifact["conformance"]
    return {
        "outcome": "JUDGED",
        "case_id": case["case_id"],
        "applicability": artifact["applicability"]["result"],
        "applicability_because": artifact["applicability"].get("because", ""),
        "conformance": None if conformance is None else conformance["result"],
        "conformance_because": "" if conformance is None else conformance.get("because", ""),
        "method": {
            "id": artifact["method"]["id"],
            "version": artifact["method"]["version"],
            "fingerprint": artifact["method"]["fingerprint"],
        },
        "context_requests": list(artifact["context_requests"]),
    }


def _build_question(
    case: dict[str, Any],
    artifact: dict[str, Any],
    proposition: str,
    subject: str,
    focus: str | None,
) -> dict[str, Any]:
    requests = artifact.get("context_requests") or []
    chosen = dict(requests[0]) if requests else None
    if focus is not None:
        structured: dict[str, str] | None = {"need": "subject_property", "property": focus}
    elif chosen is not None and chosen.get("need") == "subject_property" and chosen.get("property"):
        structured = {"need": str(chosen["need"]), "property": str(chosen["property"])}
    elif chosen is not None:
        structured = {"need": str(chosen.get("need") or "established_binding"), "property": ""}
    else:
        structured = None
    origin: dict[str, Any] = {
        "case_id": case["case_id"],
        "kind": "judgment_request" if chosen is not None else "open",
    }
    if chosen is not None:
        origin["request"] = chosen
    if chosen is not None and chosen.get("gap") == "construction":
        text = "Which established correspondence, if any, resolves this proposition for this subject?"
    elif chosen is not None:
        text = "Which recorded subject property value answers the judgment request?"
    else:
        text = (
            "Why does no established correspondence resolve this proposition "
            "for this subject under incomplete coverage?"
        )
    question_id = case["case_id"] + "::investigation" + (f"::{focus}" if focus else "")
    return make_question(
        question_id=question_id,
        question=text,
        purpose="continue an honest UNKNOWN with verified same-World material, or explain what is missing",
        proposition=proposition,
        subject=subject,
        origin=origin,
        structured_need=structured,
    )


def _explain(
    view: GovernanceView,
    proposition: str,
    subject: str,
    artifact: dict[str, Any],
    question: dict[str, Any],
    result: dict[str, Any],
    observed_fields: list[str],
    manifested: dict[str, Any],
) -> dict[str, Any]:
    detail = view.binding_candidates_for_proposition(proposition)
    conformance = artifact["conformance"]
    outcome = result["outcome"]
    if outcome == "PROPOSAL":
        field = result["proposal"]["payload"]["field"]
        missing = f"a published assertion for subject property {field!r}"
        why = (
            "the producer does not assert this field; reconstructed "
            "manifestation text is not an assertion"
        )
    elif outcome == "CASE_EXPANDED":
        added = len(result["receipt"]["added_assertion_ids"])
        missing = "verified same-World citations absent from the trigger case"
        why = f"{added} verified assertion(s) from the same publication were added to the case"
    else:
        missing = (
            f"an established governance_binding({proposition}, {subject}) or another "
            "published assertion answering the question"
        )
        status = manifested.get("status", "UNKNOWN")
        if status != "OK":
            why = (
                "the subject manifestation did not reconstruct "
                f"(status {status}); damaged evidence is reported, never treated "
                "as epistemic absence"
            )
        elif observed_fields:
            why = (
                "every published mechanical fact for the subject is already "
                "cited by the canonical case; the manifestation carries "
                f"unasserted fields {observed_fields} that the question did not "
                "ask about, so none became a proposal"
            )
        else:
            why = (
                "every published mechanical fact for the subject is already "
                "cited by the canonical case and the manifestation carries no "
                "further unasserted field; coverage is INCOMPLETE so absence "
                "decides nothing"
            )
    return {
        "trigger": {
            "applicability": artifact["applicability"]["result"],
            "applicability_because": artifact["applicability"].get("because", ""),
            "conformance": None if conformance is None else conformance["result"],
            "conformance_because": "" if conformance is None else conformance.get("because", ""),
        },
        "question_id": question["question_id"],
        "outcome": outcome,
        "established_subjects_for_proposition": detail["established_subjects"],
        "bound_propositions_for_subject": view.propositions_for_subject(subject),
        "candidate_subjects_for_proposition": sorted(
            str(item["software_subject"]) for item in detail["candidates"]
        ),
        "open_questions_for_proposition": detail["questions"],
        "coverage": view.completeness(),
        "inspected_relations": result["receipt"]["inspected_relations"],
        "manifestation_status": manifested.get("status", "UNKNOWN"),
        "observed_unasserted_fields": observed_fields,
        "missing": missing,
        "why": why,
    }


def _replay_mismatch(
    question: dict[str, Any], replayed: dict[str, Any], stored: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if question != stored["question"]:
        errors.append("stored investigation question differs from the canonical question")
    if replayed["outcome"] != stored["receipt"].get("outcome"):
        errors.append("stored receipt outcome differs from replay")
    if replayed["receipt"] != stored["receipt"]:
        errors.append("stored receipt differs from replay")
    if replayed["proposal"] != stored["proposal"]:
        errors.append("stored proposal differs from replay")
    child = replayed["case"]
    stored_child = stored["case"]
    if (child is None) != (stored_child is None):
        errors.append("stored expanded case presence differs from replay")
    elif child is not None and stored_child is not None:
        for field in ("world_id", "revision", "case_id", "question", "proposition_ids", "subject_ids", "world_address"):
            if stored_child.get(field) != child.get(field):
                errors.append(f"stored expanded case {field} differs from replay")
        if set(stored_child) != set(child):
            errors.append("stored expanded case fields differ from replay")
        if stored_child.get("inspected_relations") != child.get("inspected_relations"):
            errors.append("stored expanded case inspected relations differ from replay")
        if _sorted_facts(stored_child) != _sorted_facts(child):
            errors.append("stored expanded case facts differ from replay")
    return errors


def _sorted_facts(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts")
    if not isinstance(facts, list):
        return []
    rendered = []
    for fact in facts:
        if isinstance(fact, dict):
            rendered.append(json.dumps(fact, sort_keys=True))
    return sorted(rendered)


def _support_errors(
    view: GovernanceView, subject: str, focus: str | None, stored: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    child = stored["case"]
    if child is not None:
        if not isinstance(child, dict):
            return ["stored expanded case is not a case object"]
        if not isinstance(child.get("facts"), list):
            errors.append("stored expanded case facts are not a fact list")
        else:
            try:
                citation_errors = verify_case(view, child)
            except (KeyError, TypeError, AttributeError) as exc:
                errors.append(f"stored expanded case citations could not be inspected: {exc}")
            else:
                if citation_errors:
                    errors.append("stored expanded case citations do not verify: " + "; ".join(citation_errors))
            try:
                broken = _broken_evidence(child)
            except (KeyError, TypeError, AttributeError):
                errors.append("stored expanded case support could not be inspected")
            else:
                if broken:
                    errors.append("stored expanded case relies on support that failed to reconstruct")
    proposal = stored["proposal"]
    if proposal is not None:
        errors.extend(_proposal_basis_errors(view, subject, focus, proposal))
    return errors


def _proposal_basis_errors(
    view: GovernanceView, subject: str, focus: str | None, proposal: dict[str, Any]
) -> list[str]:
    """Prove the stored proposal is the exact focused parsed value.

    Uses the same bounded extraction as selection: top-level scalar of
    the parsed retained manifestation under the recorded focus. A real
    value under the wrong field, or a wrong value under the right field,
    fails here — not only in replay.
    """
    if not isinstance(proposal, dict):
        return ["stored proposal is not a proposal record"]
    payload = proposal.get("payload")
    basis = proposal.get("basis")
    if not isinstance(payload, dict) or not isinstance(basis, dict):
        return ["stored proposal lacks a payload/basis record"]
    if "assertion_id" in payload or "assertion_id" in basis:
        return ["stored proposal claims an assertion id"]
    field = payload.get("field")
    value = payload.get("value")
    if not isinstance(field, str) or not field:
        return ["stored proposal names no field string"]
    if field in RESERVED_PROPOSAL_FIELDS:
        return ["stored proposal uses a reserved identity field name"]
    if focus is None:
        return ["stored proposal has no recorded focus"]
    if field != focus:
        return ["stored proposal field differs from the recorded focus"]
    if not _is_supported_value(value):
        return ["stored proposal value is outside the supported scalar scope"]
    manifested = view.local_manifestation_for_subject(subject)
    if not isinstance(manifested, dict) or manifested.get("status") != "OK":
        return ["proposal basis manifestation does not reconstruct OK"]
    for name in ("scheme", "location", "content_digest"):
        if basis.get(name) != manifested.get(name):
            return ["stored proposal basis differs from the retained manifestation"]
    if basis.get("text") != manifested.get("content"):
        return ["stored proposal basis differs from the retained manifestation"]
    extras = dict(_manifested_extras(manifested, view.mechanical_facts_for_subject(subject)))
    if field not in extras or extras[field] != value or not _is_supported_value(extras[field]):
        return ["stored proposal payload is not the parsed manifestation value"]
    return []


def _observed_unasserted_fields(
    manifested: dict[str, Any], mechanical: list[dict[str, Any]]
) -> list[str]:
    return sorted(key for key, _value in _manifested_extras(manifested, mechanical))


def _manifested_extras(
    manifested: dict[str, Any], mechanical: list[dict[str, Any]]
) -> list[tuple[str, Any]]:
    if not isinstance(manifested, dict) or manifested.get("status") != "OK":
        return []
    try:
        payload = json.loads(str(manifested["content"]))
    except (ValueError, TypeError):
        return []
    if not isinstance(payload, dict):
        return []
    sealed_fields = {key for item in mechanical for key in item["values"]}
    return [
        (str(key), value)
        for key, value in payload.items()
        if key not in PUBLISHED_SOURCE_KEYS and key not in sealed_fields
    ]


def _unpublished(
    subject: str,
    mechanical: list[dict[str, Any]],
    question: dict[str, Any],
    capabilities: dict[str, Callable[..., Any]],
    inspected: list[str],
) -> dict[str, Any] | None:
    """Return the exact named extra field, or nothing.

    Only the property named by ``structured_need`` may be selected, and
    only as a top-level scalar of the parsed manifestation. No
    question-text matching: prose explains the investigation, it never
    licenses a field.
    """
    reader = capabilities.get("manifestation-text")
    if reader is None:
        return None
    manifested = reader(subject)
    inspected.append("software_manifestation")
    if not isinstance(manifested, dict) or manifested.get("status") != "OK":
        return None
    need = question.get("structured_need") or {}
    wanted = need.get("property")
    if not isinstance(wanted, str) or not wanted:
        return None
    if wanted in RESERVED_PROPOSAL_FIELDS:
        return None
    for key, value in _manifested_extras(manifested, mechanical):
        if key == wanted and _is_supported_value(value):
            return {
                "field": key,
                "value": value,
                "content_digest": str(manifested.get("content_digest") or ""),
                "scheme": str(manifested.get("scheme") or ""),
                "location": str(manifested.get("location") or ""),
                "text": str(manifested["content"]),
            }
    return None


def _is_supported_value(value: Any) -> bool:
    """JSON scalars (finite numbers) are proposable; arrays/objects are not."""
    if value is None or isinstance(value, (str, bool, int)):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _proposal(
    case: dict[str, Any],
    question: dict[str, Any],
    discovered: dict[str, Any],
) -> dict[str, Any]:
    return make_proposal(
        proposal_id=f"proposal:{question['question_id']}",
        originating_case_id=str(case["case_id"]),
        originating_question_id=str(question["question_id"]),
        epistemic_class="mechanical",
        payload={"field": discovered["field"], "value": discovered["value"]},
        basis={
            "kind": "reconstructed-manifestation",
            "scheme": discovered["scheme"],
            "location": discovered["location"],
            "content_digest": discovered["content_digest"],
            "text": discovered["text"],
        },
        method={"id": METHOD_ID, "capability": "manifestation-text"},
        reason=(
            "the sealed world has no assertion for this field; "
            "reconstructed source text is not an assertion"
        ),
    )


def _case_has(case: dict[str, Any], item: dict[str, Any]) -> bool:
    values = {str(key): str(value) for key, value in item["values"].items()}
    return any(
        fact["relation"] == item["relation"] and fact["values"] == values
        for fact in case["facts"]
    )

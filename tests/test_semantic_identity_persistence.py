"""Historical experiment: when a semantic identity adds a read.

Excluded from the default gate. Run with `pytest -m historical`.

Experimental representations only. Equivalence across wording and software
replacement is an explicit constructor decision, not a comparison result.
No spine, core, checkout, payment, or design vocabulary is involved.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding, SourceObservation
from ontology_author.world.runtime.world import ConstructionWorld

pytestmark = pytest.mark.historical

POLICY = """\
# Mail policy

Outbound email must pass through NotificationGateway.

Receipt notices and customer mail must both pass through NotificationGateway.

Operational alerts must leave through an approved mailer.

The weekly digest sender is digestMail.
"""

POLICY_REWORD = """\
# Mail policy

Outbound email must go via NotificationGateway.
"""

RUNBOOK = """\
# Operations

Customer messages may leave only through the notification gateway.
"""

REPLACEMENT = """\
# Operations

Notices leave only through the notice hub.
"""

SOFTWARE_S0 = """\
export function sendCustomerMail(body: string): string {
  return gatewayDeliver(body);
}
export function gatewayDeliver(body: string): string {
  return body;
}
export function receiptMail(body: string): string {
  return gatewayDeliver(body);
}
export function digestMail(body: string): string {
  return body;
}
export function smtpSend(body: string): string {
  return body;
}
"""

SOFTWARE_S1 = """\
export function dispatchNotice(body: string): string {
  return noticeHub(body);
}
export function noticeHub(body: string): string {
  return body;
}
"""

RULE = "semantic:outbound-mail-rule"
GATEWAY = "semantic:notification-gateway"
DIGEST = "semantic:weekly-digest"
MAILER = "semantic:approved-mailer"


def _write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _markdown(path: Path, root: Path) -> MarkdownSource:
    return MarkdownSource.from_path(path, workspace=root)


def _paragraph(source: MarkdownSource, needle: str) -> tuple[SourceObservation, str]:
    matches = []
    for region in source.paragraphs():
        text = source.reconstruct(region).strip()
        if needle in text:
            matches.append((source.observe(region), text))
    assert len(matches) == 1, (needle, matches)
    return matches[0]


def _software(path: Path, handle: str, declaration: str) -> tuple[str, SourceObservation]:
    data = path.read_bytes()
    needle = f"function {declaration}".encode("utf-8")
    start = data.find(needle)
    assert start >= 0, declaration
    referent = "software:" + handle.removesuffix(".ts") + ":" + declaration
    return referent, SourceObservation(
        provider="software-fixture",
        native_handle=handle,
        source_revision="sha256:" + hashlib.sha256(data).hexdigest(),
        native_location=f"bytes:{start}:{start + len(needle)}",
    )


def _ground(*observations: SourceObservation, method: str, support: str, resolution: dict[str, str], equivalence: str):
    return AssertionGrounding(
        observations,
        construction_method=method,
        extra={
            "relation_support": support,
            "endpoint_resolution": resolution,
            "equivalence": equivalence,
        },
    )


def _open(path: Path) -> ConstructionWorld:
    world = ConstructionWorld.create(path, world_id="semantic-identity-experiment")
    referent = RoleType.REFERENT
    text = RoleType.TEXT
    world.declare_relation(
        "software_subject",
        [Role("subject", referent), Role("snapshot", text), Role("label", text)],
        description="Experimental software subject. Not a semantic identity.",
    )
    world.declare_relation(
        "direct_constraint",
        [Role("entry", referent), Role("gateway", referent)],
        description="Authoritative evidence bound directly to two software subjects.",
    )
    world.declare_relation(
        "direct_names",
        [Role("subject", referent)],
        description="One authoritative statement naming one software subject.",
    )
    world.declare_relation(
        "unresolved_candidate",
        [Role("evidence_address", text), Role("candidate", referent), Role("role", text)],
        description="Ambiguous software candidate. The evidence address is not a semantic identity.",
    )
    world.declare_relation(
        "semantic_subject",
        [Role("subject", referent)],
        description="Durable semantic identity under test.",
    )
    world.declare_relation(
        "evidence_concerns",
        [Role("subject", referent)],
        description="Authoritative evidence attached to a semantic identity.",
    )
    world.declare_relation(
        "realizes",
        [Role("subject", referent), Role("software", referent), Role("role", text), Role("resolution", text)],
        description="Semantic-to-software binding. Resolution is not support.",
    )
    return world


def _assert(world: ConstructionWorld, relation: str, values: dict, grounding: AssertionGrounding, *, semantic: bool):
    return world.assert_tuple(
        relation,
        values,
        origin=ConstructionOrigin.SEMANTIC if semantic else ConstructionOrigin.MECHANICAL,
        grounding=grounding,
    )


def _detail(base: dict) -> dict:
    detail = base["detail"]
    return json.loads(detail) if isinstance(detail, str) else detail


def _source_bases(world: ConstructionWorld, assertion_id: str) -> list[dict]:
    bases = []
    for base in world.warrant_for_assertion(assertion_id)["bases"]:
        if base.get("kind") != "SOURCE":
            continue
        bases.append(_detail(base))
    return bases


def _extras(world: ConstructionWorld, assertion_id: str) -> list[dict]:
    found = []
    for base in world.warrant_for_assertion(assertion_id)["bases"]:
        if base.get("kind") != "WORLD":
            continue
        detail = _detail(base)
        if "extra" in detail:
            found.append(detail["extra"])
    return found


def _address(observation: SourceObservation) -> str:
    return f"{observation.native_handle}@{observation.source_revision}/{observation.native_location}"


def _build(root: Path) -> dict[str, ConstructionWorld]:
    policy = _markdown(_write(root, "policy.md", POLICY), root)
    reword = _markdown(_write(root, "policy-reword.md", POLICY_REWORD), root)
    runbook = _markdown(_write(root, "runbook.md", RUNBOOK), root)
    replacement = _markdown(_write(root, "replacement.md", REPLACEMENT), root)
    software_s0 = _write(root, "mail-s0.ts", SOFTWARE_S0)
    software_s1 = _write(root, "mail-s1.ts", SOFTWARE_S1)

    original, _ = _paragraph(policy, "Outbound email must pass through")
    both, _ = _paragraph(policy, "Receipt notices and customer mail")
    alerts, alert_text = _paragraph(policy, "Operational alerts")
    digest, _ = _paragraph(policy, "weekly digest sender")
    reworded, _ = _paragraph(reword, "must go via")
    second_source, _ = _paragraph(runbook, "notification gateway")
    replaced_wording, _ = _paragraph(replacement, "notice hub")

    send, send_obs = _software(software_s0, "mail-s0.ts", "sendCustomerMail")
    gateway, gateway_obs = _software(software_s0, "mail-s0.ts", "gatewayDeliver")
    receipt, receipt_obs = _software(software_s0, "mail-s0.ts", "receiptMail")
    digest_fn, digest_obs = _software(software_s0, "mail-s0.ts", "digestMail")
    smtp, smtp_obs = _software(software_s0, "mail-s0.ts", "smtpSend")
    dispatch, dispatch_obs = _software(software_s1, "mail-s1.ts", "dispatchNotice")
    hub, hub_obs = _software(software_s1, "mail-s1.ts", "noticeHub")
    subjects = {
        send: ("s0", "sendCustomerMail", send_obs),
        gateway: ("s0", "gatewayDeliver", gateway_obs),
        receipt: ("s0", "receiptMail", receipt_obs),
        digest_fn: ("s0", "digestMail", digest_obs),
        smtp: ("s0", "smtpSend", smtp_obs),
        dispatch: ("s1", "dispatchNotice", dispatch_obs),
        hub: ("s1", "noticeHub", hub_obs),
    }

    direct = _open(root / "direct.sqlite")
    mediated = _open(root / "mediated.sqlite")
    for world in (direct, mediated):
        for referent, (snapshot, label, observation) in subjects.items():
            world.add_referent(referent, label=label, observations=(observation,))
            _assert(
                world,
                "software_subject",
                {"subject": referent, "snapshot": snapshot, "label": label},
                _ground(observation, method="experimental declaration span", support="SOURCE_NATIVE", resolution={"subject": "SOURCE_DEFINED"}, equivalence="not-applicable"),
                semantic=False,
            )

    def bind_direct(entry: str, gateway_subject: str, *observations: SourceObservation, resolution: dict[str, str], equivalence: str):
        entry_obs = subjects[entry][2]
        gateway_observation = subjects[gateway_subject][2]
        return _assert(
            direct,
            "direct_constraint",
            {"entry": entry, "gateway": gateway_subject},
            _ground(
                *observations,
                entry_obs,
                gateway_observation,
                method="direct evidence to software subjects",
                support="SOURCE_EXPLICIT",
                resolution=resolution,
                equivalence=equivalence,
            ),
            semantic=True,
        )

    original_binding = bind_direct(
        send, gateway, original,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="not-applicable",
    )
    bind_direct(
        send, gateway, reworded,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="not-applicable",
    )
    bind_direct(
        send, gateway, second_source,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="not-applicable",
    )
    both_customer = bind_direct(
        send, gateway, both,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="not-applicable",
    )
    both_receipt = bind_direct(
        receipt, gateway, both,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="not-applicable",
    )
    replaced_entry = bind_direct(
        dispatch, gateway, original,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="experimental-entry-replacement",
    )
    replaced_both = bind_direct(
        dispatch, hub, replaced_wording,
        resolution={"entry": "AGENT_RESOLVED", "gateway": "AGENT_RESOLVED"},
        equivalence="experimental-rule-equivalence",
    )
    digest_binding = _assert(
        direct,
        "direct_names",
        {"subject": digest_fn},
        _ground(
            digest, subjects[digest_fn][2],
            method="direct evidence to the named software subject",
            support="SOURCE_EXPLICIT",
            resolution={"subject": "DETERMINISTIC"},
            equivalence="not-applicable",
        ),
        semantic=True,
    )
    assert subjects[digest_fn][1] == "digestMail"

    ambiguity = []
    for candidate, observation in ((gateway, gateway_obs), (smtp, smtp_obs)):
        ambiguity.append(_assert(
            direct,
            "unresolved_candidate",
            {"evidence_address": _address(alerts), "candidate": candidate, "role": "mailer"},
            _ground(
                alerts, observation,
                method="direct ambiguous endpoint",
                support="SOURCE_EXPLICIT",
                resolution={"mailer": "AMBIGUOUS"},
                equivalence="not-applicable",
            ),
            semantic=True,
        ))

    def concern(semantic: str, *observations: SourceObservation, equivalence: str):
        mediated.add_referent(semantic, label=semantic)
        _assert(
            mediated,
            "semantic_subject",
            {"subject": semantic},
            _ground(*observations, method="semantic identity introduction", support="SOURCE_EXPLICIT", resolution={}, equivalence=equivalence),
            semantic=True,
        )
        return _assert(
            mediated,
            "evidence_concerns",
            {"subject": semantic},
            _ground(*observations, method="evidence to semantic identity", support="SOURCE_EXPLICIT", resolution={}, equivalence=equivalence),
            semantic=True,
        )

    def realize(semantic: str, software: str, role: str, resolution: str, *observations: SourceObservation, equivalence: str):
        return _assert(
            mediated,
            "realizes",
            {"subject": semantic, "software": software, "role": role, "resolution": resolution},
            _ground(
                *observations, subjects[software][2],
                method="semantic identity to software subject",
                support="SOURCE_EXPLICIT",
                resolution={role: resolution},
                equivalence=equivalence,
            ),
            semantic=True,
        )

    rule_concern = concern(RULE, original, reworded, second_source, replaced_wording, equivalence="experimental-rule-equivalence")
    realize(RULE, send, "entry", "AGENT_RESOLVED", original, equivalence="not-applicable")
    realize(RULE, gateway, "gateway", "AGENT_RESOLVED", original, equivalence="not-applicable")
    realize(RULE, dispatch, "entry", "AGENT_RESOLVED", replaced_wording, equivalence="experimental-rule-equivalence")
    realize(RULE, hub, "gateway", "AGENT_RESOLVED", replaced_wording, equivalence="experimental-rule-equivalence")
    concern(GATEWAY, original, second_source, equivalence="duplicates-rule-role")
    realize(GATEWAY, gateway, "gateway", "AGENT_RESOLVED", original, equivalence="duplicates-rule-role")
    realize(GATEWAY, hub, "gateway", "AGENT_RESOLVED", replaced_wording, equivalence="duplicates-rule-role")
    concern(DIGEST, digest, equivalence="not-applicable")
    realize(DIGEST, digest_fn, "sender", "DETERMINISTIC", digest, equivalence="not-applicable")
    concern(MAILER, alerts, equivalence="not-applicable")
    realize(MAILER, gateway, "mailer", "AMBIGUOUS", alerts, equivalence="not-applicable")
    realize(MAILER, smtp, "mailer", "AMBIGUOUS", alerts, equivalence="not-applicable")

    assert "NotificationGateway" not in {label for _snapshot, label, _obs in subjects.values()}
    assert alert_text == "Operational alerts must leave through an approved mailer."
    return {
        "direct": direct,
        "mediated": mediated,
        "ids": {
            "send": send,
            "gateway": gateway,
            "receipt": receipt,
            "digest": digest_fn,
            "smtp": smtp,
            "dispatch": dispatch,
            "hub": hub,
            "original": original_binding.assertion_id,
            "both_customer": both_customer.assertion_id,
            "both_receipt": both_receipt.assertion_id,
            "replaced_entry": replaced_entry.assertion_id,
            "replaced_both": replaced_both.assertion_id,
            "digest_binding": digest_binding.assertion_id,
            "alerts": _address(alerts),
            "rule_concern": rule_concern.assertion_id,
            "ambiguity": [item.assertion_id for item in ambiguity],
        },
    }


def _direct_rows(world: ConstructionWorld) -> list[dict]:
    return world.relation_rows("direct_constraint")


def _observations_of(world: ConstructionWorld, assertion_id: str) -> set[tuple[str, str]]:
    return {(item["native_handle"], item["native_location"]) for item in _source_bases(world, assertion_id)}


def test_semantic_identity_earns_persistence_only_for_a_cross_replacement_join(tmp_path: Path) -> None:
    built = _build(tmp_path)
    direct = built["direct"]
    mediated = built["mediated"]
    ids = built["ids"]
    try:
        originals = [row for row in _direct_rows(direct) if row["entry"] == ids["send"] and row["gateway"] == ids["gateway"]]
        assert len(originals) == 1
        original_id = ids["original"]
        original_handles = {handle for handle, _location in _observations_of(direct, original_id)}
        assert {"policy.md", "policy-reword.md", "runbook.md"} <= original_handles

        # A and D. Rewording and a second source share software endpoints.
        # The direct tuple is the join. No semantic identity is required.
        assert len(_observations_of(direct, original_id)) >= 3

        # E. One statement, two entries, shared evidence address.
        customer_obs = _observations_of(direct, ids["both_customer"])
        receipt_obs = _observations_of(direct, ids["both_receipt"])
        assert customer_obs & receipt_obs
        assert {row["entry"] for row in _direct_rows(direct) if row["gateway"] == ids["gateway"]} >= {ids["send"], ids["receipt"]}

        # B. Entry replacement keeps the original observation and the gateway.
        entry_handles = {handle for handle, _location in _observations_of(direct, ids["replaced_entry"])}
        assert "policy.md" in entry_handles
        replaced_entry = next(row for row in _direct_rows(direct) if row["entry"] == ids["dispatch"] and row["gateway"] == ids["gateway"])
        assert replaced_entry["gateway"] == ids["gateway"]

        # C. Wording and both software endpoints are new. Direct claims share nothing.
        total = next(row for row in _direct_rows(direct) if row["entry"] == ids["dispatch"] and row["gateway"] == ids["hub"])
        total_id = ids["replaced_both"]
        assert _observations_of(direct, total_id).isdisjoint(_observations_of(direct, original_id))
        assert {total["entry"], total["gateway"]}.isdisjoint({originals[0]["entry"], originals[0]["gateway"]})

        # F. The named function is one direct subject. Its resolution is deterministic.
        digest_rows = direct.relation_rows("direct_names")
        assert digest_rows == [{"subject": ids["digest"]}]
        assert _extras(direct, ids["digest_binding"])[0]["endpoint_resolution"] == {"subject": "DETERMINISTIC"}
        assert _extras(direct, ids["digest_binding"])[0]["relation_support"] == "SOURCE_EXPLICIT"

        # Ambiguity stays two candidates. Support and resolution stay separate.
        candidates = [row for row in direct.relation_rows("unresolved_candidate") if row["evidence_address"] == ids["alerts"]]
        assert {row["candidate"] for row in candidates} == {ids["gateway"], ids["smtp"]}
        assert ids["smtp"] not in {endpoint for row in _direct_rows(direct) for endpoint in (row["entry"], row["gateway"])}
        for assertion_id in ids["ambiguity"]:
            extra = _extras(direct, assertion_id)[0]
            assert extra["relation_support"] == "SOURCE_EXPLICIT"
            assert extra["endpoint_resolution"] == {"mailer": "AMBIGUOUS"}

        mediated_realizations = mediated.relation_rows("realizes")
        ambiguous = [row for row in mediated_realizations if row["subject"] == MAILER]
        assert {row["resolution"] for row in ambiguous} == {"AMBIGUOUS"}
        assert {row["software"] for row in ambiguous} == {ids["gateway"], ids["smtp"]}
        assert not [row for row in mediated_realizations if row["subject"] == MAILER and row["resolution"] != "AMBIGUOUS"]

        rule_software = {row["software"] for row in mediated_realizations if row["subject"] == RULE}
        assert rule_software == {ids["send"], ids["gateway"], ids["dispatch"], ids["hub"]}
        rule_sources = {handle for handle, _location in _observations_of(mediated, ids["rule_concern"])}
        assert {"policy.md", "policy-reword.md", "runbook.md", "replacement.md"} <= rule_sources

        # The gateway identity only repeats the rule's gateway role.
        gateway_software = [row for row in mediated_realizations if row["subject"] == GATEWAY]
        rule_gateways = [row for row in mediated_realizations if row["subject"] == RULE and row["role"] == "gateway"]
        assert {row["software"] for row in gateway_software} == {row["software"] for row in rule_gateways}

        digest_semantics = [row for row in mediated_realizations if row["subject"] == DIGEST]
        assert digest_semantics == [{
            "subject": DIGEST,
            "software": ids["digest"],
            "role": "sender",
            "resolution": "DETERMINISTIC",
        }]

        semantic_ids = {row["subject"] for row in mediated.relation_rows("semantic_subject")}
        software_ids = {row["subject"] for row in mediated.relation_rows("software_subject")}
        assert semantic_ids.isdisjoint(software_ids)
        assert "NotificationGateway" not in semantic_ids
        assert direct.relation_rows("semantic_subject") == []

        # Removing the one-off, gateway-duplicate, and ambiguous semantic rows
        # leaves every direct answer in place. Removing the rule identity leaves
        # control C with no shared evidence address and no shared software id.
        direct_answers = {
            "wording_and_second_source": original_handles,
            "two_manifestations": customer_obs & receipt_obs,
            "entry_replacement_gateway": replaced_entry["gateway"],
            "digest_subject": digest_rows[0]["subject"],
            "ambiguous_candidates": {row["candidate"] for row in candidates},
        }
        assert direct_answers["ambiguous_candidates"] == {ids["gateway"], ids["smtp"]}
        assert _observations_of(direct, total_id).isdisjoint(_observations_of(direct, original_id))
    finally:
        direct.close()
        mediated.close()

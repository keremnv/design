"""One human-authored semantic construction over three mechanical adapters.

The interpretation convention is intentionally bounded and inspectable:
requirement prose names an operation and boundary; the production manifest
supplies candidate implementations; declarations confirm source endpoints.
Two matches remain candidates, never an arbitrary selected realization.
"""

from __future__ import annotations

import json
import re

from ontology_author.world.core.model import Completeness, CompletenessStatus, RelationMode, Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding
from profiles.core_v1.evidence import retain_bytes, sources


def construct(source, world):
    prose, program, configuration = sources(source.root)
    bundle = world.path.parent
    retain_bytes(bundle, prose.data)
    program.retain(bundle)
    configuration.retain(bundle)
    (bundle / "evidence.manifest.json").write_text(json.dumps({
        "sources": [
            {"handle": item.handle, "revision": item.revision,
             "known_losses": list(item.known_losses() if callable(item.known_losses) else item.known_losses)}
            for item in (prose, program, configuration)
        ],
        "reconstruction": "evidence/<SHA-256>; digest-checked UTF-8 byte spans",
        "interpretation": "human-authored bounded requirement/manifest/declaration join",
    }, indent=2) + "\n", encoding="utf-8")

    def declare(name, roles, description, *, derived=False):
        world.declare_relation(name, [Role(role, kind) for role, kind in roles],
                               description=description,
                               mode=RelationMode.DERIVED if derived else RelationMode.BASE)

    def assert_fact(name, values, observations, method, *, semantic=False):
        return world.assert_tuple(name, values,
            origin=ConstructionOrigin.SEMANTIC if semantic else ConstructionOrigin.MECHANICAL,
            grounding=AssertionGrounding(tuple(observations), construction_method=method))

    ref, text = RoleType.REFERENT, RoleType.TEXT
    declare("program_callable", [("program", ref), ("name", text)], "Observed top-level Python declarations; no runtime identity claim.")
    declare("direct_call", [("caller", ref), ("callee", ref)], "Direct return-call syntax between uniquely named local declarations only.")
    declare("deployment", [("deployment", ref), ("environment", text), ("operation", text),
            ("entrypoint", text), ("boundary_name", text), ("implementation", text), ("provider", ref)],
            "All records in the supplied deployment manifest; not an inventory of external runtime state.")
    declare("requirement", [("requirement", ref), ("statement", text), ("operation", text), ("boundary", ref)],
            "Human-authored interpretation of the bounded requirement prose.")
    declare("realized_by", [("boundary", ref), ("program", ref)], "Uniquely established boundary realization within supplied production evidence.")
    declare("governs", [("requirement", ref), ("program", ref), ("provider", ref)],
            "Requirement governs a production entrypoint/provider, joined through boundary configuration and program declarations.")
    declare("candidate_realization", [("requirement", ref), ("boundary", ref), ("program", ref)],
            "Possible cross-source matches; these tuples do not establish a realization.")
    declare("open_question", [("requirement", ref), ("question", text), ("status", text), ("reason", text)],
            "Explicit unresolved interpretation questions; unresolved does not mean false.")

    declarations = {}
    for item in program.declarations():
        name = item.values["name"]
        if name in declarations:
            raise ValueError("fixture requires unique top-level declaration names")
        declarations[name] = item
        world.add_referent("program:" + name, label=name, observations=(item.observation,))
        assert_fact("program_callable", {"program": "program:" + name, "name": name},
                    [item.observation], "Python AST top-level declaration projection")
    for item in program.direct_calls():
        caller, callee = item.values["caller"], item.values["callee"]
        if caller in declarations and callee in declarations:
            assert_fact("direct_call", {"caller": "program:" + caller, "callee": "program:" + callee},
                        [item.observation, declarations[callee].observation], "Unique local-name join over direct return-call syntax")

    records = configuration.records()
    seen_deployments = set()
    for item in records:
        row = item.values
        if row["deployment"] in seen_deployments:
            raise ValueError("duplicate deployment identity")
        seen_deployments.add(row["deployment"])
        world.add_referent("deployment:" + row["deployment"], label=row["deployment"], observations=(item.observation,))
        world.add_referent("provider:" + row["provider"], label=row["provider"], observations=(item.observation,))
        assert_fact("deployment", {
            "deployment": "deployment:" + row["deployment"], "environment": row["environment"],
            "operation": row["operation"], "entrypoint": row["entrypoint"], "boundary_name": row["boundary"],
            "implementation": row["implementation"], "provider": "provider:" + row["provider"],
        }, [item.observation], "CSV record projection; provider keys are manifest identifiers")

    for paragraph in prose.paragraphs():
        statement = prose.reconstruct(paragraph)
        match = re.fullmatch(
            r'(R-[A-Z]+): Production (\w+)(?: payments)? must use the approved boundary "([^"]+)"\.(?:\s.*)?',
            statement.strip(), re.DOTALL,
        )
        if match is None:
            raise ValueError("requirement outside the declared interpretation convention")
        key, operation, boundary_name = match.groups()
        requirement, boundary = "requirement:" + key, "boundary:" + boundary_name
        observation = prose.observe(paragraph)
        world.add_referent(requirement, label=key, observations=(observation,))
        world.add_referent(boundary, label=boundary_name, observations=(observation,))
        assert_fact("requirement", {"requirement": requirement, "statement": statement.strip(),
                    "operation": operation, "boundary": boundary}, [observation],
                    "Human-authored interpretation: operation and quoted approved-boundary name", semantic=True)
        matches = [item for item in records if item.values["environment"] == "production"
                   and item.values["operation"] == operation and item.values["boundary"] == boundary_name]
        observations = [observation, configuration.observe(0, len(configuration.data))]
        for item in matches:
            row = item.values
            if row["implementation"] not in declarations or row["entrypoint"] not in declarations:
                raise ValueError("manifest endpoint is not a declared program function")
            observations.extend([item.observation, declarations[row["implementation"]].observation,
                                 declarations[row["entrypoint"]].observation])
        if len(matches) != 1:
            for item in matches:
                row = item.values
                assert_fact("candidate_realization", {"requirement": requirement, "boundary": boundary,
                            "program": "program:" + row["implementation"]},
                            [observation, item.observation, declarations[row["implementation"]].observation],
                            "Cross-source candidate only; shared boundary name does not establish unique correspondence", semantic=True)
            assert_fact("open_question", {"requirement": requirement,
                        "question": f"Which program implementation realizes {boundary_name} for {operation}?",
                        "status": "UNRESOLVED", "reason": f"{len(matches)} candidate manifest matches; no unique cross-source correspondence"},
                        observations, "Human-authored uniqueness rule; no tie-break and no negative claim", semantic=True)
            continue
        row = matches[0].values
        assert_fact("realized_by", {"boundary": boundary, "program": "program:" + row["implementation"]},
                    observations, "Unique requirement boundary + production manifest + declared implementation", semantic=True)
        assert_fact("governs", {"requirement": requirement, "program": "program:" + row["entrypoint"],
                    "provider": "provider:" + row["provider"]}, observations,
                    "Cross-source interpretation: requirement applies to configured production entrypoint and provider", semantic=True)

    declare("governed_call", [("requirement", ref), ("caller", ref), ("callee", ref)],
            "Observed direct calls from entrypoints with established governing requirements.", derived=True)
    world.register_derivation("governed_call", sql="""
        SELECT DISTINCT g.requirement_id, c.caller_id, c.callee_id
        FROM governs g JOIN direct_call c ON g.program_id = c.caller_id
    """, inputs=["governs", "direct_call"])
    world.rerun("governed_call", completeness=Completeness(
        CompletenessStatus.COMPLETE, "direct_call", "All supplied direct-call tuples joined to established governs tuples; not all runtime calls or unresolved requirements."))

    for name, status, description in (
        ("paypal_in_manifest", CompletenessStatus.COMPLETE, "PayPal occurrences in the supplied finite deployment manifest."),
        ("paypal_anywhere", CompletenessStatus.UNKNOWN, "Known PayPal occurrences; deployment outside the supplied manifest is not enumerated."),
    ):
        declare(name, [("provider", ref)], description, derived=True)
        world.register_derivation(name, sql="SELECT DISTINCT provider_id FROM deployment WHERE provider_id = 'provider:PayPal'",
                                  inputs=["deployment"])
        world.rerun(name, completeness=Completeness(status, "deployment", description,
            known_gaps=() if status == CompletenessStatus.COMPLETE else ("Other manifests, environments, and live deployments were not observed.",)))

"""Test-only construction of a tiny research World from Markdown evidence."""

from __future__ import annotations

import hashlib

from ontology_author.evidence.markdown import MarkdownSource
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.core.origins import ConstructionOrigin
from ontology_author.world.core.source import AssertionGrounding


def construct(source, world):
    documents = {
        name: MarkdownSource.from_path(source.root / f"{name}.md", workspace=source.root)
        for name in ("study_a", "study_b", "study_c", "summary")
    }
    retained = world.path.parent / "evidence"
    retained.mkdir()
    for document in documents.values():
        (retained / hashlib.sha256(document.data).hexdigest()).write_bytes(document.data)

    ref, text = RoleType.REFERENT, RoleType.TEXT
    for name, roles in (
        ("study_intervention", [("study", ref), ("intervention", text)]),
        ("study_finding", [("study", ref), ("finding", ref)]),
        ("finding_outcome", [("finding", ref), ("outcome", text)]),
        ("finding_supports_claim", [("finding", ref), ("claim", ref)]),
        ("possible_humidity_effect", [("claim", ref), ("direction", text)]),
        ("open_question", [("claim", ref), ("question", text)]),
    ):
        world.declare_relation(name, [Role(role, kind) for role, kind in roles])

    def record(relation, values, document, passage, method):
        observation = documents[document].observe(documents[document].span_containing(passage))
        return world.assert_tuple(
            relation,
            values,
            origin=ConstructionOrigin.SEMANTIC,
            grounding=AssertionGrounding((observation,), construction_method=method),
        )

    world.add_referent("claim:cooling", label="shade cloth lowers basil leaf temperature",
                       observations=(documents["summary"].observe(documents["summary"].document()),))
    for letter in "abc":
        name = f"study_{letter}"
        outcome = "unchanged leaf temperature" if "unchanged leaf temperature" in documents[name].data.decode("utf-8") else "lower leaf temperature"
        passage = f"Study {letter.upper()} tested shade cloth on basil plants and reported {outcome}."
        observation = documents[name].observe(documents[name].span_containing(passage))
        world.add_referent(f"study:{letter}", label=f"Study {letter.upper()}", observations=(observation,))
        world.add_referent(f"finding:{letter}", label=outcome, observations=(observation,))
        record("study_intervention", {"study": f"study:{letter}", "intervention": "shade cloth"},
               name, passage, "Reported intervention")
        record("study_finding", {"study": f"study:{letter}", "finding": f"finding:{letter}"},
               name, passage, "Study reports finding")
        record("finding_outcome", {"finding": f"finding:{letter}", "outcome": outcome},
               name, passage, "Reported outcome")
        if outcome == "lower leaf temperature":
            record("finding_supports_claim", {"finding": f"finding:{letter}", "claim": "claim:cooling"},
                   name, passage, "Finding interpreted as support for bounded cooling claim")

    summary = "The two possible interpretations are that humidity increases the cooling effect and that humidity decreases the cooling effect. Available measurements do not distinguish them."
    for direction in ("increases cooling", "decreases cooling"):
        record("possible_humidity_effect", {"claim": "claim:cooling", "direction": direction},
               "summary", summary, "Possible interpretation, not selected finding")
    record("open_question", {"claim": "claim:cooling", "question": "Does humidity increase or decrease the cooling effect?"},
           "summary", summary, "Summary explicitly leaves the relationship unresolved")

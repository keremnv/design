"""Bind a materialized config requirement to an explicitly selected program entity.

Reuses the production authority binding seam (``realized_by`` +
SEMANTIC_PROGRAM + attachment warrant + relevance scope) over an exact
program-spine baseline. The selected requirement must already be present
as an identical complete tuple in an exact semantic requirement
publication; that occurrence is recorded in the construction basis.
Program-entity selection is an explicit bounded construction decision,
never automatic discovery.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from ontology_author.authority import (
    AuthorityConstructionError, AuthorityConstructionResult, AuthorityUniverse,
    ClaimKind, DeclaredSource, ReferentResolution, RelationSupport,
    SourceStanding, construct_authority_world,
)
from ontology_author.world.core.model import Role, RoleType
from ontology_author.world.runtime.publication import PublicationRef
from ontology_author.world.runtime.world import ConstructionWorld

from .construct import _acquire_governance
from .rules import PROFILE_ID, PROFILE_VERSION
from .semantic import materialize_requirements

BINDING_METHOD = "config.routes.binding/v1:explicit-selected-realization"


def _selected_config_requirement(
    reference: PublicationRef, selected: str
) -> tuple[str, str, str, str]:
    """Read one unambiguous selected requirement tuple from an exact publication.

    Bounded ``config_routes`` rule: the selected requirement must appear as
    exactly one ``config_requirement`` row. Same-ID duplicates fail closed.
    """
    database = Path(reference.address) / "world.sqlite"
    try:
        with closing(ConstructionWorld.open(database, read_only=True)) as world:
            matches = [
                row for row in world.relation_rows("config_requirement")
                if str(row["requirement"]) == selected
            ]
    except Exception as exc:
        raise AuthorityConstructionError(
            f"semantic requirement publication is not readable as config requirements: {exc}"
        ) from exc
    if not matches:
        raise AuthorityConstructionError(
            "selected requirement does not match the semantic requirement publication"
        )
    if len(matches) != 1:
        raise AuthorityConstructionError(
            "ambiguous selected requirement: multiple config_requirement rows share the selected ID"
        )
    row = matches[0]
    return (
        str(row["requirement"]),
        str(row["statement"]),
        str(row["domain_relation"]),
        str(row["requested_route"]),
    )


def construct_config_binding(
    governance_source: Path | str,
    program_world: Path | str,
    output: Path | str,
    *,
    program_entity: str,
    requirement: str | None = None,
    semantic_inputs: tuple[PublicationRef, ...] = (),
) -> AuthorityConstructionResult:
    """Publish a binding between one requirement and one program entity.

    ``program_entity`` must already exist in the supplied program baseline's
    governed snapshot. ``semantic_inputs`` names exact requirement
    publications consumed as construction inputs; the first must contain the
    selected requirement as exactly one ``config_requirement`` row with an
    identical complete tuple (requirement, statement, domain_relation,
    requested_route), compared by exact application-level equality. When
    ``requirement`` is omitted, the source must materialize exactly one
    requirement.
    """
    path = Path(governance_source)
    try:
        _acquire_governance(path, expected=None)
    except (OSError, ValueError) as exc:
        return AuthorityConstructionResult(False, "source_form", (str(exc),))
    if not semantic_inputs:
        return AuthorityConstructionResult(
            False, "authority_construction",
            ("binding requires at least one exact semantic requirement publication",),
        )
    universe = AuthorityUniverse(
        universe_id="config.routes/binding/v1", workspace=path.parent,
        sources=(DeclaredSource(path.name, path, SourceStanding.AUTHORITATIVE),),
    )

    def build(constructor):
        if program_entity not in constructor.program_entities():
            raise AuthorityConstructionError(
                f"selected program entity is not in the governed snapshot: {program_entity}"
            )
        materialized = materialize_requirements(constructor, constructor.source(path.name))
        by_semantic = {
            semantic_id: (proposition_id, observation)
            for proposition_id, (semantic_id, observation) in materialized.items()
        }
        if requirement is None:
            if len(by_semantic) != 1:
                raise AuthorityConstructionError(
                    "ambiguous requirement selection: select one explicitly"
                )
            selected = next(iter(by_semantic))
        else:
            if requirement not in by_semantic:
                raise AuthorityConstructionError(
                    f"selected requirement was not materialized from the source: {requirement}"
                )
            selected = requirement
        _, observation = by_semantic[selected]
        expected = [
            row for row in constructor.world.relation_rows("config_requirement")
            if str(row["requirement"]) == selected
        ]
        if not expected:
            raise AuthorityConstructionError(
                "selected requirement does not match the semantic requirement publication"
            )
        if len(expected) != 1:
            raise AuthorityConstructionError(
                "ambiguous requirement selection: re-materialized requirement is not unique"
            )
        source_tuple = (
            str(expected[0]["requirement"]),
            str(expected[0]["statement"]),
            str(expected[0]["domain_relation"]),
            str(expected[0]["requested_route"]),
        )
        published_tuple = _selected_config_requirement(semantic_inputs[0], selected)
        if published_tuple != source_tuple:
            raise AuthorityConstructionError(
                "selected requirement does not match the semantic requirement publication"
            )
        constructor.persist_claim(
            "realized_by",
            {"requirement": selected, "program": program_entity},
            roles=(Role("requirement", RoleType.REFERENT), Role("program", RoleType.REFERENT)),
            claim_kind=ClaimKind.SEMANTIC_PROGRAM, support=RelationSupport.CROSS_EVIDENCE_INFERRED,
            endpoint_resolution={
                "requirement": ReferentResolution.SOURCE_DEFINED,
                "program": ReferentResolution.AGENT_RESOLVED,
            },
            observations=(observation,), construction_method=BINDING_METHOD,
        )

    return construct_authority_world(
        program_world, output, universe, build,
        construction_id="config.routes/binding/v1", purpose="config binding",
        profile=PROFILE_ID, publication_inputs=tuple(semantic_inputs),
        constructor_id="config.routes.binding", constructor_version=PROFILE_VERSION,
    )

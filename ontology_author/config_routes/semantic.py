"""Source-only config requirements, before any software realization exists.

Reuses the bounded config.routes grammar and authority admission/retention.
The requested route is semantic content, never a fabricated software identity.
"""

from __future__ import annotations

from pathlib import Path

from ontology_author.authority import (
    AuthorityConstructionError, AuthorityConstructionResult, AuthorityUniverse,
    ClaimKind, DeclaredSource, ReferentResolution, RelationSupport,
    SourceStanding, UnresolvedKind, construct_authority_world,
)
from ontology_author.world.core.model import Role, RoleType

from .construct import _acquire_governance
from .rules import PROFILE_ID, PROFILE_VERSION, extract_propositions


def construct_config_requirements(
    governance_source: Path | str, output: Path | str,
) -> AuthorityConstructionResult:
    """Publish requirements without program input, binding, or implementation status.

    Unsupported paragraphs retain an explicit unresolved record and their
    full evidence. A source with no representable requirements fails closed.
    """
    path = Path(governance_source)
    # The driver reads immutable bytes inside authority construction. Validate
    # the declared source form first, as the existing profile already does.
    try:
        _acquire_governance(path, expected=None)
    except (OSError, ValueError) as exc:
        return AuthorityConstructionResult(False, "source_form", (str(exc),))
    universe = AuthorityUniverse(
        universe_id="config.routes/requirements/v1", workspace=path.parent,
        sources=(DeclaredSource(path.name, path, SourceStanding.AUTHORITATIVE),),
    )

    def build(constructor):
        source = constructor.source(path.name)
        regions = source.paragraphs()
        paragraphs = [(source.reconstruct(region).strip(), index) for index, region in enumerate(regions)]
        propositions, unsupported = extract_propositions(paragraphs)
        if not propositions:
            raise AuthorityConstructionError("representational gap: no supported config.routes/v1 requirement")
        observations = {text: source.observe(regions[index]) for text, index in paragraphs}
        for item in propositions:
            observation = observations[item.statement]
            semantic_id = "semantic:" + item.proposition_id
            constructor.create_semantic_referent(
                semantic_id, label=item.statement, observations=(observation,),
            )
            constructor.persist_claim(
                "config_requirement",
                {"requirement": semantic_id, "statement": item.statement,
                 "domain_relation": item.domain_relation, "requested_route": item.route_id or ""},
                roles=(Role("requirement", RoleType.REFERENT), Role("statement", RoleType.TEXT),
                       Role("domain_relation", RoleType.TEXT), Role("requested_route", RoleType.TEXT)),
                claim_kind=ClaimKind.SOURCE_PROPOSITION, support=RelationSupport.SOURCE_EXPLICIT,
                endpoint_resolution={"requirement": ReferentResolution.SOURCE_DEFINED},
                observations=(observation,), construction_method=item.establishment_rule,
            )
        for item in unsupported:
            index = int(item["paragraph_index"])
            constructor.persist_unresolved(
                f"config.routes:unsupported:{index}", kind=UnresolvedKind.UNBOUND_REGION,
                observation=source.observe(regions[index]), detail=item["reason"],
            )

    return construct_authority_world(
        None, output, universe, build,
        construction_id="config.routes/requirements/v1", purpose="config requirements",
        profile=PROFILE_ID, constructor_id="config.routes.requirements", constructor_version=PROFILE_VERSION,
    )

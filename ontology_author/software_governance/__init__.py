"""Software Governance construction above Core Product v1.

The package records governance propositions and their correspondences to
mechanically identified software subjects. It does not extract a program
and it does not interpret a policy language. Judgment of a sealed World
lives in `ontology_author.software_governance.judgment` and does not write
back into that World. Investigation of a judgment case lives in
`ontology_author.software_governance.investigation` and does not admit or
publish.
"""

from ontology_author.software_governance.construction import (
    BindingSpec,
    CandidateSpec,
    CompletenessSpec,
    GovernanceConstructionResult,
    ManifestationSpec,
    PropositionSpec,
    QuestionSpec,
    SoftwareSubjectSpec,
    construct_software_governance,
)
from ontology_author.software_governance.reads import GovernanceView, open_governance_world

__all__ = [
    "BindingSpec",
    "CandidateSpec",
    "CompletenessSpec",
    "GovernanceConstructionResult",
    "GovernanceView",
    "ManifestationSpec",
    "PropositionSpec",
    "QuestionSpec",
    "SoftwareSubjectSpec",
    "construct_software_governance",
    "open_governance_world",
]

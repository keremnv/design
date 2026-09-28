"""Investigation around a sealed Construction World and a Judgment case.

The package expands a case only with assertions the named publication
already contains, and it can record a proposal or an unresolved result.
It does not judge, admit, or publish. Profile code decides what to look for.
"""

from ontology_author.software_governance.investigation.expansion import (
    added_assertion_ids,
    citation_errors,
    expanded_case,
)
from ontology_author.software_governance.investigation.records import (
    EPISTEMIC_CLASSES,
    ORIGIN_KINDS,
    OUTCOMES,
    InvestigationBoundary,
    make_proposal,
    make_question,
    make_receipt,
)

__all__ = [
    "EPISTEMIC_CLASSES",
    "ORIGIN_KINDS",
    "OUTCOMES",
    "InvestigationBoundary",
    "added_assertion_ids",
    "citation_errors",
    "expanded_case",
    "make_proposal",
    "make_question",
    "make_receipt",
]

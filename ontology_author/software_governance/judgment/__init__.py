"""Judgment over a sealed Software Governance Construction World.

The package assembles a bounded case, checks its citations, and reads a
judgment artifact. Profile evaluators decide applicability, findings, and
conformance. This package does not know those rules, and it does not write
them into the Construction World.
"""

from ontology_author.software_governance.judgment.artifact import (
    artifact_shell,
    consumer_reads,
    method_record,
    read_artifact,
    write_artifact,
)
from ontology_author.software_governance.judgment.case import assemble_case, facts, verify_case

__all__ = [
    "artifact_shell",
    "assemble_case",
    "consumer_reads",
    "facts",
    "method_record",
    "read_artifact",
    "verify_case",
    "write_artifact",
]

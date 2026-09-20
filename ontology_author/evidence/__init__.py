"""Evidence adapters: observe sources, address regions, reconstruct evidence.

These modules mechanically structure external reality. They never assign
semantic standing: nothing here imports application authority rules.
"""

from __future__ import annotations


class EvidenceError(ValueError):
    """Native evidence cannot be addressed or reconstructed."""


__all__ = ["EvidenceError"]

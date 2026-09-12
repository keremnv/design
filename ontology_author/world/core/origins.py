"""Construction-origin axis used by the experimental harness.

This is separate from ASSERTED/DERIVED assertion bookkeeping. It classifies
how a particular construction/support path entered the World; it is not an
intrinsic property with one value per semantic proposition.
"""

from __future__ import annotations

from enum import StrEnum


class ConstructionOrigin(StrEnum):
    """How one support/construction path came to be in the World.

    ``ADJUDICATED`` remains available for a direct adjudicated construction
    path. A first-class Adjudication record is not automatically rewritten as
    an origin on an ordinary Commitment; its own record remains the source of
    that fact.
    """

    MECHANICAL = "MECHANICAL"
    SEMANTIC = "SEMANTIC"
    DERIVED = "DERIVED"
    ADJUDICATED = "ADJUDICATED"


class OriginMetadataError(ValueError):
    """An asserted tuple has no recorded construction origin."""

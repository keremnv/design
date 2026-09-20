-- These are reference query semantics, not a required implementation shape.

-- CQ-04: location at time.
-- Select the latest established holding interval whose start <= target and whose end is null or > target.

-- CQ-05: sample source owner.
-- Follow sample -> sampled_from -> inbound material -> source_owner, not the later title holder.

-- CQ-07: storage and loadout point.
-- Follow shipment -> loadout event -> source container and truck; normalize local aliases first.

-- NQ-01: multi-source composition.
-- Return all composed_of edges for the outbound shipment and preserve their quantities.

-- NQ-04: complete upstream provenance.
-- A processor receipt is complete only when every contributing input has an established inbound referent, source location, and source party, and no candidate-only allocation remains.

-- NQ-10: completeness-sensitive absence.
-- Return a negative only when a complete receiving extract covers the queried site and interval; otherwise return not_established.

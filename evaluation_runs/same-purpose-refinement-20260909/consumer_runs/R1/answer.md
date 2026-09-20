# Receiving tickets on the hopper sheet — OUT-5002 / PGE-OUT-5002

For the **26,000 kg** movement out of **North House 12** (work order **OUT-5002**, dispatch **PGE-OUT-5002**), the hopper sheet names two scale tickets in `material_note`:

- **WB-390**
- **EF-18**

Those scale tickets correspond to these Prairie Gate receiving tickets:

| Receiving ticket | Scale ticket | Grower            | Net received (kg) |
|------------------|--------------|-------------------|-------------------|
| **ER-7721**      | WB-390       | Willow Bend Farms | 23,850            |
| **ER-7729**      | EF-18        | East Fork Co-op   | 17,900            |

**Source:** bin movement **BM-004** (`BIN-12` → `LOAD-PIT-2`, 26,000 kg, work order `OUT-5002`), joined to `elevator_receipts.csv` on scale ticket. Loadout **LD-19** confirms the same 26,000 kg dispatch from North House 12 as **PGE-OUT-5002** (truck NST-204).

The hopper sheet does not split the 26,000 kg between the two tickets; it only records that both were named on the move.

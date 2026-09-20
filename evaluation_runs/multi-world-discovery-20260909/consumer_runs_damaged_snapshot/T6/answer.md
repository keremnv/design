# Canonical identity: Meadow Creek cluster

## Single canonical identity

**`ticket:MCR-118`** (label: **`MCR-118`**)

Use this as the one identity for later work. Treat every alias below as referring to the same party/lot cluster unless a downstream step explicitly reopens an unresolved claim.

## Aliases

| Alias | Where it appears | Meaning |
| --- | --- | --- |
| **MCR-118** | grain-flow intake ticket; title-custody `scope_ref` | Scale-ticket / lot code; registered referent label |
| **M. Creek** | grain-flow intake `grower_recorded` and `owner_at_intake` on `ticket:MCR-118` | Abbreviated grower name on the receiving slip |
| **Meadow Creek** | User shorthand; implied by **M. Creek** and the **MC** prefix in **MC-118** / **MCR-118** | Expanded grower name for the same party |
| **MC-118** | lab-quality sample `SMP-604Q` `local_lot` | Lab lot label for South House 14 cargo; same numeric lot as **MCR-118**, but not a proven join in source data |

Related commercial names on the same ticket (still the same party cluster, but legally ambiguous):

| Name | Where it appears |
| --- | --- |
| Meadow Creek Farms | title-custody ownership claim `TR-107` |
| Meadow Creek Grain | title-custody ownership claim `TR-107` |

## Evidence anchors

- **grain-flow:** intake receipt `ER-7744` — `ticket:MCR-118`, grower **M. Creek**, bin **B-14** / South House 14, 20,850 kg, 2025-09-07.
- **title-custody:** ownership record `TR-107` — `scope_ref` **MCR-118**; duplicate account claims from Meadow Creek Farms and Meadow Creek Grain.
- **lab-quality:** lab result on `sample:SMP-604Q` — `local_lot` **MC-118**, material hint "South House 14 cargo".

## What stays unresolved in source worlds

Do not collapse these into separate parties; keep them as open questions on **`ticket:MCR-118`**:

1. **Legal account:** Meadow Creek Farms vs Meadow Creek Grain (`mcr118_duplicate_account_claim` / `mcr118_grower_identity`).
2. **Lab join:** MC-118 is not itself a proven join to scale ticket MCR-118 or a legal account (`smp_604q_lot_label`).
3. **Blend allocation:** South House 14 also held **S-52**; loadout **PGE-OUT-5004** did not allocate the truck to one ticket (`out_5004_blend_allocation`).

## Recommended usage

```text
canonical_id: ticket:MCR-118
canonical_label: MCR-118
party_aliases: [M. Creek, Meadow Creek, MC-118, MCR-118, Meadow Creek Farms, Meadow Creek Grain]
```

When joining across worlds, key on **`ticket:MCR-118`** / **`MCR-118`** and map aliases to it. Preserve the three unresolved items above rather than inferring a single legal account or a proven lab-to-ticket link.

# Canonical identity: Meadow Creek

**Canonical party:** `party:meadow-creek` — **Meadow Creek**

Use this one referent everywhere later work needs a single party for the Meadow Creek delivery episode. Map every local label below to `party:meadow-creek`.

| Local label | Role | Grounding |
|---|---|---|
| `M. Creek` | Intake grower / owner shorthand | `evidence/elevator_receipts.csv` (`scale_ticket=MCR-118`) |
| `MCR-118` | Scale ticket and ownership scope for this delivery | `evidence/elevator_receipts.csv`, `evidence/bin_movements.csv` (`move_id=BM-007`), `evidence/ownership_records.csv` (`record_no=TR-107`) |
| `MC-118` | Lab local lot for South House 14 cargo from that delivery | `evidence/inspection_results.csv` (`sample_no=SMP-604Q`) |
| `Meadow Creek Farms` | Commercial account claim (duplicate) | `evidence/ownership_records.csv` (`record_no=TR-107`, `from_party`) |
| `Meadow Creek Grain` | Commercial account claim (duplicate) | `evidence/ownership_records.csv` (`record_no=TR-107`, `to_party`) |

## Why this identity

- `evidence/operating_notes.md` states that intake writes **“M. Creek”** for the **`MCR-118`** delivery.
- The **`MCR-118`** receipt (`ER-7744`, 20,850 kg → bin `B-14`) is copied into bin movement **`BM-007`** and is the scope of ownership record **`TR-107`**.
- Lab sample **`SMP-604Q`** labels lot **`MC-118`** against **South House 14 cargo** — the same bin (`BIN-14` / `B-14`) that received ticket **`MCR-118`** on the same day.
- **`M. Creek`**, **`MC-118`**, and **`MCR-118`** are therefore one operational party and one delivery chain, not four separate parties.

**Meadow Creek** is the neutral canonical name: it is the full form of intake shorthand **`M. Creek`** and the shared stem of the duplicate desk claims **Meadow Creek Farms** and **Meadow Creek Grain**. It does not pick between those two legal-account variants.

## Still unresolved separately

Choosing **`party:meadow-creek`** does not resolve which of **Meadow Creek Farms** vs **Meadow Creek Grain** holds title (`TR-107` remains a duplicate `party_claim` with no account key). Treat that as a downstream title question, not a reason to split the operational party above.

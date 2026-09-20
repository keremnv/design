**Canonical identity:** `ticket:MCR-118` (label **MCR-118**)

Treat Meadow Creek, M. Creek, MC-118, and MCR-118 as one party/lot cluster anchored on receiving ticket **MCR-118**. Map aliases as follows:

| Alias | Where it appears | Role |
|---|---|---|
| **MCR-118** | grain-flow intake (`ticket:MCR-118`, receipt ER-7744); title-custody `scope_ref` on TR-107 | Primary ticket / lot key |
| **M. Creek** | grain-flow intake `grower_recorded` and `owner_at_intake` for `ticket:MCR-118` | Abbreviated grower name on the scale ticket |
| **Meadow Creek** | title-custody TR-107 party claims (**Meadow Creek Farms** vs **Meadow Creek Grain**) | Full commercial party name family behind the ticket |
| **MC-118** | lab-quality sample SMP-604Q `local_lot` (South House 14 cargo) | Lab shorthand for the same Meadow Creek lot |

Use `ticket:MCR-118` in later cross-world work as the single join key. Individual worlds still mark some of these links as unresolved (grower identity on intake, duplicate Farms/Grain title claims on TR-107, and the lab lot label not being a proven join), but all four strings refer to the same Meadow Creek delivery received 2025-09-07 into South House 14 (bin B-14), 20,850 kg.

# Mill desk answer: PGE-OUT-5001

**Which mill receiving slip accepted the truck dispatched as PGE-OUT-5001?**

**HFM-IN-601** accepted that truck at Hearthland Feed Mill — North (dock N-2) on 2025-09-05 at 11:05 local. The mill slip references bill **RL-5001-A** and origin label **PG-OUT-5001** (the mill’s label for the same movement; Prairie Gate’s loadout desk uses **PGE-OUT-5001**).

**What mill run used that receipt?**

**MILL-2206** used HFM-IN-601. It started 2025-09-05 at 14:20 local and produced batch **FEED-2206** (starter feed).

## Trace

| Stage | Record | Key link |
| --- | --- | --- |
| Loadout | LD-18 | dispatch_ref **PGE-OUT-5001**, truck RLT-088, 39,000 kg |
| Carrier manifest | RL-8841 | cargo_mark **PGE-OUT-5001**, bill of lading **RL-5001-A** |
| Mill receiving slip | **HFM-IN-601** | bill_reference **RL-5001-A**, 38,700 kg received |
| Mill run | **MILL-2206** | input receipt **HFM-IN-601** |

The join from dispatch to mill slip is established through the carrier bill of lading (RL-5001-A), not through the differing dispatch/origin label spellings alone.

# Config-route Software Governance profile

Fixture only. Route ids and the English sentences are not the Software
Governance ontology.

The producer reads `software.json` and identifies each route record. It does
not use TypeScript or Program Spine relations. Generic Software Governance
then records propositions against those subjects.

```sh
uv run python profiles/software_governance_config_v0/build.py /path/to/fresh-world
```

The output path must not already exist.

`judge.judge` evaluates a case assembled from that sealed World. The rule
parameters live in that module. The generic judgment package does not import
this profile.

`investigate.investigate` may read that sealed World and caller-supplied
capabilities, then expand a case or record a proposal. The generic
investigation package does not import this profile.

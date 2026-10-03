# Software Governance v0 acceptance profile

Fixture only. `outbound_mail_passes` and the mail sentences are not the
Software Governance ontology.

This profile builds the TypeScript program spine and reads the Markdown
sources. `ontology_author.software_governance` records governance on the
resulting World. It does not extract TypeScript.

```sh
uv run python profiles/software_governance_v0/build.py /path/to/fresh-world
```

The output path must not already exist. The command constructs a TypeScript
program spine, records the fixture's propositions and correspondences,
validates them, and seals the World at that address.

`judge.judge` evaluates a case assembled from that sealed World. The rule
parameters live in that module. The generic judgment package does not import
this profile.

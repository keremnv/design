# Historical checkout-authority snapshot

Non-authoritative downstream research evidence, relocated from
`.worlds/checkout-authority/` during Core v1 checkpointing. Not a runnable or
portable sealed World: its database was never tracked.

- `fixture/`: the original prose and TypeScript source corpus (12 files).
- `authority.construction.receipt.json`: original construction, ambiguity,
  completeness and adequacy findings.
- `authority.manifest.json`: original authority observation inventory.

These 14 files are preserved byte-for-byte. Absolute paths inside the records
identify the original run; they are not instructions to access that machine.
Six intermediate generated spine/TypeScript/admission JSON files were untracked,
not carried into this archive. The original local `.worlds/checkout-authority/`
directory was not deleted or modified; all previously tracked versions remain
recoverable from Git history. Tests generate their own temporary fixtures.

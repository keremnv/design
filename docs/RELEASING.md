# Releasing Ontology Author

Maintainer checklist for a separately authorized release. Building or pushing
the repository does not publish a release. The package name is `ontology-author`;
this document does not assert that a particular version is available on PyPI.
For a local checkout install:

```bash
uv tool install .
```

## One-time publisher setup

1. Create the `ontology-author` project on TestPyPI, then configure the repository
   as a trusted publisher for it.
2. Repeat for PyPI, with the GitHub Actions environment named `pypi`.
3. In GitHub, require approval for the `pypi` environment.

Trusted publishing uses GitHub's short-lived identity token; no PyPI password
or long-lived upload token is stored in this repository. See the
[PyPA GitHub Actions publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

## Release process

1. Update `version` in `pyproject.toml` and the release notes.
2. Build the inspector assets, then run `uv run --extra dev pytest` locally.
3. Create and push a version tag such as `v0.1.0`.
4. Create a matching GitHub Release. The release workflow builds an sdist and
   wheel, checks them, uploads them as release artifacts, and publishes to PyPI.
5. In a clean shell, verify the public install:

   ```bash
   uv tool install ontology-author
   mkdir smoke-project && cd smoke-project
   author attach cursor
   ```

The released wheel must include `ontology_author.world`, its bundled inspector
assets and the World SQLite implementation. Historical graph/MCP code is not part of the
normal installation.

Repository tests are deliberately excluded from the sdist: they require the
checkout's profiles, frontend dependencies and historical fixtures. Run the
documented gates from a checkout. The wheel includes the current package,
its capability document, TypeScript extractor and bundled inspector, not
historical root graph modules, experiment transcripts or generated Worlds.

Checkpoint note (2026-09-21): `npm ci --prefix frontend` and the frontend build
succeed and reproduce the committed assets. `npm audit --prefix frontend --json`
reports four existing dependency advisories (one moderate, three high) in
`baseline-browser-mapping`, `browserslist`, `nanoid`, and `postcss`. These remain
dependency-maintenance debt, not a clean security audit. No lockfile upgrade
or vulnerability remediation was attempted during the Core v1 checkpoint.
Vite also warns about the existing large JavaScript chunk. Review these before
a separately authorized release; this checkpoint is not a release.

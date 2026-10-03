"""Command wrapper.

The acceptance fixture is not imported here. Run:

```sh
uv run python profiles/software_governance_v0/build.py <fresh-output-directory>
```
"""

from __future__ import annotations

import sys


def main() -> None:
    sys.stderr.write(
        "usage: uv run python profiles/software_governance_v0/build.py <fresh-output-directory>\n"
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()

"""Fingerprint the completed experimental container build; writes outside repo."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--container", default="design-phase6b-build")
    args = parser.parse_args()
    work = args.work.resolve()
    assert (work / "BUILD_SUCCESS").exists(), "pinned build has not completed"
    common = ["docker", "exec", "-w", "/work/Glean", args.container, "env",
              "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
              "LD_LIBRARY_PATH=/work/hsthrift-installed/lib:/work/hsthrift-installed/lib64",
              "PKG_CONFIG_PATH=/work/hsthrift-installed/lib/pkgconfig:/work/hsthrift-installed/lib64/pkgconfig",
              "PATH=/work/hsthrift-installed/bin:/usr/local/bin:/usr/bin:/bin"]

    def run(*command):
        return subprocess.check_output(common + list(command), text=True).strip()

    (work / "runtime").mkdir(exist_ok=True)
    binaries = {}
    libraries = {}
    for component, name in (("glean:exe:glean", "glean"), ("glean-clang:exe:clang-index", "clang-index"),
                            ("glean-clang:exe:clang-derive", "clang-derive")):
        path = run("cabal", "list-bin", "--builddir=/work/Glean/.build/dev/dist-newbuild",
                   "-f-bundled-folly", "-f-hack-tests", component)
        if (work / "runtime" / name).is_symlink():
            assert run("readlink", "/work/runtime/" + name) == path
        else:
            subprocess.run(common + ["ln", "-s", path, "/work/runtime/" + name], check=True)
        binaries[name] = run("sha256sum", path).split()[0]
        for library in re.findall(r"(/[^\s()]+)", run("ldd", path)):
            libraries[library] = run("sha256sum", library).split()[0]
    record = {
        "glean_commit": run("git", "rev-parse", "HEAD"),
        "hsthrift_commit": run("git", "-C", "hsthrift", "rev-parse", "HEAD"),
        "ghc": run("ghc", "--numeric-version"),
        "cabal": run("cabal", "--numeric-version"),
        "clang": run("clang-15", "--version").splitlines()[0],
        "llvm": run("llvm-config-15", "--version"),
        "base_image": "ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55",
        "build_flags": "MODE=dev; CXX_MODE=cabal (upstream C++20); GHC -O0 -optl-Wl,--no-as-needed -optl-lboost_context -optl/work/hsthrift-installed/lib/libfmt.so; glean-clang package -pgmcxx /usr/bin/clang++-15 -optcxx-O0 -optcxx-g0 -optcxx-fno-addrsig; separate Cabal configuration/Setup build; -f-bundled-folly; -f-hack-tests; -j1",
        "index_state": "2025-04-14T00:00:00Z",
        "locale": "C.UTF-8",
        "binaries": binaries,
        "shared_libraries": dict(sorted(libraries.items())),
    }
    (work / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

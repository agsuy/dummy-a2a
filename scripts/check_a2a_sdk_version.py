#!/usr/bin/env python3
"""Fail if PyPI has a newer a2a-sdk than the version pinned in pyproject.toml."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from pathlib import Path

from packaging.version import InvalidVersion, Version

_PIN_RE = re.compile(
    r"^a2a-sdk(?:\[[^\]]+])?==\s*([^\s#]+)\s*$",
    re.IGNORECASE,
)


def pinned_a2a_sdk_version(pyproject_path: Path) -> Version:
    import tomllib

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    deps: list[str] = data.get("project", {}).get("dependencies", [])
    for raw in deps:
        line = raw.strip()
        m = _PIN_RE.match(line)
        if m:
            return Version(m.group(1).strip())
    msg = "no a2a-sdk==... pin found in [project] dependencies"
    raise ValueError(msg)


def max_version_from_release_keys(keys: Iterable[str]) -> Version:
    best: Version | None = None
    for key in keys:
        try:
            v = Version(key)
        except InvalidVersion:
            continue
        if best is None or v > best:
            best = v
    if best is None:
        msg = "no valid versions found in PyPI response"
        raise ValueError(msg)
    return best


def max_version_on_pypi(package: str = "a2a-sdk") -> Version:
    url = f"https://pypi.org/pypi/{package}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "dummy-a2a-pin-check"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        data = json.load(resp)

    releases = data.get("releases") or {}
    return max_version_from_release_keys(releases.keys())


def main(pyproject_path: Path | None = None) -> int:
    root = Path(__file__).resolve().parent.parent
    pyproject = pyproject_path if pyproject_path is not None else root / "pyproject.toml"
    try:
        pinned = pinned_a2a_sdk_version(pyproject)
        latest = max_version_on_pypi()
    except (ValueError, urllib.error.URLError, OSError) as e:
        print(f"error: could not determine a2a-sdk versions: {e}", file=sys.stderr)
        return 1

    if latest > pinned:
        print(
            f"error: a2a-sdk on PyPI is newer than this repo pin.\n"
            f"  pinned in pyproject.toml: {pinned}\n"
            f"  latest on PyPI:           {latest}\n"
            f"  bump the pin, run tests, and update the README SDK note.",
            file=sys.stderr,
        )
        return 1

    print(f"ok: a2a-sdk pin {pinned} is up to date with PyPI (latest {latest}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

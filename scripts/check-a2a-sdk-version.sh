#!/usr/bin/env bash
# Fail when PyPI has a newer a2a-sdk than pyproject.toml (see check_a2a_sdk_version.py).
set -euo pipefail

repo_root="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

uv run python "$repo_root/scripts/check_a2a_sdk_version.py"

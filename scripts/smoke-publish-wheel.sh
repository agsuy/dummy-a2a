#!/usr/bin/env bash
# Mirrors .github/workflows/publish.yml: uv build then isolated import of the wheel.
# Catches undeclared runtime deps (e.g. transitive imports) before CI/tag publish.
set -euo pipefail

repo_root="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

rm -rf dist
uv build

shopt -s nullglob
whl=(dist/*.whl)
shopt -u nullglob

if ((${#whl[@]} == 0)); then
  echo "error: no wheel produced under dist/" >&2
  exit 1
fi
if ((${#whl[@]} > 1)); then
  echo "error: expected a single wheel in dist/, found: ${whl[*]}" >&2
  exit 1
fi

uv run --isolated --no-project --with "${whl[0]}" python -c "import dummy_a2a; print('smoke ok', dummy_a2a.__version__)"

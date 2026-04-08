#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"

cd "$repo_root"

"$repo_root/scripts/lint.sh"
"$repo_root/scripts/test.sh"
"$repo_root/scripts/lint-check.sh"
"$repo_root/scripts/type-check.sh"
"$repo_root/scripts/test.sh"
"$repo_root/scripts/check-a2a-sdk-version.sh"
"$repo_root/scripts/smoke-publish-wheel.sh"
"$repo_root/scripts/check-version.sh"

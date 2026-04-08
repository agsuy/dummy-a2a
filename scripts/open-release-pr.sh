#!/usr/bin/env bash
# Open a release PR from the current branch to main.
#
# With squash merge (repo default), the PR title becomes the commit that lands
# on main and is parsed by python-semantic-release to determine the version bump.
set -euo pipefail

repo_root="$(CDPATH='' cd -- "$(dirname "$0")/.." && pwd)"

usage() {
    cat <<'EOF'
Usage:
  scripts/open-release-pr.sh [--title "feat: description"] [--draft] [--dry-run]

Options:
  --title "..."   Override the PR title (default: inferred from commit types)
  --draft         Open as a draft PR
  --dry-run       Print the gh command without executing it
  -h, --help      Show this help
EOF
}

die() { echo "error: $*" >&2; exit 1; }

override_title=""
draft=false
dry_run=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --title)
            [[ $# -ge 2 ]] || die "--title requires a value"
            override_title="$2"; shift 2 ;;
        --draft)
            draft=true; shift ;;
        --dry-run)
            dry_run=true; shift ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            echo "unexpected argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

current_branch="$(git -C "$repo_root" rev-parse --abbrev-ref HEAD)"

if [[ "$current_branch" == "main" ]]; then
    die "already on main — check out dev or a release/* branch first"
fi

merge_base="$(git -C "$repo_root" merge-base HEAD main)"
commit_log="$(git -C "$repo_root" log --oneline "${merge_base}..HEAD")"
commit_subjects="$(git -C "$repo_root" log --format='%s' "${merge_base}..HEAD")"
commit_count="$(echo "$commit_subjects" | grep -c . || true)"

has_breaking=false
has_feat=false
has_fix=false

while IFS= read -r subject; do
    [[ -z "$subject" ]] && continue
    if echo "$subject" | grep -qE '^(feat|fix|refactor|perf)(\([^)]+\))?!:' ||
       echo "$subject" | grep -qi 'BREAKING CHANGE'; then
        has_breaking=true
    elif echo "$subject" | grep -qE '^feat(\([^)]+\))?:'; then
        has_feat=true
    elif echo "$subject" | grep -qE '^fix(\([^)]+\))?:'; then
        has_fix=true
    fi
done <<< "$commit_subjects"

if [[ -n "$override_title" ]]; then
    pr_title="$override_title"
elif [[ "$commit_count" -eq 1 ]]; then
    pr_title="$(echo "$commit_subjects" | head -1)"
elif $has_breaking; then
    pr_title="feat!: <describe the breaking change>"
elif $has_feat; then
    pr_title="feat: <describe the primary new capability>"
elif $has_fix; then
    pr_title="fix: <describe the primary fix>"
else
    pr_title="chore: <describe the change>"
fi

if [[ -n "$commit_log" ]]; then
    formatted_commits="$(echo "$commit_log" | sed 's/^/  - /')"
else
    formatted_commits="  _(no commits found ahead of main)_"
fi

pr_body="$(cat <<EOF
<details>
<summary>Commits (${commit_count})</summary>

${formatted_commits}

</details>

---
Merging triggers an automated release: version bump, changelog, tag, GitHub Release, and PyPI publish.
EOF
)"

if [[ "$pr_title" == *"<"* ]]; then
    echo ""
    echo "error: title requires a description — pass --title with a conventional commit." >&2
    echo ""
    echo "  Detected type : ${pr_title%%:*}:"
    echo "  Example       : scripts/open-release-pr.sh --title '${pr_title%%:*}: your description here'"
    echo ""
    exit 1
fi

if ! python3 "$repo_root/scripts/validate_commit_msg.py" --message "$pr_title"; then
    echo "" >&2
    echo "error: PR title must match scripts/validate_commit_msg.py (same check as .github/workflows/pr-title.yml)." >&2
    exit 1
fi

echo "source branch : $current_branch"
echo "commit count  : $commit_count"
echo "PR title      : $pr_title"

existing_pr_url="$(gh pr view "$current_branch" --json url,state --jq 'select(.state == "OPEN") | .url' 2>/dev/null || true)"

if [[ -n "$existing_pr_url" ]]; then
    echo "existing PR  : $existing_pr_url"
    gh_args=(
        pr edit "$current_branch"
        --title "$pr_title"
        --body "$pr_body"
    )
    action="update"
else
    gh_args=(
        pr create
        --base main
        --head "$current_branch"
        --title "$pr_title"
        --body "$pr_body"
    )
    $draft && gh_args+=(--draft)
    action="create"
fi

if $dry_run; then
    echo ""
    echo "── dry run ($action) ─────────────────────────────────────────────────"
    echo "gh ${gh_args[*]}"
    echo ""
    echo "── PR body ───────────────────────────────────────────────────────────"
    echo "$pr_body"
else
    gh "${gh_args[@]}"
fi

# Contributing

## Commit Guidelines

### Format

- Use [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
- Preferred format: `type(scope): subject`
- Omit `scope` when it does not add value.
- Keep the subject concise, imperative, and optimized for searchability.

Examples:

- `feat(core): add data validation`
- `fix(api): handle empty response`
- `docs: update installation guide`
- `chore(tooling): add repo workflow helpers`

### Strategy

- Keep commits atomic: one logical change per commit.
- Keep commits easy to revert or cherry-pick.
- Do not mix unrelated refactors, docs updates, tooling changes, and behavior changes in the same commit.

## Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

The version is declared in two places and must stay in sync:

- `pyproject.toml` (`project.version`)
- `src/dummy_a2a/__init__.py` (`__version__`)

Use `scripts/check-version.sh` locally to verify.

## Tooling

- **Python:** `3.12` or newer (`requires-python = ">=3.12"` in `pyproject.toml`).
- Use `pyenv` for interpreter pinning (optional but recommended).
- Use `uv` for environment management, dependency sync, and local tool execution.
- Prefer `uv run` for repo-local commands.

## Getting started (from zero)

1. **Clone** the repository and `cd` into it.
2. **(Optional)** Install and select Python with pyenv:
   ```bash
   pyenv install 3.12.12
   pyenv local 3.12.12
   ```
3. **Sync** the dev environment:
   ```bash
   uv sync --dev
   ```

After this, `uv run ...` and the `scripts/*.sh` helpers use the project `.venv`.

## Code style and static typing

- **Ruff** (lint + format): `scripts/lint.sh` applies fixes and formats; `scripts/lint-check.sh` checks without writing. Configuration is `[tool.ruff]` in `pyproject.toml`: line length **100**, rules **`E`, `F`, `I`**.
- **Pyright**: `scripts/type-check.sh` runs `uv run pyright` with `pyrightconfig.json`. Mode: **basic**; `reportMissingImports` is **error**.

## Local Workflow

After finishing a logical change, run:

1. `scripts/lint.sh`
2. `scripts/test.sh`
3. `scripts/lint-check.sh`
4. `scripts/type-check.sh`
5. `scripts/test.sh`
6. `scripts/check-a2a-sdk-version.sh` (PyPI has no newer **`a2a-sdk`** than the `==` pin in **`pyproject.toml`**)
7. `scripts/smoke-publish-wheel.sh` (included in `scripts/verify.sh` before `check-version.sh`)

`scripts/smoke-publish-wheel.sh` matches **Publish** CI: **`uv build`** then an **isolated** `python -c "import dummy_a2a"` with **only** the wheel (plus deps from package metadata). Use it to catch missing **`pyproject.toml`** dependencies before a release.

`scripts/verify.sh` runs the lint/test/type sequence above, **`check-a2a-sdk-version.sh`**, the wheel smoke step, then `check-version.sh`.

Use `scripts/commit.sh "<type>(<scope>): <subject>"` for conventional commits.

Run `scripts/install-git-hooks.sh` once per clone to enable local git hooks.

## License

By submitting a pull request, you agree that your contributions are licensed under the [Apache License 2.0](LICENSE).

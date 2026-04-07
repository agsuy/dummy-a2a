# dummy-a2a

A dummy a2a agent for testing.

## Install

```bash
# Development
uv sync --dev

# Optional: pin Python version with pyenv
pyenv install 3.12.12
pyenv local 3.12.12
```

## Development

### Local workflow

```bash
scripts/lint.sh           # auto-fix lint + format
scripts/test.sh           # run tests with coverage
scripts/lint-check.sh     # verify lint (no writes)
scripts/type-check.sh     # pyright
scripts/verify.sh         # all of the above
```

### Commits

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```bash
scripts/commit.sh "feat: add new feature"
scripts/commit.sh "fix(scope): resolve edge case" --body "Details here."
```

### Git hooks

```bash
scripts/install-git-hooks.sh   # one-time setup
```

- **pre-commit**: lint check
- **commit-msg**: conventional commit validation

### Release

```bash
scripts/open-release-pr.sh --title "feat: description"
```

Merging to `main` triggers automated release: version bump, changelog, tag, GitHub Release, and PyPI publish.

## Tooling

| Tool | Purpose |
|------|---------|
| [uv](https://docs.astral.sh/uv/) | Package management |
| [ruff](https://docs.astral.sh/ruff/) | Linter + formatter |
| [pyright](https://github.com/microsoft/pyright) | Type checker |
| [pytest](https://docs.pytest.org/) | Test framework |
| [python-semantic-release](https://python-semantic-release.readthedocs.io/) | Automated releases |

## License

[Apache License 2.0](LICENSE)

# Changelog

<!-- version list -->

## v0.6.0 (2026-04-11)

### Bug Fixes

- **ci**: Raise commit/PR title header limit to 100 chars
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

- **client**: Default A2A-Version 1.0 headers for JSON-RPC clients
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

- **server**: Build Starlette app with route helpers for a2a-sdk 1.0
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

### Chores

- **deps**: Bump a2a-sdk to 1.0.0a1 ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

### Documentation

- **readme**: Update contract count and extension catalog
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

### Features

- **contracts**: Add multi-extension activation compliance checks
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

- **extensions**: Add trace-id, priority, and locale test extensions
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))

- **extensions**: Multi-extension contracts and trace, priority, locale URIs
  ([#18](https://github.com/agsuy/dummy-a2a/pull/18),
  [`22f7cf1`](https://github.com/agsuy/dummy-a2a/commit/22f7cf1cdf0f2ccede59b7003e2778a0e6e30bf3))


## v0.5.0 (2026-04-09)

### Continuous Integration

- **sync-dev**: List open PRs with github-script ([#16](https://github.com/agsuy/dummy-a2a/pull/16),
  [`bd66bc6`](https://github.com/agsuy/dummy-a2a/commit/bd66bc61d8f37bbf7b88bac4c0f911f8694f72a2))

- **sync-dev**: List PRs with curl instead of gh ([#15](https://github.com/agsuy/dummy-a2a/pull/15),
  [`9bb58c3`](https://github.com/agsuy/dummy-a2a/commit/9bb58c379b24caec7e68319530c87da2ceb4efba))

### Documentation

- **readme**: Document extension plugins and update contract summary
  ([#17](https://github.com/agsuy/dummy-a2a/pull/17),
  [`e00f076`](https://github.com/agsuy/dummy-a2a/commit/e00f07650727a1ee7c825f1458d47bb2695cdb0f))

- **readme**: Update portable contract count to 41
  ([#17](https://github.com/agsuy/dummy-a2a/pull/17),
  [`e00f076`](https://github.com/agsuy/dummy-a2a/commit/e00f07650727a1ee7c825f1458d47bb2695cdb0f))

### Features

- **extensions**: A2APlugin for custom extensions
  ([#17](https://github.com/agsuy/dummy-a2a/pull/17),
  [`e00f076`](https://github.com/agsuy/dummy-a2a/commit/e00f07650727a1ee7c825f1458d47bb2695cdb0f))

- **extensions**: Add A2APlugin for registering custom extensions
  ([#17](https://github.com/agsuy/dummy-a2a/pull/17),
  [`e00f076`](https://github.com/agsuy/dummy-a2a/commit/e00f07650727a1ee7c825f1458d47bb2695cdb0f))


## v0.4.0 (2026-04-08)

### Continuous Integration

- Sync-dev workflow and release trim ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))

- **release**: Trim release workflow comments ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))

- **sync-dev**: Add workflow_dispatch for manual runs
  ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))

- **sync-dev**: Always reset dev to main after release
  ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))

- **sync-dev**: Skip reset when open dev to main PRs
  ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))

- **sync-dev**: Succeed when skipping sync for dev ahead of main
  ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))

### Features

- Recover dev integration lost to sync (#9-11) plus tooling
  ([#14](https://github.com/agsuy/dummy-a2a/pull/14),
  [`3ba499a`](https://github.com/agsuy/dummy-a2a/commit/3ba499a9287b273121f8e7ca972a6656bd6fafbd))


## v0.3.0 (2026-04-08)

### Continuous Integration

- **release**: Trim release workflow comments ([#12](https://github.com/agsuy/dummy-a2a/pull/12),
  [`d14c181`](https://github.com/agsuy/dummy-a2a/commit/d14c1819bc7ba462624f2d0c8b67937bf3698eb8))

### Features

- Merge dev with recovered integration and release tooling
  ([#12](https://github.com/agsuy/dummy-a2a/pull/12),
  [`d14c181`](https://github.com/agsuy/dummy-a2a/commit/d14c1819bc7ba462624f2d0c8b67937bf3698eb8))

- Recover dev integration lost to sync (#9-11) plus tooling
  ([#12](https://github.com/agsuy/dummy-a2a/pull/12),
  [`d14c181`](https://github.com/agsuy/dummy-a2a/commit/d14c1819bc7ba462624f2d0c8b67937bf3698eb8))


<!-- Releases through v0.2.0 were backfilled after PSR bootstrap; v0.2.1+ may include PSR-generated notes. -->

## v0.2.1 (2026-04-08)

### Bug fixes

- **changelog**: Add PSR insertion marker for semantic-release
  ([#13](https://github.com/agsuy/dummy-a2a/pull/13),
  [`1123f4c`](https://github.com/agsuy/dummy-a2a/commit/1123f4c4f8c9dde4a07f44449477298d10f5aee4))

### Continuous integration

- Require PSR CHANGELOG insertion marker ([#13](https://github.com/agsuy/dummy-a2a/pull/13),
  [`1123f4c`](https://github.com/agsuy/dummy-a2a/commit/1123f4c4f8c9dde4a07f44449477298d10f5aee4))


## v0.2.0 (2026-04-08)

### Features

- Concurrent contracts, server logging, and uv-based Docker image ([#6](https://github.com/agsuy/dummy-a2a/pull/6),
  [`dfb899b`](https://github.com/agsuy/dummy-a2a/commit/dfb899b))

### Continuous integration

- a2a-sdk freshness check and README pin badges ([#5](https://github.com/agsuy/dummy-a2a/pull/5),
  [`099b9bd`](https://github.com/agsuy/dummy-a2a/commit/099b9bd))

### Documentation

- Stabilize PyPI and license badges ([#4](https://github.com/agsuy/dummy-a2a/pull/4),
  [`5dc5c8c`](https://github.com/agsuy/dummy-a2a/commit/5dc5c8c))
- Distinguish Python versions badge from PyPI ([#3](https://github.com/agsuy/dummy-a2a/pull/3),
  [`6c70b34`](https://github.com/agsuy/dummy-a2a/commit/6c70b34))


## v0.1.2 (2026-04-08)

### Bug fixes

- Packaging for PyPI import; docs and local publish smoke ([#2](https://github.com/agsuy/dummy-a2a/pull/2),
  [`6506bb1`](https://github.com/agsuy/dummy-a2a/commit/6506bb1))


## v0.1.1 (2026-04-08)

### Documentation

- README enhancements, skill tidy-up, and CI import fixes ([#1](https://github.com/agsuy/dummy-a2a/pull/1),
  [`05b5fc0`](https://github.com/agsuy/dummy-a2a/commit/05b5fc0))


## v0.1.0 (2026-04-08)

### Features

- Add programmable dummy A2A agent and CLI ([`778c603`](https://github.com/agsuy/dummy-a2a/commit/778c603))
- Initial project scaffold ([`c20b4d0`](https://github.com/agsuy/dummy-a2a/commit/c20b4d0))

### Testing

- Add A2A HTTP and contract coverage ([`6b90383`](https://github.com/agsuy/dummy-a2a/commit/6b90383))

### Documentation

- Expand README for skills and usage ([`6c16256`](https://github.com/agsuy/dummy-a2a/commit/6c16256))

### Chores

- Add Dockerfile ([`86bfd6d`](https://github.com/agsuy/dummy-a2a/commit/86bfd6d))

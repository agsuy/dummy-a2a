# dummy-a2a review: linkedin readiness

Date: 2026-04-14

## Scope

Reviewed local repository state in `/Users/agusm3p/git/dummy-a2a`, focusing on:

- `README.md`
- `pyproject.toml`
- `src/dummy_a2a/server.py`
- `src/dummy_a2a/agent_card.py`
- `src/dummy_a2a/contracts.py`
- `tests/test_agent_card.py`
- `tests/test_plugin.py`
- `tests/test_contracts.py`

## Architecture note

No architecture document or architecture diagram was present in the repository at review time. That is a presentation gap for a protocol-testing project because first-time readers have to infer the moving pieces from the README and source.

## Validation summary

Local validation run on the reviewed branch:

- `./scripts/lint-check.sh`: passed
- `./scripts/type-check.sh`: passed
- `./scripts/test.sh`: passed
- Test result: `135 passed, 4 warnings`
- Coverage: `93.27%`

The warnings came from the concurrent contract test path and are called out below.

## Findings

### P1: Agent card can advertise an unusable endpoint

Files:

- `src/dummy_a2a/agent_card.py:205-210`
- `src/dummy_a2a/server.py:135-145`

`supportedInterfaces[0].url` is always rendered from constructor inputs as `http://{host}:{port}`. Because `DummyA2AServer.start()` builds the agent card before learning the actual bound port, the documented `port=0` mode can publish `:0`, and HTTPS servers can still publish `http://`.

Impact:

- clients that trust the advertised card instead of the fixture URL can be pointed at the wrong endpoint
- this affects a documented usage mode, not just an internal edge case

### P1: Extended card drops plugin skills

Files:

- `src/dummy_a2a/server.py:141-145`
- `src/dummy_a2a/agent_card.py:224-233`

The public card includes plugin skills, but the extended card is built with only `extra_extensions` and `[DEBUG_SKILL]`. A plugin can therefore appear in `/.well-known/agent-card.json` and disappear from `GetExtendedAgentCard`.

Impact:

- inconsistent card behavior for plugin consumers
- weakens one of the repo's main public claims: extension/plugin testing support

### P2: Concurrent contract mode is not warning-clean

Files:

- `src/dummy_a2a/contracts.py:923-932`
- `tests/test_contracts.py:19-29`

The concurrent isolated-server contract path passed functionally, but local `./scripts/test.sh` emitted `PytestUnraisableExceptionWarning` during `test_contracts_concurrent`.

Impact:

- concurrency story is green but not clean
- public claims about isolated concurrent verification are less convincing while coroutine shutdown warnings remain

### P3: README test count is stale

File:

- `README.md:623-629`

The development section still says `114 tests`, while the local validation run passed `135` tests.

Impact:

- avoidable trust friction on a repo meant to be shared publicly
- stale headline metrics make readers wonder what else is outdated

## Good

- This is real engineering work, not portfolio filler.
- The repo has working packaging, CI, release tooling, changelog discipline, and a coherent PyPI story.
- The README explains the value proposition quickly and the plugin examples are concrete.
- The test suite is substantial and coverage is strong.
- The codebase is small enough to inspect without feeling toy-level.

## Bad

- The default public branch appears to lag the branch under active development. Based on local refs, `origin/HEAD` points to `main`, while local `dev` is ahead.
- There is no architecture diagram or architecture note to orient first-time readers.
- The package still declares alpha maturity in `pyproject.toml`, which is fine technically but should shape how it is presented publicly.

## Ugly

- The advertised agent-card endpoint can be wrong in documented modes.
- The extended-card/plugin inconsistency undercuts the extension plugin story.
- The concurrent verification path is passing but noisy.

## LinkedIn readiness verdict

Not quite ready to share as-is.

The project is technically share-worthy, but the public impression still has avoidable sharp edges. The recommended order before posting is:

1. Fix the two card-related correctness issues.
2. Clean up the concurrent contract warnings if feasible.
3. Update stale README metrics.
4. Merge or release the newer `dev` state so the default public branch reflects the stronger version of the project.
5. Add a small architecture note or diagram so the repository explains itself faster.

After that, the repository should be in good shape to share publicly.

## Caveat

Live GitHub verification was not possible from the review environment because outbound GitHub access was blocked. The default-branch assessment above is therefore based on local git refs rather than a fresh network fetch.

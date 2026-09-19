# AKS Azure skills implementation notes

Implementation branch: `feature/aks-azure-skills`.
Reviewed source revision: `25c78cddd71919b316bda7df8a9fbcc845800178`.
Base: `ebade7308a`; implementation began after plan commit `83dfbd2168`.

[Design](../specs/2026-09-18-aks-azure-skills-design.md) ·
[Implementation plan](../plans/2026-09-18-aks-azure-skills.md)

## What changed

Added one native-Python ACS skills helper and unit tests, plus narrowly scoped
changes to `k8s_install_cli`, argument registration, command help, and orchestration
tests. Existing kubectl/kubelogin download implementations and dependency manifests
are unchanged. All five implementation tasks passed their spec/quality gates.

The command now offers an interactive, default-No skills installation after both
binaries succeed. It detects Claude Code, Codex, GitHub Copilot, and Pi, preselects
detected agents, and accepts a replacement comma-separated selection. A final
confirmation shows destinations, skills-only scope, and shared-discovery caveats.
Consent details remain visible with `--only-show-errors` or its core config setting.

```bash
# Offer skills interactively after installing binaries.
az aks install-cli

# Preserve binary-only behavior without an offer.
az aks install-cli --install-azure-skills false

# Explicit installation without prompts.
az aks install-cli --install-azure-skills true --skills-agents claude-code codex github-copilot pi
```

These describe the implemented branch, not a globally installed/released CLI.
No actual user agent home or default binary location was changed by verification.

## How it works

1. Validate explicit skills options before architecture selection or binary writes.
2. Run the existing binary installers in their existing order with unchanged arguments.
3. Skip an omitted skills option without a TTY, with disabled confirmations, or under
   sudo. Explicit false performs no skills work; explicit true requires targets and
   is rejected under sudo.
4. After consent/explicit opt-in, resolve the latest stable `microsoft/azure-skills`
   release to a commit. Use `--gh-token` only for new trusted GitHub metadata requests;
   keep archive retrieval token-free and bound responses at the transport boundary.
5. Validate and stage complete skill trees, retaining nested resources and upstream
   license notices. Enforce archive path/type/collision/size/count checks and actual
   selected-member lengths; execute none of the downloaded content.
6. Inspect original destination ancestors before normalization. Use cooperative
   locks and sibling staging; install absent trees, skip identical trees, and report
   conflicting existing content without replacing it.
7. Report source provenance and per-path results. Optional failure leaves binary
   success intact; explicitly requested skills failures return nonzero.

## Important decisions and limitations

- No Node/npm, Git, new runtime dependency, agent installation, MCP setup, hooks,
  updater, uninstall command, or persisted installation manifest.
- Codex uses the documented shared `~/.agents/skills` location. Other agents may
  discover those skills even when deselected; selection controls destinations,
  not agent enable/disable configuration.
- This is first-install-only. Each invocation resolves latest again; an advancing
  release can conflict with existing skills or leave mixed versions after partial
  installation. Recovery guidance preserves modifications and asks users to review
  and move selected directories to backups, never delete an entire skills root.
- Filesystem locks serialize cooperative installers; this is not a sandbox against
  a hostile local process that can concurrently modify the same user directories.
- Successful file installation does not establish that every upstream workflow
  works in every agent without separately configured tools.

## Rulings made during execution

Listed in the order made, including their trade-offs:

1. **Enforce HTTP deadlines below buffering.** A real slow-trickle probe disproved
   the plan's cooperative-only example. Preserve the configured bounds while
   enforcing the remaining budget at socket reads. Cost if wrong: extra transport
   complexity or rejection of slow downloads.
2. **Preserve lexical paths until safety inspection.** Early normalization erased
   a symlink followed by `..`. Normalize only after ancestor validation. Cost if
   wrong: displayed override paths may retain `..` and discovery expectations differ.
3. **Run controller-owned final gates after task commits/reviews.** This allows
   committed-diff reviews without worker-spawned duplicate reviewers. Cost if wrong:
   additional final-fix commits rather than a single integration commit.
4. **Validate metadata at top-level skill entry points only.** The real release has
   three nested onboarding guides named `SKILL.md` without frontmatter; they are
   explicitly not directly user-routable. Preserve them byte-for-byte. Cost if wrong:
   malformed nested standalone definitions remain upstream content for agents to
   handle; archive safety protections are unchanged.
5. **Consolidate whole-branch and polish analysis into one independent pass.** This
   follows the global single-pass review convention and avoids duplicate broad
   reviews, while including general quality, silent failures, comments, and types.
   Cost if wrong: fewer independent perspectives, mitigated by per-task reviews.

Additional review fixes did not change the design: reject CRC-valid but short ZIP
members, and keep interactive consent disclosures visible under quiet logging.

## Verification actually performed

Environment: Linux, `/opt/az/bin/python3` (Python 3.14), with the three worktree
source packages prepended to `PYTHONPATH`. Final source verification:

```bash
export PYTHONPATH="$PWD/src/azure-cli:$PWD/src/azure-cli-core:$PWD/src/azure-cli-telemetry"
/opt/az/bin/python3 -B -m unittest -q \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills \
  azure.cli.command_modules.acs.tests.latest.test_custom \
  azure.cli.command_modules.acs.tests.latest.test_validators
```

**398 tests run: 396 passed, 2 skipped.** Skips are the native Windows junction test
and the pre-existing kubelogin custom-source test. Existing mocked-HTTPError
ResourceWarnings and datetime deprecation warnings remain; unrelated fixtures were
not changed.

```bash
ruff check --no-cache --target-version py310 --select E,F --ignore E501,E722,F401,F811 \
  src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/_params.py \
  src/azure-cli/azure/cli/command_modules/acs/_help.py \
  src/azure-cli/azure/cli/command_modules/acs/custom.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_custom.py
git diff --check ebade7308a..HEAD
```

Both passed. Ruff is an additional E/F check using repository ignores, not a claim
that `azdev style` or `azdev linter` ran.

Temporary verification scripts also passed on final source:

- `task-5-live-smoke.py`: actual release `v1.2.49`, commit
  `abaf74ac8f62fbe9f83d7ccb2bd991dca929a4da`; 28 first installations, then 28
  identical no-ops; all 926 original payload files and 10 nested `SKILL.md` files
  byte-matched against the ZIP. All trees retained notices. Temporary state removed.
- `task-5-terminal-smoke.py`: five real pseudo-terminal scenarios covering decline,
  replacement/re-prompt, final decline, prompt interruption, and retrieval interruption.
- `final-fix-pty-smoke.py`: both real quiet-mode configurations kept consent details
  visible before final confirmation. Final decline caused no retrieval or skill writes.

Each script was invoked with `/opt/az/bin/python3 -B` and the source overlay from the
plan's ignored SDD workspace. They were review-time probes, not shipped utilities.
Committed tests retain the associated behavior regressions.

The independent final review and scoped fix re-review found no remaining
Critical/Important issues. Proactive polish ran in fix mode; it identified no safe
behavior-preserving auto-fixes. Its behavioral finding was fixed, regression-tested,
and independently re-reviewed rather than applied as an unchecked cleanup.

Not run: native Windows/macOS execution, Python 3.10 runtime, full Azure CLI/azdev
ACS suites and azdev style/linter, or actual agent/MCP workflows. Native runners and
azdev tooling were unavailable; no global dependencies were installed. These remain
verification limits, not implied passing gates.

## Reviewer focus

Check default-command compatibility, consent under quiet logging, credential and
redirect isolation, transport deadlines, lexical-path inspection, no-clobber
publication/cleanup, and the first-install recovery contract. Cross-platform runtime
coverage is the most useful next verification before broad release.

## Knowledge check

1. Which invocations skip prompting, and which reject invalid input before binary installation?
2. Why can selecting Codex expose skills to agents that were deselected?
3. What happens when a later upstream release differs from already installed content?
4. Which requests can receive the GitHub token, and how are response deadlines enforced?
5. Why are nested `SKILL.md` documents preserved without requiring standalone frontmatter?

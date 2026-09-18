# Optional Azure skills installation in `az aks install-cli`

## Goal and agreed scope

Offer Microsoft Azure skills installation after the existing kubectl and
kubelogin installation. Implement it natively in Python, with no Node/npm, Git,
external installer, or new interactive-UI dependency. Support Claude Code,
Codex, GitHub Copilot, and Pi using user-level skill locations.

Install complete skill directories, including their supporting resources, but
not the Azure plugin's MCP configuration, hooks, or agent applications. Some
skills require tools the user must configure separately; installation does not
promise that every Azure workflow is executable in every agent.

## Interactive experience

Preserve the existing binary installation order. Only after both installations
succeed, offer the optional step with a default of **No**:

```text
Install Microsoft Azure skills for your coding agents? [y/N]: y

Select agents:
  1. Claude Code       detected, selected
  2. Codex             detected, selected
  3. GitHub Copilot    not detected
  4. Pi                detected, selected

Enter agent numbers, comma-separated.
Enter keeps [1,2,4]; "none" skips: 1,4
```

Use Knack's existing yes/no and text prompts. The numbered selector is a small
parser, not a checkbox widget. A supplied list replaces the detected defaults;
duplicates are collapsed, surrounding whitespace is ignored, and invalid or
out-of-range entries cause a helpful re-prompt. Empty input retains defaults.
When nothing is detected, empty input skips. `none` skips regardless of defaults.
No agent is mandatory, and undetected agents remain selectable.

Show the selected destinations, shared-discovery warning where applicable, and
skills-only limitation before a final default-No confirmation. Download skill
content only after confirmation. Declining or cancelling the optional prompts
leaves the completed binary installation intact and performs no skill writes.
Do not persist prompt answers or a "don't ask again" preference in v1.

## Command-line and automation contract

Add these options to the existing command:

- `--install-azure-skills`: a three-state flag. Omitted means offer interactively;
  bare flag or `true` requests installation; `false` disables it.
- `--skills-agents`: a space-separated list of `claude-code`, `codex`,
  `github-copilot`, and `pi`. Requires explicit `--install-azure-skills true`.

Extend the existing `--gh-token` help to cover Azure skills release/commit API
lookups as well as kubelogin. Do not add a separate skills token option or change
existing kubelogin authentication behavior. The new skills request policy is
specified below.

Explicit true requires a nonempty agent list and bypasses the prompts. Validate
these arguments before installing binaries, so invalid combinations do not
perform partial work. Explicit false performs no skill detection, network
requests, prompts, or writes.

For the omitted option, skip skills when stdin is not a TTY, confirmation prompts
are disabled through `core.disable_confirm_prompt`, or the process is running
under sudo. Prompt suppression is never consent. Follow Azure CLI's TTY/config
convention rather than guessing from arbitrary CI environment variables; jobs
with a pseudo-TTY should pass `--install-azure-skills false` explicitly.

Under sudo, explain that skills should be installed unprivileged, with
user-writable binary locations if rerunning this command. Reject an explicit
skills installation under sudo before binary installation. Do not infer an
invoking user's home, change ownership, or write through to that user's files.
Outside sudo, display and use the current user's resolved destinations.

## Agent detection and destinations

Detection is a filesystem heuristic used only for defaults, not proof an agent
is installed or a restriction on selection. Check for configuration directories,
not merely any filesystem entry. An explicit config override replaces its
corresponding default, including when that override does not exist yet.

| Agent identifier | Detection directory | Skill destination |
| --- | --- | --- |
| `claude-code` | `CLAUDE_CONFIG_DIR`, otherwise `~/.claude` | `<config>/skills` |
| `codex` | `CODEX_HOME`, otherwise `~/.codex`; also recognize `/etc/codex` on Unix | `~/.agents/skills` |
| `github-copilot` | `~/.copilot` | `~/.copilot/skills` |
| `pi` | `PI_CODING_AGENT_DIR`, otherwise `~/.pi/agent` | `<config>/skills` |

Use platform-aware home/path handling on Windows, macOS, and Linux. Normalize
and deduplicate destinations before writing when overrides coincide.

Codex documents `~/.agents/skills` as its user location. Its old
`$CODEX_HOME/skills` root is explicitly deprecated in current upstream source,
so do not build new behavior on that root. Pi and Copilot also discover the
shared location. The selector and help must disclose that selecting Codex can
make skills visible to those agents even when they are deselected. Selection
controls installation destinations, not agent enable/disable configuration.

Do not scan all project directories, modify agent settings, or try to suppress
skills already discoverable through user-defined paths or installed plugins.

## Source and installation safety

Use the published `microsoft/azure-skills` distribution, not the development
repository. Resolve its latest stable GitHub release only after consent or
explicit opt-in, resolve that release tag to a commit, and download the archive
for that commit. Once resolved, report the repository, release, and commit before
skill writes and in the final summary, including partial-failure summaries. These
identify this attempt's source, not the origin of conflicting existing content.
Do not add an arbitrary source URL, automatic update, or version-management
interface in v1. TLS and the fixed upstream repository are the trust boundary;
this does not claim an independently signed or immutable release artifact.

Reuse an explicitly supplied `--gh-token` only for the new skills metadata
requests to the fixed repository on `https://api.github.com`. Anonymous lookup
remains supported when no token is supplied. Do not send the token with archive
requests, forward it to other origins, or include it in logs or errors. Reject
cross-origin redirects for authenticated metadata requests rather than forwarding
authorization. This policy applies to the new skills requests; it does not
refactor the existing kubelogin download path.

For metadata HTTP 403/429 responses, report the failed operation and status and
include rate-limit/reset or retry guidance when supported by response metadata.
Do not label every 403 as rate limiting: authorization failures require guidance
to check the supplied token's access. For anonymous rate limiting, recommend
retrying after the limit resets or supplying `--gh-token`; authenticated rate
limiting should recommend waiting rather than merely supplying another token.
Fail the skills step using the optional-versus-explicit status policy below;
do not silently fall back to an unversioned branch or retry indefinitely.

Only install the payload under `.github/plugins/azure-skills/skills/`. Preserve
each skill's relative resource layout. Validate the expected skill structure
and reject unsafe archive members, traversal, absolute paths, links, duplicate
or platform-colliding paths, and excessive downloads/extracted sizes or counts.
Set finite download timeouts and resource limits; do not use an unrestricted
`extractall()` as the installation policy. Retain applicable upstream license
notices with the installed content. Do not execute downloaded scripts.

Stage and validate before publishing complete skill directories. Do not merge
into or overwrite an existing skill directory, including a symlink. Identical
existing content is an already-installed no-op; conflicting content is left
untouched and reported. Clean temporary files on failure. Avoid writing through
symlinked skill destinations in v1; report this limitation rather than guessing
ownership. Do not create shared canonical symlinks between agent directories.

## First-install lifecycle and manual recovery

V1 is a first-install-only facility, not an updater or a resumable transaction.
The no-op/idempotency guarantee applies to unchanged content from the same
resolved bundle. Every invocation resolves latest again: if a release advances,
previously installed skills may conflict, and a partial-install retry may leave
skills from multiple releases. State this limitation in command help and conflict
messages; do not promise that an explicit retry restores a coherent bundle.
There is no persisted installation manifest or retained commit for retries in v1.

For conflicts, provide the affected paths and this manual recovery guidance:

1. Review the reported destinations and preserve any user modifications. Do not
   assume conflicting files were created or are owned by this command.
2. If replacement is wanted, move only the reviewed Azure skill directories to
   a backup outside all agent skill discovery paths. To replace a partial or
   mixed-version bundle coherently, review and back up its other Azure skill
   directories too, not just those named as conflicts. Do not remove the entire
   skills root or unrelated skills; shared-directory changes affect other agents.
3. Rerun with `--install-azure-skills true --skills-agents <selected agents>`.
   Explain that this also reruns binary installation and resolves the then-current
   release. Preserve backups until the new installation has been checked.

No automatic deletion, replacement, backup migration, or ownership inference is
introduced by this guidance. A network-only retry can rerun directly, but must
still disclose that the selected release may have changed.

## Outcomes and failure handling

Report installed, already present, skipped/conflicting, and failed results with
their destinations. Do not call a partial installation complete. Keep successful
skill directories if a later directory fails; never undo completed binaries or
unrelated files. Skip identical completed directories on a same-bundle rerun;
use the lifecycle and recovery guidance above if upstream content has changed.

- Binary failure: preserve existing failure behavior; do not attempt skills.
- Declined/cancelled automatic offer: normal binary-install success.
- Failure or conflict in the automatic optional step: clear warning and normal
  binary-install success, including cause-specific retry or manual recovery
  guidance rather than an unconditional instruction to rerun.
- Failure or conflict with explicit skill installation: nonzero exit status,
  clearly stating whether binaries or some skills were already installed.

## Implementation boundaries

Keep `k8s_install_cli` as the orchestrator, delegating optional skill work to one
focused ACS helper module. Register arguments and help in the existing ACS files.
Do not refactor unrelated binary download helpers or introduce a generic plugin
manager. Unit-test detection, selection, safe installation, and orchestration
using mocked prompts/network and temporary homes; do not touch real agent homes.

## Acceptance and verification

- Existing binary tests remain valid; both binary calls keep their arguments and
  ordering, and omitted noninteractive execution performs no skill work.
- Cover true/false/omitted flags, invalid combinations, prompt suppression,
  no-TTY, sudo, cancellation, and explicit versus optional failure status.
- Cover detected defaults, no detections, replacement selections, duplicates,
  invalid input, all four targets, environment overrides, and shared-path notices.
- Cover safe extraction, unexpected payloads, network errors, resource limits,
  filesystem permissions, existing identical/conflicting files, symlinks,
  partial success, cleanup, and same-bundle idempotent reruns.
- Cover a release advancing between successful or partial installation attempts:
  existing content stays untouched, conflicts and mixed-version risk are reported,
  and manual recovery guidance does not imply automatic updates or deletion.
- Cover anonymous/authenticated metadata requests, expanded `--gh-token` help,
  rejection of cross-origin authenticated redirects, token-free archive requests
  and logs, and 403/429 guidance for anonymous limits, authenticated limits, and
  authorization failures. Preserve existing kubelogin authentication tests.
- Check Windows path rules in unit tests and run platform-specific smoke checks
  where available. Exercise the numbered selector in a terminal.
- Validate a real released payload in a temporary destination without installing
  into actual agent homes. Check supporting-resource preservation and document
  MCP-dependent functionality as outside this installation's guarantee.
- Run focused ACS tests and relevant lint/style checks after implementation.
  Report unavailable tooling or platforms rather than claiming unrun checks.

## Evidence and review notes

- Existing orchestration: `src/azure-cli/azure/cli/command_modules/acs/custom.py`,
  `k8s_install_cli`; arguments and binary defaults in `_params.py`.
- Installed Knack 0.14.0 provides yes/no, text, and single-choice prompts, not a
  checkbox/multi-select widget. Read-only mocked probes confirmed this behavior.
- Three-state flag behavior: `azure.cli.core.commands.parameters.get_three_state_flag`.
- Existing GitHub token help: ACS `_params.py:1026`; kubelogin authenticated
  release lookup and rate-limit fallback: `custom.py:2585–2620`, with tests in
  `tests/latest/test_custom.py:822–884`. New skills requests need their own
  explicit credential/redirect policy without changing those existing behaviors.
- Distribution and upstream installation guidance:
  <https://github.com/microsoft/azure-skills>.
- Agent discovery reference implementation:
  <https://github.com/vercel-labs/skills/blob/main/src/agents.ts>.
- Codex documented location: <https://developers.openai.com/codex/skills/>;
  deprecated root evidence:
  <https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/host_roots.rs>.
- Claude personal skills: <https://code.claude.com/docs/en/skills>.
- Copilot personal skills:
  <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>.
- Pi locations and override: installed Pi `docs/skills.md` and
  `docs/environment-variables.md`.

This document defines the proposed v1 behavior. Source implementation and
repository test execution have not started; written-spec approval precedes the
implementation plan.

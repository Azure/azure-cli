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
for that commit. Report the release and commit in the installation summary.
Do not add an arbitrary source URL, automatic update, or version-management
interface in v1. TLS and the fixed upstream repository are the trust boundary;
this does not claim an independently signed or immutable release artifact.

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

## Outcomes and failure handling

Report installed, already present, skipped/conflicting, and failed results with
their destinations. Do not call a partial installation complete. Keep successful
skill directories if a later directory fails; never undo completed binaries or
unrelated files. A rerun can safely skip identical completed directories.

- Binary failure: preserve existing failure behavior; do not attempt skills.
- Declined/cancelled automatic offer: normal binary-install success.
- Failure or conflict in the automatic optional step: clear warning and normal
  binary-install success, including guidance for explicit retry.
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
  partial success, cleanup, and idempotent reruns.
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

---
name: appconfig-release-process
description: Format PR titles/changelog notes correctly for az appconfig changes (HISTORY.rst is auto-generated, never hand-edited) and bump the azure-mgmt-appconfiguration SDK dependency version. Use when finishing a PR for appconfig or when a change needs newer SDK functionality.
license: MIT
---
<!-- cspell:words appconfig azconfig configstore kwargs -->
# appconfig-release-process skill

Scope: how appconfig changes get released — PR title/changelog
conventions and SDK dependency version bumps. Grounded in
`doc/authoring_command_modules/README.md` ("Submitting Pull Requests")
and `doc/how_to_bump_SDK_version_in_cli.md` — treat both as authoritative
alongside the rules below.

## Changelog — do NOT hand-edit `src/azure-cli/HISTORY.rst`

`HISTORY.rst` entries are auto-generated from the PR title/description
starting from S165 (01/30/2020) — they are not edited directly in normal
PRs. Instead, the PR title must follow this format:

```
[Component Name] [BREAKING CHANGE: |Fix #N: ]<optional az command:> <Verb> <description>
```

- **`[Component Name]`** (e.g. `[App Configuration]`) = customer-facing;
  the message goes into `HISTORY.rst`. **`{Component Name}`** (curly
  braces) = not customer-facing; excluded from `HISTORY.rst`. This part
  is mandatory in every PR title.
- If it's a breaking change, the second part is `BREAKING CHANGE:`. For a
  hotfix, use `Hotfix`. For an issue fix, use `Fix #<number>`. Otherwise
  this part can be empty.
- Recommended: include the affected command starting with `az`, followed
  by a colon (e.g. `az appconfig create:`).
- Recommended: use a present-tense, capitalized, base-form verb:
  - `Add` — new features.
  - `Change` — changes to existing functionality.
  - `Deprecate` — once-stable features slated for removal.
  - `Remove` — deprecated features removed in this release.
  - `Fix` — bug fixes.

Examples:
```
[App Configuration] BREAKING CHANGE: az appconfig create: Remove --deprecated-arg
[App Configuration] Fix #12345: az appconfig kv list: Fix pagination for large stores
{App Configuration} Add help example for kv set
```

- For **multiple** history notes from one PR, or to **override** the
  title-derived note, use the `History Notes` section of the PR
  description (the PR template already includes this section — delete it
  if not needed). The PR title still must start with
  `[Component Name]`/`{Component Name}` even if it's just a summary in
  this case.
- **Hotfix PRs** (based on the `release` branch) are the *only* case
  where `HISTORY.rst` is manually edited, and only for customer-facing
  changes — the auto-generation process ignores PRs whose title contains
  `Hotfix`. Confirm with the user before treating a change as a hotfix;
  it's rare and follows a distinct branch/merge workflow (merge
  `release` back to `dev` with a merge commit, never squash).

## SDK dependency version bumps

If a change needs new functionality from `azure-mgmt-appconfiguration`
(or a data-plane SDK) that isn't in the currently pinned version:

1. Bump the version in `src/azure-cli/setup.py` and all three
   per-OS requirement files: `requirements.py3.windows.txt`,
   `requirements.py3.Linux.txt`, `requirements.py3.Darwin.txt`.
2. Only if the SDK is **multi-API-profile aware**: update the pinned API
   version in `AZURE_API_PROFILES` for the `'latest'` profile in
   `azure-cli-core/azure/cli/core/profiles/_shared.py` (single API
   version as a plain string, or an `operation=version` mapping for
   `SDKProfile`-style multi-operation SDKs).
3. Run a regression check after bumping: `azdev test --no-exitfirst`
   (playback) to catch anything broken by the new SDK; failures that
   only reproduce live should be re-run with
   `azdev test --live --lf --no-exitfirst`.
4. Fix any regressions the bump surfaces, or add the new feature code
   that depends on the bumped SDK.
5. There is also an internal "Regression Test Pipeline" that automates
   steps 1–3 across the whole repo when bumping broadly-used SDKs — flag
   this option to the user if the bump is large/repo-wide rather than
   appconfig-specific, but for an appconfig-only bump, doing steps 1–4
   directly is usually simpler.

Do not assume unreleased SDK APIs exist without checking the actually
installed/pinned package version first.

## Guardrails

- Never hand-edit `HISTORY.rst` outside of a confirmed hotfix PR.
- Always surface the required PR title format to the user rather than
  silently choosing one — get their confirmation on the Component Name
  and BREAKING CHANGE/Fix # portion, since only they know the full PR
  context.
- When bumping an SDK version, update all three OS-specific requirements
  files together — never just one.

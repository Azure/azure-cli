# AKS Azure Skills Installation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Offer optional, native, user-level Azure skill installation after `az aks install-cli`, with agent detection, numbered selection, and explicit automation controls.

**Architecture:** Keep the existing command as the binary-install orchestrator and put the optional feature in one focused ACS helper. Separate discovery/selection, bounded retrieval, archive staging, and publication with small internal functions so each boundary has isolated tests. Do not change the existing kubectl or kubelogin download implementations.

**Tech Stack:** Python 3.10+, standard library, existing Knack prompts/errors/logging, existing PyYAML, `unittest` and mocks. No additional runtime dependency.

**Spec:** [2026-09-18-aks-azure-skills-design.md](../specs/2026-09-18-aks-azure-skills-design.md), incorporating the accepted independent-review findings in commit `b57a3515d6`.

## Global Constraints

The complete spec applies to every task. In particular:

- "Implement it natively in Python, with no Node/npm, Git, external installer, or new interactive-UI dependency."
- "Support Claude Code, Codex, GitHub Copilot, and Pi using user-level skill locations."
- "Install complete skill directories, including their supporting resources, but not the Azure plugin's MCP configuration, hooks, or agent applications."
- "Only after both installations succeed, offer the optional step with a default of **No**."
- "Explicit true requires a nonempty agent list and bypasses the prompts."
- "Prompt suppression is never consent."
- "Selection controls installation destinations, not agent enable/disable configuration."
- "Do not merge into or overwrite an existing skill directory, including a symlink."
- "V1 is a first-install-only facility, not an updater or a resumable transaction."
- "There is no persisted installation manifest or retained commit for retries in v1."
- "Do not send the token with archive requests, forward it to other origins, or include it in logs or errors."
- "Unit-test detection, selection, safe installation, and orchestration using mocked prompts/network and temporary homes; do not touch real agent homes."

---

## Evidence and highest-risk decisions

1. **Compatibility:** `custom.py:2378–2385` currently calls architecture detection, kubectl, then kubelogin. Append the skills step, but validate explicit skill arguments before those calls. An omitted option in a noninteractive process must not discover agents or make skill requests.
2. **Prompts:** installed Knack 0.14.0 uses line input. Use `prompt_y_n(default='n')` and `prompt()` with a comma-separated-number parser, not a new terminal widget. Handle `NoTTYException`, EOF, and interruption during optional prompts as skipping the optional feature.
3. **Ownership:** stage complete directories, compare existing content without following links, and never merge. New content from a later release is a conflict, not an update. Keep the spec's manual backup/replacement guidance and warn about cross-release partial retries.
4. **Credentials:** use a separate, bounded skills HTTP path. Existing ACS `_urlopen_read` has different token/redirect/size semantics and must not be reused or refactored for this feature. Extend `--gh-token` help; preserve its existing kubelogin behavior.
5. **Distribution:** a read-only inspection on 2026-09-18 resolved `v1.2.49` to `abaf74ac8f62fbe9f83d7ccb2bd991dca929a4da`. The ZIP was 8,978,396 bytes, with 2,583 entries and 13,847,533 advertised expanded bytes. Its skill payload had 926 files and 28 top-level skill directories, including nested `SKILL.md` files. Preserve nested trees; do not flatten or hard-code this skill inventory.
6. **Legal content:** the archive has a repository-root MIT `LICENSE`. Copy that notice into every staged top-level skill as `LICENSE.azure-skills`, retaining any skill-specific notices too. If that filename already exists with different content, fail staging instead of replacing upstream content. Compare installed content against the fully prepared tree, including the notice.
7. **Limits:** start with a 1 MiB metadata-response limit, 64 MiB ZIP download limit, 256 MiB aggregate expanded-size limit, 16 MiB per extracted file, 10,000 archive entries, and 32 path components. Use a 30-second socket timeout and a 120-second per-response read deadline. These comfortably exceed the inspected release; exceeding them is an actionable error, never an automatic limit increase.
8. **Filesystem concurrency:** serialize this command's publications per destination with an exclusive temporary sibling lock; an existing lock fails that destination and is not automatically removed as stale. Stage publication on the destination filesystem outside the skill discovery root, recheck paths immediately before publishing, and clean owned temporary state in `finally`. This is not a sandbox against a hostile process that can mutate the user's directories concurrently.

### File map

All paths below are relative to the worktree root.

| File | Responsibility |
| --- | --- |
| `src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py` (new) | Internal discovery, selection, retrieval, staging, publication, and optional-flow functions |
| `src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py` (new) | Unit tests using tiny synthetic ZIPs, fake responses, temporary roots, and mocked prompts |
| `src/azure-cli/azure/cli/command_modules/acs/custom.py` | Two appended arguments, preflight validation, and post-binary delegation in `k8s_install_cli` |
| `src/azure-cli/azure/cli/command_modules/acs/_params.py` | Three-state option, agent choices, expanded token help |
| `src/azure-cli/azure/cli/command_modules/acs/_help.py` | Interactive/automation examples, shared-path and first-install limitations |
| `src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_custom.py` | Command orchestration/order and unchanged binary argument tests |

Do not modify `_validators.py`, `commands.py`, dependency manifests, or binary download helpers. Cross-field validation can run at the beginning of the handler, before any binary side effect; the parser handles agent choices. Do not add a second namespace validator with duplicate policy.

### Test environment and baseline

Use the installed Azure Python with repository sources first, not the installed `az` executable:

```bash
cd /home/tng/workspace/azure-cli-worktrees/aks-azure-skills
export PYTHONPATH="$PWD/src/azure-cli:$PWD/src/azure-cli-core:$PWD/src/azure-cli-telemetry"
/opt/az/bin/python3 -B -c 'import azure.cli.command_modules.acs.custom as m; print(m.__file__)'
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_custom \
  -k k8s_install -k get_latest_kubelogin_version
```

The import must point into this worktree. The focused baseline was executed during planning: **12 tests run, 11 passed, 1 pre-existing skip** (`test_k8s_install_kubelogin_with_custom_source_url`). Python also emitted ResourceWarnings for existing mocked HTTP errors; do not fix unrelated tests in this change.

Plain `unittest` tests work without installing test tooling. `/opt/az/bin/python3` has the runtime and YAML, but not pytest, azdev, testsdk, or style tools. Full ACS test/style gates require a separate development environment, described in the final verification section; they were not run during planning.

## Task 1: Agent discovery, selection, and argument preflight

**Files:** Create `_azure_skills.py` and `tests/latest/test_azure_skills.py` at the paths above.

**Consumes:** only standard library, Knack `CLIError`, and existing Azure CLI argument-error classes.

**Produces:**

- `AGENT_IDS`: tuple `('claude-code', 'codex', 'github-copilot', 'pi')`.
- `AgentTarget(identifier: str, label: str, destination: Path, detected: bool)`: frozen dataclass.
- `discover_agents() -> list[AgentTarget]`: deterministic registry order; filesystem discovery only when called.
- `parse_agent_selection(value: str, defaults: list[str]) -> list[str]`: returns identifiers or raises `CLIError` for invalid input.
- `validate_skills_options(install_azure_skills: bool | None, skills_agents: list[str] | None) -> None`: rejects inconsistent options, unknown identifiers, explicit true without targets, and explicit installation under sudo.
- `_is_sudo() -> bool`: on Unix, conservatively recognize `SUDO_UID` or `SUDO_USER`; never infer the invoking user's home. Do not equate every root/admin process with sudo.

- [ ] **Step 1: Add failing selection and validation tests.** Use this import and test style in the new test module:

```python
import unittest
from unittest import mock
from pathlib import Path

from knack.util import CLIError
from azure.cli.command_modules.acs import _azure_skills as skills


class AgentSelectionTests(unittest.TestCase):
    def test_selection_replaces_detected_defaults(self):
        self.assertEqual(
            skills.parse_agent_selection(' 1, 4,1 ', ['codex']),
            ['claude-code', 'pi'])

    def test_empty_input_and_none(self):
        self.assertEqual(skills.parse_agent_selection('', ['codex']), ['codex'])
        self.assertEqual(skills.parse_agent_selection('', []), [])
        self.assertEqual(skills.parse_agent_selection('none', ['codex']), [])

    def test_invalid_selection(self):
        for text in ('0', '5', '-1', '1,,4', 'claude', '1.5'):
            with self.subTest(text=text), self.assertRaises(CLIError):
                skills.parse_agent_selection(text, [])

    @mock.patch.dict('os.environ', {}, clear=True)
    def test_explicit_install_requires_targets(self):
        with self.assertRaises(CLIError):
            skills.validate_skills_options(True, None)
        with self.assertRaises(CLIError):
            skills.validate_skills_options(False, ['pi'])
        with self.assertRaises(CLIError):
            skills.validate_skills_options(None, ['pi'])
```

Add discovery tests with patched `Path.home`, controlled `os.environ`, and mocked `os.path.isdir`; never depend on real `/etc/codex`. Assert the exact four destinations, nonblank config overrides, nonexistent overrides, directory-versus-file detection, and Unix system Codex detection. Empty/whitespace-only overrides count as unset. Use real temporary directories for one end-to-end discovery test.

- [ ] **Step 2: Run the new tests and record the expected missing-module/function failure.**

```bash
/opt/az/bin/python3 -B -m unittest -v azure.cli.command_modules.acs.tests.latest.test_azure_skills
```

- [ ] **Step 3: Implement the dataclass, registry, parser, and preflight.** Core selection logic:

```python
def parse_agent_selection(value, defaults):
    text = value.strip()
    if not text:
        return list(defaults)
    if text.lower() == 'none':
        return []
    parts = [part.strip() for part in text.split(',')]
    if any(part not in ('1', '2', '3', '4') for part in parts):
        raise CLIError('Enter agent numbers 1-4 separated by commas, or "none".')
    selected = {int(part) - 1 for part in parts}
    return [identifier for index, identifier in enumerate(AGENT_IDS)
            if index in selected]
```

Resolve home at call time. Use `CLAUDE_CONFIG_DIR` and `PI_CODING_AGENT_DIR` for both discovery and their destinations; use `CODEX_HOME` for detection only. Codex's destination remains `~/.agents/skills`. Copilot uses `~/.copilot/skills`. Expand a leading user-home marker in overrides and normalize relative paths against the current directory; do not inspect project skills. Do not create directories during discovery. Preflight is side-effect-free and does not call discovery.

- [ ] **Step 4: Run the new tests green, including explicit false, unknown IDs, and sudo cases.**
- [ ] **Step 5: Commit only the helper and its tests.**

```bash
git add src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py
git commit -m "feat(aks): add Azure skills agent selection and preflight"
```

## Task 2: Bounded release resolution and credential-safe download

**Files:** Modify the new helper and its test file.

**Consumes:** `CLIError` and standard `urllib`, `ssl`, `json`, `time`, and stream APIs. Do not import download helpers from `custom.py`.

**Produces:**

- `Release(tag: str, commit: str)`: frozen dataclass.
- `resolve_release(gh_token: str | None = None) -> Release`.
- `download_archive(release: Release, destination: Path) -> None`.
- `_api_json(path: str, gh_token: str | None) -> dict`: bounded metadata reads to the fixed repository API prefix.
- `_MetadataRedirectHandler`: rejects metadata redirects rather than risking credential propagation.
- `_copy_bounded(source, destination, limit: int) -> int`: bounded streaming with the configured read deadline.

- [ ] **Step 1: Add failing release tests, including annotated tags.**

```python
class ReleaseDownloadTests(unittest.TestCase):
    @mock.patch.object(skills, '_api_json')
    def test_annotated_tag_is_peeled_to_commit(self, api):
        commit = 'a' * 40
        tag_object = 'b' * 40
        api.side_effect = [
            {'tag_name': 'v1.2.49', 'draft': False, 'prerelease': False},
            {'object': {'type': 'tag', 'sha': tag_object}},
            {'object': {'type': 'commit', 'sha': commit}},
        ]
        result = skills.resolve_release('test-token')
        self.assertEqual(result, skills.Release('v1.2.49', commit))
        self.assertEqual(api.call_args_list, [
            mock.call('/releases/latest', 'test-token'),
            mock.call('/git/ref/tags/v1.2.49', 'test-token'),
            mock.call('/git/tags/' + tag_object, 'test-token'),
        ])
```

Also test a lightweight tag, malformed JSON/fields, unsafe or empty tags, invalid commit SHAs, unsupported object types, and more than five annotated-tag hops. Add fake-opener tests that inspect actual Request headers for metadata versus archives; mocking only `resolve_release` is insufficient to prove token isolation. Exercise `_MetadataRedirectHandler.redirect_request` with a token-bearing Request and a cross-origin destination and assert rejection before another request.

- [ ] **Step 2: Run `ReleaseDownloadTests` red.**

```bash
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills.ReleaseDownloadTests
```

- [ ] **Step 3: Implement fixed-origin retrieval and release peeling.** The URL policy and core peeling algorithm are:

```python
API_ROOT = 'https://api.github.com/repos/microsoft/azure-skills'
ARCHIVE_ROOT = 'https://codeload.github.com/microsoft/azure-skills/zip/'
```

```python
def resolve_release(gh_token=None):
    release = _api_json('/releases/latest', gh_token)
    tag = release.get('tag_name')
    if (not isinstance(tag, str) or not tag or len(tag) > 255 or
            any(ord(char) < 32 for char in tag) or
            release.get('draft') is not False or
            release.get('prerelease') is not False):
        raise CLIError('GitHub returned an invalid stable Azure skills release.')
    obj = _api_json('/git/ref/tags/' + quote(tag, safe=''), gh_token).get('object')
    for depth in range(6):
        if not isinstance(obj, dict):
            break
        sha = obj.get('sha')
        if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-fA-F]{40}', sha):
            break
        if obj.get('type') == 'commit':
            return Release(tag, sha.lower())
        if obj.get('type') != 'tag' or depth == 5:
            break
        obj = _api_json('/git/tags/' + sha, gh_token).get('object')
    raise CLIError('Could not resolve the Azure skills release tag to a commit.')
```

Import `quote` from `urllib.parse` and `re` in the helper. Ignore response-provided `url`, `zipball_url`, and `target_commitish`; build both metadata paths and the archive URL locally. Use a metadata opener with default TLS/proxy handling and this handler:

```python
class _MetadataRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise CLIError('Unexpected redirect while resolving Azure skills metadata.')
```

Import `HTTPRedirectHandler` from `urllib.request`. Implement `_copy_bounded` with the following behavior (Task 3 consumes the same function, not a second implementation):

```python
def _copy_bounded(source, destination, limit):
    deadline = time.monotonic() + 120
    written = 0
    while True:
        if time.monotonic() > deadline:
            raise CLIError('Azure skills response exceeded the read deadline.')
        chunk = source.read(min(65536, limit - written + 1))
        if not chunk:
            return written
        written += len(chunk)
        if written > limit:
            raise CLIError('Azure skills content exceeded the size limit.')
        destination.write(chunk)
```

Use a separate token-free opener for archives. Permit archive redirects only to HTTPS on `codeload.github.com` and reject other origins; the archive request must never carry Authorization. Stream using 64 KiB chunks with size/deadline checks; check both advertised and actual sizes. Close responses on every path and remove incomplete archive files on failure. Use `ssl.create_default_context()` and a finite socket timeout; do not disable certificate checks.

Map HTTP errors to safe messages naming the operation, HTTP status, and guidance. A 429 is rate limiting; a 403 needs rate-limit headers or an explicit rate-limit indication in a bounded response body before calling it a rate limit. Distinguish anonymous limits, authenticated limits, and access failures. Never print the supplied token, raw request headers, or unfiltered server error bodies; parse reset/retry metadata as bounded numeric values. No unversioned fallback or unbounded retry.

- [ ] **Step 4: Run transport tests green, including oversized/chunked responses, deadline expiry, failed TLS/network requests, 403/429 variants, token-bearing fake error bodies, and partial-file cleanup.**
- [ ] **Step 5: Run all helper tests, then commit helper and tests.**

```bash
/opt/az/bin/python3 -B -m unittest -v azure.cli.command_modules.acs.tests.latest.test_azure_skills
git add src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py
git commit -m "feat(aks): retrieve Azure skills with bounded authenticated metadata"
```

## Task 3: Validate and stage complete skill trees

**Files:** Modify the helper and its test file.

**Consumes:** archive `Path`, an unused staging directory path, `_copy_bounded`, existing `yaml.safe_load`.

**Produces:** `stage_bundle(archive: Path, staging: Path) -> list[Path]`, returning sorted top-level staged skill directories. No user destination is touched.

- [ ] **Step 1: Add a reusable synthetic archive fixture and failing preservation/security tests.**

```python
import tempfile
import zipfile


def make_bundle(path, files=None):
    if files is None:
        files = {
            'demo/SKILL.md': '---\nname: demo\ndescription: Test skill\n---\n',
            'demo/references/guide.md': 'Reference content\n',
            'demo/child/SKILL.md': '---\nname: child\ndescription: Nested skill\n---\n',
        }
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('bundle/LICENSE', 'MIT License\nTest fixture copyright\n')
        for relative, content in files.items():
            archive.writestr('bundle/.github/plugins/azure-skills/skills/' + relative, content)
        archive.writestr('bundle/.github/plugins/azure-skills/.mcp.json', '{}')
        archive.writestr('bundle/.github/plugins/azure-skills/hooks/hooks.json', '{}')


class ArchiveTests(unittest.TestCase):
    def test_preserves_nested_resources_and_license_not_plugin_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'bundle.zip'
            make_bundle(archive)
            trees = skills.stage_bundle(archive, root / 'staged')
            self.assertEqual([tree.name for tree in trees], ['demo'])
            self.assertEqual((trees[0] / 'references/guide.md').read_text(), 'Reference content\n')
            self.assertTrue((trees[0] / 'child/SKILL.md').is_file())
            self.assertTrue((trees[0] / 'LICENSE.azure-skills').is_file())
            self.assertFalse(list((root / 'staged').rglob('.mcp.json')))
            self.assertFalse(list((root / 'staged').rglob('hooks.json')))

    def test_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'bundle.zip'
            make_bundle(archive, {'demo/../../escape': 'not a skill'})
            with self.assertRaises(CLIError):
                skills.stage_bundle(archive, root / 'staged')
            self.assertFalse((root / 'escape').exists())
```

Add parameterized/subTest cases for absolute paths, backslashes, drive prefixes/alternate streams, empty/dot/dot-dot components, Windows reserved basenames, trailing spaces/dots, Unicode-normalized case collisions, duplicate members, file-versus-directory collisions, symlinks/special files, encrypted entries, excessive counts/depth/sizes, invalid CRC/truncation, and invalid skill frontmatter. Patch constants down for budget tests; never generate a real ZIP bomb.

- [ ] **Step 2: Run `ArchiveTests` red.**

```bash
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills.ArchiveTests
```

- [ ] **Step 3: Implement a validate-first extraction path, not `extractall()`.**

Validate every member's raw path and advertised metadata before creating the staged trees. Require one archive root; split raw names before using `PurePosixPath`, because path normalization must not erase forbidden `.` or `..` components. Compare normalized/casefolded paths and ancestor types to reject platform collisions. Permit ordinary directories and regular files only (ZIP entries with no Unix file-type bits may be treated as regular files); reject link/special-file modes.

Select exactly `<root>/.github/plugins/azure-skills/skills/` and the repository-root `LICENSE`. Require a nonempty payload with an immediate `SKILL.md` in each top-level skill directory. Each `SKILL.md`, including nested ones, must have parseable YAML frontmatter with nonempty string `name` and `description`; use `yaml.safe_load`, catch decoding/YAML failures, and do not tighten unrelated optional metadata or description-length rules. Preserve nested paths and bytes; do not rename skills or rewrite their instructions.

Use the validated path components to join beneath staging and stream each selected member through the per-file/aggregate budgets. Reuse Task 2's `_copy_bounded` implementation; its required behavior is repeated here for clarity, not as a second definition:

```python
def _copy_bounded(source, destination, limit):
    deadline = time.monotonic() + 120
    written = 0
    while True:
        if time.monotonic() > deadline:
            raise CLIError('Azure skills response exceeded the read deadline.')
        chunk = source.read(min(65536, limit - written + 1))
        if not chunk:
            return written
        written += len(chunk)
        if written > limit:
            raise CLIError('Azure skills content exceeded the size limit.')
        destination.write(chunk)
```

Apply the aggregate budget across extracted members, not independently to each one. Preserve ordinary executable bits where supported, never setuid/setgid/sticky bits. Append the root license notice to each staged top-level tree under the agreed filename without overwriting differing content. Staging failures clean the staging directory owned by this call, while leaving the caller's archive available for diagnostics until its enclosing temporary workspace closes.

- [ ] **Step 4: Run `ArchiveTests` and all helper tests green.**
- [ ] **Step 5: Commit helper and tests.**

```bash
git add src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py
git commit -m "feat(aks): safely stage Azure skill bundles and resources"
```

## Task 4: Non-overwriting publication and first-install reporting

**Files:** Modify the helper and its test file.

**Consumes:** staged skill paths from Task 3 and `AgentTarget` objects from Task 1.

**Produces:**

- `InstallReport`: dataclass with independent default-empty lists `installed: list[Path]`, `already_present: list[Path]`, `conflicts: list[Path]`, and `failures: list[tuple[Path, str]]`.
- `publish_skills(skill_dirs: list[Path], targets: list[AgentTarget]) -> InstallReport`.
- `_same_tree(source: Path, destination: Path) -> bool`: exact names/file bytes and relevant executable-bit comparison, with no followed links; extra destination files mean conflict.
- `_publish_one(source: Path, destination: Path) -> str`: under the destination lock, returns `installed`, `already_present`, or `conflict`; operational errors propagate to `publish_skills` for per-path recording.

- [ ] **Step 1: Add failing publication and repeat-run tests using `make_bundle`.**

```python
class PublicationTests(unittest.TestCase):
    def test_same_bundle_is_noop_and_local_edits_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'bundle.zip'
            make_bundle(archive)
            trees = skills.stage_bundle(archive, root / 'staged')
            destination = root / 'home/.pi/agent/skills'
            target = skills.AgentTarget('pi', 'Pi', destination, True)
            first = skills.publish_skills(trees, [target])
            self.assertEqual(first.installed, [destination / 'demo'])
            second = skills.publish_skills(trees, [target])
            self.assertEqual(second.already_present, [destination / 'demo'])
            guide = destination / 'demo/references/guide.md'
            guide.write_text('local edit\n')
            third = skills.publish_skills(trees, [target])
            self.assertEqual(third.conflicts, [destination / 'demo'])
            self.assertEqual(guide.read_text(), 'local edit\n')
```

Add tests for extra destination files, existing empty directories, symlinked roots/ancestors/skill entries, dangling links, destination aliases, a pre-existing installation lock, permission failure, and a later-skill failure after an earlier success. Build a second synthetic release with changed content to prove that repeat installation reports conflicts without replacing old files; a new skill may install, but the report must not imply the bundle is coherent or updated.

- [ ] **Step 2: Run `PublicationTests` red.**

```bash
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills.PublicationTests
```

- [ ] **Step 3: Implement comparison and publication.** Create report lists with `dataclasses.field(default_factory=list)`, never shared mutable defaults. Deduplicate normalized destinations while retaining all selected-agent labels for user-facing display. Inspect existing destination ancestors with `lstat` before writes; do not resolve away a symlink and then accidentally approve it. Recognize Windows junction/reparse-point indirection as unsafe where the platform exposes it.

Set `lock_path = destination_root.parent / '.az-azure-skills.lock'` and acquire it with `os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)`. A pre-existing lock is a reported failure with guidance to verify no installation is running before manually addressing it; do not reclaim it automatically. Only remove a lock created by this invocation.

Stage each destination copy in a hidden temporary sibling directory, outside the agent's skills root, so incomplete trees are not discoverable and the final rename remains on one filesystem. While holding the lock: inspect the final target without following links, compare existing regular trees, and return conflict rather than merging. For an absent target, copy the fully validated staged source, recheck that the target is absent and ancestors remain safe, then rename into place. Never use `os.replace` or `shutil.copytree(source, destination, dirs_exist_ok=True)` on an installed skill. Report per-target errors and keep earlier complete installations; remove only owned temporary directories in `finally`. If publication is interrupted, append a cancellation failure for the current destination and return the accumulated report without processing further targets; retain the already-completed entries.

- [ ] **Step 4: Run publication tests green, including cleanup after exceptions and unchanged unrelated files.** Test cooperative concurrent attempts via the exclusive lock; do not claim hostile local-writer race resistance. On Windows, exercise reparse-point cases when the runner permits them; explicitly skip/report unavailable platform capabilities.
- [ ] **Step 5: Run all helper tests and commit.**

```bash
/opt/az/bin/python3 -B -m unittest -v azure.cli.command_modules.acs.tests.latest.test_azure_skills
git add src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py
git commit -m "feat(aks): publish Azure skills without overwriting existing content"
```

## Task 5: Connect the optional flow, CLI options, help, and final gates

**Files:** Modify helper/tests, `custom.py:2378–2385`, `_params.py:1019–1026`, `_help.py`'s `aks install-cli` entry, and `tests/latest/test_custom.py`.

**Consumes:** all prior task interfaces.

**Produces:**

- `maybe_install_azure_skills(cmd, install_azure_skills: bool | None = None, skills_agents: list[str] | None = None, gh_token: str | None = None) -> None`.
- Existing `k8s_install_cli` with appended parameters `install_azure_skills=None, skills_agents=None`; existing positional arguments retain their positions.
- Registered CLI flags and user help matching the spec.

- [ ] **Step 1: Add failing default-path, explicit-path, and orchestration tests.**

```python
class FlowTests(unittest.TestCase):
    @mock.patch.object(skills, 'resolve_release')
    @mock.patch.object(skills, 'discover_agents')
    @mock.patch.object(skills.sys.stdin, 'isatty', return_value=False)
    def test_noninteractive_default_does_no_skill_work(self, tty, discover, resolve):
        skills.maybe_install_azure_skills(mock.Mock())
        discover.assert_not_called()
        resolve.assert_not_called()

    @mock.patch.object(skills, 'resolve_release')
    @mock.patch.object(skills, 'discover_agents')
    def test_false_does_no_skill_work(self, discover, resolve):
        skills.maybe_install_azure_skills(mock.Mock(), False)
        discover.assert_not_called()
        resolve.assert_not_called()
```

Add a parser test with a mocked install handler, preserving its signature with `autospec=True`. This approach was probed against the current source-overlay CLI using the existing `--client-version` option; it does not install binaries:

```python
import os
from azure.cli.core import get_default_cli


class CliArgumentTests(unittest.TestCase):
    def test_three_state_flag_and_agent_list(self):
        cases = [
            (['--install-azure-skills', '--skills-agents', 'pi', 'codex'], True),
            (['--install-azure-skills', 'true', '--skills-agents', 'pi', 'codex'], True),
            (['--install-azure-skills', 'false'], False),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as config:
                with mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': config}):
                    with mock.patch(
                            'azure.cli.command_modules.acs.custom.k8s_install_cli',
                            autospec=True, return_value=None) as handler:
                        self.assertEqual(get_default_cli().invoke(['aks', 'install-cli'] + arguments), 0)
                        self.assertIs(handler.call_args.kwargs['install_azure_skills'], expected)
                        if expected:
                            self.assertEqual(handler.call_args.kwargs['skills_agents'], ['pi', 'codex'])
```

In `test_custom.py`, patch the two helper entry points and the existing binary functions. Capture call order with a parent Mock; assert validation precedes architecture/binaries and optional installation follows kubelogin. For invalid arguments, make the real preflight raise and assert neither binary is called. Assert all existing binary argument values, including `gh_token`, are unchanged. A binary exception must prevent optional installation.

Add tests for default-No, invalid selector input followed by valid replacement, an empty detected selection, `none`, final confirmation rejection, no-TTY during prompts, EOF/KeyboardInterrupt during prompts, suppressed confirmations, sudo skip, and deduplicated destinations. Explicit true never prompts, even at a TTY. Verify the shared-directory notice when Codex is selected, per-attempt source provenance, and all four outcome lists.

- [ ] **Step 2: Run new flow/orchestration tests red without making real downloads or user-home writes.**

```bash
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills.FlowTests \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills.CliArgumentTests
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_custom -k k8s_install_cli
```

- [ ] **Step 3: Implement the optional wrapper and integrate the command.** The integration must preserve this order:

```python
# At the start of k8s_install_cli, before architecture selection:
from ._azure_skills import maybe_install_azure_skills, validate_skills_options
validate_skills_options(install_azure_skills, skills_agents)
```

```python
# After the existing kubectl and kubelogin calls, with their arguments unchanged:
maybe_install_azure_skills(cmd, install_azure_skills, skills_agents, gh_token)
```

In the wrapper, explicit false returns immediately. For omitted mode, return without discovery when stdin is not a TTY or `core.disable_confirm_prompt` is true; under sudo, skip with unprivileged-install guidance. Only after the first Yes discover agents, print the numbered list, parse/re-prompt, and show destination/skills-only/shared-path information before final default-No confirmation. Capture prompt cancellation only around prompts; cleanup must still work if the user interrupts retrieval/publication later.

For explicit true, select the supplied identifiers from discovery's registry entries regardless of detected status; display the destinations and limitations but never prompt. Deduplicate repeated IDs and destinations. Preflight was already performed by the handler; do not duplicate it inside the wrapper.

Use one `TemporaryDirectory` for archive/staging, call `resolve_release`, log repository/tag/commit before publication, call `download_archive`, `stage_bundle`, and `publish_skills`, then report results. Keep source provenance visible in failure summaries once resolution succeeded. Known metadata/download/archive/filesystem errors are contextual `CLIError`s: optional mode logs a warning and returns, explicit mode raises. Do not broadly swallow programming errors. For interruptions after confirmation, preserve completed files, clean temporary state, and report cancellation/partial progress without describing the installation as complete. Interactive/omitted mode warns and returns; explicit requests raise a contextual `CLIError` and retain a nonzero outcome. `publish_skills` returns its accumulated cancellation report as specified in Task 4; a retrieval interruption has not published any skills.

When any report conflicts/fails, include the spec's manual-recovery or cause-specific retry guidance and source-change caveat. Explicit mode raises after reporting the partial outcome; optional mode warns. Keep binary success clear in both cases. Do not record a manifest, auto-delete conflicts, or add an update path.

Register options using the existing `get_three_state_flag()` convention and the registry's choices:

```python
from ._azure_skills import AGENT_IDS

c.argument('install_azure_skills', arg_type=get_three_state_flag(), default=None,
           help='Offer Azure skills interactively when omitted. Specify true with '
                '--skills-agents to install without prompts, or false to skip.')
c.argument('skills_agents', nargs='+', choices=AGENT_IDS,
           help='Agents to install user-level Azure skills for. Requires --install-azure-skills true.')
```

Expand `gh_token` help to mention Azure skills release metadata while retaining kubelogin. Update `_help.py` with examples for the ordinary command, explicit false, and explicit true with selected agents. Explain no MCP/hooks, user-level scope, noninteractive/sudo behavior, shared Codex visibility, first-install-only conflicts, and that rerunning also reruns binary installation.

- [ ] **Step 4: Run helper, custom, and validator tests, plus source-overlay help.**

```bash
/opt/az/bin/python3 -B -m unittest -v \
  azure.cli.command_modules.acs.tests.latest.test_azure_skills \
  azure.cli.command_modules.acs.tests.latest.test_custom \
  azure.cli.command_modules.acs.tests.latest.test_validators
/opt/az/bin/python3 -B - <<'PY'
import os
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as config:
    subprocess.run(
        [sys.executable, '-B', '-m', 'azure.cli', 'aks', 'install-cli', '--help'],
        env=dict(os.environ, AZURE_CONFIG_DIR=config), check=True)
PY
```

Extend `CliArgumentTests` with invalid agent choices and omitted flags, and verify the updated help output. Keep each `get_default_cli()` invocation isolated with a temporary Azure config directory and an autospecced handler. Do not run the real install command against default binary paths.

- [ ] **Step 5: Perform the final gates below, then commit only the intended source/tests/help changes.**

```bash
git add src/azure-cli/azure/cli/command_modules/acs/_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_azure_skills.py \
  src/azure-cli/azure/cli/command_modules/acs/custom.py \
  src/azure-cli/azure/cli/command_modules/acs/_params.py \
  src/azure-cli/azure/cli/command_modules/acs/_help.py \
  src/azure-cli/azure/cli/command_modules/acs/tests/latest/test_custom.py
git commit -m "feat(aks): offer native Azure skills installation from install-cli"
```

## Final verification and review gates

- [ ] **Live payload, isolated destination.** After the feature is implemented, exercise only its helper functions, not the binary installer, against a temporary destination:

```bash
/opt/az/bin/python3 -B - <<'PY'
import tempfile
from pathlib import Path
from azure.cli.command_modules.acs import _azure_skills as skills

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    release = skills.resolve_release()
    archive = root / 'azure-skills.zip'
    skills.download_archive(release, archive)
    trees = skills.stage_bundle(archive, root / 'staged')
    target = skills.AgentTarget('pi', 'Temporary smoke target', root / 'target/skills', False)
    first = skills.publish_skills(trees, [target])
    second = skills.publish_skills(trees, [target])
    assert trees and len(first.installed) == len(trees)
    assert not first.conflicts and not first.failures
    assert len(second.already_present) == len(trees)
    assert not second.installed and not second.conflicts and not second.failures
    assert all((path / 'LICENSE.azure-skills').is_file() for path in first.installed)
    print(release.tag, release.commit, 'top-level skill directories:', len(trees))
PY
```

This smoke test checks a real layout without installing into any actual agent home. Do not hard-code 28 as a permanent test expectation. Separately exercise an interactive prompt sequence in a pseudo-terminal with temporary home/config, mocked binary calls and mocked retrieval/publication. Confirm that Enter means No, selections replace defaults, final rejection makes no writes, and cancellation does not roll back binaries.

- [ ] **Broader tooling if available/approved.** Repository setup guidance is in `doc/configuring_your_machine.md:61–63`; CI pins are in `.azure-pipelines/templates/azdev_setup.yml:19–24`. Install tooling only into a dedicated environment, not `/opt/az` or the user's global Python:

```bash
python3 -m venv /tmp/aks-azure-skills-dev
source /tmp/aks-azure-skills-dev/bin/activate
python -m pip install -U pip 'setuptools<81'
python -m pip install 'azdev==0.2.13'
azdev setup -c /home/tng/workspace/azure-cli-worktrees/aks-azure-skills
azdev test acs --no-exitfirst
azdev style acs
azdev linter acs
```

Check tool help before execution if installed azdev differs from the CI pin. Do not treat unavailable tooling as a passing gate. The broad ACS suite may require recorded-test dependencies or credentials; distinguish environmental limitations from failures caused by this change and stop on unrelated hook failures rather than editing unrelated code.

- [ ] **Polish and fresh verification.** Load `polish-core` and run its `--fix` workflow against the implementation range; inspect every edit, rerun the focused tests/help/live temporary smoke, and run `git diff --check`. Review the final diff against the spec, especially no-clobber behavior, token isolation, default noninteractive compatibility, source provenance, and manual recovery.
- [ ] **Platform statement.** Run available Windows/macOS checks, including path/reparse and executable-bit behavior. If only Linux was exercised, say so; synthetic path tests do not establish native cross-platform correctness.
- [ ] **Completion write-up.** Load `change-explainer`, cite exact tests/results and remaining limits, and use the branch-finishing workflow. Do not claim agent-runtime/MCP workflow validation from successful file installation. Do not push or open a PR unless requested by the applicable finishing choice.

## Spec coverage and adaptation points

| Spec area | Plan coverage |
| --- | --- |
| Automatic default-No offer and numbered selection | Tasks 1 and 5 |
| True/false/omitted flags, targets, pre-binary validation | Tasks 1 and 5 |
| TTY, confirmation config, sudo, and cancellations | Tasks 1 and 5 |
| Agent overrides, shared Codex discovery, destination deduplication | Tasks 1, 4, and 5 |
| Latest stable release resolved to commit and source provenance | Tasks 2 and 5 |
| Token reuse, redirect isolation, rate-limit guidance | Tasks 2 and 5 |
| Full trees, nested skills, notices, bounded extraction | Task 3 |
| Existing files, links, partial failures, cleanup | Tasks 4 and 5 |
| First-install lifecycle, same-bundle reruns, advancing releases | Tasks 4 and 5 |
| Source-overlay tests, real temporary payload, platform limitations | Final gates |

Stop and revisit the relevant design decision if the published payload moves outside the agreed subtree, requires resources outside its skill trees beyond the root legal notice, cannot fit the conservative limits, or cannot be discovered at a documented agent location. Do not silently flatten nested skills, rewrite instructions, enable MCP servers, or expand to additional agents to make a smoke test pass. If the single helper grows beyond a reviewable focused module, propose a narrow split rather than introducing a generic installer framework.

This plan does not implement updates, uninstall, resumable installation state, an agent/plugin manager, extra targets, automatic elevation, Node/Git bootstrapping, or a graphical/checkbox interface. Work on the shared helper is sequential even when using fresh subagents per task; do not dispatch concurrent writers to it.

---
applyTo: "src/azure-cli/azure/cli/command_modules/appconfig/**"
---
<!-- cspell:words appconfig azconfig configstore kwargs -->
# Copilot instructions for the `appconfig` command module

Scope: these instructions apply only to
`src/azure-cli/azure/cli/command_modules/appconfig/**` (the `az appconfig`
command module). Do not generalize conventions from here to other
command modules.

These instructions distill and are grounded in the repo's own authoring
guides — consult them directly for anything not covered here:
- `doc/authoring_command_modules/README.md` — module setup, PR
  title/changelog process (`HISTORY.rst` is auto-generated from PR
  titles, not hand-edited).
- `doc/authoring_command_modules/authoring_commands.md` — command
  loader, registration, validators, preview mechanics.
- `doc/command_guidelines.md` — command/argument naming, general
  patterns, error handling, coding practices.
- `doc/error_handling_guidelines.md` — required error types
  (`azure.cli.core.azclierror`) and error-message wording rules.
- `doc/how_to_introduce_breaking_changes.md` — the `_breaking_change.py`
  pre-announcement mechanism for deprecating/renaming/changing GA
  commands or arguments (current preferred approach, supersedes ad hoc
  `deprecate_info=`).
- `doc/how_to_bump_SDK_version_in_cli.md` — process for bumping the
  pinned `azure-mgmt-appconfiguration`/data-plane SDK version.
- `doc/authoring_help.md` — `_help.py` YAML authoring rules.
- `doc/authoring_tests.md` — test policies, coverage requirements,
  recording workflow.

## Module map

| File | Purpose |
|---|---|
| `_params.py` | Registers CLI arguments (`load_arguments`) — arg names, types, validators, enum choices. |
| `_validators.py` | Argument validators/normalizers invoked by `_params.py` before command execution. |
| `_client_factory.py` | Builds SDK clients (`cf_configstore`, `cf_configstore_operations`, `cf_replicas`, `cf_nsp_configurations`). |
| `commands.py` | `load_command_table` — wires command names to implementation functions via `CliCommandType`, sets `table_transformer` and `client_factory` per group. |
| `custom.py` | Management-plane command implementations (store CRUD, identity, credentials, replicas). |
| `keyvalue.py` | Data-plane key-value command implementations. |
| `feature.py` | Feature-flag command implementations. |
| `snapshot.py` | Snapshot command implementations. |
| `network_security_perimeter.py` | NSP-related command implementations. |
| `_format.py` | Table output transformers (e.g. `configstore_output_format`). |
| `_help.py` | `helps[...]` entries: short-summary, long-summary, and `examples` for every command/group. |
| `_constants.py`, `_models.py`, `_featuremodels.py`, `_snapshotmodels.py` | Shared enums/constants and lightweight data models. |
| `_kv_helpers.py`, `_kv_import_helpers.py`, `_kv_export_helpers.py`, `_diff_utils.py`, `_json.py`, `_utils.py` | Shared helper logic used by `custom.py`/`keyvalue.py`. |
| `_credential.py` | Auth/credential helpers for data-plane calls. |
| `linter_exclusions.yml` | `azdev linter` suppressions — only add entries with a clear justification. |
| `tests/latest/` | ScenarioTests, recordings, and `_test_utils.py` helpers. |

## Adding or changing a command — checklist

0. **Naming** (`doc/command_guidelines.md`): commands follow "[noun] [noun] [verb]" with a verb in every command name; hyphenate multi-word subgroups; avoid a subgroup that would hold only one command (hyphenate into the parent instead, unless more commands are clearly planned). Argument names should not embed units (put units in help text), should reuse global aliases (e.g. `resource_group_name_type`), and should not duplicate the same concept under two different argument names.
1. **Arguments** (`_params.py`): add/extend a `with self.argument_context(...)` block; reuse existing arg types (`fields_arg_type`, `tags_type`, `get_enum_type`, `get_three_state_flag`) before inventing new ones.
2. **Validation** (`_validators.py`): add a `validate_<thing>(namespace)` or `validate_<thing>(cmd, namespace)` function; per `doc/error_handling_guidelines.md`, raise a specific `azure.cli.core.azclierror` type (`InvalidArgumentValueError`, `RequiredArgumentMissingError`, `MutuallyExclusiveArgumentError`, `ArgumentUsageError`, or another third-layer type such as `ResourceNotFoundError`/`ValidationError` when it fits better) rather than bare `CLIError`/`Exception`. Error messages start with a capital letter, state the problem and the actionable fix (e.g. "...; specify it with --arg-name"), and avoid raw `'\n'`, usage-error boilerplate, or regex/code snippets. Wire the validator into the matching argument via `validator=` in `_params.py`.
3. **Implementation**: put management-plane logic in `custom.py`, data-plane key-value logic in `keyvalue.py`, feature-flag logic in `feature.py`, snapshot logic in `snapshot.py`. Follow the existing function-per-command style (one public function per CLI command, named after the command, e.g. `def appconfig_create(...)`). Commands must return an object/dict/`None` (never a bare string/bool); log status via `logger.warning()`/`logger.error()`, never `print()` (`doc/command_guidelines.md` "General Patterns").
4. **Client factory** (`_client_factory.py`): if a new SDK client/operation group is needed, add a `cf_<name>(cli_ctx, *_)` accessor here rather than constructing clients inline.
5. **Command registration** (`commands.py`): register new commands inside `load_command_table`, choosing/creating the right `CliCommandType` (correct `operations_tmpl`, `table_transformer`, `client_factory`). Group related commands under the existing command groups rather than creating new ones unless truly novel. Mark experimental commands/args `is_preview=True`. For deprecating/renaming/otherwise breaking a GA command or argument, prefer the `_breaking_change.py` pre-announcement mechanism (`register_command_deprecate`, `register_argument_deprecate`, `register_default_value_breaking_change`, etc. — see `doc/how_to_introduce_breaking_changes.md`) over the legacy `deprecate_info=c.deprecate(...)` kwarg, which still exists in this module but is no longer the recommended path for new changes. Use `confirmation=True` for destructive commands (see `delete`/`purge`/`recover`).
6. **Output formatting** (`_format.py`): add a transformer function if the command needs custom table output, and reference it as `table_transformer` in `commands.py`.
7. **Help text** (`_help.py`): every new command or new argument needs a `helps['appconfig ...']` entry with `type`, `short-summary`, and at least one concrete `examples` entry using realistic values (see the dedicated `appconfig-help` agent for detailed rules).
8. **Tests**: add/extend a ScenarioTest under `tests/latest/` (see the dedicated `appconfig-test` agent for detailed rules).
9. **Changelog**: do not hand-edit `src/azure-cli/HISTORY.rst` — it is auto-generated from the PR title (`[Component] Verb: az appconfig <cmd>: description`) per `doc/authoring_command_modules/README.md`. Use the PR description's "History Notes" section for multiple/overriding notes.

## Style conventions observed in this module

- License header on every file:
  ```python
  # --------------------------------------------------------------------------------------------
  # Copyright (c) Microsoft Corporation. All rights reserved.
  # Licensed under the MIT License. See License.txt in the project root for license information.
  # --------------------------------------------------------------------------------------------
  ```
- `logger = get_logger(__name__)` at module scope for anything that logs, using `from knack.log import get_logger`.
- Long lines and large functions are common in this module and are explicitly tolerated via `# pylint: disable=line-too-long` / `# pylint: disable=too-many-statements` at the top of files — prefer following this existing pattern over aggressively splitting functions, but do not silence genuinely new lint issues without justification.
- Prefer keyword-only, explicit parameter names in command functions (matching the CLI argument names) over `**kwargs`.
- Reuse existing helper modules (`_utils.py`, `_kv_helpers.py`, etc.) instead of duplicating logic already present there.

## Required validation before finishing a change

Run from the repo root:
```
azdev style appconfig
azdev linter --command-modules appconfig
azdev test appconfig
```
All three must pass (or failures must be pre-existing/unrelated) before considering a change complete.

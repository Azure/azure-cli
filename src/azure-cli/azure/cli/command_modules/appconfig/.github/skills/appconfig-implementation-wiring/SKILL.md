---
name: appconfig-implementation-wiring
description: Implement and register az appconfig CLI command functions (custom.py/keyvalue.py/feature.py/snapshot.py), client factories, commands.py registration, and table output formatting. Use when writing or wiring up command logic under src/azure-cli/azure/cli/command_modules/appconfig/.
license: MIT
---
<!-- cspell:words appconfig azconfig configstore kwargs cliargumenttype -->
# appconfig-implementation-wiring skill

Scope: `custom.py`, `keyvalue.py`, `feature.py`, `snapshot.py`,
`network_security_perimeter.py`, `_client_factory.py`, `commands.py`, and
`_format.py` in
`src/azure-cli/azure/cli/command_modules/appconfig/`. Grounded in
`doc/authoring_command_modules/authoring_commands.md` and
`doc/command_guidelines.md` — treat both as authoritative alongside the
rules below.

## Where to put the implementation

- Management-plane (store CRUD, identity, credentials, replicas, NSP) →
  `custom.py` / `network_security_perimeter.py`.
- Data-plane key-value logic → `keyvalue.py`.
- Feature-flag logic → `feature.py`.
- Snapshot logic → `snapshot.py`.
- One public function per CLI command, named after the command (e.g.
  `def appconfig_create(...)`), with parameter names mirroring the CLI
  argument names exactly.
- Reuse shared helpers instead of duplicating logic: `_utils.py`,
  `_kv_helpers.py`, `_kv_import_helpers.py`, `_kv_export_helpers.py`,
  `_diff_utils.py`, `_json.py`.
- Special parameter names with infrastructure meaning
  (`doc/authoring_command_modules/authoring_commands.md`): `cmd` (must be
  first parameter if used; gives access to `cmd.cli_ctx`), `client` (bound
  automatically if the command's `client_factory` is set).

## General patterns (`doc/command_guidelines.md`)

- Commands must return an object, dict, or `None` — never a bare
  string/bool.
- All command *output* goes to stdout; everything else (status messages,
  warnings, errors) goes through `logger.warning()`/`logger.error()` —
  never `print()`.
- New output must work with JSON, TSV, and table formats; add a
  `_format.py` transformer if the default table rendering isn't useful.
- Support tab completion for parameter names/values where relevant
  (usually free via `get_enum_type`/named completers, not something you
  need to hand-write).

## Client factory (`_client_factory.py`)

- If a new SDK client or operation group is needed, add a
  `cf_<name>(cli_ctx, *_)` accessor here rather than constructing clients
  inline in `custom.py`/etc. See existing examples: `cf_configstore`,
  `cf_replicas`, `cf_nsp_configurations`, `cf_configstore_operations`.

## Registration (`commands.py`)

- Register new commands inside `load_command_table`, reusing an existing
  `CliCommandType` (e.g. `configstore_custom_util`,
  `configstore_keyvalue_util`, `configstore_snapshot_util`) where the
  `operations_tmpl`, `table_transformer`, and `client_factory` already
  match, or defining a new `CliCommandType` if truly novel.
- Group related commands under existing command groups
  (`self.command_group('appconfig ...', ...)`) rather than creating new
  ones unless the command is genuinely a new area.
- Mark experimental commands/arguments `is_preview=True` (see the
  `appconfig-breaking-changes` skill for full preview/deprecation
  guidance).
- Use `confirmation=True` on destructive/irreversible commands (delete,
  purge, recover-style operations) — see `delete`, `recover`, `purge` on
  the config store in `commands.py` — so the CLI prompts unless `--yes`
  is passed.

## Output formatting (`_format.py`)

- Add a transformer function (see `configstore_output_format`,
  `keyvalue_entry_format`, `configstore_replica_output_format`, etc. for
  the existing style) if the command needs custom table output, and
  reference it as `table_transformer=` on the relevant `CliCommandType`
  or command registration in `commands.py`.

## Guardrails

- Only edit the files listed in Scope (plus reading others for
  grounding).
- Match existing style: license header, `logger = get_logger(__name__)`
  where logging is needed, `# pylint: disable=...` comments already
  present at the top of files — don't fight the existing tolerance for
  long lines/large functions in this module.
- Don't inline SDK client construction — always go through
  `_client_factory.py`.
- Keep changes surgical: adding one command shouldn't require touching
  unrelated `CliCommandType` definitions or command groups.

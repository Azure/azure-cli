# Monitor Module: Legacy Fallback

## Overview

The monitor module ships a vendored copy of the pre-refactor code in `_legacy/`. Users can switch to this snapshot via config if the refactored implementation causes issues:

```bash
az config set monitor.use_legacy=true   # enable legacy mode
az config set monitor.use_legacy=false  # switch back to new mode (default)
```

A warning is logged each time legacy mode is active.

## How It Works

In `__init__.py`, `MonitorCommandsLoader` reads the `monitor.use_legacy` config (default `false`):

- **New mode** — loads from `aaz/`, `operations/`, and `commands.py` using `load_aaz_command_table_args_guided`.
- **Legacy mode** — loads from `_legacy/aaz/`, `_legacy/commands.py` using `load_aaz_command_table`. Arguments come from `_legacy/_params.py`.

The `_legacy/` folder is a frozen snapshot extracted from the `dev` branch. All absolute imports were rewritten from `azure.cli.command_modules.monitor.` to `azure.cli.command_modules.monitor._legacy.`.

## Known Adjustments

- **`_legacy/_params.py`**: Removed `monitor metrics alert update` argument registrations (lines for `add_actions`, `remove_actions`, `add_conditions`, `remove_conditions`) because the AAZ `MetricsAlertUpdate._build_arguments_schema` already defines them, and the old-style `action=MetricAlertAddAction` overrides corrupt AAZ argument parsing.
- **Tests**: `test_monitor_general_operations.py` mocks `gen_guid` at both `azure.cli.command_modules.monitor.operations.monitor_clone_util` and `azure.cli.command_modules.monitor._legacy.operations.monitor_clone_util` so tests pass in either mode.
- **Linting**: `_legacy/` is excluded via `pylintrc` (`ignore` list) and `.flake8` (`exclude` list).

## Dropping Legacy Support

When legacy mode is no longer needed:

1. **Delete the `_legacy/` folder**:
   ```bash
   rm -rf src/azure-cli/azure/cli/command_modules/monitor/_legacy/
   ```

2. **Simplify `__init__.py`** — remove `_use_legacy`, `_load_legacy_command_table`, and the dispatch in `load_command_table` / `load_arguments`. Inline `_load_new_command_table` as the sole `load_command_table`:
   ```python
   # Remove these
   _CONFIG_SECTION = 'monitor'
   _USE_LEGACY_CONFIG_KEY = 'use_legacy'
   self._use_legacy = ...
   def _load_legacy_command_table(self, args): ...

   # Keep only _load_new_command_table logic directly in load_command_table
   ```

3. **Clean up tests** — remove the second `mock.patch` line for `_legacy` in `test_monitor_general_operations.py`:
   ```python
   # Remove this line from each mock.patch block:
   mock.patch('azure.cli.command_modules.monitor._legacy.operations.monitor_clone_util.gen_guid', ...)
   ```

4. **Revert linter config** — remove `_legacy` from `pylintrc` `ignore` and `*/_legacy` from `.flake8` `exclude`.

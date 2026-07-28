---
name: appconfig-breaking-changes
description: Mark az appconfig commands/arguments as preview, or deprecate/rename/remove/otherwise change GA behavior using the _breaking_change.py pre-announcement mechanism, and apply confirmation=True for destructive commands. Use whenever a change to appconfig affects existing (GA) command/argument behavior, defaults, or output — not just when adding brand-new commands.
license: MIT
---
<!-- cspell:words appconfig azconfig configstore kwargs deprecate -->
# appconfig-breaking-changes skill

Scope: any change to
`src/azure-cli/azure/cli/command_modules/appconfig/` that affects
existing (GA) command/argument behavior — deprecating, renaming,
removing, changing a default, changing output shape, or otherwise
introducing a breaking change — plus marking new items as preview.
Grounded in
`doc/authoring_command_modules/authoring_commands.md` ("Preview Commands
and Arguments") and `doc/how_to_introduce_breaking_changes.md` (the
current breaking-change mechanism) — treat both as authoritative.

## Preview flag

New commands/arguments that are experimental or subject to change should
be marked `is_preview=True` (on `c.argument(...)`, `g.command(...)`, or
`self.command_group(...)`). Existing examples in this module: the
`azure_front_door_profile` argument and the
`network-security-perimeter-configuration` command group.

**Anything not marked preview is considered GA.** Changing or removing GA
behavior later requires the pre-announced breaking-change mechanism
below — never a silent change.

## Deprecating, renaming, or removing a GA item

Per `doc/how_to_introduce_breaking_changes.md`, the current, preferred
mechanism is a per-module `_breaking_change.py` file — **this module
doesn't have one yet.** Create it with the standard license header if
it's needed:

```python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
```

Then register breaking changes with `azure.cli.core.breaking_change`.
Make sure the module actually imports `_breaking_change` somewhere that
executes at load time (commonly from `commands.py` or `__init__.py`) —
registrations have no effect if the file is never imported.

- **Deprecate a command group / command / argument**:
  `register_command_group_deprecate(group, redirect=None, hide=False, target_version=None)`,
  `register_command_deprecate(command, redirect=None, hide=False, target_version=None)`,
  `register_argument_deprecate(command, argument, redirect=None, hide=False, target_version=None)`.
  - **Removal** = call with no `redirect`.
  - **Rename** = call with `redirect='--new-arg-name'` (or the new
    command/group name).
  - Do **not** combine a deprecation with another breaking-change type on
    the same item — pick one.
- **Default value change**:
  `register_default_value_breaking_change(command, arg, current_default, new_default, target_version=...)`.
- **Argument becoming required**:
  `register_required_flag_breaking_change(command, arg, target_version=...)`.
- **Output shape/field change**:
  `register_output_breaking_change(command, description=..., guide=..., target_version=..., doc_link=...)`.
- **Behavior/logic change** not covered above:
  `register_logic_breaking_change(command, summary, detail=..., target_version=..., doc_link=...)`.
- **Anything else**:
  `register_other_breaking_change(command, message, arg=None, target_version=...)`.
- `target_version` accepts a specific version or an approximate date
  (`[DDth] MMM YYYY`); defaults to the next breaking-change window if
  omitted.

```python
from azure.cli.core.breaking_change import (
    register_argument_deprecate, register_default_value_breaking_change,
    register_required_flag_breaking_change)

# Rename --old-name to --new-name on 'appconfig create'
register_argument_deprecate('appconfig create', '--old-name', redirect='--new-name')

# Announce a future default change
register_default_value_breaking_change('appconfig create', '--sku', 'standard', 'developer',
                                       target_version='May 2025')
```

### Legacy `deprecate_info=` kwarg

The older `deprecate_info=c.deprecate(redirect=..., hide=...)` kwarg
still works and still appears in this module (e.g.
`enable_public_network` → `--public-network-access` in `_params.py`), but
prefer `_breaking_change.py` for **new** deprecations/renames per the
doc's recommendation — don't add more legacy-style deprecations.

### Timing requirement

Pre-announcements must ship **at least ~1 month (usually 2 sprints)**
before the actual breaking change lands, and the actual breaking change
should only be adopted within the designated breaking-change window.
Flag this timing explicitly to the user rather than assuming an
immediate change is acceptable — a service-owned module like appconfig
needs its own PR for the pre-announcement, separate from the PR that
implements the change itself.

## Confirmation for destructive commands

Destructive/irreversible commands (delete, purge, recover-style
operations) should register with `confirmation=True` in `commands.py`
(see `delete`, `recover`, `purge` on the config store) so the CLI prompts
the user for confirmation unless `--yes` is passed.

## Guardrails

- Always call out to the user, explicitly and up front, when a requested
  change would break existing GA behavior — don't implement it silently
  even if technically straightforward.
- Don't mix a deprecation and another breaking-change type on the same
  command/argument.
- If unsure whether an item is GA or preview, check for an existing
  `is_preview=True` on it in `_params.py`/`commands.py` before assuming
  it's safe to change freely.

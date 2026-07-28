---
name: appconfig-args-validators
description: Author or review CLI argument registration and validators for the az appconfig command module (naming conventions, _params.py argument_context blocks, _validators.py functions, and error type/message selection). Use when adding, renaming, or fixing arguments/validators under src/azure-cli/azure/cli/command_modules/appconfig/.
license: MIT
---
<!-- cspell:words appconfig azconfig configstore kwargs argtype -->
# appconfig-args-validators skill

Scope: `_params.py` and `_validators.py` in
`src/azure-cli/azure/cli/command_modules/appconfig/`. Grounded in
`doc/command_guidelines.md` and `doc/error_handling_guidelines.md` —
treat both as authoritative alongside the rules below.

## Command & argument naming (`doc/command_guidelines.md`)

- Commands follow "[noun] [noun] [verb]" with a verb in every command
  name (e.g. `appconfig kv set`, not `appconfig kv`).
- Multi-word subgroups are hyphenated.
- Avoid adding a subgroup that would only ever contain one command —
  hyphenate into the parent instead, unless more commands in that
  subgroup are clearly planned soon.
- Argument names must not embed units — put units in help text instead
  (e.g. prefer `--retention-days` with "(in days)" in the help string
  over inventing new unit-suffixed names each time).
- Don't create multiple arguments that are just different ways to supply
  the same value — overload one descriptive argument instead (e.g. a
  single `--parameters` accepting either a local path or a URL, not
  `--parameters-path` and `--parameters-url`).
- Prefer globally-aliased argument types (e.g. `resource_group_name_type`
  for `-g`/`--resource-group`) over ad hoc parameter names/short options.
- Arguments ending in `-id` should be GUIDs; arguments accepting ARM IDs
  should omit the `-id` suffix and call out ARM-ID support in help text
  (common with the "name or ID" convention already used in this module,
  e.g. `--identity`/`--azure-front-door-profile`).

## Registering arguments (`_params.py`)

- Add/extend a `with self.argument_context('appconfig ...')` block
  inside `load_arguments`.
- Reuse existing `CLIArgumentType` definitions and helpers before
  defining new ones: `fields_arg_type`, `tags_type`, `get_enum_type`,
  `get_three_state_flag`, `resource_group_name_type`, `get_location_type`.
- Wire any new validator via `validator=` on the argument.
- Mark experimental/subject-to-change arguments `is_preview=True` (see
  the `appconfig-breaking-changes` skill for the full preview/deprecation
  story).

## Writing validators (`_validators.py`)

- Add `validate_<name>(namespace)` if no CLI context access is needed, or
  `validate_<name>(cmd, namespace)` if you need `cmd.cli_ctx` (e.g. to
  read defaults via `cmd.cli_ctx.config.get(...)`, as
  `validate_connection_string` does).
- Wire the validator into the matching argument via `validator=` in
  `_params.py`.

## Error types and messages (`doc/error_handling_guidelines.md`)

- **Never** raise bare `CLIError` or `Exception` in new validators. Raise
  a specific third-layer type from `azure.cli.core.azclierror`:
  - Already used in this module: `InvalidArgumentValueError`,
    `RequiredArgumentMissingError`, `MutuallyExclusiveArgumentError`,
    `ArgumentUsageError`.
  - Also available when they fit better: `ResourceNotFoundError`,
    `ValidationError`, `UnauthorizedError`, `ForbiddenError`,
    `BadRequestError`, `AzureResponseError`, `AzureConnectionError`,
    `FileOperationError`, `CommandNotFoundError`,
    `UnrecognizedArgumentError`.
  - Avoid the base/fallback types (`AzCLIError`, `UserFault`,
    `ClientError`, `ServiceError`, or the generic `UnclassifiedUserFault`/
    `ArgumentUsageError`) when a more specific type exists.
  - If truly nothing fits and the error is general enough, a new type can
    be proposed in `azure/cli/core/azclierror.py` (core, not this
    module) — flag this to the user rather than doing it silently.
- **Message wording — DOs**: start with a capital letter; describe what's
  wrong and, where possible, the exact fix (e.g. "...; please provide a
  resource group name by --resource-group").
- **Message wording — DON'Ts**: no raw `'\n'` or styling/colorization; no
  usage-error boilerplate in the message; no programming
  expressions/regex patterns in the message (e.g. don't say "must match
  `'^[-\\w\\._\\(\\)]+$'`" — describe the constraint in plain language
  instead); no vague messages like "Something unexpected happened."
- **Recommendations**: pass `recommendation=` (a string or list of
  strings) to the error constructor, or call
  `az_error.set_recommendation(...)` after construction, when the error
  message alone doesn't tell the user what to do next.

```python
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError

error_msg = 'Please specify only one of --connection-string or --name.'
recommendation = 'Try passing just --name and let the CLI resolve the connection string from defaults.'
raise MutuallyExclusiveArgumentError(error_msg, recommendation)
```

## Guardrails

- Only edit `_params.py`/`_validators.py` (and read other files for
  grounding, e.g. `_constants.py` for enum values).
- Match the module's existing style: license header, `# pylint:
  disable=line-too-long` tolerance, `logger = get_logger(__name__)` if
  logging is needed.
- Don't silently downgrade an existing specific `azclierror` type to a
  more generic one, and don't reintroduce `CLIError` in code you touch.

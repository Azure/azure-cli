---
name: common-aaz-custom-code-generation
description: "Use after routing to AAZ subclass custom, or when adding/updating Azure CLI AAZ generated command customization. Generates custom classes that subclass AAZ generated commands while limiting uncertainty with required slots, templates, and validation gates."
argument-hint: "Provide module, command group, command verb, generated AAZ command path/class, and intended customization if known."
---

# Common AAZ Custom Code Generation

Use this workflow to generate or update hand-written custom code for Azure CLI commands whose primary implementation is an AAZ generated command.

This skill starts after the route is known or strongly suspected to be `aaz-subclass-custom`. If the route is unclear, use `common-custom-code-router` first.

## Scope

This is module-general and applies across Azure CLI command modules under `src/azure-cli/azure/cli/command_modules`.

Use this skill for:

- subclassing generated AAZ command classes such as `Create`, `Show`, `List`, `Update`, `Delete`, or `Wait`
- changing generated command argument UX through `_build_arguments_schema`
- normalizing or validating CLI arguments before generated operations run
- adding resource or operation guard checks around a generated command, such as existence checks or dependency checks
- shaping generated command output when local module patterns support it
- replacing a generated command table entry with a hand-written subclass

Do not use this skill for:

- legacy SDK-backed custom functions using `CliCommandType(..., client_factory=...)`
- Legacy Non-SDK Custom: local tool, subprocess, data-plane, raw HTTP, or diagnostic workflows whose public command is not an AAZ subclass
- editing generated files under `aaz/latest` unless the user explicitly asks to modify generated output and accepts regeneration risk

## Slots To Resolve

Resolve these slots before editing the related code. Prefer repository evidence over asking the user. These are not all user-provided inputs; some are derived or conditional.

```yaml
module_name: "<module under command_modules>"
command_group: "<az command group, e.g. network vnet or aks safeguards>"
command_verb_or_action: "<CLI verb/action used to locate the generated file, e.g. create/show/wait or custom action>"
generated_module_import: "<relative import from .aaz.latest...>"
generated_base_class: "<Python class imported from the generated module and inherited by the custom class, e.g. Create/Show/Wait>"
custom_class_name: "<ModuleResourceVerbCustom>"
manual_code_file: "<custom.py or module-local manual file>"
command_table_key: "<full command name; required only when replacing a command_table entry; derive from @register_command(...) when possible>"
registration_file: "<commands.py or loader file; required only when adding/updating a command_table override>"
customization_goals: "<schema-extension | argument-normalization | argument-validation | resource-guard | operation-guard | output-shaping | wait-customization>"
validation_command: "<narrow command-load/help/test command or unknown>"
```

`command_verb_or_action` and `generated_base_class` often correspond for standard commands, but they are not the same slot. The verb/action helps locate generated files such as `_show.py` or `_wait.py`; the base class is the concrete Python class the custom class will inherit.

If `generated_module_import` or `generated_base_class` cannot be resolved, stop and ask one focused question or ask for the generated command path. Do not guess an AAZ import path. If `command_table_key` cannot be resolved but no command table override is needed, set it to `not-needed`. If an override is needed and the key cannot be derived, ask one focused question.

## Evidence To Gather

Gather only the evidence needed for the slots.

1. Confirm the generated command exists under `src/azure-cli/azure/cli/command_modules/<module>/aaz/latest/...`.
2. Read the generated `_create.py`, `_show.py`, `_list.py`, `_update.py`, `_delete.py`, or `_wait.py` enough to confirm:
   - command name in `_aaz_info` or examples
   - generated class name
   - argument names in `_build_arguments_schema`
   - operation hooks available in the class
3. Search the target module for existing `class XxxCustom(GeneratedClass)` patterns.
4. Search `commands.py` or the module loader for existing command table replacement style.
5. Inspect the nearest sibling command with the same verb or resource family.

## Uncertainty Gates

Before generating code, reduce uncertainty with these gates:

- If the generated command path is missing, do not create an AAZ subclass. Route back to SDK or non-SDK evaluation.
- If the requested behavior requires a new REST operation not present in generated AAZ code, do not invent `AAZHttpOperation` by hand in custom code.
- If the behavior can be expressed as schema customization, argument normalization/validation, or resource/operation guard checks, subclass the generated command instead of copying generated code.
- If multiple customization goals apply, keep one custom class and combine the smallest necessary hooks.
- If a guard check requires raw HTTP or a secondary command invocation, keep it isolated in `pre_operations` or `post_operations` and validate inputs before constructing URLs.
- If the module already has a local helper for shared schema or validation, reuse it instead of duplicating logic.

## Implementation Workflow

1. Add imports in the manual code file:
   - AAZ argument helpers from `azure.cli.core.aaz` only when needed.
   - The generated base class from `.aaz.latest...`.
   - Existing local validators/helpers when available.
2. Add helper functions only when shared by multiple custom classes or when they reduce repeated validation/schema code.
3. Add a custom class that subclasses the generated base class.
4. Override only the hooks needed for the requested behavior.
5. Register the custom class by replacing the generated command table entry in the module's command registration file.
6. Update parameters/help/tests only if the module's AAZ/manual help pattern requires it or the user requested examples/tests.
7. Run the narrowest validation available: command load, help for the target command, a focused unit test, or a targeted scenario test.

## Hook Templates

Use only the templates needed by the requested behavior. Treat templates as patterns, not fixed implementations. Replace every placeholder and every example argument with names found in the generated AAZ schema or the target module's local conventions. Never leave angle-bracket placeholders such as `<AAZArgType>` or `<generated_arg_name>` in generated code.

### Fallback: Unmatched Business Logic

If no template matches the requested business logic, do not force the request into one of these examples. First identify the smallest AAZ hook that can express the behavior:

- `_build_arguments_schema` for CLI argument surface changes
- `pre_operations` for validation, normalization, or checks before generated operations
- `post_operations` for checks or output changes after generated operations
- `_output` only when local module patterns support custom output shaping
- another generated lifecycle hook only after reading the generated base class and confirming the hook exists

Then generate the smallest subclass that overrides only that hook. If the behavior requires replacing the generated REST operation itself, route back to evaluation instead of stretching these templates.

### Template: Schema Extension

Use this when generated arguments need aliases, relaxed required flags, additional CLI-only arguments, or hidden generated arguments.

```python
from azure.cli.core.aaz import <AAZArgType>
from .aaz.latest.<resource_path>._<verb> import <GeneratedBase>


def _add_<resource>_args(args_schema):
    args_schema.<new_cli_arg_name> = <AAZArgType>(
        options=["--<option-name>"],
        required=<TrueOrFalse>,
        help="<help text>",
    )
    args_schema.<generated_arg_name>._required = False  # pylint: disable=protected-access
    return args_schema


class <CustomClassName>(<GeneratedBase>):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_<resource>_args(args_schema)
```

Replace placeholder argument names with real generated argument names. Do not add `resource_group`, `name`, `resource_id`, or any other example argument unless it matches the command's UX and generated schema.

### Template: Argument Normalization Or Validation

Use this when user-friendly CLI arguments must be converted into the generated AAZ argument shape before the HTTP operation runs.

```python
from azure.cli.core.aaz import has_value
from azure.cli.core.azclierror import ArgumentUsageError


def _validate_and_set_<resource>_argument(ctx):
    args = ctx.args
    has_generated_arg = has_value(args.<generated_arg_name>)
    has_cli_arg_set = has_value(args.<cli_arg_name>)

    if has_generated_arg == has_cli_arg_set:
        raise ArgumentUsageError(
            "Provide either '<generated option>' or '<friendly option set>', but not both."
        )

    if not has_generated_arg:
        args.<generated_arg_name> = <normalize_cli_args_to_generated_value>(ctx, args)


class <CustomClassName>(<GeneratedBase>):
    def pre_operations(self):
        _validate_and_set_<resource>_argument(self.ctx)
```

Use `azure.mgmt.core.tools.is_valid_resource_id` when accepting resource IDs. Normalize and validate resource IDs before using them in URLs. For non-resource-ID arguments, use the generated schema and neighboring command behavior to choose validation rules.

### Template: Resource Or Operation Guard Check

Use this when create/update/delete must check resource existence, dependencies, or state before or after the generated operation.

```python
class <CustomClassName>(<GeneratedBase>):
    def pre_operations(self):
        super().pre_operations()
        _check_<condition>(self.ctx)
```

Call an argument normalization helper first only if the guard check depends on the normalized argument value.

When using `send_raw_request`, keep URL construction explicit and validate any resource URI before concatenating it. Use raw HTTP only as a small guard around an AAZ subclass; if raw HTTP is the primary command implementation, route to legacy non-SDK custom instead.

```python
def _check_<condition>(ctx):
    from azure.cli.core.azclierror import HTTPError
    from azure.cli.core.util import send_raw_request
    from knack.util import CLIError

    resource_uri = ctx.args.<resource_id_arg>.to_serialized_data()
    if not resource_uri.startswith("/subscriptions/"):
        raise CLIError(f"Invalid resource ID format: {resource_uri}")

    url = f"https://management.azure.com{resource_uri}/providers/<Provider>/<childType>/default?api-version=<api-version>"
    try:
        response = send_raw_request(ctx.cli_ctx, "GET", url)
    except HTTPError as ex:
        if ex.response.status_code == 404:
            return
        raise

    if response.status_code == 200:
        raise CLIError("The resource already exists. Use update to modify it or delete it before creating a new one.")
```

Prefer generated AAZ operations or existing SDK helpers over raw HTTP when a local pattern exists.

### Template: Combined Schema And Pre-Operation Custom Class

Use this when the command needs both CLI-friendly arguments and generated argument normalization.

```python
class <CustomClassName>(<GeneratedBase>):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        return _add_<resource>_args(args_schema)

    def pre_operations(self):
        _validate_and_set_<resource>_argument(self.ctx)
```

### Template: Command Table Override

Use this when replacing the generated AAZ command class with the custom subclass.

```python
with self.command_group('<command_group>'):
    from .custom import <CustomClassName>

    self.command_table["<full command name>"] = <CustomClassName>(loader=self)
```

If the module already uses a different manual registration style for AAZ custom classes, follow that local style exactly.

## Output Expectations

Before editing, report:

```yaml
route: aaz-subclass-custom
module_name: "..."
command_verb_or_action: "..."
generated_module_import: "..."
generated_base_class: "..."
custom_class_name: "..."
command_table_key: "... | not-needed"
registration_file: "... | not-needed"
customization_goals: "..."
planned_hooks:
  - "_build_arguments_schema"
  - "pre_operations"
blocked_on: []
```

If `blocked_on` is non-empty, ask a focused question instead of generating code.

After editing, report the files changed and the validation command/result.

## Validation

Prefer the narrowest validation available:

1. `az <target command> -h` or the repo's equivalent command-load/help test command.
2. A focused existing unit test for the target module.
3. A command table import/load check for the target module.
4. `git status --short` and a diff review only when executable validation is unavailable.

If the generated command cannot be loaded because dependencies are unavailable in the local environment, state that clearly and provide the attempted command.

## Common Mistakes To Avoid

- Do not edit generated AAZ files under `aaz/latest` for manual customization.
- Do not copy generated operation classes into `custom.py`.
- Do not invent argument names; read the generated argument schema first.
- Do not assume every AAZ custom needs `resource_group` and `name` aliases.
- Do not overwrite command table entries before confirming the full command key.
- Do not swallow non-404 HTTP errors in pre-operation checks.

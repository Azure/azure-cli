---
name: common-legacy-sdk-backed-custom-code-generation
description: "Use after routing to legacy SDK-backed custom, or when adding/updating Azure CLI legacy custom command functions that call Azure Python SDK clients through CliCommandType, client_factory, cmd.get_models, g.command, g.show_command, or generic_update_command."
argument-hint: "Provide module, command group, command/action, SDK client/factory, SDK operation, and intended behavior if known."
---

# Common Legacy SDK-Backed Custom Code Generation

Use this workflow to generate or update hand-written Azure CLI custom command code whose primary implementation calls an Azure Python SDK client.

This skill starts after the route is known or strongly suspected to be `legacy-sdk-backed-custom`. If the route is unclear, use `common-custom-code-router` first.

## Scope

This is module-general and applies across Azure CLI command modules under `src/azure-cli/azure/cli/command_modules`.

Use this skill for:

- command handlers registered through `CliCommandType`, `g.command`, `g.show_command`, or `g.generic_update_command`
- handler functions in `custom.py` or another manual module file
- SDK client calls such as `client.get`, `client.list`, `client.list_by_resource_group`, `client.begin_create_or_update`, `client.begin_create`, `client.begin_update`, `client.begin_delete`, or action methods
- SDK model construction with `cmd.get_models(...)`
- command-specific validation, normalization, model shaping, LRO handling, and output shaping around SDK operations

Do not use this skill for:

- AAZ Subclass Custom (`aaz-subclass-custom`): generated AAZ command subclasses, `self.ctx.args`, `_build_arguments_schema`, `pre_operations`, or `post_operations`
- Legacy Non-SDK Custom (`legacy-non-sdk-custom`): local tools, subprocesses, data-plane workflows, raw HTTP as the primary implementation, diagnostics, installs, file/environment orchestration, or browser/proxy workflows
- editing generated files under `aaz/latest`

## Slots To Resolve

Resolve these slots before editing the related code. Prefer repository evidence over asking the user. These are not all user-provided inputs; some are derived or conditional.

```yaml
module_name: "<module under command_modules>"
command_group: "<az command group>"
command_verb_or_action: "<CLI verb/action>"
registration_file: "<commands.py or module loader file>"
command_type_name: "<local CliCommandType variable or new variable name>"
operations_tmpl: "<azure.cli.command_modules.<module>.<file>#{}>"
handler_file: "<custom.py or another manual module file>"
handler_name: "<Python function registered by the command>"
client_factory: "<cf_xxx or not-needed>"
sdk_client_methods: "<client method or methods used as primary service interface>"
sdk_model_names: "<cmd.get_models names or not-needed>"
table_transformer: "<existing transformer or not-needed>"
supports_no_wait: "<true | false | not-needed>"
customization_goals: "<crud | action | generic-update | validation | model-shaping | lro | output-shaping>"
validation_command: "<narrow command-load/help/test command or unknown>"
```

If `client_factory` or the SDK operation cannot be resolved, do not invent them. Search the module's `_client_factory.py`, neighboring command registrations, and SDK-backed sibling handlers first. Ask one focused question only when the SDK/API choice is a product decision.

## Evidence To Gather

Gather only the evidence needed for the slots.

1. Read the target module's `commands.py` around the command group and nearby `CliCommandType` definitions.
2. Read `_client_factory.py` for reusable `cf_*` factories and client shapes.
3. Read the nearest SDK-backed handler in `custom.py` or a sibling manual module.
4. Read `_params.py` only if the change needs new or changed CLI parameters.
5. Read `_help.py` or generated help only if examples/help need updates.
6. Inspect local validators, `_utils.py`, `_validators.py`, `_format.py`, and tests only when the target command needs those patterns.

## Uncertainty Gates

Before generating code, reduce uncertainty with these gates:

- If matching AAZ generated assets already implement the command and the work is only an AAZ wrapper/customization, route to `aaz-subclass-custom` instead.
- If local tools, subprocesses, data-plane calls, raw HTTP, diagnostics, install flows, or file/environment orchestration are the main behavior, route to `legacy-non-sdk-custom` instead.
- If no SDK client factory or SDK operation can be identified, stop and ask or route back to evaluation.
- If the command group already has a dominant SDK-backed style, follow its registration and handler style.
- If the command group is mixed, prefer the nearest sibling command with the same resource family and verb.
- Do not add broad abstractions unless the module already uses them or the new command shares real logic with existing handlers.

## Implementation Workflow

1. Add or reuse a `CliCommandType` in the registration file.
2. Register the command with the local style: `g.command`, `g.show_command`, or `g.generic_update_command`.
3. Add or update parameters in `_params.py` only when the handler signature or UX changes require it.
4. Add the handler function in the manual code file.
5. Keep the handler signature aligned with registration: include `cmd` when using CLI context/models, include `client` when using a `client_factory`.
6. Reuse local validators/helpers for resource group resolution, resource ID parsing, SKU checks, confirmation prompts, or cloud-specific behavior.
7. Construct SDK models with `cmd.get_models(...)` only for model types actually needed.
8. Return SDK pollers directly for LRO commands unless neighboring code wraps them with `LongRunningOperation` for a reason.
9. Update help/tests only when examples, parameters, or behavior changed.
10. Run the narrowest validation available.

## Templates

Treat templates as patterns, not fixed implementations. Replace every placeholder with names found in the target module. Never leave angle-bracket placeholders such as `<handler_name>` in generated code.

### Template: Command Registration

Use this when adding or wiring a SDK-backed handler.

```python
<command_type_name> = CliCommandType(
    operations_tmpl='azure.cli.command_modules.<module>.<handler_file>#{}',
    client_factory=<client_factory>,
    table_transformer=<table_transformer>,
)

with self.command_group('<command_group>', <command_type_name>) as g:
    g.command('<verb-or-action>', '<handler_name>', supports_no_wait=<TrueOrFalse>)
```

Omit `table_transformer` or `supports_no_wait` when not used by neighboring commands.

### Template: List Or Show Handler

Use this when the primary behavior is an SDK read operation.

```python
def <handler_name>(cmd, client, <resource_args>):
    <normalized_args> = <normalize_or_validate_args>(cmd, <resource_args>)
    return client.<get_or_list_method>(<normalized_args>)
```

### Template: Create Or Update Handler

Use this when the command builds a SDK model and sends it through a create/update SDK method.

```python
def <handler_name>(cmd, client, <resource_args>, <option_args>):
    <ModelName>, <NestedModelName> = cmd.get_models('<ModelName>', '<NestedModelName>')

    parameters = <ModelName>(
        <property_name>=<value>,
        <nested_property>=<NestedModelName>(<nested_values>),
    )

    <apply_optional_fields>(cmd, parameters, <option_args>)
    return client.<begin_create_or_update_method>(<resource_args>, parameters)
```

Use the exact SDK method name from the SDK client. Do not guess `begin_create_or_update` if the client uses a different method.

### Template: Delete Handler

Use this when the command deletes a resource through the SDK.

```python
def <handler_name>(cmd, client, <resource_args>, yes=False):
    from azure.cli.core.util import user_confirmation

    user_confirmation("Are you sure you want to delete '<resource display>'?", yes)
    <normalized_args> = <normalize_or_validate_args>(cmd, <resource_args>)
    return client.<begin_delete_method>(<normalized_args>)
```

Follow neighboring command behavior for `--yes` prompts and LRO return handling.

### Template: Generic Update

Use this when the module uses `g.generic_update_command` for read-modify-write behavior.

```python
with self.command_group('<command_group>', <command_type_name>) as g:
    g.generic_update_command(
        '<verb-or-action>',
        getter_name='<getter_handler_name>',
        setter_name='<setter_handler_name>',
        custom_func_name='<custom_update_function_name>',
        custom_func_type=<command_type_name>,
        client_factory=<client_factory>,
    )


def <getter_handler_name>(cmd, client, <resource_args>):
    return client.<get_method>(<resource_args>)


def <custom_update_function_name>(cmd, instance, <option_args>):
    if <option_arg> is not None:
        instance.<sdk_property> = <option_arg>
    return instance


def <setter_handler_name>(cmd, client, <resource_args>, parameters):
    return client.<begin_update_method>(<resource_args>, parameters)
```

Only use this template when the command group already uses generic update or when read-modify-write semantics are required.

### Fallback: Unmatched SDK Business Logic

If no template matches the requested SDK-backed behavior, do not force it into CRUD. First identify:

- the SDK client method or method sequence
- the SDK model inputs and return value
- whether the behavior is a single SDK action, read-modify-write, LRO, or multi-step SDK workflow
- whether command UX needs parameters, validators, confirmation, or output shaping

Then generate the smallest handler and helpers that express that SDK interaction. If the primary behavior stops being SDK-backed, route back to evaluation.

## Output Expectations

Before editing, report:

```yaml
route: legacy-sdk-backed-custom
module_name: "..."
command_group: "..."
command_verb_or_action: "..."
handler_file: "..."
handler_name: "..."
client_factory: "... | not-needed"
sdk_client_methods: "..."
sdk_model_names: "... | not-needed"
registration_file: "..."
customization_goals: "..."
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

If dependencies are unavailable in the local environment, state that clearly and provide the attempted command.

## Common Mistakes To Avoid

- Do not choose this skill just because code lives in `custom.py`.
- Do not invent SDK method names, model names, or client factories.
- Do not ignore the command group's existing registration style.
- Do not use SDK-backed templates for data-plane, subprocess, raw HTTP, or diagnostic workflows.
- Do not edit generated AAZ files under `aaz/latest`.
- Do not log secrets, tokens, credentials, or full request bodies containing sensitive fields.
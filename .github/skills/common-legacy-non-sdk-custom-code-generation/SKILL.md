---
name: common-legacy-non-sdk-custom-code-generation
description: "Use after routing to legacy non-SDK custom, or when adding/updating Azure CLI legacy custom command functions whose main behavior is local tools, subprocesses, data-plane APIs, raw HTTP, diagnostics, install flows, file/environment orchestration, or generated AAZ commands used only as helpers."
argument-hint: "Provide module, command group, command/action, primary workflow type, external tool/API, and intended behavior if known."
---

# Common Legacy Non-SDK Custom Code Generation

Use this workflow to generate or update hand-written Azure CLI custom command code whose primary behavior is not a simple Azure Python SDK resource operation and not an AAZ subclass customization.

This skill starts after the route is known or strongly suspected to be `legacy-non-sdk-custom`. If the route is unclear, use `common-custom-code-router` first.

## Scope

This is module-general and applies across Azure CLI command modules under `src/azure-cli/azure/cli/command_modules`.

Use this skill for:

- local tools and subprocesses such as `docker`, `podman`, `kubectl`, `helm`, `notary`, `Popen`, `subprocess.run`, or `subprocess.check_output`
- data-plane APIs, custom REST calls, raw HTTP, `send_raw_request`, `requests`, or `urlopen` as the primary behavior
- diagnostics, install flows, archive packaging, browser/proxy behavior, kubeconfig, local files, environment variables, or credential workflows
- multi-service orchestration where no single SDK CRUD/action handler describes the command
- generated AAZ commands used only as internal helpers inside a legacy custom workflow

Do not use this skill for:

- AAZ Subclass Custom (`aaz-subclass-custom`): public commands implemented by subclassing generated AAZ command classes
- Legacy SDK-Backed Custom (`legacy-sdk-backed-custom`): public commands whose main behavior is an Azure Python SDK client CRUD/action call
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
primary_workflow_type: "<local-tool | subprocess | data-plane | raw-http | diagnostic | install | file-workflow | multi-service-orchestration | aaz-helper>"
external_dependencies: "<tool/module/service names or not-needed>"
credential_source: "<CLI profile | AAD token | username/password | environment | not-needed>"
endpoint_or_target: "<URL/resource/tool target or derived>"
confirmation_required: "<true | false | not-needed>"
output_shape: "<plain result | dict | list | warning-only | delegated tool output | local pattern>"
validation_command: "<narrow command-load/help/test command or unknown>"
```

If the primary workflow type cannot be identified, stop and ask one focused question. Do not turn an unknown workflow into SDK-backed or AAZ custom only to fit a template.

## Evidence To Gather

Gather only the evidence needed for the slots.

1. Read the target module's `commands.py` around the command group and nearby `CliCommandType` definitions.
2. Read the nearest non-SDK handler in `custom.py` or sibling manual files.
3. Search for local helpers for tool discovery, subprocess execution, credential acquisition, endpoint construction, errors, and formatting.
4. Read `_params.py` only if new or changed CLI parameters are required.
5. Read `_help.py` or generated help only if examples/help need updates.
6. Read tests only when the workflow has existing test patterns or high behavioral risk.

## Uncertainty Gates

Before generating code, reduce uncertainty with these gates:

- If the command can be implemented as an AAZ subclass around a matching generated operation, route to `aaz-subclass-custom` instead.
- If the primary behavior is a single Azure Python SDK client CRUD/action call, route to `legacy-sdk-backed-custom` instead.
- If using raw HTTP only as a small guard around an AAZ subclass, route to `aaz-subclass-custom` instead.
- If a local tool is required, resolve how the module discovers that tool and how it reports missing tools.
- If subprocess is required, pass arguments as a list and avoid `shell=True` unless an existing local pattern requires it.
- If credentials, tokens, passwords, or connection strings are involved, never log them and never include them in errors.
- If the workflow reaches an external endpoint, use existing cloud suffix, profile, proxy, verification, retry, and error-handling patterns.
- If behavior is destructive, interactive, or expensive, follow local `--yes`/confirmation patterns.

## Implementation Workflow

1. Add or reuse a `CliCommandType` in the registration file. Non-SDK custom command types often have no `client_factory`.
2. Register the command with the local style: `g.command`, `g.show_command`, or another existing module pattern.
3. Add or update parameters in `_params.py` only when the command UX changes require it.
4. Add the handler function in the manual code file.
5. Keep workflow-specific logic in small helpers: tool discovery, command execution, endpoint building, credential acquisition, response parsing, and error mapping.
6. Reuse local error classes, validators, formatters, and logging style.
7. Sanitize logs and exceptions before surfacing subprocess commands, HTTP headers, request bodies, credentials, or tokens.
8. Update help/tests only when examples, parameters, or behavior changed.
9. Run the narrowest validation available.

## Templates

Treat templates as patterns, not fixed implementations. Replace every placeholder with names found in the target module. Never leave angle-bracket placeholders such as `<handler_name>` in generated code.

### Template: Command Registration Without SDK Client

Use this when registering a non-SDK custom handler.

```python
<command_type_name> = CliCommandType(
    operations_tmpl='azure.cli.command_modules.<module>.<handler_file>#{}',
    table_transformer=<table_transformer>,
)

with self.command_group('<command_group>', <command_type_name>) as g:
    g.command('<verb-or-action>', '<handler_name>')
```

Omit `table_transformer` when not used by neighboring commands. Add `client_factory` only when a secondary SDK helper is truly part of the existing local pattern, not because the command is registered through `CliCommandType`.

### Template: Local Tool Or Subprocess Workflow

Use this when the primary behavior invokes a local executable.

```python
def _get_<tool>_command():
    import shutil
    from knack.util import CLIError

    command = '<tool>'
    if not shutil.which(command):
        raise CLIError("'<tool>' is required for this command. Install it and try again.")
    return command


def _run_<tool>_command(command_parts):
    from subprocess import PIPE, Popen
    from knack.util import CLIError

    process = Popen(command_parts, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise CLIError(stderr.decode().strip() or "Command failed.")
    return stdout.decode().strip()


def <handler_name>(cmd, <args>):
    tool_command = _get_<tool>_command()
    return _run_<tool>_command([tool_command, '<subcommand>', <arg_values>])
```

Follow existing module patterns for tool fallback, platform-specific behavior, prompts, warning text, and diagnostics context.

### Template: Raw HTTP Or Data-Plane Workflow

Use this when the primary behavior calls an HTTP endpoint or data-plane API and no SDK-backed or AAZ subclass route fits.

```python
def <handler_name>(cmd, <args>):
    from azure.cli.core.util import send_raw_request

    url = <build_url_from_cloud_profile_and_args>(cmd, <args>)
    headers = <build_headers_without_logging_secrets>(cmd, <args>)
    response = send_raw_request(cmd.cli_ctx, '<METHOD>', url, headers=headers, body=<body_or_none>)
    return <deserialize_or_shape_response>(response)
```

Use existing auth helpers, cloud suffixes, request verification, and error mapping from the target module. If the API is data-plane and uses `requests`, follow neighboring module patterns for token acquisition and SSL/proxy handling.

### Template: Diagnostic Workflow

Use this when the command runs checks and reports pass/fail results.

```python
def <handler_name>(cmd, <args>, yes=False):
    results = []
    results.append(_check_<dependency>(<args>))
    results.append(_check_<connectivity>(cmd, <args>))
    return <format_diagnostic_results>(results)
```

Keep diagnostic checks independently testable. For expensive or destructive checks, follow local confirmation patterns.

### Template: AAZ Command As Internal Helper

Use this only when a legacy custom workflow calls a generated AAZ command internally but the public command remains legacy non-SDK custom.

```python
def <handler_name>(cmd, <args>):
    from .aaz.latest.<resource_path>._show import Show as <AAZShow>

    result = <AAZShow>(cli_ctx=cmd.cli_ctx)(command_args={
        '<arg-name>': <arg-value>,
    })
    return <continue_legacy_workflow>(cmd, result, <args>)
```

Do not confuse this with AAZ subclass custom. If the public command itself should be an AAZ subclass, route to `aaz-subclass-custom`.

### Fallback: Unmatched Non-SDK Business Logic

If no template matches the requested workflow, do not force it into local tool, raw HTTP, or diagnostics. First identify:

- the workflow boundary and primary side effect
- external dependencies and how the module already discovers or authenticates them
- whether the handler needs `cmd`, CLI context, profile/cloud data, credentials, confirmation, or local files
- output shape and error behavior
- the smallest helper functions needed to isolate risky operations

Then generate the smallest legacy handler and helpers that match the local module pattern. If the primary service interface becomes SDK or AAZ, route back to evaluation.

## Output Expectations

Before editing, report:

```yaml
route: legacy-non-sdk-custom
module_name: "..."
command_group: "..."
command_verb_or_action: "..."
handler_file: "..."
handler_name: "..."
primary_workflow_type: "..."
external_dependencies: "... | not-needed"
credential_source: "... | not-needed"
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
4. For local-tool commands, a dry-run, mockable helper test, or help/load check rather than invoking destructive external effects.
5. `git status --short` and a diff review only when executable validation is unavailable.

If dependencies are unavailable in the local environment, state that clearly and provide the attempted command.

## Common Mistakes To Avoid

- Do not choose this skill just because code lives in `custom.py`.
- Do not classify SDK CRUD/action handlers as non-SDK because they include local validation helpers.
- Do not use `shell=True` unless a local pattern requires it and inputs are controlled.
- Do not log secrets, tokens, passwords, credentials, or full commands containing sensitive values.
- Do not run destructive local tools or external operations during validation.
- Do not edit generated AAZ files under `aaz/latest`.
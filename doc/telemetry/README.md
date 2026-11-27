# Telemetry Documentation

> Two types of telemetry are used to monitor and analyze execution of Azure CLI commands. One called ARM telemetry is recorded basing on HTTP traffic by ARM, and another is client side telemetry sent by Azure CLI.

## ARM Telemetry

ARM telemetry tracks all HTTP requests and responses through ARM endpoint. As far as we know, below cases don't have ARM telemetry record.
- Command doesn't create request successfully, for instance, parameter cannot pass validation, request or payload cannot be constructed.
- Command calls data plane service API.
- Network is inaccessible.
- No request is needed during execution.


## CLI Client Telemetry

Client side telemetry is sent at the end of Azure CLI command execution. It covers all commands, no matter if it has HTTP requests or just has local operations.
Sanitized data is stored in Kusto cluster which is managed by DevDiv Data team.

All Azure CLI data is stored in a large json named `Properties` in table `RawEventsAzCli`. Some properties are flatten, some are not. Here are some useful fields:
> The telemetry has different schema pre Azure CLI 2.0.28. All the fields explained below are for new schema, in other words, CLI version > 2.0.28.

- `EventName`: `azurecli/command` or `azurecli/fault` or `azurecli/extension`
    - `azurecli/command` means this is common event record with general `Properties` field.
    - `azurecli/fault` means this is additional event record with extra exception info in `Properties` field.
    - `azurecli/extension` means this is additional event record with customized info in `Properties` field.
    - Additional event record can be joined with common event record using `CorrelationId`.
- `CorrelationId`: GUID to join additional event records with common event record
    - `azurecli/extension` event records have the same `CorrelationId` with related `azurecli/command` event record.
    - `azurecli/fault` event has `Properties['reserved.datamodel.correlation.1']` field. The field value is `{correlationId},UserTask,` where `{correlationId}` is `CorrelationId` field of related `azurecli/command` record.
- `EntityType`: `UserTask`/`Fault`
    - For `EventName == 'azurecli/command'`, the `EntityType` is `UserTask`.
    - For `EventName == 'azurecli/fault'`, the `EntityType` is `Fault`.
- `EventTimeStamp`: time when the telemetry record is sent
- `ProductVersion`: CLI core version in the format of `azurecli@{version}`
- `CoreVersion`: CLI core version
- `ExeVersion`: `{cli_core_version}@{module_version}`. In the new schema (CLI version > 2.0.28), all module versions are `none`. Hence this field is `{cli_core_version}@none`
- `OsType`: OS system, e.g., linux, windows
- `OsVersion`: OS platform version, e.g., 10.0.14942
- `PythonVersion`: platform python version
- `ShellType`: cmd/bash/ksh/zsh/cloud-shell/... Note: may not be accurate.
- `MacAddressHash`: SHA256 hashed MAC address
- `MachineId`: GUID coming from the first 128bit of MacAddressHash
- `UserId`: CLI installation id. Each CLI client installed locally will have a GUID as installation id. It's stored in $homeFolder/.azure/azureProfile.json
- `SessionId`: SHA256 hashed result of CLI installation id, parent process (terminal session) creation time and parent process (terminal session) id. Note: may not be accurate.
- `RawCommand`: CLI command name
- `Params`: CLI command arguments (without argument value)
- `AzureSubscriptionId`: current subscription id
- `ClientRequestId`: GUID which is set on HTTP header
- `StartTime`: time when the command begins executing
- `EndTime`: time when the command exits
- `ActionResult`: 
    - For `EntityType == 'UserTask'`, it could be `Success`/`Failure`/`UserFault`/`None`. All others besides `Success` means failure.
    - For `EntityType == 'Fault'`, it's empty.
- `ResultSummary`: details of result, may be suppressed to meet security & privacy requirements.
- `ExceptionMessage`: details of exception, may be suppressed to meet security & privacy requirements.
- `Properties`: large json with all constructed fields. Below is to explain some unflattened fields not introduced before.
    - `reserved.datamodel.entityname`: CLI command name with hyphens
    - `reserved.datamodel.correlation.1`: Additional field when `EventName == 'azurecli/fault'`. It's in the format of `{correlationId},UserTask,` where `{correlationId}` is `CorrelationId` field of related `EventName == 'azurecli/command'` record.
    - `reserved.datamodel.fault.typestring`: Additional field when `EventName == 'azurecli/fault'`. It logs the exception class.
    - `reserved.datamodel.fault.description`: Additional field when `EventName == 'azurecli/fault'`. It logs exception description or fault type.
    - `context.default.vs.core.os.platform`: OS platform
    - `context.default.azurecli.source`: `az`/`completer`. It's `completer` if we found argument auto complete settings in OS environment variable.
    - `context.default.azurecli.environmentvariables`: It logs customer's environment variables starting with `AZURE_CLI`
    - `context.default.azurecli.extensionname`: It logs the extension name and version in the format of `{extension_name}@{extension_version}` if the command is from CLI extension.
    - `context.default.azurecli.installer`: value of os environment variable `AZ_INSTALLER`
    - `context.default.azurecli.agent`: advertised agent context; see [Agent context](#agent-context) below. Analytics mapping and allowlisting must be confirmed by the telemetry service team.
    - `context.default.azurecli.error_type`: It logs the exception class name.
    - `context.default.azurecli.exception_name`: A supplementation for `context.default.azurecli.error_type`


## Agent context

`Context.Default.AzureCLI.Agent` is a name-only string on ordinary `azurecli/command`
events, including commands that do not authenticate. It is independent of
`AgenticSession`, which describes the agentic authentication path, not general agent use.
The existing payload builder also copies this property to additional fault events;
it does not decorate arbitrary custom/extension events. Count command events rather
than duplicated fault metadata when measuring command usage.

The initial values are `claude-code`, `copilot-cli`, `copilot-vscode`, `codex`,
`cursor`, `gemini-cli`, `unknown` and `multiple`. Detection reads only these signals:

| Environment variable | Recognized value | Agent |
| --- | --- | --- |
| `AI_AGENT` | Exactly `github_copilot_vscode_agent` | `copilot-vscode` |
| `CLAUDE_CODE_CHILD_SESSION` | Exactly `1` | `claude-code` |
| `COPILOT_CLI` | Exactly `1` | `copilot-cli` |
| `COPILOT_AGENT` | Exactly `1` | `copilot-vscode` |
| `CODEX_CI` | Exactly `1` | `codex` |
| `CURSOR_AGENT` | Any nonempty value, including `0` | `cursor` |
| `GEMINI_CLI` | Exactly `1` | `gemini-cli` |

The exact recognized `AI_AGENT` value wins over every fallback. It identifies the
advertised VS Code surface, which can host other underlying agents. Missing, empty
or unsupported `AI_AGENT` values (including version-bearing Claude formats and
values longer than 96 characters) fall back to the remaining six signals. Comparisons
are case-sensitive, with no trimming or prefix matching. Zero distinct fallback
names gives `unknown`, one gives that name, and more than one gives `multiple`.
`CLAUDECODE` alone and generic IDE/CI markers are not used.

Only constant names are emitted: no raw environment values, agent versions, account
data, prompts, paths or session/conversation IDs are collected by this detector.
Collection follows the existing telemetry consent and forbidden-cloud policy,
including `core.collect_telemetry` and `AZURE_CORE_COLLECT_TELEMETRY`; disabling
collection skips detection on the normal finalization paths as well as payload saving.
No new network request, storage or configuration surface is introduced.

Signals can be inherited, copied, stale, spoofed, absent or unavailable in some
agent execution paths. This property does not prove AI authorship, identify a
person or model, count agent sessions or imply authorization. `unknown` does not
mean human use. A missing property is different from `unknown`: older clients,
ingestion rollout, suppressed custom events and payload/upload failures can all
cause absence. Local tests establish detection and payload behavior, not vendor
runtime coverage or ingestion. The expected analytics spelling is
`context.default.azurecli.agent`; its service mapping/allowlisting is not established
by the client-side addition.


## Doc Sections

- [Kusto Examples](kusto_examples.md) - Samples for kusto query

- [FAQ](faq.md) - Frequently Asked Questions

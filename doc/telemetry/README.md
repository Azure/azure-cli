Telemetry Documentation
=======================

> Two types of telemetry are used to monitor and analyze execution of Azure CLI commands. One called ARM telemetry is recorded basing on HTTP traffic by ARM, and another is client side telemetry sent by Azure CLI.

### ARM Telemetry
ARM telemetry tracks all HTTP requests and responses through ARM endpoint. As far as we know, below cases don't have ARM telemetry record.
- Command doesn't create request successfully, for instance, parameter cannot pass validation, request or payload cannot be constructed.
- Command calls data plane service API.
- Network is inaccessible.
- No request is needed during execution.

Kusto Cluster and Database: https://dataexplorer.azure.com/clusters/armprod/databases/ARMProd


### CLI Client Telemetry
Client side telemetry is sent at the end of Azure CLI command execution. It covers all commands, no matter if it has http requests or just has local operations.
Sanitized data is stored in Kusto cluster which is managed by DevDiv Data team.

Kusto Cluster and Database: https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli

Properties
All Azure CLI data is stored in a large json named `Properties` in table `RawEventsAzCli`. Some properties are flatten, some are not. Here's some useful fields:
> The telemetry has different schema pre Azure CLI 2.0.28. All the fields explained below are for new schema, in other words, CLI version > 2.0.28.
- `EventName`: `azurecli/command` or `azurecli/fault` or `azurecli/extension`.
    - `azurecli/command` means this is common event record with general `Properties` field.
    - `azurecli/fault` means this is additional event record with extra exception info in `Properties` field.
    - `azurecli/extension` means this is additional event record with customized info in `Properties` field.
    - Addition event record can be joined with common event record using `CorrelationId`.
- `CorrelationId`: GUID to join additional events with common event
    - `azurecli/extension` event records have the same `CorrelationId` with related `azurecli/command` event record.
    - `azurecli/fault` event has `Properties['reserved.datamodel.correlation.1']` field. The field value is `{correlationId},UserTask,` where `{correlationId}` is `CorrelationId` field of related `azurecli/command` record.
- `EntityType`: `UserTask`/`Fault`.
    - For `EventName == azurecli/command`, the `EntityType` is `UserTask`.
    - For `EventName == azurecli/fault`, the `EntityType` is `Fault`.
- `EventTimeStamp`: time when the telemetry record is sent.
- `ProductVersion`: CLI core version in the format of `azurecli@{version}`
- `CoreVersion`: CLI core version
- `ExeVersion`: `{cli_version}@{module_version}`. In the new schema(CLI version > 2.0.28), all module versions are `none`.
- `PythonVersion`: platform python version
- `OsVersion`: OS platform version, eg. 10.0.14942
- `OsType`: OS system, eg. linux, windows
- `ShellType`: cmd/bash/ksh/zsh/cloud-shell/... Note: may not be accurate.
- `MacAddressHash`: SHA256 hashed MAC address
- `MachineId`: GUID coming from the first 128bit of MacAddressHash
- `UserId`: CLI installation id. Each CLI client installed locally will have a GUID as installation id.
- `SessionId`: SHA256 hashed result of CLI installation id, parent process(terminal session) creation time and parent process(terminal session) id. Note: may not be accurate.
- `RawCommand`: CLI command name
- `Params`: CLI command arguments(without argument value)
- `AzureSubscriptionId`: current subscription id.
- `ClientRequestId`: GUID which is set on HTTP header.
- `StartTime`: time when the command begins executing.
- `EndTime`: time when the command exit.
- `ActionResult`: 
    - For `EntityType == 'UserTask'`, it could be `Success`/`Failure`/`UserFault`/`None`. All others besides `Success` means failure.
    - For `EntityType == 'Fault'`, it's empty.
- `ResultSummary`: details of result, may be suppressed to meet security & privacy requirements.
- `ExceptionMessage`: details of exception, may be suppressed to meet security & privacy requirements.
- `Properties`: large json with all constructed fields. Below is to explain some fields not introduced before.
    - `reserved.datamodel.entityname`: CLI command name with hyphens
    - `reserved.datamodel.correlation.1`: Additional field when `EventName == 'azurecli/fault'`. It's in the format of `{correlationId},UserTask,` where `{correlationId}` is `CorrelationId` field of related `EventName == 'azurecli/command'` record.
    - `reserved.datamodel.fault.typestring`: Additional field when `EventName == 'azurecli/fault'`. It logs the exception class.
    - `reserved.datamodel.fault.description`: Additional field when `EventName == 'azurecli/fault'`. It logs exception description or fault type.
    - `context.default.azurecli.source`: `az`/`completer`. It's `completer` if we found argument auto complete settings in os environment variable.
    - `context.default.azurecli.environmentvariables`: It logs customer's environment variables start with `AZURE_CLI`
    - `context.default.azurecli.extensionname`: It logs the extension name and version in the format of `{extension_name}@{extension_version}` if the command is from CLI extension.
    - `context.default.azurecli.installer`: The value of os environment variable `AZ_INSTALLER`
    - `context.default.azurecli.error_type`: It logs the exception class.
    - `context.default.azurecli.exception_name`: A supplementation for `context.default.azurecli.error_type`

### Accessing Client Telemetry
To ensure you have a smooth experience using our Data Tools and Data, you have to take the required trainings and join a security group.

Please follow instruction [Accessing DevDiv Data](https://devdiv.visualstudio.com/DevDiv/_wiki/wikis/DevDiv.wiki/9768/Accessing-DevDiv-Data) to get access permission.


### Doc Sections

- [Kusto Examples](kusto_examples.md) - Samples for kusto query

- [FAQ](faq.md) - Commonly asked questions

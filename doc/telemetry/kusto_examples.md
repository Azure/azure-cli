# Samples for kusto query

## Query for new schema
CLI telemetry has different schema after version 2.0.28

```
RawEventsAzCli
| where split(ProductVersion, '.')[0] == 'azurecli@2'
| where toint(split(ProductVersion, '.')[1]) > 0 or toint(split(ProductVersion, '.')[2]) > 28
| take 5
```

## Query for specific command
e.g. `az account show` command

```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| where RawCommand == 'account show'
| take 10
```

## Query for specific command group
e.g. `az storage account` command group

```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| where RawCommand startswith "storage account"
| take 10
```

## Query for specific command with specific cli version
e.g. `az account show` command with CLI version `2.35.0`

```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| where RawCommand == 'account show'
| where ProductVersion == 'azurecli@2.35.0'
| take 10
```

## Query for specific command with specific cli extension version
e.g. `az connectedk8s connect` command with version `1.2.8` of extension `connectedk8s`

```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| extend ExtensionName = tostring(Properties["context.default.azurecli.extensionname"])
| where RawCommand == 'connectedk8s connect'
| where ExtensionName == 'connectedk8s@1.2.8'
| take 10
```

## Count specific command calls by date
e.g. `az account show` usage by date

```
RawEventsAzCli
| where EventTimestamp > ago(7d)
| where RawCommand == 'account show'
| summarize cnt=count() by ts=bin(EventTimestamp, 1d)
| order by ts desc 
```

## Calculate success rate for specific command
e.g. `az group create` command

```
RawEventsAzCli
| where EventTimestamp > ago(7d)
| where RawCommand == 'group create'
| where EventName == 'azurecli/command'
| summarize count() by ActionResult
```
Note: `where EventName == 'azurecli/command'` is necessary because in some cases one record will have additional records whose `EventName` could be `azurecli/extension` or `azurecli/fault`. If you count these additional records, some calls might be calculated twice or more times.

## Query failure details for specific command
e.g. `az group create` command

```
RawEventsAzCli
| where EventTimestamp > ago(1d)
| where RawCommand == 'group create'
| where ActionResult != 'Success'
| extend  ErrorType = tostring(Properties['context.default.azurecli.error_type'])
| extend ExceptionName = tostring(Properties['context.default.azurecli.exception_name'])
| extend FaultDescription = tostring(Properties['reserved.datamodel.fault.description'])
| project EventName, RawCommand, Params, ActionResult, ErrorType, ExceptionName, FaultDescription, ResultSummary, ExceptionMessage, Properties
```
Notes: `ResultSummary` and `ExceptionMessage` might be suppressed to meet security & privacy requirements.

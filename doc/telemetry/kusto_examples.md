#Samples for kusto query

## Query for new schema
CLI telemetry has different schema after version 2.0.28

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAAwtKLHctS80rKXascs7J5KpRKM9ILUpVKC7IySzRCCjKTylNLglLLSrOzM/TUVDXU9eMNohVsLVVUE+sKi1KTc7JdDBSh+sqyc/MK9HAo9cwVlPBTsFAIb+IsFojsFojC6DpJYnZqQqmAIl8AharAAAA)
```
RawEventsAzCli
| where split(ProductVersion, '.')[0] == 'azurecli@2'
| where toint(split(ProductVersion, '.')[1]) > 0 or toint(split(ProductVersion, '.')[2]) > 28
| take 5
```

## Query for specific command
e.g. `az account show` command

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAAwtKLHctS80rKXascs7J5KpRKM9ILUpVAIuFZOamFpck5hYo2CkkpudrGGZowhUEJZY75+fmJualKNjaKqgnJifnl+aVKBRn5JerAxWVJGanKhgaAABH9KmYXgAAAA==)
```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| where RawCommand == 'account show'
| take 10
```

## Query for specific command group
e.g. `az storage account` command group

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAAz3KQQqAIBAAwHuvWDzVLT8QhPQB6QOLLSqlhm4J0eOLDl2H0VinkyKX8VKbb26ojjLBZ7MPVBjDDgOgTa103R80VpVCwLjAWzKX6tmBKJwyWgI0Jh2RxfsZVwLZP6LV9udpAAAA)
```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| where RawCommand startswith "storage account"
| take 10
```

## Query for specific command with specific cli version
e.g. `az account show` command with CLI version `2.35.0`

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAAz3KsQqDMBAA0L1fcZt1Ea04Wlqku0hxP+LRhJpcSS4GpB9ftOD6eAOmx0JOwn3tZnP6QtLkCXZ7GktB0H7gCvjic6XzIwyYOrYW3QRtCxkqxdEJBM0pO1LveYpKRvLBsPvHNXpSs7ldiropyu0Kvgmq8gc6Rz0AigAAAA==)
```
RawEventsAzCli
| where EventTimestamp > ago(1h)
| where RawCommand == 'account show'
| where ProductVersion == 'azurecli@2.35.0'
| take 10
```

## Query for specific command with specific cli extension version
e.g. `az connectedk8s connect` command with version `1.2.8` of extension `connectedk8s`

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAA12OvQ6CQBCEe59iQwM0F7GiwWgIrTHEzlhsYMUL3B25W8QQH97D+BOtJjv5ZmdKHIsraXbbKe/k4g7jhSzB0ztIRY5R9bAGbEyUXGIP0I1J11DM4qTRO1QEGbBxbKVuor01PVmW5I5BZTR7XtR0xqFjgdNgqeqkoHda+3Rwij/FJY65UQp9Q5ZB6B9oqpjqNnXwOsLvyt8Nf/wmESuRzjRjS5AsH7YF5vDsAAAA)
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

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAA1WMwQrCMBAF737FuzUFL548RZDiDxR/YJssNmASyW4NFj/eEkHwOjPMSPXy5KRyXod72L1RZy6Mxq4hsijFB06gWzZH3/+CkeqQY6TkYS06ci4vSSFzrt0WybK5ElaGS2qbMz2mF1TsFJL5/+9xaOtcPJdvBc/iPgod8yqdAAAA)
```
RawEventsAzCli
| where EventTimestamp > ago(7d)
| where RawCommand == 'account show'
| summarize cnt=count() by ts=bin(EventTimestamp, 1d)
| order by ts desc 
```

## Calculate success rate for specific command
e.g. `az group create` command

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAA1XMwQrCMBAE0Ltfsbe2J4+eKpTi1UPwB9Z0qYEkWzYbg8GPb60geBuGN2OwXJ4UNQ119O7whvIgIdi7mwuUFMMCZ8CZ29PU/YDBMnIIGCfoe2hm4byAFUKl5v/lioF2gzULWe+O9jv8uJS3KK4SWM5R2w7uLxisOo6GUva6AvX30C+gAAAA)
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

[Execute in Web](https://dataexplorer.azure.com/clusters/ddazureclients/databases/AzureCli?query=H4sIAAAAAAAAA52Ry2rDMBBF9/0KdeUEhKEf4EJI3V1LcLIrJQzS1FGxHozGcRL68ZVtGseUbroV554Z3amgK4/oOK4u68bcfYnugIRieNsZi5HBBvEooPaLB728AhV0a28tOC2KQmQ1+TYIRQiM2RVaKTbeVRjbhsV9wratUhhjT+CJMYVFSeRpdw4oCsE+MhlXLzbkAxIbjG+Z8o4TnGv8gOTJ4dISqsbk2Cf3nKLZ+3IylieFoZ/7CvYf0p/03qX4TPzck08YFZmB+MtNGJGOqHMNqTyvscnHIXrKjuJA/hMVj23368qbXqXYAIGNclajnAqT86/KXwsm25DZtklI5xv+JR0B6hSZ9v4GVmNP5AkCAAA=)
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

#FAQ

## What's the relationship of CLI telemetry and ARM telemetry?

- CLI telemetry is client telemetry. It logs os, platform, command, parameter, result and other client info.
- ARM telemetry is server telemetry. It tracks all HTTP requests and responses through ARM endpoint from different clients, including CLI, Powershell, SDK...
- They share the same `clientRequestId` which you can leverage to join `HttpIncomingRequests` (ARM telemetry table) with `RawEventsAzCli` (CLI telemetry table)


## How can I filter CLI requests from ARM telemetry?

[Execute in Web](https://dataexplorer.azure.com/clusters/armprod/databases/ARMProd?query=H4sIAAAAAAAAA/MoKSnwzEvOz83MSw9KLSxNLS4p5qpRKM9ILUpVCPH0dQ0OcfQNULBTSEzP1zDM0ITLlRanFjmmp+aVKCTn55UkZuYVK6g7VpUWpTr7eOob6akDFZYkZqcqGBoAAPoAVdxjAAAA)
```
HttpIncomingRequests
| where TIMESTAMP > ago(1h)
| where userAgent contains 'AzureCLI/2.'
| take 10
```

## How can I collect customized properties into CLI telemetry?

You can utilize `add_extension_event` [function](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/telemetry.py#L418-L420) to collect properties for your extension.

When customers run command, in additional to general CLI record whose `EventName` is `azurecli/command`, there will be another record whose `EventName` is `azurecli/extension` recorded in CLI telemetry.

And you can join the general `azurecli/command` record with `azurecli/extension` record on `CorrelationId` field.


## How can customer disable telemetry collection?

We have an switch for customer to disable/enable telemetry collection. Try `az config set core.collect_telemetry=true` for enabling and `az config set core.collect_telemetry=false` for disabling.

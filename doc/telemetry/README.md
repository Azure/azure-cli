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
- 

### Accessing Client Telemetry
To ensure you have a smooth experience using our Data Tools and Data, you have to take the required trainings and join a security group.

Please follow instruction [Accessing DevDiv Data](https://devdiv.visualstudio.com/DevDiv/_wiki/wikis/DevDiv.wiki/9768/Accessing-DevDiv-Data) to get access permission.


### Doc Sections

- [Kusto Examples](kusto_examples.md) - Samples for kusto query

- [FAQ](faq.md) - Commonly asked questions

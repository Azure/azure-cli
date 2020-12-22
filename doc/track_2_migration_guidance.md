# Track 2 Migration Guidance

Azure CLI is built upon Azure Python SDK. Recently Azure Python SDK announced next generation product. It is named Track 2 SDK. The old version of SDK is named Track 1. It claims that it has great advantages than Track 1 SDK. It is not compatible with Track 1 SDK. Azure CLI developers need to spend considerable time and do some work to migrate from Track 1 SDK to Track 2 SDK. Let's see an example of Track 2 SDK. [azure-mgmt-compute 17.0.0b1](https://pypi.org/project/azure-mgmt-compute/17.0.0b1/) introduces important breaking changes and important new features like unified authentication and asynchronous programming.

This document summarizes typical issues and solutions when adopting Track 2 SDK in Azure CLI. Below is a list of typical issues.

1. Long running operation function name change
2. Property name change
3. Class name change
4. Error type change
5. No enum type
6. Class hierarchy change
7. Obtaining Subscription
8. Multi-API support
9. Fixing mocked object
10. Modifying patch_models.py to include missing packages
11. Missing x-ms-authorization-auxiliary

**Long running operation function name change**

Long running operations have changed their function names in Track 2 SDK. A `begin_` prefix is added. E.g. `create_or_update` becomes `begin_create_or_update`. `delete` becomes `begin_delete`. It is a naming convention in Track 2 SDK to indicate that an operation is a long running operation.

**Property name change**

Some of property names change in Track 2 SDK.

Examples:

```
hyperVgeneration -> hyperVGeneration
disk_mbps_read_only -> disk_m_bps_read_only
disk_mbps_read_write -> disk_m_bps_read_write
virtual_machine_extension_type -> type_properties_type
type1 -> type_properties_type
instance_ids -> vm_instance_i_ds
diskMbpsReadWrite -> diskMBpsReadWrite
```

Some changes are unnecessary, even wrong in English.

**Class name change**

Some of class names change in Track 2 SDK.

Examples:

```
VirtualMachineIdentityUserAssignedIdentitiesValue -> UserAssignedIdentitiesValue
```

**Error type change**

Error type changes in Track2 SDK.

Examples:

```
CloudError -> azure.core.exceptions.ResourceNotFoundError
```

**No enum type**

Track 2 SDK removes enum type and adopts string type instead. It loses the validation on values. Anyway, do not use `obj.value` any longer. Just use `obj`.

**Class hierarchy change**

The class hierarchy may change in Track 2 SDK. Some properties are not flattened. They are wrapped in classes. 

Examples:

In VMSS `begin_update_instances`, a new type `VirtualMachineScaleSetVMInstanceRequiredIDs` is added.

In DiskAccess `begin_create_or_update`, location and tags are moved to a nested structure `DiskAccess`, `disk_access = DiskAccess(location=location, tags=tags)`

**Obtaining Subscription**

There are various ways to obtain subscription ID. Obtaining it from `client.config` does not work in Track 2 SDK any longer.

Examples:

```
subscription = client.config.subscription_id ->
from azure.cli.core.commands.client_factory import get_subscription_id
subscription = get_subscription_id(cmd.cli_ctx)
```

In this example, the reason that old one fails is that `config` is renamed to `_config` in Track 2 SDK.

**Multi-API support**

Remember to support multi-API. It reveals multi-API error when Track 2 SDK is adopted if we don't run live test for all tests. Actually the original code is wrong. It doesn't handle multi-API support well.

**Fixing mocked object**

The problem I met is property name change. It is hard to find the line of code that causes the error. Please update mocked object construction code and make sure it is up-to-date.

**Modifying patch_models.py to include missing packages**

It is only used in CI jobs. It patches some code to SDK. This file should be deprecated. It was written long time ago. But for now, just modify this file and add missing packages.

**Missing x-ms-authorization-auxiliary**

Cross tenant authentication support is missing in Azure CLI Core and Azure Core package. In request header, we use x-ms-authorization-auxiliary to pass auxiliary authorization token. Compute module is the first customer to have this requirement in Track 2 SDK. In azure/core/pipeline/policies/_authentication.py, there is a class BearerTokenCredentialPolicy. It simplifies bearer token authorization header configuration. However, auxiliary bearer token authorization is not supported in Azure Core policies [1] yet. The current solution is getting tokens manually, setting headers in client constructor or in operation call time manually. They said they will support this policy in the future. Azure CLI Core also needs an upgrade to provide better interfaces for Track 2 SDK users.

You are welcome to contribute to this document if you have experience of Track 2 SDK.

**References**

[1] https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/core/azure-core/CLIENT_LIBRARY_DEVELOPER.md#available-policies


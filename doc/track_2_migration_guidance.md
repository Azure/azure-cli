# Track 2 Migration Guidance

Azure CLI is built on Azure Python SDKs. Recently, Azure Python SDK team announced the next generation product, named Track 2 SDK. The old version of SDK is called Track 1 SDK. It claims that it has some advantages than Track 1 SDK. It is not compatible with Track 1 SDK. A considerable number of work days are required for Azure CLI developers to migrate their modules from Track 1 SDK to Track 2 SDK. Let's see an example of Track 2 SDK. [azure-mgmt-compute 17.0.0b1](https://pypi.org/project/azure-mgmt-compute/17.0.0b1/) introduces important breaking changes and important new features like unified authentication and asynchronous programming.

This document summarizes the steps to apply the changes for migration, typical changes when adopting Track 2 SDK in Azure CLI.

## Example PRs
1. [Compute PR #15750](https://github.com/Azure/azure-cli/pull/15750)
2. [Network PR #16245](https://github.com/Azure/azure-cli/pull/16245)
3. [Network PR #16350](https://github.com/Azure/azure-cli/pull/16350)
4. [Storage PR #15845](https://github.com/Azure/azure-cli/pull/15845)
5. [KeyVault PR #14150](https://github.com/Azure/azure-cli/pull/14150)
6. [AppConfig PR #16376](https://github.com/Azure/azure-cli/pull/16376)
7. [AppService PR #17146](https://github.com/Azure/azure-cli/pull/17146)

## Steps to apply the changes for migration
1. Upgrade the version of your SDK to track 2 SDK in [setup.py](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/setup.py), [requirements.py3.Darwin.txt](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/requirements.py3.Darwin.txt), [requirements.py3.Linux.txt](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/requirements.py3.Linux.txt) and [requirements.py3.windows.txt](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/requirements.py3.windows.txt).
2. Run command `azdev setup` to apply track 2 SDK to your local virtual environment.
3. Run style check with command `azdev style your_module_name` and fix the errors returned from the command.
4. Run linter check with command `azdev linter your_module_name` and fix the errors returned from the command.
5. Run tests with command `azdev test your_module_name --no-exitfirst` and fix the errors returned from the command.
6. Run tests lively with command `azdev test your_module_name --live --no-exitfirst` and fix the errors returned from the command.
7. Create the pull request for migration.

## Typical changes.

1. [Long running operation function name change](#long-running-operation-function-name-change)
2. [Property name change](#property-name-change)
3. [Class name change](#class-name-change)
4. [Error type change](#error-type-change)
5. [No enum type](#no-enum-type)
6. [Class hierarchy change](#class-hierarchy-change)
7. [Obtaining Subscription](#obtaining-subscription)
8. [Multi-API support](#multi-api-support)
9. [Fixing mocked object](#fixing-mocked-object)
10. [Modifying patch_models.py to include missing packages](#modifying-patch_modelspy-to-include-missing-packages)
11. [Missing x-ms-authorization-auxiliary](#missing-external-tenant-authentication-support)

### Long running operation function name change

Long running operations have changed their function names in Track 2 SDK. A `begin_` prefix is added. For example, `create_or_update` becomes `begin_create_or_update`. `delete` becomes `begin_delete`. It is a naming convention in Track 2 SDK to indicate that an operation is a long running operation. Test cases can reveal most instances, but if a command has no test, it may be missed. A reliable approach is going through all methods to see whether they are long running operations.


### Property name change

Some of property names change in Track 2 SDK.

Here are some examples. `->` is not Python code. It represents the left one is updated to the right one.

```
hyperVgeneration -> hyperVGeneration
disk_mbps_read_only -> disk_m_bps_read_only
disk_mbps_read_write -> disk_m_bps_read_write
virtual_machine_extension_type -> type_properties_type
type1 -> type_properties_type
instance_ids -> vm_instance_i_ds
diskMbpsReadWrite -> diskMBpsReadWrite
ipv4 -> I_PV4
```

Some changes are unnecessary, even wrong in English. I opened [Azure/autorest.python#850](https://github.com/Azure/autorest.python/issues/850) to track this problem.

### Class name change

Some of class names change in Track 2 SDK.

[Example](https://github.com/Azure/azure-cli/pull/15750/files#diff-fd5160263d5431e9cdbf0f83abad213589c44c4c2724ff66b1172218caeb8396R629):

```
VirtualMachineIdentityUserAssignedIdentitiesValue -> UserAssignedIdentitiesValue
```

### Error type change

Error type changes in Track2 SDK.

Examples:

```
msrestazure.azure_exceptions.CloudError -> azure.core.exceptions.ResourceNotFoundError
msrest.exceptions.ClientException -> azure.core.exceptions.HttpResponseError
ErrorException -> HttpResponseError
```

### No enum type

Track 2 SDK removes enum type and adopts string type instead. It loses the validation on values. Anyway, do not use `obj.value` any longer. Just use `obj`.

### Class hierarchy change

The class hierarchy may change in Track 2 SDK. Some properties are not flattened. They are wrapped in classes. In Track 1 SDK, if the number of parameters is less than 3, it will be flattened.

Examples:

In [VMSS](https://github.com/Azure/azure-cli/pull/15750/files?file-filters%5B%5D=.py#diff-fd5160263d5431e9cdbf0f83abad213589c44c4c2724ff66b1172218caeb8396R2688) `begin_update_instances`, a new type `VirtualMachineScaleSetVMInstanceRequiredIDs` is added.

In [DiskAccess](https://github.com/Azure/azure-cli/pull/15750/files#diff-fd5160263d5431e9cdbf0f83abad213589c44c4c2724ff66b1172218caeb8396R3602) `begin_create_or_update`, location and tags are moved to a nested structure `DiskAccess`, `disk_access = DiskAccess(location=location, tags=tags)`

In [Storage](https://github.com/Azure/azure-cli/pull/15845/files#diff-4cfe9a680ae04774e116b45bc06a679db751bfad1de211c6d2b3bc471900d8bfR23),
```
client.check_name_availability(account_name) // account_name is string
```
turns into
```
account_name = StorageAccountCheckNameAvailabilityParameters(name=name) client.check_name_availability(account_name)
```

In [AppConfig](https://github.com/Azure/azure-cli/pull/16376/files#diff-1796b5bb574aca9235e83b02a207cb8a42aafab920f3aae1c46af22bf0ce5aa4R191), `id` cannot be passed directly to `regenerate_key method`. It needs to be wrapped in the new model `RegenerateKeyParameters`.

### Obtaining subscription

There are various ways to obtain subscription ID. Obtaining it from `client.config` does not work in Track 2 SDK any longer.

Examples:

```
subscription = client.config.subscription_id ->
from azure.cli.core.commands.client_factory import get_subscription_id
subscription = get_subscription_id(cmd.cli_ctx)
```

In this example, the reason that old one fails is that `config` is renamed to `_config` in Track 2 SDK.

### Multi-API support

Remember to support multi-API. It reveals multi-API error when Track 2 SDK is adopted if we don't run live test for all tests. Actually the original code is wrong. It doesn't handle multi-API support well.

### Fixing mocked object

The problem I met is property name change. It is hard to find the line of code that causes the error. Please update mocked object construction code and make sure it is up-to-date.

### Modifying patch_models.py to include missing packages

It is only used in CI jobs. It patches some code to SDK. This file should be deprecated. It was written long time ago. But for now, just modify this file and add missing packages.

[Example](https://github.com/Azure/azure-cli/pull/15750/files#diff-e1256a3d1d91aea524b252fa7dc4a64b83d183b7f57fb5c326b270a1c4b224a7)

### Missing external tenant authentication support

External tenant authentication support is missing in Azure CLI Core and Azure Core package. In request header, we use x-ms-authorization-auxiliary to pass auxiliary authorization token. Compute module is the first customer to have this requirement in Track 2 SDK. In azure/core/pipeline/policies/_authentication.py, there is a class BearerTokenCredentialPolicy. It simplifies bearer token authorization header configuration. However, auxiliary bearer token authorization is not supported in Azure Core policies [1] yet. The current solution is getting tokens manually, setting headers in client constructor or in operation call time manually. They said they will support this policy in the future. Azure CLI Core also needs an upgrade to provide better interfaces for Track 2 SDK users.

You are welcome to contribute to this document if you have experience of Track 2 SDK.

### References

[1] https://github.com/Azure/azure-sdk-for-python/blob/master/sdk/core/azure-core/CLIENT_LIBRARY_DEVELOPER.md#available-policies

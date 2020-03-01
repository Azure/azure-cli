## Command Guideline

#### Private Endpoint Connection

- The parent resource should expose a single command group called `private-endpoint-connection` with four commands: `approve`, `reject`, `delete`, `show`.
- If `approve` and `reject` are long running operations, please also provide `... private-endpoint-connection wait` command and support `--no-wait` in `approve` and `reject` commands.
- The `... private-endpoint-connection approve` command should look similar to the following, depending on which features are supported by the service.
```
Arguments
    --approval-description          : Comments for the approval.
    --id                            : The ID of the private endpoint connection associated with the Key
                                      Vault(Storage Account). If specified --vault-name and --name/-n, this should be omitted.
    --name -n                       : The name of the private endpoint connection associated with the Key
                                      Vault(Storage Account). Required if --id is not specified.
    --resource-group -g             : Proceed only if Key Vault(Storage Account) belongs to the specified resource group.
    --vault-name(--account-name)    : Name of the Key Vault(Storage Account). Required if --id is not specified.
```
- The `... private-endpoint-connection reject` command should look similar to the following, depending on which features are supported by the service.
```
Arguments
    --rejection-description         : Comments for the rejection.
    --id                            : The ID of the private endpoint connection associated with the Key
                                      Vault(Storage Account). If specified --vault-name and --name/-n, this should be omitted.
    --name -n                       : The name of the private endpoint connection associated with the Key
                                      Vault(Storage Account). Required if --id is not specified.
    --resource-group -g             : Proceed only if Key Vault(Storage Account) belongs to the specified resource group.
    --vault-name(--account-name)    : Name of the Key Vault(Storage Account). Required if --id is not specified.
```
- The `... private-endpoint-connection show/delete` command should look similar to the following, depending on which features are supported by the service.
```
Arguments
    --id                            : The ID of the private endpoint connection associated with the Key
                                      Vault(Storage Account). If specified --vault-name and --name/-n, this should be omitted.
    --name -n                       : The name of the private endpoint connection associated with the Key
                                      Vault(Storage Account). Required if --id is not specified.
    --resource-group -g             : Proceed only if Key Vault(Storage Account) belongs to the specified resource group.
    --vault-name(--account-name)    : Name of the Key Vault(Storage Account). Required if --id is not specified.
```

#### Private Link Resource

- The parent resource should expose a single command group called `private-link-resource` with one commands: `list`.
- The `... private-link-resource list` command should look similar to the following, depending on which features are supported by the service.

```
Arguments
    --vault-name(--account-name) [Required] : Name of the Key Vault(Storage Account).
    --resource-group -g     : Proceed only if Key Vault belongs to the specified resource group.
```
- The output of `... private-link-resource list` should be a array instead of a dictionary.

## Command Authoring

Storage and keyvault modules both are good examples. Feel free to use them as reference.

#### Parameters
We provide a build-in function `parse_proxy_resource_id` to parse private endpoint connection id. It can be used to support the `--id` argument.
```
from azure.cli.core.util import parse_proxy_resource_id
pe_resource_id = "/subscriptions/0000/resourceGroups/clirg/" \
                 "providers/Microsoft.Network/privateEndpoints/clipe/" \
                 "privateLinkServiceConnections/peconnection"
result = parse_proxy_resource_id(pe_resource_id)
namespace.resource_group = result['resource_group']
namespace.endpoint = result['clipe']
namespace.name = result['child_name_1']
```

#### Transform
In order to transform the output of the `list` command, we provide a transform function `gen_dict_to_list_transform`.
```
from azure.cli.core.command.transform import gen_dict_to_list_transform
g.command('list', transform=gen_dict_to_list_transform(key='values'))
```

#### Test
- Integration test is mandatory. It should contain the following steps at least.
    - Create a resource such as storage account or key vault.
    - List all private link resources for the created resource.
    - Create a private endpoint for the resource.
    - Approve the private endpoint connection.
    - Reject the private endpoint connection.
    - Show the private endpoint connection.
    - Delete the private endpoint connection.
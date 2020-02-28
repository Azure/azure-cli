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


## Command Authoring

Storage and keyvault modules both are good examples. Feel free to use them as reference.

#### Parameters


#### Transforms


#### Test
- Integration test is mandatory.
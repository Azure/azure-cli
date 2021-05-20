## Overview
This document provides a common design of the CLI command interface for supporting Managed Identity in Azure CLI. New commands should follow it while existing commands can stay the same before a deprecation plan.

## Command interface

### Enable managed identity during resource creation
Use `--mi-system-assigned` to enable system-assigned identity and `--mi-user-assigned` with space separated resource IDs to add user-assigned identities.

```
# <resource> can be acr, webapp, vm or any other resources that support managed identity
az <resource> create ... --mi-system-assigned --mi-user-assigned <AzureResourceId1> <AzureResourceId2>
```

### Operate managed identity on existing resource
Create the `identity` subgroup under the main resource command group. Support the below operations:

1. Assign identities with `identity assign` command

    Use `--system-assigned` to enable system assigned identity and `--user-assigned` with space separated resource IDs to add user assigned identities.
    ```
    az <resource> identity assign ... --system-assigned --user-assigned <AzureResourceId1> <AzureResourceId2>
    ```
2. Remove identities with `identity remove` command

    Use `--system-assigned` to remove system assigned identity and `--user-assigned` with space separated resource IDs to remove specified user assigned identities.
    ```
    az <resource> identity remove ... --system-assigned --user-assigned <AzureResourceId1> <AzureResourceId2>
    ```
    For the convenience scenario to remove all user assigned identities, `--user-assigned` with no values should remove all user assigned identities with proper warnings.
    ```
    az <resource> identity remove ... --user-assigned
    ```
3. Show identities with `identity show` command

    Use this command to show the managed identity type, tenant IDs and principal IDs of the system assigned identities and all user assigned identities.
    ```
    az <resource> identity show ...
    ```

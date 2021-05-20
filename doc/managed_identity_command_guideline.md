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

    Use `--system-assigned` to enable system assigned identity and `--user-assigned` with space separated recource ids to add user assigned identities.
    ```
    az <resource> identity assign ... --system-assigned --user-assigned <AzureResourceId1> <AzureResourceId2>
    ```
2. Remove identities with `identity remove` command

    Use `--system-assigned` to remove system assigned identity and `--user-assigned` with space separated resource ids to remove user assigned identities.
    ```
    az <resource> identity remove ... --system-assigned --user-assigned <AzureResourceId1> <AzureResourceId2>
    ```
3. Show identities with `identity show` command

    Use this command to show the managed identity type, tenant ids and principal ids of the system assigned identities and all user assigned identities.
    ```
    az <resource> identity show ...
    ```
4. Update identities with `identity update` command

    Use different identity types to do the following (the enum values available for type may vary with different services):
    - Remove all assigned identities
        ```
        az <resource> identity update ... --type none
        ```
    - Remove all user assigned identities if exist and enable system assigned identity if not enabled
        ```
        az <resource> identity update ... --type SystemAssigned
        ```
    - Remove system assigned identities only when both system assigned and user assigned identities exist
        ```
        az <resource> identity update ... --type UserAssigned
        ```
    - Add system assigned identity only when user assigned identities exist
        ```
        az <resource> identity update ... --type "SystemAssigned, UserAssigned"
        ```

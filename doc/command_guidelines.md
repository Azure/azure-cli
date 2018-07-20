# Command Guidelines

This document describes the command guidelines for 'az' and applies to both CLI command modules and extensions.

Guidelines marked (*) only apply to command modules, not extensions.

If in doubt, ask!

## General Patterns

- Be consistent with POSIX tools (support piping, work with grep, awk, jq, etc.)
- Support tab completion for parameter names and values (e.g. resource names)
- All commands, command group and arguments must have descriptions
- You must provide command examples for non-trivial commands
- All commands must support all output types (json, tsv, table)
- Provide custom table outputs for commands that don't provide table output automatically
- Commands must return an object, dictionary or `None` (do not string, Boolean, etc. types)
- Command output must go to `stdout`, everything else to `stderr` (log/status/errors).
- Log to `logger.error()` or `logger.warning()` for user messages; do not use the `print()` function
- Use the appropriate logging level for printing strings. e.g. `logging.info(“Upload of myfile.txt successful”)` NOT `return “Upload successful”`.

## Command Naming and Behavior

- Commands must follow a "[noun] [noun] [verb]" pattern
- Multi-word subgroups should be hyphenated
e.g. `foo-resource` instead of `fooresource`
- All command names should contain a verb
e.g. `account get-connection-string` instead of `account connection-string`
- Avoid hyphenated command names when moving the commands into a subgroup would eliminate the need.
e.g. `database show` and `database get` instead of `show-database` and `get-database`
- If a command subgroup would only have a single command, move it into the parent command group and hyphenate the name. This is common for commands which exist only to pull down cataloging information.
e.g. `database list-sku-definitions` instead of `database sku-definitions list`
- Avoid command subgroups that have no commands. This often happens at the first level of a command branch.
e.g. `keyvault create` instead of `keyvault vault create` (where `keyvault` only has subgroups and adds unnecessary depth to the tree).<details>
  <summary>Click for a full example</summary>
  <p>
  KeyVault has secrets, certificates, etc that exist within a vault. The existing (preferred) CLI structure looks like:	

    ```	
    Group	
        az keyvault: Safeguard and maintain control of keys, secrets, and certificates.	
        
    Subgroups:	
        certificate  : Manage certificates.	
        key          : Manage keys.	
        secret       : Manage secrets.	
        
    Commands:	
        create       : Create a key vault.	
        delete       : Delete a key vault.	
        delete-policy: Delete security policy settings for a Key Vault.	
        list         : List key vaults.	
        list-deleted : Gets information about the deleted vaults in a subscription.	
        purge        : Permanently deletes the specified vault.	
        recover      : Recover a key vault.	
        set-policy   : Update security policy settings for a Key Vault.	
        show         : Show details of a key vault.	
        update       : Update the properties of a key vault.	
    ```	
        
    To create a vault, you simply use `az keyvault create ...`. An alternative would be to place the vault commands into a separate subgroup, like this:	
    ```	
    Group	
        az keyvault: Safeguard and maintain control of keys, secrets, and certificates.	
        
    Subgroups:	
        certificate  : Manage certificates.	
        key          : Manage keys.	
        secret       : Manage secrets.	
        vault        : Manage vaults.	
    ```	
        
    Now, to create a vault, you have to use `az keyvault vault create ...` which is overly verbose adds unnecessary depth to the tree. The preferred style makes the command use more convenient and intuitive.
</p>
</details>

## Standard Command Types

The following are standard names and behavioral descriptions for CRUD commands commonly found within the CLI. These standard command types MUST be followed for consistency with the rest of the CLI.

- `CREATE` - standard command to create a new resource. Usually backed server-side by a PUT request. 'create' commands should be idempotent and should return the resource that was created.
- `UPDATE` - command to selectively update properties of a resource and preserve existing values. May be backed server-side by either a PUT or PATCH request, but the behavior of the command should always be PATCH-like. All `update` commands should be registered using the `generic_update_command` helper to expose the three generic update properties. `update` commands MAY also allow for create-like behavior (PATCH) in cases where a dedicated `create` command is deemed unnecessary. `update` commands should return the updated resource.
- `SET` - command to replace all properties of a resource without preserving existing values, typically backed server-side by a PUT request. This is used when PATCH-like behavior is deemed unnecessary and means that any properties not specifies are reset to their default values. `set` commands are more rare compared to `update` commands. `set` commands should return the updated resource.
- `SHOW` - command to show the properties of a resource, backed server-side by a GET request. All `show` commands should be registered using the `show_command` or `custom_show_command` helpers to ensure `404(Not Found)` is always returning an exit code of 3.
- `LIST` - command to list instances of a resource, backed server-side by a GET request. When there are multiple "list-type" commands within an SDK to list resources at different levels (for example, listing resources in a subscription vice in a resource group) the functionality should be exposed by have a single list command with arguments to control the behavior. For example, if `--resource-group` is provided, the command will call `list_by_resource_group`; otherwise, it will call `list_by_subscription`.
- `DELETE` - command to delete a resource, backed server-side by a DELETE request. Delete commands return nothing on success.

## Non-standard Commands

For commands that don't conform to one of the above-listed standard command patterns, use the following guidance.

- (*) Don't use single word verbs if they could cause confusion with the standard command types. For example, don't use `get` or `new` as these sound functionally the same as `show` and `create` respectively, leading to confusion as to what the expected behavior should be.
- (*) Descriptive, hyphenated command names are often a better option than single verbs.

## Coding Practices

- All code must support Python 2 & 3.
The CLI supports 2.7, 3.4, 3.5 and 3.6
- PRs to Azure/azure-cli and Azure/azure-cli-extensions must pass CI
- Code must pass style checks with pylint and pep8
- (*) All commands should have tests

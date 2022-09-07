# Command Guidelines

This document describes the command guidelines for 'az' and applies to both CLI command modules and extensions.

Guidelines marked (*) only apply to command modules, not extensions.

If in doubt, ask!

[1. General Patterns](#general-patterns)

[2. Command Naming and Behavior](#command-naming-and-behavior)

[3. Argument Naming Conventions](#argument-naming-conventions)

[4. Standard Command Types](#standard-command-types)

[5. Non-standard Commands](#non-standard-commands)

[6. Commands with Complex Types](#commands-with-complex-types)

[7. Network Rule Commands](#network-rule-commands)

[8. Error Handling](#error-handling)

[9. Coding Practices](#coding-practices)

## General Patterns

- Be consistent with POSIX tools (support piping, work with grep, awk, jq, etc.)
- Support tab completion for parameter names and values (e.g. resource names)
- Commands must support all output types (json, tsv, table)
- Provide custom table outputs for commands that don't provide table output automatically
- Commands must return an object, dictionary or `None` (do not string, Boolean, etc. types)
- Command output must go to `stdout`, everything else to `stderr` (log/status/errors).
- Log to `logger.error()` or `logger.warning()` for user messages; do not use the `print()` function
- Use the appropriate logging level for printing strings. e.g. `logging.info(“Upload of myfile.txt successful”)` NOT `return “Upload successful”`.

## Command Naming and Behavior

- Commands must follow a "[noun] [noun] [verb]" pattern
- Multi-word subgroups should be hyphenated (e.g. `foo-resource` instead of `fooresource`)
- All command names should contain a verb (e.g. `account get-connection-string` instead of `account connection-string`)
- For commands which maintain child collections, the follow pairings are acceptable.
  1. `CREATE`/`DELETE` (same as top level resources)
  2. `ADD`/`REMOVE`
- Avoid hyphenated command names when moving the commands into a subgroup would eliminate the need (e.g. `database show` and `database get` instead of `show-database` and `get-database`).
- If a command subgroup would only have a single command, move it into the parent command group and hyphenate the name. This is common for commands which exist only to pull down cataloging information (e.g. `database list-sku-definitions` instead of `database sku-definitions list`). However, if you plan to add commands to this group in the future, then temporarily having a command group with a single command would make more sense. For example, if you only have `database list` but eventually plan to support `database create/update/...` then having a `database` group with a single command would be fine.
- In general, avoid command subgroups that have no commands. This often happens at the first level of a command branch. For example, `keyvault create` instead of `keyvault vault create` (where `keyvault` only has subgroups and adds unnecessary depth to the tree).
<details>
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

## Argument Naming Conventions

- Arguments with specific units:
  1. In general, DO NOT put units in argument names. ALWAYS put the expected units in the help text. Example: `--duration-in-minutes` should simply be `--duration`. This prevents the need to add more arguments later if more units are supported.
  2. Consider allowing a syntax that will let the user specify units. For example, even if the service requires a value in minutes, consider accepting 1h or 60m. It is fine to assume a default (i.e. 60 = 60 minutes).
  3. It is acceptable to use a unit in the argument name when it is used like an enum. For example, `--start-day` is okay when it accepts MON, TUE, etc. `--start-hour` is okay when it indicates an hour of the day.
- ID Arguments:
  1. Arguments that end in `-id` should be GUIDs.
  2. Arguments that expect ARM IDs should omit `-id` but call out that an ARM ID is allowed in the help text. These are often used as part of the "name or ID" convention (i.e: `--storage-account` can often accept a storage account name OR ARM ID).
- Overloading Arguments:
  1. Avoid having multiple arguments that simply represent different ways of getting the same thing. Instead, use a single descriptive name and overload it appropriately. For example, assume a command which can accept a parameter file through a URL or local path.

**AVOID**
```
    --parameters-url   URL to a parameters file.
    --parameters-path  Local path to a parameters fle.
```

**PREFERRED**
```
    --parameters   Local path or URL to a parameters file.`
```

## Standard Command Types

The following are standard names and behavioral descriptions for CRUD commands commonly found within the CLI. These standard command types MUST be followed for consistency with the rest of the CLI.

- `CREATE` - standard command to create a new resource. Usually backed server-side by a PUT request. 'create' commands should be idempotent and should return the resource that was created.
- `UPDATE` - command to selectively update properties of a resource and preserve existing values. May be backed server-side by either a PUT or PATCH request, but the behavior of the command should always be PATCH-like. All `update` commands should be registered using the `generic_update_command` helper to expose the three generic update properties. `update` commands MAY also allow for create-like behavior (PATCH) in cases where a dedicated `create` command is deemed unnecessary. `update` commands should return the updated resource.
- `SET` - command to replace all properties of a resource without preserving existing values, typically backed server-side by a PUT request. This is used when PATCH-like behavior is deemed unnecessary and means that any properties not specifies are reset to their default values. `set` commands are more rare compared to `update` commands. `set` commands should return the updated resource.
- `SHOW` - command to show the properties of a resource, backed server-side by a GET request. All `show` commands should be registered using the `show_command` or `custom_show_command` helpers to ensure `404(Not Found)` is always returning an exit code of 3.
- `LIST` - command to list instances of a resource, backed server-side by a GET request. When there are multiple "list-type" commands within an SDK to list resources at different levels (for example, listing resources in a subscription vice in a resource group) the functionality should be exposed by have a single list command with arguments to control the behavior. For example, if `--resource-group` is provided, the command will call `list_by_resource_group`; otherwise, it will call `list_by_subscription`.
- `DELETE` - command to delete a resource, backed server-side by a DELETE request. Delete commands return nothing on success.
- `WAIT` - command that polls a GET endpoint until a condition is reached. If any command within a command group or subgroup exposes
  the `--no-wait` parameter, this command should be exposed.

## Non-standard Commands

For commands that don't conform to one of the above-listed standard command patterns, use the following guidance.

- (*) Don't use single word verbs if they could cause confusion with the standard command types. For example, don't use `get` or `new` as these sound functionally the same as `show` and `create` respectively, leading to confusion as to what the expected behavior should be.
- (*) Descriptive, hyphenated command names are often a better option than single verbs.

## Commands with Complex Types

Certain endpoints accept complex object that themselves contain other complex objects or collections of complex objects. Since this child resources lack endpoints of their own, it can often be difficult to craft CLI commands to manage such objects. The tendency is to simply accept a JSON blob for these arguments. **THIS PRACTICE IS UNACCEPTABLE.** Existing instances of JSON strings have demonstrably frustrated customers because (1) the required format is inadequately (if at all) conveyed, (2) inputting JSON strings on the command line is tedious and extremely difficult on certain shells, necessitating error-prone escaping and (3) parsing errors are difficult to troubleshoot.

### Single Complex Parameters

The simplest case is when a complex parameter is a single object with simple properties. In this case, the simplest approach is to expose the properties of the complex parameter as individual parameters on the parent resource and then assemble the complex parameter inside a custom command (most common) or validator.

For example, consider the following structure for an object of type Foo:
```
{
    name: str,
    type: str,
    policy: {
        action: enum,
        values: list(str)
    }
}
```

The custom code would look like:
```Python
def create_foo(cmd, client, name, resource_group_name, type, policy_action, policy_values):
    Foo, Policy = cmd.get_models('Foo', 'Policy')
    foo_obj = Foo(
        name=name,
        type=type,
        policy=Policy(
            action=policy_action,
            values=policy_values
        )
    )
    return client.create_or_update(name, resource_group_name, foo_obj)
```

Best practice would be to group the policy arguments together in help using the `arg_group` keyword, like so:
```Python
with self.argument_context('foo') as c:
    c.argument('name', options_list=['--name', '-n'], ...)

with self.argument_context('foo', arg_group='Policy') as c:
    c.argument('policy_action', get_enum_type(Policy), options_list='--action', help='The policy action to apply.')
    c.argument('policy_values', options_list='--values', nargs='+', help='Space-separated list of policy values to match.')
```

### Collection Management with Commands

Often a resource contains collections of child objects. The simplest way to handle these situations is to give the complex collection its own command subgroup. Consider our Foo resource. Let's add a complex collection:
```
{
    name: str,
    ...
    rules: [
        {
            name: str,
            metric: enum,
            operation: enum, 
            value: str
        },
        ...
    ]
}
```

In this case, the most idiomatic and straight-forward solution would be to expose a group of `rule` subcommands. The foo create command would look like:
```Python
def create_foo(cmd, client, resource_group_name, foo_name, policy_action, policy_values):
    Foo, Policy = cmd.get_models('Foo', 'Policy')
    foo_obj = Foo(
        rules=[],  # if service fails, see: Overcoming Service Limitations
        policy=Policy(
            action=policy_action,
            values=policy_values
        )
    )
    return client.create_or_update(foo_name, resource_group_name, foo_obj)
```

The corresponding rule create looks like:
```Python
def create_foo_rule(cmd, client, resource_group_name, foo_name, rule_name, metric, operation, value):
    from azure.cli.commands import upsert_to_collection, get_property
    FooRule = cmd.get_models('FooRule')
    # get the parent object
    foo_obj = client.get(resource_group_name, foo_name)
    new_rule = FooRule(
        name=rule_name,
        metric=metric,
        operation=operation,
        value=value
    )
    # add the new child to the parent collection
    upsert_to_collection(foo_obj, 'rules', new_rule, 'name')
    # update the parent object
    foo_obj = client.create_or_update(name, resource_group_name, foo_obj).result()
    # return the child object
    return get_property(foo_obj.rules, rule_name)
```

The usage pattern of this implementation to create two rules would be:
```
az foo create -g MyRG -n myfoo --action allow --values test prod
az foo rule create -g MyRG --foo-name myfoo -n rule1 --metric name --operations equals --value test
az foo rule create -g MyRG --foo-name myfoo -n rule2 --metric age --operations lessThan --value 100
```

### Collection Management with Actions

An alternative to using subcommands to manage collections is to assemble complex objects using argparse Actions. This is acceptable, but is **NOT RECOMMENDED**, for
the following reasons:
1. The UX is much more complicated and potentially confusing for the customer. See `az monitor action-group create` for an example.
2. The implementation is more complex for the command author/maintainer.
3. There is no mechanism for user-friendly features like tab-completion.

Given that, consider how we could implement the earlier example, this time using actions on the `foo create` command instead of subcommands to manage the collection:
```
{
    name: str,
    ...
    rules: [
        {
            name: str,
            metric: enum,
            operation: enum, 
            value: str
        },
        ...
    ]
}
```

The argument registration would look like:
```Python
with self.argument_context('foo create') as c:
    ...
    c.argument('rules', options_list=['--rule', '-r'], action=FooRuleAddAction, nargs='+')
```

The rule action will need some way to parse out several arguments from a single string. There are two ways of doing this. One would be to make the syntax of the action
use positional arguments. This works well when there is an obvious positional relationship between the parameters. The other would be to accept key=value pairs. This will create a much more verbose command string, but may be appropriate when there's no positional relationship between the arguments. Here is an example of each.

#### Positional Arguments
```Python
# pylint: disable=protected-access
class FooRuleAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            FooRule = namespace._cmd.get_models('FooRule')
            name, metric, operation, value = values.split()
            return FooRule(
                name=name,
                metric=metric,
                operation=operation,
                value=value
            )
        except ValueError:
            raise CLIError('usage error: {} NAME METRIC OPERATION VALUE'.format(option_string))
```

The usage pattern of this implementation to create two rules would be:
```
az foo create -g MyRG -n myfoo --action allow --values test prod --rule rule1 name equals test --rule rule2 age lessThan 100
```

#### Key=Value Arguments
```Python
# pylint: disable=protected-access
class FooRuleAddAction(argparse._AppendAction):

    def __call__(self, parser, namespace, values, option_string=None):
        FooRule = namespace._cmd.get_models('FooRule')
        kwargs = {}
        for item in values.split():
            try:
                key, value = item.split('=', 1)
                kwargs[key] = value
            except ValueError:
                raise CLIError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        return FooRule(**kwargs)
```

The usage pattern of this implementation to create two rules would be:
```
az foo create -g MyRG -n myfoo --action allow --values test prod --rule name=rule1 metric=name operation=equals value=test --rule name=rule2 metric=age operation=lessThan value=100
```

### Overcoming Service Limitations

There are times when service limitations can interfere with the recommended approach of handling complex collections using subcommand groups. In our example, the service might fail if the `foo_create` command supplied an empty rule collection. This is something we can work around in the CLI using the `--defer` caching mechanism. The following changes should be made:

In `commands.py`, add the `supports_local_cache=True` kwarg to the command registration:
```Python
with self.command_group('foo', foo_sdk) as g:
    g.custom_command('create', 'create_foo', supports_local_cache=True)
    ...

with self.command_group('foo rule', foo_sdk) as g:
    g.custom_command('create', 'create_foo_rule', supports_local_cache=True)
    ... 
```

Update the custom commands to use the `cached_get` and `cached_put` helpers:
```Python
def create_foo(cmd, client, resource_group_name, foo_name, policy_action, policy_values):
    from azure.cli.core.commands import cached_get, cached_put
    Foo, Policy = cmd.get_models('Foo', 'Policy')
    foo_obj = Foo(
        rules=[],
        policy=Policy(
            action=policy_action,
            values=policy_values
        )
    )
    # cache the payload if --defer used or send to Azure
    return cached_put(cmd, client.create_or_update, resource_group_name, foo_name, foo_obj)
```

The corresponding rule create looks like:
```Python
def create_foo_rule(cmd, client, resource_group_name, foo_name, rule_name, metric, operation, value):
    from azure.cli.core.commands import cached_put, upsert_to_colleciton, get_property
    FooRule = cmd.get_models('FooRule')
    # retrieves the object from the cache. On a miss, retrieves from Azure
    foo_obj = cached_get(cmd, client.get, resource_group_name, foo_name)
    new_rule = FooRule(
        name=rule_name,
        metric=metric,
        operation=operation,
        value=value
    )
    # add the new child to the parent collection
    upsert_to_collection(foo_obj, 'rules', new_rule, 'name')
    # re-cache the parent with --defer or send to Azure
    foo_obj = cached_put(cmd, client.create_or_update, name, resource_group_name, foo_obj).result()
    # return the child object
    return get_property(foo_obj.rules, rule_name)
```

The usage pattern of this implementation to create two rules would be:
```
az foo create -g MyRG -n myfoo --action allow --values test prod --defer
az foo rule create -g MyRG --foo-name myfoo -n rule1 --metric name --operations equals --value test --defer
az foo rule create -g MyRG --foo-name myfoo -n rule2 --metric age --operations lessThan --value 100
```

## Network Rule Commands

Several services support the concept of network rules. To drive consistency across services, command authors for these services should use the following as guidance. Questions/exceptions should be directed to the CLI team.

- The parent resource should expose a single command group called `network-rule` with three commands: `add`, `remove`, `list`.
- Internally, network rules are typically modeled as a rule set. This implementation is largely hidden from the user since these services only allow a single rule set. If there are properties that can be set on the rule set generally (the only known one as of this writing is `default_action`, these properties should be exposed on the `create/update` commands of the parent object, under an argument group called `Network Rule`.
- The following examples assume that individual rules do not have names. If your rules do have names, consult the CLI team for guidance.
- The `... network-rule add` command should look similar to the following, depending on which features are supported by the service.
```
Arguments
    --name -n [Required]      : The name of the [PARENT RESOURCE].
    --resource-group -g       : Name of resource group. You can configure the default group using `az
                                configure --defaults group=<name>`.

IP Address Rule Arguments
    --ip-address              : IPv4 address or CIDR range.
    --action                  : Action of the IP rule. Default: Allow

Virtual Network Rule Arguments
    --subnet                  : Name or ID of subnet. If name is supplied, `--vnet-name` must be
                                supplied.
    --vnet-name               : Name of a virtual network.
    --ignore-missing-endpoint : Create the rule before the virtual network has vnet service
                                endpoint enabled.
```

- The `... network-rule remove` command should look similar to the following, depending on which features are supported by the service.
```
Arguments
    --name -n [Required]         : The name of the [PARENT RESOURCE].
    --resource-group -g          : Name of resource group. You can configure the default group using
                                   `az configure --defaults group=<name>`.

IP Address Rule Arguments
    --ip-address                 : IPv4 address or CIDR range.

Virtual Network Rule Arguments
    --subnet                     : Name or ID of subnet. If name is supplied, `--vnet-name` must be
                                   supplied.
    --vnet-name                  : Name of a virtual network.
```

## Error Handling

Follow the [Error Handling Guidelines](https://github.com/Azure/azure-cli/blob/dev/doc/error_handling_guidelines.md) to select a proper error type and write an actionable error message.

## Coding Practices

- All code must support Python 3.7 ~ 3.10
- PRs to Azure/azure-cli and Azure/azure-cli-extensions must pass CI
- Code must pass style checks with pylint and pep8
- (*) All commands should have tests

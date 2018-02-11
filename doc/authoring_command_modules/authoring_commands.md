The document provides instructions and guidelines on how to author individual commands.

**AUTHORING COMMANDS**

[1. Write the Command Loader](#write-the-command-loader)

[2. Write a Command](#write-a-command)

[3. Register Commands](#register-commands)

[4. Write Help Entry](#write-help-entry)

[5. Customize Arguments](#customize-arguments)

**ADDITIONAL TOPICS**

[6. Command Naming and Behavior Guidance](#command-naming-and-behavior-guidance)

[7. Keyword Argument (kwarg) Reference](#keyword-argument-reference)

[8. Supporting the IDs Parameter](#supporting-the-ids-parameter)

[9. Generic Update Commands](#generic-update-commands)

[10. Custom Table Formats](#custom-table-formats)

[11. Tab Completion (bash only)](#tab-completion)

[12. Validators](#validators)

[13. Registering Flag Arguments](#registering-flags)

[14. Registering Enum Arguments](#registering-enums)

Authoring Commands
=============================

## Write the Command Loader

As of version 2.0.24, Azure CLI is based on the Knack framework (https://github.com/Microsoft/knack), which uses the `CLICommandsLoader` class as the mechanism for loading a module. In Azure CLI 2.0, you will create your own loader which will inherit from the `AzCommandsLoader` class.  The basic structure is:

```Python
class MyCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.sdk.util import CliCommandType
        mymod_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.mymod.custom#{}')
        super(MyCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                               min_profile='2017-03-10-profile',
                                               custom_command_type=mymod_custom)

    def load_command_table(self, args):
        super(MyCommandsLoader, self).load_command_table(args)
        # TODO: Register command groups and commands here
        return self.command_table

    def load_arguments(self, command):
        super(MyCommandsLoader, self).load_arguments(command)
        # TODO: Register argument contexts and arguments here

COMMAND_LOADER_CLS = MyCommandsLoader
```

## Write a Command

Write your command as a simple function, specifying your arguments as the parameter names.

***Parameter Naming Guidance***

When choosing names, it is recommended that you look at similiar commands and follow those naming conventions to take advantage of any aliasing that may already be in place. For example, you should choose `resource_group_name` over `rg`, `resource_group` or some other shorthand, because this parameter is globally aliased and you will inherit the `-g` short option and the completer.

Avoid using a parameter name called `name` as this is a very common alias in the CLI and will often create aliasing conflicts.

If you specify a default value in your function signature, this will flag the argument as optional and will automatically display the default value in the help text for the command. Any parameters that do not have a default value are required and will automatically appear in help with the [Required] label. The required and default behaviors for arguments can be overridden (see Argument Customization below) but this is not generally needed.

***Special Arguments***

There are two arguments you may include in your custom command that are reserved by the infrastructure and have special meaning.

`cmd`: If used, this should be the first argument in your custom command, and allows you to access the command instance within your custom command. This will allow you to access the CLI context and numerous helper methods to make writing your command simpler, particularly when working with a multi-API style module.

`client`: If your command has registered the `client_factory` keyword argument, that factory will be passed into this variable. It can appear anywhere in your command signature.

## Register Commands

Before your command can be used in the CLI, it must be registered. Within the `load_command_table` method of your command loader, you will have something like:

```Python
# (1) Registering a command type for reuse among groups
mymod_sdk = CliCommandType(
    operations_tmpl='azure.mgmt.mymod.operations.myoperations#MyOperations.{}',
    client_factory=cf_mymod
)

# (2) Registering a command group
with self.command_group('mymod', mymod_sdk) as g:
    # (3) Registering different types of commands
    g.command('command1', 'do_something_1')
    g.custom_command('command2', 'do_something_2')
    g.generic_update('update', custom_function_name='my_custom_update')
    g.generic_wait('wait')
```

At this point, you should be able to access your command using `az [name]` and access the built-in help with `az [name] -h/--help`. Your command will automatically be 'wired up' with the global parameters.  See below for amplifying information.

**(1) CliCommandType**

CliCommandType is a way to group and reuse and keyword arguments supported by commands. Earlier, in the `__init__` method of the `MyCommandsLoader` class, we created a `mymod_custom` variable and assigned it to the `custom_command_type` keyword argument. This will be used any time you use the `custom_command` method within a command group. It is registered with the loader since most modules typically put all of their custom methods in a single file.

**(2) Command Group Helper**

```Python
command_group(self, group_name, command_type=None, **kwargs)
```
- `group_name`: the group name ('network', 'storage account', etc.)
- `command_type`: a `CliCommandType` object that will be used for all calls to `command` within the group.
- `kwargs`: any supported kwarg that will be used as the basis for all command calls. Commonly used kwargs include: `custom_command_type` (if custom commands are split amongst many files) and `client_factory` (if custom commands use the `client` argument).


**(3) Command Registration Helpers**

***command***
```Python
command(self, name, method_name=None, command_type=None, **kwargs)
```

- `name`: The name of the command within the command group
- `method_name`: The name of the SDK or custom method, relative to the path specified in `operations_tmpl`.
- `command_type`: A `CliCommandType` object to apply to this command (optional).
- `kwargs`: any supported kwarg. Commonly used kwargs include `validator`, `table_transformer`, `confirmation`, `no_wait_param` and  `transform`.

Any kwargs that are not specified will be pulled from the `command_type` kwarg, if present.

***custom_command***

The signature for `custom_command` is exactly the same as `command`. The only difference is that, whereas `command` uses `command_type` as the fallback for missings kwargs, `custom_command` relies on `custom_command_type`.

***generic_update_command***

See the section on "Suppporting Generic Update"

***generic_wait_command***

The generic wait command provides a templated solution for polling Azure resources until specific conditions are met.

```Python
generic_wait_command(self, name, getter_name='get', getter_type=None, **kwargs)
```

- `name`: The name of the command within the command group. Commonly called 'wait'.
- `getter_name`: The name of the method for the object getter, relative to the path specified in `operations_tmpl`.
- `getter_type`: A `CliCommandType` object to apply to this command (optional).
- `kwargs`: any supported kwarg.

Since most wait commands rely on a simple GET call from the SDK, most of these entries simply look like:
```Python
   g.generic_wait_command('wait')
```

## Write Help Entry

See the following for guidance on writing a help entry: https://github.com/Azure/azure-cli/blob/master/doc/authoring_help.md

## Customize Arguments

While the CLI will attempt to figure out certain key properties of your command and its arguments, it is often necessary to override, add to, or customize this metadata. To modify/enhance your command arguments, create an argument context. For the standard modules, these entries are contained within a file called `_params.py`. Within the `load_arguments` method of your command loader, you will have something like:

```Python
    # (1) Create an argument context
    with self.argument_context('mymod') as c:
        # (2) Register different kinds of arguments
        c.argument('name', options_list=['--name', '-n'], help='Name of the thing.', completer=get_resource_name_completion_list('Microsoft.Example/mything'))
        c.extra('extra_thing', options_list=['--extra'], help='An extra thing.')
        c.ignore('ignore_this', 'ignore_that')
        c.argument('some_flag', arg_type=get_three_state_flag())
        c.argument('some_enum', arg_type=get_enum_type(MyEnum, default='foo'))
```

For more information:

**(1) Create an argument context**

```Python
argument_context(self, scope, **kwargs):
```

- `scope` - This string is the level at which your customizations are applied. For example, consider the case where you have commands `az mypackage command1` and `az mypackage command2`, which both have a parameter `my_param`.

```Python
with self.argument_context('my_param', ...) as c:  # applies to BOTH command1 and command2
```
But
```Python
with self.argument_context('mypackage command1', ...) as c:  # applies to command1 but not command2
```
Like CSS rules, modifications are applied in order from generic to specific.
```Python
with self.argument_context('my_param', ...) as c:  # applies to both command1 and command2
  c.argument('my_param', ...)
with self.argument_context('mypackage command1', ...) as c:  # applies to command1 but not command2
  c.argument('my_param', ...)
```
- `kwargs` - Any supported kwarg which will be applied to calls within the context block.

**(2) Register different kinds of arguments**

***argument***
```Python
argument(self, dest, arg_type=None, **kwargs)
```
- `dest` -  The name of the parameter that you are targeting.
- `arg_type` - An instance of the `azure.cli.core.commands.CliArgumentType` class. This essentially serves as a named, reusable packaging of the `kwargs` that modify your command's argument. It is useful when you want to reuse an argument definition, but is generally not required. It is most commonly used for name type parameters, or for enums and flags.
- `kwargs` - Most likely, you will simply specify keyword arguments that will accomplish what you need.  Any `kwargs` specified will override or extended the definition in `arg_type`, if provided.

***ignore***
```Python
ignore(self, *args)
```
- `args` - one or more parameter names (dest values) that should be ignored. Useful to suppress arguments that appear due to reflection on an SDK, but are unwanted in the command signature.

***extra***
```Python
extra(self, dest, arg_type=None, **kwargs)
```
Arguments are the same as `argument`, however this will create a new parameter whereas `argument` will not. This is useful when a reflected SDK method is missing a parameter that you need to expose in your command.

***expand***
```Python
expand(self, dest, model_type, group_name=None, patches=None):
```

Often reflected SDK methods have complex parameters that are difficult to expose directly. The `expand` method offers one way to expose these methods without resorting to a custom command approach.

- `dest` -  The name of the parameter that will be expanded.
- `model_type` - The model type which will be expanded and collapsed back into the `dest` value.
- `group_name` - The argument group to which the expand parameters will be assigned. (See arg_group kwarg)
- `patches` - A list of patches to apply to the expanded parameters.

Additional Topics
=============================

## Command Naming and Behavior Guidance

**General Guidelines and Conventions**

1. multi-word subgroups should be hyphenated (ex: `foo-resource` instead of `fooresource`)
2. all command names should contain a verb (ex: `storage account get-connection-string` instead of `storage account connection-string`)
3. avoid hyphenated command names when moving the commands into a subgroup would eliminate the need. (ex: instead of `show-database` and `list-database` use `database show` and `database get`.
4. If a command subgroup would only have a single command, move it into the parent command group and hyphenate the name. This is common for commands which exist only to pull down cataloging information. (ex: instead of `database sku-definitions list` use `database list-sku-definitions`).
5. Avoid command subgroups that have no commands. This often happens at the first level of a command branch. For example, KeyVault has secrets, certificates, etc that exist within a vault. The existing (preferred) CLI structure looks like:
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

**Standard Command Types**

The following are standard names and behavioral descriptions for CRUD commands commonly found within the CLI.

1. CREATE - standard command to create a new resource. Usually backed server-side by a PUT request. 'create' commands should be idempotent and should return the resource that was created.

2. UPDATE - command to selectively update properties of a resource and preserve existing values. May be backed server-side by either a PUT or PATCH request, but the behavior of the command should *always* be PATCH-like. All `update` commands should be registerd using the `generic_update_command` helper to expose the three generic update properties. `update` commands MAY also allow for create-like behavior (PUTCH) in cases where a dedicated `create` command is deemed unnecessary. `update` commands should return the updated resource.

3. SET - command to replace all properties of a resource without preserving existing values, typically backed server-side by a PUT request. This is used when PATCH-like behavior is deemed unnecessary and means that any properties not specifies are reset to their default values. `set` commands are more rare compared to `update` commands. `set` commands should return the updated resource.

4. SHOW - command to show the properties of a resource, backed server-side by a GET request.

5. LIST - command to list instances of a resource, backed server-side by a GET request. When there are multiple "list-type" commands within an SDK to list resources at different levels (for example, listing resources in a subscription vice in a resource group) the functionality should be exposed by have a single list command with arguments to control the behavior. For example, if `--resource-group` is provided, the command will call `list_by_resource_group`; otherwise, it will call `list_by_subscription`.

6. DELETE - command to delete a resource, backed server-side by a DELETE request. Delete commands return nothing on success.

**Non-standard Commands**

For commands that don't conform to one of the above-listed standard command patterns, use the following guidance:

1. Don't use single word verbs if they could cause confusion with the standard command types. For example, don't use `get` or `new` as these sound functionally the same as `show` and `create` respectively, leading to confusion as to what the expected behavior should be.
2. Descriptive, hyphenated command names are often a better option than single verbs (ex: `vm assign-identity`, `vm perform-maintenance`).
3. If in doubt, ask!

## Keyword Argument Reference

**Overview of Keyword Arguments in Azure CLI 2.0**

When writing commands for Azure CLI 2.0, it is important to understand how keyword arguments (kwargs) are applied. Refer to the following diagram.

![](/doc/assets/annotated-kwarg-structure.gif)

From the diagram you can see that any kwargs supplied when creating the `AzCommandsLoader` object are passed to and used as the baseline for any command groups or argument contexts that are later created. Any kwargs specified in the `command_group` calls serve as the baseline for any `command` or `custom_command` calls, and any kwargs passed to `argument_context` serve as the baseline for any calls to `argument`.

While kwargs are inherited from higher levels on the diagram, they can be overriden at a lower level. For example, if `custom_command_type=foo` is used as a module-level kwarg in the `AzCommandLoader.__init__` method and `custom_command_type=bar` is passed for a call to `command_group`, then `bar` will be used for all calls to `custom_command` within that command group.

Addtionally, you can see that kwargs registered on a command group *do not* carry over to argument contexts, so you must apply the kwargs in both places if necessary.

****Commands Loader****

_Special Kwargs_

The following special kwargs are only interpretted by the command loader:
- `min_profile` - Minimum profile which the module supports. If an older profile is used, the module will not be loaded.
- `max_profile` - Maximum profile which the module supports. If a newer profile is used, the module will not be loaded.

****Command Group****

_Special Kwargs_

The following special kwargs are supported by command group and its helper methods:
- `table_transformer` - See section on [Custom Table Formats](#custom-table-formats)
- `validator` - See section on [Validators](#validators)
- `confirmation` - During interactive use, will prompt the user to confirm their choice to proceed. Supply a value of True to use the default prompt, or supply a string to use a custom prompt message. If the command is invoked in non-interactive scenarios and the --yes/-y parameter is not supplied, the command will fail.
- `transform` - Accepts a callable that takes a command result, which can be manipulated as desired. The transformed result is then returned. In general, output formats should closely mirror those returned by the service, and so this should be infrequently used. The modifies the output *regardless of the output format type*.
- `deprecate_info` - Accepts a string which will be displayed whenever the command is invoked. Used to display deprecation warnings.
- `formatter_class` - Advanced. Accepts a custom class that derives from `argparse.HelpFormatter` to modify the help document generation.
- `argument_loader` - Advanced. Accepts a callable that takes no parameters which will be used in place of the default argument loader.
- `description_loader` - Advanced. Accepts a callable that takes no parameters which will be used in place of the default description loader.

_General Kwargs_

The following kwargs may be inherited from the command loader:
- `min_api` - Minimum API version for which the command will appear.
- `max_api` - Maximimum API version for which the command will appear.
- `resource_type` - An `azure.cli.core.profiles.ResourceType` enum value that is used for multi-API packages.
- `operation_group` - Only used by the `azure-cli-vm` module to specify which resource API to target.
- `command_group` - A `CliCommandType` object that contains a bundle of kwargs that will be used by the `command` method if not otherwise provided.
- `custom_command_group` - A `CliCommandType` object that contains a bundle of kwargs that will be used by the `custom_command` method if not otherwise provided.

****Argument Context****

_Special Kwargs_

The follow special kwargs are supported by argument context and its helper methods:
- `options_list` - By default, your argument will be exposed as an option in hyphenated form (ex: `my_param` becomes `--my-param`). If you would like to change the option string without changing the parameter name, and/or add a short option, specify the `options_list` kwarg. This is a list of string values. If there will only be one value, you can just specify the value (Ex: `options_list=['--myparam', '-m']` or `options_list='--myparam'`)
- `validator` - See section on [Validators](#validators)
- `completer` - See section on [Tab Completion](#tab-completion)
- `id_part` - See section on [Supporting the IDs Parameter](#supporting-the-ids-parameter).

Additionally, the following `kwargs`, supported by argparse, are supported as well:
- `nargs` - See https://docs.python.org/3/library/argparse.html#nargs
- `action` - See https://docs.python.org/3/library/argparse.html#action
- `const` - See https://docs.python.org/3/library/argparse.html#const
- `default` - See https://docs.python.org/3/library/argparse.html#default. Note that the default value is inferred from the parameter's default value in the function signature. If specified, this will override that value.
- `type` - See https://docs.python.org/3/library/argparse.html#type
- `choices` - See https://docs.python.org/3/library/argparse.html#choices. If specified this will also serve as a value completer for people using tab completion. However, it is not recommended that you use this because the choice lists will be case sensitive. Instead see "Registering Enums".
- `required` - See https://docs.python.org/3/library/argparse.html#required. Note that this value is inferred from the function signature depending on whether or not the parameter has a default value. If specified, this will override that value.
- `help` - See https://docs.python.org/3/library/argparse.html#help. Generally you should avoid adding help text in this way, instead opting to create a help file as described above.
- `metavar` - See https://docs.python.org/3/library/argparse.html#metavar

_General Kwargs_

The following kwargs may be inherited from the command loader:
- `min_api` - Minimum API version for which the argument will appear. Otherwise the argument will be ignored.
- `max_api` - Maximimum API version for which the argument will appear. Otherwise the argument will be ignored.
- `resource_type` - An `azure.cli.core.profiles.ResourceType` enum value that is used for multi-API packages.
- `operation_group` - Only used by the `azure-cli-vm` module to specify which resource API to target.

## Supporting the IDs Parameter

Most ARM resources can be identified by an ID. In many cases, for example `show` and `delete` commands, it may be more useful to copy and paste an ID to identify the target resource instead of having to specify the names of the resource group, the resource, and the parent resource (if any).

Azure CLI 2.0 supports exposing an `--ids` parameter that will parse a resource ID into its constituent named parts so that this parsing need not be done as part of a client script. Additionally `--ids` will accept a _list_ of space-separated IDs, allowing the client to loop the command over each ID.

Enabling this functionality only requires the command author specify the appropriate values for `id_part` in their calls to `AzArgumentContext.argument`.

Consider the following simplified example for NIC IP config.

```Python
def show_nic_ip_config(resource_group_name, nic_name, ip_config_name):
    # retrieve and return the IP config

# inside load_command_table(...)
with self.command_group('network nic ip-config', network_nic_sdk) as g:
   g.custom_command('show', 'show_nic_ip_config')

# inside load_arguments(...)
with self.argument_context('network nic ip-config') as c:
  c.argument('nic_name', help='The NIC name.')
  c.argument('ip_config_name', options_list=['--name', '-n'], help='The IP config name.')
```
The help output for this command would be:
```
 Arguments
    --name -n          : The IP config name.
    --nic-name         : The NIC name.
    --resource-group -g: Name of resource group.
```

Now let's specify values for the `id_part` kwarg in the calls to `argument`:
```Python
def show_nic_ip_config(resource_group_name, nic_name, ip_config_name):
    # retrieve and return the IP config

# inside load_command_table(...)
with self.command_group('network nic ip-config', network_nic_sdk) as g:
   g.custom_command('show', 'show_nic_ip_config')

# inside load_arguments(...)
with self.argument_context('network nic ip-config') as c:
  c.argument('nic_name', help='The NIC name.', id_part='name')
  c.argument('ip_config_name', id_part='child_name_1', options_list=['--name', '-n'], help='The IP config name.')
```
The help output becomes:
```
Arguments

Resource Id Arguments
    --ids              : One or more resource IDs. If provided, no other 'Resource Id' arguments
                         should be specified.
    --name -n          : The IP config name.
    --nic-name         : The NIC name.
    --resource-group -g: Name of resource group.
```
Now the user may identify the target IP config by specifying either the resource group, NIC and IP config names or by simply pasting in the ID for the IP config itself.

This feature is powered by the `parse_resource_id` helper method within the `msrestazure` package, which parses a resource ID into a dictionary. Specifying `id_part` maps the parsed value for a given key in that dictionary into your argument.

For example, consider the following ID of a subnet lock:
```
subscription/0000-0000-0000-0000/resourceGroups/myresourcegroup/Microsoft.Network/virtualNetworks/myvnet/subnets/mysubnet /providers/Microsoft.Authorization/locks/mylock
```

When run through `parse_resource_id`, the following dictionary results:
```Python
{
    "subscription": "0000-0000-0000-0000",
    "resource_group": "myresourcegroup",
    "namespace": "Microsoft.Network",
    "resource_type": "virtualNetworks",
    "name": "myvnet",
    "child_type_1": "subnets",
    "child_name_1": "mysubnet",
    "child_namespace_2": "Microsoft.Authorization",
    "child_type_2": "locks",
    "child_name_2": "mylock"
}
```

Any of these keys could be supplied as a value for `id_part`, thought typically you would only use `name`, `child_name_1`, `child_name_2`, etc.

A couple things to note:
- Currently, `--ids` is not exposed for any command that is called 'create', even if it is configured properly.

## Generic Update Commands

The update commands within the CLI expose a set of generic update arguments: `--add`, `--remove` and `--set`. This allows the user to manipulate objects in a consistent way that may not have long option flags supported by the command. The method which exposes these arguments is `AzCommandGroup.generic_update_command` in the `azure.cli.core.commands` package. The signature of this method is:

```Python
generic_update_command(self, name,
                       getter_name='get', getter_type=None,
                       setter_name='create_or_update', setter_type=None, setter_arg_name='parameters',
                       child_collection_prop_name=None, child_collection_key='name', child_arg_name='item_name',
                       custom_func_name=None, custom_func_type=None, **kwargs)
```

Since most generic update commands can be reflected from the SDK, the simplest form this command can take is:
```Python
with self.command_group('test', test_sdk) as g:
  g.generic_update_command('update')
```

- `name` - The name of the command. Most commonly 'update'.
- `getter_name` - The name of the method which will be used to retrieve the object instance. If the method is named `get` (which is the case for most SDKs), this can be omitted.
- `getter_type` - A `CliCommandType` object which will be used to locate the getter. Only needed if the getter is a custom command (uncommon).
- `setter_name` - The name of the method which will be used to update the object instance using a PUT method. If the method is named `create_or_update` (which is the case for most SDKs), this can be omitted.
- `setter_type` - A `CliCommandType` object which will be used to locate the setter. Only needed if the setter is a custom command (uncommon).
- `setter_arg_name` - The name of the argument in the setter which corresponds to the object being updated. If the name if `parameters` (which is the case for most SDKs), this can be omitted.
- `custom_func_name` (optional) - The name of a method which accepts the object being updated (must be named `instance`), mutates, and returns that object. This is commonly used to add convenience options to the command by listing them in the method signature, similar to a purely custom method. The difference is that a custom command function returns the command result while a generic update custom function returns only the object being updated. A simple custom function might look like:

  ```Python
  def my_custom_function(instance, item_name, custom_arg=None):
    if custom_arg:
        instance.property = custom_arg
    return instance
  ```
  In this case the `custom_func_name` would be `my_custom_function`.
- `custom_func_type` - A `CliCommandType` object which will be used to locate the custom function. If omitted, the CLI will look for and attempt to use the `custom_command_type` kwarg.
- `kwargs` - Any valid command kwarg.

**Working With Child Collections and Properties (Advanced)**

Sometimes you will want to write commands that operate on child resources and it may be that these child resources don't have dedicated getters and setters. In these cases, you must rely on the getter and setter of the parent resource. For these cases, `generic_update_command` has three additional parameters:
  - `child_collection_prop_name` - the name of the child collection property. For example, if object `my_parent` has a child collection called `my_children` that you would access using `my_parent.my_children` then the name you would use is 'my_children'.
  - `child_collection_key_name` - Most child collections in Azure are lists of objects (as opposed to dictionaries) which will have a property in them that serves as the key. This is the name of that key property. By default it is 'name'. In the above example, if an entry in the `my_children` collection has a key property called `my_identifier` then the value you would supply is 'my_identifier'.
  - `child_arg_name` - If you want to refer the child object key (the property identified by `child_collection_key_name`) inside a custom function, you should specify the argument name you use in your custom function. By default, this is called `item_name`. In the above example, where our child object had a key called `my_identifier`, you could refer to this property within your custom function through the `item_name` property, or specify something different.

**Logic Flow**

A simplified understanding of the flow of the generic update is as follows:

```Python
instance = getter(...)  # retrieve the object
if custom_function:
    instance = custom_function(...) # apply custom logic
instance = _process_generic_updates(...) # apply generic updates, which will overwrite custom logic in the event of a conflict
return setter(instance)  # update the instance and return the result
```

## Custom Table Formats

By default, when the `-o/--output table` option is supplied, the CLI will display the top level fields of the object structure as the columns of the table. The user can always specify a `--query` to control table and TSV formats, but the CLI also allows the command author to specify a different default table format. Two options exist:

**Supply a Callable**

Supply a callable that accepts the result as input and returns a list of OrderedDicts:

```Python
def transform_foo(result):
    result = OrderedDict([('name', result['name']),
                          ('resourceGroup', result['resourceGroup']),
                          ('location', result['location'])])
    return result
```

**Supply a JMESPath String**

A string containing Python dictionary-syntax '{Key:JMESPath path to property, ...}'

Example:
```Python
table_transformer='{Name:name, ResourceGroup:resourceGroup, Location:location, ProvisioningState:provisioningState, PowerState:instanceView.statuses[1].displayStatus}'
```

## Tab Completion

Tab completion is enabled by default (in bash or `az interactive`) for command names, argument names and argument choice lists. To enable tab completion for dynamic properties (for example, resource names) you can supply a callable which returns a list of options:

**get_resource_name_completion_list(resource_type)**

Since many completers simply return a list of resource names, you can use the `get_resource_name_completion_list` method from `azure.cli.core.commands.parameters` which accepts the type of resource you wish to get completions for.

Example:
```Python
completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines')
```

The behavior of the completer will depend on what the user has entered prior to hitting [TAB][TAB].  For example:
`az vm show -n [TAB][TAB]`
This will show VM names within the entire subscription.
`az vm show -g myrg -n [TAB][TAB]`
This will show VM names only within the provided resource group.

**Custom Completer**

```Python
from azure.cli.core.decorators import Completer

@Completer
def get_foo_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    # TODO: Your custom logic here
    result = ...
    return [r.name for r in result]
```

The method signature must be as shown and it must return a list of names. You also must use the `@Completer` decorator. You can make additional REST calls within the completer and may examine the partially processed namespace via `namespace` to filter the list based on already supplied args (as in the above case with VM).

## Validators

Validators are custom pieces of code that allow you to perform any custom logic or validation on the entire namespace prior to command execution. Their structure is as follows:

```Python
def validate_my_arg(namespace):
   if namespace.foo:
      # TODO: Your custom logic here
      ...
```

If you need access to the `cli_ctx` within your validator (for instance, to make additional REST calls) the following signature can be used:

```Python
def validate_my_arg(cmd, namespace):
   if namespace.foo:
      # TODO: Your custom logic here
      client=my_client_class(cmd.cli_ctx)
      ...
```

Validators are executed after argument parsing, and thus after the native argparse-supported `type` and `action` have been applied. A CLIError raised during a validator execution will be treated as a validation error, which will result in the display of the command usage string, as opposed to the same error raised within a custom command, which will just print the error and no validation string.

***Command Validators***
The `validator` keyword applies to commands and arguments. A command can have, at most, one validator. If supplied, then *only* this validator will be executed. Any argument-level validators will be ignored. The reason to use a command validator is if the validation sequence is important.  However, the command validator can and very often is composed to individual argument level validators. You simply define the sequence in which they execute.

***Argument Validators***
An argument can be assigned, at most, one validator. However, since a command can have many arguments, this means that a command can have many argument validators. Furthermore, since an argument context may apply to many commands, this means that this argument validator can be reused across many commands. At execution time, argument validators are executed *in random order*, so you should ensure you do not have dependencies between validators. If you do, the a command validator is the appropriate route to take. It is fine to have an argument validator involve several parameters as long as they are interdependent (for example, a validator involving a vnet name and subnet name).

## Registering Flags

The recommended way to register boolean properties in the CLI is using the `get_three_state_flag` arg_type.

```Python
with self.argument_context('mymod') as c:
  c.argument('bool_prop_enabled', arg_type=get_three_state_flag())
```

This will allow the user to specify the option as a flag or as a true/false parameter and allows for maximum convenience and consistency between create and update commands.  With the above registration, the following inputs would be accepted:

```
az mymod --bool-prop-enabled       # bool_prop_enabled = TRUE
az mymod --bool-prop-enabled true  # bool_prop_enabled = TRUE
az mymod --bool-prop-enabled false # bool_prop_enabled = FALSE

```

For flags that are switches on the command itself and not persisted as properties of a resource, the flag should be registered as follows:

```Python
with self.argument_context('mymod') as c:
  c.argument('command_switch', action='store_true')
```

In this case, it will only accept the flag form. Do not use this for boolean properties.

## Registering Enums

The recommended way to register enums (either reflected from an SDK or custom choice lists) is to use the `get_enum_type` arg_type.


```Python
from azure.mgmt.mymod.models import MyModelEnum

with self.argument_context('mymod') as c:
  c.argument('my_enum', arg_type=get_enum_type(MyModelEnum))
  c.argument('my_enum2', arg_type=get_enum_type(['choice1', 'choice2']))
```

Above are two examples of how this can be used. In the first instance, an Enum model is reflected from the SDK. In the second instance, a custom choice list is provided. This is preferable to using the native `argparse.choices` kwarg because the choice lists generated by `get_enum_type` will be case insensitive.

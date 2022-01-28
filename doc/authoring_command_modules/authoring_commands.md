The document provides instructions and guidelines on how to author individual commands.

**AUTHORING COMMANDS**

[1. Write the Command Loader](#write-the-command-loader)

[2. Write a Command](#write-a-command)

[3. Register Commands](#register-commands)

[4. Write Help Entry](#write-help-entry)

[5. Customize Arguments](#customize-arguments)

**ADDITIONAL TOPICS**

[6. Keyword Argument (kwarg) Reference](#keyword-argument-reference)

[7. Supporting the IDs Parameter](#supporting-the-ids-parameter)

[8. Supporting Name or ID Parameters](#supporting-name-or-id-parameters)

[9. Generic Update Commands](#generic-update-commands)

[10. Custom Table Formats](#custom-table-formats)

[11. Tab Completion (bash only)](#tab-completion)

[12. Validators](#validators)

[13. Registering Flag Arguments](#registering-flags)

[14. Registering Enum Arguments](#registering-enums)

[15. Preventing particular extensions from being loading](#extension-suppression)

[16. Deprecating Commands and Arguments](#deprecating-commands-and-arguments)

[17. Multi-API Aware Modules](#multi-api-aware-modules)

[18. Preview Commands and Arguments](#preview-commands-and-arguments)

Authoring Commands
=============================

## Write the Command Loader

As of version 2.0.24, Azure CLI is based on the Knack framework (https://github.com/Microsoft/knack), which uses the `CLICommandsLoader` class as the mechanism for loading a module. In Azure CLI, you will create your own loader which will inherit from the `AzCommandsLoader` class.  The basic structure is:

```Python
class MyCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.sdk.util import CliCommandType
        from azure.cli.core.profiles._shared import MGMT_MYTYPE
        mymod_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.mymod.custom#{}')

        super(MyCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                               resource_type=MGMT_MYTYPE,
                                               custom_command_type=mymod_custom)

    def load_command_table(self, args):
        # TODO: Register command groups and commands here
        return self.command_table

    def load_arguments(self, command):
        # TODO: Register argument contexts and arguments here

COMMAND_LOADER_CLS = MyCommandsLoader
```

Note that `MGMT_MYTYPE` will need to be added to the `azure\cli\core\profiles\_shared.py` file. See [Multi-API Aware Modules](#multi-api-aware-modules)

```Python
class ResourceType(Enum):  # pylint: disable=too-few-public-methods
    ...
    MGMT_MYTYPE = ('azure.mgmt.mytype', 'MyTypeManagementClient')
    ...
```

## Write a Command

Write your command as a simple function, specifying your arguments as the parameter names.

***Parameter Naming Guidance***

When choosing names, it is recommended that you look at similar commands and follow those naming conventions to take advantage of any aliasing that may already be in place. For example, you should choose `resource_group_name` over `rg`, `resource_group` or some other shorthand, because this parameter is globally aliased and you will inherit the `-g` short option and the completer.

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
    operations_tmpl='azure.mgmt.mymod.operations#MyOperations.{}',
    client_factory=cf_mymod
)

# (2) Registering a command group
with self.command_group('mymod', mymod_sdk) as g:
    # (3) Registering different types of commands
    g.command('command1', 'do_something_1')
    g.custom_command('command2', 'do_something_2')
    g.generic_update_command('update', custom_function_name='my_custom_update')
    g.wait_command('wait')
    g.show_command('show')
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
- `kwargs`: any supported kwarg. Commonly used kwargs include `validator`, `table_transformer`, `confirmation`, `supports_no_wait` and  `transform`.

Any kwargs that are not specified will be pulled from the `command_type` kwarg, if present.

***custom_command***

The signature for `custom_command` is exactly the same as `command`. The only difference is that, whereas `command` uses `command_type` as the fallback for missing kwargs, `custom_command` relies on `custom_command_type`.

***generic_update_command***

See the section on [Generic Update Commands](#generic-update-commands)

***wait_command***

The generic wait command provides a template solution for polling Azure resources until specific conditions are met.

```Python
wait_command(self, name, getter_name='get', **kwargs)
```

- `name`: The name of the command within the command group. Commonly called 'wait'.
- `getter_name`: The name of the method for the object getter, relative to the path specified in `operations_tmpl`.
- `kwargs`: any supported kwarg.

Since most wait commands rely on a simple GET call from the SDK, most of these entries simply look like:
```Python
   g.wait_command('wait')
```

***custom_wait_command***

Similar to `custom_command` and `command`, the signature for `custom_wait_command` is exactly the same as `wait_command` but uses `custom_command_type` as the fallback for missing kwargs.

***show_command***

The generic show command ensures a consistent behavior when encountering a missing Azure resource. 
With little exception, all `show` commands should be registered using this method or `custom_show_command` to ensure consistency.

```Python
show_command(self, name, getter_name='get', **kwargs)
```

- `name`: The name of the command within the command group. Commonly called 'show'.
- `getter_name`: The name of the method for the object getter, relative to the path specified in `operations_tmpl`.
- `kwargs`: any supported kwarg.

***custom_show_command***

Similar to `custom_command` and `command`, the signature for `custom_show_command` is exactly the same as `show_command` but uses `custom_command_type` as the fallback for missing kwargs.

**(4) Supporting --no-wait**

When registering a command, the boolean `supports_no_wait` property can be used to specify that the command supports `--no-wait`.

Here are examples:

***command()***

```Python
with self.command_group('mymod', mymod_sdk) as g:
    g.command('command1', 'do_something_1', supports_no_wait=True)
```

***custom_command()***

```Python
# inside load_command_table(...)
with self.command_group('mymod', mymod_sdk) as g:
    g.custom_command('command2', 'do_something_2', supports_no_wait=True)

# inside custom.py
from azure.cli.core.util import sdk_no_wait
def do_something_2(cmd, arg1, arg2, no_wait=False):
    return sdk_no_wait(no_wait, client.create_or_update, arg1, arg2)
```

The signature of `azure.cli.core.util.sdk_no_wait` is:

```Python
sdk_no_wait(no_wait, func, *args, **kwargs)
```


- `no_wait` - The boolean for no wait. `True` if `--no-wait` specified. `False` otherwise.
- `func` - The callable to use.
- `args` - The positional arguments that should be passed to the callable.
- `kwargs` - The keyword arguments that should be passed to the callable.

***generic_update_command()***

```Python
with self.command_group('mymod', mymod_sdk) as g:
    g.generic_update_command('update', supports_no_wait=True)
```

**(5) Supporting --defer**

When registering a command, the boolean `supports_local_cache` property can be used to specify that the command supports `--defer`. This will allow traditional GET and PUT requests to interact with the CLI's local object cache instead of making
calls on the wire either for performance reasons (to avoid network latency) or because the service will only accept a payload constructed from many calls.

See [Commands With Complex Types](https://github.com/Azure/azure-cli/blob/dev/doc/command_guidelines.md#commands-with-complex-types)

Here are examples:

***custom_command()***

```Python
# inside load_command_table(...)
with self.command_group('mymod', mymod_sdk) as g:
    g.custom_command('command2', 'do_something_2', supports_local_cache=True)

# inside custom.py
def do_something_2(cmd, client, arg1, arg2, no_wait=False):
    from azure.cli.core.commands import cached_get, cached_put
    item = cached_get(cmd, client.get, arg1, arg2)
    # TODO: perform some mutation of item
    return cached_put(cmd, client.create_or_update, arg1, arg2, item)
```

Cached objects are deleted upon a successful PUT and can be view and managed using the `az cache` commands.

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
with self.argument_context('mypackage', ...) as c:  # applies to BOTH command1 and command2
```
But
```Python
with self.argument_context('mypackage command1', ...) as c:  # applies to command1 but not command2
```
Like CSS rules, modifications are applied in order from generic to specific.
```Python
with self.argument_context('mypackage', ...) as c:  # applies to both command1 and command2
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

Additional Topics
=============================

## Keyword Argument Reference

**Overview of Keyword Arguments in the Azure CLI**

When writing commands for the Azure CLI, it is important to understand how keyword arguments (kwargs) are applied. Refer to the following diagram.

![](/doc/assets/annotated-kwarg-structure.gif)

From the diagram you can see that any kwargs supplied when creating the `AzCommandsLoader` object are passed to and used as the baseline for any command groups or argument contexts that are later created. Any kwargs specified in the `command_group` calls serve as the baseline for any `command` or `custom_command` calls, and any kwargs passed to `argument_context` serve as the baseline for any calls to `argument`.

While kwargs are inherited from higher levels on the diagram, they can be overridden at a lower level. For example, if `custom_command_type=foo` is used as a module-level kwarg in the `AzCommandLoader.__init__` method and `custom_command_type=bar` is passed for a call to `command_group`, then `bar` will be used for all calls to `custom_command` within that command group.

Additionally, you can see that kwargs registered on a command group *do not* carry over to argument contexts, so you must apply the kwargs in both places if necessary.

****Command Group****

_Special Kwargs_

The following special kwargs are supported by command group and its helper methods:
- `table_transformer` - See section on [Custom Table Formats](#custom-table-formats)
- `validator` - See section on [Validators](#validators)
- `confirmation` - During interactive use, will prompt the user to confirm their choice to proceed. Supply a value of True to use the default prompt, or supply a string to use a custom prompt message. If the command is invoked in non-interactive scenarios and the --yes/-y parameter is not supplied, the command will fail.
- `transform` - Accepts a callable that takes a command result, which can be manipulated as desired. The transformed result is then returned. In general, output formats should closely mirror those returned by the service, and so this should be infrequently used. The modifies the output *regardless of the output format type*.
- `deprecate_info` - See [Deprecating Commands and Arguments](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#deprecating-commands-and-arguments)
- `formatter_class` - Advanced. Accepts a custom class that derives from `argparse.HelpFormatter` to modify the help document generation.
- `argument_loader` - Advanced. Accepts a callable that takes no parameters which will be used in place of the default argument loader.
- `description_loader` - Advanced. Accepts a callable that takes no parameters which will be used in place of the default description loader.
- `is_preview` - See [Preview Commands and Arguments](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#preview-commands-and-arguments)

_General Kwargs_

The following kwargs may be inherited from the command loader:
- `min_api` - Minimum API version for which the command will appear.
- `max_api` - Maximum API version for which the command will appear.
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
- `arg_group` - Groups arguments within this context under a group name or add an argument to the group. This group name is shown in the help for the command. For example if `arg_group` is "Network", all applicable arguments will be grouped under the heading "Network Arguments" in the help text for the command.
- `is_preview` - See [Preview Commands and Arguments](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md#preview-commands-and-arguments)

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
- `max_api` - Maximum API version for which the argument will appear. Otherwise the argument will be ignored.
- `resource_type` - An `azure.cli.core.profiles.ResourceType` enum value that is used for multi-API packages.
- `operation_group` - Only used by the `azure-cli-vm` module to specify which resource API to target.

## Supporting the IDs Parameter

Most ARM resources can be identified by an ID. In many cases, for example `show` and `delete` commands, it may be more useful to copy and paste an ID to identify the target resource instead of having to specify the names of the resource group, the resource, and the parent resource (if any).

Azure CLI supports exposing an `--ids` parameter that will parse a resource ID into its constituent named parts so that this parsing need not be done as part of a client script. Additionally `--ids` will accept a _list_ of space-separated IDs, allowing the client to loop the command over each ID.

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
- `--ids` is intended to be the ID of the resource the command group is about. Thus, it needs to be suppressed on `list` commands for child resources. This simplest way to do this:
```Python
with self.argument_context('parent child') as c:
  c.argument('parent_name', id_part=None)  # This should ALWAYS be the id_part that was 'name'.
  c.argument('child_name', ...)
```

## Supporting Name or ID Parameters

Often times, the service needs references to supporting resources like storage accounts, key vault, etc. Typically, services require the ARM ID of these resources. The CLI pattern is to accept the ARM ID for this resource OR the name of the resource, assuming the resource is in the same subscription and resource group as the main resource.

DO NOT:
- Expose an ID parameter like `--storage-account-id`.
- Add parameters like `--storage-account-resource-group` to indicate the resource group for the secondary resource. The user should supply the ARM ID in this instance.

DO:
- Call the parameter `--storage-account` and indicate in the help text that it accepts the "Name or ID of the storage account."
- Add logic similar to the following to a validator or custom command to process the name or ID logic:

**Custom Command**
```Python
def my_command(cmd, resource_group_name, foo_name, storage_account):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if not is_valid_resource_id(storage_account):
        storage_account = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Storage', type='storageAccounts',
            name=storage_account
        )
```

**Validator**
```Python
def validate_storage_name_or_id(cmd, namespace):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.storage_account:
        if not is_valid_resource_id(namespace.storage_account):
            namespace.storage_account = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Storage', type='storageAccounts',
                name=namespace.storage_account
            )
```


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

However, most commonly, the `custom_func_name` and `custom_func_type` kwargs will be used to expose convenience arguments in addition to the generic arguments.

- `name` - The name of the command. Most commonly 'update'.
- `getter_name` - The name of the method which will be used to retrieve the object instance. If the method is named `get` (which is the case for most SDKs), this can be omitted.
- `getter_type` - A `CliCommandType` object which will be used to locate the getter. Only needed if the getter is a custom command (uncommon).
- `setter_name` - The name of the method which will be used to update the object instance using a PUT method. If the method is named `create_or_update` (which is the case for most SDKs), this can be omitted.
- `setter_type` - A `CliCommandType` object which will be used to locate the setter. Only needed if the setter is a custom command (uncommon).
- `setter_arg_name` - The name of the argument in the setter which corresponds to the object being updated. If the name is `parameters` (which is the case for most SDKs), this can be omitted.
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

Sometimes you will want to write commands that operate on child resources and it may be that these child resources don't have dedicated getters and setters. In these cases, you must rely on the getter and setter of the parent resource. For example, consider an object `my_parent` which has a child collection `my_child` which in turn has its own child collection `my_grandchild`. The key property for all of these objects is simply `name`. For these cases, `generic_update_command` has three additional parameters:
  - `child_collection_prop_name` - the name path to the child collection property, using dot syntax. To access `my_child`, the value would be `my_child`. To access `my_grandchild`, the value would be `my_child.my_grandchild`.
  - `child_collection_key` - Most child collections in Azure are lists of objects (as opposed to dictionaries) which will have a property in them that serves as the key. This is the name of that key property. By default it is `name`. To refer to `my_child`, the value would be `name`. To refer to `my_grandchild` the value would be `name.name`.
  - `child_arg_name` - If you want to refer the child object key (the property identified by `child_collection_key`) inside a custom function, you should specify the argument name you use in your custom function. By default, this is called `item_name`. In the above example, where our child object had a key called `name`, you could refer to this property within your custom function through the `item_name` property, or specify something different. For grandchild collections, use dot syntax (i.e.: `child_name.grandchild_name`).

**Logic Flow**

A simplified understanding of the flow of the generic update is as follows:

```Python
instance = getter(...)  # retrieve the object
if custom_function:
    instance = custom_function(...) # apply custom logic
instance = _process_generic_updates(...) # apply generic updates, which will overwrite custom logic in the event of a conflict
return setter(instance)  # update the instance and return the result
```

**Generic Update for PATCH-based Services**

`generic_update_command` was designed to simulate PATCH-like behavior for services that are backed only by a PUT API endpoint. For services that have actual PATCH-based update endpoints, the CLI's `update` command should still leverage `generic_update_command` in order to provide consistency among commands. The following guidelines should be helpful:

- You'll probably need to specify the `setter_name` since it will likely be `update` instead of `create_or_update` (the default).
- You will HAVE TO supply `custom_func_name` and `custom_func_type`. Consider the following example:
```Python
def my_custom_foo_update(instance, prop1=None, prop2=None, complex_prop1=None, complex_prop2=None):
   from my_foo_sdk import FooUpdateParameters, ComplexProperty

   # (1) instantiate the update parameters object. Generally, you can pass simple parameters
   # as-is and the service will correctly interpret this.
   parameters = FooUpdateParameters(
     prop1=prop1,
     prop2=prop2)

   # (2) complex objects must also have PATCH-like behavior, and often services do not
   # correctly support this. You may need to fill these objects with the existing
   # values if they are not being updated
   parameters.complex_prop = ComplexProperty(
     complex_prop1=complex_prop1 or instance.complex_prop.complex_prop1,
     complex_prop2=complex_prop2 or instance.complex_prop.complex_prop2
   )
   # (3) instead of returning the instance object as you do with a PUT-based generic update,
   # return the update parameters object.
   return parameters
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

## Extension Suppression

It is possible for a command module to suppress specific extensions from being loaded.

This is useful for commands that were once extensions that have now moved inside a command module.

Here, we suppress an extension by name and also by version.

This will allow the extension to be published in the future with the same name and a newer version that will not be suppressed.

This is great for experimental extensions that periodically get incorporated into the product.

```Python
class MyCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        # Suppress myextension up to and including version 0.2.0
        super(MyCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                               suppress_extension=ModExtensionSuppress(__name__, 'myextension', '0.2.0',
                                                                                       reason='These commands are now in the CLI.',
                                                                                       recommend_remove=True))
```

## Deprecating Commands and Arguments

The CLI has built-in support for deprecating the following: commands, command groups, arguments, option values. Deprecated items will appear with a warning in the help system or when invoked. The following keyword arguments are supported when deprecating an item:

- `target`: The thing being deprecated. This is often not needed as in most cases the CLI can figure out what is being deprecated.
- `redirect`: This is the alternative that should be used in lieu of the deprecated thing. If not provided, the item is expected to be removed in the future with no replacement.
- `hide`: Hide the deprecated item from the help system, reducing discoverability, but still allow it to be used. Accepts either the boolean `True` to immediately hide the item or a core CLI version. If a version is supplied, the item will appear until the core CLI rolls to the specified value, after which it will be hidden.
- `expiration`: Accepts a core CLI version at which the deprecated item will no longer function. This version will be communicated in all warning messages. 

Deprecation of different command elements are usually accomplished using the `deprecate_info` kwarg in conjunction with a `deprecate` helper method.

***Deprecate Command Group***
```Python
with self.command_group('test', test_sdk, deprecate_info=self.deprecate(redirect='new-test', hide=True)) as g:
  g.show_command('show', 'get')
  g.command('list', 'list')
```

This will deprecate the entire command group `test`. Note that call to `self.deprecate`, calling the deprecate helper method off of the command loader. The warning message for this would read: ```This command group has been deprecated and will be removed in a future release. Use `new-test` instead.```

Additionally, since the command group is deprecated then, by extension, all of the commands within it are deprecated as well. They will not be marked as such, but will display a warning:

```This command has been implicitly deprecated because command group `test` is deprecated and will be removed in a future release. Use `new-test` instead.```

***Deprecate Command***
```Python
with self.command_group('test', test_sdk) as g:
  g.command('show-parameters', 'get_params', deprecate_info=g.deprecate(redirect='test show', expiration='2.1.0'))
```

This will deprecate the command `test show-parameters`. Note that call to `g.deprecate`, calling the deprecate helper method off of the command group. The warning message for this would read: ```This command has been deprecated and will be removed in version 2.1.0. Use `test show` instead.```

***Deprecate Argument***
```Python
with self.argument_context('test show-parameters') as c:
  c.argument('junk_flag', help='Something we no longer want to support.' deprecate_info=c.deprecate(expiration='2.1.0'))
```

This will deprecate the argument `--junk-flag` on `test show-parameters`. Note that call to `c.deprecate`, calling the deprecate helper method off of the argument context. The warning message for this would read: ```Argument `--junk-flag` has been deprecated and will be removed in version 2.1.0.```

***Deprecate Argument Option***
```Python
with self.argument_context('test show-parameters') as c:
  c.argument('resource', options_list=['--resource', c.deprecate(target='--resource-id', redirect='--target')])
```

This will deprecate the argument `--resource-id` option on `test show-parameters` in favor of `--resource`. Note that call to `c.deprecate`, calling the deprecate helper method off of the argument context. The warning message for this would read: ```Option `--resource-id` has been deprecated and will be removed in a future release. Use `--resource` instead.``` Here you must specify `target` in order to identify the deprecated option. When an option value is deprecated, it appears in help as two separate arguments, with the deprecation warning on the deprecated option. 

## Multi-API Aware Modules
To convert a module that used a mono-versioned SDK to one that works with multiple API versions:

1. In `azure.cli.core.profiles._shared.py` register your SDK and client in the `ResourceType` enum:

```Python
class ResourceType(Enum):

  MGMT_MYSERVICE = ('azure.mgmt.myservice, MyServiceManagementClient')  # REGISTER YOUR SDK
  ...
```


2. In the `AZURE_API_PROFILES` dictionary in that same file, for each profile your service applies to, add an entry for it like this:

```Python
AZURE_API_PROFILES = {
  'latest': {
    ResourceType.MGMT_MYSERVICE: '2019-03-01' # the supported API version on that profile
    ...
  },
  '2020-09-01-hybrid': {
    ResourceType.MGMT_MYSERVICE: '2018-08-01' # different API version for this profile
    ...
  },
  ...
}
```

3. Update imports in your files. They must use the API profile-aware "get_models" method and have access to a command or CLI object.

Example:
```Python
from azure.mgmt.myservice import Foo, Boo

def my_command(...):
   # do stuff
```

Converted:
```Python
def my_command(cmd, ...):
  Foo, Boo = cmd.get_models('Foo', 'Boo')
  # do stuff
```

4. Use appropriate conditionals to ensure your command can run on all supported profiles:

***commands.py***

```Python
with self.command_group('test') as g:
  g.command('use-new-feature', 'use_new_feature', min_api='2018-03-01')  # won't be available unless min API is met
```

***params.py***

```Python
with self.argument_context('test create') as c:
  c.argument('enable_new_feature', min_api='2018-03-01', arg_type=get_three_state_flag())  # expose argument only when min API is satisfied
```

***custom.py***

```Python
def my_test_command(cmd, ...):
  Foo = cmd.get_models('Foo')
  my_foo = Foo(...)
  
  # will still work with older API versions because this branch will be skipped
  if cmd.supported_api_version(min_api='2018-03-01'):
    my_foo.enable_new_feature = enable_new_feature

  return client.create_or_update(..., my_foo)
```

See earlier topics for other kwargs that can be used with multi-API idioms.

## Preview Commands and Arguments

The CLI has built-in support for marking commands, command groups and arguments as being in "preview" status. Preview items will appear with a warning in the help system or when invoked. Items marked preview can be changed, broken or removed at any time without following the deprecation process. 

**Note that ANYTHING not marked "preview" is considered GA and thus a breaking change can only be enacted by following the deprecation mechanism (see earlier topic).**

Items are marked Preview using the `is_preview=True` kwarg. See the following for examples:

***Preview Command Group***
```Python
with self.command_group('test', test_sdk, is_preview=True) as g:
  g.show_command('show', 'get')
  ...
```

Additionally, since the command group is in preview then, by extension, all of the commands and arguments within it are in preview as well. No message will be displayed for implicitly in-preview arguments, but a warning will be displayed for implicitly in-preview commands.

***Preview Command***
```Python
with self.command_group('test', test_sdk) as g:
  g.command('show-parameters', 'get_params', is_preview=True)
```

This will declare just the command `test show-parameters` as being in preview. This command will appear with the `[Preview]` status tag when viewed in group help whereas other commands in the `test` group will not, indicating that only this command (and, by implication, its arguments) are in preview status.

***Preview Argument***
```Python
with self.argument_context('test show-parameters') as c:
  c.argument('cool_flag', help='Something cool new flag.', is_preview=True)
```

This will mark the argument `--cool-flag` on `test show-parameters` as being in preview, appearing with the `[Preview]` tag.

***Preview Extensions***

Extensions are marked as being in preview using an older mechanism in the `azext_metadata.json` file.

```
{
    "azext.isPreview": true,
}
```

It is recommended that, if an extension is in preview, that it also uses the above mechanisms to give the same level of visibility to in preview items.

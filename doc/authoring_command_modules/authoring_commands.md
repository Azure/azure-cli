Authoring Commands
=============================

The document provides instructions and guidelines on how to author individual commands.

**Overview**

The basic process of adding commands is presented below, and elaborated upon later in this document.

1. Create an \_\_init__.py file for your command module.
2. Write your command as a standard Python function.
3. Register your command using the `cli_command` (or similar) function.
4. Write up your command's help entry.
5. Use the `register_cli_argument` function to add the following enhancements to your arguments, as needed:
    - option names, including short names
    - validators, actions or types
    - choice lists
    - completers

**Writing a Command**

Write your command as a simple function, specifying your arguments as the parameter names.

When choosing names, it is recommended that you look at similiar commands and follow those naming conventions to take advantage of any aliasing that may already be in place. For example, you should choose `resource_group_name` over `rg`, `resource_group` or some other shorthand, because this parameter is globally aliased and you will inherit the `-g` short option and the completer.

If you specify a default value in your function signature, this will flag the argument as optional and will automatically display the default value in the help text for the command. Any parameters that do not have a default value are required and will automatically appear in help with the [Required] label. The required and default behaviors for arguments can be overridden if needed with the `register_cli_argument` function (see Argument Customization below) but this is not generally needed.

**Registering Commands**

Before your command can be used in the CLI, it must be registered. Insert the following statement in your file:

```Python
from azure.cli.core.commands import cli_command
```

The signature of this method is 
```Python
def cli_command(module_name, name, operation, client_factory=None, transform=None, table_transformer=None, confirmation=None):
```
You will generally only specify `name`, `operation` and possibly `table_transformer`.
  - `module_name` - The name of the module that is registering the command (e.g. `azure.cli.command_modules.vm.commands`). Typically this will be `__name__`.
  - `name` - String uniquely naming your command and placing it within the command hierachy. It will be the string that you would type at the command line, omitting `az` (ex: access your command at `az mypackage mycommand` using a name of `mypackage mycommand`).
  - `operation` - The handler that will be executed. Format is `<module_to_import>#<attribute_list>`
      - For example if `operation='azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.get'`, the CLI will import `azure.mgmt.compute.operations.virtual_machines_operations`, get the `VirtualMachinesOperations` attribute and then the `get` attribute of `VirtualMachinesOperations`.
  - `table_transformer` (optional) - Supply a callable that takes, transforms and returns a result for table output.
  - `confirmation` (optional) - Supply True to enable default confirmation. Alternatively, supply a callable that takes the command arguments as a dict and returning a boolean. Alternatively, supply a string for the prompt.

At this point, you should be able to access your command using `az [name]` and access the built-in help with `az [name] -h/--help`. Your command will automatically be 'wired up' with the global parameters.

**Write Your Help Entry**

See the following for guidance on writing a help entry: https://github.com/Azure/azure-cli/blob/master/doc/authoring_help.md

**Customizing Arguments**

There are a number of customizations that you can make to the arguments of a command that alter their behavior within the CLI. To modify/enhance your command arguments, use the `register_cli_argument` method from the `azure.cli.core.commands` package. For the standard modules, these entries are contained within a file called `_params.py`. 

The signature of this method is
```Python
def register_cli_argument(scope, dest, arg_type=None, **kwargs):
```

- `dest` - This string is the name of the parameter you wish to modify, as specified in the function signature.
- `scope` - This string is the level at which your customizations are applied. For example, consider the case where you have commands `az mypackage command1` and `az mypackage command2`, which both have a parameter `my_param`. 

```Python
register_cli_argument('mypackage', 'my_param', ...)  # applies to BOTH command1 and command2
```
But
```Python
register_cli_argument('mypackage command1', 'my_param', ...)  # applies to command1 but not command2
```
Like CSS rules, modifications are applied in order from generic to specific.
```Python
register_cli_argument('mypackage', 'my_param', ...)  # applies to both command1 and command2
register_cli_argument('mypackage command2', 'my_param', ...)  # command2 inherits and build upon the previous changes
```
- `arg_type` - An instance of the `azure.cli.core.commands.CliArgumentType` class. This essentially serves as a named, reusable packaging of the `kwargs` that modify your command's argument. It is useful when you want to reuse an argument definition, but is generally not required. It is most commonly used for name type parameters.
- `kwargs` - Most likely, you will simply specify keyword arguments in `register_cli_argument` that will accomplish what you need.  Any `kwargs` specified will override or extended the definition in `arg_type`, if provided.

The follow keyword arguments are supported:
- `options_list` - By default, your argument will be exposed as an option in hyphenated form (ex: `my_param` becomes `--my-param`). If you would like to change the option string without changing the parameter name, and/or add a short option, specify the `options_list` kwarg. This is a tuple of two string values, one for an standard option string, and the other for an optional short string. (Ex: `options_list=('--myparam', '-m')`)
- `validator` - The name of a callable that takes the function namespace as a parameter. Allows you to perform any custom logic or validation on the entire namespace prior to command execution. Validators are executed after argument parsing, and thus after `type` and `action` have been applied. However, because the order in which validators are exectued is random, you should not have multiple validators modifying the same parameter within the namespace.
- `completer` - The name of a callable that takes the following parameters `(prefix, action, parsed_args, **kwargs)` and return a list of completion values.

Additionally, the following `kwargs`, supported by argparse, are supported as well:
- `nargs` - See https://docs.python.org/3/library/argparse.html#nargs
- `action` - See https://docs.python.org/3/library/argparse.html#action
- `const` - See https://docs.python.org/3/library/argparse.html#const
- `default` - See https://docs.python.org/3/library/argparse.html#default. Note that the default value is inferred from the parameter's default value in the function signature. If specified, this will override that value.
- `type` - See https://docs.python.org/3/library/argparse.html#type
- `choices` - See https://docs.python.org/3/library/argparse.html#choices. If specified this will also serve as a value completer for people using tab completion.
- `required` - See https://docs.python.org/3/library/argparse.html#required. Note that this value is inferred from the function signature depending on whether or not the parameter has a default value. If specified, this will override that value.
- `help` - See https://docs.python.org/3/library/argparse.html#help. Generally you should avoid adding help text in this way, instead opting to create a help file as described above.
- `metavar` - See https://docs.python.org/3/library/argparse.html#metavar
- `id_part` - See below the section on Supporting the IDs Parameter.

Supporting the IDs Parameter
=============================

Most ARM resources can be identified by an ID. In many cases, for example show and delete commands, it may be more useful to copy and paste an ID to identify the target resource instead of having to specify the names of the resource group, the resource, and the parent resource (if any).

Azure CLI 2.0 supports exposing an `--ids` parameter that will parse a resource ID into its constituent named parts so that this parsing need not be done as part of a client script. Additionally `--ids` will accept a _list_ of space separated IDs, allowing the client to loop the command over each ID.

Enabling this functionality only requires the command author specify the appropriate values for `id_part` in their calls to `register_cli_argument`.

Consider the following simplified example for NIC IP config. 

```Python
def show_nic_ip_config(resource_group_name, nic_name, ip_config_name):
    # retrieve and return the IP config

register_cli_command('network nic ip-config show', ...#show_nic_ip_config, ...)

register_cli_argument('network nic ip-config', 'nic_name', help='The NIC name.')
register_cli_argument('network nic ip-config', 'ip_config_name', options_list=('--name', '-n'), help='The IP config name.')
```
The help output for this command would be:
```
 Arguments
    --name -n          : The IP config name.
    --nic-name         : The NIC name.
    --resource-group -g: Name of resource group.   
```

Now let's specify values for the `id_part` kwarg in the calls to `register_cli_argument`:
```Python
def show_nic_ip_config(resource_group_name, nic_name, ip_config_name):
    # retrieve and return the IP config

register_cli_command('network nic ip-config show', ...#show_nic_ip_config, ...)

register_cli_argument('network nic ip-config', 'nic_name', id_part='name', help='The NIC name.')
register_cli_argument('network nic ip-config', 'ip_config_name', id_part='child_name', options_list=('--name', '-n'), help='The IP config name.')
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

A couple things to note:
- Currently, `--ids` is not exposed for any command that is called 'create', even if it is configured properly.
- The supported values for `id_part` are: `name`, `child_name`, and `grandchild_name`.


Generic Update Commands
=============================

The update commands within the CLI expose a set of generic update arguments: `--add`, `--remove` and `--set`. This allows the user to manipulate objects in a consistent way that may not have long option flags supported by the command. The method which exposes these arguments is `cli_generic_update_command` in the `azure.cli.core.commands.arm` package. The signature of this method is:

```Python
def cli_generic_update_command(name, getter, setter, factory=None, setter_arg_name='parameters',
                               table_transformer=None, child_collection_prop_name=None,
                               child_collection_key='name', child_arg_name='item_name',
                               custom_function_op=None):
```
For many commands will only specify `name`, `getter`, `setter` and `factory`.
  - `name` - Same as registering a command with `cli_command(...)`.
  - `getter` - A method which returns an instance of the object being updated.
  - `setter` - A method which takes an instance of the object and updates it.
  - `factory` (optional) - Any client object upon which the getter and setter rely. If omitted, then the getter and setter are responsible for creating their own client objects as needed.
  - `setter_arg_name` (optional) - The is the name for the object instance used in the setter method. By default it is `parameters` because many Azure SDK APIs use this convention. If your setter uses a different name, specify it here.
  - `custom_function` (optional) - A method which accepts the object being updated (must be named `instance`) and returns that object. This is commonly used to process convenience options which may be added to the command by listing them in the method signature, similar to a purely custom method. The difference is that a custom command function returns the command result while a generic update custom function returns only the object being updated. A simple custom function might look like:
  
  ```Python
  def my_custom_function(instance, item_name, custom_arg=None):
    if custom_arg:
        instance.property = custom_arg
    return instance
  ```
  - `table_transformer` (optional) - Same as `cli_command(...)`

**Working With Child Collections and Properties (Advanced)**

Sometimes you will want to write commands that operate on child resources and it may be that these child resources don't have dedicated getters and setters. In these cases, you must rely on the getter and setter of the parent resource. For these cases, `cli_generic_update_command` has three additional parameters:
  - `child_collection_prop_name` - the name of the child collection property. For example, if object `my_parent` has a child collection called `my_children` that you would access using `my_parent.my_children` then the name you would use is 'my_children'.
  - `child_collection_key_name` - Most child collections in Azure are lists of objects (as opposed to dictionaries) which will have a property in them that serves as the key. This is the name of that key property. By default it is 'name'. In the above example, if an entry in the `my_children` collection has a key property called `my_identifier` then the value you would supply is 'my_identifier'.
  - `child_arg_name` - If you want to refer the child object key (the property identified by `child_collection_key_name`) inside a custom function, you should specify the argument name you use in your custom function. By default, this is called `item_name`. In the above example, where our child object had a key called `my_identifier`, you could refer to this property within your custom function through the `item_name` property, or specify something different.
  
**Logic Flow**

A simplified understand of the flow of the generic update is as follows:

```Python
instance = getter(...)  # retrieve the object
if custom_function:
    instance = custom_function(...) # apply custom logic
instance = _process_generic_updates(...) # apply generic updates, which will overwrite custom logic in the event of a conflict
return setter(instance)  # update the instance and return the result
```

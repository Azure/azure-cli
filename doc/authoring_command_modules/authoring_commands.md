Authoring Commands
=============================

The document provides instructions and guidelines on how to author individual commands.

**Overview**

The basic process of adding commands is presented below, and elaborated upon later in this document.

1. Write your command as a standard Python function.
2. Register your command using the `cli_command` (or similar) function.
3. Write up your command's help entry.
4. Use the `register_cli_argument` function to add the following enhancements to your arguments, as needed:
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
from azure.cli.commands import cli_command
```

The signature of this method is 
```Python
def cli_command(name, operation, client_factory=None, transform=None, table_transformer=None):
```
You will generally only specify `name`, `operation` and possibly `table_transformer`.
  - `name` - String uniquely naming your command and placing it within the command hierachy. It will be the string that you would type at the command line, omitting `az` (ex: access your command at `az mypackage mycommand` using a name of `mypackage mycommand`).
  - `operation` - Your function's name.
  - `table_transformer` (optional) - Supply a callable that takes, transforms and returns a result for table output.

At this point, you should be able to access your command using `az [name]` and access the built-in help with `az [name] -h/--help`. Your command will automatically be 'wired up' with the global parameters.

**Write Your Help Entry**

See the following for guidance on writing a help entry: https://github.com/Azure/azure-cli/blob/master/doc/authoring_help.md

**Customizing Arguments**

There are a number of customizations that you can make to the arguments of a command that alter their behavior within the CLI. To modify/enhance your command arguments, use the `register_cli_argument` method from the `azure.cli.commands` package. For the standard modules, these entries are contained within a file called `_params.py`. 

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
- `arg_type` - An instance of the `azure.cli.commands.CliArgumentType` class. This essentially serves as a named, reusable packaging of the `kwargs` that modify your command's argument. It is useful when you want to reuse an argument definition, but is generally not required. It is most commonly used for name type parameters.
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

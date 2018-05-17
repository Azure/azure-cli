Authoring Command Modules
=========================

The document provides instructions and guidelines on how to author command modules. For other help, please see the following:

**Module Authoring**:<br>You are here!

**Command Authoring**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/authoring_command_modules/authoring_commands.md

**Command Guidelines**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/command_guidelines.md

**Help Authoring**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/authoring_help.md

**Test Authoring**:<br>https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md


<a name="heading_set_up"></a>Set Up
------

Create you dev environment if you haven't already. This is how to do that.  

Clone the repo, enter the repo directory then create your virtual environment.  

For example:
```
git clone https://github.com/Azure/azure-cli.git
cd azure-cli
virtualenv env
source env/bin/activate
python scripts/dev_setup.py
```

After this, you should be able to run the CLI with `az`.

[Author your command module...](#heading_author_command_mod)

Now, install your command module into the environment with pip in editable mode.  
Where `<path_to_your_command_module>` is the path to the directory containing your `setup.py` file.
```
pip install -e <path_to_your_command_module>
```

If installation was successful, you should be able to run `pip list` and see your command module.
```
$ pip list
...
azure-cli-example (0.0.1, /Users/myuser/Repos/azure-cli-example)
...
```

Also, you can run `az` and if your command module contributes any commands, they should appear.
If your commands aren't showing with `az`, use `az --debug` to help debug. There could have been an exception
thrown whilst attempting to load your module.

**Note for locally installed Azure SDKs:**  
If you're receiving Azure import errors, run `pip install -I azure-nspkg==1.0.0` in your virtual environment
after installing your SDK locally.


<a name="heading_author_command_mod"></a>Authoring command modules
------
Currently, all command modules should start with `azure-cli-`.  
When the CLI loads, it search for packages installed that start with that prefix.

The `example_module_template` directory gives an example command module with other useful examples.

Command modules should have the following structure:
```
.
|-- README.rst
|-- azure
|   |-- __init__.py
|   `-- cli
|       |-- __init__.py
|       `-- command_modules
|           |-- __init__.py
|           `-- <MODULE_NAME>
|               `-- __init__.py
`-- setup.py
`-- HISTORY.rst
```

**Create an \_\_init__.py for your module**

In the \_\_init__ file, you will declare a command loader class that inherits from AzCommandsLoader. You will typically override the following three methods:
  - `__init__` - Useful for setting metadata that applies to the entire module. For performance reasons, no heavy processing should be done here. See command authoring for more info.
  - `load_commands_table` - Register command groups and commands here. It is common to store the implementation of this method in
                            a file named `commands.py` but for very small modules this may not be necessary. See command authoring for
                            more info.
  - `load_arguments` - Apply metadata to your command arguments. It is common to store the implementation of this method in a file 
                       named `_params.py` but for very small modules this may not be necessary. See command authoring for more info.

**__init__.py**
```Python
from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.mymod._help import helps  # pylint: disable=unused-import

class MyModCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
      from azure.cli.core.commands import CliCommandType

      mymod_custom = CliCommandType(
        operations_tmpl='azure.mgmt.mymod.operations#MyModOperations.{}',
      )

      with self.command_group('myfoo', mymod_custom) as g:
        g.command('create', 'create_myfoo')

COMMAND_LOADER_CLS = MyModCommandsLoader
```

**custom.py**
```python
def create_myfoo(cmd, myfoo_name, resource_group_name, location=None):
    from azure.mgmt.example.models import MyFoo
    from azure.cli.command_modules.example._client_factory import cf_mymod
    client = cf_mymod(cmd.cli_ctx)

    foo = MyFoo(location=location)
    return client.create_or_update(myfoo_name, resource_group_name, foo)
```

The snippet above shows what it takes to author a basic command.
1. Create a CliCommandType which holds the metadata for your command. 
2. Create a command group in which your command will exist, passing the command type created in the previous step.
3. Register your command with the `command` method, defining first the name of the command and then the name of the method which will execute.
4. Define the callable that will execute:
    The CLI inspects the callable to determine required params, defaults and help text and more.  
    Try out the example to see these in action!

When running the command with the `--help` flag, you should see the command.
You can also now execute the command for yourself.
```
$ az myfoo create --help

Command
    az myfoo create

Arguments
    --myfoo-name          [Required]: The argument that is required.
    --resource-group-name [Required]: Also required.
    --location                      : Optional arg.
...

$ az myfoo create --myfoo-name foo --resource-group-name myrg
{
  "name": "foo",
  "resourceGroup": "myrg",
  "location": None
}
```

Testing
-------

Discover tests

```
azdev test --discover
```

Run all tests in a module:

```
azdev test MODULE [--live] [--series] [--discover] [--dest-file FILENAME]
```

Run an individual test:

```
azdev test TEST [TEST ...] [--live] [--series] [--discover] [--dest-file FILENAME]
```
For example `azdev test test_myfoo`

Run a test when there is a conflict (for example, both 'azure-cli-core' and 'azure-cli-network' have 'test_foo'):
```
azdev test MODULE.TEST [--live]
```

The list of failed tests are displayed at the end of a run and dumped to the file specified with `--dest-file` or `test_failures.txt` if nothing is provided. This allows for conveniently replaying failed tests:

```
azdev test --src-file test_failures.txt [--live] [--series] [--discover]
```

Relying on the default filename, the list of failed tests should grow shorter as you fix the cause of the failures until there are no more failing tests.

Style Checks
------------

```
azdev style --module <module> [--pylint] [--pep8]
```

Submitting Pull Requests
------------------------

### Modify Change Log

Modify the `HISTORY.rst` for any customer-facing changes. If a module has changed at all since a previous release so that a version bump is required, it is fine to add a generic entry that says "* Minor fixes.".

This will be the release notes for the next release.

e.g.:  
```
.. :changelog:

Release History
===============

0.0.3
+++++
* This is my customer-facing change.

0.0.2
+++++
* Minor fixes.

0.0.1
+++++
* Initial release
```

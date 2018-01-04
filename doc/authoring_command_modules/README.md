Authoring Command Modules
=========================

The document provides instructions and guidelines on how to author command modules. For other help, please see the following:

**Module Authoring**:<br>You are here!

**Command Authoring**:<br>https://github.com/Azure/azure-cli/blob/master/doc/authoring_command_modules/authoring_commands.md

**Help Authoring**:<br>https://github.com/Azure/azure-cli/blob/master/doc/authoring_help.md

**Test Authoring**:<br>https://github.com/Azure/azure-cli/blob/master/doc/recording_vcr_tests.md


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

The `example_module_template` directory gives a basic command module with 1 command.

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
```

**Create an \_\_init__.py for your module**

In the \_\_init__ file, two methods need to be defined:
  - `load_commands` - Uses the file in the 'Writing a Command' section below to load the commands.
  - `load_params` - Uses the file in the 'Customizing Arguments' section below to load parameter customizations.

```Python
def load_params(command):
    import azure.cli.command_modules.<module_name>._params

def load_commands():
    import azure.cli.command_modules.<module_name>.commands
```

```python
from azure.cli.core.commands import cli_command

def example(my_required_arg, my_optional_arg='MyDefault'):
    '''Returns the params you passed in.
    :param str my_required_arg: The argument that is required
    '''
    result = {'a': my_required_arg, 'b': my_optional_arg}
    return result

cli_command('example', example)
```

The snippet above shows what it takes to author a basic command.
1. Import `cli_command` from `azure.cli.core.commands`  
    This holds the core logic for creating commands.
2. Use `cli_command` to create your command  
    The only required parameters to this method are:  
    - `name` Name of the command  
    - `operation`  The callable that will execute for that command
3. Define the callable that will execute  
    The CLI inspects the callable to determine required params, defaults and help text and more.  
    Try out the example to see these in action!

When running the command with the `--help` flag, you should see the command.
You can also now execute the command for yourself.
```
$ az example --help

Command
    az example

Arguments
    --my-required-arg [Required]: The argument that is required.
    --my-optional-arg           : Default: MyDefault.
...

$ az example --my-required-arg abc
{
  "a": "abc",
  "b": "MyDefault"
}
```

Testing
-------

Run all tests in a module:

```
run_tests --module <module>
OR
python -m unittest discover -s <path_to_your_command_module>/tests
```

Run an individual test:

```
python <path_to_your_command_module>/<file> <class name>
```
For example `python src/command_modules/azure-cli-appservice/tests/test_webapp_commands.py WebappBasicE2ETest`

Note:  
The following is required in the test file when running an individual test.  
```
if __name__ == '__main__':
    unittest.main()
```

PyLint
------

```
pylint -r n <path_to_your_command_module>/azure
```

Submitting Pull Requests
------------------------

### Modify Change Log

Modify the `HISTORY.rst` for all changed modules.

This will be the release notes for the next release.

e.g.:  
```
.. :changelog:

Release History
===============

0.0.2
+++++

* This is my change.

0.0.1
+++++

* This is the changelog from a prev. release.

```

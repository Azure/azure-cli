Authoring Command Modules
=========================

The document provides instructions and guidelines on how to author command modules.

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
|-- requirements.txt
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
from azure.cli.commands import cli_command

def example(my_required_arg, my_optional_arg='MyDefault'):
    '''Returns the params you passed in.
    :param str my_required_arg: The argument that is required
    '''
    result = {'a': my_required_arg, 'b': my_optional_arg}
    return result

cli_command('example', example)
```

The snippet above shows what it takes to author a basic command.
1. Import `cli_command` from `azure.cli.commands`  
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

```
python -m unittest discover -s <path_to_your_command_module>/azure/cli/command_modules/<module_name>/tests
```

```
pylint -r n <path_to_your_command_module>/azure
```


Packaging/Publishing
--------------------
### Packaging
You have finished your command module and now want to package and publish it.

Make sure you are in the directory for your command module.  
Create the package by running:
```
python setup.py sdist
```
This will create a `dist` directory that contains your package.  

### Publishing
You are now ready to publish the package to PyPI or a private PyPI server of your choice.

There are many ways to publish but here is a template using Twine.
```bash
echo "[distutils]
index-servers =
    cli-pypi

[cli-pypi]
repository: <PYPI_REPO_URL>
username: <PYPI_REPO_USERNAME>
password: <PYPI_REPO_PASSWORD>
" > ~/.pypirc

pip install twine
# Uploads the packages in dist/ to the server referred to by cli-pypi.
twine upload -r cli-pypi dist/*
```

### Installing your published command module

If you published the package publicly, simply use `az component update --add example`.

If you published it to a private server, use `az component update --add example --private`.  

NOTE:
- Don't include the `azure-cli-` prefix when installing a command module.


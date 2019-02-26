Authoring
=========

Intro
-----

Extensions should have the following structure:

```
.
|-- README.rst
|-- azext_*
|   |-- __init__.py
|-- setup.cfg
`-- setup.py
```

The `myexampleextension` directory gives a basic extension with 1 command.

The commands for Command modules and Extensions are authored in the same way. See [Authoring Commands](https://github.com/Azure/azure-cli/blob/master/doc/authoring_command_modules/authoring_commands.md).


Developing
----------

Development of extensions have been simplified by the public release of the azdev CLI. Please visit https://github.com/Azure/azure-cli-dev-tools for more information.

1. In a new virtual environment, install the azdev tool with `pip install azdev`
2. Setup your CLI and install your extension:
  - If you are only developing your extension run: `azdev setup -r <PATH> -e <NAME>` where PATH is the path to the local git folder your extension resides in and NAME is the name of your extension.
  - If you would like to develop for a CLI module and your extension, run the above, but include `-c [<CLI_PATH>]` where CLI_PATH is the path to your local Azure CLI repo. If omitted, the command will attempt to find the repo.

Building
--------

Change directory to the source directory of your extension and build the package.

```
cd ~/Dev/myexampleextension
python setup.py bdist_wheel
```

This will create a `dist` directory containing your `.whl` extension.

The `.whl` is the artifact that can be installed with the `az extension add` command.


Trying out your extension
-------------------------

**(Step 1)** Make sure that you aren't using the dev extension.

```
azdev extension remove myexampleextension
```

Verify it is removed:
```
az extension list -ojson
[]
```

**(Step 2)** Add the extension using the path to the `.whl`:

```
az extension add --source ~/Dev/myexampleextension/dist/FILENAME.whl
```

You can verify the extension was installed as follows:

```
az extension list -ojson
[
  {
    "extensionType": "whl",
    "name": "myexampleextension",
    "version": "0.0.1"
  }
]
```

Extension Metadata (optional)
-----------------------------

Additional metadata can be added to your extension.

See [Extension Metadata](metadata.md) for more information.


Tips/Notes
----------

### What can I import in my extension?

- You can import any of the modules available inside of azure-cli-core.
- You can also import any of its dependencies (see [azure-cli-core setup.py](https://github.com/Azure/azure-cli/blob/master/src/azure-cli-core/setup.py)).
- You can choose to add your own dependencies if required but keep the next point in mind...

### Limit dependencies in setup.py

- Before adding a dependency to your setup.py, check that it's not already available in [azure-cli-core setup.py](https://github.com/Azure/azure-cli/blob/master/src/azure-cli-core/setup.py).
- For Azure SDKs, use autorest to generate your SDK into a package that isn't under the `azure` directory.
- You can verify that your extension doesn't use the `azure` directory by opening your `.whl` and opening the `top_level.txt` file in the `*.dist-info` directory. It should not contain `azure`.

### How do I know I'm using my dev extension(s)?

- When you run `az --version` it will list your normal extensions directory as well as any directories being used to find developer extensions. Developer extensions will appear in the output with a path next to the version number.

### Test your extension on both Python 2 & 3

- The CLI supports both Python 2 & 3 so verify that your extension does the same.
- You can create both a Python 2 and 3 virtual environment and run your extension in both.
- e.g. `virtualenv env27` and `virtualenv -p /usr/local/bin/python3 env`.


:zap: IMPORTANT :zap:
- Since azure-cli uses the `azure` directory, no extension can use this.
- This applies to all other dependencies used by azure-cli-core.
- See [this Stack Overflow question](https://stackoverflow.com/questions/8936884/python-import-path-packages-with-the-same-name-in-different-folders).


Also, see the [FAQ](faq.md).

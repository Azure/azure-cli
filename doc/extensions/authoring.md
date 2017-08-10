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

**(Step 1)** Set the `AZURE_EXTENSION_DIR` environment variable to a directory that will hold the extension(s) being developed:

```
export AZURE_EXTENSION_DIR=~/.azure/devcliextensions
```

The CLI will now look in this directory for extensions.

**(Step 2)** Install your extension into the extensions directory:

```
pip install --upgrade --target ~/.azure/devcliextensions/myexampleextension ~/Dev/myexampleextension
```

- `~/.azure/devcliextensions/myexampleextension` is the directory `pip` will install the extension to. Notice that this value is `AZURE_EXTENSION_DIR` concatenated with the name of the extension.
- `~/Dev/myexampleextension` is the directory with the source code of your extension. One of the files in this directory would be your `setup.py`.

- The above two directories are *examples*. You can choose any directory you want. Just use the appropriate directories throughout when following this document.

**(Step 3)** Continue to develop your extension:

Any time you make changes to your extension and want to see them reflected in the CLI, run the command from step 2 again.


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

**(Step 1)** Make sure that you aren't using the dev extension directory.

One way to do this is to unset the `AZURE_EXTENSION_DIR` environment variable:

```
unset AZURE_EXTENSION_DIR
```

You can verify that you're in a clean state as no extensions should be listed:

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

- The debug log, `--debug`, prints the extension directory currently in use.
- Use that if you aren't sure which extension directory the CLI is currently using.


### Test your extension on both Python 2 & 3

- The CLI supports both Python 2 & 3 so verify that your extension does the same.
- You can create both a Python 2 and 3 virtual environment and run your extension in both.
- e.g. `virtualenv env27` and `virtualenv -p /usr/local/bin/python3 env`.


:zap: IMPORTANT :zap:
- Since azure-cli uses the `azure` directory, no extension can use this.
- This applies to all other dependencies used by azure-cli-core.
- See [this Stack Overflow question](https://stackoverflow.com/questions/8936884/python-import-path-packages-with-the-same-name-in-different-folders).


Also, see the [FAQ](faq.md).

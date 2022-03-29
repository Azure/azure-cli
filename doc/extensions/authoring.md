# Authoring

The commands for Command modules and Extensions are authored in the same way. See [Authoring Commands](https://github.com/Azure/azure-cli/blob/master/doc/authoring_command_modules/authoring_commands.md) for authoring guidance.

## Common Flows

This represents the most common sequence of steps you would perform to create, test and publish your extension.

### Setup

Development of extensions have been simplified by the public release of the azdev CLI. Please visit https://github.com/Azure/azure-cli-dev-tools for more information.

1. In a new virtual environment, install azdev: `pip install azdev`
2. Setup your Azure CLI and install your extension:
  - If you prefer to be guided via an interactive experience, just run `azdev setup` with no additional arguments.
  - If you are creating a brand new extension, run `azdev setup -r <PATH>` to add the repo to your extension dev sources. From there you can run `azdev extension create` to generate and install starter code.
  - If you are only developing on an existing extension, run: `azdev setup -r <PATH> -e <NAME>` where PATH is the path to the local git folder your extension resides in and NAME is the name of your extension. If you don't know the name of the extension, you can omit `-e` to complete the setup. Then you can run `azdev extension list -o table` to see which extensions are installable for your repo and add that extension with `azdev extension add <NAME>`.
  - If you would like to develop for an Azure CLI module and your extension, run the above, but include `-c [<CLI_PATH>]` where CLI_PATH is the path to your local Azure CLI repo. If omitted, the command will attempt to find the repo by crawling your current working directory.

### Create

Run `azdev extension create <NAME>` to create skeleton code for a new extension. As an example (for a fictional widget API):

```azurecli
azdev extension create widget --local-sdk <PATH TO SDK ZIP> --operation-name WidgetOperations --client-name WidgetManagementClient --sdk-property widget_name --github-alias myalias
```

The fields `--operation-name`, `--client-name` and `--sdk-property` will come from a review of your Python SDK.

After running `azdev extension create`, your extension should be installed in dev mode and you should be set to begin developing.

### Validate

Periodically run the following to ensure your extension will pass CI:

`azdev style <NAME>`
`azdev test <NAME>`
`azdev linter <NAME>`

Address comments as appropriate and consult the Azure CLI team if something is unclear.

### Publish

**For the extension whose source code is hosted in [Azure/azure-cli-extensions](https://github.com/Azure/azure-cli-extensionsb)**, we will release for you once your code is merged into `master` branch. You must not update [index.json](https://github.com/Azure/azure-cli-extensions/blob/master/src/index.json) manually in this case.

We detect Python package version via `python setup.py --version`. Only when the version is upgraded, the release process is triggered to help you build and upload the extension WHL file, then update the `index.json` automatically. Subsequently, a PR with newer extension info will be created to update `index.json`, we will merge it once CI passes. Then, the new extension is published.

**For the extension that source code is not hosted in [Azure/azure-cli-extensions](https://github.com/Azure/azure-cli-extensionsb)**, you need to build and upload the WHL file to a public location and optionally advertise the new extension in the repo's index.json file for discoverability. For public extensions that are published to a storage account, the following command will accomplish all of this.

`azdev extension publish <NAME> --update-index [--storage-account NAME --storage-container NAME --storage-subscription GUID]`

The storage fields can be stored in your config file or as environment variables so you need not supply them every time. Once the publish command has been run (you must be logged in to the Azure CLI for it to succeed), you can open a PR that will contain your code changes and the index update. This used to be done in two steps.

Once your extension is published, you can view it via `az extension list-avaliable -o table`.

However, if you want your extension to be listed in [Official Available Extensions for Azure CLI](https://docs.microsoft.com/cli/azure/azure-cli-extensions-list), you have to wait until the next [Azure CLI release](https://github.com/Azure/azure-cli/milestones). We update that document every time Azure CLI is released. Alternatively, you could file a PR to update it manually if it's urgent.

## Uncommon Flows

These are operations you may never need to do, or only do occasionally.

### Building

`azdev extension build <NAME>`

This will create a `dist` directory containing your `.whl` extension.

The `.whl` is the artifact that can be installed with the `az extension add` command. You will rarely need to use this command, however. Instead, you will most likely use the publish command.

### Trying out your extension

Normally, you will have you extension installed in dev mode and your code changes will be immediately testable. However, if you want to test a generated WHL file specifically, follow these directions.

**(Step 1)** Build the extension to generate a WHL file.

`azdev extension build myexampleextesion`

**(Step 2)** Uninstall the dev extension.

`azdev extension remove myexampleextension`

Verify it is removed:

```azurecli
az extension list -ojson
[]
```

**(Step 3)** Add the extension using the path to the `.whl`:

`az extension add --source ~/Dev/myexampleextension/dist/FILENAME.whl`

You can verify the extension was installed as follows:

```azurecli
az extension list -ojson
[
  {
    "extensionType": "whl",
    "name": "myexampleextension",
    "version": "0.0.1"
  }
]
```

## Extension Metadata (optional)

Additional metadata can be added to your extension.

See [Extension Metadata](metadata.md) for more information.


## Tips/Notes

### What can I import in my extension?

- You can import any of the modules available inside of azure-cli-core.
- You can also import any of its dependencies (see [azure-cli-core setup.py](https://github.com/Azure/azure-cli/blob/master/src/azure-cli-core/setup.py)).
- You can choose to add your own dependencies if required but keep the next point in mind...

### Limit dependencies in setup.py

- Before adding a dependency to your setup.py, check that it's not already available in [azure-cli-core setup.py](https://github.com/Azure/azure-cli/blob/master/src/azure-cli-core/setup.py).
- Azure SDK or Azure Management SDK dependencies may be overridden by the versions installed as requirements of azure-cli-core. If you use any, test carefully, gracefully handle API changes, and be prepared to release updates. You might also consider rebasing the libraries under a different namespace (besides `azure`) to avoid conflicting with core Azure CLI functionality. You can use [autorest](https://github.com/azure/autorest) to generate your SDK into a package that isn't under the `azure` directory.

### How do I know I'm using my dev extension(s)?

- When you run `az --version` it will list your normal extensions directory as well as any directories being used to find developer extensions. Developer extensions will appear in the output with a path next to the version number.

### Test your extension on Python 3

- The Azure CLI supports Python 3.6, 3.7, 3.8 so verify that your extension does the same.
- You can create virtual environments for different versions and run your extension in them.
- e.g. `python3.6 -m venv env36` and `python3.8 -m venv env38`.


Also, see the [FAQ](faq.md).

### Differences between hosting and not hosting source code in Azure/azure-cli-extensions

An advantage of hosting extension in [Azure/azure-cli-extensions](https://github.com/Azure/azure-cli-extensions) is that you could save the time to repeatedly build and upload the WHL file to pass CI checks.

As for hosting outside, you could easily provide a direct and explicit entry to end users with your customized introduction page, like [Azure DevOps Extension for Azure CLI](https://github.com/Azure/azure-devops-cli-extension), which is fit to popularize your Azure CLI extension if you plan to.
Otherwise, users have to go deeper to find the detailed page in Azure/azure-cli-extensions, such as `src/azure-firewall`, `src/vm-repair`.

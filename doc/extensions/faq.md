FAQ
===

### Do extensions have to start with `azure-cli-`?

- No.
- Unlike command modules, extensions can be named as you like.


### Can I depend on the order extensions are loaded?

- No.
- Therefore, extensions can't be dependent on other extensions.

### How do I specify which versions of the CLI my extension works with?

- See [Extension Metadata](metadata.md).

### How do I build my Autorest-based Azure SDK to be compatible with extensions?

- Specify the namespace when generating your SDK.
- The namespace should not be under `azure.*`.
- Choose a name that's unlikely to conflict with another extension also.

### How do I move from an extension to a command module?

- Move your `__init__.py` file (and other files) from `azext_*` to `azure.cli.command_modules.MODNAME`.
- Add a dependency on `azure-cli-core` to your `setup.py`.
- Rename your package to start with `azure-cli-*`.
- If you rely on an Azure autorest SDK, release the SDK at [azure-sdk-for-python](https://github.com/Azure/azure-sdk-for-python) and add it as a dependency.
- Create a PR to [Azure/azure-cli](https://github.com/Azure/azure-cli/).

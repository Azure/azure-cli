Extension Documentation
=======================


What is an Extension?
---------------------

> An extension adds/modifies/removes commands that are part of `az` and can be optionally installed by the user.

- Extensions are supported through all installation methods.
- Extensions are the way to go to release private/public previews of your Azure CLI commands.
- Currently, we support one extension type, a [Python Wheel](http://pythonwheels.com/).
- All extension documentation here refers to this type of extension.


What an Extension is not
------------------------

- An extension is not an external executable or product outside of `az`.

- If you're looking to create a command module which is installed by default for `az`, see [authoring command modules](https://github.com/Azure/azure-cli/tree/master/doc/authoring_command_modules).

- If you're looking to build your own CLI using `az` patterns, see [knack](https://github.com/Microsoft/knack).


How to find and install an Extension
------------------------

- List all available extensions: `az extension list-available`

- Install an extension: `az extension install --name <extension-name>`

More details on usage in [Extensions for Azure CLI 2.0](https://docs.microsoft.com/cli/azure/azure-cli-extensions-overview#install-extensions)


Doc Sections
------------

- [Authoring](authoring.md) - How to author, develop and publish an extension

- [Command Guidelines](../command_guidelines.md) - Command Guidelines

- [Summary Guidelines](extension_summary_guidelines.md) - Summary guidelines for extensions to be published

- [Extension Metadata](metadata.md) - How to add additional extension metadata

- [FAQ](faq.md) - Commonly asked questions

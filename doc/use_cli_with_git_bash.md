# Use Azure CLI with Git Bash

## Introduction
The MSI package for Windows now contains an entry script for running `az` on Git Bash. You can directly call `az` on Git Bash now. While using Git Bash on Windows gives you a similar experience on a Linux shell, it has some unexpected issues that impact the user experience of Azure CLI.

## Issues

### Auto-translation of Resource IDs

On Git Bash, if you specify command-line options starting with a slash, POSIX-to-Windows path conversion will kick in. This causes an issue for passing ARM Resource IDs, like:
```
$ az vm show --ids "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm"

invalid resource ID: C:/Program Files/Git/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm
```
To disable the path conversion. You can set enviroment variable `MSYS_NO_PATHCONV=1` or set it temporarily when a running command:
```
$ MSYS_NO_PATHCONV=1 az vm show --ids "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm"
```

More discussions [here](https://stackoverflow.com/questions/7250130/how-to-stop-mingw-and-msys-from-mangling-path-names-given-at-the-command-line#34386471).

### Quoting Issues
If you install Azure CLI with `pip install`, the double quotes will be stripped in the value and cause trouble when there are spaces inside the quotes since Git Bash will treat each parts separated by spaces as an invividual command option.
```
$ az find "vm create"
$ Command arguments: ['find', 'vm', 'create', '--debug']
...
az: error: unrecognized arguments: create
...
```
You can wrap the value with additional single quotes to avoid the issue:
```
$ az find '"vm create"' --debug
$ Command arguments: ['find', 'vm create', '--debug']
...
```
We do recommend to use MSI to install Azure CLI on Windows when it's possible.

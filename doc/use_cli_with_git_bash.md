# Use Azure CLI with Git Bash

## Introduction
The MSI package for Windows now contains an [az entry script](https://github.com/Azure/azure-cli/blob/dev/build_scripts/windows/scripts/az) for running `az` on Git Bash. You can directly call `az` on Git Bash now. While using Git Bash on Windows gives you a similar experience on a Linux shell, it has some unexpected issues that impact the user experience of Azure CLI. 

We do not recommend to use `az` installed through `pip install azure-cli` on Git Bash as that [az entry script](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/az) was meant to be run on Linux and have even more issues when running on Git Bash on Windows.  

## Issues

### Auto-translation of Resource IDs

On Git Bash, if you specify command-line options starting with a slash, POSIX-to-Windows path conversion will kick in. This causes an issue for passing ARM Resource IDs, like:

```azurecli
$ az vm show --ids "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm"

invalid resource ID: C:/Program Files/Git/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm
```

To disable the path conversion. You can set environment variable `MSYS_NO_PATHCONV=1` or set it temporarily when a running command:

```azurecli
$ MSYS_NO_PATHCONV=1 az vm show --ids "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Compute/virtualMachines/my-vm"
```

More discussions [here](https://stackoverflow.com/questions/7250130/how-to-stop-mingw-and-msys-from-mangling-path-names-given-at-the-command-line#34386471).

### Issues with pip-installed az

#### Quoting Issues
The double quotes will be stripped in the value and cause trouble when there are spaces inside the quotes since Git Bash will treat each parts separated by spaces as an individual command option.

```azurecli
$ az find "vm create"
$ Command arguments: ['find', 'vm', 'create', '--debug']
...
az: error: unrecognized arguments: create
...
```

You can wrap the value with additional single quotes to avoid the issue:

```azurecli
$ az find '"vm create"' --debug
$ Command arguments: ['find', 'vm create', '--debug']
...
```

#### Entry script exits before command finishes
The [entry script](https://github.com/Azure/azure-cli/blob/dev/src/azure-cli/az) exits once `os.execl()` is called. It does not wait for the actual command to finish.

According to [_exec, _wexec Functions](https://docs.microsoft.com/en-us/cpp/c-runtime-library/exec-wexec-functions?view=vs-2019), `os.exec` internally uses [CreateProcess](https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw) which doesn't wait for the sub-process.

#### Exit Code is 0 even when the command fails
Related to the above issue, Windows creates a new process and exits the current one with `os.exec`. Hence the calling program only sees that the script has terminated without an issue (See [Issue9148: os.execve puts process to background on windows](https://bugs.python.org/issue9148#msg109179)). The exit code does not reflect the actual result of the command execution in the new process.

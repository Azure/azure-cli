# Migrating from Azure classic CLI to Azure CLI

If you still use the original Azure classic CLI for your scripts and deployments,
you should consider switching to the new Azure CLI. Azure CLI is designed
for working with the Resource Manager deployment style, while Azure classic CLI
is recommended for only the classic (Azure Service Manager) deployment.

If you are ready to switch, please consider the following before starting:

* Both Azure CLIs can be installed and used side-by-side
* The Azure CLI will not support ASM/Classic mode services
* Scripts are not compatible between both CLIs

## Why switch?

The major reason to switch is that Azure classic CLI is currently only planned
to have support through the end of 2018. The new Azure CLI also offers the following
benefits:

* Clean outputs for common workflows
  * `--out table` for simplified human output
  * `--out json` and `--out jsonc` for JSON outputs
  * `--out tsv` for interacting with tools like grep, AWK, and jq
* Improved and consistent in-tool documentation with `-h`
  * Includes descriptions for groups, commands, and parameters
  * Indicates where to look up required values
  * Examples and links to web content
* Improved command-line productivity
  * Use `[tab][tab]` to lookup parameters, including resource groups and names (only supported in BASH and BASH on Windows)
  * Work with either Azure resource ID values (`--ids`) _or_ resource group and name (`-g -n`)
  * Built in client-side query engine powered by JMESPath

While we believe the above list is compelling, it's important to remember
**the Azure CLI only supports ARM mode**.  If you are managing ASM/Classic 
resources, you must use the Azure classic CLI.

## Getting both CLIs set up side-by-side

First, run `azure --version` and ensure you are using `0.10.5` or later, as
this is required for sharing your credentials between both CLIs.  If you installed
using NPM, upgrade with `npm upgrade -g azure-cli`.  If you used an installer,
we recommend downloading the latest installer to upgrade.

To install the latest Azure CLI, follow the steps for your preferred platform or
environment in our [Installation Guide](https://docs.microsoft.com/cli/azure/install-azure-cli).

Once installed, you run `az configure` and follow the steps to setup your default output format.  

Then run `az login` to login using device authentication.  Once this step is complete you should be authenticated to use both CLIs.  

## Important new concepts in the Azure CLI

Here is a quick list of some new and changed concepts that can help you understand the new tool.

* Interactive Concepts
  * Use `az configure` to setup your default output format
  * You will find help to be generally more useful, try `az vm create -h` for an example
  * Positional parameters are not supported, use `az vm list -g MyGroup` instead of `azure vm list MyGroup`
* Automation and Scripting Concepts
  * You can refer to resources using their Azure resource ID with `--ids` or with the resource group and name using `-g [rg] -n [name]`
  * Use `--query "[expression]"` to extract single values
  * Use `--out tsv` to get plain (no mark-up) value output
  * Use `@-` to pipe values such as `az vm list --query [0].[id] --out tsv | az vm show --ids @-`
* Service Specific Concepts
  * VM power state is no longer included in `az vm list`, use `az vm get-instance-view` instead

## Moving scripts from Azure classic CLI to Azure CLI 

Generally, converting a script from Azure classic CLI to Azure CLI follows these steps:

1. Switch `azure` commands to `az` commands
2. Update commands to use new input values
3. Update script to use new output formats
4. Use `--query` to extract values reliably

Below, we break down each of these steps.

### Finding and switching to `az` commands

While most commands keep the same group and command names between the Azure classic CLI and the latest Azure CLI, we've built a
[azure to az conversion table](https://github.com/Azure/azure-cli/blob/master/doc/azure2az_commands.rst) for common commands.

#### Set vs. Update

Mutate operations now use the `update` verb instead of `set`.  While the classic CLI
exposed some common operations as parameters, such as:

```azurecli
$ azure vm set -g MyGroup -n MyName --nic-ids $MyNicID
$ azure vm set -g MyGroup -n MyName --tags myTagName=MyTagValue
```

The Azure CLI `update` commands work generically against the resource, for example:

```azurecli
$ az vm update -g MyGroup -n MyName --add networkProfile.networkInterfaces primary=false id=$MyNicID
$ az vm update -g MyGroup -n MyName --set tags.myTagName=MyTagValue
```

#### Commands with complex input

Some commands which required complex input, such as JSON strings and documents,
have been changed to add/remove single values, instead of requiring users to
pull down the document, modify, and set the new document.  For these commands,
see help (`-h`) for details on the specific command.

An example of this is `azure storage cors set` being replaced by `az storage cors add`.

### Updating input values

Once you have identified the `az` commands required for your script, you immediately
notice changes to how inputs are handled.  The Azure CLI does not accept
'positional parameters' such as `azure vm show MyRG MyName`, but instead requires
parameter flags: `az vm show -g MyRG -n MyName`.  

In addition, when an input value is missing, we will show an error indicating the
missing parameters, instead of prompting the user automatically:

```azurecli
$ az vm show
az vm show: error: (--name --resource-group | --ids) are required
```

In addition to using resource groups and names (`-g`, `-n`), you can also refer to
resources directly by ID value using `--ids`:

```bash
$ MyVar=$(az vm list --query [0].id --out tsv)
$ echo $MyVar
/subscriptions/xxxx/resourceGroups/VMGROUP1/providers/Microsoft.Compute/virtualMachines/VM-Data
$ az vm show --ids $MyVar --out table
ResourceGroup    Name     VmId                                  Location    ProvisioningState
---------------  -------  ------------------------------------  ----------  -------------------
VMGROUP1         VM-Data  63edd6a0-2796-49e6-acc1-ad3f8bd94f13  westus      Succeeded
```

When working with files, you can use the `@` symbol to indicate the contents of a file or file descriptor.

```azurecli
$ az role create --role-definition @MyOnCallRoleDef.json
```

> **TIP** Use `@-` as short-hand to pass STDIN as a value. 

### Working with output formats

The Azure CLI supports 4 primary output formats:

1. json  - standard JSON formatted object graphs
2. jsonc - colorized JSON
3. tsv   - provides "UNIX-style" output (fields delimited with tabs, records with newlines)
4. table - simplified human-readable output

You can set your default output format with the `az configure` command or on a
by-command basis using `--out` parameter.  

Tips:
* Use `--out tsv` for raw output that is easy to parse with command-line tools
* Use `--out json` for outputting object graphs (nested objects), both `tsv` and `table` will only show fields from the outer-most object.
* Avoid using `--out jsonc` output programmatically as not all tools will accept the ANSI values that provide color in the Shell
* Currently, `--out table` does not work with some formatted outputs.

```azurecli
$ az vm list --query [0].name --out json
"VM-Data"
$ az vm list --query [0].name --out tsv
VM-Data
$ az vm list --query [0].name --out table
Result
--------
VM-Data
```

### Filtering down output values

A common pattern in Azure classic CLI scripts is using command-line tools, such as
AWK, grep, and jq, to extract values from output documents:

```azurecli
$ azure vm list --json \
     | jq -r '.[].storageProfile.osDisk.vhd.uri' \
     | cut -d / -f3 \
     | cut -d . -f1 \
     | uniq -c \
     | sort -bgr

$ MY_SUBSCRIPTION_ID=$(azure account show --json | jq -r '.[0].id')
```

With the Azure CLI, you can now use the `--query '[expression]'` parameter and the [JMESPath](http://jmespath.org/)
query language to extract values.

```azurecli
$ az vm list --query "[].{name:name,os:storageProfile.osDisk.osType}" --out table
Name           Os
-------------  -------
VM-Data        Windows
VM-StagingWeb  Linux
VM-Web         Linux
MyNewVM        Linux

$ az vm list --query "[].{name:name,os:storageProfile.osDisk.osType}" --out tsv
VM-Data	Windows
VM-StagingWeb	Linux
VM-Web	Linux
MyNewVM	Linux

$ az vm list --query "[].{name:name,os:storageProfile.osDisk.osType}" --out json
[
  {
    "name": "VM-Data",
    "os": "Windows"
  },
  {
    "name": "VM-StagingWeb",
    "os": "Linux"
  },
  {
    "name": "VM-Web",
    "os": "Linux"
  },
  {
    "name": "MyNewVM",
    "os": "Linux"
  }
]
```

You can also extract single values.  Using `--out tsv` will prevent any unintended quotes:

```azurecli
az vm list --query "[0].id" --out tsv
/subscriptions/xxxx/resourceGroups/VMGROUP1/providers/Microsoft.Compute/virtualMachines/VM-Web
```

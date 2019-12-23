# Tips for using Azure CLI effectively #

For clarity, Bash scripts are used inline. Windows batch or PowerScript examples are listed in the appendix, which you can use to build similar examples.

## Use the right output mode for your work (json, table, or tsv) ##

1. `json` format is the CLI's default, and is intended to give you the most comprehensive information. If you prefer a different format, use the `--output` argument to override for an individual command invocation, or use `az configure` to update your global default. Note that JSON format preserves the double quotes, generally making in unsuitable for scripting purposes.

2. `table` is useful for getting a summary of focused information, particularly for list commands. If you do not like the fields in the default table format (or there isn't a default format), you can use `--output json` to see all information, or leverage `--query` to specify a format you like.

    ```sh
    az vm show -g my_rg -n my_vm --query "{name: name, os:storageProfile.imageReference.offer}" -otable
    Name    Os
    ------  ------------
    my_vm   UbuntuServer
    ```

3. `tsv` is useful for concise output and scripting purposes. The tsv will strip double quotes that the JSON format preserves. To specify the format you want for TSV, use the `--query` argument.

    ```sh
    export vm_ids=$(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
    az vm stop --ids $vm_ids
    ```

## Passing values from one command to the other ##

1. If the value will be used more than once, assign it to a variable. Note the use of `-o tsv` in the following example:

    ```sh
    running_vm_ids=$(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
    ```
2. If the value is used only once, consider piping:
    ```sh
    az vm list --query "[?powerState=='VM running'].name" | grep my_vm
    ```
3. For lists consider the following suggestions:

   If you need more controls on the result, use "for" loop:
    ```sh
    #!/usr/bin/env bash
    for vm in $(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv); do
        echo stopping $vm
        az vm stop --ids $vm
        if [ $? -ne 0 ]; then
            echo "Failed to stop $vm"
            exit 1
        fi
        echo $vm stopped
    done
    ```

    Alternatively, use `xargs` and consider using the `-P` flag to run the operations in parallel for improved performance:
    ```sh
    az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | xargs -I {} -P 10 az vm start --ids "{}"
    ```
    Finally, Azure CLI has built-in support to process commands with multiple `--ids` in parallel to achieve the same effect of xargs. Note that `@-` is used to get values from the pipe:
    ```sh
    az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | az vm start --ids @-
    ```

## Async Operations ##

Many commands and group expose `--no-wait` flags on their long-running operations as well as a dedicated `wait` command. These become handy for certain scenarios:

1. Cleaning up resources when you aren't relying on the clean up for some subsequent operation, such as deleting a resource group:
    ```sh
    az group delete -n my_rg --no-wait
    ```
2. When you want to create multiple independent resources in parallel. This is similar to creating and joining threads:

    ```sh
    az vm create -g my_rg -n vm1 --image centos --no-wait
    az vm create -g my_rg -n vm2 --image centos --no-wait

    subscription=$(az account show --query "id" -otsv)
    vm1_id="/subscriptions/$subscription/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/vm1"
    vm2_id="/subscriptions/$subscription/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/vm2"
    az vm wait --created --ids $vm1_id $vm2_id
    ```

## Using the Generic Update Arguments ##
Most update commands in the CLI feature the three generic arguments: `--add`, `--set` and `--remove`. These arguments are powerful but often less convenient than the strongly-typed arguments typically featured in update commands. The CLI provides strongly-typed arguments for most common scenarios for ease-of-use, but if the property you want to set isn't listed, the generic update arguments will often present a path forward to unblock you without having to wait for a new release.

1. The generic update syntax isn't the most user friendly, so it will require some patience.
2. Verify whether the update command has the `Generic Update Arguments` group exposed. If not, you'll need to file an issue, but if they are you can attempt you scenario using them.
3. Use the `show` command on the resource you are interested in to figure out what path you should supply in the generic arguments. For example, before you try out `az vm update`, run `az vm show` to determine the right path. Generally, you will use dot syntax to access dictionary properties and brackets to index into lists.
4. Check out working examples to get started. `az vm update -h` has good ones.
5. `--set` and `--add` take a list of key value pairs in the format of `<key1>=<value1> <key2>=<value2>`. Use them to construct non- trivial payloads. If the syntax gets too message, consider using a JSON string. For example, to attach a new data disk to a VM:
    ```sh
    az vm update -g my_rg -n my_vm --add storageProfile.dataDisks "{\"createOption\": \"Attach\", \"managedDisk\": {\"id\": \"/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/yg/providers/Microsoft.Compute/disks/yg-disk\"}, \"lun\": 1}"
    ```
6. You may find it more useful to leverage the CLI's `@{file}` convention, putting the JSON into a file and loading it. This simplifies the above command to:
    ```sh
    az vm update -g my_rg -n my_vm --add storageProfile.dataDisks @~/my_disk.json
    ```

## Quoting Issues ##

This becomes an issue because when the command shell (bash, zsh, Windows Command Prompt, PowerShell etc) parses the CLI command, it will interpret the quotes. To avoid surprises, here are a few suggestions:

1. If the value contains whitespace, you must wrap it in quotes.
2. In bash or Windows PowerShell, both single and double quotes will be interpreted, while in Windows Command Prompt, only double quotes are handled which means single quotes will be interpreted as a part of the value.
3. If your command only runs on bash (or zsh), using single quotes has the benefit of preserving the content inside. This can be very helpful when supplying inline JSON. For example this works in bash: `'{"foo": "bar"}'`
4. If your command will run on Windows Command Prompt, you must use double quotes exclusively. If the value contains double quotes, you must escape it: "i like to use \\" a lot". The Command Prompt equivalent of the above would be: `"{\"foo\": \"bar\"}"`
5. Exported variables in bash inside double quotes will be evaluated. If this is not what you want, again use \\ to escape it like `"\\$var"` or use single quotes `'$var'`.
6. A few CLI arguments, including the generic update arguments, take a list of space-separated values, like `<key1>=<value1> <key2>=<value2>`. Since the key name and value can take arbitrary string which might contain whitespace, using quotes will be necessary. Wrap the pair, not individual key or value. So `"my name"=john` is wrong. Instead, use `"my name=john"`. For example:
    ```sh
    az webapp config appsettings set -g my_rg -n my_web --settings "client id=id1" "my name=john"
    ```
7. Use CLI's `@<file>` convention to load from a file so to bypass the shell's intepretion mechanisms:
    ```sh
    az ad app create --display-name my-native --native-app --required-resource-accesses @manifest.json
    ```
8. When a CLI argument says it accepts a space-separated list, these are the formats accepted:
    - `--arg foo bar`: OK. Unquoted, space-separated list
    - `--arg "foo" "bar"`: OK: Quoted, space-separated list
    - `--arg "foo bar"`: BAD. This is a string with a space in it, not a space-separated list.
9. When running Azure CLI commands in PowerShell, parsing errors will occur when the arguments contain special characters of PowerShell, such as at `@`. You can solve this problem by adding `` ` `` before the special character to escape it, or by enclosing the argument with single or double quotes `'`/`"`. For example, `az group deployment create --parameters @parameters.json` dose't work in PowerShell because `@` is parsed as a [splatting symbol](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_splatting). To fix this, you may change the argument to `` `@parameters.json`` or `'@parameters.json'`. 
10. On Windows, `az` is a batch script (at `C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd`). When there is no space in an argument, PowerShell will strip the quotes and pass the argument to Command Prompt. This causes the argument to be parsed again by Command Prompt. For example, when running `az "a&b"` in PowerShell, `b` is treated as a separate command instead of part of the argument like Command Prompt does, because quotes are removed by PowerShell and the ampersand `&` is parsed again by Command Prompt as a [command separator](https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-xp/bb490954(v=technet.10)#using-multiple-commands-and-conditional-processing-symbols). 
     
    To prevent this, you may use [stop-parsing symbol](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing) `--%` between `az` and arguments like `az --% vm create ...`. This can also solve the above-mentioned special character issue and is recommended whenever any issue happens when invoking a batch script from PowerShell.
     
    > The stop-parsing symbol (--%), introduced in PowerShell 3.0, directs PowerShell to refrain from interpreting input as PowerShell commands or expressions.
    >
    > When it encounters a stop-parsing symbol, PowerShell treats the remaining characters in the line as a literal.
     
    This issue is tracked at https://github.com/PowerShell/PowerShell/issues/1995#issuecomment-539822061

## Generic Resource Commands
  There may be cases where a service you are interested in does not have CLI command coverage. You can use the `az resource create/show/list/delete/update/invoke-action` commands to work with these resources. A few suggestions here:
  1. If only `create/update` are involved, consider using `az group deployment create`. Leverage [Azure Quickstart Templates](https://github.com/Azure/azure-quickstart-templates) for working examples.
  2. Check out the Rest API reference for the request payload, URL and API version. As an example, check out the community's comments on [how to create AppInsights](https://github.com/Azure/azure-cli/issues/5543).

## Working behind a proxy
Proxy is common behind corporate network or introduced by tracing tools like Fiddler, mitmproxy, etc. If the proxy uses self-signed certificates, the Python [Requests](https://github.com/kennethreitz/requests) library which CLI uses will throw `SSLError("bad handshake: Error([('SSL routines', 'tls_process_server_certificate', 'certificate verify failed')],)",)`. There are 2 ways to handle this error:

1. Set environment variable `REQUESTS_CA_BUNDLE` to the path of CA bundle certificate file in PEM format. This is recommended if you use CLI frequently behind a corporate proxy. The default CA bundle which CLI uses is located at `C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\Lib\site-packages\certifi\cacert.pem` on Windows and ` /opt/az/lib/python3.6/site-packages/certifi/cacert.pem` on Linux. You may append the proxy server's certificate to this file or copy the contents to another certificate file, then set `REQUESTS_CA_BUNDLE` to it. For example:

    ```
    <Original cacert.pem>

    -----BEGIN CERTIFICATE-----
    <Your proxy's certificate here>
    -----END CERTIFICATE-----
    ```

   A frequent ask is whether or not `HTTP_PROXY` or `HTTPS_PROXY` environment variables should be set, the answer is it depends. For Fiddler on Windows, by default it acts as system proxy on start, you don't need to set anything. If the option is off or using other tools which don't work as system proxy, you should set them. Since almost all traffic from CLI is SSL-based, only `HTTPS_PROXY` should be set. If you are not sure, just set them, but do remember to unset it after the proxy is shut down. For fiddler, the default value is `http://localhost:8888`.

   For other details, check out [Stefan's blog](https://blog.jhnr.ch/2018/05/16/working-with-azure-cli-behind-ssl-intercepting-proxy-server/).

2. Disable the certificate check across Azure CLI by setting environment variable `AZURE_CLI_DISABLE_CONNECTION_VERIFICATION=1`. This is not safe, but good for a short period like capturing a network trace for a specific command and promptly turning it off when finished. This may not work for some data-plane commands due to underlying SDK limitations.

## Concurrent builds

If you are using az on a build machine, and multiple jobs can be run in parallel, then there is a risk that the login tokens are shared between two build jobs is the jobs run as the same OS user.  To avoid mix ups like this, set AZURE_CONFIG_DIR to a directory where the login tokens should be stored.  It could be a randomly created folder, or just the name of the jenkins workspace, like this ```AZURE_CONFIG_DIR=.```

## Appendix
### Windows batch scripts for saving to variables and using it later
```batch
ECHO OFF
SETLOCAL
FOR /F "tokens=* USEBACKQ" %%F IN (`az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv`) DO (
    SET "vm_ids=%%F %vm_ids%"  :: construct the id list
)
az vm stop --ids %vm_ids% :: CLI stops all VMs in parallel
```

### Windows PowerShell scripts for saving to variables and using it later

```powershell
$vm_ids=(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
az vm stop --ids $vm_ids # CLI stops all VMs in parallel
```

### Windows batch scripts to loop through a list
```batch
ECHO OFF
SETLOCAL
FOR /F "tokens=* USEBACKQ" %%F IN (`az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv`) DO (
    ECHO Stopping %%F
    az vm stop --ids %%F
)
```

### Windows PowerShell scripts to loop through a list
```powershell
$vm_ids=(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
foreach ($vm_id in $vm_ids) {
    Write-Output "Stopping $vm_id"
    az vm stop --ids $vm_id
}
```

### CLI Environment Variables

|  Environment Variable          | Description            |
|--------------------------------|------------------------|
| **AZURE_CONFIG_DIR**           | Global config directory for config files, logs and telemetry. If unspecified, defaults to `~/.azure`. |
| **AZURE_EXTENSION_DIR**        | Extensions' installation directory. If unspecified, defaults to `cliextensions` directory within the global config directory. |

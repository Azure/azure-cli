# Tips for using Azure CLI effectively #

For clarity, Bash scripts are used inline. Windows batch or PowerScript examples are listed in the appendix, which you can use to build similiar examples.

## Use the right output mode for your work (json, table, or tsv) ##
  1. `json` format is the CLI's default, and is intended to give you the most comprehensive information. If you prefer a different format, use the `--output` argument to override for an individual command invocation, or use `az configure` to update your global default. Note that JSON format preserves the double quotes, generally making in unsuitable for scripting purposes.
  
  2. `table` is useful for getting a summary of focused information, particularly for list commands. If you do not like the fields in the default table format (or there isn't a default format), you can use `--output json` to see all information, or leverage `--query` to specify a format you like.

         az vm show -g my_rg -n my_vm --query "{name: name, os:storageProfile.imageReference.offer}" -otable
         Name    Os
         ------  ------------
         my_vm   UbuntuServer

  3. `tsv` for concise output and scripting purposes. The will strip double quotes that the JSON format preserves. To specify the format you want for TSV, use the `--query` argument.

         export vm_ids=$(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)  
         az vm stop --ids $vm_ids
        
## Passing values from one command to the other ##
  1. If the value will be used more than once, assign it to a variable. Note the use of `-o tsv` in the following example:
       
         running_vm_ids=$(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
       
  2. If the value is used only once, consider piping:

         az vm list --query "[?powerState=='VM running'].name" | grep my_vm

  3. For lists consider the following suggestions:

       If you need more controls on the result, use "for" loop:
       
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
        
       Alternatively, use `xargs` and consider using the `-P` flag to run the operations in parallel for improved performance:

           az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | xargs -I {} -P 10 az vm start --ids "{}"

       Finally, Azure CLI has built-in support to process commands with multiple `--ids` in parallel to achieve the same effect of xargs. Note that `@-` is used to get values from the pipe:

           az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | az vm start --ids @-

## Async Operations ##
  Many commands and group expose `--no-wait` flags on their long-running operations as well as a dedicated `wait` command. These become handy for certain scenarios:

  1. Cleaning up resources when you aren't relying on the clean up for some subsequent operation, such as deleting a resource group:

          az group delete -n my_rg --no-wait

2. When you want to create multiple independent resources in parallel. This is similar to creating and joining threads:
      
          az vm create -g my_rg -n vm1 --image centos --no-wait
          az vm create -g my_rg -n vm2 --image centos --no-wait

          subscription=$(az account show --query "id" -otsv)
          vm1_id="/subscriptions/$subscription/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/vm1"
          vm2_id="/subscriptions/$subscription/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/vm2"
          az vm wait --created --ids $vm1_id $vm2_id

## Using the Generic Update Arguments ##
  Most update commands in the CLI feature the three generic arguments: `--add`, `--set` and `--remove`. These arguments are powerful but often less convenient than the strongly-typed arguments typically featured in update commands. The CLI provides strongly-typed arguments for most common scenarios for ease-of-use, but if the property you want to set isn't listed, the generic update arguments will often present a path forward to unblock you without having to wait for a new release.

  1. The generic update syntax isn't the most user friendly, so it will require some patience.
  2. Verify whether the update command has the `Generic Update Arguments` group exposed. If not, you'll need to file an issue, but if they are you can attempt you scenario using them.
  3. Use the `show` command on the resource you are interested in to figure out what path you should supply in the generic arguments. For example, before you try out `az vm update`, run `az vm show` to determine the right path. Generally, you will use dot syntax to access dictionary properties and brackets to index into lists.
  4. Check out working examples to get started. `az vm update -h` has good ones.
  5. `--set` and `--add` take a list of key value pairs in the format of `<key1>=<value1> <key2>=<value2>`. Use them to construct non- trivial payloads. If the syntax gets too message, consider using a JSON string. For example, to attach a new data disk to a VM: 

         az vm update -g my_rg -n my_vm --add storageProfile.dataDisks "{\"createOption\": \"Attach\", \"managedDisk\": {\"id\": \"/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/yg/providers/Microsoft.Compute/disks/yg-disk\"}, \"lun\": 1}"

  You may find it more useful to leverage the CLI's `@{file}` convention, putting the JSON into a file and loading it. This simplifies the above command to:

         az vm update -g my_rg -n my_vm --add storageProfile.dataDisks @~/my_disk.json

## Quoting Issues ##
  This becomes an issue because when the command shell (bash, zsh, Windows command prompt, etc) parses the CLI command, it will interpret the quotes. To avoid surprises, here are a few suggestions:
  1. If the value contains whitespace, you must wrap it in quotes.
  2. In bash or Windows PowerShell, both single and double quotes will be intepreted, while in Windows command prompt, only double quotes are handled which means single quotes will be interpreted as a part of the value.
  3. If your command only runs on bash (or zsh), using single quotes has the benefit of preserving the content inside. This can be very helpful when supplying inline JSON. For example this works in bash: `'{"foo": "bar"}'`
  4. If your command will run on Windows command prompt, you must use double quotes exclusively. If the value contains double quotes, you must escape it: "i like to use \\" a lot". The command prompt equivalent of the above would be: `"{\"foo\": \"bar\"}"`
  5. Exported variables in bash inside double quotes will be evaluated. If this is not what you want, again use \\ to escape it like `"\\$var"` or use single quotes `'$var'`. 
  5. A few CLI arguments, including the generic update arguments, take a list of space-separated values, like `<key1>=<value1> <key2>=<value2>`. Since the key name and value can take arbitary string which might contain whitespace, using quotes will be necessary. Wrap the pair, not individual key or value. So `"my name"=john` is wrong. Instead, use `"my name=john"`. For example:
         az webapp config appsettings set -g my_rg -n my_web --settings "client id=id1" "my name=john"
  6. Use CLI's `@<file>` convention to load from a file so to bypass the shell's intepretion mechanisms:
         az ad app create --display-name my-native --native-app --required-resource-accesses @manifest.json
  7. When a CLI argument says it accepts a space-separated list, these are the formats accepted:
     - `--arg foo bar`: OK. Unquoted, space-separated list
     - `--arg "foo" "bar"`: OK: Quoted, space-separated list
     - `--arg "foo bar"`: BAD. This is a string with a space in it, not a space-separated list.

## Generic Resource Commands
  There may be cases where a service you are interested in does not have CLI command coverage. You can use the `az resource create/show/list/delete/update/invoke-action` commands to work with these resources. A few suggestions here:
  1. If only `create/update` are involved, consider using `az group deployment create`. Leverage [Azure Quickstart Templates](https://github.com/Azure/azure-quickstart-templates) for working examples.
  2. Check out the Rest API reference for the request payload, URL and API version. As an examplee, check out the community's comments on [how to create AppInsights](https://github.com/Azure/azure-cli/issues/5543).

## Working behind a proxy
  Proxy is common behind corporate network or introduced by tracing tools like fiddler, mitmproxy, etc. If the proxy uses self-signed certificates, the Python [requests library](https://github.com/kennethreitz/requests) which CLI depends on will throw `SSLError("bad handshake: Error([('SSL routines', 'tls_process_server_certificate', 'certificate verify failed')],)",)`.  There are 2 ways to handle this error:
  1. Disable the certificate check across the CLI by setting the env var of `AZURE_CLI_DISABLE_CONNECTION_VERIFICATION` to any value. This is not safe, but good for a short period like you want to capture a trace for a specific command and promptly turn it off after done.
  2. Set env var of `REQUESTS_CA_BUNDLE` to the file path of the proxy server's certificate. This is recommended if you use CLI frequently behind a corporate proxy. 

  A frequent ask is whether or not `HTTP_PROXY` or `HTTPS_PROXY` envionment variables should be set, the answer is it depends. For fiddler on Windows, by default it acts as system proxy on start, you don't need to set anything. If the option is off or using other tools which don't work as system proxy, you should set them. Since almost all traffics from CLI are SSL based, so only `HTTPS_PROXY` should be set. If you are not sure, just set them, but do remember to unset it after the proxy is shut down. For fiddler, the default value is `http://localhost:8888`.

  For other details, check out [Stefan's blog](https://blog.jhnr.ch/2018/05/16/working-with-azure-cli-behind-ssl-intercepting-proxy-server/).

## Concurrent builds

If you are using az on a build machine, and multiple jobs can be run in parallel, then there is a risk that the login tokens are shared between two build jobs is the jobs run as the same OS user.  To avoid mix ups like this, set AZURE_CONFIG_DIR to a directory where the login tokens should be stored.  It could be a randomly created folder, or just the name of the jenkins workspace, like this ```AZURE_CONFIG_DIR=.```

## Appendix
### Windows batch scripts for saving to variables and using it later
       
       ECHO OFF
       SETLOCAL
       FOR /F "tokens=* USEBACKQ" %%F IN (`az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv`) DO (
           SET "vm_ids=%%F %vm_ids%"  :: construct the id list
       )
       az vm stop --ids %vm_ids% :: CLI stops all VMs in parallel 

### Windows PowerShell scrips for saving to variables and using it later

       $vm_ids=(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
       az vm stop --ids $vm_ids # CLI stops all VMs in parallel 

### Windows batch scripts to loop through a list
       ECHO OFF
       SETLOCAL
       FOR /F "tokens=* USEBACKQ" %%F IN (`az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv`) DO (
           ECHO Stopping %%F
           az vm stop --ids %%F
       )

### Windows PowerShell scrips to loop through a list
       $vm_ids=(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
       foreach ($vm_id in $vm_ids) {
           Write-Output "Stopping $vm_id"
           az vm stop --ids $vm_id
       }

### CLI Environment Variables

|  Environment Variable          | Description            |
|--------------------------------|------------------------|
| **AZURE_CONFIG_DIR**           | Global config directory for config files, logs and telemetry. If unspecified, defaults to `~/.azure`. |
| **AZURE_EXTENSION_DIR**        | Extensions' installation directory. If unspecified, defaults to cliextensions directory within the global config directory. |

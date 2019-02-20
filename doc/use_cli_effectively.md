# Tips of using Azure CLI effectively #
Note: for less distraction, Bash scripts are used inline. Windows batch or PowerScripts examples are listed in appendix, which you can use to build similiar examples. 

## Use the right output mode for your work (json, table, or tsv) ##
  1. Use `json` (CLI's default) to give you the most comprehensive information. If you prefer less, use `--output` argument to override at individual command level, or use "az configure" for global level.
  2. Use `table` to give you less but much focused information. If some fields you care are missing, you have 2 options, use `--output json` to get all, or leverage `--query` to pick ones you like.
  
         az vm show -g my_rg -n my_vm --query "{name: name, os:storageProfile.imageReference.offer}" -otable
         Name    Os
         ------  ------------
         my_vm   UbuntuServer
         
  3. Use `tsv` for the most concise output, which is good for scripting particularly you can save to variables to be used later, e.g.

        export vm_ids=$(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)  
        az vm stop --ids $vm_ids
        
## To pass values from one command to the other ##
  1. If the value will be used more than once, assign it to a variable, e.g.
       
         running_vm_ids=$(az vm list -d -g my_rg --query "[?powerState=='VM running'].id" -o tsv)
       
     Or, if it gets used only once, you can just pipe

         az vm list --query "[?powerState=='VM running'].name" | grep my_vm

  2. For list type, 2 suggestions:

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
        
       Or, use `xargs` and optionally going parallel through `-P` flag for better performance

           az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | xargs -I {} -P 10 az vm start --ids "{}"

       Less known, but CLI also has built-in support on processing "--ids" in parallel to achieve the same effect of xargs(note, `@-` is used to get values from pipe)

           az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | az vm start --ids @-

## Async executions ##
  This becomes handy for a few scenarios:
  1. Clean up

          az group delete -n my_rg --no-wait

  2. For performance, don't wait on each operation, rather wait for all at the end
      
          az vm create -g my_rg -n vm1 --image centos --no-wait
          az vm create -g my_rg -n vm2 --image centos --no-wait

          subscription=$(az account show --query "id" -otsv)
          vm1_id="/subscriptions/$subscription/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/vm1"
          vm2_id="/subscriptions/$subscription/resourceGroups/my_rg/providers/Microsoft.Compute/virtualMachines/vm2"
          az vm wait --created --ids $vm1_id $vm2_id

## Generic update command ##
  The hallmark is the `"--add", "--set", "--remove"` generic arguments. Being generic means it can do more things but at the cost of usabilities. For common scenarios, CLI always provides custom commands to make your life easy, but leave the rest for you to explore through the generic updater. A few notes here to ease the pain:

  1. You will need some patience to pull it through.
  2. Do check out whether or not the update command has the convenient arguments exposed for your scenario. If yes, use those.
  3. The property path used with the generic arguments are tied to the output of "show" command. For example, before you try out "az vm update", do invoke the "az vm show" command, read the output, and figure out the right path.
  4. Checking out working examples is the best way to get started. `az vm update -h` has the good ones.
  5. Do remember that generic arguments of `--set` and `--add` takes a list of key value pairs in the format of `<key1>=<value1> <key2>=<value2>`. You will need them to construct non trivial payload. If the input gets complex, using json string will be the best bet, e.g. to attach a new disk:

         az vm update -g my_rg -n my_vm --add storageProfile.dataDisks "{\"createOption\": \"Attach\", \"managedDisk\": {\"id\": \"/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/yg/providers/Microsoft.Compute/disks/yg-disk\"}, \"lun\": 1}"

  6. Of course, leverage CLI's `@<file>` convention, you can put the json string to a file and simplify the command

         az vm update -g my_rg -n my_vm --add storageProfile.dataDisks @~/my_disk.json

## Single quote vs double quote ##
  This becomes a topic because when the command shell(bash, zsh, windows command prompt, etc) parses the CLI command, it will interpret the quotes. To avoid the surprise, a few suggestions here:
  1. If the argument value contains whitespace, you have to use quotes to wrap them.
  2. In Bash, both single and double quotes will be intepreted; while in windows command, only double quotes get handled which means single quotes will be interpreted as a part of the value. So be careful on this difference.
  3. If your command only runs on Bash (or zsh), using single quotes has the benefit of preserve the content inside. Say, if you are dealing with argument vaules in json, then not having to escape the double quotes is a big relief.
  4. If your command will run on windows command prompt, do use double quotes. If the value contains double quotes, make sure you escape it e.g. "i like to use \\" a lot". Please note, in Bash exported variable inside the double quote will be evaluated. If this is not what you want, again use \\ to escape it like "\\$var"
  5. A few CLI commands, including the generic updater, takes a list of values seperated by spaces, like `<key1>=<value1> <key2>=<value2>`. Since the key name and value can take arbitary string which might contain whitespaces, using quotes will be necessary. Do remember you need to wrap the pair, not individual key or value. So `"my name"=john` is wrong, and the right one would be `"my name=john"` e.g.,

         az webapp config appsettings set -g my_rg -n my_web --settings "client id=id1" "my name=john"
  6. Last, use CLI's "@<file>" convention to load from a file so to by-pass shell's intepretion, e.g.

         az ad app create --display-name my-native --native-app --required-resource-accesses @manifest.json


## Generic resource commands
  Not common, but if the relevant service hasn't got CLI command coverage, during the time gap you can use `az resource create/show/list/delete/update/invoke-action` to get things done. A few suggestions here:
  1. If only `create/update` are involved, your other option is to use `az group deployment create`. Do leverage [Azure Quickstart Templates](https://github.com/Azure/azure-quickstart-templates) for working examples.
  2. Check out the Rest API reference for the requst payload, url and api version. Once clear on that, the rest will be straightforward. For solid example, check out community's comments on [how to create AppInsights](https://github.com/Azure/azure-cli/issues/5543).


## Working behind a proxy
  Proxy is common behind corporate network or introduced by tracing tools like fiddler, mitmproxy, etc. If the proxy uses self-signed certificates, the Python [requests library](https://github.com/kennethreitz/requests) which CLI depends on will throw `SSLError("bad handshake: Error([('SSL routines', 'tls_process_server_certificate', 'certificate verify failed')],)",)`.  There are 2 ways to handle this error:
  1. Disable the certificate check across the CLI by setting the env var of `AZURE_CLI_DISABLE_CONNECTION_VERIFICATION` to any value. This is not safe, but good for a short period like you want to capture a trace for a specific command and promptly turn it off after done.
  2. Set env var of `REQUESTS_CA_BUNDLE` to the file path of the proxy server's certificate. This is recommended if you use CLI frequently behind a corporate proxy. 

  For more details, check out [Stefan's blog](https://blog.jhnr.ch/2018/05/16/working-with-azure-cli-behind-ssl-intercepting-proxy-server/).


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

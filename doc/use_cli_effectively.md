# Tips of using Azure CLI effectively #

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

       Less known, but CLI also has built-in support on processing "--ids" in parallel to achieve the same effect of xargs

          az vm list -d -g my_rg --query "[?powerState=='VM stopped'].id" -o tsv | tr '\r\n' ' ' | { read ids ; az vm start --ids $ids ; }

## Async executions ##
  This becomes handly for a few scenarios:
  1. Clean up

          az group delete -n my_rg --no-wait

  2. For performance, don't wait on each operation, rather wait for all at the end
      
          az vm create -g my_rg -n vm1 --image centos --no-wait
          az vm create -g my_rg -n vm2 --image centos --no-wait
           
          az vm wait --created --ids $(az vm list -g my_rg --query "[].id" -o tsv)

## Generic update command ##
  The hallmark is the `"--add", "--set", "--remove"` generic arguments. Being generic means it can do more things but at the cost of usabilities. For common scenarios, CLI always provides custom commands to make your life easy, but leave the rest for you to explore through the generic updater. A few notes here to ease the pain:

  1. You will need some patience to pull it through.
  2. Do check out whether or not the update command has the convinient arguments exposed for your scenario. If yes, use those.
  3. The property path used with the generic arguments are tied to the output of "show" command. For example, before you try out "az vm update", do invoke the "az vm show" command, read the output, and figure out the right path.
  4. Checking out working examples is the best way to get started. `az vm update -h` has the good ones.
  5. Do remember that generic arguments of `--set` and `--add` takes a list of key value pairs in the format of `<key1>=<value1> <key2>=<value2>`. You will need them to construct non trivial payload. If the input gets complex, using json string will be the best bet, e.g. to attach a new disk:

         az vm update -g my_rg -n my_vm --add storageProfile.dataDisks "{\"createOption\": \"Attach\", \"managedDisk\": {\"id\": \"/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/yg/providers/Microsoft.Compute/disks/yg-disk\"}, \"lun\": 1}"

  6. Of course, leverage CLI's `@<file>` convention, you can put the json string to a file and simplify the command

         az vm update -g my_rg -n my_vm --add storageProfile.dataDisks @~/my_disk.json

## Single quote vs double quote ##
  This becomes a topic becuase when the command shell(bash, zsh, windows command prompt, etc) parses the CLI command, it will interpret the quotes. To avoid the surprise, a few suggestions here:
  1. If the argument value contains whitespace, you have to use quotes to wrap them.
  2. In Bash, both single and double quotes will be intepreted; while in windows command, only double quotes get handled which means single quotes will be part of values. So be careful on this difference.
  3. If your command only runs on Bash (or zsh), using single quotes has the benefit of preserve the content inside. Say, if you are dealing with argument vaules in json, then not having to escape the double quotes is a big relief.
  4. If your command will run on windows command prompt, do use double quotes. If the value contains double quotes, make sure you escape it e.g. "i like to use \\" a lot". Please note, in Bash exported variable inside the double quote will be evaluated. If this is not what you want, again use \" to escape it like "\\$var"
  5. A few CLI commands, including the generic updater, takes a list of values seperated by spaces, like `<key1>=<value1> <key2>=<value2>`. Since the key name and value can take arbitary string which might contain whitespaces, using quotes will be necessary. Do remember you need to wrap the pair, not individual key or value. So `"my name"=john` is wrong, and the right one would be `"my name=john"` e.g.,

         az webapp config appsettings set -g my_rg -n my_web --settings "client id=id1" "my name=john"
  6. Last, use CLI's "@<fiile>" convention to load from a file so to by-pass shell's intepretion, e.g.

         az ad app create --display-name my-native --native-app --required-resource-accesses @manifest.json

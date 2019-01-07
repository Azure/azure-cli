# How to use Azure CLIeffectively#

##Output mode (json, table, or tsv)##
  a. Use `json` (CLI's default) to give you the most comprehensive information. If you prefer less, use `--output` to override at individual command level, or "az configure" at global level
  b. Use `table` to give you less but much focused information. If some fields you care are missing, you have 2 options, use "--output json" to get all, or leverage "--query" to pick ones you like.
         ```bash
         az vm show  -g yg -n yg-1 --query "{name: name, os:storageProfile.imageReference.offer}" -otable
         Name    Os
         ------  ------------
         yg-1    UbuntuServer
		 ```
  c. Use `tsv` for the most concise output, which is good to be used for scripting that you can save to variables to be used later, e.g.
        ```bash
        export vm_ids=$(az vm list -d -g yg --query "[?powerState=='VM running'].id" -o tsv)  
        az vm stop --ids $vm_ids
		```

## To pass values from one command to the other command ##
    a. if the value will be used more than once, assign the value to a variable, e.g.
	   ```bash
	   running_vm_ids=$(az vm list -d -g yg --query "[?powerState=='VM running'].id" -o tsv)
	   ```
	   However, if the vale only gets used once, then use pipe through "|"
	b. for list typed value, 2 extra Suggestions:
	   If you need more controls on the result, use "for loop":
	   ```bash
		#!/usr/bin/env bash
		for vm in $(az vm list -d -g yg --query "[?powerState=='VM running'].id" -o tsv); do
		   echo stopping $vm
		   az vm stop --ids $vm
		   #  retVal=$?
		   if [ $? -ne 0 ]; then
			   echo "Failed to stop $vm"
			   exit 1
		   fi
		   echo $vm stopped
		done
		``

	    Otherwise, use `xargs` and optional turning on parallel through `-P` flag for best performance
		   `az vm list -d -g yg --query "[?powerState=='VM stopped'].id" -o tsv | xargs -I {} -P 10 az vm start --ids "{}"`
	    Less  known, but CLI also has built-in support on processing"--ids" in parallel to achieve the same effect of xargs. Do leverage 
	       `az vm list -d -g yg --query "[?powerState=='VM stopped'].id" -o tsv | tr '\r\n' ' ' | { read ids ; az vm start --ids $ids ; }`

##No wait and wait##
   You will need this when,
   a. trash clean up `az group delete -n myGroup --no-wait`
   b. for performance, go parallel and only wait only once:
      ```bash
      az vm create -g rg -n vm1 --image centos --no-wait
      az vm create -g rg -n vm2 --image centos --no-wait
	  ...
      az vm wait --created --ids $(az vm list -g rg --query "[].id" -o tsv)
	  ```

##Generic update command##
    The hallmark is the `"--add", "--set", "--remove"` generic arguments. Being generic means it can do more things but at the cost of usabilities.
	For common scenarios, CLI always provide custom commands to get your lives easier, but leave the rest for you to explorer though the generic updater. A few notes here to ease the pain:
       a. You will need some patience to pull it through.
	   b. Do check out whether or not the update command has the convinient arguments exposed for your scenario. If yes, use those.
	   c. The property path used with the generic arguments are tied to the output of "show" command. Say, before you try out "az vm update", do invoke the "az vm show" command,
	      read the output, and figure out the right path
	   d. Checking out working examples is the best way to get started. "az vm update -h" has the best ones since it is the first generic update command.
	   d. Do remember that generic arguments of "--set" and  takes a list of key value pairs in the format of "<key1>=<value1> <key2>=<value2>". You will need them to
	      construct non trivial payload. If the value gets complex, using json string will be the best bet, e.g. to attach a new disk:
		  `az vm update -g yg -n yg-1 --add storageProfile.dataDisks "{\"createOption\": \"Attach\", \"managedDisk\": {\"id\": \"/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/yg/providers/Microsoft.Compute/disks/yg-disk\"}, \"lun\": 1}"`
	      Of course, leverage CLI's support towards the "@<file>" convention, you can put the json string to a file and simplify the command
		  `az vm update -g yg -n yg-1 --add storageProfile.dataDisks @~/mydisk.json`

##Single quote vs double quote##
   This becomes a topic becuase when the command shell(like bash, windows command prompt) parses the CLI, it will interpret the quotes. Suggestions here:
   1. If the argument value contains white space, you have to use quotes to wrap them.
   2. In Bash, both single and double quotes will be intepreted; while in windows command, only double quotes get handled which means single quotes will be part of values,
      be careful on this difference
   2. If your scipt only runs on Bash (or zsh), using single quotes has the benefit of preserve content inside. Say, if you are dealing with argument vaules in json, then not having to escape 
      the double quotes will be a big plus
   3. If your scripts will run in window batch, do use double quote. If the value contains double quotes, make sure you escape it like "i like to use \" a lot". Please note,in bash 
      exported variable inside the double quote will be evaluated, if this is not what you want, again use "\" to escape it like "\$var"
   4. A few CLI commands, including the generic updater, takes the value in array type seperated by spaces, like "<key1>=<value1> <key2>=<value2>", Since the key name and value can 
      take arbitary string with whitespace, quotes will be necessary. Do remember you need to wrap the pair, not individual key or value. So "my name"=yugangw will be wrong,
	  the right one would be "my name=yugangw", e.g.
	  az webapp config appsettings set -g rg -n web1 --settings "client id=id1" "weird\$name=john"
   5. Last, use Azure CLI specific "@<fiile>" symbol to load from a file to by-pass shell's intepretion, e.g.
      az ad app create --display-name my-native --native-app --required-resource-accesses @manifest.json
      






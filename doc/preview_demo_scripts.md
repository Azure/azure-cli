The following commands showcase how to perform some common operations available in the preview.

    # Login to Azure using DeviceAuth
    $ az login

    # Create a resource group
    $ az resource group create -l westus -n demo100
    
    # Find common vm images 
    $ az vm image list
    
    # Search all vm images, takes about 20s
    $ az vm image list --all -l westus 
        
    # simplified help experience
    $ az vm create --help
    
    # Create a simple Linux VM using SSH
    $ az vm create --ssh-key-value ~/.ssh/id_rsa.pub --authentication-type ssh --admin-username ops -l westus  --public-ip-address-type new --image UbuntuLTS  -g Demo100 -n Demo100VM
    
    # List all IP address in the resource group
    $ az vm list-ip-addresses -g Demo100 
    
    # Export a resource group to an ARM template
    $ az resource group export -n Demo100 > template.json
    $ cat template.json | less
   
    # learning to query with JPTerm (OSX: brew install jpterm)
    # try out [].{name:name, os:storageProfile.osDisk.osType}
    $ az vm list --out json | jpterm
    
    # List all VMs and their OS type in a 'grep-able' format
    $ az vm list -g demo100 --query "[].{name:name, os:storageProfile.osDisk.osType}" --out tsv
    Demo100VM	Linux
    Demo300VM	Linux


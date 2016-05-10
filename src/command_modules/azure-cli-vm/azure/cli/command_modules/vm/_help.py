from azure.cli._help_files import helps

helps['vm create'] = """
            type: command
            short-summary: Create an Azure Virtual Machine
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-quick-create-cli/ for an end-to-end tutorial
            parameters: 
                - name: --image
                  type: string
                  short-summary: OS image (Common, URN or URI).
                  long-summary: |
                  Common OS types: Win2012R2Datacenter, Win2012Datacenter, Win2008SP1. For other values please run 'az vm image list'
                  Example URN: MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest
                  Example URI: http://<storageAccount>.blob.core.windows.net/vhds/osdiskimage.vhd
                  populator-commands: 
                  - az vm image list
                  - az vm image show
                - name: --ssh-key-value
                  short-summary: SSH key file value or key file path.
            examples:
                - name: Create a simple Windows Server VM with private IP address
                  text: >
                    az vm create --image Win2012R2Datacenter --admin-username myadmin --admin-password Admin_001 
                    -l "West US" -g myvms --name myvm001
                - name: Create a simple Windows Server VM with public IP address and DNS entry
                  text: >
                    az vm create --image Win2012R2Datacenter --admin-username myadmin --admin-password Admin_001 
                    -l "West US" -g myvms --name myvm001 --public-ip-address-type new --dns-name-for-public-ip myGloballyUniqueVmDnsName
                - name: Create a Linux VM with SSH key authentication, add a public DNS entry and add to an existing Virtual Network and Availability Set.
                  text: >
                    az vm create --image <linux image from 'az vm image list'>
                    --admin-username myadmin --admin-password Admin_001 --authentication-type sshkey
                    --virtual-network-type existing --virtual-network-name myvnet --subnet-name default
                    --availability-set-type existing --availability-set-id myavailset
                    --public-ip-address-type new --dns-name-for-public-ip myGloballyUniqueVmDnsName
                    -l "West US" -g myvms --name myvm18o --ssh-key-value "<ssh-rsa-key or key-file-path>"
            """

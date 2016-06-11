from azure.cli.help_files import helps

#pylint: disable=line-too-long

image_long_summary = """                      URN aliases: CentOS, CoreOS, Debian, openSUSE, RHEL, SLES, UbuntuLTS, Win2008SP1, Win2012Datacenter, Win2012R2Datacenter.
                      Example URN: MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest.
                      Example URI: http://<storageAccount>.blob.core.windows.net/vhds/osdiskimage.vhd.
"""

helps['vm create'] = """
            type: command
            short-summary: Create an Azure Virtual Machine
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-quick-create-cli/ for an end-to-end tutorial
            parameters: 
                - name: --image
                  type: string
                  short-summary: 'OS image (URN alias, URN or URI).'
                  long-summary: |
{0}
                  populator-commands: 
                  - az vm image list
                  - az vm image show
                - name: --ssh-key-value
                  short-summary: SSH key file value or key file path.
            examples:
                - name: Create a simple Windows Server VM with private IP address
                  text: >
                    az vm create --image Win2012R2Datacenter --admin-username myadmin --admin-password Admin_001 
                    -l "West US" -g myvms --name myvm001 --public-ip-address-type none
                - name: Create a simple Windows Server VM with public IP address and DNS entry
                  text: >
                    az vm create --image Win2012R2Datacenter --admin-username myadmin --admin-password Admin_001 
                    -l "West US" -g myvms --name myvm001 --public-ip-address-type new --dns-name-for-public-ip myGloballyUniqueVmDnsName
                - name: Create a Linux VM with SSH key authentication, add a public DNS entry and add to an existing Virtual Network and Availability Set.
                  text: >
                    az vm create --image <linux image from 'az vm image list'>
                    --authentication-type ssh
                    --virtual-network-type existing --virtual-network-name myvnet --subnet-name default
                    --availability-set-type existing --availability-set-id myavailset
                    --public-ip-address-type new --dns-name-for-public-ip myGloballyUniqueVmDnsName
                    -l "West US" -g myvms --name myvm18o --ssh-key-value "<ssh-rsa-key or key-file-path>"
            """.format(image_long_summary)

helps['vm scaleset create'] = """
            type: command
            short-summary: Create an Azure Virtual Machine Scale Set
            long-summary: See https://azure.microsoft.com/en-us/blog/azure-virtual-machine-scale-sets-ga/ for an introduction to scale sets.
            parameters: 
                - name: --image
                  type: string
                  short-summary: 'OS image (URN alias, URN or URI) [default: Win2012R2Datacenter].'
                  long-summary: |
{0}
            examples:
                - name: Windows scaleset with 5 instances, a load balancer and a public IP address
                  text: >
                    az vm scaleset create -n myName -g myResourceGroup --admin-password MyPassword123 --instance-count 5
                - name: Linux scaleset with SSH authentication, a public IP address, a DNS entry, an existing load balancer, and an existing virtual network
                  text: >
                    az vm scaleset create  -n myName -g myResourceGroup --dns-name-for-public-ip myGloballyUnieqDnsName
                    --load-balancer-type existing --load-balancer-name myLoadBalancer
                    --virtual-network-type existing --virtual-network-name myVNET --subnet-name mySubnet --image canonical:Ubuntu_Snappy_Core:15.04:2016.0318.1949
                    --authentication-type ssh --ssh-key-value "<ssh-key-value or ssh-key-file-path"
""".format(image_long_summary)

helps['vm availability-set create'] = """
            type: command
            long-summary: For more info, see https://blogs.technet.microsoft.com/yungchou/2013/05/14/window-azure-fault-domain-and-upgrade-domain-explained-explained-reprised/
            """

helps['vm extension set'] = """
            type: command
            examples:
                - name: Add a new linux user
                  text: 
                    az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 --vm-name myvm --resource-group yugangw --private-config '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
            """

helps['container create'] = """
            type: command
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/container-service-intro/ for an intro to Container Service.
"""
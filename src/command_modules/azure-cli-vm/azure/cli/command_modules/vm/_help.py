#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

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
                  short-summary: SSH public key or public key file path.
            examples:
                - name: Create a simple Windows Server VM with private IP address only
                  text: >
                    az vm create -n my_vm_name -g myrg --admin-username myadmin --admin-password Password@1234 
                     --public-ip-address-type none
                - name: Create a simple Windows Server VM with public IP address and DNS entry
                  text: >
                    az vm create -n my_vm_name -g myrg --admin-username myadmin --admin-password Password@1234
                    --public-ip-address-dns-name my_globally_unique_vm_dns_name
                - name: Create a Linux VM with SSH key authentication, add a public DNS entry and add to an existing Virtual Network and Availability Set.
                  text: >
                    az vm create -n my_vm_name -g myrg --image <linux image from 'az vm image list'>
                    --authentication-type ssh
                    --vnet my_existing_vnet --subnet-name subnet1
                    --availability-set my_existing_availability_set
                    --public-ip-address-dns-name my_globally_unique_vm_dns_name
                    --ssh-key-value "<ssh-rsa-key, key-file-path or not specified for default-key-path>"
            """.format(image_long_summary)

helps['vmss create'] = """
            type: command
            short-summary: Create an Azure Virtual Machine Scale Set
            long-summary: See https://azure.microsoft.com/en-us/blog/azure-virtual-machine-scale-sets-ga/ for an introduction to scale sets.
            parameters: 
                - name: --image
                  type: string
                  short-summary: 'OS image (URN alias, URN or URI).'
                  long-summary: |
{0}
            examples:
                - name: Windows scaleset with 5 instances, a load balancer and a public IP address
                  text: >
                    az vmss create -n myName -g myResourceGroup --admin-password MyPassword123 --instance-count 5
                - name: Linux scaleset with SSH authentication, a public IP address, a DNS entry, an existing load balancer, and an existing virtual network
                  text: >
                    az vmss create  -n myName -g myResourceGroup --dns-name-for-public-ip myGloballyUnieqDnsName
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

helps['vm container create'] = """
            type: command
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/container-service-intro/ for an intro to Container Service.
"""

generic_update_help = """
                - name: Add or update a tag
                  text: az <command> -n name -g group --set tags.tagName=tagValue
                - name: Remove a tag
                  text: az <command> -n name -g group --remove tags.tagName
"""

helps['vm update'] = """
            type: command
            short-summary: Update VM properties.
            long-summary: Update VM objects and properties using paths that correspond to 'az vm show'.  See examples.
            examples:
{0}
                - name: Set primary NIC
                  text: az <command> -n name -g group --set networkProfile.networkInterfaces[1].primary=false networkProfile.networkInterfaces[0].primary=true
                - name: Add new non-primary NIC
                  text: az <command> -n name -g group --add networkProfile.networkInterfaces primary=false id=<NIC_ID>
                - name: Remove fourth NIC
                  text: az <command> -n name -g group --remove networkProfile.networkInterfaces 3
            """.format(generic_update_help)

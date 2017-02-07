# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

image_long_summary = """                      URN aliases: CentOS, CoreOS, Debian, openSUSE, RHEL, SLES, UbuntuLTS, Win2008R2SP1, Win2012Datacenter, Win2012R2Datacenter.
                      Example URN: MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest
                      Example Custom Image Resource ID or Name: /subscriptions/subscription-id/resourceGroups/myrg/providers/Microsoft.Compute/images/myImage
                      Example URI: http://<storageAccount>.blob.core.windows.net/vhds/osdiskimage.vhd
"""

helps['vm create'] = """
            type: command
            short-summary: Create an Azure Virtual Machine
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-quick-create-cli/ for an end-to-end tutorial
            parameters:
                - name: --image
                  type: string
                  short-summary: 'OS image (URN alias, URN, Custom Image name or ID, VHD Blob URI).'
                  long-summary: |
{0}
                  populator-commands:
                  - az vm image list
                  - az vm image show
                - name: --ssh-key-value
                  short-summary: SSH public key or public key file path.
            examples:
                - name: Create a Linux VM with SSH key authentication, add a public DNS entry and add to an existing Virtual Network and Availability Set.
                  text: >
                    az vm create -n my_vm_name -g myrg --image <linux image from 'az vm image list'>
                    --vnet-name my_existing_vnet --subnet subnet1
                    --availability-set my_existing_availability_set
                    --public-ip-address-dns-name my_globally_unique_vm_dns_name
                    --ssh-key-value "<ssh-rsa-key, key-file-path or not specified for default-key-path>"
                - name: Create a simple Windows Server VM with private IP address only
                  text: >
                    az vm create -n my_vm_name -g myrg --admin-username myadmin --admin-password Password@1234
                     --public-ip-address "" --image Win2012R2Datacenter
                - name: Create a simple Ubuntu VM with public IP address, DNS entry, 2 data disk(10GB, 20GB), and generate ssh key pairs under ~/.ssh
                  text: >
                    az vm create -n my_vm_name -g myrg --admin-username myadmin --admin-password Password@1234
                    --public-ip-address-dns-name my_globally_unique_vm_dns_name --image ubuntults --data-disk-sizes-gb 10 20
                    --size Standard_DS2 --generate-ssh-keys
                - name: Create a VM from a custom managed image
                  text: >
                    az vm create -g myrg -n my_vm_name --image my_image_in_myrg --admin-username myadmin --admin-password Password@1234
                - name: Create a VM with unmanaged os disk by using image blob uri
                  text: >
                    az vm create -g myrg -n my_vm_name --image https://account123.blob.core.windows.net/Images/my_vhd-osDisk.vhd
                    --os-type linux --admin-username myadmin --admin-password Password@1234
                - name: Create a VM by attaching to an existing specialized managed os disk
                  text: >
                    az vm create -g myrg -n my_vm_name --managed-os-disk my-os-disk
                    --os-type linux --admin-username myadmin --admin-password Password@1234
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
                - name: Windows scaleset with 5 instances, a load balancer, a public IP address and a 2GB data disk
                  text: >
                    az vmss create -n my_vmss_name -g myrg --admin-password MyPassword123 --instance-count 5 --image Win2012R2Datacenter --data-disk-sizes-gb 2
                - name: Linux scaleset with auto-generated ssh key pair under ~/.ssh, a public IP address, a DNS entry, an existing load balancer, and an existing virtual network
                  text: >
                    az vmss create -n my_vmss_name -g myrg --dns-name-for-public-ip myGloballyUniqueDnsName
                    --load-balancer myLoadBalancer --vnet-name myVNET --subnet mySubnet --image UbuntuLTS
                    --generate-ssh-keys
                - name: Scaleset created from custom Linux image using existing ssh public key of ~/.ssh/id_rsa.pub
                  text: >
                    az vmss create -n my_vmss_name -g myrg --image my_linuximage_in_myrg
""".format(image_long_summary)

helps['vm availability-set create'] = """
            type: command
            short-summary: Create an availability set
            long-summary: For more info, see https://blogs.technet.microsoft.com/yungchou/2013/05/14/window-azure-fault-domain-and-upgrade-domain-explained-explained-reprised/
            """

helps['vm availability-set update'] = """
            type: command
            short-summary: Update an availability set
            """

helps['vm availability-set convert'] = """
            type: command
            short-summary: convert an availability set to contain VMs with managed disks
            """

helps['vm extension set'] = """
            type: command
            examples:
                - name: Add a new linux user
                  text:
                    az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 --vm-name myvm --resource-group mygroup --protected-settings '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
            """

helps['vm access set-linux-user'] = """
            type: command
            long-summary: Note, the user will have an admin's priviledge.
            """

helps['vm access reset-windows-admin'] = """
            type: command
            long-summary: Note, this resets the admin's credentials. You can't add a new admin.
            """

helps['acs create'] = """
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
            short-summary: Update VM properties
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

helps['vmss get-instance-view'] = """
    type: command
    parameters:
        - name: --ids
          short-summary: "One or more scale set or specific VM instance IDs. If provided, no other 'Resource Id' arguments should be specified."
"""

helps['vmss reimage'] = """
    type: command
    parameters:
        - name: --ids
          short-summary: "One or more scale set or specific VM instance IDs. If provided, no other 'Resource Id' arguments should be specified."
"""

helps['vmss show'] = """
    type: command
    parameters:
        - name: --ids
          short-summary: "One or more scale set or specific VM instance IDs. If provided, no other 'Resource Id' arguments should be specified."
"""

helps['vm get-instance-view'] = """
    type: command
    short-summary: "Gets a VM including instance information (powerState)"
"""

helps['vm convert'] = """
    type: command
    short-summary: Convert VM with unmanaged disks to use managed disks
"""

helps['vm'] = """
    type: group
    short-summary: Provision Linux and Windows virtual machines in minutes
"""
helps['vm access'] = """
    type: group
    short-summary: Manage user access
"""
helps['vm availability-set'] = """
    type: group
    short-summary: Group resources into availability-sets for high-availability requirements
"""
helps['vm boot-diagnostics'] = """
    type: group
    short-summary: Troubleshoot virtual machine start-up
"""
helps['vm boot-diagnostics disable'] = """
    type: command
    short-summary: Disable boot diagnostics
"""
helps['vm boot-diagnostics get-boot-log'] = """
    type: command
    short-summary: Get the boot diagnostics log
"""
helps['acs'] = """
    type: group
    short-summary: Commands to manage Azure container services
"""
helps['acs create'] = """
    type: command
    short-summary: Create a container service with your preferred orchestrator
"""
helps['acs delete'] = """
    type: command
    short-summary: delete a container service
"""
helps['acs list'] = """
    type: command
    short-summary: list container services
"""
helps['acs show'] = """
    type: command
    short-summary: show a container service
"""
helps['acs scale'] = """
    type: command
    short-summary: change private agent count of a container service.
"""
helps['vm diagnostics'] = """
    type: group
    short-summary: Configure the Azure VM diagnostics extension
"""
helps['vm disk'] = """
    type: group
    short-summary: Manage VM data disks
"""
helps['vm unmanaged-disk'] = """
    type: group
    short-summary: Manage VM unmanaged data disks
"""
helps['vm extension'] = """
    type: group
    short-summary: Extend the functionality of your VMs with vm extensions
"""
helps['vm extension list'] = """
    type: command
    short-summary:  List extensions attached to a VM in a resource group
"""
helps['vm extension image'] = """
    type: group
    short-summary: Find VM extensions available for your subscription and region
"""
helps['vm image'] = """
    type: group
    short-summary: VM images available on the Azure marketplace
"""
helps['vm nic'] = """
    type: group
    short-summary: Manage VM network interfaces, see also 'az network nic'
"""
helps['vmss'] = """
    type: group
    short-summary: Create highly available, auto-scalable Linux or Windows virtual machines
"""
helps['vmss diagnostics'] = """
    type: group
    short-summary: Configure the Azure VMSS diagnostics extension
"""
helps['vmss list_instance_connection_info'] = """
    type: group
    short-summary: Get IP address and port number used to connect to individual instances.
"""
helps['vmss extension'] = """
    type: group
    short-summary: Extend the functionality of your scale-set with VM extensions
"""
helps['vmss extension image'] = """
    type: group
    short-summary: Find scale-set extensions available for your subscription and region
"""
helps['vm capture'] = """
            type: command
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/ for an end-to-end tutorial
            examples:
                - name: Process to deallocate, generalize, and capture a stopped virtual machine
                  text: >
                    az vm deallocate -g my_rg -n my_vm_name\n\r
                    az vm generalize -g my_rg -n my_vm_name\n\r
                    az vm capture -g my_rg -n my_vm_name --vhd-name-prefix my_prefix\n\r
                    """

helps['vm deallocate'] = """
            type: command
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/ for an end-to-end tutorial
            examples:
                - name: Process to deallocate, generalize, and capture a stopped virtual machine
                  text: >
                    az vm deallocate -g my_rg -n my_vm_name\n\r
                    az vm generalize -g my_rg -n my_vm_name\n\r
                    az vm capture -g my_rg -n my_vm_name --vhd-name-prefix my_prefix\n\r
                    """

helps['vm generalize'] = """
            type: command
            long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/ for an end-to-end tutorial
            examples:
                - name: Process to deallocate, generalize, and capture a stopped virtual machine
                  text: >
                    az vm deallocate -g my_rg -n my_vm_name\n\r
                    az vm generalize -g my_rg -n my_vm_name\n\r
                    az vm capture -g my_rg -n my_vm_name --vhd-name-prefix my_prefix\n\r
                    """

helps['vm wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the VM is met.
"""

helps['disk'] = """
    type: group
    short-summary: Commands to manage 'Managed Disks'
"""

helps['snapshot'] = """
    type: group
    short-summary: Commands to manage snapshots
"""

helps['image'] = """
    type: group
    short-summary: Commands to manage custom virtual machine images based on managed disks/snapshots
"""

helps['disk create'] = """
    type: command
    short-summary: create a managed disk
    examples:
        - name: Create by importing from blob uri
          text: az disk create -g myRG -n myDisk --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd
        - name: Create an empty disk
          text: az disk create -g myRG -n myDisk --size-gb 10
        - name: Create by copying from an existing disk or snapshot
          text: az disk create -g myRG -n myDisk2 --source myDisk
"""
helps['disk list'] = """
    type: command
    short-summary: list managed disks under a resource group or under current subscription
"""
helps['disk delete'] = """
    type: command
    short-summary: delete a managed disk
"""
helps['disk update'] = """
    type: command
    short-summary: update a managed disk
"""
helps['disk grant-access'] = """
    type: command
    short-summary: grant read access to a managed disk
"""
helps['disk revoke-access'] = """
    type: command
    short-summary: revoke read access to a managed disk
"""

helps['snapshot create'] = """
    type: command
    short-summary: create a snapshot
    examples:
        - name: Create by importing from blob uri
          text: az snapshot create -g myRG -n mySnapshot --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd
        - name: Create an empty snapshot
          text: az snapshot create -g myRG -n mySnapshot --size-gb 10
        - name: Create by copying from an existing disk from the same resource group
          text: az snapshot create -g myRG -n mySnapshot2 --source myDisk
"""
helps['snapshot update'] = """
    type: command
    short-summary: update a snapshot
"""
helps['snapshot list'] = """
    type: command
    short-summary: list snapshots under a resource group or under current subscription
"""
helps['snapshot grant-access'] = """
    type: command
    short-summary: grant read access to a snapshot
"""
helps['snapshot revoke-access'] = """
    type: command
    short-summary: revoke read access to a snapshot
"""
helps['image create'] = """
    type: command
    short-summary: create a custom image from managed disks or snapshots
    examples:
        - name: Create from an existing disk
          text: az image create -g myRG -n image1 --os-type Linux --source /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/rg1/providers/Microsoft.Compute/snapshots/s1 --data-snapshot /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/rg/providers/Microsoft.Compute/snapshots/s2
        - name: Create by capturing an existing generalize virtual machine from the same resource group
          text: az image create -g myRG -n image1 --source myvm1
"""
helps['image list'] = """
    type: command
    short-summary: list custom images under a resource group or under current subscription
"""

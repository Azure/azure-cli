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

vm_ids_example = """        - name: {0}
          text: >
            az {1} --ids $(az vm list -g group_name --query "[].id" -o tsv)
"""

name_group_example = """        - name: {0} by Name and Group
          text: az {1} -n name -g group_name
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
            az vm create -n my-vm-name -g myrg --image <linux image from 'az vm image list'>
            --vnet-name my_existing_vnet --subnet subnet1
            --availability-set my_existing_availability_set
            --public-ip-address-dns-name my_globally_unique_vm_dns_name
            --ssh-key-value "<ssh-rsa-key, key-file-path or not specified for default-key-path>"
        - name: Create a simple Windows Server VM with private IP address only
          text: >
            az vm create -n my-vm-name -g myrg --admin-username myadmin --admin-password Password@1234
             --public-ip-address "" --image Win2012R2Datacenter
        - name: Create a simple Ubuntu VM with public IP address, DNS entry, 2 data disk(10GB, 20GB), and generate ssh key pairs under ~/.ssh
          text: >
            az vm create -n my-vm-name -g myrg --admin-username myadmin --admin-password Password@1234
            --public-ip-address-dns-name my_globally_unique_vm_dns_name --image ubuntults --data-disk-sizes-gb 10 20
            --size Standard_DS2 --generate-ssh-keys
        - name: Create a VM from a custom managed image
          text: >
            az vm create -g myrg -n my-vm-name --image my_image_in_myrg --admin-username myadmin --admin-password Password@1234
        - name: Create a VM with unmanaged os disk by using image blob uri
          text: >
            az vm create -g myrg -n my-vm-name --image https://account123.blob.core.windows.net/Images/my_vhd-osDisk.vhd
            --os-type linux --admin-username myadmin --admin-password Password@1234
        - name: Create a VM by attaching to an existing specialized managed os disk
          text: >
            az vm create -g myrg -n my-vm-name --attach-os-disk my-os-disk
            --os-type linux --admin-username myadmin --admin-password Password@1234
        - name: Create an Ubuntu VM and provide a cloud-init script (https://docs.microsoft.com/en-us/azure/virtual-machines/virtual-machines-linux-using-cloud-init)
          text: >
            az vm create -g group_name -n vm-ame --image debian --custom_data ./my-cloud-init-script.yml
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
        - name: Scaleset created with a cloud-init script (https://docs.microsoft.com/en-us/azure/virtual-machines/virtual-machines-linux-using-cloud-init)
          text: >
            az vmss create -g group_name -n my-vmss-name --image debian --custom_data ./my-cloud-init-script.yml
""".format(image_long_summary)

helps['vm availability-set create'] = """
    type: command
    short-summary: Create an availability set
    long-summary: For more info, see https://blogs.technet.microsoft.com/yungchou/2013/05/14/window-azure-fault-domain-and-upgrade-domain-explained-explained-reprised/
    examples:
        - name: Create Availability Set
          text: az vm availability-set create -n av_set_name -g group_name
"""

helps['vm availability-set update'] = """
    type: command
    short-summary: Update an availability set
    examples:
        - name: Update Availability Set
          text: az vm availability-set update -n av_set_name -g group_name
        - name: Update Availability Set Tag
          text: az vm availability-set update -n av_set_name -g group_name --set tags.foo=value
        - name: Remove Availability Set Tag
          text: az vm availability-set update -n av_set_name -g group_name --remove tags.foo
"""

helps['vm availability-set convert'] = """
    type: command
    short-summary: convert an availability set to contain VMs with managed disks
    examples:
        - name: Convert AV Set with unmanaged disks to managed by resource group and name
          text: vm availability-set convert -g group_name -n av_set_name
        - name: Convert AV Set with unmanaged disks to managed by Ids
          text: >
            az vm availability-set convert --ids $(az vm availability-set \\
                list -g group_name --query "[].id" -o tsv)
"""

helps['vm extension set'] = """
    type: command
    examples:
        - name: Add a new linux user
          text:
            az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 --vm-name myvm --resource-group mygroup --protected-settings '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
"""

helps['vm availability-set delete'] = """
    type: command
    examples:
        - name: Delete Availability Set
          text: az vm availability-set delete -n av_set_name -g group_name
"""

helps['vm availability-set list'] = """
    type: command
    examples:
        - name: List Availability Sets in Resource Group
          text: az vm availability-set list -g group_name
"""

helps['vm availability-set list-sizes'] = """
    type: command
    examples:
        - name: List VM sizes for an Availability Set
          text: az vm availability-set list-sizes -n av_set_name -g group_name
"""

helps['vm availability-set show'] = """
    type: command
    examples:
        - name: Retrieve information about an Availability Set
          text: az vm availability-set show -n av_set_name -g group_name
"""

helps['vm extension set'] = """
    type: command
    examples:
        - name: Add a new linux user
          text:
            az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 --vm-name myvm
            --resource-group mygroup --protected-settings '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
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

helps['vm show'] = """
    type: command
    short-summary: Retrieves information about a virtual machine.
"""

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

helps['vm convert'] = """
    type: command
    short-summary: Convert VM with unmanaged disks to use managed disks
    examples:
        - name: Convert VM with unmanaged disks to managed by resource group and name
          text: az vm convert -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Convert VM with unmanaged disks to managed by Ids', 'vm convert'))

helps['vm'] = """
    type: group
    short-summary: Provision Linux and Windows virtual machines in minutes
"""
helps['vm user'] = """
    type: group
    short-summary: Manage users
"""

helps['vm user delete'] = """
    type: command
    long-summary: >
        Delete a user account without logging into to the VM directly.
    examples:
        - name: Delete User
          text: az vm user delete -u username -n vm-name -r group_name
{0}
""".format(vm_ids_example.format('Delete User by VM Ids', 'az vm user delete -u username'))

helps['vm user reset-ssh'] = """
    type: command
    short-summary: Reset the SSH configuration.
    long-summary: >
        The extension will restart the SSH server, open the SSH port on your VM, and reset the SSH configuration to
        default values. The user account (name, password or SSH keys) will not be changed.
    examples:
        - name: Reset SSH
          text: az vm user reset-ssh -n vm-name -r group_name
{0}
""".format(vm_ids_example.format('Reset SSH by VM Ids', 'vm user reset-ssh'))

helps['vm user update'] = """
    type: command
    long-summary: Note, the user will have an admin's privilege.
    examples:
        - name: Reset Windows Admin
          text: az vm user update -u username -p password -n vm-name -g resource_group_name
        - name: Set Linux User
          text: az vm user update -u username --ssh-key-value "$(< ~/.ssh/id_rsa.pub)" -n vm-name -r group_name
{0}
""".format(vm_ids_example.format('Set Linux User by VM Ids', 'vm user update -u username '
                                 '--ssh-key-value "$(< ~/.ssh/id_rsa.pub)"'))

helps['vm availability-set'] = """
    type: group
    short-summary: Group resources into availability-sets for high-availability requirements
    long-summary: >
        To provide redundancy to your application, we recommend that you group two or more virtual machines in an
        availability set. This configuration ensures that during either a planned or unplanned maintenance event,
        at least one virtual machine will be available and meet the 99.95% Azure SLA.
"""

helps['vm boot-diagnostics'] = """
    type: group
    short-summary: Troubleshoot virtual machine start-up
    long-summary: >
        When bringing your own image to Azure or even booting one of the platform images, there can be many reasons why
        a Virtual Machine gets into a non-bootable state. These features enable you to easily diagnose and recover your
        Virtual Machines from boot failures.
"""
vm_boot_diagnostics_disable = 'vm boot-diagnostics disable'
helps[vm_boot_diagnostics_disable] = """
    type: command
    short-summary: Disable boot diagnostics
    examples:
{0}
{1}
""".format(name_group_example.format('Disable boot diagnostics', vm_boot_diagnostics_disable),
           vm_ids_example.format('Disable boot diagnostics by VM Ids', vm_boot_diagnostics_disable))

vm_boot_diagnostics_enable = 'vm boot-diagnostics enable'
vm_boot_diagnostics_enable_cmd = "{0} --storage https://mystor.blob.core.windows.net/".format(vm_boot_diagnostics_enable)
helps[vm_boot_diagnostics_enable] = """
    type: command
    short-summary: Enable boot diagnostics
    examples:
{0}
{1}
""".format(name_group_example.format('Enable boot diagnostics', vm_boot_diagnostics_enable_cmd),
           vm_ids_example.format('Enable boot diagnostics by VM Ids', vm_boot_diagnostics_enable_cmd))

boot_diagnostics_log = 'vm boot-diagnostics get-boot-log'
helps[boot_diagnostics_log] = """
    type: command
    short-summary: Get the boot diagnostics log
    examples:
{0}
{1}
""".format(name_group_example.format('Disable boot diagnostics', boot_diagnostics_log),
           vm_ids_example.format('Disable boot diagnostics by VM Ids', boot_diagnostics_log))

helps['vm diagnostics'] = """
    type: group
    short-summary: Configure the Azure VM diagnostics extension
"""

helps['vm diagnostics get-default-config'] = """
    type: command
    examples:
        - name: Get default diagnostics on a Linux VM and override the storage account key
          text: >
            az vm diagnostics get-default-config \\
                --query "merge(@, {storageAccount: 'mystorageacct'})"
        - name: Get default diagnostics on a Windows VM
          text: >
            az vm diagnostics get-default-config --is-windows-os
"""

helps['vm diagnostics set'] = """
    type: command
    short-summary: Configure the Azure VM diagnostics extension
    examples:
        - name: Set up default diagnostics on a Linux VM
          text: >
            default_config=$(az vm diagnostics get-default-config \\
                --query "merge(@, {storageAccount: 'mystorageacct'})")

            storage_key=$(az storage account keys list -g group_name -n mystorageacct \\
                --query "[?keyName=='key1'] | [0].value" -o tsv)

            settings="{'storageAccountName': 'mystorageacct', 'storageAccountKey': \\
                '${storage_key}'}"

            az vm diagnostics set --settings "${default_config}" --protected-settings "${settings}" \\
                -n setting_name -g group_name
"""

disk_long_summary = """
        Just like any other computer, virtual machines in Azure use disks as a place to store an operating system,
        applications, and data. All Azure virtual machines have at least two disks - a Linux operating system disk
        (in the case of a Linux VM) and a temporary disk. The operating system disk is created from an image, and both
        the operating system disk and the image are actually virtual hard disks (VHDs) stored in an Azure storage
        account. Virtual machines also can have one or more data disks, that are also stored as VHDs.\n\r

        Operating System Disk\n\r
        Every virtual machine has one attached operating system disk. It's registered as a SATA drive and is labeled
        /dev/sda by default. This disk has a maximum capacity of 1023 gigabytes (GB).\n\r

        Temporary disk\n\r
        The temporary disk is automatically created for you. On Linux virtual machines, the disk is typically
        /dev/sdb and is formatted and mounted to /mnt/resource by the Azure Linux Agent. The size of the temporary disk
        varies, based on the size of the virtual machine.\n\r

        Data disk\n\r
        A data disk is a VHD that's attached to a virtual machine to store application data, or other data you need
        to keep. Data disks are registered as SCSI drives and are labeled with a letter that you choose. Each data
        disk has a maximum capacity of 1023 GB. The size of the virtual machine determines how many data disks you can
        attach to it and the type of storage you can use to host the disks.
"""

helps['vm disk'] = """
    type: group
    short-summary: Manage VM data disks
    long-summary: >
{0}
""".format(disk_long_summary)

helps['vm unmanaged-disk'] = """
    type: group
    short-summary: Manage VM unmanaged data disks
    long-summary: >
{0}
""".format(disk_long_summary)

helps['vm unmanaged-disk attach'] = """
    type: command
    long-summary: >
        Attach a persistent disk to your VM so that you can preserve your data - even if your VM is reprovisioned due
        to maintenance or resizing.
    examples:
        - name: Attach a new default sized (1023 GiB) data disk
          text: az vm unmanaged-disk attach -g group_name --vm-name vm-name
        - name: Attach an existing data disk
          text: >
            az vm unmanaged-disk attach -g group_name --vm-name vm-name \\
                --vhd-uri https://mystorage.blob.core.windows.net/vhds/d1.vhd
"""

helps['vm unmanaged-disk detach'] = """
    type: command
    examples:
        - name: Detach a data disk
          text: >
            az vm unmanaged-disk detach -g group_name --vm-name vm-name -n disk_name
"""

helps['vm unmanaged-disk list'] = """
    type: command
    examples:
        - name: List attached VM disks by VM name and Resource Group
          text: az vm unmanaged-disk list -g group_name --vm-name vm-name
        - name: List attached VM disks by IDs of disks with names containing "data_disk"
          text: >
            az vm unmanaged-disk list --ids \\
                $(az resource list --query "[?contains(name, 'data_disk')].id" -o tsv)
"""

helps['vm disk detach'] = """
    type: command
    examples:
        - name: Detach a data disk
          text: >
            az vm disk detach -g group_name --vm-name vm-name -n disk_name
"""

helps['vm disk attach'] = """
    type: command
    long-summary: >
        Attach a persistent disk to your VM so that you can preserve your data - even if your VM is reprovisioned due
        to maintenance or resizing.
    examples:
        - name: Attach a new default sized (1023 GiB) data disk
          text: az vm disk attach -g group_name --vm-name vm-name --disk disk_name --new
"""

helps['vm extension'] = """
    type: group
    short-summary: Extend the functionality of your VMs with vm extensions
    long-summary: >
        Azure virtual machine extensions are small applications that provide post-deployment configuration and
        automation tasks on Azure virtual machines. For example, if a virtual machine requires software installation,
        anti-virus protection, or Docker configuration, a VM extension can be used to complete these tasks.
        Extensions can be bundled with a new virtual machine deployment or run against any existing system.
"""

helps['vm extension list'] = """
    type: command
    short-summary:  List extensions attached to a VM in a resource group
    examples:
        - name: List extensions by VM
          text: az vm extension list -g group_name --vm-name vm-name
        - name: List extensions by Ids containing "my_extension" in the name
          text: >
            az vm extension list --ids \\
                $(az resource list --query "[?contains(name, 'my_extension')].id" -o tsv)
"""

helps['vm extension delete'] = """
    type: command
    examples:
        - name: Delete extension by VM and extension name
          text: az vm extension delete -g group_name --vm-name vm-name -n extension_name
        - name: Delete extensions by Ids containing "my_extension" in the name
          text: >
            az vm extension delete --ids \\
                $(az resource list --query "[?contains(name, 'my_extension')].id" -o tsv)
"""

helps['vm extension show'] = """
    type: command
    examples:
        - name: Show extension by VM and extension name
          text: az vm extension show -g group_name --vm-name vm-name -n extension_name
"""

helps['vm extension image'] = """
    type: group
    short-summary: Find VM extensions available for your subscription and region
"""

helps['vm extension image list'] = """
    type: command
    examples:
        - name: List unique publishers for extensions
          text: az vm extension image list --query "[].publisher" -o tsv | sort -u
        - name: Find extensions with Docker in the name
          text: az vm extension image list --query "[].name" -o tsv | sort -u | grep Docker
        - name: List extension names where publisher name starts with "Microsoft.Azure.App"
          text: >
            az vm extension image list --query \\
                "[?starts_with(publisher, 'Microsoft.Azure.App')].publisher" \\
                -o tsv | sort -u | xargs -I{} az vm extension image list-names --publisher {} -l westus
"""

helps['vm extension image list-names'] = """
    type: command
    examples:
        - name: Find Docker extension by publisher and location
          text: >
            az vm extension image list-names --publisher Microsoft.Azure.Extensions \\
                -l westus --query "[?starts_with(name, 'Docker')]"
        - name: Find the CustomScript extension by publisher and location
          text: >
            az vm extension image list-names --publisher Microsoft.Azure.Extensions \\
                -l westus --query "[?starts_with(name, 'Custom')]"
"""

helps['vm extension image list-versions'] = """
    type: command
    examples:
        - name: Find the available versions for the DockerExtension
          text: >
            az vm extension image list-versions --publisher Microsoft.Azure.Extensions \\
                -l westus -n DockerExtension -otable
"""

helps['vm extension image show'] = """
    type: command
    examples:
        - name: Show the CustomScript extension version 2.0.2
          text: >
            az vm extension image show -l westus -n CustomScript \\
              --publisher Microsoft.Azure.Extensions --version 2.0.2
        - name: Show the latest version of the DockerExtension
          text: >
            publisher=Microsoft.Azure.Extensions\n\r
            extension=DockerExtension\n\r
            location=westus\n\r
            latest=$(az vm extension image list-versions \\
              --publisher ${publisher} -l ${location} -n ${extension} \\
              --query "[].name" -o tsv | sort | tail -n 1)
            az vm extension image show -l ${location} \\
              --publisher ${publisher} -n ${extension} --version ${latest}
"""

helps['vm image'] = """
    type: group
    short-summary: VM images available on the Azure marketplace
"""

helps['vm image list'] = """
    type: command
    short-summary: List the VM images available on the Azure marketplace
    examples:
        - name: List all images
          text: az vm image list --all
        - name: List all offline cached CentOS images
          text: az vm image list -f CentOS
        - name: List all CentOS images
          text: az vm image list -f CentOS --all
"""

helps['vm image list-offers'] = """
    type: command
    short-summary: List the VM image offers available on the Azure marketplace
    examples:
        - name: List all offers from Microsoft in westus
          text: az vm image list-offers -l westus -p Microsoft
        - name: List all offers from OpenLocic in westus
          text: az vm image list-offers -l westus -p OpenLogic
"""

helps['vm image list-publishers'] = """
    type: command
    short-summary: List the VM image publishers available on the Azure marketplace
    examples:
        - name: List all publishers in westus
          text: az vm image list-publishers -l westus
        - name: List all publishers with names starting with "Open" in westus
          text: az vm image list-publishers -l westus --query "[?starts_with(name, 'Open')]"
"""

helps['vm image list-skus'] = """
    type: command
    short-summary: List the VM image skus available on the Azure marketplace
    examples:
        - name: List all skus available for CentOS published by OpenLogic in westus
          text: az vm image list-skus -l westus -f CentOS -p OpenLogic
"""

helps['vm image show'] = """
    type: command
    short-summary: Show a VM image available on the Azure marketplace
    examples:
        - name: List all skus available for CentOS published by OpenLogic in westus
          text: >
            latest=$(az vm image list -p OpenLogic -s 7.3 --all --query \\
                "[?offer=='CentOS'].version" -o tsv | sort -u | tail -n 1)
            az vm image show -l westus -f CentOS -p OpenLogic --s 7.3 --version ${latest}
"""

helps['vm nic'] = """
    type: group
    short-summary: Manage VM network interfaces, see also 'az network nic'
    long-summary: >
        A network interface (NIC) is the interconnection between a Virtual Machine (VM) and the underlying software
        network. See https://docs.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface-overview
"""

helps['vm nic list'] = """
    type: command
    examples:
        - name: List all of the network interfaces on a VM
          text: az vm nic list -g group_name --vm-name vm-name
"""

helps['vm nic add'] = """
    type: command
    examples:
        - name: Add two network interfaces to a VM
          text: az vm nic add -g group_name --vm-name vm-name --nics nic_name1 nic_name2
"""

helps['vm nic remove'] = """
    type: command
    examples:
        - name: Remove two network interfaces to a VM
          text: az vm nic remove -g group_name --vm-name vm-name --nics nic_name1 nic_name2
"""

helps['vm nic show'] = """
    type: command
    examples:
        - name: Show details of a network interface on a VM
          text: az vm nic show -g group_name --vm-name vm-name --nic nic_name1
"""

helps['vm nic set'] = """
    type: command
    examples:
        - name: Set a network interface on a VM to be the primary network interface
          text: az vm nic set -g group_name --vm-name vm-name --nic nic_name1 nic_name2 --primary-nic nic_name2
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

deallocate_generalize_capture = """        - name: Process to deallocate, generalize, and capture a stopped virtual machine
          text: >
            az vm deallocate -g my_rg -n my-vm-name\n\r
            az vm generalize -g my_rg -n my-vm-name\n\r
            az vm capture -g my_rg -n my-vm-name --vhd-name-prefix my_prefix\n\r
        - name: Process to deallocate, generalize, and capture multiple stopped virtual machines
          text: >
            vms_ids=$(az vm list -g group_name --query "[].id" -o tsv)\n\r
            az vm deallocate --ids ${vms_ids}\n\r
            az vm generalize --ids ${vms_ids}\n\r
            az vm capture --ids ${vms_ids} --vhd-name-prefix my_prefix\n\r
"""

helps['vm capture'] = """
    type: command
    long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/ for an end-to-end tutorial
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm delete'] = """
    type: command
    examples:
        - name: Delete a virtual machine without prompt for confirmation
          text: >
            az vm delete -g group_name -n vm-name --force
{0}
""".format(vm_ids_example.format('Delete a virtual machine by Ids', 'vm delete'))

helps['vm deallocate'] = """
    type: command
    long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/ for an end-to-end tutorial
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm generalize'] = """
    type: command
    long-summary: See https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-linux-capture-image/ for an end-to-end tutorial
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm get-instance-view'] = """
    type: command
    short-summary: "Gets a VM including instance information (powerState)"
    examples:
        - name: Get instance view by name and resource group
          text: az vm get-instance-view -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Get instance view by Ids', 'vm get-instance-view'))

helps['vm list'] = """
    type: command
    examples:
        - name: List all VMs
          text: az vm list
        - name: List all VMs by group
          text: az vm list -g group_name
        - name: List all VMs by group with details
          text: az vm list -g group_name -d
"""

helps['vm list-ip-addresses'] = """
    type: command
    examples:
        - name: Get IP addresses for a VM
          text: az vm list-ip-addresses -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Get IP addresses for VMs by Ids', 'vm list-ip-addresses'))

helps['vm list-sizes'] = """
    type: command
    examples:
        - name: List available VM sizes in West US
          text: az vm list-sizes -l westus
"""

helps['vm list-usage'] = """
    type: command
    examples:
        - name: Get the compute resource usage for West US
          text: az vm list-usage -l westus
"""

helps['vm list-vm-resize-options'] = """
    type: command
    examples:
        - name: List all available VM sizes for resizing for a VM by resource group and VM name
          text: az vm list-vm-resize-options -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('List all available VM sizes for resizing by VM Ids', 'vm list-vm-resize-options'))

helps['vm open-port'] = """
    type: command
    examples:
        - name: Open all ports on a VM to inbound traffic by resource group and VM name
          text: az vm open-port -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Open all ports for multiple VMs by Ids', 'vm open-port'))

helps['vm redeploy'] = """
    type: command
    examples:
        - name: Redeploy VM by resource group and VM name
          text: az vm redeploy -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Redeploy VMs by VM Ids', 'vm redeploy'))

helps['vm resize'] = """
    type: command
    examples:
        - name: Resize VM by resource group and VM name
          text: az vm resize -g group_name -n vm-name --size Standard_DS3_v2
{0}
""".format(vm_ids_example.format('Resize VMs by VM Ids', 'vm redeploy --size Standard_DS3_v2'))

helps['vm restart'] = """
    type: command
    examples:
        - name: Restart VM by resource group and VM name
          text: az vm restart -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Restart VM by by VM Ids', 'vm restart'))

helps['vm show'] = """
    type: command
    examples:
        - name: Show VM details by resource group and VM name
          text: az vm show -g group_name -n vm-name -d
{0}
""".format(vm_ids_example.format('Show VM details by by VM Ids', 'vm show -d'))

helps['vm start'] = """
    type: command
    examples:
        - name: Start a stopped VM by resource group and VM name
          text: az vm start -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Start stopped VMs by by VM Ids', 'vm start'))

helps['vm stop'] = """
    type: command
    examples:
        - name: Stop a running VM by resource group and VM name
          text: az vm stop -g group_name -n vm-name
{0}
""".format(vm_ids_example.format('Stop running VMs by by VM Ids', 'vm stop'))

helps['vm wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the VM is met.
    examples:
        - name: Wait until VM is created
          text: az vm wait -g group_name -n vm-name --created
{0}
""".format(vm_ids_example.format('Wait until VMs are deleted by Ids', 'vm wait --deleted'))

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

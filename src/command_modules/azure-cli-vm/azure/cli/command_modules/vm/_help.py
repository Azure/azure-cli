# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines

from azure.cli.core.help_files import helps

image_long_summary = """                      URN aliases: CentOS, CoreOS, Debian, openSUSE, RHEL, SLES, UbuntuLTS, Win2008R2SP1, Win2012Datacenter, Win2012R2Datacenter.
                      Example URN: MicrosoftWindowsServer:WindowsServer:2012-R2-Datacenter:latest
                      Example Custom Image Resource ID or Name: /subscriptions/subscription-id/resourceGroups/MyResourceGroup/providers/Microsoft.Compute/images/MyImage
                      Example URI: http://<storageAccount>.blob.core.windows.net/vhds/osdiskimage.vhd
"""

vm_ids_example = """        - name: {0}
          text: >
            az {1} --ids $(az vm list -g MyResourceGroup --query "[].id" -o tsv)
"""

name_group_example = """        - name: {0} by Name and Group
          text: az {1} -n name -g MyResourceGroup
"""

helps['vm format-secret'] = """
    type: command
    long-summary: >
        Transform secrets into a form consumed by VMs and VMSS create via --secrets.
    examples:
        - name: Create a self-signed certificate with a the default policy and add to a virtual machine
          text: >
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm format-secret -s "$secrets") \n

            az vm create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
"""

helps['vm create'] = """
    type: command
    short-summary: Create an Azure Virtual Machine.
    long-summary: For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-quick-create-cli.
    parameters:
        - name: --image
          type: string
          short-summary: The name of the operating system image (URN alias, URN, Custom Image name or ID, or VHD Blob URI).
                         In many cases, this parameter is required, but can be replaced by others (for example, `--attach-os-disk`).
          long-summary: |
{0}
          populator-commands:
          - az vm image list
          - az vm image show
        - name: --ssh-key-value
          short-summary: The SSH public key or public key file path.
    examples:
        - name: Create a simple Ubuntu VM with automatic SSH authentication.
          text: >
            az vm create -n MyVm -g MyResourceGroup --image UbuntuLTS
        - name: Create a simple Windows Server VM with a private IP address.
          text: >
            az vm create -n MyVm -g MyResourceGroup
             --public-ip-address "" --image Win2012R2Datacenter
        - name: Create a VM from a custom managed image (see `az image create` for generation information).
          text: >
            az vm create -g MyResourceGroup -n MyVm --image MyImage
        - name: Create a VM by attaching to a specialized managed operating system disk.
          text: >
            az vm create -g MyResourceGroup -n MyVm --attach-os-disk MyOsDisk
            --os-type linux
        - name: Create an Ubuntu Linux VM and provide a cloud-init script (https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-using-cloud-init).
          text: >
            az vm create -g MyResourceGroup -n MyVm --image debian --custom_data MyCloudInitScript.yml
        - name: Create a Linux VM with SSH key authentication, add a public DNS entry, and then add it to an existing virtual network and availability set.
          text: >
            az vm create -n MyVm -g MyResourceGroup --image <linux image from 'az vm image list'>
            --vnet-name MyVnet --subnet subnet1
            --availability-set MyAvailabilitySet
            --public-ip-address-dns-name MyUniqueDnsName
            --ssh-key-value "<ssh-rsa-key, key-file-path or not specified for default-key-path>"
        - name: Create a simple Ubuntu Linux VM with a public IP address, DNS entry, 2 data disk(10GB, 20GB), and then generate ssh key pairs under ~/.ssh.
          text: >
            az vm create -n MyVm -g MyResourceGroup
            --public-ip-address-dns-name MyUniqueDnsName --image ubuntults --data-disk-sizes-gb 10 20
            --size Standard_DS2_v2 --generate-ssh-keys
        - name: Create an Debian VM and with Key Vault secrets. The secrets are placed in /var/lib/waagent and each certificate file is named with the hex thumbprint.
          text: >
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm format-secret -s "$secrets") \n

            az vm create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
""".format(image_long_summary)

helps['vmss create'] = """
    type: command
    short-summary: Create an Azure Virtual Machine Scale Set.
    long-summary: For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-linux-create-cli.
    parameters:
        - name: --image
          type: string
          short-summary: 'The name of the operating system image (URN alias, URN, or URI).'
          long-summary: |
{0}
    examples:
        - name: Create a Windows VM scale set with 5 instances, a load balancer, a public IP address, and a 2GB data disk.
          text: >
            az vmss create -n MyVmss -g MyResourceGroup --instance-count 5 --image Win2012R2Datacenter --data-disk-sizes-gb 2
        - name: Create a Linux VM scale set with an auto-generated ssh key pair under ~/.ssh, a public IP address, a DNS entry, an existing load balancer, and an existing virtual network.
          text: >
            az vmss create -n MyVmss -g MyResourceGroup --dns-name-for-public-ip MyGloballyUniqueDnsName
            --load-balancer MyLoadBalancer --vnet-name MyVnet --subnet MySubnet --image UbuntuLTS
            --generate-ssh-keys
        - name: Create a Linux VM scale set from a custom image using an existing ssh public key of ~/.ssh/id_rsa.pub.
          text: >
            az vmss create -n MyVmss -g MyResourceGroup --image MyImage
        - name: Create a Linux VM scale set with a cloud-init script (https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-using-cloud-init).
          text: >
            az vmss create -g MyResourceGroup -n MyVmss --image debian --custom_data MyCloudInitScript.yml
        - name: Create an Debian VM scaleset and with Key Vault secrets. The secrets are placed in /var/lib/waagent and each certificate file is named with the hex thumbprint.
          text: >
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm format-secret -s "$secrets") \n

            az vmss create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
""".format(image_long_summary)

helps['vm availability-set create'] = """
    type: command
    short-summary: Create an Azure Availability Set.
    long-summary: For more information, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-manage-availability.
    examples:
        - name: Create an availability set.
          text: az vm availability-set create -n MyAvSet -g MyResourceGroup --platform-fault-domain-count 2 --platform-update-domain-count 2
"""

helps['vm availability-set update'] = """
    type: command
    short-summary: Update an Azure Availability Set.
    examples:
        - name: Update an availability set.
          text: az vm availability-set update -n MyAvSet -g MyResourceGroup
        - name: Update an availability set tag.
          text: az vm availability-set update -n MyAvSet -g MyResourceGroup --set tags.foo=value
        - name: Remove an availability set tag.
          text: az vm availability-set update -n MyAvSet -g MyResourceGroup --remove tags.foo
"""

helps['vm availability-set convert'] = """
    type: command
    short-summary: Convert an Azure Availability Set to contain VMs with managed disks.
    examples:
        - name: Use the availability set name to convert it from using unmanaged disks to managed disks.
          text: vm availability-set convert -g MyResourceGroup -n MyAvSet
        - name: Use the availability set ID to convert it from using unmanaged disks to managed disks.
          text: >
            az vm availability-set convert --ids $(az vm availability-set \\
                list -g MyResourceGroup --query "[].id" -o tsv)
"""

helps['vm extension set'] = """
    type: command
    examples:
        - name: Add a user account to a Linux VM.
          text:
            az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 --vm-name MyVm --resource-group MyResourceGroup --protected-settings '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
"""

helps['vm availability-set delete'] = """
    type: command
    examples:
        - name: Delete an availability set.
          text: az vm availability-set delete -n MyAvSet -g MyResourceGroup
"""

helps['vm availability-set list'] = """
    type: command
    examples:
        - name: List availability sets.
          text: az vm availability-set list -g MyResourceGroup
"""

helps['vm availability-set list-sizes'] = """
    type: command
    examples:
        - name: List VM sizes for an availability set.
          text: az vm availability-set list-sizes -n MyAvSet -g MyResourceGroup
"""

helps['vm availability-set show'] = """
    type: command
    examples:
        - name: Get information about an availability set.
          text: az vm availability-set show -n MyAvSet -g MyResourceGroup
"""

helps['vm extension set'] = """
    type: command
    examples:
        - name: Add a user account to a Linux VM.
          text:
            az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 --vm-name MyVm
            --resource-group MyResourceGroup --protected-settings '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
"""

generic_update_help = """
        - name: Add or update a tag.
          text: az <command> -n name -g group --set tags.tagName=tagValue
        - name: Remove a tag.
          text: az <command> -n name -g group --remove tags.tagName
"""

helps['vm update'] = """
    type: command
    short-summary: Update the properties of a VM.
    long-summary: Update VM objects and properties using paths that correspond to 'az vm show'.
    examples:
{0}
        - name: Set the primary NIC of a VM.
          text: az <command> -n name -g group --set networkProfile.networkInterfaces[1].primary=false networkProfile.networkInterfaces[0].primary=true
        - name: Add a new non-primary NIC to a VM.
          text: az <command> -n name -g group --add networkProfile.networkInterfaces primary=false id=<NIC_ID>
        - name: Remove the fourth NIC from a VM.
          text: az <command> -n name -g group --remove networkProfile.networkInterfaces 3
""".format(generic_update_help)

helps['vmss get-instance-view'] = """
    type: command
    parameters:
        - name: --ids
          short-summary: "One or more VM scale sets or specific VM instance IDs. If provided, no other 'Resource Id' arguments should be specified."
"""

helps['vmss reimage'] = """
    type: command
    parameters:
        - name: --ids
          short-summary: "One or more VM scale sets or specific VM instance IDs. If provided, no other 'Resource Id' arguments should be specified."
"""

helps['vmss disk'] = """
    type: group
    short-summary: Manage the managed data disks associated with a virtual machine scale set.
"""

helps['vmss nic'] = """
    type: group
    short-summary: Manage the network interfaces associated with a virtual machine scale set.
"""

helps['vmss show'] = """
    type: command
    parameters:
        - name: --ids
          short-summary: "One or more VM scale sets or specific VM instance IDs. If provided, no other 'Resource Id' arguments should be specified."
"""

helps['vmss update'] = """
    type: command
    short-summary: Update a virtual machine scale set.
"""

helps['vmss wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the scale set is met.
"""

helps['vm convert'] = """
    type: command
    short-summary: Convert a VM with unmanaged disks to use managed disks.
    examples:
        - name: Convert a VM with unmanaged disks to use managed disks.
          text: az vm convert -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Convert VM with unmanaged disks to managed by Ids', 'vm convert'))

helps['vm'] = """
    type: group
    short-summary: Provision Linux or Windows virtual machines in seconds.
"""
helps['vm user'] = """
    type: group
    short-summary: Manage a user account on a VM.
"""

helps['vm user delete'] = """
    type: command
    long-summary: >
        Delete a user account from a VM without logging into it.
    examples:
        - name: Delete a user account.
          text: az vm user delete -u username -n MyVm -r MyResourceGroup
{0}
""".format(vm_ids_example.format('Delete User by VM Ids', 'az vm user delete -u username'))

helps['vm user reset-ssh'] = """
    type: command
    short-summary: Reset the SSH configuration on a VM.
    long-summary: >
        The extension will restart the SSH server, open the SSH port on your VM, and reset the SSH configuration to default values. The user account (name, password, or SSH keys) are not changed.
    examples:
        - name: Reset the SSH configuration.
          text: az vm user reset-ssh -n MyVm -r MyResourceGroup
{0}
""".format(vm_ids_example.format('Reset SSH by VM Ids', 'vm user reset-ssh'))

helps['vm user update'] = """
    type: command
    long-summary: Update a user account.
    examples:
        - name: Update a Windows user account.
          text: az vm user update -u username -p password -n MyVm -g MyResourceGroup
        - name: Update a Linux user account.
          text: az vm user update -u username --ssh-key-value "$(< ~/.ssh/id_rsa.pub)" -n MyVm -r MyResourceGroup
{0}
""".format(vm_ids_example.format('Set Linux User by VM Ids', 'vm user update -u username '
                                 '--ssh-key-value "$(< ~/.ssh/id_rsa.pub)"'))

helps['vm availability-set'] = """
    type: group
    short-summary: Group resources into availability sets for high-availability requirements.
    long-summary: >
        To provide redundancy to your application, it is recommended that you group two or more virtual machines in an availability set. This configuration ensures that during either a planned or unplanned maintenance event, at least one virtual machine will be available and meet the 99.95% Azure SLA.
"""

helps['vm boot-diagnostics'] = """
    type: group
    short-summary: Troubleshoot the start up of an Azure Virtual Machine.
    long-summary: >
        When bringing your own image to Azure or even booting one of the platform images, there can be many reasons why a VM gets into a non-bootable state. These features enable you to easily diagnose and recover your VMs from boot failures.
"""
vm_boot_diagnostics_disable = 'vm boot-diagnostics disable'
helps[vm_boot_diagnostics_disable] = """
    type: command
    short-summary: Disable the boot diagnostics on a VM.
    examples:
{0}
{1}
""".format(name_group_example.format('Disable boot diagnostics', vm_boot_diagnostics_disable),
           vm_ids_example.format('Disable boot diagnostics by VM Ids', vm_boot_diagnostics_disable))

vm_boot_diagnostics_enable = 'vm boot-diagnostics enable'
vm_boot_diagnostics_enable_cmd = "{0} --storage https://mystor.blob.core.windows.net/".format(vm_boot_diagnostics_enable)
helps[vm_boot_diagnostics_enable] = """
    type: command
    short-summary: Enable the boot diagnostics on a VM.
    examples:
{0}
{1}
""".format(name_group_example.format('Enable boot diagnostics', vm_boot_diagnostics_enable_cmd),
           vm_ids_example.format('Enable boot diagnostics by VM Ids', vm_boot_diagnostics_enable_cmd))

boot_diagnostics_log = 'vm boot-diagnostics get-boot-log'
helps[boot_diagnostics_log] = """
    type: command
    short-summary: Get the boot diagnostics log from a VM.
    examples:
{0}
{1}
""".format(name_group_example.format('Get boot diagnostics log', boot_diagnostics_log),
           vm_ids_example.format('Get boot diagnostics log by VM Ids', boot_diagnostics_log))

helps['acs'] = """
    type: group
    short-summary: Manage Azure Container Services.
"""

helps['acs create'] = """
    type: command
    short-summary: Create a container service with your preferred orchestrator.
    examples:
        - name: Create a Kubernetes container service and generate keys.
          text: >
            az acs create -g MyResourceGroup -n MyContainerService --orchestrator-type kubernetes --generate-ssh-keys
"""

helps['acs delete'] = """
    type: command
    short-summary: Delete a container service from your subscription.
"""

helps['acs list'] = """
    type: command
    short-summary: List the container services in your subscription.
"""

helps['acs show'] = """
    type: command
    short-summary: Show a container service in your subscription.
"""

helps['acs scale'] = """
    type: command
    short-summary: Change the private agent count of a container service.
"""

helps['vm diagnostics'] = """
    type: group
    short-summary: Configure the Azure Virtual Machine diagnostics extension.
"""

helps['vm diagnostics get-default-config'] = """
    type: command
    examples:
        - name: Get the default diagnostics on a Linux VM and override the storage account name and the VM resource ID.
          text: >
            az vm diagnostics get-default-config \\
                | sed "s#__DIAGNOSTIC_STORAGE_ACCOUNT__#MyStorageAccount#g" \\
                | sed "s#__VM_OR_VMSS_RESOURCE_ID__#MyVmResourceId#g"
        - name: Get the default diagnostics on a Windows VM.
          text: >
            az vm diagnostics get-default-config --is-windows-os
"""

helps['vm diagnostics set'] = """
    type: command
    short-summary: Configure the Azure VM diagnostics extension.
    examples:
        - name: Set up default diagnostics on a Linux VM for Azure Portal VM metrics graphs and syslog collection.
          text: >
            # Set the following 3 parameters correctly first.\n\r
            my_resource_group=<Resource group name containing your Linux VM and the storage account>\n\r
            my_linux_vm=<Your Azure Linux VM name>\n\r
            my_diagnostic_storage_account=<Your Azure storage account for storing VM diagnostic data>\n\r

            my_vm_resource_id=$(az vm show -g $my_resource_group -n $my_linux_vm --query "id" -o tsv)\n\r

            default_config=$(az vm diagnostics get-default-config \\
                | sed "s#__DIAGNOSTIC_STORAGE_ACCOUNT__#$my_diagnostic_storage_account#g" \\
                | sed "s#__VM_OR_VMSS_RESOURCE_ID__#$my_vm_resource_id#g")

            storage_sastoken=$(az storage account generate-sas \\
                --account-name $my_diagnostic_storage_account --expiry 9999-12-31T23:59Z \\
                --permissions wlacu --resource-types co --services bt -o tsv)

            protected_settings="{'storageAccountName': '${my_diagnostic_storage_account}', \\
                'storageAccountSasToken': '${storage_sastoken}'}"

            az vm diagnostics set --settings "${default_config}" \\
                --protected-settings "${protected_settings}" \\
                --resource-group $my_resource_group --vm-name $my_linux_vm
"""

disk_long_summary = """
        Just like any other computer, virtual machines in Azure use disks as a place to store an operating system, applications, and data. All Azure virtual machines have at least two disks - a Linux operating system disk (in the case of a Linux VM) and a temporary disk. The operating system disk is created from an image, and both the operating system disk and the image are actually virtual hard disks (VHDs) stored in an Azure storage account. Virtual machines also can have one or more data disks, that are also stored as VHDs.\n\r

        Operating System Disk\n\r
        Every virtual machine has one attached operating system disk. It's registered as a SATA drive and is labeled /dev/sda by default. This disk has a maximum capacity of 1023 gigabytes (GB).\n\r

        Temporary disk\n\r
        The temporary disk is automatically created for you. On Linux virtual machines, the disk is typically /dev/sdb and is formatted and mounted to /mnt/resource by the Azure Linux Agent. The size of the temporary disk varies, based on the size of the virtual machine.\n\r

        Data disk\n\r
        A data disk is a VHD that's attached to a virtual machine to store application data, or other data you need to keep. Data disks are registered as SCSI drives and are labeled with a letter that you choose. Each data disk has a maximum capacity of 1023 GB. The size of the virtual machine determines how many data disks you can attach to it and the type of storage you can use to host the disks.
"""

helps['vm disk'] = """
    type: group
    short-summary: Manage the managed data disks attached to a VM.
    long-summary: >
{0}
""".format(disk_long_summary)

helps['vm unmanaged-disk'] = """
    type: group
    short-summary: Manage the unmanaged data disks attached to a VM.
    long-summary: >
{0}
""".format(disk_long_summary)

helps['vm unmanaged-disk attach'] = """
    type: command
    long-summary: >
        Attach a persistent disk to your VM so that you can preserve your data, even if your VM is reprovisioned due to maintenance or resizing.
    examples:
        - name: Attach a new default sized (1023 GiB) data disk to a VM.
          text: az vm unmanaged-disk attach -g MyResourceGroup --vm-name MyVm
        - name: Attach an existing data disk to a VM.
          text: >
            az vm unmanaged-disk attach -g MyResourceGroup --vm-name MyVm \\
                --vhd-uri https://mystorage.blob.core.windows.net/vhds/d1.vhd
"""

helps['vm unmanaged-disk detach'] = """
    type: command
    examples:
        - name: Detach a data disk from a VM.
          text: >
            az vm unmanaged-disk detach -g MyResourceGroup --vm-name MyVm -n disk_name
"""

helps['vm unmanaged-disk list'] = """
    type: command
    examples:
        - name: List the disks attached to a VM.
          text: az vm unmanaged-disk list -g MyResourceGroup --vm-name MyVm
        - name: Use IDs of disks with names containing "data_disk" to list the disks attached to a VM.
          text: >
            az vm unmanaged-disk list --ids \\
                $(az resource list --query "[?contains(name, 'data_disk')].id" -o tsv)
"""

helps['vm disk detach'] = """
    type: command
    examples:
        - name: Detach a data disk from a VM.
          text: >
            az vm disk detach -g MyResourceGroup --vm-name MyVm -n disk_name
"""

helps['vm disk attach'] = """
    type: command
    long-summary: >
        Attach a persistent disk to your VM so that you can preserve your data, even if your VM is reprovisioned due to maintenance or resizing.
    examples:
        - name: Attach a new default sized (1023 GiB) data disk to a VM.
          text: az vm disk attach -g MyResourceGroup --vm-name MyVm --disk disk_name --new
"""

helps['vm encryption'] = """
    type: group
    short-summary: Manage encryption of VM disks.
"""

helps['vm extension'] = """
    type: group
    short-summary: Extend the functionality of your VMs with extensions.
    long-summary: >
        Extensions are small applications that provide post-deployment configuration and automation tasks on Azure virtual machines. For example, if a virtual machine requires software installation, anti-virus protection, or Docker configuration, a VM extension can be used to complete these tasks. Extensions can be bundled with a new virtual machine deployment or run against any existing system.
"""

helps['vm extension list'] = """
    type: command
    short-summary:  List the extensions attached to a VM in a resource group.
    examples:
        - name: Use the VM name to list the extensions attached to it.
          text: az vm extension list -g MyResourceGroup --vm-name MyVm
        - name: Use IDs to list the extensions with "MyExtension" in the name.
          text: >
            az vm extension list --ids \\
                $(az resource list --query "[?contains(name, 'MyExtension')].id" -o tsv)
"""

helps['vm extension delete'] = """
    type: command
    examples:
        - name: Use VM name and extension name to delete an extension from a VM.
          text: az vm extension delete -g MyResourceGroup --vm-name MyVm -n extension_name
        - name: Use IDs to delete extensions that contain "MyExtension" in the name.
          text: >
            az vm extension delete --ids \\
                $(az resource list --query "[?contains(name, 'MyExtension')].id" -o tsv)
"""

helps['vm extension show'] = """
    type: command
    examples:
        - name: Use VM name and extension name to show the extensions attached to a VM.
          text: az vm extension show -g MyResourceGroup --vm-name MyVm -n extension_name
"""

helps['vm extension image'] = """
    type: group
    short-summary: Find the available VM extensions for your subscription and region.
"""

helps['vm extension image list'] = """
    type: command
    examples:
        - name: List the unique publishers for extensions.
          text: az vm extension image list --query "[].publisher" -o tsv | sort -u
        - name: Find extensions with Docker in the name.
          text: az vm extension image list --query "[].name" -o tsv | sort -u | grep Docker
        - name: List extension names where publisher name starts with "Microsoft.Azure.App".
          text: >
            az vm extension image list --query \\
                "[?starts_with(publisher, 'Microsoft.Azure.App')].publisher" \\
                -o tsv | sort -u | xargs -I{} az vm extension image list-names --publisher {} -l westus
"""

helps['vm extension image list-names'] = """
    type: command
    examples:
        - name: Find the Docker extensions by publisher and location.
          text: >
            az vm extension image list-names --publisher Microsoft.Azure.Extensions \\
                -l westus --query "[?starts_with(name, 'Docker')]"
        - name: Find the CustomScript extensions by publisher and location.
          text: >
            az vm extension image list-names --publisher Microsoft.Azure.Extensions \\
                -l westus --query "[?starts_with(name, 'Custom')]"
"""

helps['vm extension image list-versions'] = """
    type: command
    examples:
        - name: Find the available versions for the Docker extension.
          text: >
            az vm extension image list-versions --publisher Microsoft.Azure.Extensions \\
                -l westus -n DockerExtension -otable
"""

helps['vm extension image show'] = """
    type: command
    examples:
        - name: Show the CustomScript extension version 2.0.2.
          text: >
            az vm extension image show -l westus -n CustomScript \\
              --publisher Microsoft.Azure.Extensions --version 2.0.2
        - name: Show the latest version of the Docker extension.
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
    short-summary: Virtual machine images that are available in the Azure Marketplace.
"""

helps['vm image list'] = """
    type: command
    short-summary: List the VM images available in the Azure Marketplace.
    examples:
        - name: List all available images.
          text: az vm image list --all
        - name: List all offline cached CentOS images.
          text: az vm image list -f CentOS
        - name: List all CentOS images.
          text: az vm image list -f CentOS --all
"""

helps['vm image list-offers'] = """
    type: command
    short-summary: List the VM image offers available in the Azure Marketplace.
    examples:
        - name: List all offers from Microsoft in westus.
          text: az vm image list-offers -l westus -p Microsoft
        - name: List all offers from OpenLocic in westus.
          text: az vm image list-offers -l westus -p OpenLogic
"""

helps['vm image list-publishers'] = """
    type: command
    short-summary: List the VM image publishers available in the Azure Marketplace.
    examples:
        - name: List all publishers in westus.
          text: az vm image list-publishers -l westus
        - name: List all publishers with names starting with "Open" in westus.
          text: az vm image list-publishers -l westus --query "[?starts_with(name, 'Open')]"
"""

helps['vm image list-skus'] = """
    type: command
    short-summary: List the VM image skus available in the Azure Marketplace.
    examples:
        - name: List all skus available for CentOS published by OpenLogic in westus.
          text: az vm image list-skus -l westus -f CentOS -p OpenLogic
"""

helps['vm image show'] = """
    type: command
    short-summary: Show a VM image available in the Azure Marketplace.
    examples:
        - name: List all skus available for CentOS published by OpenLogic in westus.
          text: >
            latest=$(az vm image list -p OpenLogic -s 7.3 --all --query \\
                "[?offer=='CentOS'].version" -o tsv | sort -u | tail -n 1)
            az vm image show -l westus -f CentOS -p OpenLogic --s 7.3 --version ${latest}
"""

helps['vm nic'] = """
    type: group
    short-summary: Manage network interfaces, see also 'az network nic'.
    long-summary: >
        A network interface (NIC) is the interconnection between a VM and the underlying software
        network. For more information, see https://docs.microsoft.com/azure/virtual-network/virtual-network-network-interface-overview.
"""

helps['vm nic list'] = """
    type: command
    examples:
        - name: List all of the NICs on a VM.
          text: az vm nic list -g MyResourceGroup --vm-name MyVm
"""

helps['vm nic add'] = """
    type: command
    examples:
        - name: Add two NICs to a VM.
          text: az vm nic add -g MyResourceGroup --vm-name MyVm --nics nic_name1 nic_name2
"""

helps['vm nic remove'] = """
    type: command
    examples:
        - name: Remove two NICs from a VM.
          text: az vm nic remove -g MyResourceGroup --vm-name MyVm --nics nic_name1 nic_name2
"""

helps['vm nic show'] = """
    type: command
    examples:
        - name: Show details of a NIC on a VM.
          text: az vm nic show -g MyResourceGroup --vm-name MyVm --nic nic_name1
"""

helps['vm nic set'] = """
    type: command
    examples:
        - name: Set a NIC on a VM to be primary.
          text: az vm nic set -g MyResourceGroup --vm-name MyVm --nic nic_name1 nic_name2 --primary-nic nic_name2
"""

helps['vmss'] = """
    type: group
    short-summary: Create highly available, auto-scalable Linux or Windows virtual machines.
"""

helps['vmss diagnostics'] = """
    type: group
    short-summary: Configure the Azure Virtual Machine Scale Set diagnostics extension.
"""

helps['vmss list-instance-connection-info'] = """
    type: command
    short-summary: Get the IP address and port number used to connect to individual instances.
"""

helps['vmss extension'] = """
    type: group
    short-summary: Extend the functionality of your VM scale set with extensions.
"""

helps['vmss extension image'] = """
    type: group
    short-summary: Find VM scale set extension available for your subscription and region.
"""

deallocate_generalize_capture = """        - name: Process to deallocate, generalize, and capture a stopped virtual machine
          text: >
            az vm deallocate -g MyResourceGroup -n MyVm\n\r
            az vm generalize -g MyResourceGroup -n MyVm\n\r
            az vm capture -g MyResourceGroup -n MyVm --vhd-name-prefix MyPrefix\n\r
        - name: The process to deallocate, generalize, and capture multiple stopped virtual machines.
          text: >
            vms_ids=$(az vm list -g MyResourceGroup --query "[].id" -o tsv)\n\r
            az vm deallocate --ids ${vms_ids}\n\r
            az vm generalize --ids ${vms_ids}\n\r
            az vm capture --ids ${vms_ids} --vhd-name-prefix MyPrefix\n\r
"""

helps['vm capture'] = """
    type: command
    long-summary: For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image.
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm delete'] = """
    type: command
    examples:
        - name: Delete a VM without a prompt for confirmation.
          text: >
            az vm delete -g MyResourceGroup -n MyVm --yes
{0}
""".format(vm_ids_example.format('Delete a virtual machine by Ids', 'vm delete'))

helps['vm deallocate'] = """
    type: command
    long-summary: For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image.
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm generalize'] = """
    type: command
    long-summary: For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image.
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm get-instance-view'] = """
    type: command
    short-summary: "Get information about a VM including instance information (powerState)."
    examples:
        - name: Use resource group and name to get instance view information of a VM.
          text: az vm get-instance-view -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Get instance view by Ids', 'vm get-instance-view'))

helps['vm list'] = """
    type: command
    short-summary: List information about Virtual Machines.
    long-summary: For more information on querying information about Virtual Machines, see https://docs.microsoft.com/en-us/cli/azure/query-az-cli2.
    examples:
        - name: List all VMs.
          text: az vm list
        - name: List all VMs by resource group.
          text: az vm list -g MyResourceGroup
        - name: List all VMs by resource group with details.
          text: az vm list -g MyResourceGroup -d
"""

helps['vm list-ip-addresses'] = """
    type: command
    examples:
        - name: Get the IP addresses for a VM.
          text: az vm list-ip-addresses -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Get IP addresses for VMs by Ids', 'vm list-ip-addresses'))

helps['vm list-sizes'] = """
    type: command
    examples:
        - name: List the available VM sizes in West US.
          text: az vm list-sizes -l westus
"""

helps['vm list-usage'] = """
    type: command
    examples:
        - name: Get the compute resource usage for West US.
          text: az vm list-usage -l westus
"""

helps['vm list-vm-resize-options'] = """
    type: command
    examples:
        - name: List all available VM sizes for resizing.
          text: az vm list-vm-resize-options -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('List all available VM sizes for resizing by VM Ids', 'vm list-vm-resize-options'))

helps['vm open-port'] = """
    type: command
    examples:
        - name: Open all ports on a VM to inbound traffic.
          text: az vm open-port -g MyResourceGroup -n MyVm --port *
        - name: Open a range of ports on a VM to inbound traffic with the highest priority.
          text: az vm open-port -g MyResourceGroup -n MyVm --port 80-100 --priority 100
{0}
""".format(vm_ids_example.format('Open all ports for multiple VMs by Ids', 'vm open-port'))

helps['vm redeploy'] = """
    type: command
    examples:
        - name: Redeploy a VM.
          text: az vm redeploy -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Redeploy VMs by VM Ids', 'vm redeploy'))

helps['vm resize'] = """
    type: command
    short-summary: Update VM size.
    examples:
        - name: Resize a VM.
          text: az vm resize -g MyResourceGroup -n MyVm --size Standard_DS3_v2
{0}
""".format(vm_ids_example.format('Resize VMs by VM Ids', 'vm redeploy --size Standard_DS3_v2'))

helps['vm restart'] = """
    type: command
    examples:
        - name: Restart a VM.
          text: az vm restart -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Restart VM by by VM Ids', 'vm restart'))

helps['vm show'] = """
    type: command
    short-summary: Show details of a VM.
    examples:
        - name: Show information about a VM.
          text: az vm show -g MyResourceGroup -n MyVm -d
{0}
""".format(vm_ids_example.format('Show VM details by by VM Ids', 'vm show -d'))

helps['vm start'] = """
    type: command
    examples:
        - name: Start a stopped VM.
          text: az vm start -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Start stopped VMs by by VM Ids', 'vm start'))

helps['vm stop'] = """
    type: command
    examples:
        - name: Stop a running VM.
          text: az vm stop -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Stop running VMs by by VM Ids', 'vm stop'))

helps['vm wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the VM is met.
    examples:
        - name: Wait until the VM is created.
          text: az vm wait -g MyResourceGroup -n MyVm --created
{0}
""".format(vm_ids_example.format('Wait until VMs are deleted by Ids', 'vm wait --deleted'))

helps['disk'] = """
    type: group
    short-summary: Manage Azure Managed Disks.
"""

helps['snapshot'] = """
    type: group
    short-summary: Manage point-in-time copies of managed disks, native blobs, or other snapshots.
"""

helps['image'] = """
    type: group
    short-summary: Manage custom Virtual Machine Images.
"""

helps['disk create'] = """
    type: command
    short-summary: Create a managed disk.
    examples:
        - name: Create a managed disk by importing from a blob uri.
          text: az disk create -g MyResourceGroup -n MyDisk --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd
        - name: Create an empty managed disk.
          text: az disk create -g MyResourceGroup -n MyDisk --size-gb 10
        - name: Create a managed disk by copying from an existing disk or snapshot.
          text: az disk create -g MyResourceGroup -n MyDisk2 --source MyDisk
"""

helps['disk list'] = """
    type: command
    short-summary: List managed disks.
"""

helps['disk delete'] = """
    type: command
    short-summary: Delete a managed disk.
"""

helps['disk update'] = """
    type: command
    short-summary: Update a managed disk.
"""

helps['disk wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the managed disk is met.
"""


helps['disk grant-access'] = """
    type: command
    short-summary: Grant read access to a managed disk.
"""

helps['disk revoke-access'] = """
    type: command
    short-summary: Revoke read access to a managed disk.
"""

helps['snapshot create'] = """
    type: command
    short-summary: Create a snapshot.
    examples:
        - name: Create a snapshot by importing from a blob uri.
          text: az snapshot create -g MyResourceGroup -n MySnapshot --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd
        - name: Create an empty snapshot.
          text: az snapshot create -g MyResourceGroup -n MySnapshot --size-gb 10
        - name: Create a snapshot by copying from an existing disk in the same resource group.
          text: az snapshot create -g MyResourceGroup -n MySnapshot2 --source MyDisk
"""

helps['snapshot update'] = """
    type: command
    short-summary: Update a snapshot.
"""

helps['snapshot list'] = """
    type: command
    short-summary: List snapshots.
"""

helps['snapshot grant-access'] = """
    type: command
    short-summary: Grant read access to a snapshot.
"""

helps['snapshot revoke-access'] = """
    type: command
    short-summary: Revoke read access to a snapshot.
"""

helps['image create'] = """
    type: command
    short-summary: Create a custom Virtual Machine Image from managed disks or snapshots.
    examples:
        - name: Create an image from an existing disk.
          text: az image create -g MyResourceGroup -n image1 --os-type Linux --source /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/rg1/providers/Microsoft.Compute/snapshots/s1 --data-snapshot /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/rg/providers/Microsoft.Compute/snapshots/s2
        - name: Create an image by capturing an existing generalized virtual machine in the same resource group.
          text: az image create -g MyResourceGroup -n image1 --source MyVm1
"""

helps['image list'] = """
    type: command
    short-summary: List custom VM images.
"""

# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines

from knack.help_files import helps

vm_ids_example = """        - name: {0}
          text: >
            az {1} --ids $(az vm list -g MyResourceGroup --query "[].id" -o tsv)
"""

helps['vm secret'] = """
    type: group
    short-summary: Manage VM secrets.
"""

helps['vm secret add'] = """
    type: command
    short-summary: Add a secret to a VM.
"""

helps['vm secret list'] = """
    type: command
    short-summary: List secrets on a VM.
"""

helps['vm secret remove'] = """
    type: command
    short-summary: Remove a secret from a VM.
"""

helps['vm secret format'] = """
    type: command
    short-summary: Transform secrets into a form that can be used by VMs and VMSSes.
    parameters:
        - name: --secrets -s
          long-summary: >
            The command will attempt to resolve the vault ID for each secret. If it is unable to do so,
            specify the vault ID to use for *all* secrets using: --keyvault NAME --resource-group NAME | --keyvault ID.
    examples:
        - name: Create a self-signed certificate with the default policy, and add it to a virtual machine.
          text: >
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm secret format -s "$secrets")

            az vm create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
"""

helps['vm create'] = """
    type: command
    short-summary: Create an Azure Virtual Machine.
    long-summary: 'For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-quick-create-cli.'
    parameters:
        - name: --image
          type: string
          short-summary: >
            The name of the operating system image as a URN alias, URN, custom image name or ID, or VHD blob URI.
            This parameter is required unless using `--attach-os-disk.`
          populator-commands:
          - az vm image list
          - az vm image show
        - name: --ssh-key-value
          short-summary: The SSH public key or public key file path.
    examples:
        - name: Create a default Ubuntu VM with automatic SSH authentication.
          text: >
            az vm create -n MyVm -g MyResourceGroup --image UbuntuLTS
        - name: Create a default Windows Server VM with a private IP address.
          text: >
            az vm create -n MyVm -g MyResourceGroup --public-ip-address "" --image Win2012R2Datacenter
        - name: Create a VM from a custom managed image.
          text: >
            az vm create -g MyResourceGroup -n MyVm --image MyImage
        - name: Create a VM by attaching to a managed operating system disk.
          text: >
            az vm create -g MyResourceGroup -n MyVm --attach-os-disk MyOsDisk --os-type linux
        - name: 'Create an Ubuntu Linux VM using a cloud-init script for configuration. See: https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-using-cloud-init.'
          text: >
            az vm create -g MyResourceGroup -n MyVm --image debian --custom-data MyCloudInitScript.yml
        - name: Create a Debian VM with SSH key authentication and a public DNS entry, located on an existing virtual network and availability set.
          text: |
            az vm create -n MyVm -g MyResourceGroup --image debian --vnet-name MyVnet --subnet subnet1 \\
                --availability-set MyAvailabilitySet --public-ip-address-dns-name MyUniqueDnsName \\
                --ssh-key-value @key-file
        - name: Create a simple Ubuntu Linux VM with a public IP address, DNS entry, two data disks (10GB and 20GB), and then generate ssh key pairs.
          text: |
            az vm create -n MyVm -g MyResourceGroup --public-ip-address-dns-name MyUniqueDnsName \\
                --image ubuntults --data-disk-sizes-gb 10 20 --size Standard_DS2_v2 \\
                --generate-ssh-keys
        - name: Create a Debian VM using Key Vault secrets.
          text: >
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm secret format -s "$secrets") \n

            az vm create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
        - name: Create a CentOS VM with a system assigned identity. The VM will have a 'Contributor' role with access to a storage account.
          text: >
             az vm create -n MyVm -g rg1 --image centos --assign-identity --scope /subscriptions/99999999-1bf0-4dda-aec3-cb9272f09590/MyResourceGroup/myRG/providers/Microsoft.Storage/storageAccounts/storage1
        - name: Create a debian VM with a user assigned identity.
          text: >
             az vm create -n MyVm -g rg1 --image debian --assign-identity  /subscriptions/99999999-1bf0-4dda-aec3-cb9272f09590/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
        - name: Create a debian VM with both system and user assigned identity.
          text: >
             az vm create -n MyVm -g rg1 --image debian --assign-identity  [system] /subscriptions/99999999-1bf0-4dda-aec3-cb9272f09590/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
        - name: Create a VM in an availability zone in the current resource group's region
          min_profile: latest
          text: >
             az vm create -n MyVm -g MyResourceGroup --image Centos --zone 1
"""

helps['vmss create'] = """
    type: command
    short-summary: Create an Azure Virtual Machine Scale Set.
    long-summary: 'For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-linux-create-cli.'
    parameters:
        - name: --image
          type: string
          short-summary: The name of the operating system image as a URN alias, URN, or URI.
    examples:
        - name: Create a Windows VM scale set with 5 instances, a load balancer, a public IP address, and a 2GB data disk.
          text: >
            az vmss create -n MyVmss -g MyResourceGroup --instance-count 5 --image Win2016Datacenter --data-disk-sizes-gb 2
        - name: Create a Linux VM scale set with an auto-generated ssh key pair, a public IP address, a DNS entry, an existing load balancer, and an existing virtual network.
          text: |
            az vmss create -n MyVmss -g MyResourceGroup --dns-name-for-public-ip MyGloballyUniqueDnsName \\
                --load-balancer MyLoadBalancer --vnet-name MyVnet --subnet MySubnet --image UbuntuLTS \\
                --generate-ssh-keys
        - name: Create a Linux VM scale set from a custom image using the default existing public SSH key.
          text: >
            az vmss create -n MyVmss -g MyResourceGroup --image MyImage
        - name: Create a Linux VM scale set with a load balancer and custom DNS servers. Each VM has a public-ip address and a custom domain name.
          text: >
            az vmss create -n MyVmss -g MyResourceGroup --image centos \\
                --public-ip-per-vm --vm-domain-name myvmss --dns-servers 10.0.0.6 10.0.0.5
        - name: 'Create a Linux VM scale set using a cloud-init script for configuration. See: https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-using-cloud-init'
          text: >
            az vmss create -g MyResourceGroup -n MyVmss --image debian --custom-data MyCloudInitScript.yml
        - name: Create a Debian VM scaleset using Key Vault secrets.
          text: >
            az keyvault certificate create --vault-name vaultname -n cert1 \\
              -p "$(az keyvault certificate get-default-policy)"

            secrets=$(az keyvault secret list-versions --vault-name vaultname \\
              -n cert1 --query "[?attributes.enabled].id" -o tsv)

            vm_secrets=$(az vm secret format -s "$secrets") \n

            az vmss create -g group-name -n vm-name --admin-username deploy  \\
              --image debian --secrets "$vm_secrets"
        - name: Create a VM scaleset with system assigned identity. The VM will have a 'Contributor' Role with access to a storage account.
          text: >
             az vmss create -n MyVmss -g MyResourceGroup --image centos --assign-identity --scope /subscriptions/99999999-1bf0-4dda-aec3-cb9272f09590/MyResourceGroup/myRG/providers/Microsoft.Storage/storageAccounts/storage1
        - name: Create a debian VM scaleset with a user assigned identity.
          text: >
             az vmss create -n MyVmss -g rg1 --image debian --assign-identity  /subscriptions/99999999-1bf0-4dda-aec3-cb9272f09590/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
        - name: Create a debian VM scaleset with both system and user assigned identity.
          text: >
             az vmss create -n MyVmss -g rg1 --image debian --assign-identity  [system] /subscriptions/99999999-1bf0-4dda-aec3-cb9272f09590/resourcegroups/myRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/myID
        - name: Create a single zone VM scaleset in the current resource group's region
          min_profile: latest
          text: >
             az vmss create -n MyVmss -g MyResourceGroup --image Centos --zones 1
"""

helps['vm availability-set create'] = """
    type: command
    short-summary: Create an Azure Availability Set.
    long-summary: 'For more information, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-manage-availability.'
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
        - name: Convert an availabiity set to use managed disks by name.
          text: az vm availability-set convert -g MyResourceGroup -n MyAvSet
        - name: Convert an availability set to use managed disks by ID.
          text: >
            az vm availability-set convert --ids $(az vm availability-set list -g MyResourceGroup --query "[].id" -o tsv)
"""

helps['vm extension set'] = """
    type: command
    short-summary: Set extensions for a VM.
    long-summary: Get extension details from `az vm extension image list`.
    examples:
        - name: Add a user account to a Linux VM.
          text: |
            az vm extension set -n VMAccessForLinux --publisher Microsoft.OSTCExtensions --version 1.4 \\
                --vm-name MyVm --resource-group MyResourceGroup \\
                --protected-settings '{"username":"user1", "ssh_key":"ssh_rsa ..."}'
"""

helps['vm extension wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of a virtual machine extension is met.
"""

helps['vm availability-set delete'] = """
    type: command
    short-summary: Delete an availability set.
    examples:
        - name: Delete an availability set.
          text: az vm availability-set delete -n MyAvSet -g MyResourceGroup
"""

helps['vm availability-set list'] = """
    type: command
    short-summary: List availability sets.
    examples:
        - name: List availability sets.
          text: az vm availability-set list -g MyResourceGroup
"""

helps['vm availability-set list-sizes'] = """
    type: command
    short-summary: List VM sizes for an availability set.
    examples:
        - name: List VM sizes for an availability set.
          text: az vm availability-set list-sizes -n MyAvSet -g MyResourceGroup
"""

helps['vm availability-set show'] = """
    type: command
    short-summary: Get information for an availability set.
    examples:
        - name: Get information about an availability set.
          text: az vm availability-set show -n MyAvSet -g MyResourceGroup
"""

helps['vm update'] = """
    type: command
    short-summary: Update the properties of a VM.
    long-summary: Update VM objects and properties using paths that correspond to 'az vm show'.
    examples:
        - name: Add or update a tag.
          text: az vm update -n name -g group --set tags.tagName=tagValue
        - name: Remove a tag.
          text: az vm update -n name -g group --remove tags.tagName
        - name: Set the primary NIC of a VM.
          text: az vm update -n name -g group --set networkProfile.networkInterfaces[1].primary=false networkProfile.networkInterfaces[0].primary=true
        - name: Add a new non-primary NIC to a VM.
          text: az vm update -n name -g group --add networkProfile.networkInterfaces primary=false id=<NIC_ID>
        - name: Remove the fourth NIC from a VM.
          text: az vm update -n name -g group --remove networkProfile.networkInterfaces 3
"""

helps['vmss deallocate'] = """
    type: command
    short-summary: Deallocate VMs within a VMSS.
"""

helps['vmss delete-instances'] = """
    type: command
    short-summary: Delete VMs within a VMSS.
"""

helps['vmss get-instance-view'] = """
    type: command
    short-summary: View an instance of a VMSS.
    parameters:
        - name: --instance-id
          short-summary: A VM instance ID or "*" to list instance view for all VMs in a scale set.

"""

helps['vmss list'] = """
    type: command
    short-summary: List VMSS.
"""

helps['vmss reimage'] = """
    type: command
    short-summary: Reimage VMs within a VMSS.
    parameters:
        - name: --instance-id
          short-summary: VM instance ID. If missing, reimage all instances.
"""

helps['vmss restart'] = """
    type: command
    short-summary: Restart VMs within a VMSS.
"""

helps['vmss scale'] = """
    type: command
    short-summary: Change the number of VMs within a VMSS.
    parameters:
        - name: --new-capacity
          short-summary: Number of VMs in the VMSS.
"""

helps['vmss show'] = """
    type: command
    short-summary: Get details on VMs within a VMSS.
    parameters:
        - name: --instance-id
          short-summary: VM instance ID. If missing, show the VMSS.
"""

helps['vmss start'] = """
    type: command
    short-summary: Start VMs within a VMSS.
"""

helps['vmss stop'] = """
    type: command
    short-summary: Power off (stop) VMs within a VMSS.
"""

helps['vmss update'] = """
    type: command
    short-summary: Update a VMSS.
"""

helps['vmss update-instances'] = """
    type: command
    short-summary: Upgrade VMs within a VMSS.
"""

helps['vmss wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of a scale set is met.
"""

helps['vmss disk'] = """
    type: group
    short-summary: Manage data disks of a VMSS.
"""

helps['vmss disk attach'] = """
    type: command
    short-summary: Attach managed data disks to a scale set or its instances.
"""

helps['vmss disk detach'] = """
    type: command
    short-summary: Detach managed data disks from a scale set or its instances.
"""

helps['vmss nic'] = """
    type: group
    short-summary: Manage network interfaces of a VMSS.
"""

helps['vmss rolling-upgrade'] = """
    type: group
    short-summary: (PREVIEW) Manage rolling upgrades.
"""

helps['vm convert'] = """
    type: command
    short-summary: Convert a VM with unmanaged disks to use managed disks.
    examples:
        - name: Convert a VM with unmanaged disks to use managed disks.
          text: az vm convert -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Convert all VMs with unmanaged disks in a resource group to use managed disks.', 'vm convert'))

helps['vm'] = """
    type: group
    short-summary: Manage Linux or Windows virtual machines.
"""
helps['vm user'] = """
    type: group
    short-summary: Manage user accounts for a VM.
"""

helps['vm user delete'] = """
    type: command
    short-summary: Delete a user account from a VM.
    examples:
        - name: Delete a user account.
          text: az vm user delete -u username -n MyVm -g MyResourceGroup
{0}
""".format(vm_ids_example.format('Delete a user on all VMs in a resource group.', 'az vm user delete -u username'))

helps['vm user reset-ssh'] = """
    type: command
    short-summary: Reset the SSH configuration on a VM.
    long-summary: >
        The extension will restart the SSH service, open the SSH port on your VM, and reset the SSH configuration to default values. The user account (name, password, and SSH keys) are not changed.
    examples:
        - name: Reset the SSH configuration.
          text: az vm user reset-ssh -n MyVm -g MyResourceGroup
{0}
""".format(vm_ids_example.format("Reset the SSH server on all VMs in a resource group.", 'vm user reset-ssh'))

helps['vm user update'] = """
    type: command
    short-summary: Update a user account.
    parameters:
        - name: --ssh-key-value
          short-summary: SSH public key file value or public key file path
    examples:
        - name: Update a Windows user account.
          text: az vm user update -u username -p password -n MyVm -g MyResourceGroup
        - name: Update a Linux user account.
          text: az vm user update -u username --ssh-key-value "$(< ~/.ssh/id_rsa.pub)" -n MyVm -g MyResourceGroup
{0}
""".format(vm_ids_example.format('Update a user on all VMs in a resource group.',
                                 'vm user update -u username --ssh-key-value "$(< ~/.ssh/id_rsa.pub)"'))

helps['vm availability-set'] = """
    type: group
    short-summary: Group resources into availability sets.
    long-summary: >
        To provide redundancy to an application, it is recommended to group two or more virtual machines in an availability set.
        This configuration ensures that during either a planned or unplanned maintenance event, at least one virtual machine
        will be available.
"""

helps['vm boot-diagnostics'] = """
    type: group
    short-summary: Troubleshoot the startup of an Azure Virtual Machine.
    long-summary: Use this feature to troubleshoot boot failures for custom or platform images.
"""

vm_boot_diagnostics_disable = 'vm boot-diagnostics disable'
helps[vm_boot_diagnostics_disable] = """
    type: command
    short-summary: Disable the boot diagnostics on a VM.
    examples:
{0}
""".format(vm_ids_example.format('Disable boot diagnostics on all VMs in a resource group.', vm_boot_diagnostics_disable))

vm_boot_diagnostics_enable = 'vm boot-diagnostics enable'
vm_boot_diagnostics_enable_cmd = "{0} --storage https://mystor.blob.core.windows.net/".format(vm_boot_diagnostics_enable)
helps[vm_boot_diagnostics_enable] = """
    type: command
    short-summary: Enable the boot diagnostics on a VM.
    parameters:
        - name: --storage
          short-summary: Name or URI of a storage account (e.g. https://your_storage_account_name.blob.core.windows.net/)
    examples:
{0}
""".format(vm_ids_example.format('Enable boot diagnostics on all VMs in a resource group.', vm_boot_diagnostics_enable_cmd))

boot_diagnostics_log = 'vm boot-diagnostics get-boot-log'
helps[boot_diagnostics_log] = """
    type: command
    short-summary: Get the boot diagnostics log from a VM.
    examples:
{0}
""".format(vm_ids_example.format('Get diagnostics logs for all VMs in a resource group.', boot_diagnostics_log))

helps['acs'] = """
    type: group
    short-summary: Manage Azure Container Services.
"""

helps['acs create'] = """
    type: command
    short-summary: Create a container service.
    examples:
        - name: Create a Kubernetes container service and generate SSH keys to connect to it.
          text: >
            az acs create -g MyResourceGroup -n MyContainerService --orchestrator-type kubernetes --generate-ssh-keys
"""

helps['acs delete'] = """
    type: command
    short-summary: Delete a container service.
"""

helps['acs list'] = """
    type: command
    short-summary: List container services.
"""

helps['acs show'] = """
    type: command
    short-summary: Get the details for a container service.
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
    short-summary: Get the default configuration settings for a VM.
    examples:
        - name: Get the default diagnostics for a Linux VM and override the storage account name and the VM resource ID.
          text: |
            az vm diagnostics get-default-config \\
                | sed "s#__DIAGNOSTIC_STORAGE_ACCOUNT__#MyStorageAccount#g" \\
                | sed "s#__VM_OR_VMSS_RESOURCE_ID__#MyVmResourceId#g"
        - name: Get the default diagnostics for a Windows VM.
          text: >
            az vm diagnostics get-default-config --is-windows-os
"""

helps['vm diagnostics set'] = """
    type: command
    short-summary: Configure the Azure VM diagnostics extension.
    examples:
        - name: Set up default diagnostics on a Linux VM for Azure Portal VM metrics graphs and syslog collection.
          text: >
            # Set the following 3 parameters first.\n
            my_resource_group=<Resource group name containing your Linux VM and the storage account>\n
            my_linux_vm=<Your Azure Linux VM name>\n
            my_diagnostic_storage_account=<Your Azure storage account for storing VM diagnostic data>\n

            my_vm_resource_id=$(az vm show -g $my_resource_group -n $my_linux_vm --query "id" -o tsv)\n

            default_config=$(az vm diagnostics get-default-config \\
                | sed "s#__DIAGNOSTIC_STORAGE_ACCOUNT__#$my_diagnostic_storage_account#g" \\
                | sed "s#__VM_OR_VMSS_RESOURCE_ID__#$my_vm_resource_id#g")

            storage_sastoken=$(az storage account generate-sas \\
                --account-name $my_diagnostic_storage_account --expiry 2037-12-31T23:59:00Z \\
                --permissions wlacu --resource-types co --services bt -o tsv)

            protected_settings="{'storageAccountName': '{my_diagnostic_storage_account}', \\
                'storageAccountSasToken': '{storage_sastoken}'}"

            az vm diagnostics set --settings "{default_config}" \\
                --protected-settings "{protected_settings}" \\
                --resource-group $my_resource_group --vm-name $my_linux_vm
"""

disk_long_summary = """
        Just like any other computer, virtual machines in Azure use disks as a place to store an operating system, applications, and data.
        All Azure virtual machines have at least two disks: An operating system disk, and a temporary disk.
        The operating system disk is created from an image, and both the operating system disk and the image are actually virtual hard disks (VHDs)
        stored in an Azure storage account. Virtual machines also can have one or more data disks, that are also stored as VHDs.

        Operating System Disk
        Every virtual machine has one attached operating system disk. It's registered as a SATA drive and is labeled /dev/sda by default.
        This disk has a maximum capacity of 1023 gigabytes (GB).

        Temporary disk
        The temporary disk is automatically created for you. On Linux virtual machines, the disk is typically /dev/sdb and is formatted and
        mounted to /mnt/resource by the Azure Linux Agent. The size of the temporary disk varies, based on the size of the virtual machine.

        Data disk
        A data disk is a VHD that's attached to a virtual machine to store application data, or other data you need to keep. Data disks are
        registered as SCSI drives and are labeled by the creator. Each data disk has a maximum capacity of 1023 GB. The size of the virtual
        machine determines how many data disks can be attached and the type of storage that can be used to host the disks.
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
    short-summary: Attach an unmanaged persistent disk to a VM.
    long-summary: This allows for the preservation of data, even if the VM is reprovisioned due to maintenance or resizing.
    examples:
        - name: Attach a new default sized (1023 GB) unmanaged data disk to a VM.
          text: az vm unmanaged-disk attach -g MyResourceGroup --vm-name MyVm
        - name: Attach an existing data disk to a VM as unmanaged.
          text: >
            az vm unmanaged-disk attach -g MyResourceGroup --vm-name MyVm \\
                --vhd-uri https://mystorage.blob.core.windows.net/vhds/d1.vhd
"""

helps['vm unmanaged-disk detach'] = """
    type: command
    short-summary: Detach an unmanaged disk from a VM.
    examples:
        - name: Detach a data disk from a VM.
          text: >
            az vm unmanaged-disk detach -g MyResourceGroup --vm-name MyVm -n disk_name
"""

helps['vm unmanaged-disk list'] = """
    type: command
    short-summary: List unmanaged disks of a VM.
    examples:
        - name: List the unmanaged disks attached to a VM.
          text: az vm unmanaged-disk list -g MyResourceGroup --vm-name MyVm
        - name: List unmanaged disks with IDs containing the string "data_disk".
          text: >
            az vm unmanaged-disk list --ids \\
                $(az resource list --query "[?contains(name, 'data_disk')].id" -o tsv)
"""

helps['vm disk detach'] = """
    type: command
    short-summary: Detach a managed disk from a VM.
    examples:
        - name: Detach a data disk from a VM.
          text: >
            az vm disk detach -g MyResourceGroup --vm-name MyVm -n disk_name
"""

helps['vm disk attach'] = """
    type: command
    short-summary: Attach a managed persistent disk to a VM.
    long-summary: This allows for the preservation of data, even if the VM is reprovisioned due to maintenance or resizing.
    examples:
        - name: Attach a new default sized (1023 GB) managed data disk to a VM.
          text: az vm disk attach -g MyResourceGroup --vm-name MyVm --disk disk_name --new
"""

helps['vm encryption'] = """
    type: group
    short-summary: Manage encryption of VM disks.
"""

helps['vm encryption enable'] = """
    type: command
    short-summary: Enable disk encryption on the OS disk and/or data disks.
    parameters:
        - name: --aad-client-id
          short-summary: Client ID of an AAD app with permissions to write secrets to the key vault.
        - name: --aad-client-secret
          short-summary: Client secret of the AAD app with permissions to write secrets to the key vault.
        - name: --aad-client-cert-thumbprint
          short-summary: Thumbprint of the AAD app certificate with permissions to write secrets to the key vault.
"""

helps['vm encryption disable'] = """
    type: command
    short-summary: Disable disk encryption on the OS disk and/or data disks.
"""

helps['vm encryption show'] = """
    type: command
    short-summary: Show encryption status.
"""

helps['vm extension'] = """
    type: group
    short-summary: Manage extensions on VMs.
    long-summary: >
        Extensions are small applications that provide post-deployment configuration and automation tasks on Azure virtual machines.
        For example, if a virtual machine requires software installation, anti-virus protection, or Docker configuration, a VM extension
        can be used to complete these tasks. Extensions can be bundled with a new virtual machine deployment or run against any existing system.
"""

helps['vm extension list'] = """
    type: command
    short-summary:  List the extensions attached to a VM.
    examples:
        - name: List attached extensions to a named VM.
          text: az vm extension list -g MyResourceGroup --vm-name MyVm
        - name: List attached extensions with IDs containing the string "MyExtension".
          text: >
            az vm extension list --ids \\
                $(az resource list --query "[?contains(name, 'MyExtension')].id" -o tsv)
"""

helps['vm extension delete'] = """
    type: command
    short-summary: Remove an extension attached to a VM.
    examples:
        - name: Use a VM name and extension to delete an extension from a VM.
          text: az vm extension delete -g MyResourceGroup --vm-name MyVm -n extension_name
        - name: Delete extensions with IDs containing the string "MyExtension" from a VM.
          text: >
            az vm extension delete --ids \\
                $(az resource list --query "[?contains(name, 'MyExtension')].id" -o tsv)
"""

helps['vm extension show'] = """
    type: command
    short-summary: Display information about extensions attached to a VM.
    examples:
        - name: Use VM name and extension name to show the extensions attached to a VM.
          text: az vm extension show -g MyResourceGroup --vm-name MyVm -n extension_name
"""

helps['vm extension image'] = """
    type: group
    short-summary: Find the available VM extensions for a subscription and region.
"""

helps['vm extension image list'] = """
    type: command
    short-summary: List the information on available extensions.
    examples:
        - name: List the unique publishers for extensions.
          text: az vm extension image list --query "[].publisher" -o tsv | sort -u
        - name: Find extensions with "Docker" in the name.
          text: az vm extension image list --query "[].name" -o tsv | sort -u | grep Docker
        - name: List extension names where the publisher name starts with "Microsoft.Azure.App".
          text: |
            az vm extension image list --query \\
                "[?starts_with(publisher, 'Microsoft.Azure.App')].publisher" \\
                -o tsv | sort -u | xargs -I{} az vm extension image list-names --publisher {} -l westus
"""

helps['vm extension image list-names'] = """
    type: command
    short-summary: List the names of available extensions.
    examples:
        - name: Find Docker extensions by publisher and location.
          text: >
            az vm extension image list-names --publisher Microsoft.Azure.Extensions \\
                -l westus --query "[?starts_with(name, 'Docker')]"
        - name: Find CustomScript extensions by publisher and location.
          text: >
            az vm extension image list-names --publisher Microsoft.Azure.Extensions \\
                -l westus --query "[?starts_with(name, 'Custom')]"
"""

helps['vm extension image list-versions'] = """
    type: command
    short-summary: List the versions for available extensions.
    examples:
        - name: Find the available versions for the Docker extension.
          text: >
            az vm extension image list-versions --publisher Microsoft.Azure.Extensions \\
                -l westus -n DockerExtension -otable
"""

helps['vm extension image show'] = """
    type: command
    short-summary: Display information for an extension.
    examples:
        - name: Show the CustomScript extension version 2.0.2.
          text: >
            az vm extension image show -l westus -n CustomScript \\
              --publisher Microsoft.Azure.Extensions --version 2.0.2
        - name: Show the latest version of the Docker extension.
          text: >
            publisher=Microsoft.Azure.Extensions\n
            extension=DockerExtension\n
            location=westus\n

            latest=$(az vm extension image list-versions \\
              --publisher {publisher} -l {location} -n {extension} \\
              --query "[].name" -o tsv | sort | tail -n 1)

            az vm extension image show -l {location} \\
              --publisher {publisher} -n {extension} --version {latest}
"""

helps['vm image'] = """
    type: group
    short-summary: Information on available virtual machine images.
"""

helps['vm image list'] = """
    type: command
    short-summary: List the VM/VMSS images available in the Azure Marketplace.
    parameters:
        - name: --all
          short-summary: Retrieve image list from live Azure service rather using an offline image list
        - name: --offer -f
          short-summary: Image offer name, partial name is accepted
        - name: --publisher -p
          short-summary: Image publisher name, partial name is accepted
        - name: --sku -s
          short-summary: Image sku name, partial name is accepted
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
        - name: List all offers from Microsoft in the West US region.
          text: az vm image list-offers -l westus -p Microsoft
        - name: List all offers from OpenLocic in the West US region.
          text: az vm image list-offers -l westus -p OpenLogic
"""

helps['vm image list-publishers'] = """
    type: command
    short-summary: List the VM image publishers available in the Azure Marketplace.
    examples:
        - name: List all publishers in the West US region.
          text: az vm image list-publishers -l westus
        - name: List all publishers with names starting with "Open" in westus.
          text: az vm image list-publishers -l westus --query "[?starts_with(name, 'Open')]"
"""

helps['vm image list-skus'] = """
    type: command
    short-summary: List the VM image SKUs available in the Azure Marketplace.
    examples:
        - name: List all skus available for CentOS published by OpenLogic in the West US region.
          text: az vm image list-skus -l westus -f CentOS -p OpenLogic
"""

helps['vm image show'] = """
    type: command
    short-summary: Get the details for a VM image available in the Azure Marketplace.
    examples:
        - name: Show information for the latest available CentOS image from OpenLogic.
          text: >
            latest=$(az vm image list -p OpenLogic -s 7.3 --all --query \\
                "[?offer=='CentOS'].version" -o tsv | sort -u | tail -n 1)
            az vm image show -l westus -f CentOS -p OpenLogic --s 7.3 --version {latest}
"""

helps['vm image accept-terms'] = """
    type: command
    short-summary: Accept Azure Marketplace term so that the image can be used to create VMs
"""

helps['vm nic'] = """
    type: group
    short-summary: Manage network interfaces. See also `az network nic`.
    long-summary: >
        A network interface (NIC) is the interconnection between a VM and the underlying software
        network. For more information, see https://docs.microsoft.com/azure/virtual-network/virtual-network-network-interface-overview.
"""

helps['vm nic list'] = """
    type: command
    short-summary: List the NICs available on a VM.
    examples:
        - name: List all of the NICs on a VM.
          text: az vm nic list -g MyResourceGroup --vm-name MyVm
"""

helps['vm nic add'] = """
    type: command
    short-summary: Add existing NICs to a VM.
    examples:
        - name: Add two NICs to a VM.
          text: az vm nic add -g MyResourceGroup --vm-name MyVm --nics nic_name1 nic_name2
"""

helps['vm nic remove'] = """
    type: command
    short-summary: Remove NICs from a VM.
    examples:
        - name: Remove two NICs from a VM.
          text: az vm nic remove -g MyResourceGroup --vm-name MyVm --nics nic_name1 nic_name2
"""

helps['vm nic show'] = """
    type: command
    short-summary: Display information for a NIC attached to a VM.
    examples:
        - name: Show details of a NIC on a VM.
          text: az vm nic show -g MyResourceGroup --vm-name MyVm --nic nic_name1
"""

helps['vm nic set'] = """
    type: command
    short-summary: Configure settings of a NIC attached to a VM.
    examples:
        - name: Set a NIC on a VM to be the primary interface.
          text: az vm nic set -g MyResourceGroup --vm-name MyVm --nic nic_name1 nic_name2 --primary-nic nic_name2
"""

helps['vmss'] = """
    type: group
    short-summary: Manage groupings of virtual machines in an Azure Virtual Machine Scale Set (VMSS).
"""

helps['vmss diagnostics'] = """
    type: group
    short-summary: Configure the Azure Virtual Machine Scale Set diagnostics extension.
"""

helps['vmss diagnostics get-default-config'] = """
    type: command
    short-summary: Show the default config file which defines data to be collected.
"""

helps['vmss diagnostics set'] = """
    type: command
    short-summary: Enable diagnostics on a VMSS.
"""


helps['vmss list-instance-connection-info'] = """
    type: command
    short-summary: Get the IP address and port number used to connect to individual VM instances within a set.
"""

helps['vmss list-instance-public-ips'] = """
    type: command
    short-summary: List public IP addresses of VM instances within a set.
"""

helps['vmss extension'] = """
    type: group
    short-summary: Manage extensions on a VM scale set.
"""

helps['vmss extension delete'] = """
    type: command
    short-summary: Delete an extension from a VMSS.
"""

helps['vmss extension list'] = """
    type: command
    short-summary: List extensions associated with a VMSS.
"""

helps['vmss extension set'] = """
    type: command
    short-summary: Add an extension to a VMSS or update an existing extension.
    long-summary: Get extension details from `az vmss extension image list`.
"""

helps['vmss extension show'] = """
    type: command
    short-summary: Show details on a VMSS extension.
"""

helps['vmss extension image'] = """
    type: group
    short-summary: Find the available VM extensions for a subscription and region.
"""

helps['vmss extension image list'] = """
    type: command
    short-summary: List the information on available extensions.
    examples:
        - name: List the unique publishers for extensions.
          text: az vmss extension image list --query "[].publisher" -o tsv | sort -u
        - name: Find extensions with "Docker" in the name.
          text: az vmss extension image list --query "[].name" -o tsv | sort -u | grep Docker
        - name: List extension names where the publisher name starts with "Microsoft.Azure.App".
          text: |
            az vmss extension image list --query \\
                "[?starts_with(publisher, 'Microsoft.Azure.App')].publisher" \\
                -o tsv | sort -u | xargs -I{} az vmss extension image list-names --publisher {} -l westus
"""


deallocate_generalize_capture = """        - name: Deallocate, generalize, and capture a stopped virtual machine.
          text: |
            az vm deallocate -g MyResourceGroup -n MyVm
            az vm generalize -g MyResourceGroup -n MyVm
            az vm capture -g MyResourceGroup -n MyVm --vhd-name-prefix MyPrefix
        - name: Deallocate, generalize, and capture multiple stopped virtual machines.
          text: |
            vms_ids=$(az vm list -g MyResourceGroup --query "[].id" -o tsv)
            az vm deallocate --ids {vms_ids}
            az vm generalize --ids {vms_ids}
            az vm capture --ids {vms_ids} --vhd-name-prefix MyPrefix
"""

helps['vmss encryption'] = """
    type: group
    short-summary: (PREVIEW) Manage encryption of VMSS.
"""

helps['vmss encryption enable'] = """
    type: command
    short-summary: Encrypt a VMSS with managed disks.
    examples:
        - name: encrypt a VM scale set using a key vault in the same resource group
          text: >
            az vmss encryption enable -g MyResourceGroup -n MyVm --disk-encryption-keyvault myvault
"""

helps['vmss encryption disable'] = """
    type: command
    short-summary: Disable the encryption on a VMSS with managed disks.
    examples:
        - name: disable encryption a VMSS
          text: >
            az vmss encryption disable -g MyResourceGroup -n MyVm
"""

helps['vmss encryption show'] = """
    type: command
    short-summary: Show encryption status.
"""

helps['vm capture'] = """
    type: command
    short-summary: Capture information for a stopped VM.
    long-summary: 'For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image'
    parameters:
        - name: --vhd-name-prefix
          type: string
          short-summary: The VHD name prefix specify for the VM disks.
        - name: --storage-container
          short-summary: The storage account container name in which to save the disks.
        - name: --overwrite
          short-summary: Overwrite the existing disk file.
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm delete'] = """
    type: command
    short-summary: Delete a VM.
    examples:
        - name: Delete a VM without a prompt for confirmation.
          text: >
            az vm delete -g MyResourceGroup -n MyVm --yes
{0}
""".format(vm_ids_example.format('Delete all VMs in a resource group.', 'vm delete'))

helps['vm deallocate'] = """
    type: command
    short-summary: Deallocate a VM.
    long-summary: 'For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image'
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm generalize'] = """
    type: command
    short-summary: Mark a VM as generalized, allowing it to be imaged for multiple deployments.
    long-summary: 'For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image'
    examples:
{0}
""".format(deallocate_generalize_capture)

helps['vm get-instance-view'] = """
    type: command
    short-summary: Get instance information about a VM.
    examples:
        - name: Use a resource group and name to get instance view information of a VM.
          text: az vm get-instance-view -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Get instance views for all VMs in a resource group.', 'vm get-instance-view'))

helps['vm list'] = """
    type: command
    short-summary: List details of Virtual Machines.
    long-summary: 'For more information on querying information about Virtual Machines, see https://docs.microsoft.com/en-us/cli/azure/query-az-cli2'
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
    short-summary: List IP addresses associated with a VM.
    examples:
        - name: Get the IP addresses for a VM.
          text: az vm list-ip-addresses -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Get IP addresses for all VMs in a resource group.', 'vm list-ip-addresses'))

helps['vm list-sizes'] = """
    type: command
    short-summary: List available sizes for VMs.
    examples:
        - name: List the available VM sizes in the West US region.
          text: az vm list-sizes -l westus
"""

helps['vm list-usage'] = """
    type: command
    short-summary: List available usage resources for VMs.
    examples:
        - name: Get the compute resource usage for the West US region.
          text: az vm list-usage -l westus
"""

helps['vm list-vm-resize-options'] = """
    type: command
    short-summary: List available resizing options for VMs.
    examples:
        - name: List all available VM sizes for resizing.
          text: az vm list-vm-resize-options -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('List available sizes for all VMs in a resource group.', 'vm list-vm-resize-options'))

helps['vm list-skus'] = """
    type: command
    short-summary: Get details for compute-related resource SKUs.
    long-summary: This command incorporates subscription level restriction, offering the most accurate information.
    examples:
        - name: List all SKUs in the West US region.
          text: az vm list-skus -l westus
        - name: List all available vm sizes in the East US2 region which support availability zone.
          text: az vm list-skus -l eastus2 --zone
        - name: List all available vm sizes in the East US2 region which support availability zone with name like "standard_ds1...".
          text: az vm list-skus -l eastus2 --zone --size standard_ds1
        - name: List availability set related sku information in The West US region.
          text: az vm list-skus -l westus --resource-type availabilitySets
"""

helps['vm open-port'] = """
    type: command
    short-summary: Opens a VM to inbound traffic on specified ports.
    long-summary: >
        Adds a security rule to the network security group (NSG) that is attached to the VM's
        network interface (NIC) or subnet. The existing NSG will be used or a new one will be
        created. The rule name is 'open-port-{{port}}' and will overwrite an existing rule with
        this name. For multi-NIC VMs, or for more fine-grained control, use the appropriate
        network commands directly (nsg rule create, etc).
    examples:
        - name: Open all ports on a VM to inbound traffic.
          text: az vm open-port -g MyResourceGroup -n MyVm --port '*'
        - name: Open a range of ports on a VM to inbound traffic with the highest priority.
          text: az vm open-port -g MyResourceGroup -n MyVm --port 80-100 --priority 100
{0}
""".format(vm_ids_example.format('Open all ports for all VMs in a resource group.', 'vm open-port'))

helps['vm redeploy'] = """
    type: command
    short-summary: Redeploy an existing VM.
    examples:
        - name: Redeploy a VM.
          text: az vm redeploy -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Redeploy all VMs in a resource group.', 'vm redeploy'))

helps['vm resize'] = """
    type: command
    short-summary: Update a VM's size.
    parameters:
        - name: --size
          type: string
          short-summary: The VM size.
          populator-commands:
          - az vm list-vm-resize-options
    examples:
        - name: Resize a VM.
          text: az vm resize -g MyResourceGroup -n MyVm --size Standard_DS3_v2
{0}
""".format(vm_ids_example.format('Resize all VMs in a resource group.', 'vm resize --size Standard_DS3_v2'))

helps['vm restart'] = """
    type: command
    short-summary: Restart VMs.
    examples:
        - name: Restart a VM.
          text: az vm restart -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Restart all VMs in a resource group.', 'vm restart'))

helps['vm show'] = """
    type: command
    short-summary: Get the details of a VM.
    examples:
        - name: Show information about a VM.
          text: az vm show -g MyResourceGroup -n MyVm -d
{0}
""".format(vm_ids_example.format('Get the details for all VMs in a resource group.', 'vm show -d'))

helps['vm start'] = """
    type: command
    short-summary: Start a stopped VM.
    examples:
        - name: Start a stopped VM.
          text: az vm start -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Start all VMs in a resource group.', 'vm start'))

helps['vm stop'] = """
    type: command
    short-summary: Stop a running VM.
    examples:
        - name: Stop a running VM.
          text: az vm stop -g MyResourceGroup -n MyVm
{0}
""".format(vm_ids_example.format('Stop all VMs in a resource group.', 'vm stop'))

helps['vm wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the VM is met.
    examples:
        - name: Wait until a VM is created.
          text: az vm wait -g MyResourceGroup -n MyVm --created
{0}
""".format(vm_ids_example.format('Wait until all VMs in a resource group are deleted.', 'vm wait --deleted'))

helps['vm identity'] = """
    type: group
    short-summary: manage service identities of a VM
"""

helps['vm identity assign'] = """
    type: command
    short-summary: Enable managed service identity on a VM.
    long-summary: This is required to authenticate and interact with other Azure services using bearer tokens.
    examples:
        - name: Enable system assigned identity on a VM with the 'Reader' role.
          text: az vm identity assign -g MyResourceGroup -n MyVm --role Reader --scope /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/MyResourceGroup
"""

helps['vm identity remove'] = """
    type: command
    short-summary: (PREVIEW) Remove managed service identities from a VM.
    examples:
        - name: Remove system assigned identity
          text: az vm identity remove -g MyResourceGroup -n MyVm
        - name: Remove 2 identities which are in the same resource group with the VM
          text: az vm identity remove -g MyResourceGroup -n MyVm --identities readerId writerId
        - name: Remove system assigned identity and a user identity
          text: az vm identity remove -g MyResourceGroup -n MyVm --identities [system] readerId
"""

helps['vm identity show'] = """
    type: command
    short-summary: display VM's managed identity info.
"""

helps['vm run-command'] = """
    type: group
    short-summary: Manage run commands on a Virtual Machine.
    long-summary: 'For more information, see https://docs.microsoft.com/en-us/azure/virtual-machines/windows/run-command or https://docs.microsoft.com/en-us/azure/virtual-machines/linux/run-command.'
"""

helps['vm run-command invoke'] = """
    type: command
    short-summary: Execute a specific run command on a vm.
    examples:
        - name: install nginx on a vm
          text: az vm run-command invoke -g MyResourceGroup -n MyVm --command-id RunShellScript --scripts "sudo apt-get update && sudo apt-get install -y nginx"
        - name: invoke command with parameters
          text: az vm run-command invoke -g MyResourceGroup -n MyVm --command-id RunShellScript --scripts 'echo $1 $2' --parameters hello world
"""

helps['vmss identity'] = """
    type: group
    short-summary: manage service identities of a VM scaleset.
"""

helps['vmss identity assign'] = """
    type: command
    short-summary: Enable managed service identity on a VMSS.
    long-summary: This is required to authenticate and interact with other Azure services using bearer tokens.
    examples:
        - name: Enable system assigned identity on a VMSS with the 'Owner' role.
          text: az vmss identity assign -g MyResourceGroup -n MyVmss --role Owner --scope /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/MyResourceGroup
"""

helps['vmss identity remove'] = """
    type: command
    short-summary: (PREVIEW) Remove user assigned identities from a VM scaleset.
    examples:
        - name: Remove system assigned identity
          text: az vmss identity remove -g MyResourceGroup -n MyVmss
        - name: Remove 2 identities which are in the same resource group with the VM scaleset
          text: az vmss identity remove -g MyResourceGroup -n MyVmss --identities readerId writerId
        - name: Remove system assigned identity and a user identity
          text: az vmss identity remove -g MyResourceGroup -n MyVmss --identities [system] readerId
"""

helps['vmss identity show'] = """
    type: command
    short-summary: display VM scaleset's managed identity info.
"""

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
    short-summary: Manage custom virtual machine images.
"""

helps['disk create'] = """
    type: command
    short-summary: Create a managed disk.
    examples:
        - name: Create a managed disk by importing from a blob uri.
          text: >
            az disk create -g MyResourceGroup -n MyDisk --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd
        - name: Create an empty managed disk.
          text: >
            az disk create -g MyResourceGroup -n MyDisk --size-gb 10
        - name: Create a managed disk by copying an existing disk or snapshot.
          text: >
            az disk create -g MyResourceGroup -n MyDisk2 --source MyDisk
        - name: Create a disk in an availability zone in the region of "East US 2"
          text: >
            az disk create -n MyDisk -g MyResourceGroup --size-gb 10 --location eastus2 --zone 1
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
    short-summary: Place the CLI in a waiting state until a condition of a managed disk is met.
"""


helps['disk grant-access'] = """
    type: command
    short-summary: Grant a resource read access to a managed disk.
"""

helps['disk revoke-access'] = """
    type: command
    short-summary: Revoke a resource's read access to a managed disk.
"""

helps['snapshot create'] = """
    type: command
    short-summary: Create a snapshot.
    examples:
        - name: Create a snapshot by importing from a blob uri.
          text: >
            az snapshot create -g MyResourceGroup -n MySnapshot --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd
        - name: Create an empty snapshot.
          text: az snapshot create -g MyResourceGroup -n MySnapshot --size-gb 10
        - name: Create a snapshot by copying an existing disk in the same resource group.
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
          text: |
            az image create -g MyResourceGroup -n image1 --os-type Linux \\
                --source /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/rg1/providers/Microsoft.Compute/snapshots/s1 \\
                --data-snapshot /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/rg/providers/Microsoft.Compute/snapshots/s2
        - name: Create an image by capturing an existing generalized virtual machine in the same resource group.
          text: az image create -g MyResourceGroup -n image1 --source MyVm1
"""

helps['image list'] = """
    type: command
    short-summary: List custom VM images.
"""

helps['identity'] = """
    type: group
    short-summary: Managed Service Identities
"""

helps['identity list'] = """
    type: command
    short-summary: List Managed Service Identities
"""

helps['identity list-operations'] = """
    type: command
    short-summary: Lists available operations for the Managed Identity provider
"""

helps['sig'] = """
    type: group
    short-summary: manage shared image gallery
"""

helps['sig create'] = """
    type: command
    short-summary: create a share image gallery.
"""

helps['sig list'] = """
    type: command
    short-summary: list share image galleries.
"""

helps['sig update'] = """
    type: command
    short-summary: update a share image gallery.
"""

helps['sig image-definition'] = """
    type: group
    short-summary: create an image definition
"""

helps['sig image-definition create'] = """
    type: command
    short-summary: create a gallery image definition
    examples:
        - name: Create a linux image defintion
          text: |
            az sig image-definition create -g MyResourceGroup --gallery-name MyGallery --gallery-image-definition MyImage --publisher GreatPublisher --offer GreatOffer --sku GreatSku --os-type linux
"""

helps['sig image-definition update'] = """
    type: command
    short-summary: update a share image defintiion.
"""

helps['sig image-version'] = """
    type: group
    short-summary: create a new version from an image defintion
"""

helps['sig image-version create'] = """
    type: command
    short-summary: creat a new image version
    examples:
        - name: add a new version
          text: |
            az sig image-version create -g MyResourceGroup --gallery-name MyGallery --gallery-image-definition MyImage --gallery-image-version 1.0.0 --managed-image /subscriptions/00000000-0000-0000-0000-00000000xxxx/resourceGroups/imageGroups/providers/images/MyManagedImage
"""

helps['sig image-version update'] = """
    type: command
    short-summary: update a share image version
"""

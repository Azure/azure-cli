# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["vmss extension"] = """
"type": |-
    group
"short-summary": |-
    Manage extensions on a VM scale set.
"""

helps["vm open-port"] = """
"type": |-
    command
"short-summary": |-
    Opens a VM to inbound traffic on specified ports.
"long-summary": |
    Adds a security rule to the network security group (NSG) that is attached to the VM's network interface (NIC) or subnet. The existing NSG will be used or a new one will be created. The rule name is 'open-port-{port}' and will overwrite an existing rule with this name. For multi-NIC VMs, or for more fine-grained control, use the appropriate network commands directly (nsg rule create, etc).
"""

helps["vmss show"] = """
"type": |-
    command
"short-summary": |-
    Get details on VMs within a VMSS.
"parameters":
-   "name": |-
        --instance-id
    "short-summary": |-
        VM instance ID. If missing, show the VMSS.
"examples":
-   "name": |-
        Get details on VMs within a VMSS.
    "text": |-
        az vmss show --output json --resource-group MyResourceGroup --query [0] --name MyScaleSet
"""

helps["vm image accept-terms"] = """
"type": |-
    command
"short-summary": |-
    Accept Azure Marketplace term so that the image can be used to create VMs
"""

helps["identity list-operations"] = """
"type": |-
    command
"short-summary": |-
    Lists available operations for the Managed Identity provider
"""

helps["vm identity show"] = """
"type": |-
    command
"short-summary": |-
    display VM's managed identity info.
"examples":
-   "name": |-
        Display VM's managed identity info.
    "text": |-
        az vm identity show --name MyVirtualMachine --resource-group MyResourceGroup
"""

helps["vm image list-publishers"] = """
"type": |-
    command
"short-summary": |-
    List the VM image publishers available in the Azure Marketplace.
"""

helps["vm delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a VM.
"examples":
-   "name": |-
        Delete a VM.
    "text": |-
        az vm delete --resource-group MyResourceGroup --yes  --name MyVm
"""

helps["vmss"] = """
"type": |-
    group
"short-summary": |-
    Manage groupings of virtual machines in an Azure Virtual Machine Scale Set (VMSS).
"examples":
-   "name": |-
        View an instance of a VMSS.
    "text": |-
        az vmss get-instance-view --name MyScaleSet --resource-group MyResourceGroup
"""

helps["vm"] = """
"type": |-
    group
"short-summary": |-
    Manage Linux or Windows virtual machines.
"""

helps["sig image-version update"] = """
"type": |-
    command
"short-summary": |-
    update a share image version
"""

helps["vmss extension image"] = """
"type": |-
    group
"short-summary": |-
    Find the available VM extensions for a subscription and region.
"""

helps["vmss encryption disable"] = """
"type": |-
    command
"short-summary": |-
    Disable the encryption on a VMSS with managed disks.
"""

helps["vm diagnostics get-default-config"] = """
"type": |-
    command
"short-summary": |-
    Get the default configuration settings for a VM.
"""

helps["vm list-ip-addresses"] = """
"type": |-
    command
"short-summary": |-
    List IP addresses associated with a VM.
"""

helps["disk create"] = """
"type": |-
    command
"short-summary": |-
    Create a managed disk.
"examples":
-   "name": |-
        Create a managed disk.
    "text": |-
        az disk create --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd --resource-group MyResourceGroup --name MyDisk
"""

helps["sig"] = """
"type": |-
    group
"short-summary": |-
    manage shared image gallery
"""

helps["disk list"] = """
"type": |-
    command
"short-summary": |-
    List managed disks.
"""

helps["vmss list-instance-public-ips"] = """
"type": |-
    command
"short-summary": |-
    List public IP addresses of VM instances within a set.
"""

helps["vm boot-diagnostics get-boot-log"] = """
"type": |-
    command
"short-summary": |-
    Get the boot diagnostics log from a VM.
"""

helps["vm boot-diagnostics disable"] = """
"type": |-
    command
"short-summary": |-
    Disable the boot diagnostics on a VM.
"""

helps["vmss diagnostics get-default-config"] = """
"type": |-
    command
"short-summary": |-
    Show the default config file which defines data to be collected.
"""

helps["vm extension image"] = """
"type": |-
    group
"short-summary": |-
    Find the available VM extensions for a subscription and region.
"""

helps["vm availability-set create"] = """
"type": |-
    command
"short-summary": |-
    Create an Azure Availability Set.
"long-summary": |-
    For more information, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-manage-availability.
"""

helps["vm redeploy"] = """
"type": |-
    command
"short-summary": |-
    Redeploy an existing VM.
"""

helps["vm nic set"] = """
"type": |-
    command
"short-summary": |-
    Configure settings of a NIC attached to a VM.
"""

helps["image list"] = """
"type": |-
    command
"short-summary": |-
    List custom VM images.
"examples":
-   "name": |-
        List custom VM images.
    "text": |-
        az image list --resource-group MyResourceGroup
"""

helps["vmss list-instance-connection-info"] = """
"type": |-
    command
"short-summary": |-
    Get the IP address and port number used to connect to individual VM instances within a set.
"""

helps["sig image-definition update"] = """
"type": |-
    command
"short-summary": |-
    update a share image defintiion.
"""

helps["vm encryption"] = """
"type": |-
    group
"short-summary": |-
    Manage encryption of VM disks.
"""

helps["vm resize"] = """
"type": |-
    command
"short-summary": |-
    Update a VM's size.
"parameters":
-   "name": |-
        --size
    "type": |-
        string
    "short-summary": |-
        The VM size.
    "populator-commands":
    - |-
        az vm list-vm-resize-options
"examples":
-   "name": |-
        Update a VM's size.
    "text": |-
        az vm resize --size Standard_DS3_v2 --name MyVm --resource-group MyResourceGroup
"""

helps["disk grant-access"] = """
"type": |-
    command
"short-summary": |-
    Grant a resource read access to a managed disk.
"""

helps["disk delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a managed disk.
"examples":
-   "name": |-
        Delete a managed disk.
    "text": |-
        az disk delete --resource-group MyResourceGroup --yes  --name MyManagedDisk
"""

helps["vm extension show"] = """
"type": |-
    command
"short-summary": |-
    Display information about extensions attached to a VM.
"examples":
-   "name": |-
        Display information about extensions attached to a VM.
    "text": |-
        az vm extension show --output json --name extension_name --vm-name MyVm --resource-group MyResourceGroup
"""

helps["vmss identity remove"] = """
"type": |-
    command
"short-summary": |-
    (PREVIEW) Remove user assigned identities from a VM scaleset.
"""

helps["acs"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Container Services.
"""

helps["identity"] = """
"type": |-
    group
"short-summary": |-
    Managed Service Identities
"""

helps["vm availability-set list-sizes"] = """
"type": |-
    command
"short-summary": |-
    List VM sizes for an availability set.
"""

helps["vm run-command invoke"] = """
"type": |-
    command
"short-summary": |-
    Execute a specific run command on a vm.
"""

helps["vmss list"] = """
"type": |-
    command
"short-summary": |-
    List VMSS.
"examples":
-   "name": |-
        Get the IP address and port number used to connect to individual VM instances within a set.
    "text": |-
        az vmss list-instance-connection-info --output json --name MyScaleSet --resource-group MyResourceGroup
-   "name": |-
        Gets a list of all virtual machines in a VM scale sets.
    "text": |-
        az vmss list-instances --output json --name MyScaleSet --resource-group MyResourceGroup
-   "name": |-
        List public IP addresses of VM instances within a set.
    "text": |-
        az vmss list-instance-public-ips --output json --name MyScaleSet --query [0] --resource-group MyResourceGroup
-   "name": |-
        List VMSS.
    "text": |-
        az vmss list --output json --query [0]
"""

helps["vm nic"] = """
"type": |-
    group
"short-summary": |-
    Manage network interfaces. See also `az network nic`.
"long-summary": |
    A network interface (NIC) is the interconnection between a VM and the underlying software network. For more information, see https://docs.microsoft.com/azure/virtual-network/virtual-network-network-interface-overview.
"""

helps["vm extension"] = """
"type": |-
    group
"short-summary": |-
    Manage extensions on VMs.
"long-summary": |
    Extensions are small applications that provide post-deployment configuration and automation tasks on Azure virtual machines. For example, if a virtual machine requires software installation, anti-virus protection, or Docker configuration, a VM extension can be used to complete these tasks. Extensions can be bundled with a new virtual machine deployment or run against any existing system.
"""

helps["vmss wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of a scale set is met.
"""

helps["sig image-version create"] = """
"type": |-
    command
"short-summary": |-
    creat a new image version
"long-summary": |-
    this operation might take a long time depending on the replicate region number. Use "--no-wait" is advised.
"""

helps["vm list-usage"] = """
"type": |-
    command
"short-summary": |-
    List available usage resources for VMs.
"""

helps["vm identity remove"] = """
"type": |-
    command
"short-summary": |-
    Remove managed service identities from a VM.
"""

helps["vmss extension list"] = """
"type": |-
    command
"short-summary": |-
    List extensions associated with a VMSS.
"""

helps["vm disk detach"] = """
"type": |-
    command
"short-summary": |-
    Detach a managed disk from a VM.
"examples":
-   "name": |-
        Detach a managed disk from a VM.
    "text": |-
        az vm disk detach --name disk_name --vm-name MyVm --resource-group MyResourceGroup
"""

helps["snapshot wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of a snapshot is met.
"""

helps["vm availability-set update"] = """
"type": |-
    command
"short-summary": |-
    Update an Azure Availability Set.
"""

helps["vm restart"] = """
"type": |-
    command
"short-summary": |-
    Restart VMs.
"examples":
-   "name": |-
        Restart VMs.
    "text": |-
        az vm restart --name MyVm --no-wait  --resource-group MyResourceGroup
"""

helps["vm unmanaged-disk"] = """
"type": |-
    group
"short-summary": |-
    Manage the unmanaged data disks attached to a VM.
"long-summary": |4

    Just like any other computer, virtual machines in Azure use disks as a place to store an operating system, applications, and data. All Azure virtual machines have at least two disks: An operating system disk, and a temporary disk. The operating system disk is created from an image, and both the operating system disk and the image are actually virtual hard disks (VHDs) stored in an Azure storage account. Virtual machines also can have one or more data disks, that are also stored as VHDs.
    Operating System Disk Every virtual machine has one attached operating system disk. It's registered as a SATA drive and is labeled /dev/sda by default. This disk has a maximum capacity of 1023 gigabytes (GB).
    Temporary disk The temporary disk is automatically created for you. On Linux virtual machines, the disk is typically /dev/sdb and is formatted and mounted to /mnt/resource by the Azure Linux Agent. The size of the temporary disk varies, based on the size of the virtual machine.
    Data disk A data disk is a VHD that's attached to a virtual machine to store application data, or other data you need to keep. Data disks are registered as SCSI drives and are labeled by the creator. Each data disk has a maximum capacity of 1023 GB. The size of the virtual machine determines how many data disks can be attached and the type of storage that can be used to host the disks.
"""

helps["identity list"] = """
"type": |-
    command
"short-summary": |-
    List Managed Service Identities
"""

helps["vm boot-diagnostics enable"] = """
"type": |-
    command
"short-summary": |-
    Enable the boot diagnostics on a VM.
"parameters":
-   "name": |-
        --storage
    "short-summary": |-
        Name or URI of a storage account (e.g. https://your_storage_account_name.blob.core.windows.net/)
"""

helps["vmss extension delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an extension from a VMSS.
"""

helps["vm unmanaged-disk list"] = """
"type": |-
    command
"short-summary": |-
    List unmanaged disks of a VM.
"""

helps["vm secret remove"] = """
"type": |-
    command
"short-summary": |-
    Remove a secret from a VM.
"""

helps["vm secret list"] = """
"type": |-
    command
"short-summary": |-
    List secrets on a VM.
"""

helps["disk"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Managed Disks.
"""

helps["sig image-version wait"] = """
"type": |-
    command
"short-summary": |-
    wait for image version related operation
"""

helps["vm user update"] = """
"type": |-
    command
"short-summary": |-
    Update a user account.
"parameters":
-   "name": |-
        --ssh-key-value
    "short-summary": |-
        SSH public key file value or public key file path
"examples":
-   "name": |-
        Update a user account.
    "text": |-
        az vm user update --username username --name MyVm --ssh-key-value "$(< ~/.ssh/id_rsa.pub)" --resource-group MyResourceGroup
"""

helps["vmss update-instances"] = """
"type": |-
    command
"short-summary": |-
    Upgrade VMs within a VMSS.
"""

helps["vm secret"] = """
"type": |-
    group
"short-summary": |-
    Manage VM secrets.
"""

helps["vm user"] = """
"type": |-
    group
"short-summary": |-
    Manage user accounts for a VM.
"""

helps["sig image-version"] = """
"type": |-
    group
"short-summary": |-
    create a new version from an image defintion
"""

helps["acs delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a container service.
"""

helps["vm nic remove"] = """
"type": |-
    command
"short-summary": |-
    Remove NICs from a VM.
"""

helps["vm extension image list-names"] = """
"type": |-
    command
"short-summary": |-
    List the names of available extensions.
"""

helps["snapshot grant-access"] = """
"type": |-
    command
"short-summary": |-
    Grant read access to a snapshot.
"""

helps["vmss restart"] = """
"type": |-
    command
"short-summary": |-
    Restart VMs within a VMSS.
"examples":
-   "name": |-
        Restart VMs within a VMSS.
    "text": |-
        az vmss restart --name MyScaleSet --resource-group MyResourceGroup
"""

helps["vmss extension set"] = """
"type": |-
    command
"short-summary": |-
    Add an extension to a VMSS or update an existing extension.
"long-summary": |-
    Get extension details from `az vmss extension image list`.
"parameters":
-   "name": |-
        --name -n
    "populator-commands":
    - |-
        az vm extension image list
"examples":
-   "name": |-
        Add an extension to a VMSS or update an existing extension.
    "text": |-
        az vmss extension set --version <version> --publisher <publisher> --resource-group MyResourceGroup --name MyExtension --vmss-name MyVmss --settings <settings>
"""

helps["vm availability-set show"] = """
"type": |-
    command
"short-summary": |-
    Get information for an availability set.
"""

helps["vm unmanaged-disk attach"] = """
"type": |-
    command
"short-summary": |-
    Attach an unmanaged persistent disk to a VM.
"long-summary": |-
    This allows for the preservation of data, even if the VM is reprovisioned due to maintenance or resizing.
"""

helps["disk revoke-access"] = """
"type": |-
    command
"short-summary": |-
    Revoke a resource's read access to a managed disk.
"""

helps["vm user reset-ssh"] = """
"type": |-
    command
"short-summary": |-
    Reset the SSH configuration on a VM.
"long-summary": |
    The extension will restart the SSH service, open the SSH port on your VM, and reset the SSH configuration to default values. The user account (name, password, and SSH keys) are not changed.
"""

helps["vmss scale"] = """
"type": |-
    command
"short-summary": |-
    Change the number of VMs within a VMSS.
"parameters":
-   "name": |-
        --new-capacity
    "short-summary": |-
        Number of VMs in the VMSS.
"examples":
-   "name": |-
        Change the number of VMs within a VMSS.
    "text": |-
        az vmss scale --name MyScaleSet --new-capacity <new-capacity> --resource-group MyResourceGroup
"""

helps["vm encryption show"] = """
"type": |-
    command
"short-summary": |-
    Show encryption status.
"examples":
-   "name": |-
        Show encryption status.
    "text": |-
        az vm encryption show --name MyVirtualMachine --query [0] --resource-group MyResourceGroup
"""

helps["vm extension set"] = """
"type": |-
    command
"short-summary": |-
    Set extensions for a VM.
"long-summary": |-
    Get extension details from `az vm extension image list`.
"parameters":
-   "name": |-
        --name -n
    "populator-commands":
    - |-
        az vm extension image list
"examples":
-   "name": |-
        Set extensions for a VM.
    "text": |-
        az vm extension set --version <version> --resource-group MyResourceGroup --name MyExtension --vm-name MyVm --publisher <publisher> --settings <settings>
"""

helps["vm extension wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of a virtual machine extension is met.
"""

helps["vm unmanaged-disk detach"] = """
"type": |-
    command
"short-summary": |-
    Detach an unmanaged disk from a VM.
"""

helps["vm list"] = """
"type": |-
    command
"short-summary": |-
    List details of Virtual Machines.
"long-summary": |-
    For more information on querying information about Virtual Machines, see https://docs.microsoft.com/en-us/cli/azure/query-az-cli2
"examples":
-   "name": |-
        List available usage resources for VMs.
    "text": |-
        az vm list-usage --location westus
-   "name": |-
        List IP addresses associated with a VM.
    "text": |-
        az vm list-ip-addresses --output json
-   "name": |-
        Get details for compute-related resource SKUs.
    "text": |-
        az vm list-skus --location westus
-   "name": |-
        List available sizes for VMs.
    "text": |-
        az vm list-sizes --location westus
"""

helps["vm secret add"] = """
"type": |-
    command
"short-summary": |-
    Add a secret to a VM.
"""

helps["vm get-instance-view"] = """
"type": |-
    command
"short-summary": |-
    Get instance information about a VM.
"""

helps["vmss get-instance-view"] = """
"type": |-
    command
"short-summary": |-
    View an instance of a VMSS.
"parameters":
-   "name": |-
        --instance-id
    "short-summary": |-
        A VM instance ID or "*" to list instance view for all VMs in a scale set.
"""

helps["vm secret format"] = """
"type": |-
    command
"short-summary": |-
    Transform secrets into a form that can be used by VMs and VMSSes.
"parameters":
-   "name": |-
        --secrets -s
    "long-summary": |
        The command will attempt to resolve the vault ID for each secret. If it is unable to do so, specify the vault ID to use for *all* secrets using: --keyvault NAME --resource-group NAME | --keyvault ID.
"examples":
-   "name": |-
        Transform secrets into a form that can be used by VMs and VMSSes.
    "text": |-
        az vm secret format --secrets <secrets>
"""

helps["vm extension delete"] = """
"type": |-
    command
"short-summary": |-
    Remove an extension attached to a VM.
"examples":
-   "name": |-
        Remove an extension attached to a VM.
    "text": |-
        az vm extension delete --resource-group MyResourceGroup --vm-name MyVm --name extension_name
"""

helps["vm identity"] = """
"type": |-
    group
"short-summary": |-
    manage service identities of a VM
"""

helps["vm extension image list"] = """
"type": |-
    command
"short-summary": |-
    List the information on available extensions.
"examples":
-   "name": |-
        List the information on available extensions.
    "text": |-
        az vm extension image list --output json --location westus2
"""

helps["vm nic show"] = """
"type": |-
    command
"short-summary": |-
    Display information for a NIC attached to a VM.
"examples":
-   "name": |-
        Display information for a NIC attached to a VM.
    "text": |-
        az vm nic show --vm-name MyVm --nic nic_name1 --resource-group MyResourceGroup
"""

helps["vm encryption enable"] = """
"type": |-
    command
"short-summary": |-
    Enable disk encryption on the OS disk and/or data disks.
"parameters":
-   "name": |-
        --aad-client-id
    "short-summary": |-
        Client ID of an AAD app with permissions to write secrets to the key vault.
-   "name": |-
        --aad-client-secret
    "short-summary": |-
        Client secret of the AAD app with permissions to write secrets to the key vault.
-   "name": |-
        --aad-client-cert-thumbprint
    "short-summary": |-
        Thumbprint of the AAD app certificate with permissions to write secrets to the key vault.
"examples":
-   "name": |-
        Enable disk encryption on the OS disk and/or data disks.
    "text": |-
        az vm encryption enable --disk-encryption-keyvault <disk-encryption-keyvault> --name MyVirtualMachine --volume-type ALL --resource-group MyResourceGroup
"""

helps["vmss disk detach"] = """
"type": |-
    command
"short-summary": |-
    Detach managed data disks from a scale set or its instances.
"""

helps["vmss diagnostics"] = """
"type": |-
    group
"short-summary": |-
    Configure the Azure Virtual Machine Scale Set diagnostics extension.
"""

helps["acs list"] = """
"type": |-
    command
"short-summary": |-
    List container services.
"""

helps["vm run-command"] = """
"type": |-
    group
"short-summary": |-
    Manage run commands on a Virtual Machine.
"long-summary": |-
    For more information, see https://docs.microsoft.com/en-us/azure/virtual-machines/windows/run-command or https://docs.microsoft.com/en-us/azure/virtual-machines/linux/run-command.
"""

helps["snapshot create"] = """
"type": |-
    command
"short-summary": |-
    Create a snapshot.
"examples":
-   "name": |-
        Create a snapshot.
    "text": |-
        az snapshot create --tags key[=value] --source https://vhd1234.blob.core.windows.net/vhds/osdisk1234.vhd --name MySnapshot --resource-group MyResourceGroup
"""

helps["vmss stop"] = """
"type": |-
    command
"short-summary": |-
    Power off (stop) VMs within a VMSS.
"""

helps["vm show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a VM.
"examples":
-   "name": |-
        Get the details of a VM.
    "text": |-
        az vm show --show-details  --name MyVm --query [0] --resource-group MyResourceGroup
"""

helps["vmss nic"] = """
"type": |-
    group
"short-summary": |-
    Manage network interfaces of a VMSS.
"""

helps["vmss delete-instances"] = """
"type": |-
    command
"short-summary": |-
    Delete VMs within a VMSS.
"""

helps["vm diagnostics set"] = """
"type": |-
    command
"short-summary": |-
    Configure the Azure VM diagnostics extension.
"""

helps["image"] = """
"type": |-
    group
"short-summary": |-
    Manage custom virtual machine images.
"""

helps["vmss extension show"] = """
"type": |-
    command
"short-summary": |-
    Show details on a VMSS extension.
"""

helps["vm encryption disable"] = """
"type": |-
    command
"short-summary": |-
    Disable disk encryption on the OS disk and/or data disks.
"""

helps["vm extension image list-versions"] = """
"type": |-
    command
"short-summary": |-
    List the versions for available extensions.
"""

helps["acs create"] = """
"type": |-
    command
"short-summary": |-
    Create a container service.
"examples":
-   "name": |-
        Create a container service.
    "text": |-
        az acs create --generate-ssh-keys  --name MyContainerService --orchestrator-type kubernetes --resource-group MyResourceGroup
"""

helps["vm list-vm-resize-options"] = """
"type": |-
    command
"short-summary": |-
    List available resizing options for VMs.
"""

helps["vm wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the VM is met.
"examples":
-   "name": |-
        Place the CLI in a waiting state until a condition of the VM is met.
    "text": |-
        az vm wait --resource-group MyResourceGroup --custom <custom> --name MyVm
"""

helps["vm disk attach"] = """
"type": |-
    command
"short-summary": |-
    Attach a managed persistent disk to a VM.
"long-summary": |-
    This allows for the preservation of data, even if the VM is reprovisioned due to maintenance or resizing.
"examples":
-   "name": |-
        Attach a managed persistent disk to a VM.
    "text": |-
        az vm disk attach --disk disk_name --size-gb <size-gb> --vm-name MyVm --new  --resource-group MyResourceGroup
"""

helps["vm availability-set"] = """
"type": |-
    group
"short-summary": |-
    Group resources into availability sets.
"long-summary": |
    To provide redundancy to an application, it is recommended to group two or more virtual machines in an availability set. This configuration ensures that during either a planned or unplanned maintenance event, at least one virtual machine will be available.
"""

helps["vmss identity"] = """
"type": |-
    group
"short-summary": |-
    manage service identities of a VM scaleset.
"""

helps["vmss start"] = """
"type": |-
    command
"short-summary": |-
    Start VMs within a VMSS.
"""

helps["vmss deallocate"] = """
"type": |-
    command
"short-summary": |-
    Deallocate VMs within a VMSS.
"""

helps["sig create"] = """
"type": |-
    command
"short-summary": |-
    create a share image gallery.
"""

helps["vmss diagnostics set"] = """
"type": |-
    command
"short-summary": |-
    Enable diagnostics on a VMSS.
"""

helps["sig list"] = """
"type": |-
    command
"short-summary": |-
    list share image galleries.
"""

helps["vmss rolling-upgrade"] = """
"type": |-
    group
"short-summary": |-
    (PREVIEW) Manage rolling upgrades.
"""

helps["vmss create"] = """
"type": |-
    command
"short-summary": |-
    Create an Azure Virtual Machine Scale Set.
"long-summary": |-
    For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-linux-create-cli.
"parameters":
-   "name": |-
        --image
    "type": |-
        string
    "short-summary": |
        The name of the operating system image as a URN alias, URN, custom image name or ID, or VHD blob URI. Valid URN format: "Publisher:Offer:Sku:Version".
    "populator-commands":
    - |-
        az vm image list
    - |-
        az vm image show
"""

helps["vm image list-skus"] = """
"type": |-
    command
"short-summary": |-
    List the VM image SKUs available in the Azure Marketplace.
"parameters":
-   "name": |-
        --publisher -p
    "populator-commands":
    - |-
        az vm list-publishers
"""

helps["vm extension image show"] = """
"type": |-
    command
"short-summary": |-
    Display information for an extension.
"""

helps["vm diagnostics"] = """
"type": |-
    group
"short-summary": |-
    Configure the Azure Virtual Machine diagnostics extension.
"""

helps["vm stop"] = """
"type": |-
    command
"short-summary": |-
    Stop a running VM.
"""

helps["vmss reimage"] = """
"type": |-
    command
"short-summary": |-
    Reimage VMs within a VMSS.
"parameters":
-   "name": |-
        --instance-id
    "short-summary": |-
        VM instance ID. If missing, reimage all instances.
"""

helps["vmss update"] = """
"type": |-
    command
"short-summary": |-
    Update a VMSS.
"examples":
-   "name": |-
        Upgrade VMs within a VMSS.
    "text": |-
        az vmss update-instances --name MyScaleSet --instance-ids <instance-ids> --resource-group MyResourceGroup
-   "name": |-
        Update a VMSS.
    "text": |-
        az vmss update --set <set> --name MyScaleSet --resource-group MyResourceGroup
"""

helps["vm capture"] = """
"type": |-
    command
"short-summary": |-
    Capture information for a stopped VM.
"long-summary": |-
    For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image
"parameters":
-   "name": |-
        --vhd-name-prefix
    "type": |-
        string
    "short-summary": |-
        The VHD name prefix specify for the VM disks.
-   "name": |-
        --storage-container
    "short-summary": |-
        The storage account container name in which to save the disks.
-   "name": |-
        --overwrite
    "short-summary": |-
        Overwrite the existing disk file.
"""

helps["snapshot revoke-access"] = """
"type": |-
    command
"short-summary": |-
    Revoke read access to a snapshot.
"""

helps["vm image list"] = """
"type": |-
    command
"short-summary": |-
    List the VM/VMSS images available in the Azure Marketplace.
"parameters":
-   "name": |-
        --all
    "short-summary": |-
        Retrieve image list from live Azure service rather using an offline image list
-   "name": |-
        --offer -f
    "short-summary": |-
        Image offer name, partial name is accepted
-   "name": |-
        --publisher -p
    "short-summary": |-
        Image publisher name, partial name is accepted
-   "name": |-
        --sku -s
    "short-summary": |-
        Image sku name, partial name is accepted
"examples":
-   "name": |-
        List the VM image offers available in the Azure Marketplace.
    "text": |-
        az vm image list-offers --publisher Microsoft --location westus
-   "name": |-
        List the VM image publishers available in the Azure Marketplace.
    "text": |-
        az vm image list-publishers --location westus
-   "name": |-
        List the VM/VMSS images available in the Azure Marketplace.
    "text": |-
        az vm image list --all  --publisher <publisher>
"""

helps["vm identity assign"] = """
"type": |-
    command
"short-summary": |-
    Enable managed service identity on a VM.
"long-summary": |-
    This is required to authenticate and interact with other Azure services using bearer tokens.
"examples":
-   "name": |-
        Enable managed service identity on a VM.
    "text": |-
        az vm identity assign --role Reader --scope /subscriptions/db5eb68e-73e2-4fa8-b18a-0123456789999/resourceGroups/MyResourceGroup --name MyVm --resource-group MyResourceGroup
"""

helps["vm availability-set list"] = """
"type": |-
    command
"short-summary": |-
    List availability sets.
"""

helps["snapshot"] = """
"type": |-
    group
"short-summary": |-
    Manage point-in-time copies of managed disks, native blobs, or other snapshots.
"""

helps["vm list-sizes"] = """
"type": |-
    command
"short-summary": |-
    List available sizes for VMs.
"""

helps["vmss disk"] = """
"type": |-
    group
"short-summary": |-
    Manage data disks of a VMSS.
"""

helps["sig image-definition create"] = """
"type": |-
    command
"short-summary": |-
    create a gallery image definition
"""

helps["vm availability-set delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an availability set.
"""

helps["vm deallocate"] = """
"type": |-
    command
"short-summary": |-
    Deallocate a VM.
"long-summary": |-
    For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image
"examples":
-   "name": |-
        Deallocate a VM.
    "text": |-
        az vm deallocate --name MyVirtualMachine --no-wait  --resource-group MyResourceGroup
"""

helps["sig update"] = """
"type": |-
    command
"short-summary": |-
    update a share image gallery.
"""

helps["vm image list-offers"] = """
"type": |-
    command
"short-summary": |-
    List the VM image offers available in the Azure Marketplace.
"parameters":
-   "name": |-
        --publisher -p
    "populator-commands":
    - |-
        az vm list-publishers
"""

helps["vm disk"] = """
"type": |-
    group
"short-summary": |-
    Manage the managed data disks attached to a VM.
"long-summary": |4

    Just like any other computer, virtual machines in Azure use disks as a place to store an operating system, applications, and data. All Azure virtual machines have at least two disks: An operating system disk, and a temporary disk. The operating system disk is created from an image, and both the operating system disk and the image are actually virtual hard disks (VHDs) stored in an Azure storage account. Virtual machines also can have one or more data disks, that are also stored as VHDs.
    Operating System Disk Every virtual machine has one attached operating system disk. It's registered as a SATA drive and is labeled /dev/sda by default. This disk has a maximum capacity of 1023 gigabytes (GB).
    Temporary disk The temporary disk is automatically created for you. On Linux virtual machines, the disk is typically /dev/sdb and is formatted and mounted to /mnt/resource by the Azure Linux Agent. The size of the temporary disk varies, based on the size of the virtual machine.
    Data disk A data disk is a VHD that's attached to a virtual machine to store application data, or other data you need to keep. Data disks are registered as SCSI drives and are labeled by the creator. Each data disk has a maximum capacity of 1023 GB. The size of the virtual machine determines how many data disks can be attached and the type of storage that can be used to host the disks.
"""

helps["vm update"] = """
"type": |-
    command
"short-summary": |-
    Update the properties of a VM.
"long-summary": |-
    Update VM objects and properties using paths that correspond to 'az vm show'.
"examples":
-   "name": |-
        Update the properties of a VM.
    "text": |-
        az vm update --set tags.tagName=tagValue --resource-group group --name name
"""

helps["vm boot-diagnostics"] = """
"type": |-
    group
"short-summary": |-
    Troubleshoot the startup of an Azure Virtual Machine.
"long-summary": |-
    Use this feature to troubleshoot boot failures for custom or platform images.
"""

helps["vmss encryption show"] = """
"type": |-
    command
"short-summary": |-
    Show encryption status.
"""

helps["vm convert"] = """
"type": |-
    command
"short-summary": |-
    Convert a VM with unmanaged disks to use managed disks.
"""

helps["snapshot list"] = """
"type": |-
    command
"short-summary": |-
    List snapshots.
"examples":
-   "name": |-
        List snapshots.
    "text": |-
        az snapshot list --output json
"""

helps["vm image show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for a VM image available in the Azure Marketplace.
"examples":
-   "name": |-
        Get the details for a VM image available in the Azure Marketplace.
    "text": |-
        az vm image show --output json --query [0] --urn publisher:offer:sku:version
"""

helps["acs show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for a container service.
"""

helps["vm user delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a user account from a VM.
"""

helps["vm image"] = """
"type": |-
    group
"short-summary": |-
    Information on available virtual machine images.
"""

helps["vmss disk attach"] = """
"type": |-
    command
"short-summary": |-
    Attach managed data disks to a scale set or its instances.
"""

helps["snapshot update"] = """
"type": |-
    command
"short-summary": |-
    Update a snapshot.
"examples":
-   "name": |-
        Update a snapshot.
    "text": |-
        az snapshot update --name MySnapshot --resource-group MyResourceGroup
"""

helps["vmss encryption enable"] = """
"type": |-
    command
"short-summary": |-
    Encrypt a VMSS with managed disks.
"""

helps["sig image-definition"] = """
"type": |-
    group
"short-summary": |-
    create an image definition
"""

helps["vm nic add"] = """
"type": |-
    command
"short-summary": |-
    Add existing NICs to a VM.
"""

helps["vmss identity assign"] = """
"type": |-
    command
"short-summary": |-
    Enable managed service identity on a VMSS.
"long-summary": |-
    This is required to authenticate and interact with other Azure services using bearer tokens.
"examples":
-   "name": |-
        Enable managed service identity on a VMSS.
    "text": |-
        az vmss identity assign --name MyVmss --resource-group MyResourceGroup
"""

helps["image create"] = """
"type": |-
    command
"short-summary": |-
    Create a custom Virtual Machine Image from managed disks or snapshots.
"examples":
-   "name": |-
        Create a custom Virtual Machine Image from managed disks or snapshots.
    "text": |-
        az image create --source MyVm1 --name image1 --resource-group MyResourceGroup
"""

helps["vm start"] = """
"type": |-
    command
"short-summary": |-
    Start a stopped VM.
"examples":
-   "name": |-
        Start a stopped VM.
    "text": |-
        az vm start --output json
"""

helps["vm nic list"] = """
"type": |-
    command
"short-summary": |-
    List the NICs available on a VM.
"examples":
-   "name": |-
        List the NICs available on a VM.
    "text": |-
        az vm nic list --vm-name MyVm --resource-group MyResourceGroup
"""

helps["vm list-skus"] = """
"type": |-
    command
"short-summary": |-
    Get details for compute-related resource SKUs.
"long-summary": |-
    This command incorporates subscription level restriction, offering the most accurate information.
"""

helps["vm extension list"] = """
"type": |-
    command
"short-summary": |-
    List the extensions attached to a VM.
"examples":
-   "name": |-
        List the extensions attached to a VM.
    "text": |-
        az vm extension list --query [0] --vm-name MyVm --resource-group MyResourceGroup
"""

helps["disk update"] = """
"type": |-
    command
"short-summary": |-
    Update a managed disk.
"examples":
-   "name": |-
        Update a managed disk.
    "text": |-
        az disk update --size-gb <size-gb> --name MyManagedDisk --resource-group MyResourceGroup
"""

helps["acs scale"] = """
"type": |-
    command
"short-summary": |-
    Change the private agent count of a container service.
"""

helps["vm generalize"] = """
"type": |-
    command
"short-summary": |-
    Mark a VM as generalized, allowing it to be imaged for multiple deployments.
"long-summary": |-
    For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-capture-image
"examples":
-   "name": |-
        Mark a VM as generalized, allowing it to be imaged for multiple deployments.
    "text": |-
        az vm generalize --name MyVirtualMachine --resource-group MyResourceGroup
"""

helps["vm create"] = """
"type": |-
    command
"short-summary": |-
    Create an Azure Virtual Machine.
"long-summary": |-
    For an end-to-end tutorial, see https://docs.microsoft.com/azure/virtual-machines/virtual-machines-linux-quick-create-cli.
"parameters":
-   "name": |-
        --image
    "type": |-
        string
    "short-summary": |
        The name of the operating system image as a URN alias, URN, custom image name or ID, or VHD blob URI. This parameter is required unless using `--attach-os-disk.` Valid URN format: "Publisher:Offer:Sku:Version".
    "populator-commands":
    - |-
        az vm image list
    - |-
        az vm image show
-   "name": |-
        --ssh-key-value
    "short-summary": |-
        The SSH public key or public key file path.
"examples":
-   "name": |-
        Create an Azure Virtual Machine.
    "text": |-
        az vm create --public-ip-address "" --size <size> --resource-group MyResourceGroup --image UbuntuLTS --name MyVm
"""

helps["vm availability-set convert"] = """
"type": |-
    command
"short-summary": |-
    Convert an Azure Availability Set to contain VMs with managed disks.
"""

helps["vmss identity show"] = """
"type": |-
    command
"short-summary": |-
    display VM scaleset's managed identity info.
"""

helps["vmss extension image list"] = """
"type": |-
    command
"short-summary": |-
    List the information on available extensions.
"""

helps["disk wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of a managed disk is met.
"""

helps["vmss encryption"] = """
"type": |-
    group
"short-summary": |-
    (PREVIEW) Manage encryption of VMSS.
"""


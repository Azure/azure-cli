# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

helps['lab'] = """
            type: group
            short-summary: Commands to manage Azure DevTest Lab.
            """
helps['lab vm'] = """
            type: group
            short-summary: Commands to manage vm of Azure DevTest Lab.
            """
helps['lab vm create'] = """
            type: command
            short-summary: Command to create vm of in Azure DevTest Lab.
            parameters:
                - name: --resource-group -g
                  short-summary: Name of the lab resource group
                - name: --name -n
                  short-summary: Name of the virtual machine
                - name: --lab-name
                  short-summary: Name of the Lab
                - name: --notes
                  short-summary: Notes for the virtual machine
                - name: --image
                  short-summary: The name of the operating system image (Gallery Image Name and Custom Image Name/ID).
                                 Use az lab gallery-image list for available Gallery Images or
                                 Use az lab custom-image list for available Custom Images
                - name: --image-type
                  short-summary: Type of the image. Allowed values are gallery, custom
                - name: --formula
                  short-summary: Name of the formula. Use az lab formula list for available formulas
                - name: --size
                  short-summary: The VM size to be created. See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info
                - name: --admin-username
                  short-summary: Username for the VM
                - name: --admin-password
                  short-summary: Password for the VM
                - name: --ssh-key
                  short-summary: The SSH public key or public key file path. Use --generate-ssh-keys to regen ssh keys
                - name: --authentication-type
                  short-summary: Type of authentication to use with the VM. Allowed values are password, ssh
                - name: --vnet-name
                  short-summary: Name of the virtual network to reference an existing one in lab. If omitted, lab's existing one
                                 VNet and subnet will be selected automatically
                - name: --subnet
                  short-summary: Name of the subnet to reference an existing one in lab. If omitted, lab's existing one subnet will be
                                 selected automatically
                - name: --disallow-public-ip-address
                  short-summary: To allow public ip address set to true or false. If omitted, based on the defaulted subnet this will be set to true or false
                - name: --artifacts
                  short-summary: JSON encoded array of artifacts to be applied. Use @{file} to load from a file
                - name: --location -l
                  short-summary: Location where to create VM. Defaults to the location of the lab
                - name: --tags
                  short-summary: Space separated tags in 'key[=value]' format. Use "" to clear existing tags
                - name: --allow-claim
                  short-summary: Indicates whether another user can take ownership of the virtual machine
                - name: --disk-type
                  short-summary: Storage type to use for virtual machine (i.e. Standard, Premium)
                - name: --expiration-date
                  short-summary: The expiration date in UTC(YYYY-mm-dd) for VM. Ex. 2017-03-25
                - name: --generate-ssh-keys
                  short-summary: Generate SSH public and private key files if missing
            """
helps['lab vm list'] = """
            type: command
            short-summary: Command to retrieve my vms from the Azure DevTest Lab.
            parameters:
                - name: --resource-group -g
                  short-summary: Name of the lab resource group
                - name: --lab-name
                  short-summary: Name of the Lab
                - name: --order-by
                  short-summary: The ordering expression for the results using OData notation
                - name: --top
                  short-summary: The maximum number of resources to return from the operation
                - name: --filters
                  short-summary: The filter to apply on the operation
                - name: --expand
                  short-summary: Specify the expand query.
                - name: --claimable
                  short-summary: List of claimable virtual machines in the lab. Cannot be used with --filters
                - name: --all
                  short-summary: List all virtual machines in the lab. Cannot be used with --filters
                - name: --object-id
                  short-summary: Owner's object id. If omitted, we'll pick one if available
            """
helps['lab vm apply-artifacts'] = """
            type: command
            short-summary: Command to apply artifacts to virtual machine in Azure DevTest Lab.
            parameters:
                - name: --resource-group -g
                  short-summary: Name of the lab resource group
                - name: --lab-name
                  short-summary: Name of the Lab
                - name: --name -n
                  short-summary: Name of the virtual machine
                - name: --artifacts
                  short-summary: JSON encoded array of artifacts to be applied. Use @{file} to load from a file
            """
helps['lab custom-image'] = """
            type: group
            short-summary: Commands to manage custom images of Azure DevTest Lab.
            """
helps['lab gallery-image'] = """
            type: group
            short-summary: Commands to list gallery images of Azure DevTest Lab.
            """
helps['lab artifact'] = """
            type: group
            short-summary: Commands to manage artifact of Azure DevTest Lab.
            """
helps['lab artifact-source'] = """
            type: group
            short-summary: Commands to manage artifact source of Azure DevTest Lab.
            """
helps['lab vnet'] = """
            type: group
            short-summary: Commands to manage Azure DevTest Lab's Virtual Network.
            """
helps['lab formula'] = """
            type: group
            short-summary: Commands to manage formulas in the Azure DevTest Lab.
            """

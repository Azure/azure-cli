# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

helps['lab'] = """
            type: group
            short-summary: Commands to manage DevTest Labs.
            """
helps['lab vm'] = """
            type: group
            short-summary: Commands to manage VM in a DevTest Lab.
            """
helps['lab vm create'] = """
            type: command
            short-summary: Command to create VM in a DevTest Lab.
            parameters:
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
                  short-summary: Name of the formula. Use az lab formula list for available formulas. Use --artifacts to pass-in
                                 parameters required by the artifacts of the formula
                - name: --size
                  short-summary: The VM size to be created. See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info.
                                 Required when creating VM from gallery or custom image
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
                - name: --ip-configuration
                  short-summary: Type of ip configuration to use with the VM. Allowed values are shared, public, private.
                                 If omitted, will be selected based on selected vnet
                - name: --artifacts
                  short-summary: JSON encoded array of artifacts to be applied. Use @{file} to load from a file
                - name: --tags
                  short-summary: Space separated tags in 'key[=value]' format. Use "" to clear existing tags
                - name: --allow-claim
                  short-summary: Flag indicating whether the VM will be created as a claimable VM in the lab
                - name: --disk-type
                  short-summary: Storage type to use for virtual machine (i.e. Standard, Premium)
                - name: --expiration-date
                  short-summary: The expiration date in UTC(YYYY-mm-dd) for VM. Ex. 2017-03-25
                - name: --generate-ssh-keys
                  short-summary: Generate SSH public and private key files if missing
            examples:
                - name: Create a Virtual Machine in the lab from gallery image.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2
                - name: Create a Virtual Machine in the lab from gallery image with ssh authentication.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2 --authentication-type ssh
                - name: Create a claimable Virtual Machine in the lab from gallery image with password authentication.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2 --allow-claim
                - name: Create a windows Virtual Machine in the lab from gallery image with password authentication.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Windows Server 2008 R2 SP1" --image-type gallery --size Standard_DS1_v2
                - name: Create a Virtual Machine in the lab from custom image.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "jenkins_custom" --image-type custom --size Standard_DS1_v2
                - name: Create a Virtual Machine in the lab with public ip configuration.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2 --ip-configuration public
                - name: Create a Virtual Machine from a formula.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --formula MyFormula
            """
helps['lab vm list'] = """
            type: command
            short-summary: Command to retrieve my vms from the Azure DevTest Lab.
            parameters:
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
                  short-summary: Name of lab's resource group
                - name: --lab-name
                  short-summary: Name of the Lab
                - name: --name -n
                  short-summary: Name of the virtual machine
                - name: --artifacts
                  short-summary: JSON encoded array of artifacts to be applied. Use @{file} to load from a file
            """
helps['lab custom-image'] = """
            type: group
            short-summary: Commands to manage custom images of a DevTest Lab.
            """
helps['lab gallery-image'] = """
            type: group
            short-summary: Commands to list Azure Marketplace images allowed in a given DevTest Lab.
            """
helps['lab artifact'] = """
            type: group
            short-summary: Commands to manage DevTest Labs artifacts.
            """
helps['lab artifact-source'] = """
            type: group
            short-summary: Commands to manage DevTest Lab artifact sources.
            """
helps['lab vnet'] = """
            type: group
            short-summary: Commands to manage Virtual Networks of a DevTest Lab.
            """
helps['lab formula'] = """
            type: group
            short-summary: Commands to manage formulas of a DevTest Lab.
            """

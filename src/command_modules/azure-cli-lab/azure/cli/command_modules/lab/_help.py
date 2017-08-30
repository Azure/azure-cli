# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['lab'] = """
            type: group
            short-summary: Commands to manage DevTest Labs.
            """
helps['lab vm'] = """
            type: group
            short-summary: Commands to manage a VM in a DevTest Lab.
            """
helps['lab vm create'] = """
            type: command
            short-summary: Command to create a VM in a DevTest Lab.
            parameters:
                - name: --name -n
                  short-summary: Name of the virtual machine.
                - name: --lab-name
                  short-summary: Name of the Lab.
                - name: --notes
                  short-summary: Notes for the virtual machine.
                - name: --image
                  short-summary: The name of the operating system image (Gallery Image Name and Custom Image Name/ID).
                  long-summary:  Use 'az lab gallery-image list' for available gallery images or 'az lab custom-image list' for available custom images.
                - name: --image-type
                  short-summary: 'Type of the image. Allowed values are: gallery, custom'
                - name: --formula
                  short-summary: Name of the formula. Use 'az lab formula list' for available formulas.
                                 Use 'az lab formula' with the --export-artifacts flag to export & update artifacts then supply
                                 it via the --artifacts argument
                - name: --size
                  short-summary: The size of the VM to be created. See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info.
                - name: --admin-username
                  short-summary: Username for the VM admin.
                - name: --admin-password
                  short-summary: Password for the VM admin.
                - name: --ssh-key
                  short-summary: The SSH public key or public key file path. Use --generate-ssh-keys to generate ssh keys.
                - name: --authentication-type
                  short-summary: 'Type of authentication to use with the VM. Allowed values are: password, ssh.'
                - name: --saved-secret
                  short-summary: Name of the saved secret to be used for authentication.
                  long-summary: When this value is provided, it is used in the place of other authentication methods.
                - name: --vnet-name
                  short-summary: Name of the virtual network to add the VM to.
                - name: --subnet
                  short-summary: Name of the subnet to add the VM to.
                - name: --ip-configuration
                  short-summary: 'Type of ip configuration to use for the VM. Allowed values are: shared, public, private.'
                  long-summary: If omitted, will be selected based on the VM's vnet.
                - name: --artifacts
                  short-summary: JSON encoded array of artifacts to be applied. Use @file to load from a file.
                - name: --tags
                  short-summary: Space separated tags in 'key[=value]' format.
                - name: --allow-claim
                  short-summary: Flag indicating whether the VM will be created as claimable.
                - name: --disk-type
                  short-summary: Storage type to use for virtual machine.
                - name: --expiration-date
                  short-summary: The expiration date in UTC(YYYY-mm-dd) for the VM.
                - name: --generate-ssh-keys
                  short-summary: Generate SSH public and private key files if missing.
            examples:
                - name: Create a Virtual Machine in the lab from a gallery image.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2
                - name: Create a Virtual Machine in the lab from a gallery image with ssh authentication.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2 --authentication-type ssh
                - name: Create a claimable Virtual Machine in the lab from a gallery image with password authentication.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2 --allow-claim
                - name: Create a windows Virtual Machine in the lab from a gallery image with password authentication.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Windows Server 2008 R2 SP1" --image-type gallery --size Standard_DS1_v2
                - name: Create a Virtual Machine in the lab from a custom image.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "jenkins_custom" --image-type custom --size Standard_DS1_v2
                - name: Create a Virtual Machine in the lab with a public ip.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --image "Ubuntu Server 16.04 LTS" --image-type gallery --size Standard_DS1_v2 --ip-configuration public
                - name: Create a Virtual Machine from a formula.
                  text: >
                    az lab vm create --lab-name MyLab -g MyRG --name MyVM --formula MyFormula --artifacts @/artifacts.json
            """
helps['lab vm list'] = """
            type: command
            short-summary: List VMs in a Azure DevTest Lab.
            parameters:
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --order-by
                  short-summary: The ordering expression for the results using OData notation.
                - name: --top
                  short-summary: The maximum number of resources to return.
                - name: --filters
                  short-summary: The filter to apply.
                - name: --expand
                  short-summary: The expand query.
                - name: --claimable
                  short-summary: List only claimable virtual machines in the lab. Cannot be used with --filters
                - name: --all
                  short-summary: List all virtual machines in the lab. Cannot be used with --filters
                - name: --environment
                  short-summary: Name or ID of the environment to list virtual machines in. Cannot be used with --filters
                - name: --object-id
                  short-summary: Object ID of the owner to list  virtual machines for.
            """
helps['lab vm apply-artifacts'] = """
            type: command
            short-summary: Apply artifacts to a virtual machine in Azure DevTest Lab.
            parameters:
                - name: --resource-group -g
                  short-summary: Name of lab's resource group.
                - name: --lab-name
                  short-summary: Name of the Lab.
                - name: --name -n
                  short-summary: Name of the virtual machine.
                - name: --artifacts
                  short-summary: JSON encoded array of artifacts to be applied. Use @file to load from a file.
            """
helps['lab vm claim'] = """
            type: command
            short-summary: Claim a virtual machine from the Lab.
            parameters:
                - name: --ids
                  short-summary: Space separated list of VM IDs to claim.
                - name: --resource-group -g
                  short-summary: Name of lab's resource group.
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --name -n
                  short-summary: Name of the virtual machine to claim.
            examples:
                - name: Claim any available virtual machine in the lab.
                  text: >
                    az lab vm claim -g MyRG --lab-name MyLab
                - name: Claim a specific virtual machine in the lab.
                  text: >
                    az lab vm claim -g MyRG --lab-name MyLab --name MyVM
                - name: Claim multiple virtual machines in the lab using --ids.
                  text: >
                    az lab vm claim --ids \\
                            /subscriptions/{SubID}/resourcegroups/{MyRG}/providers/microsoft.devtestlab/labs/{MyLab}/virtualmachines/{MyVM1} \\
                            /subscriptions/{SubID}/resourcegroups/{MyRG}/providers/microsoft.devtestlab/labs/{MyLab}/virtualmachines/{MyVM2}
            """
helps['lab custom-image'] = """
            type: group
            short-summary: Manage custom images of a DevTest Lab.
            """
helps['lab custom-image create'] = """
            type: command
            short-summary: Create a custom image in a DevTest Lab.
            parameters:
                - name: --name -n
                  short-summary: Name of the image.
                - name: --lab-name
                  short-summary: Name of the Lab.
                - name: --author
                  short-summary: The author of the custom image.
                - name: --description
                  short-summary: A detailed description for the custom image.
                - name: --source-vm-id
                  short-summary: The resource ID of a virtual machine in the provided lab.
                - name: --os-type
                  short-summary: 'Type of the OS on which the custom image is based. Allowed values are: Windows, Linux'
                - name: --os-state
                  short-summary: The current state of the virtual machine.
                  long-summary: >
                    For Windows virtual machines: NonSysprepped, SysprepRequested, SysprepApplied
                    For Linux virtual machines - NonDeprovisioned, DeprovisionRequested, DeprovisionApplied
            examples:
                - name: Create a custom image in the lab from a running Windows virtual machine without applying sysprep.
                  text: >
                    az lab custom-image create --lab-name MyLab -g MyRG --name MyVM \\
                            --os-type Windows --os-state NonSysprepped \\
                            --source-vm-id "/subscriptions/mysubscription/resourcegroups/myresourcegroup/microsoft.devtestlab/labs/mylab/virtualmachines/myvirtualmachine"
            """
helps['lab gallery-image'] = """
            type: group
            short-summary: List Azure Marketplace images allowed in a given DevTest Lab.
            """
helps['lab artifact'] = """
            type: group
            short-summary: Manage DevTest Labs artifacts.
            """
helps['lab artifact-source'] = """
            type: group
            short-summary: Manage DevTest Lab artifact sources.
            """
helps['lab vnet'] = """
            type: group
            short-summary: Manage Virtual Networks of a DevTest Lab.
            """
helps['lab formula'] = """
            type: group
            short-summary: Manage formulas of a DevTest Lab.
            """
helps['lab formula show'] = """
            type: command
            short-summary: Show formulae from the Azure DevTest Lab.
            parameters:
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --name -n
                  short-summary: Name of the formula.
            """
helps['lab formula export-artifacts'] = """
            type: command
            short-summary: Export artifacts from a formula.
            parameters:
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --name -n
                  short-summary: Name of the formula.
            """
helps['lab secret'] = """
            type: group
            short-summary: Manage secrets of a DevTest Lab.
            """
helps['lab secret set'] = """
            type: command
            short-summary: Sets a secret in a DevTest Lab.
            parameters:
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --name -n
                  short-summary: Name of the secret.
                - name: --value
                  short-summary: Value of the secret.
            """
helps['lab arm-template'] = """
            type: group
            short-summary: Manage Azure Resource Manager (ARM) templates in a DevTest Lab.
            """
helps['lab arm-template show'] = """
            type: command
            short-summary: Show ARM templates in a DevTest Lab.
            parameters:
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --name -n
                  short-summary: Name of the azure resource manager template.
                - name: --resource-group -g
                  short-summary: Name of lab's resource group.
                - name: --export-parameters
                  short-summary: Whether or not to export parameters template.
                - name: --artifact-source-name
                  short-summary: Name of the artifact source.
            """
helps['lab environment'] = """
            type: group
            short-summary: Manage environments in a DevTest Lab.
            """
helps['lab environment create'] = """
            type: command
            short-summary: Create an environment.
            parameters:
                - name: --lab-name
                  short-summary: Name of the lab.
                - name: --name -n
                  short-summary: Name of the environment.
                - name: --resource-group -g
                  short-summary: Name of the lab's resource group.
                - name: --arm-template
                  short-summary: Name or ID of the resource manager template in the lab.
                - name: --artifact-source-name
                  short-summary: Name of the artifact source in the lab.
                  long-summary: Use 'az lab artifact-source list' to see available artifact sources.
                - name: --parameters
                  short-summary: JSON encoded list of parameters. Use @file to load from a file.
                - name: --tags
                  short-summary: The tags for the resource.
            """
helps['lab environment delete'] = """
            type: command
            short-summary: Delete an environment.
            """
helps['lab environment list'] = """
            type: command
            short-summary: List environments.
            """
helps['lab environment show'] = """
            type: command
            short-summary: Get an environment.
            """

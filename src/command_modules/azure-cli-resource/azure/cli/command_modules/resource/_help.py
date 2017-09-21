# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long, too-many-lines
helps['managedapp'] = """
    type: group
    short-summary: Manage template solutions provided and maintained by Independent Software Vendors (ISVs).
"""
helps['managedapp definition'] = """
    type: group
    short-summary: Manage Azure Managed Applications.
"""
helps['managedapp create'] = """
    type: command
    short-summary: Create a managed application.
    examples:
        - name: Create a managed application of kind 'ServiceCatalog'. This requires a valid managed application definition ID.
          text: |
            az managedapp create -g MyResourceGroup -n MyManagedApp -l westcentralus --kind ServiceCatalog \\
                -m "/subscriptions/{SubID}/resourceGroups/{ManagedRG}" \\
                -d "/subscriptions/{SubID}/resourceGroups/{MyRG}/providers/Microsoft.Solutions/applianceDefinitions/{ManagedAppDef}"
        - name: Create a managed application of kind 'MarketPlace'. This requires a valid plan, containing details about existing marketplace package like plan name, version, publisher and product.
          text: |
            az managedapp create -g MyResourceGroup -n MyManagedApp -l westcentralus --kind MarketPlace \\
                -m "/subscriptions/{SubID}/resourceGroups/myManagedRG" \\
                --plan-name ContosoAppliance --plan-version "1.0" --plan-product "contoso-appliance" --plan-publisher Contoso
"""
helps['managedapp definition create'] = """
    type: command
    short-summary: Create a managed application definition.
    examples:
        - name: Create a managed application defintion.
          text: >
            az managedapp definition create -g MyResourceGroup -n MyManagedAppDef -l eastus --display-name "MyManagedAppDef" \\
                --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
                --package-file-uri "https://path/to/myPackage.zip"
        - name: Create a managed application defintion with inline values for createUiDefinition and mainTemplate.
          text: >
            az managedapp definition create -g MyResourceGroup -n MyManagedAppDef -l eastus --display-name "MyManagedAppDef" \\
                --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
                --create-ui-definition @myCreateUiDef.json --main-template @myMainTemplate.json
"""
helps['managedapp definition delete'] = """
    type: command
    short-summary: Delete a managed application definition.
"""
helps['managedapp definition list'] = """
    type: command
    short-summary: List managed application definitions.
"""
helps['managedapp delete'] = """
    type: command
    short-summary: Delete a managed application.
"""
helps['managedapp list'] = """
    type: command
    short-summary: List managed applications.
"""
helps['lock'] = """
    type: group
    short-summary: Manage Azure locks.
    parameters:
        - name: --resource-type
          type: string
          text: The name of the resource type. May have a provider namespace.
        - name: --resource-provider-namespace
          type: string
          text: The name of the resource provider.
        - name: --parent-resource-path
          type: string
          text: The path to the parent resource of the resource being locked.
        - name: --resource-name
          type: string
          text: The name of the resource this lock applies to.
"""
helps['lock create'] = """
    type: command
    short-summary: Create a lock.
    long-summary: 'Locks can exist at three different scopes: subscription, resource group and resource.'
    parameters:
        - name: --notes
          type: string
          short-summary: Notes about this lock.
    examples:
        - name: Create a read-only subscription level lock.
          text: >
            az lock create --name lockName --resource-group group --lock-type ReadOnly
    """
helps['lock delete'] = """
    type: commands
    short-summary: Delete a lock.
    examples:
        - name: Delete a resource-group-level lock
          text: >
            az lock delete --name lockName --resource-group group
    """
helps['lock list'] = """
    type: command
    short-summary: List lock information.
    examples:
        - name: List out the locks on a vnet resource. Includes locks in the associated group and subscription.
          text: >
            az lock list --resource-name myvnet --resource-type Microsoft.Network/virtualNetworks -g group
        - name: List out all locks on the subscription level
          text: >
            az lock list
    """
helps['lock show'] = """
    type: command
    short-summary: Show the properties of a lock
    examples:
        - name: Show a subscription level lock
          text: >
            az lock show -n lockname
    """
helps['lock update'] = """
    type: command
    short-summary: Update a lock.
    parameters:
        - name: --notes
          type: string
          short-summary: Notes about this lock.
    examples:
        - name: Update a resource-group level lock with new notes and type
          text: >
            az lock update --name lockName --resource-group group --notes newNotesHere --lock-type CanNotDelete
    """
helps['policy'] = """
    type: group
    short-summary: Manage resource policies.
"""
helps['policy definition'] = """
    type: group
    short-summary: Manage resource policy definitions.
"""
helps['policy definition create'] = """
            type: command
            short-summary: Create a policy definition.
            parameters:
                - name: --rules
                  type: string
                  short-summary: Policy rules in JSON format, or a path to a file containing JSON rules.
            examples:
                - name: Create a read-only policy.
                  text: |
                    az policy definition create -n readOnlyStorage --rules \\
                        { \\
                            "if": \\
                            { \\
                                "source": "action", \\
                                "equals": "Microsoft.Storage/storageAccounts/write" \\
                            }, \\
                            "then": \\
                            { \\
                                "effect": "deny" \\
                            } \\
                        }
                - name: Create a policy parameter definition with the following example
                  text: |
                        {
                            "allowedLocations": {
                                "type": "array",
                                "metadata": {
                                    "description": "The list of locations that can be specified
                                                    when deploying resources",
                                    "strongType": "location",
                                    "displayName": "Allowed locations"
                                }
                            }
                        }
"""
helps['policy definition delete'] = """
    type: command
    short-summary: Delete a policy definition.
"""
helps['policy definition show'] = """
    type: command
    short-summary: get a policy definition.
"""
helps['policy definition update'] = """
    type: command
    short-summary: Update a policy definition.
"""
helps['policy definition list'] = """
    type: command
    short-summary: List policy definitions.
"""
helps['policy setdefinition create'] = """
            type: command
            short-summary: Create a policy set definition.
            parameters:
                - name: --definitions
                  type: string
                  short-summary: Policy definitions in JSON format, or a path to a file containing JSON rules.
            examples:
                - name: Create a policy set definition.
                  text: |
                    az policy setdefinition create -n readOnlyStorage --definitions \\
                        [ \\
                            { \\
                                "policyDefinitionId": "/subscriptions/mySubId/providers/Microsoft.Authorization/policyDefinitions/storagePolicy" \\
                            } \\
                        ]
"""
helps['policy setdefinition delete'] = """
    type: command
    short-summary: Delete a policy set definition.
"""
helps['policy setdefinition show'] = """
    type: command
    short-summary: get a policy set definition.
"""
helps['policy setdefinition update'] = """
    type: command
    short-summary: Update a policy set definition.
"""
helps['policy setdefinition list'] = """
    type: command
    short-summary: List policy set definitions.
"""
helps['policy assignment'] = """
    type: group
    short-summary: Manage resource policy assignments.
"""
helps['policy assignment create'] = """
    type: command
    short-summary: Create a resource policy assignment.
    examples:
        - name: Provide rule parameter values with the following example
          text: |
                {
                    "allowedLocations": {
                        "value": [
                            "australiaeast",
                            "eastus",
                            "japaneast"
                        ]
                    }
                }
"""
helps['policy assignment delete'] = """
    type: command
    short-summary: Delete a resource policy assignment.
"""
helps['policy assignment show'] = """
    type: command
    short-summary: Show a resource policy assignment.
"""
helps['policy assignment list'] = """
    type: command
    short-summary: List resource policy assignments.
"""
helps['resource'] = """
    type: group
    short-summary: Manage Azure resources.
"""
helps['resource list'] = """
    type: command
    short-summary: List resources.
    examples:
        - name: List all resources in the West US region.
          text: >
            az resource list --location westus
        - name: List all resources with the name 'resourceName'.
          text: >
            az resource list --name 'resourceName'
        - name: List all resources with the tag 'test'.
          text: >
             az resource list --tag test
        - name: List all resources with a tag that starts with 'test'.
          text: >
            az resource list --tag test*
        - name: List all resources with the tag 'test' that have the value 'example'.
          text: >
            az resource list --tag test=example
"""

helps['resource show'] = """
    type: command
    short-summary: Get the details of a resource.
    examples:
        - name: Show a virtual machine resource named 'MyVm'.
          text: >
            az vm show -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines"
        - name: Show a web app using a resource identifier.
          text: >
            az resource show --id /subscriptions/{SubID}/resourceGroups/{MyRG}/providers/Microsoft.Web/sites/{MyWebapp}
        - name: Show a subnet in the 'Microsoft.Network' namespace which belongs to the virtual network 'MyVnet'.
          text: >
            az resource show -g MyResourceGroup -n MySubnet --namespace Microsoft.Network --parent virtualnetworks/MyVnet --resource-type subnets
        - name: Show a subnet using a resource identifier.
          text: >
            az resource show --id /subscriptions/{SubID}/resourceGroups/{MyRG}/providers/Microsoft.Network/virtualNetworks/{MyVnet}/subnets/{MySubnet}
        - name: Show an application gateway path rule.
          text: >
            az resource show -g MyResourceGroup --namespace Microsoft.Network --parent applicationGateways/ag1/urlPathMaps/map1 --resource-type pathRules -n rule1
"""

helps['resource delete'] = """
    type: command
    short-summary: Delete a resource.
    examples:
        - name: Delete a virtual machine named 'MyVm'.
          text: >
            az vm delete -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines"
        - name: Delete a web app using a resource identifier.
          text: >
            az resource delete --id /subscriptions/{SubID}/resourceGroups/{MyRG}/providers/Microsoft.Web/sites/{MyWebApp}
        - name: Delete a subnet using a resource identifier.
          text: >
            az resource delete --id /subscriptions/{SubID}/resourceGroups/{MyRG}/providers/Microsoft.Network/virtualNetworks/{MyVNET}/subnets/{MySubnet}
"""

helps['resource tag'] = """
    type: command
    short-summary: Tag a resource.
    examples:
        - name: Tag the virtual machine 'MyVm' with the key 'vmlist' and value 'vm1'.
          text: >
            az resource tag --tags vmlist=vm1 -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines"
        - name: Tag a web app with the key 'vmlist' and value 'vm1', using a resource identifier.
          text: >
            az resource tag --tags vmlist=vm1 --id /subscriptions/{SubID}/resourceGroups/{MyRG}/providers/Microsoft.Web/sites/{MyWebApp}
"""

helps['resource create'] = """
    type: command
    short-summary: create a resource.
    examples:
       - name: Create an API app by providing a full JSON configuration.
         text: |
            az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites --is-full-object --properties \\
                    '{\\
                        "kind": "api",\\
                        "location": "West US",\\
                        "properties": {\\
                            "serverFarmId": "/subscriptions/{SubID}/resourcegroups/{MyRG}/providers/Microsoft.Web/serverfarms/{MyServicePlan}"\\
                        }\\
                    }'
       - name: Create a resource by loading JSON configuration from a file.
         text: >
            az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites --is-full-object --properties @jsonConfigFile
       - name: Create a web app with the minimum required configuration information.
         text: |
            az resource create -g myRG -n myWeb --resource-type Microsoft.web/sites --properties \\
                { \\
                    "serverFarmId":"/subscriptions/{SubID}/resourcegroups/{MyRG}/providers/Microsoft.Web/serverfarms/{MyServicePlan}" \\
                }
"""

helps['resource update'] = """
    type: command
    short-summary: Update a resource.
"""

helps['feature'] = """
    type: group
    short-summary: Manage resource provider features.
"""

helps['group'] = """
    type: group
    short-summary: Manage resource groups and template deployments.
"""

helps['group exists'] = """
    type: command
    short-summary: Check if a resource group exists.
    examples:
        - name: Check if 'MyResourceGroup' exists.
          text: >
            az group exists -n MyResourceGroup
"""

helps['group create'] = """
    type: command
    short-summary: Create a new resource group.
    examples:
        - name: Create a new resource group in the West US region.
          text: >
            az group create -l westus -n MyResourceGroup
"""

helps['group delete'] = """
    type: command
    short-summary: Delete a resource group.
    examples:
        - name: Delete a resource group.
          text: >
            az group delete -n MyResourceGroup
"""

helps['group list'] = """
    type: command
    short-summary: List resource groups.
    examples:
        - name: List all resource groups located in the West US region.
          text: >
            az group list --query "[?location=='westus']"
"""

helps['group update'] = """
    type: command
    short-summary: Update a resource group.
"""
helps['group wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a condition of the resource group is met.
"""
helps['group deployment'] = """
    type: group
    short-summary: Manage Azure Resource Manager deployments.
"""
helps['group deployment create'] = """
    type: command
    short-summary: Start a deployment.
    parameters:
        - name: --parameters
          short-summary: Supply deployment parameter values.
          long-summary: >
            Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
            It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
    examples:
        - name: Create a deployment from a remote template file, using parameters from a local JSON file.
          text: >
            az group deployment create -g MyResourceGroup --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
        - name: Create a deployment from a local template file, using parameters from a JSON string.
          text: |
            az group deployment create -g MyResourceGroup --template-file azuredeploy.json --parameters \\
                    '{ \\
                        "location": {\\
                            "value": "westus" \\
                        } \\
                    }'
        - name: Create a deployment from a local template, using a parameter file and selectively overriding key/value pairs.
          text: >
            az group deployment create -g MyResourceGroup --template-file azuredeploy.json --parameters @params.json --parameters MyValue=This MyArray=@array.json
"""
helps['group deployment export'] = """
    type: command
    short-summary: Export the template used for a deployment.
"""
helps['group deployment validate'] = """
    type: command
    short-summary: Validate whether a template is syntactically correct.
    parameters:
        - name: --parameters
          short-summary: Supply deployment parameter values.
          long-summary: >
            Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
            It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
"""
helps['group deployment wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a deployment condition is met.
"""
helps['group deployment operation'] = """
    type: group
    short-summary: Manage deployment operations.
"""
helps['provider'] = """
    type: group
    short-summary: Manage resource providers.
"""

helps['provider list'] = """
    type: command
    examples:
        - name: Display all resource types for the network resource provider.
          text: >
            az provider list --query [?namespace=='Microsoft.Network'].resourceTypes[].resourceType
"""

helps['provider register'] = """
    type: command
    short-summary: Register a provider.
"""
helps['provider unregister'] = """
    type: command
    short-summary: Unregister a provider.
"""
helps['provider operation'] = """
    type: group
    short-summary: Get provider operations metadatas.
"""
helps['provider operation show'] = """
    type: command
    short-summary: Get an individual provider's operations.
"""
helps['provider operation list'] = """
    type: command
    short-summary: Get operations from all providers.
"""
helps['tag'] = """
    type: group
    short-summary: Manage resource tags.
"""
helps['resource link'] = """
    type: group
    short-summary: Manage links between resources.
    long-summary: >
        Linking is a feature of the Resource Manager. It enables declaring relationships between resources even if they do not reside in the same resource group.
        Linking has no impact on resource usage, no impact on billing, and no impact on role-based access. It allows for managing multiple resources across groups
        as a single unit.
"""
helps['resource link create'] = """
    type: command
    short-summary: Create a new link between resources.
    long-summary: A link-id is of the form /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/{provider-namespace}/{resource-type}/{resource-name}/Microsoft.Resources/links/{link-name}
    examples:
        - name: Create a link from <link-id> to <resource-id> with notes "some notes to explain this link"
          text: >
            az resource link create --link-id <link-id> --target-id <resource-id> --notes "some notes to explain this link"
"""
helps['resource link update'] = """
    type: command
    short-summary: Update link between resources.
    long-summary: A link-id is of the form /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/{provider-namespace}/{resource-type}/{resource-name}/Microsoft.Resources/links/{link-name}
    examples:
        - name: Update the notes for <link-id> notes "some notes to explain this link"
          text: >
            az resource link update --link-id <link-id> --notes "some notes to explain this link"
"""
helps['resource link delete'] = """
    type: command
    short-summary: Delete a link between resources.
    long-summary: A link-id is of the form /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/{provider-namespace}/{resource-type}/{resource-name}/Microsoft.Resources/links/{link-name}
    examples:
        - name: Delete link <link-id>
          text: >
            az resource link delete --link-id <link-id>
"""
helps['resource link list'] = """
    type: command
    short-summary: List resource links.
    examples:
        - name: List links, filtering with <filter-string>
          text: >
            az resource link list --filter <filter-string>
        - name: List all links at /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myGroup
          text: >
            az resource link list --scope /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myGroup
"""
helps['resource link show'] = """
    type: command
    short-summary: Get details for a resource link.
    long-summary: A link-id is of the form /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/{provider-namespace}/{resource-type}/{resource-name}/Microsoft.Resources/links/{link-name}
    examples:
        - name: Show the <link-id> resource link.
          text: >
            az resource link show --link-id <link-id>
"""

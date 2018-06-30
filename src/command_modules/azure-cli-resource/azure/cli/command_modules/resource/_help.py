# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

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
                -m "/subscriptions/{SubID}/resourceGroups/{ManagedResourceGroup}" \\
                -d "/subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Solutions/applianceDefinitions/{ApplianceDefinition}"
        - name: Create a managed application of kind 'MarketPlace'. This requires a valid plan, containing details about existing marketplace package like plan name, version, publisher and product.
          text: |
            az managedapp create -g MyResourceGroup -n MyManagedApp -l westcentralus --kind MarketPlace \\
                -m "/subscriptions/{SubID}/resourceGroups/{ManagedResourceGroup}" \\
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
"""
helps['lock create'] = """
    type: command
    short-summary: Create a lock.
    long-summary: 'Locks can exist at three different scopes: subscription, resource group and resource.'
    examples:
        - name: Create a read-only subscription level lock.
          text: >
            az lock create --name lockName --resource-group group --lock-type ReadOnly
    """
helps['lock delete'] = """
    type: command
    short-summary: Delete a lock.
    examples:
        - name: Delete a resource group-level lock
          text: >
            az lock delete --name lockName --resource-group group
    """
helps['lock list'] = """
    type: command
    short-summary: List lock information.
    examples:
        - name: List out the locks on a vnet resource. Includes locks in the associated group and subscription.
          text: >
            az lock list --resource myvnet --resource-type Microsoft.Network/virtualNetworks -g group
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
    examples:
        - name: Update a resource group level lock with new notes and type
          text: >
            az lock update --name lockName --resource-group group --notes newNotesHere --lock-type CanNotDelete
    """
helps['account lock'] = """
    type: group
    short-summary: Manage Azure subscription level locks.
"""
helps['account lock create'] = """
    type: command
    short-summary: Create a subscription lock.
    examples:
        - name: Create a read-only subscription level lock.
          text: >
            az account lock create --lock-type ReadOnly -n lockName
    """
helps['account lock delete'] = """
    type: command
    short-summary: Delete a subscription lock.
    examples:
        - name: Delete a subscription lock
          text: >
            az account lock delete --name lockName
    """
helps['account lock list'] = """
    type: command
    short-summary: List lock information in the subscription.
    examples:
        - name: List out all locks on the subscription level
          text: >
            az account lock list
    """
helps['account lock show'] = """
    type: command
    short-summary: Show the details of a subscription lock
    examples:
        - name: Show a subscription level lock
          text: >
            az account lock show -n lockname
    """
helps['account lock update'] = """
    type: command
    short-summary: Update a subscription lock.
    examples:
        - name: Update a subscription lock with new notes and type
          text: >
            az account lock update --name lockName --notes newNotesHere --lock-type CanNotDelete
    """
helps['account management-group'] = """
    type: group
    short-summary: Manage Azure Management Groups.
"""

helps['account management-group subscription'] = """
    type: group
    short-summary: Subscription operations for Management Groups.
"""

helps['account management-group list'] = """
    type: command
    short-summary: List all management groups.
    long-summary: List of all management groups in the current tenant.
    examples:
        - name: List all management groups
          text: >
             az account management-group list
"""

helps['account management-group show'] = """
    type: command
    short-summary: Get a specific management group.
    long-summary: Get the details of the management group.
    parameters:
        - name: --name -n
          type: string
          short-summary: Name of the management group.
        - name: --expand -e
          type: bool
          short-summary: If given, lists the children in the first level of hierarchy.
        - name: --recurse -r
          type: bool
          short-summary: If given, lists the children in all levels of hierarchy.
    examples:
        - name: Get a management group.
          text: >
             az account management-group show --name GroupName
        - name: Get a management group with children in the first level of hierarchy.
          text: >
             az account management-group show --name GroupName -e
        - name: Get a management group with children in all levels of hierarchy.
          text: >
             az account management-group show --name GroupName -e -r
"""

helps['account management-group create'] = """
    type: command
    short-summary: Create a new management group.
    long-summary: Create a new management group.
    parameters:
        - name: --name -n
          type: string
          short-summary: Name of the management group.
        - name: --display-name -d
          type: string
          short-summary: Sets the display name of the management group. If null, the group name is set as the display name.
        - name: --parent -p
          type: string
          short-summary: Sets the parent of the management group. Can be the fully qualified id or the name of the management group. If null, the root tenant group is set as the parent.
    examples:
        - name: Create a new management group.
          text: >
             az account management-group create --name GroupName
        - name: Create a new management group with a specific display name.
          text: >
             az account management-group create --name GroupName --display-name DisplayName
        - name: Create a new management group with a specific parent.
          text: >
             az account management-group create --name GroupName --parent ParentId/ParentName
        - name: Create a new management group with a specific display name and parent.
          text: >
             az account management-group create --name GroupName --display-name DisplayName --parent ParentId/ParentName
"""

helps['account management-group update'] = """
    type: command
    short-summary: Update an existing management group.
    long-summary: Update an existing management group.
    parameters:
        - name: --name -n
          type: string
          short-summary: Name of the management group.
        - name: --display-name -d
          type: string
          short-summary: Updates the display name of the management group. If null, no change is made.
        - name: --parent -p
          type: string
          short-summary: Update the parent of the management group. Can be the fully qualified id or the name of the management group. If null, no change is made.
    examples:
        - name: Update an existing management group with a specific display name.
          text: >
             az account management-group update --name GroupName --display-name DisplayName
        - name: Update an existing management group with a specific parent.
          text: >
             az account management-group update --name GroupName --parent ParentId/ParentName
        - name: Update an existing management group with a specific display name and parent.
          text: >
             az account management-group update --name GroupName --display-name DisplayName --parent ParentId/ParentName
"""

helps['account management-group delete'] = """
    type: command
    short-summary: Delete an existing management group.
    long-summary: Delete an existing management group.
    parameters:
        - name: --name -n
          type: string
          short-summary: Name of the management group.
    examples:
        - name: Delete an existing management group
          text: >
             az account management-group delete --name GroupName
"""

helps['account management-group subscription add'] = """
    type: command
    short-summary: Add a subscription to a management group.
    long-summary: Add a subscription to a management group.
    parameters:
        - name: --name -n
          type: string
          short-summary: Name of the management group.
        - name: --subscription -s
          type: string
          short-summary: Subscription Id or Name
    examples:
        - name: Add a subscription to a management group.
          text: >
             az account management-group subscription add --name GroupName --subscription Subscription
"""

helps['account management-group subscription remove'] = """
    type: command
    short-summary: Remove an existing subscription from a management group.
    long-summary: Remove an existing subscription from a management group.
    parameters:
        - name: --name -n
          type: string
          short-summary: Name of the management group.
        - name: --subscription -s
          type: string
          short-summary: Subscription Id or Name
    examples:
        - name: Remove an existing subscription from a management group.
          text: >
             az account management-group subscription remove --name GroupName --subscription Subscription
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
                    az policy definition create -n readOnlyStorage --rules '{
                            "if":
                            {
                                "field": "type",
                                "equals": "Microsoft.Storage/storageAccounts/write"
                            },
                            "then":
                            {
                                "effect": "deny"
                            }
                        }'
                - name: Create a policy parameter definition with the following example
                  text: |
                    az policy definition create -n allowedLocations --rules '{
                        "allowedLocations": {
                            "type": "array",
                            "metadata": {
                                "description": "The list of locations that can be specified when deploying resources",
                                "strongType": "location",
                                "displayName": "Allowed locations"
                            }
                        }
                    }'
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
helps['policy set-definition'] = """
    type: group
    short-summary: Manage resource policy set definitions.
"""
helps['policy set-definition create'] = """
            type: command
            short-summary: Create a policy set definition.
            parameters:
                - name: --definitions
                  type: string
                  short-summary: Policy definitions in JSON format, or a path to a file containing JSON rules.
            examples:
                - name: Create a policy set definition.
                  text: |
                    az policy setdefinition create -n readOnlyStorage --definitions '[
                            {
                                "policyDefinitionId": "/subscriptions/mySubId/providers/Microsoft.Authorization/policyDefinitions/storagePolicy"
                            }
                        ]'
"""
helps['policy set-definition delete'] = """
    type: command
    short-summary: Delete a policy set definition.
"""
helps['policy set-definition show'] = """
    type: command
    short-summary: get a policy set definition.
"""
helps['policy set-definition update'] = """
    type: command
    short-summary: Update a policy set definition.
"""
helps['policy set-definition list'] = """
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
                az policy assignment create --policy {PolicyNamed} -p '{
                    "allowedLocations": {
                        "value": [
                            "australiaeast",
                            "eastus",
                            "japaneast"
                        ]
                    }
                }'
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
            az resource list --tag 'test*'
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
            az resource show --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebapp
        - name: Show a subnet.
          text: >
            az resource show -g MyResourceGroup -n MySubnet --namespace Microsoft.Network --parent virtualnetworks/MyVnet --resource-type subnets
        - name: Show a subnet using a resource identifier.
          text: >
            az resource show --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/MySubnet
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
            az resource delete --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebapp
        - name: Delete a subnet using a resource identifier.
          text: >
            az resource delete --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/MySubnet
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
            az resource tag --tags vmlist=vm1 --id /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp}
"""

helps['resource create'] = """
    type: command
    short-summary: create a resource.
    examples:
       - name: Create an API app by providing a full JSON configuration.
         text: |
            az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites --is-full-object --properties '{
                        "kind": "api",
                        "location": "West US",
                        "properties": {
                            "serverFarmId": "/subscriptions/{SubID}/resourcegroups/{ResourceGroup}/providers/Microsoft.Web/serverfarms/{ServicePlan}"
                        }
                    }'
       - name: Create a resource by loading JSON configuration from a file.
         text: >
            az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites --is-full-object --properties @jsonConfigFile
       - name: Create a web app with the minimum required configuration information.
         text: |
            az resource create -g myRG -n myWeb --resource-type Microsoft.web/sites --properties '{
                    "serverFarmId":"/subscriptions/{SubID}/resourcegroups/{ResourceGroup}/providers/Microsoft.Web/serverfarms/{ServicePlan}"
                }'
"""

helps['resource update'] = """
    type: command
    short-summary: Update a resource.
"""

helps['resource invoke-action'] = """
    type: command
    short-summary: Invoke an action on the resource.
    long-summary: >
        A list of possible actions corresponding to a resource can be found at https://docs.microsoft.com/en-us/rest/api/. All POST requests are actions that can be invoked and are specified at the end of the URI path. For instance, to stop a VM, the
        request URI is https://management.azure.com/subscriptions/{SubscriptionId}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VM}/powerOff?api-version={APIVersion} and the corresponding action is `powerOff`. This can
        be found at https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/virtualmachines-stop.
    examples:
       - name: Power-off a vm, specified by Id.
         text: >
            az resource invoke-action --action powerOff \\
              --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VMName}
       - name: Capture information for a stopped vm.
         text: >
            az resource invoke-action --action capture \\
              --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VMName} \\
              --request-body '{
                "vhdPrefix": "myPrefix",
                "destinationContainerName": "myContainer",
                "overwriteVhds": true
            }'
"""

helps['feature'] = """
    type: group
    short-summary: Manage resource provider features.
"""

helps['feature list'] = """
    type: command
    short-summary: List preview features.
"""

helps['feature register'] = """
    type: command
    short-summary: register a preview feature.
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
            az group deployment create -g MyResourceGroup --template-file azuredeploy.json --parameters '{
                    "location": {
                        "value": "westus"
                    }
                }'
        - name: Create a deployment from a local template, using a parameter file and selectively overriding key/value pairs.
          text: >
            az group deployment create -g MyResourceGroup --template-file azuredeploy.json \\
                --parameters @params.json --parameters MyValue=This MyArray=@array.json
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
helps['deployment'] = """
    type: group
    short-summary: Manage Azure Resource Manager deployments at subscription scope.
"""
helps['deployment create'] = """
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
            az deployment create --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
        - name: Create a deployment from a local template file, using parameters from a JSON string.
          text: |
            az deployment create --location WestUS --template-file azuredeploy.json --parameters '{
                    "policyName": {
                        "value": "policy2"
                    }
                }'
        - name: Create a deployment from a local template, using a parameter file and selectively overriding key/value pairs.
          text: >
            az deployment create --location WestUS --template-file azuredeploy.json \\
                --parameters @params.json --parameters MyValue=This MyArray=@array.json
"""
helps['deployment export'] = """
    type: command
    short-summary: Export the template used for a deployment.
"""
helps['deployment validate'] = """
    type: command
    short-summary: Validate whether a template is syntactically correct.
    parameters:
        - name: --parameters
          short-summary: Supply deployment parameter values.
          long-summary: >
            Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
            It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
"""
helps['deployment wait'] = """
    type: command
    short-summary: Place the CLI in a waiting state until a deployment condition is met.
"""
helps['deployment operation'] = """
    type: group
    short-summary: Manage deployment operations.
"""
helps['group lock'] = """
    type: group
    short-summary: Manage Azure resource group locks.
"""
helps['group lock create'] = """
    type: command
    short-summary: Create a resource group lock.
    examples:
        - name: Create a read-only resource group level lock.
          text: >
            az group lock create --lock-type ReadOnly -n lockName -g MyResourceGroup
    """
helps['group lock delete'] = """
    type: command
    short-summary: Delete a resource group lock.
    examples:
        - name: Delete a resource group lock
          text: >
            az group lock delete --name lockName -g MyResourceGroup
    """
helps['group lock list'] = """
    type: command
    short-summary: List lock information in the resource-group.
    examples:
        - name: List out all locks on the resource group level
          text: >
            az group lock list -g MyResourceGroup
    """
helps['group lock show'] = """
    type: command
    short-summary: Show the details of a resource group lock
    examples:
        - name: Show a resource group level lock
          text: >
            az group lock show -n lockname -g MyResourceGroup
    """
helps['group lock update'] = """
    type: command
    short-summary: Update a resource group lock.
    examples:
        - name: Update a resource group lock with new notes and type
          text: >
            az group lock update --name lockName -g MyResourceGroup --notes newNotesHere --lock-type CanNotDelete
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
    long-summary: A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
    examples:
        - name: Create a link from {SourceID} to {ResourceID} with notes
          text: >
            az resource link create --link-id {SourceID} --target-id {ResourceID} --notes "SourceID depends on ResourceID"
"""
helps['resource link update'] = """
    type: command
    short-summary: Update link between resources.
    long-summary: A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
    examples:
        - name: Update the notes for {LinkID} notes "some notes to explain this link"
          text: >
            az resource link update --link-id {LinkID} --notes "some notes to explain this link"
"""
helps['resource link delete'] = """
    type: command
    short-summary: Delete a link between resources.
    long-summary: A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
    examples:
        - name: Delete link {LinkID}
          text: >
            az resource link delete --link-id {LinkID}
"""
helps['resource link list'] = """
    type: command
    short-summary: List resource links.
    examples:
        - name: List links, filtering with <filter-string>
          text: >
            az resource link list --filter <filter-string>
        - name: List all links for resource group {ResourceGroup} in subscription {SubID}
          text: >
            az resource link list --scope /subscriptions/{SubID}/resourceGroups/{ResourceGroup}
"""
helps['resource link show'] = """
    type: command
    short-summary: Get details for a resource link.
    long-summary: A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
"""
helps['resource lock'] = """
    type: group
    short-summary: Manage Azure resource level locks.
"""
helps['resource lock create'] = """
    type: command
    short-summary: Create a resource-level lock.
    examples:
        - name: Create a read-only resource level lock on a vnet.
          text: >
            az resource lock create --lock-type ReadOnly -n lockName -g MyResourceGroup --resource myvnet --resource-type Microsoft.Network/virtualNetworks
        - name: Create a read-only resource level lock on a vnet using a vnet id.
          text: >
            az resource lock create --lock-type ReadOnly -n lockName --resource /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VNETName}
    """
helps['resource lock delete'] = """
    type: command
    short-summary: Delete a resource-level lock.
    examples:
        - name: Delete a resource level lock
          text: >
            az resource lock delete --name lockName -g MyResourceGroup --resource myvnet --resource-type Microsoft.Network/virtualNetworks
        - name: Delete a resource level lock on a vnet using a vnet id.
          text: >
            az resource lock delete -n lockName --resource /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Network/virtualNetworks/{VMName}
    """
helps['resource lock list'] = """
    type: command
    short-summary: List lock information in the resource-level.
    examples:
        - name: List out all locks on a vnet
          text: >
            az resource lock list -g MyResourceGroup --resource myvnet --resource-type Microsoft.Network/virtualNetworks
    """
helps['resource lock show'] = """
    type: command
    short-summary: Show the details of a resource-level lock
    examples:
        - name: Show a resource level lock
          text: >
            az resource lock show -n lockname -g MyResourceGroup --resource myvnet --resource-type Microsoft.Network/virtualNetworks
    """
helps['resource lock update'] = """
    type: command
    short-summary: Update a resource-level lock.
    examples:
        - name: Update a resource level lock with new notes and type
          text: >
            az resource lock update --name lockName -g MyResourceGroup --resource myvnet --resource-type Microsoft.Network/virtualNetworks --notes newNotesHere --lock-type CanNotDelete
    """

# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['account lock'] = """
type: group
short-summary: Manage Azure subscription level locks.
"""

helps['account lock create'] = """
type: command
short-summary: Create a subscription lock.
examples:
  - name: Create a read-only subscription level lock.
    text: az account lock create --lock-type ReadOnly --name MyLockName
"""

helps['account lock delete'] = """
type: command
short-summary: Delete a subscription lock.
examples:
  - name: Delete a subscription lock.
    text: az account lock delete --name MyLockName
"""

helps['account lock list'] = """
type: command
short-summary: List lock information in the subscription.
examples:
  - name: List out all locks on the subscription level.
    text: az account lock list
"""

helps['account lock show'] = """
type: command
short-summary: Show the details of a subscription lock.
examples:
  - name: Show a subscription level lock.
    text: az account lock show --name MyLockName
"""

helps['account lock update'] = """
type: command
short-summary: Update a subscription lock.
examples:
  - name: Update a subscription lock with new notes and type.
    text: az account lock update --name MyLockName --notes newNotesHere --lock-type CanNotDelete
"""

helps['account management-group'] = """
type: group
short-summary: Manage Azure subscription-level management groups.
long-summary: For more information on Azure management groups, see [What are Azure management groups?](https://learn.microsoft.com/azure/governance/management-groups/overview)
"""

helps['account management-group create'] = """
type: command
short-summary: Create a new management group.
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
    text: az account management-group create --name MyGroupName
  - name: Create a new management group with a specific display name.
    text: az account management-group create --name MyGroupName --display-name MyDisplayName
  - name: Create a new management group with a specific parent.
    text: az account management-group create --name MyGroupName --parent ParentId/ParentName
  - name: Create a new management group with a specific display name and parent.
    text: az account management-group create --name MyGroupName --display-name MyDisplayName --parent ParentId/ParentName
"""

helps['account management-group delete'] = """
type: command
short-summary: Delete an existing management group.
parameters:
- name: --name -n
  type: string
  short-summary: Name of the management group.
examples:
  - name: Delete an existing management group.
    text: az account management-group delete --name MyGroupName
"""

helps['account management-group list'] = """
type: command
short-summary: List all management groups in the current subscription.
examples:
  - name: List all management groups.
    text: az account management-group list
"""

helps['account management-group show'] = """
type: command
short-summary: Get the details of a specific management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group (the last segment of the resource ID). Do not use display name.
  - name: --expand -e
    type: bool
    short-summary: If given, lists the children in the first level of hierarchy.
  - name: --recurse -r
    type: bool
    short-summary: If given, lists the children in all levels of hierarchy.
examples:
  - name: Get a management group.
    text: az account management-group show --name MyGroupName
  - name: Get a management group with children in the first level of hierarchy.
    text: az account management-group show --name MyGroupName --expand
  - name: Get a management group with children in all levels of hierarchy.
    text: az account management-group show --name MyGroupName --expand --recurse
"""

helps['account management-group subscription'] = """
type: group
short-summary: Add or remove subscriptions in a management group.
"""

helps['account management-group subscription add'] = """
type: command
short-summary: Add a subscription to a management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
  - name: --subscription -s
    type: string
    short-summary: Subscription ID or Name
examples:
  - name: Add a subscription to a management group.
    text: az account management-group subscription add --name MyGroupName --subscription Subscription
"""

helps['account management-group subscription remove'] = """
type: command
short-summary: Remove an existing subscription from a management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
  - name: --subscription -s
    type: string
    short-summary: Subscription ID or Name
examples:
  - name: Remove an existing subscription from a management group.
    text: az account management-group subscription remove --name MyGroupName --subscription Subscription
"""

helps['account management-group update'] = """
type: command
short-summary: Update an existing management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
  - name: --display-name -d
    type: string
    short-summary: Updates the display name of the management group. If null, no change is made.
  - name: --parent -p
    type: string
    short-summary: Updates the parent of the management group. Can be the fully qualified id or the name of the management group. If null, no change is made.
examples:
  - name: Update an existing management group with a specific display name.
    text: az account management-group update --name MyGroupName --display-name MyDisplayName
  - name: Update an existing management group with a specific parent.
    text: az account management-group update --name MyGroupName --parent ParentId/ParentName
  - name: Update an existing management group with a specific display name and parent.
    text: az account management-group update --name MyGroupName --display-name MyDisplayName --parent ParentId/ParentName
"""

helps['deployment'] = """
type: group
short-summary: Manage Azure Resource Manager template deployment at subscription scope.
"""

helps['deployment list'] = """
type: command
short-summary: List deployments at subscription scope.
examples:
  - name: List deployments at subscription scope.
    text: az deployment list
"""

helps['deployment show'] = """
type: command
short-summary: Show a deployment at subscription scope.
examples:
  - name: Show a deployment at subscription scope.
    text: az deployment show --name MyDeploymentName
"""

helps['deployment delete'] = """
type: command
short-summary: Delete a deployment at subscription scope.
examples:
  - name: Delete a deployment at subscription scope.
    text: az deployment delete --name MyDeploymentName
"""

helps['deployment cancel'] = """
type: command
short-summary: Cancel a deployment at subscription scope.
examples:
  - name: Cancel a deployment at subscription scope.
    text: az deployment cancel --name MyDeploymentName
"""

helps['deployment validate'] = """
type: command
short-summary: Validate whether a template is valid at subscription scope.
long-summary: >
    Specify only one of the following: `--template-file MyFileName`, `--template-uri` such as "https://mystorageaccount.blob.core.windows.net/AzureTemplates/newStorageAccount.json",
    or `--template-spec` to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
examples:
  - name: Validate whether a template is valid at subscription scope.
    text: az deployment validate --location westus2 --parameters MyValue=This MyArray=@array.json --template-file azuredeploy.json
"""

helps['deployment create'] = """
type: command
short-summary: Start a deployment at subscription scope.
long-summary: Specify only one of the following: `--template-file MyFileName`, `--template-uri` such as "https://mystorageaccount.blob.core.windows.net/AzureTemplates/newStorageAccount.json", \
    or `--template-spec` to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when `--confirm-with-what-if` is set.
examples:
  - name: Create a deployment at subscription scope from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment create --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at subscription scope from a local template file, using parameters from a JSON string.
    text: >
        az deployment create --location WestUS --template-file azuredeploy.json \\
            --parameters "{ \\"policyName\\": { \\"value\\": \\"policy2\\" }}"
  - name: Create a deployment at subscription scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment create --location WestUS --template-file azuredeploy.json \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
  - name: Create a deployment at subscription scope from a template-spec
    text: >
        az deployment create --location WestUS --template-spec "/subscriptions/MySubscriptionID/resourceGroups/myRG/providers/Microsoft.Resources/templateSpecs/myTemplateSpec/versions/1.0"
"""

helps['deployment export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at subscription scope.
    text: >
        az deployment export --name MyDeployment
"""

helps['deployment wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met.
    text: >
        az deployment wait --deleted --name MyDeployment --subscription MySubscription

"""

helps['deployment operation'] = """
type: group
short-summary: Manage deployment operations at subscription scope.
"""

helps['deployment operation list'] = """
type: command
short-summary: List deployment operations at subscription scope.
examples:
  - name: List deployment operations at subscription scope.
    text: >
        az deployment operation list --name MyDeployment
"""

helps['deployment operation show'] = """
type: command
short-summary: Show a deployment operation at subscription scope.
"""

helps['deployment sub'] = """
type: group
short-summary: Manage Azure Resource Manager template deployment at subscription scope.
"""

helps['deployment sub list'] = """
type: command
short-summary: List deployments at subscription scope.
examples:
  - name: List deployments at subscription scope.
    text: az deployment sub list
"""

helps['deployment sub show'] = """
type: command
short-summary: Show a deployment at subscription scope.
examples:
  - name: Show a deployment at subscription scope.
    text: az deployment sub show --name MyDeploymentName
"""

helps['deployment sub delete'] = """
type: command
short-summary: Delete a deployment at subscription scope.
examples:
  - name: Delete a deployment at subscription scope.
    text: az deployment sub delete --name MyDeploymentName
"""

helps['deployment sub cancel'] = """
type: command
short-summary: Cancel a deployment at subscription scope.
examples:
  - name: Cancel a deployment at subscription scope.
    text: az deployment sub cancel --name MyDeploymentName
"""

helps['deployment sub validate'] = """
type: command
short-summary: Validate whether a template is valid at subscription scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource ID.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
examples:
  - name: Validate whether a template is valid at subscription scope.
    text: az deployment sub validate --location westus2 --template-file {template-file}
  - name: Validate whether a template is valid at subscription scope.
    text: >
        az deployment sub validate --location westus2 --parameters MyValue=This MyArray=@array.json --template-file azuredeploy.json

"""

helps['deployment sub create'] = """
type: command
short-summary: Start a deployment at subscription scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when `--confirm-with-what-if` is set.
examples:
  - name: Create a deployment at subscription scope from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment sub create --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at subscription scope from a local template file, using parameters from a JSON string.
    text: >
        az deployment sub create --location WestUS --template-file azuredeploy.json \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at subscription scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment sub create --location WestUS --template-file azuredeploy.json \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""


helps['deployment sub what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at subscription scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --location -l
    short-summary: The location to store the deployment What-If operation metadata.
  - name: --name -n
    short-summary: The deployment name.
  - name: --result-format -r
    short-summary: The format of What-If results.
examples:
  - name: Execute a deployment What-If operation at a subscription.
    text: >
        az deployment sub what-if --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Execute a deployment What-If operation at a subscription with ResourceIdOnly format.
    text: >
        az deployment sub what-if --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --result-format ResourceIdOnly
  - name: Execute a deployment What-If operation at a subscription without pretty-printing the result.
    text: >
        az deployment sub what-if --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --no-pretty-print
"""

helps['deployment sub export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at subscription scope.
    text: az deployment sub export --name MyDeployment
"""

helps['deployment sub wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met.
    text: >
        az deployment sub wait --created --name MyDeployment
"""

helps['deployment operation sub'] = """
type: group
short-summary: Manage deployment operations at subscription scope.
"""

helps['deployment operation sub list'] = """
type: command
short-summary: List deployment operations at subscription scope.
examples:
  - name: List deployment operations at subscription scope.
    text: >
        az deployment operation sub list --name MyDeployment
"""

helps['deployment operation sub show'] = """
type: command
short-summary: Show a deployment operation at subscription scope.
"""

helps['deployment group'] = """
type: group
short-summary: Manage Azure Resource Manager template deployment at resource group.
"""

helps['deployment group list'] = """
type: command
short-summary: List deployments at resource group.
examples:
  - name: List deployments at resource group.
    text: az deployment group list --resource-group MyResourceGroup
"""

helps['deployment group show'] = """
type: command
short-summary: Show a deployment at resource group.
examples:
  - name: Show a deployment at resource group.
    text: az deployment group show --resource-group MyResourceGroup --name MyDeploymentName
"""

helps['deployment group delete'] = """
type: command
short-summary: Delete a deployment at resource group.
examples:
  - name: Delete a deployment at resource group.
    text: az deployment group delete --resource-group MyResourceGroup --name MyDeploymentName
"""

helps['deployment group cancel'] = """
type: command
short-summary: Cancel a deployment at resource group.
examples:
  - name: Cancel a deployment at resource group.
    text: az deployment group cancel --resource-group MyResourceGroup --name MyDeploymentName
"""

helps['deployment group validate'] = """
type: command
short-summary: Validate whether a template is valid at resource group.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --resource-group -g
    short-summary: The resource group to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --mode
    short-summary: The deployment mode.
examples:
  - name: Validate whether a template is valid at resource group.
    text: az deployment group validate --resource-group MyResourceGroup --template-file {template-file}
  - name: Validate whether a template is valid at resource group.
    text: >
        az deployment group validate --parameters MyValue=This MyArray=@array.json --resource-group MyResourceGroup --template-file azuredeploy.json
"""

helps['deployment group create'] = """
type: command
short-summary: Create a deployment group.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --resource-group -g
    short-summary: The resource group to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --mode
    short-summary: The deployment mode.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when `--confirm-with-what-if` is set.
examples:
  - name: Create a deployment at resource group from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment group create --resource-group MyResourceGroup --name rollout01 \\
            --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at resource group from a local template file, using parameters from a JSON string.
    text: >
        az deployment group create --resource-group MyResourceGroup --name rollout01 \\
            --template-file azuredeploy.json \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at resource group from a local template file, using parameters from an array string.
    text: >
      az deployment group create --resource-group MyResourceGroup --template-file demotemplate.json --parameters exampleString='inline string' exampleArray='("value1", "value2")'
  - name: Create a deployment at resource group from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment group create --resource-group MyResourceGroup --name rollout01 \\
            --template-file azuredeploy.json --parameters @params.json \\
            --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
  - name: Create a deployment at resource group scope from a template-spec
    text: >
        az deployment group create --resource-group MyResourceGroup --template-spec "/subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Resources/templateSpecs/myTemplateSpec/versions/1.0"
"""

helps['deployment group what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at resource group scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --resource-group -g
    short-summary: The resource group to execute deployment What-If operation at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --mode
    short-summary: The deployment mode.
  - name: --result-format -r
    short-summary: The format of What-If results.
examples:
  - name: Execute a deployment What-If operation at a resource group.
    text: >
        az deployment group what-if --resource-group MyResourceGroup --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Execute a deployment What-If operation at a resource group with ResourceIdOnly format.
    text: >
        az deployment group what-if --resource-group MyResourceGroup --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --result-format ResourceIdOnly
  - name: Execute a deployment What-If operation at a resource group without pretty-printing the result.
    text: >
        az deployment group what-if --resource-group MyResourceGroup --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --no-pretty-print
"""

helps['deployment group export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at resource group.
    text: az deployment group export --resource-group MyResourceGroup --name MyDeployment
"""

helps['deployment group wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met.
    text: >
        az deployment group wait --created --name MyDeployment --resource-group MyResourceGroup
"""

helps['deployment operation group'] = """
type: group
short-summary: Manage deployment operations of a resource group.
"""

helps['deployment operation group list'] = """
type: command
short-summary: List deployment operations at resource group.
examples:
  - name: List deployment operations at resource group
    text: >
        az deployment operation group list --name MyDeployment --resource-group MyResourceGroup
"""

helps['deployment operation group show'] = """
type: command
short-summary: Show a deployment operation of a resource group.
"""

helps['deployment mg'] = """
type: group
short-summary: Manage Azure Resource Manager template deployment of a management group.
"""

helps['deployment mg list'] = """
type: command
short-summary: List deployments of a management group.
examples:
  - name: List deployments of a management group.
    text: az deployment mg list --management-group-id MyGroupID
"""

helps['deployment mg show'] = """
type: command
short-summary: Show the deployment of a management group.
examples:
  - name: Show the deployment of a management group.
    text: az deployment mg show --management-group-id MyGroupID --name MyDeploymentName
"""

helps['deployment mg delete'] = """
type: command
short-summary: Delete the deployment of a management group.
examples:
  - name: Delete the deployment of a management group.
    text: az deployment mg delete --management-group-id MyManagementGroup --name MyDeploymentName
"""

helps['deployment mg cancel'] = """
type: command
short-summary: Cancel a deployment of a management group.
examples:
  - name: Cancel the deployment of a management group.
    text: az deployment mg cancel --management-group-id MyManagementGroup --name MyDeploymentName
"""

helps['deployment mg validate'] = """
type: command
short-summary: Validate whether a template is valid of a management group.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --management-group-id -m
    short-summary: The management group ID in which to create the deployment.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
examples:
  - name: Validate whether a template is valid of a management group.
    text: az deployment mg validate --management-group-id MyManagementGroup --location WestUS --template-file MyTemplateFile
  - name: Validate whether a template is valid of a management group for a specific deployment name and parameters.
    text: az deployment mg validate --management-group-id MyManagementGroup --location WestUS --name MyDeployment --parameters @myparameters.json --template-file azuredeploy.json
"""

helps['deployment mg what-if'] = """
type: command
short-summary: Execute a deployment What-If operation of a management group scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --management-group-id -m
    short-summary: The management group id to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --result-format -r
    short-summary: The format of What-If results.
examples:
  - name: Execute a deployment What-If operation of a management group.
    text: >
        az deployment mg what-if --management-group-id MyManagementGroup --location westus --name MyDeployment -template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Execute a deployment What-If operation of a management group with ResourceIdOnly format.
    text: >
        az deployment mg what-if --management-group-id MyManagementGroup --location westus --name MyDeployment --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --result-format ResourceIdOnly
  - name: Execute a deployment What-If operation of a management group without pretty-printing the result.
    text: >
        az deployment mg what-if --management-group-id MyManagementGroup --location westus --name MyDeployment --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --no-pretty-print
"""

helps['deployment mg create'] = """
type: command
short-summary: Start a deployment of a management group.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --management-group-id -m
    short-summary: The management group id to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when `--confirm-with-what-if` is set.
examples:
  - name: Create a deployment of a management group from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment mg create --management-group-id MyResourceGroup --name rollout01 --location WestUS \\
            --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment of a management group from a local template file, using parameters from a JSON string.
    text: >
        az deployment mg create --management-group-id MyManagementGroup --name rollout01 --location WestUS \\
            --template-file azuredeploy.json \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment of a management group from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment mg create --management-group-id MyManagementGroup --name rollout01 --location WestUS \\
            --template-file azuredeploy.json --parameters @params.json \\
            --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""

helps['deployment mg export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment of a management group.
    text: az deployment mg export --management-group-id MyManagementGroup --name MyDeployment
"""

helps['deployment mg wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
"""

helps['deployment operation mg'] = """
type: group
short-summary: Manage deployment operations of a management group.
"""

helps['deployment operation mg list'] = """
type: command
short-summary: List deployment operations of a management group.
"""

helps['deployment operation mg show'] = """
type: command
short-summary: Show a deployment operation of a management group.
"""

helps['deployment tenant'] = """
type: group
short-summary: Manage Azure Resource Manager template deployment at tenant scope.
"""

helps['deployment tenant list'] = """
type: command
short-summary: List deployments at tenant scope.
examples:
  - name: List deployments at tenant scope.
    text: az deployment tenant list
"""

helps['deployment tenant show'] = """
type: command
short-summary: Show a deployment at tenant scope.
examples:
  - name: Show a deployment at tenant scope.
    text: az deployment tenant show --name MyDeploymentName
"""

helps['deployment tenant delete'] = """
type: command
short-summary: Delete a deployment at tenant scope.
examples:
  - name: Delete a deployment at tenant scope.
    text: az deployment tenant delete --name MyDeploymentName
"""

helps['deployment tenant cancel'] = """
type: command
short-summary: Cancel a deployment at tenant scope.
examples:
  - name: Cancel a deployment at tenant scope.
    text: az deployment tenant cancel --name MyDeploymentName
"""

helps['deployment tenant validate'] = """
type: command
short-summary: Validate whether a template is valid at tenant scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
examples:
  - name: Validate whether a template is valid at tenant scope.
    text: az deployment tenant validate --location WestUS --template-file {template-file}
  - name: Validate whether a template is valid at tenant scope.
    text: az deployment tenant validate --location WestUS --name MyDeployment --parameters @myparameters.json --template-file azuredeploy.json
"""

helps['deployment tenant what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at tenant scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --location -l
    short-summary: The location to store the deployment What-If operation metadata.
  - name: --name -n
    short-summary: The deployment name.
  - name: --result-format -r
    short-summary: The format of What-If results.
examples:
  - name: Execute a deployment What-If operation at tenant scope.
    text: >
        az deployment tenant what-if --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Execute a deployment What-If operation at tenant scope with ResourceIdOnly format.
    text: >
        az deployment tenant what-if --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --result-format ResourceIdOnly
  - name: Execute a deployment What-If operation at tenant scope without pretty-printing the result.
    text: >
        az deployment tenant what-if --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --no-pretty-print
"""

helps['deployment tenant create'] = """
type: command
short-summary: Start a deployment at tenant scope.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file or Bicep file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --template-spec -s
    short-summary: The template spec resource id.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when `--confirm-with-what-if` is set.
examples:
  - name: Create a deployment at tenant scope from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment tenant create --name rollout01 --location WestUS \\
            --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at tenant scope from a local template file, using parameters from a JSON string.
    text: >
        az deployment tenant create --name rollout01 --location WestUS \\
            --template-file azuredeploy.json \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at tenant scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment tenant create --name rollout01 --location WestUS \\
            --template-file azuredeploy.json --parameters @params.json \\
            --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""

helps['deployment tenant export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at tenant scope.
    text: az deployment tenant export --name MyDeployment
"""

helps['deployment tenant wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met.
    text: >
        az deployment tenant wait --deleted --name MyDeployment
"""

helps['deployment operation tenant'] = """
type: group
short-summary: Manage deployment operations at tenant scope.
"""

helps['deployment operation tenant list'] = """
type: command
short-summary: List deployment operations at tenant scope.
"""

helps['deployment operation tenant show'] = """
type: command
short-summary: Show a deployment operation at tenant scope.
"""

helps['deployment-scripts'] = """
type: group
short-summary: Manage deployment scripts at subscription or resource group scope.
"""

helps['deployment-scripts list'] = """
type: command
short-summary: List all deployment scripts.
examples:
  - name: Retrieve all deployment scripts found in the user's logged-in default subscription.
    text: >
        az deployment-scripts list
  - name: Retrieve all deployment scripts found in a resource group.
    text: >
        az deployment-scripts list --resource-group MyResourceGroup
"""

helps['deployment-scripts show'] = """
type: command
short-summary: Retrieve a deployment script.
parameters:
  - name: --name
    short-summary: Deployment script resource name.
examples:
  - name: Retrieve a deployment script found in the user's logged-in default subscription.
    text: >
        az deployment-scripts show --resource-group MyResourceGroup --name MyBashScript
"""

helps['deployment-scripts show-log'] = """
type: command
short-summary: Show deployment script logs.
parameters:
  - name: --name
    short-summary: Deployment script resource name.
examples:
  - name: Retrieve deployment script logs found in the user's logged-in default subscription, max limit is 4MB.
    text: >
        az deployment-scripts show-log --resource-group MyResourceGroup --name MyBashScript
"""

helps['deployment-scripts delete'] = """
type: command
short-summary: Delete a deployment script.
parameters:
  - name: --name
    short-summary: Deployment script resource name.
examples:
  - name: Delete a deployment script found in the user's logged-in default subscription.
    text: >
        az deployment-scripts delete --resource-group MyResourceGroup --name MyBashScript
"""

helps['feature'] = """
type: group
short-summary: Manage resource provider features.
"""

helps['feature list'] = """
type: command
short-summary: List preview features.
examples:
  - name: List preview features.
    text: az feature list
"""

helps['feature register'] = """
type: command
short-summary: register a preview feature.
examples:
  - name: Register the "Shared Image Gallery" feature.
    text: az feature register --namespace Microsoft.Compute --name GalleryPreview
"""

helps['feature unregister'] = """
type: command
short-summary: Unregister a preview feature.
examples:
  - name: Unregister the "Shared Image Gallery" feature.
    text: az feature unregister --namespace Microsoft.Compute --name GalleryPreview
"""

helps['feature registration'] = """
type: group
short-summary: Manage resource provider feature registrations.
"""

helps['feature registration list'] = """
type: command
short-summary: List feature registrations.
examples:
  - name: List feature registrations.
    text: az feature registration list
"""

helps['feature registration create'] = """
type: command
short-summary: Create a feature registration.
examples:
  - name: Create the "Shared Image Gallery" feature.
    text: az feature registration create --namespace Microsoft.Compute --name GalleryPreview
"""

helps['feature registration delete'] = """
type: command
short-summary: Delete a feature registration.
examples:
  - name: Delete the "Shared Image Gallery" feature.
    text: az feature registration delete --namespace Microsoft.Compute --name GalleryPreview
"""

helps['group'] = """
type: group
short-summary: Manage Azure resource groups and template deployments.
"""

helps['group create'] = """
type: command
short-summary: Create a resource group.
examples:
  - name: Create a new resource group in the West US region.
    text: >
        az group create --location westus --name MyResourceGroup
  - name: >
      Create a new resource group from a variable using a random ID.
      Adding radom IDs to the resource group name will allow you to run a script repeatedly without having to wait for all resources in the prior group to be deleted.
    text: >
        # Bash script
        let "randomIdentifier=$RANDOM*$RANDOM"
        location="East US"
        resourceGroup="rg-$randomIdentifier"
        az group create --name $resourceGroup --location $location
   - name: >
      Create a resource group but only if it does not exist.
    text: >
        # Bash script
        resourceGroup="MyResourceGroup"
        location="eastus"
        if [ $(az group exists --name $resourceGroup --output json) = false ]; then 
          az group create --name $resourceGroup --location $location
        else
          echo A resource group named $resourceGroup already exists in this subscription.
        fi 
"""

helps['group delete'] = """
type: command
short-summary: Delete a resource group.
examples:
  - name: Delete a resource group.
    text: >
        az group delete --name MyResourceGroup
  - name: Force delete all the Virtual Machines in a resource group.
    text: >
        az group delete --name MyResourceGroup --force-deletion-types Microsoft.Compute/virtualMachines
   - name: >
      Delete a resource group but only if it exists. Bypass the confirmation prompt. Do not wait for the operation to finish.
    text: >
        resourceGroup=MyResourceGroup
        if [ $(az group exists --name $resourceGroup --output json) = true ]; then 
          az group delete --name $resourceGroup --yes --no-wait
        else
          echo Resource group $resourceGroup does not exist.
        fi 
"""

helps['group deployment'] = """
type: group
short-summary: Manage Azure Resource Manager (ARM) deployments.
"""

helps['group deployment create'] = """
type: command
short-summary: Start a deployment.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
examples:
  - name: Create a deployment from a remote template file, using parameters from a local JSON file.
    text: >
        az group deployment create --resource-group MyResourceGroup --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment from a local template file, using parameters from a JSON string.
    text: >
        az group deployment create --resource-group MyResourceGroup --template-file azuredeploy.json \\
            --parameters "{ \\"location\\": { \\"value\\": \\"westus\\" } }"
  - name: Create a deployment from a local template, using a local parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az group deployment create --resource-group MyResourceGroup --template-file azuredeploy.json \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""

helps['group deployment export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment.
    text: >
        az group deployment export --name MyDeployment --resource-group MyResourceGroup
"""

helps['group deployment operation'] = """
type: group
short-summary: Manage deployment operations.
"""

helps['group deployment validate'] = """
type: command
short-summary: Validate whether a template is syntactically correct.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
examples:
  - name: Validate whether a template is syntactically correct.
    text: >
        az group deployment validate --parameters "{ \\"location\\": { \\"value\\": \\"westus\\" } }" \\
            --resource-group MyResourceGroup --template-file storage.json
"""

helps['group deployment wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met.
    text: >
        az group deployment wait --name MyDeployment --resource-group MyResourceGroup --updated

  - name: Place the CLI in a waiting state until a deployment condition is met.
    text: >
        az group deployment wait --created --name MyDeployment --resource-group MyResourceGroup
"""

helps['group exists'] = """
type: command
short-summary: Check if a resource group exists.
examples:
  - name: Check if 'MyResourceGroup' exists.
    text: >
        az group exists --name MyResourceGroup
"""

helps['group list'] = """
type: command
short-summary: List resource groups.
examples:
  - name: List all resource groups for the current subscription returning results in a table
    text: >
        az group list --output table
  - name: List all resource groups located in the West US region.
    text: >
        az group list --query "[?location=='westus']"
"""

helps['group lock'] = """
type: group
short-summary: Manage Azure resource group locks.
long-summary: >
    To manage resource group locks you must have access to `Microsoft.Authorization/*` or `Microsoft.Authorization/locks/*` actions.  
    For information see [Management Locks - Create Or Update At Resource Group Level](https://learn.microsoft.com/rest/api/resources/management-locks/create-or-update-at-resource-group-level).
    To learn about locks for subscriptions or individual resources, see [az lock](https://learn.microsoft.com/cli/azure/lock)
"""

helps['group lock create'] = """
type: command
short-summary: Create a resource group lock. 
long-summary: Use locks to restrict updates or deletions of a resource group.
examples:
  - name: Create a read-only resource group level lock with notes.
    text: >
        az group lock create --lock-type ReadOnly --name MyLockName --resource-group MyResourceGroup --notes "My note that I want to remember."
  - name: Create a lock that prohibits deletion of the resource group.
    text: >
        az group lock create --lock-type CanNotDelete --name MyLockName --resource-group MyResourceGroup
"""

helps['group lock delete'] = """
type: command
short-summary: Delete a resource group lock.
examples:
  - name: Delete a resource group lock using the resource group name. The resource group name and lock name are both required if the `--ids` parameter is not used.
    text: >
        az group lock delete --name MyLockName --resource-group MyResourceGroup
  - name: Delete a one or more resource group locks using the lock Id. For a list of available lock Ids, run `az group lock list --resource-group MyResourceGroup -o json`.
    text: >
        az group lock delete --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Authorization/locks/MyLockName
"""

helps['group lock list'] = """
type: command
short-summary: List lock information in a resource-group.
long-summary: To list all locks for a subscription, regardless of resource group, use `az lock list`.
examples:
  - name: List all locks for a resource group.
    text: >
        az group lock list --resource-group MyResourceGroup
  - name: List all locks meeting a filter criteria. For more information on using the OData `$filter` query parameter, see [Use the $filter query parameter](https://learn.microsoft.com/graph/filter-query-parameter)
        az group lock list --filter-string "name eq 'MyLockName'"
  - name: List all locks meeting a `--query` criteria.
        az group lock list --resource-group MyResourceGroup --query "[?level=='ReadOnly']"
"""

helps['group lock show'] = """
type: command
short-summary: Show the details of a resource group lock.
examples:
  - name: Show the details of a resource group lock. The resource group name and lock name are both required if the `--ids` parameter is not used.
    text: >
        az group lock show --name MyLockName --resource-group MyResourceGroup
  - name: >
      Show the details of a many resource group locks using the Id.
      The `--resource-group` and `--name` parameters are not needed in this example as these values exist in the ID.
      For a list of available lock Ids, run `az group lock list --resource-group MyResourceGroup -o json`.
    text: >
        az group lock show --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Authorization/locks/MyLockName1 \\
            /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Authorization/locks/MyLockName2 
"""

helps['group lock update'] = """
type: command
short-summary: Update a resource group lock with new notes, or change the lock type.
examples:
  - name: Update a resource group lock with new notes and type
    text: >
        az group lock update --name MyLockName --resource-group MyResourceGroup --notes newNotesHere --lock-type CanNotDelete
  - name: Update a resource group lock using the Id.  For a list of available lock Ids, run `az group lock list --resource-group MyResourceGroup -o json`.
    text: >
        az group lock update --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Authorization/locks/MyLockName --notes MyNewNote
  - name: Update several resource group locks at the same time using a space delimited list of Ids.
    text: >
        az group lock update --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Authorization/locks/MyLockName1 \\
            /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Authorization/locks/MyLockName2 \\
            --notes MyNewNoteForAllIDs
"""

helps['group update'] = """
type: command
short-summary: Update a resource group.
examples:
  - name: Add tags to a resource group.
    text: >
        az group update --resource-group MyResourceGroup --set tags.Department1='{"Department name":"IT","Cost Center":"tech002"}'
        az group update --resource-group MyResourceGroup --set tags.Environment=DEV
  - name: Add tags to a resource group preserving string literals.
    text: >
        az group update --resource-group MyResourceGroup --set tags.Department1='{"Department name":"IT","Cost Center":"tech002"}' --force-string
  - name: Remove tags from a resource group.
    text: >
        az group update --resource-group MyResourceGroup --remove tags
"""

helps['group wait'] = """
type: command
short-summary: Place the Azure CLI in a waiting state until a condition of the resource group is met.
examples:
  - name: Place the Azure CLI in a waiting state until `provisioningState` becomes `succeeded`.
    text: >
        az group wait --created  --resource-group MyResourceGroup
  - name: Place the Azure CLI in a waiting state as a resource group is deleted.
    text: >
        az group wait --deleted --resource-group MyResourceGroup
"""

helps['lock'] = """
type: group
short-summary: Manage Azure locks.
long-summary: Locks can exist at three different scopes: subscription, resource group and resource. \
                For more information on managing Azure locks, \
                see [Management Locks](https://learn.microsoft.com/rest/api/resources/management-locks).
"""

helps['lock create'] = """
type: command
short-summary: Create a lock.
long-summary: Here are examples of how to create Azure locks at the subscription, resource group and resource levels.
examples:
  - name: Create a read-only subscription level lock.
    text: >
        az lock create --name MyLockName --lock-type ReadOnly
  - name: Create a read-only resource group level lock.
    text: >
        az lock create --name MyLockName --resource-group MyResourceGroup --lock-type ReadOnly
  - name: Create a read-only resource level lock on a VNet resource.
    text: >
        az lock create --name MyLockName --resource-group MyResourceGroup --lock-type ReadOnly \\
            --resource-type Microsoft.Network/virtualNetworks --resource MyVNet
  - name: Create a read-only resource level lock on a subnet resource with a specific parent.
    text: >
        az lock create --name MyLockName --resource-group MyResourceGroup --lock-type ReadOnly \\
            --resource-type Microsoft.Network/subnets --parent virtualNetworks/MyVNet --resource mySubnet
"""

helps['lock delete'] = """
type: command
short-summary: Delete a lock.
long-summary: Here are examples of how to delete Azure locks at the subscription, resource group and resource levels.
examples:
  - name: Delete a subscription level lock
    text: >
        az lock delete --name MyLockName
  - name: Delete a resource group level lock
    text: >
        az lock delete --name MyLockName --resource-group MyResourceGroup
  - name: Delete a resource level lock
    text: >
        az lock delete --name MyLockName --resource-group MyResourceGroup --resource resourceName --resource-type ResourceType
"""

helps['lock list'] = """
type: command
short-summary: List lock information.
examples:
  - name: List out all locks on the subscription level
    text: >
        az lock list
  - name: List out the locks on an Azure Virtual Network resource. Includes locks in the associated group and subscription.
    text: >
        az lock list --resource-name MyVNetName --resource-type Microsoft.Network/virtualNetworks --resource-group MyResourceGroup
"""

helps['lock show'] = """
type: command
short-summary: Show the properties of a lock
examples:
  - name: Show a subscription level lock
    text: >
        az lock show --name MyLockName
  - name: Show the properties of a lock
    text: >
        az lock show --name MyLockName --resource-group MyResourceGroup --resource-name MyResourceName --resource-type Microsoft.Network/virtualNetworks
"""

helps['lock update'] = """
type: command
short-summary: Update a lock.
examples:
  - name: Update a resource group level lock with new notes and type
    text: >
        az lock update --name MyLockName --resource-group MyResourceGroup --notes newNotesHere --lock-type CanNotDelete
"""

helps['managedapp'] = """
type: group
short-summary: Manage template solutions provided and maintained by Independent Software Vendors (ISVs).
"""

helps['managedapp create'] = """
type: command
short-summary: Create a managed application.
examples:
  - name: Create a managed application of kind 'ServiceCatalog'. This requires a valid managed application definition ID.
    text: >
        az managedapp create --resource-group MyResourceGroup --name MyManagedApp --location westcentralus --kind ServiceCatalog \\
            --managed-rg-id "/subscriptions/MySubscriptionID/resourceGroups/{ManagedResourceGroup}" \\
            --managedapp-definition-id "/subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Solutions/applianceDefinitions/{ApplianceDefinition}"
  - name: Create a managed application of kind 'MarketPlace'. This requires a valid plan, containing details about existing marketplace package like plan name, version, publisher and product.
    text: >
        az managedapp create --resource-group MyResourceGroup --name MyManagedApp --location westcentralus --kind MarketPlace \\
            --management-group-id "/subscriptions/MySubscriptionID/resourceGroups/{ManagedResourceGroup}" \\
            --plan-name MyAppliancePlan --plan-version "1.0" --plan-product "my-appliance" --plan-publisher MyPlanPublisher
"""

helps['managedapp definition'] = """
type: group
short-summary: Manage Azure Managed Applications.
"""

helps['managedapp definition create'] = """
type: command
short-summary: Create a managed application definition.
examples:
  - name: Create a managed application definition.
    text: >
        az managedapp definition create --resource-group MyResourceGroup --name MyManagedAppDef --location eastus --display-name "MyManagedAppDef" \\
            --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
            --package-file-uri "https://path/to/myPackage.zip"
  - name: Create a managed application definition with inline values for createUiDefinition and mainTemplate.
    text: >
        az managedapp definition create --resource-group MyResourceGroup --name MyManagedAppDef --location eastus --display-name "MyManagedAppDef" \\
            --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
            --create-ui-definition @myCreateUiDef.json --main-template @myMainTemplate.json
"""

helps['managedapp definition update'] = """
type: command
short-summary: Update a managed application definition.
examples:
  - name: Update a managed application definition.
    text: >
        az managedapp definition update --resource-group MyResourceGroup --name MyManagedAppDef --location eastus --display-name "MyManagedAppDef" \\
            --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
            --package-file-uri "https://path/to/myPackage.zip"
  - name: Update a managed application definition with inline values for createUiDefinition and mainTemplate.
    text: >
        az managedapp definition update --resource-group MyResourceGroup --name MyManagedAppDef --location eastus --display-name "MyManagedAppDef" \\
            --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
            --create-ui-definition @myCreateUiDef.json --main-template @myMainTemplate.json
"""

helps['managedapp definition delete'] = """
type: command
short-summary: Delete a managed application definition.
examples:
  - name: Delete a managed application definition.
    text: >
        az managedapp definition delete --name MyManagedApplicationDefinition --resource-group MyResourceGroup
"""

helps['managedapp definition list'] = """
type: command
short-summary: List managed application definitions.
examples:
  - name: List managed application definitions.
    text: >
        az managedapp definition list --resource-group MyResourceGroup
"""

helps['managedapp delete'] = """
type: command
short-summary: Delete a managed application.
examples:
  - name: Delete a managed application.
    text: >
        az managedapp delete --name MyManagedApplication --resource-group MyResourceGroup --subscription MySubscription
"""

helps['managedapp list'] = """
type: command
short-summary: List managed applications.
examples:
  - name: List managed applications.
    text: >
        az managedapp list --resource-group MyResourceGroup
"""

helps['policy'] = """
type: group
short-summary: Manage resource policies.
"""

helps['policy assignment'] = """
type: group
short-summary: Manage resource policy assignments.
"""

helps['policy assignment create'] = """
type: command
short-summary: Create a resource policy assignment.
parameters:
  - name: --scope
    type: string
    short-summary: Scope to which this policy assignment applies.
examples:
  - name: Create a resource policy assignment at scope
    text: >
        Valid scopes are management group, subscription, resource group, and resource, for example
           management group:  /providers/Microsoft.Management/managementGroups/MyManagementGroup
           subscription:      /subscriptions/MySubscriptionID
           resource group:    /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup
           resource:          /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/myVM
             az policy assignment create --scope \\
                "/providers/Microsoft.Management/managementGroups/MyManagementGroup" \\
                    --policy MyPolicyDefinition --params "{ \\"allowedLocations\\": \\
                        { \\"value\\": [ \\"australiaeast\\", \\"eastus\\", \\"japaneast\\" ] } }"
  - name: Create a resource policy assignment and provide rule parameter values.
    text: >
        az policy assignment create --policy MyPolicyDefinition --params "{ \\"allowedLocations\\": \\
            { \\"value\\": [ \\"australiaeast\\", \\"eastus\\", \\"japaneast\\" ] } }"
  - name: Create a resource policy assignment with a system assigned identity.
    text: >
        az policy assignment create --name MyPolicyName --policy MyPolicyDefinition --assign-identity
  - name: Create a resource policy assignment with a system assigned identity. The identity will have 'Contributor' role access to the subscription.
    text: >
        az policy assignment create --name MyPolicyName --policy MyPolicyDefinition --assign-identity --identity-scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --role Contributor
  - name: Create a resource policy assignment with an enforcement mode. It indicates whether a policy effect will be enforced or not during assignment creation and update. Please visit https://aka.ms/azure-policyAssignment-enforcement-mode for more information.
    text: >
        az policy assignment create --name MyPolicyName --policy MyPolicyDefinition--enforcement-mode 'DoNotEnforce'
"""

helps['policy assignment update'] = """
type: command
short-summary: Update a resource policy assignment.
examples:
  - name: Update a resource policy assignment's description.
    text: >
        az policy assignment update --name MyPolicyName --description 'My policy description'
"""

helps['policy assignment delete'] = """
type: command
short-summary: Delete a resource policy assignment.
examples:
  - name: Delete a resource policy assignment.
    text: >
        az policy assignment delete --name MyPolicyAssignment
"""

helps['policy assignment identity'] = """
type: group
short-summary: Manage a policy assignment's managed identity.
"""

helps['policy assignment identity assign'] = """
type: command
short-summary: Add a system assigned identity to a policy assignment.
examples:
  - name: Add a system assigned managed identity to a policy assignment.
    text: >
        az policy assignment identity assign --resource-group MyResourceGroup --name MyPolicyAssignment
  - name: Add a system assigned managed identity to a policy assignment and grant it the 'Contributor' role for the current resource group.
    text: >
        az policy assignment identity assign --resource-group MyResourceGroup --name MyPolicyAssignment --role Contributor --identity-scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/MyResourceGroup
"""

helps['policy assignment identity remove'] = """
type: command
short-summary: Remove a managed identity from a policy assignment.
"""

helps['policy assignment identity show'] = """
type: command
short-summary: Show a policy assignment's managed identity.
examples:
  - name: Show a policy assignment's managed identity.
    text: >
        az policy assignment identity show --name MyPolicyAssignment --scope '/providers/Microsoft.Management/managementGroups/MyManagementGroup'
"""

helps['policy assignment non-compliance-message'] = """
type: group
short-summary: Manage a policy assignment's non-compliance messages.
"""

helps['policy assignment non-compliance-message create'] = """
type: command
short-summary: Add a non-compliance message to a policy assignment.
examples:
- name: Add a non-compliance message to a policy assignment.
  text: >
      az policy assignment non-compliance-message create --resource-group MyResourceGroup --name MyPolicyAssignment --message 'Resources must follow naming standards'
- name: Add a non-compliance message for a specific policy in an assigned policy set definition.
  text: >
      az policy assignment non-compliance-message create --resource-group MyResourceGroup --name MyPolicySetAssignment --message 'Resources must use allowed SKUs' --policy-definition-reference-id SkuPolicyRefId
"""

helps['policy assignment non-compliance-message list'] = """
type: command
short-summary: List the non-compliance messages for a policy assignment.
examples:
- name: List the non-compliance messages for a policy assignment.
  text: >
      az policy assignment non-compliance-message list --resource-group MyResourceGroup --name MyPolicyAssignment
"""

helps['policy assignment non-compliance-message delete'] = """
type: command
short-summary: Remove one or more non-compliance messages from a policy assignment.
examples:
- name: Remove non-compliance messages from a policy assignment that contain a specific message and no policy definition reference ID.
  text: >
      az policy assignment non-compliance-message delete --resource-group MyResourceGroup --name MyPolicyAssignment --message 'Resources must follow naming standards'
- name: Remove non-compliance messages from a policy assignment that contain a specific message and a specific policy definition reference ID.
  text: >
      az policy assignment non-compliance-message delete --resource-group MyResourceGroup --name MyPolicySetAssignment --message 'Resources must use allowed SKUs' --policy-definition-reference-id SkuPolicyRefId
"""

helps['policy assignment list'] = """
type: command
short-summary: List resource policy assignments.
"""

helps['policy assignment show'] = """
type: command
short-summary: Show a resource policy assignment.
examples:
  - name: Show a resource policy assignment.
    text: >
        az policy assignment show --name MyPolicyAssignment
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
  - name: --management-group
    type: string
    short-summary: Name of the management group the new policy definition can be assigned in.
  - name: --subscription
    type: string
    short-summary: Name or id of the subscription the new policy definition can be assigned in.
examples:
- name: Create a read-only policy.
  text: >
      az policy definition create --name readOnlyStorage --rules "{ \\"if\\": \\
          { \\"field\\": \\"type\\", \\"equals\\": \\"Microsoft.Storage/storageAccounts/write\\" }, \\
              \\"then\\": { \\"effect\\": \\"deny\\" } }"
- name: Create a policy parameter definition.
  text: >
      az policy definition create --name allowedLocations \\
          --rules "{ \\"if\\": { \\"allOf\\": [ \\
              { \\"field\\": \\"location\\",\\"notIn\\": \\"[parameters('listOfAllowedLocations')]\\" }, \\
                  { \\"field\\": \\"location\\", \\"notEquals\\": \\"global\\" }, \\
                      { \\"field\\": \\"type\\", \\"notEquals\\": \\
                          \\"Microsoft.AzureActiveDirectory/b2cDirectories\\"} \\
                              ] }, \\"then\\": { \\"effect\\": \\"deny\\" } }" \\
          --params "{ \\"allowedLocations\\": { \\
              \\"type\\": \\"array\\", \\"metadata\\": { \\"description\\": \\
                  \\"The list of locations that can be specified when deploying resources\\", \\
                      \\"strongType\\": \\"location\\", \\"displayName\\": \\"Allowed locations\\" } } }"
- name: Create a read-only policy that can be applied within a management group.
  text: >
      az policy definition create --name readOnlyStorage --management-group "MyManagementGroup" \\
          --rules "{ \\"if\\": { \\"field\\": \\"type\\", \\
              \\"equals\\": \\"Microsoft.Storage/storageAccounts/write\\" }, \\
                  \\"then\\": { \\"effect\\": \\"deny\\" } }"
- name: Create a policy definition with mode. The mode 'Indexed' indicates the policy should be evaluated only for resource types that support tags and location.
  text: >
      az policy definition create --name TagsPolicyDefinition --subscription "MySubscription" \\
          --mode Indexed --rules "{ \\"if\\": { \\"field\\": \\"tags\\", \\"exists\\": \\"false\\" }, \\
              \\"then\\": { \\"effect\\": \\"deny\\" } }"
"""

helps['policy definition delete'] = """
type: command
short-summary: Delete a policy definition.
examples:
  - name: Delete a policy definition.
    text: >
        az policy definition delete --name MyPolicyDefinition
"""

helps['policy definition list'] = """
type: command
short-summary: List policy definitions.
"""

helps['policy definition show'] = """
type: command
short-summary: Show a policy definition.
examples:
  - name: Show a policy definition.
    text: >
        az policy definition show --name MyPolicyDefinition
"""

helps['policy definition update'] = """
type: command
short-summary: Update a policy definition.
examples:
  - name: Update a policy definition.
    text: >
        az policy definition update --name MyPolicyDefinition
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
    short-summary: Policy definitions in JSON format, or a path to a file or URI containing JSON rules.
  - name: --management-group
    type: string
    short-summary: Name of management group the new policy set definition can be assigned in.
  - name: --subscription
    type: string
    short-summary: Name or id of the subscription the new policy set definition can be assigned in.
examples:
  - name: Create a policy set definition.
    text: >
        az policy set-definition create --name readOnlyStorage \\
            --definitions "[ { \\"policyDefinitionId\\": \\"/subscriptions/MySubscriptionID/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\", \\"parameters\\": \\
                    { \\"storageSku\\": { \\"value\\": \\"[parameters(\\\\"requiredSku\\\\")]\\" } } }]" \\
            --params "{ \\"requiredSku\\": { \\"type\\": \\"String\\" } }"
  - name: Create a policy set definition with parameters.
    text: >
        az policy set-definition create --name readOnlyStorage \\
            --definitions '[ { \\"policyDefinitionId\\": \\"/subscriptions/MySubscriptionID/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\" } ]'
  - name: Create a policy set definition in a subscription.
    text: >
        az policy set-definition create --name readOnlyStorage \\
            --subscription '0b1f6471-1bf0-4dda-aec3-111122223333' \\
            --definitions '[ { \\"policyDefinitionId\\": \\"/subscriptions/ \\
                0b1f6471-1bf0-4dda-aec3-111122223333/providers/Microsoft.Authorization/ \\
                    policyDefinitions/storagePolicy\\" } ]'
  - name: Create a policy set definition with policy definition groups.
    text: >
        az policy set-definition create --name computeRequirements \\
            --definitions "[ { \\"policyDefinitionId \\": \\"/subscriptions/MySubscriptionID/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\", \\"groupNames\\": \\
                    [ \\"CostSaving\\", \\"Organizational\\" ] }, { \\"policyDefinitionId\\": \\
                        \\"/subscriptions/MySubscriptionID/providers/Microsoft.Authorization/ \\
                            policyDefinitions/tagPolicy\\", \\"groupNames\\": [ \\
                                \\"Organizational\\" ] } ]" \\
            --definition-groups "[{ \\"name\\": \\"CostSaving\\" }, { \\"name\\": \\"Organizational\\" } ]"
"""

helps['policy set-definition delete'] = """
type: command
short-summary: Delete a policy set definition.
examples:
  - name: Delete a policy set definition.
    text: >
        az policy set-definition delete --management-group MyManagementGroup --name MyPolicySetDefinition
"""

helps['policy set-definition list'] = """
type: command
short-summary: List policy set definitions.
"""

helps['policy set-definition show'] = """
type: command
short-summary: Show a policy set definition.
examples:
  - name: Show a policy set definition. If the policy set is scoped to a management group, then you must include the `--management-group` parameter and value.
    text: >
        az policy set-definition show --name MyPolicySetDefinition --management-group MyManagementGroup
"""

helps['policy set-definition update'] = """
type: command
short-summary: Update a policy set definition.
examples:
  - name: Update a policy set definition.
    text: >-
        az policy set-definition update \\
            --definitions '[ { \\"policyDefinitionId\\": \\"/subscriptions/MySubscriptionID/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\" } ]' \\
            --name MyPolicySetDefinition
  - name: Update the groups and definitions within a policy set definition.
    text: >
        az policy set-definition update --name computeRequirements \\
            --definitions "[ { \\"policyDefinitionId\\": \\"/subscriptions/MySubscriptionID/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\", \\"groupNames\\": [ \\
                    \\"CostSaving\\", \\"Organizational\\" ] }, { \\"policyDefinitionId\\": \\
                        \\"/subscriptions/MySubscriptionID/providers/Microsoft.Authorization/ \\
                            policyDefinitions/tagPolicy\\", \\
                                \\"groupNames\\": [ \\"Organizational\\" ] } ]" \\
            --definition-groups "[{ \\"name\\": \\"CostSaving\\" }, { \\"name\\": \\"Organizational\\" } ]"
"""

helps['policy exemption'] = """
type: group
short-summary: Manage resource policy exemptions.
"""

helps['policy exemption create'] = """
type: command
short-summary: Create a policy exemption.
examples:
  - name: Create a policy exemption in default subscription.
    text: >
        az policy exemption create --name MyExemptVM \\
            --policy-assignment "/subscriptions/MySubscriptionID/providers/Microsoft.Authorization/policyAssignments/limitVMSku" \\
            --exemption-category "Waiver"
  - name: Create a policy exemption in the resource group.
    text: >
        az policy exemption create --name MyExemptVM \\
            --policy-assignment "/subscriptions/MySubscriptionID/providers/Microsoft.Authorization/policyAssignments/limitVMSku" \\
            --exemption-category "Waiver" \\
            --resource-group "MyResourceGroup"
  - name: Create a policy exemption in a management group.
    text: >
        az policy exemption create --name MyExemptVM \\
            --policy-assignment "/providers/Microsoft.Management/managementGroups/MyManagementGroup/providers/Microsoft.Authorization/policyAssignments/limitVMSku" \\
            --exemption-category "Waiver" \\
            --scope "/providers/Microsoft.Management/managementGroups/MyManagementGroup"
"""

helps['policy exemption delete'] = """
type: command
short-summary: Delete a policy exemption.
examples:
  - name: Delete a policy exemption.
    text: >
        az policy exemption delete --name MyPolicyExemption --resource-group "MyResourceGroup"
"""

helps['policy exemption list'] = """
type: command
short-summary: List policy exemptions.
"""

helps['policy exemption show'] = """
type: command
short-summary: Show a policy exemption.
examples:
  - name: Show a policy exemption.
    text: >
        az policy exemption show --name MyPolicyExemption --resource-group "MyResourceGroup"
"""

helps['policy exemption update'] = """
type: command
short-summary: Update a policy exemption.
examples:
  - name: Update a policy exemption.
    text: >
        az policy exemption update --name MyExemptVM \\
            --exemption-category "Mitigated"
  - name: Update a policy exemption in the resource group.
    text: >
        az policy exemption update --name MyExemptVM \\
            --exemption-category "Mitigated" \\
            --resource-group "MyResourceGroup"
  - name: Update a policy exemption in a management group.
    text: >
        az policy exemption update --name MyExemptVM \\
            --exemption-category "Mitigated" \\
            --scope "/providers/Microsoft.Management/managementGroups/MyManagementGroup"
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

helps['provider permission'] = """
type: group
short-summary: Manage permissions for a provider.
"""

helps['provider permission list'] = """
type: command
short-summary: List permissions from a provider.
"""

helps['provider operation'] = """
type: group
short-summary: Get provider operations metadatas.
"""

helps['provider operation list'] = """
type: command
short-summary: Get operations from all providers.
"""

helps['provider operation show'] = """
type: command
short-summary: Get an individual provider's operations.
examples:
  - name: Get an individual provider's operations.
    text: >
        az provider operation show --namespace Microsoft.Storage
"""

helps['provider register'] = """
type: command
short-summary: Register a provider.
examples:
  - name: Register a provider.
    text: >
        az provider register --namespace 'Microsoft.PolicyInsights'

  - name: Register a provider from RPaaS.
    text: >
        az provider register --name 'Microsoft.Confluent' --accept-terms
  - name: Register a management group.
    text: >
        az provider register --namespace Microsoft.Automation --management-group-id mgID
"""

helps['provider unregister'] = """
type: command
short-summary: Unregister a provider.
examples:
  - name: Unregister a provider.
    text: >
        az provider unregister --namespace Microsoft.Automation
"""

helps['resource'] = """
type: group
short-summary: Manage Azure resources.
"""

helps['resource create'] = """
type: command
short-summary: Create a resource.
examples:
  - name: Create an API app by providing a full JSON configuration.
    text: >
        az resource create --resource-group myRG --name myApiApp --resource-type Microsoft.web/sites \\
            --is-full-object --properties "{ \\"kind\\": \\"api\\", \\"location\\": \\
                \\"West US\\", \\"properties\\": { \\"serverFarmId\\": \\
                    \\"/subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup \\
                        /providers/Microsoft.Web/serverfarms/MyServicePlan\\" } }"
  - name: Create a resource by loading JSON configuration from a file.
    text: >
        az resource create --resource-group myRG --name myApiApp --resource-type Microsoft.web/sites --is-full-object --properties @jsonConfigFile
  - name: Create a web app with the minimum required configuration information.
    text: >
        az resource create --resource-group myRG --name myWeb --resource-type Microsoft.web/sites \\
            --properties "{ \\"serverFarmId\\":\\"/subscriptions/MySubscriptionID/resourcegroups/ \\
                MyResourceGroup/providers/Microsoft.Web/serverfarms/MyServicePlan\\" }"
  - name: Create a resource by using the latest api-version whether this version is a preview version.
    text: >
        az resource create --resource-group myRG --name myApiApp --resource-type Microsoft.web/sites --is-full-object --properties @jsonConfigFile --latest-include-preview
  - name: Create a site extension to a web app
    text: >
        az resource create --resource-group myRG --api-version "2018-02-01" \\
            --name "{sitename+slot}/siteextensions/Contrast.NetCore.Azure.SiteExtension" \\
                --resource-type Microsoft.Web/sites/siteextensions --is-full-object \\
                    --properties "{ \\"id\\": \\"Contrast.NetCore.Azure.SiteExtension\\", \\
                        \\"location\\": \\"West US\\", \\"version\\": \\"1.9.0\\" }"
"""

helps['resource delete'] = """
type: command
short-summary: Delete a resource.
examples:
  - name: Delete a virtual machine named 'MyVm'.
    text: >
        az resource delete --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines"
  - name: Delete a web app using a resource identifier.
    text: >
        az resource delete --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebapp
  - name: Delete a subnet using a resource identifier.
    text: >
        az resource delete --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVNet/subnets/MySubnet
  - name: Delete a virtual machine named 'MyVm' by using the latest api-version whether this version is a preview version.
    text: >
        az resource delete --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines" --latest-include-preview
"""

helps['resource invoke-action'] = """
type: command
short-summary: Invoke an action on the resource.
long-summary: >
    A list of possible actions corresponding to a resource can be found at https://docs.microsoft.com/rest/api/. All POST requests are actions that can be invoked and are specified at the end of the URI path. For instance, to stop a VM, the
    request URI is https://management.azure.com/subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/MyVMName/powerOff?api-version={APIVersion} and the corresponding action is `powerOff`. This can
    be found at https://docs.microsoft.com/rest/api/compute/virtualmachines/virtualmachines-stop.
examples:
  - name: Power-off a vm, specified by Id.
    text: >
        az resource invoke-action --action powerOff \\
          --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/MyVMName
  - name: Capture information for a stopped vm.
    text: >
        az resource invoke-action --action capture \\
          --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/ \\
            Microsoft.Compute/virtualMachines/MyVMName \\
          --request-body "{ \\"vhdPrefix\\": \\"myPrefix\\", \\"destinationContainerName\\": \\
            \\"myContainer\\", \\"overwriteVhds\\": true }"
  - name: Invoke an action on the resource.
    text: >
        az resource invoke-action --action capture --name MyResource --resource-group MyResourceGroup --resource-type Microsoft.web/sites
"""

helps['resource link'] = """
type: group
short-summary: Manage links between resources.
long-summary: >
    Linking is a feature of the Resource Manager. It enables declaring relationships between resources even if they do not reside in the same resource group.
    Linking has no impact on resource usage, billing, or role-based access. It allows for managing multiple resources across groups as a single unit.
"""

helps['resource link create'] = """
type: command
short-summary: Create a new link between resources.
parameters:
  - name: --link
    long-summary: >
        Format: /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
examples:
  - name: Create a link from MySourceId to MyResourceId with notes
    text: >
        az resource link create --link MySourceId --target MyResourceId --notes "SourceID depends on ResourceID"
"""

helps['resource link delete'] = """
type: command
short-summary: Delete a link between resources.
parameters:
  - name: --link
    long-summary: >
        Format: /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
examples:
  - name: Delete link MyLinkId
    text: >
        az resource link delete --link MyLinkId
"""

helps['resource link list'] = """
type: command
short-summary: List resource links.
examples:
  - name: List links, filtering with {filter-string}
    text: >
        az resource link list --filter {filter-string}
  - name: List all links for resource group MyResourceGroup in subscription MySubscriptionID
    text: >
        az resource link list --scope /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup
"""

helps['resource link update'] = """
type: command
short-summary: Update a link between resources.
parameters:
  - name: --link
    long-summary: >
        Format: /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
examples:
  - name: Update the notes for MyLinkId notes "some notes to explain this link"
    text: >
        az resource link update --link MyLinkId --notes "some notes to explain this link"
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
  - name: List all resources with the tag 'MyTagName'.
    text: >
        az resource list --tag MyTagName
  - name: List all resources with a tag that starts with 'MyTagName'.
    text: >
        az resource list --tag 'MyTagName*'
  - name: List all resources with the tag 'MyTagName' that have the value 'example'.
    text: >
        az resource list --tag MyTagName=example
"""

helps['resource lock'] = """
type: group
short-summary: Manage Azure resource level locks.
"""

helps['resource lock create'] = """
type: command
short-summary: Create a resource-level lock.
examples:
  - name: Create a read-only resource level lock on a VNet.
    text: >
        az resource lock create --lock-type ReadOnly --name MyLockName --resource-group MyResourceGroup --resource MyVNet --resource-type Microsoft.Network/virtualNetworks
  - name: Create a read-only resource level lock on a VNet using a VNet id.
    text: >
        az resource lock create --lock-type ReadOnly --name MyLockName --resource /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/VNetName
"""

helps['resource lock delete'] = """
type: command
short-summary: Delete a resource-level lock.
examples:
  - name: Delete a resource level lock
    text: >
        az resource lock delete --name MyLockName --resource-group MyResourceGroup --resource MyVNet --resource-type Microsoft.Network/virtualNetworks
  - name: Delete a resource level lock on a VNet using a VNet id.
    text: >
        az resource lock delete --name MyLockName --resource /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVMName
  - name: Delete a resource-level lock.
    text: >
        az resource lock delete --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebApp
"""

helps['resource lock list'] = """
type: command
short-summary: List lock information at the resource-level.
examples:
  - name: List out all locks on a VNet
    text: >
        az resource lock list --resource-group MyResourceGroup --resource MyVNet --resource-type Microsoft.Network/virtualNetworks
"""

helps['resource lock show'] = """
type: command
short-summary: Show the details of a resource-level lock
examples:
  - name: Show a resource level lock
    text: >
        az resource lock show --name MyLockName --resource-group MyResourceGroup --resource MyVNet --resource-type Microsoft.Network/virtualNetworks
"""

helps['resource lock update'] = """
type: command
short-summary: Update a resource-level lock.
examples:
  - name: Update a resource level lock with new notes and type
    text: >
        az resource lock update --name MyLockName --resource-group MyResourceGroup --resource MyVNet --resource-type Microsoft.Network/virtualNetworks --notes newNotesHere --lock-type CanNotDelete
  - name: Update a resource-level lock.
    text: >
        az resource lock update --lock-type CanNotDelete --name MyLockName --namespace Microsoft.Network --resource-group MyResourceGroup --resource-name MyVNet --resource-type Microsoft.Network/virtualNetworks
"""

helps['resource show'] = """
type: command
short-summary: Get the details of a resource.
examples:
  - name: Show a virtual machine resource named 'MyVm'.
    text: >
        az resource show --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines"
  - name: Show a web app using a resource identifier.
    text: >
        az resource show --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebapp
  - name: Show a subnet.
    text: >
        az resource show --resource-group MyResourceGroup --name MySubnet --namespace Microsoft.Network --parent virtualnetworks/MyVNet --resource-type subnets
  - name: Show a subnet using a resource identifier.
    text: >
        az resource show --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVNet/subnets/MySubnet
  - name: Show an application gateway path rule.
    text: >
        az resource show --resource-group MyResourceGroup --namespace Microsoft.Network --parent applicationGateways/ag1/urlPathMaps/map1 --resource-type pathRules --name rule1
  - name: Show a virtual machine resource named 'MyVm' by using the latest api-version whether this version is a preview version.
    text: >
        az resource show --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines" --latest-include-preview
"""

helps['resource tag'] = """
type: command
short-summary: Tag a resource.
examples:
  - name: Tag the virtual machine 'MyVm' with the key 'vmlist' and value 'vm1'.
    text: >
        az resource tag --tags vmlist=vm1 --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines"
  - name: Tag a web app with the key 'vmlist' and value 'vm1', using a resource identifier.
    text: >
        az resource tag --tags vmlist=vm1 --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebApp
  - name: Tag the virtual machine 'MyVm' with the key 'vmlist' and value 'vm1' incrementally. It doesn't empty the existing tags.
    text: >
        az resource tag --tags vmlist=vm1 --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines" -i
  - name: Tag the virtual machine 'MyVm' with the key 'vmlist' and value 'vm1' by using the latest api-version whether this version is a preview version.
    text: >
        az resource tag --tags vmlist=vm1 --resource-group MyResourceGroup --name MyVm --resource-type "Microsoft.Compute/virtualMachines" --latest-include-preview
"""

helps['resource update'] = """
type: command
short-summary: Update a resource.
examples:
  - name: Update a webapp by using the latest api-version whether this version is a preview version.
    text: >
        az resource update --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebApp --set tags.key=value --latest-include-preview
  - name: Update a resource.
    text: >
        az resource update --ids $id --set properties.connectionType=Proxy

  - name: Update a resource.
    text: >
        az resource update --name MyResource --resource-group MyResourceGroup --resource-type subnets --set tags.key=value
"""

helps['resource wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a resources is met.
examples:
  - name: Place the CLI in a waiting state until a condition of a resources is met.
    text: >
        az resource wait --exists --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebApp

  - name: Place the CLI in a waiting state until a condition of a resources is met.
    text: >
        az resource wait --exists --ids /subscriptions/MySubscriptionID/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebApp --include-response-body true

  - name: Place the CLI in a waiting state until a condition of a resources is met.
    text: >
        az resource wait --exists --name MyResource --resource-group MyResourceGroup --resource-type subnets
"""

helps['tag'] = """
type: group
short-summary: Manage the tags of a resource.
"""

helps['tag add-value'] = """
type: command
short-summary: Create a tag value.
parameters:
  - name: --name -n
    short-summary: The name of the tag to create.
  - name: --subscription
    short-summary: Name or ID of subscription. You can configure the default subscription using `az account set` --subscription MySubscriptionNameOrID.
  - name: --resource-id
    short-summary: The resource identifier for the entity being tagged. A resource, a resource group or a subscription may be tagged.
  - name: --tags
    short-summary: The tags to be applied on the resource.
examples:
  - name: Create a tag value.
    text: >
        az tag add-value --name MyTag --value MyValue
"""

helps['tag create'] = """
type: command
short-summary: Create tags on a specific resource.
long-summary: >
    The az tag create command with an id creates or updates the entire set of tags on a resource, resource group or subscription.
    This operation allows adding or replacing the entire set of tags on the specified resource, resource group or subscription.
    The specified entity can have a maximum of 50 tags.
    Please note: 'tag create' acts like a 'tag init' hence tags created with this command are the only ones being present after execution.
examples:
  - name: Create a tag in the subscription.
    text: >
        az tag create --name MyTag
  - name: Create or update the entire set of tags on a subscription.
    text: >
        az tag create --resource-id /subscriptions/MySubscriptionID --tags Dept=Finance Status=Normal
  - name: Create or update the entire set of tags on a resource group.
    text: >
        az tag create --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup --tags Dept=Finance Status=Normal
  - name: Create or update the entire set of tags on a resource.
    text: >
        az tag create --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/MyVMName --tags Dept=Finance Status=Normal
"""

helps['tag delete'] = """
type: command
short-summary: Delete tags on a specific resource.
long-summary:
    The az tag delete command with an id deletes the entire set of tags on a resource, resource group or subscription.
parameters:
  - name: --name -n
    short-summary: The name of the tag to be deleted.
  - name: --resource-id
    short-summary: The resource identifier for the entity being tagged. A resource, a resource group or a subscription may be tagged.
examples:
  - name: Delete a tag from the subscription.
    text: >
        az tag delete --name MyTag
  - name: Delete the entire set of tags on a subscription.
    text: >
        az tag delete --resource-id /subscriptions/MySubscriptionID
  - name: Delete the entire set of tags on a resource group.
    text: >
        az tag delete --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup
  - name: Delete the entire set of tags on a resource.
    text: >
        az tag delete --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/MyVMName
"""

helps['tag list'] = """
type: command
short-summary: List the entire set of tags on a specific resource.
long-summary: The az tag list command with an id lists the entire set of tags on a resource, resource group or subscription.
parameters:
  - name: --resource-id
    short-summary: The resource identifier for the entity being tagged. A resource, a resource group or a subscription may be tagged.
examples:
  - name: List the entire set of tags on a subscription.
    text: >
        az tag list --resource-id /subscriptions/MySubscriptionID
  - name: List the entire set of tags on a resource group.
    text: >
        az tag list --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup
  - name: List the entire set of tags on a resource.
    text: >
        az tag list --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/MyVMName
"""

helps['tag update'] = """
type: command
short-summary: Selectively update the set of tags on a specific resource.
long-summary: >
    The az tag update command with an id selectively updates the set of tags on a resource, resource group or subscription.
    This operation allows replacing, merging or selectively deleting tags on the specified resource, resource group or subscription.
    The specified entity can have a maximum of 50 tags at the end of the operation.
    The 'replace' option replaces the entire set of existing tags with a new set.
    The 'merge' option allows adding tags with new names and updating the values of tags with existing names.
    The 'delete' option allows selectively deleting tags based on given names or name/value pairs.
parameters:
  - name: --resource-id
    short-summary: The resource identifier for the entity being tagged. A resource, a resource group or a subscription may be tagged.
  - name: --operation
    short-summary: The update operation. Options are Merge, Replace and Delete.
  - name: --tags
    short-summary: The tags to be updated on the resource.
examples:
  - name: Selectively update the set of tags on a subscription with "merge" Operation.
    text: >
        az tag update --resource-id /subscriptions/MySubscriptionID --operation merge --tags key1=value1 key3=value3
  - name: Selectively update the set of tags on a resource group with "replace" Operation.
    text: >
        az tag update --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup --operation replace --tags key1=value1 key3=value3
  - name: Selectively update the set of tags on a resource with "delete" Operation.
    text: >
        az tag update --resource-id /subscriptions/MySubscriptionID/resourcegroups/MyResourceGroup/providers/Microsoft.Compute/virtualMachines/MyVMName --operation delete --tags key1=value1
"""

helps['ts'] = """
type: group
short-summary: Manage template specs at subscription or resource group scope.
"""

helps['ts create'] = """
type: command
short-summary: Create a template spec and or template spec version.
examples:
  - name: Create a template spec.
    text: az ts create --resource-group MyResourceGroup --name TemplateSpecName --location WestUS --display-name "MyDisplayName" --description "Simple template spec" --tags key1=value1
  - name: Create a template spec version.
    text: az ts create --resource-group MyResourceGroup --name TemplateSpecName -v 2.0 --location WestUS --template-file templateSpec.json --version-description "Less simple template spec" --tags key1=value1 key3=value3
  - name: Create a template spec and a version of the template spec.
    text: az ts create --resource-group MyResourceGroup --name TemplateSpecName -v 1.0 --location WestUS --template-file templateSpec.json --display-name "MyDisplayName" --description "Simple template spec" --version-description "Version of simple template spec" --tags key1=value1 key2=value2
"""

helps['ts update'] = """
type: command
short-summary: Update a template spec version.
examples:
  - name: Update the template content of a template spec or template spec version based on the resource ID.
    text: az ts update --template-spec resourceID -f updatedFile.json
  - name: Update the display name and tag(s) of a template spec based on the resource ID.
    text: az ts update --template-spec resourceID --display-name "NewParentDisplayName" --tags key1=value1
  - name: Update the description of a template spec version with no prompt.
    text: az ts update --resource-group ExistingRG --name ExistingName -v 3.0 --version-description "New description" --yes
  - name: Update all the properties of a template spec version.
    text: az ts update --resource-group ExistingRG --name ExistingName -v 3.0 -f updatedTemplate.json --display-name "New parent display name" --description "New parent description" --version-description "New child description" --ui-form-definition formDefinition.json
  - name: Remove tag(s) from template spec version with no prompt.
    text: az ts update --resource-group ExistingRG --name ExistingName -v 3.0 -f updatedTemplate.json --tags --yes
"""

helps['ts show'] = """
type: command
short-summary: Get the specified template spec or template spec version.
examples:
  - name: Show the specified template spec.
    text: az ts show --resource-group MyResourceGroup --name TemplateSpecName
  - name: Show the specified template spec version.
    text: az ts show --resource-group MyResourceGroup --name TemplateSpecName --version VersionName
  - name: Show the specified template spec or template spec version based on the resource ID.
    text: az ts show --template-spec resourceID
"""

helps['ts export'] = """
type: command
short-summary: Export the specified template spec version and artifacts (if any) to the specified output folder.
examples:
  - name: Export the specified template spec version based on resource ID.
    text: az ts export --template-spec MyTemplateSpecResourceID --output-folder C:/path/
  - name: Export the specified template spec version.
    text: az ts export --resource-group MyResourceGroup --name TemplateSpecName --version VersionName --output-folder C:/path/
"""

helps['ts delete'] = """
type: command
short-summary: Delete a specified template spec or template spec version by name or resource ID..
examples:
  - name: Delete the specified template spec and all versions.
    text: az ts delete --resource-group MyResourceGroup --name TemplateSpecName
  - name: Delete the specified version from the template spec.
    text: az ts delete --resource-group MyResourceGroup --name TemplateSpecName --version VersionName
  - name: Delete the template spec or version based on resource ID.
    text: az ts delete --template-spec resourceID
"""

helps['ts list'] = """
type: command
short-summary: List template specs or template spec versions.
examples:
  - name: List all template specs in current default subscription.
    text: az ts list
  - name: List all template specs in specified subscription.
    text: az ts list --subscription Subscription
  - name: List all template specs in resource group.
    text: az ts list --resource-group MyResourceGroup
  - name: List all versions of parent template spec.
    text: az ts list --resource-group MyResourceGroup --name TemplateSpecName
"""

helps['bicep'] = """
type: group
short-summary: Deploy Azure resources using Bicep.
"""

helps['bicep install'] = """
type: command
short-summary: Install Bicep CLI.
examples:
  - name: Install Bicep CLI.
    text: az bicep install
  - name: Install a specific version of Bicep CLI.
    text: az bicep install --version v0.2.212
"""

helps['bicep uninstall'] = """
type: command
short-summary: Uninstall Bicep CLI.
"""

helps['bicep upgrade'] = """
type: command
short-summary: Upgrade Bicep CLI to the latest version.
"""

helps['bicep build'] = """
type: command
short-summary: Build a Bicep file.
examples:
  - name: Build a Bicep file.
    text: az bicep build --file MyFileName.bicep
  - name: Build a Bicep file and print all output to stdout.
    text: az bicep build --file MyFileName.bicep --stdout
  - name: Build a Bicep file and save the result to the specified directory.
    text: az bicep build --file MyFileName.bicep --outdir c:\MyOutputFolderName
  - name: Build a Bicep file and save the result to the specified file.
    text: az bicep build --file MyFileName.bicep --outfile c:\MyOutputFolderName\MyOutputFileName.json
  - name: Build a Bicep file without restoring external modules.
    text: az bicep build --file MyFileName.bicep --no-restore
"""

helps['bicep decompile'] = """
type: command
short-summary: Attempt to decompile an ARM template file to a Bicep file.
examples:
  - name: Decompile an ARM template file.
    text: az bicep decompile --file 'path/to/file.json'
"""

helps['bicep publish'] = """
type: command
short-summary: Publish a bicep file to a remote module registry.
examples:
  - name: Publish a bicep file.
    text: az bicep publish --file MyFileName.bicep --target "br:{registry}/{module_path}:{tag}"
"""

helps['bicep restore'] = """
type: command
short-summary: Restore external modules for a bicep file.
examples:
  - name: Restore external modules.
    text: az bicep restore --file MyFileName.bicep
  - name: Restore external modules and overwrite cached external modules.
    text: az bicep restore --file MyFileName.bicep --force
"""

helps['bicep version'] = """
type: command
short-summary: Show the installed version of Bicep CLI.
"""

helps['bicep list-versions'] = """
type: command
short-summary: List out all available versions of Bicep CLI.
"""

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

helps['account management-group tenant-backfill'] = """
type: group
short-summary: Backfill Tenant Subscription Operations for Management Groups
"""

helps['account management-group tenant-backfill get'] = """
type: command
short-summary: Get the backfill status for a tenant.
examples:
  - name: Get the backfill status for a tenant.
    text: >
        az account management-group tenant-backfill get
"""

helps['account management-group tenant-backfill start'] = """
type: command
short-summary: Start backfilling subscriptions for a tenant.
examples:
  - name: Start backfilling subscriptions for a tenant.
    text: >
        az account management-group tenant-backfill start
"""

helps['account management-group check-name-availability'] = """
type: command
short-summary: Check if a Management Group Name is Valid.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
examples:
  - name: Check if a Management Group Name is Valid.
    text: >
        az account management-group check-name-availability --name GroupName
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

helps['account management-group delete'] = """
type: command
short-summary: Delete an existing management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
examples:
  - name: Delete an existing management group
    text: >
        az account management-group delete --name GroupName
"""

helps['account management-group list'] = """
type: command
short-summary: List all management groups in the current tenant.
examples:
  - name: List all management groups
    text: >
        az account management-group list
"""

helps['account management-group show'] = """
type: command
short-summary: Get the details of the management group.
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
    text: >
        az account management-group show --name GroupName
  - name: Get a management group with children in the first level of hierarchy.
    text: >
        az account management-group show --name GroupName -e
  - name: Get a management group with children in all levels of hierarchy.
    text: >
        az account management-group show --name GroupName -e -r
"""

helps['account management-group subscription'] = """
type: group
short-summary: Subscription operations for Management Groups.
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
    short-summary: Subscription Id or Name
examples:
  - name: Add a subscription to a management group.
    text: >
        az account management-group subscription add --name GroupName --subscription Subscription
"""

helps['account management-group subscription show'] = """
type: command
short-summary: Show the details of a subscription under a known management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
  - name: --subscription -s
    type: string
    short-summary: Subscription Id or Name
examples:
  - name: Show the details of a subscription under a known management group.
    text: >
        az account management-group subscription show --name GroupName --subscription Subscription
"""

helps['account management-group subscription show-sub-under-mg'] = """
type: command
short-summary: Get the subscription under a management group.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
examples:
  - name: Get the subscription under a management group.
    text: >
        az account management-group subscription show-sub-under-mg --name GroupName
"""

helps['account management-group entities'] = """
type: group
short-summary: Entity operations (Management Group and Subscriptions) for Management Groups.
"""

helps['account management-group entities list'] = """
type: command
short-summary: List all entities for the authenticated user.
examples:
  - name: List all entities for the authenticated user.
    text: >
        az account management-group entities list
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
    short-summary: Subscription Id or Name
examples:
  - name: Remove an existing subscription from a management group.
    text: >
        az account management-group subscription remove --name GroupName --subscription Subscription
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

helps['account management-group hierarchy-settings'] = """
type: group
short-summary: Provide operations for hierarchy settings defined at the management group level. Settings can only be set on the root Management Group of the hierarchy.
"""

helps['account management-group hierarchy-settings create'] = """
type: command
short-summary: Create hierarchy settings defined at the Management Group level.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
  - name: --default-management-group -m
    type: string
    short-summary: Set the default Management Group under which new subscriptions get added in this tenant. Default setting is the Root Management Group.
  - name: --require-authorization-for-group-creation -r
    type: boolean
    short-summary: Indicate whether RBAC access is required upon group creation under the root Management Group. True means user will require Microsoft.Management/managementGroups/write action on the root Management Group. Default setting is false.
examples:
  - name: Create hierarchy settings defined at the Management Group level.
    text: >
        az account management-group hierarchy-settings create --name GroupName
  - name: Set the default Management Group new Subscriptions get placed under.
    text: >
        az account management-group hierarchy-settings create --name GroupName -m /providers/Microsoft.Management/managementGroups/DefaultGroup
  - name: Require user to have Microsoft.Management/managementGroups/write access on the Root to create new Management Groups under the Root.
    text: >
        az account management-group hierarchy-settings create --name GroupName -r True
  - name: Update both hierarchy settings.
    text: >
        az account management-group hierarchy-settings create --name GroupName -m /providers/Microsoft.Management/managementGroups/DefaultGroup -r True
"""

helps['account management-group hierarchy-settings list'] = """
type: command
short-summary: Get all the hierarchy settings defined at the Management Group level.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
examples:
  - name: Get all hierarchy settings defined at the Management Group level.
    text: >
        az account management-group hierarchy-settings list --name GroupName
"""

helps['account management-group hierarchy-settings delete'] = """
type: command
short-summary: Delete the hierarchy settings defined at the Management Group level.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
examples:
  - name: Delete all hierarchy settings defined at the Management Group level.
    text: >
        az account management-group hierarchy-settings delete --name GroupName
"""

helps['account management-group hierarchy-settings update'] = """
type: command
short-summary: Update the hierarchy settings defined at the Management Group level.
parameters:
  - name: --name -n
    type: string
    short-summary: Name of the management group.
  - name: --default-management-group -m
    type: string
    short-summary: Set the default Management Group under which new subscriptions get added in this tenant. Default setting is the Root Management Group.
  - name: --require-authorization-for-group-creation -r
    type: boolean
    short-summary: Indicate whether RBAC access is required upon group creation under the root Management Group. True means user will require Microsoft.Management/managementGroups/write action on the root Management Group. Default setting is false.
examples:
  - name: Create hierarchy settings defined at the Management Group level.
    text: >
        az account management-group hierarchy-settings update --name GroupName
  - name: Set the default Management Group new Subscriptions get placed under.
    text: >
        az account management-group hierarchy-settings update --name GroupName -m /providers/Microsoft.Management/managementGroups/DefaultGroup
  - name: Require user to have Microsoft.Management/managementGroups/write access on the Root to create new Management Groups under the Root.
    text: >
        az account management-group hierarchy-settings update --name GroupName -r True
  - name: Update both hierarchy settings.
    text: >
        az account management-group hierarchy-settings update --name GroupName -m /providers/Microsoft.Management/managementGroups/DefaultGroup -r True
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
    text: az deployment show -n deployment01
"""

helps['deployment delete'] = """
type: command
short-summary: Delete a deployment at subscription scope.
examples:
  - name: Delete a deployment at subscription scope.
    text: az deployment delete -n deployment01
"""

helps['deployment cancel'] = """
type: command
short-summary: Cancel a deployment at subscription scope.
examples:
  - name: Cancel a deployment at subscription scope.
    text: az deployment cancel -n deployment01
"""

helps['deployment validate'] = """
type: command
short-summary: Validate whether a template is valid at subscription scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
    text: |
        az deployment validate --location westus2 --parameters MyValue=This MyArray=@array.json --template-file azuredeploy.json
"""

helps['deployment create'] = """
type: command
short-summary: Start a deployment at subscription scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
    text: |
        az deployment create --location WestUS --template-file azuredeploy.json  \\
            --parameters "{ \\"policyName\\": { \\"value\\": \\"policy2\\" }}"
  - name: Create a deployment at subscription scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment create --location WestUS --template-file azuredeploy.json  \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
  - name: Create a deployment at subscription scope from a template-spec
    text: >
        az deployment create --location WestUS --template-spec "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myRG/providers/Microsoft.Resources/templateSpecs/myTemplateSpec/versions/1.0"
"""

helps['deployment export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at subscription scope.
    text: |
        az deployment export --name MyDeployment
"""

helps['deployment wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met. (autogenerated)
    text: |
        az deployment wait --deleted --name MyDeployment --subscription MySubscription
    crafted: true
"""

helps['deployment operation'] = """
type: group
short-summary: Manage deployment operations at subscription scope.
"""

helps['deployment operation list'] = """
type: command
short-summary: List deployment operations at subscription scope.
examples:
  - name: List deployment operations at subscription scope. (autogenerated)
    text: |
        az deployment operation list --name MyDeployment
    crafted: true
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
    text: az deployment sub show -n deployment01
"""

helps['deployment sub delete'] = """
type: command
short-summary: Delete a deployment at subscription scope.
examples:
  - name: Delete a deployment at subscription scope.
    text: az deployment sub delete -n deployment01
"""

helps['deployment sub cancel'] = """
type: command
short-summary: Cancel a deployment at subscription scope.
examples:
  - name: Cancel a deployment at subscription scope.
    text: az deployment sub cancel -n deployment01
"""

helps['deployment sub validate'] = """
type: command
short-summary: Validate whether a template is valid at subscription scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
    text: az deployment sub validate --location westus2 --template-file {template-file}
  - name: Validate whether a template is valid at subscription scope. (autogenerated)
    text: |
        az deployment sub validate --location westus2 --parameters MyValue=This MyArray=@array.json --template-file azuredeploy.json
    crafted: true
"""

helps['deployment sub create'] = """
type: command
short-summary: Start a deployment at subscription scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
    text: |
        az deployment sub create --location WestUS --template-file azuredeploy.json  \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at subscription scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment sub create --location WestUS --template-file azuredeploy.json  \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""


helps['deployment sub what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at subscription scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
  - name: Place the CLI in a waiting state until a deployment condition is met. (autogenerated)
    text: |
        az deployment sub wait --created --name MyDeployment
    crafted: true
"""

helps['deployment operation sub'] = """
type: group
short-summary: Manage deployment operations at subscription scope.
"""

helps['deployment operation sub list'] = """
type: command
short-summary: List deployment operations at subscription scope.
examples:
  - name: List deployment operations at subscription scope. (autogenerated)
    text: |
        az deployment operation sub list --name mydeployment
    crafted: true
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
    text: az deployment group list -g testrg
"""

helps['deployment group show'] = """
type: command
short-summary: Show a deployment at resource group.
examples:
  - name: Show a deployment at resource group.
    text: az deployment group show -g testrg -n deployment01
"""

helps['deployment group delete'] = """
type: command
short-summary: Delete a deployment at resource group.
examples:
  - name: Delete a deployment at resource group.
    text: az deployment group delete -g testrg -n deployment01
"""

helps['deployment group cancel'] = """
type: command
short-summary: Cancel a deployment at resource group.
examples:
  - name: Cancel a deployment at resource group.
    text: az deployment group cancel -g testrg -n deployment01
"""

helps['deployment group validate'] = """
type: command
short-summary: Validate whether a template is valid at resource group.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
    text: az deployment group validate --resource-group testrg --template-file {template-file}
  - name: Validate whether a template is valid at resource group. (autogenerated)
    text: |
        az deployment group validate --parameters MyValue=This MyArray=@array.json --resource-group testrg --template-file azuredeploy.json
    crafted: true
"""

helps['deployment group create'] = """
type: command
short-summary: Start a deployment at resource group.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax. Also note if you are providing a bicepparam file then you can use this argument only once.
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
        az deployment group create --resource-group testrg --name rollout01 \\
            --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at resource group from a local template file, using parameters from a JSON string.
    text: |
        az deployment group create --resource-group testrg --name rollout01 \\
            --template-file azuredeploy.json  \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at resource group from a local template file, using parameters from an array string.
    text: |
      az deployment group create --resource-group testgroup --template-file demotemplate.json --parameters exampleString='inline string' exampleArray='("value1", "value2")'
  - name: Create a deployment at resource group from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment group create --resource-group testrg --name rollout01 \\
            --template-file azuredeploy.json  --parameters @params.json \\
            --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
  - name: Create a deployment at resource group scope from a template-spec
    text: >
        az deployment group create --resource-group testrg --template-spec "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/testrg/providers/Microsoft.Resources/templateSpecs/myTemplateSpec/versions/1.0"
  - name: Create a deployment at resource group scope from a bicepparam parameter file
    text: >
        az deployment group create --resource-group testrg --parameters parameters.bicepparam
  - name: Create a deployment at resource group across tenants
    text: >
        az deployment group create --resource-group testrg --name rollout01 \\
            --template-file azuredeploy.json --parameters @myparameters.json --aux-tenants auxiliary_tenant01 auxiliary_tenant02
"""

helps['deployment group what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at resource group scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
        az deployment group what-if --resource-group testrg --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Execute a deployment What-If operation at a resource group with ResourceIdOnly format.
    text: >
        az deployment group what-if --resource-group testrg --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --result-format ResourceIdOnly
  - name: Execute a deployment What-If operation at a resource group without pretty-printing the result.
    text: >
        az deployment group what-if --resource-group testrg --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --no-pretty-print
"""

helps['deployment group export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at resource group.
    text: az deployment group export --resource-group testrg --name MyDeployment
"""

helps['deployment group wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met. (autogenerated)
    text: |
        az deployment group wait --created --name MyDeployment --resource-group MyResourceGroup
    crafted: true
"""

helps['deployment operation group'] = """
type: group
short-summary: Manage deployment operations at resource group.
"""

helps['deployment operation group list'] = """
type: command
short-summary: List deployment operations at resource group.
examples:
  - name: List deployment operations at resource group (autogenerated)
    text: |
        az deployment operation group list --name MyDeployment --resource-group MyResourceGroup
    crafted: true
"""

helps['deployment operation group show'] = """
type: command
short-summary: Show a deployment operation at resource group.
"""

helps['deployment mg'] = """
type: group
short-summary: Manage Azure Resource Manager template deployment at management group.
"""

helps['deployment mg list'] = """
type: command
short-summary: List deployments at management group.
examples:
  - name: List deployments at management group.
    text: az deployment mg list -m testmg
"""

helps['deployment mg show'] = """
type: command
short-summary: Show a deployment at management group.
examples:
  - name: Show a deployment at management group.
    text: az deployment mg show -m testmg -n deployment01
"""

helps['deployment mg delete'] = """
type: command
short-summary: Delete a deployment at management group.
examples:
  - name: Delete a deployment at management group.
    text: az deployment mg delete -m testmg -n deployment01
"""

helps['deployment mg cancel'] = """
type: command
short-summary: Cancel a deployment at management group.
examples:
  - name: Cancel a deployment at management group.
    text: az deployment mg cancel -m testmg -n deployment01
"""

helps['deployment mg validate'] = """
type: command
short-summary: Validate whether a template is valid at management group.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
examples:
  - name: Validate whether a template is valid at management group.
    text: az deployment mg validate --management-group-id testmg --location WestUS --template-file {template-file}
  - name: Validate whether a template is valid at management group. (autogenerated)
    text: |
        az deployment mg validate --location WestUS --management-group-id testmg --name mydeployment --parameters @myparameters.json --template-file azuredeploy.json
    crafted: true
"""

helps['deployment mg what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at management group scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
  - name: Execute a deployment What-If operation at a management group.
    text: >
        az deployment mg what-if --management-group-id testmg --location westus --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Execute a deployment What-If operation at a management group with ResourceIdOnly format.
    text: >
        az deployment mg what-if --management-group-id testmg --location westus --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --result-format ResourceIdOnly
  - name: Execute a deployment What-If operation at a management group without pretty-printing the result.
    text: >
        az deployment mg what-if --management-group-id testmg --location westus --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json --no-pretty-print
"""

helps['deployment mg create'] = """
type: command
short-summary: Start a deployment at management group.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
  - name: Create a deployment at management group from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment mg create --management-group-id testrg --name rollout01 --location WestUS \\
            --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at management group from a local template file, using parameters from a JSON string.
    text: |
        az deployment mg create --management-group-id testmg --name rollout01 --location WestUS \\
            --template-file azuredeploy.json \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at management group from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment mg create --management-group-id testmg --name rollout01 --location WestUS \\
            --template-file azuredeploy.json --parameters @params.json \\
            --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""

helps['deployment mg export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment at management group.
    text: az deployment mg export --management-group-id testmg --name MyDeployment
"""

helps['deployment mg wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
"""

helps['deployment operation mg'] = """
type: group
short-summary: Manage deployment operations at management group.
"""

helps['deployment operation mg list'] = """
type: command
short-summary: List deployment operations at management group.
"""

helps['deployment operation mg show'] = """
type: command
short-summary: Show a deployment operation at management group.
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
    text: az deployment tenant show -n deployment01
"""

helps['deployment tenant delete'] = """
type: command
short-summary: Delete a deployment at tenant scope.
examples:
  - name: Delete a deployment at tenant scope.
    text: az deployment tenant delete -n deployment01
"""

helps['deployment tenant cancel'] = """
type: command
short-summary: Cancel a deployment at tenant scope.
examples:
  - name: Cancel a deployment at tenant scope.
    text: az deployment tenant cancel -n deployment01
"""

helps['deployment tenant validate'] = """
type: command
short-summary: Validate whether a template is valid at tenant scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
  - name: Validate whether a template is valid at tenant scope. (autogenerated)
    text: |
        az deployment tenant validate --location WestUS --name mydeployment --parameters @myparameters.json --template-file azuredeploy.json
    crafted: true
"""

helps['deployment tenant what-if'] = """
type: command
short-summary: Execute a deployment What-If operation at tenant scope.
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
long-summary: Please specify only one of --template-file FILE | --template-uri URI | --template-spec to input the ARM template.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
    text: |
        az deployment tenant create --name rollout01 --location WestUS \\
            --template-file azuredeploy.json \\
            --parameters '{ \\"policyName\\": { \\"value\\": \\"policy2\\" } }'
  - name: Create a deployment at tenant scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment tenant create --name rollout01 --location WestUS \\
            --template-file azuredeploy.json  --parameters @params.json \\
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
  - name: Place the CLI in a waiting state until a deployment condition is met. (autogenerated)
    text: |
        az deployment tenant wait --deleted --name MyDeployment
    crafted: true
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
  - name: Retrieve all deployment scripts found in a resource group
    text: |
        az deployment-scripts list --resource-group contoso-rg
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
        az deployment-scripts show --resource-group contoso-rg --name contosoBashScript
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
        az deployment-scripts show-log --resource-group contoso-rg --name contosoBashScript
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
        az deployment-scripts delete --resource-group contoso-rg --name contosoBashScript
"""

helps['feature'] = """
type: group
short-summary: Manage resource provider features.
"""

helps['feature list'] = """
type: command
short-summary: List preview features.
examples:
  - name: List preview features
    text: az feature list
"""

helps['feature register'] = """
type: command
short-summary: register a preview feature.
examples:
  - name: register the "Shared Image Gallery" feature
    text: az feature register --namespace Microsoft.Compute --name GalleryPreview
"""

helps['feature unregister'] = """
type: command
short-summary: unregister a preview feature.
examples:
  - name: unregister the "Shared Image Gallery" feature
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
  - name: List feature registrations
    text: az feature registration list
"""

helps['feature registration create'] = """
type: command
short-summary: Create a feature registration.
examples:
  - name: create the "Shared Image Gallery" feature
    text: az feature registration create --namespace Microsoft.Compute --name GalleryPreview
"""

helps['feature registration delete'] = """
type: command
short-summary: Delete a feature registration.
examples:
  - name: delete the "Shared Image Gallery" feature
    text: az feature registration delete --namespace Microsoft.Compute --name GalleryPreview
"""

helps['group'] = """
type: group
short-summary: Manage resource groups and template deployments.
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
  - name: Force delete all the Virtual Machines in a resource group.
    text: >
        az group delete -n MyResourceGroup --force-deletion-types Microsoft.Compute/virtualMachines
"""

helps['group deployment'] = """
type: group
short-summary: Manage Azure Resource Manager deployments.
"""

helps['group deployment create'] = """
type: command
short-summary: Start a deployment.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
examples:
  - name: Create a deployment from a remote template file, using parameters from a local JSON file.
    text: >
        az group deployment create -g MyResourceGroup --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment from a local template file, using parameters from a JSON string.
    text: |
        az group deployment create -g MyResourceGroup --template-file azuredeploy.json \\
            --parameters "{ \\"location\\": { \\"value\\": \\"westus\\" } }"
  - name: Create a deployment from a local template, using a local parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az group deployment create -g MyResourceGroup --template-file azuredeploy.json \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
"""

helps['group deployment export'] = """
type: command
short-summary: Export the template used for a deployment.
examples:
  - name: Export the template used for a deployment. (autogenerated)
    text: |
        az group deployment export --name MyDeployment --resource-group MyResourceGroup
    crafted: true
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
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as `<KEY=VALUE>` pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
examples:
  - name: Validate whether a template is syntactically correct. (autogenerated)
    text: |
        az group deployment validate --parameters "{ \\"location\\": { \\"value\\": \\"westus\\" } }" \\
            --resource-group MyResourceGroup --template-file storage.json
    crafted: true
"""

helps['group deployment wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a deployment condition is met.
examples:
  - name: Place the CLI in a waiting state until a deployment condition is met. (autogenerated)
    text: |
        az group deployment wait --name MyDeployment --resource-group MyResourceGroup --updated
    crafted: true
  - name: Place the CLI in a waiting state until a deployment condition is met. (autogenerated)
    text: |
        az group deployment wait --created --name MyDeployment --resource-group MyResourceGroup
    crafted: true
"""

helps['group exists'] = """
type: command
short-summary: Check if a resource group exists.
examples:
  - name: Check if 'MyResourceGroup' exists.
    text: >
        az group exists -n MyResourceGroup
"""

helps['group list'] = """
type: command
short-summary: List resource groups.
examples:
  - name: List all resource groups located in the West US region.
    text: >
        az group list --query "[?location=='westus']"
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

helps['group update'] = """
type: command
short-summary: Update a resource group.
examples:
  - name: Update a resource group. (autogenerated)
    text: |
        az group update --resource-group MyResourceGroup --set tags.CostCenter='{"Dept":"IT","Environment":"Test"}'
    crafted: true
"""

helps['group wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of the resource group is met.
examples:
  - name: Place the CLI in a waiting state until a condition of the resource group is met. (autogenerated)
    text: |
        az group wait --created  --resource-group MyResourceGroup
    crafted: true
  - name: Place the CLI in a waiting state until a condition of the resource group is met. (autogenerated)
    text: |
        az group wait --deleted --resource-group MyResourceGroup
    crafted: true
"""

helps['lock'] = """
type: group
short-summary: Manage Azure locks.
"""

helps['lock create'] = """
type: command
short-summary: Create a lock.
long-summary: 'Locks can exist at three different scopes: subscription, resource group and resource. \
                For how to add locks at different levels, please refer to the following examples.'
examples:
  - name: Create a read-only subscription level lock.
    text: >
        az lock create --name lockName --lock-type ReadOnly
  - name: Create a read-only resource group level lock.
    text: >
        az lock create --name lockName --resource-group group --lock-type ReadOnly
  - name: Create a read-only resource level lock on a vnet resource.
    text: >
        az lock create --name lockName --resource-group group --lock-type ReadOnly --resource-type \\
            Microsoft.Network/virtualNetworks --resource myVnet
  - name: Create a read-only resource level lock on a subnet resource with a specific parent.
    text: >
        az lock create --name lockName --resource-group group --lock-type ReadOnly --resource-type \\
            Microsoft.Network/subnets --parent virtualNetworks/myVnet --resource mySubnet
"""

helps['lock delete'] = """
type: command
short-summary: Delete a lock.
long-summary: 'Locks can exist at three different scopes: subscription, resource group and resource. \
                For how to delete locks at different levels, please refer to the following examples.'
examples:
  - name: Delete a subscription level lock
    text: >
        az lock delete --name lockName
  - name: Delete a resource group level lock
    text: >
        az lock delete --name lockName --resource-group group
  - name: Delete a resource level lock
    text: >
        az lock delete --name lockName --resource-group group --resource resourceName --resource-type resourceType
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
  - name: Show the properties of a lock (autogenerated)
    text: |
        az lock show --name lockname --resource-group MyResourceGroup --resource-name MyResource --resource-type Microsoft.Network/virtualNetworks
    crafted: true
"""

helps['lock update'] = """
type: command
short-summary: Update a lock.
examples:
  - name: Update a resource group level lock with new notes and type
    text: >
        az lock update --name lockName --resource-group group --notes newNotesHere --lock-type CanNotDelete
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

helps['managedapp definition'] = """
type: group
short-summary: Manage Azure Managed Applications.
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

helps['managedapp definition update'] = """
type: command
short-summary: Update a managed application definition.
examples:
  - name: Update a managed application defintion.
    text: >
        az managedapp definition update -g MyResourceGroup -n MyManagedAppDef -l eastus --display-name "MyManagedAppDef" \\
            --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
            --package-file-uri "https://path/to/myPackage.zip"
  - name: Update a managed application defintion with inline values for createUiDefinition and mainTemplate.
    text: >
        az managedapp definition update -g MyResourceGroup -n MyManagedAppDef -l eastus --display-name "MyManagedAppDef" \\
            --description "My Managed App Def description" -a "myPrincipalId:myRoleId" --lock-level None \\
            --create-ui-definition @myCreateUiDef.json --main-template @myMainTemplate.json
"""

helps['managedapp definition delete'] = """
type: command
short-summary: Delete a managed application definition.
examples:
  - name: Delete a managed application definition. (autogenerated)
    text: |
        az managedapp definition delete --name MyManagedApplicationDefinition --resource-group MyResourceGroup
    crafted: true
"""

helps['managedapp definition list'] = """
type: command
short-summary: List managed application definitions.
examples:
  - name: List managed application definitions. (autogenerated)
    text: |
        az managedapp definition list --resource-group MyResourceGroup
    crafted: true
"""

helps['managedapp delete'] = """
type: command
short-summary: Delete a managed application.
examples:
  - name: Delete a managed application. (autogenerated)
    text: |
        az managedapp delete --name MyManagedApplication --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['managedapp list'] = """
type: command
short-summary: List managed applications.
examples:
  - name: List managed applications. (autogenerated)
    text: |
        az managedapp list --resource-group MyResourceGroup
    crafted: true
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
        az provider list --query "[?namespace=='Microsoft.Network'].resourceTypes[].resourceType"
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
  - name: Get an individual provider's operations. (autogenerated)
    text: |
        az provider operation show --namespace Microsoft.Storage
    crafted: true
"""

helps['provider register'] = """
type: command
short-summary: Register a provider.
examples:
  - name: Register a provider. (autogenerated)
    text: |
        az provider register --namespace 'Microsoft.PolicyInsights'
    crafted: true
  - name: Register a provider from RPaaS.
    text: |
        az provider register -n 'Microsoft.Confluent' --accept-terms
  - name: Register a management group.
    text: |
        az provider register --namespace Microsoft.Automation -m mgID
"""

helps['provider unregister'] = """
type: command
short-summary: Unregister a provider.
examples:
  - name: Unregister a provider. (autogenerated)
    text: |
        az provider unregister --namespace Microsoft.Automation
    crafted: true
"""

helps['resource'] = """
type: group
short-summary: Manage Azure resources.
"""

helps['resource create'] = """
type: command
short-summary: create a resource.
examples:
  - name: Create an API app by providing a full JSON configuration.
    text: |
        az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites \\
            --is-full-object --properties "{ \\"kind\\": \\"api\\", \\"location\\": \\
                \\"West US\\", \\"properties\\": { \\"serverFarmId\\": \\
                    \\"/subscriptions/{SubID}/resourcegroups/{ResourceGroup} \\
                        /providers/Microsoft.Web/serverfarms/{ServicePlan}\\" } }"
  - name: Create a resource by loading JSON configuration from a file.
    text: >
        az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites --is-full-object --properties @jsonConfigFile
  - name: Create a web app with the minimum required configuration information.
    text: |
        az resource create -g myRG -n myWeb --resource-type Microsoft.web/sites \\
            --properties "{ \\"serverFarmId\\":\\"/subscriptions/{SubID}/resourcegroups/ \\
                {ResourceGroup}/providers/Microsoft.Web/serverfarms/{ServicePlan}\\" }"
  - name: Create a resource by using the latest api-version whether this version is a preview version.
    text: >
        az resource create -g myRG -n myApiApp --resource-type Microsoft.web/sites --is-full-object --properties @jsonConfigFile --latest-include-preview
  - name: Create a site extension to a web app
    text: |
        az resource create -g myRG --api-version "2018-02-01" \\
            --name "{sitename+slot}/siteextensions/Contrast.NetCore.Azure.SiteExtension"  \\
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
        az resource delete -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines"
  - name: Delete a web app using a resource identifier.
    text: >
        az resource delete --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebapp
  - name: Delete a subnet using a resource identifier.
    text: >
        az resource delete --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Network/virtualNetworks/MyVnet/subnets/MySubnet
  - name: Delete a virtual machine named 'MyVm' by using the latest api-version whether this version is a preview version.
    text: >
        az resource delete -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines" --latest-include-preview
"""

helps['resource invoke-action'] = """
type: command
short-summary: Invoke an action on the resource.
long-summary: >
    A list of possible actions corresponding to a resource can be found at https://learn.microsoft.com/rest/api/. All POST requests are actions that can be invoked and are specified at the end of the URI path. For instance, to stop a VM, the
    request URI is https://management.azure.com/subscriptions/{SubscriptionId}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VM}/powerOff?api-version={APIVersion} and the corresponding action is `powerOff`. This can
    be found at https://learn.microsoft.com/rest/api/compute/virtualmachines/virtualmachines-stop.
examples:
  - name: Power-off a vm, specified by Id.
    text: >
        az resource invoke-action --action powerOff \\
          --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VMName}
  - name: Capture information for a stopped vm.
    text: >
        az resource invoke-action --action capture \\
          --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/ \\
            Microsoft.Compute/virtualMachines/{VMName} \\
          --request-body "{ \\"vhdPrefix\\": \\"myPrefix\\", \\"destinationContainerName\\": \\
            \\"myContainer\\", \\"overwriteVhds\\": true }"
  - name: Invoke an action on the resource. (autogenerated)
    text: |
        az resource invoke-action --action capture --name MyResource --resource-group MyResourceGroup --resource-type Microsoft.web/sites
    crafted: true
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
  - name: Create a link from {SourceID} to {ResourceID} with notes
    text: >
        az resource link create --link {SourceID} --target {ResourceID} --notes "SourceID depends on ResourceID"
"""

helps['resource link delete'] = """
type: command
short-summary: Delete a link between resources.
parameters:
  - name: --link
    long-summary: >
        Format: /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
examples:
  - name: Delete link {LinkID}
    text: >
        az resource link delete --link {LinkID}
"""

helps['resource link list'] = """
type: command
short-summary: List resource links.
examples:
  - name: List links, filtering with {filter-string}
    text: >
        az resource link list --filter {filter-string}
  - name: List all links for resource group {ResourceGroup} in subscription {SubID}
    text: >
        az resource link list --scope /subscriptions/{SubID}/resourceGroups/{ResourceGroup}
"""

helps['resource link update'] = """
type: command
short-summary: Update link between resources.
parameters:
  - name: --link
    long-summary: >
        Format: /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
examples:
  - name: Update the notes for {LinkID} notes "some notes to explain this link"
    text: >
        az resource link update --link {LinkID} --notes "some notes to explain this link"
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
  - name: Delete a resource-level lock. (autogenerated)
    text: |
        az resource lock delete --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp}
    crafted: true
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
  - name: Update a resource-level lock. (autogenerated)
    text: |
        az resource lock update --lock-type CanNotDelete --name lockName --namespace Microsoft.Network --resource-group MyResourceGroup --resource-name myvnet --resource-type Microsoft.Network/virtualNetworks
    crafted: true
"""

helps['resource show'] = """
type: command
short-summary: Get the details of a resource.
examples:
  - name: Show a virtual machine resource named 'MyVm'.
    text: >
        az resource show -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines"
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
  - name: Show a virtual machine resource named 'MyVm' by using the latest api-version whether this version is a preview version.
    text: >
        az resource show -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines" --latest-include-preview
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
        az resource tag --tags vmlist=vm1 --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp}
  - name: Tag the virtual machine 'MyVm' with the key 'vmlist' and value 'vm1' incrementally. It doesn't empty the existing tags.
    text: >
        az resource tag --tags vmlist=vm1 -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines" -i
  - name: Tag the virtual machine 'MyVm' with the key 'vmlist' and value 'vm1' by using the latest api-version whether this version is a preview version.
    text: >
        az resource tag --tags vmlist=vm1 -g MyResourceGroup -n MyVm --resource-type "Microsoft.Compute/virtualMachines" --latest-include-preview
"""

helps['resource update'] = """
type: command
short-summary: Update a resource by PUT request.
long-summary: It supports the generic update (using property path) to update resources.
              If the update operation fails, please try run 'az resource patch' instead.
examples:
  - name: Update a webapp by using the latest api-version whether this version is a preview version.
    text: >
        az resource update --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp} --set tags.key=value --latest-include-preview
  - name: Update a resource. (autogenerated)
    text: |
        az resource update --ids $id --set properties.connectionType=Proxy
    crafted: true
  - name: Update a resource. (autogenerated)
    text: |
        az resource update --name MyResource --resource-group MyResourceGroup --resource-type subnets --set tags.key=value
    crafted: true
"""

helps['resource patch'] = """
type: command
short-summary: Update a resource by PATCH request.
long-summary: It supports updating resources with JSON-formatted string.
              If the patch operation fails, please try run 'az resource update' instead.
examples:
  - name: Update a webapp by using the latest api-version whether this version is a preview version.
    text: >
        az resource patch --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp} \\
          --latest-include-preview --is-full-object --properties "{ \\"tags\\": { \\"key\\": \\"value\\" } }"
  - name: Update a resource by using JSON configuration from a file.
    text: >
        az resource patch --name MyResource --resource-group MyResourceGroup --resource-type Microsoft.web/sites \\
          --is-full-object --properties @jsonConfigFile
  - name: Update an API app by providing a JSON configuration.
    text: |
        az resource patch --name MyApiApp --resource-group MyResourceGroup --resource-type Microsoft.web/sites \\
            --is-full-object --properties "{ \\"kind\\": \\"api\\", \\"properties\\": { \\"serverFarmId\\": \\
                    \\"/subscriptions/{SubID}/resourcegroups/{ResourceGroup} \\
                        /providers/Microsoft.Web/serverfarms/{ServicePlan}\\" } }"
"""

helps['resource wait'] = """
type: command
short-summary: Place the CLI in a waiting state until a condition of a resources is met.
examples:
  - name: Place the CLI in a waiting state until a condition of a resources is met. (autogenerated)
    text: |
        az resource wait --exists --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp}
    crafted: true
  - name: Place the CLI in a waiting state until a condition of a resources is met. (autogenerated)
    text: |
        az resource wait --exists --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Web/sites/{WebApp} --include-response-body true
    crafted: true
  - name: Place the CLI in a waiting state until a condition of a resources is met. (autogenerated)
    text: |
        az resource wait --exists --name MyResource --resource-group MyResourceGroup --resource-type subnets
    crafted: true
"""

helps['resource move'] = """
type: command
short-summary: Move resources from one resource group to another (can be under different subscription).
examples:
  - name: Move multiple resources to the destination resource group under the destination subscription
    text: >
        az resource move --destination-group ResourceGroup --destination-subscription-id SubscriptionId --ids "ResourceId1" "ResourceId2" "ResourceId3"
"""

helps['tag'] = """
type: group
short-summary: Tag Management on a resource.
"""

helps['tag add-value'] = """
type: command
short-summary: Create a tag value.
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
parameters:
  - name: --name -n
    short-summary: The name of the tag to create.
  - name: --subscription
    short-summary: Name or ID of subscription. You can configure the default subscription using az account set -s NAME_OR_ID.
  - name: --resource-id
    short-summary: The resource identifier for the entity being tagged. A resource, a resource group or a subscription may be tagged.
  - name: --tags
    short-summary: The tags to be applied on the resource.
examples:
  - name: Create a tag in the subscription.
    text: >
        az tag create --name MyTag
  - name: Create or update the entire set of tags on a subscription.
    text: >
        az tag create --resource-id /subscriptions/{subId} --tags Dept=Finance Status=Normal
  - name: Create or update the entire set of tags on a resource group.
    text: >
        az tag create --resource-id /subscriptions/{sub-id}/resourcegroups/{rg} --tags Dept=Finance Status=Normal
  - name: Create or update the entire set of tags on a resource.
    text: >
        az tag create --resource-id /subscriptions/{sub-id}/resourcegroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vmName} --tags Dept=Finance Status=Normal
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
  - name: Delete a predefined tag from the subscription not associated with a resource or having no tag values.
    text: >
        az tag delete --name MyTag
  - name: Delete the entire set of tags on a subscription.
    text: >
        az tag delete --resource-id /subscriptions/{sub-id}
  - name: Delete the entire set of tags on a resource group.
    text: >
        az tag delete --resource-id /subscriptions/{sub-id}/resourcegroups/{rg}
  - name: Delete the entire set of tags on a resource. (Even using --name along with --resource-id to specify a single tag)
    text: >
        az tag delete --resource-id /subscriptions/{sub-id}/resourcegroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vmName}
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
        az tag list --resource-id /subscriptions/{sub-id}
  - name: List the entire set of tags on a resource group.
    text: >
        az tag list --resource-id /subscriptions/{sub-id}/resourcegroups/{rg}
  - name: List the entire set of tags on a resource.
    text: >
        az tag list --resource-id /subscriptions/{sub-id}/resourcegroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vmName}
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
        az tag update --resource-id /subscriptions/{sub-id} --operation merge --tags key1=value1 key3=value3
  - name: Selectively update the set of tags on a resource group with "replace" Operation.
    text: >
        az tag update --resource-id /subscriptions/{sub-id}/resourcegroups/{rg} --operation replace --tags key1=value1 key3=value3
  - name: Selectively update the set of tags on a resource with "delete" Operation.
    text: >
        az tag update --resource-id /subscriptions/{sub-id}/resourcegroups/{rg}/providers/Microsoft.Compute/virtualMachines/{vmName} --operation delete --tags key1=value1
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
    text: az ts create -g testRG --name TemplateSpecName -l WestUS --display-name "MyDisplayName" --description "Simple template spec" --tags key1=value1
  - name: Create a template spec version.
    text: az ts create -g testRG --name TemplateSpecName -v 2.0 -l WestUS --template-file templateSpec.json --version-description "Less simple template spec" --tags key1=value1 key3=value3
  - name: Create a template spec and a version of the template spec.
    text: az ts create -g testRG --name TemplateSpecName -v 1.0 -l WestUS --template-file templateSpec.json --display-name "MyDisplayName" --description "Simple template spec" --version-description "Version of simple template spec" --tags key1=value1 key2=value2
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
    text: az ts update -g ExistingRG --name ExistingName -v 3.0 --version-description "New description" --yes
  - name: Update all the properties of a template spec version.
    text: az ts update -g ExistingRG --name ExistingName -v 3.0 -f updatedTemplate.json --display-name "New parent display name" --description "New parent description" --version-description "New child description" --ui-form-definition formDefinition.json
  - name: Remove tag(s) from template spec version with no prompt.
    text: az ts update -g ExistingRG --name ExistingName -v 3.0 -f updatedTemplate.json --tags --yes

"""

helps['ts show'] = """
type: command
short-summary: Get the specified template spec or template spec version.
examples:
  - name: Show the specified template spec.
    text: az ts show -g testrg --name TemplateSpecName
  - name: Show the specified template spec version.
    text: az ts show -g testrg --name TemplateSpecName --version VersionName
  - name: Show the specified template spec or template spec version based on the resource ID.
    text: az ts show --template-spec resourceID
"""

helps['ts export'] = """
type: command
short-summary: Export the specified template spec version and artifacts (if any) to the specified output folder.
examples:
  - name: Export the specified template spec version based on resource ID.
    text: az ts export -s resourceID --output-folder C:/path/
  - name: Export the specified template spec version.
    text: az ts export -g testrg --name TemplateSpecName --version VersionName --output-folder C:/path/
"""

helps['ts delete'] = """
type: command
short-summary: Delete a specified template spec or template spec version by name or resource ID..
examples:
  - name: Delete the specified template spec and all versions.
    text: az ts delete -g MyResourceGroup --name TemplateSpecName
  - name: Delete the specified version from the template spec.
    text: az ts delete -g MyResourceGroup --name TemplateSpecName --version VersionName
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
    text: az ts list -g MyResourceGroup
  - name: List all versions of parent template spec.
    text: az ts list -g MyResourceGroup -n TemplateSpecName
"""

helps['bicep'] = """
type: group
short-summary: Bicep CLI command group.
long-summary: |
  There are two configurations that can be set for the command group, including bicep.check_version and bicep.use_binary_from_path:

  [1] az config set bicep.check_version=True/False
      Turn on/off Bicep CLI version check when executing az bicep commands.

  [2] az config set bicep.use_binary_from_path=True/False/if_found_in_ci
      Specify whether to use Bicep CLI from PATH or not. The default value is if_found_in_ci.
"""

helps['bicep install'] = """
type: command
short-summary: Install Bicep CLI.
examples:
  - name: Install Bicep CLI.
    text: az bicep install
  - name: Install a specific version of Bicep CLI.
    text: az bicep install --version v0.2.212
  - name: Install Bicep CLI and specify the target platform.
    text: az bicep install --target-platform linux-x64
"""

helps['bicep uninstall'] = """
type: command
short-summary: Uninstall Bicep CLI.
"""

helps['bicep upgrade'] = """
type: command
short-summary: Upgrade Bicep CLI to the latest version.
examples:
  - name: Upgrade Bicep CLI.
    text: az bicep upgrade
  - name: Upgrade Bicep CLI and specify the target platform.
    text: az bicep upgrade --target-platform linux-x64
"""

helps['bicep build'] = """
type: command
short-summary: Build a Bicep file.
examples:
  - name: Build a Bicep file.
    text: az bicep build --file {bicep_file}
  - name: Build a Bicep file and print all output to stdout.
    text: az bicep build --file {bicep_file} --stdout
  - name: Build a Bicep file and save the result to the specified directory.
    text: az bicep build --file {bicep_file} --outdir {out_dir}
  - name: Build a Bicep file and save the result to the specified file.
    text: az bicep build --file {bicep_file} --outfile {out_file}
  - name: Build a Bicep file without restoring external modules.
    text: az bicep build --file {bicep_file} --no-restore
"""

helps['bicep build-params'] = """
type: command
short-summary: Build .bicepparam file.
examples:
  - name: Build a .bicepparam file.
    text: az bicep build-params --file {bicepparam_file}
  - name: Build a .bicepparam file and print all output to stdout.
    text: az bicep build-params --file {bicepparam_file} --stdout
  - name: Build a .bicepparam file and save the result to the specified file.
    text: az bicep build-params --file {bicepparam_file} --outfile {out_file}
"""

helps['bicep format'] = """
type: command
short-summary: Format a Bicep file.
examples:
  - name: Format a Bicep file.
    text: az bicep format --file {bicep_file}
  - name: Format a Bicep file and print all output to stdout.
    text: az bicep format --file {bicep_file} --stdout
  - name: Format a Bicep file and save the result to the specified directory.
    text: az bicep format --file {bicep_file} --outdir {out_dir}
  - name: Format a Bicep file and save the result to the specified file.
    text: az bicep format --file {bicep_file} --outfile {out_file}
  - name: Format a Bicep file insert a final newline.
    text: az bicep format --file {bicep_file} --insert-final-newline
  - name: Format a Bicep file set indentation kind. Valid values are ( Space | Tab ).
    text: az bicep format --file {bicep_file} --indent-kind {indent_kind}
  - name: Format a Bicep file set number of spaces to indent with (Only valid with --indent-kind set to Space).
    text: az bicep format --file {bicep_file} --indent-size {indent_size}
"""

helps['bicep decompile'] = """
type: command
short-summary: Attempt to decompile an ARM template file to a Bicep file.
examples:
  - name: Decompile an ARM template file.
    text: az bicep decompile --file {json_template_file}
  - name: Decompile an ARM template file and overwrite existing Bicep file.
    text: az bicep decompile --file {json_template_file} --force
"""

helps['bicep decompile-params'] = """
type: command
short-summary: Decompile a parameters .json file to .bicepparam.
examples:
  - name: Attempts to decompile a parameters .json file to .bicepparam.
    text: az bicep decompile-params --file {json_template_file}
  - name: Attempts to decompile a parameters .json file to .bicepparam using the bicep file given.
    text: az bicep decompile-params --file {json_template_file} --bicep-file {bicep_file}
  - name: Attempts to decompile a parameters .json file to .bicepparam and print all output to stdout.
    text: az bicep decompile-params --file {json_template_file} --stdout
  - name: Attempts to decompile a parameters .json file to .bicepparam and print all output to stdout and save the result to the specified directory.
    text: az bicep decompile-params --file {json_template_file} --outdir {out_dir}
  - name: Attempts to decompile a parameters .json file to .bicepparam and print all output to stdout and save the result to the specified file.
    text: az bicep decompile-params --file {json_template_file} --outfile {out_file}
"""

helps['bicep publish'] = """
type: command
short-summary: Publish a bicep file to a remote module registry.
examples:
  - name: Publish a bicep file.
    text: az bicep publish --file {bicep_file} --target "br:{registry}/{module_path}:{tag}"
  - name: Publish a bicep file overwriting an existing tag.
    text: az bicep publish --file {bicep_file} --target "br:{registry}/{module_path}:{tag} --force"
  - name: Publish a bicep file with documentation uri.
    text: az bicep publish --file {bicep_file} --target "br:{registry}/{module_path}:{tag}" --documentation-uri {documentation_uri}
  - name: Publish a bicep file with documentation uri and include source code
    text: az bicep publish --file {bicep_file} --target "br:{registry}/{module_path}:{tag}" --documentation-uri {documentation_uri} --with-source
"""

helps['bicep restore'] = """
type: command
short-summary: Restore external modules for a bicep file.
examples:
  - name: Restore external modules.
    text: az bicep restore --file {bicep_file}
  - name: Restore external modules and overwrite cached external modules.
    text: az bicep restore --file {bicep_file} --force
"""

helps['bicep version'] = """
type: command
short-summary: Show the installed version of Bicep CLI.
"""

helps['bicep list-versions'] = """
type: command
short-summary: List out all available versions of Bicep CLI.
"""

helps['stack'] = """
type: group
short-summary: A deployment stack is a native Azure resource type that enables you to perform operations on a resource collection as an atomic unit.
long-summary: Deployment stacks are defined in ARM as the type Microsoft.Resources/deploymentStacks.
"""

helps['stack mg'] = """
type: group
short-summary: Manage Deployment Stacks at management group.
"""

helps['stack mg create'] = """
type: command
short-summary: Create or update a deployment stack at management group scope
examples:
  - name: Create a deployment stack using template file and detach all resources on unmanage.
    text: az stack mg create --name StackName --management-group-id myMg --template-file simpleTemplate.json --location westus2 --description description --deny-settings-mode None --action-on-unmanage detachAll
  - name: Create a deployment stack with parameter file and delete resources on unmanage.
    text: az stack mg create --name StackName --management-group-id myMg --action-on-unmanage deleteResources --template-file simpleTemplate.json --parameters simpleTemplateParams.json --location westus2 --description description --deny-settings-mode None
  - name: Create a deployment stack with template spec.
    text: az stack mg create --name StackName --management-group-id myMg --template-spec TemplateSpecResourceIDWithVersion --location westus2 --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack using bicep file and delete all resources on unmanage.
    text: az stack mg create --name StackName --management-group-id myMg --action-on-unmanage deleteAll --template-file simple.bicep --location westus2 --description description --deny-settings-mode None
  - name: Create a deployment stack using parameters from key/value pairs.
    text: az stack mg create --name StackName --management-group-id myMg --template-file simpleTemplate.json --location westus --description description --parameters simpleTemplateParams.json value1=foo value2=bar --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: az stack mg create --name StackName --management-group-id myMg --template-file azuredeploy.json --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json --location westus --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, using deny settings.
    text: az stack mg create --name StackName --management-group-id myMg --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-excluded-principals "test1 test2" --location westus --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, apply deny settings to child scope.
    text: az stack mg create --name StackName --management-group-id myMg --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-apply-to-child-scopes --location westus --action-on-unmanage deleteResources
"""

helps['stack mg validate'] = """
type: command
short-summary: Validate a deployment stack at management group scope
examples:
  - name: Validate a deployment stack using template file and detach all resources on unmanage.
    text: az stack mg validate --name StackName --management-group-id myMg --template-file simpleTemplate.json --location westus2 --description description --deny-settings-mode None --action-on-unmanage detachAll
  - name: Validate a deployment stack with parameter file and delete resources on unmanage.
    text: az stack mg validate --name StackName --management-group-id myMg --action-on-unmanage deleteResources --template-file simpleTemplate.json --parameters simpleTemplateParams.json --location westus2 --description description --deny-settings-mode None
  - name: Validate a deployment stack with template spec.
    text: az stack mg validate --name StackName --management-group-id myMg --template-spec TemplateSpecResourceIDWithVersion --location westus2 --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack using bicep file and delete all resources on unmanage.
    text: az stack mg validate --name StackName --management-group-id myMg --action-on-unmanage deleteAll --template-file simple.bicep --location westus2 --description description --deny-settings-mode None
  - name: Validate a deployment stack using parameters from key/value pairs.
    text: az stack mg validate --name StackName --management-group-id myMg --template-file simpleTemplate.json --location westus --description description --parameters simpleTemplateParams.json value1=foo value2=bar --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: az stack mg validate --name StackName --management-group-id myMg --template-file azuredeploy.json --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json --location westus --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, using deny settings.
    text: az stack mg validate --name StackName --management-group-id myMg --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-excluded-principals "test1 test2" --location westus --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, apply deny settings to child scope.
    text: az stack mg validate --name StackName --management-group-id myMg --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-apply-to-child-scopes --location westus --action-on-unmanage deleteResources
"""

helps['stack mg list'] = """
type: command
short-summary: List all deployment stacks in management group
examples:
  - name: List all stacks
    text: az stack mg list --management-group-id myMg
"""

helps['stack mg show'] = """
type: command
short-summary: Get specified deployment stack from management group scope
examples:
  - name: Get stack by name.
    text: az stack mg show --name StackName --management-group-id myMg
  - name: Get stack by stack resource id.
    text: az stack mg show --id /providers/Microsoft.Management/managementGroups/myMg/providers/Microsoft.Resources/deploymentStacks/StackName --management-group-id myMg
"""

helps['stack mg export'] = """
type: command
short-summary: Export the template used to create the deployment stack
examples:
  - name: Export template by name.
    text: az stack mg export --name StackName --management-group-id myMg
  - name: Export template by stack resource id.
    text: az stack mg export --id /providers/Microsoft.Management/managementGroups/myMg/providers/Microsoft.Resources/deploymentStacks/StackName --management-group-id myMg
"""

helps['stack mg delete'] = """
type: command
short-summary: Delete specified deployment stack from management group scope
examples:
  - name: Delete stack by name.
    text: az stack mg delete --name StackName --management-group-id myMg --action-on-unmanage detachAll
  - name: Delete stack by stack resource id.
    text: az stack mg delete --id /providers/Microsoft.Management/managementGroups/myMg/providers/Microsoft.Resources/deploymentStacks/StackName --management-group-id myMg --action-on-unmanage deleteAll
"""

helps['stack sub'] = """
type: group
short-summary: Manage Deployment Stacks at subscription.
"""

helps['stack sub create'] = """
type: command
short-summary: Create or update a deployment stack at subscription scope
examples:
  - name: Create a deployment stack using template file and detach all resources on unmanage.
    text: az stack sub create --name StackName --template-file simpleTemplate.json --location westus2 --description description --deny-settings-mode None --action-on-unmanage detachAll
  - name: Create a deployment stack with parameter file and delete resources on unmanage.
    text: az stack sub create --name StackName --action-on-unmanage deleteResources --template-file simpleTemplate.json --parameters simpleTemplateParams.json --location westus2 --description description --deny-settings-mode None
  - name: Create a deployment stack with template spec.
    text: az stack sub create --name StackName --template-spec TemplateSpecResourceIDWithVersion --location westus2 --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack using bicep file and delete all resources on unmanage.
    text: az stack sub create --name StackName --action-on-unmanage deleteAll --template-file simple.bicep --location westus2 --description description --deny-settings-mode None
  - name: Create a deployment stack at a different subscription.
    text: az stack sub create --name StackName --template-file simpleTemplate.json --location westus2 --description description --subscription subscriptionId --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack and deploy at the resource group scope.
    text: az stack sub create --name StackName --template-file simpleTemplate.json --location westus --deployment-resource-group ResourceGroup --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack using parameters from key/value pairs.
    text: az stack sub create --name StackName --template-file simpleTemplate.json --location westus --description description --parameters simpleTemplateParams.json value1=foo value2=bar --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: az stack sub create --name StackName --template-file azuredeploy.json --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json --location westus --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, using deny settings.
    text: az stack sub create --name StackName --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-excluded-principals "test1 test2" --location westus --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, apply deny settings to child scopes.
    text: az stack sub create --name StackName --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-apply-to-child-scopes --location westus --action-on-unmanage deleteResources
"""

helps['stack sub validate'] = """
type: command
short-summary: Validate a deployment stack at subscription scope
examples:
  - name: Validate a deployment stack using template file and detach all resources on unmanage.
    text: az stack sub validate --name StackName --template-file simpleTemplate.json --location westus2 --description description --deny-settings-mode None --action-on-unmanage detachAll
  - name: Validate a deployment stack with parameter file and delete resources on unmanage.
    text: az stack sub validate --name StackName --action-on-unmanage deleteResources --template-file simpleTemplate.json --parameters simpleTemplateParams.json --location westus2 --description description --deny-settings-mode None
  - name: Validate a deployment stack with template spec.
    text: az stack sub validate --name StackName --template-spec TemplateSpecResourceIDWithVersion --location westus2 --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack using bicep file and delete all resources on unmanage.
    text: az stack sub validate --name StackName --action-on-unmanage deleteAll --template-file simple.bicep --location westus2 --description description --deny-settings-mode None
  - name: Validate a deployment stack at a different subscription.
    text: az stack sub validate --name StackName --template-file simpleTemplate.json --location westus2 --description description --subscription subscriptionId --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack and deploy at the resource group scope.
    text: az stack sub validate --name StackName --template-file simpleTemplate.json --location westus --deployment-resource-group ResourceGroup --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack using parameters from key/value pairs.
    text: az stack sub validate --name StackName --template-file simpleTemplate.json --location westus --description description --parameters simpleTemplateParams.json value1=foo value2=bar --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: az stack sub validate --name StackName --template-file azuredeploy.json --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json --location westus --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, using deny settings.
    text: az stack sub validate --name StackName --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-excluded-principals "test1 test2" --location westus --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, apply deny settings to child scopes.
    text: az stack sub validate --name StackName --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-apply-to-child-scopes --location westus --action-on-unmanage deleteResources
"""

helps['stack sub list'] = """
type: command
short-summary: List all deployment stacks in subscription
examples:
  - name: List all stacks
    text: az stack sub list
"""

helps['stack sub show'] = """
type: command
short-summary: Get specified deployment stack from subscription scope
examples:
  - name: Get stack by name.
    text: az stack sub show --name StackName
  - name: Get stack by stack resource id.
    text: az stack sub show --id /subscriptions/111111111111/providers/Microsoft.Resources/deploymentStacks/StackName
"""

helps['stack sub export'] = """
type: command
short-summary: Export the template used to create the deployment stack
examples:
  - name: Export template by name.
    text: az stack sub export --name StackName
  - name: Export template by stack resource id.
    text: az stack sub export --id /subscriptions/111111111111/providers/Microsoft.Resources/deploymentStacks/StackName
"""

helps['stack sub delete'] = """
type: command
short-summary: Delete specified deployment stack from subscription scope
examples:
  - name: Delete stack by name.
    text: az stack sub delete --name StackName --action-on-unmanage deleteResources
  - name: Delete stack by stack resource id.
    text: az stack sub delete --id /subscriptions/111111111111/providers/Microsoft.Resources/deploymentStacks/StackName --action-on-unmanage detachAll
"""

helps['stack group'] = """
type: group
short-summary: Manage Deployment Stacks at resource group.
"""

helps['stack group create'] = """
type: command
short-summary: Create or update a deployment stack at resource group scope
examples:
  - name: Create a deployment stack using template file and delete resources on unmanage.
    text: az stack group create --name StackName --resource-group ResourceGroup --action-on-unmanage deleteResources --template-file simpleTemplate.json --description description --deny-settings-mode None
  - name: Create a deployment stack with parameter file and detach all resources on unmanage.
    text: az stack group create --name StackName --resource-group ResourceGroup --action-on-unmanage detachAll --template-file simpleTemplate.json --parameters simpleTemplateParams.json --description description --deny-settings-mode None
  - name: Create a deployment stack with template spec and delete all resources on unmanage.
    text: az stack group create --name StackName --resource-group ResourceGroup --action-on-unmanage deleteAll --template-spec TemplateSpecResourceIDWithVersion --description description --deny-settings-mode None
  - name: Create a deployment stack using bicep file.
    text: az stack group create --name StackName --resource-group ResourceGroup --template-file simple.bicep --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack at a different subscription.
    text: az stack group create --name StackName --resource-group ResourceGroup --template-file simpleTemplate.json --description description --subscription subscriptionId --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack using parameters from key/value pairs.
    text: az stack group create --name StackName --template-file simpleTemplate.json --resource-group ResourceGroup --description description --parameters simpleTemplateParams.json value1=foo value2=bar --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: az stack group create --name StackName --template-file azuredeploy.json --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json --resource-group ResourceGroup --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, using deny settings.
    text: az stack group create --name StackName --resource-group ResourceGroup --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-excluded-principals "test1 test2" --action-on-unmanage deleteResources
  - name: Create a deployment stack from a local template, apply deny setting to child scopes.
    text: az stack group create --name StackName --resource-group ResourceGroup --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-apply-to-child-scopes --action-on-unmanage deleteResources
"""

helps['stack group validate'] = """
type: command
short-summary: Validate a deployment stack at resource group scope
examples:
  - name: Validate a deployment stack using template file and delete resources on unmanage.
    text: az stack group validate --name StackName --resource-group ResourceGroup --action-on-unmanage deleteResources --template-file simpleTemplate.json --description description --deny-settings-mode None
  - name: Validate a deployment stack with parameter file and detach all resources on unmanage.
    text: az stack group validate --name StackName --resource-group ResourceGroup --action-on-unmanage detachAll --template-file simpleTemplate.json --parameters simpleTemplateParams.json --description description --deny-settings-mode None
  - name: Validate a deployment stack with template spec and delete all resources on unmanage.
    text: az stack group validate --name StackName --resource-group ResourceGroup --action-on-unmanage deleteAll --template-spec TemplateSpecResourceIDWithVersion --description description --deny-settings-mode None
  - name: Validate a deployment stack using bicep file.
    text: az stack group validate --name StackName --resource-group ResourceGroup --template-file simple.bicep --description description --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack at a different subscription.
    text: az stack group validate --name StackName --resource-group ResourceGroup --template-file simpleTemplate.json --description description --subscription subscriptionId --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack using parameters from key/value pairs.
    text: az stack group validate --name StackName --template-file simpleTemplate.json --resource-group ResourceGroup --description description --parameters simpleTemplateParams.json value1=foo value2=bar --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: az stack group validate --name StackName --template-file azuredeploy.json --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json --resource-group ResourceGroup --deny-settings-mode None --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, using deny settings.
    text: az stack group validate --name StackName --resource-group ResourceGroup --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-excluded-principals "test1 test2" --action-on-unmanage deleteResources
  - name: Validate a deployment stack from a local template, apply deny setting to child scopes.
    text: az stack group validate --name StackName --resource-group ResourceGroup --template-file azuredeploy.json --deny-settings-mode denyDelete --deny-settings-excluded-actions Microsoft.Compute/virtualMachines/write --deny-settings-apply-to-child-scopes --action-on-unmanage deleteResources
"""

helps['stack group list'] = """
type: command
short-summary: List all deployment stacks in resource group
examples:
  - name: List all stacks in resource group
    text: az stack group list --resource-group ResourceGroup
"""

helps['stack group show'] = """
type: command
short-summary: Get specified deployment stack from resource group scope
examples:
  - name: Get stack by name.
    text: az stack group show --name StackName --resource-group ResourceGroup
  - name: Get stack by stack resource id.
    text: az stack group show --id /subscriptions/111111111111/resourceGroups/ResourceGroup/providers/Microsoft.Resources/deploymentStacks/StackName
"""

helps['stack group export'] = """
type: command
short-summary: Export the template used to create the deployment stack from resource group scope
examples:
  - name: Export template by name.
    text: az stack group export --name StackName --resource-group ResourceGroup
  - name: Export template by stack resource id.
    text: az stack group export --id /subscriptions/111111111111/resourceGroups/ResourceGroup/providers/Microsoft.Resources/deploymentStacks/StackName
"""

helps['stack group delete'] = """
type: command
short-summary: Delete specified deployment stack from resource group scope
examples:
  - name: Delete stack by name.
    text: az stack group delete --name StackName --resource-group ResourceGroup --action-on-unmanage deleteResources
  - name: Delete stack by stack resource id.
    text: az stack group delete --id /subscriptions/111111111111/resourceGroups/ResourceGroup/providers/Microsoft.Resources/deploymentStacks/StackName --action-on-unmanage detachAll
"""

helps['bicep generate-params'] = """
type: command
short-summary: Generate parameters file for a Bicep file.
examples:
  - name: Generate parameters file for a Bicep file.
    text: az bicep generate-params --file {bicep_file}
  - name: Generate parameters file for a Bicep file and print all output to stdout.
    text: az bicep generate-params --file {bicep_file} --stdout
  - name: Generate parameters file for a Bicep file and save the result to the specified directory.
    text: az bicep generate-params --file {bicep_file} --outdir {out_dir}
  - name: Generate parameters file for a Bicep file and save the result to the specified file.
    text: az bicep generate-params --file {bicep_file} --outfile {out_file}
  - name: Generate parameters file for a Bicep file without restoring external modules.
    text: az bicep generate-params --file {bicep_file} --no-restore
  - name: Generate parameters file for a Bicep file with specified output format. Valid values are ( json | bicepparam ).
    text: az bicep generate-params --file {bicep_file} --output-format {output_format} --include-params {include_params}
"""

helps['bicep lint'] = """
type: command
short-summary: Lint a Bicep file.
examples:
  - name: Lint a Bicep file.
    text: az bicep lint --file {bicep_file}
  - name: Lint a Bicep file without restoring external modules.
    text: az bicep lint --file {bicep_file} --no-restore
  - name: Lint a Bicep file with specified diagnostics format. Valid values are ( default | sarif ).
    text: az bicep lint --file {bicep_file} --diagnostics-format {diagnostics_format}
"""

helps['resourcemanagement'] = """
type: group
short-summary: resourcemanagement CLI command group.
"""
helps['resourcemanagement private-link'] = """
type: group
short-summary: resourcemanagement private-link management on a resource.
"""
helps['private-link'] = """
type: group
short-summary: private-link association CLI command group.
"""
helps['private-link association'] = """
type: group
short-summary: private-link association management on a resource.
"""

helps['resourcemanagement private-link create'] = """
type: command
short-summary: Create a resource management group private link.
examples:
  - name: Create a resource management group private link.
    text: az resourcemanagement private-link create --resource-group testRG --name TestRMPL --location WestUS
"""
helps['resourcemanagement private-link show'] = """
type: command
short-summary: Get resource management private.
examples:
  - name: Get single resource management private link.
    text: az resourcemanagement private-link show --resource-group testRG --name TestRMPL
"""
helps['resourcemanagement private-link list'] = """
type: command
short-summary: Get all the resource management private links at scope.
examples:
  - name: List all resource management private links in a subscription.
    text: az resourcemanagement private-link list
  - name: List all resource management private links in a resource group.
    text: az resourcemanagement private-link list --resource-group testRG
"""
helps['resourcemanagement private-link delete'] = """
type: command
short-summary: Delete a resource management private link.
examples:
  - name: Delete a resource management private link.
    text: az resourcemanagement private-link delete --resource-group TestRG --name testRMPL
"""
helps['private-link association create'] = """
type: command
short-summary: Create a PrivateLinkAssociation.
examples:
  - name: Create a PrivateLinkAssociation.
    text: az private-link association create --management-group-id TestMG --name testPLA --privatelink testPL --public-network-access enabled
"""
helps['private-link association show'] = """
type: command
short-summary: Get a private link association.
examples:
  - name: Get a single private link association.
    text: az private-link association show --management-group-id TestMG --name testPLA
"""
helps['private-link association list'] = """
type: command
short-summary: Get a private link association for a management group scope.
examples:
  - name: Get a private link association for a management group scope.
    text: az private-link association list --management-group-id TestMG
"""
helps['private-link association delete'] = """
type: command
short-summary: Delete a PrivateLinkAssociation.
examples:
  - name: Delete a PrivateLinkAssociation.
    text: az private-link association delete --management-group-id TestMG --name testPLA
"""

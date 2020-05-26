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

helps['account management-group subscription'] = """
type: group
short-summary: Subscription operations for Management Groups.
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
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
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
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when --confirm-with-what-if is set.
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
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
examples:
  - name: Validate whether a template is valid at subscription scope.
    text: az deployment sub validate --location westus2 --template-file {template-file}
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
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
  - name: --name -n
    short-summary: The deployment name.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when --confirm-with-what-if is set.
examples:
  - name: Create a deployment at subscription scope from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment sub create --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at subscription scope from a local template file, using parameters from a JSON string.
    text: |
        az deployment sub create --location WestUS --template-file azuredeploy.json --parameters '{
                "policyName": {
                    "value": "policy2"
                }
            }'
  - name: Create a deployment at subscription scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment sub create --location WestUS --template-file azuredeploy.json  \\
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
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
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
"""

helps['deployment operation sub'] = """
type: group
short-summary: Manage deployment operations at subscription scope.
"""

helps['deployment operation sub list'] = """
type: command
short-summary: List deployment operations at subscription scope.
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
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --resource-group -g
    short-summary: The resource group to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --mode
    short-summary: The deployment mode.
examples:
  - name: Validate whether a template is valid at resource group.
    text: az deployment group validate --resource-group testrg --template-file {template-file}
"""

helps['deployment group create'] = """
type: command
short-summary: Start a deployment at resource group.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --resource-group -g
    short-summary: The resource group to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --mode
    short-summary: The deployment mode.
  - name: --what-if-result-format -r
    short-summary: The format of What-If results. Applicable when --confirm-with-what-if is set.
examples:
  - name: Create a deployment at resource group from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment group create --resource-group testrg --name rollout01 --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at resource group from a local template file, using parameters from a JSON string.
    text: |
        az deployment group create --resource-group testrg --name rollout01 --template-file azuredeploy.json --parameters '{
                "policyName": {
                    "value": "policy2"
                }
            }'
  - name: Create a deployment at resource group from a local template file, using parameters from an array string.
    text: |
      az deployment group create --resource-group testgroup --template-file demotemplate.json --parameters exampleString='inline string' exampleArray='("value1", "value2")'
  - name: Create a deployment at resource group from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment group create --resource-group testrg --name rollout01 --template-file azuredeploy.json  \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
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
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
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
"""

helps['deployment operation group'] = """
type: group
short-summary: Manage deployment operations at resource group.
"""

helps['deployment operation group list'] = """
type: command
short-summary: List deployment operations at resource group.
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
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --management-group-id -m
    short-summary: The management group id to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
examples:
  - name: Validate whether a template is valid at management group.
    text: az deployment mg validate --management-group-id testmg --location WestUS --template-file {template-file}
"""

helps['deployment mg create'] = """
type: command
short-summary: Start a deployment at management group.
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --management-group-id -m
    short-summary: The management group id to create deployment at.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
examples:
  - name: Create a deployment at management group from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment mg create --management-group-id testrg --name rollout01 --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at management group from a local template file, using parameters from a JSON string.
    text: |
        az deployment mg create --management-group-id testmg --name rollout01 --location WestUS --template-file azuredeploy.json --parameters '{
                "policyName": {
                    "value": "policy2"
                }
            }'
  - name: Create a deployment at management group from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment mg create --management-group-id testmg --name rollout01 --location WestUS --template-file azuredeploy.json  \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
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
parameters:
  - name: --parameters -p
    short-summary: Supply deployment parameter values.
    long-summary: >
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
        It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
  - name: --template-file -f
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
examples:
  - name: Validate whether a template is valid at tenant scope.
    text: az deployment tenant validate --location WestUS --template-file {template-file}
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
    short-summary: The path to the template file.
  - name: --template-uri -u
    short-summary: The URI to the template file.
  - name: --name -n
    short-summary: The deployment name.
  - name: --location -l
    short-summary: The location to store the deployment metadata.
examples:
  - name: Create a deployment at tenant scope from a remote template file, using parameters from a local JSON file.
    text: >
        az deployment tenant create --name rollout01 --location WestUS --template-uri https://myresource/azuredeploy.json --parameters @myparameters.json
  - name: Create a deployment at tenant scope from a local template file, using parameters from a JSON string.
    text: |
        az deployment tenant create --name rollout01 --location WestUS --template-file azuredeploy.json --parameters '{
                "policyName": {
                    "value": "policy2"
                }
            }'
  - name: Create a deployment at tenant scope from a local template, using a parameter file, a remote parameter file, and selectively overriding key/value pairs.
    text: >
        az deployment tenant create --name rollout01 --location WestUS --template-file azuredeploy.json  \\
            --parameters @params.json --parameters https://mysite/params.json --parameters MyValue=This MyArray=@array.json
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
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used.
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
long-summary: 'Locks can exist at three different scopes: subscription, resource group and resource.'
examples:
  - name: Create a read-only subscription level lock.
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
        az managedapp delete --name MyManagedApplication --resource-group MyResourceGroup
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
    text: |
        Valid scopes are management group, subscription, resource group, and resource, for example
           management group:  /providers/Microsoft.Management/managementGroups/MyManagementGroup
           subscription:      /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333
           resource group:    /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup
           resource:          /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM
             az policy assignment create --scope \\
                "/providers/Microsoft.Management/managementGroups/MyManagementGroup" \\
                    --policy {PolicyName} -p "{ \\"allowedLocations\\": \\
                        { \\"value\\": [ \\"australiaeast\\", \\"eastus\\", \\"japaneast\\" ] } }"
  - name: Create a resource policy assignment and provide rule parameter values.
    text: |
        az policy assignment create --policy {PolicyName} -p "{ \\"allowedLocations\\": \\
            { \\"value\\": [ \\"australiaeast\\", \\"eastus\\", \\"japaneast\\" ] } }"
  - name: Create a resource policy assignment with a system assigned identity.
    text: >
        az policy assignment create --name myPolicy --policy {PolicyName} --assign-identity
  - name: Create a resource policy assignment with a system assigned identity. The identity will have 'Contributor' role access to the subscription.
    text: >
        az policy assignment create --name myPolicy --policy {PolicyName} --assign-identity --identity-scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx --role Contributor
  - name: Create a resource policy assignment with an enforcement mode. It indicates whether a policy effect will be enforced or not during assignment creation and update. Please visit https://aka.ms/azure-policyAssignment-enforcement-mode for more information.
    text: >
        az policy assignment create --name myPolicy --policy {PolicyName} --enforcement-mode 'DoNotEnforce'
"""

helps['policy assignment delete'] = """
type: command
short-summary: Delete a resource policy assignment.
examples:
  - name: Delete a resource policy assignment. (autogenerated)
    text: |
        az policy assignment delete --name MyPolicyAssignment
    crafted: true
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
        az policy assignment identity assign -g MyResourceGroup -n MyPolicyAssignment
  - name: Add a system assigned managed identity to a policy assignment and grant it the 'Contributor' role for the current resource group.
    text: >
        az policy assignment identity assign -g MyResourceGroup -n MyPolicyAssignment --role Contributor --identity-scope /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/MyResourceGroup
"""

helps['policy assignment identity remove'] = """
type: command
short-summary: Remove a managed identity from a policy assignment.
"""

helps['policy assignment identity show'] = """
type: command
short-summary: Show a policy assignment's managed identity.
examples:
  - name: Show a policy assignment's managed identity. (autogenerated)
    text: |
        az policy assignment identity show --name MyPolicyAssignment --scope '/providers/Microsoft.Management/managementGroups/MyManagementGroup'
    crafted: true
"""

helps['policy assignment list'] = """
type: command
short-summary: List resource policy assignments.
"""

helps['policy assignment show'] = """
type: command
short-summary: Show a resource policy assignment.
examples:
  - name: Show a resource policy assignment. (autogenerated)
    text: |
        az policy assignment show --name MyPolicyAssignment
    crafted: true
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
    text: |
        az policy definition create --name readOnlyStorage --rules "{ \\"if\\": \\
            { \\"field\\": \\"type\\", \\"equals\\": \\"Microsoft.Storage/storageAccounts/write\\" }, \\
                \\"then\\": { \\"effect\\": \\"deny\\" } }"
  - name: Create a policy parameter definition.
    text: |
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
    text: |
        az policy definition create -n readOnlyStorage --management-group "MyManagementGroup" \\
            --rules "{ \\"if\\": { \\"field\\": \\"type\\", \\
                \\"equals\\": \\"Microsoft.Storage/storageAccounts/write\\" }, \\
                    \\"then\\": { \\"effect\\": \\"deny\\" } }"
  - name: Create a policy definition with mode. The mode 'Indexed' indicates the policy should be evaluated only for resource types that support tags and location.
    text: |
        az policy definition create --name TagsPolicyDefinition --subscription "MySubscription" \\
            --mode Indexed --rules "{ \\"if\\": { \\"field\\": \\"tags\\", \\"exists\\": \\"false\\" }, \\
                \\"then\\": { \\"effect\\": \\"deny\\" } }"
"""

helps['policy definition delete'] = """
type: command
short-summary: Delete a policy definition.
examples:
  - name: Delete a policy definition. (autogenerated)
    text: |
        az policy definition delete --name MyPolicyDefinition
    crafted: true
"""

helps['policy definition list'] = """
type: command
short-summary: List policy definitions.
"""

helps['policy definition show'] = """
type: command
short-summary: Show a policy definition.
examples:
  - name: Show a policy definition. (autogenerated)
    text: |
        az policy definition show --name MyPolicyDefinition
    crafted: true
"""

helps['policy definition update'] = """
type: command
short-summary: Update a policy definition.
examples:
  - name: Update a policy definition. (autogenerated)
    text: |
        az policy definition update --name MyPolicyDefinition
    crafted: true
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
    text: |
        az policy set-definition create -n readOnlyStorage \\
            --definitions "[ { \\"policyDefinitionId\\": \\"/subscriptions/mySubId/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\", \\"parameters\\": \\
                    { \\"storageSku\\": { \\"value\\": \\"[parameters(\\\\"requiredSku\\\\")]\\" } } }]" \\
            --params "{ \\"requiredSku\\": { \\"type\\": \\"String\\" } }"
  - name: Create a policy set definition with parameters.
    text: |
        az policy set-definition create -n readOnlyStorage --definitions '[
                { "policyDefinitionId": "/subscriptions/mySubId/providers/Microsoft.Authorization/policyDefinitions/storagePolicy" }
            ]'
  - name: Create a policy set definition in a subscription.
    text: |
        az policy set-definition create -n readOnlyStorage --subscription '0b1f6471-1bf0-4dda-aec3-111122223333' --definitions '[
                { "policyDefinitionId": "/subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/providers/Microsoft.Authorization/policyDefinitions/storagePolicy" }
            ]'
  - name: Create a policy set definition with policy definition groups.
    text: |
        az policy set-definition create -n computeRequirements \\
            --definitions "[ { \\"policyDefinitionId \\": \\"/subscriptions/mySubId/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\", \\"groupNames\\": \\
                    [ \\"CostSaving\\", \\"Organizational\\" ] }, { \\"policyDefinitionId\\": \\
                        \\"/subscriptions/mySubId/providers/Microsoft.Authorization/ \\
                            policyDefinitions/tagPolicy\\", \\"groupNames\\": [ \\
                                \\"Organizational\\" ] } ]" \\
            --definition-groups "[{ \\"name\\": \\"CostSaving\\" }, { \\"name\\": \\"Organizational\\" } ]"
"""

helps['policy set-definition delete'] = """
type: command
short-summary: Delete a policy set definition.
examples:
  - name: Delete a policy set definition. (autogenerated)
    text: |
        az policy set-definition delete --management-group myMg --name MyPolicySetDefinition
    crafted: true
"""

helps['policy set-definition list'] = """
type: command
short-summary: List policy set definitions.
"""

helps['policy set-definition show'] = """
type: command
short-summary: Show a policy set definition.
examples:
  - name: Show a policy set definition. (autogenerated)
    text: |
        az policy set-definition show --name MyPolicySetDefinition
    crafted: true
"""

helps['policy set-definition update'] = """
type: command
short-summary: Update a policy set definition.
examples:
  - name: Update a policy set definition.
    text: |-
        az policy set-definition update --definitions '[
                { "policyDefinitionId": "/subscriptions/mySubId/providers/Microsoft.Authorization/policyDefinitions/storagePolicy" }
            ]' --name MyPolicySetDefinition
  - name: Update the groups and definitions within a policy set definition.
    text: |
        az policy set-definition update -n computeRequirements \\
            --definitions "[ { \\"policyDefinitionId\\": \\"/subscriptions/mySubId/providers/ \\
                Microsoft.Authorization/policyDefinitions/storagePolicy\\", \\"groupNames\\": [ \\
                    \\"CostSaving\\", \\"Organizational\\" ] }, { \\"policyDefinitionId\\": \\
                        \\"/subscriptions/mySubId/providers/Microsoft.Authorization/ \\
                            policyDefinitions/tagPolicy\\", \\
                                \\"groupNames\\": [ \\"Organizational\\" ] } ]" \\
            --definition-groups "[{ \\"name\\": \\"CostSaving\\" }, { \\"name\\": \\"Organizational\\" } ]"
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
"""

helps['resource invoke-action'] = """
type: command
short-summary: Invoke an action on the resource.
long-summary: >
    A list of possible actions corresponding to a resource can be found at https://docs.microsoft.com/rest/api/. All POST requests are actions that can be invoked and are specified at the end of the URI path. For instance, to stop a VM, the
    request URI is https://management.azure.com/subscriptions/{SubscriptionId}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VM}/powerOff?api-version={APIVersion} and the corresponding action is `powerOff`. This can
    be found at https://docs.microsoft.com/rest/api/compute/virtualmachines/virtualmachines-stop.
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
"""

helps['resource update'] = """
type: command
short-summary: Update a resource.
examples:
  - name: Update a resource. (autogenerated)
    text: |
        az resource update --ids $id --set properties.connectionType=Proxy
    crafted: true
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

helps['rest'] = """
type: command
short-summary: Invoke a custom request.
long-summary: >
    This command automatically authenticates using the credential logged in: If Authorization header is not set, it
    attaches header `Authorization: Bearer <token>`, where `<token>` is retrieved from AAD. The target resource of the
    token is derived from --url if --url starts with an endpoint from `az cloud show --query endpoints`. You may also
    use --resource for a custom resource.

    If Content-Type header is not set and --body is a valid JSON string, Content-Type header will default to
    application/json.
examples:
  - name: Get Audit log through Microsoft Graph
    text: >
        az rest --method get --uri https://graph.microsoft.com/beta/auditLogs/directoryAudits
  - name: Update a Azure Active Directory Graph User's display name
    text: >
        az rest --method patch --uri "https://graph.microsoft.com/v1.0/users/johndoe@azuresdkteam.onmicrosoft.com" --body "{\\"displayName\\": \\"jondoe2\\"}"
  - name: Get a virtual machine
    text: >
        az rest --method get --uri /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Compute/virtualMachines/{vmName}?api-version=2019-03-01
  - name: Create a public IP address from body.json file
    text: >
        az rest --method put --uri https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/publicIPAddresses/{publicIpAddressName}?api-version=2019-09-01 --body @body.json
"""

helps['tag'] = """
type: group
short-summary: Manage resource tags.
"""

helps['version'] = """
type: command
short-summary: Show the versions of Azure CLI modules and extensions in JSON format by default or format configured by --output
"""

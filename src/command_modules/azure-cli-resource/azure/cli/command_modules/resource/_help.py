# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["policy assignment delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a resource policy assignment.
"""

helps["account lock"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure subscription level locks.
"""

helps["deployment operation"] = """
"type": |-
    group
"short-summary": |-
    Manage deployment operations.
"""

helps["feature register"] = """
"type": |-
    command
"short-summary": |-
    register a preview feature.
"examples":
-   "name": |-
        Register a preview feature.
    "text": |-
        az feature register --namespace <namespace> --name MyFeature
"""

helps["account management-group subscription add"] = """
"type": |-
    command
"short-summary": |-
    Add a subscription to a management group.
"long-summary": |-
    Add a subscription to a management group.
"parameters":
-   "name": |-
        --name -n
    "type": |-
        string
    "short-summary": |-
        Name of the management group.
-   "name": |-
        --subscription -s
    "type": |-
        string
    "short-summary": |-
        Subscription Id or Name
"""

helps["group update"] = """
"type": |-
    command
"short-summary": |-
    Update a resource group.
"examples":
-   "name": |-
        Update a resource group.
    "text": |-
        az group update --set <set> --name MyResourceGroup
"""

helps["resource link show"] = """
"type": |-
    command
"short-summary": |-
    Get details for a resource link.
"long-summary": |-
    A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
"""

helps["policy definition create"] = """
"type": |-
    command
"short-summary": |-
    Create a policy definition.
"parameters":
-   "name": |-
        --rules
    "type": |-
        string
    "short-summary": |-
        Policy rules in JSON format, or a path to a file containing JSON rules.
-   "name": |-
        --management-group
    "type": |-
        string
    "short-summary": |-
        Name of the management group the new policy definition can be assigned in.
-   "name": |-
        --subscription
    "type": |-
        string
    "short-summary": |-
        Name or id of the subscription the new policy definition can be assigned in.
"""

helps["managedapp delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a managed application.
"""

helps["group lock"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure resource group locks.
"""

helps["group deployment"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Resource Manager deployments.
"""

helps["policy set-definition delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a policy set definition.
"""

helps["policy set-definition show"] = """
"type": |-
    command
"short-summary": |-
    Show a policy set definition.
"""

helps["provider list"] = """
"type": |-
    command
"examples":
-   "name": |-
        Gets all resource providers for a subscription.
    "text": |-
        az provider list --output json
"""

helps["group deployment create"] = """
"type": |-
    command
"short-summary": |-
    Start a deployment.
"parameters":
-   "name": |-
        --parameters
    "short-summary": |-
        Supply deployment parameter values.
    "long-summary": |
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used. It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
"examples":
-   "name": |-
        Start a deployment.
    "text": |-
        az group deployment create --template-file <template-file> --parameters @myparameters.json --resource-group MyResourceGroup --name MyDeployment
"""

helps["account management-group show"] = """
"type": |-
    command
"short-summary": |-
    Get a specific management group.
"long-summary": |-
    Get the details of the management group.
"parameters":
-   "name": |-
        --name -n
    "type": |-
        string
    "short-summary": |-
        Name of the management group.
-   "name": |-
        --expand -e
    "type": |-
        bool
    "short-summary": |-
        If given, lists the children in the first level of hierarchy.
-   "name": |-
        --recurse -r
    "type": |-
        bool
    "short-summary": |-
        If given, lists the children in all levels of hierarchy.
"""

helps["managedapp definition delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a managed application definition.
"""

helps["resource lock show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a resource-level lock
"""

helps["group exists"] = """
"type": |-
    command
"short-summary": |-
    Check if a resource group exists.
"examples":
-   "name": |-
        Check if a resource group exists.
    "text": |-
        az group exists --name MyResourceGroup
"""

helps["deployment export"] = """
"type": |-
    command
"short-summary": |-
    Export the template used for a deployment.
"""

helps["group delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a resource group.
"examples":
-   "name": |-
        Delete a resource group.
    "text": |-
        az group delete --no-wait  --yes  --name MyResourceGroup
"""

helps["account management-group"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Management Groups.
"""

helps["tag"] = """
"type": |-
    group
"short-summary": |-
    Manage resource tags.
"""

helps["provider operation list"] = """
"type": |-
    command
"short-summary": |-
    Get operations from all providers.
"""

helps["policy definition delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a policy definition.
"""

helps["provider"] = """
"type": |-
    group
"short-summary": |-
    Manage resource providers.
"""

helps["provider register"] = """
"type": |-
    command
"short-summary": |-
    Register a provider.
"examples":
-   "name": |-
        Register a provider.
    "text": |-
        az provider register --namespace <namespace>
"""

helps["account lock delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a subscription lock.
"""

helps["policy definition"] = """
"type": |-
    group
"short-summary": |-
    Manage resource policy definitions.
"""

helps["resource lock create"] = """
"type": |-
    command
"short-summary": |-
    Create a resource-level lock.
"""

helps["resource invoke-action"] = """
"type": |-
    command
"short-summary": |-
    Invoke an action on the resource.
"long-summary": |
    A list of possible actions corresponding to a resource can be found at https://docs.microsoft.com/en-us/rest/api/. All POST requests are actions that can be invoked and are specified at the end of the URI path. For instance, to stop a VM, the request URI is https://management.azure.com/subscriptions/{SubscriptionId}/resourceGroups/{ResourceGroup}/providers/Microsoft.Compute/virtualMachines/{VM}/powerOff?api-version={APIVersion} and the corresponding action is `powerOff`. This can be found at https://docs.microsoft.com/en-us/rest/api/compute/virtualmachines/virtualmachines-stop.
"""

helps["deployment"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Resource Manager deployments at subscription scope.
"""

helps["deployment validate"] = """
"type": |-
    command
"short-summary": |-
    Validate whether a template is syntactically correct.
"parameters":
-   "name": |-
        --parameters
    "short-summary": |-
        Supply deployment parameter values.
    "long-summary": |
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used. It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
"""

helps["group list"] = """
"type": |-
    command
"short-summary": |-
    List resource groups.
"""

helps["account lock list"] = """
"type": |-
    command
"short-summary": |-
    List lock information in the subscription.
"""

helps["provider unregister"] = """
"type": |-
    command
"short-summary": |-
    Unregister a provider.
"""

helps["group deployment wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a deployment condition is met.
"""

helps["policy assignment create"] = """
"type": |-
    command
"short-summary": |-
    Create a resource policy assignment.
"parameters":
-   "name": |-
        --scope
    "type": |-
        string
    "short-summary": |-
        Scope to which this policy assignment applies.
"""

helps["feature"] = """
"type": |-
    group
"short-summary": |-
    Manage resource provider features.
"""

helps["resource delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a resource.
"examples":
-   "name": |-
        Delete a resource.
    "text": |-
        az resource delete --ids /subscriptions/0b1f6471-1bf0-4dda-aec3-111111111111/resourceGroups/MyResourceGroup/providers/Microsoft.Web/sites/MyWebapp
"""

helps["resource lock update"] = """
"type": |-
    command
"short-summary": |-
    Update a resource-level lock.
"""

helps["resource lock"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure resource level locks.
"""

helps["resource link create"] = """
"type": |-
    command
"short-summary": |-
    Create a new link between resources.
"long-summary": |-
    A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
"""

helps["resource tag"] = """
"type": |-
    command
"short-summary": |-
    Tag a resource.
"""

helps["account lock create"] = """
"type": |-
    command
"short-summary": |-
    Create a subscription lock.
"""

helps["policy set-definition list"] = """
"type": |-
    command
"short-summary": |-
    List policy set definitions.
"""

helps["account management-group create"] = """
"type": |-
    command
"short-summary": |-
    Create a new management group.
"long-summary": |-
    Create a new management group.
"parameters":
-   "name": |-
        --name -n
    "type": |-
        string
    "short-summary": |-
        Name of the management group.
-   "name": |-
        --display-name -d
    "type": |-
        string
    "short-summary": |-
        Sets the display name of the management group. If null, the group name is set as the display name.
-   "name": |-
        --parent -p
    "type": |-
        string
    "short-summary": |-
        Sets the parent of the management group. Can be the fully qualified id or the name of the management group. If null, the root tenant group is set as the parent.
"""

helps["account management-group subscription remove"] = """
"type": |-
    command
"short-summary": |-
    Remove an existing subscription from a management group.
"long-summary": |-
    Remove an existing subscription from a management group.
"parameters":
-   "name": |-
        --name -n
    "type": |-
        string
    "short-summary": |-
        Name of the management group.
-   "name": |-
        --subscription -s
    "type": |-
        string
    "short-summary": |-
        Subscription Id or Name
"""

helps["group create"] = """
"type": |-
    command
"short-summary": |-
    Create a new resource group.
"examples":
-   "name": |-
        Create a new resource group.
    "text": |-
        az group create --location westus --name MyResourceGroup
"""

helps["resource lock delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a resource-level lock.
"""

helps["resource show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a resource.
"examples":
-   "name": |-
        Get the details of a resource.
    "text": |-
        az resource show --resource-group MyResourceGroup --resource-type "Microsoft.Compute/virtualMachines" --name MyVm
"""

helps["policy"] = """
"type": |-
    group
"short-summary": |-
    Manage resource policies.
"""

helps["resource"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure resources.
"""

helps["lock list"] = """
"type": |-
    command
"short-summary": |-
    List lock information.
"""

helps["account management-group update"] = """
"type": |-
    command
"short-summary": |-
    Update an existing management group.
"long-summary": |-
    Update an existing management group.
"parameters":
-   "name": |-
        --name -n
    "type": |-
        string
    "short-summary": |-
        Name of the management group.
-   "name": |-
        --display-name -d
    "type": |-
        string
    "short-summary": |-
        Updates the display name of the management group. If null, no change is made.
-   "name": |-
        --parent -p
    "type": |-
        string
    "short-summary": |-
        Update the parent of the management group. Can be the fully qualified id or the name of the management group. If null, no change is made.
"""

helps["lock delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a lock.
"examples":
-   "name": |-
        Delete a lock.
    "text": |-
        az lock delete --resource-group group --name lockName
"""

helps["group"] = """
"type": |-
    group
"short-summary": |-
    Manage resource groups and template deployments.
"""

helps["resource update"] = """
"type": |-
    command
"short-summary": |-
    Update a resource.
"examples":
-   "name": |-
        Update a resource.
    "text": |-
        az resource update --ids <ids> --set <set> --api-version <api-version>
"""

helps["policy definition show"] = """
"type": |-
    command
"short-summary": |-
    Show a policy definition.
"""

helps["group wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of the resource group is met.
"""

helps["group lock delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a resource group lock.
"""

helps["policy set-definition update"] = """
"type": |-
    command
"short-summary": |-
    Update a policy set definition.
"""

helps["group deployment validate"] = """
"type": |-
    command
"short-summary": |-
    Validate whether a template is syntactically correct.
"parameters":
-   "name": |-
        --parameters
    "short-summary": |-
        Supply deployment parameter values.
    "long-summary": |
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used. It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
"examples":
-   "name": |-
        Validate whether a template is syntactically correct.
    "text": |-
        az group deployment validate --template-file <template-file> --parameters <parameters> --resource-group MyResourceGroup
"""

helps["policy assignment list"] = """
"type": |-
    command
"short-summary": |-
    List resource policy assignments.
"""

helps["group lock list"] = """
"type": |-
    command
"short-summary": |-
    List lock information in the resource-group.
"""

helps["provider operation show"] = """
"type": |-
    command
"short-summary": |-
    Get an individual provider's operations.
"""

helps["group deployment export"] = """
"type": |-
    command
"short-summary": |-
    Export the template used for a deployment.
"""

helps["resource link delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a link between resources.
"long-summary": |-
    A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroupID}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
"""

helps["group lock create"] = """
"type": |-
    command
"short-summary": |-
    Create a resource group lock.
"""

helps["policy set-definition"] = """
"type": |-
    group
"short-summary": |-
    Manage resource policy set definitions.
"""

helps["policy definition update"] = """
"type": |-
    command
"short-summary": |-
    Update a policy definition.
"""

helps["resource list"] = """
"type": |-
    command
"short-summary": |-
    List resources.
"examples":
-   "name": |-
        List resources.
    "text": |-
        az resource list --resource-group MyResourceGroup
"""

helps["group lock update"] = """
"type": |-
    command
"short-summary": |-
    Update a resource group lock.
"""

helps["resource create"] = """
"type": |-
    command
"short-summary": |-
    create a resource.
"""

helps["managedapp"] = """
"type": |-
    group
"short-summary": |-
    Manage template solutions provided and maintained by Independent Software Vendors (ISVs).
"""

helps["policy assignment"] = """
"type": |-
    group
"short-summary": |-
    Manage resource policy assignments.
"""

helps["managedapp create"] = """
"type": |-
    command
"short-summary": |-
    Create a managed application.
"""

helps["account management-group list"] = """
"type": |-
    command
"short-summary": |-
    List all management groups.
"long-summary": |-
    List of all management groups in the current tenant.
"""

helps["resource wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a condition of a resources is met.
"""

helps["policy set-definition create"] = """
"type": |-
    command
"short-summary": |-
    Create a policy set definition.
"parameters":
-   "name": |-
        --definitions
    "type": |-
        string
    "short-summary": |-
        Policy definitions in JSON format, or a path to a file containing JSON rules.
-   "name": |-
        --management-group
    "type": |-
        string
    "short-summary": |-
        Name of management group the new policy set definition can be assigned in.
-   "name": |-
        --subscription
    "type": |-
        string
    "short-summary": |-
        Name or id of the subscription the new policy set definition can be assigned in.
"""

helps["lock update"] = """
"type": |-
    command
"short-summary": |-
    Update a lock.
"""

helps["managedapp definition"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure Managed Applications.
"""

helps["deployment create"] = """
"type": |-
    command
"short-summary": |-
    Start a deployment.
"parameters":
-   "name": |-
        --parameters
    "short-summary": |-
        Supply deployment parameter values.
    "long-summary": |
        Parameters may be supplied from a file using the `@{path}` syntax, a JSON string, or as <KEY=VALUE> pairs. Parameters are evaluated in order, so when a value is assigned twice, the latter value will be used. It is recommended that you supply your parameters file first, and then override selectively using KEY=VALUE syntax.
"examples":
-   "name": |-
        Start a deployment.
    "text": |-
        az deployment create --template-file <template-file> --location WestUS
"""

helps["managedapp definition create"] = """
"type": |-
    command
"short-summary": |-
    Create a managed application definition.
"""

helps["resource link"] = """
"type": |-
    group
"short-summary": |-
    Manage links between resources.
"long-summary": |
    Linking is a feature of the Resource Manager. It enables declaring relationships between resources even if they do not reside in the same resource group. Linking has no impact on resource usage, no impact on billing, and no impact on role-based access. It allows for managing multiple resources across groups as a single unit.
"""

helps["account management-group subscription"] = """
"type": |-
    group
"short-summary": |-
    Subscription operations for Management Groups.
"""

helps["resource lock list"] = """
"type": |-
    command
"short-summary": |-
    List lock information in the resource-level.
"""

helps["lock create"] = """
"type": |-
    command
"short-summary": |-
    Create a lock.
"long-summary": |-
    Locks can exist at three different scopes: subscription, resource group and resource.
"examples":
-   "name": |-
        Create a lock.
    "text": |-
        az lock create --lock-type ReadOnly --resource-group group --notes <notes> --name lockName
"""

helps["managedapp definition list"] = """
"type": |-
    command
"short-summary": |-
    List managed application definitions.
"""

helps["resource link update"] = """
"type": |-
    command
"short-summary": |-
    Update link between resources.
"long-summary": |-
    A link-id is of the form /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/{ProviderNamespace}/{ResourceType}/{ResourceName}/providers/Microsoft.Resources/links/{LinkName}
"""

helps["account management-group delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an existing management group.
"long-summary": |-
    Delete an existing management group.
"parameters":
-   "name": |-
        --name -n
    "type": |-
        string
    "short-summary": |-
        Name of the management group.
"""

helps["provider operation"] = """
"type": |-
    group
"short-summary": |-
    Get provider operations metadatas.
"""

helps["account lock show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a subscription lock
"""

helps["group lock show"] = """
"type": |-
    command
"short-summary": |-
    Show the details of a resource group lock
"""

helps["resource link list"] = """
"type": |-
    command
"short-summary": |-
    List resource links.
"""

helps["group deployment operation"] = """
"type": |-
    group
"short-summary": |-
    Manage deployment operations.
"""

helps["feature list"] = """
"type": |-
    command
"short-summary": |-
    List preview features.
"examples":
-   "name": |-
        List preview features.
    "text": |-
        az feature list --namespace <namespace>
"""

helps["deployment wait"] = """
"type": |-
    command
"short-summary": |-
    Place the CLI in a waiting state until a deployment condition is met.
"""

helps["policy assignment show"] = """
"type": |-
    command
"short-summary": |-
    Show a resource policy assignment.
"""

helps["lock show"] = """
"type": |-
    command
"short-summary": |-
    Show the properties of a lock
"""

helps["policy definition list"] = """
"type": |-
    command
"short-summary": |-
    List policy definitions.
"""

helps["account lock update"] = """
"type": |-
    command
"short-summary": |-
    Update a subscription lock.
"""

helps["managedapp list"] = """
"type": |-
    command
"short-summary": |-
    List managed applications.
"""

helps["lock"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure locks.
"""


# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['policy event'] = """
type: group
short-summary: Manage policy events.
"""

helps['policy event list'] = """
type: command
short-summary: List policy events.
examples:
  - name: Get policy events at current subscription scope created in the last day.
    text: >
        az policy event list
  - name: Get policy events at management group scope.
    text: >
        az policy event list -m "myMg"
  - name: Get policy events at resource group scope in current subscription.
    text: >
        az policy event list -g "myRg"
  - name: Get policy events for a resource using resource ID.
    text: >
        az policy event list --resource "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myResourceGroup /providers/Microsoft.EventHub/namespaces/myns1/eventhubs/eh1/consumergroups/cg1"
  - name: Get policy events for a resource using resource name.
    text: >
        az policy event list --resource "myKeyVault" --namespace "Microsoft.KeyVault" --resource-type "vaults" -g "myresourcegroup"
  - name: Get policy events for a nested resource using resource name.
    text: >
        az policy event list --resource "myRule1" --namespace "Microsoft.Network" --resource-type "securityRules" --parent "networkSecurityGroups/mysecuritygroup1" -g "myresourcegroup"
  - name: Get policy events for a policy set definition in current subscription.
    text: >
        az policy event list -s "fff58873-fff8-fff5-fffc-fffbe7c9d697"
  - name: Get policy events for a policy definition in current subscription.
    text: >
        az policy event list -d "fff69973-fff8-fff5-fffc-fffbe7c9d698"
  - name: Get policy events for a policy assignment in current subscription.
    text: >
        az policy event list -a "ddd8ef92e3714a5ea3d208c1"
  - name: Get policy events for a policy assignment in the specified resource group in current subscription.
    text: >
        az policy event list -g "myRg" -a "ddd8ef92e3714a5ea3d208c1"
  - name: Get top 5 policy events in current subscription, selecting a subset of properties and customizing ordering.
    text: >
        az policy event list --top 5 --order-by "timestamp desc, policyAssignmentName asc" --select "timestamp, resourceId, policyAssignmentId, policySetDefinitionId, policyDefinitionId"
  - name: Get policy events in current subscription during a custom time interval.
    text: >
        az policy event list --from "2018-03-08T00:00:00Z" --to "2018-03-15T00:00:00Z"
  - name: Get policy events in current subscription filtering results based on some property values.
    text: >
        az policy event list --filter "(policyDefinitionAction eq 'deny' or policyDefinitionAction eq 'audit') and resourceLocation ne 'eastus'"
  - name: Get number of policy events in current subscription.
    text: >
        az policy event list --apply "aggregate($count as numberOfRecords)"
  - name: Get policy events in current subscription aggregating results based on some properties.
    text: >
        az policy event list --apply "groupby((policyAssignmentId, policyDefinitionId, policyDefinitionAction, resourceId), aggregate($count as numEvents))"
  - name: Get policy events in current subscription grouping results based on some properties.
    text: >
        az policy event list --apply "groupby((policyAssignmentName, resourceId))"
  - name: Get policy events in current subscription aggregating results based on some properties specifying multiple groupings.
    text: >
        az policy event list --apply "groupby((policyAssignmentId, policyDefinitionId, resourceId))/groupby((policyAssignmentId, policyDefinitionId), aggregate($count as numResourcesWithEvents))"
"""

helps['policy remediation'] = """
type: group
short-summary: Manage resource policy remediations.
"""

helps['policy remediation cancel'] = """
type: command
short-summary: Cancel a resource policy remediation.
"""

helps['policy remediation create'] = """
type: command
short-summary: Create a resource policy remediation.
examples:
  - name: Create a remediation at resource group scope for a policy assignment
    text: >
        az policy remediation create -g myRg -n myRemediation --policy-assignment eeb18edc813c42d0ad5a9eab
  - name: Create a remediation at resource group scope for a policy assignment using the policy assignment resource ID
    text: >
        az policy remediation create -g myRg -n myRemediation --policy-assignment "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/providers/Microsoft.Authorization/policyAssignments/myPa"
  - name: Create a remediation at subscription scope for a policy set assignment
    text: >
        az policy remediation create -n myRemediation --policy-assignment eeb18edc813c42d0ad5a9eab --definition-reference-id auditVMPolicyReference
  - name: Create a remediation at management group scope for specific resource locations
    text: >
        az policy remediation create -m myMg -n myRemediation --policy-assignment eeb18edc813c42d0ad5a9eab --location-filters eastus westeurope
  - name: Create a remediation for a specific resource using the resource ID
    text: >
        az policy remediation create --resource "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myRg/providers/Microsoft.Compute/virtualMachines/myVm" -n myRemediation --policy-assignment eeb18edc813c42d0ad5a9eab
  - name: Create a remediation that will re-evaluate compliance before remediating
    text: >
        az policy remediation create -g myRg -n myRemediation --policy-assignment eeb18edc813c42d0ad5a9eab --resource-discovery-mode ReEvaluateCompliance
"""

helps['policy remediation delete'] = """
type: command
short-summary: Delete a resource policy remediation.
"""

helps['policy remediation deployment'] = """
type: group
short-summary: Manage resource policy remediation deployments.
"""

helps['policy remediation deployment list'] = """
type: command
short-summary: Lists deployments for a resource policy remediation.
"""

helps['policy remediation list'] = """
type: command
short-summary: List resource policy remediations.
"""

helps['policy remediation show'] = """
type: command
short-summary: Show a resource policy remediation.
"""

helps['policy state'] = """
type: group
short-summary: Manage policy compliance states.
"""

helps['policy state list'] = """
type: command
short-summary: List policy compliance states.
examples:
  - name: Get latest policy states at current subscription scope.
    text: >
        az policy state list
  - name: Get all policy states at current subscription scope.
    text: >
        az policy state list --all
  - name: Get latest policy states at management group scope.
    text: >
        az policy state list -m "myMg"
  - name: Get latest policy states at resource group scope in current subscription.
    text: >
        az policy state list -g "myRg"
  - name: Get latest policy states for a resource using resource ID.
    text: >
        az policy state list --resource "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myResourceGroup /providers/Microsoft.EventHub/namespaces/myns1/eventhubs/eh1/consumergroups/cg1"
  - name: Get latest policy states for a resource using resource name.
    text: >
        az policy state list --resource "myKeyVault" --namespace "Microsoft.KeyVault" --resource-type "vaults" -g "myresourcegroup"
  - name: Get latest policy states for a nested resource using resource name.
    text: >
        az policy state list --resource "myRule1" --namespace "Microsoft.Network" --resource-type "securityRules" --parent "networkSecurityGroups/mysecuritygroup1" -g "myresourcegroup"
  - name: Get latest policy states for a policy set definition in current subscription.
    text: >
        az policy state list -s "fff58873-fff8-fff5-fffc-fffbe7c9d697"
  - name: Get latest policy states for a policy definition in current subscription.
    text: >
        az policy state list -d "fff69973-fff8-fff5-fffc-fffbe7c9d698"
  - name: Get latest policy states for a policy assignment in current subscription.
    text: >
        az policy state list -a "ddd8ef92e3714a5ea3d208c1"
  - name: Get latest policy states for a policy assignment in the specified resource group in current subscription.
    text: >
        az policy state list -g "myRg" -a "ddd8ef92e3714a5ea3d208c1"
  - name: Get top 5 latest policy states in current subscription, selecting a subset of properties and customizing ordering.
    text: >
        az policy state list --top 5 --order-by "timestamp desc, policyAssignmentName asc" --select "timestamp, resourceId, policyAssignmentId, policySetDefinitionId, policyDefinitionId"
  - name: Get latest policy states in current subscription during a custom time interval.
    text: >
        az policy state list --from "2018-03-08T00:00:00Z" --to "2018-03-15T00:00:00Z"
  - name: Get latest policy states in current subscription filtering results based on some property values.
    text: >
        az policy state list --filter "(policyDefinitionAction eq 'deny' or policyDefinitionAction eq 'audit') and resourceLocation ne 'eastus'"
  - name: Get number of latest policy states in current subscription.
    text: >
        az policy state list --apply "aggregate($count as numberOfRecords)"
  - name: Get latest policy states in current subscription aggregating results based on some properties.
    text: >
        az policy state list --apply "groupby((policyAssignmentId, policySetDefinitionId, policyDefinitionReferenceId, policyDefinitionId), aggregate($count as numStates))"
  - name: Get latest policy states in current subscription grouping results based on some properties.
    text: >
        az policy state list --apply "groupby((policyAssignmentName, resourceId))"
  - name: Get latest policy states in current subscription aggregating results based on some properties specifying multiple groupings.
    text: >
        az policy state list --apply "groupby((policyAssignmentId, policySetDefinitionId, policyDefinitionReferenceId, policyDefinitionId, resourceId))/groupby((policyAssignmentId, policySetDefinitionId, policyDefinitionReferenceId, policyDefinitionId), aggregate($count as numNonCompliantResources))"
  - name: Get latest policy states for a resource including policy evaluation details.
    text: >
        az policy state list --resource "myKeyVault" --namespace "Microsoft.KeyVault" --resource-type "vaults" -g "myresourcegroup" --expand PolicyEvaluationDetails
"""

helps['policy state summarize'] = """
type: command
short-summary: Summarize policy compliance states.
examples:
  - name: Get latest non-compliant policy states summary at current subscription scope.
    text: >
        az policy state summarize
  - name: Get latest non-compliant policy states summary at management group scope.
    text: >
        az policy state summarize -m "myMg"
  - name: Get latest non-compliant policy states summary at resource group scope in current subscription.
    text: >
        az policy state summarize -g "myRg"
  - name: Get latest non-compliant policy states summary for a resource using resource ID.
    text: >
        az policy state summarize --resource "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myResourceGroup /providers/Microsoft.EventHub/namespaces/myns1/eventhubs/eh1/consumergroups/cg1"
  - name: Get latest non-compliant policy states summary for a resource using resource name.
    text: >
        az policy state summarize --resource "myKeyVault" --namespace "Microsoft.KeyVault" --resource-type "vaults" -g "myresourcegroup"
  - name: Get latest non-compliant policy states summary for a nested resource using resource name.
    text: >
        az policy state summarize --resource "myRule1" --namespace "Microsoft.Network" --resource-type "securityRules" --parent "networkSecurityGroups/mysecuritygroup1" -g "myresourcegroup"
  - name: Get latest non-compliant policy states summary for a policy set definition in current subscription.
    text: >
        az policy state summarize -s "fff58873-fff8-fff5-fffc-fffbe7c9d697"
  - name: Get latest non-compliant policy states summary for a policy definition in current subscription.
    text: >
        az policy state summarize -d "fff69973-fff8-fff5-fffc-fffbe7c9d698"
  - name: Get latest non-compliant policy states summary for a policy assignment in current subscription.
    text: >
        az policy state summarize -a "ddd8ef92e3714a5ea3d208c1"
  - name: Get latest non-compliant policy states summary for a policy assignment in the specified resource group in current subscription.
    text: >
        az policy state summarize -g "myRg" -a "ddd8ef92e3714a5ea3d208c1"
  - name: Get latest non-compliant policy states summary in current subscription, limiting the assignments summary to top 5.
    text: >
        az policy state summarize --top 5
  - name: Get latest non-compliant policy states summary in current subscription for a custom time interval.
    text: >
        az policy state summarize --from "2018-03-08T00:00:00Z" --to "2018-03-15T00:00:00Z"
  - name: Get latest non-compliant policy states summary in current subscription filtering results based on some property values.
    text: >
        az policy state summarize --filter "(policyDefinitionAction eq 'deny' or policyDefinitionAction eq 'audit') and resourceLocation ne 'eastus'"
"""

helps['policy state trigger-scan'] = """
type: command
short-summary: Trigger a policy compliance evaluation for a scope.
examples:
  - name: Trigger a policy compliance evaluation at the current subscription scope.
    text: >
        az policy state trigger-scan
  - name: Trigger a policy compliance evaluation for a resource group.
    text: >
        az policy state trigger-scan -g "myRg"
  - name: Trigger a policy compliance evaluation for a resource group and do not wait for it to complete.
    text: >
        az policy state trigger-scan -g "myRg" --no-wait
"""

helps['policy metadata'] = """
type: group
short-summary: Get policy metadata resources.
"""

helps['policy metadata list'] = """
type: command
short-summary: List policy metadata resources.
examples:
  - name: Get all policy metadata resources.
    text: >
        az policy metadata list
  - name: Get policy metadata resources, limit the output to 5 resources.
    text: >
        az policy metadata list --top 5
"""

helps['policy metadata show'] = """
type: command
short-summary: Get a single policy metadata resource.
examples:
  - name: Get the policy metadata resource with the name 'ACF1000'.
    text: >
        az policy metadata show --name ACF1000
"""

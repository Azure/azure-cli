# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['policy event'] = """
    type: group
    short-summary: Manage policy events.
"""
helps['policy event list'] = """
    type: command
    short-summary: List policy events.
    parameters:
        - name: --management-group-name -mg
          type: string

        - name: --subscription-id -s
          type: string

        - name: --resource-group-name -rg
          type: string

        - name: --resource-id -r
          type: string

        - name: --policy-set-definition-name -ps
          type: string

        - name: --policy-definition-name -pd
          type: string

        - name: --policy-assignment-name -pa
          type: string

        - name: --from
          type: datetime

        - name: --to
          type: datetime

        - name: --top -t
          type: long

        - name: --order-by -o
          type: string

        - name: --select -sl
          type: string

        - name: --filter -f
          type: string

        - name: --apply -a
          type: string
    examples:
        - name: Get policy events at current subscription scope created in the last day.
          text: >
              az policy event list 
        - name: Get policy events at specified subscription scope.
          text: >
              az policy event list -s "fff10b27-fff3-fff5-fff8-fffbe01e86a5"
        - name: Get policy events at management group scope.
          text: >
              az policy event list -mg "myMg" 
        - name: Get policy events at resource group scope in current subscription.
          text: >
              az policy event list -rg "myRg"
        - name: Get policy events for a resource.
          text: >
              az policy event list -r "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myResourceGroup /providers/Microsoft.EventHub/namespaces/myns1/eventhubs/eh1/consumergroups/cg1"
        - name: Get policy events for a policy set definition in current subscription.
          text: >
              az policy event list -ps "fff58873-fff8-fff5-fffc-fffbe7c9d697"
        - name: Get policy events for a policy definition in current subscription.
          text: >
              az policy event list -pd "fff69973-fff8-fff5-fffc-fffbe7c9d698"
        - name: Get policy events for a policy assignment in current subscription.
          text: >
              az policy event list -pa "ddd8ef92e3714a5ea3d208c1"
        - name: Get policy events for a policy assignment in the specified resource group in current subscription.
          text: >
              az policy event list -rg "myRg" -pa "ddd8ef92e3714a5ea3d208c1"
        - name: Get top 5 policy events in current subscription, selecting a subset of properties and customizing ordering.
          text: >
              az policy event list -top 5 -ob "timestamp desc, policyAssignmentName asc" -sl "timestamp, resourceId, policyAssignmentId, policySetDefinitionId, policyDefinitionId"
        - name: Get policy events in current subscription during a custom time interval.
          text: >
              az policy event list -from "2018-03-08T00:00:00Z" -to "2018-03-15T00:00:00Z"
        - name: Get policy events in current subscription filtering results based on some property values.
          text: >
              az policy event list -f "(policyDefinitionAction eq 'deny' or policyDefinitionAction eq 'audit') and resourceLocation ne 'eastus'"
        - name: Get number of policy events in current subscription.
          text: >
              az policy event list -a "aggregate($count as numberOfRecords)"
        - name: Get policy events in current subscription aggregating results based on some properties.
          text: >
              az policy event list -a "groupby((policyAssignmentId, policyDefinitionId, policyDefinitionAction, resourceId), aggregate($count as numEvents))"
        - name: Get policy events in current subscription grouping results based on some properties.
          text: >
              az policy event list -a "groupby((policyAssignmentName, resourceId))"
        - name: Get policy events in current subscription aggregating results based on some properties specifying multiple groupings.
          text: >
              az policy event list -a "groupby((policyAssignmentId, policyDefinitionId, resourceId))/groupby((policyAssignmentId, policyDefinitionId), aggregate($count as numResourcesWithEvents))"
"""
helps['policy state'] = """
    type: group
    short-summary: Manage policy compliance states.
"""
helps['policy state list'] = """
    type: command
    short-summary: List policy compliance states.
    parameters:
        - name: --management-group-name -mg
          type: string

        - name: --subscription-id -s
          type: string

        - name: --resource-group-name -rg
          type: string

        - name: --resource-id -r
          type: string

        - name: --policy-set-definition-name -ps
          type: string

        - name: --policy-definition-name -pd
          type: string

        - name: --policy-assignment-name -pa
          type: string

        - name: --from
          type: datetime

        - name: --to
          type: datetime

        - name: --top -t
          type: long

        - name: --order-by -o
          type: string

        - name: --select -sl
          type: string

        - name: --filter -f
          type: string

        - name: --apply -a
          type: string
    examples:
        - name: Get latest policy states at current subscription scope.
          text: >
              az policy state list 
        - name: Get latest policy states at specified subscription scope.
          text: >
              az policy state list -s "fff10b27-fff3-fff5-fff8-fffbe01e86a5"
        - name: Get all policy states at current subscription scope.
          text: >
              az policy state list -all
        - name: Get latest policy states at management group scope.
          text: >
              az policy state list -mg "myMg" 
        - name: Get latest policy states at resource group scope in current subscription.
          text: >
              az policy state list -rg "myRg"
        - name: Get latest policy states for a resource.
          text: >
              az policy state list -r "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myResourceGroup /providers/Microsoft.EventHub/namespaces/myns1/eventhubs/eh1/consumergroups/cg1"
        - name: Get latest policy states for a policy set definition in current subscription.
          text: >
              az policy state list -ps "fff58873-fff8-fff5-fffc-fffbe7c9d697"
        - name: Get latest policy states for a policy definition in current subscription.
          text: >
              az policy state list -pd "fff69973-fff8-fff5-fffc-fffbe7c9d698"
        - name: Get latest policy states for a policy assignment in current subscription.
          text: >
              az policy state list -pa "ddd8ef92e3714a5ea3d208c1"
        - name: Get latest policy states for a policy assignment in the specified resource group in current subscription.
          text: >
              az policy state list -rg "myRg" -pa "ddd8ef92e3714a5ea3d208c1"
        - name: Get top 5 latest policy states in current subscription, selecting a subset of properties and customizing ordering.
          text: >
              az policy state list -top 5 -ob "timestamp desc, policyAssignmentName asc" -sl "timestamp, resourceId, policyAssignmentId, policySetDefinitionId, policyDefinitionId"
        - name: Get latest policy states in current subscription during a custom time interval.
          text: >
              az policy state list -from "2018-03-08T00:00:00Z" -to "2018-03-15T00:00:00Z"
        - name: Get latest policy states in current subscription filtering results based on some property values.
          text: >
              az policy state list -f "(policyDefinitionAction eq 'deny' or policyDefinitionAction eq 'audit') and resourceLocation ne 'eastus'"
        - name: Get number of latest policy states in current subscription.
          text: >
              az policy state list -a "aggregate($count as numberOfRecords)"
        - name: Get latest policy states in current subscription aggregating results based on some properties.
          text: >
              az policy state list -a "groupby((policyAssignmentId, policySetDefinitionId, policyDefinitionReferenceId, policyDefinitionId), aggregate($count as numStates))"
        - name: Get latest policy states in current subscription grouping results based on some properties.
          text: >
              az policy state list -a "groupby((policyAssignmentName, resourceId))"
        - name: Get latest policy states in current subscription aggregating results based on some properties specifying multiple groupings.
          text: >
              az policy state list -a "groupby((policyAssignmentId, policySetDefinitionId, policyDefinitionReferenceId, policyDefinitionId, resourceId))/groupby((policyAssignmentId, policySetDefinitionId, policyDefinitionReferenceId, policyDefinitionId), aggregate($count as numNonCompliantResources))"
"""
helps['policy state summarize'] = """
    type: command
    short-summary: Summarize policy compliance states.
    parameters:
        - name: --management-group-name -mg
          type: string

        - name: --subscription-id -s
          type: string

        - name: --resource-group-name -rg
          type: string

        - name: --resource-id -r
          type: string

        - name: --policy-set-definition-name -ps
          type: string

        - name: --policy-definition-name -pd
          type: string

        - name: --policy-assignment-name -pa
          type: string

        - name: --from
          type: datetime

        - name: --to
          type: datetime

        - name: --top -t
          type: long

        - name: --filter -f
          type: string
    examples:
        - name: Get latest non-compliant policy states summary at current subscription scope.
          text: >
              az policy state summarize 
        - name: Get latest non-compliant policy states summary at specified subscription scope.
          text: >
              az policy state summarize -s "fff10b27-fff3-fff5-fff8-fffbe01e86a5"
        - name: Get latest non-compliant policy states summary at management group scope.
          text: >
              az policy state summarize -mg "myMg" 
        - name: Get latest non-compliant policy states summary at resource group scope in current subscription.
          text: >
              az policy state summarize -rg "myRg"
        - name: Get latest non-compliant policy states summary for a resource.
          text: >
              az policy state summarize -r "/subscriptions/fff10b27-fff3-fff5-fff8-fffbe01e86a5/resourceGroups/myResourceGroup /providers/Microsoft.EventHub/namespaces/myns1/eventhubs/eh1/consumergroups/cg1"
        - name: Get latest non-compliant policy states summary for a policy set definition in current subscription.
          text: >
              az policy state summarize -ps "fff58873-fff8-fff5-fffc-fffbe7c9d697"
        - name: Get latest non-compliant policy states summary for a policy definition in current subscription.
          text: >
              az policy state summarize -pd "fff69973-fff8-fff5-fffc-fffbe7c9d698"
        - name: Get latest non-compliant policy states summary for a policy assignment in current subscription.
          text: >
              az policy state summarize -pa "ddd8ef92e3714a5ea3d208c1"
        - name: Get latest non-compliant policy states summary for a policy assignment in the specified resource group in current subscription.
          text: >
              az policy state summarize -rg "myRg" -pa "ddd8ef92e3714a5ea3d208c1"
        - name: Get latest non-compliant policy states summary in current subscription, limiting the assignments summary to top 5.
          text: >
              az policy state summarize -top 5
        - name: Get latest non-compliant policy states summary in current subscription for a custom time interval.
          text: >
              az policy state summarize -from "2018-03-08T00:00:00Z" -to "2018-03-15T00:00:00Z"
        - name: Get latest non-compliant policy states summary in current subscription filtering results based on some property values.
          text: >
              az policy state summarize -f "(policyDefinitionAction eq 'deny' or policyDefinitionAction eq 'audit') and resourceLocation ne 'eastus'"
"""

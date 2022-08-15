# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['security'] = """
type: group
short-summary: Manage your security posture with Microsoft Defender for Cloud.
"""

helps['security alert'] = """
type: group
short-summary: View security alerts.
"""

helps['security alert list'] = """
type: command
short-summary: List security alerts.
examples:
  - name: Get security alerts on a subscription scope.
    text: >
        az security alert list
  - name: Get security alerts on a resource group scope.
    text: >
        az security alert list -g "myRg"
"""

helps['security alert show'] = """
type: command
short-summary: Shows a security alert.
examples:
  - name: Get a security alert on a subscription scope.
    text: >
        az security alert show --location "centralus" -n "alertName"
  - name: Get a security alert on a resource group scope.
    text: >
        az security alert show -g "myRg" --location "centralus" -n "alertName"
"""

helps['security alert update'] = """
type: command
short-summary: Updates a security alert status.
examples:
  - name: Dismiss a security alert on a subscription scope.
    text: >
        az security alert update --location "centralus" -n "alertName" --status "dismiss"
  - name: Dismiss a security alert on a resource group scope.
    text: >
        az security alert update -g "myRg" --location "centralus" -n "alertName" --status "dismiss"
  - name: Activate a security alert on a subscritpion scope.
    text: >
        az security alert update --location "centralus" -n "alertName" --status "activate"
  - name: Activate a security alert on a resource group scope.
    text: >
        az security alert update -g "myRg" --location "centralus" -n "alertName" --status "activate"
"""

helps['security alerts-suppression-rule'] = """
type: group
short-summary: View and manage alerts suppression rules.
"""

helps['security alerts-suppression-rule list'] = """
type: command
short-summary: List all alerts suppression rule on a subscription scope.
examples:
  - name: List alerts suppression rules.
    text: >
        az security alerts-suppression-rule list
"""

helps['security alerts-suppression-rule show'] = """
type: command
short-summary: Shows an alerts suppression rule.
examples:
  - name: Get an alerts suppression rule on a subscription scope.
    text: >
        az security alerts-suppression-rule show --rule-name RuleName
"""

helps['security alerts-suppression-rule update'] = """
type: command
short-summary: Updates or create an alerts suppression rule.
examples:
  - name: Create suppression rule with entities.
    text: >
        az security alerts-suppression-rule update --rule-name RuleName --alert-type "Test" --reason "Other" --comment "Test comment" --state "Enabled"
"""

helps['security alerts-suppression-rule delete'] = """
type: command
short-summary: Delete an alerts suppression rule.
examples:
  - name: Delete an alerts suppression rule.
    text: >
        az security alerts-suppression-rule delete --rule-name RuleName
"""

helps['security alerts-suppression-rule upsert_scope'] = """
type: command
short-summary: Update an alerts suppression rule with scope element.
examples:
  - name: Add "entities.host.dnsdomain" scope to an alerts suppression rule.
    text: >
        az security alerts-suppression-rule upsert_scope --field "entities.process.commandline" --contains-substring "example" --rule-name RuleName
"""

helps['security alerts-suppression-rule delete_scope'] = """
type: command
short-summary: Delete an alerts suppression rule scope.
examples:
  - name: Delete an alerts suppression rule scope.
    text: >
        az security alerts-suppression-rule delete_scope --rule-name RuleName --field "entities.process.commandline"
"""

helps['security atp'] = """
type: group
short-summary: View and manage Advanced Threat Protection settings.
"""

helps['security atp storage'] = """
type: group
short-summary: View and manage Advanced Threat Protection settings for storage accounts.
"""

helps['security atp cosmosdb'] = """
type: group
short-summary: View and manage Advanced Threat Protection settings for Cosmos DB accounts.
"""

helps['security atp storage show'] = """
type: command
short-summary: Display Advanced Threat Protection settings for a storage account.
examples:
  - name: Retrieve Advanced Threat Protection settings for a storage account on a subscription scope.
    text: >
        az security atp storage show --resource-group MyResourceGroup --storage-account MyStorageAccount
"""

helps['security atp cosmosdb show'] = """
type: command
short-summary: Display Advanced Threat Protection settings for an Azure Cosmos DB account.
examples:
  - name: Retrieve Advanced Threat Protection settings for an Azure Cosmos DB account on a subscription scope.
    text: >
        az security atp cosmosdb show --resource-group MyResourceGroup --cosmosdb-account MyCosmosDbAccount
"""

helps['security atp storage update'] = """
type: command
short-summary: Toggle status of Advanced Threat Protection for a storage account.
examples:
  - name: Enable Advanced Threat Protection for a storage account on a subscription scope.
    text: >
        az security atp storage update --resource-group MyResourceGroup --storage-account MyStorageAccount --is-enabled true
  - name: Disable Advanced Threat Protection for a storage account on a subscription scope.
    text: >
        az security atp storage update --resource-group MyResourceGroup --storage-account MyStorageAccount --is-enabled false
"""

helps['security atp cosmosdb update'] = """
type: command
short-summary: Toggle status of Advanced Threat Protection for an Azure Cosmos DB account.
examples:
  - name: Enable Advanced Threat Protection for an Azure Cosmos DB account on a subscription scope.
    text: >
        az security atp cosmosdb update --resource-group MyResourceGroup --cosmosdb-account MyCosmosDbAccount --is-enabled true
  - name: Disable Advanced Threat Protection for an Azure Cosmos DB account on a subscription scope.
    text: >
        az security atp cosmosdb update --resource-group MyResourceGroup --cosmosdb-account MyCosmosDbAccount --is-enabled false
"""

helps['security va'] = """
type: group
short-summary: View Vulnerability Assessment.
"""

helps['security va sql'] = """
type: group
short-summary: View Sql Vulnerability Assessment scan results and manage baseline.
"""

helps['security va sql scans'] = """
type: group
short-summary: View Sql Vulnerability Assessment scan summaries.
"""

helps['security va sql scans show'] = """
type: command
short-summary: View Sql Vulnerability Assessment scan summaries.
examples:
  - name: View Sql Vulnerability Assessment scan summary on an Azure virtual machine.
    text: >
        az security va sql scans show --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --scan-id MyScanId
  - name: View Sql Vulnerability Assessment scan summary on an On-Premise machine.
    text: >
        az security va sql scans show --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --scan-id MyScanId
"""

helps['security va sql scans list'] = """
type: command
short-summary: List all Sql Vulnerability Assessment scan summaries.
examples:
  - name: List all Sql Vulnerability Assessment scan summaries on an Azure virtual machine.
    text: >
        az security va sql scans list --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName
  - name: List all Sql Vulnerability Assessment scan summaries on an On-Premise machine.
    text: >
        az security va sql scans list --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID
"""

helps['security va sql results'] = """
type: group
short-summary: View Sql Vulnerability Assessment scan results.
"""

helps['security va sql results show'] = """
type: command
short-summary: View Sql Vulnerability Assessment scan results.
examples:
  - name: View Sql Vulnerability Assessment scan results on an Azure virtual machine.
    text: >
        az security va sql results show --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --scan-id MyScanId --rule-id VA9999
  - name: View Sql Vulnerability Assessment scan results on an On-Premise machine.
    text: >
        az security va sql results show --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --scan-id MyScanId --rule-id VA9999
"""

helps['security va sql results list'] = """
type: command
short-summary: View all Sql Vulnerability Assessment scan results.
examples:
  - name: View all Sql Vulnerability Assessment scan results on an Azure virtual machine.
    text: >
        az security va sql results list --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --scan-id MyScanId
  - name: View all Sql Vulnerability Assessment scan results on an On-Premise machine.
    text: >
        az security va sql results list --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --scan-id MyScanId
"""

helps['security va sql baseline'] = """
type: group
short-summary: View and manage Sql Vulnerability Assessment baseline.
"""

helps['security va sql baseline show'] = """
type: command
short-summary: View Sql Vulnerability Assessment rule baseline.
examples:
  - name: View Sql Vulnerability Assessment rule baseline on an Azure virtual machine.
    text: >
        az security va sql baseline show --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --rule-id VA9999
  - name: View Sql Vulnerability Assessment rule baseline on an On-Premise machine.
    text: >
        az security va sql baseline show --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --rule-id VA9999
"""

helps['security va sql baseline list'] = """
type: command
short-summary: View Sql Vulnerability Assessment baseline for all rules.
examples:
  - name: View Sql Vulnerability Assessment baseline for all rules on an Azure virtual machine.
    text: >
        az security va sql baseline list --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName
  - name: View Sql Vulnerability Assessment baseline for all rules on an On-Premise machine.
    text: >
        az security va sql baseline list --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID
"""

helps['security va sql baseline delete'] = """
type: command
short-summary: Delete Sql Vulnerability Assessment rule baseline.
examples:
  - name: Delete Sql Vulnerability Assessment rule baseline on an Azure virtual machine.
    text: >
        az security va sql baseline delete --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --rule-id VA9999
  - name: Delete Sql Vulnerability Assessment rule baseline on an On-Premise machine.
    text: >
        az security va sql baseline delete --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --rule-id VA9999
"""

helps['security va sql baseline update'] = """
type: command
short-summary: Update Sql Vulnerability Assessment rule baseline. Replaces the current rule baseline.
examples:
  - name: Update Sql Vulnerability Assessment rule baseline on an Azure virtual machine. Replaces the current rule baseline with latest scan results.
    text: >
        az security va sql baseline update --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --rule-id VA9999 --latest
  - name: Update Sql Vulnerability Assessment rule baseline on an Azure virtual machine. Replaces the current rule baseline with provided results.
    text: >
        az security va sql baseline update --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --rule-id VA9999 --baseline Line1_Col1 Line1_Col2 --baseline Line2_Col1 Line2_Col2
  - name: Update Sql Vulnerability Assessment rule baseline on an On-Premise machine. Replaces the current rule baseline with latest scan results.
    text: >
        az security va sql baseline update --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --rule-id VA9999 --latest
  - name: Update Sql Vulnerability Assessment rule baseline on an On-Premise machine. Replaces the current rule baseline with provided results.
    text: >
        az security va sql baseline update --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --rule-id VA9999 --baseline Line1_Col1 Line1_Col2 --baseline Line2_Col1 Line2_Col2
"""

helps['security va sql baseline set'] = """
type: command
short-summary: Sets Sql Vulnerability Assessment baseline. Replaces the current baseline.
examples:
  - name: Sets Sql Vulnerability Assessment baseline on an Azure virtual machine. Replaces the current baseline with latest scan results.
    text: >
        az security va sql baseline set --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --latest
  - name: Sets Sql Vulnerability Assessment baseline on an Azure virtual machine. Replaces the current baseline with provided results.
    text: >
        az security va sql baseline set --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.Compute/VirtualMachines/MyVmName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --baseline rule=VA9999 Line1_col1 Line1_col2 Line1_col3 --baseline rule=VA8888 Line1_col1 Line1_col2 --baseline rule=VA9999 Line2_col1 Line2_col2 Line2_col3
  - name: Sets Sql Vulnerability Assessment baseline on an On-Premise machine. Replaces the current baseline with latest scan results.
    text: >
        az security va sql baseline set --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --latest
  - name: Sets Sql Vulnerability Assessment baseline on an On-Premise machine. Replaces the current baseline with provided results.
    text: >
        az security va sql baseline set --vm-resource-id subscriptions/MySubscription/ResourceGroups/MyResourceGroup/Providers/Microsoft.OperationalInsights/Workspaces/MyWorkspaceName --workspace-id 00000000-0000-0000-0000-000000000000 --server-name MyServerName --database-name MyDbName --vm-name MyVmName --agent-id MyAgentId --vm-uuid MyVmUUID --baseline rule=VA9999 Line1_col1 Line1_col2 Line1_col3 --baseline rule=VA8888 Line1_col1 Line1_col2 --baseline rule=VA9999 Line2_col1 Line2_col2 Line2_col3
"""

helps['security auto-provisioning-setting'] = """
type: group
short-summary: View your auto provisioning settings.
"""

helps['security auto-provisioning-setting list'] = """
type: command
short-summary: List the auto provisioning settings.
examples:
  - name: Get auto provisioning settings.
    text: >
        az security auto-provisioning-setting list
"""

helps['security auto-provisioning-setting show'] = """
type: command
short-summary: Shows an auto provisioning setting.
examples:
  - name: Get an auto provisioning setting.
    text: >
        az security auto-provisioning-setting show -n "default"
"""

helps['security auto-provisioning-setting update'] = """
type: command
short-summary: Updates your automatic provisioning settings on the subscription.
examples:
  - name: Turns on automatic provisioning on the subscription.
    text: >
        az security auto-provisioning-setting update -n "default" --auto-provision "On"
  - name: Turns off automatic provisioning on the subscription.
    text: >
        az security auto-provisioning-setting update -n "default" --auto-provision "Off"
  - name: Updates your automatic provisioning settings on the subscription. (autogenerated)
    text: |
        az security auto-provisioning-setting update --auto-provision "Off" --name "default" --subscription MySubscription
    crafted: true
"""

helps['security contact'] = """
type: group
short-summary: View your security contacts.
"""

helps['security contact create'] = """
type: command
short-summary: Creates a security contact.
examples:
  - name: Creates a security contact.
    text: >
        az security contact create -n "default1" --email 'john@contoso.com' --phone '(214)275-4038' --alert-notifications 'on' --alerts-admins 'on'
"""

helps['security contact delete'] = """
type: command
short-summary: Deletes a security contact.
examples:
  - name: Deletes a security contact.
    text: >
        az security contact delete -n "default1"
"""

helps['security contact list'] = """
type: command
short-summary: List security contact.
examples:
  - name: Get security contacts.
    text: >
        az security contact list
"""

helps['security contact show'] = """
type: command
short-summary: Shows a security contact.
examples:
  - name: Get a security contact.
    text: >
        az security contact show -n "default1"
"""

helps['security discovered-security-solution'] = """
type: group
short-summary: View your discovered security solutions
"""

helps['security discovered-security-solution list'] = """
type: command
short-summary: List the discovered security solutions.
examples:
  - name: Get discovered security solutions.
    text: >
        az security discovered-security-solution list
"""

helps['security discovered-security-solution show'] = """
type: command
short-summary: Shows a discovered security solution.
examples:
  - name: Get a discovered security solution.
    text: >
        az security discovered-security-solution show -n ContosoWAF2 -g myService1
"""

helps['security external-security-solution'] = """
type: group
short-summary: View your external security solutions
"""

helps['security external-security-solution list'] = """
type: command
short-summary: List the external security solutions.
examples:
  - name: Get external security solutions.
    text: >
        az security external-security-solution list
"""

helps['security external-security-solution show'] = """
type: command
short-summary: Shows an external security solution.
examples:
  - name: Get an external security solution.
    text: >
        az security external-security-solution show -n aad_defaultworkspace-20ff7fc3-e762-44dd-bd96-b71116dcdc23-eus -g defaultresourcegroup-eus
"""

helps['security jit-policy'] = """
type: group
short-summary: Manage your Just in Time network access policies
"""

helps['security jit-policy list'] = """
type: command
short-summary: List your Just in Time network access policies.
examples:
  - name: Get all the Just in Time network access policies.
    text: >
        az security jit-policy list
"""

helps['security jit-policy show'] = """
type: command
short-summary: Shows a Just in Time network access policy.
examples:
  - name: Get a Just in Time network access policy.
    text: >
        az security jit-policy show -l northeurope -n default -g myService1
"""

helps['security location'] = """
type: group
short-summary: Shows the Microsoft Defender for Cloud Home region location.
"""

helps['security location list'] = """
type: command
short-summary: Shows the Microsoft Defender for Cloud Home region location.
examples:
  - name: Shows the Microsoft Defender for Cloud Home region location.
    text: >
        az security location list
"""

helps['security location show'] = """
type: command
short-summary: Shows the Microsoft Defender for Cloud Home region location.
examples:
  - name: Shows the Microsoft Defender for Cloud Home region location.
    text: >
        az security location show -n centralus
"""

helps['security pricing'] = """
type: group
short-summary: Enables managing the Azure Defender plan for the subscription
"""

helps['security pricing create'] = """
type: command
short-summary: Updates the Azure defender plan for the subscription.
examples:
  - name: Updates the Azure defender plan for the subscription.
    text: >
        az security pricing create -n VirtualMachines --tier 'standard'
  - name: Updates the Azure defender plan for the subscription. (autogenerated)
    text: az security pricing create -n VirtualMachines --tier 'standard'
    crafted: true
"""

helps['security pricing list'] = """
type: command
short-summary: Shows the Azure Defender plans for the subscription.
examples:
  - name: Shows the Azure Defender plans for the subscription.
    text: >
        az security pricing list
"""

helps['security pricing show'] = """
type: command
short-summary: Shows the Azure Defender plan for the subscription
examples:
  - name: Shows the Azure Defender plan for the subscription
    text: >
        az security pricing show -n VirtualMachines
"""

helps['security setting'] = """
type: group
short-summary: View your security settings.
"""

helps['security setting list'] = """
type: command
short-summary: List security settings.
examples:
  - name: Get security settings.
    text: >
        az security setting list
"""

helps['security setting show'] = """
type: command
short-summary: Shows a security setting.
examples:
  - name: Get a security setting.
    text: >
        az security setting show -n "MCAS"
"""

helps['security setting update'] = """
type: command
short-summary: Updates a security setting.
examples:
  - name: Update a security setting.
    text: >
        az security setting update -n "Sentinel" --enabled true
"""

helps['security task'] = """
type: group
short-summary: View security tasks (recommendations).
"""

helps['security task list'] = """
type: command
short-summary: List security tasks (recommendations).
examples:
  - name: Get security tasks (recommendations) on a subscription scope.
    text: >
        az security task list
  - name: Get security tasks (recommendations) on a resource group scope.
    text: >
        az security task list -g "myRg"
"""

helps['security task show'] = """
type: command
short-summary: shows a security task (recommendation).
examples:
  - name: Get a security task (recommendation) on a subscription scope.
    text: >
        az security task show -n "taskName"
  - name: Get a security task (recommendation) on a resource group scope.
    text: >
        az security task show -g "myRg" -n "taskName"
"""

helps['security topology'] = """
type: group
short-summary: Shows the network topology in your subscription.
"""

helps['security topology list'] = """
type: command
short-summary: Shows the network topology in your subscription.
examples:
  - name: Shows the network topology in your subscription.
    text: >
        az security topology list
"""

helps['security topology show'] = """
type: command
short-summary: Shows the network topology in your subscription.
examples:
  - name: Shows the network topology in your subscription.
    text: >
        az security topology show -n default -g myService1
"""

helps['security workspace-setting'] = """
type: group
short-summary: Shows the workspace settings in your subscription - these settings let you control which workspace will hold your security data
"""

helps['security workspace-setting create'] = """
type: command
short-summary: Creates a workspace settings in your subscription - these settings let you control which workspace will hold your security data
examples:
  - name: Creates a workspace settings in your subscription - these settings let you control which workspace will hold your security data
    text: >
        az security workspace-setting create -n default --target-workspace '/subscriptions/20ff7fc3-e762-44dd-bd96-b71116dcdc23/resourceGroups/myRg/providers/Microsoft.OperationalInsights/workspaces/myWorkspace'
"""

helps['security workspace-setting delete'] = """
type: command
short-summary: Deletes the workspace settings in your subscription - this will make the security events on the subscription be reported to the default workspace
examples:
  - name: Deletes the workspace settings in your subscription - this will make the security events on the subscription be reported to the default workspace
    text: >
        az security workspace-setting delete -n default
"""

helps['security workspace-setting list'] = """
type: command
short-summary: Shows the workspace settings in your subscription - these settings let you control which workspace will hold your security data
examples:
  - name: Shows the workspace settings in your subscription - these settings let you control which workspace will hold your security data
    text: >
        az security workspace-setting list
"""

helps['security workspace-setting show'] = """
type: command
short-summary: Shows the workspace settings in your subscription - these settings let you control which workspace will hold your security data
examples:
  - name: Shows the workspace settings in your subscription - these settings let you control which workspace will hold your security data
    text: >
        az security workspace-setting show -n default
"""

helps['security assessment'] = """
type: group
short-summary: View your security assessment results.
"""

helps['security assessment create'] = """
type: command
short-summary: Creates a customer managed security assessment.
examples:
  - name: Creates a security assessment.
    text: >
        az security assessment create -n '4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d' --status-code  'unhealthy'
"""

helps['security assessment delete'] = """
type: command
short-summary: Deletes a security assessment.
examples:
  - name: Deletes a security assessment.
    text: >
        az security assessment delete -n '4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d'
"""

helps['security assessment list'] = """
type: command
short-summary: List all security assessment results.
examples:
  - name: Get security assessments.
    text: >
        az security assessment list
"""

helps['security assessment show'] = """
type: command
short-summary: Shows a security assessment.
examples:
  - name: Get a security assessment.
    text: >
        az security assessment show -n '4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d'
"""

helps['security assessment-metadata'] = """
type: group
short-summary: View your security assessment metadata.
"""

helps['security assessment-metadata create'] = """
type: command
short-summary: Creates a customer managed security assessment type.
examples:
  - name: Creates a security assessment type.
    text: >
        az security assessment-metadata create -n "4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d" --display-name  "Resource should be secured" --severity "high" --description "The resource should be secured according to my company security policy"
"""

helps['security assessment-metadata delete'] = """
type: command
short-summary: Deletes a security assessment type and all it's assessment results.
examples:
  - name: Deletes a security assessment type.
    text: >
        az security assessment-metadata delete -n '4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d'
"""

helps['security assessment-metadata list'] = """
type: command
short-summary: List all security assessment results.
examples:
  - name: Get security assessment metadata.
    text: >
        az security assessment-metadata list
"""

helps['security assessment-metadata show'] = """
type: command
short-summary: Shows a security assessment.
examples:
  - name: Get a security assessment metadata.
    text: >
        az security assessment-metadata show -n '4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d'
"""

helps['security sub-assessment'] = """
type: group
short-summary: View your security sub assessments.
"""

helps['security sub-assessment list'] = """
type: command
short-summary: List all security sub assessment results.
examples:
  - name: Get security sub assessments.
    text: >
        az security sub-assessment list
"""

helps['security sub-assessment show'] = """
type: command
short-summary: Shows a security sub assessment.
examples:
  - name: Get a security sub assessment.
    text: >
        az security sub-assessment show --assessed-resource-id '/subscriptions/f8b197db-3b2b-4404-a3a3-0dfec293d0d0/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1' --assessment-name '4fb6c0a0-1137-42c7-a1c7-4bd37c91de8d' -n 'd7c4d9ec-227c-4fb3-acf9-25fdd97c1bf1'
"""

helps['security adaptive-application-controls'] = """
type: group
short-summary: Enable control which applications can run on your Azure and non-Azure machines (Windows and Linux)
"""

helps['security adaptive-application-controls list'] = """
type: command
short-summary: Adaptive Application Controls - List
examples:
  - name: list all application control VM/server groups.
    text: >
        az security adaptive-application-controls list
"""

helps['security adaptive-application-controls show'] = """
type: command
short-summary: Adaptive Application Controls - Get
examples:
  - name: Get a single application control VM/server group.
    text: >
        az security adaptive-application-controls show --group-name GROUP1
"""

helps['security allowed_connections'] = """
type: group
short-summary: View all possible traffic between resources for the subscription and location, based on connection type.
"""

helps['security allowed_connections list'] = """
type: command
short-summary: list of all possible traffic between resources for the subscription.
examples:
  - name: Get possible traffic between resources at the subscription level.
    text: >
        az security allowed_connections list
"""

helps['security allowed_connections show'] = """
type: command
short-summary: List all possible traffic between resources for the subscription and location, based on connection type.
examples:
  - name: Get all possible traffic between resources for the subscription and location, based on connection type.
    text: >
        az security allowed_connections show --name Internal --resource-group mygroup
"""

helps['security adaptive_network_hardenings'] = """
type: group
short-summary: View all Adaptive Network Hardening resources
"""

helps['security adaptive_network_hardenings list'] = """
type: command
short-summary: Gets a list of Adaptive Network Hardenings resources in scope of an extended resource.
examples:
  - name: Adaptive Network Hardenings - List By Extended Resource
    text: >
        az security adaptive_network_hardenings list --resource-group 'RG1' --resource-type 'virtualMachines' --resource-namespace 'Microsoft.Compute' --resource-name 'VM1'
"""

helps['security adaptive_network_hardenings show'] = """
type: command
short-summary: Gets a single Adaptive Network Hardening resource.
examples:
  - name: Adaptive Network Hardenings - Get.
    text: >
        az security adaptive_network_hardenings show --resource-group 'RG1' --resource-type 'virtualMachines' --resource-namespace 'Microsoft.Compute' --resource-name 'VM1' --adaptive-network-hardenings-resource-name 'default'
"""

helps['security iot-solution'] = """
type: group
short-summary: Manage your IoT Security solution.
"""

helps['security iot-solution create'] = """
type: command
short-summary: Create your IoT Security solution.
examples:
  - name: create an IoT Security solution on existing IoT Hub.
    text: >
        az security iot-solution create --solution-name 'IoT-Hub1' --resource-group 'rg1' --iot-hubs /subscriptions/subscriptionId/resourcegroups/rg1/providers/Microsoft.Devices/IotHubs/IoT-Hub1 --display-name "Solution Default" --location "eastus"
"""

helps['security iot-solution update'] = """
type: command
short-summary: Update your IoT Security solution.
examples:
  - name: Update your IoT Security solution.
    text: >
        az security iot-solution update --solution-name 'IoT-Hub1' --resource-group 'rg1' --iot-hubs /subscriptions/subscriptionId/resourcegroups/rg1/providers/Microsoft.Devices/IotHubs/IoT-Hub1 --display-name "Solution Default"
"""

helps['security iot-solution delete'] = """
type: command
short-summary: Delete your IoT Security solution.
examples:
  - name: Delete an IoT Security solutions.
    text: >
        az security iot-solution delete --solution-name 'IoT-Hub1' --resource-group 'rg1'
"""

helps['security iot-solution show'] = """
type: command
short-summary: Shows a IoT Security solution.
examples:
  - name: Get an IoT Security solutions.
    text: >
        az security iot-solution show --solution-name 'IoT-Hub1' --resource-group 'rg1'
"""

helps['security iot-solution list'] = """
type: command
short-summary: List all IoT Security solutions.
examples:
  - name: Get List of all IoT Security solutions in subscription.
    text: >
        az security iot-solution list
"""

helps['security iot-analytics'] = """
type: group
short-summary:  View IoT Security Analytics metrics.
"""

helps['security iot-analytics show'] = """
type: command
short-summary: Shows IoT Security Analytics metrics.
examples:
  - name: Get an IoT Security Analytics metrics.
    text: >
        az security iot-analytics show --solution-name 'IoT-Hub1' --resource-group 'rg1'
"""

helps['security iot-analytics list'] = """
type: command
short-summary: List all IoT security Analytics metrics.
examples:
  - name: Get List of all IoT security Analytics metrics.
    text: >
        az security iot-analytics list --solution-name 'IoT-Hub1' --resource-group 'rg1'
"""

helps['security iot-alerts'] = """
type: group
short-summary: View IoT Security aggregated alerts.
"""

helps['security iot-alerts delete'] = """
type: command
short-summary: Dismiss an aggregated IoT Security Alert.
examples:
  - name: Dismiss an aggregated IoT Security Alert.
    text: >
       az security iot-alerts delete --solution-name 'IoT-Hub1' --resource-group 'rg1' --name 'IoT_CryptoMiner/2020-06-24'
"""

helps['security iot-alerts show'] = """
type: command
short-summary: Shows a single aggregated alert of yours IoT Security solution.
examples:
  - name:  Get an IoT Security solution aggregated alert.
    text: >
        az security iot-alerts show --solution-name 'IoT-Hub1' --resource-group 'rg1' --name 'IoT_CryptoMiner/2020-06-24'
"""

helps['security iot-alerts list'] = """
type: command
short-summary: List all yours IoT Security solution aggregated alerts.
examples:
  - name: Get list of all IoT Security solution aggregated alerts.
    text: >
        az security iot-alerts list --solution-name 'IoT-Hub1' --resource-group 'rg1'
"""

helps['security iot-recommendations'] = """
type: group
short-summary: View IoT Security aggregated recommendations.
"""

helps['security iot-recommendations show'] = """
type: command
short-summary: Shows a single aggregated recommendation of yours IoT Security solution.
examples:
  - name: Get an IoT Security solution aggregated recommendation.
    text: >
        az security iot-recommendations show --solution-name 'IoT-Hub1' --resource-group 'rg1' --name 'IoT_PermissiveFirewallPolicy'
"""

helps['security iot-recommendations list'] = """
type: command
short-summary: List all yours IoT Security solution aggregated recommendations.
examples:
  - name: Get list of all IoT Security solution aggregated recommendations.
    text: >
        az security iot-recommendations list --solution-name 'IoT-Hub1' --resource-group 'rg1'
"""

helps['security regulatory-compliance-standards'] = """
type: group
short-summary: regulatory compliance standards.
"""

helps['security regulatory-compliance-standards list'] = """
type: command
short-summary: List supported regulatory compliance standards details and state results.
examples:
  - name: Get regulatory compliance standards list.
    text: >
        az security regulatory-compliance-standards list
"""

helps['security regulatory-compliance-standards show'] = """
type: command
short-summary: Shows a regulatory compliance details state for selected standard.
examples:
  - name: Get regulatory compliance standard details.
    text: >
        az security regulatory-compliance-standards show -n 'Azure-CIS-1.1.0'
"""

helps['security regulatory-compliance-controls'] = """
type: group
short-summary: regulatory compliance controls.
"""

helps['security regulatory-compliance-controls list'] = """
type: command
short-summary: List supported of regulatory compliance controls details and state for selected standard.
examples:
  - name: Get regulatory compliance controls list.
    text: >
        az security regulatory-compliance-controls list --standard-name 'Azure-CIS-1.1.0'
"""

helps['security regulatory-compliance-controls show'] = """
type: command
short-summary: Shows a regulatory compliance details state for selected standard.
examples:
  - name: Get selected regulatory compliance control details and state.
    text: >
        az security regulatory-compliance-controls show --standard-name 'Azure-CIS-1.1.0' -n '1.1'
"""

helps['security regulatory-compliance-assessments'] = """
type: group
short-summary: regulatory compliance assessments.
"""

helps['security regulatory-compliance-assessments list'] = """
type: command
short-summary: Get details and state of assessments mapped to selected regulatory compliance control.
examples:
  - name: Get state of mapped assessments.
    text: >
        az security regulatory-compliance-assessments list --standard-name 'Azure-CIS-1.1.0' --control-name '1.1'
"""

helps['security regulatory-compliance-assessments show'] = """
type: command
short-summary: Shows supported regulatory compliance details and state for selected assessment.
examples:
  - name: Get selected regulatory compliance control details and state.
    text: >
        az security regulatory-compliance-assessments show --standard-name 'Azure-CIS-1.1.0' --control-name '1.1' -n '94290b00-4d0c-d7b4-7cea-064a9554e681'
"""

helps['security secure-scores'] = """
type: group
short-summary: secure scores.
"""

helps['security secure-scores list'] = """
type: command
short-summary: List of secure-scores details and state results.
examples:
  - name: Get secure scores list.
    text: >
        az security secure-scores list
"""

helps['security secure-scores show'] = """
type: command
short-summary: Shows a secure score details for selected initiative.
examples:
  - name: Get secure score details.
    text: >
        az security secure-scores show -n 'ascScore'
"""

helps['security secure-score-controls'] = """
type: group
short-summary: secure score controls.
"""

helps['security secure-score-controls list'] = """
type: command
short-summary: List supported of secure score controls details and state for scope.
examples:
  - name: Get secure score controls list.
    text: >
        az security secure-score-controls list
"""

helps['security secure-score-controls list_by_score'] = """
type: command
short-summary: List supported of secure score controls details and state for selected score.
examples:
  - name: Get secure score controls list.
    text: >
        az security secure-score-controls list_by_score -n 'ascScore'
"""

helps['security secure-score-control-definitions'] = """
type: group
short-summary: secure score control definitions.
"""

helps['security secure-score-control-definitions list'] = """
type: command
short-summary: Get details of secure score control definitions.
examples:
  - name: Get secure score control definitions.
    text: >
        az security secure-score-control-definitions list
"""

helps['security security-solutions-reference-data'] = """
type: group
short-summary: Display all security solutions reference data at the subscription level.
"""

helps['security security-solutions-reference-data list'] = """
type: command
short-summary: Display all security solutions reference data at the subscription level.
examples:
  - name: Display all security solutions reference data.
    text: >
        az security security-solutions-reference-data list
"""

helps['security automation'] = """
type: group
short-summary: View your security automations.
"""

helps['security automation list'] = """
type: command
short-summary: List all security automations under subscription/resource group
examples:
  - name: List all security automations under subscription
    text: >
        az security automation list
  - name: List all security automations under resource group
    text: >
        az security automation list -g 'sampleRg'
"""

helps['security automation show'] = """
type: command
short-summary: Shows a security automation.
examples:
  - name: Shows a security automation.
    text: >
        az security automation show -g Sample-RG -n 'sampleAutomation'
"""

helps['security automation create_or_update'] = """
type: command
short-summary: Creates or update a security automation.
examples:
  - name: Creates a security automation.
    text: >
        az security automation create_or_update -g Sample-RG -n sampleAutomation -l eastus --scopes '[{\"description\": \"Scope for 487bb485-b5b0-471e-9c0d-10717612f869\", \"scopePath\": \"/subscriptions/487bb485-b5b0-471e-9c0d-10717612f869\"}]' --sources '[{\"eventSource\":\"SubAssessments\",\"ruleSets\":null}]' --actions '[{\"actionType\":\"EventHub\",\"eventHubResourceId\":\"subscriptions/212f9889-769e-45ae-ab43-6da33674bd26/resourceGroups/ContosoSiemPipeRg/providers/Microsoft.EventHub/namespaces/contososiempipe-ns/eventhubs/surashed-test\",\"connectionString\":\"Endpoint=sb://contososiempipe-ns.servicebus.windows.net/;SharedAccessKeyName=Send;SharedAccessKey=dummy=;EntityPath=dummy\",\"SasPolicyName\":\"dummy\"}]'
"""

helps['security automation validate'] = """
type: command
short-summary: Validates a security automation model before create or update.
examples:
  - name: Validates a security automation model before create or update.
    text: >
        az security automation validate -g Sample-RG -n sampleAutomation -l eastus --scopes '[{\"description\": \"Scope for 487bb485-b5b0-471e-9c0d-10717612f869\", \"scopePath\": \"/subscriptions/487bb485-b5b0-471e-9c0d-10717612f869\"}]' --sources '[{\"eventSource\":\"SubAssessments\",\"ruleSets\":null}]' --actions '[{\"actionType\":\"EventHub\",\"eventHubResourceId\":\"subscriptions/212f9889-769e-45ae-ab43-6da33674bd26/resourceGroups/ContosoSiemPipeRg/providers/Microsoft.EventHub/namespaces/contososiempipe-ns/eventhubs/surashed-test\",\"connectionString\":\"Endpoint=sb://contososiempipe-ns.servicebus.windows.net/;SharedAccessKeyName=Send;SharedAccessKey=dummy=;EntityPath=dummy\",\"SasPolicyName\":\"dummy\"}]'
"""

helps['security automation delete'] = """
type: command
short-summary: Deletes a security automation.
examples:
  - name: Deletes a security automation.
    text: >
        az security automation delete -g 'sampleRg' -n 'sampleAutomation'
"""

helps['security automation-scope'] = """
type: group
short-summary: Creates security automation scope.
"""

helps['security automation-scope create'] = """
type: command
short-summary: Creates security automation scope.
examples:
  - name: Creates security automation scope.
    text: >
        az security automation-scope create --description 'this is a sample description' --scope-path '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/'
"""

helps['security automation-rule'] = """
type: group
short-summary: Creates security automation rule.
"""

helps['security automation-rule create'] = """
type: command
short-summary: Creates security automation rule.
examples:
  - name: Creates security automation rule.
    text: >
        az security automation-rule create --expected-value 'High' --operator 'Equals' --property-j-path 'properties.metadata.severity' --property-type 'string'
"""

helps['security automation-rule-set'] = """
type: group
short-summary: Creates security automation rule set.
"""

helps['security automation-rule-set create'] = """
type: command
short-summary: Creates security automation rule set.
examples:
  - name: Creates security automation rule set.
    text: >
        az security automation-rule-set create
"""

helps['security automation-source'] = """
type: group
short-summary: Creates security automation source.
"""

helps['security automation-source create'] = """
type: command
short-summary: Creates security automation source.
examples:
  - name: Creates security automation source.
    text: >
        az security automation-source create --event-source 'Assessments'
"""

helps['security automation-action-logic-app'] = """
type: group
short-summary: Creates security automation logic app action.
"""

helps['security automation-action-logic-app create'] = """
type: command
short-summary: Creates security automation logic app action.
examples:
  - name: Creates security automation logic app action.
    text: >
        az security automation-action-logic-app create --logic-app-resource-id '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/resourceGroups/sample-rg/providers/Microsoft.Logic/workflows/LA' --uri 'https://ms.portal.azure.com/'
"""

helps['security automation-action-event-hub'] = """
type: group
short-summary: Creates security automation event hub action.
"""

helps['security security-solutions'] = """
type: group
short-summary: Display all security solutions at the subscription level.
"""

helps['security security-solutions list'] = """
type: command
short-summary: Display all security solutions at the subscription level.
examples:
  - name: Display all security solutions.
    text: >
        az security security-solutions list
"""

helps['security automation-action-event-hub create'] = """
type: command
short-summary: Creates security automation event hub action.
examples:
  - name: Creates security automation event hub action.
    text: >
        az security automation-action-event-hub create --event-hub-resource-id '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/resourceGroups/sample-rg/providers/Microsoft.EventHub/namespaces/evenhubnamespace1/eventhubs/evenhubname1' --connection-string 'Endpoint=sb://dummy/;SharedAccessKeyName=dummy;SharedAccessKey=dummy;EntityPath=dummy' --sas-policy-name 'Send'
"""

helps['security automation-action-workspace'] = """
type: group
short-summary: Creates security automation workspace action.
"""

helps['security automation-action-workspace create'] = """
type: command
short-summary: Creates security automation workspace action.
examples:
  - name: Creates security automation workspace action.
    text: >
        az security automation-action-workspace create --workspace-resource-id '/subscriptions/03b601f1-7eca-4496-8f8d-355219eee254/resourcegroups/sample-rg/providers/microsoft.operationalinsights/workspaces/sampleworkspace'
"""

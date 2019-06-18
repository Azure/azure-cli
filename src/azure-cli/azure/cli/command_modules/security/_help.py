# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps['security'] = """
    type: group
    short-summary: Manage your security posture with Azure Security Center.
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
helps['security contact'] = """
    type: group
    short-summary: View your security contacts.
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
              az security auto-provisioning-setting update -n "default" --auto-provision "on"
        - name: Turns off automatic provisioning on the subscription.
          text: >
              az security auto-provisioning-setting update -n "default" --auto-provision "off"
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
    short-summary: Shows the Azure Security Center Home region location.
"""
helps['security location list'] = """
    type: command
    short-summary: Shows the Azure Security Center Home region location.
    examples:
        - name: Shows the Azure Security Center Home region location.
          text: >
              az security location list
"""
helps['security location show'] = """
    type: command
    short-summary: Shows the Azure Security Center Home region location.
    examples:
        - name: Shows the Azure Security Center Home region location.
          text: >
              az security location show -n centralus
"""
helps['security pricing'] = """
    type: group
    short-summary: Shows the Azure Security Center Pricing tier for the subscription.
"""
helps['security pricing list'] = """
    type: command
    short-summary: Shows the Azure Security Center Pricing tier for the subscription.
    examples:
        - name: Shows the Azure Security Center Pricing tier for the subscription.
          text: >
              az security pricing list
"""
helps['security pricing show'] = """
    type: command
    short-summary: Shows the Azure Security Center Pricing tier for the subscription.
    examples:
        - name: Shows the Azure Security Center Pricing tier for the subscription.
          text: >
              az security pricing show -n default
"""
helps['security pricing create'] = """
    type: command
    short-summary: Updates the Azure Security Center Pricing tier for the subscription.
    examples:
        - name: Updates the Azure Security Center Pricing tier for the subscription.
          text: >
              az security pricing create -n default --tier 'standard'
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

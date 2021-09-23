# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['logicapp'] = """
type: group
short-summary: Manage logic apps.
"""

helps['logicapp create'] = """
type: command
short-summary: Create a logic app.
long-summary: The logic app's name must be able to produce a unique FQDN as AppName.azurewebsites.net.
examples:
  - name: Create a basic logic app.
    text: >
        az logicapp create -g MyResourceGroup --subscription MySubscription -p MyPlan -n MyUniqueAppName -s MyStorageAccount
"""

helps['logicapp delete'] = """
type: command
short-summary: Delete a logic app.
examples:
  - name: Delete a logic app.
    text: az logicapp delete --name MyLogicapp --resource-group MyResourceGroup --subscription MySubscription
"""

helps['logicapp show'] = """
type: command
short-summary: Get the details of a logic app.
examples:
  - name: Get the details of a logic app.
    text: az logicapp show --name MyLogicapp --resource-group MyResourceGroup --subscription MySubscription
"""

helps['logicapp list'] = """
type: command
short-summary: List logic apps.
examples:
  - name: List default host name and state for all logic apps.
    text: >
        az logicapp list --query "[].{hostName: defaultHostName, state: state}"
  - name: List all running logic apps.
    text: >
        az logicapp list --query "[?state=='Running']"
"""

helps['logicapp restart'] = """
type: command
short-summary: Restart a logic app.
examples:
  - name: Restart a logic app.
    text: az logicapp restart --name MyLogicApp --resource-group MyResourceGroup
    crafted: true
"""

helps['logicapp start'] = """
type: command
short-summary: Start a logic app.
examples:
  - name: Start a logic app
    text: az logicapp start --name MyLogicApp --resource-group MyResourceGroup
    crafted: true
"""

helps['logicapp stop'] = """
type: command
short-summary: Stop a logic app.
examples:
  - name: Stop a logic app.
    text: az logicapp stop --name MyLogicApp --resource-group MyResourceGroup
    crafted: true
"""

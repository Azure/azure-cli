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

helps['logicapp config'] = """
type: group
short-summary: Configure a logic app.
"""

helps['logicapp config appsettings'] = """
type: group
short-summary: Configure logic app settings.
"""

helps['logicapp config appsettings delete'] = """
type: command
short-summary: Delete a logic app's settings.
examples:
  - name: Delete a logic app's settings.
    text: az logicapp config appsettings delete --name MyLogicApp --resource-group MyResourceGroup --setting-names {setting-names}
"""

helps['logicapp config appsettings list'] = """
type: command
short-summary: Show settings for a logic app.
examples:
  - name: Show settings for a logic app.
    text: az logicapp config appsettings list --name MyLogicapp --resource-group MyResourceGroup
"""

helps['logicapp config appsettings set'] = """
type: command
short-summary: Update a logic app's settings.
examples:
  - name: Update a logic app's settings.
    text: |
        az logicapp config appsettings set --name MyLogicApp --resource-group MyResourceGroup --settings "AzureWebJobsStorage=$storageConnectionString"
"""

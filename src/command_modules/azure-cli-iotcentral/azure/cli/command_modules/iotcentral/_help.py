# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long

helps['iotcentral'] = """
    type: group
    short-summary: Manage IoT Central assets.
"""

helps['iotcentral app'] = """
    type: group
    short-summary: Manage IoT Central applications.
"""

helps['iotcentral app create'] = """
    type: command
    short-summary: Create an IoT Central application.
    long-summary: For an introduction to IoT Central, see https://docs.microsoft.com/en-us/azure/iot-central/
    examples:
        - name: Create an IoT Central application with the free pricing tier F1, in the region of the resource group.
          text: >
            az iotcentral app create --resource-group MyResourceGroup --name MyApp --subdomain myapp
        - name: Create an IoT Central application with the standard pricing tier S1 in the 'westus' region.
          text: >
            az iotcentral app create --resource-group MyResourceGroup --name MyApp --sku S1 --location westus
            --subdomain myapp
"""

helps['iotcentral app show'] = """
    type: command
    short-summary: Get the details of an IoT Central application.
    examples:
        - name: Show an IoT Central application.
          text: >
            az iotcentral app show --name MyApp
"""

helps['iotcentral app update'] = """
    type: command
    short-summary: Update metadata for an IoT Central application.
"""

helps['iotcentral app list'] = """
    type: command
    short-summary: List IoT Central applications.
    examples:
        - name: List all IoT Central applications in a subscription.
          text: >
            az iotcentral app list
        - name: List all IoT Central applications in the resource group 'MyGroup'
          text: >
            az iotcentral app list --resource-group MyGroup
"""

helps['iotcentral app delete'] = """
    type: command
    short-summary: Delete an IoT Central application.
"""

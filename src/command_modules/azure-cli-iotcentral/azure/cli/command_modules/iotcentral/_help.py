# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["iotcentral app update"] = """
"type": |-
    command
"short-summary": |-
    Update metadata for an IoT Central application.
"""

helps["iotcentral"] = """
"type": |-
    group
"short-summary": |-
    Manage IoT Central assets.
"""

helps["iotcentral app show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an IoT Central application.
"""

helps["iotcentral app list"] = """
"type": |-
    command
"short-summary": |-
    List IoT Central applications.
"""

helps["iotcentral app create"] = """
"type": |-
    command
"short-summary": |-
    Create an IoT Central application.
"long-summary": |
    For an introduction to IoT Central, see https://docs.microsoft.com/en-us/azure/iot-central/.
    The F1 Sku is no longer supported. Please use the S1 Sku (default) for app creation.
    For more pricing information, please visit https://azure.microsoft.com/en-us/pricing/details/iot-central/.
"""

helps["iotcentral app"] = """
"type": |-
    group
"short-summary": |-
    Manage IoT Central applications.
"""

helps["iotcentral app delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an IoT Central application.
"examples":
-   "name": |-
        Delete an IoT Central application.
    "text": |-
        az iotcentral app delete --resource-group MyResourceGroup --name MyIoTCentralApplication
"""


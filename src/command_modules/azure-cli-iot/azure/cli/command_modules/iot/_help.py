#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['iot'] = """
    type: group
    short-summary: Connect, monitor, and control millions of IoT assets
"""

helps['iot hub create'] = """
            type: command
            short-summary: Create an Azure IoT Hub.
            long-summary: See https://azure.microsoft.com/en-us/services/iot-hub/ for an intro to Azure IoT Hub.
"""

helps['iot hub list'] = """
            type: command
            short-summary: List IoT Hubs in your subscription or resource group.
            long-summary: When resource group is specified, IoT Hubs in target resource group will be listed.
                        Otherwise, IoT Hubs in your subscription will be listed.
"""

helps['iot hub show-connection-string'] = """
            type: command
            short-summary: Show connection string of target Azure IoT Hub.
"""

helps['iot device create'] = """
            type: command
            short-summary: Register a device in your Azure IoT Hub.
"""

helps['iot device list'] = """
            type: command
            short-summary: List devices in target Azure IoT Hub.
"""

helps['iot device show-connection-string'] = """
            type: command
            short-summary: Show connection string of a device in target Azure IoT Hub.
"""

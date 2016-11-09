#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['iot'] = """
    type: group
    short-summary: Connect, monitor, and control millions of IoT assets
"""

helps['iot hub'] = """
    type: group
    short-summary: Manage IoT Hubs.
"""

helps['iot hub create'] = """
    type: command
    short-summary: Create an Azure IoT Hub.
    long-summary: See https://azure.microsoft.com/en-us/services/iot-hub/ for an intro to Azure IoT Hub.
"""

helps['iot hub show'] = """
    type: command
    short-summary: Show non-security metadata of an IoT Hub.
"""

helps['iot hub list'] = """
    type: command
    short-summary: List IoT Hubs in your subscription or resource group.
    long-summary: If resource group is provided, IoT Hubs in target resource group will be listed.
                Otherwise, IoT Hubs in your subscription will be listed.
"""

helps['iot hub show-connection-string'] = """
    type: command
    short-summary: Show connection string of an IoT Hub.
    long-summary: If resource group and IoT Hub name are not provided, connection strings for all IoT Hubs in your subscription will be returned.
                If only resource group is provided, connection strings for all IoT Hubs in the resource group will be returned.
                If both resource group and IoT Hub name are provided, connection string of the IoT Hub will be returned.
"""

helps['iot hub consumer-group'] = """
    type: group
    short-summary: Manage event hub consumer groups of an IoT Hub.
"""

helps['iot hub consumer-group create'] = """
    type: command
    short-summary: Create an event hub consumer group.
"""

helps['iot hub consumer-group list'] = """
    type: command
    short-summary: List all event hub consumer groups.
"""

helps['iot hub consumer-group show'] = """
    type: command
    short-summary: Get an event hub consumer group.
"""

helps['iot hub consumer-group delete'] = """
    type: command
    short-summary: Delete an event hub consumer group.
"""

helps['iot hub key'] = """
    type: group
    short-summary: Manage shared access policies of an IoT Hub.
"""

helps['iot hub key list'] = """
    type: command
    short-summary: List all shared access policies of an IoT Hub.
"""

helps['iot hub key show'] = """
    type: command
    short-summary: Get a shared access policy of an IoT Hub.
"""

helps['iot hub list-skus'] = """
    type: command
    short-summary: List all valid pricing tiers.
"""

helps['iot device'] = """
    type: group
    short-summary: Manage devices attached to an IoT Hub.
"""

helps['iot device create'] = """
    type: command
    short-summary: Register a device in an IoT Hub.
    examples:
        - name: Create a device authenticating with symmetric key.
          text: >
            az iot device create --hub-name my-iot-hub --device-id my-device
        - name: Create a device authenticating with existing X.509 certificate.
          text: >
            az iot device create --hub-name my-iot-hub --device-id my-device --x509 --primary-thumbprint X.509_certificate_thumbprint
        - name: Create a device authenticating with self-signed X.509 certificate,
                which will be generated and output to current directory.
          text: >
            az iot device create --hub-name my-iot-hub --device-id my-device --x509
        - name: Create a device authenticating with self-signed X.509 certificate, which will be valid for 100 days.
          text: >
            az iot device create --hub-name my-iot-hub --device-id my-device --x509 --valid-days 100
        - name: Create a device authenticating with self-signed X.509 certificate,
                which will be generated and output to specified directory.
          text: >
            az iot device create --hub-name my-iot-hub --device-id my-device --x509 --output-directory /path/to/output
"""

helps['iot device show'] = """
    type: command
    short-summary: Show metadata of a device in an IoT Hub.
"""

helps['iot device list'] = """
    type: command
    short-summary: List devices in an IoT Hub.
"""

helps['iot device delete'] = """
    type: command
    short-summary: Delete a device from an IoT Hub.
"""

helps['iot device show-connection-string'] = """
    type: command
    short-summary: Show connection string of device(s) in an IoT Hub.
    long-summary: If device id is not provided, connection strings for all devices in your IoT Hub will be returned.
                Otherwise, connection string of target device will be returned.
"""

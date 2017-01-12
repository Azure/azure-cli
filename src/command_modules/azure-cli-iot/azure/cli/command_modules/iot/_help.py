# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['iot'] = """
    type: group
    short-summary: Commands to connect, monitor, and control millions of IoT assets
    long-summary: If you don't have the iot component installed, add it with `az component update --add iot`
"""

helps['iot device'] = """
    type: group
    short-summary: Commands to manage devices in your IoT hub
"""

helps['iot hub'] = """
    type: group
    short-summary: Commands to manage IoT Hubs.
"""

helps['iot hub create'] = """
    type: command
    short-summary: Create an Azure IoT Hub.
    long-summary: See https://azure.microsoft.com/en-us/services/iot-hub/ for an intro to Azure IoT Hub.
    examples:
        - name: Create an IoT Hub with free pricing tier F1, in the region of resource group.
          text: >
            az iot hub create --resource-group my-resource-group --name my-iot-hub
        - name: Create an IoT Hub with standard pricing tier S1, in the region of resource group.
          text: >
            az iot hub create --resource-group my-resource-group --name my-iot-hub --sku S1
        - name: Create an IoT Hub with free pricing tier F1, in `westus` region.
          text: >
            az iot hub create --resource-group my-resource-group --name my-iot-hub --location westus
"""

helps['iot hub show'] = """
    type: command
    short-summary: Show non-security metadata of an IoT Hub.
"""

helps['iot hub update'] = """
    type: command
    short-summary: Update non-security metadata of an IoT Hub.
    examples:
        - name: Add a new IP filter rule.
          text: >
            az iot hub update --name my-iot-hub --add properties.ipFilterRules filter_name=test-rule action=Accept ip_mask=127.0.0.0/31
            az iot hub update --name my-iot-hub --add properties.ipFilterRules filter_name=test-rule action=Reject ip_mask=127.0.0.0/31
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
    examples:
        - name: Show connection string of an IoT Hub using default policy (`iothubowner`) and primary key.
          text: >
            az iot hub show-connection-string --name my-iot-hub
        - name: Show connection string of an IoT Hub using policy `service` and secondary key.
          text: >
            az iot hub show-connection-string --name my-iot-hub --policy-name service --key secondary
        - name: Show connection strings of all IoT Hubs in a resource group.
          text: >
            az iot hub show-connection-string --resource-group my-resource-group
        - name: Show connection strings of all IoT Hubs in current subscription.
          text: >
            az iot hub show-connection-string
"""

helps['iot hub delete'] = """
    type: command
    short-summary: Delete an IoT Hub.
"""

helps['iot hub consumer-group'] = """
    type: group
    short-summary: Manage event hub consumer groups of an IoT Hub.
"""

helps['iot hub consumer-group create'] = """
    type: command
    short-summary: Create an event hub consumer group.
    examples:
        - name: Create new consumer group `cg1` in default event hub endpoint `events`.
          text: >
            az iot hub consumer-group create --hub-name my-iot-hub --name cg1
        - name: Create new consumer group `cg1` in operation monitoring event hub endpoint `operationsMonitoringEvents`.
          text: >
            az iot hub consumer-group create --hub-name my-iot-hub --event-hub-name operationsMonitoringEvents --name cg1
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

helps['iot hub policy'] = """
    type: group
    short-summary: Manage shared access policies of an IoT Hub.
"""

helps['iot hub policy list'] = """
    type: command
    short-summary: List all shared access policies of an IoT Hub.
"""

helps['iot hub policy show'] = """
    type: command
    short-summary: Get a shared access policy of an IoT Hub.
"""

helps['iot hub policy create'] = """
    type: command
    short-summary: Create a new shared access policy in an IoT Hub.
    examples:
        - name: Create a new shared access policy
          text: >
            az iot hub policy create --hub-name my-iot-hub --name new-policy --permissions RegistryWrite ServiceConnect DeviceConnect
"""

helps['iot hub policy delete'] = """
    type: command
    short-summary: Delete a shared access policy from an IoT Hub.
"""

helps['iot hub list-skus'] = """
    type: command
    short-summary: List all valid pricing tiers.
"""

helps['iot hub job'] = """
    type: group
    short-summary: Manage jobs in an IoT Hub.
"""

helps['iot hub job list'] = """
    type: command
    short-summary: List all jobs in an IoT Hub.
"""

helps['iot hub job show'] = """
    type: command
    short-summary: Show a job in an IoT Hub.
"""

helps['iot hub job cancel'] = """
    type: command
    short-summary: Cancel a job in an IoT Hub.
"""

helps['iot hub show-quota-metrics'] = """
    type: command
    short-summary: Show quota metrics for an IoT Hub.
"""

helps['iot hub show-stats'] = """
    type: command
    short-summary: Show stats of an IoT Hub.
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
            az iot device create --hub-name my-iot-hub --device-id my-device --x509 --output-dir /path/to/output
"""

helps['iot device show'] = """
    type: command
    short-summary: Show metadata of a device in an IoT Hub.
"""

helps['iot device update'] = """
    type: command
    short-summary: Update metadata of a device in an IoT Hub.
    examples:
        - name: Disable a device.
          text: >
            az iot device update --hub-name my-iot-hub --device-id my-device --set status=disabled
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
    examples:
        - name: Show connection string of a device in an IoT Hub using primary key.
          text: >
            az iot device show-connection-string --hub-name my-iot-hub --device-id my-device
        - name: Show connection string of a device in an IoT Hub using secondary key.
          text: >
            az iot device show-connection-string --hub-name my-iot-hub --device-id my-device --key secondary
        - name: Show connection strings of default number of devices in an IoT Hub using primary key.
          text: >
            az iot device show-connection-string --hub-name my-iot-hub
        - name: Show connection strings of top 100 devices in an IoT Hub using primary key.
          text: >
            az iot device show-connection-string --hub-name my-iot-hub --top 100
"""

helps['iot device message'] = """
    type: group
    short-summary: IoT device messaging commands.
"""

helps['iot device message send'] = """
    type: command
    short-summary: Send a device-to-cloud message.
    examples:
        - name: Send a device-to-cloud message to IoT Hub with default message.
          text: >
            az iot device message send --hub-name my-iot-hub --device-id my-device
        - name: Send a device-to-cloud message to IoT Hub with custom message.
          text: >
            az iot device message send --hub-name my-iot-hub --device-id my-device --data "Custom Message"
"""

helps['iot device message receive'] = """
    type: command
    short-summary: Receive a cloud-to-device message.
    examples:
        - name: Receive a cloud-to-device message from IoT Hub with default lock timeout.
          text: >
            az iot device message receive --hub-name my-iot-hub --device-id my-device
        - name: Receive a cloud-to-device message from IoT Hub with lock timeout of 300 seconds.
          text: >
            az iot device message receive --hub-name my-iot-hub --device-id my-device --lock-timeout 300
"""

helps['iot device message complete'] = """
    type: command
    short-summary: Complete a cloud-to-device message.
"""

helps['iot device message reject'] = """
    type: command
    short-summary: Reject a cloud-to-device message.
"""

helps['iot device message abandon'] = """
    type: command
    short-summary: Abandon a cloud-to-device message.
"""

helps['iot device export'] = """
    type: command
    short-summary: Exports all the device identities in the IoT hub identity registry to an Azure Storage blob container.
    long-summary: For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities.
"""

helps['iot device import'] = """
    type: command
    short-summary: Import, update, or delete device identities in the IoT hub identity registry from a blob.
    long-summary: For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities.
"""

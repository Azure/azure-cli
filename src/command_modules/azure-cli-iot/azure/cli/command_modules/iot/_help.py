# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['iot'] = """
    type: group
    short-summary: Connect, monitor, and control millions of IoT assets.
    long-summary: If you don't have the iot component installed, add it with `az component update --add iot`.
    long-summary: These commands are in preview.
"""

helps['iot device'] = """
    type: group
    short-summary: Manage devices in your Azure IoT hub.
    long-summary: These commands are in preview.
"""

helps['iot hub'] = """
    type: group
    short-summary: Manage Azure IoT Hubs.
    long-summary: These commands are in preview.
"""

helps['iot hub create'] = """
    type: command
    short-summary: Create an Azure IoT Hub.
    long-summary: For an introduction to Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/.
    examples:
        - name: Create an IoT Hub with the free pricing tier F1, in the region of the resource group.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub
        - name: Create an IoT Hub with the standard pricing tier S1, in the region of the resource group.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub --sku S1
        - name: Create an IoT Hub with the free pricing tier F1, in the `westus` region.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub --location westus
"""

helps['iot hub show'] = """
    type: command
    short-summary: Show non-security metadata of an IoT Hub.
"""

helps['iot hub update'] = """
    type: command
    short-summary: Update non-security metadata of an IoT Hub.
    examples:
        - name: Add an IP filter rule.
          text: >
            az iot hub update --name MyIotHub --add properties.ipFilterRules filter_name=test-rule action=Accept ip_mask=127.0.0.0/31
            az iot hub update --name MyIotHub --add properties.ipFilterRules filter_name=test-rule action=Reject ip_mask=127.0.0.0/31
"""

helps['iot hub list'] = """
    type: command
    short-summary: List IoT Hubs.
    long-summary: If the resource group is provided, IoT Hubs in the target resource group are listed. Otherwise, IoT Hubs in your subscription are listed.
"""

helps['iot hub show-connection-string'] = """
    type: command
    short-summary: Show the connection string of an IoT Hub.
    long-summary: If resource group and IoT Hub name are not provided, connection strings for all IoT Hubs in your subscription are returned. If only the resource group is provided, connection strings for all IoT Hubs in the resource group are returned. If both resource group and IoT Hub name are provided, the connection string of the IoT Hub is returned.
    examples:
        - name: Show the connection string of an IoT Hub using default policy (`iothubowner`) and primary key.
          text: >
            az iot hub show-connection-string --name MyIotHub
        - name: Show the connection string of an IoT Hub using policy `service` and secondary key.
          text: >
            az iot hub show-connection-string --name MyIotHub --policy-name service --key secondary
        - name: Show the connection strings of all IoT Hubs in a resource group.
          text: >
            az iot hub show-connection-string --resource-group MyResourceGroup
        - name: Show the connection strings of all IoT Hubs in a subscription.
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
    long-summary: These commands are in preview.
"""

helps['iot hub consumer-group create'] = """
    type: command
    short-summary: Create an event hub consumer group.
    examples:
        - name: Create a consumer group `cg1` in the default event hub endpoint `events`.
          text: >
            az iot hub consumer-group create --hub-name MyIotHub --name cg1
        - name: Create a consumer group `cg1` in the operation monitoring event hub endpoint `operationsMonitoringEvents`.
          text: >
            az iot hub consumer-group create --hub-name MyIotHub --event-hub-name operationsMonitoringEvents --name cg1
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
    long-summary: These commands are in preview.
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
        - name: Create a new shared access policy.
          text: >
            az iot hub policy create --hub-name MyIotHub --name new-policy --permissions RegistryWrite ServiceConnect DeviceConnect
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
    long-summary: These commands are in preview.
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
    short-summary: Show statistics of an IoT Hub.
"""

helps['iot device create'] = """
    type: command
    short-summary: Register a device in an IoT Hub.
    examples:
        - name: Create a device authenticating with symmetric key.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice
        - name: Create a device authenticating with existing X.509 certificate.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509 --primary-thumbprint X.509_certificate_thumbprint
        - name: Create a device authenticating with self-signed X.509 certificate, which is put into to the current directory.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509
        - name: Create a device authenticating with self-signed X.509 certificate, which is valid for 100 days.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509 --valid-days 100
        - name: Create a device authenticating with self-signed X.509 certificate, which is put into the specified directory.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509 --output-dir /path/to/output
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
            az iot device update --hub-name MyIotHub --device-id MyDevice --set status=disabled
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
    short-summary: Show the connection string of devices in an IoT Hub.
    long-summary: If the device identifier is not provided, connection strings for all devices in your IoT Hub are returned. Otherwise, the connection string of the target device is returned.
    examples:
        - name: Show the connection string of a device in an IoT Hub using primary key.
          text: >
            az iot device show-connection-string --hub-name MyIotHub --device-id MyDevice
        - name: Show the connection string of a device in an IoT Hub using secondary key.
          text: >
            az iot device show-connection-string --hub-name MyIotHub --device-id MyDevice --key secondary
        - name: Show the connection strings of the default devices in an IoT Hub using primary key.
          text: >
            az iot device show-connection-string --hub-name MyIotHub
        - name: Show the connection strings of the top 100 devices in an IoT Hub using primary key.
          text: >
            az iot device show-connection-string --hub-name MyIotHub --top 100
"""

helps['iot device message'] = """
    type: group
    short-summary: Manage IoT device messaging.
    long-summary: These commands are in preview.
"""

helps['iot device message send'] = """
    type: command
    short-summary: Send a device-to-cloud message.
    examples:
        - name: Send a device-to-cloud message to an IoT Hub with a default message.
          text: >
            az iot device message send --hub-name MyIotHub --device-id MyDevice
        - name: Send a device-to-cloud message to an IoT Hub with a custom message.
          text: >
            az iot device message send --hub-name MyIotHub --device-id MyDevice --data "Custom Message"
"""

helps['iot device message receive'] = """
    type: command
    short-summary: Receive a cloud-to-device message.
    examples:
        - name: Receive a cloud-to-device message from an IoT Hub with a default lock timeout.
          text: >
            az iot device message receive --hub-name MyIotHub --device-id MyDevice
        - name: Receive a cloud-to-device message from an IoT Hub with a lock timeout of 300 seconds.
          text: >
            az iot device message receive --hub-name MyIotHub --device-id MyDevice --lock-timeout 300
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
    short-summary: Export all the device identities in the IoT hub identity registry to an Azure Storage blob container.
    long-summary: For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities.
"""

helps['iot device import'] = """
    type: command
    short-summary: Import, update, or delete device identities in the IoT hub identity registry from a blob.
    long-summary: For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities.
"""

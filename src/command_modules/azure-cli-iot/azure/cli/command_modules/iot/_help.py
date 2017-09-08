# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

helps['iot'] = """
    type: group
    short-summary: (PREVIEW) Manage Internet of Things (IoT) assets.
"""

helps['iot device'] = """
    type: group
    short-summary: (PREVIEW) Manage devices in your Azure IoT hub.
"""

helps['iot hub'] = """
    type: group
    short-summary: (PREVIEW) Manage Azure IoT hubs.
"""

helps['iot hub create'] = """
    type: command
    short-summary: Create an Azure IoT hub.
    long-summary: 'For an introduction to Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/'
    examples:
        - name: Create an IoT Hub with the free pricing tier F1, in the region of the resource group.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub
        - name: Create an IoT Hub with the standard pricing tier S1, in the 'westus' region.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub --sku S1 --location westus
"""

helps['iot hub show'] = """
    type: command
    short-summary: Get the details of an IoT hub.
"""

helps['iot hub update'] = """
    type: command
    short-summary: Update metadata for an IoT hub.
    examples:
        - name: Add a firewall filter rule to accept traffic from the IP mask 127.0.0.0/31.
          text: >
            az iot hub update --name MyIotHub --add properties.ipFilterRules filter_name=test-rule action=Accept ip_mask=127.0.0.0/31
"""

helps['iot hub list'] = """
    type: command
    short-summary: List IoT hubs.
    examples:
        - name: List all IoT hubs in a subscription.
          text: >
            az iot hub list
        - name: List all IoT hubs in the resource group 'MyGroup'
          text: >
            az iot hub list --resource-group MyGroup
"""

helps['iot hub show-connection-string'] = """
    type: command
    short-summary: Show the connection strings for an IoT hub.
    examples:
        - name: Show the connection string of an IoT hub using default policy and primary key.
          text: >
            az iot hub show-connection-string --name MyIotHub
        - name: Show the connection string of an IoT Hub using policy 'service' and secondary key.
          text: >
            az iot hub show-connection-string --name MyIotHub --policy-name service --key secondary
        - name: Show the connection strings for all IoT hubs in a resource group.
          text: >
            az iot hub show-connection-string --resource-group MyResourceGroup
        - name: Show the connection strings for all IoT hubs in a subscription.
          text: >
            az iot hub show-connection-string
"""

helps['iot hub delete'] = """
    type: command
    short-summary: Delete an IoT hub.
"""

helps['iot hub consumer-group'] = """
    type: group
    short-summary: (PREVIEW) Manage the event hub consumer groups of an IoT hub.
"""

helps['iot hub consumer-group create'] = """
    type: command
    short-summary: Create an event hub consumer group.
    examples:
        - name: Create a consumer group 'cg1' in the default event hub endpoint.
          text: >
            az iot hub consumer-group create --hub-name MyIotHub --name cg1
        - name: Create a consumer group `cg1` in the operation monitoring event hub endpoint `operationsMonitoringEvents`.
          text: >
            az iot hub consumer-group create --hub-name MyIotHub --event-hub-name operationsMonitoringEvents --name cg1
"""

helps['iot hub consumer-group list'] = """
    type: command
    short-summary: List event hub consumer groups.
"""

helps['iot hub consumer-group show'] = """
    type: command
    short-summary: Get the details for an event hub consumer group.
"""

helps['iot hub consumer-group delete'] = """
    type: command
    short-summary: Delete an event hub consumer group.
"""

helps['iot hub policy'] = """
    type: group
    short-summary: (PREVIEW) Manage shared access policies of an IoT hub.
"""

helps['iot hub policy list'] = """
    type: command
    short-summary: List shared access policies of an IoT hub.
"""

helps['iot hub policy show'] = """
    type: command
    short-summary: Get the details of a shared access policy of an IoT hub.
"""

helps['iot hub policy create'] = """
    type: command
    short-summary: Create a new shared access policy in an IoT hub.
    examples:
        - name: Create a new shared access policy.
          text: >
            az iot hub policy create --hub-name MyIotHub --name new-policy --permissions RegistryWrite ServiceConnect DeviceConnect
"""

helps['iot hub policy delete'] = """
    type: command
    short-summary: Delete a shared access policy from an IoT hub.
"""

helps['iot hub list-skus'] = """
    type: command
    short-summary: List available pricing tiers.
"""

helps['iot hub job'] = """
    type: group
    short-summary: (PREVIEW) Manage jobs in an IoT hub.
"""

helps['iot hub job list'] = """
    type: command
    short-summary: List the jobs in an IoT hub.
"""

helps['iot hub job show'] = """
    type: command
    short-summary: Get the details of a job in an IoT hub.
"""

helps['iot hub job cancel'] = """
    type: command
    short-summary: Cancel a job in an IoT hub.
"""

helps['iot hub show-quota-metrics'] = """
    type: command
    short-summary: Get the quota metrics for an IoT hub.
"""

helps['iot hub show-stats'] = """
    type: command
    short-summary: Get the statistics for an IoT hub.
"""

helps['iot device create'] = """
    type: command
    short-summary: Register a device for an IoT hub.
    examples:
        - name: Create a device authenticating with symmetric key.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice
        - name: Create a device authenticating with an existing X.509 certificate.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509 --primary-thumbprint X.509_certificate_thumbprint
        - name: Create a device authenticating with a self-signed X.509 certificate, which is put into to the current directory.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509
        - name: Create a device authenticating with a self-signed X.509 certificate that is valid for 100 days.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509 --valid-days 100
        - name: Create a device authenticating with a self-signed X.509 certificate, and write the certificate to /path/to/output.
          text: >
            az iot device create --hub-name MyIotHub --device-id MyDevice --x509 --output-dir /path/to/output
"""

helps['iot device show'] = """
    type: command
    short-summary: Get the details for a device in an IoT hub.
"""

helps['iot device update'] = """
    type: command
    short-summary: Update the metadata of a device in an IoT hub.
    examples:
        - name: Disable a device.
          text: >
            az iot device update --hub-name MyIotHub --device-id MyDevice --set status=disabled
"""

helps['iot device list'] = """
    type: command
    short-summary: List devices in an IoT hub.
"""

helps['iot device delete'] = """
    type: command
    short-summary: Delete a device from an IoT hub.
"""

helps['iot device show-connection-string'] = """
    type: command
    short-summary: Show the connection strings for devices in an IoT hub.
    examples:
        - name: Show the connection string of a device in an IoT Hub using the primary key.
          text: >
            az iot device show-connection-string --hub-name MyIotHub --device-id MyDevice
        - name: Show the connection string of a device in an IoT Hub using the secondary key.
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
    short-summary: (PREVIEW) Manage IoT device messaging.
"""

helps['iot device message send'] = """
    type: command
    short-summary: Send a device-to-cloud message.
    examples:
        - name: Send a device-to-cloud message to an IoT hub with a default message.
          text: >
            az iot device message send --hub-name MyIotHub --device-id MyDevice
        - name: Send a device-to-cloud message to an IoT hub with a custom message.
          text: >
            az iot device message send --hub-name MyIotHub --device-id MyDevice --data "Custom Message"
"""

helps['iot device message receive'] = """
    type: command
    short-summary: Receive a cloud-to-device message.
    examples:
        - name: Receive a cloud-to-device message from an IoT hub with a default timeout.
          text: >
            az iot device message receive --hub-name MyIotHub --device-id MyDevice
        - name: Receive a cloud-to-device message from an IoT Hub with a timeout of 300 seconds.
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
    long-summary: 'For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities'
"""

helps['iot device import'] = """
    type: command
    short-summary: Import, update, or delete device identities in the IoT hub identity registry from a blob.
    long-summary: 'For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities'
"""

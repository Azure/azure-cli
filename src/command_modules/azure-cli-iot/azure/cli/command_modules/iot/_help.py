# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

from ._constants import certificate_help


helps['iot'] = """
    type: group
    short-summary: (PREVIEW) Manage Internet of Things (IoT) assets.
    long-summary: Comprehensive IoT data-plane functionality is available
                  in the Azure IoT CLI Extension. For more info and install guide
                  go to https://github.com/Azure/azure-iot-cli-extension
"""

helps['iot device'] = """
    type: group
    short-summary: (PREVIEW) Manage devices in your Azure IoT hub.
"""

helps['iot hub'] = """
    type: group
    short-summary: (PREVIEW) Manage Azure IoT hubs.
"""
helps['iot dps'] = """
    type: group
    short-summary: Manage Azure IoT Hub Device Provisioning Service.
"""

helps['iot dps create'] = """
    type: command
    short-summary: Create an Azure IoT Hub device provisioning service.
    long-summary: For an introduction to Azure IoT Hub Device Provisioning Service, see https://docs.microsoft.com/en-us/azure/iot-dps/about-iot-dps
    examples:
        - name: Create an Azure IoT Hub device provisioning service with the standard pricing tier S1, in the region of the resource group.
          text: >
            az iot dps create --name MyDps --resource-group MyResourceGroup
        - name: Create an Azure IoT Hub device provisioning service with the standard pricing tier S1, in the 'eastus' region.
          text: >
            az iot dps create --name MyDps --resource-group MyResourceGroup --location eastus
"""

helps['iot dps list'] = """
    type: command
    short-summary: List Azure IoT Hub device provisioning services.
    examples:
        - name: List all Azure IoT Hub device provisioning services in a subscription.
          text: >
            az iot dps list
        - name: List all Azure IoT Hub device provisioning services in the resource group 'MyResourceGroup'
          text: >
            az iot dps list --resource-group MyResourceGroup
"""

helps['iot dps show'] = """
    type: command
    short-summary: Get the details of an Azure IoT Hub device provisioning service.
    examples:
        - name: Show details of an Azure IoT Hub device provisioning service 'MyDps'
          text: >
            az iot dps show --name MyDps --resource-group MyResourceGroup
"""

helps['iot dps delete'] = """
    type: command
    short-summary: Delete an Azure IoT Hub device provisioning service.
    examples:
        - name: Delete an Azure IoT Hub device provisioning service 'MyDps'
          text: >
            az iot dps delete --name MyDps --resource-group MyResourceGroup
"""

helps['iot dps update'] = """
    type: command
    short-summary: Update an Azure IoT Hub device provisioning service.
    examples:
        - name: Update Allocation Policy to 'GeoLatency' of an Azure IoT Hub device provisioning service 'MyDps'
          text: >
            az iot dps update --name MyDps --resource-group MyResourceGroup --set properties.allocationPolicy="GeoLatency"
"""

helps['iot dps access-policy'] = """
    type: group
    short-summary: Manage Azure IoT Hub Device Provisioning Service access policies.
"""

helps['iot dps access-policy create'] = """
    type: command
    short-summary: Create a new shared access policy in an Azure IoT Hub device provisioning service.
    examples:
        - name: Create a new shared access policy in an Azure IoT Hub device provisioning service with EnrollmentRead right
          text: >
            az iot dps access-policy create --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy --rights EnrollmentRead
"""

helps['iot dps access-policy update'] = """
    type: command
    short-summary: Update a shared access policy in an Azure IoT Hub device provisioning service.
    examples:
        - name: Update access policy 'MyPolicy' in an Azure IoT Hub device provisioning service with EnrollmentWrite right
          text: >
            az iot dps access-policy update --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy --rights EnrollmentWrite
"""

helps['iot dps access-policy list'] = """
    type: command
    short-summary: List all shared access policies in an Azure IoT Hub device provisioning service.
    examples:
        - name: List all shared access policies in MyDps
          text: >
            az iot dps access-policy list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps access-policy show'] = """
    type: command
    short-summary: Show details of a shared access policies in an Azure IoT Hub device provisioning service.
    examples:
        - name: Show details of shared access policy 'MyPolicy' in an Azure IoT Hub device provisioning service
          text: >
            az iot dps access-policy show --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy
"""

helps['iot dps access-policy delete'] = """
    type: command
    short-summary: Delete a shared access policies in an Azure IoT Hub device provisioning service.
    examples:
        - name: Delete shared access policy 'MyPolicy' in an Azure IoT Hub device provisioning service
          text: >
            az iot dps access-policy delete --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy
"""

helps['iot dps linked-hub'] = """
    type: group
    short-summary: Manage Azure IoT Hub Device Provisioning Service linked IoT hubs.
"""

helps['iot dps linked-hub create'] = """
    type: command
    short-summary: Create a linked IoT hub in an Azure IoT Hub device provisioning service.
    examples:
        - name: Create a linked IoT hub in an Azure IoT Hub device provisioning service
          text: >
            az iot dps linked-hub create --dps-name MyDps --resource-group MyResourceGroup --connection-string
            HostName=test.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=XNBhoasdfhqRlgGnasdfhivtshcwh4bJwe7c0RIGuWsirW0=
            --location westus
        - name: Create a linked IoT hub in an Azure IoT Hub device provisioning service which applies allocation weight and weight being 10
          text: >
            az iot dps linked-hub create --dps-name MyDps --resource-group MyResourceGroup --connection-string
            HostName=test.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=XNBhoasdfhqRlgGnasdfhivtshcwh4bJwe7c0RIGuWsirW0=
            --location westus --allocation-weight 10 --apply-allocation-policy True
"""

helps['iot dps linked-hub update'] = """
    type: command
    short-summary: Update a linked IoT hub in an Azure IoT Hub device provisioning service.
    examples:
        - name: Update linked IoT hub 'MyLinkedHub.azure-devices.net' in an Azure IoT Hub device provisioning service
          text: >
            az iot dps linked-hub update --dps-name MyDps --resource-group MyResourceGroup --name MyLinkedHub.azure-devices.net
            --allocation-weight 10 --apply-allocation-policy True
"""

helps['iot dps linked-hub list'] = """
    type: command
    short-summary: List all linked IoT hubs in an Azure IoT Hub device provisioning service.
    examples:
        - name: List all linked IoT hubs in MyDps
          text: >
            az iot dps linked-hub list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps linked-hub show'] = """
    type: command
    short-summary: Show details of a linked IoT hub in an Azure IoT Hub device provisioning service.
    examples:
        - name: Show details of linked IoT hub 'MyLinkedHub' in an Azure IoT Hub device provisioning service
          text: >
            az iot dps linked-hub show --dps-name MyDps --resource-group MyResourceGroup --name MyLinkedHub
"""

helps['iot dps linked-hub delete'] = """
    type: command
    short-summary: Update a linked IoT hub in an Azure IoT Hub device provisioning service.
    examples:
        - name: Delete linked IoT hub 'MyLinkedHub' in an Azure IoT Hub device provisioning service
          text: >
            az iot dps linked-hub delete --dps-name MyDps --resource-group MyResourceGroup --name MyLinkedHub
"""

helps['iot dps certificate'] = """
    type: group
    short-summary: Manage Azure IoT Hub Device Provisioning Service certificates.
"""

helps['iot dps certificate create'] = """
    type: command
    short-summary: Create/upload an Azure IoT Hub Device Provisioning Service certificate.
    examples:
        - name: Upload a CA certificate PEM file to an Azure IoT Hub device provisioning service.
          text: >
            az iot dps certificate create --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/Certificate.pem
        - name: Upload a CA certificate CER file to an Azure IoT Hub device provisioning service.
          text: >
            az iot dps certificate create --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/Certificate.cer
"""

helps['iot dps certificate update'] = """
    type: command
    short-summary: Update an Azure IoT Hub Device Provisioning Service certificate.
    long-summary: Upload a new certificate to replace the existing certificate with the same name.
    examples:
        - name: Update a CA certificate in an Azure IoT Hub device provisioning service by uploading a new PEM file.
          text: >
            az iot dps certificate update --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate
            --path /certificates/NewCertificate.pem --etag AAAAAAAAAAA=
        - name: Update a CA certificate in an Azure IoT Hub device provisioning service by uploading a new CER file.
          text: >
            az iot dps certificate update --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate
            --path /certificates/NewCertificate.cer --etag AAAAAAAAAAA=
"""

helps['iot dps certificate delete'] = """
    type: command
    short-summary: Delete an Azure IoT Hub Device Provisioning Service certificate.
    examples:
        - name: Delete MyCertificate in an Azure IoT Hub device provisioning service
          text: >
            az iot dps certificate delete --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --etag AAAAAAAAAAA=
"""

helps['iot dps certificate show'] = """
    type: command
    short-summary: Show information about a particular Azure IoT Hub Device Provisioning Service certificate.
    examples:
        - name: Show details about MyCertificate in an Azure IoT Hub device provisioning service
          text: >
            az iot dps certificate show --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate
"""

helps['iot dps certificate list'] = """
    type: command
    short-summary: List all certificates contained within an Azure IoT Hub device provisioning service
    examples:
        - name: List all certificates in MyDps
          text: >
            az iot dps certificate list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps certificate generate-verification-code'] = """
    type: command
    short-summary: Generate a verification code for an Azure IoT Hub Device Provisioning Service certificate.
    long-summary: This verification code is used to complete the proof of possession step for a certificate. Use this
                  verification code as the CN of a new certificate signed with the root certificates private key.
    examples:
        - name: Generate a verification code for MyCertificate
          text: >
            az iot dps certificate generate-verification-code --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate
            --etag AAAAAAAAAAA=
"""

helps['iot dps certificate verify'] = """
    type: command
    short-summary: Verify an Azure IoT Hub Device Provisioning Service certificate.
    long-summary: Verify a certificate by uploading a verification certificate containing the verification code obtained
                  by calling generate-verification-code. This is the last step in the proof of possession process.
    examples:
        - name: Verify ownership of the MyCertificate private key.
          text: >
            az iot dps certificate verify --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate
            --path /certificates/Verification.pem --etag AAAAAAAAAAA=
"""

helps['iot hub certificate'] = """
    type: group
    short-summary: Manage IoT Hub certificates.
"""

helps['iot hub certificate create'] = """
    type: command
    short-summary: Create/upload an Azure IoT Hub certificate.
    long-summary: {0}
    examples:
        - name: Uploads a CA certificate PEM file to an IoT hub.
          text: >
            az iot hub certificate create --hub-name MyIotHub --name MyCertificate --path /certificates/Certificate.pem
        - name: Uploads a CA certificate CER file to an IoT hub.
          text: >
            az iot hub certificate create --hub-name MyIotHub --name MyCertificate --path /certificates/Certificate.cer
""".format(certificate_help)

helps['iot hub certificate update'] = """
    type: command
    short-summary: Update an Azure IoT Hub certificate.
    long-summary: Uploads a new certificate to replace the existing certificate with the same name. {0}
    examples:
        - name: Updates a CA certificate in an IoT hub by uploading a new PEM file.
          text: >
            az iot hub certificate update --hub-name MyIotHub --name MyCertificate --path /certificates/NewCertificate.pem --etag
            AAAAAAAAAAA=
        - name: Updates a CA certificate in an IoT hub by uploading a new CER file.
          text: >
            az iot hub certificate update --hub-name MyIotHub --name MyCertificate --path /certificates/NewCertificate.cer --etag
            AAAAAAAAAAA=
""".format(certificate_help)

helps['iot hub certificate delete'] = """
    type: command
    short-summary: Deletes an Azure IoT Hub certificate.
    long-summary: {0}
    examples:
        - name: Deletes MyCertificate
          text: >
            az iot hub certificate delete --hub-name MyIotHub --name MyCertificate --etag AAAAAAAAAAA=
""".format(certificate_help)

helps['iot hub certificate show'] = """
    type: command
    short-summary: Shows information about a particular Azure IoT Hub certificate.
    long-summary: {0}
    examples:
        - name: Show details about MyCertificate
          text: >
            az iot hub certificate show --hub-name MyIotHub --name MyCertificate
""".format(certificate_help)

helps['iot hub certificate list'] = """
    type: command
    short-summary: Lists all certificates contained within an Azure IoT Hub
    long-summary: {0}
    examples:
        - name: List all certificates in MyIotHub
          text: >
            az iot hub certificate list --hub-name MyIotHub
""".format(certificate_help)

helps['iot hub certificate generate-verification-code'] = """
    type: command
    short-summary: Generates a verification code for an Azure IoT Hub certificate.
    long-summary: This verification code is used to complete the proof of possession step for a certificate. Use this
                  verification code as the CN of a new certificate signed with the root certificates private key. {0}
    examples:
        - name: Generates a verification code for MyCertificate
          text: >
            az iot hub certificate generate-verification-code --hub-name MyIotHub --name MyCertificate --etag
            AAAAAAAAAAA=
""".format(certificate_help)

helps['iot hub certificate verify'] = """
    type: command
    short-summary: Verifies an Azure IoT Hub certificate.
    long-summary: Verifies a certificate by uploading a verification certificate containing the verification code obtained
                  by calling generate-verification-code. This is the last step in the proof of possession process. {0}
    examples:
        - name: Verifies ownership of the MyCertificate private key.
          text: >
            az iot hub certificate verify --hub-name MyIotHub --name MyCertificate --path /certificates/Verification.pem --etag
            AAAAAAAAAAA=
""".format(certificate_help)

helps['iot hub create'] = """
    type: command
    short-summary: Create an Azure IoT hub.
    long-summary: For an introduction to Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/
    examples:
        - name: Create an IoT Hub with the free pricing tier F1, in the region of the resource group.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub
        - name: Create an IoT Hub with the standard pricing tier S1 and 4 partitions, in the 'westus' region.
          text: >
            az iot hub create --resource-group MyResourceGroup --name MyIotHub --sku S1 --location westus
            --partition-count 4
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
    long-summary: This command is deprecating. Use 'az iot hub device-identity create' via the IoT Extension instead.
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
    long-summary: This command is deprecating. Use 'az iot hub device-identity show' via the IoT Extension instead.
"""

helps['iot device update'] = """
    type: command
    short-summary: Update the metadata of a device in an IoT hub.
    long-summary: This command is deprecating. Use 'az iot hub device-identity update' via the IoT Extension instead.
    examples:
        - name: Disable a device.
          text: >
            az iot device update --hub-name MyIotHub --device-id MyDevice --set status=disabled
"""

helps['iot device list'] = """
    type: command
    short-summary: List devices in an IoT hub.
    long-summary: This command is deprecating. Use 'az iot hub device-identity list' via the IoT Extension instead.
"""

helps['iot device delete'] = """
    type: command
    short-summary: Delete a device from an IoT hub.
    long-summary: This command is deprecating. Use 'az iot hub device-identity delete' via the IoT Extension instead.
"""

helps['iot device show-connection-string'] = """
    type: command
    short-summary: Show the connection strings for devices in an IoT hub.
    long-summary: This command is deprecating.
                  Use 'az iot hub device-identity show-connection-string' via the IoT Extension instead.
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
    long-summary: This command is deprecating. Use 'az iot device send-d2c-message' via the IoT Extension instead.
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
    long-summary: This command is deprecating. Use 'az iot device c2d-message receive' via the IoT Extension instead.
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
    long-summary: This command is deprecating. Use 'az iot device c2d-message complete' via the IoT Extension instead.
"""

helps['iot device message reject'] = """
    type: command
    short-summary: Reject a cloud-to-device message.
    long-summary: This command is deprecating. Use 'az iot device c2d-message reject' via the IoT Extension instead.
"""

helps['iot device message abandon'] = """
    type: command
    short-summary: Abandon a cloud-to-device message.
    long-summary: This command is deprecating. Use 'az iot device c2d-message abandon' via the IoT Extension instead.
"""

helps['iot device export'] = """
    type: command
    short-summary: Export all the device identities in the IoT hub identity registry to an Azure Storage blob container.
    long-summary: This command is deprecating. Use 'az iot hub device-identity export' via the IoT Extension instead.
                  For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities
"""

helps['iot device import'] = """
    type: command
    short-summary: Import, update, or delete device identities in the IoT hub identity registry from a blob.
    long-summary: This command is deprecating. Use 'az iot hub device-identity import' via the IoT Extension instead.
                  For more information, see https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-identity-registry#import-and-export-device-identities
"""

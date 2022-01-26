# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import
# pylint: disable=line-too-long, too-many-lines

helps['iot'] = """
type: group
short-summary: Manage Internet of Things (IoT) assets.
long-summary: Comprehensive IoT data-plane functionality is available in the Azure IoT CLI Extension. For more info and install guide go to https://github.com/Azure/azure-iot-cli-extension
"""

helps['iot dps'] = """
type: group
short-summary: Manage Azure IoT Hub Device Provisioning Service.
"""

helps['iot dps access-policy'] = """
type: group
short-summary: Manage shared access policies for an Azure IoT Hub Device Provisioning Service instance.
"""

helps['iot dps access-policy create'] = """
type: command
short-summary: Create a new shared access policy in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Create a new shared access policy in an Azure IoT Hub Device Provisioning Service instance with EnrollmentRead right
    text: >
        az iot dps access-policy create --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy --rights EnrollmentRead
"""

helps['iot dps access-policy delete'] = """
type: command
short-summary: Delete a shared access policies in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Delete shared access policy 'MyPolicy' in the Azure IoT Hub Device Provisioning Service instance 'MyDps'
    text: >
        az iot dps access-policy delete --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy
"""

helps['iot dps access-policy list'] = """
type: command
short-summary: List all shared access policies in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: List all shared access policies in the Azure IoT Hub Device Provisioning Service instance 'MyDps'
    text: >
        az iot dps access-policy list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps access-policy show'] = """
type: command
short-summary: Show details of a shared access policies in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Show details of shared access policy 'MyPolicy' in the Azure IoT Hub Device Provisioning Service instance 'MyDps'
    text: >
        az iot dps access-policy show --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy
"""

helps['iot dps access-policy update'] = """
type: command
short-summary: Update a shared access policy in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Update shared access policy 'MyPolicy' in an Azure IoT Hub Device Provisioning Service instance with EnrollmentWrite right
    text: >
        az iot dps access-policy update --dps-name MyDps --resource-group MyResourceGroup --name MyPolicy --rights EnrollmentWrite
"""

helps['iot dps policy'] = """
type: group
short-summary: Manage shared access policies for an Azure IoT Hub Device Provisioning Service instance.
"""

helps['iot dps policy create'] = """
type: command
short-summary: Create a new shared access policy in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Create a new shared access policy in an Azure IoT Hub Device Provisioning Service instance with EnrollmentRead right
    text: >
        az iot dps policy create --dps-name MyDps --resource-group MyResourceGroup --policy-name MyPolicy --rights EnrollmentRead
"""

helps['iot dps policy delete'] = """
type: command
short-summary: Delete a shared access policies in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Delete shared access policy 'MyPolicy' in the Azure IoT Hub Device Provisioning Service instance 'MyDps'
    text: >
        az iot dps policy delete --dps-name MyDps --resource-group MyResourceGroup --policy-name MyPolicy
"""

helps['iot dps policy list'] = """
type: command
short-summary: List all shared access policies in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: List all shared access policies in MyDps in the Azure IoT Hub Device Provisioning Service instance 'MyDps'
    text: >
        az iot dps policy list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps policy show'] = """
type: command
short-summary: Show details of a shared access policies in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Show details of shared access policy 'MyPolicy' in the Azure IoT Hub Device Provisioning Service instance 'MyDps'
    text: >
        az iot dps policy show --dps-name MyDps --resource-group MyResourceGroup --policy-name MyPolicy
"""

helps['iot dps policy update'] = """
type: command
short-summary: Update a shared access policy in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Update shared access policy 'MyPolicy' in an Azure IoT Hub Device Provisioning Service instance with EnrollmentWrite right
    text: >
        az iot dps policy update --dps-name MyDps --resource-group MyResourceGroup --policy-name MyPolicy --rights EnrollmentWrite
"""

helps['iot dps certificate'] = """
type: group
short-summary: Manage certificates for an Azure IoT Hub Device Provisioning Service instance.
"""

helps['iot dps certificate create'] = """
type: command
short-summary: Create/upload a certficate to an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Upload a CA certificate PEM file to an Azure IoT Hub Device Provisioning Service instance.
    text: >
        az iot dps certificate create --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/Certificate.pem
  - name: Upload a verified CA certificate CER file to an Azure IoT Hub Device Provisioning Service.instance
    text: >
        az iot dps certificate create --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/Certificate.cer --verified
"""

helps['iot dps certificate delete'] = """
type: command
short-summary: Delete a certificate in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Delete MyCertificate in an Azure IoT Hub Device Provisioning Service instance
    text: >
        az iot dps certificate delete --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --etag AAAAAAAAAAA=
"""

helps['iot dps certificate generate-verification-code'] = """
type: command
short-summary: Generate a verification code for a certificate in an Azure IoT Hub Device Provisioning Service instance.
long-summary: This verification code is used to complete the proof of possession step for a certificate. Use this verification code as the CN of a new certificate signed with the root certificates private key.
examples:
  - name: Generate a verification code for MyCertificate
    text: >
        az iot dps certificate generate-verification-code --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --etag AAAAAAAAAAA=
"""

helps['iot dps certificate list'] = """
type: command
short-summary: List all certificates contained within an Azure IoT Hub Device Provisioning Service instance
examples:
  - name: List all certificates in MyDps
    text: >
        az iot dps certificate list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps certificate show'] = """
type: command
short-summary: Show information about a particular certificate in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Show details about MyCertificate in an Azure IoT Hub Device Provisioning Service instance
    text: >
        az iot dps certificate show --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate
  - name: Show information about a particular Azure IoT Hub Device Provisioning Service certificate. (autogenerated)
    text: az iot dps certificate show --certificate-name MyCertificate --dps-name MyDps --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['iot dps certificate update'] = """
type: command
short-summary: Update a certificate in an Azure IoT Hub Device Provisioning Service instance.
long-summary: Upload a new certificate to replace the existing certificate with the same name.
examples:
  - name: Update a CA certificate in an Azure IoT Hub Device Provisioning Service by uploading a new PEM file.
    text: >
        az iot dps certificate update --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/NewCertificate.pem --etag AAAAAAAAAAA=
  - name: Update a CA certificate in an Azure IoT Hub Device Provisioning Service by uploading a new CER file.
    text: >
        az iot dps certificate update --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/NewCertificate.cer --etag AAAAAAAAAAA=
"""

helps['iot dps certificate verify'] = """
type: command
short-summary: Verify a certificate in an Azure IoT Hub Device Provisioning Service instance.
long-summary: Verify a certificate by uploading a verification certificate containing the verification code obtained by calling generate-verification-code. This is the last step in the proof of possession process.
examples:
  - name: Verify ownership of the MyCertificate private key.
    text: >
        az iot dps certificate verify --dps-name MyDps --resource-group MyResourceGroup --name MyCertificate --path /certificates/Verification.pem --etag AAAAAAAAAAA=
"""

helps['iot dps create'] = """
type: command
short-summary: Create an Azure IoT Hub Device Provisioning Service instance.
long-summary: For an introduction to Azure IoT Hub Device Provisioning Service, see https://docs.microsoft.com/azure/iot-dps/about-iot-dps
examples:
  - name: Create an Azure IoT Hub Device Provisioning Service with the standard pricing tier S1, in the region of the resource group.
    text: >
        az iot dps create --name MyDps --resource-group MyResourceGroup
  - name: Create an Azure IoT Hub Device Provisioning Service with the standard pricing tier S1, in the 'eastus' region.
    text: >
        az iot dps create --name MyDps --resource-group MyResourceGroup --location eastus
"""

helps['iot dps delete'] = """
type: command
short-summary: Delete an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Delete an Azure IoT Hub Device Provisioning Service 'MyDps'
    text: >
        az iot dps delete --name MyDps --resource-group MyResourceGroup
"""

helps['iot dps linked-hub'] = """
type: group
short-summary: Manage linked IoT Hubs in an Azure IoT Hub Device Provisioning Service instance.
"""

helps['iot dps linked-hub create'] = """
type: command
short-summary: Create a linked IoT hub in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Create a linked IoT hub in an Azure IoT Hub Device Provisioning Service instance
    text: >
        az iot dps linked-hub create --dps-name MyDps --resource-group MyResourceGroup --connection-string HostName=test.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=XNBhoasdfhqRlgGnasdfhivtshcwh4bJwe7c0RIGuWsirW0= --location westus
  - name: Create a linked IoT hub in an Azure IoT Hub Device Provisioning Service which applies allocation weight and weight being 10
    text: >
        az iot dps linked-hub create --dps-name MyDps --resource-group MyResourceGroup --connection-string HostName=test.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=XNBhoasdfhqRlgGnasdfhivtshcwh4bJwe7c0RIGuWsirW0= --location westus --allocation-weight 10 --apply-allocation-policy True
"""

helps['iot dps linked-hub delete'] = """
type: command
short-summary: Update a linked IoT hub in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Delete linked IoT hub 'MyLinkedHub' in an Azure IoT Hub Device Provisioning Service instance
    text: >
        az iot dps linked-hub delete --dps-name MyDps --resource-group MyResourceGroup --linked-hub MyLinkedHub
"""

helps['iot dps linked-hub list'] = """
type: command
short-summary: List all linked IoT hubs in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: List all linked IoT hubs in MyDps
    text: >
        az iot dps linked-hub list --dps-name MyDps --resource-group MyResourceGroup
"""

helps['iot dps linked-hub show'] = """
type: command
short-summary: Show details of a linked IoT hub in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Show details of linked IoT hub 'MyLinkedHub' in an Azure IoT Hub Device Provisioning Service
    text: >
        az iot dps linked-hub show --dps-name MyDps --resource-group MyResourceGroup --linked-hub MyLinkedHub
"""

helps['iot dps linked-hub update'] = """
type: command
short-summary: Update a linked IoT hub in an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Update linked IoT hub 'MyLinkedHub.azure-devices.net' in an Azure IoT Hub Device Provisioning Service
    text: >
        az iot dps linked-hub update --dps-name MyDps --resource-group MyResourceGroup --linked-hub MyLinkedHub.azure-devices.net --allocation-weight 10 --apply-allocation-policy True
"""

helps['iot dps list'] = """
type: command
short-summary: List Azure IoT Hub Device Provisioning Service instances.
examples:
  - name: List all Azure IoT Hub Device Provisioning Services in a subscription.
    text: >
        az iot dps list
  - name: List all Azure IoT Hub Device Provisioning Services in the resource group 'MyResourceGroup'
    text: >
        az iot dps list --resource-group MyResourceGroup
"""

helps['iot dps show'] = """
type: command
short-summary: Get the details of an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Show details of an Azure IoT Hub Device Provisioning Service 'MyDps'
    text: >
        az iot dps show --name MyDps --resource-group MyResourceGroup
"""

helps['iot dps update'] = """
type: command
short-summary: Update an Azure IoT Hub Device Provisioning Service instance.
examples:
  - name: Update Allocation Policy to 'GeoLatency' of an Azure IoT Hub Device Provisioning Service 'MyDps'
    text: >
        az iot dps update --name MyDps --resource-group MyResourceGroup --set properties.allocationPolicy="GeoLatency"
"""

helps['iot hub'] = """
type: group
short-summary: Manage Azure IoT hubs.
"""

helps['iot hub certificate'] = """
type: group
short-summary: Manage IoT Hub certificates.
"""

helps['iot hub certificate create'] = """
type: command
short-summary: Create/upload an Azure IoT Hub certificate.
long-summary: For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: Uploads a verified CA certificate PEM file to an IoT hub.
    text: >
        az iot hub certificate create --hub-name MyIotHub --name MyCertificate --path /certificates/Certificate.pem --verified
  - name: Uploads a CA certificate CER file to an IoT hub.
    text: >
        az iot hub certificate create --hub-name MyIotHub --name MyCertificate --path /certificates/Certificate.cer
  - name: Create/upload an Azure IoT Hub certificate (autogenerated)
    text: az iot hub certificate create --hub-name MyIotHub --name MyCertificate --path /certificates/Certificate.cer --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['iot hub certificate delete'] = """
type: command
short-summary: Deletes an Azure IoT Hub certificate.
long-summary: For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: Deletes MyCertificate
    text: >
        az iot hub certificate delete --hub-name MyIotHub --name MyCertificate --etag AAAAAAAAAAA=
"""

helps['iot hub certificate generate-verification-code'] = """
type: command
short-summary: Generates a verification code for an Azure IoT Hub certificate.
long-summary: This verification code is used to complete the proof of possession step for a certificate. Use this verification code as the CN of a new certificate signed with the root certificates private key. For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: Generates a verification code for MyCertificate
    text: >
        az iot hub certificate generate-verification-code --hub-name MyIotHub --name MyCertificate --etag AAAAAAAAAAA=
  - name: Generates a verification code for an Azure IoT Hub certificate (autogenerated)
    text: az iot hub certificate generate-verification-code --etag AAAAAAAAAAA= --hub-name MyIotHub --name MyCertificate --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['iot hub certificate list'] = """
type: command
short-summary: Lists all certificates contained within an Azure IoT Hub
long-summary: For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: List all certificates in MyIotHub
    text: >
        az iot hub certificate list --hub-name MyIotHub
"""

helps['iot hub certificate show'] = """
type: command
short-summary: Shows information about a particular Azure IoT Hub certificate.
long-summary: For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: Show details about MyCertificate
    text: >
        az iot hub certificate show --hub-name MyIotHub --name MyCertificate
  - name: Shows information about a particular Azure IoT Hub certificate (autogenerated)
    text: az iot hub certificate show --hub-name MyIotHub --name MyCertificate --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['iot hub certificate update'] = """
type: command
short-summary: Update an Azure IoT Hub certificate.
long-summary: Uploads a new certificate to replace the existing certificate with the same name. For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: Updates a CA certificate in an IoT hub by uploading a new PEM file.
    text: >
        az iot hub certificate update --hub-name MyIotHub --name MyCertificate --path /certificates/NewCertificate.pem --etag AAAAAAAAAAA=
  - name: Updates a CA certificate in an IoT hub by uploading a new CER file.
    text: >
        az iot hub certificate update --hub-name MyIotHub --name MyCertificate --path /certificates/NewCertificate.cer --etag AAAAAAAAAAA=
"""

helps['iot hub certificate verify'] = """
type: command
short-summary: Verifies an Azure IoT Hub certificate.
long-summary: Verifies a certificate by uploading a verification certificate containing the verification code obtained by calling generate-verification-code. This is the last step in the proof of possession process. For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/iot-hub-x509ca-overview
examples:
  - name: Verifies ownership of the MyCertificate private key.
    text: >
        az iot hub certificate verify --hub-name MyIotHub --name MyCertificate --path /certificates/Verification.pem --etag AAAAAAAAAAA=
  - name: Verifies an Azure IoT Hub certificate (autogenerated)
    text: az iot hub certificate verify --etag AAAAAAAAAAA= --hub-name MyIotHub --name MyCertificate --path /certificates/Verification.pem --resource-group MyResourceGroup --subscription MySubscription
    crafted: true
"""

helps['iot hub consumer-group'] = """
type: group
short-summary: Manage the event hub consumer groups of an IoT hub.
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

helps['iot hub consumer-group delete'] = """
type: command
short-summary: Delete an event hub consumer group.
"""

helps['iot hub consumer-group list'] = """
type: command
short-summary: List event hub consumer groups.
examples:
  - name: List event hub consumer groups. (autogenerated)
    text: az iot hub consumer-group list --hub-name MyHub
    crafted: true
"""

helps['iot hub consumer-group show'] = """
type: command
short-summary: Get the details for an event hub consumer group.
examples:
  - name: Get the details for an event hub consumer group. (autogenerated)
    text: az iot hub consumer-group show --hub-name MyHub --name MyEventHubConsumerGroup
    crafted: true
"""

helps['iot hub create'] = """
type: command
short-summary: Create an Azure IoT hub.
long-summary: For an introduction to Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/
examples:
  - name: Create an IoT Hub with the free pricing tier F1, in the region of the resource group.
    text: >
        az iot hub create --resource-group MyResourceGroup --name MyIotHub --sku F1 --partition-count 2
  - name: Create an IoT Hub with the standard pricing tier S1 and 4 partitions, in the 'westus' region, with tags.
    text: >
        az iot hub create --resource-group MyResourceGroup --name MyIotHub --location westus --tags a=b c=d
  - name: Create an IoT Hub with a system-assigned managed identity, and assign a role and scope to a storage account for the created identity.
    text: >
        az iot hub create --resource-group MyResourceGroup --name MyIotHub --location westus --mi-system-assigned --role "Storage Blob Data Contributor" --scopes {resourceId}
  - name: Create an IoT Hub with local authentication, device SAS keys, and module SAS keys all disabled
    text: >
        az iot hub create --resource-group MyResourceGroup --name MyIotHub --location westus --disable-local-auth --disable-device-sas --disable-module-sas
"""

helps['iot hub delete'] = """
type: command
short-summary: Delete an IoT hub.
examples:
  - name: Delete an IoT hub. (autogenerated)
    text: az iot hub delete --name MyIoTHub --resource-group MyResourceGroup
    crafted: true
"""

helps['iot hub devicestream'] = """
type: group
short-summary: Manage device streams of an IoT hub.
"""

helps['iot hub devicestream show'] = """
type: command
short-summary: Get IoT Hub's device streams endpoints.
long-summary: Get IoT Hub's device streams endpoints.
examples:
  - name: Get all the device streams from "MyIotHub" IoT Hub.
    text: >
        az iot hub devicestream show -n MyIotHub
"""

helps['iot hub identity'] = """
type: group
short-summary: Manage identities of an Azure IoT hub.
"""

helps['iot hub identity assign'] = """
type: command
short-summary: Assign managed identities to an IoT Hub
examples:
  - name: Assign user-assigned managed identities to an IoT Hub
    text: >
        az iot hub identity assign --name MyIoTHub --resource-group MyResourceGroup --user-assigned {resourceId1} {resourceId2}
  - name: Assign a system-assigned managed identity to an IoT Hub and assign a role to that identity.
    text: >
        az iot hub identity assign --name MyIoTHub --resource-group MyResourceGroup --system-assigned --role "Storage Blob Data Contributor" --scopes {resourceId}
"""

helps['iot hub identity show'] = """
type: command
short-summary: Show the identity properties of an IoT Hub
examples:
  - name: Show identity properties of an IoT Hub
    text: >
        az iot hub identity show --name MyIoTHub --resource-group MyResourceGroup
"""

helps['iot hub identity remove'] = """
type: command
short-summary: Remove managed identities from an IoT Hub
examples:
  - name: Remove a user-assigned managed identity from an IoT Hub
    text: >
        az iot hub identity remove --name MyIoTHub --resource-group MyResourceGroup --user-assigned {resourceId}
  - name: Remove a system-assigned managed identity from an IoT Hub.
    text: >
        az iot hub identity remove --name MyIoTHub --resource-group MyResourceGroup --system-assigned
  - name: Remove all identities from an IoT Hub.
    text: >
        az iot hub identity remove --name MyIoTHub --resource-group MyResourceGroup --system-assigned --user-assigned
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

helps['iot hub list-skus'] = """
type: command
short-summary: List available pricing tiers.
examples:
  - name: List available pricing tiers. (autogenerated)
    text: az iot hub list-skus --name MyIoTHub
    crafted: true
"""

helps['iot hub manual-failover'] = """
type: command
short-summary: Initiate a manual failover for the IoT Hub to the geo-paired disaster recovery region.
examples:
  - name: Initiate failover “myhub” from primary to secondary region.
    text: >
        az iot hub manual-failover -n myhub
"""

helps['iot hub message-enrichment'] = """
type: group
short-summary: Manage message enrichments for endpoints of an IoT Hub.
"""

helps['iot hub message-enrichment create'] = """
type: command
short-summary: Create a message enrichment for chosen endpoints in your IoT Hub
long-summary: Create a message enrichment for chosen endpoints in your IoT Hub
examples:
  - name: Create a message enrichment of {"key":"value"} for the "events" endpoint in your IoT Hub
    text: >
        az iot hub message-enrichment create --key key --value value --endpoints events -n {iothub_name}
"""

helps['iot hub message-enrichment delete'] = """
type: command
short-summary: Delete a message enrichment in your IoT hub (by key)
long-summary: Delete a message enrichment in your IoT hub (by key)
examples:
  - name: Delete a message enrichment with key 'test' from your IoT Hub
    text: >
        az iot hub message-enrichment delete --key test -n {iothub_name}
"""

helps['iot hub message-enrichment list'] = """
type: command
short-summary: Get information on all message enrichments for your IoT Hub
long-summary: Get information on all message enrichments for your IoT Hub
examples:
  - name: List all message enrichments for your IoT Hub
    text: >
        az iot hub message-enrichment list -n {iothub_name}
"""

helps['iot hub message-enrichment update'] = """
type: command
short-summary: Update a message enrichment in your IoT hub (by key)
long-summary: Update a message enrichment in your IoT hub (by key)
examples:
  - name: Update a message enrichment in your IoT hub to apply to a new set of endpoints
    text: >
        az iot hub message-enrichment update --key {key} --value {value} --endpoints NewEndpoint1 NewEndpoint2 -n {iothub_name}
"""

helps['iot hub policy'] = """
type: group
short-summary: Manage shared access policies of an IoT hub.
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
examples:
  - name: Delete a shared access policy from an IoT hub. (autogenerated)
    text: az iot hub policy delete --hub-name MyHub --name MySharedAccessPolicy
    crafted: true
"""

helps['iot hub policy list'] = """
type: command
short-summary: List shared access policies of an IoT hub.
examples:
  - name: List shared access policies of an IoT hub. (autogenerated)
    text: az iot hub policy list --hub-name MyHub --resource-group MyResourceGroup
    crafted: true
"""

helps['iot hub policy renew-key'] = """
type: command
short-summary: Regenerate keys of a shared access policy of an IoT hub.
examples:
  - name: Regenerate primary key of a shared access policy of an IoT hub.
    text: az iot hub policy renew-key --hub-name MyHub --name MySharedAccessPolicy --rk Primary
    crafted: true
"""

helps['iot hub policy show'] = """
type: command
short-summary: Get the details of a shared access policy of an IoT hub.
examples:
  - name: Get the details of a shared access policy of an IoT hub. (autogenerated)
    text: az iot hub policy show --hub-name MyHub --name MySharedAccessPolicy
    crafted: true
"""

helps['iot hub route'] = """
type: group
short-summary: Manage routes of an IoT hub.
"""

helps['iot hub route create'] = """
type: command
short-summary: Create a route in IoT Hub.
long-summary: Create a route to send specific data source and condition to a desired endpoint.
examples:
  - name: Create a new route "R1".
    text: >
        az iot hub route create -g MyResourceGroup --hub-name MyIotHub --endpoint-name E2 --source-type DeviceMessages --route-name R1
  - name: Create a new route "R1" with all parameters.
    text: >
        az iot hub route create -g MyResourceGroup --hub-name MyIotHub --endpoint-name E2 --source-type DeviceMessages --route-name R1 --condition true --enabled true
"""

helps['iot hub route delete'] = """
type: command
short-summary: Delete all or mentioned route for your IoT Hub.
long-summary: Delete a route or all routes for your IoT Hub.
examples:
  - name: Delete route "R1" from "MyIotHub" IoT Hub.
    text: >
        az iot hub route delete -g MyResourceGroup --hub-name MyIotHub --route-name R1
  - name: Delete all the routes of source type "DeviceMessages" from "MyIotHub" IoT Hub.
    text: >
        az iot hub route delete -g MyResourceGroup --hub-name MyIotHub --source-type DeviceMessages
  - name: Delete all the routes from "MyIotHub" IoT Hub.
    text: >
        az iot hub route delete -g MyResourceGroup --hub-name MyIotHub
"""

helps['iot hub route list'] = """
type: command
short-summary: Get all the routes in IoT Hub.
long-summary: Get information on all routes from an IoT Hub.
examples:
  - name: Get all route from "MyIotHub" IoT Hub.
    text: >
        az iot hub route list -g MyResourceGroup --hub-name MyIotHub
  - name: Get all the routes of source type "DeviceMessages" from "MyIotHub" IoT Hub.
    text: >
        az iot hub route list -g MyResourceGroup --hub-name MyIotHub --source-type DeviceMessages
"""

helps['iot hub route show'] = """
type: command
short-summary: Get information about the route in IoT Hub.
long-summary: Get information on a specific route in your IoT Hub.
examples:
  - name: Get an route information from "MyIotHub" IoT Hub.
    text: >
        az iot hub route show -g MyResourceGroup --hub-name MyIotHub --route-name {routeName}
"""

helps['iot hub route test'] = """
type: command
short-summary: Test all routes or mentioned route in IoT Hub.
long-summary: Test all existing routes or mentioned route in your IoT Hub. You can provide a sample message to test your routes.
examples:
  - name: Test the route "R1" from "MyIotHub" IoT Hub.
    text: >
        az iot hub route test -g MyResourceGroup --hub-name MyIotHub --route-name R1
  - name: Test all the route of source type "DeviceMessages" from "MyIotHub" IoT Hub.
    text: >
        az iot hub route test -g MyResourceGroup --hub-name MyIotHub --source-type DeviceMessages
"""

helps['iot hub route update'] = """
type: command
short-summary: Update a route in IoT Hub.
long-summary: Updates a route in IoT Hub. You can change the source, endpoint or query on the route.
examples:
  - name: Update source type of route "R1" from "MyIotHub" IoT Hub.
    text: >
        az iot hub route update -g MyResourceGroup --hub-name MyIotHub --source-type DeviceMessages --route-name R1
"""

helps['iot hub routing-endpoint'] = """
type: group
short-summary: Manage custom endpoints of an IoT hub.
"""

helps['iot hub routing-endpoint create'] = """
type: command
short-summary: Add an endpoint to your IoT Hub.
long-summary: Create a new custom endpoint in your IoT Hub.
examples:
  - name: Add a new endpoint "E2" of type EventHub to "MyIotHub" IoT Hub.
    text: >
        az iot hub routing-endpoint create --resource-group MyResourceGroup --hub-name MyIotHub --endpoint-name E2 --endpoint-type eventhub --endpoint-resource-group {ResourceGroup} --endpoint-subscription-id {SubscriptionId} --connection-string {ConnectionString}
  - name: Add a new endpoint "S1" of type AzureStorageContainer to "MyIotHub" IoT Hub.
    text: |
        az iot hub routing-endpoint create --resource-group MyResourceGroup --hub-name MyIotHub \\
        --endpoint-name S1 --endpoint-type azurestoragecontainer --endpoint-resource-group "[Resource Group]" \\
        --endpoint-subscription-id {SubscriptionId} --connection-string {ConnectionString} \\
        --container-name {ContainerName} --batch-frequency 100 --chunk-size 100 \\
        --ff {iothub}-{partition}-{YYYY}-{MM}-{DD}-{HH}-{mm}
  - name: Add a new identity-based EventHub endpoint named "EventHubIdentity" and authenticate using a user-assigned managed identity
    text: >
        az iot hub routing-endpoint create --resource-group MyResourceGroup --hub-name MyIotHub --endpoint-name EventHubIdentity --endpoint-type eventhub --endpoint-resource-group {ResourceGroup} --endpoint-subscription-id {SubscriptionId} --auth-type identityBased --identity {userIdentityResourceId} --endpoint-uri {EventHubEndpointUri} --entity-path {EntityPath}
"""

helps['iot hub routing-endpoint delete'] = """
type: command
short-summary: Delete all or mentioned endpoint for your IoT Hub.
long-summary: Delete an endpoint for your IoT Hub. We recommend that you delete any routes to the endpoint, before deleting the endpoint.
examples:
  - name: Delete endpoint "E2" from "MyIotHub" IoT Hub.
    text: >
        az iot hub routing-endpoint delete --resource-group MyResourceGroup --hub-name MyIotHub --endpoint-name E2
  - name: Delete all the endpoints of type "EventHub" from "MyIotHub" IoT Hub.
    text: >
        az iot hub routing-endpoint delete --resource-group MyResourceGroup --hub-name MyIotHub --endpoint-type eventhub
  - name: Delete all the endpoints from "MyIotHub" IoT Hub.
    text: >
        az iot hub routing-endpoint delete --resource-group MyResourceGroup --hub-name MyIotHub
"""

helps['iot hub routing-endpoint list'] = """
type: command
short-summary: Get information on all the endpoints for your IoT Hub.
long-summary: Get information on all endpoints in your IoT Hub. You can also specify which endpoint type you want to get informaiton on.
examples:
  - name: Get all the endpoints from "MyIotHub" IoT Hub.
    text: >
        az iot hub routing-endpoint list -g MyResourceGroup --hub-name MyIotHub
  - name: Get all the endpoints of type "EventHub" from "MyIotHub" IoT Hub.
    text: >
        az iot hub routing-endpoint list -g MyResourceGroup --hub-name MyIotHub --endpoint-type eventhub
"""

helps['iot hub routing-endpoint show'] = """
type: command
short-summary: Get information on mentioned endpoint for your IoT Hub.
long-summary: Get information on a specific endpoint in your IoT Hub
examples:
  - name: Get an endpoint information from "MyIotHub" IoT Hub.
    text: |
        az iot hub routing-endpoint show --resource-group MyResourceGroup --hub-name MyIotHub \\
        --endpoint-name {endpointName}
"""

helps['iot hub show'] = """
type: command
short-summary: Get the details of an IoT hub.
examples:
  - name: Get the details of an IoT hub. (autogenerated)
    text: az iot hub show --name MyIoTHub
    crafted: true
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
  - name: Show the connection strings for an IoT hub. (autogenerated)
    text: az iot hub show-connection-string --key primary --policy-name MyPolicy
    crafted: true
"""

helps['iot hub show-quota-metrics'] = """
type: command
short-summary: Get the quota metrics for an IoT hub.
examples:
  - name: Get the quota metrics for an IoT hub. (autogenerated)
    text: az iot hub show-quota-metrics --ids {ids}
    crafted: true
  - name: Get the quota metrics for an IoT hub. (autogenerated)
    text: az iot hub show-quota-metrics --name MyIoTHub
    crafted: true
"""

helps['iot hub show-stats'] = """
type: command
short-summary: Get the statistics for an IoT hub.
examples:
  - name: Get the statistics for an IoT hub. (autogenerated)
    text: az iot hub show-stats --name MyIoTHub
    crafted: true
"""

helps['iot hub update'] = """
type: command
short-summary: Update metadata for an IoT hub.
examples:
  - name: Add storage container settings to file upload
    text: >
        az iot hub update --name MyIotHub --fileupload-storage-connectionstring "connection-string" \\
        --fileupload-storage-container-name "container_name"
  - name: Add a firewall filter rule to accept traffic from the IP mask 127.0.0.0/31.
    text: >
        az iot hub update --name MyIotHub --add properties.ipFilterRules filter_name=test-rule action=Accept ip_mask=127.0.0.0/31
  - name: Update metadata for an IoT hub. (autogenerated)
    text: |
        az iot hub update --name MyIotHub --set properties.allocationPolicy="GeoLatency"
    crafted: true
  - name: Update units of an IoT Hub to 2 and add tags
    text: >
        az iot hub update -n MyIotHub --unit 2 --tags a=b c=d
  - name: Update pricing tier for an IoT Hub as S2
    text: >
        az iot hub update -n MyIotHub --sku S2
  - name: Update the retention days of IoT Hub device-to-cloud events as 3 days
    text: >
        az iot hub update -n MyIotHub --retention-day 3
  - name: Update the IoT Hub cloud-to-device messaging settings
    text: >
        az iot hub update --name MyIotHub --c2d-max-delivery-count 30 --c2d-ttl 5
  - name: Update the IoT Hub feedback queue settings
    text: >
        az iot hub update --name MyIoTHub --feedback-max-delivery-count 20 --feedback-lock-duration 100 --feedback-ttl 4
  - name: Update the IoT Hub file upload settings, and assign a managed identity to user for file upload
    text: >
        az iot hub update -n MyIoTHub --fileupload-sas-ttl 5 --fileupload-storage-auth-type identityBased --fileupload-storage-identity [system]
  - name: Update the IoT Hub file upload notification settings and queue lock duration
    text: >
        az iot hub update -n MyIoTHub --fileupload-notification-max-delivery-count 50
        --fileupload-notification-ttl 48 --fileupload-notifications --fileupload-notification-lock-duration 10
  - name: Update the IoT Hub local authentication, device SAS, and module SAS settings
    text: >
        az iot hub update -n MyIoTHub --disable-local-auth --disable-device-sas false --disable-module-sas true
"""

helps['iot central'] = """
type: group
short-summary: Manage IoT Central resources.
long-summary: |
    IoT Central is an IoT application platform that reduces the burden and cost of developing, managing, and maintaining enterprise-grade IoT solutions. Choosing to build with IoT Central gives you the opportunity to focus time, money, and energy on transforming your business with IoT data, rather than just maintaining and updating a complex and continually evolving IoT infrastructure.
    IoT Central documentation is available at https://aka.ms/iotcentral-documentation
    Comprehensive IoT Central data-plane functionality is available in the Azure IoT CLI Extension. For more info on how to install visit https://github.com/Azure/azure-iot-cli-extension
"""

helps['iot central app'] = """
type: group
short-summary: Manage IoT Central applications.
long-summary: Create, delete, view, and update your IoT Central apps.
"""

helps['iot central app create'] = """
type: command
short-summary: Create an IoT Central application.
long-summary: |
    An IoT Central app is a cloud-based application that you can use to manage your IoT devices.
    For more information on deploying an IoT Central app via CLI or a list of available arguments, visit https://aka.ms/iotcentral-manage-cli
examples:
  - name: Create an IoT Central application in the region of the resource group using the default pricing SKU.
    text: >
        az iot central app create -n my-first-iot-app -g MyResourceGroup -s my-iot-app
  - name: Create an IoT Central application the in the 'East US' region with the 'ST1' pricing plan and an industry template.
    text: >
        az iot central app create -n my-first-iot-app -g MyResourceGroup -s my-iot-app -l eastus -p ST1 -t iotc-distribution
  - name: Create an IoT Central application using system-assigned managed identity.
    text: >
        az iot central app create -n my-first-iot-app -g MyResourceGroup -s my-iot-app --mi-system-assigned
"""

helps['iot central app delete'] = """
type: command
short-summary: Delete an IoT Central application.
long-summary: |
    Permanently delete your IoT Central app.
    -Warning- This operation is irreversible. Once you've deleted your app, you cannot restore it.
examples:
  - name: Delete an IoT Central app called 'my-first-iot-app'.
    text: az iot central app delete -n my-first-iot-app -g MyResourceGroup
"""

helps['iot central app list'] = """
type: command
short-summary: List IoT Central applications.
long-summary: All of the IoT Central apps that are part of your subscription.
examples:
  - name: List all IoT Central apps in my subscription.
    text: >
        az iot central app list
  - name: List all IoT Central apps in the resource group 'MyResourceGroup' within my subscription.
    text: >
        az iot central app list -g MyResourceGroup
"""

helps['iot central app show'] = """
type: command
short-summary: Get the details of an IoT Central application.
long-summary: Information about your app, like app name, subdomain, pricing plan, and location.
examples:
  - name: Show details for an app named 'my-first-iot-app'.
    text: >
        az iot central app show -n my-first-iot-app
  - name: Show details for an app named 'my-first-iot-app' in the resource group 'MyResourceGroup'.
    text: >
        az iot central app show -n my-first-iot-app -g MyResourceGroup
"""

helps['iot central app update'] = """
type: command
short-summary: Update metadata for an IoT Central application.
long-summary: Update metadata, like app name, subdomain, pricing plan, and location.
examples:
  - name: Update the SKU for 'my-first-iot-app'
    text: >
        az iot central app update -n my-first-iot-app -g MyResourceGroup --set sku.name=ST1
  - name: Change the subdomain for 'my-first-iot-app'
    text: >
        az iot central app update -n my-first-iot-app -g MyResourceGroup --set subdomain.name=my-iot-app-new
"""

helps['iot central app identity'] = """
type: group
short-summary: Manage IoT Central application identities.
long-summary: Assign, remove, and show your IoT Central application identities.
"""

helps['iot central app identity assign'] = """
type: command
short-summary: Assign managed identities to an IoT Central application
examples:
  - name: Assign a system-assigned managed identity to an IoT Central application.
    text: >
        az iot central app identity assign --name my-iotc-app --resource-group MyResourceGroup --system-assigned
"""

helps['iot central app identity show'] = """
type: command
short-summary: Show the identity properties of an IoT Central application
examples:
  - name: Show identity properties of an IoT Central application
    text: >
        az iot central app identity show --name my-iotc-app --resource-group MyResourceGroup
"""

helps['iot central app identity remove'] = """
type: command
short-summary: Remove managed identities from an IoT Central application
examples:
  - name: Remove a system-assigned managed identity from an IoT Central application.
    text: >
        az iot central app identity remove --name my-iotc-app --resource-group MyResourceGroup --system-assigned
"""

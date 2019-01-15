# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["iot hub routing-endpoint delete"] = """
"type": |-
    command
"short-summary": |-
    Delete all or mentioned endpoint for your IoT Hub.
"long-summary": |-
    Delete an endpoint for your IoT Hub. We recommend that you delete any routes to the endpoint, before deleting the endpoint.
"""

helps["iot hub route list"] = """
"type": |-
    command
"short-summary": |-
    Get all the routes in IoT Hub.
"long-summary": |-
    Get information on all routes from an IoT Hub.
"""

helps["iot hub consumer-group delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an event hub consumer group.
"""

helps["iot dps certificate list"] = """
"type": |-
    command
"short-summary": |-
    List all certificates contained within an Azure IoT Hub device provisioning service
"""

helps["iot dps access-policy list"] = """
"type": |-
    command
"short-summary": |-
    List all shared access policies in an Azure IoT Hub device provisioning service.
"""

helps["iot hub certificate verify"] = """
"type": |-
    command
"short-summary": |-
    Verifies an Azure IoT Hub certificate.
"long-summary": |-
    Verifies a certificate by uploading a verification certificate containing the verification code obtained by calling generate-verification-code. This is the last step in the proof of possession process. For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot hub show-quota-metrics"] = """
"type": |-
    command
"short-summary": |-
    Get the quota metrics for an IoT hub.
"""

helps["iot hub show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an IoT hub.
"examples":
-   "name": |-
        Get the details of an IoT hub.
    "text": |-
        az iot hub show --query [0] --name MyIoTHub
-   "name": |-
        Get the quota metrics for an IoT hub.
    "text": |-
        az iot hub show-quota-metrics --query [0]
-   "name": |-
        Show the connection strings for an IoT hub.
    "text": |-
        az iot hub show-connection-string --key secondary --policy-name service
"""

helps["iot dps linked-hub show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a linked IoT hub in an Azure IoT Hub device provisioning service.
"""

helps["iot hub route create"] = """
"type": |-
    command
"short-summary": |-
    Create a route in IoT Hub.
"long-summary": |-
    Create a route to send specific data source and condition to a desired endpoint.
"""

helps["iot hub job show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a job in an IoT hub.
"""

helps["iot hub job"] = """
"type": |-
    group
"short-summary": |-
    Manage jobs in an IoT hub.
"""

helps["iot hub certificate update"] = """
"type": |-
    command
"short-summary": |-
    Update an Azure IoT Hub certificate.
"long-summary": |-
    Uploads a new certificate to replace the existing certificate with the same name. For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot hub certificate show"] = """
"type": |-
    command
"short-summary": |-
    Shows information about a particular Azure IoT Hub certificate.
"long-summary": |-
    For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot hub create"] = """
"type": |-
    command
"short-summary": |-
    Create an Azure IoT hub.
"long-summary": |-
    For an introduction to Azure IoT Hub, see https://docs.microsoft.com/azure/iot-hub/
"""

helps["iot dps access-policy"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure IoT Hub Device Provisioning Service access policies.
"""

helps["iot hub consumer-group list"] = """
"type": |-
    command
"short-summary": |-
    List event hub consumer groups.
"""

helps["iot dps certificate create"] = """
"type": |-
    command
"short-summary": |-
    Create/upload an Azure IoT Hub Device Provisioning Service certificate.
"""

helps["iot hub job cancel"] = """
"type": |-
    command
"short-summary": |-
    Cancel a job in an IoT hub.
"""

helps["iot hub routing-endpoint show"] = """
"type": |-
    command
"short-summary": |-
    Get information on mentioned endpoint for your IoT Hub.
"long-summary": |-
    Get information on a specific endpoint in your IoT Hub
"""

helps["iot hub list"] = """
"type": |-
    command
"short-summary": |-
    List IoT hubs.
"examples":
-   "name": |-
        List IoT hubs.
    "text": |-
        az iot hub list --resource-group MyGroup
"""

helps["iot hub show-connection-string"] = """
"type": |-
    command
"short-summary": |-
    Show the connection strings for an IoT hub.
"""

helps["iot hub route delete"] = """
"type": |-
    command
"short-summary": |-
    Delete all or mentioned route for your IoT Hub.
"long-summary": |-
    Delete a route or all routes for your IoT Hub.
"""

helps["iot hub certificate"] = """
"type": |-
    group
"short-summary": |-
    Manage IoT Hub certificates.
"""

helps["iot hub policy create"] = """
"type": |-
    command
"short-summary": |-
    Create a new shared access policy in an IoT hub.
"""

helps["iot hub routing-endpoint create"] = """
"type": |-
    command
"short-summary": |-
    Add an endpoint to your IoT Hub.
"long-summary": |-
    Create a new custom endpoint in your IoT Hub.
"""

helps["iot dps linked-hub list"] = """
"type": |-
    command
"short-summary": |-
    List all linked IoT hubs in an Azure IoT Hub device provisioning service.
"""

helps["iot hub show-stats"] = """
"type": |-
    command
"short-summary": |-
    Get the statistics for an IoT hub.
"""

helps["iot dps linked-hub update"] = """
"type": |-
    command
"short-summary": |-
    Update a linked IoT hub in an Azure IoT Hub device provisioning service.
"""

helps["iot hub update"] = """
"type": |-
    command
"short-summary": |-
    Update metadata for an IoT hub.
"examples":
-   "name": |-
        Update metadata for an IoT hub.
    "text": |-
        az iot hub update --set <set> --name MyIotHub
"""

helps["iot dps access-policy delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a shared access policies in an Azure IoT Hub device provisioning service.
"""

helps["iot dps certificate show"] = """
"type": |-
    command
"short-summary": |-
    Show information about a particular Azure IoT Hub Device Provisioning Service certificate.
"""

helps["iot hub list-skus"] = """
"type": |-
    command
"short-summary": |-
    List available pricing tiers.
"""

helps["iot hub certificate list"] = """
"type": |-
    command
"short-summary": |-
    Lists all certificates contained within an Azure IoT Hub
"long-summary": |-
    For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot hub routing-endpoint list"] = """
"type": |-
    command
"short-summary": |-
    Get information on all the endpoints for your IoT Hub.
"long-summary": |-
    Get information on all endpoints in your IoT Hub. You can also specify which endpoint type you want to get informaiton on.
"""

helps["iot dps"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure IoT Hub Device Provisioning Service.
"""

helps["iot dps certificate update"] = """
"type": |-
    command
"short-summary": |-
    Update an Azure IoT Hub Device Provisioning Service certificate.
"long-summary": |-
    Upload a new certificate to replace the existing certificate with the same name.
"""

helps["iot dps linked-hub"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure IoT Hub Device Provisioning Service linked IoT hubs.
"""

helps["iot dps certificate"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure IoT Hub Device Provisioning Service certificates.
"""

helps["iot hub job list"] = """
"type": |-
    command
"short-summary": |-
    List the jobs in an IoT hub.
"""

helps["iot hub policy delete"] = """
"type": |-
    command
"short-summary": |-
    Delete a shared access policy from an IoT hub.
"""

helps["iot hub route"] = """
"type": |-
    group
"short-summary": |-
    Manage routes of an IoT hub.
"""

helps["iot hub policy"] = """
"type": |-
    group
"short-summary": |-
    Manage shared access policies of an IoT hub.
"""

helps["iot hub policy show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of a shared access policy of an IoT hub.
"examples":
-   "name": |-
        Get the details of a shared access policy of an IoT hub.
    "text": |-
        az iot hub policy show --query [0] --hub-name MyHub --name MySharedAccessPolicy
"""

helps["iot"] = """
"type": |-
    group
"short-summary": |-
    Manage Internet of Things (IoT) assets.
"long-summary": |-
    Comprehensive IoT data-plane functionality is available in the Azure IoT CLI Extension. For more info and install guide go to https://github.com/Azure/azure-iot-cli-extension
"""

helps["iot hub certificate delete"] = """
"type": |-
    command
"short-summary": |-
    Deletes an Azure IoT Hub certificate.
"long-summary": |-
    For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot hub certificate generate-verification-code"] = """
"type": |-
    command
"short-summary": |-
    Generates a verification code for an Azure IoT Hub certificate.
"long-summary": |-
    This verification code is used to complete the proof of possession step for a certificate. Use this verification code as the CN of a new certificate signed with the root certificates private key. For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot hub route update"] = """
"type": |-
    command
"short-summary": |-
    Update a route in IoT Hub.
"long-summary": |-
    Updates a route in IoT Hub. You can change the source, enpoint or query on the route.
"""

helps["iot dps list"] = """
"type": |-
    command
"short-summary": |-
    List Azure IoT Hub device provisioning services.
"""

helps["iot hub route test"] = """
"type": |-
    command
"short-summary": |-
    Test all routes or mentioned route in IoT Hub.
"long-summary": |-
    Test all existing routes or mentioned route in your IoT Hub. You can provide a sample message to test your routes.
"""

helps["iot dps certificate verify"] = """
"type": |-
    command
"short-summary": |-
    Verify an Azure IoT Hub Device Provisioning Service certificate.
"long-summary": |-
    Verify a certificate by uploading a verification certificate containing the verification code obtained by calling generate-verification-code. This is the last step in the proof of possession process.
"""

helps["iot hub consumer-group create"] = """
"type": |-
    command
"short-summary": |-
    Create an event hub consumer group.
"""

helps["iot dps update"] = """
"type": |-
    command
"short-summary": |-
    Update an Azure IoT Hub device provisioning service.
"""

helps["iot dps show"] = """
"type": |-
    command
"short-summary": |-
    Get the details of an Azure IoT Hub device provisioning service.
"""

helps["iot hub delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an IoT hub.
"""

helps["iot dps linked-hub create"] = """
"type": |-
    command
"short-summary": |-
    Create a linked IoT hub in an Azure IoT Hub device provisioning service.
"""

helps["iot dps access-policy show"] = """
"type": |-
    command
"short-summary": |-
    Show details of a shared access policies in an Azure IoT Hub device provisioning service.
"""

helps["iot dps certificate generate-verification-code"] = """
"type": |-
    command
"short-summary": |-
    Generate a verification code for an Azure IoT Hub Device Provisioning Service certificate.
"long-summary": |-
    This verification code is used to complete the proof of possession step for a certificate. Use this verification code as the CN of a new certificate signed with the root certificates private key.
"""

helps["iot dps linked-hub delete"] = """
"type": |-
    command
"short-summary": |-
    Update a linked IoT hub in an Azure IoT Hub device provisioning service.
"""

helps["iot hub"] = """
"type": |-
    group
"short-summary": |-
    Manage Azure IoT hubs.
"""

helps["iot hub routing-endpoint"] = """
"type": |-
    group
"short-summary": |-
    Manage custom endpoints of an IoT hub.
"""

helps["iot dps delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an Azure IoT Hub device provisioning service.
"""

helps["iot hub policy list"] = """
"type": |-
    command
"short-summary": |-
    List shared access policies of an IoT hub.
"""

helps["iot dps create"] = """
"type": |-
    command
"short-summary": |-
    Create an Azure IoT Hub device provisioning service.
"long-summary": |-
    For an introduction to Azure IoT Hub Device Provisioning Service, see https://docs.microsoft.com/en-us/azure/iot-dps/about-iot-dps
"""

helps["iot dps certificate delete"] = """
"type": |-
    command
"short-summary": |-
    Delete an Azure IoT Hub Device Provisioning Service certificate.
"""

helps["iot dps access-policy update"] = """
"type": |-
    command
"short-summary": |-
    Update a shared access policy in an Azure IoT Hub device provisioning service.
"""

helps["iot hub consumer-group"] = """
"type": |-
    group
"short-summary": |-
    Manage the event hub consumer groups of an IoT hub.
"""

helps["iot hub consumer-group show"] = """
"type": |-
    command
"short-summary": |-
    Get the details for an event hub consumer group.
"""

helps["iot hub route show"] = """
"type": |-
    command
"short-summary": |-
    Get information about the route in IoT Hub.
"long-summary": |-
    Get information on a specific route in your IoT Hub.
"""

helps["iot hub certificate create"] = """
"type": |-
    command
"short-summary": |-
    Create/upload an Azure IoT Hub certificate.
"long-summary": |-
    For a detailed explanation of CA certificates in Azure IoT Hub, see https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-x509ca-overview
"""

helps["iot dps access-policy create"] = """
"type": |-
    command
"short-summary": |-
    Create a new shared access policy in an Azure IoT Hub device provisioning service.
"""


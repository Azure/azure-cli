# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import ApiManagementServiceResource

def create_apim(cmd, client, 
    resource_group_name, 
    name, 
    publisher_email,
    sku,
    capacity=1,
    enable_client_certificate=False,
    publisher_name=None,
    location=None, 
    tags=None,
    no_wait=False):

    resource = {
        'location': location,
        'notification_sender_email': publisher_email,
        'publisher_email': publisher_email,
        'publisher_name': publisher_email,
        'sku': {
            'name': sku,
            'capacity': capacity
        },
        'enable_client_certificate': enable_client_certificate,
        'tags': tags
    }

    cms = client.api_management_service

    return sdk_no_wait(no_wait, cms.create_or_update, 
        resource_group_name = resource_group_name, 
        service_name = name, 
        parameters = resource
        )

def list_apim(client, resource_group_name=None):
    """List all APIM instances.  Resource group is optional """
    if resource_group_name:
        return client.api_management_service.list_by_resource_group(resource_group_name)
    return client.api_management_service.list()

def get_apim(client, resource_group_name, name):
    """Show details of an APIM instance """
    return client.api_management_service.get(resource_group_name, name)

def check_name_availability(client,  name):
    """checks to see if a service name is available to use """
    return client.api_management_service.check_name_availability(name)

def apim_backup(client, resource_group_name, name):
    """back up an API Management service to the configured storage account """
    return client.api_management_service.backup(resource_group_name, name)

def apim_apply_network_configuration_updates(client, resource_group_name, name):
    """back up an API Management service to the configured storage account """
    return client.api_management_service.apply_network_configuration_updates(resource_group_name, name)

# API Operations
def list_apim_api(client, resource_group_name, service_name):
    """List all APis for the given service instance """
    return client.api.list_by_service(resource_group_name, service_name)
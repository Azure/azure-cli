# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.apimanagement.models import (ApiManagementServiceResource, ApiManagementServiceIdentity, 
                                                                                       ApiManagementServiceSkuProperties)
from azure.mgmt.apimanagement.models.api_management_client_enums import (VirtualNetworkType, SkuType)

def create_apim(cmd, client, 
        resource_group_name, 
        name, 
        publisher_email,
        sku_name=SkuType.developer.value,
        sku_capacity=1,
        virtual_network_type=VirtualNetworkType.external.value,
        enable_managed_identity=False,
        enable_client_certificate=True,
        publisher_name=None,
        location=None, 
        tags=None,
        no_wait=False
    ):

    resource = ApiManagementServiceResource(
        location = location,
        notification_sender_email =publisher_email,
        publisher_email = publisher_email,
        publisher_name = publisher_email,
        sku = ApiManagementServiceSkuProperties(name = sku_name, capacity = sku_capacity),
        enable_client_certificate = enable_client_certificate,
        virtual_network_type = VirtualNetworkType(virtual_network_type),
        tags = tags
    )

    if (enable_managed_identity):
        resource['identity'] = ApiManagementServiceIdentity(type="SystemAssigned")

    cms = client.api_management_service

    return sdk_no_wait(no_wait, cms.create_or_update, 
        resource_group_name = resource_group_name, 
        service_name = name, 
        parameters = resource
        )

def update_apim(instance, start_ip_address=None, end_ip_address=None):
    #TODO: implement
    return instance

def update_apim_getter(client, resource_group_name, name):
    return client.api_management_service.get(resource_group_name, name)

def update_apim_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    return client.create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters.start_ip_address,
        parameters.end_ip_address)

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
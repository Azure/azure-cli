# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError
from azure.cli.core.commands.parameters import get_resources_in_subscription

from ._constants import (
    ACR_RESOURCE_PROVIDER,
    ACR_RESOURCE_TYPE,
    STORAGE_RESOURCE_TYPE
)
from ._factory import (
    get_arm_service_client,
    get_storage_service_client,
    get_acr_service_client,
    get_acr_api_version
)

def _arm_get_resource_by_name(resource_name, resource_type):
    '''Returns the ARM resource in the current subscription with resource_name.
    :param str resource_name: The name of resource
    :param str resource_type: The type of resource
    '''
    result = get_resources_in_subscription(resource_type)
    elements = [item for item in result if item.name.lower() == resource_name.lower()]

    if len(elements) == 0:
        raise CLIError(
            'No resource with type {} can be found with name: {}'.format(
                resource_type, resource_name))
    elif len(elements) == 1:
        return elements[0]
    else:
        raise CLIError(
            'More than one resources with type {} are found with name: {}'.format(
                resource_type, resource_name))

def get_resource_group_name_by_resource_id(resource_id):
    '''Returns the resource group name from parsing the resource id.
    :param str resource_id: The resource id
    '''
    resource_id = resource_id.lower()
    resource_group_keyword = '/resourcegroups/'
    return resource_id[resource_id.index(resource_group_keyword) + len(resource_group_keyword):
                       resource_id.index('/providers/')]

def get_resource_group_name_by_registry_name(registry_name):
    '''Returns the resource group name for the container registry.
    :param str registry_name: The name of container registry
    '''
    arm_resource = _arm_get_resource_by_name(registry_name, ACR_RESOURCE_TYPE)
    return get_resource_group_name_by_resource_id(arm_resource.id)

def get_resource_group_name_by_storage_account_name(storage_account_name):
    '''Returns the resource group name for the storage account.
    :param str storage_account_name: The name of storage account
    '''
    arm_resource = _arm_get_resource_by_name(storage_account_name, STORAGE_RESOURCE_TYPE)
    return get_resource_group_name_by_resource_id(arm_resource.id)

def get_registry_by_name(registry_name, resource_group_name=None):
    '''Returns a tuple of Registry object and resource group name.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    '''
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    client = get_acr_service_client().registries

    return client.get_properties(resource_group_name, registry_name), resource_group_name

def get_access_key_by_storage_account_name(storage_account_name, resource_group_name=None):
    '''Returns access key for the storage account.
    :param str storage_account_name: The name of storage account
    :param str resource_group_name: The name of resource group
    '''
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_storage_account_name(storage_account_name)

    client = get_storage_service_client().storage_accounts

    return client.list_keys(resource_group_name, storage_account_name).keys[0].value #pylint: disable=no-member

def arm_deploy_template(resource_group_name,
                        registry_name,
                        location,
                        storage_account_name,
                        admin_user_enabled):
    '''Deploys ARM template to create a container registry with a new storage account.
    :param str resource_group_name: The name of resource group
    :param str registry_name: The name of container registry
    :param str location: The name of location
    :param str storage_account_name: The name of storage account
    :param bool admin_user_enabled: Enable admin user
    '''
    from azure.mgmt.resource.resources.models import DeploymentProperties
    from azure.cli.core._util import get_file_json
    import os

    parameters = _parameters(registry_name, location, storage_account_name, admin_user_enabled)

    file_path = os.path.join(os.path.dirname(__file__), 'template.json')
    template = get_file_json(file_path)
    properties = DeploymentProperties(template=template, parameters=parameters, mode='incremental')

    return _arm_deploy_template(
        get_arm_service_client().deployments, resource_group_name, properties)

def _arm_deploy_template(deployments_client,
                         resource_group_name,
                         properties,
                         index=0):
    '''Deploys ARM template to create a container registry.
    :param obj deployments_client: ARM deployments service client
    :param str resource_group_name: The name of resource group
    :param DeploymentProperties properties: The properties of a deployment
    :param int index: The index added to deployment name to avoid conflict
    '''
    if index == 0:
        deployment_name = ACR_RESOURCE_PROVIDER
    elif index > 9: # Just a number to avoid infinite loops
        raise CLIError(
            'The resource group {} has too many deployments'.format(resource_group_name))
    else:
        deployment_name = ACR_RESOURCE_PROVIDER + '_' + str(index)

    try:
        deployments_client.validate(
            resource_group_name, deployment_name, properties)
        return deployments_client.create_or_update(
            resource_group_name, deployment_name, properties)
    except: #pylint: disable=bare-except
        return _arm_deploy_template(
            deployments_client, resource_group_name, properties, index + 1)

def _parameters(registry_name,
                location,
                storage_account_name,
                admin_user_enabled):
    '''Returns a dict of deployment parameters.
    :param str registry_name: The name of container registry
    :param str location: The name of location
    :param str storage_account_name: The name of storage account
    :param bool admin_user_enabled: Enable admin user
    '''
    parameters = {
        'registryName': {'value': registry_name},
        'registryLocation': {'value': location},
        'storageAccountName': {'value': storage_account_name},
        'adminUserEnabled': {'value': admin_user_enabled},
    }
    customized_api_version = get_acr_api_version()
    if customized_api_version:
        parameters['registryApiVersion'] = {'value': customized_api_version}
    return parameters

def random_storage_account_name(registry_name):
    from datetime import datetime

    client = get_storage_service_client().storage_accounts

    while True:
        time_stamp_suffix = datetime.utcnow().strftime('%H%M%S')
        storage_account_name = ''.join([registry_name[:18], time_stamp_suffix])[:24]
        if client.check_name_availability(storage_account_name).name_available: #pylint: disable=no-member
            return storage_account_name

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError

from ._factory import get_acr_service_client

def _get_registries_in_subscription():
    '''Returns the list of container registries in the current subscription.
    '''
    client = get_acr_service_client().registries
    return client.list().value #pylint: disable=no-member

def _get_registries_in_resource_group(resource_group_name):
    '''Returns the list of container registries in the resource group.
    :param str resource_group_name: The name of resource group
    '''
    client = get_acr_service_client().registries
    return client.list_by_resource_group(resource_group_name).value #pylint: disable=no-member

def get_registry_by_name(registry_name):
    '''Returns the container registry that matches the registry name.
    :param str registry_name: The name of container registry
    '''
    registries = _get_registries_in_subscription()
    elements = [item for item in registries if item.name.lower() == registry_name.lower()]

    if len(elements) == 0:
        return None
    elif len(elements) == 1:
        return elements[0]
    else:
        raise ValueError('More than one container registries are found with name: ' + registry_name)

def get_resource_group_name_by_resource_id(resource_id):
    '''Returns the resource group name from parsing the resource id.
    :param str resource_id: The resource id
    '''
    resource_id = resource_id.lower()
    resource_group_keyword = '/resourcegroups/'
    return resource_id[resource_id.index(resource_group_keyword) + len(resource_group_keyword):
                       resource_id.index('/providers/')]

def registry_not_found(registry_name):
    raise CLIError(
        'Registry {} cannot be found in the current subscription.'\
        .format(registry_name))

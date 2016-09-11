#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import uuid
import datetime

from azure.graphrbac.models import ServicePrincipalCreateParameters
from azure.cli.core._util import CLIError
from azure.cli.command_modules.role.custom import create_application

from ._factory import (
    get_acr_service_client,
    get_graph_mgmt_client
)

def _get_registries_in_subscription():
    '''Returns the list of container registries in the current subscription.
    '''
    client = get_acr_service_client().registries
    return client.list().value #pylint: disable=E1101

def _get_registries_in_resource_group(resource_group_name):
    '''Returns the list of container registries in the resource group.
    :param str resource_group_name: The name of resource group
    '''
    client = get_acr_service_client().registries
    return client.list_by_resource_group(resource_group_name).value #pylint: disable=E1101

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

def create_service_principal(registry_name, password=None):
    '''Creates an application and a service principal.
    :param str registry_name: The name of container registry
    :param str password: The password for container registry login
    '''
    client = get_graph_mgmt_client()

    start_date = datetime.datetime.now()
    app_display_name = registry_name + '-' + start_date.strftime('%Y%m%d%H%M%S')
    app_uri = 'http://' + app_display_name # just a valid uri, no need to exist
    password_creds = password or str(uuid.uuid4())

    application = create_application(client.applications,
                                     display_name=app_display_name,
                                     homepage=app_uri,
                                     identifier_uris=[app_uri],
                                     password=password_creds)

    app_id = application.app_id #pylint: disable=E1101
    service_principal = client.service_principals.create(
        ServicePrincipalCreateParameters(app_id, True), raw=True)
    session_key = service_principal.response.headers._store['ocp-aad-session-key'][1] #pylint: disable=W0212

    return (app_id,
            password_creds,
            session_key)

def registry_not_found(registry_name):
    raise CLIError(
        'ERROR: Registry {} cannot be found in the current subscription.'\
        .format(registry_name))

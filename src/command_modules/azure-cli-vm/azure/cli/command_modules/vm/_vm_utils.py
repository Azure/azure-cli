# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from azure.cli.core._util import get_file_json, CLIError
from azure.cli.core.commands.arm import parse_resource_id


def random_string(length=16, force_lower=False):
    from string import ascii_letters, digits, ascii_lowercase
    from random import choice
    choice_set = ascii_lowercase + digits if force_lower else ascii_letters + digits
    return ''.join([choice(choice_set) for n in range(length)])  # pylint: disable=unused-variable


def read_content_if_is_file(string_or_file):
    content = string_or_file
    if os.path.exists(string_or_file):
        with open(string_or_file, 'r') as f:
            content = f.read()
    return content


def load_json(string_or_file_path):
    if os.path.exists(string_or_file_path):
        return get_file_json(string_or_file_path)
    else:
        return json.loads(string_or_file_path)


def _resolve_api_version(provider_namespace, resource_type, parent_path):
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    client = get_mgmt_service_client(ResourceManagementClient)
    provider = client.providers.get(provider_namespace)

    # If available, we will use parent resource's api-version
    resource_type_str = (parent_path.split('/')[0] if parent_path else resource_type)

    rt = [t for t in provider.resource_types  # pylint: disable=no-member
          if t.resource_type.lower() == resource_type_str.lower()]
    if not rt:
        raise CLIError('Resource type {} not found.'.format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    else:
        raise CLIError(
            'API version is required and could not be resolved for resource {}'
            .format(resource_type))


# pylint: disable=too-many-arguments
def check_existence(value, resource_group, provider_namespace, resource_type,
                    parent_name=None, parent_type=None):
    # check for name or ID and set the type flags
    from azure.mgmt.resource.resources import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from msrestazure.azure_exceptions import CloudError
    resource_client = get_mgmt_service_client(ResourceManagementClient).resources

    id_parts = parse_resource_id(value)

    rg = id_parts.get('resource_group', resource_group)
    ns = id_parts.get('namespace', provider_namespace)

    if parent_name and parent_type:
        parent_path = '{}/{}'.format(parent_type, parent_name)
        resource_name = id_parts.get('child_name', value)
        resource_type = id_parts.get('child_type', resource_type)
    else:
        parent_path = ''
        resource_name = id_parts['name']
        resource_type = id_parts.get('type', resource_type)
    api_version = _resolve_api_version(provider_namespace, resource_type, parent_path)

    try:
        resource_client.get(rg, ns, parent_path, resource_type, resource_name, api_version)
        return True
    except CloudError:
        return False

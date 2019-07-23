# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError


def create_apim(cmd, client, resource_group_name, apimanamagement, location=None, tags=None):
    raise CLIError('TODO: Implement `apim create`')

def list_apim(client, resource_group_name=None):
    """List all APIM instances.  Resource group is optional """
    if resource_group_name:
        return client.api_management_service.list_by_resource_group(resource_group_name)
    return client.api_management_service.list()

def get_apim(client, resource_group_name, name):
    """Show details of an APIM instance """
    return client.get(resource_group_name, name)

def update_apim(cmd, instance, tags=None):
    with cmd.update_context(instance) as c:
        c.set_param('tags', tags)
    return instance
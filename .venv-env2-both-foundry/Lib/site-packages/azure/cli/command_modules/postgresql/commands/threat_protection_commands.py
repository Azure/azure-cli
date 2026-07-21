# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.core.exceptions import HttpResponseError
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import validate_resource_group


def flexible_server_threat_protection_get(
        client,
        resource_group_name,
        server_name):
    '''
    Gets an advanced threat protection setting.
    '''

    validate_resource_group(resource_group_name)

    return client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        threat_protection_name="Default")


def flexible_server_threat_protection_update(
        cmd,
        client, resource_group_name, server_name,
        state=None):
    # pylint: disable=unused-argument
    '''
    Updates an advanced threat protection setting. Custom update function to apply parameters to instance.
    '''

    validate_resource_group(resource_group_name)

    try:
        parameters = {
            'properties': {
                'state': state
            }
        }
        return resolve_poller(
            client.begin_create_or_update(
                resource_group_name=resource_group_name,
                server_name=server_name,
                threat_protection_name="Default",
                parameters=parameters),
            cmd.cli_ctx,
            'PostgreSQL Flexible Server Advanced Threat Protection Setting Update')
    except HttpResponseError as ex:
        if "Operation returned an invalid status 'Accepted'" in ex.message:
            # TODO: Once the swagger is updated, this won't be needed.
            pass
        else:
            raise ex


def flexible_server_threat_protection_set(
        cmd,
        client,
        resource_group_name,
        server_name,
        parameters):
    validate_resource_group(resource_group_name)

    return resolve_poller(
        client.begin_create_or_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            threat_protection_name="Default",
            parameters=parameters),
        cmd.cli_ctx,
        'PostgreSQL Flexible Server Advanced Threat Protection Setting Update')

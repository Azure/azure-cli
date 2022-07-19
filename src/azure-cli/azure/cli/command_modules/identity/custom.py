# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def list_user_assigned_identities(cmd, resource_group_name=None):
    from azure.cli.command_modules.identity._client_factory import _msi_client_factory
    client = _msi_client_factory(cmd.cli_ctx)
    if resource_group_name:
        return client.user_assigned_identities.list_by_resource_group(resource_group_name)
    return client.user_assigned_identities.list_by_subscription()


def create_identity(client, resource_group_name, resource_name, location, tags=None):
    parameters = {}
    parameters['location'] = location
    if tags is not None:
        parameters['tags'] = tags
    return client.create_or_update(resource_group_name=resource_group_name,
                                   resource_name=resource_name,
                                   parameters=parameters)

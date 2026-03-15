# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import CLIError
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from .._client_factory import cf_postgres_flexible_config
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import validate_citus_cluster, validate_resource_group


def flexible_server_identity_update(cmd, client, resource_group_name, server_name, system_assigned):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)
    identity_type = server.identity.type if (server and server.identity and server.identity.type) else 'None'

    if system_assigned.lower() == 'enabled':
        # user wants to enable system-assigned identity
        if identity_type == 'None':
            # if user-assigned identity is not enabled, then enable system-assigned identity
            identity_type = 'SystemAssigned'
        elif identity_type == 'UserAssigned':
            # if user-assigned identity is enabled, then enable both system-assigned and user-assigned identity
            identity_type = 'SystemAssigned,UserAssigned'
    else:
        # check if fabric is enabled
        config_client = cf_postgres_flexible_config(cmd.cli_ctx, '_')
        fabric_mirror_status = config_client.get(resource_group_name, server_name, 'azure.fabric_mirror_enabled')
        if (fabric_mirror_status and fabric_mirror_status.value.lower() == 'on'):
            raise CLIError("On servers for which Fabric mirroring is enabled, system assigned managed identity cannot be disabled.")
        if server.data_encryption.type == 'AzureKeyVault':
            # if data encryption is enabled, then system-assigned identity cannot be disabled
            raise CLIError("On servers for which data encryption is based on customer managed key, system assigned managed identity cannot be disabled.")
        if identity_type == 'SystemAssigned,UserAssigned':
            # if both system-assigned and user-assigned identity is enabled, then disable system-assigned identity
            identity_type = 'UserAssigned'
        elif identity_type == 'SystemAssigned':
            # if only system-assigned identity is enabled, then disable system-assigned identity
            identity_type = 'None'

    if identity_type == 'UserAssigned' or identity_type == 'SystemAssigned,UserAssigned':
        identities_map = {}
        for identity in server.identity.user_assigned_identities:
            identities_map[identity] = {}
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                user_assigned_identities=identities_map,
                type=identity_type)}
    else:
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                type=identity_type)}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Updating user assigned identity type for server {}'.format(server_name)
    )

    return result.identity


def flexible_server_identity_assign(cmd, client, resource_group_name, server_name, identities):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)
    identity_type = server.identity.type if (server and server.identity and server.identity.type) else 'None'

    if identity_type == 'SystemAssigned':
        # if system-assigned identity is enabled, then enable both system
        identity_type = 'SystemAssigned,UserAssigned'
    elif identity_type == 'None':
        # if system-assigned identity is not enabled, then enable user-assigned identity
        identity_type = 'UserAssigned'

    identities_map = {}
    for identity in identities:
        identities_map[identity] = {}

    parameters = {
        'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
            user_assigned_identities=identities_map,
            type=identity_type)}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Adding identities to server {}'.format(server_name)
    )

    return result.identity


def flexible_server_identity_remove(cmd, client, resource_group_name, server_name, identities):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    instance = client.get(resource_group_name, server_name)

    if instance.data_encryption:
        primary_id = instance.data_encryption.primary_user_assigned_identity_id

        if primary_id and primary_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for data encryption.".format(primary_id))

        geo_backup_id = instance.data_encryption.geo_backup_user_assigned_identity_id

        if geo_backup_id and geo_backup_id.lower() in [identity.lower() for identity in identities]:
            raise CLIError("Cannot remove identity {} because it's used for geo backup data encryption.".format(geo_backup_id))

    identities_map = {}
    for identity in identities:
        identities_map[identity] = None

    system_assigned_identity = instance.identity and instance.identity.principal_id is not None

    # if there are no user-assigned identities or all user-assigned identities are already removed
    if not (instance.identity and instance.identity.user_assigned_identities) or \
       all(key.lower() in [identity.lower() for identity in identities] for key in instance.identity.user_assigned_identities.keys()):
        if system_assigned_identity:
            # if there is system assigned identity, then set identity type to SystemAssigned
            parameters = {
                'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                    type="SystemAssigned")}
        else:
            # no system assigned identity, set identity type to None
            parameters = {
                'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                    type="None")}
    # if there are user-assigned identities and system assigned identity, then set identity type to SystemAssigned,UserAssigned
    elif system_assigned_identity:
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                user_assigned_identities=identities_map,
                type="SystemAssigned,UserAssigned")}
    # there is no system assigned identity, but there are user-assigned identities, then set identity type to UserAssigned
    else:
        parameters = {
            'identity': postgresql_flexibleservers.models.UserAssignedIdentity(
                user_assigned_identities=identities_map,
                type="UserAssigned")}

    result = resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Removing identities from server {}'.format(server_name)
    )

    return result.identity or postgresql_flexibleservers.models.UserAssignedIdentity(type="SystemAssigned")


def flexible_server_identity_list(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)
    return server.identity or postgresql_flexibleservers.models.UserAssignedIdentity(type="SystemAssigned")


def flexible_server_identity_show(cmd, client, resource_group_name, server_name, identity):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    server = client.get(resource_group_name, server_name)

    for key, value in server.identity.user_assigned_identities.items():
        if key.lower() == identity.lower():
            return value

    raise CLIError("Identity '{}' does not exist in server {}.".format(identity, server_name))

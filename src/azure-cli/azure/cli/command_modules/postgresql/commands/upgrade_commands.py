# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import user_confirmation
from knack.util import CLIError
from .._client_factory import cf_postgres_flexible_replica
from ..utils._flexible_server_location_capabilities_util import get_postgres_server_capability_info
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import pg_version_validator, validate_citus_cluster, validate_resource_group


def flexible_server_version_upgrade(cmd, client, resource_group_name, server_name, version, yes=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    if not yes:
        user_confirmation(
            "Upgrading major version in server {} is irreversible. The action you're about to take can't be undone. "
            "Going further will initiate major version upgrade to the selected version on this server."
            .format(server_name), yes=yes)

    instance = client.get(resource_group_name, server_name)

    if instance and instance.storage.type == "PremiumV2_LRS" and version and int(version) < 14:
        raise CLIError('Storage type PremiumV2_LRS is only supported for PostgreSQL version 14 and above.')

    current_version = int(instance.version.split('.')[0])
    if current_version >= int(version):
        raise CLIError("The version to upgrade to must be greater than the current version.")

    list_server_capability_info = get_postgres_server_capability_info(cmd, resource_group_name, server_name)
    eligible_versions = list_server_capability_info['supported_server_versions'][str(current_version)]

    pg_version_validator(version, eligible_versions)

    if version not in eligible_versions:
        # version not supported
        error_message = ""
        if len(eligible_versions) > 0:
            error_message = "Server is running version {}. It can only be upgraded to the following versions: {} ".format(str(current_version), eligible_versions)
        else:
            error_message = "Server is running version {}. It cannot be upgraded to any higher version. ".format(str(current_version))

        raise CLIError(error_message)

    replica_operations_client = cf_postgres_flexible_replica(cmd.cli_ctx, '_')
    version_mapped = version

    replicas = replica_operations_client.list_by_server(resource_group_name, server_name)

    if 'replica' in instance.replication_role.lower() or len(list(replicas)) > 0:
        raise CLIError("Major version upgrade is not yet supported for servers in a read replica setup.")

    parameters = {
        'properties': {
            'version': version_mapped
        }
    }

    return resolve_poller(
        client.begin_update(
            resource_group_name=resource_group_name,
            server_name=server_name,
            parameters=parameters),
        cmd.cli_ctx, 'Upgrading server {} to major version {}'.format(server_name, version)
    )

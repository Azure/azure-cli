# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.command_modules.postgresql.utils.validators import is_citus_cluster, validate_resource_group
from azure.cli.core.azclierror import ValidationError
from azure.cli.core.util import CLIError
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers


def flexible_replica_promote(cmd, client, resource_group_name, replica_name, promote_mode='standalone', promote_option='planned'):
    validate_resource_group(resource_group_name)
    if is_citus_cluster(cmd, resource_group_name, replica_name):
        # some settings validation
        if promote_mode.lower() == 'standalone':
            raise ValidationError("Standalone replica promotion on elastic cluster isn't currently supported. Please use 'switchover' instead.")
        if promote_option.lower() == 'planned':
            raise ValidationError("Planned replica promotion on elastic cluster isn't currently supported. Please use 'forced' instead.")

    try:
        server_object = client.get(resource_group_name, replica_name)
    except Exception as e:
        raise ResourceNotFoundError(e)

    if server_object.replica.role is not None and "replica" not in server_object.replica.role.lower():
        raise CLIError('Server {} is not a replica server.'.format(replica_name))

    if promote_mode == "standalone":
        params = postgresql_flexibleservers.models.ServerForPatch(
            replica=postgresql_flexibleservers.models.Replica(
                role='None',
                promote_mode=promote_mode,
                promote_option=promote_option
            )
        )
    else:
        params = postgresql_flexibleservers.models.ServerForPatch(
            replica=postgresql_flexibleservers.models.Replica(
                role='Primary',
                promote_mode=promote_mode,
                promote_option=promote_option
            )
        )

    return client.begin_update(resource_group_name, replica_name, params)

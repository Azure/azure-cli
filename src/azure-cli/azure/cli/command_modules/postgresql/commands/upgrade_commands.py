# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
import time
from knack.log import get_logger
from azure.cli.core.util import user_confirmation
from knack.util import CLIError
from .._client_factory import cf_postgres_flexible_replica, cf_postgres_flexible_major_version_upgrade_precheck
from ..utils._flexible_server_location_capabilities_util import get_postgres_server_capability_info
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import pg_version_validator, validate_citus_cluster, validate_resource_group

logger = get_logger(__name__)


def flexible_server_version_upgrade(cmd, client, resource_group_name, server_name, version, validate=None, yes=None):
    if validate:
        return _flexible_server_version_upgrade_validate(cmd, client, resource_group_name, server_name, version)

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


def _flexible_server_version_upgrade_validate(cmd, client, resource_group_name, server_name, version):
    body = {
        'targetVersion': version
    }

    start_response = resolve_poller(
        client.begin_start_major_version_upgrade_precheck(
            resource_group_name=resource_group_name,
            server_name=server_name,
            body=body),
        cmd.cli_ctx,
        'Starting major version upgrade precheck for server {} targeting version {}'.format(server_name, version)
    )

    precheck_validation_id = _get_attr_or_key(start_response, 'name')
    if not precheck_validation_id:
        raise CLIError('Failed to retrieve precheck validation id from the upgrade precheck response.')

    precheck_client = cf_postgres_flexible_major_version_upgrade_precheck(cmd.cli_ctx, '_')
    
    return precheck_client.get(
        resource_group_name=resource_group_name,
        server_name=server_name,
        precheck_validation_id=precheck_validation_id)


def _get_attr_or_key(obj, name):
    if obj is None:
        return None
    value = getattr(obj, name, None)
    if value is not None:
        return value
    if isinstance(obj, dict):
        return obj.get(name)
    properties = getattr(obj, 'properties', None)
    if properties is not None:
        return _get_attr_or_key(properties, name)
    return None


def _get_status(obj):
    status = _get_attr_or_key(obj, 'status')
    if status is None:
        return None
    # Some SDK enums expose .value
    return getattr(status, 'value', status)

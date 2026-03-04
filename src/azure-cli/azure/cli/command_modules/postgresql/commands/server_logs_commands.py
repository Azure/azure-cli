# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
import re

from azure.cli.core.util import CLIError, user_confirmation
from datetime import datetime, timedelta
from dateutil.tz import tzutc   # pylint: disable=import-error
from knack.log import get_logger
from urllib.request import urlretrieve
from .._client_factory import cf_postgres_flexible_replica
from ..utils._flexible_server_location_capabilities_util import get_postgres_server_capability_info
from ..utils._flexible_server_util import resolve_poller
from ..utils.validators import validate_citus_cluster, validate_resource_group

logger = get_logger(__name__)


def flexible_server_download_log_files(client, resource_group_name, server_name, file_name):
    validate_resource_group(resource_group_name)

    # list all files
    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name.replace("/", "_"))


def flexible_server_list_log_files_with_filter(client, resource_group_name, server_name, filename_contains=None,
                                               file_last_written=None, max_file_size=None):
    validate_resource_group(resource_group_name)

    # list all files
    all_files = client.list_by_server(resource_group_name, server_name)
    files = []

    if file_last_written is None:
        file_last_written = 72
    time_line = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(hours=file_last_written)

    for f in all_files:
        if f.last_modified_time < time_line:
            continue
        if filename_contains is not None and re.search(filename_contains, f.name) is None:
            continue
        if max_file_size is not None and f.size_in_kb > max_file_size:
            continue

        del f.created_time
        files.append(f)

    return files


def flexible_server_log_list(client, resource_group_name, server_name, filename_contains=None,
                             file_last_written=None, max_file_size=None):
    validate_resource_group(resource_group_name)

    all_files = client.list_by_server(resource_group_name, server_name)
    files = []

    if file_last_written is None:
        file_last_written = 72
    time_line = datetime.utcnow().replace(tzinfo=tzutc()) - timedelta(hours=file_last_written)

    for f in all_files:
        if f.last_modified_time < time_line:
            continue
        if filename_contains is not None and re.search(filename_contains, f.name) is None:
            continue
        if max_file_size is not None and f.size_in_kb > max_file_size:
            continue

        del f.created_time
        files.append(f)

    return files


def flexible_server_version_upgrade(cmd, client, resource_group_name, server_name, version, yes=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    if not yes:
        user_confirmation(
            "Upgrading major version in server {} is irreversible. The action you're about to take can't be undone. "
            "Going further will initiate major version upgrade to the selected version on this server."
            .format(server_name), yes=yes)

    instance = client.get(resource_group_name, server_name)

    current_version = int(instance.version.split('.')[0])
    if current_version >= int(version):
        raise CLIError("The version to upgrade to must be greater than the current version.")

    list_server_capability_info = get_postgres_server_capability_info(cmd, resource_group_name, server_name)
    eligible_versions = list_server_capability_info['supported_server_versions'][str(current_version)]

    if version == '13':
        logger.warning("PostgreSQL version 13 will reach end-of-life (EOL) soon. "
                       "Upgrade to PostgreSQL 14 or later as soon as possible to "
                       "maintain security, performance, and supportability.")

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

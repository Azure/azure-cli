# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from datetime import datetime
from azure.cli.core.util import user_confirmation
from knack.log import get_logger
from ..utils.validators import validate_resource_group, validate_backup_name

logger = get_logger(__name__)

_BACKUP_NAME_PREFIX = "ondemandbackup"


def _generate_backup_name(client, resource_group_name, server_name):
    existing_backups = client.list_by_server(resource_group_name, server_name)
    existing_names = {backup.name for backup in existing_backups}

    on_demand_count = sum(1 for name in existing_names if name.startswith(_BACKUP_NAME_PREFIX))

    date_str = datetime.utcnow().strftime("%m%d%Y")
    suffix = on_demand_count + 1
    backup_name = f"{_BACKUP_NAME_PREFIX}-{date_str}-{suffix}"
    while backup_name in existing_names:
        suffix += 1
        backup_name = f"{_BACKUP_NAME_PREFIX}-{date_str}-{suffix}"

    return backup_name


def backup_create_func(client, resource_group_name, server_name, backup_name=None):
    validate_resource_group(resource_group_name)

    if not backup_name:
        backup_name = _generate_backup_name(client, resource_group_name, server_name)
        logger.warning("No backup name provided. Using generated name: %s", backup_name)
    else:
        validate_backup_name(backup_name)

    return client.begin_create(
        resource_group_name,
        server_name,
        backup_name)


def backup_delete_func(client, resource_group_name, server_name, backup_name, yes=False):
    validate_resource_group(resource_group_name)

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the backup '{0}' in server '{1}'".format(backup_name, server_name), yes=yes)

    return client.begin_delete(
        resource_group_name,
        server_name,
        backup_name)

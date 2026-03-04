# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import user_confirmation
from knack.log import get_logger
from ..utils.validators import validate_resource_group, validate_backup_name

logger = get_logger(__name__)


def backup_create_func(client, resource_group_name, server_name, backup_name):
    validate_resource_group(resource_group_name)
    validate_backup_name(backup_name)

    return client.begin_create(
        resource_group_name,
        server_name,
        backup_name)


def ltr_precheck_func(client, resource_group_name, server_name, backup_name):
    validate_resource_group(resource_group_name)

    return client.check_prerequisites(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters={"backupSettings": {"backupName": backup_name}}
    )


def ltr_start_func(client, resource_group_name, server_name, backup_name, sas_url):
    validate_resource_group(resource_group_name)

    parameters = {
        "backupSettings": {
            "backupName": backup_name
        },
        "targetDetails": {
            "sasUriList": [sas_url]
        }
    }

    return client.begin_start(
        resource_group_name=resource_group_name,
        server_name=server_name,
        parameters=parameters
    )


def backup_delete_func(client, resource_group_name, server_name, backup_name, yes=False):
    validate_resource_group(resource_group_name)

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the backup '{0}' in server '{1}'".format(backup_name, server_name), yes=yes)

    return client.begin_delete(
        resource_group_name,
        server_name,
        backup_name)

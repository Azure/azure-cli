# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.util import CLIError, user_confirmation
from knack.log import get_logger
from ..utils.validators import (
    validate_resource_group,
    check_resource_group,
    validate_citus_cluster,
    validate_database_name)

logger = get_logger(__name__)


def database_create_func(cmd, client, resource_group_name, server_name, database_name=None, charset=None, collation=None):
    validate_database_name(database_name)
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    if charset is None and collation is None:
        charset = 'utf8'
        collation = 'en_US.utf8'
        logger.warning("Creating database with utf8 charset and en_US.utf8 collation")
    elif (not charset and collation) or (charset and not collation):
        raise RequiredArgumentMissingError("charset and collation have to be input together.")

    parameters = {
        'name': database_name,
        'charset': charset,
        'collation': collation
    }

    return client.begin_create(
        resource_group_name,
        server_name,
        database_name,
        parameters)


def database_delete_func(cmd, client, resource_group_name=None, server_name=None, database_name=None, yes=None):
    if not check_resource_group(resource_group_name):
        resource_group_name = None

    result = None
    if resource_group_name is None or server_name is None or database_name is None:
        raise CLIError("Incorrect Usage : Deleting a database needs resource-group, server-name and database-name. "
                       "If your parameter persistence is turned ON, make sure these three parameters exist in "
                       "persistent parameters using \'az config param-persist show\'. "
                       "If your parameter persistence is turned OFF, consider passing them explicitly.")
    if not yes:
        user_confirmation(
            "Are you sure you want to delete the database '{0}' of server '{1}'".format(database_name,
                                                                                        server_name), yes=yes)

    validate_citus_cluster(cmd, resource_group_name, server_name)
    try:
        result = client.begin_delete(resource_group_name, server_name, database_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result

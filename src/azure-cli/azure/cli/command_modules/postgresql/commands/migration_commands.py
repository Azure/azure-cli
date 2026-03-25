# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
import json
import os
import uuid

from azure.cli.core.azclierror import (
    BadRequestError,
    FileOperationError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.mgmt import postgresqlflexibleservers as postgresql_flexibleservers
from knack.log import get_logger
from ..utils._flexible_server_util import (
    generate_missing_parameters,
    get_case_insensitive_key_value,
    get_enum_value_true_false,
)
from ..utils.validators import (
    validate_citus_cluster,
    validate_migration_runtime_server,
    validate_resource_group,
)

logger = get_logger(__name__)


def migration_create_func(cmd, client, resource_group_name, server_name, properties, migration_mode="offline",
                          migration_name=None, migration_option=None, tags=None, location=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    logging_name = 'PostgreSQL'
    subscription_id = get_subscription_id(cmd.cli_ctx)
    properties_filepath = os.path.join(os.path.abspath(os.getcwd()), properties)
    # Generate missing parameters
    location, resource_group_name, server_name = generate_missing_parameters(cmd, location, resource_group_name,
                                                                             server_name, 'postgres')

    # Get the properties for migration from the json file at the specific properties file path
    if not os.path.exists(properties_filepath):
        raise FileOperationError("Properties file does not exist in the given location")
    with open(properties_filepath, "r") as f:
        try:
            request_payload = json.load(f)
            migration_parameters = request_payload.get("properties")
        except ValueError as err:
            logger.error(err)
            raise BadRequestError("Invalid json file. Make sure that the json file content is properly formatted.")

    if migration_name is None:
        # Convert a UUID to a string of hex digits in standard form
        migration_name = str(uuid.uuid4())

    if migration_option is None:
        # Use default migration_option as 'ValidateAndMigrate'
        migration_option = "ValidateAndMigrate"

    return _create_migration(cmd, logging_name, client, subscription_id, resource_group_name, server_name, migration_name,
                             migration_mode, migration_option, migration_parameters, tags, location)


def _create_migration(cmd, logging_name, client, subscription_id, resource_group_name, target_db_server_name,
                      migration_name, migration_mode, migration_option, parameters, tags, location):
    validate_resource_group(resource_group_name)

    parameter_keys = list(parameters.keys())
    migrationInstanceResourceId = get_case_insensitive_key_value("MigrationRuntimeResourceId", parameter_keys, parameters)
    if migrationInstanceResourceId is not None:
        validate_migration_runtime_server(cmd, migrationInstanceResourceId, resource_group_name, target_db_server_name)

    logger.warning('Creating %s Migration for server \'%s\' in group \'%s\' and subscription \'%s\'...', logging_name, target_db_server_name, resource_group_name, subscription_id)
    secret_parameter_dictionary = get_case_insensitive_key_value("SecretParameters", parameter_keys, parameters)
    secret_parameter_keys = list(secret_parameter_dictionary.keys())
    admin_credentials_dictionary = get_case_insensitive_key_value("AdminCredentials", secret_parameter_keys, secret_parameter_dictionary)
    admin_credentials_keys = list(admin_credentials_dictionary.keys())
    source_type = get_case_insensitive_key_value("SourceType", parameter_keys, parameters)
    ssl_mode = get_case_insensitive_key_value("SslMode", parameter_keys, parameters)

    admin_credentials = postgresql_flexibleservers.models.AdminCredentials(
        source_server_password=get_case_insensitive_key_value("SourceServerPassword", admin_credentials_keys, admin_credentials_dictionary),
        target_server_password=get_case_insensitive_key_value("TargetServerPassword", admin_credentials_keys, admin_credentials_dictionary))
    secret_parameters = postgresql_flexibleservers.models.MigrationSecretParameters(
        admin_credentials=admin_credentials,
        source_server_username=get_case_insensitive_key_value("SourceServerUsername", secret_parameter_keys, secret_parameter_dictionary),
        target_server_username=get_case_insensitive_key_value("TargetServerUsername", secret_parameter_keys, secret_parameter_dictionary))
    migration_parameters = postgresql_flexibleservers.models.Migration(
        tags=tags,
        location=location,
        migration_mode=migration_mode,
        source_db_server_resource_id=get_case_insensitive_key_value("SourceDbServerResourceId", parameter_keys, parameters),
        secret_parameters=secret_parameters,
        source_db_server_fully_qualified_domain_name=get_case_insensitive_key_value("SourceDbServerFullyQualifiedDomainName", parameter_keys, parameters),
        target_db_server_fully_qualified_domain_name=get_case_insensitive_key_value("TargetDbServerFullyQualifiedDomainName", parameter_keys, parameters),
        dbs_to_migrate=get_case_insensitive_key_value("DbsToMigrate", parameter_keys, parameters),
        setup_logical_replication_on_source_db_if_needed=get_enum_value_true_false(get_case_insensitive_key_value("SetupLogicalReplicationOnSourceDbIfNeeded", parameter_keys, parameters), "SetupLogicalReplicationOnSourceDbIfNeeded"),
        overwrite_dbs_in_target=get_enum_value_true_false(get_case_insensitive_key_value("OverwriteDbsInTarget", parameter_keys, parameters), "OverwriteDbsInTarget"),
        source_type=source_type,
        migration_option=migration_option,
        ssl_mode=ssl_mode,
        migration_instance_resource_id=migrationInstanceResourceId)

    return client.create(resource_group_name, server_name=target_db_server_name, migration_name=migration_name, parameters=migration_parameters)


def migration_show_func(cmd, client, resource_group_name, server_name, migration_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.get(resource_group_name, server_name, migration_name)


def migration_list_func(cmd, client, resource_group_name, server_name, migration_filter="Active"):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    return client.list_by_target_server(resource_group_name, server_name, migration_list_filter=migration_filter)


def migration_delete_func(cmd, client, resource_group_name, server_name, migration_name):
    validate_resource_group(resource_group_name)

    return client.cancel(resource_group_name, server_name, migration_name)


def migration_update_func(cmd, client, resource_group_name, server_name, migration_name, setup_logical_replication=None, cutover=None, cancel=None):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    operationSpecified = False
    if setup_logical_replication is True:
        operationSpecified = True
        parameters = postgresql_flexibleservers.models.MigrationResourceForPatch(setup_logical_replication_on_source_db_if_needed=True)

    if cutover is not None:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        migration_resource = migration_show_func(cmd, client, resource_group_name, server_name, migration_name)
        if migration_resource.migration_mode == "Offline":
            raise BadRequestError("Cutover is not possible for migration {} if the migration_mode set to offline. The migration will cutover automatically".format(migration_name))
        parameters = postgresql_flexibleservers.models.MigrationResourceForPatch(trigger_cutover="True", dbs_to_trigger_cutover_migration_on=migration_resource.dbs_to_migrate)

    if cancel is not None:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        migration_resource = migration_show_func(cmd, client, resource_group_name, server_name, migration_name)
        parameters = postgresql_flexibleservers.models.MigrationResourceForPatch(cancel="True", dbs_to_cancel_migration_on=migration_resource.dbs_to_migrate)

    if operationSpecified is False:
        raise RequiredArgumentMissingError("Incorrect Usage: At least one update operation needs to be specified.")

    return client.update(resource_group_name, server_name, migration_name, parameters)


def migration_check_name_availability(cmd, client, resource_group_name, server_name, migration_name):
    validate_resource_group(resource_group_name)
    validate_citus_cluster(cmd, resource_group_name, server_name)

    migration_name_availability_parammeters = {"name": "%s" % migration_name, "type": "Microsoft.DBforPostgreSQL/flexibleServers/migrations"}
    return client.check_name_availability(resource_group_name, server_name, migration_name_availability_parammeters)

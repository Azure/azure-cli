# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import uuid
from datetime import datetime
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import send_raw_request
from azure.cli.core.util import user_confirmation

logger = get_logger(__name__)
# pylint: disable=raise-missing-from


# Common functions used by other providers
def flexible_server_update_get(client, resource_group_name, server_name):
    return client.get(resource_group_name, server_name)


def flexible_server_stop(cmd, client, resource_group_name=None, server_name=None):
    logger.warning("Server will be automatically started after 7 days "
                   "if you do not perform a manual start operation")
    return client.begin_stop(resource_group_name, server_name)


def flexible_server_update_set(client, resource_group_name, server_name, parameters):
    return client.begin_update(resource_group_name, server_name, parameters)


def server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def firewall_rule_create_func(client, resource_group_name, server_name, firewall_rule_name=None, start_ip_address=None, end_ip_address=None):

    if end_ip_address is None and start_ip_address is not None:
        end_ip_address = start_ip_address
        logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip_address)

    if firewall_rule_name is None:
        now = datetime.now()
        firewall_rule_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                          now.second)
        if start_ip_address == '0.0.0.0' and end_ip_address == '0.0.0.0':
            logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                           'Azure resources...')
            firewall_rule_name = 'AllowAllAzureServicesAndResourcesWithinAzureIps_{}-{}-{}_{}-{}-{}'.format(now.year, now.month,
                                                                                                            now.day, now.hour,
                                                                                                            now.minute,
                                                                                                            now.second)
        else:
            if start_ip_address == '0.0.0.0' and end_ip_address == '255.255.255.255':
                firewall_rule_name = 'AllowAll_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day,
                                                                         now.hour, now.minute, now.second)
            logger.warning('Configuring server firewall rule to accept connections from \'%s\' to \'%s\'...', start_ip_address,
                           end_ip_address)

    parameters = {
        'name': firewall_rule_name,
        'start_ip_address': start_ip_address,
        'end_ip_address': end_ip_address
    }

    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters)


def migration_create_func(cmd, client, resource_group_name, server_name, body, migration_id=None):

    subscription_id=get_subscription_id(cmd.cli_ctx)

    if migration_id is None:
        # Convert a UUID to a string of hex digits in standard form
        migration_id = str(uuid.uuid4())

    r = send_raw_request(cmd.cli_ctx, "put", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_id), None, None, body)

    return r.json()


def migration_show_func(cmd, client, resource_group_name, server_name, migration_id, level="Default"):

    subscription_id=get_subscription_id(cmd.cli_ctx)

    r = send_raw_request(cmd.cli_ctx, "get", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?level={}&api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_id, level))

    return r.json()


def migration_list_func(cmd, client, resource_group_name, server_name, migration_filter="Active"):

    subscription_id=get_subscription_id(cmd.cli_ctx)

    r = send_raw_request(cmd.cli_ctx, "get", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations?migrationListFilter={}&api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_filter))

    return r.json()


def migration_update_func(cmd, client, resource_group_name, server_name, migration_id, setup_logical_replication=None, db1=None, db2=None, db3=None, db4=None, db5=None, db6=None, db7=None, db8=None, overwrite_dbs=None, cutover=None):

    subscription_id=get_subscription_id(cmd.cli_ctx)

    operationSpecified = False
    if setup_logical_replication is True:
        operationSpecified = True
        body = "{\"properties\": {\"setupLogicalReplicationOnSourceDBIfNeeded\": \"true\"} }"

    db_names = None
    db_names = db_names_concat_func(db_names, db1)
    db_names = db_names_concat_func(db_names, db2)
    db_names = db_names_concat_func(db_names, db3)
    db_names = db_names_concat_func(db_names, db4)
    db_names = db_names_concat_func(db_names, db5)
    db_names = db_names_concat_func(db_names, db6)
    db_names = db_names_concat_func(db_names, db7)
    db_names = db_names_concat_func(db_names, db8)

    if db_names is not None:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        prefix = "{ \"properties\": { \"dBsToMigrate\": ["
        suffix = "] } }"
        body = prefix + db_names + suffix

    if overwrite_dbs is True:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        body = "{\"properties\": {\"overwriteDBsInTarget\": \"true\"} }"

    # if start_time_utc is not None:
    #     if operationSpecified is True:
    #         raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
    #     operationSpecified = True
    #     body = "{\"properties\": {\"MigrationWindowStartTimeInUtc\": \"{}\"} }".format(start_time_utc)

    # if initiate_data_migration is True:
    #     if operationSpecified is True:
    #         raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
    #     operationSpecified = True
    #     body = "{\"properties\": {\"startDataMigration\": \"true\"} }"

    if cutover is True:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        body = "{\"properties\": {\"triggerCutover\": \"true\"} }"

    if operationSpecified is False:
        raise RequiredArgumentMissingError("Incorrect Usage: Atleast one update operation needs to be specified.")

    send_raw_request(cmd.cli_ctx, "patch", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_id), None, None, body)

    return migration_id


def migration_delete_func(cmd, client, resource_group_name, server_name, migration_id):

    subscription_id=get_subscription_id(cmd.cli_ctx)

    r = send_raw_request(cmd.cli_ctx, "delete", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_id))

    return r.json()


def db_names_concat_func(current_db_names, new_db_name):

    if new_db_name is not None:
        db = "\"{}\"".format(new_db_name)
        current_db_names = db if current_db_names is None else current_db_names + ", " + db

    return current_db_names


def firewall_rule_delete_func(client, resource_group_name, server_name, firewall_rule_name, yes=None):
    result = None
    if not yes:
        user_confirmation(
            "Are you sure you want to delete the firewall-rule '{0}' in server '{1}', resource group '{2}'".format(
                firewall_rule_name, server_name, resource_group_name))
    try:
        result = client.begin_delete(resource_group_name, server_name, firewall_rule_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result


def flexible_firewall_rule_custom_getter(client, resource_group_name, server_name, firewall_rule_name):
    return client.get(resource_group_name, server_name, firewall_rule_name)


def flexible_firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters)


def flexible_firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


def database_delete_func(client, resource_group_name=None, server_name=None, database_name=None, yes=None):
    result = None
    if resource_group_name is None or server_name is None or database_name is None:
        raise CLIError("Incorrect Usage : Deleting a database needs resource-group, server-name and database-name."
                       "If your parameter persistence is turned ON, make sure these three parameters exist in "
                       "persistent parameters using \'az config param-persist show\'. "
                       "If your parameter persistence is turned OFF, consider passing them explicitly.")
    if not yes:
        user_confirmation(
            "Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name,
                                                                                              resource_group_name), yes=yes)

    try:
        result = client.begin_delete(resource_group_name, server_name, database_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result

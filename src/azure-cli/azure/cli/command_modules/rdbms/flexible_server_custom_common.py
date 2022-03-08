# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import os
import json
import uuid
from datetime import datetime
from knack.log import get_logger
from knack.util import CLIError
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import send_raw_request
from azure.cli.core.util import user_confirmation
from azure.cli.core.azclierror import ClientRequestError, RequiredArgumentMissingError, FileOperationError, BadRequestError
from azure.mgmt.rdbms.mysql_flexibleservers.operations._servers_operations import ServersOperations as MySqlServersOperations
from ._flexible_server_util import run_subprocess, run_subprocess_get_output, fill_action_template, get_git_root_dir, \
    GITHUB_ACTION_PATH
from .validators import validate_public_access_server

logger = get_logger(__name__)
# pylint: disable=raise-missing-from


# Common functions used by other providers
def flexible_server_update_get(client, resource_group_name, server_name):
    return client.get(resource_group_name, server_name)


def flexible_server_stop(client, resource_group_name=None, server_name=None):
    logger.warning("Server will be automatically started after 7 days "
                   "if you do not perform a manual start operation")
    return client.begin_stop(resource_group_name, server_name)


def flexible_server_update_set(client, resource_group_name, server_name, parameters):
    return client.begin_update(resource_group_name, server_name, parameters)


def server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def migration_create_func(cmd, client, resource_group_name, server_name, properties, migration_name=None):

    subscription_id = get_subscription_id(cmd.cli_ctx)
    properties_filepath = os.path.join(os.path.abspath(os.getcwd()), properties)
    if not os.path.exists(properties_filepath):
        raise FileOperationError("Properties file does not exist in the given location")
    with open(properties_filepath, "r") as f:
        try:
            request_payload = json.load(f)
            request_payload.get("properties")['TriggerCutover'] = 'true'
            json_data = json.dumps(request_payload)
        except ValueError as err:
            logger.error(err)
            raise BadRequestError("Invalid json file. Make sure that the json file content is properly formatted.")
    if migration_name is None:
        # Convert a UUID to a string of hex digits in standard form
        migration_name = str(uuid.uuid4())
    r = send_raw_request(cmd.cli_ctx, "put", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_name), None, None, json_data)

    return r.json()


def migration_show_func(cmd, client, resource_group_name, server_name, migration_name, level="Default"):

    subscription_id = get_subscription_id(cmd.cli_ctx)

    r = send_raw_request(cmd.cli_ctx, "get", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?level={}&api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_name, level))

    return r.json()


def migration_list_func(cmd, client, resource_group_name, server_name, migration_filter="Active"):

    subscription_id = get_subscription_id(cmd.cli_ctx)

    r = send_raw_request(cmd.cli_ctx, "get", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations?migrationListFilter={}&api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_filter))

    return r.json()


def migration_update_func(cmd, client, resource_group_name, server_name, migration_name, setup_logical_replication=None, db_names=None, overwrite_dbs=None, start_data_migration=None):

    subscription_id = get_subscription_id(cmd.cli_ctx)

    operationSpecified = False
    if setup_logical_replication is True:
        operationSpecified = True
        properties = "{\"properties\": {\"setupLogicalReplicationOnSourceDBIfNeeded\": \"true\"} }"

    if db_names is not None:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        prefix = "{ \"properties\": { \"dBsToMigrate\": ["
        db_names_str = "\"" + "\", \"".join(db_names) + "\""
        suffix = "] } }"
        properties = prefix + db_names_str + suffix

    if overwrite_dbs is True:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        properties = "{\"properties\": {\"overwriteDBsInTarget\": \"true\"} }"

    if start_data_migration is True:
        if operationSpecified is True:
            raise MutuallyExclusiveArgumentError("Incorrect Usage: Can only specify one update operation.")
        operationSpecified = True
        properties = "{\"properties\": {\"startDataMigration\": \"true\"} }"

    if operationSpecified is False:
        raise RequiredArgumentMissingError("Incorrect Usage: Atleast one update operation needs to be specified.")

    r = send_raw_request(cmd.cli_ctx, "patch", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_name), None, None, properties)

    return r.json()


def migration_delete_func(cmd, client, resource_group_name, server_name, migration_name, yes=None):

    subscription_id = get_subscription_id(cmd.cli_ctx)

    if not yes:
        user_confirmation(
            "Are you sure you want to delete the migration '{0}' on target server '{1}', resource group '{2}'".format(
                migration_name, server_name, resource_group_name))

    r = send_raw_request(cmd.cli_ctx, "delete", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/migrations/{}?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name, migration_name))

    return r.json()


def migration_check_name_availability(cmd, client, resource_group_name, server_name, migration_name):

    subscription_id = get_subscription_id(cmd.cli_ctx)
    properties = json.dumps({"name": "%s" % migration_name, "type": "Microsoft.DBforPostgreSQL/flexibleServers/migrations"})
    r = send_raw_request(cmd.cli_ctx, "post", "https://management.azure.com/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/checkMigrationNameAvailability?api-version=2020-02-14-privatepreview".format(subscription_id, resource_group_name, server_name), None, None, properties)
    return r.json()


def firewall_rule_delete_func(cmd, client, resource_group_name, server_name, firewall_rule_name, yes=None):
    validate_public_access_server(cmd, client, resource_group_name, server_name)

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


def firewall_rule_create_func(cmd, client, resource_group_name, server_name, firewall_rule_name=None, start_ip_address=None, end_ip_address=None):

    validate_public_access_server(cmd, client, resource_group_name, server_name)

    if end_ip_address is None and start_ip_address is not None:
        end_ip_address = start_ip_address
    elif start_ip_address is None and end_ip_address is not None:
        start_ip_address = end_ip_address

    if firewall_rule_name is None:
        now = datetime.now()
        firewall_rule_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute,
                                                                          now.second)
        if start_ip_address == '0.0.0.0' and end_ip_address == '0.0.0.0':
            logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                           'Azure resources...')
            firewall_rule_name = 'AllowAllAzureServicesAndResourcesWithinAzureIps_{}-{}-{}_{}-{}-{}'.format(now.year, now.month,
                                                                                                            now.day, now.hour,
                                                                                                            now.minute, now.second)
        elif start_ip_address == end_ip_address:
            logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip_address)
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


def flexible_firewall_rule_custom_getter(cmd, client, resource_group_name, server_name, firewall_rule_name):
    validate_public_access_server(cmd, client, resource_group_name, server_name)
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


def firewall_rule_get_func(cmd, client, resource_group_name, server_name, firewall_rule_name):
    validate_public_access_server(cmd, client, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def firewall_rule_list_func(cmd, client, resource_group_name, server_name):
    validate_public_access_server(cmd, client, resource_group_name, server_name)
    return client.list_by_server(resource_group_name, server_name)


def database_delete_func(client, resource_group_name=None, server_name=None, database_name=None, yes=None):
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

    try:
        result = client.begin_delete(resource_group_name, server_name, database_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result


def create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip):
    # allow access to azure ip addresses
    cf_firewall = db_context.cf_firewall  # NOQA pylint: disable=unused-variable
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    firewall = firewall_rule_create_func(cmd=cmd,
                                         client=firewall_client,
                                         resource_group_name=resource_group_name,
                                         server_name=server_name,
                                         start_ip_address=start_ip, end_ip_address=end_ip)
    return firewall.result().name


def github_actions_setup(cmd, client, resource_group_name, server_name, database_name, administrator_login, administrator_login_password, sql_file_path, repository, action_name=None, branch=None, allow_push=None):

    server = client.get(resource_group_name, server_name)
    if server.network.public_network_access == 'Disabled':
        raise ClientRequestError("This command only works with public access enabled server.")
    if allow_push and not branch:
        raise RequiredArgumentMissingError("Provide remote branch name to allow pushing the action file to your remote branch.")
    if action_name is None:
        action_name = server.name + '_' + database_name + "_deploy"
    gitcli_check_and_login()

    if isinstance(client, MySqlServersOperations):
        database_engine = 'mysql'
    else:
        database_engine = 'postgresql'

    fill_action_template(cmd,
                         database_engine=database_engine,
                         server=server,
                         database_name=database_name,
                         administrator_login=administrator_login,
                         administrator_login_password=administrator_login_password,
                         file_name=sql_file_path,
                         repository=repository,
                         action_name=action_name)

    action_path = get_git_root_dir() + GITHUB_ACTION_PATH + action_name + '.yml'
    logger.warning("Making git commit for file %s", action_path)
    run_subprocess("git add {}".format(action_path))
    run_subprocess("git commit -m \"Add github action file\"")

    if allow_push:
        logger.warning("Pushing the created action file to origin %s branch", branch)
        run_subprocess("git push origin {}".format(branch))
    else:
        logger.warning('You did not set --allow-push parameter. Please push the prepared file %s to your remote repo and run "deploy run" command to activate the workflow.', action_path)


def github_actions_run(action_name, branch):

    gitcli_check_and_login()
    logger.warning("Created an event for %s.yml in branch %s", action_name, branch)
    run_subprocess("gh workflow run {}.yml --ref {}".format(action_name, branch))


def gitcli_check_and_login():
    output = run_subprocess_get_output("gh")
    if output.returncode:
        raise ClientRequestError('Please install "Github CLI" to run this command.')

    output = run_subprocess_get_output("gh auth status")
    if output.returncode:
        run_subprocess("gh auth login", stdout_show=True)

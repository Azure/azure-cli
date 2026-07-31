# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

import re
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from knack.log import get_logger
from knack.util import CLIError
from urllib.request import urlretrieve
from azure.cli.core.util import sdk_no_wait, user_confirmation, run_cmd
from azure.cli.core.azclierror import ClientRequestError
from ._flexible_server_util import run_subprocess
from .validators import validate_public_access_server, validate_resource_group, check_resource_group

logger = get_logger(__name__)
# pylint: disable=raise-missing-from


# Common functions used by other providers
def flexible_server_update_get(client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)

    return client.get(resource_group_name, server_name)


def flexible_server_stop(client, resource_group_name=None, server_name=None, no_wait=False):
    if not check_resource_group(resource_group_name):
        resource_group_name = None

    days = 7
    logger.warning("Server will be automatically started after %d days "
                   "if you do not perform a manual start operation", days)
    return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, server_name)


def flexible_server_update_set(client, resource_group_name, server_name, parameters):
    validate_resource_group(resource_group_name)

    return client.begin_update(resource_group_name, server_name, parameters)


def server_list_custom_func(client, resource_group_name=None, show_cluster=None):
    if not check_resource_group(resource_group_name):
        resource_group_name = None

    servers = client.list_by_subscription()

    if resource_group_name:
        servers = client.list_by_resource_group(resource_group_name)

    if show_cluster:
        servers = [s for s in servers if s.cluster is not None]
    else:
        servers = [s for s in servers if s.cluster is None]

    return servers


def firewall_rule_delete_func(cmd, client, resource_group_name, server_name, firewall_rule_name, yes=None):
    validate_resource_group(resource_group_name)
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
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, client, resource_group_name, server_name)

    if end_ip_address is None and start_ip_address is not None:
        end_ip_address = start_ip_address
    elif start_ip_address is None and end_ip_address is not None:
        start_ip_address = end_ip_address
    elif start_ip_address is None and end_ip_address is None:
        raise CLIError("Incorrect Usage : Need to pass in value for either \'--start-ip-address\' or \'--end-ip-address\'.")

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
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, client, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def flexible_firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    validate_resource_group(resource_group_name)

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
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, client, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def firewall_rule_list_func(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, client, resource_group_name, server_name)
    return client.list_by_server(resource_group_name, server_name)


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

    try:
        result = client.begin_delete(resource_group_name, server_name, database_name)
    except Exception as ex:  # pylint: disable=broad-except
        logger.error(ex)
    return result


def create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip):
    validate_resource_group(resource_group_name)

    # allow access to azure ip addresses
    cf_firewall = db_context.cf_firewall  # NOQA pylint: disable=unused-variable
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    firewall = firewall_rule_create_func(cmd=cmd,
                                         client=firewall_client,
                                         resource_group_name=resource_group_name,
                                         server_name=server_name,
                                         start_ip_address=start_ip, end_ip_address=end_ip)
    return firewall.result().name


def github_actions_run(action_name, branch):

    gitcli_check_and_login()
    logger.warning("Created an event for %s.yml in branch %s", action_name, branch)
    run_subprocess("gh workflow run {}.yml --ref {}".format(action_name, branch))


def gitcli_check_and_login():
    output = run_cmd(["gh"], capture_output=True)
    if output.returncode:
        raise ClientRequestError('Please install "Github CLI" to run this command.')

    output = run_cmd(["gh", "auth", "status"], capture_output=True)
    if output.returncode:
        run_subprocess("gh auth login", stdout_show=True)


# Custom functions for server logs
def flexible_server_log_download(client, resource_group_name, server_name, file_name):
    validate_resource_group(resource_group_name)

    files = client.list_by_server(resource_group_name, server_name)

    for f in files:
        if f.name in file_name:
            urlretrieve(f.url, f.name)


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

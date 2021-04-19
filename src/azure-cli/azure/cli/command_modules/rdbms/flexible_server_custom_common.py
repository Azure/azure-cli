# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


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
        from datetime import datetime
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


def firewall_rule_delete_func(client, resource_group_name, server_name, firewall_rule_name, yes=None):
    confirm = yes
    result = None
    if not yes:
        confirm = user_confirmation(
            "Are you sure you want to delete the firewall-rule '{0}' in server '{1}', resource group '{2}'".format(
                firewall_rule_name, server_name, resource_group_name))
    if confirm:
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
    confirm = yes
    result = None
    if resource_group_name is None or server_name is None or database_name is None:
        raise CLIError("Incorrect Usage : Deleting a database needs resource-group, server-name and database-name."
                       "If your local context is turned ON, make sure these three parameters exist in local context "
                       "using \'az local-context show\' If your local context is turned ON, but they are missing or "
                       "If your local context is turned OFF, consider passing them explicitly.")
    if not yes:
        confirm = user_confirmation(
            "Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name,
                                                                                              resource_group_name),
            yes=yes)
    if confirm:
        try:
            result = client.begin_delete(resource_group_name, server_name, database_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
    return result


def user_confirmation(message, yes=False):
    if yes:
        return True
    from knack.prompting import prompt_y_n, NoTTYException
    try:
        if not prompt_y_n(message):
            raise CLIError('Operation cancelled.')
        return True
    except NoTTYException:
        raise CLIError(
            'Unable to prompt for confirmation as no tty available. Use --yes.')

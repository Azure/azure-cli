# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


## Common functions used by other providers
def _flexible_server_update_get(client, resource_group_name, server_name):
    return client.get(resource_group_name, server_name)

def _flexible_server_update_set(client, resource_group_name, server_name, parameters):
    return client.update(resource_group_name, server_name, parameters)

def server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()

def firewall_rule_delete_func(client, resource_group_name=None, server_name=None, firewall_rule_name=None, prompt=None):
    confirm = True
    if not prompt or prompt ==' yes':
        confirm = user_confirmation("Are you sure you want to delete the firewall-rule '{0}' in server '{1}', resource group '{2}'".format(firewall_rule_name, server_name, resource_group_name))
    if confirm:
        try:
            result = client.delete(resource_group_name, server_name, firewall_rule_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
        return result


def database_delete_func(client, resource_group_name=None, server_name=None, database_name=None, force=None):
    if resource_group_name is None or server_name is None or database_name is None:
        raise CLIError("Incorrect Usage : Deleting a database needs resource-group, server-name and database-name."
                       "If your local context is turned ON, make sure these three parameters exist in local context "
                       "using \'az local-context show\' If your local context is turned ON, but they are missing or "
                       "If your local context is turned OFF, consider passing them explicitly.")
    if not force:
        confirm = user_confirmation("Are you sure you want to delete the server '{0}' in resource group '{1}'".format(server_name, resource_group_name), yes=force)
    if (confirm):
        try:
            result = client.delete(resource_group_name, server_name, database_name)
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(ex)
        return result

def _flexible_firewall_rule_custom_getter(client, resource_group_name, server_name, firewall_rule_name):
    return client.get(resource_group_name, server_name, firewall_rule_name)


def _flexible_firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    return client.create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters.start_ip_address,
        parameters.end_ip_address)

def flexible_firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


def user_confirmation(message, yes=False):
    if yes:
        return True
    from knack.prompting import prompt_y_n, NoTTYException
    try:
        if not prompt_y_n(message):
            raise CLIError('Operation cancelled.')
        else:
            return True
    except NoTTYException:
        raise CLIError(
            'Unable to prompt for confirmation as no tty available. Use --force.')
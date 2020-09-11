# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid
import random
from knack.log import get_logger
from azure.cli.core.commands import LongRunningOperation, _is_poller
from azure.cli.core.profiles import ResourceType
from azure.mgmt.resource.resources.models import ResourceGroup
from ._client_factory import resource_client_factory, network_client_factory
from msrestazure.tools import is_valid_resource_id, parse_resource_id# pylint: disable=import-error
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError

logger = get_logger(__name__)

DEFAULT_LOCATION = 'eastus2euap' #'eastus2euap'


def resolve_poller(result, cli_ctx, name):
    if _is_poller(result):
        return LongRunningOperation(cli_ctx, 'Starting {}'.format(name))(result)
    return result


def create_random_resource_name(prefix='azure', length=15):
    append_length = length - len(prefix)
    digits = [str(random.randrange(10)) for i in range(append_length)]
    return prefix + ''.join(digits)


def generate_missing_parameters(cmd, location, resource_group_name, server_name):
    # if location is not passed as a parameter or is missing from local context
    if location is None:
        location = DEFAULT_LOCATION

    # If resource group is there in local context, check for its existence.
    resource_group_exists = True
    if resource_group_name is not None:
        logger.warning('Checking the existence of the resource group \'%s\'...', resource_group_name)
        resource_group_exists = _check_resource_group_existence(cmd, resource_group_name)
        logger.warning('Resource group \'%s\' exists ? : %s ', resource_group_name, resource_group_exists)

    # If resource group is not passed as a param or is not in local context or the rg in the local context has been deleted
    if not resource_group_exists or resource_group_name is None:
        resource_group_name = _create_resource_group(cmd, location, resource_group_name)

    # If servername is not passed, always create a new server - even if it is stored in the local context
    if server_name is None:
        server_name = create_random_resource_name('server')

    # This is for the case when user does not pass a location but the resource group exists in the local context.
    #  In that case, the location needs to be set to the location of the rg, not the default one.

    ## TODO: Fix this because it changes the default location even when I pass in a location param
    # location = _update_location(cmd, resource_group_name)

    return location, resource_group_name, server_name


def generate_password(administrator_login_password):
    import string,secrets
    if administrator_login_password is None:
        passwordLength = 16
        special_character = random.choice('!@#,?;:$&*')
        administrator_login_password = secrets.token_urlsafe(passwordLength)
        random_position = random.randint(1, len(administrator_login_password)-1)
        administrator_login_password = administrator_login_password[:random_position] + special_character + administrator_login_password[random_position + 1:]
    return administrator_login_password


def create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip):
    from datetime import datetime
    # allow access to azure ip addresses
    cf_firewall, logging_name = db_context.cf_firewall, db_context.logging_name
    now = datetime.now()
    firewall_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    if start_ip == '0.0.0.0' and end_ip == '0.0.0.0':
        logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                   'Azure resources...')
        firewall_name = 'AllowAllAzureServicesAndResourcesWithinAzureIps_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    elif start_ip == end_ip:
        logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip)
    else:
        if start_ip == '0.0.0.0' and end_ip == '255.255.255.255':
            firewall_name = 'AllowAll_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
        logger.warning('Configuring server firewall rule to accept connections from \'%s\' to \'%s\'...', start_ip, end_ip)
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    '''
    return resolve_poller(
        firewall_client.create_or_update(resource_group_name, server_name, firewall_name , start_ip, end_ip),
        cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))
    '''
    firewall = firewall_client.create_or_update(resource_group_name, server_name, firewall_name, start_ip, end_ip).result()
    return firewall.name


def parse_public_access_input(public_access):
    allow_azure_services = False
    if public_access is not None:
        parsed_input = public_access.split('-')
        if len(parsed_input) == 1:
            return parsed_input[0], parsed_input[0]
        else:
            return parsed_input[0], parsed_input[1]


def server_list_custom_func(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def flexible_firewall_rule_update_custom_func(instance, start_ip_address=None, end_ip_address=None):
    if start_ip_address is not None:
        instance.start_ip_address = start_ip_address
    if end_ip_address is not None:
        instance.end_ip_address = end_ip_address
    return instance


def update_kwargs(kwargs, key, value):
    if value is not None:
        kwargs[key] = value


def parse_maintenance_window(maintenance_window_string):
    parsed_input = maintenance_window_string.split(':')
    if len(parsed_input) == 1:
        return parsed_input[0], None, None
    elif len(parsed_input) == 2:
        return parsed_input[0], parsed_input[1], None
    elif len(parsed_input) == 3:
        return parsed_input[0], parsed_input[1], parsed_input[2]
    return None, None, None


def _update_location(cmd, resource_group_name):
    resource_client = resource_client_factory(cmd.cli_ctx)
    rg = resource_client.resource_groups.get(resource_group_name)
    location = rg.location
    return location


def _create_resource_group(cmd, location, resource_group_name):
    if resource_group_name is None:
        resource_group_name = create_random_resource_name('group')
    params = ResourceGroup(location=location)
    resource_client = resource_client_factory(cmd.cli_ctx)
    logger.warning('Creating Resource Group \'%s\'...', resource_group_name)
    resource_client.resource_groups.create_or_update(resource_group_name, params)
    return resource_group_name


def _check_resource_group_existence(cmd, resource_group_name):
    resource_client = resource_client_factory(cmd.cli_ctx)
    return  resource_client.resource_groups.check_existence(resource_group_name)




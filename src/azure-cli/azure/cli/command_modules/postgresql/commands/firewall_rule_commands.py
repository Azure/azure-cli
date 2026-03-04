# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long
from azure.cli.core.util import user_confirmation
from datetime import datetime
from knack.log import get_logger
from knack.util import CLIError
from ..utils.validators import validate_public_access_server, validate_resource_group

logger = get_logger(__name__)
# pylint: disable=raise-missing-from


def firewall_rule_delete_func(cmd, client, resource_group_name, server_name, firewall_rule_name, yes=None):
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, resource_group_name, server_name)

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
    validate_public_access_server(cmd, resource_group_name, server_name)

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
        'properties': {
            'startIpAddress': start_ip_address,
            'endIpAddress': end_ip_address
        }
    }

    return client.begin_create_or_update(
        resource_group_name,
        server_name,
        firewall_rule_name,
        parameters)


def flexible_firewall_rule_custom_getter(cmd, client, resource_group_name, server_name, firewall_rule_name):
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def flexible_firewall_rule_custom_setter(client, resource_group_name, server_name, firewall_rule_name, parameters):
    validate_resource_group(resource_group_name)

    endIpAddress = parameters.get('properties', {}).get('endIpAddress')
    startIpAddress = parameters.get('properties', {}).get('startIpAddress')
    parameters = {"properties": {"endIpAddress": endIpAddress, "startIpAddress": startIpAddress}}

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
    validate_public_access_server(cmd, resource_group_name, server_name)
    return client.get(resource_group_name, server_name, firewall_rule_name)


def firewall_rule_list_func(cmd, client, resource_group_name, server_name):
    validate_resource_group(resource_group_name)
    validate_public_access_server(cmd, resource_group_name, server_name)
    return client.list_by_server(resource_group_name, server_name)


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

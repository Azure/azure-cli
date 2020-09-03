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

logger = get_logger(__name__)

DEFAULT_LOCATION = 'southeastasia' #'eastus2euap'


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
    if administrator_login_password is None:
        administrator_login_password = str(uuid.uuid4())
    return administrator_login_password


def create_vnet(cmd, servername, location, resource_group_name, delegation_service_name):
    Subnet, VirtualNetwork, AddressSpace, Delegation = cmd.get_models('Subnet', 'VirtualNetwork', 'AddressSpace', 'Delegation', resource_type=ResourceType.MGMT_NETWORK)
    client = network_client_factory(cmd.cli_ctx)
    vnet_name, subnet_name, vnet_address_prefix, subnet_prefix = _create_vnet_metadata(servername)

    logger.warning('Creating new vnet "%s" in resource group "%s"', vnet_name, resource_group_name)
    client.virtual_networks.create_or_update(resource_group_name, vnet_name, VirtualNetwork(name=vnet_name, location=location, address_space=AddressSpace(
                                                                 address_prefixes=[vnet_address_prefix])))
    delegation = Delegation(name=delegation_service_name, service_name=delegation_service_name)
    subnet = Subnet(name=subnet_name, location=location, address_prefix=subnet_prefix, delegations=[delegation])

    logger.warning('Creating new subnet "%s" in resource group "%s"', subnet_name, resource_group_name)
    subnet = client.subnets.create_or_update(resource_group_name, vnet_name, subnet_name, subnet).result()
    return subnet.id


def create_firewall_rule(db_context, cmd, resource_group_name, server_name, start_ip, end_ip):
    from datetime import datetime
    # allow access to azure ip addresses
    cf_firewall, logging_name = db_context.cf_firewall, db_context.logging_name
    now = datetime.now()
    firewall_name = 'FirewallIPAddress_{}-{}-{}_{}-{}-{}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    if start_ip == '0.0.0.0' and end_ip == '0.0.0.0':
        logger.warning('Configuring server firewall rule, \'azure-access\', to accept connections from all '
                   'Azure resources...')
    elif start_ip == end_ip:
        logger.warning('Configuring server firewall rule to accept connections from \'%s\'...', start_ip)
    else:
        logger.warning('Configuring server firewall rule to accept connections from \'%s\' to \'%s\'...', start_ip, end_ip)
    firewall_client = cf_firewall(cmd.cli_ctx, None)
    '''
    return resolve_poller(
        firewall_client.create_or_update(resource_group_name, server_name, firewall_name , start_ip, end_ip),
        cmd.cli_ctx, '{} Firewall Rule Create/Update'.format(logging_name))
    '''
    firewall = firewall_client.create_or_update(resource_group_name, server_name, firewall_name, start_ip, end_ip).result()
    return firewall.id


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


def _create_vnet_metadata(servername):
    vnet_name = servername + 'VNET'
    subnet_name = servername + 'Subnet'
    vnet_address_prefix = '10.0.0.0/16'
    subnet_prefix = '10.0.0.0/24'
    return vnet_name, subnet_name, vnet_address_prefix, subnet_prefix

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
DEFAULT_VNET_ADDRESS_PREFIX = '10.0.0.0/16'
DEFAULT_SUBNET_PREFIX = '10.0.0.0/24'


def prepareVnet(cmd,vnet,subnet, resource_group_name, loc, delegation_service_name):
    Delegation = cmd.get_models('Delegation', resource_type=ResourceType.MGMT_NETWORK)
    delegation = Delegation(name=delegation_service_name, service_name=delegation_service_name)
    nw_client = network_client_factory(cmd.cli_ctx)
    if subnet is not None and vnet is None:
        if is_valid_resource_id(subnet):
            logger.warning("You have supplied a Subnet Id. Verifying its existence...")
            parsed_subnet_id = parse_resource_id(subnet)
            subnet_name = parsed_subnet_id['resource_name']
            vnet_name = parsed_subnet_id['name']
            resource_group = parsed_subnet_id['resource_group']
            subscription = parsed_subnet_id['subscription']
            resource_client = resource_client_factory(cmd.cli_ctx)
            rg = resource_client.resource_groups.get(resource_group)
            location = rg.location
            validate_rg_loc_sub(resource_group, subscription, location, resource_group_name, get_subscription_id(cmd.cli_ctx), loc)
            subnet_result = check_resource_existence(cmd, subnet_name, vnet_name, resource_group_name)
            if subnet_result:
                logger.info('Using existing subnet "%s" in resource group "%s"', subnet_result.name, resource_group)

                if not subnet_result.delegations:
                    logger.info('Adding "%s" delegation to the existing subnet.', )
                    subnet_result.delegations = [delegation]
                    subnet_result = nw_client.subnets.create_or_update(resource_group, vnet_name, subnet_name, subnet_result).result()
                else:
                    for delgtn in subnet_result.delegations:
                        if delgtn.service_name != delegation_service_name:
                            raise CLIError("Can not use subnet with existing delegations other than {}".format(
                                delegation_service_name))
            else:
                Subnet, VirtualNetwork, AddressSpace = cmd.get_models('Subnet', 'VirtualNetwork',
                                                                      'AddressSpace',
                                                                      resource_type=ResourceType.MGMT_NETWORK)
                logger.warning("The Subnet does not exist with the supplied subnet id. Checking the existence of the Vnet in the supplied Id...")
                vnet_exist = _get_resource(nw_client.virtual_networks, resource_group, vnet_name)
                if not vnet_exist:
                    logger.info('The vNet is the supplied subnet Id also does not exist. Creating new vnet "%s" in resource group "%s"', vnet_name, resource_group)
                    nw_client.virtual_networks.create_or_update(resource_group,
                                                          vnet_name,
                                                          VirtualNetwork(name=vnet_name,
                                                                         location=location,
                                                                         address_space=AddressSpace(
                                                                             address_prefixes=[DEFAULT_VNET_ADDRESS_PREFIX])))
                subnet_result = Subnet(
                    name=subnet_name,
                    location=location,
                    address_prefix=DEFAULT_SUBNET_PREFIX,
                    delegations=[delegation])

                logger.info('Creating new subnet "%s" in resource group "%s"', subnet_name, resource_group)
                subnet_result = nw_client.subnets.create_or_update(resource_group_name, vnet_name, subnet_name, subnet_result).result()
        else:
            raise CLIError("Incorrectly formed Subnet id.")
    else:
        return None
    return subnet_result.id


def validate_rg_loc_sub(s_resource_group, s_subscription, s_location, resource_group, subscription, location):
    if not ((s_resource_group == resource_group) and (s_location == location) and (s_subscription == subscription)):
        raise CLIError("Incorrect Usage : The resource group, location and subscription of the server,Vnet and Subnet should be same.")


def check_resource_existence(cmd, subnet_name, vnet_name, resource_group_name,):
    nw_client = network_client_factory(cmd.cli_ctx)
    subnet = _get_resource(nw_client.subnets, resource_group_name, vnet_name, subnet_name)
    return subnet


def _get_resource(client, resource_group_name, *subresources):
    from msrestazure.azure_exceptions import CloudError
    try:
        resource = client.get(resource_group_name, *subresources)
        return resource
    except CloudError as ex:
        if ex.error.error == "NotFound" or ex.error.error == "ResourceNotFound":
            return None
        raise


def create_vnet(cmd, servername, location, resource_group_name, delegation_service_name):
    Subnet, VirtualNetwork, AddressSpace, Delegation = cmd.get_models('Subnet', 'VirtualNetwork', 'AddressSpace', 'Delegation', resource_type=ResourceType.MGMT_NETWORK)
    client = network_client_factory(cmd.cli_ctx)
    vnet_name, subnet_name, vnet_address_prefix, subnet_prefix = _create_vnet_metadata(servername)

    logger.warning('Creating new vnet "%s" in resource group "%s"...', vnet_name, resource_group_name)
    client.virtual_networks.create_or_update(resource_group_name, vnet_name, VirtualNetwork(name=vnet_name, location=location, address_space=AddressSpace(
                                                                 address_prefixes=[vnet_address_prefix])))
    delegation = Delegation(name=delegation_service_name, service_name=delegation_service_name)
    subnet = Subnet(name=subnet_name, location=location, address_prefix=subnet_prefix, delegations=[delegation])

    logger.warning('Creating new subnet "%s" in resource group "%s" and delegating it to "%s"...', subnet_name, resource_group_name, delegation_service_name)
    subnet = client.subnets.create_or_update(resource_group_name, vnet_name, subnet_name, subnet).result()
    return subnet.id


def _create_vnet_metadata(servername):
    vnet_name = servername + 'VNET'
    subnet_name = servername + 'Subnet'
    vnet_address_prefix = DEFAULT_VNET_ADDRESS_PREFIX
    subnet_prefix = DEFAULT_SUBNET_PREFIX
    return vnet_name, subnet_name, vnet_address_prefix, subnet_prefix
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from msrestazure.tools import is_valid_resource_id, parse_resource_id, is_valid_resource_name  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError
from azure.cli.core.azclierror import ValidationError
from ._client_factory import resource_client_factory, network_client_factory
from ._flexible_server_util import get_id_components, check_existence

logger = get_logger(__name__)
DEFAULT_VNET_ADDRESS_PREFIX = '10.0.0.0/16'
DEFAULT_SUBNET_ADDRESS_PREFIX = '10.0.0.0/24'


# pylint: disable=too-many-locals, too-many-statements, too-many-branches
def prepare_private_network(cmd, resource_group_name, server_name, vnet, subnet, location, delegation_service_name, vnet_address_pref, subnet_address_pref):

    nw_client = network_client_factory(cmd.cli_ctx)
    resource_client = resource_client_factory(cmd.cli_ctx)

    # Handle vnet and subnet prefix
    if (vnet_address_pref is not None and subnet_address_pref is None) or \
       (vnet_address_pref is None and subnet_address_pref is not None):
        raise ValidationError("You need to provide both Vnet address prefix and Subnet address prefix.")
    if vnet_address_pref is None:
        vnet_address_pref = DEFAULT_VNET_ADDRESS_PREFIX
    if subnet_address_pref is None:
        subnet_address_pref = DEFAULT_SUBNET_ADDRESS_PREFIX

    # pylint: disable=too-many-nested-blocks
    if subnet is not None and vnet is None:
        if not is_valid_resource_id(subnet):
            raise ValidationError("Incorrectly formed Subnet ID. If you are providing only --subnet (not --vnet), the Subnet parameter should be in resource ID format.")
        if 'child_name_1' not in parse_resource_id(subnet):
            raise ValidationError("Incorrectly formed Subnet ID. Check if the Subnet ID is in the right format.")
        logger.warning("You have supplied a Subnet ID. Verifying its existence...")
        subnet_result = address_private_network_with_id_input(cmd, subnet, nw_client, resource_client, server_name, location, delegation_service_name, vnet_address_pref, subnet_address_pref)

    elif subnet is None and vnet is not None:
        if is_valid_resource_id(vnet):
            logger.warning("You have supplied a Vnet ID. Verifying its existence...")
            subnet_result = address_private_network_with_id_input(cmd, vnet, nw_client, resource_client, server_name, location, delegation_service_name, vnet_address_pref, subnet_address_pref)

        elif _check_if_resource_name(vnet) and is_valid_resource_name(vnet):
            logger.warning("You have supplied a Vnet name. Verifying its existence...")
            subnet_result = _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group_name, vnet, 'Subnet' + server_name[6:],
                                                           location, server_name, vnet_address_pref, subnet_address_pref)
        else:
            raise ValidationError("Incorrectly formed Vnet ID or Vnet name")

    elif subnet is not None and vnet is not None:
        if _check_if_resource_name(vnet) and _check_if_resource_name(subnet):
            logger.warning("You have supplied a Vnet and Subnet name. Verifying its existence...")

            subnet_result = _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group_name, vnet, subnet,
                                                           location, server_name, vnet_address_pref, subnet_address_pref)

        else:
            raise ValidationError("If you pass both --vnet and --subnet, consider passing names instead of IDs.")

    elif subnet is None and vnet is None:
        subnet_result = _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group_name, 'Vnet' + server_name[6:], 'Subnet' + server_name[6:],
                                                       location, server_name, vnet_address_pref, subnet_address_pref)
    else:
        return None

    return subnet_result.id


def address_private_network_with_id_input(cmd, rid, nw_client, resource_client, server_name, location, delegation_service_name, vnet_address_pref, subnet_address_pref):
    id_subscription, id_resource_group, id_vnet, id_subnet = get_id_components(rid)
    nw_client, resource_client = _change_client_with_different_subscription(cmd, id_subscription, nw_client, resource_client)
    _resource_group_verify_and_create(resource_client, id_resource_group, location)
    if id_subnet is None:
        id_subnet = 'Subnet' + server_name[6:]

    return _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, id_resource_group, id_vnet, id_subnet,
                                          location, server_name, vnet_address_pref, subnet_address_pref)


def _change_client_with_different_subscription(cmd, subscription, nw_client, resource_client):
    if subscription != get_subscription_id(cmd.cli_ctx):
        logger.warning('The Vnet/Subnet ID provided is in different subscription from the server')
        nw_client = network_client_factory(cmd.cli_ctx, subscription_id=subscription)
        resource_client = resource_client_factory(cmd.cli_ctx, subscription_id=subscription)

    return nw_client, resource_client


def _resource_group_verify_and_create(resource_client, resource_group, location):
    if not resource_client.resource_groups.check_existence(resource_group):
        logger.warning("Provided resource group in the Vnet/Subnet ID doesn't exist. Creating the resource group %s", resource_group)
        resource_client.resource_groups.create_or_update(resource_group, {'location': location})


def _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group, vnet_name, subnet_name, location, server_name, vnet_address_pref, subnet_address_pref):
    VirtualNetwork, AddressSpace = cmd.get_models('VirtualNetwork', 'AddressSpace', resource_type=ResourceType.MGMT_NETWORK)
    if not check_existence(resource_client, vnet_name, resource_group, 'Microsoft.Network', 'virtualNetworks'):
        logger.warning('Creating new Vnet "%s" in resource group "%s"', vnet_name, resource_group)
        nw_client.virtual_networks.begin_create_or_update(resource_group,
                                                          vnet_name,
                                                          VirtualNetwork(name=vnet_name,
                                                                         location=location,
                                                                         address_space=AddressSpace(
                                                                             address_prefixes=[
                                                                                 vnet_address_pref]))).result()
    else:
        logger.warning('Using existing Vnet "%s" in resource group "%s"', vnet_name, resource_group)
        # check if vnet prefix is in address space and add if not there
        vnet = nw_client.virtual_networks.get(resource_group, vnet_name)
        prefixes = vnet.address_space.address_prefixes
        if vnet_address_pref not in prefixes:
            logger.warning('Adding address prefix %s to Vnet %s', vnet_address_pref, vnet_name)
            nw_client.virtual_networks.begin_create_or_update(resource_group, vnet_name,
                                                              VirtualNetwork(location=location,
                                                                             address_space=AddressSpace(
                                                                                 address_prefixes=prefixes + [vnet_address_pref]))).result()

    return _create_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group, vnet_name, subnet_name, location, server_name, subnet_address_pref)


def _create_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group, vnet_name, subnet_name, location, server_name, subnet_address_pref):
    Delegation, Subnet, ServiceEndpoint = cmd.get_models('Delegation', 'Subnet', 'ServiceEndpointPropertiesFormat', resource_type=ResourceType.MGMT_NETWORK)
    delegation = Delegation(name=delegation_service_name, service_name=delegation_service_name)
    service_endpoint = ServiceEndpoint(service='Microsoft.Storage')

    # subnet exist
    if not check_existence(resource_client, subnet_name, resource_group, 'Microsoft.Network', 'subnets', parent_name=vnet_name, parent_type='virtualNetworks'):
        subnet_result = Subnet(
            name=subnet_name,
            location=location,
            address_prefix=subnet_address_pref,
            delegations=[delegation],
            service_endpoints=[service_endpoint])

        vnet = nw_client.virtual_networks.get(resource_group, vnet_name)
        vnet_subnet_prefixes = [subnet.address_prefix for subnet in vnet.subnets]
        if subnet_address_pref in vnet_subnet_prefixes:
            raise ValidationError("The Subnet (default) prefix {} is already taken by another Subnet in the Vnet. Please provide a different prefix for --subnet-prefix parameter".format(subnet_address_pref))

        logger.warning('Creating new Subnet "%s" in resource group "%s"', subnet_name, resource_group)
        subnet = nw_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name,
                                                          subnet_result).result()
    else:
        subnet = nw_client.subnets.get(resource_group, vnet_name, subnet_name)
        logger.warning('Using existing Subnet "%s" in resource group "%s"', subnet_name, resource_group)
        if subnet_address_pref not in (DEFAULT_SUBNET_ADDRESS_PREFIX, subnet.address_prefix):
            logger.warning("The prefix of the subnet you provided does not match the --subnet-prefix value %s. Using current prefix %s", subnet_address_pref, subnet.address_prefix)

        # Add Delegation if not delegated already
        if not subnet.delegations:
            logger.warning('Adding "%s" delegation to the existing subnet %s.', delegation_service_name, subnet_name)
        else:
            for delgtn in subnet.delegations:
                if delgtn.service_name != delegation_service_name:
                    raise CLIError("Can not use subnet with existing delegations other than {}".format(
                        delegation_service_name))

        subnet.service_endpoints = [service_endpoint]
        subnet.delegations = [delegation]
        subnet = nw_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name, subnet).result()

    return subnet


def _check_if_resource_name(resource):
    if len(resource.split('/')) == 1:
        return True
    return False

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long

from msrestazure.tools import is_valid_resource_id, parse_resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError
from ._client_factory import resource_client_factory, network_client_factory

logger = get_logger(__name__)
DEFAULT_VNET_ADDRESS_PREFIX = '10.0.0.0/16'
DEFAULT_SUBNET_PREFIX = '10.0.0.0/24'


# pylint: disable=too-many-locals, too-many-statements
def prepare_vnet(cmd, server_name, vnet, subnet, resource_group_name, loc, delegation_service_name, vnet_address_pref, subnet_address_pref):
    Delegation, Subnet, VirtualNetwork, AddressSpace = cmd.get_models('Delegation', 'Subnet', 'VirtualNetwork',
                                                                      'AddressSpace',
                                                                      resource_type=ResourceType.MGMT_NETWORK)
    delegation = Delegation(name=delegation_service_name, service_name=delegation_service_name)
    nw_client = network_client_factory(cmd.cli_ctx)

    # pylint: disable=too-many-nested-blocks
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
            validate_rg_loc_sub(subscription, location, get_subscription_id(cmd.cli_ctx), loc)
            subnet_result = check_resource_existence(cmd, subnet_name, vnet_name, resource_group)
            if subnet_result:
                logger.info('Using existing subnet "%s" in resource group "%s"', subnet_result.name, resource_group)

                if not subnet_result.delegations:
                    logger.info('Adding "%s" delegation to the existing subnet.', )
                    subnet_result.delegations = [delegation]
                    subnet_result = nw_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name,
                                                                             subnet_result).result()
                else:
                    for delgtn in subnet_result.delegations:
                        if delgtn.service_name != delegation_service_name:
                            raise CLIError("Can not use subnet with existing delegations other than {}".format(
                                delegation_service_name))
            else:
                logger.warning("The supplied subnet id does not exist.")
                subnet_result = _create_vnet_subnet_delegation(nw_client, resource_group_name, vnet_name,
                                                               'Subnet' + server_name[6:], location, server_name,
                                                               delegation,
                                                               VirtualNetwork, Subnet, AddressSpace,
                                                               DEFAULT_VNET_ADDRESS_PREFIX, DEFAULT_SUBNET_PREFIX)
        else:
            raise CLIError("Incorrectly formed Subnet id.")
    elif subnet is None and vnet is not None:
        if is_valid_resource_id(vnet):
            logger.warning("You have supplied a Vnet Id. Verifying its existence...")
            parsed_vnet_id = parse_resource_id(vnet)
            vnet_name = parsed_vnet_id['resource_name']
            resource_group = parsed_vnet_id['resource_group']
            subscription = parsed_vnet_id['subscription']
            resource_client = resource_client_factory(cmd.cli_ctx)
            rg = resource_client.resource_groups.get(resource_group)
            location = rg.location
            validate_rg_loc_sub(subscription, location, get_subscription_id(cmd.cli_ctx), loc)
            subnet_result = _create_vnet_subnet_delegation(nw_client, resource_group, vnet_name, 'Subnet' + server_name[6:],
                                                           location, server_name, delegation, VirtualNetwork, Subnet,
                                                           AddressSpace, DEFAULT_VNET_ADDRESS_PREFIX,
                                                           DEFAULT_SUBNET_PREFIX)
        elif len(vnet.split('\\')) == 1:
            logger.warning("You have supplied a Vnet Name. Verifying its existence...")
            subnet_result = _create_vnet_subnet_delegation(nw_client, resource_group_name, vnet, 'Subnet' + server_name[6:],
                                                           loc, server_name, delegation, VirtualNetwork, Subnet,
                                                           AddressSpace, DEFAULT_VNET_ADDRESS_PREFIX,
                                                           DEFAULT_SUBNET_PREFIX)

            # If the supplied Vnet name was an existing one, ensure that it was on the right sub, vnet and location.
            parsed_subnet_id = parse_resource_id(subnet_result.id)
            resource_group = parsed_subnet_id['resource_group']
            subscription = parsed_subnet_id['subscription']
            resource_client = resource_client_factory(cmd.cli_ctx)
            rg = resource_client.resource_groups.get(resource_group)
            location = rg.location
            validate_rg_loc_sub(subscription, location, get_subscription_id(cmd.cli_ctx), loc)
        else:
            raise CLIError("Incorrectly formed Vnet id or Vnet name")
    elif subnet is not None and vnet is not None and vnet_address_pref is not None and subnet_address_pref is not None:
        if (len(vnet.split('\\')) == 1) and (len(subnet.split('\\')) == 1):
            subnet_result = _create_with_resource_names(cmd, vnet, subnet, resource_group_name, delegation, nw_client,
                                                        delegation_service_name, server_name, VirtualNetwork, Subnet,
                                                        AddressSpace, loc, vnet_address_pref,
                                                        subnet_address_pref)
        else:
            raise CLIError(
                "If you pass an address prefix, please consider passing a name (instead of Id) for a subnet or vnet.")
    elif subnet is not None and vnet is not None:
        if (len(vnet.split('\\')) == 1) and (len(subnet.split('\\')) == 1):
            subnet_result = _create_with_resource_names(cmd, vnet, subnet, resource_group_name, delegation, nw_client,
                                                        delegation_service_name, server_name, VirtualNetwork, Subnet,
                                                        AddressSpace, loc, DEFAULT_VNET_ADDRESS_PREFIX,
                                                        DEFAULT_SUBNET_PREFIX)
        else:
            raise CLIError("If you pass both --vnet and --subnet, consider passing names instead of ids.")
    else:
        return None
    return subnet_result.id


def _create_with_resource_names(cmd, vnet, subnet, resource_group_name, delegation, nw_client,
                                delegation_service_name, server_name, VirtualNetwork, Subnet,
                                AddressSpace, loc, vnet_add, subnet_add):
    if (len(vnet.split('\\')) == 1) and (len(subnet.split('\\')) == 1):
        subnet_result = check_resource_existence(cmd, subnet, vnet, resource_group_name)
        # pylint: disable=no-else-return
        # disabling no-else-return as both if and else return or raise a CLI error, which is needed
        if subnet_result:
            logger.info('Using existing subnet "%s" in resource group "%s"', subnet_result.name, resource_group_name)

            if not subnet_result.delegations:
                logger.info('Adding "%s" delegation to the existing subnet.', )
                subnet_result.delegations = [delegation]
                subnet_result = nw_client.subnets.begin_create_or_update(resource_group_name, vnet, subnet,
                                                                         subnet_result).result()
            else:
                for delgtn in subnet_result.delegations:
                    if delgtn.service_name != delegation_service_name:
                        raise CLIError("Can not use subnet with existing delegations other than {}".format(
                            delegation_service_name))
            return subnet_result
        else:
            logger.warning(
                "The Subnet does not exist. Checking the existence of the Vnet...")
            return _create_vnet_subnet_delegation(nw_client, resource_group_name, vnet, subnet, loc,
                                                  server_name, delegation, VirtualNetwork, Subnet,
                                                  AddressSpace, vnet_add,
                                                  subnet_add)
    else:
        raise CLIError("Invalid Vnet Name or Subnet Name provided.")


def validate_rg_loc_sub(s_subscription, s_location, subscription, location):
    if not ((s_location == location) and (s_subscription == subscription)):
        raise CLIError(
            "Incorrect Usage : The location and subscription of the server,Vnet and Subnet should be same.")


def check_resource_existence(cmd, subnet_name, vnet_name, resource_group_name, ):
    nw_client = network_client_factory(cmd.cli_ctx)
    subnet = _get_resource(nw_client.subnets, resource_group_name, vnet_name, subnet_name)
    return subnet


def _create_vnet_subnet_delegation(nw_client, resource_group, vnet_name, subnet_name, location, server_name, delegation,
                                   VirtualNetwork, Subnet, AddressSpace, vnet_address_pref, subnet_address_pref):
    from azure.core.exceptions import HttpResponseError
    try:
        vnet_exist = _get_resource(nw_client.virtual_networks, resource_group, vnet_name)
        if not vnet_exist:
            logger.info('The Vnet does not exist. Creating new vnet "%s" in resource group "%s"',
                        vnet_name, resource_group)
            nw_client.virtual_networks.begin_create_or_update(resource_group,
                                                              vnet_name,
                                                              VirtualNetwork(name=vnet_name,
                                                                             location=location,
                                                                             address_space=AddressSpace(
                                                                                 address_prefixes=[
                                                                                     vnet_address_pref])))
        subnet_result = Subnet(
            name=subnet_name,
            location=location,
            address_prefix=subnet_address_pref,
            delegations=[delegation])

        logger.info('Creating new subnet "%s" in resource group "%s"', subnet_name, resource_group)
        return nw_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name,
                                                        subnet_result).result()
    except HttpResponseError as err:
        if err.error.code == 'NetcfgInvalidSubnet':
            raise CLIError('Cannot add the subnet {} to the vnet {}.The subnet address space exceeds'
                           ' the available vnet address space.'.format(subnet_name, vnet_name))
        raise


def _get_resource(client, resource_group_name, *subresources):
    from azure.core.exceptions import HttpResponseError
    try:
        resource = client.get(resource_group_name, *subresources)
        return resource
    except HttpResponseError as ex:
        if ex.error.code == "NotFound" or ex.error.code == "ResourceNotFound":
            return None
        raise


def create_vnet(cmd, servername, location, resource_group_name, delegation_service_name):
    Subnet, VirtualNetwork, AddressSpace, Delegation = cmd.get_models('Subnet', 'VirtualNetwork', 'AddressSpace',
                                                                      'Delegation',
                                                                      resource_type=ResourceType.MGMT_NETWORK)
    client = network_client_factory(cmd.cli_ctx)
    vnet_name, subnet_name, vnet_address_prefix, subnet_prefix = _create_vnet_metadata(servername[6:])

    logger.warning('Creating new vnet "%s" in resource group "%s"...', vnet_name, resource_group_name)
    client.virtual_networks.begin_create_or_update(resource_group_name, vnet_name,
                                                   VirtualNetwork(name=vnet_name, location=location,
                                                                  address_space=AddressSpace(
                                                                      address_prefixes=[vnet_address_prefix])))
    delegation = Delegation(name=delegation_service_name, serv_name=delegation_service_name)
    subnet = Subnet(name=subnet_name, location=location, address_prefix=subnet_prefix, delegations=[delegation])

    logger.warning('Creating new subnet "%s" in resource group "%s" and delegating it to "%s"...', subnet_name,
                   resource_group_name, delegation_service_name)
    subnet = client.subnets.begin_create_or_update(resource_group_name, vnet_name, subnet_name, subnet).result()
    return subnet.id


def _create_vnet_metadata(servername):
    vnet_name = 'VNET' + servername
    subnet_name = 'Subnet' + servername
    vnet_address_prefix = DEFAULT_VNET_ADDRESS_PREFIX
    subnet_prefix = DEFAULT_SUBNET_PREFIX
    return vnet_name, subnet_name, vnet_address_prefix, subnet_prefix

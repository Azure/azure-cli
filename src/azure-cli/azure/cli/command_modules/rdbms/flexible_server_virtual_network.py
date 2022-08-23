# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-argument, line-too-long, import-outside-toplevel
from requests import get
from msrestazure.tools import is_valid_resource_id, parse_resource_id, is_valid_resource_name, resource_id  # pylint: disable=import-error
from knack.log import get_logger
from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError, user_confirmation
from azure.cli.core.azclierror import ValidationError
from azure.mgmt.privatedns.models import PrivateZone
from azure.mgmt.privatedns.models import SubResource
from azure.mgmt.privatedns.models import VirtualNetworkLink
from ._client_factory import resource_client_factory, network_client_factory, private_dns_client_factory, private_dns_link_client_factory
from ._flexible_server_util import get_id_components, check_existence, _is_resource_name, parse_public_access_input, get_user_confirmation
from .validators import validate_private_dns_zone, validate_vnet_location

logger = get_logger(__name__)
DEFAULT_VNET_ADDRESS_PREFIX = '10.0.0.0/16'
DEFAULT_SUBNET_ADDRESS_PREFIX = '10.0.0.0/24'
IP_ADDRESS_CHECKER = 'https://api.ipify.org'


# pylint: disable=too-many-locals, too-many-statements, too-many-branches, import-outside-toplevel
def prepare_private_network(cmd, resource_group_name, server_name, vnet, subnet, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes):

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
        subnet_result = process_private_network_with_id_input(cmd, subnet, nw_client, resource_client, server_name, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes)
    elif subnet is None and vnet is not None:
        if is_valid_resource_id(vnet):
            logger.warning("You have supplied a Vnet ID. Verifying its existence...")
            subnet_result = process_private_network_with_id_input(cmd, vnet, nw_client, resource_client, server_name, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes)
        elif _is_resource_name(vnet) and is_valid_resource_name(vnet):
            logger.warning("You have supplied a Vnet name. Verifying its existence...")
            subnet_result = _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group_name, vnet, 'Subnet' + server_name,
                                                           location, server_name, vnet_address_pref, subnet_address_pref, yes)
        else:
            raise ValidationError("Incorrectly formed Vnet ID or Vnet name")
    elif subnet is not None and vnet is not None:
        if _is_resource_name(vnet) and _is_resource_name(subnet):
            logger.warning("You have supplied a Vnet and Subnet name. Verifying its existence...")

            subnet_result = _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group_name, vnet, subnet,
                                                           location, server_name, vnet_address_pref, subnet_address_pref, yes)

        else:
            raise ValidationError("If you pass both --vnet and --subnet, consider passing names instead of IDs. If you want to use an existing subnet, please provide the subnet Id only (not vnet Id).")
    else:
        return None

    return subnet_result.id


def process_private_network_with_id_input(cmd, rid, nw_client, resource_client, server_name, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes):
    id_subscription, id_resource_group, id_vnet, id_subnet = get_id_components(rid)
    nw_client, resource_client = _change_client_with_different_subscription(cmd, id_subscription, nw_client, resource_client)
    _create_and_verify_resource_group(resource_client, id_resource_group, location, yes)
    if id_subnet is None:
        id_subnet = 'Subnet' + server_name

    return _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, id_resource_group, id_vnet, id_subnet,
                                          location, server_name, vnet_address_pref, subnet_address_pref, yes)


def _change_client_with_different_subscription(cmd, subscription, nw_client, resource_client):
    if subscription != get_subscription_id(cmd.cli_ctx):
        logger.warning('The Vnet/Subnet ID provided is in different subscription from the server')
        nw_client = network_client_factory(cmd.cli_ctx, subscription_id=subscription)
        resource_client = resource_client_factory(cmd.cli_ctx, subscription_id=subscription)

    return nw_client, resource_client


def _create_and_verify_resource_group(resource_client, resource_group, location, yes):
    if not resource_client.resource_groups.check_existence(resource_group):
        logger.warning("Provided resource group in the resource ID doesn't exist.")
        user_confirmation("Do you want to create a new resource group {0}".format(resource_group), yes=yes)
        resource_client.resource_groups.create_or_update(resource_group, {'location': location})


def _create_vnet_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group, vnet_name, subnet_name, location, server_name, vnet_address_pref, subnet_address_pref, yes):
    VirtualNetwork, AddressSpace = cmd.get_models('VirtualNetwork', 'AddressSpace', resource_type=ResourceType.MGMT_NETWORK)
    if not check_existence(resource_client, vnet_name, resource_group, 'Microsoft.Network', 'virtualNetworks'):
        user_confirmation("Do you want to create a new Vnet {0} in resource group {1}".format(vnet_name, resource_group), yes=yes)
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
        # validate whether vnet location is same as server
        validate_vnet_location(vnet, location)
        prefixes = vnet.address_space.address_prefixes
        subnet_exist = check_existence(resource_client, subnet_name, resource_group, 'Microsoft.Network', 'subnets', parent_name=vnet_name, parent_type='virtualNetworks')
        if not subnet_exist and vnet_address_pref not in prefixes:
            logger.warning('The address prefix does not exist in the Vnet. Adding address prefix %s to Vnet %s.', vnet_address_pref, vnet_name)
            vnet.address_space.address_prefixes += [vnet_address_pref]
            nw_client.virtual_networks.begin_create_or_update(resource_group, vnet_name, vnet).result()

    return _create_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group, vnet_name, subnet_name, location, server_name, subnet_address_pref, yes)


def _create_subnet_delegation(cmd, nw_client, resource_client, delegation_service_name, resource_group, vnet_name, subnet_name, location, server_name, subnet_address_pref, yes):
    Delegation, Subnet = cmd.get_models('Delegation', 'Subnet', resource_type=ResourceType.MGMT_NETWORK)
    delegation = Delegation(name=delegation_service_name, service_name=delegation_service_name)

    # subnet not exist
    if not check_existence(resource_client, subnet_name, resource_group, 'Microsoft.Network', 'subnets', parent_name=vnet_name, parent_type='virtualNetworks'):
        subnet_result = Subnet(
            name=subnet_name,
            location=location,
            address_prefix=subnet_address_pref,
            delegations=[delegation])

        vnet = nw_client.virtual_networks.get(resource_group, vnet_name)
        vnet_subnet_prefixes = [subnet.address_prefix for subnet in vnet.subnets]
        if subnet_address_pref in vnet_subnet_prefixes:
            raise ValidationError("The Subnet (default) prefix {} is already taken by another Subnet in the Vnet. Please provide a different prefix for --subnet-prefix parameter".format(subnet_address_pref))

        user_confirmation("Do you want to create a new Subnet {0} in resource group {1}".format(subnet_name, resource_group), yes=yes)
        logger.warning('Creating new Subnet "%s" in resource group "%s"', subnet_name, resource_group)
        subnet = nw_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name,
                                                          subnet_result).result()
    # subnet exist
    else:
        subnet = nw_client.subnets.get(resource_group, vnet_name, subnet_name)
        logger.warning('Using existing Subnet "%s" in resource group "%s"', subnet_name, resource_group)
        if subnet_address_pref not in (DEFAULT_SUBNET_ADDRESS_PREFIX, subnet.address_prefix):
            logger.warning("The prefix of the subnet you provided does not match the --subnet-prefix value %s. Using current prefix %s", subnet_address_pref, subnet.address_prefix)

        # Add Delegation if not delegated already
        if not subnet.delegations:
            logger.warning('Adding "%s" delegation to the existing subnet %s.', delegation_service_name, subnet_name)
            subnet.delegations = [delegation]
            subnet = nw_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name, subnet).result()
        else:
            for delgtn in subnet.delegations:
                if delgtn.service_name != delegation_service_name:
                    raise CLIError("Can not use subnet with existing delegations other than {}".format(
                        delegation_service_name))

    return subnet


def prepare_private_dns_zone(db_context, database_engine, resource_group, server_name, private_dns_zone, subnet_id, location, yes):
    cmd = db_context.cmd
    dns_suffix_client = db_context.cf_private_dns_zone_suffix(cmd.cli_ctx, '_')
    private_dns_zone_suffix = dns_suffix_client.execute()
    if db_context.command_group == 'mysql':
        private_dns_zone_suffix = private_dns_zone_suffix.private_dns_zone_suffix

    # suffix should start with .
    if private_dns_zone_suffix[0] != '.':
        private_dns_zone_suffix = '.' + private_dns_zone_suffix

    # Get Vnet Components
    vnet_subscription, vnet_rg, vnet_name, _ = get_id_components(subnet_id)
    nw_client = network_client_factory(cmd.cli_ctx, subscription_id=vnet_subscription)
    vnet_id = resource_id(subscription=vnet_subscription,
                          resource_group=vnet_rg,
                          namespace='Microsoft.Network',
                          type='virtualNetworks',
                          name=vnet_name)
    vnet = nw_client.virtual_networks.get(vnet_rg, vnet_name)

    # Process private dns zone (no input or Id input)
    dns_rg = None
    dns_subscription = vnet_subscription
    if private_dns_zone is None:
        if 'private' in private_dns_zone_suffix:
            private_dns_zone = server_name + private_dns_zone_suffix
        else:
            private_dns_zone = server_name + '.private' + private_dns_zone_suffix
    elif not _is_resource_name(private_dns_zone) and is_valid_resource_id(private_dns_zone):
        dns_subscription, dns_rg, private_dns_zone, _ = get_id_components(private_dns_zone)

    validate_private_dns_zone(db_context,
                              server_name=server_name,
                              private_dns_zone=private_dns_zone,
                              private_dns_zone_suffix=private_dns_zone_suffix)

    server_sub_resource_client = resource_client_factory(cmd.cli_ctx, subscription_id=get_subscription_id(cmd.cli_ctx))
    vnet_sub_resource_client = resource_client_factory(cmd.cli_ctx, subscription_id=vnet_subscription)
    dns_sub_resource_client = resource_client_factory(cmd.cli_ctx, subscription_id=dns_subscription)

    # check existence DNS zone and change resource group
    if dns_rg is not None:
        _create_and_verify_resource_group(dns_sub_resource_client, dns_rg, location, yes)

    # decide which resource group the dns zone provision
    zone_exist_flag = False
    if dns_rg is not None and check_existence(dns_sub_resource_client, private_dns_zone, dns_rg, 'Microsoft.Network', 'privateDnsZones'):
        zone_exist_flag = True
    elif dns_rg is None and check_existence(server_sub_resource_client, private_dns_zone, resource_group, 'Microsoft.Network', 'privateDnsZones'):
        zone_exist_flag = True
        dns_rg = resource_group
        dns_subscription = get_subscription_id(cmd.cli_ctx)
    elif dns_rg is None and check_existence(vnet_sub_resource_client, private_dns_zone, vnet_rg, 'Microsoft.Network', 'privateDnsZones'):
        zone_exist_flag = True
        dns_subscription = vnet_subscription
        dns_rg = vnet_rg
    elif dns_rg is None:
        zone_exist_flag = False
        dns_subscription = vnet_subscription
        dns_rg = vnet_rg

    private_dns_client = private_dns_client_factory(cmd.cli_ctx, subscription_id=dns_subscription)
    private_dns_link_client = private_dns_link_client_factory(cmd.cli_ctx, subscription_id=dns_subscription)
    link = VirtualNetworkLink(location='global', virtual_network=SubResource(id=vnet.id))
    link.registration_enabled = False

    # create DNS zone if not exist
    if not zone_exist_flag:
        user_confirmation("Do you want to create a new private DNS zone {0} in resource group {1}".format(private_dns_zone, dns_rg), yes=yes)
        logger.warning('Creating a private dns zone %s in resource group "%s"', private_dns_zone, dns_rg)
        private_zone = private_dns_client.begin_create_or_update(resource_group_name=dns_rg,
                                                                 private_zone_name=private_dns_zone,
                                                                 parameters=PrivateZone(location='global'),
                                                                 if_none_match='*').result()

        private_dns_link_client.begin_create_or_update(resource_group_name=dns_rg,
                                                       private_zone_name=private_dns_zone,
                                                       virtual_network_link_name=vnet_name + '-link',
                                                       parameters=link, if_none_match='*').result()
    else:
        logger.warning('Using the existing private dns zone %s in resource group "%s"', private_dns_zone, dns_rg)

        private_zone = private_dns_client.get(resource_group_name=dns_rg,
                                              private_zone_name=private_dns_zone)
        virtual_links = private_dns_link_client.list(resource_group_name=dns_rg,
                                                     private_zone_name=private_dns_zone)

        link_exist_flag = False
        for virtual_link in virtual_links:
            if virtual_link.virtual_network.id == vnet_id:
                link_exist_flag = True
                break

        if not link_exist_flag:
            private_dns_link_client.begin_create_or_update(resource_group_name=dns_rg,
                                                           private_zone_name=private_dns_zone,
                                                           virtual_network_link_name=vnet_name + '-link',
                                                           parameters=link, if_none_match='*').result()

    return private_zone.id


def prepare_public_network(public_access, yes):
    if public_access is None:
        ip_address = get(IP_ADDRESS_CHECKER).text
        logger.warning("Detected current client IP : %s", ip_address)
        if yes:
            return ip_address, ip_address

        if get_user_confirmation("Do you want to enable access to client {0} (y/n)".format(ip_address), yes=yes):
            return ip_address, ip_address

        if get_user_confirmation("Do you want to enable access for all IPs ", yes=yes):
            return '0.0.0.0', '255.255.255.255'
        return -1, -1

    if str(public_access).lower() == 'all':
        start_ip, end_ip = '0.0.0.0', '255.255.255.255'
    elif str(public_access).lower() in ['none', 'disabled', 'enabled']:
        start_ip, end_ip = -1, -1
    else:
        start_ip, end_ip = parse_public_access_input(public_access)

    return start_ip, end_ip

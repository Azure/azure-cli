import argparse
import base64
import socket

from azure.cli.commands.arm import is_valid_resource_id, resource_id
from azure.cli._util import CLIError
from azure.cli.commands.validators import SPECIFIED_SENTINEL
from azure.cli.commands.client_factory import get_subscription_id

def _convert_id_list_to_object(data):
    if not data:
        return None

    if not isinstance(data, list):
        data = [data]
    data_list = []
    for val in data:
        if not is_valid_resource_id(val):
            raise CLIError('{} is not a valid ID.'.format(val))
        data_list.append({'id': val})
    return data_list

# PARAMETER VALIDATORS

def validate_inbound_nat_rule_id_list(namespace):
    ids = namespace.load_balancer_inbound_nat_rule_ids
    if ids and '' not in ids:
        namespace.load_balancer_inbound_nat_rule_ids = \
            _convert_id_list_to_object(namespace.load_balancer_inbound_nat_rule_ids)

def validate_address_pool_id_list(namespace):
    ids = namespace.load_balancer_backend_address_pool_ids
    if ids and '' not in ids:
        namespace.load_balancer_backend_address_pool_ids =\
            _convert_id_list_to_object(namespace.load_balancer_backend_address_pool_ids)

def validate_inbound_nat_rule_name_or_id(namespace):
    rule_name = namespace.inbound_nat_rule
    lb_name = namespace.load_balancer_name

    if is_valid_resource_id(rule_name):
        if lb_name:
            raise CLIError('Please omit --lb-name when specifying an inbound NAT rule ID.')
    else:
        if not lb_name:
            raise CLIError('Please specify --lb-name when specifying an inbound NAT rule name.')
        namespace.inbound_nat_rule = resource_id(
            subscription=get_subscription_id(),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='loadBalancers',
            name=lb_name,
            child_type='inboundNatRules',
            child_name=rule_name)

def validate_address_pool_name_or_id(namespace):
    pool_name = namespace.backend_address_pool
    lb_name = namespace.load_balancer_name

    if is_valid_resource_id(pool_name):
        if lb_name:
            raise CLIError('Please omit --lb-name when specifying an address pool ID.')
    else:
        if not lb_name:
            raise CLIError('Please specify --lb-name when specifying an address pool name.')
        namespace.backend_address_pool = resource_id(
            subscription=get_subscription_id(),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='loadBalancers',
            name=lb_name,
            child_type='backendAddressPools',
            child_name=pool_name)

def validate_subnet_name_or_id(namespace):
    """ Validates a subnet ID or, if a name is provided, formats it as an ID. """
    # no validation if params not specified or clear sigal is used
    if namespace.virtual_network_name is None and namespace.subnet is None:
        return
    if namespace.subnet == '':
        return

    # error if vnet-name is provided without subnet
    if namespace.virtual_network_name and not namespace.subnet:
        raise CLIError('You must specify --subnet name when using --vnet-name.')

    # determine if subnet is name or ID
    is_id = is_valid_resource_id(namespace.subnet)

    # error if vnet-name is provided along with a subnet ID
    if is_id and namespace.virtual_network_name:
        raise argparse.ArgumentError(None, 'Please omit --vnet-name when specifying a subnet ID')
    elif not is_id and not namespace.virtual_network_name:
        raise argparse.ArgumentError(None,
                                     'Please specify --vnet-name when specifying a subnet name')
    if not is_id:
        namespace.subnet = resource_id(
            subscription=get_subscription_id(),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=namespace.virtual_network_name,
            child_type='subnets',
            child_name=namespace.subnet)

def validate_private_ip_address(namespace):
    if namespace.private_ip_address:
        namespace.private_ip_address_allocation = 'static'

def validate_public_ip_name_or_id(namespace):
    """ Validates a public IP ID or, if a name is provided, formats it as an ID. """
    if namespace.public_ip_address:
        # determine if public_ip_address is name or ID
        is_id = is_valid_resource_id(namespace.public_ip_address)
        if not is_id:
            namespace.public_ip_address = resource_id(
                subscription=get_subscription_id(),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='publicIPAddresses',
                name=namespace.public_ip_address)

def validate_nsg_name_or_id(namespace):
    """ Validates a NSG ID or, if a name is provided, formats it as an ID. """
    if namespace.network_security_group:
        # determine if network_security_group is name or ID
        is_id = is_valid_resource_id(namespace.network_security_group)
        if not is_id:
            namespace.network_security_group = resource_id(
                subscription=get_subscription_id(),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='networkSecurityGroups',
                name=namespace.network_security_group)

# COMMAND NAMESPACE VALIDATORS

def process_nic_create_namespace(namespace):
    if namespace.internal_dns_name_label:
        namespace.use_dns_settings = 'true'

    if not namespace.public_ip_address:
        namespace.public_ip_address_type = 'none'

    if not namespace.network_security_group:
        namespace.network_security_group_type = 'none'

def process_network_lb_create_namespace(namespace):
    if namespace.public_ip_dns_name:
        namespace.dns_name_type = 'new'

    if namespace.subnet and namespace.public_ip_address:
        raise argparse.ArgumentError(
            None, 'Must specify a subnet OR a public IP address, not both.')

def validate_public_ip_type(namespace): # pylint: disable=unused-argument
    if namespace.subnet:
        namespace.public_ip_address_type = 'none'

def process_public_ip_create_namespace(namespace):
    if namespace.dns_name:
        namespace.public_ip_address_type = 'dns'

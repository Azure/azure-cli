# pylint: disable=no-self-use,too-many-arguments
from azure.mgmt.network.models import Subnet, SecurityRule
from ._factory import _network_client_factory

def create_update_subnet(resource_group_name, subnet_name, virtual_network_name,
                         address_prefix='10.0.0.0/24'):
    '''Create or update a virtual network (VNet) subnet'''
    subnet_settings = Subnet(name=subnet_name, address_prefix=address_prefix)
    ncf = _network_client_factory()
    return ncf.subnets.create_or_update(
        resource_group_name, virtual_network_name, subnet_name, subnet_settings)

def create_update_nsg_rule(resource_group_name, network_security_group_name, security_rule_name,
                           protocol, source_address_prefix, destination_address_prefix,
                           access, direction, source_port_range, destination_port_range,
                           description=None, priority=None):
    settings = SecurityRule(protocol=protocol, source_address_prefix=source_address_prefix,
                            destination_address_prefix=destination_address_prefix, access=access,
                            direction=direction,
                            description=description, source_port_range=source_port_range,
                            destination_port_range=destination_port_range, priority=priority,
                            name=security_rule_name)
    ncf = _network_client_factory()
    return ncf.security_rules.create_or_update(
        resource_group_name, network_security_group_name, security_rule_name, settings)

create_update_nsg_rule.__doc__ = SecurityRule.__doc__

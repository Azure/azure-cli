# pylint: disable=no-self-use,too-many-arguments
from azure.mgmt.network.models import Subnet, SecurityRule
from ._factory import _network_client_factory

def create_update_subnet(resource_group_name, subnet_name, virtual_network_name, address_prefix):
    '''Create or update a virtual network (VNet) subnet'''
    subnet_settings = Subnet(name=subnet_name, address_prefix=address_prefix)
    ncf = _network_client_factory()
    return ncf.subnets.create_or_update(
        resource_group_name, virtual_network_name, subnet_name, subnet_settings)

def create_update_nsg_rule(resource_group_name, network_security_group_name, security_rule_name,
                           protocol, source_address_prefix, destination_address_prefix,
                           access, direction, description=None, source_port_range=None,
                           destination_port_range=None, priority=None, provisioning_state=None,
                           name=None):
    settings = SecurityRule(protocol=protocol, source_address_prefix=source_address_prefix,
                            destination_address_prefix=destination_address_prefix, access=access,
                            direction=direction,
                            description=description, source_port_range=source_port_range,
                            destination_port_range=destination_port_range, priority=priority,
                            provisioning_state=provisioning_state, name=name)
    ncf = _network_client_factory()
    return ncf.security_rules.create_or_update(
        resource_group_name, network_security_group_name, security_rule_name, settings)

create_update_nsg_rule.__doc__ = SecurityRule.__doc__

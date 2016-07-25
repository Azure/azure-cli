#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,no-member
from azure.mgmt.network.models import Subnet, SecurityRule, NetworkSecurityGroup

from azure.cli._util import CLIError

from ._factory import _network_client_factory

def _generic_list(operation_name, resource_group_name):
    ncf = _network_client_factory()
    operation_group = getattr(ncf, operation_name)
    if resource_group_name:
        return operation_group.list(resource_group_name)
    else:
        return operation_group.list_all()

def list_vnet(resource_group_name=None):
    return _generic_list('virtual_networks', resource_group_name)

def list_express_route_circuits(resource_group_name=None):
    return _generic_list('express_route_circuits', resource_group_name)

def list_lbs(resource_group_name=None):
    return _generic_list('load_balancers', resource_group_name)

def list_nics(resource_group_name=None):
    return _generic_list('network_interfaces', resource_group_name)

def list_nsgs(resource_group_name=None):
    return _generic_list('network_security_groups', resource_group_name)

def list_public_ips(resource_group_name=None):
    return _generic_list('public_ip_addresses', resource_group_name)

def list_route_tables(resource_group_name=None):
    return _generic_list('route_tables', resource_group_name)

def list_application_gateways(resource_group_name=None):
    return _generic_list('application_gateways', resource_group_name)

def create_nsg_rule(resource_group_name, network_security_group_name, security_rule_name,
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

create_nsg_rule.__doc__ = SecurityRule.__doc__

def update_vnet(resource_group_name, virtual_network_name, address_prefixes):
    '''update existing virtual network
    :param address_prefixes: update address spaces. Use space separated address prefixes,
        for example, "10.0.0.0/24 10.0.1.0/24"
    '''
    ncf = _network_client_factory()
    vnet = ncf.virtual_networks.get(resource_group_name, virtual_network_name)
    #server side validation reports pretty good error message on invalid CIDR,
    #so we don't validate at client side
    vnet.address_space.address_prefixes = address_prefixes
    return ncf.virtual_networks.create_or_update(resource_group_name, virtual_network_name, vnet)

def create_subnet(resource_group_name, virtual_network_name, subnet_name,
                  address_prefix='10.0.0.0/24', network_security_group=None):
    '''Create a virtual network (VNet) subnet
    :param str address_prefix: address prefix in CIDR format.
    :param str network_security_group: attach with existing network security group,
        both name or id are accepted.
    '''
    ncf = _network_client_factory()
    subnet = Subnet(name=subnet_name, address_prefix=address_prefix)
    subnet.address_prefix = address_prefix

    if network_security_group:
        subnet.network_security_group = NetworkSecurityGroup(network_security_group)

    return ncf.subnets.create_or_update(resource_group_name, virtual_network_name,
                                        subnet_name, subnet)

def update_subnet(resource_group_name, virtual_network_name, subnet_name,
                  address_prefix=None, network_security_group=None):
    '''update existing virtual sub network
    :param str address_prefix: New address prefix in CIDR format, for example 10.0.0.0/24.
    :param str network_security_group: attach with existing network security group,
        both name or id are accepted. Use empty string "" to detach it.
    '''
    ncf = _network_client_factory()
    subnet = ncf.subnets.get(resource_group_name, virtual_network_name, subnet_name)#pylint: disable=redefined-variable-type

    if address_prefix:
        subnet.address_prefix = address_prefix

    if network_security_group:
        subnet.network_security_group = NetworkSecurityGroup(network_security_group)
    elif network_security_group == '': #clear it
        subnet.network_security_group = None

    return ncf.subnets.create_or_update(resource_group_name, virtual_network_name,
                                        subnet_name, subnet)


# Load Balancer factory methods

def list_load_balancer_property(prop):
    """ Factory method for creating load balancer list functions. """
    def list_func(resource_group_name, load_balancer_name):
        return _network_client_factory().load_balancers.get(
            resource_group_name, load_balancer_name).__getattribute__(prop)
    return list_func

def get_load_balancer_property_entry(prop):
    """ Factory method for creating load balancer get functions. """
    def get_func(resource_group_name, load_balancer_name, item_name):
        items = _network_client_factory().load_balancers.get(
            resource_group_name, load_balancer_name).__getattribute__(prop)

        result = next((x for x in items if x.name.lower() == item_name.lower()), None)
        if not result:
            raise CLIError("Item '{}' does not exist on load balancer '{}'".format(
                item_name, load_balancer_name))
        else:
            return result
    return get_func

def delete_load_balancer_property_entry(prop):
    """ Factory method for creating load balancer delete functions. """
    def delete_func(resource_group_name, load_balancer_name, item_name):
        ncf = _network_client_factory()
        lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
        keep_items = \
            [x for x in lb.__getattribute__(prop) if x.name.lower() != item_name.lower()]
        _set_param(lb, prop, keep_items)
        return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return delete_func

def _get_lb_property(items, name):
    result = next((x for x in items if x.name.lower() == name.lower()), None)
    if not result:
        raise CLIError("Property '{}' does not exist on load balancer".format(name))
    else:
        return result

def _set_param(item, prop, value):
    if value == "":
        setattr(item, prop, None)
    elif value is not None:
        setattr(item, prop, value)

# Inbound NAT Rules

def create_lb_inbound_nat_rule(
        resource_group_name, load_balancer_name, item_name, protocol, frontend_port,
        frontend_ip_name, backend_port, floating_ip="false", idle_timeout=None):
    from azure.mgmt.network.models import InboundNatRule
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    frontend_ip = _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name) # pylint: disable=no-member
    lb.inbound_nat_rules.append(
        InboundNatRule(name=item_name, protocol=protocol,
                       frontend_port=frontend_port, backend_port=backend_port,
                       frontend_ip_configuration=frontend_ip,
                       enable_floating_ip=floating_ip == 'true',
                       idle_timeout_in_minutes=idle_timeout))
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_inbound_nat_rule(
        resource_group_name, load_balancer_name, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, floating_ip=None, idle_timeout=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_lb_property(lb.inbound_nat_rules, item_name)
    if frontend_ip_name:
        item.frontend_ip_configuration = \
            _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name)
    if floating_ip is not None:
        item.enable_floating_ip = floating_ip == 'true'
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port', frontend_port)
    _set_param(item, 'backend_port', backend_port)
    _set_param(item, 'idle_timeout_in_minutes', idle_timeout)
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

# Inbound NAT Pools

def create_lb_inbound_nat_pool(
        resource_group_name, load_balancer_name, item_name, protocol, frontend_port_range_start,
        frontend_port_range_end, backend_port, frontend_ip_name=None):
    from azure.mgmt.network.models import InboundNatPool
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    frontend_ip = _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name) \
        if frontend_ip_name else None
    lb.inbound_nat_pools.append(
        InboundNatPool(name=item_name,
                       protocol=protocol,
                       frontend_ip_configuration=frontend_ip,
                       frontend_port_range_start=frontend_port_range_start,
                       frontend_port_range_end=frontend_port_range_end,
                       backend_port=backend_port))
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_inbound_nat_pool(
        resource_group_name, load_balancer_name, item_name, protocol=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_port=None,
        frontend_ip_name=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_lb_property(lb.inbound_nat_pools, item_name)
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port_range_start', frontend_port_range_start)
    _set_param(item, 'frontend_port_range_end', frontend_port_range_end)
    _set_param(item, 'backend_port', backend_port)
    if frontend_ip_name == "":
        item.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        item.frontend_ip_configuration = \
            _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name)
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

# Frontend IP Configuration

def create_lb_frontend_ip_configuration(
        resource_group_name, load_balancer_name, item_name, public_ip_address_name=None,
        virtual_network_name=None, subnet_name=None, private_ip_address=None):
    from azure.mgmt.network.models import FrontendIPConfiguration
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    public_ip = ncf.public_ip_addresses.get(resource_group_name, public_ip_address_name) \
        if public_ip_address_name else None
    subnet = ncf.subnets.get(resource_group_name, virtual_network_name, subnet_name) \
        if virtual_network_name and subnet_name else None
    lb.frontend_ip_configurations.append(
        FrontendIPConfiguration(
            name=item_name,
            private_ip_address=private_ip_address,
            private_ip_allocation_method='dynamic' if not private_ip_address else 'static',
            public_ip_address=public_ip,
            subnet=subnet))
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_frontend_ip_configuration(
        resource_group_name, load_balancer_name, item_name, private_ip_address=None,
        public_ip_address_name=None, virtual_network_name=None, subnet_name=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_lb_property(lb.frontend_ip_configurations, item_name)
    if private_ip_address == "":
        item.private_ip_allocation_method = 'dynamic'
        item.private_ip_address = None
    elif private_ip_address is not None:
        item.private_ip_allocation_method = 'static'
        item.private_ip_address = private_ip_address
    if subnet_name == "":
        item.subnet = None
    elif virtual_network_name is not None and not subnet_name:
        raise CLIError('You must specify --subnet-name when using --vnet-name.')
    elif subnet_name is not None:
        item.subnet = ncf.subnets.get(resource_group_name, virtual_network_name, subnet_name)
    if public_ip_address_name == "":
        item.public_ip_address = None
    elif public_ip_address_name is not None:
        item.public_ip_address = ncf.public_ip_addresses.get(
            resource_group_name, public_ip_address_name)
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

# Backend Address Pools

def create_lb_backend_address_pool(resource_group_name, load_balancer_name, item_name):
    from azure.mgmt.network.models import BackendAddressPool
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.backend_address_pools.append(BackendAddressPool(name=item_name))
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

# Load Balancer Probe

def create_lb_probe(resource_group_name, load_balancer_name, item_name, protocol, port,
                    path=None, interval=None, threshold=None):
    from azure.mgmt.network.models import Probe
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.probes.append(
        Probe(protocol, port, interval_in_seconds=interval, number_of_probes=threshold,
              request_path=path, name=item_name))
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_probe(resource_group_name, load_balancer_name, item_name, protocol=None, port=None,
                 path=None, interval=None, threshold=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_lb_property(lb.probes, item_name)
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'port', port)
    _set_param(item, 'request_path', path)
    _set_param(item, 'interval_in_seconds', interval)
    _set_param(item, 'number_of_probes', threshold)
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

# Load Balancer Rule

def create_lb_rule(
        resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name,
        backend_address_pool_name, probe_name=None, load_distribution='default',
        floating_ip='false', idle_timeout=None):
    from azure.mgmt.network.models import LoadBalancingRule
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.load_balancing_rules.append(
        LoadBalancingRule(
            name=item_name,
            protocol=protocol,
            frontend_port=frontend_port,
            backend_port=backend_port,
            frontend_ip_configuration=_get_lb_property(lb.frontend_ip_configurations,
                                                       frontend_ip_name),
            backend_address_pool=_get_lb_property(lb.backend_address_pools,
                                                  backend_address_pool_name),
            probe=_get_lb_property(lb.probes, probe_name) if probe_name else None,
            load_distribution=load_distribution,
            enable_floating_ip=floating_ip == 'true',
            idle_timeout_in_minutes=idle_timeout))
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_rule(
        resource_group_name, load_balancer_name, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution='default', floating_ip=None, idle_timeout=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_lb_property(lb.load_balancing_rules, item_name)
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port', frontend_port)
    _set_param(item, 'backend_port', backend_port)
    _set_param(item, 'idle_timeout_in_minutes', idle_timeout)
    _set_param(item, 'load_distribution', load_distribution)
    if frontend_ip_name is not None:
        item.frontend_ip_configuration = \
            _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name)
    if floating_ip is not None:
        item.enable_floating_ip = floating_ip == 'true'
    if backend_address_pool_name is not None:
        item.backend_address_pool = \
            _get_lb_property(lb.backend_address_pools, backend_address_pool_name)
    if probe_name == "":
        item.probe = None
    elif probe_name is not None:
        item.probe = _get_lb_property(lb.probes, probe_name)
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def update_nsg_rule(resource_group_name, network_security_group_name, security_rule_name,
                    protocol=None, source_address_prefix=None, destination_address_prefix=None,
                    access=None, direction=None, description=None, source_port_range=None,
                    destination_port_range=None, priority=None):
    ncf = _network_client_factory()

    nsg = ncf.network_security_groups.get(resource_group_name, network_security_group_name)

    r = next((r for r in nsg.security_rules if r.name.lower() == security_rule_name.lower()), None)
    if not r:
        raise CLIError("Rule '{}' doesn't exist in the network security group of '{}'".format(
            security_rule_name, network_security_group_name))

    #No client validation as server side returns pretty good errors

    r.protocol = protocol if protocol is not None else r.protocol
    #pylint: disable=line-too-long
    r.source_address_prefix = (source_address_prefix if source_address_prefix is not None
                               else r.source_address_prefix)
    r.destination_address_prefix = (destination_address_prefix if destination_address_prefix is not None
                                    else r.destination_address_prefix)
    r.access = access if access is not None else r.access
    r.direction = direction if direction is not None else r.direction
    r.description = description if description is not None else r.description
    r.source_port_range = source_port_range if source_port_range is not None else r.source_port_range
    r.destination_port_range = (destination_port_range if destination_port_range is not None
                                else r.destination_port_range)
    r.priority = priority if priority is not None else r.priority

    return ncf.security_rules.create_or_update(resource_group_name, network_security_group_name, security_rule_name, r)

update_nsg_rule.__doc__ = SecurityRule.__doc__

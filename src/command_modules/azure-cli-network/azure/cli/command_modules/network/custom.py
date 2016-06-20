# pylint: disable=no-self-use,too-many-arguments,unused-argument
from functools import wraps

from azure.mgmt.network.models import Subnet, SecurityRule

from azure.cli._util import CLIError
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
        try:
            return next(x for x in items if x.name.lower() == item_name.lower())
        except StopIteration:
            raise CLIError("Item '{}' does not exist on load balancer '{}'".format(
                item_name, load_balancer_name))
    return get_func

def delete_load_balancer_property_entry(prop):
    """ Factory method for creating load balancer delete functions. """
    def delete_func(resource_group_name, load_balancer_name, item_name):
        ncf = _network_client_factory()
        lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
        keep_items = \
            [x for x in lb.__getattribute__(prop) if x.name.lower() != item_name.lower()]
        lb.__setattr__(prop, keep_items)
        return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return delete_func

def create_load_balancer_property_entry(prop, func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ncf = _network_client_factory()
        rg_name = kwargs.get('resource_group_name')
        lb_name = kwargs.get('load_balancer_name')
        lb = ncf.load_balancers.get(rg_name, lb_name)
        property_list = getattr(lb, prop)
        kwargs['lb'] = lb
        property_list.append(func(*args, **kwargs))
        return ncf.load_balancers.create_or_update(rg_name, lb_name, lb)
    return wrapper

def set_load_balancer_property_entry(prop, func):
    @wraps(func)
    def wrapper(**kwargs):
        ncf = _network_client_factory()
        rg_name = kwargs.get('resource_group_name')
        lb_name = kwargs.get('load_balancer_name')
        item_name = kwargs.get('item_name')
        lb = ncf.load_balancers.get(rg_name, lb_name)
        try:
            item = next(x for x in getattr(lb, prop) if x.name.lower() == item_name.lower())
        except StopIteration:
            raise CLIError("Item '{}' does not exist on load balancer "
                           " '{}' for property '{}'".format(item_name, lb_name, prop))
        kwargs['item'] = item
        kwargs['lb'] = lb
        func(**kwargs)
        return ncf.load_balancers.create_or_update(rg_name, lb_name, lb)
    return wrapper

def _get_lb_property(items, name):
    try:
        return next(x for x in items if x.name.lower() == name.lower())
    except StopIteration:
        raise CLIError("Item '{}' does not exist on load balancer".format(name))

def _set_param(item, prop, value):
    if value == "":
        setattr(item, prop, None)
    elif value is not None:
        setattr(item, prop, value)

# Inbound NAT Rules

def create_lb_inbound_nat_rule(
        resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, frontend_ip_name, backend_port, floating_ip="false",
        idle_timeout=None, lb=None):
    from azure.mgmt.network.models import InboundNatRule
    frontend_ip = _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name)
    return InboundNatRule(name=item_name, protocol=protocol,
                          frontend_port=frontend_port, backend_port=backend_port,
                          frontend_ip_configuration=frontend_ip,
                          enable_floating_ip=floating_ip == 'true',
                          idle_timeout_in_minutes=idle_timeout)

def set_lb_inbound_nat_rule(
        resource_group_name, load_balancer_name, item_name, item=None, lb=None,
        protocol=None, frontend_port=None, frontend_ip_name=None, backend_port=None,
        floating_ip=None, idle_timeout=None):
    if frontend_ip_name:
        item.frontend_ip_configuration = \
            _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name)
    if floating_ip is not None:
        item.enable_floating_ip = floating_ip == 'true'
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port', frontend_port)
    _set_param(item, 'backend_port', backend_port)
    _set_param(item, 'idle_timeout_in_minutes', idle_timeout)

# Inbound NAT Pools

def create_lb_inbound_nat_pool(
        resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port_range_start, frontend_port_range_end, backend_port,
        frontend_ip_name=None, lb=None):
    from azure.mgmt.network.models import InboundNatPool
    frontend_ip = _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name) \
        if frontend_ip_name else None
    return InboundNatPool(name=item_name,
                          protocol=protocol,
                          frontend_ip_configuration=frontend_ip,
                          frontend_port_range_start=frontend_port_range_start,
                          frontend_port_range_end=frontend_port_range_end,
                          backend_port=backend_port)

def set_lb_inbound_nat_pool(
        resource_group_name, load_balancer_name, item_name, item=None, lb=None,
        protocol=None, frontend_port_range_start=None, frontend_port_range_end=None,
        backend_port=None, frontend_ip_name=None):
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port_range_start', frontend_port_range_start)
    _set_param(item, 'frontend_port_range_end', frontend_port_range_end)
    _set_param(item, 'backend_port', backend_port)
    if frontend_ip_name == "":
        item.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        item.frontend_ip_configuration = \
            _get_lb_property(lb.frontend_ip_configurations, frontend_ip_name)

# Frontend IP Configuration

def create_lb_frontend_ip_configuration(
        resource_group_name, load_balancer_name, item_name,
        public_ip_address_name=None, virtual_network_name=None, subnet_name=None,
        private_ip_address=None, lb=None):
    from azure.mgmt.network.models import FrontendIPConfiguration
    ncf = _network_client_factory()
    public_ip = ncf.public_ip_addresses.get(resource_group_name, public_ip_address_name) \
        if public_ip_address_name else None
    subnet = ncf.subnets.get(resource_group_name, virtual_network_name, subnet_name) \
        if virtual_network_name and subnet_name else None
    return FrontendIPConfiguration(
        name=item_name,
        private_ip_address=private_ip_address,
        private_ip_allocation_method='dynamic' if not private_ip_address else 'static',
        public_ip_address=public_ip,
        subnet=subnet)

def set_lb_frontend_ip_configuration(
        resource_group_name, load_balancer_name, item_name, item=None,
        lb=None, private_ip_address=None, public_ip_address_name=None, virtual_network_name=None,
        subnet_name=None):
    ncf = _network_client_factory()
    if private_ip_address == "":
        item.private_ip_allocation_method = 'dynamic'
        item.private_ip_address = None
    elif private_ip_address is not None:
        item.private_ip_allocation_method = 'static'
        item.private_ip_address = private_ip_address
    if subnet_name == "":
        item.subnet = None
    elif virtual_network_name is not None and subnet_name is not None:
        item.subnet = ncf.subnets.get(resource_group_name, virtual_network_name, subnet_name)
    if public_ip_address_name == "":
        item.public_ip_address = None
    elif public_ip_address_name is not None:
        item.public_ip_address = ncf.public_ip_addresses.get(
            resource_group_name, public_ip_address_name)

# Backend Address Pools

def create_lb_backend_address_pool(resource_group_name, load_balancer_name, item_name, lb=None):
    from azure.mgmt.network.models import BackendAddressPool
    return BackendAddressPool(name=item_name)

# Load Balancer Probe

def create_lb_probe(resource_group_name, load_balancer_name, item_name, protocol, port,
                    path=None, interval=None, threshold=None, lb=None):
    from azure.mgmt.network.models import Probe
    return Probe(protocol, port, interval_in_seconds=interval, number_of_probes=threshold,
                 request_path=path, name=item_name)

def set_lb_probe(resource_group_name, load_balancer_name, item_name, item=None, lb=None,
                 protocol=None, port=None, path=None, interval=None, threshold=None):
    _set_param(item, 'protocol', protocol)
    _set_param(item, 'port', port)
    _set_param(item, 'request_path', path)
    _set_param(item, 'interval_in_seconds', interval)
    _set_param(item, 'number_of_probes', threshold)

# Load Balancer Rule

def create_lb_rule(
        resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name,
        backend_address_pool_name, probe_name, load_distribution='default',
        floating_ip='false', idle_timeout=None, lb=None):
    from azure.mgmt.network.models import LoadBalancingRule
    return LoadBalancingRule(
        name=item_name,
        protocol=protocol,
        frontend_port=frontend_port,
        backend_port=backend_port,
        frontend_ip_configuration=_get_lb_property(lb.frontend_ip_configurations, frontend_ip_name),
        backend_address_pool=_get_lb_property(lb.backend_address_pools, backend_address_pool_name),
        probe=_get_lb_property(lb.probes, probe_name),
        load_distribution=load_distribution,
        enable_floating_ip=floating_ip == 'true',
        idle_timeout_in_minutes=idle_timeout)

def set_lb_rule(
        resource_group_name, load_balancer_name, item_name, item=None, lb=None,
        protocol=None, frontend_port=None, frontend_ip_name=None, backend_port=None,
        load_distribution='default', floating_ip=None, idle_timeout=None):
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

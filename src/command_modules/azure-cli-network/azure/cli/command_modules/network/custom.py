# pylint: disable=no-self-use,too-many-arguments
from azure.mgmt.network.models import Subnet, SecurityRule

from azure.cli._util import CLIError
from ._factory import _network_client_factory

def create_update_subnet(resource_group_name, subnet_name, virtual_network_name, address_prefix):
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

# Load Balancer Probes

def list_lb_probes(resource_group_name, load_balancer_name):
    ''' List probes associated with the specified load balancer. '''
    return _network_client_factory().load_balancers.get(
        resource_group_name, load_balancer_name).probes

def get_lb_probe(resource_group_name, load_balancer_name, probe_name):
    ''' Get a probe associated with the specified load balancer. '''
    probes = _network_client_factory().load_balancers.get(
        resource_group_name, load_balancer_name).probes
    try:
        return next(x for x in probes if x.name.lower() == probe_name.lower())
    except StopIteration:
        raise CLIError("Probe '{}' does not exist on load balancer '{}'".format(
            probe_name, load_balancer_name))

def remove_lb_probe(resource_group_name, load_balancer_name, probe_name):
    ''' Remove a probe from the specified load balancer. '''
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    keep_probes = [x for x in lb.probes if x.name.lower() != probe_name.lower()]
    lb.probes = keep_probes
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def add_lb_probe(resource_group_name, load_balancer_name, probe_name, protocol='http', port=80,
                 path=None, interval=5, threshold=2):
    ''' Add a probe to the specified load balancer. '''
    from azure.mgmt.network.models import Probe
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    probe = Probe(protocol, port, interval_in_seconds=interval, number_of_probes=threshold,
                  request_path=path, name=probe_name)
    lb.probes.append(probe)
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def update_lb_probe(resource_group_name, load_balancer_name, probe_name, protocol=None, port=None,
                    path=None, interval=None, threshold=None):
    ''' Update a parameter on an existing load balancer probe. '''
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    try:
        probe = next(x for x in lb.probes if x.name.lower() == probe_name.lower())
    except StopIteration:
        raise CLIError("Probe '{}' does not exist on load balancer '{}'".format(
            probe_name, load_balancer_name))

    if protocol:
        probe.protcol = protocol
    if port:
        probe.port = port
    if path:
        probe.request_path = path
    if interval:
        probe.interval_in_seconds = interval
    if threshold:
        probe.number_of_probes = threshold
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

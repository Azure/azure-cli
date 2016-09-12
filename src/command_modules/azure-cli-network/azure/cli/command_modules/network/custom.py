#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from collections import Counter
from itertools import groupby
from msrestazure.azure_exceptions import CloudError

# pylint: disable=no-self-use,too-many-arguments,no-member,too-many-lines
from azure.mgmt.network.models import \
    (Subnet, SecurityRule, PublicIPAddress, NetworkSecurityGroup, InboundNatRule, InboundNatPool,
     FrontendIPConfiguration, BackendAddressPool, Probe, LoadBalancingRule,
     NetworkInterfaceIPConfiguration, Route, VpnClientRootCertificate, VpnClientConfiguration,
     AddressSpace, VpnClientRevokedCertificate, ExpressRouteCircuitAuthorization, SubResource,
     VirtualNetworkPeering)

from azure.cli.core.commands.arm import parse_resource_id, is_valid_resource_id, resource_id
from azure.cli.core._util import CLIError
from azure.cli.command_modules.network._factory import _network_client_factory
from azure.cli.command_modules.network.mgmt_app_gateway.lib.operations.app_gateway_operations \
    import AppGatewayOperations

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from ._factory import _network_client_factory
from azure.cli.command_modules.network.mgmt_nic.lib.operations.nic_operations import NicOperations
from azure.mgmt.trafficmanager import TrafficManagerManagementClient
from azure.mgmt.trafficmanager.models import Endpoint
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.dns.models import (RecordSet, AaaaRecord, ARecord, CnameRecord, MxRecord,
                                   NsRecord, PtrRecord, SoaRecord, SrvRecord, TxtRecord, Zone)

from azure.cli.command_modules.network.zone_file.parse_zone_file import parse_zone_file
from azure.cli.command_modules.network.zone_file.make_zone_file import make_zone_file

#region Network subresource factory methods

def list_network_resource_property(resource, prop):
    """ Factory method for creating list functions. """
    def list_func(resource_group_name, resource_name):
        client = getattr(_network_client_factory(), resource)
        return client.get(resource_group_name, resource_name).__getattribute__(prop)
    return list_func

def get_network_resource_property_entry(resource, prop):
    """ Factory method for creating get functions. """
    def get_func(resource_group_name, resource_name, item_name):
        client = getattr(_network_client_factory(), resource)
        items = getattr(client.get(resource_group_name, resource_name), prop)

        result = next((x for x in items if x.name.lower() == item_name.lower()), None)
        if not result:
            raise CLIError("Item '{}' does not exist on {} '{}'".format(
                item_name, resource, resource_name))
        else:
            return result
    return get_func

def delete_network_resource_property_entry(resource, prop):
    """ Factory method for creating delete functions. """
    def delete_func(resource_group_name, resource_name, item_name):
        client = getattr(_network_client_factory(), resource)
        item = client.get(resource_group_name, resource_name)
        keep_items = \
            [x for x in item.__getattribute__(prop) if x.name.lower() != item_name.lower()]
        _set_param(item, prop, keep_items)
        return client.create_or_update(resource_group_name, resource_name, item)
    return delete_func

def _get_property(items, name):
    result = next((x for x in items if x.name.lower() == name.lower()), None)
    if not result:
        raise CLIError("Property '{}' does not exist".format(name))
    else:
        return result

def _set_param(item, prop, value):
    if value == '':
        setattr(item, prop, None)
    elif value is not None:
        setattr(item, prop, value)
#endregion

#region Generic list commands
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

#endregion

#region Application Gateway subresource commands

def create_ag_address_pool(resource_group_name, application_gateway_name, item_name, servers):
    from azure.mgmt.network.models import ApplicationGatewayBackendAddressPool
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.backend_address_pools.append(ApplicationGatewayBackendAddressPool(
        name=item_name, backend_addresses=servers))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)
create_ag_address_pool.__doc__ = AppGatewayOperations.create_or_update.__doc__

def create_ag_frontend_ip(resource_group_name, application_gateway_name, item_name,
                          public_ip_address=None, subnet=None, virtual_network_name=None, # pylint: disable=unused-argument
                          private_ip_address=None, private_ip_address_allocation=None): # pylint: disable=unused-argument
    from azure.mgmt.network.models import ApplicationGatewayFrontendIPConfiguration
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.frontend_ip_configurations.append(ApplicationGatewayFrontendIPConfiguration(
        name=item_name,
        private_ip_address=private_ip_address if private_ip_address else None,
        private_ip_allocation_method='static' if private_ip_address else 'dynamic',
        public_ip_address=SubResource(public_ip_address) if public_ip_address else None,
        subnet=SubResource(subnet) if subnet else None))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)
create_ag_frontend_ip.__doc__ = AppGatewayOperations.create_or_update.__doc__

def create_ag_frontend_port(resource_group_name, application_gateway_name, item_name, port):
    from azure.mgmt.network.models import ApplicationGatewayFrontendPort
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.frontend_ports.append(ApplicationGatewayFrontendPort(name=item_name, port=port))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def create_ag_http_listener(resource_group_name, application_gateway_name, item_name,
                            frontend_ip, frontend_port, ssl_cert=None):
    from azure.mgmt.network.models import ApplicationGatewayHttpListener
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.http_listeners.append(ApplicationGatewayHttpListener(
        name=item_name,
        frontend_ip_configuration=SubResource(frontend_ip),
        frontend_port=SubResource(frontend_port),
        protocol='https' if ssl_cert else 'http',
        ssl_certificate=SubResource(ssl_cert) if ssl_cert else None))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def create_ag_http_settings(resource_group_name, application_gateway_name, item_name,
                            port, probe=None, protocol='http', cookie_based_affinity=None,
                            timeout=None):
    from azure.mgmt.network.models import ApplicationGatewayBackendHttpSettings
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.backend_http_settings_collection.append(ApplicationGatewayBackendHttpSettings(
        port=port,
        protocol=protocol,
        cookie_based_affinity=cookie_based_affinity or 'Disabled',
        request_timeout=timeout,
        probe=SubResource(probe) if probe else None,
        name=item_name
    ))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def create_ag_probe(resource_group_name, application_gateway_name, item_name, protocol, host,
                    path, interval=30, timeout=120, threshold=8):
    from azure.mgmt.network.models import ApplicationGatewayProbe
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.probes.append(ApplicationGatewayProbe(
        name=item_name,
        protocol=protocol,
        host=host,
        path=path,
        interval=interval,
        timeout=timeout,
        unhealthy_threshold=threshold
    ))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def create_ag_rule(resource_group_name, application_gateway_name, item_name,
                   address_pool, http_settings, http_listener, url_path_map=None,
                   rule_type='Basic'):
    from azure.mgmt.network.models import ApplicationGatewayRequestRoutingRule
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.request_routing_rules.append(ApplicationGatewayRequestRoutingRule(
        name=item_name,
        rule_type=rule_type,
        backend_address_pool=SubResource(address_pool),
        backend_http_settings=SubResource(http_settings),
        http_listener=SubResource(http_listener),
        url_path_map=SubResource(url_path_map) if url_path_map else None
    ))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def create_ag_ssl_cert(resource_group_name, application_gateway_name, item_name, cert_data,
                       cert_password):
    from azure.mgmt.network.models import ApplicationGatewaySslCertificate
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.ssl_certificates.append(ApplicationGatewaySslCertificate(
        name=item_name, data=cert_data, password=cert_password))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)
create_ag_ssl_cert.__doc__ = AppGatewayOperations.create_or_update.__doc__

def create_ag_url_path_map(resource_group_name, application_gateway_name, item_name,
                           paths, address_pool, http_settings, rule_name='default',
                           default_address_pool=None, default_http_settings=None):
    from azure.mgmt.network.models import ApplicationGatewayUrlPathMap, ApplicationGatewayPathRule
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    ag.url_path_maps.append(ApplicationGatewayUrlPathMap(
        name=item_name,
        default_backend_address_pool=SubResource(default_address_pool) \
            if default_address_pool else SubResource(address_pool),
        default_backend_http_settings=SubResource(default_http_settings) \
            if default_http_settings else SubResource(http_settings),
        path_rules=[ApplicationGatewayPathRule(
            name=rule_name,
            backend_address_pool=SubResource(address_pool),
            backend_http_settings=SubResource(http_settings),
            paths=paths
        )]
    ))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def create_ag_url_path_map_rule(resource_group_name, application_gateway_name, url_path_map_name,
                                item_name, paths, address_pool=None, http_settings=None):
    from azure.mgmt.network.models import ApplicationGatewayPathRule
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    url_map = next((x for x in ag.url_path_maps if x.name == url_path_map_name), None)
    if not url_map:
        raise CLIError('URL path map "{}" not found.'.format(url_path_map_name))
    url_map.path_rules.append(ApplicationGatewayPathRule(
        name=item_name,
        paths=paths,
        backend_address_pool=SubResource(address_pool) \
            if address_pool else SubResource(url_map.default_backend_address_pool.id),
        backend_http_settings=SubResource(http_settings) \
            if http_settings else SubResource(url_map.default_backend_http_settings.id)
    ))
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

def delete_ag_url_path_map_rule(resource_group_name, application_gateway_name, url_path_map_name,
                                item_name):
    ncf = _network_client_factory()
    ag = ncf.application_gateways.get(resource_group_name, application_gateway_name)
    url_map = next((x for x in ag.url_path_maps if x.name == url_path_map_name), None)
    if not url_map:
        raise CLIError('URL path map "{}" not found.'.format(url_path_map_name))
    url_map.path_rules = \
        [x for x in url_map.path_rules if x.name.lower() != item_name.lower()]
    return ncf.application_gateways.create_or_update(
        resource_group_name, application_gateway_name, ag)

#endregion

#region Load Balancer subresource commands

def create_lb_inbound_nat_rule(
        resource_group_name, load_balancer_name, item_name, protocol, frontend_port,
        frontend_ip_name, backend_port, floating_ip="false", idle_timeout=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    frontend_ip = _get_property(lb.frontend_ip_configurations, frontend_ip_name) # pylint: disable=no-member
    lb.inbound_nat_rules.append(
        InboundNatRule(name=item_name, protocol=protocol,
                       frontend_port=frontend_port, backend_port=backend_port,
                       frontend_ip_configuration=frontend_ip,
                       enable_floating_ip=floating_ip == 'true',
                       idle_timeout_in_minutes=idle_timeout))
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().inbound_nat_rules, item_name)

def set_lb_inbound_nat_rule(
        instance, parent, item_name, protocol=None, frontend_port=None, # pylint: disable=unused-argument
        frontend_ip_name=None, backend_port=None, floating_ip=None, idle_timeout=None):
    if frontend_ip_name:
        instance.frontend_ip_configuration = \
            _get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if floating_ip is not None:
        instance.enable_floating_ip = floating_ip == 'true'

    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'frontend_port', frontend_port)
    _set_param(instance, 'backend_port', backend_port)
    _set_param(instance, 'idle_timeout_in_minutes', idle_timeout)

    return parent

def create_lb_inbound_nat_pool(
        resource_group_name, load_balancer_name, item_name, protocol, frontend_port_range_start,
        frontend_port_range_end, backend_port, frontend_ip_name=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    frontend_ip = _get_property(lb.frontend_ip_configurations, frontend_ip_name) \
        if frontend_ip_name else None
    lb.inbound_nat_pools.append(
        InboundNatPool(name=item_name,
                       protocol=protocol,
                       frontend_ip_configuration=frontend_ip,
                       frontend_port_range_start=frontend_port_range_start,
                       frontend_port_range_end=frontend_port_range_end,
                       backend_port=backend_port))
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().inbound_nat_pools, item_name)

def set_lb_inbound_nat_pool(
        instance, parent, item_name, protocol=None, # pylint: disable=unused-argument
        frontend_port_range_start=None, frontend_port_range_end=None, backend_port=None,
        frontend_ip_name=None):
    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'frontend_port_range_start', frontend_port_range_start)
    _set_param(instance, 'frontend_port_range_end', frontend_port_range_end)
    _set_param(instance, 'backend_port', backend_port)

    if frontend_ip_name == '':
        instance.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            _get_property(parent.frontend_ip_configurations, frontend_ip_name)

    return parent

def create_lb_frontend_ip_configuration(
        resource_group_name, load_balancer_name, item_name, public_ip_address=None,
        subnet=None, virtual_network_name=None, private_ip_address=None, # pylint: disable=unused-argument
        private_ip_address_allocation='dynamic'):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.frontend_ip_configurations.append(FrontendIPConfiguration(
        name=item_name,
        private_ip_address=private_ip_address,
        private_ip_allocation_method=private_ip_address_allocation,
        public_ip_address=PublicIPAddress(public_ip_address) if public_ip_address else None,
        subnet=Subnet(subnet) if subnet else None))
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().frontend_ip_configurations, item_name)


def set_lb_frontend_ip_configuration(
        instance, parent, item_name, private_ip_address=None, # pylint: disable=unused-argument
        private_ip_address_allocation=None, public_ip_address=None, subnet=None,
        virtual_network_name=None): # pylint: disable=unused-argument
    if private_ip_address == '':
        instance.private_ip_allocation_method = private_ip_address_allocation
        instance.private_ip_address = None
    elif private_ip_address is not None:
        instance.private_ip_allocation_method = private_ip_address_allocation
        instance.private_ip_address = private_ip_address

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(public_ip_address)

    return parent

def create_lb_backend_address_pool(resource_group_name, load_balancer_name, item_name):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.backend_address_pools.append(BackendAddressPool(name=item_name))

    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def create_lb_probe(resource_group_name, load_balancer_name, item_name, protocol, port,
                    path=None, interval=None, threshold=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.probes.append(
        Probe(protocol, port, interval_in_seconds=interval, number_of_probes=threshold,
              request_path=path, name=item_name))
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().probes, item_name)

def set_lb_probe(instance, parent, item_name, protocol=None, port=None, # pylint: disable=unused-argument
                 path=None, interval=None, threshold=None):
    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'port', port)
    _set_param(instance, 'request_path', path)
    _set_param(instance, 'interval_in_seconds', interval)
    _set_param(instance, 'number_of_probes', threshold)

    return parent

def create_lb_rule(
        resource_group_name, load_balancer_name, item_name,
        protocol, frontend_port, backend_port, frontend_ip_name,
        backend_address_pool_name, probe_name=None, load_distribution='default',
        floating_ip='false', idle_timeout=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    lb.load_balancing_rules.append(
        LoadBalancingRule(
            name=item_name,
            protocol=protocol,
            frontend_port=frontend_port,
            backend_port=backend_port,
            frontend_ip_configuration=_get_property(lb.frontend_ip_configurations,
                                                    frontend_ip_name),
            backend_address_pool=_get_property(lb.backend_address_pools,
                                               backend_address_pool_name),
            probe=_get_property(lb.probes, probe_name) if probe_name else None,
            load_distribution=load_distribution,
            enable_floating_ip=floating_ip == 'true',
            idle_timeout_in_minutes=idle_timeout))
    poller = ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
    return _get_property(poller.result().load_balancing_rules, item_name)

def set_lb_rule(
        instance, parent, item_name, protocol=None, frontend_port=None, # pylint: disable=unused-argument
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution='default', floating_ip=None, idle_timeout=None):
    _set_param(instance, 'protocol', protocol)
    _set_param(instance, 'frontend_port', frontend_port)
    _set_param(instance, 'backend_port', backend_port)
    _set_param(instance, 'idle_timeout_in_minutes', idle_timeout)
    _set_param(instance, 'load_distribution', load_distribution)

    if frontend_ip_name is not None:
        instance.frontend_ip_configuration = \
            _get_property(parent.frontend_ip_configurations, frontend_ip_name)

    if floating_ip is not None:
        instance.enable_floating_ip = floating_ip == 'true'

    if backend_address_pool_name is not None:
        instance.backend_address_pool = \
            _get_property(parent.backend_address_pools, backend_address_pool_name)

    if probe_name == '':
        instance.probe = None
    elif probe_name is not None:
        instance.probe = _get_property(parent.probes, probe_name)

    return parent
#endregion

#region NIC commands

def set_nic(instance, network_security_group=None, enable_ip_forwarding=None,
            internal_dns_name_label=None):

    if enable_ip_forwarding is not None:
        instance.enable_ip_forwarding = enable_ip_forwarding == 'true'

    if network_security_group == '':
        instance.network_security_group = None
    elif network_security_group is not None:
        instance.network_security_group = NetworkSecurityGroup(network_security_group)

    if internal_dns_name_label == '':
        instance.dns_settings.internal_dns_name_label = None
    elif internal_dns_name_label is not None:
        instance.dns_settings.internal_dns_name_label = internal_dns_name_label

    return instance
set_nic.__doc__ = NicOperations.create_or_update.__doc__

def create_nic_ip_config(resource_group_name, network_interface_name, ip_config_name, subnet=None,
                         virtual_network_name=None, public_ip_address=None, load_balancer_name=None, # pylint: disable=unused-argument
                         load_balancer_backend_address_pool_ids=None,
                         load_balancer_inbound_nat_rule_ids=None,
                         private_ip_address=None, private_ip_address_allocation='dynamic',
                         private_ip_address_version='ipv4'):
    ncf = _network_client_factory()
    nic = ncf.network_interfaces.get(resource_group_name, network_interface_name)
    nic.ip_configurations.append(
        NetworkInterfaceIPConfiguration(
            name=ip_config_name,
            subnet=Subnet(subnet) if subnet else None,
            public_ip_address=PublicIPAddress(public_ip_address) if public_ip_address else None,
            load_balancer_backend_address_pools=load_balancer_backend_address_pool_ids,
            load_balancer_inbound_nat_rules=load_balancer_inbound_nat_rule_ids,
            private_ip_address=private_ip_address,
            private_ip_allocation_method=private_ip_address_allocation,
            private_ip_address_version=private_ip_address_version
        )
    )
    return ncf.network_interfaces.create_or_update(
        resource_group_name, network_interface_name, nic)
create_nic_ip_config.__doc__ = NicOperations.create_or_update.__doc__

def set_nic_ip_config(instance, parent, ip_config_name, subnet=None, # pylint: disable=unused-argument
                      virtual_network_name=None, public_ip_address=None, load_balancer_name=None, # pylint: disable=unused-argument
                      load_balancer_backend_address_pool_ids=None,
                      load_balancer_inbound_nat_rule_ids=None,
                      private_ip_address=None, private_ip_address_allocation=None, # pylint: disable=unused-argument
                      private_ip_address_version='ipv4'):
    if private_ip_address == '':
        instance.private_ip_address = None
        instance.private_ip_allocation_method = 'dynamic'
        instance.private_ip_address_version = 'ipv4'
    elif private_ip_address is not None:
        instance.private_ip_address = private_ip_address
        instance.private_ip_allocation_method = 'static'
        if private_ip_address_version is not None:
            instance.private_ip_address_version = private_ip_address_version

    if subnet == '':
        instance.subnet = None
    elif subnet is not None:
        instance.subnet = Subnet(subnet)

    if public_ip_address == '':
        instance.public_ip_address = None
    elif public_ip_address is not None:
        instance.public_ip_address = PublicIPAddress(public_ip_address)

    if load_balancer_backend_address_pool_ids == '':
        instance.load_balancer_backend_address_pools = None
    elif load_balancer_backend_address_pool_ids is not None:
        instance.load_balancer_backend_address_pools = load_balancer_backend_address_pool_ids

    if load_balancer_inbound_nat_rule_ids == '':
        instance.load_balancer_inbound_nat_rules = None
    elif load_balancer_inbound_nat_rule_ids is not None:
        instance.load_balancer_inbound_nat_rules = load_balancer_inbound_nat_rule_ids

    return parent
set_nic_ip_config.__doc__ = NicOperations.create_or_update.__doc__

def add_nic_ip_config_address_pool(
        resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None): # pylint: disable=unused-argument
    client = _network_client_factory().network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = next(
        (x for x in nic.ip_configurations if x.name.lower() == ip_config_name.lower()), None)
    try:
        ip_config.load_balancer_backend_address_pools.append(
            BackendAddressPool(backend_address_pool))
    except AttributeError:
        ip_config.load_balancer_backend_address_pools = [BackendAddressPool(backend_address_pool)]
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return _get_property(poller.result().ip_configurations, ip_config_name)

def remove_nic_ip_config_address_pool(
        resource_group_name, network_interface_name, ip_config_name, backend_address_pool,
        load_balancer_name=None): # pylint: disable=unused-argument
    client = _network_client_factory().network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = next(
        (x for x in nic.ip_configurations if x.name.lower() == ip_config_name.lower()), None)
    if not ip_config:
        raise CLIError('IP configuration {} not found.'.format(ip_config_name))
    keep_items = \
        [x for x in ip_config.load_balancer_backend_address_pools or [] \
            if x.id != backend_address_pool]
    ip_config.load_balancer_backend_address_pools = keep_items
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return  _get_property(poller.result().ip_configurations, ip_config_name)

def add_nic_ip_config_inbound_nat_rule(
        resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None): # pylint: disable=unused-argument
    client = _network_client_factory().network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = next(
        (x for x in nic.ip_configurations if x.name.lower() == ip_config_name.lower()), None)
    try:
        ip_config.load_balancer_inbound_nat_rules.append(InboundNatRule(inbound_nat_rule))
    except AttributeError:
        ip_config.load_balancer_inbound_nat_rules = [InboundNatRule(inbound_nat_rule)]
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return  _get_property(poller.result().ip_configurations, ip_config_name)

def remove_nic_ip_config_inbound_nat_rule(
        resource_group_name, network_interface_name, ip_config_name, inbound_nat_rule,
        load_balancer_name=None): # pylint: disable=unused-argument
    client = _network_client_factory().network_interfaces
    nic = client.get(resource_group_name, network_interface_name)
    ip_config = next(
        (x for x in nic.ip_configurations or [] if x.name.lower() == ip_config_name.lower()), None)
    if not ip_config:
        raise CLIError('IP configuration {} not found.'.format(ip_config_name))
    keep_items = \
        [x for x in ip_config.load_balancer_inbound_nat_rules if x.id != inbound_nat_rule]
    ip_config.load_balancer_inbound_nat_rules = keep_items
    poller = client.create_or_update(resource_group_name, network_interface_name, nic)
    return  _get_property(poller.result().ip_configurations, ip_config_name)
#endregion

#region Network Security Group commands

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

def update_nsg_rule(instance, protocol=None, source_address_prefix=None,
                    destination_address_prefix=None, access=None, direction=None, description=None,
                    source_port_range=None, destination_port_range=None, priority=None):
    #No client validation as server side returns pretty good errors
    instance.protocol = protocol if protocol is not None else instance.protocol
    #pylint: disable=line-too-long
    instance.source_address_prefix = (source_address_prefix if source_address_prefix is not None \
        else instance.source_address_prefix)
    instance.destination_address_prefix = destination_address_prefix \
        if destination_address_prefix is not None else instance.destination_address_prefix
    instance.access = access if access is not None else instance.access
    instance.direction = direction if direction is not None else instance.direction
    instance.description = description if description is not None else instance.description
    instance.source_port_range = source_port_range \
        if source_port_range is not None else instance.source_port_range
    instance.destination_port_range = destination_port_range \
        if destination_port_range is not None else instance.destination_port_range
    instance.priority = priority if priority is not None else instance.priority
    return instance
update_nsg_rule.__doc__ = SecurityRule.__doc__
#endregion

#region Vnet Peering commands

def create_vnet_peering(resource_group_name, virtual_network_name, virtual_network_peering_name,
                        remote_virtual_network, allow_virtual_network_access=False,
                        allow_forwarded_traffic=False, allow_gateway_transit=False,
                        use_remote_gateways=False):
    from azure.cli.core.commands.client_factory import get_subscription_id
    peering = VirtualNetworkPeering(
        id=resource_id(
            subscription=get_subscription_id(),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=virtual_network_name),
        name=virtual_network_peering_name,
        remote_virtual_network=SubResource(remote_virtual_network),
        allow_virtual_network_access=allow_virtual_network_access,
        allow_gateway_transit=allow_gateway_transit,
        allow_forwarded_traffic=allow_forwarded_traffic,
        use_remote_gateways=use_remote_gateways)
    ncf = _network_client_factory()
    return ncf.virtual_network_peerings.create_or_update(
        resource_group_name, virtual_network_name, virtual_network_peering_name, peering)
create_vnet_peering.__doc__ = VirtualNetworkPeering.__doc__
#endregion

#region Vnet/Subnet commands

def update_vnet(instance, address_prefixes=None):
    '''update existing virtual network
    :param address_prefixes: update address spaces. Use space separated address prefixes,
        for example, "10.0.0.0/24 10.0.1.0/24"
    '''
    #server side validation reports pretty good error message on invalid CIDR,
    #so we don't validate at client side
    if address_prefixes:
        instance.address_space.address_prefixes = address_prefixes
    return instance

def _set_route_table(ncf, resource_group_name, route_table, subnet):
    if route_table:
        is_id = is_valid_resource_id(route_table)
        rt = None
        if is_id:
            res_id = parse_resource_id(route_table)
            rt = ncf.route_tables.get(res_id['resource_group'], res_id['name'])
        else:
            rt = ncf.route_tables.get(resource_group_name, route_table)
        subnet.route_table = rt
    elif route_table == '':
        subnet.route_table = None

def create_subnet(resource_group_name, virtual_network_name, subnet_name,
                  address_prefix='10.0.0.0/24', network_security_group=None,
                  route_table=None):
    '''Create a virtual network (VNet) subnet
    :param str address_prefix: address prefix in CIDR format.
    :param str network_security_group: Name or ID of network security
        group to associate with the subnet.
    '''
    ncf = _network_client_factory()
    subnet = Subnet(name=subnet_name, address_prefix=address_prefix)
    subnet.address_prefix = address_prefix

    if network_security_group:
        subnet.network_security_group = NetworkSecurityGroup(network_security_group)
    _set_route_table(ncf, resource_group_name, route_table, subnet)

    return ncf.subnets.create_or_update(resource_group_name, virtual_network_name,
                                        subnet_name, subnet)

def update_subnet(instance, resource_group_name, address_prefix=None, network_security_group=None,
                  route_table=None):
    '''update existing virtual sub network
    :param str address_prefix: New address prefix in CIDR format, for example 10.0.0.0/24.
    :param str network_security_group: attach with existing network security group,
        both name or id are accepted. Use empty string "" to detach it.
    '''
    if address_prefix:
        instance.address_prefix = address_prefix

    if network_security_group:
        instance.network_security_group = NetworkSecurityGroup(network_security_group)
    elif network_security_group == '': #clear it
        instance.network_security_group = None

    _set_route_table(_network_client_factory(), resource_group_name, route_table, instance)

    return instance
update_nsg_rule.__doc__ = SecurityRule.__doc__

def delete_vpn_gateway_root_cert(resource_group_name, gateway_name, cert_name):
    ncf = _network_client_factory().virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_root_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_root_certificates.remove(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)

def create_vpn_gateway_revoked_cert(resource_group_name, gateway_name, thumbprint, cert_name):
    config, gateway, ncf = _prep_cert_create(gateway_name, resource_group_name)

    cert = VpnClientRevokedCertificate(name=cert_name, thumbprint=thumbprint)
    config.vpn_client_revoked_certificates.append(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)

def delete_vpn_gateway_revoked_cert(resource_group_name, gateway_name, cert_name):
    ncf = _network_client_factory().virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    config = gateway.vpn_client_configuration

    try:
        cert = next(c for c in config.vpn_client_revoked_certificates if c.name == cert_name)
    except (AttributeError, StopIteration):
        raise CLIError('Certificate "{}" not found in gateway "{}"'.format(cert_name, gateway_name))
    config.vpn_client_revoked_certificates.remove(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)

def _prep_cert_create(gateway_name, resource_group_name):
    ncf = _network_client_factory().virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    if not gateway.vpn_client_configuration:
        gateway.vpn_client_configuration = VpnClientConfiguration()
    config = gateway.vpn_client_configuration

    if not config.vpn_client_address_pool or not config.vpn_client_address_pool.address_prefixes:
        raise CLIError('Address prefixes must be set on VPN gateways before adding'
                       ' certificates.  Please use "update" with --address-prefixes first.')

    if config.vpn_client_revoked_certificates is None:
        config.vpn_client_revoked_certificates = []
    if config.vpn_client_root_certificates is None:
        config.vpn_client_root_certificates = []

    return config, gateway, ncf

def update_network_vpn_gateway(instance, address_prefixes=None):
    if address_prefixes:
        gateway = instance
        if not gateway.vpn_client_configuration:
            gateway.vpn_client_configuration = VpnClientConfiguration()
        config = gateway.vpn_client_configuration

        if not config.vpn_client_address_pool:
            config.vpn_client_address_pool = AddressSpace()
        if not config.vpn_client_address_pool.address_prefixes:
            config.vpn_client_address_pool.address_prefixes = []

        config.vpn_client_address_pool.address_prefixes = address_prefixes

def create_express_route_auth(resource_group_name, circuit_name, authorization_name,
                              authorization_key):
    ncf = _network_client_factory().express_route_circuit_authorizations
    auth = ExpressRouteCircuitAuthorization(authorization_key=authorization_key)
    return ncf.create_or_update(resource_group_name, circuit_name, authorization_name, auth)

def create_route(resource_group_name, route_table_name, route_name, next_hop_type, address_prefix,
                 next_hop_ip_address=None):
    route = Route(next_hop_type, None, address_prefix, next_hop_ip_address, None, route_name)
    ncf = _network_client_factory()
    return ncf.routes.create_or_update(resource_group_name, route_table_name, route_name, route)

create_route.__doc__ = Route.__doc__

def create_vpn_gateway_root_cert(resource_group_name, gateway_name, public_cert_data, cert_name):
    ncf = _network_client_factory().virtual_network_gateways
    gateway = ncf.get(resource_group_name, gateway_name)
    if not gateway.vpn_client_configuration:
        gateway.vpn_client_configuration = VpnClientConfiguration()
    config = gateway.vpn_client_configuration

    if config.vpn_client_root_certificates is None:
        config.vpn_client_root_certificates = []

    cert = VpnClientRootCertificate(name=cert_name, public_cert_data=public_cert_data)
    config.vpn_client_root_certificates.append(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)
#endregion

#region Traffic Manager Commands
def list_traffic_manager_profiles(resource_group_name=None):
    ncf = get_mgmt_service_client(TrafficManagerManagementClient).profiles
    if resource_group_name:
        return ncf.list_all_in_resource_group(resource_group_name)
    else:
        return ncf.list_all()

def create_traffic_manager_endpoint(resource_group_name, profile_name, endpoint_type, endpoint_name,
                                    target_resource_id=None, target=None,
                                    endpoint_status=None, weight=None, priority=None,
                                    endpoint_location=None, endpoint_monitor_status=None,
                                    min_child_endpoints=None):
    ncf = get_mgmt_service_client(TrafficManagerManagementClient).endpoints

    endpoint = Endpoint(target_resource_id=target_resource_id, target=target,
                        endpoint_status=endpoint_status, weight=weight, priority=priority,
                        endpoint_location=endpoint_location,
                        endpoint_monitor_status=endpoint_monitor_status,
                        min_child_endpoints=min_child_endpoints)

    return ncf.create_or_update(resource_group_name, profile_name, endpoint_type, endpoint_name,
                                endpoint)

create_traffic_manager_endpoint.__doc__ = Endpoint.__doc__

def list_traffic_manager_endpoints(resource_group_name, profile_name, endpoint_type=None):
    ncf = get_mgmt_service_client(TrafficManagerManagementClient).profiles
    profile = ncf.get(resource_group_name, profile_name)
    return [e for e in profile.endpoints if not endpoint_type or e.type.endswith(endpoint_type)]
#endregion

#region DNS Commands
def list_dns_zones(resource_group_name=None):
    ncf = get_mgmt_service_client(DnsManagementClient).zones
    if resource_group_name:
        return ncf.list_in_resource_group(resource_group_name)
    else:
        return ncf.list_in_subscription()

def create_dns_record_set(resource_group_name, zone_name, record_set_name, record_set_type,
                          ttl=None):
    ncf = get_mgmt_service_client(DnsManagementClient).record_sets
    record_set = RecordSet(name=record_set_name, type=record_set_type, ttl=ttl)
    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_set_type, record_set)

def export_zone(resource_group_name, zone_name, file_name):
    client = get_mgmt_service_client(DnsManagementClient)
    record_sets = client.record_sets.list_all_in_resource_group(resource_group_name, zone_name)

    record_property_types = {
        'arecords': 'a',
        'aaaa_records': 'aaaa',
        'cname_record': 'cname',
        'mx_records': 'mx',
        'ns_records': 'ns',
        'ptr_records': 'ptr',
        'soa_record': 'soa',
        'srv_records': 'srv',
        'txt_records': 'txt'
        }

    zone_obj = {
        '$origin': zone_name.rstrip('.') + '.'
        }

    for record_set in record_sets:
        for property_name, record_type in record_property_types.items():
            record_data = getattr(record_set, property_name, None)
            if not record_data:
                continue
            if not isinstance(record_data, list):
                record_data = [record_data]
            if record_type not in zone_obj:
                zone_obj[record_type] = []
            for record in record_data:
                record_obj = {'ip': record.ipv6_address} if record_type == 'aaaa' \
                    else {'ip': record.ipv4_address} if record_type == 'a' \
                    else {'alias': record.cname} if record_type == 'cname' \
                    else {'preference': record.preference, 'host': record.exchange} \
                    if record_type == 'mx' \
                    else {'host': record.nsdname} if record_type == 'ns' \
                    else {'host': record.ptrdname} if record_type == 'ptr' \
                    else {'mname': record.host, 'rname': record.email,
                          'serial': record.serial_number, 'refresh': record.refresh_time,
                          'retry': record.retry_time, 'expire': record.expire_time,
                          'minimum': record.minimum_ttl} if record_type == 'soa' \
                    else {'priority': record.priority, 'weight': record.weight,
                          'port': record.port, 'target': record.target} if record_type == 'srv' \
                    else {'txt': ' '.join(record.value)} if record_type == 'txt' \
                    else None
                record_obj['name'] = record_set.name
                record_obj['ttl'] = record_set.ttl
                zone_obj[record_type].append(record_obj)

    if 'soa' in zone_obj:
        # there is only 1 soa record allowed, so it shouldn't be a list, take the first element
        zone_obj['soa'] = zone_obj['soa'][0]
        zone_obj['soa']['mname'] = zone_obj['soa']['mname'].rstrip('.') + '.'
        zone_obj['soa']['rname'] = zone_obj['soa']['rname'].rstrip('.') + '.'

    zone_file_text = make_zone_file(zone_obj)

    with open(file_name, 'w') as f:
        f.write(zone_file_text)

def import_zone(resource_group_name, zone_name, file_name, location='global'):
    file_text = None
    with open(file_name) as f:
        file_text = f.read()
    zone_obj = parse_zone_file(file_text)

    zone_origin = zone_obj['$origin'].rstrip('.')
    if zone_name != zone_origin:
        raise CLIError('Zone file origin "{}" does not match zone name "{}"'
                       .format(zone_origin, zone_name))

    client = get_mgmt_service_client(DnsManagementClient)

    try:
        if client.zones.get(resource_group_name, zone_name):
            raise CLIError('Zone "{}" already exists'.format(zone_name))
    except CloudError:
        pass

    zone = Zone(location)
    client.zones.create_or_update(resource_group_name, zone_name, zone)

    for record_type in [k for k in zone_obj if not k.startswith('$')]:
        key_func = lambda x: x['name']
        for name, group in groupby(sorted(zone_obj[record_type], key=key_func), key_func):
            record_set = RecordSet(name=name, type=record_type, ttl=3600)
            for record_obj in list(group):
                record = None
                try:
                    record = AaaaRecord(record_obj['ip']) if record_type == 'aaaa' \
                        else ARecord(record_obj['ip']) if record_type == 'a' \
                        else CnameRecord(record_obj['alias']) if record_type == 'cname' \
                        else MxRecord(record_obj['preference'],
                                      record_obj['host']) if record_type == 'mx' \
                        else NsRecord(record_obj['host']) if record_type == 'ns' \
                        else PtrRecord(record_obj['host']) if record_type == 'ptr' \
                        else SoaRecord(record_obj['mname'], record_obj['rname'],
                                       record_obj['serial'], record_obj['refresh'],
                                       record_obj['retry'], record_obj['expire'],
                                       record_obj['minimum']) if record_type == 'soa' \
                        else SrvRecord(record_obj['priority'], record_obj['weight'],
                                       record_obj['port'],
                                       record_obj['target']) if record_type == 'srv' \
                        else TxtRecord([record_obj['txt']]) if record_type == 'txt' \
                        else None
                except KeyError as ke:
                    raise CLIError('The {} record "{}" is missing a property.  {}'
                                   .format(record_type, record_obj, ke))

                if not record:
                    raise CLIError('Record type "{}" is not supported'.format(record_type))

                record_set.ttl = record_obj['ttl']

                _add_record(record_set, record, record_type,
                            is_list=record_type != 'soa' and record_type != 'cname',
                            property_name='arecords' if record_type == 'a' else None)

            # skip built-in records because they can't be predicted or changed
            if (record_type == 'soa' and name == '@') \
                or (record_type == 'ns' and name == '@'):
                continue

            client.record_sets.create_or_update(resource_group_name, zone_name, record_set.name,
                                                record_type, record_set)

def add_dns_aaaa_record(resource_group_name, zone_name, record_set_name, ipv6_address):
    record = AaaaRecord(ipv6_address)
    record_type = 'aaaa'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name)

def add_dns_a_record(resource_group_name, zone_name, record_set_name, ipv4_address):
    record = ARecord(ipv4_address)
    record_type = 'a'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name,
                            'arecords')

def add_dns_cname_record(resource_group_name, zone_name, record_set_name, cname):
    record = CnameRecord(cname)
    record_type = 'cname'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False)

def add_dns_mx_record(resource_group_name, zone_name, record_set_name, preference, exchange):
    record = MxRecord(int(preference), exchange)
    record_type = 'mx'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name)

def add_dns_ns_record(resource_group_name, zone_name, record_set_name, dname):
    record = NsRecord(dname)
    record_type = 'ns'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name)

def add_dns_ptr_record(resource_group_name, zone_name, record_set_name, dname):
    record = PtrRecord(dname)
    record_type = 'ptr'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name)

def update_dns_soa_record(resource_group_name, zone_name, email=None,
                          serial_number=None, refresh_time=None, retry_time=None, expire_time=None,
                          minimum_ttl=None):
    record_set_name = '@'
    record_type = 'soa'

    ncf = get_mgmt_service_client(DnsManagementClient).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)
    record = record_set.soa_record

    record.email = email or record.email
    record.serial_number = serial_number or record.serial_number
    record.refresh_time = refresh_time or record.refresh_time
    record.retry_time = retry_time or record.retry_time
    record.expire_time = expire_time or record.expire_time
    record.minimum_ttl = minimum_ttl or record.minimum_ttl

    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name,
                            is_list=False)

def add_dns_srv_record(resource_group_name, zone_name, record_set_name, priority, weight,
                       port, target):
    record = SrvRecord(priority, weight, port, target)
    record_type = 'srv'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name)

def add_dns_txt_record(resource_group_name, zone_name, record_set_name, value):
    record = TxtRecord(value)
    record_type = 'txt'
    return _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name)

def remove_dns_aaaa_record(resource_group_name, zone_name, record_set_name, ipv6_address):
    record = AaaaRecord(ipv6_address)
    record_type = 'aaaa'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name)

def remove_dns_a_record(resource_group_name, zone_name, record_set_name, ipv4_address):
    record = ARecord(ipv4_address)
    record_type = 'a'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name,
                          'arecords')

def remove_dns_cname_record(resource_group_name, zone_name, record_set_name, cname):
    record = CnameRecord(cname)
    record_type = 'cname'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False)

def remove_dns_mx_record(resource_group_name, zone_name, record_set_name, preference, exchange):
    record = MxRecord(int(preference), exchange)
    record_type = 'mx'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name)

def remove_dns_ns_record(resource_group_name, zone_name, record_set_name, dname):
    record = NsRecord(dname)
    record_type = 'ns'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name)

def remove_dns_ptr_record(resource_group_name, zone_name, record_set_name, dname):
    record = PtrRecord(dname)
    record_type = 'ptr'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name)

def remove_dns_soa_record(resource_group_name, zone_name, record_set_name, host, email,
                          serial_number, refresh_time, retry_time, expire_time, minimum_ttl):
    record = SoaRecord(host, email, serial_number, refresh_time, retry_time, expire_time,
                       minimum_ttl)
    record_type = 'soa'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name,
                          is_list=False)

def remove_dns_srv_record(resource_group_name, zone_name, record_set_name, priority, weight,
                          port, target):
    record = SrvRecord(priority, weight, port, target)
    record_type = 'srv'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name)

def remove_dns_txt_record(resource_group_name, zone_name, record_set_name, value):
    record = TxtRecord(value)
    record_type = 'txt'
    return _remove_record(record, record_type, record_set_name, resource_group_name, zone_name)

def _add_record(record_set, record, record_type, property_name=None, is_list=False):
    record_property = property_name or (record_type + '_record' + ('s' if is_list else ''))

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is None:
            setattr(record_set, record_property, [])
            record_list = getattr(record_set, record_property)
        record_list.append(record)
    else:
        setattr(record_set, record_property, record)

def _add_save_record(record, record_type, record_set_name, resource_group_name, zone_name,
                     property_name=None, is_list=True):
    ncf = get_mgmt_service_client(DnsManagementClient).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)

    _add_record(record_set, record, record_type, property_name, is_list)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_type, record_set)

def _remove_record(record, record_type, record_set_name, resource_group_name, zone_name,
                   property_name=None, is_list=True):
    ncf = get_mgmt_service_client(DnsManagementClient).record_sets
    record_set = ncf.get(resource_group_name, zone_name, record_set_name, record_type)

    record_property = property_name or (record_type + '_record' + ('s' if is_list else ''))

    if is_list:
        record_list = getattr(record_set, record_property)
        if record_list is not None:
            keep_list = [r for r in record_list
                         if not dict_matches_filter(r.__dict__, record.__dict__)]
            if len(keep_list) == len(record_list):
                raise CLIError('Record {} not found.'.format(str(record)))
            setattr(record_set, record_property, keep_list)
    else:
        setattr(record_set, record_property, None)

    return ncf.create_or_update(resource_group_name, zone_name, record_set_name,
                                record_type, record_set)

def dict_matches_filter(d, filter_dict):
    sentinel = object()
    return all(filter_dict.get(key, None) is None
               or str(filter_dict[key]) == str(d.get(key, sentinel))
               or lists_match(filter_dict[key], d.get(key, []))
               for key in filter_dict)

def lists_match(l1, l2):
    return Counter(l1) == Counter(l2)
#endregion

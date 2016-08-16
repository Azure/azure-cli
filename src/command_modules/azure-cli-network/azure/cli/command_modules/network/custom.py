#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=no-self-use,too-many-arguments,no-member
from azure.mgmt.network.models import \
    (Subnet, SecurityRule, PublicIPAddress, NetworkSecurityGroup, InboundNatRule, InboundNatPool,
     FrontendIPConfiguration, BackendAddressPool, Probe, LoadBalancingRule,
     NetworkInterfaceIPConfiguration, Route, VpnClientRootCertificate, VpnClientConfiguration,
     AddressSpace, VpnClientRevokedCertificate, ExpressRouteCircuitAuthorization, SubResource)

from azure.cli._util import CLIError
from azure.cli.command_modules.network._factory import _network_client_factory
from azure.cli.command_modules.network.mgmt_app_gateway.lib.operations.app_gateway_operations \
    import AppGatewayOperations

from ._factory import _network_client_factory
from azure.cli.command_modules.network.mgmt_nic.lib.operations.nic_operations import NicOperations

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
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_inbound_nat_rule(
        resource_group_name, load_balancer_name, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, floating_ip=None, idle_timeout=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_property(lb.inbound_nat_rules, item_name)

    if frontend_ip_name:
        item.frontend_ip_configuration = \
            _get_property(lb.frontend_ip_configurations, frontend_ip_name)

    if floating_ip is not None:
        item.enable_floating_ip = floating_ip == 'true'

    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port', frontend_port)
    _set_param(item, 'backend_port', backend_port)
    _set_param(item, 'idle_timeout_in_minutes', idle_timeout)

    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

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
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_inbound_nat_pool(
        resource_group_name, load_balancer_name, item_name, protocol=None,
        frontend_port_range_start=None, frontend_port_range_end=None, backend_port=None,
        frontend_ip_name=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_property(lb.inbound_nat_pools, item_name)

    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port_range_start', frontend_port_range_start)
    _set_param(item, 'frontend_port_range_end', frontend_port_range_end)
    _set_param(item, 'backend_port', backend_port)

    if frontend_ip_name == '':
        item.frontend_ip_configuration = None
    elif frontend_ip_name is not None:
        item.frontend_ip_configuration = \
            _get_property(lb.frontend_ip_configurations, frontend_ip_name)

    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

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
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_frontend_ip_configuration(
        resource_group_name, load_balancer_name, item_name, private_ip_address=None,
        private_ip_address_allocation=None, public_ip_address=None, subnet=None,
        virtual_network_name=None): # pylint: disable=unused-argument
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_property(lb.frontend_ip_configurations, item_name)

    if private_ip_address == '':
        item.private_ip_allocation_method = private_ip_address_allocation
        item.private_ip_address = None
    elif private_ip_address is not None:
        item.private_ip_allocation_method = private_ip_address_allocation
        item.private_ip_address = private_ip_address

    if subnet == '':
        item.subnet = None
    elif subnet is not None:
        item.subnet = Subnet(subnet)

    if public_ip_address == '':
        item.public_ip_address = None
    elif public_ip_address is not None:
        item.public_ip_address = PublicIPAddress(public_ip_address)

    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

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
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_probe(resource_group_name, load_balancer_name, item_name, protocol=None, port=None,
                 path=None, interval=None, threshold=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_property(lb.probes, item_name)

    _set_param(item, 'protocol', protocol)
    _set_param(item, 'port', port)
    _set_param(item, 'request_path', path)
    _set_param(item, 'interval_in_seconds', interval)
    _set_param(item, 'number_of_probes', threshold)

    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

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
    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)

def set_lb_rule(
        resource_group_name, load_balancer_name, item_name, protocol=None, frontend_port=None,
        frontend_ip_name=None, backend_port=None, backend_address_pool_name=None, probe_name=None,
        load_distribution='default', floating_ip=None, idle_timeout=None):
    ncf = _network_client_factory()
    lb = ncf.load_balancers.get(resource_group_name, load_balancer_name)
    item = _get_property(lb.load_balancing_rules, item_name)

    _set_param(item, 'protocol', protocol)
    _set_param(item, 'frontend_port', frontend_port)
    _set_param(item, 'backend_port', backend_port)
    _set_param(item, 'idle_timeout_in_minutes', idle_timeout)
    _set_param(item, 'load_distribution', load_distribution)

    if frontend_ip_name is not None:
        item.frontend_ip_configuration = \
            _get_property(lb.frontend_ip_configurations, frontend_ip_name)

    if floating_ip is not None:
        item.enable_floating_ip = floating_ip == 'true'

    if backend_address_pool_name is not None:
        item.backend_address_pool = \
            _get_property(lb.backend_address_pools, backend_address_pool_name)

    if probe_name == '':
        item.probe = None
    elif probe_name is not None:
        item.probe = _get_property(lb.probes, probe_name)

    return ncf.load_balancers.create_or_update(resource_group_name, load_balancer_name, lb)
#endregion

#region NIC commands

def set_nic(resource_group_name, network_interface_name, network_security_group=None,
            enable_ip_forwarding=None, internal_dns_name_label=None):
    ncf = _network_client_factory()
    nic = ncf.network_interfaces.get(resource_group_name, network_interface_name)

    if enable_ip_forwarding is not None:
        nic.enable_ip_forwarding = enable_ip_forwarding == 'true'

    if network_security_group == '':
        nic.network_security_group = None
    elif network_security_group is not None:
        nic.network_security_group = NetworkSecurityGroup(network_security_group)

    if internal_dns_name_label == '':
        nic.dns_settings.internal_dns_name_label = None
    elif internal_dns_name_label is not None:
        nic.dns_settings.internal_dns_name_label = internal_dns_name_label

    return ncf.network_interfaces.create_or_update(
        resource_group_name, network_interface_name, nic)
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

def set_nic_ip_config(resource_group_name, network_interface_name, ip_config_name, subnet=None,
                      virtual_network_name=None, public_ip_address=None, load_balancer_name=None, # pylint: disable=unused-argument
                      load_balancer_backend_address_pool_ids=None,
                      load_balancer_inbound_nat_rule_ids=None,
                      private_ip_address=None, private_ip_address_allocation=None, # pylint: disable=unused-argument
                      private_ip_address_version='ipv4'):
    ncf = _network_client_factory()
    nic = ncf.network_interfaces.get(resource_group_name, network_interface_name)
    ip_config = _get_property(nic.ip_configurations, ip_config_name)

    if private_ip_address == '':
        ip_config.private_ip_address = None
        ip_config.private_ip_allocation_method = 'dynamic'
        ip_config.private_ip_address_version = 'ipv4'
    elif private_ip_address is not None:
        ip_config.private_ip_address = private_ip_address
        ip_config.private_ip_allocation_method = 'static'
        if private_ip_address_version is not None:
            ip_config.private_ip_address_version = private_ip_address_version

    if subnet == '':
        ip_config.subnet = None
    elif subnet is not None:
        ip_config.subnet = Subnet(subnet)

    if public_ip_address == '':
        ip_config.public_ip_address = None
    elif public_ip_address is not None:
        ip_config.public_ip_address = PublicIPAddress(public_ip_address)

    if load_balancer_backend_address_pool_ids == '':
        ip_config.load_balancer_backend_address_pools = None
    elif load_balancer_backend_address_pool_ids is not None:
        ip_config.load_balancer_backend_address_pools = load_balancer_backend_address_pool_ids

    if load_balancer_inbound_nat_rule_ids == '':
        ip_config.load_balancer_inbound_nat_rules = None
    elif load_balancer_inbound_nat_rule_ids is not None:
        ip_config.load_balancer_inbound_nat_rules = load_balancer_inbound_nat_rule_ids

    return ncf.network_interfaces.create_or_update(
        resource_group_name, network_interface_name, nic)
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
    return client.create_or_update(resource_group_name, network_interface_name, nic)

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
    return client.create_or_update(resource_group_name, network_interface_name, nic)

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
    return client.create_or_update(resource_group_name, network_interface_name, nic)

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
    return client.create_or_update(resource_group_name, network_interface_name, nic)

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
#endregion

#region Vnet/Subnet commands

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

update_nsg_rule.__doc__ = SecurityRule.__doc__

def create_route(resource_group_name, route_table_name, route_name, next_hop_type, address_prefix,
                 next_hop_ip_address=None):
    route = Route(next_hop_type, None, address_prefix, next_hop_ip_address, None, route_name)
    ncf = _network_client_factory()
    return ncf.routes.create_or_update(resource_group_name, route_table_name, route_name, route)

create_route.__doc__ = Route.__doc__

def create_vpn_gateway_root_cert(resource_group_name, gateway_name, public_cert_data, cert_name):
    config, gateway, ncf = _prep_cert_create(gateway_name, resource_group_name)

    cert = VpnClientRootCertificate(name=cert_name, public_cert_data=public_cert_data)
    config.vpn_client_root_certificates.append(cert)

    return ncf.create_or_update(resource_group_name, gateway_name, gateway)

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

def handle_address_prefixes(instance, _, arg_value):
    gateway = instance
    if not gateway.vpn_client_configuration:
        gateway.vpn_client_configuration = VpnClientConfiguration()
    config = gateway.vpn_client_configuration

    if not config.vpn_client_address_pool:
        config.vpn_client_address_pool = AddressSpace()
    if not config.vpn_client_address_pool.address_prefixes:
        config.vpn_client_address_pool.address_prefixes = []

    config.vpn_client_address_pool.address_prefixes = arg_value

def create_express_route_auth(resource_group_name, circuit_name, authorization_name,
                              authorization_key):
    ncf = _network_client_factory().express_route_circuit_authorizations
    auth = ExpressRouteCircuitAuthorization(authorization_key=authorization_key)
    return ncf.create_or_update(resource_group_name, circuit_name, authorization_name, auth)
#endregion

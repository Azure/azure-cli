# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict
import json


class ArmTemplateBuilder(object):
    def __init__(self):
        template = OrderedDict()
        template['$schema'] = \
            'https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#'
        template['contentVersion'] = '1.0.0.0'
        template['parameters'] = {}
        template['variables'] = {}
        template['resources'] = []
        template['outputs'] = {}
        self.template = template

    def add_resource(self, resource):
        self.template['resources'].append(resource)

    def add_variable(self, key, value):
        self.template['variables'][key] = value

    def add_parameter(self, key, value):
        self.template['parameters'][key] = value

    def add_id_output(self, key, provider, property_type, property_name):
        new_output = {
            key: {
                'type': 'string',
                'value': "[resourceId('{}/{}', '{}')]".format(
                    provider, property_type, property_name)
            }
        }
        self.template['outputs'].update(new_output)

    def add_output(self, key, property_name, provider=None, property_type=None,
                   output_type='string', path=None):

        if provider and property_type:
            template = "[reference(resourceId('{provider}/{type}', '{property}')," \
                       "providers('{provider}', '{type}').apiVersions[0])"
            value = template.format(provider=provider, type=property_type, property=property_name)
        else:
            value = "[reference('{}')".format(property_name)
        value = '{}.{}]'.format(value, path) if path else '{}]'.format(value)
        new_output = {
            key: {
                'type': output_type,
                'value': value
            }
        }
        self.template['outputs'].update(new_output)

    def build(self):
        return json.loads(json.dumps(self.template))


def _build_frontend_ip_config(name, public_ip_id=None, subnet_id=None, private_ip_address=None,
                              private_ip_allocation=None):
    frontend_ip_config = {
        'name': name
    }

    if public_ip_id:
        frontend_ip_config.update({
            'properties': {
                'publicIPAddress': {'id': public_ip_id}
            }
        })
    else:
        frontend_ip_config.update({
            'properties': {
                'privateIPAllocationMethod': private_ip_allocation,
                'privateIPAddress': private_ip_address,
                'subnet': {'id': subnet_id}
            }
        })
    return frontend_ip_config


# pylint: disable=too-many-locals
def build_application_gateway_resource(name, location, tags, sku_name, sku_tier, capacity, servers, frontend_port,
                                       private_ip_address, private_ip_allocation, cert_data, cert_password,
                                       cookie_based_affinity, http_settings_protocol, http_settings_port,
                                       http_listener_protocol, routing_rule_type, public_ip_id, subnet_id,
                                       connection_draining_timeout):
    from azure.cli.core.profiles import ResourceType, supported_api_version, get_api_version

    # set the default names
    frontend_ip_name = 'appGatewayFrontendIP'
    backend_pool_name = 'appGatewayBackendPool'
    frontend_port_name = 'appGatewayFrontendPort'
    http_listener_name = 'appGatewayHttpListener'
    http_settings_name = 'appGatewayBackendHttpSettings'
    routing_rule_name = 'rule1'
    ssl_cert_name = '{}SslCert'.format(name)

    ssl_cert = None

    frontend_ip_config = _build_frontend_ip_config(frontend_ip_name, public_ip_id, subnet_id,
                                                   private_ip_address, private_ip_allocation)
    backend_address_pool = {'name': backend_pool_name}
    if servers:
        backend_address_pool['properties'] = {'BackendAddresses': servers}

    def _ag_subresource_id(_type, name):
        return "[concat(variables('appGwID'), '/{}/{}')]".format(_type, name)

    frontend_ip_config_id = _ag_subresource_id('frontendIPConfigurations', frontend_ip_name)
    frontend_port_id = _ag_subresource_id('frontendPorts', frontend_port_name)
    http_listener_id = _ag_subresource_id('httpListeners', http_listener_name)
    backend_address_pool_id = _ag_subresource_id('backendAddressPools', backend_pool_name)
    backend_http_settings_id = _ag_subresource_id('backendHttpSettingsCollection',
                                                  http_settings_name)
    ssl_cert_id = _ag_subresource_id('sslCertificates', ssl_cert_name)

    http_listener = {
        'name': http_listener_name,
        'properties': {
            'FrontendIpConfiguration': {'Id': frontend_ip_config_id},
            'FrontendPort': {'Id': frontend_port_id},
            'Protocol': http_listener_protocol,
            'SslCertificate': None
        }
    }
    if cert_data:
        http_listener['properties'].update({'SslCertificate': {'id': ssl_cert_id}})
        ssl_cert = {
            'name': ssl_cert_name,
            'properties': {
                'data': cert_data,
                'password': cert_password
            }
        }

    backend_http_settings = {
        'name': http_settings_name,
        'properties': {
            'Port': http_settings_port,
            'Protocol': http_settings_protocol,
            'CookieBasedAffinity': cookie_based_affinity
        }
    }
    if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-12-01'):
        backend_http_settings['properties']['connectionDraining'] = {
            'enabled': bool(connection_draining_timeout),
            'drainTimeoutInSec': connection_draining_timeout if connection_draining_timeout else 1
        }

    ag_properties = {
        'backendAddressPools': [backend_address_pool],
        'backendHttpSettingsCollection': [backend_http_settings],
        'frontendIPConfigurations': [frontend_ip_config],
        'frontendPorts': [
            {
                'name': frontend_port_name,
                'properties': {
                    'Port': frontend_port
                }
            }
        ],
        'gatewayIPConfigurations': [
            {
                'name': frontend_ip_name,
                'properties': {
                    'subnet': {'id': subnet_id}
                }
            }
        ],
        'httpListeners': [http_listener],
        'sku': {
            'name': sku_name,
            'tier': sku_tier,
            'capacity': capacity
        },
        'requestRoutingRules': [
            {
                'Name': routing_rule_name,
                'properties': {
                    'RuleType': routing_rule_type,
                    'httpListener': {'id': http_listener_id},
                    'backendAddressPool': {'id': backend_address_pool_id},
                    'backendHttpSettings': {'id': backend_http_settings_id}
                }
            }
        ]
    }
    if ssl_cert:
        ag_properties.update({'sslCertificates': [ssl_cert]})

    ag = {
        'type': 'Microsoft.Network/applicationGateways',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': get_api_version(ResourceType.MGMT_NETWORK),
        'dependsOn': [],
        'properties': ag_properties
    }
    return ag


def build_load_balancer_resource(name, location, tags, backend_pool_name, frontend_ip_name, public_ip_id, subnet_id,
                                 private_ip_address, private_ip_allocation):
    frontend_ip_config = _build_frontend_ip_config(frontend_ip_name, public_ip_id, subnet_id, private_ip_address,
                                                   private_ip_allocation)

    lb_properties = {
        'backendAddressPools': [
            {
                'name': backend_pool_name
            }
        ],
        'frontendIPConfigurations': [frontend_ip_config]
    }

    lb = {
        'type': 'Microsoft.Network/loadBalancers',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'properties': lb_properties
    }
    return lb


def build_public_ip_resource(name, location, tags, address_allocation, dns_name=None):
    public_ip_properties = {'publicIPAllocationMethod': address_allocation}

    if dns_name:
        public_ip_properties['dnsSettings'] = {'domainNameLabel': dns_name}

    public_ip = {
        'apiVersion': '2015-06-15',
        'type': 'Microsoft.Network/publicIPAddresses',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': public_ip_properties
    }
    return public_ip


def build_vnet_resource(name, location, tags, vnet_prefix=None, subnet=None, subnet_prefix=None, dns_servers=None):
    vnet = {
        'name': name,
        'type': 'Microsoft.Network/virtualNetworks',
        'location': location,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'tags': tags,
        'properties': {
            'addressSpace': {'addressPrefixes': [vnet_prefix]},
        }
    }
    if dns_servers:
        vnet['properties']['dhcpOptions'] = {
            'dnsServers': dns_servers
        }
    if subnet:
        vnet['properties']['subnets'] = [{
            'name': subnet,
            'properties': {
                'addressPrefix': subnet_prefix
            }
        }]
    return vnet


def build_vpn_connection_resource(name, location, tags, gateway1, gateway2, vpn_type, authorization_key, enable_bgp,
                                  routing_weight, shared_key, use_policy_based_traffic_selectors):
    from azure.cli.core.profiles import ResourceType, supported_api_version
    vpn_properties = {
        'virtualNetworkGateway1': {'id': gateway1},
        'authorizationKey': authorization_key,
        'enableBgp': enable_bgp,
        'connectionType': vpn_type,
        'routingWeight': routing_weight
    }
    if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-03-01'):
        vpn_properties['usePolicyBasedTrafficSelectors'] = use_policy_based_traffic_selectors

    # add scenario specific properties
    if vpn_type == 'IPSec':
        vpn_properties.update({
            'localNetworkGateway2': {'id': gateway2},
            'sharedKey': shared_key
        })
    elif vpn_type == 'Vnet2Vnet':
        vpn_properties.update({
            'virtualNetworkGateway2': {'id': gateway2},
            'sharedKey': shared_key
        })
    elif vpn_type == 'ExpressRoute':
        vpn_properties.update({
            'peer': {'id': gateway2}
        })

    vpn_connection = {
        'type': 'Microsoft.Network/connections',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'properties': vpn_properties if vpn_type != 'VpnClient' else {}
    }
    return vpn_connection

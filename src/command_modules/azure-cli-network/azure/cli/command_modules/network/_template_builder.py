# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-arguments

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
            value = "[reference(resourceId('{provider}/{type}', '{property}'),providers('{provider}', '{type}').apiVersions[0])".format(  # pylint: disable=line-too-long
                provider=provider, type=property_type, property=property_name)
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


def _build_frontend_ip_config(name, public_ip_id=None, private_ip_allocation=None,
                              private_ip_address=None, subnet_id=None):
    frontend_ip_config = {
        'name': name
    }

    if public_ip_id:
        frontend_ip_config.update({
            'properties': {
                'publicIPAddress': {
                    'id': public_ip_id
                }
            }
        })
    else:
        frontend_ip_config.update({
            'properties': {
                'privateIPAllocationMethod': private_ip_allocation,
                'privateIPAddress': private_ip_address,
                'subnet': {
                    'id': subnet_id
                }
            }
        })
    return frontend_ip_config


def build_application_gateway_resource(name, location, tags, backend_pool_name, backend_port,
                                       frontend_ip_name, public_ip_id,
                                       subnet_id, gateway_subnet_id,
                                       private_ip_address, private_ip_allocation):
    frontend_ip_config = _build_frontend_ip_config(frontend_ip_name, public_ip_id,
                                                   private_ip_address, private_ip_allocation,
                                                   subnet_id)

    def _ag_subresource_id(_type, name):
        return "[concat(variables('appGwID'), '/{}/{}')]".format(_type, name)

    frontend_ip_config_id = _ag_subresource_id('frontendIPConfigurations', frontend_ip_name)
    frontend_port_id = _ag_subresource_id('frontendPorts', 'appGwFrontendPort')
    http_listener_id = _ag_subresource_id('httpListeners', 'appGwHttpListener')
    backend_address_pool_id = _ag_subresource_id('backendAddressPools', backend_pool_name)
    backend_http_settings_id = _ag_subresource_id(
        'backendHttpSettingsCollection', 'appGwBackendHttpSettings')

    ag_properties = {
        'backendAddressPools': [
            {
                'name': backend_pool_name
            }
        ],
        'backendHttpSettingsCollection': [
            {
                'name': 'appGwBackendHttpSettings',
                'properties': {
                    'Port': backend_port,
                    'Protocol': 'Http',
                    'CookieBasedAffinity': 'Disabled'
                }
            }
        ],
        'frontendIPConfigurations': [frontend_ip_config],
        'frontendPorts': [
            {
                'name': 'appGwFrontendPort',
                'properties': {
                    'Port': 80
                }
            }
        ],
        'gatewayIPConfigurations': [
            {
                'name': 'appGwIpConfig',
                'properties': {
                    'subnet': {'id': gateway_subnet_id}
                }
            }
        ],
        'httpListeners': [
            {
                'name': 'appGwHttpListener',
                'properties': {
                    'FrontendIPConfiguration': {'Id': frontend_ip_config_id},
                    'FrontendPort': {'Id': frontend_port_id},
                    'Protocol': 'Http',
                    'SslCertificate': None
                }
            }
        ],
        'sku': {
            'name': 'Standard_Large',
            'tier': 'Standard',
            'capacity': '10'
        },
        'requestRoutingRules': [
            {
                'Name': 'rule1',
                'properties': {
                    'RuleType': 'Basic',
                    'httpListener': {'id': http_listener_id},
                    'backendAddressPool': {'id': backend_address_pool_id},
                    'backendHttpSettings': {'id': backend_http_settings_id}
                }
            }
        ]
    }

    ag = {
        'type': 'Microsoft.Network/applicationGateways',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'properties': ag_properties
    }
    return ag


def build_load_balancer_resource(name, location, tags, backend_pool_name, nat_pool_name,
                                 backend_port, frontend_ip_name, public_ip_id, subnet_id,
                                 private_ip_address, private_ip_allocation):
    lb_id = "resourceId('Microsoft.Network/loadBalancers', '{}')".format(name)

    frontend_ip_config = _build_frontend_ip_config(frontend_ip_name, public_ip_id,
                                                   private_ip_address, private_ip_allocation,
                                                   subnet_id)

    lb_properties = {
        'backendAddressPools': [
            {
                'name': backend_pool_name
            }
        ],
        'inboundNatPools': [
            {
                'name': nat_pool_name,
                'properties': {
                    'frontendIPConfiguration': {
                        'id': "[concat({}, '/frontendIPConfigurations/', '{}')]".format(
                            lb_id, frontend_ip_name)
                    },
                    'protocol': 'tcp',
                    'frontendPortRangeStart': '50000',
                    'frontendPortRangeEnd': '50119',
                    'backendPort': backend_port
                }
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


def build_vpn_connection_resource(name, location, tags, gateway1, gateway2, vpn_type,
                                  authorization_key, enable_bgp, routing_weight, shared_key):
    vpn_properties = {
        'virtualNetworkGateway1': {'id': gateway1},
        'authorizationKey': authorization_key,
        'enableBgp': enable_bgp,
        'connectionType': vpn_type,
        'routingWeight': routing_weight
    }

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


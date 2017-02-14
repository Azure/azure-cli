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

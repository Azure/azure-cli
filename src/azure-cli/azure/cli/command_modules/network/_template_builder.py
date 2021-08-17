# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _build_frontend_ip_config(cmd, name, public_ip_id=None, subnet_id=None, private_ip_address=None,
                              private_ip_allocation=None, zone=None, private_ip_address_version=None,
                              enable_private_link=False,
                              private_link_configuration_id=None):
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

    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        frontend_ip_config['zones'] = zone

    if private_ip_address_version and cmd.supported_api_version(min_api='2019-04-01'):
        frontend_ip_config['properties']['privateIPAddressVersion'] = private_ip_address_version

    if enable_private_link is True and cmd.supported_api_version(min_api='2020-05-01'):
        frontend_ip_config['properties'].update({
            'privateLinkConfiguration': {'id': private_link_configuration_id}
        })

    return frontend_ip_config


def _build_appgw_private_link_ip_configuration(name,
                                               private_link_ip_address,
                                               private_link_ip_allocation_method,
                                               private_link_primary,
                                               private_link_subnet_id):
    return {
        'name': name,
        'properties': {
            'privateIPAddress': private_link_ip_address,
            'privateIPAllocationMethod': private_link_ip_allocation_method,
            'primary': private_link_primary,
            'subnet': {'id': private_link_subnet_id}
        }
    }


# pylint: disable=too-many-locals, too-many-statements, too-many-branches
def build_application_gateway_resource(cmd, name, location, tags, sku_name, sku_tier, capacity, servers, frontend_port,
                                       private_ip_address, private_ip_allocation,
                                       cert_data, cert_password, key_vault_secret_id,
                                       cookie_based_affinity, http_settings_protocol, http_settings_port,
                                       http_listener_protocol, routing_rule_type, public_ip_id, subnet_id,
                                       connection_draining_timeout, enable_http2, min_capacity, zones,
                                       custom_error_pages, firewall_policy, max_capacity,
                                       user_assigned_identity,
                                       enable_private_link=False,
                                       private_link_name=None,
                                       private_link_ip_address=None,
                                       private_link_ip_allocation_method=None,
                                       private_link_primary=None,
                                       private_link_subnet_id=None,
                                       trusted_client_certificates=None,
                                       ssl_profile=None,
                                       ssl_profile_id=None,
                                       ssl_cert_name=None):

    # set the default names
    frontend_public_ip_name = 'appGatewayFrontendIP'
    frontend_private_ip_name = 'appGatewayPrivateFrontendIP'
    backend_pool_name = 'appGatewayBackendPool'
    frontend_port_name = 'appGatewayFrontendPort'
    http_listener_name = 'appGatewayHttpListener'
    http_settings_name = 'appGatewayBackendHttpSettings'
    routing_rule_name = 'rule1'

    if not ssl_cert_name:
        ssl_cert_name = '{}SslCert'.format(name)

    ssl_cert = None

    backend_address_pool = {'name': backend_pool_name}
    if servers:
        backend_address_pool['properties'] = {'BackendAddresses': servers}

    def _ag_subresource_id(_type, name):
        return "[concat(variables('appGwID'), '/{}/{}')]".format(_type, name)

    frontend_port_id = _ag_subresource_id('frontendPorts', frontend_port_name)
    http_listener_id = _ag_subresource_id('httpListeners', http_listener_name)
    backend_address_pool_id = _ag_subresource_id('backendAddressPools', backend_pool_name)
    backend_http_settings_id = _ag_subresource_id('backendHttpSettingsCollection',
                                                  http_settings_name)
    ssl_cert_id = _ag_subresource_id('sslCertificates', ssl_cert_name)

    private_link_configuration_id = None
    privateLinkConfigurations = []
    if cmd.supported_api_version(min_api='2020-05-01') and enable_private_link:
        private_link_configuration_id = _ag_subresource_id('privateLinkConfigurations',
                                                           private_link_name)

        default_private_link_ip_config = _build_appgw_private_link_ip_configuration(
            'PrivateLinkDefaultIPConfiguration',
            private_link_ip_address,
            private_link_ip_allocation_method,
            private_link_primary,
            private_link_subnet_id
        )
        privateLinkConfigurations.append({
            'name': private_link_name,
            'properties': {
                'ipConfigurations': [default_private_link_ip_config]
            }
        })

    frontend_ip_configs = []

    # 4 combinations are valid for creating application gateway regarding to private IP and public IP
    # --------------------------------------------------------------------------------------------|
    # |                   |        private_ip_address         |        private_ip_address         |
    # |                   |         it not None               |          is None                  |
    # --------------------------------------------------------------------------------------------|
    # |                   |  private_ip_allocation: "Static"  | private_ip_allocation: "Dynamic"  |
    # |                   |  frontend_private_ip built: yes   | frontend_private_ip built: no     |
    # | public_ip_address |                                   |                                   |
    # |    it not None    | frontend_public_ip built: yes     | frontend_public_ip built: no      |
    # |                   |                                   |                                   |
    # |                   | 2 frontend IP configs entries     | 1 frontend IP configs entry       |
    # |                   |                                   |                                   |
    # |                   | frontend_ip_config_id: public_ip  | frontend_ip_config_id:public_ip   |
    # |                   |                                   |                                   |
    # |                   | private link link to public IP    | private link link to public IP    |
    # |-------------------------------------------------------------------------------------------|
    # |                   | private_ip_allocation: "Static"   | private_ip_allocation: "Dynamic"  |
    # | public_ip_address | frontend_private_ip built: yes    | frontend_private_ip built: no     |
    # |     is None       |                                   |                                   |
    # |                   | frontend_public_ip built: no      | frontend_public_ip built: no      |
    # |                   |                                   |                                   |
    # |                   | 1 frontend IP configs entry       | 1 frontend IP configs entry       |
    # |                   |                                   |                                   |
    # |                   | frontend_ip_config_id: priavte_ip | frontend_ip_config_id: priavte_ip |
    # |                   |                                   |                                   |
    # |                   | private link link to private IP   | private link link to private IP   |
    # |-------------------------------------------------------------------------------------------|
    if private_ip_address is not None or public_ip_id is None:
        enable_private_link = False if public_ip_id else enable_private_link
        frontend_private_ip = _build_frontend_ip_config(cmd, frontend_private_ip_name,
                                                        subnet_id=subnet_id,
                                                        private_ip_address=private_ip_address,
                                                        private_ip_allocation=private_ip_allocation,
                                                        enable_private_link=enable_private_link,
                                                        private_link_configuration_id=private_link_configuration_id)
        frontend_ip_configs.append(frontend_private_ip)

        frontend_ip_config_id = _ag_subresource_id('frontendIPConfigurations', frontend_private_ip_name)
    if public_ip_id:
        frontend_public_ip = _build_frontend_ip_config(cmd, frontend_public_ip_name,
                                                       public_ip_id=public_ip_id,
                                                       enable_private_link=enable_private_link,
                                                       private_link_configuration_id=private_link_configuration_id)
        frontend_ip_configs.append(frontend_public_ip)

        frontend_ip_config_id = _ag_subresource_id('frontendIPConfigurations', frontend_public_ip_name)

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
            }
        }
        if cert_password:
            ssl_cert['properties']['password'] = "[parameters('certPassword')]"

    if key_vault_secret_id:
        http_listener['properties'].update({'SslCertificate': {'id': ssl_cert_id}})
        ssl_cert = {
            'name': ssl_cert_name,
            'properties': {
                'keyVaultSecretId': key_vault_secret_id,
            }
        }
    if ssl_profile_id and cmd.supported_api_version(min_api='2020-06-01'):
        http_listener['properties'].update({'sslProfile': {'id': ssl_profile_id}})

    backend_http_settings = {
        'name': http_settings_name,
        'properties': {
            'Port': http_settings_port,
            'Protocol': http_settings_protocol,
            'CookieBasedAffinity': cookie_based_affinity
        }
    }
    if cmd.supported_api_version(min_api='2016-12-01'):
        backend_http_settings['properties']['connectionDraining'] = {
            'enabled': bool(connection_draining_timeout),
            'drainTimeoutInSec': connection_draining_timeout if connection_draining_timeout else 1
        }

    ag_properties = {
        'backendAddressPools': [backend_address_pool],
        'backendHttpSettingsCollection': [backend_http_settings],
        'frontendIPConfigurations': frontend_ip_configs,
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
                'name': frontend_public_ip_name if public_ip_id else frontend_private_ip_name,
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
        ],
        'privateLinkConfigurations': privateLinkConfigurations,
    }
    if ssl_cert:
        ag_properties.update({'sslCertificates': [ssl_cert]})
    if enable_http2 and cmd.supported_api_version(min_api='2017-10-01'):
        ag_properties.update({'enableHttp2': enable_http2})
    if min_capacity and cmd.supported_api_version(min_api='2018-07-01'):
        if 'autoscaleConfiguration' not in ag_properties:
            ag_properties['autoscaleConfiguration'] = {}
        ag_properties['autoscaleConfiguration'].update({'minCapacity': min_capacity})
        ag_properties['sku'].pop('capacity', None)
    if max_capacity and cmd.supported_api_version(min_api='2018-12-01'):
        if 'autoscaleConfiguration' not in ag_properties:
            ag_properties['autoscaleConfiguration'] = {}
        ag_properties['autoscaleConfiguration'].update({'maxCapacity': max_capacity})
        ag_properties['sku'].pop('capacity', None)
    if custom_error_pages and cmd.supported_api_version(min_api='2018-08-01'):
        ag_properties.update({'customErrorConfigurations': custom_error_pages})
    if firewall_policy and cmd.supported_api_version(min_api='2018-12-01'):
        ag_properties.update({'firewallPolicy': {'id': firewall_policy}})

    # mutual authentication support
    if cmd.supported_api_version(min_api='2020-06-01') and trusted_client_certificates:
        parameters = []
        for item in trusted_client_certificates:
            parameters.append(
                {
                    "name": item['name'],
                    "properties": {
                        "data": item['data']
                    }
                }
            )
        ag_properties.update({"trustedClientCertificates": parameters})

    # ssl profiles
    if cmd.supported_api_version(min_api='2020-06-01') and ssl_profile:
        parameters = []
        for item in ssl_profile:
            parameter = {
                "name": item['name'],
                "properties": {
                    "sslPolicy": {}
                }
            }
            if 'policy_name' in item:
                parameter['properties']['sslPolicy'].update({"policyName": item['policy_name']})
            if 'policy_type' in item:
                parameter['properties']['sslPolicy'].update({"policyType": item['policy_type']})
            if 'min_protocol_version' in item:
                parameter['properties']['sslPolicy'].update({"minProtocolVersion": item['min_protocol_version']})
            if 'cipher_suites' in item:
                parameter['properties']['sslPolicy'].update({"cipherSuites": item['cipher_suites']})
            if 'client_auth_configuration' in item:
                parameter['properties'].update(
                    {"clientAuthConfiguration": {"verifyClientCertIssuerDN": item['client_auth_configuration']}})
            if 'trusted_client_certificates' in item:
                parameter['properties'].update(
                    {"trustedClientCertificates": [{"id": id['trusted_client_certificates']} for id in item]})

            parameters.append(parameter)

        ag_properties.update({"sslProfiles": parameters})

    ag = {
        'type': 'Microsoft.Network/applicationGateways',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': cmd.get_api_version(),
        'dependsOn': [],
        'properties': ag_properties
    }
    if cmd.supported_api_version(min_api='2018-08-01'):
        ag.update({'zones': zones})
    if user_assigned_identity and cmd.supported_api_version(min_api='2018-12-01'):
        ag.update(
            {
                "identity": {
                    "type": "UserAssigned",
                    "userAssignedIdentities": {
                        user_assigned_identity: {}
                    }
                }
            }
        )

    return ag


def build_load_balancer_resource(cmd, name, location, tags, backend_pool_name, frontend_ip_name, public_ip_id,
                                 subnet_id, private_ip_address, private_ip_allocation,
                                 sku, frontend_ip_zone, private_ip_address_version, tier=None,
                                 edge_zone=None, edge_zone_type=None):
    frontend_ip_config = _build_frontend_ip_config(cmd, frontend_ip_name, public_ip_id, subnet_id, private_ip_address,
                                                   private_ip_allocation, frontend_ip_zone, private_ip_address_version)

    lb_properties = {
        'backendAddressPools': [
            {
                'name': backend_pool_name
            }
        ],
        'frontendIPConfigurations': [frontend_ip_config]
    }

    # when sku is 'gateway', 'tunnelInterfaces' can't be None. Otherwise service will response error
    if cmd.supported_api_version(min_api='2021-02-01') and sku and str(sku).lower() == 'gateway':
        lb_properties['backendAddressPools'][0]['properties'] = {
            'tunnelInterfaces': [{'protocol': 'VXLAN',
                                  'type': 'Internal',
                                  "identifier": 900}]}

    lb = {
        'type': 'Microsoft.Network/loadBalancers',
        'name': name,
        'location': location,
        'tags': tags,
        'apiVersion': cmd.get_api_version(),
        'dependsOn': [],
        'properties': lb_properties
    }
    if sku and cmd.supported_api_version(min_api='2017-08-01'):
        lb['sku'] = {'name': sku}
    if tier and cmd.supported_api_version(min_api='2020-07-01'):
        lb['sku'].update({'tier': tier})
    if edge_zone and edge_zone_type:
        lb['extendedLocation'] = {'name': edge_zone, 'type': edge_zone_type}
    return lb


def build_public_ip_resource(cmd, name, location, tags, address_allocation, dns_name, sku, zone, tier=None,
                             edge_zone=None, edge_zone_type=None):
    public_ip_properties = {'publicIPAllocationMethod': address_allocation}

    if dns_name:
        public_ip_properties['dnsSettings'] = {'domainNameLabel': dns_name}

    public_ip = {
        'apiVersion': cmd.get_api_version(),
        'type': 'Microsoft.Network/publicIPAddresses',
        'name': name,
        'location': location,
        'tags': tags,
        'dependsOn': [],
        'properties': public_ip_properties
    }
    if sku and cmd.supported_api_version(min_api='2017-08-01'):
        public_ip['sku'] = {'name': sku}
    if tier and cmd.supported_api_version(min_api='2020-07-01'):
        if not sku:
            public_ip['sku'] = {'name': 'Basic'}
        public_ip['sku'].update({'tier': tier})
    if zone and cmd.supported_api_version(min_api='2017-06-01'):
        public_ip['zones'] = zone
    if edge_zone and edge_zone_type:
        public_ip['extendedLocation'] = {'name': edge_zone, 'type': edge_zone_type}
    return public_ip


def build_vnet_resource(_, name, location, tags, vnet_prefix=None, subnet=None, subnet_prefix=None, dns_servers=None,
                        enable_private_link=False, private_link_subnet=None, private_link_subnet_prefix=None):
    vnet = {
        'name': name,
        'type': 'Microsoft.Network/virtualNetworks',
        'location': location,
        'apiVersion': '2015-06-15',
        'dependsOn': [],
        'tags': tags,
        'properties': {
            'addressSpace': {'addressPrefixes': [vnet_prefix]},
            'subnets': []
        }
    }
    if dns_servers:
        vnet['properties']['dhcpOptions'] = {
            'dnsServers': dns_servers
        }
    if subnet:
        vnet['properties']['subnets'].append({
            'name': subnet,
            'properties': {
                'addressPrefix': subnet_prefix
            }
        })
    if enable_private_link:
        vnet['properties']['subnets'].append({
            'name': private_link_subnet,
            'properties': {
                'addressPrefix': private_link_subnet_prefix,
                'privateLinkServiceNetworkPolicies': 'Disabled',
            }
        })

    return vnet


def build_vpn_connection_resource(cmd, name, location, tags, gateway1, gateway2, vpn_type, authorization_key,
                                  enable_bgp, routing_weight, shared_key, use_policy_based_traffic_selectors,
                                  express_route_gateway_bypass, ingress_nat_rule, egress_nat_rule):
    vpn_properties = {
        'virtualNetworkGateway1': {'id': gateway1},
        'enableBgp': enable_bgp,
        'connectionType': vpn_type,
        'routingWeight': routing_weight
    }
    if authorization_key:
        vpn_properties['authorizationKey'] = "[parameters('authorizationKey')]"
    if cmd.supported_api_version(min_api='2017-03-01'):
        vpn_properties['usePolicyBasedTrafficSelectors'] = use_policy_based_traffic_selectors
    if cmd.supported_api_version(min_api='2018-07-01'):
        vpn_properties['expressRouteGatewayBypass'] = express_route_gateway_bypass

    # add scenario specific properties
    if shared_key:
        shared_key = "[parameters('sharedKey')]"
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

    if ingress_nat_rule:
        vpn_properties['ingressNatRules'] = [{'id': rule} for rule in ingress_nat_rule]

    if egress_nat_rule:
        vpn_properties['egressNatRules'] = [{'id': rule} for rule in egress_nat_rule]

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

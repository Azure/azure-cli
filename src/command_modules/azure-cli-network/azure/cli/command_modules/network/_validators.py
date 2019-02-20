# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

import argparse
import base64
import socket
import os

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.commands.validators import \
    (validate_tags, get_default_location_from_resource_group)
from azure.cli.core.commands.template_create import get_folded_parameter_validator
from azure.cli.core.commands.client_factory import get_subscription_id, get_mgmt_service_client
from azure.cli.core.commands.validators import validate_parameter_set
from azure.cli.core.profiles import ResourceType


logger = get_logger(__name__)


def get_asg_validator(loader, dest):
    from msrestazure.tools import is_valid_resource_id, resource_id

    ApplicationSecurityGroup = loader.get_models('ApplicationSecurityGroup')

    def _validate_asg_name_or_id(cmd, namespace):
        subscription_id = get_subscription_id(cmd.cli_ctx)
        resource_group = namespace.resource_group_name
        names_or_ids = getattr(namespace, dest)
        ids = []

        if names_or_ids == [""] or not names_or_ids:
            return

        for val in names_or_ids:
            if not is_valid_resource_id(val):
                val = resource_id(
                    subscription=subscription_id,
                    resource_group=resource_group,
                    namespace='Microsoft.Network', type='applicationSecurityGroups',
                    name=val
                )
            ids.append(ApplicationSecurityGroup(id=val))
        setattr(namespace, dest, ids)

    return _validate_asg_name_or_id


def get_vnet_validator(dest):
    from msrestazure.tools import is_valid_resource_id, resource_id

    def _validate_vnet_name_or_id(cmd, namespace):
        SubResource = cmd.get_models('SubResource')
        subscription_id = get_subscription_id(cmd.cli_ctx)

        resource_group = namespace.resource_group_name
        names_or_ids = getattr(namespace, dest)
        ids = []

        if names_or_ids == [''] or not names_or_ids:
            return

        for val in names_or_ids:
            if not is_valid_resource_id(val):
                val = resource_id(
                    subscription=subscription_id,
                    resource_group=resource_group,
                    namespace='Microsoft.Network', type='virtualNetworks',
                    name=val
                )
            ids.append(SubResource(id=val))
        setattr(namespace, dest, ids)

    return _validate_vnet_name_or_id


def validate_ddos_name_or_id(cmd, namespace):

    if namespace.ddos_protection_plan:
        from msrestazure.tools import is_valid_resource_id, resource_id
        if not is_valid_resource_id(namespace.ddos_protection_plan):
            namespace.ddos_protection_plan = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network', type='ddosProtectionPlans',
                name=namespace.ddos_protection_plan
            )


# pylint: disable=inconsistent-return-statements
def dns_zone_name_type(value):
    if value:
        return value[:-1] if value[-1] == '.' else value


def _generate_ag_subproperty_id(cli_ctx, namespace, child_type, child_name, subscription=None):
    from msrestazure.tools import resource_id
    return resource_id(
        subscription=subscription or get_subscription_id(cli_ctx),
        resource_group=namespace.resource_group_name,
        namespace='Microsoft.Network',
        type='applicationGateways',
        name=namespace.application_gateway_name,
        child_type_1=child_type,
        child_name_1=child_name)


def _generate_lb_subproperty_id(cli_ctx, namespace, child_type, child_name, subscription=None):
    from msrestazure.tools import resource_id
    return resource_id(
        subscription=subscription or get_subscription_id(cli_ctx),
        resource_group=namespace.resource_group_name,
        namespace='Microsoft.Network',
        type='loadBalancers',
        name=namespace.load_balancer_name,
        child_type_1=child_type,
        child_name_1=child_name)


def _generate_lb_id_list_from_names_or_ids(cli_ctx, namespace, prop, child_type):
    from msrestazure.tools import is_valid_resource_id
    raw = getattr(namespace, prop)
    if not raw:
        return
    raw = raw if isinstance(raw, list) else [raw]
    result = []
    for item in raw:
        if is_valid_resource_id(item):
            result.append({'id': item})
        else:
            if not namespace.load_balancer_name:
                raise CLIError('Unable to process {}. Please supply a well-formed ID or '
                               '--lb-name.'.format(item))
            else:
                result.append({'id': _generate_lb_subproperty_id(
                    cli_ctx, namespace, child_type, item)})
    setattr(namespace, prop, result)


def validate_address_pool_id_list(cmd, namespace):
    _generate_lb_id_list_from_names_or_ids(
        cmd.cli_ctx, namespace, 'load_balancer_backend_address_pool_ids', 'backendAddressPools')


def validate_address_pool_name_or_id(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    address_pool = namespace.backend_address_pool
    lb_name = namespace.load_balancer_name
    gateway_name = namespace.application_gateway_name

    usage_error = CLIError('usage error: --address-pool ID | --lb-name NAME --address-pool NAME '
                           '| --gateway-name NAME --address-pool NAME')

    if is_valid_resource_id(address_pool):
        if lb_name or gateway_name:
            raise usage_error
        parts = parse_resource_id(address_pool)
        if parts['type'] == 'loadBalancers':
            namespace.load_balancer_name = parts['name']
        elif parts['type'] == 'applicationGateways':
            namespace.application_gateway_name = parts['name']
        else:
            raise usage_error
    else:
        if bool(lb_name) == bool(gateway_name):
            raise usage_error

        if lb_name:
            namespace.backend_address_pool = _generate_lb_subproperty_id(
                cmd.cli_ctx, namespace, 'backendAddressPools', address_pool)
        elif gateway_name:
            namespace.backend_address_pool = _generate_ag_subproperty_id(
                cmd.cli_ctx, namespace, 'backendAddressPools', address_pool)


def validate_address_prefixes(namespace):

    if namespace.subnet_type != 'new':
        validate_parameter_set(namespace,
                               required=[],
                               forbidden=['subnet_address_prefix', 'vnet_address_prefix'],
                               description='existing subnet')


def read_base_64_file(filename):
    with open(filename, 'rb') as f:
        contents = f.read()
        base64_data = base64.b64encode(contents)
        try:
            return base64_data.decode('utf-8')
        except UnicodeDecodeError:
            return str(base64_data)


def validate_cert(namespace):
    if namespace.cert_data:
        namespace.cert_data = read_base_64_file(namespace.cert_data)


def validate_ssl_cert(namespace):
    params = [namespace.cert_data, namespace.cert_password]
    if all([not x for x in params]):
        # no cert supplied -- use HTTP
        if not namespace.frontend_port:
            namespace.frontend_port = 80
    else:
        # cert supplied -- use HTTPS
        if not all(params):
            raise CLIError(
                None, 'To use SSL certificate, you must specify both the filename and password')

        # extract the certificate data from the provided file
        namespace.cert_data = read_base_64_file(namespace.cert_data)

        try:
            # change default to frontend port 443 for https
            if not namespace.frontend_port:
                namespace.frontend_port = 443
        except AttributeError:
            # app-gateway ssl-cert create does not have these fields and that is okay
            pass


def validate_delegations(cmd, namespace):
    if namespace.delegations:
        Delegation = cmd.get_models('Delegation')
        delegations = []
        for i, item in enumerate(namespace.delegations):
            if '/' not in item and len(item.split('.')) == 3:
                # convert names to serviceNames
                _, service, resource_type = item.split('.')
                item = 'Microsoft.{}/{}'.format(service, resource_type)
            delegations.append(Delegation(name=str(i), service_name=item))
        namespace.delegations = delegations


def validate_dns_record_type(namespace):
    tokens = namespace.command.split(' ')
    types = ['a', 'aaaa', 'caa', 'cname', 'mx', 'ns', 'ptr', 'soa', 'srv', 'txt']
    for token in tokens:
        if token in types:
            if hasattr(namespace, 'record_type'):
                namespace.record_type = token
            else:
                namespace.record_set_type = token
            return


def validate_express_route_peering(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    circuit = namespace.circuit_name
    peering = namespace.peering

    if not circuit and not peering:
        return

    usage_error = CLIError('usage error: --peering ID | --peering NAME --circuit-name CIRCUIT')
    if not is_valid_resource_id(peering):
        namespace.peering = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='expressRouteCircuits',
            name=circuit,
            child_type_1='peerings',
            child_name_1=peering
        )
    elif circuit:
        raise usage_error


def validate_express_route_port(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.express_route_port and not is_valid_resource_id(namespace.express_route_port):
        namespace.express_route_port = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='expressRoutePorts',
            name=namespace.express_route_port
        )


def validate_virtual_hub(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.virtual_hub and not is_valid_resource_id(namespace.virtual_hub):
        namespace.virtual_hub = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualHubs',
            name=namespace.virtual_hub
        )


def bandwidth_validator_factory(mbps=True):
    def validator(namespace):
        return validate_circuit_bandwidth(namespace, mbps=mbps)
    return validator


def validate_circuit_bandwidth(namespace, mbps=True):
    # use gbps if mbps is False
    unit = 'mbps' if mbps else 'gbps'
    bandwidth = None
    bandwidth = getattr(namespace, 'bandwidth_in_{}'.format(unit), None)
    if bandwidth is None:
        return

    if len(bandwidth) == 1:
        bandwidth_comps = bandwidth[0].split(' ')
    else:
        bandwidth_comps = bandwidth

    usage_error = CLIError('usage error: --bandwidth INT {Mbps,Gbps}')
    if len(bandwidth_comps) == 1:
        logger.warning('interpretting --bandwidth as %s. Consider being explicit: Mbps, Gbps', unit)
        setattr(namespace, 'bandwidth_in_{}'.format(unit), float(bandwidth_comps[0]))
        return
    if len(bandwidth_comps) > 2:
        raise usage_error

    if float(bandwidth_comps[0]) and bandwidth_comps[1].lower() in ['mbps', 'gbps']:
        input_unit = bandwidth_comps[1].lower()
        if input_unit == unit:
            converted_bandwidth = float(bandwidth_comps[0])
        elif input_unit == 'gbps':
            converted_bandwidth = float(bandwidth_comps[0]) * 1000
        else:
            converted_bandwidth = float(bandwidth_comps[0]) / 1000
        setattr(namespace, 'bandwidth_in_{}'.format(unit), converted_bandwidth)
    else:
        raise usage_error


def validate_er_peer_circuit(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id

    if not is_valid_resource_id(namespace.peer_circuit):
        peer_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='expressRouteCircuits',
            name=namespace.peer_circuit,
            child_type_1='peerings',
            child_name_1=namespace.peering_name)
    else:
        peer_id = namespace.peer_circuit

    # if the circuit ID is provided, we need to append /peerings/{peering_name}
    if namespace.peering_name not in peer_id:
        peer_id = '{}/peerings/{}'.format(peer_id, namespace.peering_name)

    namespace.peer_circuit = peer_id


def validate_inbound_nat_rule_id_list(cmd, namespace):
    _generate_lb_id_list_from_names_or_ids(
        cmd.cli_ctx, namespace, 'load_balancer_inbound_nat_rule_ids', 'inboundNatRules')


def validate_inbound_nat_rule_name_or_id(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id
    rule_name = namespace.inbound_nat_rule
    lb_name = namespace.load_balancer_name

    if is_valid_resource_id(rule_name):
        if lb_name:
            raise CLIError('Please omit --lb-name when specifying an inbound NAT rule ID.')
    else:
        if not lb_name:
            raise CLIError('Please specify --lb-name when specifying an inbound NAT rule name.')
        namespace.inbound_nat_rule = _generate_lb_subproperty_id(
            cmd.cli_ctx, namespace, 'inboundNatRules', rule_name)


def validate_ip_tags(cmd, namespace):
    ''' Extracts multiple space-separated tags in TYPE=VALUE format '''
    IpTag = cmd.get_models('IpTag')
    if namespace.ip_tags and IpTag:
        ip_tags = []
        for item in namespace.ip_tags:
            tag_type, tag_value = item.split('=', 1)
            ip_tags.append(IpTag(ip_tag_type=tag_type, tag=tag_value))
        namespace.ip_tags = ip_tags


def validate_frontend_ip_configs(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id
    if namespace.frontend_ip_configurations:
        config_ids = []
        for item in namespace.frontend_ip_configurations:
            if not is_valid_resource_id(item):
                config_ids.append(_generate_lb_subproperty_id(
                    cmd.cli_ctx, namespace, 'frontendIpConfigurations', item))
            else:
                config_ids.append(item)
        namespace.frontend_ip_configurations = config_ids


def validate_local_gateway(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.gateway_default_site and not is_valid_resource_id(namespace.gateway_default_site):
        namespace.gateway_default_site = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.gateway_default_site,
            namespace='Microsoft.Network',
            type='localNetworkGateways')


def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)


def validate_peering_type(namespace):
    if namespace.peering_type and namespace.peering_type == 'MicrosoftPeering':

        if not namespace.advertised_public_prefixes:
            raise CLIError(
                'missing required MicrosoftPeering parameter --advertised-public-prefixes')


def validate_public_ip_prefix(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.public_ip_prefix and not is_valid_resource_id(namespace.public_ip_prefix):
        namespace.public_ip_prefix = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.public_ip_prefix,
            namespace='Microsoft.Network',
            type='publicIPPrefixes')


def validate_private_ip_address(namespace):
    if namespace.private_ip_address and hasattr(namespace, 'private_ip_address_allocation'):
        namespace.private_ip_address_allocation = 'static'


def validate_route_filter(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.route_filter:
        if not is_valid_resource_id(namespace.route_filter):
            namespace.route_filter = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='routeFilters',
                name=namespace.route_filter)


def get_public_ip_validator(has_type_field=False, allow_none=False, allow_new=False,
                            default_none=False):
    """ Retrieves a validator for public IP address. Accepting all defaults will perform a check
    for an existing name or ID with no ARM-required -type parameter. """
    from msrestazure.tools import is_valid_resource_id, resource_id

    def simple_validator(cmd, namespace):
        if namespace.public_ip_address:
            is_list = isinstance(namespace.public_ip_address, list)

            def _validate_name_or_id(public_ip):
                # determine if public_ip_address is name or ID
                is_id = is_valid_resource_id(public_ip)
                return public_ip if is_id else resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='publicIPAddresses',
                    name=public_ip)

            if is_list:
                for i, public_ip in enumerate(namespace.public_ip_address):
                    namespace.public_ip_address[i] = _validate_name_or_id(public_ip)
            else:
                namespace.public_ip_address = _validate_name_or_id(namespace.public_ip_address)

    def complex_validator_with_type(cmd, namespace):
        get_folded_parameter_validator(
            'public_ip_address', 'Microsoft.Network/publicIPAddresses', '--public-ip-address',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(cmd, namespace)

    return complex_validator_with_type if has_type_field else simple_validator


def get_subnet_validator(has_type_field=False, allow_none=False, allow_new=False,
                         default_none=False):
    from msrestazure.tools import is_valid_resource_id, resource_id

    def simple_validator(cmd, namespace):
        if namespace.virtual_network_name is None and namespace.subnet is None:
            return
        if namespace.subnet == '':
            return
        usage_error = ValueError('incorrect usage: ( --subnet ID | --subnet NAME --vnet-name NAME)')
        # error if vnet-name is provided without subnet
        if namespace.virtual_network_name and not namespace.subnet:
            raise usage_error

        # determine if subnet is name or ID
        is_id = is_valid_resource_id(namespace.subnet)

        # error if vnet-name is provided along with a subnet ID
        if is_id and namespace.virtual_network_name:
            raise usage_error
        elif not is_id and not namespace.virtual_network_name:
            raise usage_error

        if not is_id:
            namespace.subnet = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='virtualNetworks',
                name=namespace.virtual_network_name,
                child_type_1='subnets',
                child_name_1=namespace.subnet)

    def complex_validator_with_type(cmd, namespace):

        get_folded_parameter_validator(
            'subnet', 'subnets', '--subnet',
            'virtual_network_name', 'Microsoft.Network/virtualNetworks', '--vnet-name',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(cmd, namespace)

    return complex_validator_with_type if has_type_field else simple_validator


def get_nsg_validator(has_type_field=False, allow_none=False, allow_new=False, default_none=False):
    from msrestazure.tools import is_valid_resource_id, resource_id

    def simple_validator(cmd, namespace):
        if namespace.network_security_group:
            # determine if network_security_group is name or ID
            is_id = is_valid_resource_id(namespace.network_security_group)
            if not is_id:
                namespace.network_security_group = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='networkSecurityGroups',
                    name=namespace.network_security_group)

    def complex_validator_with_type(cmd, namespace):
        get_folded_parameter_validator(
            'network_security_group', 'Microsoft.Network/networkSecurityGroups', '--nsg',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(cmd, namespace)

    return complex_validator_with_type if has_type_field else simple_validator


def validate_service_endpoint_policy(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.service_endpoint_policy:
        policy_ids = []
        for policy in namespace.service_endpoint_policy:
            if not is_valid_resource_id(policy):
                policy = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=namespace.resource_group_name,
                    name=policy,
                    namespace='Microsoft.Network',
                    type='serviceEndpointPolicies')
            policy_ids.append(policy)
        namespace.service_endpoint_policy = policy_ids


def get_servers_validator(camel_case=False):
    def validate_servers(namespace):
        servers = []
        for item in namespace.servers if namespace.servers else []:
            try:
                socket.inet_aton(item)  # pylint:disable=no-member
                servers.append({'ipAddress' if camel_case else 'ip_address': item})
            except socket.error:  # pylint:disable=no-member
                servers.append({'fqdn': item})
        namespace.servers = servers
    return validate_servers


def validate_subresource_list(cmd, namespace):
    if namespace.target_resources:
        SubResource = cmd.get_models('SubResource')
        subresources = []
        for item in namespace.target_resources:
            subresources.append(SubResource(id=item))
        namespace.target_resources = subresources


def validate_target_listener(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.target_listener and not is_valid_resource_id(namespace.target_listener):
        namespace.target_listener = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.application_gateway_name,
            namespace='Microsoft.Network',
            type='applicationGateways',
            child_type_1='httpListeners',
            child_name_1=namespace.target_listener)


def get_virtual_network_validator(has_type_field=False, allow_none=False, allow_new=False,
                                  default_none=False):
    from msrestazure.tools import is_valid_resource_id, resource_id

    def simple_validator(cmd, namespace):
        if namespace.virtual_network:
            # determine if vnet is name or ID
            is_id = is_valid_resource_id(namespace.virtual_network)
            if not is_id:
                namespace.virtual_network = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='virtualNetworks',
                    name=namespace.virtual_network)

    def complex_validator_with_type(cmd, namespace):
        get_folded_parameter_validator(
            'virtual_network', 'Microsoft.Network/virtualNetworks', '--vnet',
            allow_none=allow_none, allow_new=allow_new, default_none=default_none)(cmd, namespace)

    return complex_validator_with_type if has_type_field else simple_validator


# COMMAND NAMESPACE VALIDATORS

def process_ag_listener_create_namespace(cmd, namespace):  # pylint: disable=unused-argument
    from msrestazure.tools import is_valid_resource_id
    if namespace.frontend_ip and not is_valid_resource_id(namespace.frontend_ip):
        namespace.frontend_ip = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'frontendIpConfigurations', namespace.frontend_ip)

    if namespace.frontend_port and not is_valid_resource_id(namespace.frontend_port):
        namespace.frontend_port = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'frontendPorts', namespace.frontend_port)

    if namespace.ssl_cert and not is_valid_resource_id(namespace.ssl_cert):
        namespace.ssl_cert = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'sslCertificates', namespace.ssl_cert)


def process_ag_http_settings_create_namespace(cmd, namespace):  # pylint: disable=unused-argument
    from msrestazure.tools import is_valid_resource_id
    if namespace.probe and not is_valid_resource_id(namespace.probe):
        namespace.probe = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'probes', namespace.probe)
    if namespace.auth_certs:
        def _validate_name_or_id(val):
            return val if is_valid_resource_id(val) else _generate_ag_subproperty_id(
                cmd.cli_ctx, namespace, 'authenticationCertificates', val)
        namespace.auth_certs = [_validate_name_or_id(x) for x in namespace.auth_certs]


def process_ag_rule_create_namespace(cmd, namespace):  # pylint: disable=unused-argument
    from msrestazure.tools import is_valid_resource_id
    if namespace.address_pool and not is_valid_resource_id(namespace.address_pool):
        namespace.address_pool = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'backendAddressPools', namespace.address_pool)

    if namespace.http_listener and not is_valid_resource_id(namespace.http_listener):
        namespace.http_listener = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'httpListeners', namespace.http_listener)

    if namespace.http_settings and not is_valid_resource_id(namespace.http_settings):
        namespace.http_settings = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'backendHttpSettingsCollection', namespace.http_settings)

    if namespace.url_path_map and not is_valid_resource_id(namespace.url_path_map):
        namespace.url_path_map = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'urlPathMaps', namespace.url_path_map)

    if namespace.redirect_config and not is_valid_resource_id(namespace.redirect_config):
        namespace.redirect_config = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'redirectConfigurations', namespace.redirect_config)


def process_ag_ssl_policy_set_namespace(namespace):
    if namespace.disabled_ssl_protocols and getattr(namespace, 'clear', None):
        raise ValueError('incorrect usage: --disabled-ssl-protocols PROTOCOL [...] | --clear')


def process_ag_url_path_map_create_namespace(cmd, namespace):  # pylint: disable=unused-argument
    from msrestazure.tools import is_valid_resource_id
    if namespace.default_address_pool and not is_valid_resource_id(namespace.default_address_pool):
        namespace.default_address_pool = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'backendAddressPools', namespace.default_address_pool)

    if namespace.default_http_settings and not is_valid_resource_id(
            namespace.default_http_settings):
        namespace.default_http_settings = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'backendHttpSettingsCollection', namespace.default_http_settings)

    if namespace.default_redirect_config and not is_valid_resource_id(
            namespace.default_redirect_config):
        namespace.default_redirect_config = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'redirectConfigurations', namespace.default_redirect_config)

    if hasattr(namespace, 'rule_name'):
        process_ag_url_path_map_rule_create_namespace(cmd, namespace)


def process_ag_url_path_map_rule_create_namespace(cmd, namespace):  # pylint: disable=unused-argument
    from msrestazure.tools import is_valid_resource_id
    if namespace.address_pool and not is_valid_resource_id(namespace.address_pool):
        namespace.address_pool = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'backendAddressPools', namespace.address_pool)

    if namespace.http_settings and not is_valid_resource_id(namespace.http_settings):
        namespace.http_settings = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'backendHttpSettingsCollection', namespace.http_settings)

    if namespace.redirect_config and not is_valid_resource_id(
            namespace.redirect_config):
        namespace.redirect_config = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'redirectConfigurations', namespace.redirect_config)


def process_ag_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    get_servers_validator(camel_case=True)(namespace)

    # process folded parameters
    if namespace.subnet or namespace.virtual_network_name:
        get_subnet_validator(has_type_field=True, allow_new=True)(cmd, namespace)
    validate_address_prefixes(namespace)
    if namespace.public_ip_address:
        get_public_ip_validator(
            has_type_field=True, allow_none=True, allow_new=True, default_none=True)(cmd, namespace)
    validate_ssl_cert(namespace)
    validate_tags(namespace)
    validate_custom_error_pages(namespace)


def process_auth_create_namespace(cmd, namespace):
    ExpressRouteCircuitAuthorization = cmd.get_models('ExpressRouteCircuitAuthorization')
    namespace.authorization_parameters = ExpressRouteCircuitAuthorization()


def process_lb_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)

    if namespace.subnet and namespace.public_ip_address:
        raise ValueError(
            'incorrect usage: --subnet NAME --vnet-name NAME | '
            '--subnet ID | --public-ip-address NAME_OR_ID')

    if namespace.subnet:
        # validation for an internal load balancer
        get_subnet_validator(
            has_type_field=True, allow_new=True, allow_none=True, default_none=True)(cmd, namespace)

        namespace.public_ip_address_type = None
        namespace.public_ip_address = None

    else:
        # validation for internet facing load balancer
        get_public_ip_validator(has_type_field=True, allow_none=True, allow_new=True)(cmd, namespace)

        if namespace.public_ip_dns_name and namespace.public_ip_address_type != 'new':
            raise CLIError(
                'specify --public-ip-dns-name only if creating a new public IP address.')

        namespace.subnet_type = None
        namespace.subnet = None
        namespace.virtual_network_name = None


def process_lb_frontend_ip_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.subnet and namespace.public_ip_address:
        raise ValueError(
            'incorrect usage: --subnet NAME --vnet-name NAME | '
            '--subnet ID | --public-ip NAME_OR_ID')

    if namespace.public_ip_prefix:
        if not is_valid_resource_id(namespace.public_ip_prefix):
            namespace.public_ip_prefix = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='publicIpPrefixes',
                name=namespace.public_ip_prefix)

    if namespace.subnet:
        get_subnet_validator()(cmd, namespace)
    else:
        get_public_ip_validator()(cmd, namespace)


def process_local_gateway_create_namespace(cmd, namespace):
    ns = namespace
    get_default_location_from_resource_group(cmd, ns)
    validate_tags(ns)

    use_bgp_settings = any([ns.asn or ns.bgp_peering_address or ns.peer_weight])
    if use_bgp_settings and (not ns.asn or not ns.bgp_peering_address):
        raise ValueError(
            'incorrect usage: --bgp-peering-address IP --asn ASN [--peer-weight WEIGHT]')


def process_nic_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)

    validate_ag_address_pools(cmd, namespace)
    validate_address_pool_id_list(cmd, namespace)
    validate_inbound_nat_rule_id_list(cmd, namespace)
    get_asg_validator(cmd.loader, 'application_security_groups')(cmd, namespace)

    # process folded parameters
    get_subnet_validator(has_type_field=False)(cmd, namespace)
    get_public_ip_validator(has_type_field=False, allow_none=True, default_none=True)(cmd, namespace)
    get_nsg_validator(has_type_field=False, allow_none=True, default_none=True)(cmd, namespace)


def process_public_ip_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_public_ip_prefix(cmd, namespace)
    validate_ip_tags(cmd, namespace)
    validate_tags(namespace)


def process_route_table_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)


def process_tm_endpoint_create_namespace(cmd, namespace):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient

    client = get_mgmt_service_client(cmd.cli_ctx, TrafficManagerManagementClient).profiles
    profile = client.get(namespace.resource_group_name, namespace.profile_name)

    routing_type = profile.traffic_routing_method  # pylint: disable=no-member
    endpoint_type = namespace.endpoint_type
    all_options = ['target_resource_id', 'target', 'min_child_endpoints', 'priority', 'weight', 'endpoint_location']
    props_to_options = {
        'target_resource_id': '--target-resource-id',
        'target': '--target',
        'min_child_endpoints': '--min-child-endpoints',
        'priority': '--priority',
        'weight': '--weight',
        'endpoint_location': '--endpoint-location',
        'geo_mapping': '--geo-mapping'
    }
    validate_subnet_ranges(namespace)
    validate_custom_headers(namespace)

    required_options = []

    # determine which options are required based on profile and routing method
    if endpoint_type.lower() == 'externalendpoints':
        required_options.append('target')
    else:
        required_options.append('target_resource_id')

    if routing_type.lower() == 'weighted':
        required_options.append('weight')
    elif routing_type.lower() == 'priority':
        required_options.append('priority')

    if endpoint_type.lower() == 'nestedendpoints':
        required_options.append('min_child_endpoints')

    if endpoint_type.lower() in ['nestedendpoints', 'externalendpoints'] and routing_type.lower() == 'performance':
        required_options.append('endpoint_location')

    if routing_type.lower() == 'geographic':
        required_options.append('geo_mapping')

    # ensure required options are provided
    missing_options = [props_to_options[x] for x in required_options if getattr(namespace, x, None) is None]
    extra_options = [props_to_options[x] for x in all_options if
                     getattr(namespace, x, None) is not None and x not in required_options]

    if missing_options or extra_options:
        error_message = "Incorrect options for profile routing method '{}' and endpoint type '{}'.".format(routing_type,
                                                                                                           endpoint_type)  # pylint: disable=line-too-long
        if missing_options:
            error_message = '{}\nSupply the following: {}'.format(error_message, ', '.join(
                missing_options))
        if extra_options:
            error_message = '{}\nOmit the following: {}'.format(error_message, ', '.join(
                extra_options))
        raise CLIError(error_message)


def process_vnet_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_ddos_name_or_id(cmd, namespace)
    validate_tags(namespace)

    if namespace.subnet_prefix and not namespace.subnet_name:
        if cmd.supported_api_version(min_api='2018-08-01'):
            raise ValueError('incorrect usage: --subnet-name NAME [--subnet-prefixes PREFIXES]')
        else:
            raise ValueError('incorrect usage: --subnet-name NAME [--subnet-prefix PREFIX]')

    if namespace.subnet_name and not namespace.subnet_prefix:
        if isinstance(namespace.vnet_prefixes, str):
            namespace.vnet_prefixes = [namespace.vnet_prefixes]
        prefix_components = namespace.vnet_prefixes[0].split('/', 1)
        address = prefix_components[0]
        bit_mask = int(prefix_components[1])
        subnet_mask = 24 if bit_mask < 24 else bit_mask
        subnet_prefix = '{}/{}'.format(address, subnet_mask)
        namespace.subnet_prefix = [subnet_prefix] if cmd.supported_api_version(min_api='2018-08-01') else subnet_prefix


def process_vnet_gateway_create_namespace(cmd, namespace):
    ns = namespace
    get_default_location_from_resource_group(cmd, ns)
    validate_tags(ns)

    get_virtual_network_validator()(cmd, ns)

    get_public_ip_validator()(cmd, ns)
    public_ip_count = len(ns.public_ip_address or [])
    if public_ip_count > 2:
        raise CLIError('Specify a single public IP to create an active-standby gateway or two '
                       'public IPs to create an active-active gateway.')

    validate_local_gateway(cmd, ns)

    enable_bgp = any([ns.asn, ns.bgp_peering_address, ns.peer_weight])
    if enable_bgp and not ns.asn:
        raise ValueError(
            'incorrect usage: --asn ASN [--peer-weight WEIGHT --bgp-peering-address IP ]')


def process_vnet_gateway_update_namespace(cmd, namespace):
    ns = namespace
    get_virtual_network_validator()(cmd, ns)
    get_public_ip_validator()(cmd, ns)
    validate_tags(ns)
    public_ip_count = len(ns.public_ip_address or [])
    if public_ip_count > 2:
        raise CLIError('Specify a single public IP to create an active-standby gateway or two '
                       'public IPs to create an active-active gateway.')


def process_vpn_connection_create_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)

    args = [a for a in [namespace.express_route_circuit2,
                        namespace.local_gateway2,
                        namespace.vnet_gateway2]
            if a]
    if len(args) != 1:
        raise ValueError('usage error: --vnet-gateway2 NAME_OR_ID | --local-gateway2 NAME_OR_ID '
                         '| --express-route-circuit2 NAME_OR_ID')

    def _validate_name_or_id(value, resource_type):
        if not is_valid_resource_id(value):
            subscription = getattr(namespace, 'subscription', get_subscription_id(cmd.cli_ctx))
            return resource_id(
                subscription=subscription,
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type=resource_type,
                name=value)
        return value

    if (namespace.local_gateway2 or namespace.vnet_gateway2) and not namespace.shared_key:
        raise CLIError('--shared-key is required for VNET-to-VNET or Site-to-Site connections.')

    if namespace.express_route_circuit2 and namespace.shared_key:
        raise CLIError('--shared-key cannot be used with an ExpressRoute connection.')

    namespace.vnet_gateway1 = \
        _validate_name_or_id(namespace.vnet_gateway1, 'virtualNetworkGateways')

    if namespace.express_route_circuit2:
        namespace.express_route_circuit2 = \
            _validate_name_or_id(
                namespace.express_route_circuit2, 'expressRouteCircuits')
        namespace.connection_type = 'ExpressRoute'
    elif namespace.local_gateway2:
        namespace.local_gateway2 = \
            _validate_name_or_id(namespace.local_gateway2, 'localNetworkGateways')
        namespace.connection_type = 'IPSec'
    elif namespace.vnet_gateway2:
        namespace.vnet_gateway2 = \
            _validate_name_or_id(namespace.vnet_gateway2, 'virtualNetworkGateways')
        namespace.connection_type = 'Vnet2Vnet'


def load_cert_file(param_name):
    def load_cert_validator(namespace):
        attr = getattr(namespace, param_name)
        if attr and os.path.isfile(attr):
            setattr(namespace, param_name, read_base_64_file(attr))

    return load_cert_validator


def get_network_watcher_from_vm(cmd, namespace):
    from msrestazure.tools import parse_resource_id

    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machines
    vm_name = parse_resource_id(namespace.vm)['name']
    vm = compute_client.get(namespace.resource_group_name, vm_name)
    namespace.location = vm.location  # pylint: disable=no-member
    get_network_watcher_from_location()(cmd, namespace)


def get_network_watcher_from_resource(cmd, namespace):
    from azure.cli.core.commands.arm import get_arm_resource_by_id
    resource = get_arm_resource_by_id(cmd.cli_ctx, namespace.resource)
    namespace.location = resource.location  # pylint: disable=no-member
    get_network_watcher_from_location(remove=True)(cmd, namespace)


def get_network_watcher_from_location(remove=False, watcher_name='watcher_name',
                                      rg_name='watcher_rg'):
    def _validator(cmd, namespace):
        from msrestazure.tools import parse_resource_id

        location = namespace.location
        network_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_NETWORK).network_watchers
        watcher = next((x for x in network_client.list_all() if x.location.lower() == location.lower()), None)
        if not watcher:
            raise CLIError("network watcher is not enabled for region '{}'.".format(location))
        id_parts = parse_resource_id(watcher.id)
        setattr(namespace, rg_name, id_parts['resource_group'])
        setattr(namespace, watcher_name, id_parts['name'])

        if remove:
            del namespace.location

    return _validator


def process_nw_cm_create_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id

    validate_tags(namespace)

    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machines
    vm_name = parse_resource_id(namespace.source_resource)['name']
    rg = namespace.resource_group_name or parse_resource_id(namespace.source_resource).get('resource_group', None)
    if not rg:
        raise CLIError('usage error: --source-resource ID | --source-resource NAME --resource-group NAME')
    vm = compute_client.get(rg, vm_name)
    namespace.location = vm.location  # pylint: disable=no-member
    get_network_watcher_from_location()(cmd, namespace)

    if namespace.source_resource and not is_valid_resource_id(namespace.source_resource):
        namespace.source_resource = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=rg,
            namespace='Microsoft.Compute',
            type='virtualMachines',
            name=namespace.source_resource)

    if namespace.dest_resource and not is_valid_resource_id(namespace.dest_resource):
        namespace.dest_resource = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Compute',
            type='virtualMachines',
            name=namespace.dest_resource)


def process_nw_test_connectivity_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id

    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machines
    vm_name = parse_resource_id(namespace.source_resource)['name']
    rg = namespace.resource_group_name or parse_resource_id(namespace.source_resource).get('resource_group', None)
    if not rg:
        raise CLIError('usage error: --source-resource ID | --source-resource NAME --resource-group NAME')
    vm = compute_client.get(rg, vm_name)
    namespace.location = vm.location  # pylint: disable=no-member
    get_network_watcher_from_location(remove=True)(cmd, namespace)

    if namespace.source_resource and not is_valid_resource_id(namespace.source_resource):
        namespace.source_resource = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=rg,
            namespace='Microsoft.Compute',
            type='virtualMachines',
            name=namespace.source_resource)

    if namespace.dest_resource and not is_valid_resource_id(namespace.dest_resource):
        namespace.dest_resource = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Compute',
            type='virtualMachines',
            name=namespace.dest_resource)

    if namespace.headers:
        HTTPHeader = cmd.get_models('HTTPHeader')
        headers = []
        for item in namespace.headers:
            parts = item.split('=')
            if len(parts) != 2:
                raise CLIError("usage error '{}': --headers KEY=VALUE [KEY=VALUE ...]".format(item))
            headers.append(HTTPHeader(name=parts[0], value=parts[1]))
        namespace.headers = headers


def process_nw_flow_log_set_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
        namespace.storage_account = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Storage',
            type='storageAccounts',
            name=namespace.storage_account)
    if namespace.traffic_analytics_workspace and not is_valid_resource_id(namespace.traffic_analytics_workspace):
        namespace.traffic_analytics_workspace = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.OperationalInsights',
            type='workspaces',
            name=namespace.traffic_analytics_workspace)

    process_nw_flow_log_show_namespace(cmd, namespace)


def process_nw_flow_log_show_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    from azure.cli.core.commands.arm import get_arm_resource_by_id

    if not is_valid_resource_id(namespace.nsg):
        namespace.nsg = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='networkSecurityGroups',
            name=namespace.nsg)

    nsg = get_arm_resource_by_id(cmd.cli_ctx, namespace.nsg)
    namespace.location = nsg.location  # pylint: disable=no-member
    get_network_watcher_from_location(remove=True)(cmd, namespace)


def process_nw_topology_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id, parse_resource_id
    SubResource = cmd.get_models('SubResource')
    subscription_id = get_subscription_id(cmd.cli_ctx)

    location = namespace.location
    rg = namespace.target_resource_group_name
    vnet = namespace.target_vnet
    subnet = namespace.target_subnet

    vnet_id = vnet if is_valid_resource_id(vnet) else None
    subnet_id = subnet if is_valid_resource_id(subnet) else None

    if rg and not vnet and not subnet:
        # targeting resource group - OK
        pass
    elif subnet:
        subnet_usage = CLIError('usage error: --subnet ID | --subnet NAME --resource-group NAME --vnet NAME')
        # targeting subnet - OK
        if subnet_id and (vnet or rg):
            raise subnet_usage
        elif not subnet_id and (not rg or not vnet or vnet_id):
            raise subnet_usage
        if subnet_id:
            rg = parse_resource_id(subnet_id)['resource_group']
            namespace.target_subnet = SubResource(id=subnet)
        else:
            subnet_id = subnet_id or resource_id(
                subscription=subscription_id,
                resource_group=rg,
                namespace='Microsoft.Network',
                type='virtualNetworks',
                name=vnet,
                child_type_1='subnets',
                child_name_1=subnet
            )
            namespace.target_resource_group_name = None
            namespace.target_vnet = None
            namespace.target_subnet = SubResource(id=subnet_id)
    elif vnet:
        # targeting vnet - OK
        vnet_usage = CLIError('usage error: --vnet ID | --vnet NAME --resource-group NAME')
        if vnet_id and (subnet or rg):
            raise vnet_usage
        elif not vnet_id and not rg or subnet:
            raise vnet_usage
        if vnet_id:
            rg = parse_resource_id(vnet_id)['resource_group']
            namespace.target_vnet = SubResource(id=vnet)
        else:
            vnet_id = vnet_id or resource_id(
                subscription=subscription_id,
                resource_group=rg,
                namespace='Microsoft.Network',
                type='virtualNetworks',
                name=vnet
            )
            namespace.target_resource_group_name = None
            namespace.target_vnet = SubResource(id=vnet_id)
    else:
        raise CLIError('usage error: --resource-group NAME | --vnet NAME_OR_ID | --subnet NAME_OR_ID')

    # retrieve location from resource group
    if not location:
        resource_client = \
            get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES).resource_groups
        resource_group = resource_client.get(rg)
        namespace.location = resource_group.location  # pylint: disable=no-member

    get_network_watcher_from_location(
        remove=True, watcher_name='network_watcher_name', rg_name='resource_group_name')(cmd, namespace)


def process_nw_packet_capture_create_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    get_network_watcher_from_vm(cmd, namespace)

    storage_usage = CLIError('usage error: --storage-account NAME_OR_ID [--storage-path '
                             'PATH] [--file-path PATH] | --file-path PATH')
    if not namespace.storage_account and not namespace.file_path:
        raise storage_usage

    if namespace.storage_path and not namespace.storage_account:
        raise storage_usage

    if not is_valid_resource_id(namespace.vm):
        namespace.vm = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Compute',
            type='virtualMachines',
            name=namespace.vm)

    if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
        namespace.storage_account = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Storage',
            type='storageAccounts',
            name=namespace.storage_account)

    if namespace.file_path:
        file_path = namespace.file_path
        if not file_path.endswith('.cap'):
            raise CLIError("usage error: --file-path PATH must end with the '*.cap' extension")
        file_path = file_path.replace('/', '\\')
        namespace.file_path = file_path


def process_nw_troubleshooting_start_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    storage_usage = CLIError('usage error: --storage-account NAME_OR_ID [--storage-path PATH]')
    if namespace.storage_path and not namespace.storage_account:
        raise storage_usage

    if not is_valid_resource_id(namespace.storage_account):
        namespace.storage_account = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Storage',
            type='storageAccounts',
            name=namespace.storage_account)

    process_nw_troubleshooting_show_namespace(cmd, namespace)


def process_nw_troubleshooting_show_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    resource_usage = CLIError('usage error: --resource ID | --resource NAME --resource-type TYPE '
                              '--resource-group NAME')
    id_params = [namespace.resource_type, namespace.resource_group_name]
    if not is_valid_resource_id(namespace.resource):
        if not all(id_params):
            raise resource_usage
        type_map = {
            'vnetGateway': 'virtualNetworkGateways',
            'vpnConnection': 'connections'
        }
        namespace.resource = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type=type_map[namespace.resource_type],
            name=namespace.resource)
    else:
        if any(id_params):
            raise resource_usage

    get_network_watcher_from_resource(cmd, namespace)


def process_nw_config_diagnostic_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id

    # validate target resource
    resource_usage = CLIError('usage error: --resource ID | --resource NAME --resource-type TYPE '
                              '--resource-group NAME [--parent PATH]')

    # omit --parent since it is optional
    id_params = [namespace.resource_type, namespace.resource_group_name]
    if not is_valid_resource_id(namespace.resource):
        if not all(id_params):
            raise resource_usage
        # infer resource namespace
        NAMESPACES = {
            'virtualMachines': 'Microsoft.Compute',
            'applicationGateways': 'Microsoft.Network',
            'networkInterfaces': 'Microsoft.Network'
        }
        resource_namespace = NAMESPACES[namespace.resource_type]
        if namespace.parent:
            # special case for virtualMachineScaleSets/NetworkInterfaces, since it is
            # the only one to need `--parent`.
            resource_namespace = 'Microsoft.Compute'
        namespace.resource = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace=resource_namespace,
            type=namespace.resource_type,
            parent=namespace.parent,
            name=namespace.resource)
    elif any(id_params) or namespace.parent:
        raise resource_usage

    # validate query
    query_usage = CLIError('usage error: --queries JSON | --destination DEST --source SRC --direction DIR '
                           '--port PORT --protocol PROTOCOL')
    query_params = [namespace.destination, namespace.source, namespace.direction, namespace.protocol,
                    namespace.destination_port]
    if namespace.queries:
        if any(query_params):
            raise query_usage
    elif not all(query_params):
        raise query_usage

    get_network_watcher_from_resource(cmd, namespace)


def process_lb_outbound_rule_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id

    validate_frontend_ip_configs(cmd, namespace)

    if namespace.backend_address_pool:
        if not is_valid_resource_id(namespace.backend_address_pool):
            namespace.backend_address_pool = _generate_lb_subproperty_id(
                cmd.cli_ctx, namespace, 'backendAddressPools', namespace.backend_address_pool)


def process_list_delegations_namespace(cmd, namespace):

    if not namespace.resource_group_name and not namespace.location:
        raise CLIError('usage error: --location LOCATION | --resource-group NAME [--location LOCATION]')

    if not namespace.location:
        get_default_location_from_resource_group(cmd, namespace)


def validate_ag_address_pools(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    address_pools = namespace.app_gateway_backend_address_pools
    gateway_name = namespace.application_gateway_name
    delattr(namespace, 'application_gateway_name')
    if not address_pools:
        return
    ids = []
    for item in address_pools:
        if not is_valid_resource_id(item):
            if not gateway_name:
                raise CLIError('usage error: --app-gateway-backend-pools IDS | --gateway-name NAME '
                               '--app-gateway-backend-pools NAMES')
            item = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='applicationGateways',
                name=gateway_name,
                child_type_1='backendAddressPools',
                child_name_1=item)
            ids.append(item)
    namespace.app_gateway_backend_address_pools = ids


def validate_custom_error_pages(namespace):

    if not namespace.custom_error_pages:
        return

    values = []
    for item in namespace.custom_error_pages:
        try:
            (code, url) = item.split('=')
            values.append({'statusCode': code, 'customErrorPageUrl': url})
        except (ValueError, TypeError):
            raise CLIError('usage error: --custom-error-pages STATUS_CODE=URL [STATUS_CODE=URL ...]')
    namespace.custom_error_pages = values


def validate_custom_headers(namespace):

    if not namespace.monitor_custom_headers:
        return

    values = []
    for item in namespace.monitor_custom_headers:
        try:
            item_split = item.split('=', 1)
            values.append({'name': item_split[0], 'value': item_split[1]})
        except IndexError:
            raise CLIError('usage error: --custom-headers KEY=VALUE')

    namespace.monitor_custom_headers = values


def validate_status_code_ranges(namespace):

    if not namespace.status_code_ranges:
        return

    values = []
    for item in namespace.status_code_ranges:
        item_split = item.split('-', 1)
        usage_error = CLIError('usage error: --status-code-ranges VAL | --status-code-ranges MIN-MAX')
        try:
            if len(item_split) == 1:
                values.append({'min': int(item_split[0]), 'max': int(item_split[0])})
            elif len(item_split) == 2:
                values.append({'min': int(item_split[0]), 'max': int(item_split[1])})
            else:
                raise usage_error
        except ValueError:
            raise usage_error

    namespace.status_code_ranges = values


def validate_subnet_ranges(namespace):

    if not namespace.subnets:
        return

    values = []
    for item in namespace.subnets:
        try:
            item_split = item.split('-', 1)
            if len(item_split) == 2:
                values.append({'first': item_split[0], 'last': item_split[1]})
                continue
        except ValueError:
            pass

        try:
            item_split = item.split(':', 1)
            if len(item_split) == 2:
                values.append({'first': item_split[0], 'scope': item_split[1]})
                continue
        except ValueError:
            pass

        values.append({'first': item})

    namespace.subnets = values


# pylint: disable=too-few-public-methods
class WafConfigExclusionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        cmd = namespace._cmd  # pylint: disable=protected-access
        ApplicationGatewayFirewallExclusion = cmd.get_models('ApplicationGatewayFirewallExclusion')
        if not namespace.exclusions:
            namespace.exclusions = []
        if isinstance(values, list):
            values = ' '.join(values)
        try:
            variable, op, selector = values.split(' ')
        except (ValueError, TypeError):
            raise CLIError('usage error: --exclusion VARIABLE OPERATOR VALUE')
        namespace.exclusions.append(ApplicationGatewayFirewallExclusion(
            match_variable=variable,
            selector_match_operator=op,
            selector=selector
        ))

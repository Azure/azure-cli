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
from azure.cli.core.azclierror import RequiredArgumentMissingError, InvalidArgumentValueError

logger = get_logger(__name__)


def _resolve_api_version(rcf, resource_provider_namespace, parent_resource_path, resource_type):
    """
    This is copied from src/azure-cli/azure/cli/command_modules/resource/custom.py in Azure/azure-cli
    """
    from azure.cli.core.parser import IncorrectUsageError

    provider = rcf.providers.get(resource_provider_namespace)

    # If available, we will use parent resource's api-version
    resource_type_str = (parent_resource_path.split('/')[0] if parent_resource_path else resource_type)

    rt = [t for t in provider.resource_types if t.resource_type.lower() == resource_type_str.lower()]
    if not rt:
        raise IncorrectUsageError('Resource type {} not found.'.format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    raise IncorrectUsageError(
        'API version is required and could not be resolved for resource {}'.format(resource_type))


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


def get_subscription_list_validator(dest, model_class):
    def _validate_subscription_list(cmd, namespace):
        val = getattr(namespace, dest, None)
        if not val:
            return
        model = cmd.get_models(model_class)
        setattr(namespace, dest, model(subscriptions=val))

    return _validate_subscription_list


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


def _validate_vpn_gateway_generation(namespace):
    if namespace.gateway_type != 'Vpn' and namespace.vpn_gateway_generation:
        raise CLIError('vpn_gateway_generation should not be provided if gateway_type is not Vpn.')


def validate_vpn_connection_name_or_id(cmd, namespace):
    if namespace.vpn_connection_ids:
        from msrestazure.tools import is_valid_resource_id, resource_id
        for index, vpn_connection_id in enumerate(namespace.vpn_connection_ids):
            if not is_valid_resource_id(vpn_connection_id):
                namespace.vpn_connection_ids[index] = resource_id(
                    subscription=get_subscription_id(cmd.cli_ctx),
                    resource_group=namespace.resource_group_name,
                    namespace='Microsoft.Network',
                    type='connections',
                    name=vpn_connection_id
                )


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


def validate_trusted_client_cert(namespace):
    if namespace.client_cert_data is None or namespace.client_cert_name is None:
        raise RequiredArgumentMissingError('To use this cmd, you must specify both name and data')
    namespace.client_cert_data = read_base_64_file(namespace.client_cert_data)


def validate_ssl_cert(namespace):
    params = [namespace.cert_data, namespace.cert_password]
    if all(not x for x in params) and not namespace.key_vault_secret_id:
        # no cert supplied -- use HTTP
        if not namespace.frontend_port:
            namespace.frontend_port = 80
    else:
        if namespace.key_vault_secret_id:
            return
        # cert supplied -- use HTTPS
        if not namespace.cert_data:
            raise CLIError(
                None, 'To use SSL certificate, you must specify both the filename')

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


def validate_user_assigned_identity(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id

    if namespace.user_assigned_identity and not is_valid_resource_id(namespace.user_assigned_identity):
        namespace.user_assigned_identity = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.ManagedIdentity',
            type='userAssignedIdentities',
            name=namespace.user_assigned_identity
        )


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


def validate_virtul_network_gateway(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.hosted_gateway and not is_valid_resource_id(namespace.hosted_gateway):
        namespace.hosted_gateway = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworkGateways',
            name=namespace.hosted_gateway
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


def validate_waf_policy(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.firewall_policy and not is_valid_resource_id(namespace.firewall_policy):
        namespace.firewall_policy = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='ApplicationGatewayWebApplicationFirewallPolicies',
            name=namespace.firewall_policy
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


def validate_match_variables(cmd, namespace):
    if not namespace.match_variables:
        return

    MatchVariable = cmd.get_models('MatchVariable')
    variables = []
    for match in namespace.match_variables:
        try:
            name, selector = match.split('.', 1)
        except ValueError:
            name = match
            selector = None
        variables.append(MatchVariable(variable_name=name, selector=selector))
    namespace.match_variables = variables


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


def validate_nat_gateway(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.nat_gateway and not is_valid_resource_id(namespace.nat_gateway):
        namespace.nat_gateway = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.nat_gateway,
            namespace='Microsoft.Network',
            type='natGateways')


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
        if not is_id and not namespace.virtual_network_name:
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
        namespace.servers = servers if servers else None

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


def validate_private_dns_zone(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.private_dns_zone and not is_valid_resource_id(namespace.private_dns_zone):
        namespace.private_dns_zone = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.private_dns_zone,
            namespace='Microsoft.Network',
            type='privateDnsZones')


def validate_scale_unit_ranges(namespace):
    unit_num = namespace.scale_units
    err_msg = "The number of --scale-units should in range [2, 50]."
    if unit_num is not None and (unit_num < 2 or unit_num > 50):
        raise InvalidArgumentValueError(err_msg)


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
    from msrestazure.tools import is_valid_resource_id, resource_id
    if namespace.frontend_ip and not is_valid_resource_id(namespace.frontend_ip):
        namespace.frontend_ip = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'frontendIpConfigurations', namespace.frontend_ip)

    if namespace.frontend_port and not is_valid_resource_id(namespace.frontend_port):
        namespace.frontend_port = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'frontendPorts', namespace.frontend_port)

    if namespace.ssl_cert and not is_valid_resource_id(namespace.ssl_cert):
        namespace.ssl_cert = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'sslCertificates', namespace.ssl_cert)

    if namespace.firewall_policy and not is_valid_resource_id(namespace.firewall_policy):
        namespace.firewall_policy = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='ApplicationGatewayWebApplicationFirewallPolicies',
            name=namespace.firewall_policy
        )


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
    if namespace.root_certs:
        def _validate_name_or_id(val):
            return val if is_valid_resource_id(val) else _generate_ag_subproperty_id(
                cmd.cli_ctx, namespace, 'trustedRootCertificates', val)

        namespace.root_certs = [_validate_name_or_id(x) for x in namespace.root_certs]


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

    if namespace.rewrite_rule_set and not is_valid_resource_id(namespace.rewrite_rule_set):
        namespace.rewrite_rule_set = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'rewriteRuleSets', namespace.rewrite_rule_set)


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

    if hasattr(namespace, 'firewall_policy') and \
            namespace.firewall_policy and not is_valid_resource_id(namespace.firewall_policy):
        namespace.firewall_policy = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'firewallPolicy', namespace.firewall_policy
        )

    if namespace.default_rewrite_rule_set and not is_valid_resource_id(namespace.default_rewrite_rule_set):
        namespace.default_rewrite_rule_set = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'rewriteRuleSets', namespace.default_rewrite_rule_set)

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

    if namespace.rewrite_rule_set and not is_valid_resource_id(namespace.rewrite_rule_set):
        namespace.rewrite_rule_set = _generate_ag_subproperty_id(
            cmd.cli_ctx, namespace, 'rewriteRuleSets', namespace.rewrite_rule_set)


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
    validate_waf_policy(cmd, namespace)
    validate_user_assigned_identity(cmd, namespace)


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


def process_cross_region_lb_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)

    # validation for internet facing load balancer
    get_public_ip_validator(has_type_field=True, allow_none=True, allow_new=True)(cmd, namespace)

    if namespace.public_ip_dns_name and namespace.public_ip_address_type != 'new':
        raise CLIError(
            'specify --public-ip-dns-name only if creating a new public IP address.')


def process_cross_region_lb_frontend_ip_namespace(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

    if namespace.public_ip_prefix:
        if not is_valid_resource_id(namespace.public_ip_prefix):
            namespace.public_ip_prefix = resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=namespace.resource_group_name,
                namespace='Microsoft.Network',
                type='publicIpPrefixes',
                name=namespace.public_ip_prefix)

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
    _inform_coming_breaking_change_for_public_ip(namespace)


def _inform_coming_breaking_change_for_public_ip(namespace):
    if namespace.sku == 'Standard' and not namespace.zone:
        logger.warning('[Coming breaking change] In the coming release, the default behavior will be changed as follows'
                       ' when sku is Standard and zone is not provided:'
                       ' For zonal regions, you will get a zone-redundant IP indicated by zones:["1","2","3"];'
                       ' For non-zonal regions, you will get a non zone-redundant IP indicated by zones:null.')


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
    get_nsg_validator()(cmd, namespace)

    if namespace.subnet_prefix and not namespace.subnet_name:
        if cmd.supported_api_version(min_api='2018-08-01'):
            raise ValueError('incorrect usage: --subnet-name NAME [--subnet-prefixes PREFIXES]')
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


def _validate_cert(namespace, param_name):
    attr = getattr(namespace, param_name)
    if attr and os.path.isfile(attr):
        setattr(namespace, param_name, read_base_64_file(attr))


def process_vnet_gateway_create_namespace(cmd, namespace):
    ns = namespace
    get_default_location_from_resource_group(cmd, ns)
    validate_tags(ns)

    _validate_vpn_gateway_generation(ns)

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

    if cmd.supported_api_version(min_api='2020-11-01'):
        _validate_cert(namespace, 'root_cert_data')


def process_vnet_gateway_update_namespace(cmd, namespace):
    ns = namespace
    get_virtual_network_validator()(cmd, ns)
    get_public_ip_validator()(cmd, ns)
    validate_tags(ns)
    if cmd.supported_api_version(min_api='2020-11-01'):
        _validate_cert(namespace, 'root_cert_data')
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


def process_nw_cm_v1_create_namespace(cmd, namespace):
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


def process_nw_cm_v2_create_namespace(cmd, namespace):
    if namespace.location is None:  # location is None only occurs in creating a V2 connection monitor
        endpoint_source_resource_id = namespace.endpoint_source_resource_id

        from msrestazure.tools import is_valid_resource_id, parse_resource_id
        from azure.mgmt.resource import ResourceManagementClient

        # parse and verify endpoint_source_resource_id
        if endpoint_source_resource_id is None:
            raise CLIError('usage error: '
                           '--location/--endpoint-source-resource-id is required to create a V2 connection monitor')
        if is_valid_resource_id(endpoint_source_resource_id) is False:
            raise CLIError('usage error: "{}" is not a valid resource id'.format(endpoint_source_resource_id))

        resource = parse_resource_id(namespace.endpoint_source_resource_id)
        resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceManagementClient)
        resource_api_version = _resolve_api_version(resource_client,
                                                    resource['namespace'],
                                                    resource['resource_parent'],
                                                    resource['resource_type'])
        resource = resource_client.resources.get_by_id(namespace.endpoint_source_resource_id, resource_api_version)

        namespace.location = resource.location
        if namespace.location is None:
            raise CLIError("Can not get location from --endpoint-source-resource-id")

    v2_required_parameter_set = [
        'endpoint_source_resource_id', 'endpoint_source_name', 'endpoint_dest_name', 'test_config_name'
    ]
    for p in v2_required_parameter_set:
        if not hasattr(namespace, p) or getattr(namespace, p) is None:
            raise CLIError(
                'usage error: --{} is required to create a V2 connection monitor'.format(p.replace('_', '-')))
    if namespace.test_config_protocol is None:
        raise CLIError('usage error: --protocol is required to create a test configuration for V2 connection monitor')

    v2_optional_parameter_set = ['workspace_ids']
    if namespace.output_type is not None:
        tmp = [p for p in v2_optional_parameter_set if getattr(namespace, p) is None]
        if v2_optional_parameter_set == tmp:
            raise CLIError('usage error: --output-type is specified but no other resource id provided')

    return get_network_watcher_from_location()(cmd, namespace)


def process_nw_cm_create_namespace(cmd, namespace):
    # V2 parameter set
    if namespace.source_resource is None:
        return process_nw_cm_v2_create_namespace(cmd, namespace)

    # V1 parameter set
    return process_nw_cm_v1_create_namespace(cmd, namespace)


def process_nw_cm_v2_endpoint_namespace(cmd, namespace):
    if hasattr(namespace, 'filter_type') or hasattr(namespace, 'filter_items'):
        filter_type, filter_items = namespace.filter_type, namespace.filter_items
        if (filter_type and not filter_items) or (not filter_type and filter_items):
            raise CLIError('usage error: --filter-type and --filter-item must be present at the same time.')

    if hasattr(namespace, 'dest_test_groups') or hasattr(namespace, 'source_test_groups'):
        dest_test_groups, source_test_groups = namespace.dest_test_groups, namespace.source_test_groups
        if dest_test_groups is None and source_test_groups is None:
            raise CLIError('usage error: endpoint has to be referenced from at least one existing test group '
                           'via --dest-test-groups/--source-test-groups')

    return get_network_watcher_from_location()(cmd, namespace)


def process_nw_cm_v2_test_configuration_namespace(cmd, namespace):
    return get_network_watcher_from_location()(cmd, namespace)


def process_nw_cm_v2_test_group(cmd, namespace):
    return get_network_watcher_from_location()(cmd, namespace)


def process_nw_cm_v2_output_namespace(cmd, namespace):
    v2_output_optional_parameter_set = ['workspace_id']
    if hasattr(namespace, 'out_type') and namespace.out_type is not None:
        tmp = [p for p in v2_output_optional_parameter_set if getattr(namespace, p) is None]
        if v2_output_optional_parameter_set == tmp:
            raise CLIError('usage error: --type is specified but no other resource id provided')

    return get_network_watcher_from_location()(cmd, namespace)


# pylint: disable=protected-access,too-few-public-methods
class NWConnectionMonitorEndpointFilterItemAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        ConnectionMonitorEndpointFilterItem = namespace._cmd.get_models('ConnectionMonitorEndpointFilterItem')

        if not namespace.filter_items:
            namespace.filter_items = []

        filter_item = ConnectionMonitorEndpointFilterItem()

        for item in values:
            try:
                key, val = item.split('=', 1)

                if hasattr(filter_item, key):
                    setattr(filter_item, key, val)
                else:
                    raise CLIError(
                        "usage error: '{}' is not a valid property of ConnectionMonitorEndpointFilterItem".format(key))
            except ValueError:
                raise CLIError(
                    'usage error: {} PropertyName=PropertyValue [PropertyName=PropertyValue ...]'.format(option_string))

        namespace.filter_items.append(filter_item)


# pylint: disable=protected-access,too-few-public-methods
class NWConnectionMonitorTestConfigurationHTTPRequestHeaderAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        HTTPHeader = namespace._cmd.get_models('HTTPHeader')

        if not namespace.http_request_headers:
            namespace.http_request_headers = []

        request_header = HTTPHeader()

        for item in values:
            try:
                key, val = item.split('=', 1)
                if hasattr(request_header, key):
                    setattr(request_header, key, val)
                else:
                    raise CLIError("usage error: '{}' is not a value property of HTTPHeader".format(key))
            except ValueError:
                raise CLIError(
                    'usage error: {} name=HTTPHeader value=HTTPHeaderValue'.format(option_string))

        namespace.http_request_headers.append(request_header)


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


def process_nw_flow_log_create_namespace(cmd, namespace):
    """
    Flow Log is the sub-resource of Network Watcher, they must be in the same region and subscription.
    """
    from msrestazure.tools import is_valid_resource_id, resource_id

    # for both create and update
    if namespace.resource_group_name is None:
        err_tpl, err_body = 'usage error: use {} instead.', None

        if namespace.nsg and not is_valid_resource_id(namespace.nsg):
            err_body = '--nsg ID / --nsg NSD_NAME --resource-group NSD_RESOURCE_GROUP'

        if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
            err_body = '--storage-account ID / --storage-account NAME --resource_group STORAGE_ACCOUNT_RESOURCE_GROUP'

        if namespace.traffic_analytics_workspace and not is_valid_resource_id(namespace.traffic_analytics_workspace):
            err_body = '--workspace ID / --workspace NAME --resource-group WORKSPACE_RESOURCE_GROUP'

        if err_body is not None:
            raise CLIError(err_tpl.format(err_body))

    # for both create and update
    if namespace.nsg and not is_valid_resource_id(namespace.nsg):
        kwargs = {
            'subscription': get_subscription_id(cmd.cli_ctx),
            'resource_group': namespace.resource_group_name,
            'namespace': 'Microsoft.Network',
            'type': 'networkSecurityGroups',
            'name': namespace.nsg
        }
        namespace.nsg = resource_id(**kwargs)

    # for both create and update
    if namespace.storage_account and not is_valid_resource_id(namespace.storage_account):
        kwargs = {
            'subscription': get_subscription_id(cmd.cli_ctx),
            'resource_group': namespace.resource_group_name,
            'namespace': 'Microsoft.Storage',
            'type': 'storageAccounts',
            'name': namespace.storage_account
        }
        namespace.storage_account = resource_id(**kwargs)

    # for both create and update
    if namespace.traffic_analytics_workspace and not is_valid_resource_id(namespace.traffic_analytics_workspace):
        kwargs = {
            'subscription': get_subscription_id(cmd.cli_ctx),
            'resource_group': namespace.resource_group_name,
            'namespace': 'Microsoft.OperationalInsights',
            'type': 'workspaces',
            'name': namespace.traffic_analytics_workspace
        }
        namespace.traffic_analytics_workspace = resource_id(**kwargs)

    get_network_watcher_from_location(remove=False)(cmd, namespace)

    validate_tags(namespace)


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

    if hasattr(namespace, 'nsg') and namespace.nsg is not None:
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
    elif namespace.flow_log_name is not None and namespace.location is not None:
        get_network_watcher_from_location(remove=False)(cmd, namespace)
    else:
        raise CLIError('usage error: --nsg NSG | --location NETWORK_WATCHER_LOCATION --name FLOW_LOW_NAME')


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
        if not subnet_id and (not rg or not vnet or vnet_id):
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
        if not vnet_id and not rg or subnet:
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


def get_header_configuration_validator(dest):
    def validator(namespace):
        values = getattr(namespace, dest, None)
        if not values:
            return

        results = []
        for item in values:
            key, value = item.split('=', 1)
            results.append({
                'header_name': key,
                'header_value': value
            })
        setattr(namespace, dest, results)

    return validator


def process_private_link_resource_id_argument(cmd, namespace):
    if all([namespace.resource_group_name,
            namespace.name,
            namespace.resource_provider]):
        logger.warning("Resource ID will be ignored since other three arguments have been provided.")
        del namespace.id
        return

    if not (namespace.id or all([namespace.resource_group_name,
                                 namespace.name,
                                 namespace.resource_provider])):
        raise CLIError("usage error: --id / -g -n --type")

    from msrestazure.tools import is_valid_resource_id, parse_resource_id
    if not is_valid_resource_id(namespace.id):
        raise CLIError("Resource ID is not invalid. Please check it.")
    split_resource_id = parse_resource_id(namespace.id)
    cmd.cli_ctx.data['subscription_id'] = split_resource_id['subscription']
    namespace.resource_group_name = split_resource_id['resource_group']
    namespace.name = split_resource_id['name']
    namespace.resource_provider = '{}/{}'.format(split_resource_id['namespace'], split_resource_id['type'])
    del namespace.id


def process_private_endpoint_connection_id_argument(cmd, namespace):
    from azure.cli.core.util import parse_proxy_resource_id
    if all([namespace.resource_group_name,
            namespace.name,
            namespace.resource_provider,
            namespace.resource_name]):
        logger.warning("Resource ID will be ignored since other three arguments have been provided.")
        del namespace.connection_id
        return

    if not (namespace.connection_id or all([namespace.resource_group_name,
                                            namespace.name,
                                            namespace.resource_provider,
                                            namespace.resource_name])):
        raise CLIError("usage error: --id / -g -n --type --resource-name")

    result = parse_proxy_resource_id(namespace.connection_id)
    cmd.cli_ctx.data['subscription_id'] = result['subscription']
    namespace.resource_group_name = result['resource_group']
    namespace.resource_name = result['name']
    namespace.resource_provider = '{}/{}'.format(result['namespace'], result['type'])
    namespace.name = result['child_name_1']
    del namespace.connection_id


def process_vnet_name_or_id(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if namespace.vnet and not is_valid_resource_id(namespace.vnet):
        namespace.vnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=namespace.vnet)


def process_appgw_waf_policy_update(cmd, namespace):    # pylint: disable=unused-argument
    rule_group_name = namespace.rule_group_name
    rules = namespace.rules

    if rules is None and rule_group_name is not None:
        raise CLIError('--rules and --rule-group-name must be provided at the same time')
    if rules is not None and rule_group_name is None:
        raise CLIError('--rules and --rule-group-name must be provided at the same time')

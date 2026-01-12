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

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.commands.validators import validate_tags, get_default_location_from_resource_group
from azure.cli.core.commands.template_create import get_folded_parameter_validator
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.commands.validators import validate_parameter_set
from azure.cli.core.profiles import ResourceType

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


def get_vnet_validator(dest):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

    def _validate_vnet_name_or_id(cmd, namespace):
        SubResource = cmd.get_models('SubResource', resource_type=ResourceType.MGMT_RESOURCE_RESOURCES)
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


def validate_ddos_name_or_id(cmd, namespace):
    if namespace.ddos_protection_plan:
        from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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
    from azure.mgmt.core.tools import resource_id
    return resource_id(
        subscription=subscription or get_subscription_id(cli_ctx),
        resource_group=namespace.resource_group_name,
        namespace='Microsoft.Network',
        type='applicationGateways',
        name=namespace.application_gateway_name,
        child_type_1=child_type,
        child_name_1=child_name)


def _generate_lb_subproperty_id(cli_ctx, namespace, child_type, child_name, subscription=None):
    from azure.mgmt.core.tools import resource_id
    return resource_id(
        subscription=subscription or get_subscription_id(cli_ctx),
        resource_group=namespace.resource_group_name,
        namespace='Microsoft.Network',
        type='loadBalancers',
        name=namespace.load_balancer_name,
        child_type_1=child_type,
        child_name_1=child_name)


def _generate_lb_id_list_from_names_or_ids(cli_ctx, namespace, prop, child_type):
    from azure.mgmt.core.tools import is_valid_resource_id
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
    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
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


def validate_dns_record_type(namespace):
    tokens = namespace.command.split(' ')
    types = ['a', 'aaaa', 'caa', 'cname', 'ds', 'mx', 'naptr', 'ns', 'ptr', 'soa', 'srv', 'tlsa', 'txt']
    for token in tokens:
        if token in types:
            if hasattr(namespace, 'record_type'):
                namespace.record_type = token
            else:
                namespace.record_set_type = token
            return


def validate_managed_identity_resource_id(resource_id):
    if resource_id.lower() == 'none':
        return True
    parts = resource_id.split('/')
    if len(parts) != 9:
        raise ValueError(
            'Invalid resource ID format for a managed identity. It should be in the format:'
            '/subscriptions/{subscription}/resourceGroups/{resource_group}/providers/'
            'Microsoft.ManagedIdentity/userAssignedIdentities/{identity_name}')

    if (parts[1] != 'subscriptions' or parts[3] != 'resourceGroups' or parts[5] != 'providers' or
            parts[6] != 'Microsoft.ManagedIdentity' or parts[7] != 'userAssignedIdentities'):
        raise ValueError(
            'Invalid resource ID format for a managed identity. It should contain subscriptions,'
            'resourceGroups, providers/Microsoft.ManagedIdentity/userAssignedIdentities'
            'in the correct order.')
    return True


def validate_user_assigned_identity(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

    if namespace.user_assigned_identity and not is_valid_resource_id(namespace.user_assigned_identity):
        namespace.user_assigned_identity = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.ManagedIdentity',
            type='userAssignedIdentities',
            name=namespace.user_assigned_identity
        )


def validate_waf_policy(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if namespace.firewall_policy and not is_valid_resource_id(namespace.firewall_policy):
        namespace.firewall_policy = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='ApplicationGatewayWebApplicationFirewallPolicies',
            name=namespace.firewall_policy
        )


def validate_inbound_nat_rule_id_list(cmd, namespace):
    _generate_lb_id_list_from_names_or_ids(
        cmd.cli_ctx, namespace, 'load_balancer_inbound_nat_rule_ids', 'inboundNatRules')


def validate_inbound_nat_rule_name_or_id(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id
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


def validate_ip_tags(namespace):
    """ Extracts multiple space-separated tags in TYPE=VALUE format """
    if namespace.ip_tags:
        ip_tags = []
        for item in namespace.ip_tags:
            tag_type, tag_value = item.split('=', 1)
            ip_tags.append({"ip_tag_type": tag_type, "tag": tag_value})
        namespace.ip_tags = ip_tags


def validate_frontend_ip_configs(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id
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
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if namespace.public_ip_prefix and not is_valid_resource_id(namespace.public_ip_prefix):
        namespace.public_ip_prefix = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.public_ip_prefix,
            namespace='Microsoft.Network',
            type='publicIPPrefixes')


def validate_nat_gateway(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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


def get_public_ip_validator(has_type_field=False, allow_none=False, allow_new=False,
                            default_none=False):
    """ Retrieves a validator for public IP address. Accepting all defaults will perform a check
    for an existing name or ID with no ARM-required -type parameter. """
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

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
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

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
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

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
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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
            except OSError:  # pylint:disable=no-member
                servers.append({'fqdn': item})
        namespace.servers = servers if servers else None

    return validate_servers


def validate_private_dns_zone(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if namespace.private_dns_zone and not is_valid_resource_id(namespace.private_dns_zone):
        namespace.private_dns_zone = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            name=namespace.private_dns_zone,
            namespace='Microsoft.Network',
            type='privateDnsZones')


def get_virtual_network_validator(has_type_field=False, allow_none=False, allow_new=False,
                                  default_none=False):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

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


def process_cross_region_lb_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)

    # validation for internet facing load balancer
    get_public_ip_validator(has_type_field=True, allow_none=True, allow_new=True)(cmd, namespace)

    if namespace.public_ip_dns_name and namespace.public_ip_address_type != 'new':
        raise CLIError(
            'specify --public-ip-dns-name only if creating a new public IP address.')


def process_public_ip_create_namespace(cmd, namespace):
    get_default_location_from_resource_group(cmd, namespace)
    validate_public_ip_prefix(cmd, namespace)
    validate_ip_tags(namespace)
    validate_tags(namespace)
    _inform_coming_breaking_change_for_public_ip(namespace)


def _inform_coming_breaking_change_for_public_ip(namespace):
    if namespace.sku == 'Standard' and not namespace.zone:
        logger.warning('[Coming breaking change] In the coming release, the default behavior will be changed as follows'
                       ' when sku is Standard and zone is not provided:'
                       ' For zonal regions, you will get a zone-redundant IP indicated by zones:["1","2","3"];'
                       ' For non-zonal regions, you will get a non zone-redundant IP indicated by zones:null.')


def _validate_cert(namespace, param_name):
    attr = getattr(namespace, param_name)
    if attr and os.path.isfile(attr):
        setattr(namespace, param_name, read_base_64_file(attr))


def auto_scale_config_validator(namespace):
    # see VirtualRouterAutoScaleConfiguration properties in swagger
    config_props = ['min-capacity']

    def _parse(item):
        prop, value = item.split('=', 1)
        if prop not in config_props:
            raise ValidationError(f"Invalid property '{prop}' in auto-scale-config. Supported: {config_props}")
        return {prop: value} if value else {prop: ""}

    if isinstance(namespace.auto_scale_config, list):
        auto_scale_config = {}
        for item in namespace.auto_scale_config:
            auto_scale_config.update(_parse(item))
        namespace.auto_scale_config = auto_scale_config


def process_vpn_connection_create_namespace(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    get_default_location_from_resource_group(cmd, namespace)
    validate_tags(namespace)

    args = [a for a in [namespace.express_route_circuit2,
                        namespace.local_gateway2,
                        namespace.vnet_gateway2]
            if a]
    if len(args) != 1:
        raise ValueError('usage error: --vnet-gateway2 NAME_OR_ID | --local-gateway2 NAME_OR_ID '
                         '| --express-route-circuit2 NAME_OR_ID')

    def _normalize_shared_key_fields(n):
        # Turn "" into None so the sdk layer won’t serialize them
        if getattr(n, 'shared_key', None) == '':
            n.shared_key = None
        if getattr(n, 'shared_key_keyvault_id', None) == '':
            n.shared_key_keyvault_id = None

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

    auth = (getattr(namespace, 'auth_type', '') or '').strip().lower()

    _normalize_shared_key_fields(namespace)

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

    if auth == 'certificate':
        # SharedKey/SharedKeyKeyvaultId should be empty when AuthenticationType is Certificate.
        # Follow the link for more details : https://go.microsoft.com/fwlink/?linkid=2208263
        if getattr(namespace, 'shared_key', None):
            namespace.shared_key = None
        if getattr(namespace, 'shared_key_keyvault_id', None):
            namespace.shared_key_keyvault_id = None


def load_cert_file(param_name):
    def load_cert_validator(namespace):
        attr = getattr(namespace, param_name)
        if attr and os.path.isfile(attr):
            setattr(namespace, param_name, read_base_64_file(attr))

    return load_cert_validator


def get_network_watcher_from_location(remove=False, watcher_name='watcher_name',
                                      rg_name='watcher_rg'):
    def _validator(cmd, namespace):
        from azure.mgmt.core.tools import parse_resource_id
        from .aaz.latest.network.watcher import List

        location = namespace.location
        watcher_list = List(cli_ctx=cmd.cli_ctx)(command_args={})
        watcher = next((w for w in watcher_list if w["location"].lower() == location.lower()), None)
        if not watcher:
            raise ValidationError(f"network watcher is not enabled for region {location}.")
        id_parts = parse_resource_id(watcher['id'])
        setattr(namespace, rg_name, id_parts['resource_group'])
        setattr(namespace, watcher_name, id_parts['name'])

        if remove:
            del namespace.location

    return _validator


def _process_vnet_name_and_id(vnet, cmd, resource_group_name):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
    if vnet and not is_valid_resource_id(vnet):
        vnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet)
    return vnet


def _process_subnet_name_and_id(subnet, vnet, cmd, resource_group_name):
    from azure.cli.core.azclierror import UnrecognizedArgumentError
    from azure.mgmt.core.tools import is_valid_resource_id
    if subnet and not is_valid_resource_id(subnet):
        vnet = _process_vnet_name_and_id(vnet, cmd, resource_group_name)
        if vnet is None:
            raise UnrecognizedArgumentError('vnet should be provided when input subnet name instead of subnet id')

        subnet = vnet + f'/subnets/{subnet}'
    return subnet


def process_nw_flow_log_show_namespace(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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


def process_lb_outbound_rule_namespace(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id

    validate_frontend_ip_configs(cmd, namespace)

    if namespace.backend_address_pool:
        if not is_valid_resource_id(namespace.backend_address_pool):
            namespace.backend_address_pool = _generate_lb_subproperty_id(
                cmd.cli_ctx, namespace, 'backendAddressPools', namespace.backend_address_pool)


def validate_ag_address_pools(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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
                values.append({'first': item_split[0], 'scope': int(item_split[1])})
                continue
        except ValueError:
            pass

        values.append({'first': item})

    namespace.subnets = values


# pylint: disable=too-few-public-methods
class WafConfigExclusionAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not namespace.exclusions:
            namespace.exclusions = []
        if isinstance(values, list):
            values = ' '.join(values)
        try:
            variable, op, selector = values.split(' ')
        except (ValueError, TypeError):
            raise CLIError('usage error: --exclusion VARIABLE OPERATOR VALUE')
        namespace.exclusions.append({
            "match_variable": variable,
            "selector_match_operator": op,
            "selector": selector
        })


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

    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
    if not is_valid_resource_id(namespace.id):
        raise CLIError("Resource ID is invalid. Please check it.")
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

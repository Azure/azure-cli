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
from azure.cli.core.azclierror import RequiredArgumentMissingError

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
    gateway_name = getattr(namespace, 'application_gateway_name', None)

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


def validate_ip_tags(namespace):
    ''' Extracts multiple space-separated tags in TYPE=VALUE format '''
    if namespace.ip_tags:
        ip_tags = []
        for item in namespace.ip_tags:
            tag_type, tag_value = item.split('=', 1)
            ip_tags.append({"ip_tag_type": tag_type, "tag": tag_value})
        namespace.ip_tags = ip_tags


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


def validate_subresource_list(cmd, namespace):
    if namespace.target_resources:
        SubResource = cmd.get_models('SubResource')
        subresources = []
        for item in namespace.target_resources:
            subresources.append(SubResource(id=item))
        namespace.target_resources = subresources


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
    if 'public_ip_prefix' in namespace:
        validate_public_ip_prefix(cmd, namespace)
    if 'ip_tags' in namespace:
        validate_ip_tags(namespace)
    validate_tags(namespace)
    if 'sku' in namespace or 'zone' in namespace:
        _inform_coming_breaking_change_for_public_ip(namespace)


def _inform_coming_breaking_change_for_public_ip(namespace):
    if namespace.sku == 'Standard' and not namespace.zone:
        logger.warning('[Coming breaking change] In the coming release, the default behavior will be changed as follows'
                       ' when sku is Standard and zone is not provided:'
                       ' For zonal regions, you will get a zone-redundant IP indicated by zones:["1","2","3"];'
                       ' For non-zonal regions, you will get a non zone-redundant IP indicated by zones:null.')


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


def get_network_watcher_from_vmss(cmd, namespace):
    from msrestazure.tools import parse_resource_id

    compute_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_COMPUTE).virtual_machine_scale_sets
    vmss_name = parse_resource_id(namespace.target)['name']
    vmss = compute_client.get(namespace.resource_group_name, vmss_name)
    namespace.location = vmss.location  # pylint: disable=no-member
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

# pylint: disable=protected-access,too-few-public-methods
def _process_vnet_name_and_id(vnet, cmd, resource_group_name):
    from msrestazure.tools import is_valid_resource_id, resource_id
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
    from msrestazure.tools import is_valid_resource_id
    if subnet and not is_valid_resource_id(subnet):
        vnet = _process_vnet_name_and_id(vnet, cmd, resource_group_name)
        if vnet is None:
            raise UnrecognizedArgumentError('vnet should be provided when input subnet name instead of subnet id')

        subnet = vnet + f'/subnets/{subnet}'
    return subnet


def process_lb_outbound_rule_namespace(cmd, namespace):
    from msrestazure.tools import is_valid_resource_id

    validate_frontend_ip_configs(cmd, namespace)

    if namespace.backend_address_pool:
        if not is_valid_resource_id(namespace.backend_address_pool):
            namespace.backend_address_pool = _generate_lb_subproperty_id(
                cmd.cli_ctx, namespace, 'backendAddressPools', namespace.backend_address_pool)


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

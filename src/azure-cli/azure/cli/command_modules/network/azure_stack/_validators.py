# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.commands.validators import \
    (validate_tags, get_default_location_from_resource_group)
from azure.cli.core.commands.template_create import get_folded_parameter_validator
from azure.cli.core.commands.client_factory import get_subscription_id

logger = get_logger(__name__)


def get_vnet_validator(dest):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id

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


def validate_address_pool_name_or_id(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, parse_resource_id
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


def validate_ip_tags(namespace):
    ''' Extracts multiple space-separated tags in TYPE=VALUE format '''
    if namespace.ip_tags:
        ip_tags = []
        for item in namespace.ip_tags:
            tag_type, tag_value = item.split('=', 1)
            ip_tags.append({"ip_tag_type": tag_type, "tag": tag_value})
        namespace.ip_tags = ip_tags


def validate_metadata(namespace):
    if namespace.metadata:
        namespace.metadata = dict(x.split('=', 1) for x in namespace.metadata)


def validate_public_ip_prefix(cmd, namespace):
    from azure.mgmt.core.tools import is_valid_resource_id, resource_id
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


def validate_subresource_list(cmd, namespace):
    if namespace.target_resources:
        SubResource = cmd.get_models('SubResource')
        subresources = []
        for item in namespace.target_resources:
            subresources.append(SubResource(id=item))
        namespace.target_resources = subresources


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

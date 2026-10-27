# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import get_subscription_id
from ._client_factory import cf_acr_registries
from ._utils import validate_premium_registry


NETWORK_RULE_NOT_SUPPORTED = 'Network rules are only supported for managed registries in Premium SKU.'


def _get_enum_value(value):
    return getattr(value, 'value', value)


def _format_virtual_network_rule(rule):
    """Preserve the legacy field while surfacing the SDK's subnet resource ID."""
    subnet_id = rule.virtual_network_subnet_resource_id
    return {
        'virtualNetworkResourceId': subnet_id,
        'virtualNetworkSubnetResourceId': subnet_id,
        'action': _get_enum_value(rule.action) or 'Allow',
    }


def _format_registry_response(registry):
    """Format the registry SDK model for CLI output."""
    network_rule_set = registry.network_rule_set
    virtual_network_rules = []
    ip_rules = []
    if network_rule_set:
        virtual_network_rules = [
            _format_virtual_network_rule(rule)
            for rule in (network_rule_set.virtual_network_rules or [])
        ]
        ip_rules = [
            {
                'ipAddressOrRange': rule.ip_address_or_range,
                'action': _get_enum_value(rule.action) or 'Allow',
            }
            for rule in (network_rule_set.ip_rules or [])
        ]

    return {
        'name': registry.name,
        'provisioningState': _get_enum_value(registry.provisioning_state),
        'networkRuleSet': {
            'defaultAction': _get_enum_value(network_rule_set.default_action) if network_rule_set else None,
            'virtualNetworkRules': virtual_network_rules,
            'ipRules': ip_rules,
        },
    }


def _get_network_rule_set(cmd, registry):
    if registry.network_rule_set:
        return registry.network_rule_set
    NetworkRuleSet = cmd.get_models('NetworkRuleSet')
    return NetworkRuleSet(default_action='Allow')


def _update_registry(cmd, resource_group_name, registry_name, network_rule_set):
    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(network_rule_set=network_rule_set)
    client = cf_acr_registries(cmd.cli_ctx)
    return LongRunningOperation(cmd.cli_ctx)(
        client.begin_update(resource_group_name, registry_name, parameters)
    )


def acr_network_rule_list(cmd, registry_name, resource_group_name=None):
    registry, _ = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    network_rule_set = _format_registry_response(registry)['networkRuleSet']
    return {'virtualNetworkRules': network_rule_set['virtualNetworkRules'], 'ipRules': network_rule_set['ipRules']}


def acr_network_rule_add(cmd,
                         registry_name,
                         subnet=None,
                         vnet_name=None,
                         ip_address=None,
                         resource_group_name=None):
    registry, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    VirtualNetworkRule, IPRule = cmd.get_models('VirtualNetworkRule', 'IPRule')
    rules = _get_network_rule_set(cmd, registry)

    if subnet or vnet_name:
        virtual_network_rules = list(rules.virtual_network_rules or [])
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
        virtual_network_rules.append(
            VirtualNetworkRule(virtual_network_subnet_resource_id=subnet_id, action='Allow')
        )
        rules.virtual_network_rules = virtual_network_rules

    if ip_address:
        ip_rules = list(rules.ip_rules or [])
        ip_rules.append(IPRule(ip_address_or_range=ip_address, action='Allow'))
        rules.ip_rules = ip_rules

    response = _update_registry(cmd, resource_group_name, registry_name, rules)
    return _format_registry_response(response)


def acr_network_rule_remove(cmd,
                            registry_name,
                            subnet=None,
                            vnet_name=None,
                            ip_address=None,
                            resource_group_name=None):
    registry, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    rules = _get_network_rule_set(cmd, registry)

    if subnet or vnet_name:
        virtual_network_rules = list(rules.virtual_network_rules or [])
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name).lower()
        rules.virtual_network_rules = [
            x for x in virtual_network_rules
            if (x.virtual_network_subnet_resource_id or '').lower() != subnet_id
        ]

    if ip_address:
        ip_rules = list(rules.ip_rules or [])
        rules.ip_rules = [
            x for x in ip_rules
            if x.ip_address_or_range != ip_address
        ]

    response = _update_registry(cmd, resource_group_name, registry_name, rules)
    return _format_registry_response(response)


def _validate_subnet(cli_ctx, subnet, vnet_name, resource_group_name):
    from azure.mgmt.core.tools import is_valid_resource_id
    subnet_is_id = is_valid_resource_id(subnet)

    if subnet_is_id and not vnet_name:
        return subnet
    if subnet and not subnet_is_id and vnet_name:
        from azure.mgmt.core.tools import resource_id
        return resource_id(
            subscription=get_subscription_id(cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_name,
            child_type_1='subnets',
            child_name_1=subnet)
    raise CLIError('Usage error: [--subnet ID | --subnet NAME --vnet-name NAME]')

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from ._utils import validate_premium_registry
from ._client_factory import cf_acr_network_rules


# API version that supports virtual network rules
NETWORK_RULE_API_VERSION = "2021-08-01-preview"

NETWORK_RULE_NOT_SUPPORTED = 'Network rules are only supported for managed registries in Premium SKU.'


def _get_virtual_network_rules(network_rule_set):
    """Get virtual network rules from network_rule_set.additional_properties."""
    if network_rule_set is None:
        return []
    return network_rule_set.additional_properties.get('virtualNetworkRules', [])


def _set_virtual_network_rules(network_rule_set, vnet_rules):
    """Set virtual network rules on network_rule_set using additional_properties."""
    network_rule_set.enable_additional_properties_sending()
    # Serialize VirtualNetworkRule objects to dicts
    serialized = []
    for rule in vnet_rules:
        if hasattr(rule, 'serialize'):
            serialized.append(rule.serialize())
        else:
            serialized.append(rule)
    network_rule_set.additional_properties['virtualNetworkRules'] = serialized


# Used in commands.py for command group acr network-rule
def _transform_network_rule_response(result):
    """Transform the registry response to use virtualNetworkResourceId instead of id.

    The 2021-08-01-preview API returns virtualNetworkRules with 'id' field,
    but for CLI compatibility we need 'virtualNetworkResourceId'.
    """
    # If result is a poller, wait for the result
    from azure.core.polling import LROPoller
    if isinstance(result, LROPoller):
        registry = result.result()
    else:
        registry = result

    return _transform_registry_network_rules(registry)


def _transform_registry_network_rules(registry):
    """Transform a Registry object's networkRuleSet to use virtualNetworkResourceId.

    This modifies the registry's network_rule_set additional_properties in place,
    then returns the registry object for the CLI to serialize normally.
    """
    if registry is None:
        return registry

    # Get the network rule set
    nrs = getattr(registry, 'network_rule_set', None)
    if nrs is None:
        return registry

    # Get virtualNetworkRules from additional_properties
    vnet_rules = nrs.additional_properties.get('virtualNetworkRules', [])

    # Transform the rules in place to use virtualNetworkResourceId
    transformed = []
    for rule in vnet_rules:
        if isinstance(rule, dict):
            transformed.append({
                'virtualNetworkResourceId': rule.get('id'),
                'action': rule.get('action', 'Allow')
            })
        else:
            transformed.append({
                'virtualNetworkResourceId': getattr(rule, 'id', None),
                'action': getattr(rule, 'action', 'Allow')
            })

    # Replace in additional_properties
    nrs.additional_properties['virtualNetworkRules'] = transformed

    # Return the registry object - CLI will handle serialization
    return registry


def acr_network_rule_list(cmd, registry_name, resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    client = cf_acr_network_rules(cmd.cli_ctx)
    registry = client.get(resource_group_name, registry_name, api_version=NETWORK_RULE_API_VERSION)
    rules = registry.network_rule_set

    # Transform response to use virtualNetworkResourceId for compatibility
    vnet_rules = []
    for rule in _get_virtual_network_rules(rules):
        vnet_rules.append({
            'virtualNetworkResourceId': rule.get('id'),
            'action': rule.get('action', 'Allow')
        })

    return {
        'ipRules': [{'ipAddressOrRange': r.ip_address_or_range, 'action': r.action} for r in (rules.ip_rules or [])],
        'virtualNetworkRules': vnet_rules
    }


def acr_network_rule_add(cmd,
                         client,
                         registry_name,
                         subnet=None,
                         vnet_name=None,
                         ip_address=None,
                         resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    client = cf_acr_network_rules(cmd.cli_ctx)
    registry = client.get(resource_group_name, registry_name, api_version=NETWORK_RULE_API_VERSION)

    rules = registry.network_rule_set

    if subnet or vnet_name:
        vnet_rules = _get_virtual_network_rules(rules)
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
        vnet_rules.append({'id': subnet_id, 'action': 'Allow'})
        _set_virtual_network_rules(rules, vnet_rules)

    if ip_address:
        rules.ip_rules = rules.ip_rules if rules.ip_rules else []
        IPRule = cmd.get_models('IPRule')
        rules.ip_rules.append(IPRule(ip_address_or_range=ip_address))

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(network_rule_set=rules)
    return client.begin_update(resource_group_name, registry_name, parameters, api_version=NETWORK_RULE_API_VERSION)


def acr_network_rule_remove(cmd,
                            client,
                            registry_name,
                            subnet=None,
                            vnet_name=None,
                            ip_address=None,
                            resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    client = cf_acr_network_rules(cmd.cli_ctx)
    registry = client.get(resource_group_name, registry_name, api_version=NETWORK_RULE_API_VERSION)
    rules = registry.network_rule_set

    if subnet or vnet_name:
        vnet_rules = _get_virtual_network_rules(rules)
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name).lower()
        vnet_rules = [x for x in vnet_rules if x.get('id', '').lower() != subnet_id]
        _set_virtual_network_rules(rules, vnet_rules)

    if ip_address:
        rules.ip_rules = rules.ip_rules if rules.ip_rules else []
        rules.ip_rules = [x for x in rules.ip_rules if x.ip_address_or_range != ip_address]

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(network_rule_set=rules)
    return client.begin_update(resource_group_name, registry_name, parameters, api_version=NETWORK_RULE_API_VERSION)


def _validate_subnet(cli_ctx, subnet, vnet_name, resource_group_name):
    from azure.mgmt.core.tools import is_valid_resource_id
    subnet_is_id = is_valid_resource_id(subnet)

    if subnet_is_id and not vnet_name:
        return subnet
    if subnet and not subnet_is_id and vnet_name:
        from azure.mgmt.core.tools import resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id
        return resource_id(
            subscription=get_subscription_id(cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_name,
            child_type_1='subnets',
            child_name_1=subnet)
    raise CLIError('Usage error: [--subnet ID | --subnet NAME --vnet-name NAME]')

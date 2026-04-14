# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from knack.util import CLIError
from azure.cli.core.util import send_raw_request
from azure.cli.core.commands.client_factory import get_subscription_id
from ._utils import validate_premium_registry


NETWORK_RULE_NOT_SUPPORTED = 'Network rules are only supported for managed registries in Premium SKU.'
# TODO: The networkRuleSet property was unintentionally removed from preview APIs.
# This was not previously exposed, because of multi-api support in the Python SDK.
# The Python SDK no longer supports multi-api, highlighting this issue.
# Until the next preview API release is deployed, this code uses direct REST calls to get and update
# the registry's networkRuleSet. Once the next preview API is released, this code should be updated
# to use the SDK methods to get and update the networkRuleSet, and the api version should be updated
# to reflect the latest API version, rather than hard coded, as it currently is below.
API_VERSION = "2021-08-01-preview"


def _get_registry_url(cli_ctx, resource_group_name, registry_name):
    """Build the REST API URL for a registry."""
    subscription_id = get_subscription_id(cli_ctx)
    return (
        "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.ContainerRegistry/registries/{}?api-version={}"
        .format(subscription_id, resource_group_name, registry_name, API_VERSION)
    )


def _get_registry(cli_ctx, resource_group_name, registry_name):
    """Get registry using REST API."""
    url = _get_registry_url(cli_ctx, resource_group_name, registry_name)
    response = send_raw_request(cli_ctx, "GET", url)
    return response.json()


def _update_registry(cli_ctx, resource_group_name, registry_name, update_payload):
    """Update registry using REST API (PATCH)."""
    url = _get_registry_url(cli_ctx, resource_group_name, registry_name)
    response = send_raw_request(cli_ctx, "PATCH", url, body=json.dumps(update_payload))
    return response.json()


def _format_registry_response(response):
    """Format the registry REST response for CLI output."""
    properties = response.get('properties', {})
    network_rule_set = properties.get('networkRuleSet', {})

    virtual_network_rules = [
        {'virtualNetworkResourceId': rule.get('id'), 'action': rule.get('action', 'Allow')}
        for rule in (network_rule_set.get('virtualNetworkRules') or [])
    ]
    ip_rules = [
        {'ipAddressOrRange': rule.get('value') or rule.get('ipAddressOrRange'), 'action': rule.get('action', 'Allow')}
        for rule in (network_rule_set.get('ipRules') or [])
    ]

    return {
        'name': response.get('name'),
        'provisioningState': properties.get('provisioningState'),
        'networkRuleSet': {
            'defaultAction': network_rule_set.get('defaultAction'),
            'virtualNetworkRules': virtual_network_rules,
            'ipRules': ip_rules,
        },
    }


def acr_network_rule_list(cmd, registry_name, resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    registry = _get_registry(cmd.cli_ctx, resource_group_name, registry_name)
    network_rule_set = _format_registry_response(registry)['networkRuleSet']
    return {'virtualNetworkRules': network_rule_set['virtualNetworkRules'], 'ipRules': network_rule_set['ipRules']}


def acr_network_rule_add(cmd,
                         registry_name,
                         subnet=None,
                         vnet_name=None,
                         ip_address=None,
                         resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    registry = _get_registry(cmd.cli_ctx, resource_group_name, registry_name)
    rules = registry.get('properties', {}).get('networkRuleSet', {})

    if subnet or vnet_name:
        virtual_network_rules = list(rules.get('virtualNetworkRules') or [])
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
        virtual_network_rules.append({'id': subnet_id, 'action': 'Allow'})
        rules['virtualNetworkRules'] = virtual_network_rules

    if ip_address:
        ip_rules = list(rules.get('ipRules') or [])
        ip_rules.append({'value': ip_address, 'action': 'Allow'})
        rules['ipRules'] = ip_rules

    response = _update_registry(cmd.cli_ctx, resource_group_name, registry_name,
                                {'properties': {'networkRuleSet': rules}})
    return _format_registry_response(response)


def acr_network_rule_remove(cmd,
                            registry_name,
                            subnet=None,
                            vnet_name=None,
                            ip_address=None,
                            resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    registry = _get_registry(cmd.cli_ctx, resource_group_name, registry_name)
    rules = registry.get('properties', {}).get('networkRuleSet', {})

    if subnet or vnet_name:
        virtual_network_rules = list(rules.get('virtualNetworkRules') or [])
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name).lower()
        rules['virtualNetworkRules'] = [
            x for x in virtual_network_rules if x.get('id', '').lower() != subnet_id
        ]

    if ip_address:
        ip_rules = list(rules.get('ipRules') or [])
        rules['ipRules'] = [
            x for x in ip_rules
            if (x.get('value') or x.get('ipAddressOrRange')) != ip_address
        ]

    response = _update_registry(cmd.cli_ctx, resource_group_name, registry_name,
                                {'properties': {'networkRuleSet': rules}})
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

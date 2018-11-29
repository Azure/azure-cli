# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError

from azure.mgmt.containerregistry.v2018_09_01.models import (
    VirtualNetworkRule,
    RegistryUpdateParameters
)

from ._utils import validate_premium_registry


NETWORK_RULE_NOT_SUPPORTED = 'Network rules are only supported for managed registries in Premium SKU.'


def acr_network_rule_list(cmd, registry_name, resource_group_name=None):
    registry, _ = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)
    rules = registry.network_rule_set
    delattr(rules, 'default_action')
    return rules


def acr_network_rule_add(cmd,
                         client,
                         registry_name,
                         subnet,
                         vnet_name=None,
                         resource_group_name=None):
    registry, resource_group_name = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)
    subnet_id = validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
    rules = registry.network_rule_set

    if not rules.virtual_network_rules:
        rules.virtual_network_rules = []
    rules.virtual_network_rules.append(VirtualNetworkRule(id=subnet_id))

    parameters = RegistryUpdateParameters(network_rule_set=rules)
    return client.update(resource_group_name, registry_name, parameters)


def acr_network_rule_remove(cmd,
                            client,
                            registry_name,
                            subnet,
                            vnet_name=None,
                            resource_group_name=None):
    registry, resource_group_name = validate_premium_registry(
        cmd.cli_ctx, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)
    subnet_id = validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name).lower()
    rules = registry.network_rule_set

    rules.virtual_network_rules = [x for x in rules.virtual_network_rules if x.id.lower() != subnet_id]

    parameters = RegistryUpdateParameters(network_rule_set=rules)
    return client.update(resource_group_name, registry_name, parameters)


def validate_subnet(cli_ctx, subnet, vnet_name, resource_group_name):
    from msrestazure.tools import is_valid_resource_id
    subnet_is_id = is_valid_resource_id(subnet)

    if subnet_is_id and not vnet_name:
        return subnet
    elif subnet and not subnet_is_id and vnet_name:
        from msrestazure.tools import resource_id
        from azure.cli.core.commands.client_factory import get_subscription_id
        return resource_id(
            subscription=get_subscription_id(cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet_name,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        raise CLIError('Usage error: [--subnet ID | --subnet NAME --vnet-name NAME]')

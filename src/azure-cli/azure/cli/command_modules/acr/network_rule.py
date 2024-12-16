# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from ._utils import validate_premium_registry
from ._client_factory import cf_acr_network_rules
from typing import Optional, Union
import msrest.serialization


class VirtualNetworkRule(msrest.serialization.Model):
    """Virtual network rule.
    All required parameters must be populated in order to send to Azure.
    :ivar action: The action of virtual network rule. Possible values include: "Allow".
    :vartype action: str or ~azure.mgmt.containerregistry.v2021_08_01_preview.models.Action
    :ivar virtual_network_resource_id: Required. Resource ID of a subnet, for example:
     '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/
     providers/Microsoft.Network/virtualNetworks/{vnetName}/subnets/{subnetName}.'
    :vartype virtual_network_resource_id: str
    """

    _validation = {
        'virtual_network_resource_id': {'required': True},
    }

    _attribute_map = {
        'action': {'key': 'action', 'type': 'str'},
        'virtual_network_resource_id': {'key': 'id', 'type': 'str'},
    }

    def __init__(
        self,
        *,
        virtual_network_resource_id: str,
        action: Optional[Union[str, "Action"]] = None,  # noqa: F821
        **kwargs
    ):
        """
        :keyword action: The action of virtual network rule. Possible values include: "Allow".
        :paramtype action: str or ~azure.mgmt.containerregistry.v2021_08_01_preview.models.Action
        :keyword virtual_network_resource_id: Required. Resource ID of a subnet, for example:
         '/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/
         providers/Microsoft.Network/virtualNetworks/{vnetName}/subnets/{subnetName}.'
        :paramtype virtual_network_resource_id: str
        """
        super().__init__(**kwargs)
        self.action = action
        self.virtual_network_resource_id = virtual_network_resource_id


NETWORK_RULE_NOT_SUPPORTED = 'Network rules are only supported for managed registries in Premium SKU.'


def acr_network_rule_list(cmd, registry_name, resource_group_name=None):
    _, resource_group_name = validate_premium_registry(
        cmd, registry_name, resource_group_name, NETWORK_RULE_NOT_SUPPORTED)

    client = cf_acr_network_rules(cmd.cli_ctx)
    registry = client.get(resource_group_name, registry_name)
    rules = registry.network_rule_set
    delattr(rules, 'default_action')
    return rules


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
    registry = client.get(resource_group_name, registry_name)

    rules = registry.network_rule_set

    if subnet or vnet_name:
        rules.virtual_network_rules = rules.virtual_network_rules if rules.virtual_network_rules else []
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name)
        rules.virtual_network_rules.append(VirtualNetworkRule(virtual_network_resource_id=subnet_id))
    if ip_address:
        rules.ip_rules = rules.ip_rules if rules.ip_rules else []
        IPRule = cmd.get_models('IPRule')
        rules.ip_rules.append(IPRule(ip_address_or_range=ip_address))

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(network_rule_set=rules)
    return client.begin_update(resource_group_name, registry_name, parameters)


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
    registry = client.get(resource_group_name, registry_name)
    rules = registry.network_rule_set

    if subnet or vnet_name:
        rules.virtual_network_rules = rules.virtual_network_rules if rules.virtual_network_rules else []
        subnet_id = _validate_subnet(cmd.cli_ctx, subnet, vnet_name, resource_group_name).lower()
        rules.virtual_network_rules = [
            x for x in rules.virtual_network_rules if x.virtual_network_resource_id.lower() != subnet_id]
    if ip_address:
        rules.ip_rules = rules.ip_rules if rules.ip_rules else []
        rules.ip_rules = [x for x in rules.ip_rules if x.ip_address_or_range != ip_address]

    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    parameters = RegistryUpdateParameters(network_rule_set=rules)
    return client.begin_update(resource_group_name, registry_name, parameters)


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

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from msrestazure.tools import resource_id

from azure.cli.core.util import sdk_no_wait
from azure.cli.core.commands.client_factory import get_subscription_id

logger = get_logger(__name__)


def network_client_factory(cli_ctx, **kwargs):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK, **kwargs)


def create_nat_gateway(cmd, nat_gateway_name, resource_group_name,
                       location=None, public_ip_addresses=None,
                       public_ip_prefixes=None, idle_timeout=None, no_wait=False):

    SubResource = cmd.get_models('SubResource')
    public_ip_prefixes_natgateway = []
    public_ip_addresses_natgateway = []

    if public_ip_addresses is not None and public_ip_prefixes is not None:
        logger.error("public_ip_addresses OR public_ip_prefixes required")

    if public_ip_addresses is not None:
        for i in public_ip_addresses.split(','):
            public_ip_addresses_natgateway.append(SubResource(id=resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.Network', type='publicIPAddresses',
                name=i)))

    if public_ip_prefixes is not None:
        for i in public_ip_prefixes.split(','):
            public_ip_prefixes_natgateway.append(SubResource(id=resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.Network', type='publicIPPrefixes',
                name=i)))

    client = network_client_factory(cmd.cli_ctx).nat_gateways
    NatGateway, NatGatewaySku = cmd.get_models('NatGateway', 'NatGatewaySku')

    nat_gateway = NatGateway(name=nat_gateway_name,
                             location=location,
                             sku=NatGatewaySku(name='Standard'),
                             idle_timeout_in_minutes=idle_timeout,
                             public_ip_addresses=public_ip_addresses_natgateway,
                             public_ip_prefixes=public_ip_prefixes_natgateway)

    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, nat_gateway_name, nat_gateway)


def update_nat_gateway(instance, cmd, resource_group_name, public_ip_addresses=None,
                       public_ip_prefixes=None, idle_timeout=None):

    SubResource = cmd.get_models('SubResource')
    public_ip_prefixes_natgateway = []
    public_ip_addresses_natgateway = []

    if public_ip_addresses is not None and public_ip_prefixes is not None:
        logger.error("public_ip_addresses OR public_ip_prefixes required")

    if public_ip_addresses is not None:
        for i in public_ip_addresses.split(','):
            public_ip_addresses_natgateway.append(SubResource(id=resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.Network', type='publicIPAddresses',
                name=i)))

    if public_ip_prefixes is not None:
        for i in public_ip_prefixes.split(','):
            public_ip_prefixes_natgateway.append(SubResource(id=resource_id(
                subscription=get_subscription_id(cmd.cli_ctx),
                resource_group=resource_group_name,
                namespace='Microsoft.Network', type='publicIPPrefixes',
                name=i)))

    with cmd.update_context(instance) as c:
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        if public_ip_addresses is not None:
            c.set_param('public_ip_addresses', public_ip_addresses_natgateway)
        if public_ip_prefixes_natgateway is not None:
            c.set_param('public_ip_prefixes', public_ip_prefixes_natgateway)
    return instance


def list_nat_gateway(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).nat_gateways
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_all()


def show_nat_gateway(cmd, resource_group_name, nat_gateway_name):
    client = network_client_factory(cmd.cli_ctx).nat_gateways
    return client.get(resource_group_name, nat_gateway_name)

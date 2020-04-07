# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import sdk_no_wait

from knack.log import get_logger

logger = get_logger(__name__)


def network_client_factory(cli_ctx, **kwargs):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK, **kwargs)


def create_nat_gateway(cmd, nat_gateway_name, resource_group_name,
                       location=None, public_ip_addresses=None,
                       public_ip_prefixes=None, idle_timeout=None, zone=None, no_wait=False):

    client = network_client_factory(cmd.cli_ctx).nat_gateways
    NatGateway, NatGatewaySku = cmd.get_models('NatGateway', 'NatGatewaySku')

    nat_gateway = NatGateway(name=nat_gateway_name,
                             location=location,
                             sku=NatGatewaySku(name='Standard'),
                             idle_timeout_in_minutes=idle_timeout,
                             zones=zone,
                             public_ip_addresses=public_ip_addresses,
                             public_ip_prefixes=public_ip_prefixes)

    return sdk_no_wait(no_wait, client.create_or_update, resource_group_name, nat_gateway_name, nat_gateway)


def update_nat_gateway(instance, cmd, public_ip_addresses=None,
                       public_ip_prefixes=None, idle_timeout=None):

    with cmd.update_context(instance) as c:
        c.set_param('idle_timeout_in_minutes', idle_timeout)
        if public_ip_addresses is not None:
            c.set_param('public_ip_addresses', public_ip_addresses)
        if public_ip_prefixes is not None:
            c.set_param('public_ip_prefixes', public_ip_prefixes)
    return instance


def list_nat_gateway(cmd, resource_group_name=None):
    client = network_client_factory(cmd.cli_ctx).nat_gateways
    if resource_group_name:
        return client.list(resource_group_name)
    return client.list_all()

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def network_client_factory(cli_ctx, **kwargs):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK, **kwargs)


def resource_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def cf_load_balancers(cli_ctx, _):
    return network_client_factory(cli_ctx).load_balancers


def cf_load_balancer_backend_pools(cli_ctx, _):
    return network_client_factory(cli_ctx).load_balancer_backend_address_pools


def cf_network_interfaces(cli_ctx, _):
    return network_client_factory(cli_ctx).network_interfaces


def cf_private_access(cli_ctx, _):
    return network_client_factory(cli_ctx).available_private_access_services


def cf_subnets(cli_ctx, _):
    return network_client_factory(cli_ctx).subnets


def cf_usages(cli_ctx, _):
    return network_client_factory(cli_ctx).usages


def cf_virtual_network_gateway_connections(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_gateway_connections


def cf_virtual_network_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_gateways


def cf_virtual_networks(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_networks


def cf_virtual_network_peerings(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_peerings


def cf_dns_references(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).dns_resource_reference


def cf_dns_mgmt_zones(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).zones


def cf_dns_mgmt_record_sets(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets

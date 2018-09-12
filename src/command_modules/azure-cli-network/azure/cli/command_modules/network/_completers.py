# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.network._client_factory import network_client_factory
from azure.cli.command_modules.network.custom import list_traffic_manager_endpoints


# pylint: disable=inconsistent-return-statements
@Completer
def subnet_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    client = network_client_factory(cmd.cli_ctx)
    if namespace.resource_group_name and namespace.virtual_network_name:
        rg = namespace.resource_group_name
        vnet = namespace.virtual_network_name
        return [r.name for r in client.subnets.list(resource_group_name=rg, virtual_network_name=vnet)]


def get_lb_subresource_completion_list(prop):

    # pylint: disable=inconsistent-return-statements
    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        client = network_client_factory(cmd.cli_ctx)
        try:
            lb_name = namespace.load_balancer_name
        except AttributeError:
            lb_name = namespace.resource_name
        if namespace.resource_group_name and lb_name:
            lb = client.load_balancers.get(namespace.resource_group_name, lb_name)
            return [r.name for r in getattr(lb, prop)]
    return completer


def get_ag_subresource_completion_list(prop):

    # pylint: disable=inconsistent-return-statements
    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        client = network_client_factory(cmd.cli_ctx)
        try:
            ag_name = namespace.application_gateway_name
        except AttributeError:
            ag_name = namespace.resource_name
        if namespace.resource_group_name and ag_name:
            ag = client.application_gateways.get(namespace.resource_group_name, ag_name)
            return [r.name for r in getattr(ag, prop)]
    return completer


# pylint: disable=inconsistent-return-statements
@Completer
def ag_url_map_rule_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    client = network_client_factory(cmd.cli_ctx)
    try:
        ag_name = namespace.application_gateway_name
    except AttributeError:
        ag_name = namespace.resource_name
    if namespace.resource_group_name and ag_name:
        ag = client.application_gateways.get(namespace.resource_group_name, ag_name)
        url_map = next((x for x in ag.url_path_maps if x.name == namespace.url_path_map_name), None)  # pylint: disable=no-member
        return [r.name for r in url_map.path_rules]


@Completer
def tm_endpoint_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    return list_traffic_manager_endpoints(cmd, namespace.resource_group_name, namespace.profile_name) \
        if namespace.resource_group_name and namespace.profile_name \
        else []


@Completer
def service_endpoint_completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    client = network_client_factory(cmd.cli_ctx).available_endpoint_services
    location = namespace.location
    return [x.name for x in client.list(location=location)]

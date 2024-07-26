# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.network.custom import list_traffic_manager_endpoints


# pylint: disable=inconsistent-return-statements
@Completer
def subnet_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    from .aaz.latest.network.vnet.subnet import List
    if namespace.resource_group_name and namespace.virtual_network_name:
        rg = namespace.resource_group_name
        vnet = namespace.virtual_network_name
        subnets = List(cli_ctx=cmd.cli_ctx)(command_args={
            "vnet_name": vnet,
            "resource_group": rg
        })
        return [r["name"] for r in subnets]


def get_lb_subresource_completion_list(prop):

    # pylint: disable=inconsistent-return-statements
    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        from .aaz.latest.network.lb import Show
        try:
            lb_name = namespace.load_balancer_name
        except AttributeError:
            lb_name = namespace.resource_name
        if namespace.resource_group_name and lb_name:
            lb = Show(cli_ctx=cmd.cli_ctx)(command_args={
                "name": lb_name,
                "resource_group": namespace.resource_group_name
            })
            return [r["name"] for r in lb.get(prop, [])]
    return completer


def get_ag_subresource_completion_list(prop):

    # pylint: disable=inconsistent-return-statements
    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        from .aaz.latest.network.application_gateway import Show
        try:
            ag_name = namespace.application_gateway_name
        except AttributeError:
            ag_name = namespace.resource_name
        if namespace.resource_group_name and ag_name:
            ag = Show(cli_ctx=cmd.cli_ctx)(command_args={
                "name": ag_name,
                "resource_group": namespace.resource_group_name
            })
            return [r["name"] for r in ag.get(prop, [])]
    return completer


@Completer
def tm_endpoint_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    return list_traffic_manager_endpoints(cmd, namespace.resource_group_name, namespace.profile_name) \
        if namespace.resource_group_name and namespace.profile_name \
        else []

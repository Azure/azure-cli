# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.network.azure_stack._client_factory import network_client_factory


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

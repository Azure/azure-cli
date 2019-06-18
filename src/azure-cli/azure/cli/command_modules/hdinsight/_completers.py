# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import threading

from azure.cli.core.commands.parameters import get_resources_in_subscription
from azure.cli.core.decorators import Completer
from ._client_factory import cf_network, cf_graph


COMPLETION_TIME_OUT = 10


# pylint: disable=inconsistent-return-statements
@Completer
def subnet_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument

    def worker(cmd, prefix, namespace):  # pylint: disable=unused-argument
        from msrestazure.tools import parse_resource_id
        client = cf_network(cmd.cli_ctx)
        subnets = []
        vnets = get_resources_in_subscription(cmd.cli_ctx, 'Microsoft.Network/virtualNetworks')
        if namespace.vnet_name and vnets:
            vnets = [r for r in vnets if r.name.lower() == namespace.vnet_name.lower()]
            for vnet in vnets:
                vnet_resource_group = parse_resource_id(vnet.id)['resource_group']
                for subnet in client.subnets.list(
                        resource_group_name=vnet_resource_group,
                        virtual_network_name=namespace.vnet_name):
                    subnets.append(subnet.name)
        return subnets

    return HDInsightCompleter(worker=worker).complete(cmd, prefix, namespace)


@Completer
def cluster_admin_account_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument

    def worker(cmd, prefix, namespace):  # pylint: disable=unused-argument
        client = cf_graph(cmd.cli_ctx)
        filter_str = "startswith(userPrincipalName, '{0}') or startswith(mail, '{0}')" \
                     .format(prefix) if prefix else None
        users = client.users.list(filter=filter_str).advance_page()
        return [user.mail if ("#EXT#" in user.user_principal_name) else user.user_principal_name for user in users]

    return HDInsightCompleter(worker=worker).complete(cmd, prefix, namespace)


@Completer
def cluster_user_group_completion_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument

    def worker(cmd, prefix, namespace):  # pylint: disable=unused-argument
        client = cf_graph(cmd.cli_ctx)
        filter_str = "startswith(displayName, '{}')".format(prefix) if prefix else None
        groups = client.groups.list(filter=filter_str).advance_page()
        return [group.display_name for group in groups]

    return HDInsightCompleter(worker=worker).complete(cmd, prefix, namespace)


def get_resource_name_completion_list_under_subscription(resource_type):

    @Completer
    def completer(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
        return [r.name for r in get_resources_in_subscription(cmd.cli_ctx, resource_type)]

    return completer


class HDInsightCompleter():

    def __init__(self, worker=None, timeout=COMPLETION_TIME_OUT):
        self.worker = worker
        self.timeout = timeout
        self.worker_result = []

    def complete(self, cmd, prefix, namespace):  # pylint: disable=unused-argument
        thread = threading.Thread(target=self.complete_worker, args=[self.worker, cmd, prefix, namespace])
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout)
        return self.worker_result

    def complete_worker(self, worker, cmd, prefix, namespace):
        self.worker_result = worker(cmd, prefix, namespace)

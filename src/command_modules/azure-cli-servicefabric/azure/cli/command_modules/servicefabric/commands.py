# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import servicefabric_fabric_client_factory


def load_command_table(self, _):
    cluster_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabric.operations.clusters_operations#ClustersOperations.{}',
        client_factory=servicefabric_fabric_client_factory
    )

    with self.command_group('sf cluster', cluster_mgmt_util, client_factory=servicefabric_fabric_client_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_cluster')
        g.custom_command('create', 'new_cluster')
        g.custom_command('certificate add', 'add_cluster_cert')
        g.custom_command('certificate remove', 'remove_cluster_cert')
        g.custom_command('client-certificate add', 'add_client_cert')
        g.custom_command('client-certificate remove', 'remove_client_cert')
        g.custom_command('setting set', 'set_cluster_setting')
        g.custom_command('setting remove', 'remove_cluster_setting')
        g.custom_command('reliability update', 'update_cluster_reliability_level')
        g.custom_command('durability update', 'update_cluster_durability')
        g.custom_command('node-type add', 'add_cluster_node_type')
        g.custom_command('node add', 'add_cluster_node')
        g.custom_command('node remove', 'remove_cluster_node')
        g.custom_command('upgrade-type set', 'update_cluster_upgrade_type')

    with self.command_group('sf application certificate') as g:
        g.custom_command('add', 'add_app_cert')

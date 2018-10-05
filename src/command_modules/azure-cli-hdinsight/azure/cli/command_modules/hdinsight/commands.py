# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import cf_hdinsight_clusters

    hdinsight_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.clusters_operations#ClustersOperations.{}',
        client_factory=cf_hdinsight_clusters
    )

    with self.command_group('hdinsight', hdinsight_clusters_sdk, client_factory=cf_hdinsight_clusters) as g:
        g.custom_command('create', 'create_cluster', supports_no_wait=True)
        g.command('resize', 'resize', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_clusters')
        g.wait_command('wait')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)

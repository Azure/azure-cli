# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.horizondb._client_factory import (
    cf_horizondb_clusters)
from azure.cli.command_modules.horizondb.utils._transformers import (
    table_transform_output,
    table_transform_output_list_clusters)


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_command_table(self, _):
    # Flexible server SDKs:
    horizondb_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.horizondb.operations#HorizonDbClustersOperations.{}',
        client_factory=cf_horizondb_clusters
    )

    # commands
    custom_commands = CliCommandType(
        operations_tmpl='azure.cli.command_modules.horizondb.commands.custom_commands#{}')
    with self.command_group('horizondb clusters', horizondb_clusters_sdk,
                            custom_command_type=custom_commands,
                            client_factory=cf_horizondb_clusters) as g:
        g.custom_command('create', 'horizondb_cluster_create', table_transformer=table_transform_output)
        g.custom_command('delete', 'horizondb_cluster_delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'horizondb_cluster_list', table_transformer=table_transform_output_list_clusters)

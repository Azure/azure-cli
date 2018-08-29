# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import cf_hdinsight_applications, cf_hdinsight_clusters, cf_hdinsight_configurations, \
        cf_hdinsight_extensions, cf_hdinsight_locations, cf_hdinsight_operations, cf_hdinsight_script_actions, cf_hdinsight

    hdinsight_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#{}',
        client_factory=cf_hdinsight
    )

    hdinsight_applications_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.applications_operations#ApplicationsOperations.{}',
        client_factory=cf_hdinsight_applications
    )

    hdinsight_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.clusters_operations#ClustersOperations.{}',
        client_factory=cf_hdinsight_clusters
    )

    hdinsight_configurations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.configurations_operations#ConfigurationsOperations.{}',
        client_factory=cf_hdinsight_configurations
    )

    hdinsight_extensions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.extensions_operations#ExtensionsOperations.{}',
        client_factory=cf_hdinsight_extensions
    )

    hdinsight_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.locations_operations#LocationsOperations.{}',
        client_factory=cf_hdinsight_locations
    )

    hdinsight_operations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.operations#Operations.{}',
        client_factory=cf_hdinsight_operations
    )

    hdinsight_script_actions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.script_actions#ScriptActionsOperations.{}',
        client_factory=cf_hdinsight_script_actions
    )

    with self.command_group('hdinsight cluster', hdinsight_clusters_sdk, client_factory=cf_hdinsight_clusters) as g:
        g.custom_command('create', 'create_cluster', supports_no_wait=True)
        g.show_command('show', 'get')
        g.wait_command('wait')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)

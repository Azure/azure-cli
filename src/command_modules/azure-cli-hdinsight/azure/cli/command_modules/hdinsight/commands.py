# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import cf_hdinsight_applications
    from ._client_factory import cf_hdinsight_clusters
    from ._client_factory import cf_hdinsight_extensions
    from ._client_factory import cf_hdinsight_locations
    from ._client_factory import cf_hdinsight_script_execution_history
    from ._client_factory import cf_hdinsight_script_actions

    hdinsight_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.clusters_operations#ClustersOperations.{}',
        client_factory=cf_hdinsight_clusters
    )

    hdinsight_script_actions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.script_actions_operations#ScriptActionsOperations.{}',
        client_factory=cf_hdinsight_script_actions
    )

    hdinsight_applications_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.applications_operations#ApplicationsOperations.{}',
        client_factory=cf_hdinsight_applications
    )

    hdinsight_extensions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.extensions_operations#ExtensionsOperations.{}',
        client_factory=cf_hdinsight_extensions
    )

    hdinsight_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.locations_operations#LocationsOperations.{}',
        client_factory=cf_hdinsight_locations
    )

    hdinsight_script_execution_history_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations.script_execution_history_operations#'
                        'ScriptExecutionHistoryOperations.{}',
        client_factory=cf_hdinsight_script_execution_history
    )

    # cluster operations
    with self.command_group('hdinsight', hdinsight_clusters_sdk, client_factory=cf_hdinsight_clusters) as g:
        g.custom_command('create', 'create_cluster', supports_no_wait=True)
        g.command('resize', 'resize', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_clusters')
        g.wait_command('wait')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.custom_command('rotate-disk-encryption-key', 'rotate_hdi_cluster_key', supports_no_wait=True)
        g.command('update', 'update', supports_no_wait=True)

    # usage operations
    with self.command_group('hdinsight', hdinsight_locations_sdk, client_factory=cf_hdinsight_locations) as g:
        g.command('list-usage', 'list_usages')

    # script action operations
    with self.command_group('hdinsight script-action',
                            hdinsight_script_actions_sdk,
                            client_factory=cf_hdinsight_script_actions) as g:
        g.show_command('show', 'get_execution_detail')
        g.custom_command('list', 'list_hdi_script_actions')
        g.command('delete', 'delete')
        g.custom_command('execute',
                         'execute_hdi_script_action',
                         command_type=hdinsight_clusters_sdk,
                         client_factory=cf_hdinsight_clusters)
        g.command('promote',
                  'promote',
                  command_type=hdinsight_script_execution_history_sdk,
                  client_factory=cf_hdinsight_script_execution_history)

    # application operations
    with self.command_group('hdinsight application',
                            hdinsight_applications_sdk, client_factory=cf_hdinsight_applications) as g:
        g.custom_command('create', 'create_hdi_application')
        g.show_command('show', 'get')
        g.command('list', 'list_by_cluster')
        g.wait_command('wait')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)

    # OMS operations
    with self.command_group('hdinsight oms', hdinsight_extensions_sdk, client_factory=cf_hdinsight_extensions) as g:
        g.show_command('show', 'get_monitoring_status')
        g.custom_command('enable', 'enable_hdi_monitoring')
        g.command('disable', 'disable_monitoring')

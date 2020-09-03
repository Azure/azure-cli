# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):  # pylint: disable=too-many-statements
    from azure.cli.core.commands import CliCommandType
    from ._client_factory import cf_hdinsight_applications
    from ._client_factory import cf_hdinsight_clusters
    from ._client_factory import cf_hdinsight_extensions
    from ._client_factory import cf_hdinsight_locations
    from ._client_factory import cf_hdinsight_script_execution_history
    from ._client_factory import cf_hdinsight_script_actions
    from ._client_factory import cf_hdinsight_virtual_machines

    hdinsight_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#ClustersOperations.{}',
        client_factory=cf_hdinsight_clusters
    )

    hdinsight_script_actions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#ScriptActionsOperations.{}',
        client_factory=cf_hdinsight_script_actions
    )

    hdinsight_applications_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#ApplicationsOperations.{}',
        client_factory=cf_hdinsight_applications
    )

    hdinsight_extensions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#ExtensionsOperations.{}',
        client_factory=cf_hdinsight_extensions
    )

    hdinsight_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#LocationsOperations.{}',
        client_factory=cf_hdinsight_locations
    )

    hdinsight_script_execution_history_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#ScriptExecutionHistoryOperations.{}',
        client_factory=cf_hdinsight_script_execution_history
    )

    hdinsight_virtual_machines_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.hdinsight.operations#VirtualMachinesOperations.{}',
        client_factory=cf_hdinsight_virtual_machines
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
        g.show_command('show-execution-details', 'get_execution_detail')
        g.command('list', 'list_by_cluster')
        g.command('delete', 'delete')
        g.custom_command('execute',
                         'execute_hdi_script_action',
                         command_type=hdinsight_clusters_sdk,
                         client_factory=cf_hdinsight_clusters)
        g.command('list-execution-history',
                  'list_by_cluster',
                  command_type=hdinsight_script_execution_history_sdk,
                  client_factory=cf_hdinsight_script_execution_history)
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

    # Monitoring operations
    with self.command_group('hdinsight monitor', hdinsight_extensions_sdk, client_factory=cf_hdinsight_extensions) as g:
        g.show_command('show', 'get_monitoring_status')
        g.custom_command('enable', 'enable_hdi_monitoring')
        g.command('disable', 'disable_monitoring')

    # VirtualMachine operations
    with self.command_group('hdinsight host', hdinsight_virtual_machines_sdk,
                            client_factory=cf_hdinsight_virtual_machines) as g:
        g.command('list', 'list_hosts')
        g.command('restart', 'restart_hosts', confirmation=True)

    # Autoscale operations
    with self.command_group('hdinsight autoscale', hdinsight_clusters_sdk, client_factory=cf_hdinsight_clusters) as g:
        g.custom_command('create', 'create_autoscale', supports_no_wait=True)
        g.custom_command('update', 'update_autoscale', supports_no_wait=True)
        g.custom_show_command('show', 'show_autoscale')
        g.custom_command('delete', 'delete_autoscale', supports_no_wait=True, confirmation=True)
        g.custom_command('list-timezones', 'list_timezones')
        g.wait_command('wait')

    with self.command_group('hdinsight autoscale condition', hdinsight_clusters_sdk,
                            client_factory=cf_hdinsight_clusters) as g:
        g.custom_command('create', 'create_autoscale_condition', supports_no_wait=True)
        g.custom_command('update', 'update_autoscale_condition', supports_no_wait=True)
        g.custom_command('list', 'list_autoscale_condition')
        g.custom_command('delete', 'delete_autoscale_condition', supports_no_wait=True, confirmation=True)
        g.wait_command('wait')

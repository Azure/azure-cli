# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import CliCommandType


# pylint: disable=line-too-long, too-many-statements
def load_command_table(self, _):
    from ._client_factory import cf_synapse_client_workspace_factory
    from ._client_factory import cf_synapse_client_operations_factory
    from ._client_factory import cf_synapse_client_bigdatapool_factory
    from ._client_factory import cf_synapse_client_sqlpool_factory
    from ._client_factory import cf_synapse_client_ipfirewallrules_factory

    def get_custom_sdk(custom_module, client_factory):
        return CliCommandType(
            operations_tmpl='azure.cli.command_modules.synapse.operations.{}#'.format(custom_module) + '{}',
            client_factory=client_factory,
        )

    synapse_workspace_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#WorkspacesOperations.{}',
        client_factory=cf_synapse_client_workspace_factory)

    synapse_operations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#Operations.{}',
        client_factory=cf_synapse_client_operations_factory)

    synapse_bigdatapool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#BigDataPoolsOperations.{}',
        client_factory=cf_synapse_client_bigdatapool_factory)

    synapse_sqlpool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolsOperations.{}',
        client_factory=cf_synapse_client_sqlpool_factory)

    synapse_firewallrules_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IpFirewallRulesOperations.{}',
        client_factory=cf_synapse_client_ipfirewallrules_factory)

    synapse_spark_session_sdk = CliCommandType(
        operations_tmpl='azure.synapse.spark.operations#SparkSessionOperations.{}',
        client_factory=None)

    synapse_spark_batch_sdk = CliCommandType(
        operations_tmpl='azure.synapse.spark.operations#SparkBatchOperations.{}',
        client_factory=None)

    synapse_accesscontrol_sdk = CliCommandType(
        operations_tmpl='azure.synapse.accesscontrol.operations#AccessControlClientOperationsMixin.{}',
        client_factory=None)

    synapse_linked_service_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#LinkedServiceOperations.{}',
        client_factory=None)

    synapse_dataset_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#DatasetOperations.{}',
        client_factory=None)

    synapse_pipeline_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#PipelineOperations.{}',
        client_factory=None)

    synapse_pipeline_run_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#PipelineRunOperations.{}',
        client_factory=None)

    synapse_trigger_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#TriggerOperations.{}',
        client_factory=None)

    synapse_data_flow_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#DataFlowOperations.{}',
        client_factory=None)

    synapse_trigger_run_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#TriggerRunOperations.{}',
        client_factory=None)

    synapse_notebook_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#NotebookOperations.{}',
        client_factory=None)

    # Management Plane Commands --Workspace
    with self.command_group('synapse workspace', command_type=synapse_workspace_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_workspace_factory),
                            client_factory=cf_synapse_client_workspace_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_workspaces')
        g.custom_command('create', 'create_workspace', supports_no_wait=True)
        g.custom_command('update', 'update_workspace', supports_no_wait=True)
        g.custom_command('check-name', 'custom_check_name_availability',
                         command_type=synapse_operations_sdk,
                         client_factory=cf_synapse_client_operations_factory)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --SparkPool
    with self.command_group('synapse spark pool', command_type=synapse_bigdatapool_sdk,
                            custom_command_type=get_custom_sdk('sparkpool', cf_synapse_client_bigdatapool_factory),
                            client_factory=cf_synapse_client_bigdatapool_factory) as g:
        g.custom_show_command('show', 'get_spark_pool')
        g.command('list', 'list_by_workspace')
        g.custom_command('create', 'create_spark_pool', supports_no_wait=True)
        g.custom_command('update', 'update_spark_pool', supports_no_wait=True)
        g.custom_command('delete', 'delete_spark_pool', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --SqlPool
    with self.command_group('synapse sql pool', command_type=synapse_sqlpool_sdk,
                            custom_command_type=get_custom_sdk('sqlpool', cf_synapse_client_sqlpool_factory),
                            client_factory=cf_synapse_client_sqlpool_factory) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_workspace')
        g.custom_command('create', 'create_sql_pool', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.custom_command('update', 'update_sql_pool')
        g.command('pause', 'pause')
        g.command('resume', 'resume')
        g.wait_command('wait')

    # Management Plane Commands --FirewallRule
    with self.command_group('synapse workspace firewall-rule', command_type=synapse_firewallrules_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_ipfirewallrules_factory),
                            client_factory=cf_synapse_client_ipfirewallrules_factory) as g:
        g.command('list', 'list_by_workspace')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_firewall_rule', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Data Plane Commands --Spark batch opertions
    with self.command_group('synapse spark job', command_type=synapse_spark_batch_sdk,
                            custom_command_type=get_custom_sdk('spark', None)) as g:
        g.custom_command('submit', 'create_spark_batch_job')
        g.custom_command('list', 'list_spark_batch_jobs')
        g.custom_show_command('show', 'get_spark_batch_job')
        g.custom_command('cancel', 'cancel_spark_batch_job', confirmation=True)

    # Data Plane Commands --Spark session operations
    with self.command_group('synapse spark session', synapse_spark_session_sdk,
                            custom_command_type=get_custom_sdk('spark', None)) as g:
        g.custom_command('create', 'create_spark_session_job')
        g.custom_command('list', 'list_spark_session_jobs')
        g.custom_show_command('show', 'get_spark_session_job')
        g.custom_command('cancel', 'cancel_spark_session_job', confirmation=True)
        g.custom_command('reset-timeout', 'reset_timeout')

    # Data Plane Commands --Spark session statements operations
    with self.command_group('synapse spark statement', synapse_spark_session_sdk,
                            custom_command_type=get_custom_sdk('spark', None)) as g:
        g.custom_command('invoke', 'create_spark_session_statement')
        g.custom_command('list', 'list_spark_session_statements')
        g.custom_show_command('show', 'get_spark_session_statement')
        g.custom_command('cancel', 'cancel_spark_session_statement', confirmation=True)

    # Data Plane Commands --Access control operations
    with self.command_group('synapse role assignment', synapse_accesscontrol_sdk,
                            custom_command_type=get_custom_sdk('accesscontrol', None)) as g:
        g.custom_command('create', 'create_role_assignment')
        g.custom_command('list', 'list_role_assignments')
        g.custom_show_command('show', 'get_role_assignment_by_id')
        g.custom_command('delete', 'delete_role_assignment', confirmation=True)

    with self.command_group('synapse role definition', synapse_accesscontrol_sdk,
                            custom_command_type=get_custom_sdk('accesscontrol', None)) as g:
        g.custom_command('list', 'list_role_definitions')
        g.custom_show_command('show', 'get_role_definition')

    # Data Plane Commands --Artifacts Linked service operations
    with self.command_group('synapse linked-service', synapse_linked_service_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_linked_service', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_linked_service', supports_no_wait=True)
        g.custom_command('list', 'list_linked_service')
        g.custom_show_command('show', 'get_linked_service')
        g.custom_command('delete', 'delete_linked_service', confirmation=True, supports_no_wait=True)

    # Data Plane Commands --Artifacts dataset operations
    with self.command_group('synapse dataset', synapse_dataset_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_dataset', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_dataset', supports_no_wait=True)
        g.custom_command('list', 'list_datasets')
        g.custom_show_command('show', 'get_dataset')
        g.custom_command('delete', 'delete_dataset', confirmation=True, supports_no_wait=True)

    # Data Plane Commands --Artifacts pipeline operations
    with self.command_group('synapse pipeline', synapse_pipeline_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_pipeline', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_pipeline', supports_no_wait=True)
        g.custom_command('list', 'list_pipelines')
        g.custom_show_command('show', 'get_pipeline')
        g.custom_command('delete', 'delete_pipeline', confirmation=True, supports_no_wait=True)
        g.custom_command('create-run', 'create_pipeline_run')

    # Data Plane Commands --Artifacts pipeline run operations
    with self.command_group('synapse pipeline-run', synapse_pipeline_run_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('query-by-workspace', 'query_pipeline_runs_by_workspace')
        g.custom_show_command('show', 'get_pipeline_run')
        g.custom_command('cancel', 'cancel_pipeline_run', confirmation=True)

    with self.command_group('synapse activity-run', synapse_pipeline_run_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('query-by-pipeline-run', 'query_activity_runs')

    # Data Plane Commands --Artifacts trigger operations
    with self.command_group('synapse trigger', synapse_trigger_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_trigger', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_trigger', supports_no_wait=True)
        g.custom_command('list', 'list_triggers')
        g.custom_show_command('show', 'get_trigger')
        g.custom_command('delete', 'delete_trigger', confirmation=True, supports_no_wait=True)
        g.custom_command('subscribe-to-event', 'subscribe_trigger_to_events', supports_no_wait=True)
        g.custom_command('get-event-subscription-status', 'get_event_subscription_status')
        g.custom_command('unsubscribe-from-event', 'unsubscribe_trigger_from_events', supports_no_wait=True)
        g.custom_command('start', 'start_trigger', supports_no_wait=True)
        g.custom_command('stop', 'stop_trigger', supports_no_wait=True)

    # Data Plane Commands --Artifacts trigger run operations
    with self.command_group('synapse trigger-run', synapse_trigger_run_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('rerun', 'rerun_trigger')
        g.custom_command('query-by-workspace', 'query_trigger_runs_by_workspace')

    # Data Plane Commands --Artifacts data flow operations
    with self.command_group('synapse data-flow', synapse_data_flow_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_data_flow', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_data_flow', supports_no_wait=True)
        g.custom_command('list', 'list_data_flows')
        g.custom_show_command('show', 'get_data_flow')
        g.custom_command('delete', 'delete_data_flow', confirmation=True, supports_no_wait=True)

    # Data Plane Commands --Artifacts notebook operations
    with self.command_group('synapse notebook', synapse_notebook_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_notebook', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_notebook', supports_no_wait=True)
        g.custom_command('import', 'create_or_update_notebook', supports_no_wait=True)
        g.custom_command('list', 'list_notebooks')
        g.custom_show_command('show', 'get_notebook')
        g.custom_command('export', 'export_notebook')
        g.custom_command('delete', 'delete_notebook', confirmation=True, supports_no_wait=True)

    with self.command_group('synapse', is_preview=True):
        pass

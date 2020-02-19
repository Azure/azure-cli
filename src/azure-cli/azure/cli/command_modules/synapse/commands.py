# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from azure.cli.core.profiles import ResourceType
    from ._client_factory import cf_synapse_client_workspace_factory
    from ._client_factory import cf_synapse_client_bigdatapool_factory
    from ._client_factory import cf_synapse_spark_batch
    from ._client_factory import cf_synapse_spark_session

    synapse_workspace_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#WorkspacesOperations.{}',
        client_factory=cf_synapse_client_workspace_factory,
        resource_type=ResourceType.MGMT_SYNAPSE
    )

    synapse_bigdatapool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#BigDataPoolsOperations.{}',
        client_factory=cf_synapse_client_bigdatapool_factory,
        resource_type=ResourceType.MGMT_SYNAPSE
    )

    synapse_spark_batch_sdk = CliCommandType(
        operations_tmpl='azure.synapse.operations#SparkBatchOperations.{}',
        client_factory=cf_synapse_spark_batch
    )

    synapse_spark_session_sdk = CliCommandType(
        operations_tmpl='azure.synapse.operations#SparkSessionOperations.{}',
        client_factory=cf_synapse_spark_session
    )

    # Management Plane Commands
    with self.command_group('synapse workspace', synapse_workspace_sdk,
                            client_factory=cf_synapse_client_workspace_factory, is_preview=True) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_workspaces')
        g.custom_command('create', 'create_workspace', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('synapse spark pool', synapse_bigdatapool_sdk,
                            client_factory=cf_synapse_client_bigdatapool_factory, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_workspace')
        g.custom_command('create', 'create_spark_pool', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Data Plane Commands
    # Spark batch opertions
    with self.command_group('synapse spark batch', synapse_spark_batch_sdk, client_factory=cf_synapse_spark_batch) as g:
        g.custom_command('create', 'create_spark_batch_job', supports_no_wait=True, is_preview=True)
        g.custom_command('list', 'list_spark_batch_jobs')
        g.custom_command('show', 'get_spark_batch_job')
        g.custom_command('cancel', 'cancel_spark_batch_job', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Spark session operations
    with self.command_group('synapse spark session', synapse_spark_session_sdk,
                            client_factory=cf_synapse_spark_session, is_preview=True) as g:
        g.custom_command('create', 'create_spark_session_job', supports_no_wait=True)
        g.custom_command('list', 'list_spark_session_jobs')
        g.custom_command('show', 'get_spark_session_job')
        g.custom_command('cancel', 'cancel_spark_session_job', confirmation=True, supports_no_wait=True)
        g.custom_command('reset-timeout', 'reset_timeout')
        g.wait_command('wait')

    # Spark session statements operations
    with self.command_group('synapse spark session-statement', synapse_spark_session_sdk,
                            client_factory=cf_synapse_spark_session, is_preview=True) as g:
        g.custom_command('create', 'create_spark_session_statement', supports_no_wait=True)
        g.custom_command('list', 'list_spark_session_statements')
        g.custom_command('show', 'get_spark_session_statement')
        g.custom_command('cancel', 'cancel_spark_session_statement', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

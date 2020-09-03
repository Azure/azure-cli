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

    with self.command_group('synapse', is_preview=True):
        pass

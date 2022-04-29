# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import CliCommandType


# pylint: disable=line-too-long, too-many-statements, too-many-locals
def load_command_table(self, _):
    from ._client_factory import cf_synapse_client_workspace_factory
    from ._client_factory import cf_synapse_client_operations_factory
    from ._client_factory import cf_synapse_client_bigdatapool_factory
    from ._client_factory import cf_synapse_client_sqlpool_factory
    from ._client_factory import cf_synapse_client_ipfirewallrules_factory
    from ._client_factory import cf_synapse_client_cmk_factory
    from ._client_factory import cf_synapse_client_sqlpool_sensitivity_labels_factory
    from ._client_factory import cf_synapse_client_restorable_dropped_sqlpools_factory
    from ._client_factory import cf_synapse_client_sqlpool_transparent_data_encryptions_factory
    from ._client_factory import cf_synapse_client_sqlpool_security_alert_policies_factory
    from ._client_factory import cf_synapse_client_sqlpool_blob_auditing_policies_factory
    from ._client_factory import cf_synapse_client_managed_identity_sqlcontrol_factory
    from ._client_factory import cf_synapse_client_workspace_aad_admins_factory
    from ._client_factory import cf_synapse_client_sqlserver_blob_auditing_policies_factory
    from ._client_factory import cf_synapse_client_integrationruntimes_factory
    from ._client_factory import cf_synapse_client_integrationruntimeauthkeys_factory
    from ._client_factory import cf_synapse_client_integrationruntimemonitoringdata_factory
    from ._client_factory import cf_synapse_client_integrationruntimenodeipaddress_factory
    from ._client_factory import cf_synapse_client_integrationruntimenodes_factory
    from ._client_factory import cf_synapse_client_integrationruntimecredentials_factory
    from ._client_factory import cf_synapse_client_integrationruntimeconnectioninfos_factory
    from ._client_factory import cf_synapse_client_integrationruntimestatus_factory
    from ._client_factory import cf_kusto_pool
    from ._client_factory import cf_kusto_script
    from ._client_factory import cf_kusto_scripts

    def get_custom_sdk(custom_module, client_factory):
        return CliCommandType(
            operations_tmpl='azure.cli.command_modules.synapse.manual.operations.{}#'.format(custom_module) + '{}',
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

    synapse_workspace_aad_admin_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#WorkspaceAadAdminsOperations.{}'
    )

    synapse_sqlpool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolsOperations.{}',
        client_factory=cf_synapse_client_sqlpool_factory)

    # Classification operation
    synapse_sqlpool_sensitivity_labels_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolSensitivityLabelsOperations.{}',
        client_factory=cf_synapse_client_sqlpool_sensitivity_labels_factory)

    # List deleted
    synapse_restorable_dropped_sqlpools_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#RestorableDroppedSqlPoolsOperations.{}',
        client_factory=cf_synapse_client_restorable_dropped_sqlpools_factory)

    # Tde operation
    synapse_sqlpool_transparent_data_encryptions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolTransparentDataEncryptionsOperations.{}',
        client_factory=cf_synapse_client_sqlpool_transparent_data_encryptions_factory)

    # Threat policy operation
    synapse_sqlpool_security_alert_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolSecurityAlertPoliciesOperations.{}',
        client_factory=cf_synapse_client_sqlpool_security_alert_policies_factory)

    # Audit policy operation
    synapse_sqlpool_blob_auditing_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#SqlPoolBlobAuditingPoliciesOperations.{}',
        client_factory=cf_synapse_client_sqlpool_blob_auditing_policies_factory)

    # Workspace managed sql server audit policy operation
    synapse_workspace_managed_sqlserver_blob_auditing_policies_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#WorkspaceManagedSqlServerBlobAuditingPoliciesOperations.{}',
        client_factory=cf_synapse_client_sqlserver_blob_auditing_policies_factory)

    synapse_firewallrules_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IpFirewallRulesOperations.{}',
        client_factory=cf_synapse_client_ipfirewallrules_factory)

    synapse_cmk_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#KeysOperations.{}',
        client_factory=cf_synapse_client_cmk_factory)

    synapse_managedidentitysqlcontrol_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#WorkspaceManagedIdentitySqlControlSettingsOperations.{}',
        client_factory=cf_synapse_client_managed_identity_sqlcontrol_factory)

    synapse_integrationruntimes_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimesOperations.{}',
        client_factory=cf_synapse_client_integrationruntimes_factory)

    synapse_integrationruntimeauthkeys_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeAuthKeysOperations.{}',
        client_factory=cf_synapse_client_integrationruntimeauthkeys_factory)

    synapse_integrationruntimemonitoringdata_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeMonitoringDataOperations.{}',
        client_factory=cf_synapse_client_integrationruntimemonitoringdata_factory)

    synapse_integrationruntimenodes_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeNodesOperations.{}',
        client_factory=cf_synapse_client_integrationruntimenodes_factory)

    synapse_integrationruntimenodeipaddress_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeNodeIpAddressOperations.{}',
        client_factory=cf_synapse_client_integrationruntimenodeipaddress_factory)

    synapse_integrationruntimecredentials_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeCredentialsOperations.{}',
        client_factory=cf_synapse_client_integrationruntimecredentials_factory)

    synapse_integrationruntimeconnectioninfos_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeConnectionInfosOperations.{}',
        client_factory=cf_synapse_client_integrationruntimeconnectioninfos_factory)

    synapse_integrationruntimestatus_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations#IntegrationRuntimeStatusOperations.{}',
        client_factory=cf_synapse_client_integrationruntimestatus_factory)

    synapse_spark_session_sdk = CliCommandType(
        operations_tmpl='azure.synapse.spark.operations#SparkSessionOperations.{}',
        client_factory=None)

    synapse_spark_batch_sdk = CliCommandType(
        operations_tmpl='azure.synapse.spark.operations#SparkBatchOperations.{}',
        client_factory=None)

    synapse_role_assignment_sdk = CliCommandType(
        operations_tmpl='azure.synapse.accesscontrol.operations#RoleAssignmentsOperations.{}',
        client_factory=None)

    synapse_role_definitions_sdk = CliCommandType(
        operations_tmpl='azure.synapse.accesscontrol.operations#RoleDefinitionsOperations.{}',
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
        operations_tmpl='azure.synapse.artifacts.operations#TriggerOperations.{}',
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

    synapse_library_sdk = CliCommandType(
        operation_tmpl='azure.synapse.artifacts.operations#LibraryOperations.{}',
        client_factory=None)

    synapse_managed_private_endpoints_sdk = CliCommandType(
        operations_tmpl='azure.synapse.managedprivateendpoints.operations#ManagedPrivateEndpoints.{}',
        client_factory=None)

    synapse_spark_job_definition_sdk = CliCommandType(
        operations_tmpl='azure.synapse.artifacts.operations#SparkJobDefinitionOperations.{}',
        client_factory=None)

    synapse_sql_script_sdk = CliCommandType(
        operations_tmpl='azure.synapse.artifacts.operations#SqlScriptOperations.{}',
        client_factory=None)

    synapse_kusto_pool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.synapse.operations._kusto_pools_operations#KustoPoolsOperations.{}',
        client_factory=cf_kusto_pool,
    )

    synapse_kusto_script_sdk = CliCommandType(
        operations_tmpl='azure.synapse.artifacts.operations#KqlScriptOperations.{}',
        client_factory=cf_kusto_script,
    )

    synapse_link_connection_sdk = CliCommandType(
        operations_tmpl='azure.synapse.artifacts.operations#linkconnectionOperations.{}',
        client_factory=None,
    )    
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
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.custom_command('activate', 'activate_workspace', command_type=synapse_cmk_sdk, client_factory=cf_synapse_client_cmk_factory, supports_no_wait=True)
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
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.custom_command('update', 'update_sql_pool')
        g.command('pause', 'begin_pause')
        g.command('resume', 'begin_resume')
        g.custom_command('restore', 'restore_sql_pool')
        g.custom_command('show-connection-string', 'sql_pool_show_connection_string')
        g.wait_command('wait')

    # Management Plane Commands --SqlPool list-deleted
    with self.command_group('synapse sql pool', command_type=synapse_restorable_dropped_sqlpools_sdk,
                            client_factory=cf_synapse_client_restorable_dropped_sqlpools_factory) as g:
        g.command('list-deleted', 'list_by_workspace')

    #  Management Plane Commands --SqlPool Classification
    with self.command_group('synapse sql pool classification', command_type=synapse_sqlpool_sensitivity_labels_sdk,
                            custom_command_type=get_custom_sdk('sqlpoolsensitivitylabel',
                                                               cf_synapse_client_sqlpool_sensitivity_labels_factory),
                            client_factory=cf_synapse_client_sqlpool_sensitivity_labels_factory) as g:
        g.custom_show_command('show', 'sqlpool_sensitivity_label_show')
        g.command('list', 'list_current')
        g.custom_command('create', 'sqlpool_sensitivity_label_create')
        g.command('delete', 'delete')
        g.custom_command('update', 'sqlpool_sensitivity_label_update')

    with self.command_group('synapse sql pool classification recommendation',
                            command_type=synapse_sqlpool_sensitivity_labels_sdk,
                            custom_command_type=get_custom_sdk('sqlpoolsensitivitylabel',
                                                               cf_synapse_client_sqlpool_sensitivity_labels_factory),
                            client_factory=cf_synapse_client_sqlpool_sensitivity_labels_factory) as g:
        g.command('list', 'list_recommended')
        g.command('enable', 'enable_recommendation')
        g.command('disable', 'disable_recommendation')

    #  Management Plane Commands --SqlPool Tde
    with self.command_group('synapse sql pool tde', command_type=synapse_sqlpool_transparent_data_encryptions_sdk,
                            custom_command_type=get_custom_sdk('sqlpooltde',
                                                               cf_synapse_client_sqlpool_transparent_data_encryptions_factory),
                            client_factory=cf_synapse_client_sqlpool_transparent_data_encryptions_factory) as g:
        g.custom_command('set', 'create_or_update')
        g.show_command('show', 'get')

    #  Management Plane Commands --SqlPool Threat-policy
    with self.command_group('synapse sql pool threat-policy', command_type=synapse_sqlpool_security_alert_policies_sdk,
                            custom_command_type=get_custom_sdk('sqlpoolsecurityalertpolicy',
                                                               cf_synapse_client_sqlpool_security_alert_policies_factory),
                            client_factory=cf_synapse_client_sqlpool_security_alert_policies_factory) as g:
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='sqlpool_security_alert_policy_update')

    #  Management Plane Commands --SqlPool Audit-policy
    with self.command_group('synapse sql pool audit-policy', command_type=synapse_sqlpool_blob_auditing_policies_sdk,
                            custom_command_type=get_custom_sdk('sqlpoolblobauditingpolicy',
                                                               cf_synapse_client_sqlpool_blob_auditing_policies_factory),
                            client_factory=cf_synapse_client_sqlpool_blob_auditing_policies_factory) as g:
        g.custom_show_command('show', 'sqlpool_audit_policy_show')
        g.generic_update_command('update', custom_func_name='sqlpool_blob_auditing_policy_update')

    # Management Plane Commands --Sql Ad-Admin
    with self.command_group('synapse sql ad-admin', command_type=synapse_workspace_aad_admin_sdk,
                            custom_command_type=get_custom_sdk('workspacesqlaadadmin',
                                                               cf_synapse_client_workspace_aad_admins_factory),
                            client_factory=cf_synapse_client_workspace_aad_admins_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('create', 'create_workspace_sql_aad_admin', supports_no_wait=True)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_workspace_sql_aad_admin',
                                 setter_arg_name='aad_admin_info', supports_no_wait=True)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --Sql audit-policy
    with self.command_group('synapse sql audit-policy',
                            command_type=synapse_workspace_managed_sqlserver_blob_auditing_policies_sdk,
                            custom_command_type=get_custom_sdk('sqlpoolblobauditingpolicy',
                                                               cf_synapse_client_sqlserver_blob_auditing_policies_factory),
                            client_factory=cf_synapse_client_sqlserver_blob_auditing_policies_factory) as g:
        g.custom_show_command('show', 'workspace_audit_policy_show')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='sqlserver_blob_auditing_policy_update',
                                 supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --FirewallRule
    with self.command_group('synapse workspace firewall-rule', command_type=synapse_firewallrules_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_ipfirewallrules_factory),
                            client_factory=cf_synapse_client_ipfirewallrules_factory) as g:
        g.command('list', 'list_by_workspace')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_firewall_rule', supports_no_wait=True)
        g.custom_command('update', 'update_firewall_rule', supports_no_wait=True)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --IntegrationRuntime
    with self.command_group('synapse integration-runtime', command_type=synapse_integrationruntimes_sdk,
                            custom_command_type=get_custom_sdk('integrationruntime', cf_synapse_client_integrationruntimes_factory),
                            client_factory=cf_synapse_client_integrationruntimes_factory) as g:
        g.command('list', 'list_by_workspace')
        g.show_command('show', 'get')
        g.custom_command('create', 'create', deprecate_info=g.deprecate(redirect='managed create， self-hosted create'), supports_no_wait=True)
        g.custom_command('managed create', 'Managed_Create', supports_no_wait=True)
        g.custom_command('self-hosted create', 'Selfhosted_Create', supports_no_wait=True)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.custom_command('update', 'update')
        g.command('start', 'begin_start', supports_no_wait=True)
        g.command('stop', 'begin_stop', confirmation=True, supports_no_wait=True)
        g.command('upgrade', 'upgrade')
        g.command('list-auth-key', 'list', command_type=synapse_integrationruntimeauthkeys_sdk,
                  client_factory=cf_synapse_client_integrationruntimeauthkeys_factory)
        g.custom_command('regenerate-auth-key', 'regenerate', command_type=synapse_integrationruntimeauthkeys_sdk,
                         client_factory=cf_synapse_client_integrationruntimeauthkeys_factory)
        g.command('get-monitoring-data', 'list', command_type=synapse_integrationruntimemonitoringdata_sdk,
                  client_factory=cf_synapse_client_integrationruntimemonitoringdata_factory)
        g.command('sync-credentials', 'sync', command_type=synapse_integrationruntimecredentials_sdk,
                  client_factory=cf_synapse_client_integrationruntimecredentials_factory)
        g.command('get-connection-info', 'get', command_type=synapse_integrationruntimeconnectioninfos_sdk,
                  client_factory=cf_synapse_client_integrationruntimeconnectioninfos_factory)
        g.command('get-status', 'get', command_type=synapse_integrationruntimestatus_sdk,
                  client_factory=cf_synapse_client_integrationruntimestatus_factory)
        g.wait_command('wait')

    # Management Plane Commands --Keys
    with self.command_group('synapse workspace key', command_type=synapse_cmk_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_cmk_factory),
                            client_factory=cf_synapse_client_cmk_factory) as g:
        g.command('list', 'list_by_workspace')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_workspace_key', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.wait_command('wait')

    # Management Plane Commands --Managed-Identity
    with self.command_group('synapse workspace managed-identity', command_type=synapse_managedidentitysqlcontrol_sdk,
                            custom_command_type=get_custom_sdk('workspace', cf_synapse_client_managed_identity_sqlcontrol_factory),
                            client_factory=cf_synapse_client_managed_identity_sqlcontrol_factory) as g:
        g.show_command('show-sql-access', 'get')
        g.custom_command('grant-sql-access', 'grant_sql_access_to_managed_identity', supports_no_wait=True)
        g.custom_command('revoke-sql-access', 'revoke_sql_access_to_managed_identity', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('synapse integration-runtime-node', command_type=synapse_integrationruntimenodes_sdk,
                            custom_command_type=get_custom_sdk('integrationruntimenode',
                                                               cf_synapse_client_integrationruntimenodes_factory),
                            client_factory=cf_synapse_client_integrationruntimenodes_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('update', 'update')
        g.command('delete', 'delete', confirmation=True)
        g.command('get-ip-address', 'get', command_type=synapse_integrationruntimenodeipaddress_sdk,
                  client_factory=cf_synapse_client_integrationruntimenodeipaddress_factory)

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
    with self.command_group('synapse role assignment', synapse_role_assignment_sdk,
                            custom_command_type=get_custom_sdk('accesscontrol', None)) as g:
        g.custom_command('create', 'create_role_assignment')
        g.custom_command('list', 'list_role_assignments')
        g.custom_show_command('show', 'get_role_assignment_by_id')
        g.custom_command('delete', 'delete_role_assignment', confirmation=True)

    with self.command_group('synapse role definition', synapse_role_definitions_sdk,
                            custom_command_type=get_custom_sdk('accesscontrol', None)) as g:
        g.custom_command('list', 'list_role_definitions')
        g.custom_show_command('show', 'get_role_definition')

    with self.command_group('synapse role scope', synapse_role_definitions_sdk,
                            custom_command_type=get_custom_sdk('accesscontrol', None)) as g:
        g.custom_command('list', 'list_scopes')

    # Data Plane Commands --Artifacts Linked service operations
    with self.command_group('synapse linked-service', synapse_linked_service_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_linked_service', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_linked_service', deprecate_info=g.deprecate(redirect='update'), supports_no_wait=True)
        g.custom_command('update', 'create_or_update_linked_service', supports_no_wait=True)
        g.custom_command('list', 'list_linked_service')
        g.custom_show_command('show', 'get_linked_service')
        g.custom_command('delete', 'delete_linked_service', confirmation=True, supports_no_wait=True)

    # Data Plane Commands --Artifacts dataset operations
    with self.command_group('synapse dataset', synapse_dataset_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_dataset', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_dataset', deprecate_info=g.deprecate(redirect='update'), supports_no_wait=True)
        g.custom_command('update', 'create_or_update_dataset', supports_no_wait=True)
        g.custom_command('list', 'list_datasets')
        g.custom_show_command('show', 'get_dataset')
        g.custom_command('delete', 'delete_dataset', confirmation=True, supports_no_wait=True)

    # Data Plane Commands --Artifacts pipeline operations
    with self.command_group('synapse pipeline', synapse_pipeline_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('create', 'create_or_update_pipeline', supports_no_wait=True)
        g.custom_command('set', 'create_or_update_pipeline', deprecate_info=g.deprecate(redirect='update'), supports_no_wait=True)
        g.custom_command('update', 'create_or_update_pipeline', supports_no_wait=True)
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
        g.custom_command('set', 'create_or_update_trigger', deprecate_info=g.deprecate(redirect='update'), supports_no_wait=True)
        g.custom_command('update', 'create_or_update_trigger', supports_no_wait=True)
        g.custom_command('list', 'list_triggers')
        g.custom_show_command('show', 'get_trigger')
        g.custom_command('delete', 'delete_trigger', confirmation=True, supports_no_wait=True)
        g.custom_command('subscribe-to-event', 'subscribe_trigger_to_events', supports_no_wait=True)
        g.custom_command('get-event-subscription-status', 'get_event_subscription_status')
        g.custom_command('unsubscribe-from-event', 'unsubscribe_trigger_from_events', supports_no_wait=True)
        g.custom_command('start', 'start_trigger', supports_no_wait=True)
        g.custom_command('stop', 'stop_trigger', supports_no_wait=True)
        g.custom_wait_command('wait', 'get_trigger')

    # Data Plane Commands --Artifacts trigger run operations
    with self.command_group('synapse trigger-run', synapse_trigger_run_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('rerun', 'rerun_trigger')
        g.custom_command('cancel', 'cancel_trigger')
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

    # Data Plane Commands --Artifacts library operations
    with self.command_group('synapse workspace-package', synapse_library_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('upload', 'upload_workspace_package')
        g.custom_command('upload-batch', 'workspace_package_upload_batch')
        g.custom_command('list', 'list_workspace_package')
        g.custom_show_command('show', 'get_workspace_package')
        g.custom_command('delete', 'delete_workspace_package', confirmation=True, supports_no_wait=True)

    # Data Plane Commands --Managed private endpoints operations
    with self.command_group('synapse managed-private-endpoints', synapse_managed_private_endpoints_sdk,
                            custom_command_type=get_custom_sdk('managedprivateendpoints', None)) as g:
        g.custom_show_command('show', 'get_Managed_private_endpoints')
        g.custom_command('create', 'create_Managed_private_endpoints')
        g.custom_command('list', 'list_Managed_private_endpoints')
        g.custom_command('delete', 'delete_Managed_private_endpoints', confirmation=True)

    # Data Plane Commands --Artifacts Spark job definitions operations
    with self.command_group('synapse spark-job-definition', synapse_spark_job_definition_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('list', 'list_spark_job_definition')
        g.custom_show_command('show', 'get_spark_job_definition')
        g.custom_command('delete', 'delete_spark_job_definition', supports_no_wait=True)
        g.custom_command('create', 'create_or_update_spark_job_definition', supports_no_wait=True)
        g.custom_wait_command('wait', 'get_spark_job_definition')
        g.custom_command('update', 'create_or_update_spark_job_definition', supports_no_wait=True)

    with self.command_group('synapse sql-script', synapse_sql_script_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('list', 'list_sql_scripts')
        g.custom_show_command('show', 'get_sql_script')
        g.custom_command('delete', 'delete_sql_script', supports_no_wait=True)
        g.custom_command('create', 'create_sql_script', supports_no_wait=True)
        g.custom_wait_command('wait', 'get_sql_script')
        g.custom_show_command('export', 'export_sql_script')
        g.custom_command('import', 'create_sql_script', supports_no_wait=True)

    with self.command_group('synapse', is_preview=True):
        pass

    # synapse kusto pool Commands --Managed kusto pool Commands
    with self.command_group('synapse kusto pool',
                            command_type=synapse_kusto_pool_sdk,
                            custom_command_type=get_custom_sdk('kustopool',
                                                               cf_kusto_pool),
                            client_factory=cf_kusto_pool) as g:
        g.custom_command('create', 'synapse_kusto_pool_create', supports_no_wait=True)
        g.custom_command('update', 'synapse_kusto_pool_update', supports_no_wait=True)
        g.custom_command('add-language-extension', 'synapse_kusto_pool_add_language_extension', supports_no_wait=True)
        g.custom_command('detach-follower-database', 'synapse_kusto_pool_detach_follower_database', supports_no_wait=True)
        g.custom_command('remove-language-extension', 'synapse_kusto_pool_remove_language_extension', supports_no_wait=True)

    with self.command_group('synapse kql-script', command_type=synapse_kusto_script_sdk,
                            custom_command_type=get_custom_sdk('kustopool', cf_kusto_script),
                            client_factory=cf_kusto_script) as g:
        g.custom_show_command('show', 'synapse_kusto_script_show')
        g.custom_command('create', 'synapse_kusto_script_create', supports_no_wait=True)
        g.custom_command('import', 'synapse_kusto_script_create', supports_no_wait=True)
        g.custom_command('delete', 'synapse_kusto_script_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('list', 'synapse_kusto_script_list', client_factory=cf_kusto_scripts)
        g.custom_command('export', 'synapse_kusto_script_export')
        g.custom_wait_command('wait', 'synapse_kusto_script_show')

    with self.command_group('synapse link-connection', synapse_link_connection_sdk,
                            custom_command_type=get_custom_sdk('artifacts', None)) as g:
        g.custom_command('list', 'list_link_connection')
        g.custom_show_command('show', 'get_link_connection')
        g.custom_command('delete', 'delete_link_connection')
        g.custom_command('create', 'create_or_update_link_connection')
        g.custom_command('update', 'create_or_update_link_connection')
        g.custom_command('get-status', 'get_link_connection_status')
        g.custom_command('start ', 'start_link_connection')
        g.custom_command('stop', 'stop_link_connection')
        g.custom_command('list-link-tables', 'synapse_list_link_table')
        g.custom_command('edit-link-tables', 'synapse_edit_link_table')
        g.custom_command('get-link-tables-status', 'synapse_get_link_tables_status')
        g.custom_command('update-landing-zone-credential', 'synapse_update_landing_zone_credential')

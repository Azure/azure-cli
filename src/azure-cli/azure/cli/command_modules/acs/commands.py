# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.acs._client_factory import (
    cf_agent_pools,
    cf_managed_namespaces,
    cf_managed_clusters,
    cf_maintenance_configurations,
    cf_snapshots,
    cf_trustedaccess_role,
    cf_trustedaccess_role_binding,
    cf_machines
)
from azure.cli.command_modules.acs._format import (
    aks_agentpool_list_table_format,
    aks_namespace_list_table_format,
    aks_agentpool_show_table_format,
    aks_list_nodepool_snapshot_table_format,
    aks_list_table_format,
    aks_run_command_result_format,
    aks_show_nodepool_snapshot_table_format,
    aks_show_table_format,
    aks_upgrades_table_format,
    aks_versions_table_format,
    aks_mesh_revisions_table_format,
    aks_mesh_upgrades_table_format,
    aks_machine_list_table_format,
    aks_machine_show_table_format,
)
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType


# pylint: disable=too-many-statements
# pylint: disable=line-too-long
def load_command_table(self, _):

    managed_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_managed_clusters_operations#ManagedClustersOperations.{}',
        operation_group='managed_clusters',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_managed_clusters
    )

    agent_pools_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_agent_pools_operations#AgentPoolsOperations.{}',
        operation_group='agent_pools',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_managed_clusters
    )

    machines_sdk = CliCommandType(
        operations_tmpl='azext_aks_preview.vendored_sdks.azure_mgmt_preview_aks.'
                        'operations._machine_operations#MachinesOperations.{}',
        client_factory=cf_managed_clusters
    )

    maintenance_configuration_sdk = CliCommandType(
        operations_tmpl='aazure.mgmt.containerservice.operations.'
                        '_maintenance_configurations_operations#MaintenanceConfigurationsOperations.{}',
        operation_group='maintenance_configurations',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_maintenance_configurations
    )

    managed_namespaces_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_managed_namespaces_operations#ManagedNamespacesOperations.{}',
        operation_group='managed_namespaces',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_managed_namespaces,
    )

    snapshot_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_snapshots_operations#SnapshotsOperations.{}',
        operation_group='snapshots',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_snapshots
    )

    trustedaccess_role_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_trusted_access_roles_operations#TrustedAccessRolesOperations.{}',
        operation_group='trustedaccess_role',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_trustedaccess_role
    )

    trustedaccess_role_binding_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_trusted_access_role_bindings_operations#TrustedAccessRoleBindingsOperations.{}',
        operation_group='trustedaccess_role_binding',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_trustedaccess_role_binding
    )

    # AKS commands
    with self.command_group('aks', managed_clusters_sdk,
                            client_factory=cf_managed_clusters) as g:
        g.custom_command('browse', 'aks_browse')
        g.custom_command('create', 'aks_create', supports_no_wait=True)
        g.custom_command('update', 'aks_update', supports_no_wait=True)
        g.command('get-upgrades', 'get_upgrade_profile',
                  table_transformer=aks_upgrades_table_format)
        g.custom_command('upgrade', 'aks_upgrade', supports_no_wait=True)
        g.custom_command('scale', 'aks_scale', supports_no_wait=True)
        g.command('delete', 'begin_delete',
                  supports_no_wait=True, confirmation=True)
        g.custom_show_command('show', 'aks_show',
                              table_transformer=aks_show_table_format)
        g.custom_command('list', 'aks_list',
                         table_transformer=aks_list_table_format)
        g.custom_command('enable-addons', 'aks_enable_addons',
                         supports_no_wait=True)
        g.custom_command('disable-addons', 'aks_disable_addons',
                         supports_no_wait=True)
        g.custom_command('get-credentials', 'aks_get_credentials')
        g.custom_command('update-credentials',
                         'aks_update_credentials', supports_no_wait=True)
        g.custom_command('check-acr', 'aks_check_acr')
        g.custom_command('install-cli', 'k8s_install_cli', client_factory=None)
        g.custom_command('rotate-certs', 'aks_rotate_certs', supports_no_wait=True,
                         confirmation='Kubernetes will be unavailable during certificate rotation process.\n' +
                         'Are you sure you want to perform this operation?')
        g.custom_command('stop', 'aks_stop',
                         supports_no_wait=True)
        g.command('start', 'begin_start',
                  supports_no_wait=True)
        g.wait_command('wait')
        g.custom_command('use-dev-spaces', 'aks_use_dev_spaces',
                         deprecate_info=g.deprecate())
        g.custom_command('remove-dev-spaces',
                         'aks_remove_dev_spaces', deprecate_info=g.deprecate())
        g.custom_command('operation-abort',
                         'aks_operation_abort', supports_no_wait=True)
        g.custom_command('get-versions', 'aks_get_versions',
                         table_transformer=aks_versions_table_format)

    with self.command_group('aks machine', machines_sdk, client_factory=cf_machines) as g:
        g.custom_command('list', 'aks_machine_list',
                         table_transformer=aks_machine_list_table_format)
        g.custom_show_command('show', 'aks_machine_show',
                              table_transformer=aks_machine_show_table_format)

    # AKS maintenance configuration commands
    with self.command_group('aks maintenanceconfiguration', maintenance_configuration_sdk, client_factory=cf_maintenance_configurations) as g:
        g.custom_command('list', 'aks_maintenanceconfiguration_list')
        g.custom_show_command('show', 'aks_maintenanceconfiguration_show')
        g.custom_command('add', 'aks_maintenanceconfiguration_add')
        g.custom_command('update', 'aks_maintenanceconfiguration_update')
        g.custom_command('delete', 'aks_maintenanceconfiguration_delete')

    # AKS managed namespace commands
    with self.command_group(
        "aks namespace",
        managed_namespaces_sdk,
        client_factory=cf_managed_namespaces,
    ) as g:
        g.custom_command("add", "aks_namespace_add", supports_no_wait=True)
        g.custom_command("update", "aks_namespace_update", supports_no_wait=True)
        g.custom_show_command("show", "aks_namespace_show")
        g.custom_command("list", "aks_namespace_list", table_transformer=aks_namespace_list_table_format)
        g.custom_command("delete", "aks_namespace_delete", supports_no_wait=True)
        g.custom_command("get-credentials", "aks_namespace_get_credentials")

    # AKS agent pool commands
    with self.command_group('aks nodepool',
                            agent_pools_sdk,
                            client_factory=cf_agent_pools) as g:
        g.custom_command('add', 'aks_agentpool_add', supports_no_wait=True)
        g.custom_command('update', 'aks_agentpool_update',
                         supports_no_wait=True)
        g.custom_command('get-upgrades', 'aks_agentpool_get_upgrade_profile')
        g.custom_command('upgrade', 'aks_agentpool_upgrade',
                         supports_no_wait=True)
        g.custom_command('scale', 'aks_agentpool_scale', supports_no_wait=True)
        g.custom_command('delete', 'aks_agentpool_delete',
                         supports_no_wait=True)
        g.custom_show_command('show', 'aks_agentpool_show',
                              table_transformer=aks_agentpool_show_table_format)
        g.custom_command('list', 'aks_agentpool_list',
                         table_transformer=aks_agentpool_list_table_format)
        g.custom_command('stop', 'aks_agentpool_stop', supports_no_wait=True)
        g.custom_command('start', 'aks_agentpool_start', supports_no_wait=True)
        g.wait_command('wait')
        g.custom_command(
            'operation-abort', 'aks_agentpool_operation_abort', supports_no_wait=True)
        g.custom_command(
            'delete-machines', 'aks_agentpool_delete_machines', supports_no_wait=True)

    # AKS nodepool manual-scale command
    with self.command_group('aks nodepool manual-scale', agent_pools_sdk, client_factory=cf_agent_pools) as g:
        g.custom_command("add", "aks_agentpool_manual_scale_add", supports_no_wait=True)
        g.custom_command("update", "aks_agentpool_manual_scale_update", supports_no_wait=True)
        g.custom_command("delete", "aks_agentpool_manual_scale_delete", supports_no_wait=True, confirmation=True)

    with self.command_group('aks command', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command('invoke', 'aks_runcommand', supports_no_wait=True,
                         table_transformer=aks_run_command_result_format)
        g.custom_command('result', 'aks_command_result',
                         supports_no_wait=False, table_transformer=aks_run_command_result_format)

    # AKS nodepool snapshot commands
    with self.command_group('aks snapshot',
                            snapshot_sdk,
                            client_factory=cf_snapshots,
                            deprecate_info=self.deprecate(
                                redirect='aks nodepool snapshot', hide=True),
                            ) as g:
        g.custom_command('list', 'aks_nodepool_snapshot_list',
                         deprecate_info=g.deprecate(
                             redirect='aks nodepool snapshot list'),
                         table_transformer=aks_list_nodepool_snapshot_table_format)
        g.custom_show_command('show', 'aks_nodepool_snapshot_show',
                              deprecate_info=g.deprecate(
                                  redirect='aks nodepool snapshot show'),
                              table_transformer=aks_show_nodepool_snapshot_table_format)
        g.custom_command('create', 'aks_nodepool_snapshot_create',
                         deprecate_info=g.deprecate(redirect='aks nodepool snapshot create'), supports_no_wait=True)
        g.custom_command('delete', 'aks_nodepool_snapshot_delete',
                         deprecate_info=g.deprecate(redirect='aks nodepool snapshot delete'), supports_no_wait=True)
        g.wait_command('wait', deprecate_info=g.deprecate(
            redirect='aks nodepool snapshot wait'))

    with self.command_group('aks nodepool snapshot',
                            snapshot_sdk,
                            client_factory=cf_snapshots,
                            ) as g:
        g.custom_command('list', 'aks_nodepool_snapshot_list',
                         table_transformer=aks_list_nodepool_snapshot_table_format)
        g.custom_show_command('show', 'aks_nodepool_snapshot_show',
                              table_transformer=aks_show_nodepool_snapshot_table_format)
        g.custom_command(
            'create', 'aks_nodepool_snapshot_create', supports_no_wait=True)
        g.custom_command(
            'delete', 'aks_nodepool_snapshot_delete', supports_no_wait=True)
        g.custom_command('update', 'aks_nodepool_snapshot_update')
        g.wait_command('wait')

    with self.command_group('aks oidc-issuer', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command('rotate-signing-keys', 'aks_rotate_service_account_signing_keys', supports_no_wait=True,
                         confirmation='Be careful that rotate oidc issuer signing keys twice within short period' +
                         ' will invalidate service accounts token immediately. Please refer to doc for details.\n' +
                         'Are you sure you want to perform this operation?')

    # AKS trusted access role commands
    with self.command_group('aks trustedaccess role', trustedaccess_role_sdk, client_factory=cf_trustedaccess_role) as g:
        g.custom_command('list', 'aks_trustedaccess_role_list')

    # AKS trusted access rolebinding commands
    with self.command_group('aks trustedaccess rolebinding', trustedaccess_role_binding_sdk, client_factory=cf_trustedaccess_role_binding) as g:
        g.custom_command('list', 'aks_trustedaccess_role_binding_list')
        g.custom_show_command('show', 'aks_trustedaccess_role_binding_get')
        g.custom_command('create', 'aks_trustedaccess_role_binding_create')
        g.custom_command('update', 'aks_trustedaccess_role_binding_update')
        g.custom_command(
            'delete', 'aks_trustedaccess_role_binding_delete', confirmation=True)

    # AKS mesh commands
    with self.command_group('aks mesh', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command(
            'enable',
            'aks_mesh_enable',
            supports_no_wait=True)
        g.custom_command(
            "disable",
            "aks_mesh_disable",
            supports_no_wait=True,
            confirmation="Existing Azure Service Mesh Profile values will be reset.\n" +
            "Are you sure you want to perform this operation?")
        g.custom_command(
            'enable-ingress-gateway',
            'aks_mesh_enable_ingress_gateway',
            supports_no_wait=True)
        g.custom_command(
            "enable-egress-gateway",
            "aks_mesh_enable_egress_gateway",
            supports_no_wait=True)
        g.custom_command(
            'disable-ingress-gateway',
            'aks_mesh_disable_ingress_gateway',
            supports_no_wait=True,
            confirmation=True)
        g.custom_command(
            "disable-egress-gateway",
            "aks_mesh_disable_egress_gateway",
            supports_no_wait=True,
            confirmation=True)
        g.custom_command(
            'get-revisions',
            'aks_mesh_get_revisions',
            table_transformer=aks_mesh_revisions_table_format)
        g.custom_command(
            'get-upgrades',
            'aks_mesh_get_upgrades',
            table_transformer=aks_mesh_upgrades_table_format)

    # AKS mesh upgrade commands
    with self.command_group('aks mesh upgrade', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command(
            'start',
            'aks_mesh_upgrade_start',
            supports_no_wait=True)
        g.custom_command(
            'complete',
            'aks_mesh_upgrade_complete',
            supports_no_wait=True)
        g.custom_command(
            'rollback',
            'aks_mesh_upgrade_rollback',
            supports_no_wait=True)

    # AKS approuting commands
    with self.command_group('aks approuting', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command('enable', 'aks_approuting_enable')
        g.custom_command('disable', 'aks_approuting_disable',
                         confirmation=True)
        g.custom_command('update', 'aks_approuting_update')

    # AKS approuting dns-zone commands
    with self.command_group('aks approuting zone', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command('add', 'aks_approuting_zone_add')
        g.custom_command(
            'delete', 'aks_approuting_zone_delete', confirmation=True)
        g.custom_command('update', 'aks_approuting_zone_update')
        g.custom_command('list', 'aks_approuting_zone_list')

    with self.command_group('aks safeguards'):
        from .custom import AKSSafeguardsShowCustom as Show
        from .custom import AKSSafeguardsCreateCustom as Create
        from .custom import AKSSafeguardsUpdateCustom as Update
        from .custom import AKSSafeguardsDeleteCustom as Delete
        from .custom import AKSSafeguardsListCustom as List
        from .custom import AKSSafeguardsWaitCustom as Wait

        self.command_table["aks safeguards show"] = Show(loader=self)
        self.command_table["aks safeguards create"] = Create(loader=self)
        self.command_table["aks safeguards update"] = Update(loader=self)
        self.command_table["aks safeguards delete"] = Delete(loader=self)
        self.command_table["aks safeguards list"] = List(loader=self)
        self.command_table["aks safeguards wait"] = Wait(loader=self)

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=no-name-in-module,import-error
from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.arm import deployment_validate_table_format
from azure.cli.core.profiles import ResourceType

from ._client_factory import cf_container_services
from ._client_factory import cf_managed_clusters
from ._client_factory import cf_agent_pools
from ._client_factory import cf_openshift_managed_clusters
from ._client_factory import cf_snapshots
from ._format import aks_list_table_format
from ._format import aks_show_table_format
from ._format import aks_agentpool_show_table_format
from ._format import aks_agentpool_list_table_format
from ._format import osa_list_table_format
from ._format import aks_upgrades_table_format
from ._format import aks_versions_table_format
from ._format import aks_run_command_result_format
from ._format import aks_show_snapshot_table_format
from ._format import aks_list_snapshot_table_format


# pylint: disable=too-many-statements
def load_command_table(self, _):

    container_services_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_container_services_operations#ContainerServicesOperations.{}',
        operation_group='container_services',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_container_services
    )

    managed_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_managed_clusters_operations#ManagedClustersOperations.{}',
        operation_group='managed_clusters',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_managed_clusters
    )

    agent_pools_sdk = CliCommandType(
        operations_tmpl='azext_aks_preview.vendored_sdks.azure_mgmt_preview_aks.'
                        'operations._agent_pools_operations#AgentPoolsOperations.{}',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_managed_clusters
    )

    snapshot_sdk = CliCommandType(
        operations_tmpl='azext_aks_preview.vendored_sdks.azure_mgmt_preview_aks.'
                        'operations._snapshots_operations#SnapshotsOperations.{}',
        client_factory=cf_snapshots
    )

    openshift_managed_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        '_open_shift_managed_clusters_operations#OpenShiftManagedClustersOperations.{}',
        operation_group='open_shift_managed_clusters',
        resource_type=ResourceType.MGMT_CONTAINERSERVICE,
        client_factory=cf_openshift_managed_clusters
    )

    # ACS base commands
    # TODO: When the first azure-cli release after January 31, 2020 is planned, add
    # `expiration=<CLI core version>` to the `self.deprecate()` args below.
    deprecate_info = self.deprecate(redirect='aks', hide=True)
    with self.command_group('acs', container_services_sdk, deprecate_info=deprecate_info,
                            client_factory=cf_container_services) as g:
        g.custom_command('browse', 'acs_browse')
        g.custom_command('create', 'acs_create', supports_no_wait=True,
                         table_transformer=deployment_validate_table_format)
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'list_container_services')
        g.custom_command('list-locations', 'list_acs_locations')
        g.custom_command('scale', 'update_acs')
        g.show_command('show', 'get')
        g.wait_command('wait')

    # ACS Mesos DC/OS commands
    with self.command_group('acs dcos', container_services_sdk, client_factory=cf_container_services) as g:
        g.custom_command('browse', 'dcos_browse')
        g.custom_command('install-cli', 'dcos_install_cli',
                         client_factory=None)

    # ACS Kubernetes commands
    with self.command_group('acs kubernetes', container_services_sdk,
                            client_factory=cf_container_services) as g:
        g.custom_command('browse', 'k8s_browse')
        g.custom_command('get-credentials', 'k8s_get_credentials')
        g.custom_command('install-cli', 'k8s_install_cli', client_factory=None)

    # AKS commands
    with self.command_group('aks', managed_clusters_sdk,
                            client_factory=cf_managed_clusters) as g:
        g.custom_command('browse', 'aks_browse')
        g.custom_command('create', 'aks_create', supports_no_wait=True)
        g.custom_command('update', 'aks_update', supports_no_wait=True)
        g.command('delete', 'begin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('update-credentials',
                         'aks_update_credentials', supports_no_wait=True)
        g.custom_command('disable-addons', 'aks_disable_addons',
                         supports_no_wait=True)
        g.custom_command('enable-addons', 'aks_enable_addons',
                         supports_no_wait=True)
        g.custom_command('get-credentials', 'aks_get_credentials')
        g.custom_command('check-acr', 'aks_check_acr')
        g.command('get-upgrades', 'get_upgrade_profile',
                  table_transformer=aks_upgrades_table_format)
        g.custom_command('install-cli', 'k8s_install_cli', client_factory=None)
        g.custom_command('list', 'aks_list',
                         table_transformer=aks_list_table_format)
        g.custom_command('remove-dev-spaces',
                         'aks_remove_dev_spaces', deprecate_info=g.deprecate())
        g.custom_command('scale', 'aks_scale', supports_no_wait=True)
        g.custom_show_command('show', 'aks_show',
                              table_transformer=aks_show_table_format)
        g.custom_command('upgrade', 'aks_upgrade', supports_no_wait=True)
        g.custom_command('use-dev-spaces', 'aks_use_dev_spaces',
                         deprecate_info=g.deprecate())
        g.custom_command('rotate-certs', 'aks_rotate_certs', supports_no_wait=True,
                         confirmation='Kubernetes will be unavailable during certificate rotation process.\n' +
                         'Are you sure you want to perform this operation?')
        g.wait_command('wait')
        g.command('stop', 'begin_stop', supports_no_wait=True, min_api='2020-09-01')
        g.command('start', 'begin_start', supports_no_wait=True, min_api='2020-09-01')

    with self.command_group('aks', container_services_sdk, client_factory=cf_container_services) as g:
        g.custom_command('get-versions', 'aks_get_versions',
                         table_transformer=aks_versions_table_format)

    # AKS agent pool commands
    with self.command_group('aks nodepool',
                            agent_pools_sdk,
                            client_factory=cf_agent_pools) as g:
        g.custom_command('list', 'aks_agentpool_list',
                         table_transformer=aks_agentpool_list_table_format)
        g.custom_show_command('show', 'aks_agentpool_show',
                              table_transformer=aks_agentpool_show_table_format)
        g.custom_command('add', 'aks_agentpool_add', supports_no_wait=True)
        g.custom_command('scale', 'aks_agentpool_scale', supports_no_wait=True)
        g.custom_command('upgrade', 'aks_agentpool_upgrade',
                         supports_no_wait=True)
        g.custom_command('update', 'aks_agentpool_update',
                         supports_no_wait=True)
        g.custom_command('delete', 'aks_agentpool_delete',
                         supports_no_wait=True)
        g.custom_command('get-upgrades', 'aks_agentpool_get_upgrade_profile')

    with self.command_group('aks command', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command('invoke', 'aks_runcommand', supports_no_wait=True,
                         table_transformer=aks_run_command_result_format)
        g.custom_command('result', 'aks_command_result',
                         supports_no_wait=False, table_transformer=aks_run_command_result_format)

    # AKS snapshot commands
    with self.command_group('aks snapshot', snapshot_sdk, client_factory=cf_snapshots) as g:
        g.custom_command('list', 'aks_snapshot_list', table_transformer=aks_list_snapshot_table_format)
        g.custom_show_command('show', 'aks_snapshot_show', table_transformer=aks_show_snapshot_table_format)
        g.custom_command('create', 'aks_snapshot_create', supports_no_wait=True)
        g.custom_command('delete', 'aks_snapshot_delete', supports_no_wait=True)

    # OSA commands
    with self.command_group('openshift', openshift_managed_clusters_sdk,
                            client_factory=cf_openshift_managed_clusters,
                            deprecate_info=self.deprecate(redirect='aro', hide=True)) as g:
        g.custom_command('create', 'openshift_create', supports_no_wait=True)
        g.command('delete', 'begin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('scale', 'openshift_scale', supports_no_wait=True)
        g.custom_show_command('show', 'openshift_show')
        g.custom_command('list', 'osa_list',
                         table_transformer=osa_list_table_format)
        g.wait_command('wait')

    # OSA monitor subgroup
    with self.command_group('openshift monitor', openshift_managed_clusters_sdk,
                            client_factory=cf_openshift_managed_clusters) as g:
        g.custom_command('enable', 'openshift_monitor_enable',
                         supports_no_wait=True)
        g.custom_command('disable', 'openshift_monitor_disable',
                         supports_no_wait=True)

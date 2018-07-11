# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.arm import deployment_validate_table_format

from ._client_factory import cf_container_services
from ._client_factory import cf_managed_clusters
from ._format import aks_list_table_format
from ._format import aks_show_table_format
from ._format import aks_upgrades_table_format
from ._format import aks_versions_table_format


def load_command_table(self, _):

    container_services_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        'container_services_operations#ContainerServicesOperations.{}',
        client_factory=cf_container_services
    )

    managed_clusters_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.containerservice.operations.'
                        'managed_clusters_operations#ManagedClustersOperations.{}',
        client_factory=cf_managed_clusters
    )

    # ACS base commands
    with self.command_group('acs', container_services_sdk, client_factory=cf_container_services) as g:
        g.custom_command('browse', 'acs_browse')
        g.custom_command('create', 'acs_create', supports_no_wait=True,
                         table_transformer=deployment_validate_table_format)
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_container_services')
        g.custom_command('list-locations', 'list_acs_locations')
        g.custom_command('scale', 'update_acs')
        g.show_command('show', 'get')
        g.wait_command('wait')

    # ACS Mesos DC/OS commands
    with self.command_group('acs dcos', container_services_sdk, client_factory=cf_container_services) as g:
        g.custom_command('browse', 'dcos_browse')
        g.custom_command('install-cli', 'dcos_install_cli', client_factory=None)

    # ACS Kubernetes commands
    with self.command_group('acs kubernetes', container_services_sdk, client_factory=cf_container_services) as g:
        g.custom_command('browse', 'k8s_browse')
        g.custom_command('get-credentials', 'k8s_get_credentials')
        g.custom_command('install-cli', 'k8s_install_cli', client_factory=None)

    # AKS commands
    with self.command_group('aks', managed_clusters_sdk, client_factory=cf_managed_clusters) as g:
        g.custom_command('browse', 'aks_browse')
        g.custom_command('create', 'aks_create', supports_no_wait=True)
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.custom_command('disable-addons', 'aks_disable_addons', supports_no_wait=True)
        g.custom_command('enable-addons', 'aks_enable_addons', supports_no_wait=True)
        g.custom_command('get-credentials', 'aks_get_credentials')
        g.command('get-upgrades', 'get_upgrade_profile', table_transformer=aks_upgrades_table_format)
        g.custom_command('install-cli', 'k8s_install_cli', client_factory=None)
        g.custom_command('install-connector', 'k8s_install_connector')
        g.custom_command('list', 'aks_list', table_transformer=aks_list_table_format)
        g.custom_command('remove-connector', 'k8s_uninstall_connector')
        g.custom_command('remove-dev-spaces', 'aks_remove_dev_spaces')
        g.custom_command('scale', 'aks_scale', supports_no_wait=True)
        g.custom_show_command('show', 'aks_show', table_transformer=aks_show_table_format)
        g.custom_command('upgrade', 'aks_upgrade', supports_no_wait=True,
                         confirmation='Kubernetes may be unavailable during cluster upgrades.\n' +
                         'Are you sure you want to perform this operation?')
        g.custom_command('upgrade-connector', 'k8s_upgrade_connector')
        g.custom_command('use-dev-spaces', 'aks_use_dev_spaces')
        g.wait_command('wait')

    with self.command_group('aks', container_services_sdk, client_factory=cf_container_services) as g:
        g.custom_command('get-versions', 'aks_get_versions', table_transformer=aks_versions_table_format)

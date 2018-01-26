# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.arm import deployment_validate_table_format
from azure.cli.core.util import empty_on_404

from ._client_factory import cf_container_services
from ._client_factory import cf_managed_clusters
from ._format import aks_get_versions_table_format
from ._format import aks_list_table_format
from ._format import aks_show_table_format


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
        g.custom_command('create', 'acs_create', no_wait_param='no_wait',
                         table_transformer=deployment_validate_table_format)
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_container_services')
        g.custom_command('list-locations', 'list_acs_locations')
        g.custom_command('scale', 'update_acs')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.generic_wait_command('wait')

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
        g.custom_command('create', 'aks_create', no_wait_param='no_wait')
        g.command('delete', 'delete', no_wait_param='raw', confirmation=True)
        g.custom_command('get-credentials', 'aks_get_credentials')
        g.command('get-versions', 'get_upgrade_profile', table_transformer=aks_get_versions_table_format)
        g.custom_command('install-cli', 'k8s_install_cli', client_factory=None)
        g.custom_command('install-connector', 'k8s_install_connector')
        g.custom_command('list', 'aks_list', table_transformer=aks_list_table_format)
        g.custom_command('remove-connector', 'k8s_uninstall_connector')
        g.custom_command('scale', 'aks_scale', no_wait_param='no_wait')
        g.custom_command('show', 'aks_show', table_transformer=aks_show_table_format)
        g.custom_command('upgrade', 'aks_upgrade', no_wait_param='no_wait',
                         confirmation='Kubernetes may be unavailable during cluster upgrades.\n' +
                         'Are you sure you want to perform this operation?')
        g.generic_wait_command('wait')

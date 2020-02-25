# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import (servicefabric_clusters_client_factory,
                              servicefabric_client_factory_all,
                              servicefabric_application_type_client_factory,
                              servicefabric_application_type_version_client_factory,
                              servicefabric_application_client_factory,
                              servicefabric_service_client_factory)


def load_command_table(self, _):
    cluster_mgmt_util = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabric.operations#ClustersOperations.{}',
        client_factory=servicefabric_clusters_client_factory
    )

    application_type_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabric.operations#ApplicationTypesOperations.{}',
        client_factory=servicefabric_application_type_client_factory
    )

    application_type_version_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabric.operations#ApplicationTypeVersionsOperations.{}',
        client_factory=servicefabric_application_type_version_client_factory
    )

    application_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabric.operations#ApplicationsOperations.{}',
        client_factory=servicefabric_application_client_factory
    )

    service_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabric.operations#ServicesOperations.{}',
        client_factory=servicefabric_service_client_factory
    )

    application_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicefabric.operations.applications#{}',
        client_factory=servicefabric_client_factory_all
    )

    with self.command_group('sf cluster', cluster_mgmt_util, client_factory=servicefabric_clusters_client_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_cluster')
        g.custom_command('create', 'new_cluster')
        g.custom_command('certificate add', 'add_cluster_cert')
        g.custom_command('certificate remove', 'remove_cluster_cert')
        g.custom_command('client-certificate add', 'add_client_cert')
        g.custom_command('client-certificate remove', 'remove_client_cert')
        g.custom_command('setting set', 'set_cluster_setting')
        g.custom_command('setting remove', 'remove_cluster_setting')
        g.custom_command('reliability update', 'update_cluster_reliability_level')
        g.custom_command('durability update', 'update_cluster_durability')
        g.custom_command('node-type add', 'add_cluster_node_type')
        g.custom_command('node add', 'add_cluster_node')
        g.custom_command('node remove', 'remove_cluster_node')
        g.custom_command('upgrade-type set', 'update_cluster_upgrade_type')

    with self.command_group('sf application certificate') as g:
        g.custom_command('add', 'add_app_cert')

    with self.command_group('sf application-type', application_type_mgmt,
                            custom_command_type=application_custom_type) as g:
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_app_type')

    with self.command_group('sf application-type version', application_type_version_mgmt,
                            custom_command_type=application_custom_type) as g:
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_app_type_version')

    with self.command_group('sf application', application_mgmt,
                            custom_command_type=application_custom_type) as g:
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_app')
        g.custom_command('update', 'update_app')

    with self.command_group('sf service', service_mgmt,
                            custom_command_type=application_custom_type) as g:
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_service')

    with self.command_group('sf', is_preview=True):
        pass

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
                              servicefabric_service_client_factory,
                              servicefabric_managed_client_factory_all,
                              servicefabric_managed_cluster_client_factory,
                              servicefabric_managed_node_type_client_factory,
                              servicefabric_managed_application_type_client_factory,
                              servicefabric_managed_application_type_version_client_factory,
                              servicefabric_managed_application_client_factory,
                              servicefabric_managed_service_client_factory)


# pylint: disable=too-many-statements
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

    with self.command_group('sf cluster', cluster_mgmt_util,
                            client_factory=servicefabric_clusters_client_factory) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_cluster')
        g.custom_command('create', 'new_cluster')
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

    with self.command_group('sf'):
        pass

    # Managed clusters

    managed_cluster_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicefabric.operations.managed_clusters#{}',
        client_factory=servicefabric_managed_client_factory_all
    )

    managed_cluster_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabricmanagedclusters.operations#ManagedClustersOperations.{}',
        client_factory=servicefabric_managed_cluster_client_factory
    )

    managed_node_type_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicefabric.operations.managed_node_types#{}',
        client_factory=servicefabric_managed_client_factory_all
    )

    node_type_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabricmanagedclusters.operations#NodeTypesOperations.{}',
        client_factory=servicefabric_managed_node_type_client_factory
    )

    managed_application_type_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabricmanagedclusters.operations#ApplicationTypesOperations.{}',
        client_factory=servicefabric_managed_application_type_client_factory
    )

    managed_application_type_version_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabricmanagedclusters.operations#ApplicationTypeVersionsOperations.{}',
        client_factory=servicefabric_managed_application_type_version_client_factory
    )

    managed_application_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabricmanagedclusters.operations#ApplicationsOperations.{}',
        client_factory=servicefabric_managed_application_client_factory
    )

    managed_service_mgmt = CliCommandType(
        operations_tmpl='azure.mgmt.servicefabricmanagedclusters.operations#ServicesOperations.{}',
        client_factory=servicefabric_managed_service_client_factory
    )

    managed_application_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.servicefabric.operations.managed_applications#{}',
        client_factory=servicefabric_managed_client_factory_all
    )

    with self.command_group('sf managed-cluster', managed_cluster_mgmt,
                            custom_command_type=managed_cluster_custom_type) as g:
        g.custom_command('list', 'list_clusters')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_cluster')
        g.custom_command('update', 'update_cluster')

    with self.command_group('sf managed-cluster client-certificate', managed_cluster_mgmt,
                            custom_command_type=managed_cluster_custom_type) as g:
        g.custom_command('add', 'add_client_cert')
        g.custom_command('delete', 'delete_client_cert')

    with self.command_group('sf managed-node-type', node_type_mgmt,
                            custom_command_type=managed_node_type_custom_type) as g:
        g.command('list', 'list_by_managed_clusters')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_node_type')
        g.custom_command('update', 'update_node_type')

    with self.command_group('sf managed-node-type node', node_type_mgmt,
                            custom_command_type=managed_node_type_custom_type) as g:
        g.custom_command('reimage', 'reimage_node')
        g.custom_command('restart', 'restart_node')
        g.custom_command('delete', 'delete_node')

    with self.command_group('sf managed-node-type vm-extension', node_type_mgmt,
                            custom_command_type=managed_node_type_custom_type) as g:
        g.custom_command('add', 'add_vm_extension')
        g.custom_command('delete', 'delete_vm_extension')

    with self.command_group('sf managed-node-type vm-secret', node_type_mgmt,
                            custom_command_type=managed_node_type_custom_type) as g:
        g.custom_command('add', 'add_vm_secret')

    with self.command_group('sf managed-application-type', managed_application_type_mgmt,
                            custom_command_type=managed_application_custom_type) as g:
        g.command('list', 'list')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_app_type')
        g.custom_command('update', 'update_app_type')

    with self.command_group('sf managed-application-type version', managed_application_type_version_mgmt,
                            custom_command_type=managed_application_custom_type) as g:
        g.command('list', 'list_by_application_types')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_app_type_version')
        g.custom_command('update', 'update_app_type_version')

    with self.command_group('sf managed-application', managed_application_mgmt,
                            custom_command_type=managed_application_custom_type) as g:
        g.command('list', 'list')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_app')
        g.custom_command('update', 'update_app')

    with self.command_group('sf managed-service', managed_service_mgmt,
                            custom_command_type=managed_application_custom_type) as g:
        g.command('list', 'list_by_applications')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('create', 'create_service')
        g.custom_command('update', 'update_service')

    with self.command_group('sf managed-service correlation-scheme', managed_service_mgmt,
                            custom_command_type=managed_application_custom_type) as g:
        g.custom_command('create', 'create_service_correlation')
        g.custom_command('update', 'update_service_correlation')
        g.custom_command('delete', 'delete_service_correlation')

    with self.command_group('sf managed-service load-metrics', managed_service_mgmt,
                            custom_command_type=managed_application_custom_type) as g:
        g.custom_command('create', 'create_service_load_metric')
        g.custom_command('update', 'update_service_load_metric')
        g.custom_command('delete', 'delete_service_load_metric')

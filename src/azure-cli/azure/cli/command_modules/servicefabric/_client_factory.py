# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def servicefabric_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.servicefabric import ServiceFabricManagementClient
    return get_mgmt_service_client(cli_ctx, ServiceFabricManagementClient)


def servicefabric_client_factory_all(cli_ctx, kwargs):
    return servicefabric_client_factory(cli_ctx, **kwargs)


def servicefabric_clusters_client_factory(cli_ctx, kwargs):
    return servicefabric_client_factory(cli_ctx, **kwargs).clusters


def servicefabric_application_type_client_factory(cli_ctx, kwargs):
    return servicefabric_client_factory(cli_ctx, **kwargs).application_types


def servicefabric_application_type_version_client_factory(cli_ctx, kwargs):
    return servicefabric_client_factory(cli_ctx, **kwargs).application_type_versions


def servicefabric_application_client_factory(cli_ctx, kwargs):
    return servicefabric_client_factory(cli_ctx, **kwargs).applications


def servicefabric_service_client_factory(cli_ctx, kwargs):
    return servicefabric_client_factory(cli_ctx, **kwargs).services


def resource_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def keyvault_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_KEYVAULT)


def compute_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_COMPUTE)


def storage_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_STORAGE)


# Managed clusters

def servicefabric_managed_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.servicefabricmanagedclusters import ServiceFabricManagedClustersManagementClient
    return get_mgmt_service_client(cli_ctx, ServiceFabricManagedClustersManagementClient)


def servicefabric_managed_client_factory_all(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs)


def servicefabric_managed_cluster_client_factory(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs).managed_clusters


def servicefabric_managed_node_type_client_factory(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs).node_types


def servicefabric_managed_application_type_client_factory(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs).application_types


def servicefabric_managed_application_type_version_client_factory(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs).application_type_versions


def servicefabric_managed_application_client_factory(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs).applications


def servicefabric_managed_service_client_factory(cli_ctx, kwargs):
    return servicefabric_managed_client_factory(cli_ctx, **kwargs).services

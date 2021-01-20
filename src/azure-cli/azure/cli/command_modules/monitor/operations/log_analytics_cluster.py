# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.loganalytics.models import Cluster, ClusterSku, KeyVaultProperties, Identity, ClusterPatch


def create_log_analytics_cluster(client, resource_group_name, cluster_name, sku_capacity,
                                 sku_name='CapacityReservation', identity_type='SystemAssigned',
                                 location=None, tags=None, no_wait=False):
    sku = ClusterSku(capacity=sku_capacity, name=sku_name)
    identity = Identity(type=identity_type)
    cluster_instance = Cluster(location=location,
                               tags=tags,
                               sku=sku,
                               identity=identity)

    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, cluster_name, cluster_instance)


def update_log_analytics_cluster(client, resource_group_name, cluster_name,
                                 key_vault_uri=None, key_name=None, key_version=None,
                                 sku_capacity=None, tags=None):
    cluster_patch = ClusterPatch()
    if key_vault_uri is not None and key_name is not None and key_version is not None:
        cluster_patch.key_vault_properties = KeyVaultProperties(key_vault_uri=key_vault_uri, key_name=key_name,
                                                                key_version=key_version)
    if sku_capacity is not None:
        cluster_patch.sku = ClusterSku(capacity=sku_capacity, name='CapacityReservation')
    if tags is not None:
        cluster_patch.tags = tags

    return client.update(resource_group_name, cluster_name, cluster_patch)


def list_log_analytics_clusters(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()

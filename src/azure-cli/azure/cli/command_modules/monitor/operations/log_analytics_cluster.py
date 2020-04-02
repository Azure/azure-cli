# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.mgmt.loganalytics.models import ClusterSkuNameEnum, ClusterSku, KeyVaultProperties, Identity, ClusterPatch


def create_log_analytics_cluster(cmd, client, resource_group_name, cluster_name, capacity, key_vault_uri='https://vault-or-cluster.vault.azure.net/',
                                 key_name='my-key', key_version='2f5fa106de2c49829930b87d82cab72d', identity_type='SystemAssigned',
                                 location=None, tags=None,
                                 sku=ClusterSkuNameEnum.capacity_reservation):
    from azure.mgmt.loganalytics.models import Cluster
    from azure.cli.core.commands import LongRunningOperation
    sku = ClusterSku(capacity=capacity, name=sku)
    identity = Identity(type=identity_type)
    key_vault_properties = KeyVaultProperties(key_vault_uri=key_vault_uri, key_name=key_name, key_version=key_version)
    cluster_instance = Cluster(location=location,
                               tags=tags,
                               sku=sku,
                               identity=identity,
                               key_vault_properties=key_vault_properties)

    return LongRunningOperation(cmd.cli_ctx)(client.create_or_update(resource_group_name, cluster_name, cluster_instance))


def update_log_analytics_cluster(instance, tags=None, sku=None, capacity=None, key_vault_uri=None, key_name=None, key_version=None):
    if tags is not None:
        instance.tags = tags

    if sku is not None:
        instance.sku.name = sku

    return instance


# Use SDK patch directly
def update_log_analytics_cluster1(client, resource_group_name, cluster_name, tags=None, sku=None, capacity=None,
                                 key_vault_uri=None, key_name=None, key_version=None):
    cluster_patch = ClusterPatch()
    if tags is not None:
        cluster_patch.tags = tags

    client.update(resource_group_name=resource_group_name, cluster_name=cluster_name, parameters=cluster_patch)


def list_log_analytics_clusters(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()

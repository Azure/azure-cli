# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.util import sdk_no_wait
from azure.mgmt.loganalytics.models import Cluster, ClusterSku, Identity


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

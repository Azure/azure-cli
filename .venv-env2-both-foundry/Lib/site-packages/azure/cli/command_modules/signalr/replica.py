# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.mgmt.signalr.models import (
    ResourceSku,
    Replica)

from azure.mgmt.signalr.operations import SignalRReplicasOperations


def signalr_replica_list(client: SignalRReplicasOperations, resource_group_name, signalr_name):
    return client.list(resource_group_name, signalr_name)


def signalr_replica_show(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name):
    return client.get(resource_group_name=resource_group_name, resource_name=signalr_name, replica_name=replica_name)


def signalr_replica_get(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name):
    return client.get(resource_group_name=resource_group_name, resource_name=signalr_name, replica_name=replica_name)


def signalr_replica_start(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name):
    parameter = Replica(location=None, resource_stopped=False)
    return client.begin_update(resource_group_name=resource_group_name, resource_name=signalr_name, replica_name=replica_name, parameters=parameter)


def signalr_replica_stop(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name):
    parameter = Replica(location=None, resource_stopped=True)
    return client.begin_update(resource_group_name=resource_group_name, resource_name=signalr_name, replica_name=replica_name, parameters=parameter)


def signalr_replica_restart(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name):
    return client.begin_restart(resource_group_name=resource_group_name, resource_name=signalr_name, replica_name=replica_name)


def signalr_replica_delete(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name):
    return client.delete(resource_group_name=resource_group_name, resource_name=signalr_name, replica_name=replica_name)


def signalr_replica_create(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name,
                           sku, unit_count=1, location=None, tags=None):
    sku = ResourceSku(name=sku, capacity=unit_count)
    parameter = Replica(tags=tags,
                        sku=sku,
                        location=location,
                        )

    return client.begin_create_or_update(resource_group_name=resource_group_name, resource_name=signalr_name,
                                         replica_name=replica_name, parameters=parameter)


def signalr_replica_set(client: SignalRReplicasOperations, signalr_name, replica_name, resource_group_name, parameters):
    return client.begin_update(resource_group_name=resource_group_name, resource_name=signalr_name,
                               replica_name=replica_name, parameters=parameters)


def signalr_replica_update(instance: Replica, unit_count=None, region_endpoint_enabled=None):
    unit_count = unit_count if unit_count else instance.sku.capacity
    instance.sku = ResourceSku(name=instance.sku.name, capacity=unit_count)

    if region_endpoint_enabled is not None:
        if region_endpoint_enabled:
            instance.region_endpoint_enabled = "Enabled"
        else:
            instance.region_endpoint_enabled = "Disabled"

    return instance

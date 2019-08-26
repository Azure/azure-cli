# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.mgmt.signalr.models import (ResourceSku, SignalRCreateOrUpdateProperties, SignalRCreateParameters,
                                       SignalRFeature, SignalRCorsSettings, SignalRUpdateParameters)


def signalr_create(client, signalr_name, resource_group_name,
                   sku, unit_count=1, location=None, tags=None, service_mode='Default', allowed_origins=None):
    sku = ResourceSku(name=sku, capacity=unit_count)
    service_mode_feature = SignalRFeature(value=service_mode)
    cors_setting = SignalRCorsSettings(allowed_origins=allowed_origins)

    properties = SignalRCreateOrUpdateProperties(host_name_prefix=signalr_name,
                                                 features=[service_mode_feature], cors=cors_setting)

    parameter = SignalRCreateParameters(tags=tags,
                                        sku=sku,
                                        properties=properties,
                                        location=location)

    return client.create_or_update(resource_group_name, signalr_name, parameter)


def signalr_delete(client, signalr_name, resource_group_name):
    return client.delete(resource_group_name, signalr_name)


def signalr_list(client, resource_group_name=None):
    if not resource_group_name:
        return client.list_by_subscription()
    return client.list_by_resource_group(resource_group_name)


def signalr_show(client, signalr_name, resource_group_name):
    return client.get(resource_group_name, signalr_name)


def signalr_restart(client, signalr_name, resource_group_name):
    return client.restart(resource_group_name, signalr_name)


def signalr_update_get():
    return SignalRUpdateParameters()


def signalr_update_set(client, signalr_name, resource_group_name, parameters):
    return client.update(resource_group_name, signalr_name, parameters)


def signalr_update_custom(instance, sku=None, unit_count=1, tags=None, service_mode=None, allowed_origins=None):
    if sku is not None:
        instance.sku = ResourceSku(name=sku, capacity=unit_count)

    if tags is not None:
        instance.tags = tags

    properties = SignalRCreateOrUpdateProperties()

    if service_mode is not None:
        properties.features = [SignalRFeature(value=service_mode)]

    if allowed_origins is not None:
        properties.cors = SignalRCorsSettings(allowed_origins=allowed_origins)

    instance.properties = properties

    return instance

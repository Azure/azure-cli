# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.mgmt.signalr.models import (ResourceSku, SignalRCreateOrUpdateProperties, SignalRCreateParameters, SignalRFeature, SignalRCorsSettings, SignalRUpdateParameters)
from ._constants import (SIGNALR_SERVICE_MODE_TYPE)


def signalr_create(client, signalr_name, resource_group_name, sku, unit_count=1, location=None, tags=None, service_mode='default', allowed_origins=None):
    sku = ResourceSku(name=sku, capacity=unit_count)
    properties = SignalRCreateOrUpdateProperties(host_name_prefix=signalr_name)

    service_mode_feature = SignalRFeature(value=service_mode)
    cors_setting = SignalRCorsSettings(allowed_origins=allowed_origins)
    parameter = SignalRCreateParameters(tags=tags,
                                        sku=sku,
                                        properties=properties,
                                        location=location,
                                        features=[service_mode_feature],
                                        cors=cors_setting)

    return client.create_or_update(resource_group_name, signalr_name, parameter)


def signalr_delete(client, signalr_name, resource_group_name):
    return client.delete(resource_group_name, signalr_name)


def signalr_list(client, resource_group_name=None):
    if not resource_group_name:
        return client.list_by_subscription()
    return client.list_by_resource_group(resource_group_name)


def signalr_show(client, signalr_name, resource_group_name):
    return client.get(resource_group_name, signalr_name)

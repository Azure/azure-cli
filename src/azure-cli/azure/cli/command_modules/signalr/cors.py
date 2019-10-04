# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.mgmt.signalr.models import (SignalRCorsSettings, SignalRUpdateParameters, SignalRCreateOrUpdateProperties)


def signalr_cors_list(client, resource_group_name, signalr_name):
    return _get_cors_details(client, resource_group_name, signalr_name)


def signalr_cors_add(client, resource_group_name, signalr_name, allowed_origins):
    cors = _get_cors_details(client, resource_group_name, signalr_name)
    if cors is None:
        cors = SignalRCorsSettings(allowed_origins=[])
    cors.allowed_origins = cors.allowed_origins + allowed_origins
    parameters = SignalRUpdateParameters(properties=SignalRCreateOrUpdateProperties(cors=cors))

    return client.update(resource_group_name, signalr_name, parameters)


def signalr_cors_remove(client, resource_group_name, signalr_name, allowed_origins):
    cors = _get_cors_details(client, resource_group_name, signalr_name)
    if cors is None:
        cors = SignalRCorsSettings(allowed_origins=[])
    cors.allowed_origins = [x for x in cors.allowed_origins if x not in allowed_origins]
    if not cors.allowed_origins:
        cors.allowed_origins = ['*']
    parameters = SignalRUpdateParameters(properties=SignalRCreateOrUpdateProperties(cors=cors))

    return client.update(resource_group_name, signalr_name, parameters)


def _get_cors_details(client, resource_group_name, signalr_name):
    resource = client.get(resource_group_name, signalr_name)
    return resource.cors

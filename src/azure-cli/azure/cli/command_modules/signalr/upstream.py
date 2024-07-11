# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.mgmt.signalr.models import (
    SignalRResource,
    ServerlessUpstreamSettings)


def signalr_upstream_list(client, resource_group_name, signalr_name):
    resource = client.get(resource_group_name, signalr_name)
    return resource.upstream


def signalr_upstream_update(client, resource_group_name, signalr_name, template):
    upstream = ServerlessUpstreamSettings(templates=template)
    parameters = SignalRResource(location=None, upstream=upstream)
    return client.begin_update(resource_group_name, signalr_name, parameters)


def signalr_upstream_clear(client, resource_group_name, signalr_name):
    upstream = ServerlessUpstreamSettings(templates=[])
    parameters = SignalRResource(location=None, upstream=upstream)
    return client.begin_update(resource_group_name, signalr_name, parameters)

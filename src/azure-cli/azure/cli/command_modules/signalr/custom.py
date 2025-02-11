# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.mgmt.signalr.models import (
    ResourceSku,
    SignalRFeature,
    SignalRCorsSettings,
    SignalRResource,
    SignalRNetworkACLs,
    SignalRTlsSettings
)

from azure.mgmt.signalr.operations import SignalROperations


def signalr_create(client, signalr_name, resource_group_name,
                   sku, unit_count=1, location=None, tags=None, service_mode='Default', enable_message_logs=False, allowed_origins=None, default_action="Allow"):
    sku = ResourceSku(name=sku, capacity=unit_count)
    service_mode_feature = SignalRFeature(flag="ServiceMode", value=service_mode)
    enable_message_logs_feature = SignalRFeature(flag="EnableMessagingLogs", value=enable_message_logs)
    cors_setting = SignalRCorsSettings(allowed_origins=allowed_origins)

    parameter = SignalRResource(tags=tags,
                                sku=sku,
                                host_name_prefix=signalr_name,
                                features=[service_mode_feature, enable_message_logs_feature],
                                cors=cors_setting,
                                location=location,
                                network_ac_ls=SignalRNetworkACLs(default_action=default_action))

    return client.begin_create_or_update(resource_group_name, signalr_name, parameter)


def signalr_delete(client, signalr_name, resource_group_name):
    return client.begin_delete(resource_group_name, signalr_name)


def signalr_list(client, resource_group_name=None):
    if not resource_group_name:
        return client.list_by_subscription()
    return client.list_by_resource_group(resource_group_name)


def signalr_show(client, signalr_name, resource_group_name):
    return client.get(resource_group_name, signalr_name)


def signalr_start(client: SignalROperations, signalr_name, resource_group_name):
    parameter = SignalRResource(location=None, resource_stopped=False)
    return client.begin_update(resource_group_name, signalr_name, parameter)


def signalr_stop(client: SignalROperations, signalr_name, resource_group_name):
    parameter = SignalRResource(location=None, resource_stopped=True)
    return client.begin_update(resource_group_name, signalr_name, parameter)


def signalr_restart(client, signalr_name, resource_group_name):
    return client.begin_restart(resource_group_name, signalr_name)


def signalr_update_get():
    return SignalRResource(location=None)


def signalr_update_set(client, signalr_name, resource_group_name, parameters):
    return client.begin_update(resource_group_name, signalr_name, parameters)


def signalr_update_custom(instance, sku=None, unit_count=1, tags=None, service_mode=None,
                          allowed_origins=None, default_action=None, enable_message_logs=None,
                          client_cert_enabled=None, disable_local_auth=None, region_endpoint_enabled=None):
    instance.features = []

    if sku is not None:
        instance.sku = ResourceSku(name=sku, capacity=unit_count)

    if tags is not None:
        instance.tags = tags

    if service_mode is not None:
        instance.features += [SignalRFeature(flag="ServiceMode", value=service_mode)]

    if enable_message_logs is not None:
        instance.features += [SignalRFeature(flag="EnableMessagingLogs", value=enable_message_logs)]

    if allowed_origins is not None:
        instance.cors = SignalRCorsSettings(allowed_origins=allowed_origins)

    if default_action is not None:
        instance.network_ac_ls = SignalRNetworkACLs(default_action=default_action)

    if client_cert_enabled is not None:
        instance.tls = SignalRTlsSettings(client_cert_enabled=client_cert_enabled)

    if disable_local_auth is not None:
        instance.disable_local_auth = disable_local_auth

    if region_endpoint_enabled is not None:
        if region_endpoint_enabled:
            instance.region_endpoint_enabled = "Enabled"
        else:
            instance.region_endpoint_enabled = "Disabled"

    return instance

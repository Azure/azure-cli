# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_mgmt_service_client


def cf_eventhub(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_EVENTHUB)


def namespaces_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).namespaces


def cf_namespace2018(cli_ctx, *_):
    return get_2018preview_client(cli_ctx).namespaces


def event_hub_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).event_hubs


def consumer_groups_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).consumer_groups


def disaster_recovery_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).disaster_recovery_configs


def get_2018preview_client(cli_ctx, **_):
    from azure.mgmt.eventhub.v2018_01_01_preview import EventHub2018PreviewManagementClient
    return get_mgmt_service_client(cli_ctx, EventHub2018PreviewManagementClient)

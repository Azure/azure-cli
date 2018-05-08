# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_eventhub(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.eventhub import EventHubManagementClient
    return get_mgmt_service_client(cli_ctx, EventHubManagementClient)


def namespaces_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).namespaces


def event_hub_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).event_hubs


def consumer_groups_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).consumer_groups


def disaster_recovery_mgmt_client_factory(cli_ctx, _):
    return cf_eventhub(cli_ctx).disaster_recovery_configs

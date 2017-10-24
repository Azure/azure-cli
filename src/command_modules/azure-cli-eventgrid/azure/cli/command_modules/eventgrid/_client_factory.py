# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_eventgrid(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.eventgrid import EventGridManagementClient
    return get_mgmt_service_client(EventGridManagementClient)


def topics_factory(_):
    return cf_eventgrid().topics


def event_subscriptions_factory(_):
    return cf_eventgrid().event_subscriptions


def topic_types_factory(_):
    return cf_eventgrid().topic_types

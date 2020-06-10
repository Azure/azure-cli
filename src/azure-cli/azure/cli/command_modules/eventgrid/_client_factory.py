# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_eventgrid(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.eventgrid import EventGridManagementClient
    return get_mgmt_service_client(cli_ctx, EventGridManagementClient)


def topics_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).topics


def domains_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).domains


def domain_topics_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).domain_topics


def event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).event_subscriptions


def topic_types_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).topic_types

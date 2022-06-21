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

def topic_event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).topic_event_subscriptions


def domain_topic_event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).domain_topic_event_subscriptions


def domain_event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).domain_event_subscriptions


def domains_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).domains


def domain_topics_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).domain_topics


def system_topics_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).system_topics


def system_topic_event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).system_topic_event_subscriptions


def extension_topics_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).extension_topics


def partner_registrations_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).partner_registrations


def partner_namespaces_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).partner_namespaces


def event_channels_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).event_channels


def channels_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).channels


def partner_topics_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).partner_topics


def partner_topic_event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).partner_topic_event_subscriptions


def partner_configurations_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).partner_configurations


def partner_destinations_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).partner_destinations


def verified_partners_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).verified_partners


def event_subscriptions_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).event_subscriptions


def topic_types_factory(cli_ctx, _):
    return cf_eventgrid(cli_ctx).topic_types

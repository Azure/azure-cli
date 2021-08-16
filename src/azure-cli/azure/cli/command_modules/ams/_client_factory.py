# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def cf_media(cli_ctx, *_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.media import AzureMediaServices
    return get_mgmt_service_client(cli_ctx, AzureMediaServices)


def get_mediaservices_client(cli_ctx, *_):
    return cf_media(cli_ctx).mediaservices


def _auth_client_factory(cli_ctx, scope=None):
    import re
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    subscription_id = None
    if scope:
        matched = re.match('/subscriptions/(?P<subscription>[^/]*)/', scope)
        if matched:
            subscription_id = matched.groupdict()['subscription']
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION, subscription_id=subscription_id)


def _graph_client_factory(cli_ctx, **_):
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import configure_common_settings
    from azure.graphrbac import GraphRbacManagementClient
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        resource=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    client = GraphRbacManagementClient(cred, tenant_id,
                                       base_url=cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    configure_common_settings(cli_ctx, client)
    return client


def get_transforms_client(cli_ctx, *_):
    return cf_media(cli_ctx).transforms


def get_assets_client(cli_ctx, *_):
    return cf_media(cli_ctx).assets


def get_jobs_client(cli_ctx, *_):
    return cf_media(cli_ctx).jobs


def get_streaming_locators_client(cli_ctx, *_):
    return cf_media(cli_ctx).streaming_locators


def get_streaming_policies_client(cli_ctx, *_):
    return cf_media(cli_ctx).streaming_policies


def get_streaming_endpoints_client(cli_ctx, *_):
    return cf_media(cli_ctx).streaming_endpoints


def get_locations_client(cli_ctx, *_):
    return cf_media(cli_ctx).locations


def get_live_events_client(cli_ctx, *_):
    return cf_media(cli_ctx).live_events


def get_live_outputs_client(cli_ctx, *_):
    return cf_media(cli_ctx).live_outputs


def get_content_key_policies_client(cli_ctx, *_):
    return cf_media(cli_ctx).content_key_policies


def get_account_filters_client(cli_ctx, *_):
    return cf_media(cli_ctx).account_filters


def get_asset_filters_client(cli_ctx, *_):
    return cf_media(cli_ctx).asset_filters

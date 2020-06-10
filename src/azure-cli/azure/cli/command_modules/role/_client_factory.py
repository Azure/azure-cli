# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _auth_client_factory(cli_ctx, scope=None):
    import re
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
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


def _msi_client_factory(cli_ctx, **_):
    from azure.mgmt.msi import ManagedServiceIdentityClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ManagedServiceIdentityClient)


def _msi_user_identities_operations(cli_ctx, _):
    return _msi_client_factory(cli_ctx).user_assigned_identities


def _msi_operations_operations(cli_ctx, _):
    return _msi_client_factory(cli_ctx).operations

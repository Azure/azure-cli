# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _auth_client_factory(cli_ctx, scope=None):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client

    subscription_id = None
    # Try to extract subscription from scope
    if scope:
        subscription_id = _extract_subscription_from_scope(scope)

    # Try to extract subscription from --subscription argument or use the current subscription
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_AUTHORIZATION, subscription_id=subscription_id)


def _graph_client_factory(cli_ctx, scope=None, **_):
    from azure.cli.core._profile import Profile
    from azure.cli.core.commands.client_factory import configure_common_settings
    from azure.graphrbac import GraphRbacManagementClient

    subscription_id = None
    # Try to extract subscription from scope
    if scope:
        subscription_id = _extract_subscription_from_scope(scope)

    # Try to extract subscription from --subscription argument
    if not subscription_id and 'subscription_id' in cli_ctx.data:
        subscription_id = cli_ctx.data['subscription_id']

    # If subscription is still None, use the current subscription
    profile = Profile(cli_ctx=cli_ctx)
    cred, _, tenant_id = profile.get_login_credentials(
        subscription_id=subscription_id,
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


def _extract_subscription_from_scope(scope):
    """Extract subscription ID from scope. For example:
    /subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/rg1 -> 0b1f6471-1bf0-4dda-aec3-cb9272f09590

    Subscription can be missing from the scope, such as '/providers/Microsoft.Management/managementGroups/mg1'.
    """
    from azure.mgmt.core.tools import parse_resource_id
    return parse_resource_id(scope).get('subscription')

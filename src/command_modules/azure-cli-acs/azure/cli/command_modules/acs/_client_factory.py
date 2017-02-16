# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _auth_client_factory(scope=None):
    import re
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.mgmt.authorization import AuthorizationManagementClient
    subscription_id = None
    if scope:
        matched = re.match('/subscriptions/(?P<subscription>[^/]*)/', scope)
        if matched:
            subscription_id = matched.groupdict()['subscription']
    return get_mgmt_service_client(AuthorizationManagementClient, subscription_id=subscription_id)


def _graph_client_factory(**_):
    from azure.cli.core._profile import Profile, CLOUD
    from azure.cli.core.commands.client_factory import configure_common_settings
    from azure.graphrbac import GraphRbacManagementClient
    profile = Profile()
    cred, _, tenant_id = profile.get_login_credentials(
        resource=CLOUD.endpoints.active_directory_graph_resource_id)
    client = GraphRbacManagementClient(cred,
                                       tenant_id,
                                       base_url=CLOUD.endpoints.active_directory_graph_resource_id)
    configure_common_settings(client)
    return client

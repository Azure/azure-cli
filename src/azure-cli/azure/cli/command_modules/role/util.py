# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

logger = get_logger(__name__)


def _get_current_user_object_id(graph_client):
    # Calling this API with a service principal raises GraphError:
    #   /me request is only valid with delegated authentication flow.
    current_user = graph_client.signed_in_user_get()
    return current_user['id']


def _get_object_id_by_spn(graph_client, spn):
    accounts = list(graph_client.service_principal_list(filter="servicePrincipalNames/any(c:c eq '{}')".format(spn)))
    # 2+ matches should never happen, so we only check 'no match' here
    if not accounts:
        logger.warning("Unable to find service principal with spn '%s'", spn)
        return None
    return accounts[0]['id']


def _get_object_id_by_upn(graph_client, upn):
    accounts = list(graph_client.user_list(filter="userPrincipalName eq '{}'".format(upn)))
    # 2+ matches should never happen, so we only check 'no match' here
    if not accounts:
        logger.warning("Unable to find user with upn '%s'", upn)
        return None
    return accounts[0]['id']


def _get_object_id_from_subscription(graph_client, subscription):
    if subscription['user']['type'] == 'user':
        return _get_object_id_by_upn(graph_client, subscription['user']['name'])
    if subscription['user']['type'] == 'servicePrincipal':
        return _get_object_id_by_spn(graph_client, subscription['user']['name'])
    return None


def _get_object_id(graph_client, spn=None, upn=None):
    if spn:
        return _get_object_id_by_spn(graph_client, spn)
    if upn:
        return _get_object_id_by_upn(graph_client, upn)
    return None


def get_object_id(cli_ctx, spn=None, upn=None):
    from azure.cli.command_modules.role import graph_client_factory
    graph_client = graph_client_factory(cli_ctx)
    return _get_object_id(graph_client, spn=spn, upn=upn)


def get_current_identity_object_id(cli_ctx):
    """This function tries to get the current identity's object ID following below steps:

    1. First try to resolve with /me API: https://learn.microsoft.com/en-us/graph/api/user-get
    2. If failed, try to resolve with either
      - /users API: https://learn.microsoft.com/en-us/graph/api/user-list
      - /servicePrincipals API: https://learn.microsoft.com/en-us/graph/api/serviceprincipal-list

    If all of these attempts fail, return None.
    """
    from azure.cli.command_modules.role import graph_client_factory, GraphError
    graph_client = graph_client_factory(cli_ctx)

    try:
        return _get_current_user_object_id(graph_client)
    except GraphError:
        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx)
        # To align with _get_current_user_object_id, only look up the current upn/spn, so
        # cli_ctx.data['subscription_id'] should not be used in get_subscription.
        # Otherwise, it may result in looking up a upn/spn different from the current login context.
        subscription = profile.get_subscription()
        return _get_object_id_from_subscription(graph_client, subscription)

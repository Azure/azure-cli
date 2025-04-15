# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.acs._client_factory import get_graph_client
from azure.cli.command_modules.acs._helpers import _get_test_sp_object_id
from azure.cli.core.azclierror import AzCLIError
from knack.log import get_logger

logger = get_logger(__name__)


def resolve_object_id(cli_ctx, assignee):
    if assignee is None:
        raise AzCLIError('Inputted parameter "assignee" is None.')
    # the assignee is the test sp
    object_id = _get_test_sp_object_id(assignee)
    if object_id:
        return object_id
    client = get_graph_client(cli_ctx)
    result = None
    # looks like a user principal name, find by upn (e.g., xxx@xxx.xxx)
    if assignee.find("@") >= 0:
        result = list(client.user_list(filter="userPrincipalName eq '{}'".format(assignee)))
    # find by spn (e.g., appId like xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    if not result:
        result = list(client.service_principal_list(filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    # find by display name (e.g., my-aks-sp)
    if not result:
        result = list(client.service_principal_list(filter="displayName eq '{}'".format(assignee)))
    # find by object id (e.g., (object) id like xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    if not result:
        body = {"ids": [assignee], "types": ["user", "group", "servicePrincipal", "directoryObjectPartnerReference"]}
        result = list(client.directory_object_get_by_ids(body))

    # 2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise AzCLIError("No matches in graph database for '{}'".format(assignee))
    return result[0]["id"]

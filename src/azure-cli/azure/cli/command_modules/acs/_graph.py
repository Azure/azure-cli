# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import binascii
import datetime
import os
import time
import uuid
from typing import List

import dateutil
from azure.cli.command_modules.acs._client_factory import cf_graph_client
from azure.cli.command_modules.role import GraphError
from azure.cli.core.azclierror import AzCLIError
from dateutil.relativedelta import relativedelta
from knack.log import get_logger

logger = get_logger(__name__)


def resolve_object_id(cli_ctx, assignee):
    client = cf_graph_client(cli_ctx)
    result = None
    if assignee is None:
        raise AzCLIError('Inputted parameter "assignee" is None.')
    # looks like a user principal name, find by upn
    if assignee.find("@") >= 0:
        result = list(client.user_list(filter="userPrincipalName eq '{}'".format(assignee)))
    # find by spn
    if not result:
        result = list(client.service_principal_list(filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    # find by display name
    if not result:
        result = list(client.service_principal_list(filter="displayName eq '{}'".format(assignee)))
    # find by object id
    if not result:
        body = {"ids": [assignee], "types": ["user", "group", "servicePrincipal", "directoryObjectPartnerReference"]}
        result = list(client.directory_object_get_by_ids(body))

    # 2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise AzCLIError("No matches in graph database for '{}'".format(assignee))
    return result[0]["id"]


def create_service_principal(cli_ctx, identifier, resolve_app=True, graph_client=None):
    if graph_client is None:
        graph_client = cf_graph_client(cli_ctx)

    if resolve_app:
        try:
            uuid.UUID(identifier)
            result = list(graph_client.application_list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
            result = list(graph_client.application_list(filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        if not result:  # assume we get an object id
            result = [graph_client.application_get(identifier)]
        app_id = result[0]["appId"]
    else:
        app_id = identifier

    sp_create_body = {"appId": app_id, "accountEnabled": True}
    return graph_client.service_principal_create(sp_create_body)


def _build_application_creds(password=None, start_date=None, end_date=None):
    from azure.cli.command_modules.role.custom import _datetime_to_utc

    if not start_date:
        start_date = datetime.datetime.utcnow()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + relativedelta(years=1)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)

    password_creds = None
    if password:
        password_creds = [
            {
                "startDateTime": _datetime_to_utc(start_date),
                "endDateTime": _datetime_to_utc(end_date),
                "keyId": str(uuid.uuid4()),
                # "secretText": password,
            }
        ]
    return password_creds


def create_application(
    client,
    display_name: str,
    homepage: str,
    identifier_uris: List[str],
    password=None,
    start_date=None,
    end_date=None,
):
    password_creds = _build_application_creds(password, start_date, end_date)
    app_create_body = {
        "displayName": display_name,
        "identifierUris": identifier_uris,
        "passwordCredentials": password_creds,
        "web": {
            "homePageUrl": homepage,
        },
    }
    try:
        result = client.application_create(app_create_body)
        return result
    except GraphError as ex:
        if "insufficient privileges" in str(ex).lower():
            link = "https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal"  # pylint: disable=line-too-long
            raise AzCLIError(
                "Directory permission is needed for the current user to register the application. "
                "For how to configure, please refer '{}'. Original error: {}".format(link, ex)
            )
        raise


def build_service_principal(graph_client, cli_ctx, name, url, client_secret):
    # use get_progress_controller
    hook = cli_ctx.get_progress_controller(True)
    hook.add(messsage="Creating service principal", value=0, total_val=1.0)
    logger.info("Creating service principal")
    # always create application with 5 years expiration
    start_date = datetime.datetime.utcnow()
    end_date = start_date + relativedelta(years=5)
    result = create_application(
        graph_client, name, url, [url], password=client_secret, start_date=start_date, end_date=end_date
    )
    service_principal = result["appId"]  # pylint: disable=no-member
    for x in range(0, 10):
        hook.add(message="Creating service principal", value=0.1 * x, total_val=1.0)
        try:
            create_service_principal(cli_ctx, service_principal, graph_client=graph_client)
            break
        # TODO figure out what exception AAD throws here sometimes.
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(str(ex))
        time.sleep(2 + 2 * x)
    else:
        return False
    hook.add(message="Finished service principal creation", value=1.0, total_val=1.0)
    logger.info("Finished service principal creation")
    return service_principal


def _create_client_secret():
    # Add a special character to satisfy AAD SP secret requirements
    special_char = "$"
    client_secret = binascii.b2a_hex(os.urandom(10)).decode("utf-8") + special_char
    return client_secret


# pylint: disable=unused-argument
def ensure_aks_service_principal(
    cli_ctx,
    service_principal=None,
    client_secret=None,
    subscription_id=None,
    dns_name_prefix=None,
    fqdn_subdomain=None,
    location=None,
    name=None,
):
    aad_session_key = None
    # TODO: This really needs to be unit tested.
    graph_client = cf_graph_client(cli_ctx)
    if not service_principal:
        # --service-principal not specified, make one.
        if not client_secret:
            client_secret = _create_client_secret()
        salt = binascii.b2a_hex(os.urandom(3)).decode("utf-8")
        if dns_name_prefix:
            url = "https://{}.{}.{}.cloudapp.azure.com".format(salt, dns_name_prefix, location)
        else:
            url = "https://{}.{}.{}.cloudapp.azure.com".format(salt, fqdn_subdomain, location)

        service_principal = build_service_principal(graph_client, cli_ctx, name, url, client_secret)
        if not service_principal:
            raise AzCLIError(
                "Could not create a service principal with the right permissions. " "Are you an Owner on this project?"
            )
        logger.info("Created a service principal: %s", service_principal)
        # We don't need to add role assignment for this created SPN
    else:
        # --service-principal specfied, validate --client-secret was too
        if not client_secret:
            raise AzCLIError("--client-secret is required if --service-principal is specified")
    return {
        "client_secret": client_secret,
        "service_principal": service_principal,
        "aad_session_key": aad_session_key,
    }

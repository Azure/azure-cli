# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import binascii
import datetime
import os
import time
import uuid

import dateutil
from azure.cli.command_modules.acs._client_factory import get_graph_rbac_management_client
from azure.cli.core.azclierror import AzCLIError
from azure.graphrbac.models import (
    ApplicationCreateParameters,
    GetObjectsParameters,
    GraphErrorException,
    KeyCredential,
    PasswordCredential,
    ServicePrincipalCreateParameters,
)
from knack.log import get_logger

logger = get_logger(__name__)


def _get_object_stubs(graph_client, assignees):
    params = GetObjectsParameters(include_directory_object_references=True, object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))


def resolve_object_id(cli_ctx, assignee):
    client = get_graph_rbac_management_client(cli_ctx)
    result = None
    if assignee is None:
        raise AzCLIError('Inputted parameter "assignee" is None.')
    if assignee.find("@") >= 0:  # looks like a user principal name
        result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
    if not result:
        result = list(client.service_principals.list(filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    if not result:  # assume an object id, let us verify it
        result = _get_object_stubs(client, [assignee])

    # 2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise AzCLIError("No matches in graph database for '{}'".format(assignee))

    return result[0].object_id


def _build_application_creds(
    password=None, key_value=None, key_type=None, key_usage=None, start_date=None, end_date=None
):
    if password and key_value:
        raise AzCLIError("specify either --password or --key-value, but not both.")

    if not start_date:
        start_date = datetime.datetime.utcnow()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + dateutil.relativedelta(years=1)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)

    key_type = key_type or "AsymmetricX509Cert"
    key_usage = key_usage or "Verify"

    password_creds = None
    key_creds = None
    if password:
        password_creds = [
            PasswordCredential(start_date=start_date, end_date=end_date, key_id=str(uuid.uuid4()), value=password)
        ]
    elif key_value:
        key_creds = [
            KeyCredential(
                start_date=start_date,
                end_date=end_date,
                value=key_value,
                key_id=str(uuid.uuid4()),
                usage=key_usage,
                type=key_type,
            )
        ]

    return (password_creds, key_creds)


def create_application(
    client,
    display_name,
    homepage,
    identifier_uris,
    available_to_other_tenants=False,
    password=None,
    reply_urls=None,
    key_value=None,
    key_type=None,
    key_usage=None,
    start_date=None,
    end_date=None,
    required_resource_accesses=None,
):
    password_creds, key_creds = _build_application_creds(password, key_value, key_type, key_usage, start_date, end_date)

    app_create_param = ApplicationCreateParameters(
        available_to_other_tenants=available_to_other_tenants,
        display_name=display_name,
        identifier_uris=identifier_uris,
        homepage=homepage,
        reply_urls=reply_urls,
        key_credentials=key_creds,
        password_credentials=password_creds,
        required_resource_access=required_resource_accesses,
    )
    try:
        result = client.create(app_create_param, raw=True)
        return result.output, result.response.headers["ocp-aad-session-key"]
    except GraphErrorException as ex:
        if "insufficient privileges" in str(ex).lower():
            link = "https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal"  # pylint: disable=line-too-long
            raise AzCLIError(
                "Directory permission is needed for the current user to register the application. "
                "For how to configure, please refer '{}'. Original error: {}".format(link, ex)
            )
        raise


def create_service_principal(cli_ctx, identifier, resolve_app=True, rbac_client=None):
    if rbac_client is None:
        rbac_client = get_graph_rbac_management_client(cli_ctx)

    if resolve_app:
        try:
            uuid.UUID(identifier)
            result = list(rbac_client.applications.list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
            result = list(rbac_client.applications.list(filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        if not result:  # assume we get an object id
            result = [rbac_client.applications.get(identifier)]
        app_id = result[0].app_id
    else:
        app_id = identifier

    return rbac_client.service_principals.create(ServicePrincipalCreateParameters(app_id=app_id, account_enabled=True))


def build_service_principal(rbac_client, cli_ctx, name, url, client_secret):
    # use get_progress_controller
    hook = cli_ctx.get_progress_controller(True)
    hook.add(messsage="Creating service principal", value=0, total_val=1.0)
    logger.info("Creating service principal")
    # always create application with 5 years expiration
    start_date = datetime.datetime.utcnow()
    end_date = start_date + dateutil.relativedelta(years=5)
    result, aad_session_key = create_application(
        rbac_client.applications, name, url, [url], password=client_secret, start_date=start_date, end_date=end_date
    )
    service_principal = result.app_id  # pylint: disable=no-member
    for x in range(0, 10):
        hook.add(message="Creating service principal", value=0.1 * x, total_val=1.0)
        try:
            create_service_principal(cli_ctx, service_principal, rbac_client=rbac_client)
            break
        # TODO figure out what exception AAD throws here sometimes.
        except Exception as ex:  # pylint: disable=broad-except
            logger.error(str(ex))
        time.sleep(2 + 2 * x)
    else:
        return False, aad_session_key
    hook.add(message="Finished service principal creation", value=1.0, total_val=1.0)
    logger.info("Finished service principal creation")
    return service_principal, aad_session_key


def _create_client_secret():
    # Add a special character to satisfy AAD SP secret requirements
    special_char = "$"
    client_secret = binascii.b2a_hex(os.urandom(10)).decode("utf-8") + special_char
    return client_secret


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
    rbac_client = get_graph_rbac_management_client(cli_ctx)
    if not service_principal:
        # --service-principal not specified, make one.
        if not client_secret:
            client_secret = _create_client_secret()
        salt = binascii.b2a_hex(os.urandom(3)).decode("utf-8")
        if dns_name_prefix:
            url = "https://{}.{}.{}.cloudapp.azure.com".format(salt, dns_name_prefix, location)
        else:
            url = "https://{}.{}.{}.cloudapp.azure.com".format(salt, fqdn_subdomain, location)

        service_principal, aad_session_key = build_service_principal(rbac_client, cli_ctx, name, url, client_secret)
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

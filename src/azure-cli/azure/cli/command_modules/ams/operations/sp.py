# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import datetime
import time
import re

from dateutil.relativedelta import relativedelta

from knack.util import CLIError, todict
from knack.log import get_logger
from msrest.serialization import TZ_UTC
from azure.core.exceptions import HttpResponseError
from azure.cli.core._profile import Profile

from azure.cli.command_modules.ams._client_factory import (_graph_client_factory, _auth_client_factory)
from azure.cli.command_modules.ams._utils import (_gen_guid, _is_guid)
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.command_modules.role import GraphError

logger = get_logger(__name__)


def reset_sp_credentials_for_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None,
                                          role='Contributor', password_display_name=None, xml=False, years=1):
    ams = client.get(resource_group_name, account_name)

    graph_client = _graph_client_factory(cmd.cli_ctx)

    sp_name = _create_sp_name(account_name, sp_name) if sp_name is None else sp_name

    app_display_name = sp_name.replace('http://', '')

    aad_sp = _get_service_principal(graph_client, sp_name)
    if not aad_sp:
        raise CLIError("Can't find a service principal matching '{}'".format(app_display_name))

    app_id = aad_sp['appId']  # pylint: disable=unsubscriptable-object
    sp_oid = aad_sp['id']  # pylint: disable=unsubscriptable-object

    profile = Profile(cli_ctx=cmd.cli_ctx)
    _, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    app_object_id = _get_application_object_id(graph_client, app_id)

    new_password = add_sp_password(graph_client, entity_name_string='password', app_id=app_object_id,
                                   password_display_name=password_display_name, years=years)

    _assign_role(cmd, entity_name_string="role assignment", role=role, sp_oid=sp_oid, scope=ams.id)

    return _build_sp_result(subscription_id, ams.location, resource_group_name, account_name,
                            tenant_id, app_id, app_display_name, new_password, password_display_name,
                            cmd.cli_ctx.cloud.endpoints.management, cmd.cli_ctx.cloud.endpoints.active_directory,
                            cmd.cli_ctx.cloud.endpoints.resource_manager, role, xml)


def create_or_update_assign_sp_to_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None,
                                               new_sp_name=None, role=None, password_display_name=None,
                                               xml=False, years=None):
    ams = client.get(resource_group_name, account_name)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    graph_client = _graph_client_factory(cmd.cli_ctx)

    sp_name = _create_sp_name(account_name, sp_name)

    app_display_name = sp_name.replace('http://', '')

    aad_sp = _get_service_principal(graph_client, app_display_name)
    if aad_sp:
        return _update_sp(cmd, graph_client, aad_sp, ams, account_name, resource_group_name,
                          app_display_name, new_sp_name, role, years, password_display_name, xml)

    aad_application = create_application(graph_client,
                                         display_name=app_display_name)
    app_id = aad_application['appId']
    app_object_id = aad_application['id']

    profile = Profile(cli_ctx=cmd.cli_ctx)
    _, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    created_password = add_sp_password(graph_client, entity_name_string='password', app_id=app_object_id,
                                       password_display_name=password_display_name, years=years)

    sp_oid = _create_service_principal(graph_client, entity_name_string='service principal', app_id=app_id)

    if role is None:
        role = 'Contributor'
    _assign_role(cmd, entity_name_string="role assignment", role=role, sp_oid=sp_oid, scope=ams.id)

    return _build_sp_result(subscription_id, ams.location, resource_group_name, account_name,
                            tenant_id, app_id, app_display_name, created_password, password_display_name,
                            cmd.cli_ctx.cloud.endpoints.management, cmd.cli_ctx.cloud.endpoints.active_directory,
                            cmd.cli_ctx.cloud.endpoints.resource_manager, role, xml)


def _update_sp(cmd, graph_client, aad_sp, ams, account_name, resource_group_name, display_name,
               new_sp_name, role, years, sp_password, xml):
    profile = Profile(cli_ctx=cmd.cli_ctx)
    _, _, tenant_id = profile.get_login_credentials(
        resource=cmd.cli_ctx.cloud.endpoints.active_directory_graph_resource_id)
    sp_oid = aad_sp['id']
    app_id = aad_sp['appId']
    app_object_id = _get_application_object_id(graph_client, app_id)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    if sp_password or years:
        raise CLIError("To update the credentials please use the reset-credentials command.")

    if new_sp_name:
        display_name = new_sp_name.replace('http://', '')
        update_application(graph_client, app_object_id, display_name)

    if role:
        _assign_role(cmd, entity_name_string="role assignment", role=role, sp_oid=sp_oid, scope=ams.id)

    return _build_sp_result(subscription_id=subscription_id, location=ams.location,
                            resource_group_name=resource_group_name, account_name=account_name,
                            tenant=tenant_id, app_id=app_id, sp_name=display_name, sp_password=None,
                            password_friendly=None, management_endpoint=cmd.cli_ctx.cloud.endpoints.management,
                            active_directory_endpoint=cmd.cli_ctx.cloud.endpoints.active_directory,
                            resource_manager_endpoint=cmd.cli_ctx.cloud.endpoints.resource_manager, role=role, xml=xml)


def _get_displayable_name(graph_object):
    if getattr(graph_object, 'user_principal_name', None):
        return graph_object.user_principal_name

    if getattr(graph_object, 'service_principal_names', None):
        return graph_object.service_principal_names[0]

    return graph_object.get('name') or ''


def list_role_assignments(cmd, assignee_object_id, scope=None):
    '''
    :param include_groups: include extra assignments to the groups of which the user is a
    member(transitively).
    '''
    graph_client = _graph_client_factory(cmd.cli_ctx)
    factory = _auth_client_factory(cmd.cli_ctx)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    assignments = _search_role_assignments(assignments_client, assignee_object_id)

    subscription_id = get_subscription_id(cmd.cli_ctx)

    results = todict(assignments) if assignments else []

    if not results:
        return []

    # 1. fill in logic names to get things understandable.
    # (it's possible that associated roles and principals were deleted, and we just do nothing.)
    # 2. fill in role names
    role_defs = list(definitions_client.list(
        scope=(scope if scope else '/subscriptions/' + subscription_id)))
    role_dics = {i.id: i.role_name for i in role_defs}
    for i in results:
        if role_dics.get(i['roleDefinitionId']):
            i['roleDefinitionName'] = role_dics[i['roleDefinitionId']]

    # fill in principal names
    principal_ids = set(i['principalId'] for i in results if i['principalId'])
    if principal_ids:
        try:
            principals = _get_object_stubs(graph_client, principal_ids)
            principal_dics = {i.get('principalId'): _get_displayable_name(i) for i in principals}

            for i in [r for r in results if not r.get('principalName')]:
                i['principalName'] = ''
                if principal_dics.get(i['principalId']):
                    i['principalName'] = principal_dics[i['principalId']]
        except (HttpResponseError, GraphError) as ex:
            # failure on resolving principal due to graph permission should not fail the whole thing
            logger.info("Failed to resolve graph object information per error '%s'", ex)

    return results


def _create_role_assignment(cli_ctx, role, assignee_object_id, scope):
    from azure.cli.core.profiles import ResourceType, get_sdk
    factory = _auth_client_factory(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    role_id = _resolve_role_id(cli_ctx, role, scope, definitions_client)

    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')
    parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=assignee_object_id)

    return assignments_client.create(scope=scope,
                                     role_assignment_name=_gen_guid(),
                                     parameters=parameters)


def _resolve_role_id(cli_ctx, role, scope, definitions_client):
    role_id = None
    if re.match(r'/subscriptions/.+/providers/Microsoft.Authorization/roleDefinitions/',
                role, re.I):
        role_id = role
    else:
        if _is_guid(role):
            subscription_id = get_subscription_id(cli_ctx)
            role_id = '/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(
                subscription_id, role)
        if not role_id:  # retrieve role id
            role_defs = list(definitions_client.list(scope, "roleName eq '{}'".format(role)))

            if not role_defs:
                raise CLIError("Role '{}' doesn't exist.".format(role))

            if len(role_defs) > 1:
                ids = [r.id for r in role_defs]
                err = "More than one role matches the given name '{}'. Please pick a value from '{}'"
                raise CLIError(err.format(role, ids))
            role_id = role_defs[0].id
    return role_id


def _get_object_stubs(graph_client, assignees):
    return list(graph_client.directory_object_get_by_ids({'ids': list(assignees)}))


def _get_application_object_id(client, identifier):
    return list(client.application_list(filter="appId eq '{}'".format(identifier)))[0]['id']


def retry(func):

    def inner(*args, **kwargs):
        _RETRY_TIMES = 36
        # retry till server replication is done
        for retry_time in range(0, _RETRY_TIMES):
            try:
                return func(*args, **kwargs)
                break  # pylint: disable=unreachable
            except Exception as ex:  # pylint: disable=broad-except
                if retry_time < _RETRY_TIMES:
                    time.sleep(5)
                    logger.warning('Retrying %s creation: %s/%s', kwargs['entity_name_string'],
                                   retry_time + 1, _RETRY_TIMES)
                else:
                    logger.warning("Creating %s failed for appid. Trace followed:\n%s",
                                   kwargs['entity_name_string'], ex.response.headers if hasattr(ex, 'response') else ex)
                    # pylint: disable=no-member
                    raise

    return inner


@retry
def _create_service_principal(graph_client, entity_name_string, app_id):  # pylint: disable=unused-argument
    aad_sp = graph_client.service_principal_create({"appId": app_id, 'accountEnabled': True})
    return aad_sp['id']


def create_application(client, display_name):
    app_create_param = {
        "signInAudience": "AzureADMyOrg",
        "displayName": display_name,
        "identifierUris": []
    }

    try:
        return client.application_create(app_create_param)
    except GraphError as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = ('https://docs.microsoft.com/en-us/azure/azure-resource-manager/' +
                    'resource-group-create-service-principal-portal')
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise


def update_application(client, app_object_id, display_name):
    try:
        return client.application_update(app_object_id, {"displayName": display_name})
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning(
            "Updating service principal failed for appid '%s'. Trace followed:\n%s",
            app_object_id, ex.response.headers if hasattr(ex, 'response') else ex)   # pylint: disable=no-member
        raise


def _search_role_assignments(assignments_client, assignee_object_id):
    f = "principalId eq '{}'".format(assignee_object_id)
    assignments = list(assignments_client.list(filter=f))
    return assignments


@retry
def _assign_role(cmd, entity_name_string, role, sp_oid, scope):  # pylint: disable=unused-argument
    assignments = list_role_assignments(cmd, sp_oid, scope)

    if assignments and list(filter(lambda x: x['roleDefinitionName'] == role, assignments)):
        return

    _create_role_assignment(cmd.cli_ctx, role, sp_oid, scope)


def _build_sp_result(subscription_id, location, resource_group_name, account_name,
                     tenant, app_id, sp_name, sp_password, password_friendly, management_endpoint,
                     active_directory_endpoint, resource_manager_endpoint, role, xml):
    if not sp_password:
        sp_password = "Cannot redisplay secret. Please use reset-credentials to generate a new secret."

    result = {
        'SubscriptionId': subscription_id,
        'ServicePrincipalName': sp_name,
        'Region': location,
        'Location': location,
        'ResourceGroup': resource_group_name,
        'AccountName': account_name,
        'AadTenantId': tenant,
        'AadClientId': app_id,
        'AadSecret': sp_password,
        'ArmAadAudience': management_endpoint,
        'AadEndpoint': active_directory_endpoint,
        'ArmEndpoint': resource_manager_endpoint
    }

    if password_friendly:
        result['AadSecretFriendlyName'] = password_friendly
    if role:
        result['Role'] = role

    format_xml_fn = getattr(importlib.import_module('azure.cli.command_modules.ams._format'),
                            'get_sp_create_output_{}'.format('xml'))

    return format_xml_fn(result) if xml else result


def _get_service_principal(graph_client, sp_name):
    query_exp = "displayName eq '{}'".format(sp_name)
    aad_sps = list(graph_client.service_principal_list(filter=query_exp))
    return aad_sps[0] if aad_sps else None


@retry
def add_sp_password(graph_client, entity_name_string, app_id, password_display_name, years=1):
    # pylint: disable=unused-argument
    years = 1 if years is None else years
    start_date = datetime.datetime.now(TZ_UTC)
    end_date = start_date + relativedelta(years=years)
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    password_body = {
        "passwordCredential": {
            "displayName": password_display_name,
            "endDateTime": end_date,
            "keyId": str(_gen_guid()),
            "startDateTime": start_date,
        }

    }

    password = graph_client.application_add_password(app_id, password_body)['secretText']
    return password


def _create_sp_name(account_name, sp_name):
    sp_name = '{}-access-sp'.format(account_name) if sp_name is None else sp_name
    if '://' not in sp_name:
        sp_name = "http://" + sp_name
    return sp_name


def list_role_definitions(cmd):
    definitions_client = _auth_client_factory(cmd.cli_ctx, None).role_definitions
    subscription_id = get_subscription_id(cmd.cli_ctx)
    scope = '/subscriptions/' + subscription_id
    return list(definitions_client.list(scope))

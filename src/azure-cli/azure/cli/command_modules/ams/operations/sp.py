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
from msrestazure.azure_exceptions import CloudError
from azure.graphrbac.models import (ApplicationCreateParameters,
                                    ApplicationUpdateParameters,
                                    GraphErrorException,
                                    ServicePrincipalCreateParameters)

from azure.cli.command_modules.ams._client_factory import (_graph_client_factory, _auth_client_factory)
from azure.cli.command_modules.ams._utils import (_gen_guid, _is_guid)

logger = get_logger(__name__)


def reset_sp_credentials_for_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None,
                                          role='Contributor', sp_password=None, xml=False, years=None):
    ams = client.get(resource_group_name, account_name)

    graph_client = _graph_client_factory(cmd.cli_ctx)

    sp_name = _create_sp_name(account_name, sp_name)
    sp_password = _create_sp_password(sp_password)

    app_display_name = sp_name.replace('http://', '')

    aad_sp = _get_service_principal(graph_client, sp_name)
    if not aad_sp:
        raise CLIError("Can't find a service principal matching '{}'".format(app_display_name))

    tenant = graph_client.config.tenant_id
    sp_oid = aad_sp.object_id
    app_id = aad_sp.app_id

    app_object_id = _get_application_object_id(graph_client.applications, app_id)

    _update_password_credentials(graph_client, app_object_id, sp_password, years)

    _assign_role(cmd, role, sp_oid, ams.id)

    return _build_sp_result(client.config.subscription_id, ams.location, resource_group_name, account_name,
                            tenant, app_id, app_display_name, sp_password, cmd.cli_ctx.cloud.endpoints.management,
                            cmd.cli_ctx.cloud.endpoints.active_directory,
                            cmd.cli_ctx.cloud.endpoints.resource_manager, role, xml)


def create_or_update_assign_sp_to_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None,
                                               new_sp_name=None, role='Contributor', sp_password=None,
                                               xml=False, years=None):
    ams = client.get(resource_group_name, account_name)

    graph_client = _graph_client_factory(cmd.cli_ctx)

    sp_name = _create_sp_name(account_name, sp_name)

    app_display_name = sp_name.replace('http://', '')

    aad_sp = _get_service_principal(graph_client, sp_name)
    if aad_sp:
        return _update_sp(cmd, client, graph_client, aad_sp, ams, account_name, resource_group_name,
                          app_display_name, new_sp_name, role, years, sp_password, xml)

    sp_password = _create_sp_password(sp_password)
    aad_application = create_application(graph_client.applications,
                                         display_name=app_display_name,
                                         homepage=sp_name,
                                         years=years,
                                         password=sp_password,
                                         identifier_uris=[sp_name],
                                         available_to_other_tenants=False)

    app_id = aad_application.app_id
    tenant = graph_client.config.tenant_id
    sp_oid = _create_service_principal(graph_client, name=sp_name,
                                       app_id=app_id)

    _assign_role(cmd, role, sp_oid, ams.id)

    return _build_sp_result(client.config.subscription_id, ams.location, resource_group_name, account_name,
                            tenant, app_id, app_display_name, sp_password, cmd.cli_ctx.cloud.endpoints.management,
                            cmd.cli_ctx.cloud.endpoints.active_directory,
                            cmd.cli_ctx.cloud.endpoints.resource_manager, role, xml)


def _update_sp(cmd, client, graph_client, aad_sp, ams, account_name, resource_group_name, display_name,
               new_sp_name, role, years, sp_password, xml):
    tenant = graph_client.config.tenant_id
    sp_oid = aad_sp.object_id
    app_id = aad_sp.app_id
    app_object_id = _get_application_object_id(graph_client.applications, app_id)

    if sp_password or years:
        raise CLIError("To update the credentials please use the reset-credentials command.")

    if new_sp_name:
        display_name = new_sp_name.replace('http://', '')
        update_application(graph_client.applications, app_object_id, display_name)

    if role:
        _assign_role(cmd, role, sp_oid, ams.id)

    return _build_sp_result(client.config.subscription_id, ams.location, resource_group_name, account_name,
                            tenant, app_id, display_name, sp_password, cmd.cli_ctx.cloud.endpoints.management,
                            cmd.cli_ctx.cloud.endpoints.active_directory,
                            cmd.cli_ctx.cloud.endpoints.resource_manager, role, xml)


def _update_password_credentials(client, app_object_id, sp_password, years):
    app_creds = list(client.applications.list_password_credentials(app_object_id))
    app_creds.append(_build_password_credential(sp_password, years))
    client.applications.update_password_credentials(app_object_id, app_creds)


def _get_displayable_name(graph_object):
    if getattr(graph_object, 'user_principal_name', None):
        return graph_object.user_principal_name

    if getattr(graph_object, 'service_principal_names', None):
        return graph_object.service_principal_names[0]

    return graph_object.display_name or ''


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

    results = todict(assignments) if assignments else []

    if not results:
        return []

    # 1. fill in logic names to get things understandable.
    # (it's possible that associated roles and principals were deleted, and we just do nothing.)
    # 2. fill in role names
    role_defs = list(definitions_client.list(
        scope=(scope if scope else '/subscriptions/' + definitions_client.config.subscription_id)))
    role_dics = {i.id: i.role_name for i in role_defs}
    for i in results:
        if role_dics.get(i['roleDefinitionId']):
            i['roleDefinitionName'] = role_dics[i['roleDefinitionId']]

    # fill in principal names
    principal_ids = set(i['principalId'] for i in results if i['principalId'])
    if principal_ids:
        try:
            principals = _get_object_stubs(graph_client, principal_ids)
            principal_dics = {i.object_id: _get_displayable_name(i) for i in principals}

            for i in [r for r in results if not r.get('principalName')]:
                i['principalName'] = ''
                if principal_dics.get(i['principalId']):
                    i['principalName'] = principal_dics[i['principalId']]
        except (CloudError, GraphErrorException) as ex:
            # failure on resolving principal due to graph permission should not fail the whole thing
            logger.info("Failed to resolve graph object information per error '%s'", ex)

    return results


def _create_role_assignment(cli_ctx, role, assignee_object_id, scope):
    from azure.cli.core.profiles import ResourceType, get_sdk
    factory = _auth_client_factory(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    role_id = _resolve_role_id(role, scope, definitions_client)

    RoleAssignmentCreateParameters = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                             'RoleAssignmentCreateParameters', mod='models',
                                             operation_group='role_assignments')
    parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=assignee_object_id)

    return assignments_client.create(scope=scope,
                                     role_assignment_name=_gen_guid(),
                                     parameters=parameters)


def _resolve_role_id(role, scope, definitions_client):
    role_id = None
    if re.match(r'/subscriptions/.+/providers/Microsoft.Authorization/roleDefinitions/',
                role, re.I):
        role_id = role
    else:
        if _is_guid(role):
            role_id = '/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(
                definitions_client.config.subscription_id, role)
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
    from azure.graphrbac.models import GetObjectsParameters
    params = GetObjectsParameters(include_directory_object_references=True, object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))


def _get_application_object_id(client, identifier):
    return list(client.list(filter="appId eq '{}'".format(identifier)))[0].object_id


def _build_password_credential(password, years):
    years = years or 1

    start_date = datetime.datetime.now(TZ_UTC)
    end_date = start_date + relativedelta(years=years)

    from azure.graphrbac.models import PasswordCredential
    return PasswordCredential(start_date=start_date, end_date=end_date, key_id=str(_gen_guid()), value=password)


def _create_service_principal(
        graph_client, name, app_id):
    _RETRY_TIMES = 36
    # retry till server replication is done
    for retry_time in range(0, _RETRY_TIMES):
        try:
            aad_sp = graph_client.service_principals.create(ServicePrincipalCreateParameters(app_id=app_id,
                                                                                             account_enabled=True))
            break
        except Exception as ex:  # pylint: disable=broad-except
            if retry_time < _RETRY_TIMES and (
                    ' does not reference ' in str(ex) or ' does not exist ' in str(ex)):
                time.sleep(5)
                logger.warning('Retrying service principal creation: %s/%s', retry_time + 1, _RETRY_TIMES)
            else:
                logger.warning(
                    "Creating service principal failed for appid '%s'. Trace followed:\n%s",
                    name, ex.response.headers if hasattr(ex, 'response') else ex)   # pylint: disable=no-member
                raise

    return aad_sp.object_id


def create_application(client, display_name, homepage, years, password, identifier_uris,
                       available_to_other_tenants=False, reply_urls=None):
    password_credential = _build_password_credential(password, years)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants=available_to_other_tenants,
                                                   display_name=display_name,
                                                   identifier_uris=identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   password_credentials=[password_credential])
    try:
        return client.create(app_create_param)
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = ('https://docs.microsoft.com/en-us/azure/azure-resource-manager/' +
                    'resource-group-create-service-principal-portal')
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise


def update_application(client, app_object_id, display_name):
    app_update_param = ApplicationUpdateParameters(display_name=display_name)

    try:
        return client.patch(app_object_id, app_update_param)
    except Exception as ex:  # pylint: disable=broad-except
        logger.warning(
            "Updating service principal failed for appid '%s'. Trace followed:\n%s",
            app_object_id, ex.response.headers if hasattr(ex, 'response') else ex)   # pylint: disable=no-member
        raise


def _search_role_assignments(assignments_client, assignee_object_id):
    f = "principalId eq '{}'".format(assignee_object_id)
    assignments = list(assignments_client.list(filter=f))
    return assignments


def _assign_role(cmd, role, sp_oid, scope):
    assignments = list_role_assignments(cmd, sp_oid, scope)

    if assignments and list(filter(lambda x: x['roleDefinitionName'] == role, assignments)):
        return

    _RETRY_TIMES = 36
    for retry_time in range(0, _RETRY_TIMES):
        try:
            _create_role_assignment(cmd.cli_ctx, role, sp_oid, scope)
            break
        except Exception as ex:  # pylint: disable=broad-except
            if retry_time < _RETRY_TIMES and ' does not exist in the directory ' in str(ex):
                time.sleep(5)
                logger.warning('Retrying role assignment creation: %s/%s', retry_time + 1,
                               _RETRY_TIMES)
                continue
            else:
                # dump out history for diagnoses
                logger.warning('Role assignment creation failed.\n')
                if getattr(ex, 'response', None) is not None:
                    logger.warning('role assignment response headers: %s\n',
                                   ex.response.headers)  # pylint: disable=no-member
                raise


def _build_sp_result(subscription_id, location, resource_group_name, account_name,
                     tenant, app_id, sp_name, sp_password, management_endpoint,
                     active_directory_endpoint, resource_manager_endoint, role, xml):
    if not sp_password:
        sp_password = "Cannot redisplay secret. Please use reset-credentials to generate a new secret."

    result = {
        'SubscriptionId': subscription_id,
        'ServicePrincipalName': sp_name,
        'Region': location,
        'Location': location,
        'ResourceGroup': resource_group_name,
        'Role': role,
        'AccountName': account_name,
        'AadTenantId': tenant,
        'AadClientId': app_id,
        'AadSecret': sp_password,
        'ArmAadAudience': management_endpoint,
        'AadEndpoint': active_directory_endpoint,
        'ArmEndpoint': resource_manager_endoint
    }

    format_xml_fn = getattr(importlib.import_module('azure.cli.command_modules.ams._format'),
                            'get_sp_create_output_{}'.format('xml'))

    return format_xml_fn(result) if xml else result


def _get_service_principal(graph_client, sp_name):
    query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format(sp_name)
    aad_sps = list(graph_client.service_principals.list(filter=query_exp))
    return aad_sps[0] if aad_sps else None


def _create_sp_password(sp_password):
    return str(_gen_guid()) if sp_password is None else sp_password


def _create_sp_name(account_name, sp_name):
    sp_name = '{}-access-sp'.format(account_name) if sp_name is None else sp_name
    if '://' not in sp_name:
        sp_name = "http://" + sp_name
    return sp_name


def list_role_definitions(cmd):
    definitions_client = _auth_client_factory(cmd.cli_ctx, None).role_definitions
    scope = '/subscriptions/' + definitions_client.config.subscription_id
    return list(definitions_client.list(scope))

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation.  All rights reserved.
# Licensed under the MIT License.  See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------

import importlib
import datetime
import time

import re
from dateutil.relativedelta import relativedelta
import pytz

from knack.util import CLIError, todict
from knack.log import get_logger

from msrestazure.azure_exceptions import CloudError
from azure.graphrbac.models.graph_error import GraphErrorException
from azure.graphrbac.models import (ApplicationCreateParameters,
                                    ServicePrincipalCreateParameters)

from ._client_factory import (_graph_client_factory, _auth_client_factory)
from ._utils import (_gen_guid, _is_guid)

logger = get_logger(__name__)


def list_mediaservices(client, resource_group_name=None):
    return client.list(resource_group_name) if resource_group_name else client.list_by_subscription()


def create_mediaservice(client, resource_group_name, account_name, storage_account, location=None, tags=None):
    storage_account_id = _build_storage_account_id(client.config.subscription_id,
                                                   resource_group_name,
                                                   storage_account)

    from azure.mediav3.models import StorageAccount
    storage_account_primary = StorageAccount('Primary', storage_account_id)

    return create_or_update_mediaservice(client, resource_group_name, account_name, [storage_account_primary],
                                         location,
                                         tags)


def add_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    storage_account_id = _build_storage_account_id(client.config.subscription_id,
                                                   resource_group_name,
                                                   storage_account)

    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account in s.id, ams.storage_accounts))

    from azure.mediav3.models import StorageAccount
    storage_account_secondary = StorageAccount('Secondary', storage_account_id)

    if not storage_accounts_filtered:
        ams.storage_accounts.append(storage_account_secondary)

    return create_or_update_mediaservice(client, resource_group_name, account_name,
                                         ams.storage_accounts,
                                         ams.location,
                                         ams.tags)


def remove_mediaservice_secondary_storage(client, resource_group_name, account_name, storage_account):
    ams = client.get(resource_group_name, account_name)

    storage_accounts_filtered = list(filter(lambda s: storage_account not in s.id and 'Secondary' in s.type.value,
                                            ams.storage_accounts))

    primary_storage_account = list(filter(lambda s: 'Primary' in s.type.value, ams.storage_accounts))[0]
    storage_accounts_filtered.append(primary_storage_account)

    return create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts_filtered,
                                         ams.location,
                                         ams.tags)


def create_or_update_mediaservice(client, resource_group_name, account_name, storage_accounts=None,
                                  location=None,
                                  tags=None):

    from azure.mediav3.models import MediaService
    media_service = MediaService(location=location, storage_accounts=storage_accounts, tags=tags)

    return client.create_or_update(resource_group_name, account_name, media_service)


def _build_storage_account_id(subscription_id, resource_group_name, storage_account):
    id_template = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Storage/storageAccounts/{2}"
    return id_template.format(subscription_id,
                              resource_group_name,
                              storage_account)


def create_assign_sp_to_mediaservice(cmd, client, account_name, resource_group_name, sp_name=None,
                                     role='Contributor', sp_password=None, xml=False, years=None):
    ams = client.get(resource_group_name, account_name)

    graph_client = _graph_client_factory(cmd.cli_ctx)

    sp_name = '{}-access-sp'.format(account_name) if sp_name is None else sp_name
    sp_password = str(_gen_guid()) if sp_password is None else sp_password

    app_display_name = sp_name

    app_id = None
    sp_oid = None
    tenant = graph_client.config.tenant_id

    if '://' not in sp_name:
        sp_name = "http://" + sp_name

    years = years or 1

    start_date = datetime.datetime.now(pytz.utc)
    end_date = start_date + relativedelta(years=years)

    query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format(sp_name)
    aad_sps = list(graph_client.service_principals.list(filter=query_exp))
    if aad_sps:
        tenant = aad_sps[0].additional_properties['appOwnerTenantId']
        sp_oid = aad_sps[0].object_id

        app_id = aad_sps[0].app_id
        app_object_id = _get_application_object_id(graph_client.applications, app_id)

        _update_password_credentials(graph_client, app_object_id, sp_password,
                                     start_date, end_date)
    else:
        aad_application = create_application(graph_client.applications,
                                             display_name=app_display_name,
                                             homepage=sp_name,
                                             identifier_uris=[sp_name],
                                             available_to_other_tenants=False,
                                             password=sp_password,
                                             start_date=start_date,
                                             end_date=end_date)

        app_id = aad_application.app_id

        sp_oid = _create_service_principal(graph_client, name=sp_name,
                                           app_id=app_id)

    assignments = list_role_assignments(cmd, sp_oid)

    if assignments:
        if not list(filter(lambda x: x['properties']['roleDefinitionName'] == role, assignments)):
            _assign_role(cmd, role, sp_oid, ams.id)
    else:
        _assign_role(cmd, role, sp_oid, ams.id)

    result = {
        'SubscriptionId': client.config.subscription_id,
        'Region': ams.location,
        'ResourceGroup': resource_group_name,
        'AccountName': account_name,
        'AadTenantId': tenant,
        'AadClientId': app_id,
        'AadSecret': sp_password,
        'ArmAadAudience': cmd.cli_ctx.cloud.endpoints.management,
        'AadEndpoint': cmd.cli_ctx.cloud.endpoints.active_directory,
        'ArmEndpoint': cmd.cli_ctx.cloud.endpoints.resource_manager
    }

    format_xml_fn = getattr(importlib.import_module('azure.cli.command_modules.ams._format'),
                            'get_sp_create_output_{}'.format('xml'))

    return format_xml_fn(result) if xml else result


def _update_password_credentials(client, app_object_id, sp_password, start_date, end_date):
    app_creds = list(client.applications.list_password_credentials(app_object_id))
    app_creds.append(_build_password_credential(sp_password, start_date, end_date))
    client.applications.update_password_credentials(app_object_id, app_creds)


def _get_displayable_name(graph_object):
    if graph_object.user_principal_name:
        return graph_object.user_principal_name
    elif graph_object.service_principal_names:
        return graph_object.service_principal_names[0]
    return graph_object.display_name or ''


def list_role_assignments(cmd, assignee_object_id):
    '''
    :param include_groups: include extra assignments to the groups of which the user is a
    member(transitively). Supported only for a user principal.
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
        scope=('/subscriptions/' + definitions_client.config.subscription_id)))
    role_dics = {i.id: i.properties.role_name for i in role_defs}
    for i in results:
        if role_dics.get(i['properties']['roleDefinitionId']):
            i['properties']['roleDefinitionName'] = role_dics[i['properties']['roleDefinitionId']]

    # fill in principal names
    principal_ids = set(i['properties']['principalId'] for i in results if i['properties']['principalId'])
    if principal_ids:
        try:
            principals = _get_object_stubs(graph_client, principal_ids)
            principal_dics = {i.object_id: _get_displayable_name(i) for i in principals}

            for i in [r for r in results if not r['properties'].get('principalName')]:
                i['properties']['principalName'] = ''
                if principal_dics.get(i['properties']['principalId']):
                    i['properties']['principalName'] = principal_dics[i['properties']['principalId']]
        except (CloudError, GraphErrorException) as ex:
            # failure on resolving principal due to graph permission should not fail the whole thing
            logger.info("Failed to resolve graph object information per error '%s'", ex)

    return results


def _create_role_assignment(cli_ctx, role, assignee_object_id, scope):
    factory = _auth_client_factory(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = '/subscriptions/' + assignments_client.config.subscription_id

    role_id = _resolve_role_id(role, scope, definitions_client)
    from azure.mgmt.authorization.models import RoleAssignmentProperties
    properties = RoleAssignmentProperties(role_id, assignee_object_id)
    assignment_name = _gen_guid()
    custom_headers = None
    return assignments_client.create(scope, assignment_name, properties,
                                     custom_headers=custom_headers)


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
            elif len(role_defs) > 1:
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


def _build_password_credential(password, start_date, end_date):
    from azure.graphrbac.models import PasswordCredential
    return PasswordCredential(start_date, end_date, str(_gen_guid()), password)


def _create_service_principal(
        graph_client, name, app_id):
    _RETRY_TIMES = 36
    # retry till server replication is done
    for l in range(0, _RETRY_TIMES):
        try:
            aad_sp = graph_client.service_principals.create(ServicePrincipalCreateParameters(app_id, True))
            break
        except Exception as ex:  # pylint: disable=broad-except
            if l < _RETRY_TIMES and (
                    ' does not reference ' in str(ex) or ' does not exist ' in str(ex)):
                time.sleep(5)
                logger.warning('Retrying service principal creation: %s/%s', l + 1, _RETRY_TIMES)
            else:
                logger.warning(
                    "Creating service principal failed for appid '%s'. Trace followed:\n%s",
                    name, ex.response.headers if hasattr(ex, 'response') else ex)   # pylint: disable=no-member
                raise

    return aad_sp.object_id


def create_application(client, display_name, homepage, identifier_uris,
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       start_date=None, end_date=None):
    password_credential = _build_password_credential(password, start_date, end_date)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants,
                                                   display_name,
                                                   identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   password_credentials=[password_credential])

    try:
        return client.create(app_create_param)
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise


def _search_role_assignments(assignments_client, assignee_object_id):
    f = "principalId eq '{}'".format(assignee_object_id)
    assignments = list(assignments_client.list(filter=f))
    return assignments


def _assign_role(cmd, role, sp_oid, scope):
    _RETRY_TIMES = 36
    for l in range(0, _RETRY_TIMES):
        try:
            _create_role_assignment(cmd.cli_ctx, role, sp_oid, scope)
            break
        except Exception as ex:  # pylint: disable=broad-except
            if l < _RETRY_TIMES and ' does not exist in the directory ' in str(ex):
                time.sleep(5)
                logger.warning('Retrying role assignment creation: %s/%s', l + 1,
                               _RETRY_TIMES)
                continue
            else:
                # dump out history for diagnoses
                logger.warning('Role assignment creation failed.\n')
                if getattr(ex, 'response', None) is not None:
                    logger.warning('role assignment response headers: %s\n',
                                   ex.response.headers)  # pylint: disable=no-member
                raise

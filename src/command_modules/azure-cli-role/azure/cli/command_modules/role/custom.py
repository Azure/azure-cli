# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import datetime
import json
import re
import os
import uuid
from dateutil.relativedelta import relativedelta
import dateutil.parser

from knack.log import get_logger
from knack.util import CLIError, todict

from msrest.serialization import TZ_UTC
from msrestazure.azure_exceptions import CloudError
from azure.graphrbac.models.graph_error import GraphErrorException

from azure.cli.core.util import get_file_json, shell_safe_json_parse

from azure.graphrbac.models import (ApplicationCreateParameters, ApplicationUpdateParameters, PasswordCredential,
                                    KeyCredential, UserCreateParameters, PasswordProfile,
                                    ServicePrincipalCreateParameters, RequiredResourceAccess,
                                    ResourceAccess, GroupCreateParameters, CheckGroupMembershipParameters)

from ._client_factory import _auth_client_factory, _graph_client_factory

logger = get_logger(__name__)

_CUSTOM_RULE = 'CustomRole'

# pylint: disable=too-many-lines


def list_role_definitions(cmd, name=None, resource_group_name=None, scope=None,
                          custom_role_only=False):
    definitions_client = _auth_client_factory(cmd.cli_ctx, scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    return _search_role_definitions(definitions_client, name, scope, custom_role_only)


def create_role_definition(cmd, role_definition):
    return _create_update_role_definition(cmd, role_definition, for_update=False)


def update_role_definition(cmd, role_definition):
    return _create_update_role_definition(cmd, role_definition, for_update=True)


def _get_role_property(obj, property_name):
    if isinstance(obj, dict):
        if 'properties' in obj:
            return obj['properties'][property_name]
        return obj[property_name]

    if hasattr(obj, 'properties'):
        return getattr(obj.properties, property_name)
    return getattr(obj, property_name)


def _set_role_definition_property(obj, property_name, property_value):
    if isinstance(obj, dict):
        if 'properties' in obj:
            obj['properties'][property_name] = property_value
        else:
            obj[property_name] = property_value
    else:
        if hasattr(obj, 'properties'):
            setattr(obj.properties, property_name, property_value)
        else:
            setattr(obj, property_name, property_value)


def _create_update_role_definition(cmd, role_definition, for_update):
    from azure.cli.core.profiles import ResourceType, get_sdk, get_api_version
    definitions_client = _auth_client_factory(cmd.cli_ctx).role_definitions
    if os.path.exists(role_definition):
        role_definition = get_file_json(role_definition)
    else:
        role_definition = shell_safe_json_parse(role_definition)

    if not isinstance(role_definition, dict):
        raise CLIError('Invalid role defintion. A valid dictionary JSON representation is expected.')
    # to workaround service defects, ensure property names are camel case
    names = [p for p in role_definition if p[:1].isupper()]
    for n in names:
        new_name = n[:1].lower() + n[1:]
        role_definition[new_name] = role_definition.pop(n)

    role_name = role_definition.get('name', None)
    if not role_name:
        raise CLIError("please provide role name")
    if for_update:  # for update, we need to use guid style unique name
        scopes_in_definition = role_definition.get('assignableScopes', None)
        scope = (scopes_in_definition[0] if scopes_in_definition else
                 '/subscriptions/' + definitions_client.config.subscription_id)
        matched = _search_role_definitions(definitions_client, role_name, scope)
        if len(matched) != 1:
            raise CLIError('Please provide the unique logic name of an existing role')
        role_definition['name'] = matched[0].name
        # ensure correct logical name and guid name. For update we accept both
        role_name = _get_role_property(matched[0], 'role_name')
        role_id = matched[0].name
    else:
        role_id = _gen_guid()

    if not for_update and 'assignableScopes' not in role_definition:
        raise CLIError("please provide 'assignableScopes'")

    Permission, RoleDefinition, RoleDefinitionProperties = get_sdk(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                                                   'Permission', 'RoleDefinition',
                                                                   'RoleDefinitionProperties', mod='models',
                                                                   operation_group='role_definitions')

    version = getattr(get_api_version(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION), 'role_definitions')
    if version == '2015-07-01':
        permission = Permission(actions=role_definition.get('actions', None),
                                not_actions=role_definition.get('notActions', None))

        properties = RoleDefinitionProperties(role_name=role_name,
                                              description=role_definition.get('description', None),
                                              type=_CUSTOM_RULE,
                                              assignable_scopes=role_definition['assignableScopes'],
                                              permissions=[permission])
        definition = RoleDefinition(name=role_id, properties=properties)
        return definitions_client.create_or_update(role_definition_id=role_id,
                                                   scope=properties.assignable_scopes[0],
                                                   properties=properties)

    permission = Permission(actions=role_definition.get('actions', None),
                            not_actions=role_definition.get('notActions', None),
                            data_actions=role_definition.get('dataActions', None),
                            not_data_actions=role_definition.get('notDataActions', None))

    definition = RoleDefinition(role_name=role_name,
                                description=role_definition.get('description', None),
                                role_type=_CUSTOM_RULE,
                                assignable_scopes=role_definition['assignableScopes'],
                                permissions=[permission])
    return definitions_client.create_or_update(role_definition_id=role_id,
                                               scope=definition.assignable_scopes[0],
                                               role_definition=definition)


def delete_role_definition(cmd, name, resource_group_name=None, scope=None,
                           custom_role_only=False):
    definitions_client = _auth_client_factory(cmd.cli_ctx, scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    roles = _search_role_definitions(definitions_client, name, scope, custom_role_only)
    for r in roles:
        definitions_client.delete(role_definition_id=r.name, scope=scope)


def _search_role_definitions(definitions_client, name, scope, custom_role_only=False):
    roles = list(definitions_client.list(scope))
    if name:
        roles = [r for r in roles if r.name == name or _get_role_property(r, 'role_name') == name]
    if custom_role_only:
        roles = [r for r in roles if _get_role_property(r, 'role_type') == _CUSTOM_RULE]
    return roles


def create_role_assignment(cmd, role, assignee=None, assignee_object_id=None, resource_group_name=None,
                           scope=None):
    if bool(assignee) == bool(assignee_object_id):
        raise CLIError('usage error: --assignee STRING | --assignee-object-id GUID')
    return _create_role_assignment(cmd.cli_ctx, role, assignee or assignee_object_id, resource_group_name, scope,
                                   resolve_assignee=(not assignee_object_id))


def _create_role_assignment(cli_ctx, role, assignee, resource_group_name=None, scope=None,
                            resolve_assignee=True):
    from azure.cli.core.profiles import ResourceType, get_sdk, get_api_version
    factory = _auth_client_factory(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions
    RoleAssignmentCreateParameters, RoleAssignmentProperties = get_sdk(cli_ctx, ResourceType.MGMT_AUTHORIZATION,
                                                                       'RoleAssignmentCreateParameters',
                                                                       'RoleAssignmentProperties', mod='models',
                                                                       operation_group='role_assignments')

    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(cli_ctx, assignee) if resolve_assignee else assignee
    version = getattr(get_api_version(cli_ctx, ResourceType.MGMT_AUTHORIZATION), 'role_assignments')
    assignment_name = _gen_guid()
    custom_headers = None

    if version == '2015-07-01':
        properties = RoleAssignmentProperties(role_definition_id=role_id, principal_id=object_id)
        return assignments_client.create(scope=scope, role_assignment_name=assignment_name,
                                         properties=properties,
                                         custom_headers=custom_headers)

    parameters = RoleAssignmentCreateParameters(role_definition_id=role_id, principal_id=object_id)
    return assignments_client.create(scope=scope, role_assignment_name=assignment_name,
                                     parameters=parameters,
                                     custom_headers=custom_headers)


def list_role_assignments(cmd, assignee=None, role=None, resource_group_name=None,
                          scope=None, include_inherited=False,
                          show_all=False, include_groups=False, include_classic_administrators=False):
    '''
    :param include_groups: include extra assignments to the groups of which the user is a
    member(transitively).
    '''
    graph_client = _graph_client_factory(cmd.cli_ctx)
    factory = _auth_client_factory(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    if show_all:
        if resource_group_name or scope:
            raise CLIError('group or scope are not required when --all is used')
        scope = None
    else:
        scope = _build_role_scope(resource_group_name, scope,
                                  definitions_client.config.subscription_id)

    assignments = _search_role_assignments(cmd.cli_ctx, assignments_client, definitions_client,
                                           scope, assignee, role,
                                           include_inherited, include_groups)

    results = todict(assignments) if assignments else []
    if include_classic_administrators:
        results += _backfill_assignments_for_co_admins(cmd.cli_ctx, factory, assignee)

    if not results:
        return []

    # 1. fill in logic names to get things understandable.
    # (it's possible that associated roles and principals were deleted, and we just do nothing.)
    # 2. fill in role names
    role_defs = list(definitions_client.list(
        scope=scope or ('/subscriptions/' + definitions_client.config.subscription_id)))
    role_dics = {i.id: _get_role_property(i, 'role_name') for i in role_defs}
    for i in results:
        if not i.get('roleDefinitionName'):
            if role_dics.get(_get_role_property(i, 'roleDefinitionId')):
                _set_role_definition_property(i, 'roleDefinitionName',
                                              role_dics[_get_role_property(i, 'roleDefinitionId')])
            else:
                i['roleDefinitionName'] = None  # the role definition might have been deleted

    # fill in principal names
    principal_ids = set(_get_role_property(i, 'principalId') for i in results if _get_role_property(i, 'principalId'))

    if principal_ids:
        try:
            principals = _get_object_stubs(graph_client, principal_ids)
            principal_dics = {i.object_id: _get_displayable_name(i) for i in principals}

            for i in [r for r in results if not r.get('principalName')]:
                i['principalName'] = ''
                if principal_dics.get(_get_role_property(i, 'principalId')):
                    _set_role_definition_property(i, 'principalName', _get_role_property(i, 'principalId'))
        except (CloudError, GraphErrorException) as ex:
            # failure on resolving principal due to graph permission should not fail the whole thing
            logger.info("Failed to resolve graph object information per error '%s'", ex)

    return results


def _get_assignment_events(cli_ctx, start_time=None, end_time=None):
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    client = get_mgmt_service_client(cli_ctx, MonitorManagementClient)
    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    if end_time:
        try:
            end_time = datetime.datetime.strptime(end_time, DATE_TIME_FORMAT)
        except ValueError:
            raise CLIError("Input '{}' is not valid datetime. Valid example: 2000-12-31T12:59:59Z".format(end_time))
    else:
        end_time = datetime.datetime.utcnow()

    if start_time:
        try:
            start_time = datetime.datetime.strptime(start_time, DATE_TIME_FORMAT)
            if start_time >= end_time:
                raise CLIError("Start time cannot be later than end time.")
        except ValueError:
            raise CLIError("Input '{}' is not valid datetime. Valid example: 2000-12-31T12:59:59Z".format(start_time))
    else:
        start_time = end_time - datetime.timedelta(hours=1)

    time_filter = 'eventTimestamp ge {} and eventTimestamp le {}'.format(start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                                                         end_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

    # set time range filter
    odata_filters = 'resourceProvider eq Microsoft.Authorization and {}'.format(time_filter)

    activity_log = list(client.activity_logs.list(filter=odata_filters))
    start_events, end_events, offline_events = {}, {}, []

    for l in activity_log:
        if l.http_request:
            if l.status.value == 'Started':
                start_events[l.operation_id] = l
            else:
                end_events[l.operation_id] = l
        elif l.event_name and l.event_name.value.lower() == 'classicadministrators':
            offline_events.append(l)
    return start_events, end_events, offline_events, client


# A custom command around 'monitoring' events to produce understandable output for RBAC audit, a common scenario.
def list_role_assignment_change_logs(cmd, start_time=None, end_time=None):
    # pylint: disable=too-many-nested-blocks, too-many-statements
    result = []
    start_events, end_events, offline_events, client = _get_assignment_events(cmd.cli_ctx, start_time, end_time)
    role_defs = {d.id: [_get_role_property(d, 'role_name'), d.id.split('/')[-1]] for d in list_role_definitions(cmd)}

    for op_id in start_events:
        e = end_events.get(op_id, None)
        if not e:
            continue

        entry = {}
        op = e.operation_name and e.operation_name.value
        if (op.lower().startswith('microsoft.authorization/roleassignments') and e.status.value == 'Succeeded'):
            s, payload = start_events[op_id], None
            entry = dict.fromkeys(
                ['principalId', 'principalName', 'scope', 'scopeName', 'scopeType', 'roleDefinitionId', 'roleName'],
                None)
            entry['timestamp'], entry['caller'] = e.event_timestamp, s.caller

            if s.http_request:
                if s.http_request.method == 'PUT':
                    # 'requestbody' has a wrong camel-case. Should be 'requestBody'
                    payload = s.properties and s.properties.get('requestbody')
                    entry['action'] = 'Granted'
                    entry['scope'] = e.authorization.scope
                elif s.http_request.method == 'DELETE':
                    payload = e.properties and e.properties.get('responseBody')
                    entry['action'] = 'Revoked'
            if payload:
                try:
                    payload = json.loads(payload)
                except ValueError:
                    pass
                if payload:
                    payload = payload['properties']
                    entry['principalId'] = payload['principalId']
                    if not entry['scope']:
                        entry['scope'] = payload['scope']
                    if entry['scope']:
                        index = entry['scope'].lower().find('/providers/microsoft.authorization')
                        if index != -1:
                            entry['scope'] = entry['scope'][:index]
                        parts = list(filter(None, entry['scope'].split('/')))
                        entry['scopeName'] = parts[-1]
                        if len(parts) < 3:
                            entry['scopeType'] = 'Subscription'
                        elif len(parts) < 5:
                            entry['scopeType'] = 'Resource group'
                        else:
                            entry['scopeType'] = 'Resource'

                    entry['roleDefinitionId'] = role_defs[payload['roleDefinitionId']][1]
                    entry['roleName'] = role_defs[payload['roleDefinitionId']][0]
            result.append(entry)

    # Fill in logical user/sp names as guid principal-id not readable
    principal_ids = set([x['principalId'] for x in result if x['principalId']])
    if principal_ids:
        graph_client = _graph_client_factory(cmd.cli_ctx)
        stubs = _get_object_stubs(graph_client, principal_ids)
        principal_dics = {i.object_id: _get_displayable_name(i) for i in stubs}
        if principal_dics:
            for e in result:
                e['principalName'] = principal_dics.get(e['principalId'], None)

    offline_events = [x for x in offline_events if (x.status and x.status.value == 'Succeeded' and x.operation_name and
                                                    x.operation_name.value.lower().startswith(
                                                        'microsoft.authorization/classicadministrators'))]
    for e in offline_events:
        entry = {
            'timestamp': e.event_timestamp,
            'caller': 'Subscription Admin',
            'roleDefinitionId': None,
            'principalId': None,
            'principalType': 'User',
            'scope': '/subscriptions/' + client.config.subscription_id,
            'scopeType': 'Subscription',
            'scopeName': client.config.subscription_id,
        }
        if e.properties:
            entry['principalName'] = e.properties.get('adminEmail')
            entry['roleName'] = e.properties.get('adminType')
        result.append(entry)

    return result


def _backfill_assignments_for_co_admins(cli_ctx, auth_client, assignee=None):
    co_admins = auth_client.classic_administrators.list()  # known swagger bug on api-version handling
    co_admins = [x for x in co_admins if _get_role_property(x, 'email_address')]
    graph_client = _graph_client_factory(cli_ctx)
    if assignee:  # apply assignee filter if applicable
        if _is_guid(assignee):
            try:
                result = _get_object_stubs(graph_client, [assignee])
                if not result:
                    return []
                assignee = _get_displayable_name(result[0]).lower()
            except ValueError:
                pass
        co_admins = [x for x in co_admins if assignee == _get_role_property(x, 'email_address').lower()]

    if not co_admins:
        return []

    result, users = [], []
    for i in range(0, len(co_admins), 10):  # graph allows up to 10 query filters, so split into chunks here
        upn_queries = ["userPrincipalName eq '{}'".format(_get_role_property(x, 'email_address'))
                       for x in co_admins[i:i + 10]]
        temp = list(list_users(graph_client.users, query_filter=' or '.join(upn_queries)))
        users += temp
    upns = {u.user_principal_name: u.object_id for u in users}
    for admin in co_admins:
        na_text = 'NA(classic admins)'
        email = _get_role_property(admin, 'email_address')
        result.append({
            'id': na_text,
            'name': na_text,
            'principalId': upns.get(email),
            'principalName': email,
            'roleDefinitionName': _get_role_property(admin, 'role'),
            'roleDefinitionId': 'NA(classic admin role)',
            'scope': '/subscriptions/' + auth_client.config.subscription_id
        })
    return result


def _get_displayable_name(graph_object):
    if graph_object.user_principal_name:
        return graph_object.user_principal_name
    elif graph_object.service_principal_names:
        return graph_object.service_principal_names[0]
    return graph_object.display_name or ''


def delete_role_assignments(cmd, ids=None, assignee=None, role=None,
                            resource_group_name=None, scope=None, include_inherited=False):
    factory = _auth_client_factory(cmd.cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions
    ids = ids or []
    if ids:
        if assignee or role or resource_group_name or scope or include_inherited:
            raise CLIError('When assignment ids are used, other parameter values are not required')
        for i in ids:
            assignments_client.delete_by_id(i)
        return

    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)
    assignments = _search_role_assignments(cmd.cli_ctx, assignments_client, definitions_client,
                                           scope, assignee, role, include_inherited,
                                           include_groups=False)

    if assignments:
        for a in assignments:
            assignments_client.delete_by_id(a.id)
    else:
        raise CLIError('No matched assignments were found to delete')


def _search_role_assignments(cli_ctx, assignments_client, definitions_client,
                             scope, assignee, role, include_inherited, include_groups):
    assignee_object_id = None
    if assignee:
        assignee_object_id = _resolve_object_id(cli_ctx, assignee, fallback_to_object_id=True)

    # combining filters is unsupported, so we pick the best, and do limited maunal filtering
    if assignee_object_id:
        if include_groups:
            f = "assignedTo('{}')".format(assignee_object_id)
        else:
            f = "principalId eq '{}'".format(assignee_object_id)
        assignments = list(assignments_client.list(filter=f))
    elif scope:
        assignments = list(assignments_client.list_for_scope(scope=scope, filter='atScope()'))
    else:
        assignments = list(assignments_client.list())

    if assignments:
        assignments = [a for a in assignments if (
            not scope or
            include_inherited and re.match(_get_role_property(a, 'scope'), scope, re.I) or
            _get_role_property(a, 'scope').lower() == scope.lower()
        )]

        if role:
            role_id = _resolve_role_id(role, scope, definitions_client)
            assignments = [i for i in assignments if _get_role_property(i, 'role_definition_id') == role_id]

    return assignments


def _build_role_scope(resource_group_name, scope, subscription_id):
    subscription_scope = '/subscriptions/' + subscription_id
    if scope:
        if resource_group_name:
            err = 'Resource group "{}" is redundant because scope is supplied'
            raise CLIError(err.format(resource_group_name))
    elif resource_group_name:
        scope = subscription_scope + '/resourceGroups/' + resource_group_name
    else:
        scope = subscription_scope
    return scope


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


def list_apps(client, app_id=None, display_name=None, identifier_uri=None, query_filter=None):
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if app_id:
        sub_filters.append("appId eq '{}'".format(app_id))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))
    if identifier_uri:
        sub_filters.append("identifierUris/any(s:s eq '{}')".format(identifier_uri))

    return client.list(filter=(' and '.join(sub_filters)))


def list_sps(client, spn=None, display_name=None, query_filter=None):
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if spn:
        sub_filters.append("servicePrincipalNames/any(c:c eq '{}')".format(spn))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    return client.list(filter=(' and '.join(sub_filters)))


def list_users(client, upn=None, display_name=None, query_filter=None):
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if upn:
        sub_filters.append("userPrincipalName eq '{}'".format(upn))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    return client.list(filter=(' and ').join(sub_filters))


def create_user(client, user_principal_name, display_name, password,
                mail_nickname=None, immutable_id=None, force_change_password_next_login=False):
    '''
    :param mail_nickname: mail alias. default to user principal name
    '''
    mail_nickname = mail_nickname or user_principal_name.split('@')[0]
    param = UserCreateParameters(user_principal_name=user_principal_name, account_enabled=True,
                                 display_name=display_name, mail_nickname=mail_nickname,
                                 immutable_id=immutable_id,
                                 password_profile=PasswordProfile(
                                     password=password,
                                     force_change_password_next_login=force_change_password_next_login))
    return client.create(param)


def create_group(client, display_name, mail_nickname):
    return client.create(GroupCreateParameters(display_name=display_name, mail_nickname=mail_nickname))


def check_group_membership(cmd, client, group_id, member_object_id):  # pylint: disable=unused-argument
    return client.is_member_of(CheckGroupMembershipParameters(group_id=group_id,
                                                              member_id=member_object_id))


def list_groups(client, display_name=None, query_filter=None):
    '''
    list groups in the directory
    '''
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))
    return client.list(filter=(' and ').join(sub_filters))


def create_application(client, display_name, homepage=None, identifier_uris=None,
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       key_value=None, key_type=None, key_usage=None, start_date=None, end_date=None,
                       oauth2_allow_implicit_flow=None, required_resource_accesses=None, native_app=None):
    key_creds, password_creds, required_accesses = None, None, None
    if native_app:
        if identifier_uris:
            raise CLIError("'--identifier-uris' is not required for creating a native application")
        identifier_uris = ['http://{}'.format(_gen_guid())]  # we will create a temporary one and remove it later
    else:
        if not identifier_uris:
            raise CLIError("'--identifier-uris' is required for creating an application")
        password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                             key_usage, start_date, end_date)

    if required_resource_accesses:
        required_accesses = _build_application_accesses(required_resource_accesses)

    app_patch_param = ApplicationCreateParameters(available_to_other_tenants=available_to_other_tenants,
                                                  display_name=display_name,
                                                  identifier_uris=identifier_uris,
                                                  homepage=homepage,
                                                  reply_urls=reply_urls,
                                                  key_credentials=key_creds,
                                                  password_credentials=password_creds,
                                                  oauth2_allow_implicit_flow=oauth2_allow_implicit_flow,
                                                  required_resource_access=required_accesses)

    try:
        result = client.create(app_patch_param)
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise

    if native_app:
        # AAD graph doesn't have the API to create a native app, aka public client, the recommended hack is
        # to create a web app first, then convert to a native one
        # pylint: disable=protected-access
        if 'public_client' not in ApplicationUpdateParameters._attribute_map:
            ApplicationUpdateParameters._attribute_map['public_client'] = {'key': 'publicClient', 'type': 'bool'}
        app_patch_param = ApplicationUpdateParameters(identifier_uris=[])
        setattr(app_patch_param, 'public_client', True)
        client.patch(result.object_id, app_patch_param)
        result = client.get(result.object_id)

    return result


def update_application(instance, display_name=None, homepage=None,  # pylint: disable=unused-argument
                       identifier_uris=None, password=None, reply_urls=None, key_value=None,
                       key_type=None, key_usage=None, start_date=None, end_date=None, available_to_other_tenants=None,
                       oauth2_allow_implicit_flow=None, required_resource_accesses=None):
    from azure.cli.core.commands.arm import make_camel_case, make_snake_case
    password_creds, key_creds, required_accesses = None, None, None
    if any([key_value, key_type, key_usage, start_date, end_date]):
        password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                             key_usage, start_date, end_date)

    if required_resource_accesses:
        required_accesses = _build_application_accesses(required_resource_accesses)

    # Workaround until https://github.com/Azure/azure-rest-api-specs/issues/3437 is fixed
    def _get_property(name):
        try:
            return getattr(instance, make_snake_case(name))
        except AttributeError:
            return instance.additional_properties.get(make_camel_case(name), None)

    app_patch_param = ApplicationUpdateParameters(
        display_name=display_name or _get_property('display_name'),
        homepage=homepage or _get_property('homepage'),
        identifier_uris=identifier_uris or _get_property('identifier_uris'),
        reply_urls=reply_urls or _get_property('reply_urls'),
        key_credentials=key_creds or _get_property('key_credentials'),
        password_credentials=password_creds or _get_property('password_credentials'),
        available_to_other_tenants=available_to_other_tenants or _get_property('available_to_other_tenants'),
        required_resource_access=required_accesses or _get_property('required_resource_access'),
        oauth2_allow_implicit_flow=oauth2_allow_implicit_flow or _get_property('oauth2_allow_implicit_flow'))

    return app_patch_param


def patch_application(cmd, identifier, parameters):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    object_id = _resolve_application(graph_client.applications, identifier)
    return graph_client.applications.patch(object_id, parameters)


def _build_application_accesses(required_resource_accesses):
    required_accesses = None
    for x in required_resource_accesses:
        accesses = [ResourceAccess(id=y['id'], type=y['type']) for y in x['resourceAccess']]
        if required_accesses is None:
            required_accesses = []
        required_accesses.append(RequiredResourceAccess(resource_app_id=x['resourceAppId'],
                                                        resource_access=accesses))
    return required_accesses


def show_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    return client.get(object_id)


def delete_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    client.delete(object_id)


def _resolve_application(client, identifier):
    result = list(client.list(filter="identifierUris/any(s:s eq '{}')".format(identifier)))
    if not result:
        if _is_guid(identifier):
            # it is either app id or object id, let us verify
            result = list(client.list(filter="appId eq '{}'".format(identifier)))
        else:
            raise CLIError("Application '{}' doesn't exist".format(identifier))

    return result[0].object_id if result else identifier


def _build_application_creds(password=None, key_value=None, key_type=None,
                             key_usage=None, start_date=None, end_date=None):
    if password and key_value:
        raise CLIError('specify either --password or --key-value, but not both.')

    if not start_date:
        start_date = datetime.datetime.utcnow()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + relativedelta(years=1)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)

    key_type = key_type or 'AsymmetricX509Cert'
    key_usage = key_usage or 'Verify'

    password_creds = None
    key_creds = None
    if password:
        password_creds = [PasswordCredential(start_date=start_date, end_date=end_date,
                                             key_id=str(_gen_guid()), value=password)]
    elif key_value:
        key_creds = [KeyCredential(start_date=start_date, end_date=end_date,
                                   key_id=str(_gen_guid()), value=key_value,
                                   usage=key_usage, type=key_type)]

    return (password_creds, key_creds)


def create_service_principal(cmd, identifier):
    return _create_service_principal(cmd.cli_ctx, identifier)


def _create_service_principal(cli_ctx, identifier, resolve_app=True):
    client = _graph_client_factory(cli_ctx)
    app_id = identifier
    if resolve_app:
        if _is_guid(identifier):
            result = list(client.applications.list(filter="appId eq '{}'".format(identifier)))
        else:
            result = list(client.applications.list(
                filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        try:
            if not result:  # assume we get an object id
                result = [client.applications.get(identifier)]
            app_id = result[0].app_id
        except GraphErrorException:
            pass  # fallback to appid (maybe from an external tenant?)

    return client.service_principals.create(ServicePrincipalCreateParameters(app_id, True))


def show_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    return client.get(object_id)


def delete_service_principal(cmd, identifier):
    client = _graph_client_factory(cmd.cli_ctx)
    sp_object_id = _resolve_service_principal(client.service_principals, identifier)
    app_object_id = _get_app_object_id_from_sp_object_id(client, sp_object_id)

    assignments = list_role_assignments(cmd, assignee=identifier, show_all=True)
    if assignments:
        logger.warning('Removing role assignments')
        delete_role_assignments(cmd, [a['id'] for a in assignments])

    if app_object_id:  # delete the application, and AAD service will automatically clean up the SP
        client.applications.delete(app_object_id)
    else:
        client.service_principals.delete(sp_object_id)


def _get_app_object_id_from_sp_object_id(client, sp_object_id):
    sp = client.service_principals.get(sp_object_id)
    app_object_id = None

    if sp.service_principal_names:
        result = list(client.applications.list(
            filter="identifierUris/any(s:s eq '{}')".format(sp.service_principal_names[0])))
        if result:
            app_object_id = result[0].object_id
    return app_object_id


def list_service_principal_credentials(cmd, identifier, cert=False):
    client = _graph_client_factory(cmd.cli_ctx)
    sp_object_id = _resolve_service_principal(client.service_principals, identifier)
    app_object_id = _get_app_object_id_from_sp_object_id(client, sp_object_id)
    sp_creds, app_creds = [], []
    if cert:
        sp_creds = list(client.service_principals.list_key_credentials(sp_object_id))
        if app_object_id:
            app_creds = list(client.applications.list_key_credentials(app_object_id))
    else:
        sp_creds = list(client.service_principals.list_password_credentials(sp_object_id))
        if app_object_id:
            app_creds = list(client.applications.list_password_credentials(app_object_id))

    for x in sp_creds:
        setattr(x, 'source', 'ServicePrincipal')
    for x in app_creds:
        setattr(x, 'source', 'Application')
    return app_creds + sp_creds


def delete_service_principal_credential(cmd, identifier, key_id, cert=False):
    client = _graph_client_factory(cmd.cli_ctx)
    sp_object_id = _resolve_service_principal(client.service_principals, identifier)
    if cert:
        result = list(client.service_principals.list_key_credentials(sp_object_id))
    else:
        result = list(client.service_principals.list_password_credentials(sp_object_id))

    to_delete = next((x for x in result if x.key_id == key_id), None)

    # we will try to delete the creds at service principal level, if not found, we try application level

    if to_delete:
        result.remove(to_delete)
        if cert:
            return client.service_principals.update_key_credentials(sp_object_id, result)
        return client.service_principals.update_password_credentials(sp_object_id, result)
    else:
        app_object_id = _get_app_object_id_from_sp_object_id(client, sp_object_id)
        if app_object_id:
            if cert:
                result = list(client.applications.list_key_credentials(app_object_id))
            else:
                result = list(client.applications.list_password_credentials(app_object_id))
            to_delete = next((x for x in result if x.key_id == key_id), None)
            if to_delete:
                result.remove(to_delete)
                if cert:
                    return client.applications.update_key_credentials(app_object_id, result)
                return client.applications.update_password_credentials(app_object_id, result)

    raise CLIError("'{}' doesn't exist in the service principal of '{}' or associated application".format(
        key_id, identifier))


def _resolve_service_principal(client, identifier):
    # todo: confirm with graph team that a service principal name must be unique
    result = list(client.list(filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier)))
    if result:
        return result[0].object_id
    if _is_guid(identifier):
        return identifier  # assume an object id
    else:
        raise CLIError("service principal '{}' doesn't exist".format(identifier))


def _process_service_principal_creds(cli_ctx, years, app_start_date, app_end_date, cert, create_cert,
                                     password, keyvault):

    if not any((cert, create_cert, password, keyvault)):
        # 1 - Simplest scenario. Use random password
        return str(_gen_guid()), None, None, None, None

    if password:
        # 2 - Password supplied -- no certs
        return password, None, None, None, None

    # The rest of the scenarios involve certificates
    public_cert_string = None
    cert_file = None

    if cert and not keyvault:
        # 3 - User-supplied public cert data
        logger.debug("normalizing x509 certificate with fingerprint %s", cert.digest("sha1"))
        cert_start_date = dateutil.parser.parse(cert.get_notBefore().decode())
        cert_end_date = dateutil.parser.parse(cert.get_notAfter().decode())
        public_cert_string = _get_public(cert)
    elif create_cert and not keyvault:
        # 4 - Create local self-signed cert
        public_cert_string, cert_file, cert_start_date, cert_end_date = \
            _create_self_signed_cert(app_start_date, app_end_date)
    elif create_cert and keyvault:
        # 5 - Create self-signed cert in KeyVault
        public_cert_string, cert_file, cert_start_date, cert_end_date = \
            _create_self_signed_cert_with_keyvault(cli_ctx, years, keyvault, cert)
    elif keyvault:
        import base64
        # 6 - Use existing cert from KeyVault
        kv_client = _get_keyvault_client(cli_ctx)
        vault_base = 'https://{}{}/'.format(keyvault, cli_ctx.cloud.suffixes.keyvault_dns)
        cert_obj = kv_client.get_certificate(vault_base, cert, '')
        public_cert_string = base64.b64encode(cert_obj.cer).decode('utf-8')  # pylint: disable=no-member
        cert_start_date = cert_obj.attributes.not_before  # pylint: disable=no-member
        cert_end_date = cert_obj.attributes.expires  # pylint: disable=no-member

    return (password, public_cert_string, cert_file, cert_start_date, cert_end_date)


def _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date):

    if not cert_start_date and not cert_end_date:
        return app_start_date, app_end_date, None, None

    if cert_start_date > app_start_date:
        logger.warning('Certificate is not valid until %s. Adjusting SP start date to match.',
                       cert_start_date)
        app_start_date = cert_start_date + datetime.timedelta(seconds=1)

    if cert_end_date < app_end_date:
        logger.warning('Certificate expires %s. Adjusting SP end date to match.',
                       cert_end_date)
        app_end_date = cert_end_date - datetime.timedelta(seconds=1)

    return (app_start_date, app_end_date, cert_start_date, cert_end_date)


# pylint: disable=inconsistent-return-statements
def create_service_principal_for_rbac(
        # pylint:disable=too-many-statements,too-many-locals, too-many-branches
        cmd, name=None, password=None, years=None,
        create_cert=False, cert=None,
        scopes=None, role='Contributor',
        show_auth_for_sdk=None, skip_assignment=False, keyvault=None):
    import time

    graph_client = _graph_client_factory(cmd.cli_ctx)
    role_client = _auth_client_factory(cmd.cli_ctx).role_assignments
    scopes = scopes or ['/subscriptions/' + role_client.config.subscription_id]
    years = years or 1
    sp_oid = None
    _RETRY_TIMES = 36

    app_display_name = None
    if name and '://' not in name:
        app_display_name = name
        name = "http://" + name  # normalize be a valid graph service principal name

    if name:
        query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format(name)
        aad_sps = list(graph_client.service_principals.list(filter=query_exp))
        if aad_sps:
            raise CLIError("'{}' already exists.".format(name))

    app_start_date = datetime.datetime.now(TZ_UTC)
    app_end_date = app_start_date + relativedelta(years=years or 1)

    app_display_name = app_display_name or ('azure-cli-' +
                                            app_start_date.strftime('%Y-%m-%d-%H-%M-%S'))
    if name is None:
        name = 'http://' + app_display_name  # just a valid uri, no need to exist

    password, public_cert_string, cert_file, cert_start_date, cert_end_date = \
        _process_service_principal_creds(cmd.cli_ctx, years, app_start_date, app_end_date, cert, create_cert,
                                         password, keyvault)

    app_start_date, app_end_date, cert_start_date, cert_end_date = \
        _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date)

    aad_application = create_application(graph_client.applications,
                                         display_name=app_display_name,
                                         homepage='http://' + app_display_name,
                                         identifier_uris=[name],
                                         available_to_other_tenants=False,
                                         password=password,
                                         key_value=public_cert_string,
                                         start_date=app_start_date,
                                         end_date=app_end_date)
    # pylint: disable=no-member
    app_id = aad_application.app_id
    # retry till server replication is done
    for l in range(0, _RETRY_TIMES):
        try:
            aad_sp = _create_service_principal(cmd.cli_ctx, app_id, resolve_app=False)
            break
        except Exception as ex:  # pylint: disable=broad-except
            if l < _RETRY_TIMES and (
                    ' does not reference ' in str(ex) or ' does not exist ' in str(ex)):
                time.sleep(5)
                logger.warning('Retrying service principal creation: %s/%s', l + 1, _RETRY_TIMES)
            else:
                logger.warning(
                    "Creating service principal failed for appid '%s'. Trace followed:\n%s",
                    name, ex.response.headers if hasattr(ex,
                                                         'response') else ex)  # pylint: disable=no-member
                raise
    sp_oid = aad_sp.object_id

    # retry while server replication is done
    if not skip_assignment:
        for scope in scopes:
            for l in range(0, _RETRY_TIMES):
                try:
                    _create_role_assignment(cmd.cli_ctx, role, sp_oid, None, scope, resolve_assignee=False)
                    break
                except Exception as ex:
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

    if show_auth_for_sdk:
        from azure.cli.core._profile import Profile
        profile = Profile(cli_ctx=cmd.cli_ctx)
        result = profile.get_sp_auth_info(scopes[0].split('/')[2] if scopes else None,
                                          app_id, password, cert_file)
        # sdk-auth file should be in json format all the time, hence the print
        print(json.dumps(result, indent=2))
        return

    result = {
        'appId': app_id,
        'password': password,
        'name': name,
        'displayName': app_display_name,
        'tenant': graph_client.config.tenant_id
    }
    if cert_file:
        logger.warning(
            "Please copy %s to a safe place. When run 'az login' provide the file path to the --password argument",
            cert_file)
        result['fileWithCertAndPrivateKey'] = cert_file
    return result


def _get_keyvault_client(cli_ctx):
    from azure.cli.core._profile import Profile
    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

    def _get_token(server, resource, scope):  # pylint: disable=unused-argument
        return Profile(cli_ctx=cli_ctx).get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access

    return KeyVaultClient(KeyVaultAuthentication(_get_token))


def _create_self_signed_cert(start_date, end_date):  # pylint: disable=too-many-locals
    from os import path
    import tempfile
    from OpenSSL import crypto
    from datetime import timedelta

    _, cert_file = tempfile.mkstemp()
    _, key_file = tempfile.mkstemp()

    # create a file with both cert & key so users can use to login
    # leverage tempfile ot produce a random file name
    _, temp_file = tempfile.mkstemp()
    creds_file = path.join(path.expanduser("~"), path.basename(temp_file) + '.pem')

    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = crypto.X509()
    subject = cert.get_subject()
    # as long it works, we skip fileds C, ST, L, O, OU, which we have no reasonable defaults for
    subject.CN = 'CLI-Login'
    cert.set_serial_number(1000)
    asn1_format = '%Y%m%d%H%M%SZ'
    cert_start_date = start_date - timedelta(seconds=1)
    cert_end_date = end_date + timedelta(seconds=1)
    cert.set_notBefore(cert_start_date.strftime(asn1_format).encode('utf-8'))
    cert.set_notAfter(cert_end_date.strftime(asn1_format).encode('utf-8'))
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')

    with open(cert_file, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode())
    with open(key_file, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode())

    cert_string = None
    with open(creds_file, 'wt') as cf:
        with open(key_file, 'rt') as f:
            cf.write(f.read())
        with open(cert_file, "rt") as f:
            cert_string = f.read()
            cf.write(cert_string)

    # get rid of the header and tails for upload to AAD: ----BEGIN CERT....----
    cert_string = re.sub(r'\-+[A-z\s]+\-+', '', cert_string).strip()
    return (cert_string, creds_file, cert_start_date, cert_end_date)


def _create_self_signed_cert_with_keyvault(cli_ctx, years, keyvault, keyvault_cert_name):  # pylint: disable=too-many-locals
    import base64
    import time

    kv_client = _get_keyvault_client(cli_ctx)
    cert_policy = {
        'issuer_parameters': {
            'name': 'Self'
        },
        'key_properties': {
            'exportable': True,
            'key_size': 2048,
            'key_type': 'RSA',
            'reuse_key': True
        },
        'lifetime_actions': [{
            'action': {
                'action_type': 'AutoRenew'
            },
            'trigger': {
                'days_before_expiry': 90
            }
        }],
        'secret_properties': {
            'content_type': 'application/x-pkcs12'
        },
        'x509_certificate_properties': {
            'key_usage': [
                'cRLSign',
                'dataEncipherment',
                'digitalSignature',
                'keyEncipherment',
                'keyAgreement',
                'keyCertSign'
            ],
            'subject': 'CN=KeyVault Generated',
            'validity_in_months': ((years * 12) + 1)
        }
    }
    vault_base_url = 'https://{}{}/'.format(keyvault, cli_ctx.cloud.suffixes.keyvault_dns)
    kv_client.create_certificate(vault_base_url, keyvault_cert_name, cert_policy)
    while kv_client.get_certificate_operation(vault_base_url, keyvault_cert_name).status != 'completed':  # pylint: disable=no-member, line-too-long
        time.sleep(5)

    cert = kv_client.get_certificate(vault_base_url, keyvault_cert_name, '')
    cert_string = base64.b64encode(cert.cer).decode('utf-8')  # pylint: disable=no-member
    cert_start_date = cert.attributes.not_before  # pylint: disable=no-member
    cert_end_date = cert.attributes.expires  # pylint: disable=no-member
    creds_file = None
    return (cert_string, creds_file, cert_start_date, cert_end_date)


def _try_x509_pem(cert):
    import OpenSSL.crypto
    try:
        return OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    except OpenSSL.crypto.Error:
        # could not load the pem, try with headers
        try:
            pem_with_headers = '-----BEGIN CERTIFICATE-----\n' \
                               + cert + \
                               '-----END CERTIFICATE-----\n'
            return OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_with_headers)
        except OpenSSL.crypto.Error:
            return None
    except UnicodeEncodeError:
        # this must be a binary encoding
        return None


def _try_x509_der(cert):
    import OpenSSL.crypto
    import base64
    try:
        cert = base64.b64decode(cert)
        return OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)
    except OpenSSL.crypto.Error:
        return None


def _get_public(x509):
    import OpenSSL.crypto
    pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509)
    if isinstance(pem, bytes):
        pem = pem.decode("utf-8")
    stripped = pem.replace('-----BEGIN CERTIFICATE-----\n', '')
    stripped = stripped.replace('-----END CERTIFICATE-----\n', '')
    return stripped


def reset_service_principal_credential(cmd, name, password=None, create_cert=False,
                                       cert=None, years=None, keyvault=None, append=False):
    client = _graph_client_factory(cmd.cli_ctx)

    # pylint: disable=no-member

    years = years or 1

    # look for the existing application
    query_exp = "servicePrincipalNames/any(x:x eq \'{0}\') or displayName eq '{0}'".format(name)
    aad_sps = list(client.service_principals.list(filter=query_exp))
    if not aad_sps:
        raise CLIError("can't find a service principal matching '{}'".format(name))
    if len(aad_sps) > 1:
        raise CLIError(
            'more than one entry matches the name, please provide unique names like '
            'app id guid, or app id uri')
    app = show_application(client.applications, aad_sps[0].app_id)

    app_start_date = datetime.datetime.now(TZ_UTC)
    app_end_date = app_start_date + relativedelta(years=years or 1)

    # build a new password/cert credential and patch it
    public_cert_string = None
    cert_file = None

    password, public_cert_string, cert_file, cert_start_date, cert_end_date = \
        _process_service_principal_creds(cmd.cli_ctx, years, app_start_date, app_end_date, cert, create_cert,
                                         password, keyvault)

    app_start_date, app_end_date, cert_start_date, cert_end_date = \
        _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date)

    app_creds = None
    cert_creds = None

    if password:
        app_creds = []
        if append:
            app_creds = list(client.applications.list_password_credentials(app.object_id))
        app_creds.append(PasswordCredential(
            start_date=app_start_date,
            end_date=app_end_date,
            key_id=str(_gen_guid()),
            value=password
        ))

    if public_cert_string:
        cert_creds = []
        if append:
            cert_creds = list(client.applications.list_key_credentials(app.object_id))
        cert_creds.append(KeyCredential(
            start_date=app_start_date,
            end_date=app_end_date,
            value=public_cert_string,
            key_id=str(_gen_guid()),
            usage='Verify',
            type='AsymmetricX509Cert'
        ))

    app_create_param = ApplicationUpdateParameters(password_credentials=app_creds, key_credentials=cert_creds)

    client.applications.patch(app.object_id, app_create_param)

    result = {
        'appId': app.app_id,
        'password': password,
        'name': name,
        'tenant': client.config.tenant_id
    }
    if cert_file:
        result['fileWithCertAndPrivateKey'] = cert_file
    return result


def _resolve_object_id(cli_ctx, assignee, fallback_to_object_id=False):
    client = _graph_client_factory(cli_ctx)
    result = None
    try:
        if assignee.find('@') >= 0:  # looks like a user principal name
            result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
        if not result:
            result = list(client.service_principals.list(
                filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
        if not result:  # assume an object id, let us verify it
            result = _get_object_stubs(client, [assignee])

        # 2+ matches should never happen, so we only check 'no match' here
        if not result:
            raise CLIError("No matches in graph database for '{}'".format(assignee))

        return result[0].object_id
    except (CloudError, GraphErrorException):
        if fallback_to_object_id and _is_guid(assignee):
            return assignee
        raise


def _is_guid(guid):
    try:
        uuid.UUID(guid)
        return True
    except ValueError:
        pass
    return False


def _get_object_stubs(graph_client, assignees):
    from azure.graphrbac.models import GetObjectsParameters
    result = []
    assignees = list(assignees)  # callers could pass in a set
    for i in range(0, len(assignees), 1000):
        params = GetObjectsParameters(include_directory_object_references=True, object_ids=assignees[i:i + 1000])
        result += list(graph_client.objects.get_objects_by_object_ids(params))
    return result


# for injecting test seams to produce predicatable role assignment id for playback
def _gen_guid():
    return uuid.uuid4()

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import base64
import datetime
import itertools
import json
import os
import re
import uuid
from dateutil.relativedelta import relativedelta
import dateutil.parser

from msrest.serialization import TZ_UTC
from msrestazure.azure_exceptions import CloudError

from knack.log import get_logger
from knack.util import CLIError, todict

from azure.cli.core.profiles import ResourceType
from azure.graphrbac.models import GraphErrorException

from azure.cli.core.util import get_file_json, shell_safe_json_parse, is_guid

from azure.graphrbac.models import (ApplicationCreateParameters, ApplicationUpdateParameters, AppRole,
                                    PasswordCredential, KeyCredential, UserCreateParameters, PasswordProfile,
                                    ServicePrincipalCreateParameters, RequiredResourceAccess, ResourceAccess,
                                    GroupCreateParameters, CheckGroupMembershipParameters, UserUpdateParameters,
                                    OptionalClaim, OptionalClaims)

from ._client_factory import _auth_client_factory, _graph_client_factory
from ._multi_api_adaptor import MultiAPIAdaptor

CREDENTIAL_WARNING = (
    "The output includes credentials that you must protect. Be sure that you do not include these credentials in "
    "your code or check the credentials into your source control. For more information, see https://aka.ms/azadsp-cli")

logger = get_logger(__name__)

# pylint: disable=too-many-lines


def list_role_definitions(cmd, name=None, resource_group_name=None, scope=None,
                          custom_role_only=False):
    definitions_client = _auth_client_factory(cmd.cli_ctx, scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    return _search_role_definitions(cmd.cli_ctx, definitions_client, name, [scope], custom_role_only)


def create_role_definition(cmd, role_definition):
    return _create_update_role_definition(cmd, role_definition, for_update=False)


def update_role_definition(cmd, role_definition):
    return _create_update_role_definition(cmd, role_definition, for_update=True)


def _create_update_role_definition(cmd, role_definition, for_update):
    if os.path.exists(role_definition):
        role_definition = get_file_json(role_definition)
    else:
        role_definition = shell_safe_json_parse(role_definition)

    if not isinstance(role_definition, dict):
        raise CLIError('Invalid role definition. A valid dictionary JSON representation is expected.')
    # to workaround service defects, ensure property names are camel case
    # e.g. AssignableScopes -> assignableScopes
    names = [p for p in role_definition if p[:1].isupper()]
    for n in names:
        new_name = n[:1].lower() + n[1:]
        role_definition[new_name] = role_definition.pop(n)

    worker = MultiAPIAdaptor(cmd.cli_ctx)
    if for_update:  # for update, we need to use guid style unique name
        role_resource_id = role_definition.get('id')
        if not role_resource_id:
            logger.warning('Role "id" is missing. Look for the role in the current subscription...')
        definitions_client = _auth_client_factory(cmd.cli_ctx, scope=role_resource_id).role_definitions
        scopes_in_definition = role_definition.get('assignableScopes', None)
        scopes = (scopes_in_definition if scopes_in_definition else
                  ['/subscriptions/' + definitions_client.config.subscription_id])
        if role_resource_id:
            from msrestazure.tools import parse_resource_id
            role_id = parse_resource_id(role_resource_id)['name']
            role_name = role_definition['roleName']
        else:
            matched = _search_role_definitions(cmd.cli_ctx, definitions_client, role_definition['name'], scopes)
            if len(matched) > 1:
                raise CLIError('More than 2 definitions are found with the name of "{}"'.format(
                    role_definition['name']))
            if not matched:
                raise CLIError('No definition was found with the name of "{}"'.format(role_definition['name']))
            role_id = role_definition['name'] = matched[0].name
            role_name = worker.get_role_property(matched[0], 'role_name')
    else:  # for create
        definitions_client = _auth_client_factory(cmd.cli_ctx).role_definitions
        role_id = _gen_guid()
        role_name = role_definition.get('name', None)
        if not role_name:
            raise CLIError("please provide role name")

    if not for_update and not role_definition.get('assignableScopes', None):
        raise CLIError("please provide 'assignableScopes'")

    return worker.create_role_definition(definitions_client, role_name, role_id, role_definition)


def delete_role_definition(cmd, name, resource_group_name=None, scope=None,
                           custom_role_only=False):
    definitions_client = _auth_client_factory(cmd.cli_ctx, scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    roles = _search_role_definitions(cmd.cli_ctx, definitions_client, name, [scope], custom_role_only)
    for r in roles:
        definitions_client.delete(role_definition_id=r.name, scope=scope)


def _search_role_definitions(cli_ctx, definitions_client, name, scopes, custom_role_only=False):
    for scope in scopes:
        roles = list(definitions_client.list(scope))
        worker = MultiAPIAdaptor(cli_ctx)
        if name:
            roles = [r for r in roles if r.name == name or worker.get_role_property(r, 'role_name') == name]
        if custom_role_only:
            roles = [r for r in roles if worker.get_role_property(r, 'role_type') == 'CustomRole']
        if roles:
            return roles
    return []


def create_role_assignment(cmd, role, assignee=None, assignee_object_id=None, resource_group_name=None,
                           scope=None, assignee_principal_type=None, description=None,
                           condition=None, condition_version=None):
    """Check parameters are provided correctly, then call _create_role_assignment."""
    if bool(assignee) == bool(assignee_object_id):
        raise CLIError('usage error: --assignee STRING | --assignee-object-id GUID')

    if assignee_principal_type and not assignee_object_id:
        raise CLIError('usage error: --assignee-object-id GUID --assignee-principal-type TYPE')

    # If condition is set and condition-version is empty, condition-version defaults to "2.0".
    if condition and not condition_version:
        condition_version = "2.0"

    # If condition-version is set, condition must be set as well.
    if condition_version and not condition:
        raise CLIError('usage error: When --condition-version is set, --condition must be set as well.')

    if assignee:
        object_id, principal_type = _resolve_object_id_and_type(cmd.cli_ctx, assignee, fallback_to_object_id=True)
    else:
        object_id = assignee_object_id
        if assignee_principal_type:
            # If principal type is provided, nothing to resolve, do not call Graph
            principal_type = assignee_principal_type
        else:
            # Try best to get principal type
            logger.warning('RBAC service might reject creating role assignment without --assignee-principal-type '
                           'in the future. Better to specify --assignee-principal-type manually.')
            principal_type = _get_principal_type_from_object_id(cmd.cli_ctx, assignee_object_id)

    try:
        return _create_role_assignment(cmd.cli_ctx, role, object_id, resource_group_name, scope, resolve_assignee=False,
                                       assignee_principal_type=principal_type, description=description,
                                       condition=condition, condition_version=condition_version)
    except Exception as ex:  # pylint: disable=broad-except
        if _error_caused_by_role_assignment_exists(ex):  # for idempotent
            return list_role_assignments(cmd, assignee, role, resource_group_name, scope)[0]
        raise


def _create_role_assignment(cli_ctx, role, assignee, resource_group_name=None, scope=None,
                            resolve_assignee=True, assignee_principal_type=None, description=None,
                            condition=None, condition_version=None):
    """Prepare scope, role ID and resolve object ID from Graph API."""
    factory = _auth_client_factory(cli_ctx, scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(cli_ctx, assignee) if resolve_assignee else assignee
    worker = MultiAPIAdaptor(cli_ctx)
    return worker.create_role_assignment(assignments_client, _gen_guid(), role_id, object_id, scope,
                                         assignee_principal_type, description=description,
                                         condition=condition, condition_version=condition_version)


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
    worker = MultiAPIAdaptor(cmd.cli_ctx)
    role_dics = {i.id: worker.get_role_property(i, 'role_name') for i in role_defs}
    for i in results:
        if not i.get('roleDefinitionName'):
            if role_dics.get(worker.get_role_property(i, 'roleDefinitionId')):
                worker.set_role_property(i, 'roleDefinitionName',
                                         role_dics[worker.get_role_property(i, 'roleDefinitionId')])
            else:
                i['roleDefinitionName'] = None  # the role definition might have been deleted

    # fill in principal names
    principal_ids = set(worker.get_role_property(i, 'principalId')
                        for i in results if worker.get_role_property(i, 'principalId'))

    if principal_ids:
        try:
            principals = _get_object_stubs(graph_client, principal_ids)
            principal_dics = {i.object_id: _get_displayable_name(i) for i in principals}

            for i in [r for r in results if not r.get('principalName')]:
                i['principalName'] = ''
                if principal_dics.get(worker.get_role_property(i, 'principalId')):
                    worker.set_role_property(i, 'principalName',
                                             principal_dics[worker.get_role_property(i, 'principalId')])
        except (CloudError, GraphErrorException) as ex:
            # failure on resolving principal due to graph permission should not fail the whole thing
            logger.info("Failed to resolve graph object information per error '%s'", ex)

    for r in results:
        if not r.get('additionalProperties'):  # remove the useless "additionalProperties"
            r.pop('additionalProperties', None)
    return results


def update_role_assignment(cmd, role_assignment):
    # Try role_assignment as a file.
    if os.path.exists(role_assignment):
        role_assignment = get_file_json(role_assignment)
    else:
        role_assignment = shell_safe_json_parse(role_assignment)

    # Updating role assignment is only supported after 2020-04-01-preview, so we don't need to use MultiAPIAdaptor.
    from azure.cli.core.profiles import get_sdk

    RoleAssignment = get_sdk(cmd.cli_ctx, ResourceType.MGMT_AUTHORIZATION, 'RoleAssignment', mod='models',
                             operation_group='role_assignments')
    assignment = RoleAssignment.from_dict(role_assignment)
    scope = assignment.scope
    name = assignment.name

    auth_client = _auth_client_factory(cmd.cli_ctx, scope)
    assignments_client = auth_client.role_assignments

    # Get the existing assignment to do some checks.
    original_assignment = assignments_client.get(scope, name)

    # Forbid condition version downgrading.
    # This should be implemented on the service-side in the future.
    if (assignment.condition_version and original_assignment.condition_version and
            original_assignment.condition_version.startswith('2.') and assignment.condition_version.startswith('1.')):
        raise CLIError("Condition version cannot be downgraded to '1.X'.")

    if not assignment.principal_type:
        assignment.principal_type = original_assignment.principal_type

    return assignments_client.create(scope, name, parameters=assignment)


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
    start_events, end_events = {}, {}

    for item in activity_log:
        if item.operation_name.value.startswith('Microsoft.Authorization/roleAssignments'):
            if item.status.value == 'Started':
                start_events[item.operation_id] = item
            else:
                end_events[item.operation_id] = item
    return start_events, end_events


# A custom command around 'monitoring' events to produce understandable output for RBAC audit, a common scenario.
def list_role_assignment_change_logs(cmd, start_time=None, end_time=None):  # pylint: disable=too-many-branches
    # pylint: disable=too-many-nested-blocks, too-many-statements
    result = []
    worker = MultiAPIAdaptor(cmd.cli_ctx)
    start_events, end_events = _get_assignment_events(cmd.cli_ctx, start_time, end_time)

    # Use the resource `name` of roleDefinitions as keys, instead of `id`, because `id` can be inherited.
    #   name: b24988ac-6180-42a0-ab88-20f7382dd24c
    #   id: /subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c  # pylint: disable=line-too-long
    if start_events:
        # Only query Role Definitions and Graph when there are events returned
        role_defs = {d.name: worker.get_role_property(d, 'role_name') for d in list_role_definitions(cmd)}

        for op_id in start_events:
            e = end_events.get(op_id, None)
            if not e:
                continue

            entry = {}
            if e.status.value == 'Succeeded':
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
                        if payload.get('properties') is None:
                            continue
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

                        # Look up the resource `name`, like b24988ac-6180-42a0-ab88-20f7382dd24c
                        role_resource_name = payload['roleDefinitionId'].split('/')[-1]
                        entry['roleDefinitionId'] = role_resource_name
                        # In case the role definition has been deleted.
                        entry['roleName'] = role_defs.get(role_resource_name, "N/A")

                result.append(entry)

        # Fill in logical user/sp names as guid principal-id not readable
        principal_ids = {x['principalId'] for x in result if x['principalId']}
        if principal_ids:
            graph_client = _graph_client_factory(cmd.cli_ctx)
            stubs = _get_object_stubs(graph_client, principal_ids)
            principal_dics = {i.object_id: _get_displayable_name(i) for i in stubs}
            if principal_dics:
                for e in result:
                    e['principalName'] = principal_dics.get(e['principalId'], None)

    return result


def _backfill_assignments_for_co_admins(cli_ctx, auth_client, assignee=None):
    worker = MultiAPIAdaptor(cli_ctx)
    co_admins = auth_client.classic_administrators.list()  # known swagger bug on api-version handling
    co_admins = [x for x in co_admins if x.email_address]
    graph_client = _graph_client_factory(cli_ctx)
    if assignee:  # apply assignee filter if applicable
        if is_guid(assignee):
            try:
                result = _get_object_stubs(graph_client, [assignee])
                if not result:
                    return []
                assignee = _get_displayable_name(result[0]).lower()
            except ValueError:
                pass
        co_admins = [x for x in co_admins if assignee == x.email_address.lower()]

    if not co_admins:
        return []

    result, users = [], []
    for i in range(0, len(co_admins), 10):  # graph allows up to 10 query filters, so split into chunks here
        upn_queries = ["userPrincipalName eq '{}'".format(x.email_address)
                       for x in co_admins[i:i + 10]]
        temp = list(list_users(graph_client.users, query_filter=' or '.join(upn_queries)))
        users += temp
    upns = {u.user_principal_name: u.object_id for u in users}
    for admin in co_admins:
        na_text = 'NA(classic admins)'
        email = admin.email_address
        result.append({
            'id': na_text,
            'name': na_text,
        })
        properties = {
            'principalId': upns.get(email),
            'principalName': email,
            'roleDefinitionName': admin.role,
            'roleDefinitionId': 'NA(classic admin role)',
            'scope': '/subscriptions/' + auth_client.config.subscription_id
        }
        if worker.old_api:
            result[-1]['properties'] = properties
        else:
            result[-1].update(properties)
    return result


def _get_displayable_name(graph_object):
    if getattr(graph_object, 'user_principal_name', None):
        return graph_object.user_principal_name
    if getattr(graph_object, 'service_principal_names', None):
        return graph_object.service_principal_names[0]
    return graph_object.display_name or ''


def delete_role_assignments(cmd, ids=None, assignee=None, role=None, resource_group_name=None,
                            scope=None, include_inherited=False, yes=None):
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
    if not any([ids, assignee, role, resource_group_name, scope, assignee, yes]):
        from knack.prompting import prompt_y_n
        msg = 'This will delete all role assignments under the subscription. Are you sure?'
        if not prompt_y_n(msg, default="n"):
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

    # always use "scope" if provided, so we can get assignments beyond subscription e.g. management groups
    if scope:
        f = 'atScope()'
        if assignee_object_id and include_groups:
            f = f + " and assignedTo('{}')".format(assignee_object_id)
        assignments = list(assignments_client.list_for_scope(scope=scope, filter=f))
    elif assignee_object_id:
        if include_groups:
            f = "assignedTo('{}')".format(assignee_object_id)
        else:
            f = "principalId eq '{}'".format(assignee_object_id)
        assignments = list(assignments_client.list(filter=f))
    else:
        assignments = list(assignments_client.list())

    worker = MultiAPIAdaptor(cli_ctx)
    if assignments:
        assignments = [a for a in assignments if (
            not scope or
            include_inherited and re.match(worker.get_role_property(a, 'scope'), scope, re.I) or
            worker.get_role_property(a, 'scope').lower() == scope.lower()
        )]

        if role:
            role_id = _resolve_role_id(role, scope, definitions_client)
            assignments = [i for i in assignments if worker.get_role_property(i, 'role_definition_id') == role_id]

        # filter the assignee if "include_groups" is not provided because service side
        # does not accept filter "principalId eq and atScope()"
        if assignee_object_id and not include_groups:
            assignments = [i for i in assignments if worker.get_role_property(i, 'principal_id') == assignee_object_id]

    return assignments


def _build_role_scope(resource_group_name, scope, subscription_id):
    subscription_scope = '/subscriptions/' + subscription_id
    if scope:
        if resource_group_name:
            err = 'Resource group "{}" is redundant because scope is supplied'
            raise CLIError(err.format(resource_group_name))
        from azure.mgmt.core.tools import is_valid_resource_id
        if scope.startswith('/subscriptions/') and not is_valid_resource_id(scope):
            raise CLIError('Invalid scope. Please use --help to view the valid format.')
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
        if is_guid(role):
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


def list_apps(cmd, app_id=None, display_name=None, identifier_uri=None, query_filter=None, include_all=None,
              show_mine=None):
    client = _graph_client_factory(cmd.cli_ctx)
    if show_mine:
        return list_owned_objects(client.signed_in_user, 'application')
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if app_id:
        sub_filters.append("appId eq '{}'".format(app_id))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))
    if identifier_uri:
        sub_filters.append("identifierUris/any(s:s eq '{}')".format(identifier_uri))

    result = client.applications.list(filter=' and '.join(sub_filters) if sub_filters else None)
    if sub_filters or include_all:
        return list(result)

    result = list(itertools.islice(result, 101))
    if len(result) == 101:
        logger.warning("The result is not complete. You can still use '--all' to get all of them with"
                       " long latency expected, or provide a filter through command arguments")
    return result[:100]


def list_application_owners(cmd, identifier):
    client = _graph_client_factory(cmd.cli_ctx).applications
    return client.list_owners(_resolve_application(client, identifier))


def add_application_owner(cmd, owner_object_id, identifier):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    app_object_id = _resolve_application(graph_client.applications, identifier)
    owners = graph_client.applications.list_owners(app_object_id)
    if not next((x for x in owners if x.object_id == owner_object_id), None):
        owner_url = _get_owner_url(cmd.cli_ctx, owner_object_id)
        graph_client.applications.add_owner(app_object_id, owner_url)


def remove_application_owner(cmd, owner_object_id, identifier):
    client = _graph_client_factory(cmd.cli_ctx).applications
    return client.remove_owner(_resolve_application(client, identifier), owner_object_id)


def list_sps(cmd, spn=None, display_name=None, query_filter=None, show_mine=None, include_all=None):
    client = _graph_client_factory(cmd.cli_ctx)
    if show_mine:
        return list_owned_objects(client.signed_in_user, 'servicePrincipal')

    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if spn:
        sub_filters.append("servicePrincipalNames/any(c:c eq '{}')".format(spn))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    result = client.service_principals.list(filter=' and '.join(sub_filters) if sub_filters else None)

    if sub_filters or include_all:
        return result

    result = list(itertools.islice(result, 101))
    if len(result) == 101:
        logger.warning("The result is not complete. You can still use '--all' to get all of them with"
                       " long latency expected, or provide a filter through command arguments")
    return result[:100]


def list_owned_objects(client, object_type=None):
    result = client.list_owned_objects()
    if object_type:
        result = [r for r in result if r.object_type and r.object_type.lower() == object_type.lower()]
    return result


def list_users(client, upn=None, display_name=None, query_filter=None):
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if upn:
        sub_filters.append("userPrincipalName eq '{}'".format(upn))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    return client.list(filter=' and '.join(sub_filters) if sub_filters else None)


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


def update_user(client, upn_or_object_id, display_name=None, force_change_password_next_login=None, password=None,
                account_enabled=None, mail_nickname=None):
    password_profile = None
    if password is not None:
        password_profile = PasswordProfile(password=password,
                                           force_change_password_next_login=force_change_password_next_login)

    update_parameters = UserUpdateParameters(display_name=display_name, password_profile=password_profile,
                                             account_enabled=account_enabled, mail_nickname=mail_nickname)
    return client.update(upn_or_object_id=upn_or_object_id, parameters=update_parameters)


def get_user_member_groups(cmd, upn_or_object_id, security_enabled_only=False):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    if not is_guid(upn_or_object_id):
        upn_or_object_id = graph_client.users.get(upn_or_object_id).object_id

    results = list(graph_client.users.get_member_groups(
        upn_or_object_id, security_enabled_only=security_enabled_only))
    try:
        stubs = _get_object_stubs(graph_client, results)
    except GraphErrorException:
        stubs = []
    stubs = {s.object_id: s.display_name for s in stubs}
    return [{'objectId': x, 'displayName': stubs.get(x)} for x in results]


def create_group(cmd, display_name, mail_nickname, force=None, description=None):
    graph_client = _graph_client_factory(cmd.cli_ctx)

    # workaround to ensure idempotent even AAD graph service doesn't support it
    if not force:
        matches = list(graph_client.groups.list(filter="displayName eq '{}' and mailNickname eq '{}'".format(
            display_name, mail_nickname)))
        if matches:
            if len(matches) > 1:
                err = ('There is more than one group with the same display and nick names: "{}". '
                       'Please delete them first.')
                raise CLIError(err.format(', '.join([x.object_id for x in matches])))
            logger.warning('A group with the same display name and mail nickname already exists, returning.')
            return matches[0]
        group_create_parameters = GroupCreateParameters(display_name=display_name, mail_nickname=mail_nickname)
        if description is not None:
            group_create_parameters.additional_properties = {'description': description}
    group = graph_client.groups.create(group_create_parameters)

    return group


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
    return client.list(filter=' and '.join(sub_filters) if sub_filters else None)


def list_group_owners(cmd, group_id):
    client = _graph_client_factory(cmd.cli_ctx).groups
    return client.list_owners(_resolve_group(client, group_id))


def add_group_owner(cmd, owner_object_id, group_id):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    group_object_id = _resolve_group(graph_client.groups, group_id)
    owners = graph_client.groups.list_owners(group_object_id)
    if not next((x for x in owners if x.object_id == owner_object_id), None):
        owner_url = _get_owner_url(cmd.cli_ctx, owner_object_id)
        graph_client.groups.add_owner(group_object_id, owner_url)


def remove_group_owner(cmd, owner_object_id, group_id):
    client = _graph_client_factory(cmd.cli_ctx).groups
    return client.remove_owner(_resolve_group(client, group_id), owner_object_id)


def _resolve_group(client, identifier):
    if not is_guid(identifier):
        res = list(list_groups(client, display_name=identifier))
        if not res:
            raise CLIError('Group {} is not found in Graph '.format(identifier))
        if len(res) != 1:
            raise CLIError('More than 1 group objects has the display name of ' + identifier)
        identifier = res[0].object_id
    return identifier


def create_application(cmd, display_name, homepage=None, identifier_uris=None,  # pylint: disable=too-many-locals
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       key_value=None, key_type=None, key_usage=None, start_date=None, end_date=None,
                       oauth2_allow_implicit_flow=None, required_resource_accesses=None, native_app=None,
                       credential_description=None, app_roles=None, optional_claims=None):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    key_creds, password_creds, required_accesses = None, None, None
    existing_apps = list_apps(cmd, display_name=display_name)
    if existing_apps:
        if identifier_uris:
            existing_apps = [x for x in existing_apps if set(identifier_uris).issubset(set(x.identifier_uris))]
        existing_apps = [x for x in existing_apps if x.display_name == display_name]
        if native_app:
            existing_apps = [x for x in existing_apps if x.public_client]
        if len(existing_apps) > 1:
            raise CLIError('More than one application have the same display name "{}", please remove '
                           'them first'.format(', '.join([x.object_id for x in existing_apps])))
        if len(existing_apps) == 1:
            logger.warning('Found an existing application instance of "%s". We will patch it', existing_apps[0].app_id)
            param = update_application(existing_apps[0], display_name=display_name, homepage=homepage,
                                       identifier_uris=identifier_uris, password=password, reply_urls=reply_urls,
                                       key_value=key_value, key_type=key_type, key_usage=key_usage,
                                       start_date=start_date, end_date=end_date,
                                       available_to_other_tenants=available_to_other_tenants,
                                       oauth2_allow_implicit_flow=oauth2_allow_implicit_flow,
                                       required_resource_accesses=required_resource_accesses,
                                       credential_description=credential_description, app_roles=app_roles)
            patch_application(cmd, existing_apps[0].app_id, param)
            return show_application(graph_client.applications, existing_apps[0].app_id)
    if not identifier_uris:
        identifier_uris = []
    if native_app:
        if identifier_uris:
            raise CLIError("'--identifier-uris' is not required for creating a native application")
    else:
        password_creds, key_creds = _build_application_creds(password, key_value, key_type, key_usage,
                                                             start_date, end_date, credential_description)

    if required_resource_accesses:
        required_accesses = _build_application_accesses(required_resource_accesses)

    if app_roles:
        app_roles = _build_app_roles(app_roles)
    if optional_claims:
        optional_claims = _build_optional_claims(optional_claims)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants=available_to_other_tenants,
                                                   display_name=display_name,
                                                   identifier_uris=identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   key_credentials=key_creds,
                                                   password_credentials=password_creds,
                                                   oauth2_allow_implicit_flow=oauth2_allow_implicit_flow,
                                                   required_resource_access=required_accesses,
                                                   app_roles=app_roles,
                                                   optional_claims=optional_claims)

    try:
        result = graph_client.applications.create(app_create_param)
    except GraphErrorException as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise

    if native_app:
        # AAD graph doesn't have the API to create a native app, aka public client, the recommended hack is
        # to create a web app first, then convert to a native one
        # pylint: disable=protected-access
        app_patch_param = ApplicationUpdateParameters(public_client=True)
        graph_client.applications.patch(result.object_id, app_patch_param)
        result = graph_client.applications.get(result.object_id)

    return result


def _get_grant_permissions(graph_client, client_sp_object_id=None, query_filter=None):
    query_filter = query_filter or ("clientId eq '{}'".format(client_sp_object_id) if client_sp_object_id else None)
    grant_info = graph_client.oauth2_permission_grant.list(filter=query_filter)
    try:
        # Make the REST request immediately so that errors can be raised and handled.
        return list(grant_info)
    except CloudError as ex:
        if ex.status_code == 404:
            raise CLIError("Service principal with appId or objectId '{id}' doesn't exist. "
                           "If '{id}' is an appId, make sure an associated service principal is created "
                           "for the app. To create one, run `az ad sp create --id {id}`."
                           .format(id=client_sp_object_id))
        raise


def list_permissions(cmd, identifier):
    # the important and hard part is to tell users which permissions have been granted.
    # we will due diligence to dig out what matters

    graph_client = _graph_client_factory(cmd.cli_ctx)

    # first get the permission grant history
    client_sp_object_id = _resolve_service_principal(graph_client.service_principals, identifier)

    # get original permissions required by the application, we will cross check the history
    # and mark out granted ones
    graph_client = _graph_client_factory(cmd.cli_ctx)
    application = show_application(graph_client.applications, identifier)
    permissions = application.required_resource_access
    if permissions:
        grant_permissions = _get_grant_permissions(graph_client, client_sp_object_id=client_sp_object_id)
    for p in permissions:
        result = list(graph_client.service_principals.list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(p.resource_app_id)))
        expiry_time = 'N/A'
        if result:
            expiry_time = ', '.join([x.expiry_time for x in grant_permissions if
                                     x.resource_id == result[0].object_id])
        setattr(p, 'expiryTime', expiry_time)
    return permissions


def list_permission_grants(cmd, identifier=None, query_filter=None, show_resource_name=None):
    if identifier and query_filter:
        raise CLIError('Please only use one of "--identifier" and "--filter", not both')
    graph_client = _graph_client_factory(cmd.cli_ctx)
    client_sp_object_id = None
    if identifier:
        client_sp_object_id = _resolve_service_principal(graph_client.service_principals, identifier)
    result = _get_grant_permissions(graph_client, client_sp_object_id=client_sp_object_id, query_filter=query_filter)
    result = list(result)
    if show_resource_name:
        for r in result:
            sp = graph_client.service_principals.get(r.resource_id)
            setattr(r, 'resource_display_name', sp.display_name)
    return result


def add_permission(cmd, identifier, api, api_permissions):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    application = show_application(graph_client.applications, identifier)
    existing = application.required_resource_access
    resource_accesses = []
    for e in api_permissions:
        access_id, access_type = e.split('=')
        resource_accesses.append(ResourceAccess(id=access_id, type=access_type))

    existing_resource_access = next((e for e in existing if e.resource_app_id == api), None)
    if existing_resource_access:
        existing_resource_access.resource_access += resource_accesses
    else:
        required_resource_access = RequiredResourceAccess(resource_app_id=api,
                                                          resource_access=resource_accesses)
        existing.append(required_resource_access)
    update_parameter = ApplicationUpdateParameters(required_resource_access=existing)
    graph_client.applications.patch(application.object_id, update_parameter)
    logger.warning('Invoking "az ad app permission grant --id %s --api %s" is needed to make the '
                   'change effective', identifier, api)


def delete_permission(cmd, identifier, api, api_permissions=None):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    application = show_application(graph_client.applications, identifier)
    required_resource_access = application.required_resource_access
    # required_resource_access (list of RequiredResourceAccess)
    #   RequiredResourceAccess
    #     resource_app_id   <- api
    #     resource_access   (list of ResourceAccess)
    #       ResourceAccess
    #         id            <- api_permissions
    #         type

    # Get the RequiredResourceAccess object whose resource_app_id == api
    rra = next((a for a in required_resource_access if a.resource_app_id == api), None)

    if not rra:
        # Silently pass if the api is not required.
        logger.warning("App %s doesn't require access to API %s.", identifier, api)
        return None

    if api_permissions:
        # Check if the user tries to delete any ResourceAccess that is not required.
        ra_ids = [ra.id for ra in rra.resource_access]
        non_existing_ra_ids = [p for p in api_permissions if p not in ra_ids]
        if non_existing_ra_ids:
            logger.warning("App %s doesn't require access to API %s's permission %s.",
                           identifier, api, ', '.join(non_existing_ra_ids))
            if len(non_existing_ra_ids) == len(api_permissions):
                # Skip the REST call if nothing to remove
                return None

        # Remove specified ResourceAccess under RequiredResourceAccess.resource_access
        rra.resource_access = [a for a in rra.resource_access if a.id not in api_permissions]
        # Remove the RequiredResourceAccess if its resource_access is empty
        if not rra.resource_access:
            required_resource_access.remove(rra)
    else:
        # Remove the whole RequiredResourceAccess
        required_resource_access.remove(rra)

    update_parameter = ApplicationUpdateParameters(required_resource_access=required_resource_access)
    return graph_client.applications.patch(application.object_id, update_parameter)


def admin_consent(cmd, identifier):
    from azure.cli.core.cloud import AZURE_PUBLIC_CLOUD
    from azure.cli.core.util import send_raw_request

    if cmd.cli_ctx.cloud.name != AZURE_PUBLIC_CLOUD.name:
        raise CLIError('This command is not yet supported on sovereign clouds')

    graph_client = _graph_client_factory(cmd.cli_ctx)
    application = show_application(graph_client.applications, identifier)
    url = 'https://main.iam.ad.ext.azure.com/api/RegisteredApplications/{}/Consent?onBehalfOfAll=true'.format(
        application.app_id)
    send_raw_request(cmd.cli_ctx, 'post', url, resource='74658136-14ec-4630-ad9b-26e160ff0fc6')


def grant_application(cmd, identifier, api, consent_type=None, principal_id=None,
                      expires='1', scope='user_impersonation'):
    graph_client = _graph_client_factory(cmd.cli_ctx)

    # Get the Service Principal ObjectId for the client app
    client_sp_object_id = _resolve_service_principal(graph_client.service_principals, identifier)

    # Get the Service Principal ObjectId for associated app
    associated_sp_object_id = _resolve_service_principal(graph_client.service_principals, api)

    # ensure to remove the older grant
    grant_permissions = _get_grant_permissions(graph_client, client_sp_object_id=client_sp_object_id)
    to_delete = [p.object_id for p in grant_permissions if p.client_id == client_sp_object_id and
                 p.resource_id == associated_sp_object_id]
    for p in to_delete:
        graph_client.oauth2_permission_grant.delete(p)

    # Build payload
    start_date = datetime.datetime.utcnow()
    end_date = start_date + relativedelta(years=1)

    if expires.lower() == 'never':
        end_date = start_date + relativedelta(years=1000)
    else:
        try:
            end_date = start_date + relativedelta(years=int(expires))
        except ValueError:
            raise CLIError('usage error: --expires <INT>|never')

    payload = {
        "odata.type": "Microsoft.DirectoryServices.OAuth2PermissionGrant",
        "clientId": client_sp_object_id,
        "consentType": consent_type,
        "resourceId": associated_sp_object_id,
        "scope": scope,
        'principalId': principal_id,
        "startTime": start_date.isoformat(),
        "expiryTime": end_date.isoformat()
    }

    # Grant OAuth2 permissions
    return graph_client.oauth2_permission_grant.create(payload)  # pylint: disable=no-member


def update_application(instance, display_name=None, homepage=None,  # pylint: disable=unused-argument
                       identifier_uris=None, password=None, reply_urls=None, key_value=None,
                       key_type=None, key_usage=None, start_date=None, end_date=None, available_to_other_tenants=None,
                       oauth2_allow_implicit_flow=None, required_resource_accesses=None,
                       credential_description=None, app_roles=None, optional_claims=None):

    # propagate the values
    app_patch_param = ApplicationUpdateParameters()
    properties = [attr for attr in dir(instance)
                  if not callable(getattr(instance, attr)) and
                  not attr.startswith("_") and attr != 'additional_properties' and hasattr(app_patch_param, attr)]
    for p in properties:
        setattr(app_patch_param, p, getattr(instance, p))

    # handle credentials. Note, we will not put existing ones on the wire to avoid roundtrip problems caused
    # by time precision difference between SDK and Graph Services
    password_creds, key_creds = None, None
    if any([password, key_value]):
        password_creds, key_creds = _build_application_creds(password, key_value, key_type, key_usage, start_date,
                                                             end_date, credential_description)
    app_patch_param.key_credentials = key_creds
    app_patch_param.password_credentials = password_creds

    if required_resource_accesses:
        app_patch_param.required_resource_access = _build_application_accesses(required_resource_accesses)

    if app_roles:
        app_patch_param.app_roles = _build_app_roles(app_roles)

    if optional_claims:
        app_patch_param.optional_claims = _build_optional_claims(optional_claims)

    if available_to_other_tenants is not None:
        app_patch_param.available_to_other_tenants = available_to_other_tenants
    if oauth2_allow_implicit_flow is not None:
        app_patch_param.oauth2_allow_implicit_flow = oauth2_allow_implicit_flow
    if identifier_uris is not None:
        app_patch_param.identifier_uris = identifier_uris
    if display_name is not None:
        app_patch_param.display_name = display_name
    if reply_urls is not None:
        app_patch_param.reply_urls = reply_urls
    if homepage is not None:
        app_patch_param.homepage = homepage

    return app_patch_param


def patch_application(cmd, identifier, parameters):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    object_id = _resolve_application(graph_client.applications, identifier)
    return graph_client.applications.patch(object_id, parameters)


def patch_service_principal(cmd, identifier, parameters):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    object_id = _resolve_service_principal(graph_client.service_principals, identifier)
    return graph_client.service_principals.update(object_id, parameters)


def _build_application_accesses(required_resource_accesses):
    if not required_resource_accesses:
        return None
    required_accesses = []
    if isinstance(required_resource_accesses, dict):
        logger.info('Getting "requiredResourceAccess" from a full manifest')
        required_resource_accesses = required_resource_accesses.get('requiredResourceAccess', [])
    for x in required_resource_accesses:
        accesses = [ResourceAccess(id=y['id'], type=y['type']) for y in x['resourceAccess']]
        required_accesses.append(RequiredResourceAccess(resource_app_id=x['resourceAppId'],
                                                        resource_access=accesses))
    return required_accesses


def _build_app_roles(app_roles):
    if not app_roles:
        return None
    result = []
    if isinstance(app_roles, dict):
        logger.info('Getting "appRoles" from a full manifest')
        app_roles = app_roles.get('appRoles', [])
    for x in app_roles:
        role = AppRole(id=x.get('id', None) or _gen_guid(), allowed_member_types=x.get('allowedMemberTypes', None),
                       description=x.get('description', None), display_name=x.get('displayName', None),
                       is_enabled=x.get('isEnabled', None), value=x.get('value', None))
        result.append(role)
    return result


def _build_optional_claims(optional_claims):
    if not optional_claims:
        return None
    available_keys = {
        'idToken': 'id_token',
        'accessToken': 'access_token'
    }
    result = OptionalClaims()
    for key, object_key in available_keys.items():
        if optional_claims.get(key, []):
            tokens = []
            for token in optional_claims.get(key):
                tokens.append(OptionalClaim(
                    name=token.get('name', None),
                    source=token.get('source', None),
                    essential=token.get('essential', None),
                    additional_properties=token.get('additionalProperties', None)
                ))
            if tokens:
                setattr(result, object_key, tokens)
    return result


def show_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    return client.get(object_id)


def delete_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    client.delete(object_id)


def _resolve_application(client, identifier):
    result = list(client.list(filter="identifierUris/any(s:s eq '{}')".format(identifier)))
    if not result:
        if is_guid(identifier):
            # it is either app id or object id, let us verify
            result = list(client.list(filter="appId eq '{}'".format(identifier)))
        else:
            error = CLIError("Application '{}' doesn't exist".format(identifier))
            error.status_code = 404  # Make sure CLI returns 3
            raise error

    return result[0].object_id if result else identifier


def _build_application_creds(password=None, key_value=None, key_type=None, key_usage=None,
                             start_date=None, end_date=None, key_description=None):
    if password and key_value:
        raise CLIError('specify either --password or --key-value, but not both.')

    if not start_date:
        start_date = datetime.datetime.utcnow()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + relativedelta(years=1) - relativedelta(hours=24)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)

    custom_key_id = None
    if key_description and password:
        custom_key_id = _encode_custom_key_description(key_description)

    key_type = key_type or 'AsymmetricX509Cert'
    key_usage = key_usage or 'Verify'

    password_creds = None
    key_creds = None
    if password:
        password_creds = [PasswordCredential(start_date=start_date, end_date=end_date, key_id=str(_gen_guid()),
                                             value=password, custom_key_identifier=custom_key_id)]
    elif key_value:
        key_creds = [KeyCredential(start_date=start_date, end_date=end_date, key_id=str(_gen_guid()), value=key_value,
                                   usage=key_usage, type=key_type, custom_key_identifier=custom_key_id)]

    return (password_creds, key_creds)


def create_service_principal(cmd, identifier):
    return _create_service_principal(cmd.cli_ctx, identifier)


def _create_service_principal(cli_ctx, identifier, resolve_app=True):
    client = _graph_client_factory(cli_ctx)
    app_id = identifier
    if resolve_app:
        if is_guid(identifier):
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

    return client.service_principals.create(ServicePrincipalCreateParameters(app_id=app_id, account_enabled=True))


def show_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    return client.get(object_id)


def delete_service_principal(cmd, identifier):
    from azure.cli.core._profile import Profile
    client = _graph_client_factory(cmd.cli_ctx)
    sp_object_id = _resolve_service_principal(client.service_principals, identifier)

    app_object_id = None
    try:
        app_object_id = _get_app_object_id_from_sp_object_id(client, sp_object_id)
    except CLIError as ex:
        logger.info("%s. Skip application deletion.", ex)

    profile = Profile()
    if not profile.is_tenant_level_account():
        assignments = list_role_assignments(cmd, assignee=identifier, show_all=True)
        if assignments:
            logger.warning('Removing role assignments')
            delete_role_assignments(cmd, [a['id'] for a in assignments])

    if app_object_id:  # delete the application, and AAD service will automatically clean up the SP
        logger.info("Deleting associated application %s", app_object_id)
        client.applications.delete(app_object_id)
    else:
        client.service_principals.delete(sp_object_id)


def _get_app_object_id_from_sp_object_id(client, sp_object_id):
    sp = client.service_principals.get(sp_object_id)
    result = list(client.applications.list(filter="appId eq '{}'".format(sp.app_id)))

    if result:
        return result[0].object_id
    raise CLIError("Can't find associated application id from '{}'".format(sp_object_id))


def list_service_principal_owners(cmd, identifier):
    client = _graph_client_factory(cmd.cli_ctx)
    sp_object_id = _resolve_service_principal(client.service_principals, identifier)
    return client.service_principals.list_owners(sp_object_id)


def list_service_principal_credentials(cmd, identifier, cert=False):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    if " sp " in cmd.name:
        sp_object_id = _resolve_service_principal(graph_client.service_principals, identifier)
        app_object_id = _get_app_object_id_from_sp_object_id(graph_client, sp_object_id)
    else:
        app_object_id = _resolve_application(graph_client.applications, identifier)
    return _get_service_principal_credentials(graph_client, app_object_id, cert)


def _get_service_principal_credentials(graph_client, app_object_id, cert=False):
    if cert:
        app_creds = list(graph_client.applications.list_key_credentials(app_object_id))
    else:
        app_creds = list(graph_client.applications.list_password_credentials(app_object_id))

    return app_creds


def delete_service_principal_credential(cmd, identifier, key_id, cert=False):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    if " sp " in cmd.name:
        sp_object_id = _resolve_service_principal(graph_client.service_principals, identifier)
        app_object_id = _get_app_object_id_from_sp_object_id(graph_client, sp_object_id)
    else:
        app_object_id = _resolve_application(graph_client.applications, identifier)
    result = _get_service_principal_credentials(graph_client, app_object_id, cert)

    to_delete = next((x for x in result if x.key_id == key_id), None)
    if to_delete:
        result.remove(to_delete)
        if cert:
            return graph_client.applications.update_key_credentials(app_object_id, result)
        return graph_client.applications.update_password_credentials(app_object_id, result)

    raise CLIError("'{}' doesn't exist in the service principal of '{}' or associated application".format(
        key_id, identifier))


def _resolve_service_principal(client, identifier):
    # todo: confirm with graph team that a service principal name must be unique
    result = list(client.list(filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier)))
    if result:
        return result[0].object_id
    if is_guid(identifier):
        return identifier  # assume an object id
    error = CLIError("Service principal '{}' doesn't exist".format(identifier))
    error.status_code = 404  # Make sure CLI returns 3
    raise error


def _process_service_principal_creds(cli_ctx, years, app_start_date, app_end_date, cert, create_cert,
                                     password, keyvault):

    if not any((cert, create_cert, password, keyvault)):
        # 1 - Simplest scenario. Use random password
        return _random_password(34), None, None, None, None

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
        # 6 - Use existing cert from KeyVault
        kv_client = _get_keyvault_client(cli_ctx)
        vault_base = 'https://{}{}/'.format(keyvault, cli_ctx.cloud.suffixes.keyvault_dns)
        cert_obj = kv_client.get_certificate(vault_base, cert, '')
        public_cert_string = base64.b64encode(cert_obj.cer).decode('utf-8')  # pylint: disable=no-member
        cert_start_date = cert_obj.attributes.not_before  # pylint: disable=no-member
        cert_end_date = cert_obj.attributes.expires  # pylint: disable=no-member

    return (password, public_cert_string, cert_file, cert_start_date, cert_end_date)


def _error_caused_by_role_assignment_exists(ex):
    return getattr(ex, 'status_code', None) == 409 and 'role assignment already exists' in ex.message


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
        # pylint:disable=too-many-statements,too-many-locals, too-many-branches, unused-argument
        cmd, name=None, years=None, create_cert=False, cert=None, scopes=None, role=None,
        show_auth_for_sdk=None, skip_assignment=False, keyvault=None):
    import time

    if role and not scopes or not role and scopes:
        from azure.cli.core.azclierror import ArgumentUsageError
        raise ArgumentUsageError("Usage error: To create role assignments, specify both --role and --scopes.")

    graph_client = _graph_client_factory(cmd.cli_ctx)

    years = years or 1
    _RETRY_TIMES = 36
    existing_sps = None

    if not name:
        # No name is provided, create a new one
        app_display_name = 'azure-cli-' + datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
    else:
        app_display_name = name
        # patch existing app with the same displayName to make the command idempotent
        query_exp = "displayName eq '{}'".format(name)
        existing_sps = list(graph_client.service_principals.list(filter=query_exp))

    app_start_date = datetime.datetime.now(TZ_UTC)
    app_end_date = app_start_date + relativedelta(years=years or 1)

    password, public_cert_string, cert_file, cert_start_date, cert_end_date = \
        _process_service_principal_creds(cmd.cli_ctx, years, app_start_date, app_end_date, cert, create_cert,
                                         None, keyvault)

    app_start_date, app_end_date, cert_start_date, cert_end_date = \
        _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date)

    aad_application = create_application(cmd,
                                         display_name=app_display_name,
                                         available_to_other_tenants=False,
                                         password=password,
                                         key_value=public_cert_string,
                                         start_date=app_start_date,
                                         end_date=app_end_date,
                                         credential_description='rbac')
    # pylint: disable=no-member
    app_id = aad_application.app_id

    # retry till server replication is done
    aad_sp = existing_sps[0] if existing_sps else None
    if not aad_sp:
        for retry_time in range(0, _RETRY_TIMES):
            try:
                aad_sp = _create_service_principal(cmd.cli_ctx, app_id, resolve_app=False)
                break
            except Exception as ex:  # pylint: disable=broad-except
                err_msg = str(ex)
                if retry_time < _RETRY_TIMES and (
                        ' does not reference ' in err_msg or
                        ' does not exist ' in err_msg or
                        'service principal being created must in the local tenant' in err_msg):
                    logger.warning("Creating service principal failed with error '%s'. Retrying: %s/%s",
                                   err_msg, retry_time + 1, _RETRY_TIMES)
                    time.sleep(5)
                else:
                    logger.warning(
                        "Creating service principal failed for '%s'. Trace followed:\n%s",
                        app_id, ex.response.headers
                        if hasattr(ex, 'response') else ex)  # pylint: disable=no-member
                    raise
    sp_oid = aad_sp.object_id

    if role:
        for scope in scopes:
            logger.warning("Creating '%s' role assignment under scope '%s'", role, scope)
            # retry till server replication is done
            for retry_time in range(0, _RETRY_TIMES):
                try:
                    _create_role_assignment(cmd.cli_ctx, role, sp_oid, None, scope, resolve_assignee=False,
                                            assignee_principal_type='ServicePrincipal')
                    break
                except Exception as ex:
                    if retry_time < _RETRY_TIMES and ' does not exist in the directory ' in str(ex):
                        time.sleep(5)
                        logger.warning('  Retrying role assignment creation: %s/%s', retry_time + 1,
                                       _RETRY_TIMES)
                        continue
                    if _error_caused_by_role_assignment_exists(ex):
                        logger.warning('  Role assignment already exists.\n')
                        break

                    # dump out history for diagnoses
                    logger.warning('  Role assignment creation failed.\n')
                    if getattr(ex, 'response', None) is not None:
                        logger.warning('  role assignment response headers: %s\n',
                                       ex.response.headers)  # pylint: disable=no-member
                    raise

    logger.warning(CREDENTIAL_WARNING)

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
        'displayName': app_display_name,
        'tenant': graph_client.config.tenant_id
    }
    if cert_file:
        logger.warning(
            "Please copy %s to a safe place. When you run 'az login', provide the file path in the --password argument",
            cert_file)
        result['fileWithCertAndPrivateKey'] = cert_file
    return result


def _get_signed_in_user_object_id(graph_client):
    try:
        return graph_client.signed_in_user.get().object_id
    except GraphErrorException:  # error could be possible if you logged in as a service principal
        pass


def _get_keyvault_client(cli_ctx):
    from azure.cli.command_modules.keyvault._client_factory import keyvault_data_plane_factory
    return keyvault_data_plane_factory(cli_ctx)


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
    os.chmod(creds_file, 0o600)  # make the file readable/writable only for current user

    # get rid of the header and tails for upload to AAD: ----BEGIN CERT....----
    cert_string = re.sub(r'\-+[A-z\s]+\-+', '', cert_string).strip()
    return (cert_string, creds_file, cert_start_date, cert_end_date)


def _create_self_signed_cert_with_keyvault(cli_ctx, years, keyvault, keyvault_cert_name):  # pylint: disable=too-many-locals
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
            'validity_in_months': int(years * 12)
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


def reset_service_principal_credential(cmd, name, password=None, create_cert=False, cert=None, years=None,
                                       end_date=None, keyvault=None, append=False, credential_description=None):
    client = _graph_client_factory(cmd.cli_ctx)

    # pylint: disable=no-member
    app_start_date = datetime.datetime.now(TZ_UTC)
    if years is not None and end_date is not None:
        raise CLIError('usage error: --years | --end-date')
    if end_date is None:
        years = years or 1
        app_end_date = app_start_date + relativedelta(years=years)
    else:
        app_end_date = dateutil.parser.parse(end_date)
        if app_end_date.tzinfo is None:
            app_end_date = app_end_date.replace(tzinfo=TZ_UTC)
        years = (app_end_date - app_start_date).days / 365

    # look for the existing application
    query_exp = "servicePrincipalNames/any(x:x eq \'{0}\') or displayName eq '{0}'".format(name)
    aad_sps = list(client.service_principals.list(filter=query_exp))

    if len(aad_sps) > 1:
        raise CLIError(
            'more than one entry matches the name, please provide unique names like '
            'app id guid, or app id uri')
    app = (show_application(client.applications, aad_sps[0].app_id) if aad_sps else
           show_application(client.applications, name))  # possible there is no SP created for the app

    if not app:
        raise CLIError("can't find an application matching '{}'".format(name))

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

    custom_key_identifier = None
    if credential_description and password:
        custom_key_identifier = _encode_custom_key_description(credential_description)

    if password:
        app_creds = []
        if append:
            app_creds = list(client.applications.list_password_credentials(app.object_id))
        app_creds.append(PasswordCredential(
            start_date=app_start_date,
            end_date=app_end_date,
            key_id=str(_gen_guid()),
            value=password,
            custom_key_identifier=custom_key_identifier
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
            type='AsymmetricX509Cert',
            custom_key_identifier=custom_key_identifier
        ))

    app_patch_param = ApplicationUpdateParameters(password_credentials=app_creds, key_credentials=cert_creds)

    client.applications.patch(app.object_id, app_patch_param)

    result = {
        'appId': app.app_id,
        'password': password,
        'name': name,
        'tenant': client.config.tenant_id
    }
    if cert_file:
        result['fileWithCertAndPrivateKey'] = cert_file

    logger.warning(CREDENTIAL_WARNING)
    return result


def _encode_custom_key_description(key_description):
    # utf16 is used by AAD portal. Do not change it to other random encoding
    # unless you know what you are doing.
    return key_description.encode('utf-16')


def _get_principal_type_from_object_id(cli_ctx, assignee_object_id):
    client = _graph_client_factory(cli_ctx)
    try:
        result = _get_object_stubs(client, [assignee_object_id])
        if result:
            return result[0].object_type
    except CloudError:
        logger.warning('Failed to query --assignee-principal-type for --assignee-object-id %s by invoking Graph API.',
                       assignee_object_id)
    return None


def _resolve_object_id(cli_ctx, assignee, fallback_to_object_id=False):
    object_id, _ = _resolve_object_id_and_type(cli_ctx, assignee, fallback_to_object_id=fallback_to_object_id)
    return object_id


def _resolve_object_id_and_type(cli_ctx, assignee, fallback_to_object_id=False):
    client = _graph_client_factory(cli_ctx)
    result = None
    try:
        if assignee.find('@') >= 0:  # looks like a user principal name
            result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
        if not result:
            result = list(client.service_principals.list(
                filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
        if not result and is_guid(assignee):  # assume an object id, let us verify it
            result = _get_object_stubs(client, [assignee])

        # 2+ matches should never happen, so we only check 'no match' here
        if not result:
            raise CLIError("Cannot find user or service principal in graph database for '{assignee}'. "
                           "If the assignee is an appId, make sure the corresponding service principal is created "
                           "with 'az ad sp create --id {assignee}'.".format(assignee=assignee))

        return result[0].object_id, result[0].object_type
    except (CloudError, GraphErrorException):
        logger.warning('Failed to query %s by invoking Graph API. '
                       'If you don\'t have permission to query Graph API, please '
                       'specify --assignee-object-id and --assignee-principal-type.', assignee)
        if fallback_to_object_id and is_guid(assignee):
            logger.warning('Assuming %s as an object ID.', assignee)
            return assignee, None
        raise


def _get_object_stubs(graph_client, assignees):
    from azure.graphrbac.models import GetObjectsParameters
    result = []
    assignees = list(assignees)  # callers could pass in a set
    for i in range(0, len(assignees), 1000):
        params = GetObjectsParameters(include_directory_object_references=True, object_ids=assignees[i:i + 1000])
        result += list(graph_client.objects.get_objects_by_object_ids(params))
    return result


def _get_owner_url(cli_ctx, owner_object_id):
    if '://' in owner_object_id:
        return owner_object_id
    graph_url = cli_ctx.cloud.endpoints.active_directory_graph_resource_id
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    _, _2, tenant_id = profile.get_login_credentials()
    return graph_url + tenant_id + '/directoryObjects/' + owner_object_id


def _set_owner(cli_ctx, graph_client, asset_object_id, setter):
    signed_in_user_object_id = _get_signed_in_user_object_id(graph_client)
    if signed_in_user_object_id:
        setter(asset_object_id, _get_owner_url(cli_ctx, signed_in_user_object_id))


# for injecting test seems to produce predictable role assignment id for playback
def _gen_guid():
    return uuid.uuid4()


# reference: https://pynative.com/python-generate-random-string/
def _random_password(length):
    import random
    import string
    safe_punctuation = '-_.~'
    random_source = string.ascii_letters + string.digits + safe_punctuation
    alphanumeric = string.ascii_letters + string.digits

    # make sure first character is not a punctuation like '--' which will make CLI command break
    first_character = random.SystemRandom().choice(alphanumeric)

    # make sure we have special character in the password
    password = random.SystemRandom().choice(string.ascii_lowercase)
    password += random.SystemRandom().choice(string.ascii_uppercase)
    password += random.SystemRandom().choice(string.digits)
    password += random.SystemRandom().choice(safe_punctuation)

    # generate a password of the given length from the options in the random_source variable
    for _ in range(length - 5):
        password += random.SystemRandom().choice(random_source)

    # turn it into a list for some extra shuffling
    password_list = list(password)
    random.SystemRandom().shuffle(password_list)

    password = first_character + ''.join(password_list)
    return password

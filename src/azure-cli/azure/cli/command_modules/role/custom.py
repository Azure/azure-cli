# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
`az ad` module has been migrated to use Microsoft Graph API: https://docs.microsoft.com/en-us/graph/api/overview

See:
Property differences between Azure AD Graph and Microsoft Graph
https://docs.microsoft.com/en-us/graph/migrate-azure-ad-graph-property-differences
"""

import base64
import datetime
import itertools
import json
import os
import re
import uuid

import dateutil.parser
from dateutil.relativedelta import relativedelta
from knack.log import get_logger
from knack.util import CLIError, todict
from msrestazure.azure_exceptions import CloudError

from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import get_file_json, shell_safe_json_parse, is_guid
from ._client_factory import _auth_client_factory, _graph_client_factory
from ._multi_api_adaptor import MultiAPIAdaptor
from ._msgrpah import GraphError, set_object_properties

# ARM RBAC's principalType
USER = 'User'
SERVICE_PRINCIPAL = 'ServicePrincipal'
GROUP = 'Group'

# Map Graph '@odata.type' to ARM RBAC's principalType
ODATA_TYPE_TO_PRINCIPAL_TYPE = {
    '#microsoft.graph.user': USER,
    '#microsoft.graph.servicePrincipal': SERVICE_PRINCIPAL,
    '#microsoft.graph.group': GROUP
}

# Object ID property name
ID = 'id'

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
            principal_dics = {i[ID]: _get_displayable_name(i) for i in principals}

            for i in [r for r in results if not r.get('principalName')]:
                i['principalName'] = ''
                if principal_dics.get(worker.get_role_property(i, 'principalId')):
                    worker.set_role_property(i, 'principalName',
                                             principal_dics[worker.get_role_property(i, 'principalId')])
        except (CloudError, GraphError) as ex:
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

    time_filter = 'eventTimestamp ge {} and eventTimestamp le {}'.format(_datetime_to_utc(start_time),
                                                                         _datetime_to_utc(end_time))

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
            principal_dics = {i['id']: _get_displayable_name(i) for i in stubs}
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
        temp = list(list_users(graph_client, query_filter=' or '.join(upn_queries)))
        users += temp
    upns = {u['userPrincipalName']: u[ID] for u in users}
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
    # user
    if 'userPrincipalName' in graph_object:
        return graph_object['userPrincipalName']
    # service principal
    if 'servicePrincipalNames' in graph_object:
        return graph_object['servicePrincipalNames'][0]
    # group
    return graph_object['displayName'] or ''


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

    # https://docs.microsoft.com/en-us/azure/role-based-access-control/role-assignments-list-rest
    # "atScope()" and "principalId eq '{value}'" query cannot be used together (API limitation).
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


def create_application(cmd, client, display_name, identifier_uris=None,
                       is_fallback_public_client=None, sign_in_audience=None,
                       # keyCredentials
                       key_value=None, key_type=None, key_usage=None, start_date=None, end_date=None,
                       key_display_name=None,
                       # web
                       web_home_page_url=None, web_redirect_uris=None,
                       enable_id_token_issuance=None, enable_access_token_issuance=None,
                       # publicClient
                       public_client_redirect_uris=None,
                       # JSON properties
                       app_roles=None, optional_claims=None, required_resource_accesses=None):
    # pylint:disable=too-many-locals
    graph_client = _graph_client_factory(cmd.cli_ctx)

    existing_apps = list_applications(cmd, client, display_name=display_name)
    if existing_apps:
        if identifier_uris:
            existing_apps = [x for x in existing_apps if set(identifier_uris).issubset(set(x['identifierUris']))]
        existing_apps = [x for x in existing_apps if x['displayName'] == display_name]
        if len(existing_apps) > 1:
            raise CLIError("More than one application have the same display name '{}': (id) {}, please remove "
                           'them first.'.format(display_name, ', '.join([x[ID] for x in existing_apps])))
        if len(existing_apps) == 1:
            logger.warning("Found an existing application instance: (id) %s. We will patch it.",
                           existing_apps[0][ID])
            body = update_application(
                existing_apps[0], display_name=display_name, identifier_uris=identifier_uris,
                is_fallback_public_client=is_fallback_public_client, sign_in_audience=sign_in_audience,
                # keyCredentials
                key_value=key_value, key_type=key_type, key_usage=key_usage,
                start_date=start_date, end_date=end_date,
                key_display_name=key_display_name,
                # web
                web_home_page_url=web_home_page_url, web_redirect_uris=web_redirect_uris,
                enable_id_token_issuance=enable_id_token_issuance,
                enable_access_token_issuance=enable_access_token_issuance,
                # publicClient
                public_client_redirect_uris=public_client_redirect_uris,
                # JSON properties
                app_roles=app_roles,
                optional_claims=optional_claims,
                required_resource_accesses=required_resource_accesses)
            patch_application(cmd, existing_apps[0][ID], body)

            # no need to resolve identifierUris or appId. Just use id.
            return client.application_get(existing_apps[0][ID])

    # identifierUris is no longer required, compared to AD Graph
    key_credentials = _build_key_credentials(
        key_value=key_value, key_type=key_type, key_usage=key_usage,
        start_date=start_date, end_date=end_date, display_name=key_display_name)

    body = {}

    _set_application_properties(
        body, display_name=display_name, identifier_uris=identifier_uris,
        is_fallback_public_client=is_fallback_public_client, sign_in_audience=sign_in_audience,
        # keyCredentials
        key_credentials=key_credentials,
        # web
        web_home_page_url=web_home_page_url, web_redirect_uris=web_redirect_uris,
        enable_id_token_issuance=enable_id_token_issuance,
        enable_access_token_issuance=enable_access_token_issuance,
        # publicClient
        public_client_redirect_uris=public_client_redirect_uris,
        # JSON properties
        app_roles=app_roles, optional_claims=optional_claims, required_resource_accesses=required_resource_accesses
    )

    try:
        result = graph_client.application_create(body)
    except GraphError as ex:
        if 'insufficient privileges' in str(ex).lower():
            link = 'https://docs.microsoft.com/azure/azure-resource-manager/resource-group-create-service-principal-portal'  # pylint: disable=line-too-long
            raise CLIError("Directory permission is needed for the current user to register the application. "
                           "For how to configure, please refer '{}'. Original error: {}".format(link, ex))
        raise
    return result


def update_application(instance, display_name=None, identifier_uris=None,  # pylint: disable=unused-argument
                       is_fallback_public_client=None, sign_in_audience=None,
                       # keyCredentials
                       key_value=None, key_type=None, key_usage=None, start_date=None, end_date=None,
                       key_display_name=None,
                       # web
                       web_home_page_url=None, web_redirect_uris=None,
                       enable_id_token_issuance=None, enable_access_token_issuance=None,
                       # publicClient
                       public_client_redirect_uris=None,
                       # JSON properties
                       app_roles=None, optional_claims=None, required_resource_accesses=None):
    body = {}

    key_credentials = None
    if key_value:
        key_credentials = _build_key_credentials(
            key_value=key_value, key_type=key_type, key_usage=key_usage,
            start_date=start_date, end_date=end_date, display_name=key_display_name)

    _set_application_properties(
        body, display_name=display_name, identifier_uris=identifier_uris,
        is_fallback_public_client=is_fallback_public_client, sign_in_audience=sign_in_audience,
        # keyCredentials
        key_credentials=key_credentials,
        # web
        web_home_page_url=web_home_page_url, web_redirect_uris=web_redirect_uris,
        enable_id_token_issuance=enable_id_token_issuance,
        enable_access_token_issuance=enable_access_token_issuance,
        # publicClient
        public_client_redirect_uris=public_client_redirect_uris,
        # JSON properties
        app_roles=app_roles, optional_claims=optional_claims, required_resource_accesses=required_resource_accesses
    )

    return body


def patch_application(cmd, identifier, parameters):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    object_id = _resolve_application(graph_client, identifier)
    return graph_client.application_update(object_id, parameters)


def show_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    result = client.application_get(object_id)
    return result


def delete_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    client.application_delete(object_id)


def list_applications(cmd, client, app_id=None,  # pylint: disable=unused-argument
                      display_name=None, identifier_uri=None, query_filter=None,
                      include_all=None, show_mine=None):
    if show_mine:
        return list_owned_objects(client, '#microsoft.graph.application')
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if app_id:
        sub_filters.append("appId eq '{}'".format(app_id))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))
    if identifier_uri:
        sub_filters.append("identifierUris/any(s:s eq '{}')".format(identifier_uri))

    result = client.application_list(filter=' and '.join(sub_filters) if sub_filters else None)
    if sub_filters or include_all:
        return list(result)

    result = list(itertools.islice(result, 101))
    if len(result) == 101:
        logger.warning("The result is not complete. You can still use '--all' to get all of them with"
                       " long latency expected, or provide a filter through command arguments")
    return result[:100]


def _resolve_application(client, identifier):
    """Resolve an application's id (previously known as objectId) from
      - appId
      - id (returned as-is)
      - identifierUris
    """
    if is_guid(identifier):
        # it is either app id or object id, let us verify
        result = client.application_list(filter="appId eq '{}'".format(identifier))
        # If not found, this looks like an object id
        return result[0][ID] if result else identifier

    result = client.application_list(filter="identifierUris/any(s:s eq '{}')".format(identifier))
    if not result:
        error = CLIError("Application with identifier URI '{}' doesn't exist".format(identifier))
        error.status_code = 404  # Make sure CLI returns 3
        raise error
    return result[0][ID]


def reset_application_credential(cmd, client, identifier, create_cert=False, cert=None, years=None,
                                 end_date=None, keyvault=None, append=False, display_name=None):
    app = show_application(client, identifier)
    if not app:
        raise CLIError("can't find an application matching '{}'".format(identifier))
    result = _reset_credential(
        cmd, app, client.application_add_password, client.application_remove_password,
        client.application_update, create_cert=create_cert, cert=cert, years=years,
        end_date=end_date, keyvault=keyvault, append=append, display_name=display_name)
    result['tenant'] = client.tenant
    return result


def delete_application_credential(cmd, client, identifier, key_id, cert=False):  # pylint: disable=unused-argument
    sp = show_application(client, identifier)
    _delete_credential(sp, client.application_remove_password, client.application_update,
                       key_id=key_id, cert=cert)


def list_application_credentials(cmd, identifier, cert=False):
    # Also see: list_service_principal_credentials
    client = _graph_client_factory(cmd.cli_ctx)
    app = show_application(client, identifier)
    return _list_credentials(app, cert)


def add_application_owner(client, owner_object_id, identifier):
    app_object_id = _resolve_application(client, identifier)
    owners = client.application_owner_list(app_object_id)
    # API not idempotent and fails with:
    #   One or more added object references already exist for the following modified properties: 'owners'
    # We make it idempotent.
    if not next((x for x in owners if x[ID] == owner_object_id), None):
        body = _build_directory_object_json(client, owner_object_id)
        client.application_owner_add(app_object_id, body)


def remove_application_owner(client, owner_object_id, identifier):
    app_object_id = _resolve_application(client, identifier)
    return client.application_owner_remove(app_object_id, owner_object_id)


def list_application_owners(client, identifier):
    app_object_id = _resolve_application(client, identifier)
    return client.application_owner_list(app_object_id)


def _get_grant_permissions(client, client_sp_object_id=None, query_filter=None):
    query_filter = query_filter or ("clientId eq '{}'".format(client_sp_object_id) if client_sp_object_id else None)
    grant_info = client.oauth2_permission_grant_list(filter=query_filter)
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


def add_permission(client, identifier, api, api_permissions):
    # requiredResourceAccess property (requiredResourceAccess collection)
    #   requiredResourceAccess resource type
    #     resourceAppId   <- api
    #     resourceAccess property   (resourceAccess collection)
    #       resourceAccess resource type
    #         id            <- api_permissions
    #         type

    application = show_application(client, identifier)

    resource_access_list = []
    for e in api_permissions:
        access_id, access_type = e.split('=')
        resource_access = {
            "id": access_id,
            "type": access_type
        }
        resource_access_list.append(resource_access)

    required_resource_access_list = application['requiredResourceAccess']
    existing_required_resource_access = next((e for e in required_resource_access_list if e['resourceAppId'] == api),
                                             None)
    if existing_required_resource_access:
        existing_required_resource_access['resourceAccess'] += resource_access_list
    else:
        required_resource_access = {
            'resourceAppId': api,
            'resourceAccess': resource_access_list
        }
        required_resource_access_list.append(required_resource_access)
    body = {'requiredResourceAccess': required_resource_access_list}
    client.application_update(application[ID], body)
    logger.warning('Invoking `az ad app permission grant --id %s --api %s` is needed to make the '
                   'change effective', identifier, api)


def delete_permission(client, identifier, api, api_permissions=None):
    application = show_application(client, identifier)
    required_resource_access_list = application['requiredResourceAccess']

    # Get the RequiredResourceAccess object whose resource_app_id == api
    existing_required_resource_access = next((e for e in required_resource_access_list if e['resourceAppId'] == api),
                                             None)

    if not existing_required_resource_access:
        # Silently pass if the api is not required.
        logger.warning("App %s doesn't require access to API %s.", identifier, api)
        return None

    if api_permissions:
        resource_access_list = existing_required_resource_access['resourceAccess']
        # Check if the user tries to delete any ResourceAccess that is not required.
        ra_ids = [ra[ID] for ra in resource_access_list]
        non_existing_ra_ids = [p for p in api_permissions if p not in ra_ids]
        if non_existing_ra_ids:
            logger.warning("App %s doesn't require access to API %s's permission %s.",
                           identifier, api, ', '.join(non_existing_ra_ids))
            if len(non_existing_ra_ids) == len(api_permissions):
                # Skip the REST call if nothing to remove
                return None

        # Remove specified ResourceAccess under RequiredResourceAccess.resource_access
        existing_required_resource_access['resourceAccess'] = \
            [ra for ra in resource_access_list if ra[ID] not in api_permissions]
        # Remove the RequiredResourceAccess if its resource_access is empty
        if not existing_required_resource_access['resourceAccess']:
            required_resource_access_list.remove(existing_required_resource_access)
    else:
        # Remove the whole RequiredResourceAccess
        required_resource_access_list.remove(existing_required_resource_access)

    body = {'requiredResourceAccess': required_resource_access_list}
    return client.application_update(application[ID], body)


def list_permissions(cmd, identifier):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    application = show_application(graph_client, identifier)
    return application['requiredResourceAccess']


def admin_consent(cmd, client, identifier):
    from azure.cli.core.cloud import AZURE_PUBLIC_CLOUD
    from azure.cli.core.util import send_raw_request

    if cmd.cli_ctx.cloud.name != AZURE_PUBLIC_CLOUD.name:
        raise CLIError('This command is not yet supported on sovereign clouds')

    application = show_application(client, identifier)
    url = 'https://main.iam.ad.ext.azure.com/api/RegisteredApplications/{}/Consent?onBehalfOfAll=true'.format(
        application['appId'])
    send_raw_request(cmd.cli_ctx, 'post', url, resource='74658136-14ec-4630-ad9b-26e160ff0fc6')


def grant_application(cmd, client, identifier,  # pylint: disable=unused-argument
                      api, scope, consent_type=None, principal_id=None):
    # Get the Service Principal ObjectId for the client app
    client_sp_object_id = _resolve_service_principal(client, identifier)

    # Get the Service Principal ObjectId for resource app
    resource_sp_object_id = _resolve_service_principal(client, api)

    # ensure to remove the older grant
    # TODO: Filtering with clientId and resourceId removes too many.
    #   https://github.com/Azure/azure-cli/issues/20974
    grant_permissions = _get_grant_permissions(client, client_sp_object_id=client_sp_object_id)
    to_delete = [p[ID] for p in grant_permissions if p['clientId'] == client_sp_object_id and
                 p['resourceId'] == resource_sp_object_id]
    for p in to_delete:
        client.oauth2_permission_grant_delete(p)

    body = {
        "clientId": client_sp_object_id,
        "consentType": consent_type,
        "principalId": principal_id,
        "resourceId": resource_sp_object_id,
        "scope": ' '.join(scope)
    }
    return client.oauth2_permission_grant_create(body)  # pylint: disable=no-member


def list_permission_grants(client, identifier=None, query_filter=None, show_resource_name=None):
    if identifier and query_filter:
        raise CLIError('Please only use one of "--identifier" and "--filter", not both')
    client_sp_object_id = None
    if identifier:
        client_sp_object_id = _resolve_service_principal(client, identifier)
    result = _get_grant_permissions(client, client_sp_object_id=client_sp_object_id, query_filter=query_filter)
    if show_resource_name:
        for r in result:
            sp = client.service_principal_get(r['resourceId'])
            r['resourceDisplayName'] = sp['displayName']
    return result


def create_service_principal(cmd, identifier):
    return _create_service_principal(cmd.cli_ctx, identifier)


def update_service_principal(instance):  # pylint: disable=unused-argument
    # Do not PATCH back properties retrieved with GET and leave everything else to generic update.
    return {}


def patch_service_principal(cmd, identifier, parameters):
    graph_client = _graph_client_factory(cmd.cli_ctx)
    object_id = _resolve_service_principal(graph_client, identifier)
    return graph_client.service_principal_update(object_id, parameters)


def _create_service_principal(cli_ctx, identifier, resolve_app=True):
    client = _graph_client_factory(cli_ctx)
    app_id = identifier
    if resolve_app:
        if is_guid(identifier):
            result = list(client.application_list(filter="appId eq '{}'".format(identifier)))
        else:
            result = list(client.application_list(
                filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        try:
            if not result:  # assume we get an object id
                result = [client.application_get(identifier)]
            app_id = result[0]['appId']
        except GraphError:
            pass  # fallback to appid (maybe from an external tenant?)

    body = {
        "appId": app_id,
        "accountEnabled": True
    }
    return client.service_principal_create(body)


def show_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    return client.service_principal_get(object_id)


def delete_service_principal(cmd, identifier):
    client = _graph_client_factory(cmd.cli_ctx)
    sp_object_id = _resolve_service_principal(client, identifier)
    client.service_principal_delete(sp_object_id)


def list_service_principals(cmd, client,  # pylint: disable=unused-argument
                            spn=None, display_name=None, query_filter=None, show_mine=None,
                            include_all=None):
    if show_mine:
        return list_owned_objects(client, '#microsoft.graph.servicePrincipal')

    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if spn:
        sub_filters.append("servicePrincipalNames/any(c:c eq '{}')".format(spn))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    result = client.service_principal_list(filter=' and '.join(sub_filters) if sub_filters else None)

    if sub_filters or include_all:
        return result

    result = list(itertools.islice(result, 101))
    if len(result) == 101:
        logger.warning("The result is not complete. You can still use '--all' to get all of them with"
                       " long latency expected, or provide a filter through command arguments")
    return result[:100]


def reset_service_principal_credential(cmd, client, identifier, create_cert=False, cert=None, years=None,
                                       end_date=None, keyvault=None, append=False, display_name=None):
    sp = show_service_principal(client, identifier)
    if not sp:
        raise CLIError("can't find an service principal matching '{}'".format(identifier))
    result = _reset_credential(
        cmd, sp,
        client.service_principal_add_password, client.service_principal_remove_password,
        client.service_principal_update,
        create_cert=create_cert, cert=cert, years=years,
        end_date=end_date, keyvault=keyvault, append=append, display_name=display_name)
    result['tenant'] = client.tenant
    return result


def delete_service_principal_credential(cmd, client,  # pylint: disable=unused-argument
                                        identifier, key_id, cert=False):
    sp = show_service_principal(client, identifier)
    _delete_credential(sp, client.service_principal_remove_password, client.service_principal_update,
                       key_id=key_id, cert=cert)


def list_service_principal_credentials(cmd, identifier, cert=False):
    # Also see list_application_credentials
    client = _graph_client_factory(cmd.cli_ctx)
    sp = show_service_principal(client, identifier)
    return _list_credentials(sp, cert)


def _get_app_object_id_from_sp_object_id(client, sp_object_id):
    sp = client.service_principals.get(sp_object_id)
    result = list(client.applications.list(filter="appId eq '{}'".format(sp.app_id)))

    if result:
        return result[0].object_id
    raise CLIError("Can't find associated application id from '{}'".format(sp_object_id))


def list_service_principal_owners(client, identifier):
    sp_object_id = _resolve_service_principal(client, identifier)
    return client.service_principal_owner_list(sp_object_id)


# pylint: disable=inconsistent-return-statements
def create_service_principal_for_rbac(
        # pylint:disable=too-many-statements,too-many-locals, too-many-branches, unused-argument
        cmd, display_name=None, years=None, create_cert=False, cert=None, scopes=None, role=None,
        show_auth_for_sdk=None, skip_assignment=False, keyvault=None):
    import time

    if role and not scopes or not role and scopes:
        from azure.cli.core.azclierror import ArgumentUsageError
        raise ArgumentUsageError("Usage error: To create role assignments, specify both --role and --scopes.")

    graph_client = _graph_client_factory(cmd.cli_ctx)

    years = years or 1
    _RETRY_TIMES = 36
    existing_sps = None

    if not display_name:
        # No display name is provided, create a new one
        app_display_name = 'azure-cli-' + datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
    else:
        app_display_name = display_name
        # patch existing app with the same displayName to make the command idempotent
        query_exp = "displayName eq '{}'".format(display_name)
        existing_sps = list(graph_client.service_principal_list(filter=query_exp))

    app_start_date = datetime.datetime.now(datetime.timezone.utc)
    app_end_date = app_start_date + relativedelta(years=years or 1)

    use_cert = False
    public_cert_string = None
    password = None
    cert_file = None

    if cert or create_cert:
        # Key credential is created *at the same time* of application creation.
        # https://docs.microsoft.com/en-us/graph/application-rollkey-prooftoken
        use_cert = True
        public_cert_string, cert_file, cert_start_date, cert_end_date = \
            _process_certificate(
                cmd.cli_ctx, years, app_start_date, app_end_date, cert, create_cert, keyvault)

        app_start_date, app_end_date, cert_start_date, cert_end_date = \
            _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date)

    aad_application = create_application(cmd,
                                         graph_client,
                                         app_display_name,
                                         key_value=public_cert_string,
                                         start_date=app_start_date,
                                         end_date=app_end_date)
    app_id = aad_application['appId']
    # logger.warning("Created application: appId=%s, id=%s, displayName=%s",
    #                app_id, aad_application[ID], aad_application['displayName'])

    # For existing applications, delete all passwords first.
    for cred in aad_application['passwordCredentials']:
        body = {"keyId": cred['keyId']}
        graph_client.application_remove_password(aad_application[ID], body)

    # Password credential is created *after* application creation.
    # https://docs.microsoft.com/en-us/graph/api/resources/passwordcredential
    if not use_cert:
        result = _application_add_password(graph_client, aad_application, app_start_date, app_end_date, 'rbac')
        password = result['secretText']

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
    sp_oid = aad_sp[ID]
    # logger.warning("Created service principal: appId=%s, id=%s", aad_sp['appId'], sp_oid)

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
        'tenant': graph_client.tenant
    }
    if cert_file:
        logger.warning(
            "Please copy %s to a safe place. When you run 'az login', provide the file path in the --password argument",
            cert_file)
        result['fileWithCertAndPrivateKey'] = cert_file

    login_hint = ('To log in with this service principal, run:\n'
                  f'az login --service-principal --username {app_id} --password {password or cert_file} '
                  f'--tenant {graph_client.tenant}')
    logger.info(login_hint)
    return result


def _resolve_service_principal(client, identifier):
    """Resolve a service principal's id (previously known as objectId) from
      - servicePrincipalNames (contains appId and identifierUris of the corresponding app)
      - id (returned as-is)
    """
    result = client.service_principal_list(filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier))
    if result:
        return result[0][ID]
    if is_guid(identifier):
        return identifier  # assume an object id
    error = CLIError("Service principal '{}' doesn't exist".format(identifier))
    error.status_code = 404  # Make sure CLI returns 3
    raise error


def _process_certificate(cli_ctx, years, app_start_date, app_end_date, cert, create_cert, keyvault):
    # The rest of the scenarios involve certificates
    public_cert_string = None
    cert_file = None
    cert_start_date = None
    cert_end_date = None

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

    return public_cert_string, cert_file, cert_start_date, cert_end_date


def _error_caused_by_role_assignment_exists(ex):
    return getattr(ex, 'status_code', None) == 409 and 'role assignment already exists' in ex.message


def _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date):

    if not cert_start_date and not cert_end_date:
        return app_start_date, app_end_date, None, None

    if cert_start_date > app_start_date:
        logger.warning('Certificate is not valid until %s. Adjusting key credential start date to match.',
                       cert_start_date)
        app_start_date = cert_start_date + datetime.timedelta(seconds=1)

    if cert_end_date < app_end_date:
        logger.warning('Certificate expires %s. Adjusting key credential end date to match.',
                       cert_end_date)
        app_end_date = cert_end_date - datetime.timedelta(seconds=1)

    return app_start_date, app_end_date, cert_start_date, cert_end_date


def _get_keyvault_client(cli_ctx):
    from azure.cli.command_modules.keyvault._client_factory import keyvault_data_plane_factory
    return keyvault_data_plane_factory(cli_ctx)


def _create_self_signed_cert(start_date, end_date):  # pylint: disable=too-many-locals
    from os import path
    import tempfile
    from OpenSSL import crypto
    from datetime import timedelta

    # Create a PEM file ~/tmpxxxxxxxx.pem with both PRIVATE KEY & CERTIFICATE so users can use to log in.
    # The PEM file looks like
    # -----BEGIN PRIVATE KEY-----
    # MIIEv...
    # -----END PRIVATE KEY-----
    # -----BEGIN CERTIFICATE-----
    # MIICo...
    # -----END CERTIFICATE-----

    # Leverage tempfile to produce a random file name. The temp file itself is automatically deleted.
    # There doesn't seem to be a good way to create a random file name without creating the file itself:
    # https://stackoverflow.com/questions/26541416/generate-temporary-file-names-without-creating-actual-file-in-python
    with tempfile.NamedTemporaryFile() as f:
        temp_file_name = f.name
    creds_file = path.join(path.expanduser("~"), path.basename(temp_file_name) + '.pem')

    # Create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # Create a self-signed cert
    cert = crypto.X509()
    subject = cert.get_subject()
    # As long as it works, we skip fields C, ST, L, O, OU, which we have no reasonable defaults for
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

    cert_string = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode()
    key_string = crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode()

    with os.fdopen(_open(creds_file), 'w+') as cf:
        cf.write(key_string)
        cf.write(cert_string)

    # Get rid of the header and tail for uploading to AAD: -----BEGIN CERTIFICATE-----, -----END CERTIFICATE-----
    cert_string = re.sub(r'-+[A-z\s]+-+', '', cert_string).strip()
    return cert_string, creds_file, cert_start_date, cert_end_date


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


def _get_principal_type_from_object_id(cli_ctx, assignee_object_id):
    client = _graph_client_factory(cli_ctx)
    try:
        result = _get_object_stubs(client, [assignee_object_id])
        if result:
            return _odata_type_to_arm_principal_type(result[0]['@odata.type'])
    except GraphError:
        logger.warning('Failed to query --assignee-principal-type for --assignee-object-id %s by invoking Graph API.',
                       assignee_object_id)
    return None


def _resolve_object_id(cli_ctx, assignee, fallback_to_object_id=False):
    object_id, _ = _resolve_object_id_and_type(cli_ctx, assignee, fallback_to_object_id=fallback_to_object_id)
    return object_id


def _resolve_object_id_and_type(cli_ctx, assignee, fallback_to_object_id=False):
    client = _graph_client_factory(cli_ctx)
    try:
        # Try resolving as user
        if assignee.find('@') >= 0:  # looks like a user principal name
            result = list(client.user_list(filter="userPrincipalName eq '{}'".format(assignee)))
            if result:
                return result[0][ID], USER

        # Try resolving as service principal
        result = list(client.service_principal_list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
        if result:
            return result[0][ID], SERVICE_PRINCIPAL

        # Try resolving as object ID
        if is_guid(assignee):  # assume an object id, let us verify it
            result = _get_object_stubs(client, [assignee])
            if result:
                return result[0][ID], _odata_type_to_arm_principal_type(result[0]['@odata.type'])

        # 2+ matches should never happen, so we only check 'no match' here
        raise CLIError("Cannot find user or service principal in graph database for '{assignee}'. "
                       "If the assignee is an appId, make sure the corresponding service principal is created "
                       "with 'az ad sp create --id {assignee}'.".format(assignee=assignee))
    except GraphError:
        logger.warning('Failed to query %s by invoking Graph API. '
                       'If you don\'t have permission to query Graph API, please '
                       'specify --assignee-object-id and --assignee-principal-type.', assignee)
        if fallback_to_object_id and is_guid(assignee):
            logger.warning('Assuming %s as an object ID.', assignee)
            return assignee, None
        raise


def _get_object_stubs(graph_client, assignees):
    result = []
    assignees = list(assignees)  # callers could pass in a set
    # Per https://docs.microsoft.com/en-us/graph/api/directoryobject-getbyids
    # > You can specify up to 1000 IDs.
    for i in range(0, len(assignees), 1000):
        body = {
            "ids": assignees[i:i + 1000],
            # According to https://docs.microsoft.com/en-us/graph/api/directoryobject-getbyids,
            # directoryObject should work as all of the resource types defined in the directory, but it doesn't.
            "types": ['user', 'group', 'servicePrincipal', 'directoryObjectPartnerReference']
        }
        result.extend(list(graph_client.directory_object_get_by_ids(body)))
    return result


# for injecting test seems to produce predictable role assignment id for playback
def _gen_guid():
    return uuid.uuid4()


def _application_add_password(client, app, start_datetime, end_datetime, display_name):
    """Let graph service generate a random password."""
    body = {
        "passwordCredential": {
            "startDateTime": _datetime_to_utc(start_datetime),
            "endDateTime": _datetime_to_utc(end_datetime),
            "displayName": display_name
        }
    }
    result = client.application_add_password(app[ID], body)
    return result


def _set_application_properties(body, **kwargs):

    # Preprocess JSON properties
    if kwargs.get('app_roles'):
        kwargs['app_roles'] = _build_app_roles(kwargs['app_roles'])
    if kwargs.get('optional_claims'):
        kwargs['optional_claims'] = _build_optional_claims(kwargs['optional_claims'])
    if kwargs.get('required_resource_accesses'):
        kwargs['required_resource_accesses'] = _build_required_resource_accesses(kwargs['required_resource_accesses'])

    set_object_properties('application', body, **kwargs)


def _datetime_to_utc(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def _build_required_resource_accesses(required_resource_accesses):
    # https://docs.microsoft.com/en-us/graph/api/resources/requiredresourceaccess
    if isinstance(required_resource_accesses, dict):
        logger.info('Getting "requiredResourceAccess" from a full manifest')
        required_resource_accesses = required_resource_accesses.get('requiredResourceAccess', [])
    return required_resource_accesses


def _build_app_roles(app_roles):
    # https://docs.microsoft.com/en-us/graph/api/resources/approle
    if isinstance(app_roles, dict):
        logger.info('Getting "appRoles" from a full manifest')
        app_roles = app_roles.get('appRoles', [])
    for x in app_roles:
        # Make sure 'id' is specified as a GUID if not provided.
        if not x.get(ID):
            x[ID] = str(_gen_guid())
    return app_roles


def _build_optional_claims(optional_claims):
    # https://docs.microsoft.com/en-us/graph/api/resources/optionalclaim
    # https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-optional-claims#configuring-optional-claims
    if 'optionalClaims' in optional_claims:
        logger.info('Getting "optionalClaims" from a full manifest')
        optional_claims = optional_claims.get('optionalClaims', [])
    return optional_claims


def _build_add_password_credential_body(display_name, start_datetime, end_datetime):
    # https://docs.microsoft.com/en-us/graph/api/resources/passwordcredential
    body = {
        "passwordCredential": {
            "displayName": display_name,
            "endDateTime": _datetime_to_utc(end_datetime),
            "startDateTime": _datetime_to_utc(start_datetime)
        }
    }
    return body


def _build_key_credentials(key_value=None, key_type=None, key_usage=None,
                           start_date=None, end_date=None, display_name=None):
    if not key_value:
        # No key credential should be set
        return []

    if not start_date:
        start_date = datetime.datetime.utcnow()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + relativedelta(years=1) - relativedelta(hours=24)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)

    key_type = key_type or 'AsymmetricX509Cert'
    key_usage = key_usage or 'Verify'

    # https://docs.microsoft.com/en-us/graph/api/resources/keycredential
    key_credential = {
        "@odata.type": "#microsoft.graph.keyCredential",
        "displayName": display_name,
        "endDateTime": _datetime_to_utc(end_date),
        "key": key_value,
        "keyId": str(_gen_guid()),
        "startDateTime": _datetime_to_utc(start_date),
        "type": key_type,
        "usage": key_usage
    }
    return [key_credential]


def _reset_credential(cmd, graph_object, add_password_func, remove_password_func, patch_func,
                      create_cert=False, cert=None, years=None,
                      end_date=None, keyvault=None, append=False, display_name=None):
    # pylint: disable=too-many-locals
    """Reset passwordCredentials and keyCredentials properties for application or service principal.
    Application and service principal share the same interface for operating credentials.

    :param graph_object: The application or service principal object (dict).
    :param add_password_func: Add password API function.
    :param remove_password_func: Remove password API function.
    :param patch_func: Patch API function. Used to update keyCredentials.
    """

    # https://docs.microsoft.com/en-us/graph/api/resources/passwordcredential
    # https://docs.microsoft.com/en-us/graph/api/resources/keycredential
    # Only displayName should be set.
    # For passwordCredential, customKeyIdentifier is not applicable.
    # For keyCredential, customKeyIdentifier is automatically computed by Graph service as certificate thumbprint.
    # https://github.com/Azure/azure-cli/issues/20561

    app_start_date = datetime.datetime.now(datetime.timezone.utc)
    if years is not None and end_date is not None:
        raise CLIError('usage error: --years | --end-date')
    if end_date is None:
        years = years or 1
        app_end_date = app_start_date + relativedelta(years=years)
    else:
        app_end_date = dateutil.parser.parse(end_date)
        if app_end_date.tzinfo is None:
            app_end_date = app_end_date.replace(tzinfo=datetime.timezone.utc)
        years = (app_end_date - app_start_date).days / 365

    # Created password
    password = None
    # Created certificate
    cert_file = None

    if not append:
        # Delete all existing password
        for cred in graph_object['passwordCredentials']:
            body = {"keyId": cred['keyId']}
            remove_password_func(graph_object[ID], body)

    # By default, add password
    if not (cert or create_cert):
        body = _build_add_password_credential_body(display_name, app_start_date, app_end_date)
        add_password_result = add_password_func(graph_object[ID], body)
        password = add_password_result['secretText']
        # key_id = add_password_result['keyId']

    else:
        public_cert_string, cert_file, cert_start_date, cert_end_date = \
            _process_certificate(cmd.cli_ctx, years, app_start_date, app_end_date, cert, create_cert,
                                 keyvault)

        app_start_date, app_end_date, cert_start_date, cert_end_date = \
            _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date)

        key_creds = []
        if append:
            key_creds = graph_object['keyCredentials']

        new_key_creds = _build_key_credentials(
            key_value=public_cert_string, start_date=app_start_date, end_date=app_end_date, display_name=display_name)

        # key_id = new_key_creds[0]['keyId']
        key_creds.extend(new_key_creds)

        patch_body = {
            'keyCredentials': key_creds
        }
        patch_func(graph_object[ID], patch_body)

    # Keep backward compatibility
    # TODO: Should we return the passwordCredential or keyCredential directly?
    result = {
        'appId': graph_object['appId'],
        # 'keyId': key_id,
        'password': password
    }
    if cert_file:
        result['fileWithCertAndPrivateKey'] = cert_file

    logger.warning(CREDENTIAL_WARNING)
    return result


def _delete_credential(graph_object, remove_password_func, patch_function, key_id, cert=False):
    if cert:
        key_creds = graph_object['keyCredentials']

        to_delete = next((x for x in key_creds if x['keyId'] == key_id), None)
        if to_delete:
            key_creds.remove(to_delete)
            body = {
                'keyCredentials': key_creds
            }
            patch_function(graph_object[ID], body)
        else:
            raise CLIError("No key credential found with keyId as '{}' in graph object '{}'.".format(
                key_id, graph_object[ID]))
    else:
        body = {
            "keyId": key_id
        }
        remove_password_func(graph_object[ID], body)


def _list_credentials(graph_object, cert):
    if cert:
        return graph_object['keyCredentials']
    return graph_object['passwordCredentials']


def _match_odata_type(odata_type, user_input):
    """Compare the @odata.type property of the object with the user's input.
    For example, a service principal object has
      "@odata.type": "#microsoft.graph.servicePrincipal"
    """
    odata_type = odata_type.lower()
    user_input = user_input.lower()
    # Full match "#microsoft.graph.servicePrincipal" == "#microsoft.graph.servicePrincipal"
    # Partial match "#microsoft.graph.servicePrincipal" ~= "servicePrincipal"
    return odata_type == user_input or odata_type.split('.')[-1] == user_input


def _open(location):
    """Open a file that only the current user can access."""
    # The 600 seems no-op on Windows, and that is fine.
    return os.open(location, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)


def _odata_type_to_arm_principal_type(odata_type):
    # TODO: Figure out a more generic conversion method
    return ODATA_TYPE_TO_PRINCIPAL_TYPE.get(odata_type)


def show_signed_in_user(client):
    result = client.signed_in_user_get()
    return result


def list_owned_objects(client, object_type=None):
    result = client.owned_objects_list()
    if object_type:
        result = [r for r in result if r.get('@odata.type') and _match_odata_type(r.get('@odata.type'), object_type)]
    return result


def create_user(client, user_principal_name, display_name, password,
                mail_nickname=None, immutable_id=None, force_change_password_next_sign_in=False):
    '''
    :param mail_nickname: mail alias. default to user principal name
    '''
    mail_nickname = mail_nickname or user_principal_name.split('@')[0]
    body = {}
    _set_user_properties(body, user_principal_name=user_principal_name, display_name=display_name, password=password,
                         mail_nickname=mail_nickname, immutable_id=immutable_id,
                         force_change_password_next_sign_in=force_change_password_next_sign_in, account_enabled=True)
    return client.user_create(body)


def update_user(client, upn_or_object_id, display_name=None, force_change_password_next_sign_in=None, password=None,
                account_enabled=None, mail_nickname=None):
    body = {}
    _set_user_properties(body, display_name=display_name, password=password, mail_nickname=mail_nickname,
                         force_change_password_next_sign_in=force_change_password_next_sign_in,
                         account_enabled=account_enabled)
    return client.user_update(upn_or_object_id, body)


def _set_user_properties(body, **kwargs):
    set_object_properties('user', body, **kwargs)


def show_user(client, upn_or_object_id):
    return client.user_get(upn_or_object_id)


def delete_user(client, upn_or_object_id):
    client.user_delete(upn_or_object_id)


def list_users(client, upn=None, display_name=None, query_filter=None):
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if upn:
        sub_filters.append("userPrincipalName eq '{}'".format(upn))
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    return client.user_list(filter=' and '.join(sub_filters) if sub_filters else None)


def get_user_member_groups(client, upn_or_object_id, security_enabled_only=False):
    results = _get_member_groups(client.user_get_member_groups, upn_or_object_id, security_enabled_only)
    try:
        stubs = _get_object_stubs(client, results)
    except GraphError:
        stubs = []
    stubs = {s[ID]: s['displayName'] for s in stubs}
    return [{'id': x, 'displayName': stubs.get(x)} for x in results]


def create_group(client, display_name, mail_nickname, force=None, description=None):
    # workaround to ensure idempotent even AAD graph service doesn't support it
    if not force:
        matches = client.group_list(filter="displayName eq '{}' and mailNickname eq '{}'".format(display_name,
                                                                                                 mail_nickname))
        if matches:
            if len(matches) > 1:
                err = ('There is more than one group with the same display and nick names: "{}". '
                       'Please delete them first.')
                raise CLIError(err.format(', '.join([x.object_id for x in matches])))
            logger.warning('A group with the same display name and mail nickname already exists, returning.')
            return matches[0]

    body = {}
    set_object_properties('group', body, display_name=display_name,
                          mail_nickname=mail_nickname, description=description,
                          mail_enabled=False, security_enabled=True)

    return client.group_create(body)


def list_groups(client, display_name=None, query_filter=None):
    """List groups in the directory"""
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))
    return client.group_list(filter=' and '.join(sub_filters) if sub_filters else None)


def get_group(client, object_id):
    """Get group information from the directory."""
    return client.group_get(object_id)


def delete_group(client, object_id):
    """Delete a group from the directory."""
    return client.group_delete(object_id)


def get_group_member_groups(client, object_id, security_enabled_only=False):
    """Get a collection of object IDs of groups of which the specified group is a member."""
    return _get_member_groups(client.group_get_member_groups, object_id, security_enabled_only)


def list_group_owners(client, group_id):
    return client.group_owner_list(_resolve_group(client, group_id))


def add_group_owner(client, owner_object_id, group_id):
    group_object_id = _resolve_group(client, group_id)
    owners = client.group_owner_list(group_object_id)
    # API is not idempotent and fails with:
    #   One or more added object references already exist for the following modified properties: 'owners'.
    if not next((x for x in owners if x['id'] == owner_object_id), None):
        body = _build_directory_object_json(client, owner_object_id)
        return client.group_owner_add(group_object_id, body)


def remove_group_owner(client, owner_object_id, group_id):
    return client.group_owner_remove(_resolve_group(client, group_id), owner_object_id)


def check_group_membership(client, group_id, member_object_id):
    body = {"groupIds": [group_id]}
    response = client.directory_object_check_member_groups(member_object_id, body)
    return {"value": response is not None and group_id in response}


def list_group_members(client, group_id):
    """Get the members of a group."""
    return client.group_member_list(group_id)


def add_group_member(client, group_id, member_object_id):
    """Add a member to a group."""
    # API is not idempotent and fails with:
    #   One or more added object references already exist for the following modified properties: 'members'.
    # TODO: make it idempotent like add_group_owner
    body = _build_directory_object_json(client, member_object_id)
    return client.group_member_add(group_id, body)


def remove_group_member(client, group_id, member_object_id):
    """Remove a member from a group."""
    return client.group_member_remove(group_id, member_object_id)


def _resolve_group(client, identifier):
    if not is_guid(identifier):
        res = list(list_groups(client, display_name=identifier))
        if not res:
            raise CLIError('Group {} is not found in Graph '.format(identifier))
        if len(res) != 1:
            raise CLIError('More than 1 group objects has the display name of ' + identifier)
        identifier = res[0].object_id
    return identifier


def _build_directory_object_json(client, object_id):
    """Get JSON representation of the id of the directoryObject.
    The object URL should be in the form of https://graph.microsoft.com/v1.0/directoryObjects/{id}
    """
    # If object_id is not a GUID, use it as-is.
    object_url = f'{client.base_url}/directoryObjects/{object_id}'if is_guid(object_id) else object_id
    body = {
        "@odata.id": object_url
    }
    return body


def _get_member_groups(get_member_group_func, identifier, security_enabled_only):
    """Call 'directoryObject: getMemberGroups' API with specified get_member_group_func.
    https://docs.microsoft.com/en-us/graph/api/directoryobject-getmembergroups
    """
    body = {
        "securityEnabledOnly": security_enabled_only
    }
    return get_member_group_func(identifier, body)

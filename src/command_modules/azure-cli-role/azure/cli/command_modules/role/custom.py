#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
import re
import uuid

from azure.cli._util import CLIError, todict
from azure.cli.commands.client_factory import get_mgmt_service_client, configure_common_settings
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.graphrbac import GraphRbacManagementClient
from azure.mgmt.authorization.models import RoleAssignmentProperties
from azure.graphrbac.models import UserCreateParameters, PasswordProfile

def _auth_client_factory(**_):
    return get_mgmt_service_client(AuthorizationManagementClient)

def _graph_client_factory(**_):
    from azure.cli._profile import Profile
    profile = Profile()
    cred, _, tenant_id = profile.get_login_credentials(True)
    client = GraphRbacManagementClient(cred, tenant_id)
    configure_common_settings(client)
    return client

def list_role_definitions(name=None, resource_group_name=None, resource_id=None,
                          custom_role_only=False):
    '''
    :param name: the role logical name
    '''
    definitions_client = _auth_client_factory().role_definitions
    scope = _build_role_scope(resource_group_name, resource_id,
                              definitions_client.config.subscription_id)

    roles = definitions_client.list(scope, filter="roleName eq '{}'".format(name) if name else None)
    if custom_role_only:
        roles = [r for r in roles if r.properties.type == 'CustomRole']
    return roles

def show_role_definition(role_resource_id=None, role_id=None):
    definitions_client = _auth_client_factory().role_definitions
    if (not role_resource_id and not role_id) or (role_resource_id and role_id):
        raise CLIError('Please provide either role id or role resource id, but not both')
    elif role_resource_id:
        return definitions_client.get_by_id(role_resource_id)
    else:
        scope = '/subscriptions/' + definitions_client.config.subscription_id
        return definitions_client.get(scope=scope, role_definition_id=role_id)

def create_role_assignment(role, assignee, resource_group_name=None, resource_id=None):
    factory = _auth_client_factory()
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = _build_role_scope(resource_group_name, resource_id,
                              assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(assignee)
    properties = RoleAssignmentProperties(role_id, object_id)
    assignment_name = uuid.uuid4()
    return assignments_client.create(scope, assignment_name, properties)

def list_role_assignments(assignee=None, role=None, resource_group_name=None,#pylint: disable=too-many-arguments
                          resource_id=None, include_inherited=False,
                          show_all=False, include_groups=False):
    '''
    :param include_groups: include extra assignments to the groups of which the user is a
    member(transitively). Supported only for a user principal.
    '''
    graph_client = _graph_client_factory()
    definitions_client = _auth_client_factory().role_definitions

    scope = None
    if show_all:
        if resource_group_name or resource_id:
            raise CLIError('group or resource id are not required when --all is used')
        scope = None
    else:
        scope = _build_role_scope(resource_group_name, resource_id,
                                  definitions_client.config.subscription_id)

    assignments = _search_role_assignments(scope, assignee, role,
                                           include_inherited, include_groups)

    if not assignments:
        return []

    #fill in logic names to get things understandable.
    #it's possible that associated roles and principals were deleted, and we just do nothing.

    from azure.cli.application import Application
    results = todict(assignments)

    #pylint: disable=line-too-long
    #fill in role names
    role_defs = list(definitions_client.list(
        scope=scope or ('/subscriptions/' + definitions_client.config.subscription_id)))
    role_dics = {i.id: i.properties.role_name for i in role_defs}
    for i in results:
        i['properties']['roleDefinitionName'] = role_dics.get(i['properties']['roleDefinitionId'], None)

    #fill in principal names
    principal_ids = set(i['properties']['principalId'] for i in results)
    if principal_ids:
        principals = _get_object_stubs(graph_client, principal_ids)
        principal_dics = {i.object_id:(i.user_principal_name or i.service_principal_names) for i in principals}
        for i in results:
            i['properties']['principalName'] = principal_dics.get(i['properties']['principalId'], None)

    return results

def delete_role_assignments(ids=None, assignee=None, role=None, #pylint: disable=too-many-arguments
                            resource_group_name=None, resource_id=None, include_inherited=False):
    assignments_client = _auth_client_factory().role_assignments
    ids = ids or []
    if ids:
        if assignee or role or resource_group_name or resource_id or include_inherited:
            raise CLIError('When assignment ids are used, other parameter values are not required')
        for i in ids:
            assignments_client.delete_by_id(i)
        return

    scope = _build_role_scope(resource_group_name, resource_id,
                              assignments_client.config.subscription_id)
    assignments = _search_role_assignments(scope, assignee, role, include_inherited,
                                           include_groups=False)

    if assignments:
        for a in assignments:
            assignments_client.delete_by_id(a.id)
    else:
        raise CLIError('No matched assignments were found to delete')

def _search_role_assignments(scope, assignee, role, include_inherited, include_groups):
    factory = _auth_client_factory()
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    assignee_object_id = None
    if assignee:
        assignee_object_id = _resolve_object_id(assignee)

    #combining filters is unsupported, so we pick the best, and do limited maunal filtering
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
            include_inherited and re.match(a.properties.scope, scope, re.I) or
            a.properties.scope.lower() == scope.lower()
            )]

        if role:
            role_id = _resolve_role_id(role, scope, definitions_client)
            assignments = [i for i in assignments if i.properties.role_definition_id == role_id]

    return assignments

def _build_role_scope(resource_group_name, resource_id, subscription_id):
    subscription_scope = '/subscriptions/' + subscription_id
    if resource_id:
        if resource_group_name:
            err = 'Resource group "{}" is redundant because resource id is supplied'
            raise CLIError(err.format(resource_group_name))
        scope = resource_id
    elif resource_group_name:
        scope = subscription_scope + '/resourceGroups/' + resource_group_name
    else:
        scope = subscription_scope
    return scope

def _resolve_role_id(role, scope, definitions_client):
    role_id = None
    try:
        uuid.UUID(role)
        role_id = role
    except ValueError:
        pass
    if not role_id: #retrieve role id
        role_defs = list(definitions_client.list(scope, "roleName eq '{}'".format(role)))
        if not role_defs:
            raise CLIError("Role '{}' doesn't exist.".format(role))
        elif len(role_defs) > 1:
            ids = [r.id for r in role_defs]
            err = "More than one roles match the given name '{}'. Please pick a value from '{}'"
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

def create_user(client, user_principal_name, display_name, password, mail_nickname=None, #pylint: disable=too-many-arguments
                immutable_id=None, force_change_password_next_login=False):
    '''
    :param mail_nickname: mail alias. default to user principal name
    '''
    mail_nickname = mail_nickname or user_principal_name.split('@')[0]
    param = UserCreateParameters(user_principal_name=user_principal_name, account_enabled=True,
                                 display_name=display_name, mail_nickname=mail_nickname,
                                 immutable_id=immutable_id,
                                 password_profile=PasswordProfile(
                                     password, force_change_password_next_login))
    return client.create(param)

create_user.__doc__ = UserCreateParameters.__doc__

def list_groups(client, display_name=None, query_filter=None):
    sub_filters = []
    if query_filter:
        sub_filters.append(query_filter)
    if display_name:
        sub_filters.append("startswith(displayName,'{}')".format(display_name))

    return client.list(filter=(' and ').join(sub_filters))

def _resolve_object_id(assignee):
    client = _graph_client_factory()
    result = None
    if assignee.find('@') >= 0: #looks like a user principal name
        result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
    if not result:
        result = list(client.service_principals.list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    if not result: #assume an object id, let us verify it
        from azure.graphrbac.models import GetObjectsParameters
        result = _get_object_stubs(client, [assignee])

    #2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise CLIError("No matches in graph database for '{}'".format(assignee))

    return result[0].object_id

def _get_object_stubs(graph_client, assignees):
    from azure.graphrbac.models import GetObjectsParameters
    params = GetObjectsParameters(include_directory_object_references=True,
                                  object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))


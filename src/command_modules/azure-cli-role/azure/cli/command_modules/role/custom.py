#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import uuid

from azure.cli._util import CLIError
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

def create_role_assignment(role, assignee, resource_group_name=None, resource_id=None):
    '''
    :param assignee: represent a user, group, or service principal.
    supported format: object id, user sign-in name, or service principal name
    :param resource_id: resource id
    '''
    assignments_client = _auth_client_factory().role_assignments
    definitions_client = _auth_client_factory().role_definitions

    if resource_id:
        if resource_group_name:
            err = 'Resource group "{}" is redundant because resource id is supplied'
            raise CLIError(err.format(resource_group_name))
        scope = resource_id
    else:
        scope = '/subscriptions/' + definitions_client.config.subscription_id
        if resource_group_name:
            scope = scope + '/resourceGroups/' + resource_group_name

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
            err = ("More than one role matches the given name '{}'. "
                   "Set 'role' to one of the unique ids from {}'")
            raise CLIError(err.format(role, ids))
        role_id = role_defs[0].id

    object_id = _get_object_id(assignee)
    properties = RoleAssignmentProperties(role_id, object_id)
    assignment_name = uuid.uuid4()
    return assignments_client.create(scope, assignment_name, properties)

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

def _get_object_id(assignee):
    client = _graph_client_factory()
    result = None
    if assignee.find('@') >= 0: #looks like a user principal name
        result = list(client.users.list(filter="userPrincipalName eq '{}'".format(assignee)))
    if not result:
        result = list(client.service_principals.list(
            filter="servicePrincipalNames/any(c:c eq '{}')".format(assignee)))
    if not result: #assume an object id, let us verify it
        from azure.graphrbac.models import GetObjectsParameters
        result = list(client.objects.get_objects_by_object_ids(
            GetObjectsParameters(include_directory_object_references=True, object_ids=[assignee])))

    #2+ matches should never happen, so we only check 'no match' here
    if not result:
        raise CLIError("No matches in graph database for '{}'".format(assignee))

    return result[0].object_id

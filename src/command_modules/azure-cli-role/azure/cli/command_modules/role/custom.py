#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
import datetime
import json
import re
import os
import uuid
from dateutil.relativedelta import relativedelta
import dateutil.parser

from azure.cli.core._util import CLIError, todict, get_file_json
import azure.cli.core._logging as _logging
from azure.cli.core.help_files import helps

from azure.cli.core.commands.client_factory import (get_mgmt_service_client,
                                                    configure_common_settings)

from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import (RoleAssignmentProperties, Permission, RoleDefinition,
                                             RoleDefinitionProperties)
from azure.graphrbac import GraphRbacManagementClient

from azure.graphrbac.models import (ApplicationCreateParameters,
                                    ApplicationUpdateParameters,
                                    PasswordCredential,
                                    KeyCredential,
                                    UserCreateParameters,
                                    PasswordProfile,
                                    ServicePrincipalCreateParameters)

logger = _logging.get_az_logger(__name__)


_CUSTOM_RULE = 'CustomRole'

def _auth_client_factory(scope=None):
    subscription_id = None
    if scope:
        matched = re.match('/subscriptions/(?P<subscription>[^/]*)/', scope)
        if matched:
            subscription_id = matched.groupdict()['subscription']
    return get_mgmt_service_client(AuthorizationManagementClient, subscription_id=subscription_id)

def _graph_client_factory(**_):
    from azure.cli.core._profile import Profile, CLOUD
    from azure.cli.core.cloud import CloudEndpoint
    profile = Profile()
    cred, _, tenant_id = profile.get_login_credentials(
        resource=CLOUD.endpoints[CloudEndpoint.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID])
    client = GraphRbacManagementClient(cred,
                                       tenant_id,
                                       base_url=CLOUD.endpoints[CloudEndpoint.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID]) # pylint: disable=line-too-long
    configure_common_settings(client)
    return client

def list_role_definitions(name=None, resource_group_name=None, scope=None,
                          custom_role_only=False):
    definitions_client = _auth_client_factory(scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    return _search_role_definitions(definitions_client, name, scope, custom_role_only)

def get_role_definition_name_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    definitions = list_role_definitions()
    return [x.properties.role_name for x in list(definitions)]

helps['role definition create'] = """
            type: command
            parameters: 
                - name: --role-definition
                  type: string
                  short-summary: 'JSON formatted string or a path to a file with such content'
            examples:
                - name: Create a role with following definition content
                  text: |
                        {
                            "Name": "Contoso On-call",
                            "Description": "Can monitor compute, network and storage, and restart virtual machines",
                            "Actions": [
                                "Microsoft.Compute/*/read",
                                "Microsoft.Compute/virtualMachines/start/action",
                                "Microsoft.Compute/virtualMachines/restart/action",
                                "Microsoft.Network/*/read",
                                "Microsoft.Storage/*/read",
                                "Microsoft.Authorization/*/read",
                                "Microsoft.Resources/subscriptions/resourceGroups/read",
                                "Microsoft.Resources/subscriptions/resourceGroups/resources/read",
                                "Microsoft.Insights/alertRules/*",
                                "Microsoft.Support/*"
                            ],
                            "AssignableScopes": ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"]
                        }

            """
def create_role_definition(role_definition):
    role_id = uuid.uuid4()
    if os.path.exists(role_definition):
        role_definition = get_file_json(role_definition)
    else:
        role_definition = json.loads(role_definition)

    #to workaround service defects, ensure property names are camel case
    names = [p for p in role_definition if p[:1].isupper()]
    for n in names:
        new_name = n[:1].lower() + n[1:]
        role_definition[new_name] = role_definition.pop(n)

    if not 'name' in role_definition:
        raise CLIError("please provide 'name'")
    if not 'assignableScopes' in role_definition:
        raise CLIError("please provide 'assignableScopes'")

    permission = Permission(actions=role_definition.get('actions', None),
                            not_actions=role_definition.get('notActions', None))
    properties = RoleDefinitionProperties(role_name=role_definition['name'],
                                          description=role_definition.get('description', None),
                                          type=_CUSTOM_RULE,
                                          assignable_scopes=role_definition['assignableScopes'],
                                          permissions=[permission])

    definition = RoleDefinition(name=role_id, properties=properties)

    definitions_client = _auth_client_factory().role_definitions
    return definitions_client.create_or_update(role_definition_id=role_id,
                                               scope=properties.assignable_scopes[0],
                                               role_definition=definition)


def delete_role_definition(name, resource_group_name=None, scope=None,
                           custom_role_only=False):
    definitions_client = _auth_client_factory(scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    roles = _search_role_definitions(definitions_client, name, scope, custom_role_only)
    for r in roles:
        definitions_client.delete(role_definition_id=r.name, scope=scope)

def _search_role_definitions(definitions_client, name, scope, custom_role_only=False):
    roles = definitions_client.list(scope, filter="roleName eq '{}'".format(name) if name else None)
    if custom_role_only:
        roles = [r for r in roles if r.properties.type == _CUSTOM_RULE]
    return roles

def create_role_assignment(role, assignee, resource_group_name=None, scope=None):
    return _create_role_assignment(role, assignee, resource_group_name, scope)

def _create_role_assignment(role, assignee, resource_group_name=None, scope=None,
                            ocp_aad_session_key=None):
    factory = _auth_client_factory(scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(assignee)
    properties = RoleAssignmentProperties(role_id, object_id)
    assignment_name = uuid.uuid4()
    custom_headers = None
    if ocp_aad_session_key:
        custom_headers = {'ocp-aad-session-key': ocp_aad_session_key}

    return assignments_client.create(scope, assignment_name, properties,
                                     custom_headers=custom_headers)

def list_role_assignments(assignee=None, role=None, resource_group_name=None,#pylint: disable=too-many-arguments
                          scope=None, include_inherited=False,
                          show_all=False, include_groups=False):
    '''
    :param include_groups: include extra assignments to the groups of which the user is a
    member(transitively). Supported only for a user principal.
    '''
    graph_client = _graph_client_factory()
    factory = _auth_client_factory(scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = None
    if show_all:
        if resource_group_name or scope:
            raise CLIError('group or scope are not required when --all is used')
        scope = None
    else:
        scope = _build_role_scope(resource_group_name, scope,
                                  definitions_client.config.subscription_id)

    assignments = _search_role_assignments(assignments_client, definitions_client,
                                           scope, assignee, role,
                                           include_inherited, include_groups)

    if not assignments:
        return []

    #fill in logic names to get things understandable.
    #it's possible that associated roles and principals were deleted, and we just do nothing.

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
        principal_dics = {i.object_id:_get_displayable_name(i) for i in principals}
        for i in results:
            i['properties']['principalName'] = principal_dics.get(i['properties']['principalId'], None)

    return results

def _get_displayable_name(graph_object):
    if graph_object.user_principal_name:
        return graph_object.user_principal_name
    elif graph_object.service_principal_names:
        return graph_object.service_principal_names[0]
    else:
        return ''

def delete_role_assignments(ids=None, assignee=None, role=None, #pylint: disable=too-many-arguments
                            resource_group_name=None, scope=None, include_inherited=False):
    factory = _auth_client_factory(scope)
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
    assignments = _search_role_assignments(assignments_client, definitions_client,
                                           scope, assignee, role, include_inherited,
                                           include_groups=False)

    if assignments:
        for a in assignments:
            assignments_client.delete_by_id(a.id)
    else:
        raise CLIError('No matched assignments were found to delete')

def _search_role_assignments(assignments_client, definitions_client,#pylint: disable=too-many-arguments
                             scope, assignee, role, include_inherited, include_groups):
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

def create_application(client, display_name, homepage, identifier_uris, #pylint: disable=too-many-arguments
                       available_to_other_tenants=False, password=None, reply_urls=None,
                       key_value=None, key_type=None, key_usage=None, start_date=None,
                       end_date=None):
    password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                         key_usage, start_date, end_date)

    app_create_param = ApplicationCreateParameters(available_to_other_tenants,
                                                   display_name,
                                                   identifier_uris,
                                                   homepage=homepage,
                                                   reply_urls=reply_urls,
                                                   key_credentials=key_creds,
                                                   password_credentials=password_creds)
    return client.create(app_create_param)

def update_application(client, identifier, display_name=None, homepage=None, identifier_uris=None,#pylint: disable=too-many-arguments
                       password=None, reply_urls=None, key_value=None, key_type=None,
                       key_usage=None, start_date=None, end_date=None):
    object_id = _resolve_application(client, identifier)
    password_creds, key_creds = _build_application_creds(password, key_value, key_type,
                                                         key_usage, start_date, end_date)

    app_patch_param = ApplicationUpdateParameters(display_name=display_name,
                                                  homepage=homepage,
                                                  identifier_uris=identifier_uris,
                                                  reply_urls=reply_urls,
                                                  key_credentials=key_creds,
                                                  password_credentials=password_creds)
    return client.patch(object_id, app_patch_param)

def show_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    return client.get(object_id)

def delete_application(client, identifier):
    object_id = _resolve_application(client, identifier)
    client.delete(object_id)

def _resolve_application(client, identifier):
    result = list(client.list(filter="identifierUris/any(s:s eq '{}')".format(identifier)))
    if not result:
        try:
            uuid.UUID(identifier)
            #it is either app id or object id, let us verify
            result = list(client.list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
            raise CLIError("Application '{}' doesn't exist".format(identifier))

    return result[0].object_id if result else identifier

def _build_application_creds(password=None, key_value=None, key_type=None,#pylint: disable=too-many-arguments
                             key_usage=None, start_date=None, end_date=None):
    if password and key_value:
        raise CLIError('specify either --password or --key-value, but not both.')

    if not start_date:
        start_date = datetime.datetime.now()
    elif isinstance(start_date, str):
        start_date = dateutil.parser.parse(start_date)

    if not end_date:
        end_date = start_date + relativedelta(years=1)
    elif isinstance(end_date, str):
        end_date = dateutil.parser.parse(end_date)#pylint: disable=redefined-variable-type

    key_type = key_type or 'AsymmetricX509Cert'
    key_usage = key_usage or 'Verify'

    password_creds = None
    key_creds = None
    if password:
        password_creds = [PasswordCredential(start_date, end_date, str(uuid.uuid4()), password)]
    elif key_value:
        key_creds = [KeyCredential(start_date, end_date, key_value, str(uuid.uuid4()),
                                   key_usage, key_type)]

    return (password_creds, key_creds)

def create_service_principal(identifier):
    return _create_service_principal(identifier)

def _create_service_principal(identifier, retain_raw_response=False):
    client = _graph_client_factory()
    try:
        uuid.UUID(identifier)
        result = list(client.applications.list(filter="appId eq '{}'".format(identifier)))
    except ValueError:
        result = list(client.applications.list(
            filter="identifierUris/any(s:s eq '{}')".format(identifier)))

    if not result: #assume we get an object id
        result = [client.applications.get(identifier)]
    app_id = result[0].app_id

    return client.service_principals.create(ServicePrincipalCreateParameters(app_id, True),
                                            raw=retain_raw_response)

def show_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    return client.get(object_id)

def delete_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    client.delete(object_id)

def _resolve_service_principal(client, identifier):
    #todo: confirm with graph team that a service principal name must be unique
    result = list(client.list(filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier)))
    if result:
        return result[0].object_id
    try:
        uuid.UUID(identifier)
        return identifier #assume an object id
    except ValueError:
        raise CLIError("service principal '{}' doesn't exist".format(identifier))

def create_service_principal_for_rbac(name=None, secret=None, years=1,
                                      scopes=None, role=None):
    '''create a service principal that can access or modify resources
    :param str name: an unique uri. If missing, the command will generate one.
    :param str secret: the secret used to login. If missing, command will generate one.
    :param str years: Years the secret will be valid.
    :param str scopes: space separated scopes the service principal's role assignment applies to.
    :param str role: role the service principal has on the resources. only use with 'resource-ids'.
    '''
    if bool(scopes) != bool(role):
        raise CLIError("'--scopes' and '--role' must be used together.")
    client = _graph_client_factory()
    start_date = datetime.datetime.now()
    app_display_name = 'azure-cli-' + start_date.strftime('%Y-%m-%d-%H-%M-%S')
    if name is None:
        name = 'http://' + app_display_name # just a valid uri, no need to exist

    end_date = start_date + relativedelta(years=years)
    secret = secret or str(uuid.uuid4())
    aad_application = create_application(client.applications, display_name=app_display_name, #pylint: disable=too-many-function-args
                                         homepage='http://'+app_display_name,
                                         identifier_uris=[name],
                                         available_to_other_tenants=False,
                                         password=secret,
                                         start_date=start_date,
                                         end_date=end_date)
    #pylint: disable=no-member
    aad_sp = _create_service_principal(aad_application.app_id, bool(scopes))
    oid = aad_sp.output.object_id if scopes else aad_sp.object_id

    if scopes:
        #It is possible the SP has not been propagated to all servers, so creating assignments
        #might fail. The reliable workaround is to call out the server where creation occurred.
        #pylint: disable=protected-access
        session_key = aad_sp.response.headers._store['ocp-aad-session-key'][1]
        for scope in scopes:
            _create_role_assignment(role, oid, None, scope, ocp_aad_session_key=session_key)

    return {
        'client_id': aad_application.app_id,
        'client_secret': secret,
        'sp_name': name,
        'tenant': client.config.tenant_id
        }

def reset_service_principal_credential(name, secret=None, years=1):
    '''reset credential, on expiration or you forget it.

    :param str name: the uri representing the name of the service principal
    :param str secret: the secret used to login. If missing, command will generate one.
    :param str years: Years the secret will be valid.
    '''
    client = _graph_client_factory()

    #pylint: disable=no-member

    #look for the existing application
    query_exp = 'identifierUris/any(x:x eq \'{}\')'.format(name)
    aad_apps = list(client.applications.list(filter=query_exp))
    if not aad_apps:
        raise CLIError('can\'t find an application matching \'{}\''.format(name))
    #no need to check 2+ matches, as app id uri is unique
    app = aad_apps[0]

    #look for the existing service principal
    query_exp = 'servicePrincipalNames/any(x:x eq \'{}\')'.format(name)
    aad_sps = list(client.service_principals.list(filter=query_exp))
    if not aad_sps:
        raise CLIError('can\'t find a service principal matching \'{}\''.format(name))

    #build a new password credential and patch it
    secret = secret or str(uuid.uuid4())
    start_date = datetime.datetime.now()
    end_date = start_date + relativedelta(years=years)
    key_id = str(uuid.uuid4())
    app_cred = PasswordCredential(start_date, end_date, key_id, secret)
    app_create_param = ApplicationUpdateParameters(password_credentials=[app_cred])

    client.applications.patch(app.object_id, app_create_param)

    return {
        'client_id': app.app_id,
        'client_secret': secret,
        'sp_name': name,
        'tenant': client.config.tenant_id
        }

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


# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import datetime
import re
import os
import uuid
from dateutil.relativedelta import relativedelta
import dateutil.parser

from azure.cli.core.util import CLIError, todict, get_file_json, shell_safe_json_parse
import azure.cli.core.azlogging as azlogging

from azure.mgmt.authorization.models import (RoleAssignmentProperties, Permission, RoleDefinition,
                                             RoleDefinitionProperties)

from azure.graphrbac.models import (ApplicationCreateParameters,
                                    ApplicationUpdateParameters,
                                    PasswordCredential,
                                    KeyCredential,
                                    UserCreateParameters,
                                    PasswordProfile,
                                    ServicePrincipalCreateParameters)

from ._client_factory import _auth_client_factory, _graph_client_factory

logger = azlogging.get_az_logger(__name__)

_CUSTOM_RULE = 'CustomRole'


def list_role_definitions(name=None, resource_group_name=None, scope=None,
                          custom_role_only=False):
    definitions_client = _auth_client_factory(scope).role_definitions
    scope = _build_role_scope(resource_group_name, scope,
                              definitions_client.config.subscription_id)
    return _search_role_definitions(definitions_client, name, scope, custom_role_only)


def get_role_definition_name_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    definitions = list_role_definitions()
    return [x.properties.role_name for x in list(definitions)]


def create_role_definition(role_definition):
    return _create_update_role_definition(role_definition, for_update=False)


def update_role_definition(role_definition):
    return _create_update_role_definition(role_definition, for_update=True)


def _create_update_role_definition(role_definition, for_update):
    definitions_client = _auth_client_factory().role_definitions
    if os.path.exists(role_definition):
        role_definition = get_file_json(role_definition)
    else:
        role_definition = shell_safe_json_parse(role_definition)

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
        role_name = matched[0].properties.role_name
        role_id = matched[0].name
    else:
        role_id = uuid.uuid4()

    if not for_update and 'assignableScopes' not in role_definition:
        raise CLIError("please provide 'assignableScopes'")

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
    roles = list(definitions_client.list(scope))
    if name:
        roles = [r for r in roles if r.name == name or r.properties.role_name == name]
    if custom_role_only:
        roles = [r for r in roles if r.properties.type == _CUSTOM_RULE]
    return roles


def create_role_assignment(role, assignee, resource_group_name=None, scope=None):
    return _create_role_assignment(role, assignee, resource_group_name, scope)


def _create_role_assignment(role, assignee, resource_group_name=None, scope=None,
                            resolve_assignee=True):
    factory = _auth_client_factory(scope)
    assignments_client = factory.role_assignments
    definitions_client = factory.role_definitions

    scope = _build_role_scope(resource_group_name, scope,
                              assignments_client.config.subscription_id)

    role_id = _resolve_role_id(role, scope, definitions_client)
    object_id = _resolve_object_id(assignee) if resolve_assignee else assignee
    properties = RoleAssignmentProperties(role_id, object_id)
    assignment_name = uuid.uuid4()
    custom_headers = None
    return assignments_client.create(scope, assignment_name, properties,
                                     custom_headers=custom_headers)


def list_role_assignments(assignee=None, role=None, resource_group_name=None,
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

    # fill in logic names to get things understandable.
    # it's possible that associated roles and principals were deleted, and we just do nothing.

    results = todict(assignments)

    # fill in role names
    role_defs = list(definitions_client.list(
        scope=scope or ('/subscriptions/' + definitions_client.config.subscription_id)))
    role_dics = {i.id: i.properties.role_name for i in role_defs}
    for i in results:
        i['properties']['roleDefinitionName'] = role_dics.get(i['properties']['roleDefinitionId'],
                                                              None)

    # fill in principal names
    principal_ids = set(i['properties']['principalId'] for i in results)
    if principal_ids:
        principals = _get_object_stubs(graph_client, principal_ids)
        principal_dics = {i.object_id: _get_displayable_name(i) for i in principals}
        for i in results:
            i['properties']['principalName'] = principal_dics.get(i['properties']['principalId'],
                                                                  None)

    return results


def _get_displayable_name(graph_object):
    if graph_object.user_principal_name:
        return graph_object.user_principal_name
    elif graph_object.service_principal_names:
        return graph_object.service_principal_names[0]
    return ''


def delete_role_assignments(ids=None, assignee=None, role=None,
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


def _search_role_assignments(assignments_client, definitions_client,
                             scope, assignee, role, include_inherited, include_groups):
    assignee_object_id = None
    if assignee:
        assignee_object_id = _resolve_object_id(assignee)

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
    if re.match(r'/subscriptions/.+/providers/Microsoft.Authorization/roleDefinitions/',
                role, re.I):
        role_id = role
    else:
        try:
            uuid.UUID(role)
            role_id = '/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(
                definitions_client.config.subscription_id, role)
        except ValueError:
            pass
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
                                     password, force_change_password_next_login))
    return client.create(param)


create_user.__doc__ = UserCreateParameters.__doc__


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


def create_application(client, display_name, homepage, identifier_uris,
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


def update_application(client, identifier, display_name=None, homepage=None,
                       identifier_uris=None, password=None, reply_urls=None, key_value=None,
                       key_type=None, key_usage=None, start_date=None, end_date=None):
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
            # it is either app id or object id, let us verify
            result = list(client.list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
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
        password_creds = [PasswordCredential(start_date, end_date, str(uuid.uuid4()), password)]
    elif key_value:
        key_creds = [KeyCredential(start_date, end_date, key_value, str(uuid.uuid4()),
                                   key_usage, key_type)]

    return (password_creds, key_creds)


def create_service_principal(identifier):
    return _create_service_principal(identifier)


def _create_service_principal(identifier, resolve_app=True):
    client = _graph_client_factory()

    if resolve_app:
        try:
            uuid.UUID(identifier)
            result = list(client.applications.list(filter="appId eq '{}'".format(identifier)))
        except ValueError:
            result = list(client.applications.list(
                filter="identifierUris/any(s:s eq '{}')".format(identifier)))

        if not result:  # assume we get an object id
            result = [client.applications.get(identifier)]
        app_id = result[0].app_id
    else:
        app_id = identifier

    return client.service_principals.create(ServicePrincipalCreateParameters(app_id, True))


def show_service_principal(client, identifier):
    object_id = _resolve_service_principal(client, identifier)
    return client.get(object_id)


def delete_service_principal(identifier):
    client = _graph_client_factory()
    sp = client.service_principals.get(_resolve_service_principal(client.service_principals, identifier))
    app_object_id = None

    # see whether we need to delete the application if it is in the same tenant
    if sp.service_principal_names:
        result = list(client.applications.list(
            filter="identifierUris/any(s:s eq '{}')".format(sp.service_principal_names[0])))
        if result:
            app_object_id = result[0].object_id

    assignments = list_role_assignments(assignee=identifier, show_all=True)
    if assignments:
        logger.warning('Removing role assignments')
        delete_role_assignments([a['id'] for a in assignments])

    if app_object_id:  # delete the application, and AAD service will automatically clean up the SP
        client.applications.delete(app_object_id)
    else:
        client.service_principals.delete(sp.object_id)


def _resolve_service_principal(client, identifier):
    # todo: confirm with graph team that a service principal name must be unique
    result = list(client.list(filter="servicePrincipalNames/any(c:c eq '{}')".format(identifier)))
    if result:
        return result[0].object_id
    try:
        uuid.UUID(identifier)
        return identifier  # assume an object id
    except ValueError:
        raise CLIError("service principal '{}' doesn't exist".format(identifier))


def _process_service_principal_creds(years, app_start_date, app_end_date, cert, create_cert,
                                     password, keyvault):

    if not any((cert, create_cert, password, keyvault)):
        # 1 - Simplest scenario. Use random password
        return str(uuid.uuid4()), None, None, None, None

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
            _create_self_signed_cert_with_keyvault(
                years, keyvault, cert)
    elif keyvault:
        import base64
        from azure.cli.core._profile import CLOUD
        # 6 - Use existing cert from KeyVault
        kv_client = _get_keyvault_client()
        vault_base = 'https://{}{}/'.format(keyvault, CLOUD.suffixes.keyvault_dns)
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


def create_service_principal_for_rbac(
        # pylint:disable=too-many-statements,too-many-locals, too-many-branches
        name=None, password=None, years=None,
        create_cert=False, cert=None,
        scopes=None, role='Contributor',
        expanded_view=None, skip_assignment=False, keyvault=None):
    import time
    import pytz

    graph_client = _graph_client_factory()
    role_client = _auth_client_factory().role_assignments
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

    app_start_date = datetime.datetime.now(pytz.utc)
    app_end_date = app_start_date + relativedelta(years=years or 1)

    app_display_name = app_display_name or ('azure-cli-' +
                                            app_start_date.strftime('%Y-%m-%d-%H-%M-%S'))
    if name is None:
        name = 'http://' + app_display_name  # just a valid uri, no need to exist

    password, public_cert_string, cert_file, cert_start_date, cert_end_date = \
        _process_service_principal_creds(years, app_start_date, app_end_date, cert, create_cert,
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
            aad_sp = _create_service_principal(app_id, resolve_app=False)
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
                    _create_role_assignment(role, sp_oid, None, scope, resolve_assignee=False)
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

    if expanded_view:
        logger.warning("'--expanded-view' is deprecating and will be removed in a future release. "
                       "You can get the same information using 'az cloud show'")
        from azure.cli.core._profile import Profile
        profile = Profile()
        result = profile.get_expanded_subscription_info(scopes[0].split('/')[2] if scopes else None,
                                                        app_id, password)
    else:
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


def _get_keyvault_client():
    from azure.cli.core._profile import Profile
    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication

    def _get_token(server, resource, scope):  # pylint: disable=unused-argument
        return Profile().get_login_credentials(resource)[0]._token_retriever()  # pylint: disable=protected-access

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


def _create_self_signed_cert_with_keyvault(years, keyvault, keyvault_cert_name):  # pylint: disable=too-many-locals
    from azure.cli.core._profile import CLOUD
    import base64
    import time

    kv_client = _get_keyvault_client()
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
    vault_base_url = 'https://{}{}/'.format(keyvault, CLOUD.suffixes.keyvault_dns)
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


def reset_service_principal_credential(name, password=None, create_cert=False,
                                       cert=None, years=None, keyvault=None):
    import pytz
    client = _graph_client_factory()

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

    app_start_date = datetime.datetime.now(pytz.utc)
    app_end_date = app_start_date + relativedelta(years=years or 1)

    # build a new password/cert credential and patch it
    public_cert_string = None
    cert_file = None

    password, public_cert_string, cert_file, cert_start_date, cert_end_date = \
        _process_service_principal_creds(years, app_start_date, app_end_date, cert, create_cert,
                                         password, keyvault)

    app_start_date, app_end_date, cert_start_date, cert_end_date = \
        _validate_app_dates(app_start_date, app_end_date, cert_start_date, cert_end_date)

    app_creds = None
    cert_creds = None

    if password:
        app_creds = [
            PasswordCredential(
                start_date=app_start_date,
                end_date=app_end_date,
                key_id=str(uuid.uuid4()),
                value=password
            )
        ]

    if public_cert_string:
        cert_creds = [
            KeyCredential(
                start_date=app_start_date,
                end_date=app_end_date,
                value=public_cert_string,
                key_id=str(uuid.uuid4()),
                usage='Verify',
                type='AsymmetricX509Cert'
            )
        ]

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


def _resolve_object_id(assignee):
    client = _graph_client_factory()
    result = None
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


def _get_object_stubs(graph_client, assignees):
    from azure.graphrbac.models import GetObjectsParameters
    params = GetObjectsParameters(include_directory_object_references=True, object_ids=assignees)
    return list(graph_client.objects.get_objects_by_object_ids(params))

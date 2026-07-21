# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import get_enum_type, get_three_state_flag
from azure.cli.core.commands.validators import validate_file_or_dict
# from azure.cli.core.profiles import ResourceType


from azure.cli.command_modules.role._completers import get_role_definition_name_completion_list
from azure.cli.command_modules.role._validators import validate_group, validate_cert, VARIANT_GROUP_ID_ARGS

name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')

JSON_PROPERTY_HELP = "Should be JSON file path or in-line JSON string. See examples for details"


# pylint: disable=too-many-statements
def load_arguments(self, _):
    with self.argument_context('ad') as c:
        c.argument('owner_object_id', help="owner's object id")
        c.argument('show_mine', action='store_true', help='list entities owned by the current user')
        c.argument('include_all', options_list='--all', action='store_true',
                   help='list all entities, expect long delay if under a big organization')

    with self.argument_context('ad app') as c:
        c.ignore('_subscription')
        # https://learn.microsoft.com/en-us/graph/api/resources/application?view=graph-rest-1.0
        c.argument('app_id', help='application id')
        c.argument('application_object_id', options_list=('--object-id',))
        c.argument('display_name', help='the display name of the application')

        c.argument('identifier', options_list=['--id'], help='identifier uri, application id, or object id')
        c.argument('identifier_uris', nargs='+',
                   help='space-separated values. '
                        'Also known as App ID URI, this value is set when an application is used as a resource app. '
                        'The identifierUris acts as the prefix for the scopes you\'ll reference in your API\'s code, '
                        'and it must be globally unique. You can use the default value provided, which is in the '
                        'form `api://<application-client-id>`, or specify a more readable URI like '
                        'https://contoso.com/api.')

        c.argument('is_fallback_public_client', arg_type=get_three_state_flag(),
                   help="Specifies the fallback application type as public client, such as an installed application "
                        "running on a mobile device. The default value is false which means the fallback application "
                        "type is confidential client such as a web app.")
        c.argument('service_management_reference',
                   help='References application or service contact information from a Service or Asset Management '
                        'database.')
        c.argument('sign_in_audience',
                   arg_type=get_enum_type(['AzureADMyOrg', 'AzureADMultipleOrgs', 'AzureADandPersonalMicrosoftAccount',
                                           'PersonalMicrosoftAccount']),
                   help='Specifies the Microsoft accounts that are supported for the current application.')

        # api
        # https://learn.microsoft.com/en-us/graph/api/resources/apiapplication?view=graph-rest-1.0
        c.argument('requested_access_token_version', arg_group='api', type=int,
                   help='Specifies the access token version expected by this resource. This changes the version and '
                        'format of the JWT produced independent of the endpoint or client used to request the access '
                        'token.')

        # web
        # https://learn.microsoft.com/en-us/graph/api/resources/webapplication?view=graph-rest-1.0
        c.argument('web_home_page_url', arg_group='web', help='Home page or landing page of the application.')
        c.argument('web_redirect_uris', arg_group='web', nargs='+',
                   help='Space-separated values. '
                        'Specifies the URLs where user tokens are sent for sign-in, or the redirect URIs '
                        'where OAuth 2.0 authorization codes and access tokens are sent.')
        c.argument('enable_id_token_issuance', arg_group='web',
                   arg_type=get_three_state_flag(),
                   help='Specifies whether this web application can request an ID token using the OAuth 2.0 '
                        'implicit flow.')
        c.argument('enable_access_token_issuance', arg_group='web',
                   arg_type=get_three_state_flag(),
                   help='Specifies whether this web application can request an access token using the OAuth 2.0 '
                        'implicit flow.')

        # publicClient
        # https://learn.microsoft.com/en-us/graph/api/resources/publicclientapplication?view=graph-rest-1.0
        c.argument('public_client_redirect_uris', arg_group='publicClient', nargs='+',
                   help='Space-separated values. '
                        'Specifies the URLs where user tokens are sent for sign-in, or the redirect URIs '
                        'where OAuth 2.0 authorization codes and access tokens are sent.')

        # keyCredential
        # https://learn.microsoft.com/en-us/graph/api/resources/keycredential?view=graph-rest-1.0
        c.argument('start_date', arg_group='keyCredential',
                   help="Date or datetime at which credentials become valid (e.g. '2017-01-01T01:00:00+00:00' or "
                        "'2017-01-01'). Default value is current time")
        c.argument('end_date', arg_group='keyCredential',
                   help="Date or datetime after which credentials expire (e.g. '2017-12-31T11:59:59+00:00' or "
                        "'2017-12-31'). Default value is one year after current time")
        c.argument('key_value', arg_group='keyCredential',
                   help='the value for the key credentials associated with the application')
        # Even in `az ad app update`, key_type and key_usage need to have default values if key_value is specified
        c.argument('key_type', arg_group='keyCredential',
                   help='the type of the key credentials associated with the application',
                   arg_type=get_enum_type(['AsymmetricX509Cert', 'Password', 'Symmetric'],
                                          default='AsymmetricX509Cert'))
        c.argument('key_usage', arg_group='keyCredential',
                   help='the usage of the key credentials associated with the application.',
                   arg_type=get_enum_type(['Sign', 'Verify'], default='Verify'))
        c.argument('key_display_name', arg_group='keyCredential',
                   help="Friendly name for the key.")

        # JSON properties
        c.argument('required_resource_accesses', arg_group='JSON property', type=validate_file_or_dict,
                   help="Specifies the resources that the application needs to access. This property also specifies "
                        "the set of delegated permissions and application roles that it needs for each of those "
                        "resources. This configuration of access to the required resources drives the consent "
                        "experience. " + JSON_PROPERTY_HELP)
        c.argument('app_roles', arg_group='JSON property', type=validate_file_or_dict,
                   help="The collection of roles assigned to the application. With app role assignments, these roles "
                        "can be assigned to users, groups, or service principals associated with other applications. " +
                        JSON_PROPERTY_HELP)
        c.argument('optional_claims', arg_group='JSON property', type=validate_file_or_dict,
                   help="Application developers can configure optional claims in their Microsoft Entra applications to "
                        "specify the claims that are sent to their application by the Microsoft security token "
                        "service. For more information, see https://learn.microsoft.com/azure/active-directory/develop"
                        "/active-directory-optional-claims. " + JSON_PROPERTY_HELP)

    with self.argument_context('ad app owner list') as c:
        c.argument('identifier', options_list=['--id'], help='identifier uri, application id, or object id of the application')

    with self.argument_context('ad app permission') as c:
        # https://learn.microsoft.com/en-us/graph/api/resources/requiredresourceaccess
        c.argument('api',
                   help='requiredResourceAccess.resourceAppId - '
                        'The unique identifier for the resource that the application requires access to. '
                        'This should be equal to the appId declared on the target resource application.')
        # https://learn.microsoft.com/en-us/graph/api/resources/resourceaccess
        c.argument('api_permissions', nargs='+',
                   help='Space-separated list of {id}={type}. '
                        "{id} is resourceAccess.id - The unique identifier for one of the oauth2PermissionScopes or "
                        'appRole instances that the resource application exposes. '
                        "{type} is resourceAccess.type - Specifies whether the id property references an "
                        'oauth2PermissionScopes or an appRole. The possible values are: Scope (for OAuth 2.0 '
                        'permission scopes) or Role (for app roles).')

    with self.argument_context('ad app permission grant') as c:
        c.argument('identifier', options_list=['--id, --client-id'],
                   help='The id of the client service principal for the application which is authorized to act on '
                        'behalf of a signed-in user when accessing an API.')
        c.argument('scope', nargs='*',
                   help='A space-separated list of the claim values for delegated permissions which should be included '
                        'in access tokens for the resource application (the API). '
                        'For example, openid User.Read GroupMember.Read.All. '
                        'Each claim value should match the value field of one of the delegated permissions defined by '
                        'the API, listed in the oauth2PermissionScopes property of the resource service principal.')
        c.argument('consent_type', arg_type=get_enum_type(["AllPrincipals", "Principal"]), default="AllPrincipals",
                   help="Indicates whether authorization is granted for the client application to impersonate all "
                        "users or only a specific user. 'AllPrincipals' indicates authorization to impersonate all "
                        "users. 'Principal' indicates authorization to impersonate a specific user. Consent on behalf "
                        "of all users can be granted by an administrator. Non-admin users may be authorized to consent "
                        "on behalf of themselves in some cases, for some delegated permissions.")
        c.argument('principal_id',
                   help='The id of the user on behalf of whom the client is authorized to access the resource, '
                        "when consentType is 'Principal'. If consentType is 'AllPrincipals' this value is null. "
                        "Required when consentType is 'Principal'.")
        c.argument('api', options_list=['--api, --resource-id'],
                   help='The id of the resource service principal to which access is authorized. This identifies the '
                        'API which the client is authorized to attempt to call on behalf of a signed-in user.')

    with self.argument_context('ad app permission list-grants') as c:
        c.argument('show_resource_name', options_list=['--show-resource-name', '-r'],
                   arg_type=get_three_state_flag(), help="show resource's display name")

    with self.argument_context('ad app permission delete') as c:
        # `=<type>` is not needed.
        c.argument('api_permissions', nargs='+', help='Specify `ResourceAccess.id` - The unique identifier for one of the OAuth2Permission or AppRole instances that the resource application exposes. Space-separated list of `<resource-access-id>`.')

    with self.argument_context('ad app permission list') as c:
        c.argument('identifier', options_list=['--id'], help='identifier uri, application id, or object id of the associated application')

    with self.argument_context('ad sp') as c:
        c.ignore('_subscription')
        c.argument('identifier', options_list=['--id'], help='service principal name, or object id')

    with self.argument_context('ad sp create') as c:
        c.argument('identifier', options_list=['--id'], help='identifier uri, application id, or object id of the associated application')

    with self.argument_context('ad sp create-for-rbac') as c:
        c.argument('display_name', options_list=['--display-name', '--name', '-n'],
                   help='Display name of the service principal. If not present, default to azure-cli-%Y-%m-%d-%H-%M-%S '
                        'where the suffix is the time of creation.')
        c.argument('create_password', arg_type=get_three_state_flag(), arg_group='Credential',
                   help='Create a password credential (secret) on the the application. This is the default behavior. '
                        'Set this argument to false to disable creating password credential.')
        c.argument('scopes', nargs='+',
                   help="Space-separated list of scopes the service principal's role assignment applies to. e.g., "
                        "subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, "
                        "/subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM")
        c.argument('role', completer=get_role_definition_name_completion_list,
                   help='Role of the service principal.')
        c.argument('skip_assignment', arg_type=get_three_state_flag(),
                   deprecate_info=c.deprecate(target='--skip-assignment', hide=True), help='No-op.')
        c.argument('show_auth_in_json', options_list=['--sdk-auth', '--json-auth'],
                   deprecate_info=c.deprecate(target='--sdk-auth'),
                   help='Output service principal credential along with cloud endpoints in JSON format. ',
                   arg_type=get_three_state_flag())
        c.argument('service_management_reference',
                   help='Set the serviceManagementReference property of the created application. '
                        'Reference application or service contact information from a Service or Asset Management '
                        'database.')

    with self.argument_context('ad sp owner list') as c:
        c.argument('identifier', options_list=['--id'], help='service principal name, or object id or the service principal')

    for item in ['ad app credential reset', 'ad sp credential reset', 'ad sp create-for-rbac']:
        with self.argument_context(item) as c:
            # general credential arguments
            c.argument('years', type=int, default=None, arg_group='Credential',
                       help='Number of years for which the credentials will be valid. Default: 1 year')
            c.argument('append', action='store_true', arg_group='Credential',
                       help='Append the new credential instead of overwriting.')
            c.argument('end_date', default=None, arg_group='Credential',
                       help="Finer grain of expiry time if '--years' is insufficient, e.g. '2020-12-31T11:59:59+00:00' "
                            "or '2299-12-31'")

            # keyCredential arguments
            c.argument('cert', arg_group='keyCredential', validator=validate_cert,
                       help='Certificate to use for credentials. When used with `--keyvault,`, indicates the name of the '
                            'cert to use or create. Otherwise, supply a PEM or DER formatted public certificate string. '
                            'Use `@{path}` to load from a file. Do not include the private key.')
            c.argument('create_cert', arg_group='keyCredential', action='store_true',
                       help='Create a self-signed certificate to use for the credential. Only the current OS user has '
                            'read/write permission to this certificate. Use with `--keyvault` to create the certificate in '
                            'Key Vault. Otherwise, a certificate will be created locally.')
            c.argument('keyvault', arg_group='keyCredential',
                       help='Name or ID of a KeyVault to use for creating or retrieving certificates.')

    # --display-name in `ad sp create-for-rbac` is for the sp, not credential, so we only apply it to `credential reset`
    # commands.
    for item in ['ad app credential reset', 'ad sp credential reset']:
        with self.argument_context(item) as c:
            c.argument('display_name', arg_group='Credential',
                       help="Friendly name for the credential.")

    for item in ['ad app credential list', 'ad app credential delete',
                 'ad sp credential list', 'ad sp credential delete']:
        with self.argument_context(item) as c:
            c.argument('key_id', help='credential key id')
            c.argument('cert', action='store_true', help='Operate on certificate credentials')

    with self.argument_context('ad app federated-credential') as c:
        c.argument('app_identifier', options_list=['--id'],
                   help="Application's appId, identifierUri, or id (formerly known as objectId)")
        c.argument('federated_identity_credential_id_or_name', options_list=['--federated-credential-id'],
                   help='ID or name of the federated identity credential')
        c.argument('parameters', type=validate_file_or_dict,
                   help='Parameters for creating federated identity credential. ' + JSON_PROPERTY_HELP)

    with self.argument_context('ad') as c:
        c.argument('display_name', help='object\'s display name or its prefix')
        c.argument('identifier_uri', help='graph application identifier, must be in uri format')
        c.argument('spn', help='service principal name')
        c.argument('upn', help='user principal name, e.g. john.doe@contoso.com')
        c.argument('query_filter', options_list=['--filter'], help='OData filter, e.g. --filter "displayname eq \'test\' and servicePrincipalType eq \'Application\'"')

    with self.argument_context('ad user') as c:
        c.ignore('_subscription')
        c.argument('mail_nickname', help='mail alias. Defaults to user principal name')
        c.argument('account_enabled', arg_type=get_three_state_flag(), help='enable the user account')
        c.argument('password', help='user password')
        c.argument('upn_or_object_id', options_list=['--id'],
                   help='The object ID or principal name of the user for which to get information')
        c.argument('force_change_password_next_sign_in', arg_type=get_three_state_flag(),
                   help='If the user must change her password on the next login.')

    with self.argument_context('ad user create') as c:
        c.argument('immutable_id',
                   help="This property is used to associate an on-premises Active Directory user account to their "
                        "Microsoft Entra user object. This property must be specified when creating a new user account "
                        "in the Graph if you're using a federated domain for the user's userPrincipalName (UPN) "
                        "property. NOTE: The $ and _ characters can't be used when specifying this property.")
        c.argument('user_principal_name',
                   help="The user principal name (someuser@contoso.com). It must contain one of the verified domains "
                        "for the tenant.")

    with self.argument_context('ad user get-member-groups') as c:
        c.argument('security_enabled_only', arg_type=get_three_state_flag(),
                   help='true to specify that only security groups that the entity is a member of should be returned; '
                        'false to specify that all groups and directory roles that the entity is a member of should be '
                        'returned.')

    group_help_msg = "group's object id or display name(prefix also works if there is a unique match)"
    with self.argument_context('ad group') as c:
        c.ignore('_subscription')
        for arg in VARIANT_GROUP_ID_ARGS:
            c.argument(arg, options_list=['--group', '-g'], validator=validate_group, help=group_help_msg)

    with self.argument_context('ad group create') as c:
        c.argument('mail_nickname', help='Mail nickname')
        c.argument('force', arg_type=get_three_state_flag(),
                   help='always create a new group instead of updating the one with same display and mail nickname')
        c.argument('description', help='Group description')

    with self.argument_context('ad group show') as c:
        c.extra('cmd')

    member_id_help_msg = 'The object ID of the contact, group, user, or service principal'
    with self.argument_context('ad group get-member-groups') as c:
        c.argument('security_enabled_only', arg_type=get_three_state_flag(),
                   help='true to specify that only security groups that the entity is a member of should be returned; '
                        'false to specify that all groups and directory roles that the entity is a member of should be '
                        'returned.')
        c.extra('cmd')

    # with self.argument_context('ad group member add') as c:
    #     c.argument('url', options_list='--member-id', validator=validate_member_id, help=member_id_help_msg)

    for item in ['member add', 'member check', 'member list', 'member remove', 'delete']:
        with self.argument_context('ad group {}'.format(item)) as c:
            c.extra('cmd')

    with self.argument_context('ad group member') as c:
        c.argument('member_object_id', options_list='--member-id', help=member_id_help_msg)

    with self.argument_context('ad signed-in-user') as c:
        c.ignore('_subscription')
        c.argument('object_type', options_list=['--type', '-t'], help='object type filter, e.g. "application", "servicePrincipal"  "group", etc')

    with self.argument_context('role') as c:
        c.argument('scope', help='scope at which the role assignment or definition applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
        c.argument('resource_group_name', options_list=['--resource-group', '-g'], help='use it only if the role or assignment was added at the level of a resource group')

    with self.argument_context('role assignment') as c:
        c.argument('role', help='role name or id', completer=get_role_definition_name_completion_list)
        c.argument('show_all', options_list=['--all'], action='store_true', help='show all assignments under the current subscription')
        c.argument('include_inherited', action='store_true', help='include assignments applied on parent scopes')
        c.argument('can_delegate', action='store_true', help='when set, the assignee will be able to create further role assignments to the same role')
        c.argument('assignee', help='represent a user, group, or service principal. supported format: object id, user sign-in name, or service principal name')
        c.argument('assignee_object_id',
                   help="The assignee's object ID (also known as principal ID). "
                        "Use this argument instead of '--assignee' to bypass Microsoft Graph query in case "
                        "the logged-in account has no permission or the machine has no network access to query "
                        "Microsoft Graph.")
        c.argument('ids', nargs='+', help='space-separated role assignment ids')
        c.argument('description', is_preview=True, help='Description of role assignment.')
        c.argument('condition', is_preview=True, help='Condition under which the user can be granted permission.')
        c.argument('condition_version', is_preview=True, help='Version of the condition syntax. If --condition is specified without --condition-version, default to 2.0.')
        c.argument('assignment_name', name_arg_type,
                   help='A GUID for the role assignment. It must be unique and different for each role assignment. If omitted, a new GUID is generated.')

    with self.argument_context('role assignment list') as c:
        c.argument('fill_principal_name', arg_type=get_three_state_flag(),
                   help="Query Microsoft Graph to get the assignee's userPrincipalName (for user), "
                        "servicePrincipalNames (for service principal) or displayName (for group), then fill "
                        "principalName property with it. "
                        "If the logged-in account has no permission or the machine has no network access to query "
                        "Microsoft Graph, set this flag to false to avoid warning or error.")
        c.argument('fill_role_definition_name', arg_type=get_three_state_flag(),
                   help="Fill roleDefinitionName property in addition to roleDefinitionId. This operation is "
                        "expensive. If you encounter performance issue, set this flag to false.")
        c.argument('include_groups', action='store_true',
                   help='Include extra assignments to the groups of which the user is a member (transitively).')

    time_help = 'The {} of the query in the format of %Y-%m-%dT%H:%M:%SZ, e.g. 2000-12-31T12:59:59Z. Defaults to {}'
    with self.argument_context('role assignment list-changelogs') as c:
        c.argument('start_time', help=time_help.format('start time', '1 Hour prior to the current time'))
        c.argument('end_time', help=time_help.format('end time', 'the current time'))

    with self.argument_context('role assignment create') as c:
        # PrincipalType = self.get_models('PrincipalType', resource_type=ResourceType.MGMT_AUTHORIZATION)

        # A temporary fix for https://github.com/Azure/azure-cli/issues/11594
        # As only 'User', 'Group' or 'ServicePrincipal' are allowed values, the REST spec contains invalid values
        # (like MSI) which are used only internally by the service. So hide them.
        # https://github.com/Azure/azure-rest-api-specs/blob/962013a1cf9bf5b87e3aad75a14c7dd620acda62/specification/authorization/resource-manager/Microsoft.Authorization/preview/2020-04-01-preview/authorization-RoleAssignmentsCalls.json#L508-L522
        from enum import Enum

        class PrincipalType(str, Enum):
            user = "User"
            group = "Group"
            service_principal = "ServicePrincipal"
            foreign_group = "ForeignGroup"

        c.argument('assignee_principal_type', arg_type=get_enum_type(PrincipalType),
                   help='use with --assignee-object-id to avoid errors caused by propagation latency in Microsoft Graph')

    with self.argument_context('role assignment update') as c:
        c.argument('role_assignment',
                   help='Description of an existing role assignment as JSON, or a path to a file containing a '
                        'JSON description.')

    with self.argument_context('role assignment delete') as c:
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Currently no-op.')

    with self.argument_context('role definition') as c:
        c.argument('custom_role_only', arg_type=get_three_state_flag(), help='custom roles only(vs. build-in ones)')
        c.argument('role_definition', help="json formatted content which defines the new role.")

    with self.argument_context('role definition list') as c:
        c.argument('name', arg_type=name_arg_type, completer=get_role_definition_name_completion_list,
                   help="Matches the role definition's name (GUID) or roleName (e.g. 'Reader') property. "
                        "If a GUID is provided, for better performance, use `az role definition show` command.")

    with self.argument_context('role definition show') as c:
        c.argument('name', arg_type=name_arg_type, help="The role definition's name (GUID)")
        c.argument('role_id', options_list=['--id'],
                   help='The fully qualified role definition ID. Use the format, '
                        '/subscriptions/{guid}/providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId} '
                        'for subscription level role definitions, or '
                        '/providers/Microsoft.Authorization/roleDefinitions/{roleDefinitionId} '
                        'for tenant level role definitions.')

    with self.argument_context('role definition delete') as c:
        c.argument('name', arg_type=name_arg_type, completer=get_role_definition_name_completion_list,
                   help="Matches the role definition's name (GUID) or roleName (e.g. 'Reader') property.")

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path
from copy import deepcopy
from enum import Enum

from azure.cli.core._session import ACCOUNT
from azure.cli.core.azclierror import AuthenticationError
from azure.cli.core.cloud import get_active_cloud, set_cloud_subscription
from azure.cli.core.util import in_cloud_console, can_launch_browser
from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)

# Names below are used by azure-xplat-cli to persist account information into
# ~/.azure/azureProfile.json or osx/keychainer or windows secure storage,
# which azure-cli will share.
# Please do not rename them unless you know what you are doing.
_IS_DEFAULT_SUBSCRIPTION = 'isDefault'
_SUBSCRIPTION_ID = 'id'
_SUBSCRIPTION_NAME = 'name'
# Tenant of the token which is used to list the subscription
_TENANT_ID = 'tenantId'
# Home tenant of the subscription, which maps to tenantId in 'Subscriptions - List REST API'
# https://docs.microsoft.com/en-us/rest/api/resources/subscriptions/list
_HOME_TENANT_ID = 'homeTenantId'
_MANAGED_BY_TENANTS = 'managedByTenants'
_USER_ENTITY = 'user'
_USER_NAME = 'name'
_CLIENT_ID = 'clientId'
_CLOUD_SHELL_ID = 'cloudShellID'
_SUBSCRIPTIONS = 'subscriptions'
_INSTALLATION_ID = 'installationId'
_ENVIRONMENT_NAME = 'environmentName'
_STATE = 'state'
_USER_TYPE = 'type'
_USER = 'user'
_SERVICE_PRINCIPAL = 'servicePrincipal'
_SERVICE_PRINCIPAL_CERT_SN_ISSUER_AUTH = 'useCertSNIssuerAuth'
_TOKEN_ENTRY_USER_ID = 'userId'
_TOKEN_ENTRY_TOKEN_TYPE = 'tokenType'

_TENANT_LEVEL_ACCOUNT_NAME = 'N/A(tenant level account)'

_SYSTEM_ASSIGNED_IDENTITY = 'systemAssignedIdentity'
_USER_ASSIGNED_IDENTITY = 'userAssignedIdentity'
_ASSIGNED_IDENTITY_INFO = 'assignedIdentityInfo'

_AZ_LOGIN_MESSAGE = "Please run 'az login' to setup account."


def load_subscriptions(cli_ctx, all_clouds=False, refresh=False):
    profile = Profile(cli_ctx=cli_ctx)
    if refresh:
        profile.refresh_accounts()
    subscriptions = profile.load_cached_subscriptions(all_clouds)
    return subscriptions


def _detect_adfs_authority(authority_url, tenant):
    """Prepare authority and tenant for Azure Identity with ADFS support.
    If `authority_url` ends with '/adfs', `tenant` will be set to 'adfs'. For example:
        'https://adfs.redmond.azurestack.corp.microsoft.com/adfs'
        -> ('https://adfs.redmond.azurestack.corp.microsoft.com/', 'adfs')
    """
    authority_url = authority_url.rstrip('/')

    if authority_url.endswith('/adfs'):
        authority_url = authority_url[:-len('/adfs')]
        # The custom tenant is discarded in ADFS environment
        tenant = 'adfs'

    return authority_url, tenant


def get_credential_types(cli_ctx):
    class CredentialType(Enum):  # pylint: disable=too-few-public-methods
        cloud = get_active_cloud(cli_ctx)
        management = cli_ctx.cloud.endpoints.management
        rbac = cli_ctx.cloud.endpoints.active_directory_graph_resource_id

    return CredentialType


def _get_cloud_console_token_endpoint():
    return os.environ.get('MSI_ENDPOINT')


def _attach_token_tenant(subscription, tenant):
    """Attach the token tenant ID to the subscription as tenant_id, so that CLI knows which token should be used
    to access the subscription.

    This function supports multiple APIs:
      - v2016_06_01's Subscription doesn't have tenant_id
      - v2019_11_01's Subscription has tenant_id representing the home tenant ID. It will mapped to home_tenant_id
    """
    if hasattr(subscription, "tenant_id"):
        setattr(subscription, 'home_tenant_id', subscription.tenant_id)
    setattr(subscription, 'tenant_id', tenant)


# pylint: disable=too-many-lines,too-many-instance-attributes,unused-argument
class Profile:

    def __init__(self, cli_ctx=None, storage=None):
        """Class to manage CLI's accounts (profiles) and identities (credentials).

        :param cli_ctx: The CLI context
        :param storage: A dict to store accounts, by default persisted to ~/.azure/azureProfile.json as JSON
        """
        from azure.cli.core import get_default_cli

        self.cli_ctx = cli_ctx or get_default_cli()
        self._storage = storage or ACCOUNT
        self._authority = self.cli_ctx.cloud.endpoints.active_directory

        from .auth.util import resource_to_scopes
        self._arm_scope = resource_to_scopes(self.cli_ctx.cloud.endpoints.active_directory_resource_id)

    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def login(self,
              interactive,
              username,
              password,
              is_service_principal,
              tenant,
              scopes=None,
              use_device_code=False,
              allow_no_subscriptions=False,
              use_cert_sn_issuer=None,
              **kwargs):
        """
        For service principal, `password` is a dict returned by ServicePrincipalAuth.build_credential
        """
        if not scopes:
            scopes = self._arm_scope

        identity = _create_identity_instance(self.cli_ctx, self._authority, tenant_id=tenant)

        user_identity = None
        if interactive:
            if not use_device_code and not can_launch_browser():
                logger.info('No web browser is available. Fall back to device code.')
                use_device_code = True

            if use_device_code:
                user_identity = identity.login_with_device_code(scopes=scopes, **kwargs)
            else:
                user_identity = identity.login_with_auth_code(scopes=scopes, **kwargs)
        else:
            if not is_service_principal:
                user_identity = identity.login_with_username_password(username, password, scopes=scopes, **kwargs)
            else:
                identity.login_with_service_principal(username, password, scopes=scopes)

        # We have finished login. Let's find all subscriptions.
        if user_identity:
            username = user_identity['username']

        subscription_finder = SubscriptionFinder(self.cli_ctx)

        # Create credentials
        if user_identity:
            credential = identity.get_user_credential(username)
        else:
            credential = identity.get_service_principal_credential(username)

        if tenant:
            subscriptions = subscription_finder.find_using_specific_tenant(tenant, credential)
        else:
            subscriptions = subscription_finder.find_using_common_tenant(username, credential)

        if not subscriptions and not allow_no_subscriptions:
            raise CLIError("No subscriptions found for {}.".format(username))

        if allow_no_subscriptions:
            t_list = [s.tenant_id for s in subscriptions]
            bare_tenants = [t for t in subscription_finder.tenants if t not in t_list]
            tenant_accounts = self._build_tenant_level_accounts(bare_tenants)
            subscriptions.extend(tenant_accounts)
            if not subscriptions:
                return []

        consolidated = self._normalize_properties(username, subscriptions,
                                                  is_service_principal, bool(use_cert_sn_issuer))

        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def login_with_managed_identity(self, identity_id=None, allow_no_subscriptions=None):
        from azure.cli.core.auth.msal_authentication import ManagedIdentityCredential
        import jwt

        cred = None

        if identity_id:
            from azure.mgmt.core.tools import is_valid_resource_id
            if is_valid_resource_id(identity_id):
                cred = ManagedIdentityCredential(mi_res_id=identity_id)
                identity_type = ManagedIdentityAuth.id_type_resource_id
            else:
                authenticated = False
                # Use trial and error approach to determine the ID type - client ID or object ID
                try:
                    cred = ManagedIdentityCredential(client_id=identity_id)
                    cred.get_token(*self._arm_scope)
                    identity_type = ManagedIdentityAuth.id_type_client_id
                    authenticated = True
                except AuthenticationError as ex:
                    if 'Identity not found' in str(ex):
                        logger.info('Sniff: not a client ID')
                    else:
                        raise

                if not authenticated:
                    try:
                        cred = ManagedIdentityCredential(object_id=identity_id)
                        cred.get_token(*self._arm_scope)
                        identity_type = ManagedIdentityAuth.id_type_object_id
                        authenticated = True
                    except AuthenticationError as ex:
                        if 'Identity not found' in str(ex):
                            logger.info('Sniff: not an object ID')
                        else:
                            raise

                if not authenticated:
                    raise CLIError('Failed to connect to managed identity, check your managed identity ID.')
        else:
            cred = ManagedIdentityCredential()
            identity_type = ManagedIdentityAuth.id_type_no_id

        access_token = cred.get_token(*self._arm_scope)

        logger.info('Managed identity token was retrieved. Now trying to initialize local accounts...')
        decoded = jwt.decode(access_token.token, algorithms=['RS256'], options={"verify_signature": False})
        tenant = decoded['tid']
        resource_id = decoded['xms_mirid']
        # user.name is the managed identity type - systemAssignedIdentity or userAssignedIdentity.
        # It should be deduced from whether /Microsoft.ManagedIdentity/userAssignedIdentities exists in xms_mirid
        # claim. It shouldn't be deduced from whether identity_id is provided. This is because if identity_id
        # is not provided, the token can be for either a system-assigned identity or a user-assigned identity.
        # https://github.com/Azure/azure-cli/issues/13188
        user = _USER_ASSIGNED_IDENTITY if '/Microsoft.ManagedIdentity/userAssignedIdentities' in resource_id \
            else _SYSTEM_ASSIGNED_IDENTITY

        subscription_finder = SubscriptionFinder(self.cli_ctx)
        subscriptions = subscription_finder.find_using_specific_tenant(tenant, cred)

        # user.assignedIdentityInfo is the ID info: MSI, MSIClient-{id}, MSIObject-{id}, MSIResource-{id}
        base_name = ('{}-{}'.format(identity_type, identity_id) if identity_id else identity_type)

        if not subscriptions:
            if allow_no_subscriptions:
                subscriptions = self._build_tenant_level_accounts([tenant])
            else:
                raise CLIError('No access was configured for the managed identity, hence no subscriptions were found. '
                               "If this is expected, use '--allow-no-subscriptions' to have tenant level access.")

        consolidated = self._normalize_properties(user, subscriptions, is_service_principal=True,
                                                  user_assigned_identity_id=base_name)
        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def login_in_cloud_shell(self):
        import jwt
        from .auth.msal_authentication import CloudShellCredential

        cred = CloudShellCredential()
        access_token = cred.get_token(*self._arm_scope)
        logger.info('Cloud Shell token was retrieved. Now trying to initialize local accounts...')
        decode = jwt.decode(access_token.token, algorithms=['RS256'], options={"verify_signature": False})
        tenant = decode['tid']

        subscription_finder = SubscriptionFinder(self.cli_ctx)
        subscriptions = subscription_finder.find_using_specific_tenant(tenant, cred)
        if not subscriptions:
            raise CLIError('No subscriptions were found in the cloud shell')
        user = decode.get('unique_name', 'N/A')

        consolidated = self._normalize_properties(user, subscriptions, is_service_principal=False)
        for s in consolidated:
            s[_USER_ENTITY][_CLOUD_SHELL_ID] = True
        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def logout(self, user_or_sp):
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        result = [x for x in subscriptions
                  if user_or_sp.lower() == x[_USER_ENTITY][_USER_NAME].lower()]
        subscriptions = [x for x in subscriptions if x not in result]
        self._storage[_SUBSCRIPTIONS] = subscriptions

        identity = _create_identity_instance(self.cli_ctx, self._authority)
        identity.logout_user(user_or_sp)
        identity.logout_service_principal(user_or_sp)

    def logout_all(self):
        self._storage[_SUBSCRIPTIONS] = []

        identity = _create_identity_instance(self.cli_ctx, self._authority)
        identity.logout_all_users()
        identity.logout_all_service_principal()

    def get_login_credentials(self, resource=None, subscription_id=None, aux_subscriptions=None, aux_tenants=None):
        """Get a CredentialAdaptor instance to be used with both Track 1 and Track 2 SDKs.
        Only one of aux_subscriptions or aux_tenants can be provided.

        :param resource: The resource ID to acquire an access token. Only provide it for Track 1 SDKs.
        :param subscription_id: The primary key to select the account from `az account list`. If not provided, use
            the account with isDefault=true.
        :param aux_subscriptions: Auxiliary subscriptions for cross-tenant authentication.
        :param aux_tenants: Auxiliary tenants for cross-tenant authentication.
        """
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id

        if aux_tenants and aux_subscriptions:
            raise CLIError("Please specify only one of aux_subscriptions and aux_tenants, not both")

        account = self.get_subscription(subscription_id)

        managed_identity_type, managed_identity_id = Profile._parse_managed_identity_info(account)
        external_credentials = []

        if managed_identity_type:
            # managed identity
            cred = ManagedIdentityAuth.credential_factory(managed_identity_type, managed_identity_id)

        elif in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            # Cloud Shell
            from .auth.msal_authentication import CloudShellCredential
            cred = CloudShellCredential()

        else:
            # user and service principal
            cred = self._create_credential(account)

            # Create external credentials
            external_tenants = []
            if aux_tenants:
                external_tenants = [tenant for tenant in aux_tenants if tenant != account[_TENANT_ID]]
            if aux_subscriptions:
                ext_subs = [aux_sub for aux_sub in aux_subscriptions if aux_sub != subscription_id]
                for ext_sub in ext_subs:
                    sub = self.get_subscription(ext_sub)
                    if sub[_TENANT_ID] != account[_TENANT_ID]:
                        external_tenants.append(sub[_TENANT_ID])

            for external_tenant in external_tenants:
                external_credentials.append(self._create_credential(account, external_tenant))

        # Make the credential compatible with Track 1 SDK
        from azure.cli.core.auth.credential_adaptor import CredentialAdaptor
        cred = CredentialAdaptor(cred,
                                 auxiliary_credentials=external_credentials,
                                 resource=resource)

        return (cred,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def get_raw_token(self, resource=None, scopes=None, subscription=None, tenant=None):
        # Convert resource to scopes
        if resource and not scopes:
            from .auth.util import resource_to_scopes
            scopes = resource_to_scopes(resource)

        # Use ARM as the default scopes
        if not scopes:
            scopes = self._arm_scope

        if subscription and tenant:
            raise CLIError("Please specify only one of subscription and tenant, not both")

        account = self.get_subscription(subscription)

        managed_identity_type, managed_identity_id = Profile._parse_managed_identity_info(account)

        if managed_identity_type:
            # managed identity
            if tenant:
                raise CLIError("Tenant shouldn't be specified for managed identity account")
            cred = ManagedIdentityAuth.credential_factory(managed_identity_type, managed_identity_id)

        elif in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            # Cloud Shell
            if tenant:
                raise CLIError("Tenant shouldn't be specified for Cloud Shell account")
            from .auth.msal_authentication import CloudShellCredential
            cred = CloudShellCredential()

        else:
            # user and service principal
            cred = self._create_credential(account, tenant_id=tenant)

        sdk_token = cred.get_token(*scopes)

        # Convert epoch int 'expires_on' to datetime string 'expiresOn' for backward compatibility
        # WARNING: expiresOn is deprecated and will be removed in future release.
        import datetime
        expiresOn = datetime.datetime.fromtimestamp(sdk_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f")

        token_entry = {
            'accessToken': sdk_token.token,
            'expires_on': sdk_token.expires_on,  # epoch int, like 1605238724
            'expiresOn': expiresOn  # datetime string, like "2020-11-12 13:50:47.114324"
        }

        # (tokenType, accessToken, tokenEntry)
        creds = 'Bearer', sdk_token.token, token_entry

        # (cred, subscription, tenant)
        return (creds,
                None if tenant else str(account[_SUBSCRIPTION_ID]),
                str(tenant if tenant else account[_TENANT_ID]))

    def _normalize_properties(self, user, subscriptions, is_service_principal, cert_sn_issuer_auth=None,
                              user_assigned_identity_id=None):
        consolidated = []
        for s in subscriptions:
            subscription_dict = {
                _SUBSCRIPTION_ID: s.id.rpartition('/')[2],
                _SUBSCRIPTION_NAME: s.display_name,
                _STATE: s.state,
                _USER_ENTITY: {
                    _USER_NAME: user,
                    _USER_TYPE: _SERVICE_PRINCIPAL if is_service_principal else _USER
                },
                _IS_DEFAULT_SUBSCRIPTION: False,
                _TENANT_ID: s.tenant_id,
                _ENVIRONMENT_NAME: self.cli_ctx.cloud.name
            }

            if subscription_dict[_SUBSCRIPTION_NAME] != _TENANT_LEVEL_ACCOUNT_NAME:
                _transform_subscription_for_multiapi(s, subscription_dict)

            consolidated.append(subscription_dict)

            if cert_sn_issuer_auth:
                consolidated[-1][_USER_ENTITY][_SERVICE_PRINCIPAL_CERT_SN_ISSUER_AUTH] = True
            if user_assigned_identity_id:
                consolidated[-1][_USER_ENTITY][_ASSIGNED_IDENTITY_INFO] = user_assigned_identity_id

        return consolidated

    def _build_tenant_level_accounts(self, tenants):
        result = []
        for t in tenants:
            s = self._new_account()
            s.id = '/subscriptions/' + t
            s.subscription = t
            s.tenant_id = t
            s.display_name = _TENANT_LEVEL_ACCOUNT_NAME
            result.append(s)
        return result

    def _new_account(self):
        """Build an empty Subscription which will be used as a tenant account.
        API version doesn't matter as only specified attributes are preserved by _normalize_properties."""
        from azure.cli.core.profiles import ResourceType, get_sdk
        SubscriptionType = get_sdk(self.cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS,
                                   'Subscription', mod='models')
        s = SubscriptionType()
        s.state = 'Enabled'
        return s

    def _set_subscriptions(self, new_subscriptions, merge=True, secondary_key_name=None):

        def _get_key_name(account, secondary_key_name):
            return (account[_SUBSCRIPTION_ID] if secondary_key_name is None
                    else '{}-{}'.format(account[_SUBSCRIPTION_ID], account[secondary_key_name]))

        def _match_account(account, subscription_id, secondary_key_name, secondary_key_val):
            return (account[_SUBSCRIPTION_ID] == subscription_id and
                    (secondary_key_val is None or account[secondary_key_name] == secondary_key_val))

        existing_ones = self.load_cached_subscriptions(all_clouds=True)
        active_one = next((x for x in existing_ones if x.get(_IS_DEFAULT_SUBSCRIPTION)), None)
        active_subscription_id = active_one[_SUBSCRIPTION_ID] if active_one else None
        active_secondary_key_val = active_one[secondary_key_name] if (active_one and secondary_key_name) else None
        active_cloud = self.cli_ctx.cloud
        default_sub_id = None

        # merge with existing ones
        if merge:
            dic = {_get_key_name(x, secondary_key_name): x for x in existing_ones}
        else:
            dic = {}

        dic.update((_get_key_name(x, secondary_key_name), x) for x in new_subscriptions)
        subscriptions = list(dic.values())
        if subscriptions:
            if active_one:
                new_active_one = next(
                    (x for x in new_subscriptions if _match_account(x, active_subscription_id, secondary_key_name,
                                                                    active_secondary_key_val)), None)

                for s in subscriptions:
                    s[_IS_DEFAULT_SUBSCRIPTION] = False

                if not new_active_one:
                    new_active_one = Profile._pick_working_subscription(new_subscriptions)
            else:
                new_active_one = Profile._pick_working_subscription(new_subscriptions)

            new_active_one[_IS_DEFAULT_SUBSCRIPTION] = True
            default_sub_id = new_active_one[_SUBSCRIPTION_ID]

            set_cloud_subscription(self.cli_ctx, active_cloud.name, default_sub_id)
        self._storage[_SUBSCRIPTIONS] = subscriptions

    @staticmethod
    def _pick_working_subscription(subscriptions):
        s = next((x for x in subscriptions if x.get(_STATE) == 'Enabled'), None)
        return s or subscriptions[0]

    def is_tenant_level_account(self):
        return self.get_subscription()[_SUBSCRIPTION_NAME] == _TENANT_LEVEL_ACCOUNT_NAME

    def set_active_subscription(self, subscription):  # take id or name
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        active_cloud = self.cli_ctx.cloud
        subscription = subscription.lower()
        result = [x for x in subscriptions
                  if subscription in [x[_SUBSCRIPTION_ID].lower(),
                                      x[_SUBSCRIPTION_NAME].lower()] and
                  x[_ENVIRONMENT_NAME] == active_cloud.name]

        if len(result) != 1:
            raise CLIError("The subscription of '{}' {} in cloud '{}'.".format(
                subscription, "doesn't exist" if not result else 'has more than one match', active_cloud.name))

        for s in subscriptions:
            s[_IS_DEFAULT_SUBSCRIPTION] = False
        result[0][_IS_DEFAULT_SUBSCRIPTION] = True

        set_cloud_subscription(self.cli_ctx, active_cloud.name, result[0][_SUBSCRIPTION_ID])
        self._storage[_SUBSCRIPTIONS] = subscriptions

    def load_cached_subscriptions(self, all_clouds=False):
        subscriptions = self._storage.get(_SUBSCRIPTIONS) or []
        active_cloud = self.cli_ctx.cloud
        cached_subscriptions = [sub for sub in subscriptions
                                if all_clouds or sub[_ENVIRONMENT_NAME] == active_cloud.name]
        # use deepcopy as we don't want to persist these changes to file.
        return deepcopy(cached_subscriptions)

    def get_current_account_user(self):
        try:
            active_account = self.get_subscription()
        except CLIError:
            raise CLIError('There are no active accounts.')

        return active_account[_USER_ENTITY][_USER_NAME]

    def get_subscription(self, subscription=None):  # take id or name
        subscriptions = self.load_cached_subscriptions()
        if not subscriptions:
            raise CLIError(_AZ_LOGIN_MESSAGE)

        result = [x for x in subscriptions if (
            not subscription and x.get(_IS_DEFAULT_SUBSCRIPTION) or
            subscription and subscription.lower() in [x[_SUBSCRIPTION_ID].lower(), x[
                _SUBSCRIPTION_NAME].lower()])]
        if not result and subscription:
            raise CLIError("Subscription '{}' not found. "
                           "Check the spelling and casing and try again.".format(subscription))
        if not result and not subscription:
            raise CLIError("No subscription found. Run 'az account set' to select a subscription.")
        if len(result) > 1:
            raise CLIError("Multiple subscriptions with the name '{}' found. "
                           "Specify the subscription ID.".format(subscription))
        return result[0]

    def get_subscription_id(self, subscription=None):  # take id or name
        return self.get_subscription(subscription)[_SUBSCRIPTION_ID]

    @staticmethod
    def _parse_managed_identity_info(account):
        identity_info = account[_USER_ENTITY].get(_ASSIGNED_IDENTITY_INFO)
        user_name = account[_USER_ENTITY].get(_USER_NAME)

        if user_name in [_SYSTEM_ASSIGNED_IDENTITY, _USER_ASSIGNED_IDENTITY]:
            # We no longer support login profile created by versions < 2.0.51, which uses _SUBSCRIPTION_NAME as
            # _ASSIGNED_IDENTITY_INFO.
            # https://github.com/Azure/azure-cli/pull/7744
            if not identity_info:
                raise CLIError(f'{_ASSIGNED_IDENTITY_INFO} property is missing from the current account. '
                               'Please run `az login --identity`.')
            parts = identity_info.split('-', 1)
            return parts[0], (None if len(parts) <= 1 else parts[1])
        return None, None

    def _create_credential(self, account, tenant_id=None):
        """Create a user or service principal credential object driven by MSAL.

        :param account: Azure CLI account from `az account list`
        :param tenant_id: If not None, override tenantId from 'account'
        :return:
        """
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        tenant_id = tenant_id if tenant_id else account[_TENANT_ID]
        identity = _create_identity_instance(self.cli_ctx, self._authority, tenant_id=tenant_id)

        # User
        if user_type == _USER:
            return identity.get_user_credential(username_or_sp_id)

        # Service Principal
        if user_type == _SERVICE_PRINCIPAL:
            return identity.get_service_principal_credential(username_or_sp_id)

        raise ValueError('Invalid user type.')

    def refresh_accounts(self):
        subscriptions = self.load_cached_subscriptions()
        to_refresh = subscriptions

        subscription_finder = SubscriptionFinder(self.cli_ctx)
        refreshed_list = set()
        result = []
        for s in to_refresh:
            user_name = s[_USER_ENTITY][_USER_NAME]
            if user_name in refreshed_list:
                continue
            refreshed_list.add(user_name)
            is_service_principal = (s[_USER_ENTITY][_USER_TYPE] == _SERVICE_PRINCIPAL)
            tenant = s[_TENANT_ID]
            subscriptions = []
            try:
                identity_credential = self._create_credential(s, tenant)
                if is_service_principal:
                    subscriptions = subscription_finder.find_using_specific_tenant(tenant, identity_credential)
                else:
                    # pylint: disable=protected-access
                    subscriptions = subscription_finder.find_using_common_tenant(user_name, identity_credential)
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("Refreshing for '%s' failed with an error '%s'. The existing accounts were not "
                               "modified. You can run 'az login' later to explicitly refresh them", user_name, ex)
                result += deepcopy([r for r in to_refresh if r[_USER_ENTITY][_USER_NAME] == user_name])
                continue

            if not subscriptions:
                if s[_SUBSCRIPTION_NAME] == _TENANT_LEVEL_ACCOUNT_NAME:
                    subscriptions = self._build_tenant_level_accounts([s[_TENANT_ID]])

                if not subscriptions:
                    continue

            consolidated = self._normalize_properties(user_name,
                                                      subscriptions,
                                                      is_service_principal)
            result += consolidated

        self._set_subscriptions(result, merge=False)

    def get_sp_auth_info(self, subscription_id=None, name=None, password=None, cert_file=None):
        """Generate a JSON for --sdk-auth argument when used in:
            - az ad sp create-for-rbac --sdk-auth
        """
        from collections import OrderedDict
        account = self.get_subscription(subscription_id)

        # is the credential created through command like 'create-for-rbac'?
        result = OrderedDict()

        result['clientId'] = name
        if password:
            result['clientSecret'] = password
        else:
            result['clientCertificate'] = cert_file
        result['subscriptionId'] = subscription_id or account[_SUBSCRIPTION_ID]

        result[_TENANT_ID] = account[_TENANT_ID]
        endpoint_mappings = OrderedDict()  # use OrderedDict to control the output sequence
        endpoint_mappings['active_directory'] = 'activeDirectoryEndpointUrl'
        endpoint_mappings['resource_manager'] = 'resourceManagerEndpointUrl'
        endpoint_mappings['active_directory_graph_resource_id'] = 'activeDirectoryGraphResourceId'
        endpoint_mappings['sql_management'] = 'sqlManagementEndpointUrl'
        endpoint_mappings['gallery'] = 'galleryEndpointUrl'
        endpoint_mappings['management'] = 'managementEndpointUrl'
        from azure.cli.core.cloud import CloudEndpointNotSetException
        for e in endpoint_mappings:
            try:
                result[endpoint_mappings[e]] = getattr(get_active_cloud(self.cli_ctx).endpoints, e)
            except CloudEndpointNotSetException:
                result[endpoint_mappings[e]] = None
        return result

    def get_installation_id(self):
        installation_id = self._storage.get(_INSTALLATION_ID)
        if not installation_id:
            try:
                # We share the same installationId with Azure Powershell. So try to load installationId from PSH file
                # Contact: DEV@Nanxiang Liu, PM@Damien Caro
                shared_installation_id_file = os.path.join(self.cli_ctx.config.config_dir,
                                                           'AzureRmContextSettings.json')
                with open(shared_installation_id_file, 'r', encoding='utf-8-sig') as f:
                    import json
                    content = json.load(f)
                    installation_id = content['Settings']['InstallationId']
            except Exception as ex:  # pylint: disable=broad-except
                logger.debug('Failed to load installationId from AzureRmSurvey.json. %s', str(ex))
                import uuid
                installation_id = str(uuid.uuid1())
            self._storage[_INSTALLATION_ID] = installation_id
        return installation_id


class ManagedIdentityAuth:  # pylint: disable=too-few-public-methods

    # String constants defined in this class are saved to azureProfile.json, so this class shouldn't be put
    # under auth/identity.py
    id_type_no_id = 'MSI'  # Not necessarily system-assigned. It merely means no ID is provided.
    id_type_client_id = 'MSIClient'
    id_type_object_id = 'MSIObject'
    id_type_resource_id = 'MSIResource'

    @staticmethod
    def credential_factory(identity_type, identity_id):
        from azure.cli.core.auth.msal_authentication import ManagedIdentityCredential
        if identity_type == ManagedIdentityAuth.id_type_no_id:
            return ManagedIdentityCredential()
        if identity_type == ManagedIdentityAuth.id_type_client_id:
            return ManagedIdentityCredential(client_id=identity_id)
        if identity_type == ManagedIdentityAuth.id_type_object_id:
            return ManagedIdentityCredential(object_id=identity_id)
        if identity_type == ManagedIdentityAuth.id_type_resource_id:
            return ManagedIdentityCredential(mi_res_id=identity_id)
        raise ValueError("Unrecognized managed identity account type '{}'".format(identity_type))


class SubscriptionFinder:
    # An ARM client. It finds subscriptions for a user or service principal. It shouldn't do any
    # authentication work, but only find subscriptions
    def __init__(self, cli_ctx):
        self.cli_ctx = cli_ctx
        self.secret = None
        self._arm_resource_id = cli_ctx.cloud.endpoints.active_directory_resource_id
        self._authority = self.cli_ctx.cloud.endpoints.active_directory
        self.tenants = []

    def find_using_common_tenant(self, username, credential=None):
        # pylint: disable=too-many-statements
        all_subscriptions = []
        empty_tenants = []
        mfa_tenants = []

        client = self._create_subscription_client(credential)
        tenants = client.tenants.list()

        for t in tenants:
            tenant_id = t.tenant_id
            # display_name is available since /tenants?api-version=2018-06-01,
            # not available in /tenants?api-version=2016-06-01
            if not hasattr(t, 'display_name'):
                t.display_name = None

            t.tenant_id_name = tenant_id
            if t.display_name:
                # e.g. '72f988bf-86f1-41af-91ab-2d7cd011db47 Microsoft'
                t.tenant_id_name = "{} '{}'".format(tenant_id, t.display_name)

            logger.info("Finding subscriptions under tenant %s", t.tenant_id_name)

            identity = _create_identity_instance(self.cli_ctx, self._authority, tenant_id=tenant_id)

            specific_tenant_credential = identity.get_user_credential(username)

            try:
                subscriptions = self.find_using_specific_tenant(tenant_id, specific_tenant_credential)
            except AuthenticationError as ex:
                # because user creds went through the 'common' tenant, the error here must be
                # tenant specific, like the account was disabled. For such errors, we will continue
                # with other tenants.
                msg = ex.error_msg
                if 'AADSTS50076' in msg:
                    # The tenant requires MFA and can't be accessed with home tenant's refresh token
                    mfa_tenants.append(t)
                else:
                    logger.warning("Failed to authenticate %s due to error '%s'", t.tenant_id_name, ex)
                continue

            if not subscriptions:
                empty_tenants.append(t)

            # When a subscription can be listed by multiple tenants, only the first appearance is retained
            for sub_to_add in subscriptions:
                add_sub = True
                for sub_to_compare in all_subscriptions:
                    if sub_to_add.subscription_id == sub_to_compare.subscription_id:
                        logger.warning("Subscription %s '%s' can be accessed from tenants %s(default) and %s. "
                                       "To select a specific tenant when accessing this subscription, "
                                       "use 'az login --tenant TENANT_ID'.",
                                       sub_to_add.subscription_id, sub_to_add.display_name,
                                       sub_to_compare.tenant_id, sub_to_add.tenant_id)
                        add_sub = False
                        break
                if add_sub:
                    all_subscriptions.append(sub_to_add)

        # Show warning for empty tenants
        if empty_tenants:
            logger.warning("The following tenants don't contain accessible subscriptions. "
                           "Use 'az login --allow-no-subscriptions' to have tenant level access.")
            for t in empty_tenants:
                logger.warning("%s", t.tenant_id_name)

        # Show warning for MFA tenants
        if mfa_tenants:
            logger.warning("The following tenants require Multi-Factor Authentication (MFA). "
                           "Use 'az login --tenant TENANT_ID' to explicitly login to a tenant.")
            for t in mfa_tenants:
                logger.warning("%s", t.tenant_id_name)
        return all_subscriptions

    def find_using_specific_tenant(self, tenant, credential):
        client = self._create_subscription_client(credential)
        subscriptions = client.subscriptions.list()
        all_subscriptions = []
        for s in subscriptions:
            _attach_token_tenant(s, tenant)
            all_subscriptions.append(s)
        self.tenants.append(tenant)
        return all_subscriptions

    def _create_subscription_client(self, credential):
        from azure.cli.core.profiles import ResourceType, get_api_version
        from azure.cli.core.profiles._shared import get_client_class
        from azure.cli.core.commands.client_factory import _prepare_mgmt_client_kwargs_track2

        client_type = get_client_class(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
        if client_type is None:
            from azure.cli.core.azclierror import CLIInternalError
            raise CLIInternalError("Unable to get '{}' in profile '{}'"
                                   .format(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS, self.cli_ctx.cloud.profile))
        api_version = get_api_version(self.cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
        client_kwargs = _prepare_mgmt_client_kwargs_track2(self.cli_ctx, credential)

        client = client_type(credential, api_version=api_version,
                             base_url=self.cli_ctx.cloud.endpoints.resource_manager,
                             **client_kwargs)
        return client


def _transform_subscription_for_multiapi(s, s_dict):
    """
    Transforms properties from Subscriptions - List 2019-06-01 and later to the subscription dict.

    :param s: subscription object
    :param s_dict: subscription dict
    """
    if hasattr(s, 'home_tenant_id'):
        s_dict[_HOME_TENANT_ID] = s.home_tenant_id
    if hasattr(s, 'managed_by_tenants'):
        if s.managed_by_tenants is None:
            s_dict[_MANAGED_BY_TENANTS] = None
        else:
            s_dict[_MANAGED_BY_TENANTS] = [{_TENANT_ID: t.tenant_id} for t in s.managed_by_tenants]


def _create_identity_instance(cli_ctx, *args, **kwargs):
    """Lazily import and create Identity instance to avoid unnecessary imports."""
    from .auth.identity import Identity
    from .util import should_encrypt_token_cache
    encrypt = should_encrypt_token_cache(cli_ctx)

    # EXPERIMENTAL: Use core.use_msal_http_cache=False to turn off MSAL HTTP cache.
    use_msal_http_cache = cli_ctx.config.getboolean('core', 'use_msal_http_cache', fallback=True)

    # PREVIEW: On Windows, use core.allow_broker=true to use broker (WAM) for authentication.
    allow_broker = cli_ctx.config.getboolean('core', 'allow_broker', fallback=False)
    from .telemetry import set_broker_info
    set_broker_info(allow_broker=allow_broker)

    return Identity(*args, encrypt=encrypt, use_msal_http_cache=use_msal_http_cache, allow_broker=allow_broker,
                    **kwargs)

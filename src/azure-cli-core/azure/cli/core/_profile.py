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
from azure.cli.core.auth.credential_adaptor import CredentialAdaptor
from azure.cli.core.util import in_cloud_console, can_launch_browser, is_github_codespaces
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

# More information on the token tenant. Maps to properties in 'Tenants - List' REST API
# https://learn.microsoft.com/en-us/rest/api/resources/tenants/list
_TENANT_DEFAULT_DOMAIN = 'tenantDefaultDomain'  # defaultDomain
_TENANT_DISPLAY_NAME = 'tenantDisplayName'  # displayName

# Home tenant of the subscription. Maps to tenantId in 'Subscriptions - List' REST API
# https://learn.microsoft.com/en-us/rest/api/resources/subscriptions/list
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


def _attach_token_tenant(subscription, tenant, tenant_id_description=None):
    """Attach the token tenant information to the subscription. CLI uses tenant_id to know which token should be used
    to access the subscription.

    This function supports multiple APIs:
      - v2016_06_01: Subscription doesn't have tenant_id
      - v2022_12_01:
        - Subscription has tenant_id representing the home tenant ID, mapped to home_tenant_id
        - TenantIdDescription has default_domain, mapped to tenant_default_domain
        - TenantIdDescription has display_name, mapped to tenant_display_name
    """
    if hasattr(subscription, "tenant_id"):
        setattr(subscription, 'home_tenant_id', subscription.tenant_id)
    setattr(subscription, 'tenant_id', tenant)

    # Attach tenant_default_domain, if available
    if tenant_id_description and hasattr(tenant_id_description, "default_domain"):
        setattr(subscription, 'tenant_default_domain', tenant_id_description.default_domain)
    # Attach display_name, if available
    if tenant_id_description and hasattr(tenant_id_description, "display_name"):
        setattr(subscription, 'tenant_display_name', tenant_id_description.display_name)


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
              show_progress=False,
              claims_challenge=None):
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

            if not use_device_code and is_github_codespaces():
                logger.info('GitHub Codespaces is detected. Fall back to device code.')
                use_device_code = True

            if use_device_code:
                user_identity = identity.login_with_device_code(scopes=scopes, claims_challenge=claims_challenge)
            else:
                user_identity = identity.login_with_auth_code(scopes=scopes, claims_challenge=claims_challenge)
        else:
            if not is_service_principal:
                user_identity = identity.login_with_username_password(username, password, scopes=scopes)
            else:
                identity.login_with_service_principal(username, password, scopes=scopes)

        # We have finished login. Let's find all subscriptions.
        if show_progress:
            message = ('Retrieving subscriptions for the selection...' if tenant else
                       'Retrieving tenants and subscriptions for the selection...')
            print(f"\n{message}")

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

    def login_with_managed_identity(self, client_id=None, object_id=None, resource_id=None,
                                    allow_no_subscriptions=None):
        import jwt
        from .auth.constants import ACCESS_TOKEN

        identity_id_type, identity_id_value = ManagedIdentityAuth.parse_ids(
            client_id=client_id, object_id=object_id, resource_id=resource_id)
        cred = ManagedIdentityAuth.credential_factory(identity_id_type, identity_id_value)
        token = cred.acquire_token(self._arm_scope)[ACCESS_TOKEN]
        logger.info('Managed identity: token was retrieved. Now trying to initialize local accounts...')
        decode = jwt.decode(token, algorithms=['RS256'], options={"verify_signature": False})
        tenant = decode['tid']

        subscription_finder = SubscriptionFinder(self.cli_ctx)
        subscriptions = subscription_finder.find_using_specific_tenant(tenant, cred)
        base_name = ('{}-{}'.format(identity_id_type, identity_id_value) if identity_id_value else identity_id_type)
        user = _USER_ASSIGNED_IDENTITY if identity_id_value else _SYSTEM_ASSIGNED_IDENTITY
        if not subscriptions:
            if allow_no_subscriptions:
                subscriptions = self._build_tenant_level_accounts([tenant])
            else:
                raise CLIError('No access was configured for the managed identity, hence no subscriptions were found. '
                               "If this is expected, use '--allow-no-subscriptions' to have tenant level access.")

        consolidated = self._normalize_properties(user, subscriptions, is_service_principal=True,
                                                  assigned_identity_info=base_name)
        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def login_in_cloud_shell(self):
        import jwt
        from .auth.msal_credentials import CloudShellCredential
        from .auth.constants import ACCESS_TOKEN

        cred = CloudShellCredential()
        token = cred.acquire_token(self._arm_scope)[ACCESS_TOKEN]
        logger.info('Cloud Shell token was retrieved. Now trying to initialize local accounts...')
        decode = jwt.decode(token, algorithms=['RS256'], options={"verify_signature": False})
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
        # The order of below steps matter! We must
        #   1. Remove the account from MSAL token cache and SP store
        #   2. Remove the account from CLI profile
        # This way, if step 1 fails, CLI still keeps track of the account. Otherwise, if we do the
        # reverse and step 1 fails, CLI will lose track of the account.

        # Step 1: Remove the account from MSAL token cache and SP store (SP only)
        # We can't distinguish whether user_or_sp is a user or SP, so try both
        identity = _create_identity_instance(self.cli_ctx, self._authority)
        identity.logout_user(user_or_sp)
        identity.logout_service_principal(user_or_sp)

        # Step 2: Remove the account from CLI profile
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        result = [x for x in subscriptions
                  if user_or_sp.lower() == x[_USER_ENTITY][_USER_NAME].lower()]
        subscriptions = [x for x in subscriptions if x not in result]
        self._storage[_SUBSCRIPTIONS] = subscriptions

    def logout_all(self):
        self._storage[_SUBSCRIPTIONS] = []

        identity = _create_identity_instance(self.cli_ctx, self._authority)
        identity.logout_all_users()
        identity.logout_all_service_principal()

    def get_login_credentials(self, subscription_id=None, aux_subscriptions=None, aux_tenants=None,
                              sdk_credential=True):
        """Get a credential compatible with Track 2 SDK."""
        if aux_tenants and aux_subscriptions:
            raise CLIError("Please specify only one of aux_subscriptions and aux_tenants, not both")

        account = self.get_subscription(subscription_id)

        managed_identity_type, managed_identity_id = Profile._parse_managed_identity_account(account)
        external_credentials = None
        if in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            # Cloud Shell
            from .auth.msal_credentials import CloudShellCredential
            cred = CloudShellCredential()

        elif managed_identity_type:
            # managed identity
            cred = ManagedIdentityAuth.credential_factory(managed_identity_type, managed_identity_id)

        else:
            # user and service principal
            external_tenants = []
            if aux_tenants:
                external_tenants = [tenant for tenant in aux_tenants if tenant != account[_TENANT_ID]]
            if aux_subscriptions:
                ext_subs = [aux_sub for aux_sub in aux_subscriptions if aux_sub != subscription_id]
                for ext_sub in ext_subs:
                    sub = self.get_subscription(ext_sub)
                    if sub[_TENANT_ID] != account[_TENANT_ID]:
                        external_tenants.append(sub[_TENANT_ID])

            cred = self._create_credential(account)
            external_credentials = []
            for external_tenant in external_tenants:
                external_credentials.append(self._create_credential(account, tenant_id=external_tenant))

        # Wrapping the credential with CredentialAdaptor makes it compatible with SDK.
        cred_result = CredentialAdaptor(cred, auxiliary_credentials=external_credentials) if sdk_credential else cred

        return (cred_result,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def get_raw_token(self, resource=None, scopes=None, subscription=None, tenant=None, credential_out=None):
        # credential_out is only used by unit tests to inspect the credential. Do not use it!
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

        managed_identity_type, managed_identity_id = Profile._parse_managed_identity_account(account)

        non_current_tenant_template = ("For {} account, getting access token for non-current tenants is not "
                                       "supported. The specified tenant must be the current tenant "
                                       f"{account[_TENANT_ID]}")
        if in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            # Cloud Shell
            if tenant and tenant != account[_TENANT_ID]:
                raise CLIError(non_current_tenant_template.format('Cloud Shell'))
            from .auth.msal_credentials import CloudShellCredential
            cred = CloudShellCredential()

        elif managed_identity_type:
            # managed identity
            if tenant and tenant != account[_TENANT_ID]:
                raise CLIError(non_current_tenant_template.format('managed identity'))
            cred = ManagedIdentityAuth.credential_factory(managed_identity_type, managed_identity_id)
            if credential_out:
                credential_out['credential'] = cred

        else:
            cred = self._create_credential(account, tenant_id=tenant)

        msal_token = cred.acquire_token(scopes)
        # Convert epoch int 'expires_on' to datetime string 'expiresOn' for backward compatibility
        # WARNING: expiresOn is deprecated and will be removed in future release.
        import datetime
        from .auth.util import now_timestamp
        from .auth.constants import EXPIRES_IN, ACCESS_TOKEN
        expires_on = now_timestamp() + msal_token[EXPIRES_IN]
        expiresOn = datetime.datetime.fromtimestamp(expires_on).strftime("%Y-%m-%d %H:%M:%S.%f")

        token_entry = {
            'accessToken': msal_token[ACCESS_TOKEN],
            'expires_on': expires_on,  # epoch int, like 1605238724
            'expiresOn': expiresOn  # datetime string, like "2020-11-12 13:50:47.114324"
        }

        # Build a tuple of (token_type, token, token_entry)
        token_tuple = 'Bearer', msal_token[ACCESS_TOKEN], token_entry

        # Return a tuple of (token_tuple, subscription, tenant)
        return (token_tuple,
                None if tenant else str(account[_SUBSCRIPTION_ID]),
                str(tenant if tenant else account[_TENANT_ID]))

    def get_msal_token(self, scopes, data):
        """Get VM SSH certificate. DO NOT use it for other purposes. To get an access token, use get_raw_token instead.
        """
        credential, _, _ = self.get_login_credentials(sdk_credential=False)
        from .auth.constants import ACCESS_TOKEN
        certificate_string = credential.acquire_token(scopes, data=data)[ACCESS_TOKEN]
        # The first value used to be username, but it is no longer used.
        return None, certificate_string

    def _normalize_properties(self, user, subscriptions, is_service_principal, cert_sn_issuer_auth=None,
                              assigned_identity_info=None):
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
            if assigned_identity_info:
                consolidated[-1][_USER_ENTITY][_ASSIGNED_IDENTITY_INFO] = assigned_identity_info

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
    def _parse_managed_identity_account(account):
        # user.name will always exist, so we check it first.
        # user.userAssignedIdentity will only exist if user.name is systemAssignedIdentity or userAssignedIdentity
        user_name = account[_USER_ENTITY][_USER_NAME]
        if user_name == _SYSTEM_ASSIGNED_IDENTITY:
            # The account contains:
            #   "name": "systemAssignedIdentity"
            #   "assignedIdentityInfo": "MSI"
            return ManagedIdentityAuth.system_assigned, None
        if user_name == _USER_ASSIGNED_IDENTITY:
            # The account contains:
            #   "name": "userAssignedIdentity"
            #   "assignedIdentityInfo": "MSIClient-xxx"/"MSIObject-xxx"/"MSIResource-xxx"
            return tuple(account[_USER_ENTITY][_ASSIGNED_IDENTITY_INFO].split('-', maxsplit=1))
        return None, None

    def _create_credential(self, account, tenant_id=None, client_id=None):
        """Create a credential object driven by MSAL

        :param account: The CLI account to create credential for
        :param tenant_id: If not None, override tenantId from 'account'
        :param client_id: Client ID of another public client application
        :return:
        """
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        tenant_id = tenant_id or account[_TENANT_ID]
        identity = _create_identity_instance(self.cli_ctx, self._authority, tenant_id=tenant_id, client_id=client_id)

        # User
        if user_type == _USER:
            return identity.get_user_credential(username_or_sp_id)

        # Service Principal
        if user_type == _SERVICE_PRINCIPAL:
            return identity.get_service_principal_credential(username_or_sp_id)

        raise NotImplementedError

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
            is_service_principal = s[_USER_ENTITY][_USER_TYPE] == _SERVICE_PRINCIPAL
            tenant = s[_TENANT_ID]
            subscriptions = []
            try:
                identity_credential = self._create_credential(s, tenant_id=tenant)
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
        """Generate a JSON for --json-auth argument when used in:
            - az ad sp create-for-rbac --json-auth
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


class ManagedIdentityAuth:
    # pylint: disable=no-method-argument,no-self-argument
    system_assigned = 'MSI'
    user_assigned_client_id = 'MSIClient'
    user_assigned_object_id = 'MSIObject'
    user_assigned_resource_id = 'MSIResource'

    @staticmethod
    def parse_ids(client_id=None, object_id=None, resource_id=None):
        """Parse IDs into ID type and ID value:
        - system-assigned: MSI, None
        - user-assigned client ID: MSIClient, <GUID>
        - user-assigned object ID: MSIObject, <GUID>
        - user-assigned resource ID: MSIResource, <Resource ID>
        """
        id_arg_count = len([arg for arg in (client_id, object_id, resource_id) if arg])
        if id_arg_count > 1:
            raise CLIError('Usage error: Provide only one of --client-id, --object-id, --resource-id.')

        id_type = None
        id_value = None
        if id_arg_count == 0:
            id_type = ManagedIdentityAuth.system_assigned
            id_value = None
        elif client_id:
            id_type = ManagedIdentityAuth.user_assigned_client_id
            id_value = client_id
        elif object_id:
            id_type = ManagedIdentityAuth.user_assigned_object_id
            id_value = object_id
        elif resource_id:
            id_type = ManagedIdentityAuth.user_assigned_resource_id
            id_value = resource_id
        return id_type, id_value

    @staticmethod
    def credential_factory(id_type, id_value):
        from azure.cli.core.auth.msal_credentials import ManagedIdentityCredential
        if id_type == ManagedIdentityAuth.system_assigned:
            return ManagedIdentityCredential()
        if id_type == ManagedIdentityAuth.user_assigned_client_id:
            return ManagedIdentityCredential(client_id=id_value)
        if id_type == ManagedIdentityAuth.user_assigned_object_id:
            return ManagedIdentityCredential(object_id=id_value)
        if id_type == ManagedIdentityAuth.user_assigned_resource_id:
            return ManagedIdentityCredential(resource_id=id_value)
        raise ValueError("Unrecognized managed identity ID type '{}'".format(id_type))


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
        interaction_required_tenants = []

        client = self._create_subscription_client(credential)
        # https://learn.microsoft.com/en-us/rest/api/resources/tenants/list
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
                subscriptions = self.find_using_specific_tenant(tenant_id, specific_tenant_credential,
                                                                tenant_id_description=t)
            except AuthenticationError as ex:
                # because user creds went through the 'organizations' tenant, the error here must be
                # tenant specific, like the account was disabled, being blocked by MFA. For such errors,
                # we continue with other tenants.
                # As we don't check AADSTS error code, show the original error message for user's reference.
                logger.warning("Authentication failed against tenant %s: %s", t.tenant_id_name, ex)
                interaction_required_tenants.append(t)
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
                           "Use `az login --allow-no-subscriptions` to have tenant level access.")
            for t in empty_tenants:
                logger.warning("%s", t.tenant_id_name)

        # Show warning for InteractionRequired tenants
        if interaction_required_tenants:
            logger.warning("If you need to access subscriptions in the following tenants, please use "
                           "`az login --tenant TENANT_ID`.")
            for t in interaction_required_tenants:
                logger.warning("%s", t.tenant_id_name)
        return all_subscriptions

    def find_using_specific_tenant(self, tenant, credential, tenant_id_description=None):
        """List subscriptions that can be accessed from a specific tenant.
        If called from find_using_common_tenant, tenant_id_description is TenantIdDescription retrieved from
        'Tenants - List' REST API. If directly called, tenant_id_description is None.
        """
        client = self._create_subscription_client(credential)
        # https://learn.microsoft.com/en-us/rest/api/resources/subscriptions/list
        subscriptions = client.subscriptions.list()
        all_subscriptions = []
        for s in subscriptions:
            _attach_token_tenant(s, tenant, tenant_id_description=tenant_id_description)
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

        sdk_cred = CredentialAdaptor(credential)
        client_kwargs = _prepare_mgmt_client_kwargs_track2(self.cli_ctx, sdk_cred)
        client = client_type(sdk_cred, api_version=api_version,
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
    if hasattr(s, 'tenant_default_domain'):
        s_dict[_TENANT_DEFAULT_DOMAIN] = s.tenant_default_domain
    if hasattr(s, 'tenant_display_name'):
        s_dict[_TENANT_DISPLAY_NAME] = s.tenant_display_name

    if hasattr(s, 'managed_by_tenants'):
        if s.managed_by_tenants is None:
            s_dict[_MANAGED_BY_TENANTS] = None
        else:
            s_dict[_MANAGED_BY_TENANTS] = [{_TENANT_ID: t.tenant_id} for t in s.managed_by_tenants]


def _create_identity_instance(cli_ctx, authority, tenant_id=None, client_id=None):
    """Lazily import and create Identity instance to avoid unnecessary imports."""
    from .auth.identity import Identity
    from .util import should_encrypt_token_cache
    encrypt = should_encrypt_token_cache(cli_ctx)

    # EXPERIMENTAL: Use core.use_msal_http_cache=False to turn off MSAL HTTP cache.
    use_msal_http_cache = cli_ctx.config.getboolean('core', 'use_msal_http_cache', fallback=True)

    # On Windows, use core.enable_broker_on_windows=false to disable broker (WAM) for authentication.
    enable_broker_on_windows = cli_ctx.config.getboolean('core', 'enable_broker_on_windows', fallback=True)
    from .telemetry import set_broker_info
    set_broker_info(enable_broker_on_windows)

    # PREVIEW: In Azure Stack environment, use core.instance_discovery=false to disable MSAL's instance discovery.
    instance_discovery = cli_ctx.config.getboolean('core', 'instance_discovery', True)

    return Identity(authority, tenant_id=tenant_id, client_id=client_id,
                    encrypt=encrypt,
                    use_msal_http_cache=use_msal_http_cache,
                    enable_broker_on_windows=enable_broker_on_windows,
                    instance_discovery=instance_discovery)

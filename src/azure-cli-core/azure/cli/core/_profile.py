# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import collections

import os
import os.path
import re
from copy import deepcopy
from enum import Enum

from azure.cli.core._session import ACCOUNT
from azure.cli.core.util import in_cloud_console, can_launch_browser
from azure.cli.core.cloud import get_active_cloud, set_cloud_subscription
from azure.cli.core._identity import Identity, ADALCredentialCache, MSALSecretStore

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
_USER_HOME_ACCOUNT_ID = 'homeAccountId'
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

_COMMON_TENANT = 'common'

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


def _get_authority_url(cli_ctx, tenant):
    authority_url = cli_ctx.cloud.endpoints.active_directory
    is_adfs = bool(re.match('.+(/adfs|/adfs/)$', authority_url, re.I))
    if is_adfs:
        authority_url = authority_url.rstrip('/')  # workaround: ADAL is known to reject auth urls with trailing /
    else:
        authority_url = authority_url.rstrip('/') + '/' + (tenant or _COMMON_TENANT)
    return authority_url, is_adfs


def get_credential_types(cli_ctx):
    class CredentialType(Enum):  # pylint: disable=too-few-public-methods
        cloud = get_active_cloud(cli_ctx)
        management = cli_ctx.cloud.endpoints.management
        rbac = cli_ctx.cloud.endpoints.active_directory_graph_resource_id

    return CredentialType


def _get_cloud_console_token_endpoint():
    return os.environ.get('MSI_ENDPOINT')


# pylint: disable=too-many-lines,too-many-instance-attributes,unused-argument
class Profile(object):

    def __init__(self, storage=None, auth_ctx_factory=None, use_global_creds_cache=True,
                 async_persist=True, cli_ctx=None):
        from azure.cli.core import get_default_cli

        self.cli_ctx = cli_ctx or get_default_cli()
        self._storage = storage or ACCOUNT

        self._management_resource_uri = self.cli_ctx.cloud.endpoints.management
        self._ad_resource_uri = self.cli_ctx.cloud.endpoints.active_directory_resource_id
        self._authority = self.cli_ctx.cloud.endpoints.active_directory.replace('https://', '')
        self._ad = self.cli_ctx.cloud.endpoints.active_directory
        self._adal_cache = ADALCredentialCache(cli_ctx=self.cli_ctx)

    # pylint: disable=too-many-branches,too-many-statements
    def login(self,
              interactive,
              username,
              password,
              is_service_principal,
              tenant,
              use_device_code=False,
              allow_no_subscriptions=False,
              subscription_finder=None,
              use_cert_sn_issuer=None,
              find_subscriptions=True):

        credential = None
        auth_record = None
        identity = Identity(self._authority, tenant, cred_cache=self._adal_cache,
                            allow_unencrypted=self.cli_ctx.config
                            .getboolean('core', 'allow_fallback_to_plaintext', fallback=True)
                            )

        if not subscription_finder:
            subscription_finder = SubscriptionFinder(self.cli_ctx, adal_cache=self._adal_cache)
        if interactive:
            if not use_device_code and (in_cloud_console() or not can_launch_browser()):
                logger.info('Detect no GUI is available, so fall back to device code')
                use_device_code = True

            if not use_device_code:
                from azure.identity import CredentialUnavailableError
                try:
                    credential, auth_record = identity.login_with_interactive_browser()
                except CredentialUnavailableError:
                    use_device_code = True
                    logger.warning('Not able to launch a browser to log you in, falling back to device code...')

            if use_device_code:
                credential, auth_record = identity.login_with_device_code()
        else:
            if is_service_principal:
                if not tenant:
                    raise CLIError('Please supply tenant using "--tenant"')
                if os.path.isfile(password):
                    credential = identity.login_with_service_principal_certificate(username, password)
                else:
                    credential = identity.login_with_service_principal_secret(username, password)
            else:
                credential, auth_record = identity.login_with_username_password(username, password)

        # List tenants and find subscriptions by calling ARM
        subscriptions = []
        if find_subscriptions:
            if tenant and credential:
                subscriptions = subscription_finder.find_using_specific_tenant(tenant, credential)
            elif credential and auth_record:
                subscriptions = subscription_finder.find_using_common_tenant(auth_record, credential)
            if not allow_no_subscriptions and not subscriptions:
                if username:
                    msg = "No subscriptions found for {}.".format(username)
                else:
                    # Don't show username if bare 'az login' is used
                    msg = "No subscriptions found."
                raise CLIError(msg)

            if allow_no_subscriptions:
                t_list = [s.tenant_id for s in subscriptions]
                bare_tenants = [t for t in subscription_finder.tenants if t not in t_list]
                profile = Profile(cli_ctx=self.cli_ctx)
                tenant_accounts = profile._build_tenant_level_accounts(bare_tenants)  # pylint: disable=protected-access
                subscriptions.extend(tenant_accounts)
                if not subscriptions:
                    return []
        else:
            bare_tenant = tenant or auth_record.tenant_id
            subscriptions = self._build_tenant_level_accounts([bare_tenant])

        home_account_id = None
        if auth_record:
            username = auth_record.username
            home_account_id = auth_record.home_account_id

        consolidated = self._normalize_properties(username, subscriptions,
                                                  is_service_principal, bool(use_cert_sn_issuer),
                                                  home_account_id=home_account_id)

        self._set_subscriptions(consolidated)
        # todo: remove after ADAL token deprecation
        self._adal_cache.persist_cached_creds()
        # use deepcopy as we don't want to persist these changes to file.
        return deepcopy(consolidated)

    def login_with_managed_identity(self, identity_id=None, allow_no_subscriptions=None, find_subscriptions=True):
        # pylint: disable=too-many-statements

        # https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview
        # Managed identities for Azure resources is the new name for the service formerly known as
        # Managed Service Identity (MSI).

        resource = self.cli_ctx.cloud.endpoints.active_directory_resource_id
        identity = Identity()
        credential, mi_info = identity.login_with_managed_identity(resource, identity_id)

        tenant = mi_info[Identity.MANAGED_IDENTITY_TENANT_ID]
        if find_subscriptions:
            logger.info('Finding subscriptions...')
            subscription_finder = SubscriptionFinder(self.cli_ctx)
            subscriptions = subscription_finder.find_using_specific_tenant(tenant, credential)
            if not subscriptions:
                if allow_no_subscriptions:
                    subscriptions = self._build_tenant_level_accounts([tenant])
                else:
                    raise CLIError('No access was configured for the VM, hence no subscriptions were found. '
                                   "If this is expected, use '--allow-no-subscriptions' to have tenant level access.")
        else:
            subscriptions = self._build_tenant_level_accounts([tenant])

        # Get info for persistence
        user_name = mi_info[Identity.MANAGED_IDENTITY_TYPE]
        id_type_to_identity_type = {
            Identity.MANAGED_IDENTITY_CLIENT_ID: MsiAccountTypes.user_assigned_client_id,
            Identity.MANAGED_IDENTITY_OBJECT_ID: MsiAccountTypes.user_assigned_object_id,
            Identity.MANAGED_IDENTITY_RESOURCE_ID: MsiAccountTypes.user_assigned_resource_id,
            None: MsiAccountTypes.system_assigned
        }

        # Previously we persist user's input in assignedIdentityInfo:
        #     "assignedIdentityInfo": "MSIClient-eecb2419-a29d-4580-a92a-f6a7b7b71300",
        # Now we persist the output - info extracted from the access token.
        # client_id, object_id, and resource_id are unified to client_id, which is the only persisted field.
        # Also, the name "MSI" is deprecated. So will be assignedIdentityInfo.
        legacy_identity_type = id_type_to_identity_type[mi_info[Identity.MANAGED_IDENTITY_ID_TYPE]]
        legacy_base_name = ('{}-{}'.format(legacy_identity_type, identity_id) if identity_id else legacy_identity_type)

        consolidated = self._normalize_properties(user_name, subscriptions, is_service_principal=True,
                                                  user_assigned_identity_id=legacy_base_name,
                                                  managed_identity_info=mi_info)
        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def login_in_cloud_shell(self, allow_no_subscriptions=None, find_subscriptions=True):
        # TODO: deprecate allow_no_subscriptions
        resource = self.cli_ctx.cloud.endpoints.active_directory_resource_id
        identity = Identity()
        credential, identity_info = identity.login_in_cloud_shell(resource)

        tenant = identity_info[Identity.MANAGED_IDENTITY_TENANT_ID]
        if find_subscriptions:
            logger.info('Finding subscriptions...')
            subscription_finder = SubscriptionFinder(self.cli_ctx)
            subscriptions = subscription_finder.find_using_specific_tenant(tenant, credential)
            if not subscriptions:
                if allow_no_subscriptions:
                    subscriptions = self._build_tenant_level_accounts([tenant])
                else:
                    raise CLIError('No access was configured for the VM, hence no subscriptions were found. '
                                   "If this is expected, use '--allow-no-subscriptions' to have tenant level access.")
        else:
            subscriptions = self._build_tenant_level_accounts([tenant])

        consolidated = self._normalize_properties(identity_info[Identity.CLOUD_SHELL_IDENTITY_UNIQUE_NAME],
                                                  subscriptions, is_service_principal=False)
        for s in consolidated:
            s[_USER_ENTITY][_CLOUD_SHELL_ID] = True
        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def _normalize_properties(self, user, subscriptions, is_service_principal, cert_sn_issuer_auth=None,
                              user_assigned_identity_id=None, home_account_id=None, managed_identity_info=None):
        import sys
        consolidated = []
        for s in subscriptions:
            display_name = s.display_name
            if display_name is None:
                display_name = ''
            try:
                display_name.encode(sys.getdefaultencoding())
            except (UnicodeEncodeError, UnicodeDecodeError):  # mainly for Python 2.7 with ascii as the default encoding
                display_name = re.sub(r'[^\x00-\x7f]', lambda x: '?', display_name)

            subscription_dict = {
                _SUBSCRIPTION_ID: s.id.rpartition('/')[2],
                _SUBSCRIPTION_NAME: display_name,
                _STATE: s.state.value,
                _USER_ENTITY: {
                    _USER_NAME: user,
                    _USER_TYPE: _SERVICE_PRINCIPAL if is_service_principal else _USER
                },
                _IS_DEFAULT_SUBSCRIPTION: False,
                _TENANT_ID: s.tenant_id,
                _ENVIRONMENT_NAME: self.cli_ctx.cloud.name
            }

            if home_account_id:
                subscription_dict[_USER_ENTITY][_USER_HOME_ACCOUNT_ID] = home_account_id
            # for Subscriptions - List REST API 2019-06-01's subscription account
            if subscription_dict[_SUBSCRIPTION_NAME] != _TENANT_LEVEL_ACCOUNT_NAME:
                if hasattr(s, 'home_tenant_id'):
                    subscription_dict[_HOME_TENANT_ID] = s.home_tenant_id
                if hasattr(s, 'managed_by_tenants'):
                    subscription_dict[_MANAGED_BY_TENANTS] = [{_TENANT_ID: t.tenant_id} for t in s.managed_by_tenants]

            if cert_sn_issuer_auth:
                subscription_dict[_USER_ENTITY][_SERVICE_PRINCIPAL_CERT_SN_ISSUER_AUTH] = True
            if managed_identity_info:
                subscription_dict[_USER_ENTITY]['clientId'] = managed_identity_info[Identity.MANAGED_IDENTITY_CLIENT_ID]
                subscription_dict[_USER_ENTITY]['objectId'] = managed_identity_info[Identity.MANAGED_IDENTITY_OBJECT_ID]
                subscription_dict[_USER_ENTITY]['resourceId'] = \
                    managed_identity_info[Identity.MANAGED_IDENTITY_RESOURCE_ID]

            # This will be deprecated and client_id will be the only persisted ID
            if user_assigned_identity_id:
                logger.warning("assignedIdentityInfo will be deprecated in the future. Only client ID should be used.")
                subscription_dict[_USER_ENTITY][_ASSIGNED_IDENTITY_INFO] = user_assigned_identity_id

            consolidated.append(subscription_dict)
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
        from azure.cli.core.profiles import ResourceType, get_sdk
        SubscriptionType, StateType = get_sdk(self.cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS, 'Subscription',
                                              'SubscriptionState', mod='models')
        s = SubscriptionType()
        s.state = StateType.enabled
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
            dic = collections.OrderedDict((_get_key_name(x, secondary_key_name), x) for x in existing_ones)
        else:
            dic = collections.OrderedDict()

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
        from azure.mgmt.resource.subscriptions.models import SubscriptionState
        s = next((x for x in subscriptions if x.get(_STATE) == SubscriptionState.enabled.value), None)
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

    def logout(self, user_or_sp, clear_credential):
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        result = [x for x in subscriptions
                  if user_or_sp.lower() == x[_USER_ENTITY][_USER_NAME].lower()]

        if result:
            # Remove the account from the profile
            subscriptions = [x for x in subscriptions if x not in result]
            self._storage[_SUBSCRIPTIONS] = subscriptions

            # Always remove credential from the legacy cred cache, regardless of MSAL cache, to be deprecated
            adal_cache = ADALCredentialCache(cli_ctx=self.cli_ctx)
            adal_cache.remove_cached_creds(user_or_sp)

            logger.warning('Account %s was logged out from Azure CLI', user_or_sp)
        else:
            # https://english.stackexchange.com/questions/5302/log-in-to-or-log-into-or-login-to
            logger.warning("Account %s was not logged in to Azure CLI.", user_or_sp)

        # Log out from MSAL cache
        identity = Identity(self._authority)
        accounts = identity.get_user(user_or_sp)
        if accounts:
            logger.info("The credential of %s were found from MSAL encrypted cache.", user_or_sp)
            if clear_credential:
                identity.logout_user(user_or_sp)
                logger.warning("The credential of %s were cleared from MSAL encrypted cache. This account is "
                               "also logged out from other SDK tools which use Azure CLI's credential "
                               "via Single Sign-On.", user_or_sp)
            else:
                logger.warning('The credential of %s is still stored in MSAL encrypted cached. Other SDK tools may use '
                               'Azure CLI\'s credential via Single Sign-On. '
                               'To clear the credential, run `az logout --username %s --clear-credential`.',
                               user_or_sp, user_or_sp)
        else:
            # remove service principle secret
            identity.logout_sp(user_or_sp)

    def logout_all(self, clear_credential):
        self._storage[_SUBSCRIPTIONS] = []

        # Always remove credentials from the legacy cred cache, regardless of MSAL cache
        adal_cache = ADALCredentialCache(cli_ctx=self.cli_ctx)
        adal_cache.remove_all_cached_creds()
        logger.warning('All accounts were logged out.')

        # Deal with MSAL cache
        identity = Identity(self._authority)
        accounts = identity.get_user()
        if accounts:
            logger.info("These credentials were found from MSAL encrypted cache: %s", accounts)
            if clear_credential:
                identity.logout_all()
                logger.warning('All credentials store in MSAL encrypted cache were cleared.')
            else:
                logger.warning('These credentials are still stored in MSAL encrypted cached:')
                for account in identity.get_user():
                    logger.warning(account['username'])
                logger.warning('Other SDK tools may use Azure CLI\'s credential via Single Sign-On. '
                               'To clear all credentials, run `az account clear --clear-credential`. '
                               'To clear one of them, run `az logout --username USERNAME` --clear-credential.')
        else:
            logger.warning('No credential was not found from MSAL encrypted cache.')

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

    def get_access_token_for_resource(self, username, tenant, resource):
        """get access token for current user account, used by vsts and iot module"""
        tenant = tenant or 'common'
        account = self.get_subscription()
        home_account_id = account[_USER_ENTITY][_USER_HOME_ACCOUNT_ID]
        authority = self.cli_ctx.cloud.endpoints.active_directory.replace('https://', '')
        identity = Identity(authority, tenant, cred_cache=self._adal_cache)
        identity_credential = identity.get_user_credential(home_account_id, username)
        from azure.cli.core.authentication import AuthenticationWrapper
        auth = AuthenticationWrapper(identity_credential, resource=resource)
        token = auth.get_token()
        return token.token

    @staticmethod
    def _try_parse_msi_account_name(account):
        user_name = account[_USER_ENTITY].get(_USER_NAME)

        if user_name in [_SYSTEM_ASSIGNED_IDENTITY, _USER_ASSIGNED_IDENTITY]:
            return user_name, account[_USER_ENTITY].get(_CLIENT_ID)
        return None, None

    def _create_identity_credential(self, account, aux_tenant_id=None):
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        home_account_id = account[_USER_ENTITY].get(_USER_HOME_ACCOUNT_ID)
        identity_type, identity_id = Profile._try_parse_msi_account_name(account)
        tenant_id = aux_tenant_id if aux_tenant_id else account[_TENANT_ID]

        authority = self.cli_ctx.cloud.endpoints.active_directory.replace('https://', '')
        identity = Identity(authority, tenant_id, cred_cache=self._adal_cache)

        if identity_type is None:
            if in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
                if aux_tenant_id:
                    raise CLIError("Tenant shouldn't be specified for Cloud Shell account")
                return Identity.get_msi_credential()

            # User
            if user_type == _USER:
                if not home_account_id:
                    raise CLIError("CLI authentication is migrated to AADv2.0, please run 'az login' to re-login")
                return identity.get_user_credential(home_account_id, username_or_sp_id)

            # Service Principal
            use_cert_sn_issuer = account[_USER_ENTITY].get(_SERVICE_PRINCIPAL_CERT_SN_ISSUER_AUTH)
            return identity.get_service_principal_credential(username_or_sp_id, use_cert_sn_issuer)

        # MSI
        if aux_tenant_id:
            raise CLIError("Tenant shouldn't be specified for MSI account")
        return Identity.get_msi_credential(identity_id)

    def get_login_credentials(self, resource=None, subscription_id=None, aux_subscriptions=None, aux_tenants=None):
        if aux_tenants and aux_subscriptions:
            raise CLIError("Please specify only one of aux_subscriptions and aux_tenants, not both")

        account = self.get_subscription(subscription_id)
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id
        external_tenants_info = []
        if aux_tenants:
            external_tenants_info = [tenant for tenant in aux_tenants if tenant != account[_TENANT_ID]]
        if aux_subscriptions:
            ext_subs = [aux_sub for aux_sub in aux_subscriptions if aux_sub != subscription_id]
            for ext_sub in ext_subs:
                sub = self.get_subscription(ext_sub)
                if sub[_TENANT_ID] != account[_TENANT_ID]:
                    external_tenants_info.append(sub[_TENANT_ID])
        identity_credential = self._create_identity_credential(account)
        external_credentials = []
        for sub_tenant_id in external_tenants_info:
            external_credentials.append(self._create_identity_credential(account, sub_tenant_id))
        from azure.cli.core.authentication import AuthenticationWrapper
        auth_object = AuthenticationWrapper(identity_credential,
                                            external_credentials=external_credentials if external_credentials else None,
                                            resource=resource)
        return (auth_object,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def get_raw_token(self, resource=None, subscription=None, tenant=None):
        if subscription and tenant:
            raise CLIError("Please specify only one of subscription and tenant, not both")
        account = self.get_subscription(subscription)
        identity_credential = self._create_identity_credential(account, tenant)
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id
        from azure.cli.core.authentication import AuthenticationWrapper, _convert_token_entry
        auth = AuthenticationWrapper(identity_credential, resource=resource)
        token = auth.get_token()
        cred = 'Bearer', token.token, _convert_token_entry(token)
        return (cred,
                None if tenant else str(account[_SUBSCRIPTION_ID]),
                str(tenant if tenant else account[_TENANT_ID]))

    def refresh_accounts(self, subscription_finder=None):
        subscriptions = self.load_cached_subscriptions()
        to_refresh = subscriptions

        subscription_finder = subscription_finder or SubscriptionFinder(self.cli_ctx, adal_cache=self._adal_cache)
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
                identity_credential = self._create_identity_credential(s, tenant)
                if is_service_principal:
                    subscriptions = subscription_finder.find_using_specific_tenant(tenant, identity_credential)
                else:
                    # pylint: disable=protected-access
                    subscriptions = subscription_finder. \
                        find_using_common_tenant(identity_credential._auth_record,  # pylint: disable=protected-access
                                                 identity_credential)
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

            consolidated = self._normalize_properties(subscription_finder.user_id,
                                                      subscriptions,
                                                      is_service_principal)
            result += consolidated

        self._set_subscriptions(result, merge=False)

    def get_sp_auth_info(self, subscription_id=None, name=None, password=None, cert_file=None):
        from collections import OrderedDict
        account = self.get_subscription(subscription_id)

        # is the credential created through command like 'create-for-rbac'?
        result = OrderedDict()
        if name and (password or cert_file):
            result['clientId'] = name
            if password:
                result['clientSecret'] = password
            else:
                result['clientCertificate'] = cert_file
            result['subscriptionId'] = subscription_id or account[_SUBSCRIPTION_ID]
        else:  # has logged in through cli
            user_type = account[_USER_ENTITY].get(_USER_TYPE)
            if user_type == _SERVICE_PRINCIPAL:
                result['clientId'] = account[_USER_ENTITY][_USER_NAME]
                msal_cache = MSALSecretStore(True)
                secret, certificate_file = msal_cache.retrieve_secret_of_service_principal(
                    account[_USER_ENTITY][_USER_NAME], account[_TENANT_ID])
                if secret:
                    result['clientSecret'] = secret
                else:
                    # we can output 'clientCertificateThumbprint' if asked
                    result['clientCertificate'] = certificate_file
                result['subscriptionId'] = account[_SUBSCRIPTION_ID]
            else:
                raise CLIError('SDK Auth file is only applicable when authenticated using a service principal')

        result[_TENANT_ID] = account[_TENANT_ID]
        endpoint_mappings = OrderedDict()  # use OrderedDict to control the output sequence
        endpoint_mappings['active_directory'] = 'activeDirectoryEndpointUrl'
        endpoint_mappings['resource_manager'] = 'resourceManagerEndpointUrl'
        endpoint_mappings['active_directory_graph_resource_id'] = 'activeDirectoryGraphResourceId'
        endpoint_mappings['sql_management'] = 'sqlManagementEndpointUrl'
        endpoint_mappings['gallery'] = 'galleryEndpointUrl'
        endpoint_mappings['management'] = 'managementEndpointUrl'

        for e in endpoint_mappings:
            result[endpoint_mappings[e]] = getattr(get_active_cloud(self.cli_ctx).endpoints, e)
        return result

    def get_installation_id(self):
        installation_id = self._storage.get(_INSTALLATION_ID)
        if not installation_id:
            import uuid
            installation_id = str(uuid.uuid1())
            self._storage[_INSTALLATION_ID] = installation_id
        return installation_id


class MsiAccountTypes(object):
    # pylint: disable=no-method-argument,no-self-argument
    system_assigned = 'MSI'
    user_assigned_client_id = 'MSIClient'
    user_assigned_object_id = 'MSIObject'
    user_assigned_resource_id = 'MSIResource'

    @staticmethod
    def valid_msi_account_types():
        return [MsiAccountTypes.system_assigned, MsiAccountTypes.user_assigned_client_id,
                MsiAccountTypes.user_assigned_object_id, MsiAccountTypes.user_assigned_resource_id]

    @staticmethod
    def msi_auth_factory(cli_account_name, identity, resource):
        from msrestazure.azure_active_directory import MSIAuthentication
        if cli_account_name == MsiAccountTypes.system_assigned:
            return MSIAuthentication(resource=resource)
        if cli_account_name == MsiAccountTypes.user_assigned_client_id:
            return MSIAuthentication(resource=resource, client_id=identity)
        if cli_account_name == MsiAccountTypes.user_assigned_object_id:
            return MSIAuthentication(resource=resource, object_id=identity)
        if cli_account_name == MsiAccountTypes.user_assigned_resource_id:
            return MSIAuthentication(resource=resource, msi_res_id=identity)
        raise ValueError("unrecognized msi account name '{}'".format(cli_account_name))


class SubscriptionFinder(object):
    # An ARM client. It finds subscriptions for a user or service principal. It shouldn't do any
    # authentication work, but only find subscriptions
    def __init__(self, cli_ctx, arm_client_factory=None, **kwargs):

        self.user_id = None  # will figure out after log user in
        self.cli_ctx = cli_ctx
        self.secret = None
        self._graph_resource_id = cli_ctx.cloud.endpoints.active_directory_resource_id
        self.authority = self.cli_ctx.cloud.endpoints.active_directory.replace('https://', '')
        self.adal_cache = kwargs.pop("adal_cache", None)

        def create_arm_client_factory(credentials):
            if arm_client_factory:
                return arm_client_factory(credentials)
            from azure.cli.core.profiles._shared import get_client_class
            from azure.cli.core.profiles import ResourceType, get_api_version
            from azure.cli.core.commands.client_factory import configure_common_settings
            client_type = get_client_class(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
            api_version = get_api_version(cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
            client = client_type(credentials, api_version=api_version,
                                 base_url=self.cli_ctx.cloud.endpoints.resource_manager)
            configure_common_settings(cli_ctx, client)
            return client

        self._arm_client_factory = create_arm_client_factory
        self.tenants = []

    #  only occur inside cloud console or VM with identity
    def find_from_raw_token(self, tenant, token):
        # decode the token, so we know the tenant
        # msal : todo
        result = self.find_using_specific_tenant(tenant, token)
        self.tenants = [tenant]
        return result

    def find_using_common_tenant(self, auth_record, credential=None):
        import adal
        all_subscriptions = []
        empty_tenants = []
        mfa_tenants = []

        from azure.cli.core.authentication import AuthenticationWrapper
        track1_credential = AuthenticationWrapper(credential, resource=self._graph_resource_id)
        client = self._arm_client_factory(track1_credential)
        tenants = client.tenants.list()

        for t in tenants:
            tenant_id = t.tenant_id
            # display_name is available since /tenants?api-version=2018-06-01,
            # not available in /tenants?api-version=2016-06-01
            if not hasattr(t, 'display_name'):
                t.display_name = None
            if hasattr(t, 'additional_properties'):  # Remove this line once SDK is fixed
                t.display_name = t.additional_properties.get('displayName')

            identity = Identity(self.authority, tenant_id,
                                allow_unencrypted=self.cli_ctx.config
                                .getboolean('core', 'allow_fallback_to_plaintext', fallback=True))
            try:
                specific_tenant_credential = identity.get_user_credential(auth_record.home_account_id,
                                                                          auth_record.username)
                # todo: remove after ADAL deprecation
                if self.adal_cache:
                    self.adal_cache.add_credential(specific_tenant_credential)
            # TODO: handle MSAL exceptions
            except adal.AdalError as ex:
                # because user creds went through the 'common' tenant, the error here must be
                # tenant specific, like the account was disabled. For such errors, we will continue
                # with other tenants.
                msg = (getattr(ex, 'error_response', None) or {}).get('error_description') or ''
                if 'AADSTS50076' in msg:
                    # The tenant requires MFA and can't be accessed with home tenant's refresh token
                    mfa_tenants.append(t)
                else:
                    logger.warning("Failed to authenticate '%s' due to error '%s'", t, ex)
                continue
            subscriptions = self.find_using_specific_tenant(
                tenant_id,
                specific_tenant_credential)

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
                if t.display_name:
                    logger.warning("%s '%s'", t.tenant_id, t.display_name)
                else:
                    logger.warning("%s", t.tenant_id)

        # Show warning for MFA tenants
        if mfa_tenants:
            logger.warning("The following tenants require Multi-Factor Authentication (MFA). "
                           "Use 'az login --tenant TENANT_ID' to explicitly login to a tenant.")
            for t in mfa_tenants:
                if t.display_name:
                    logger.warning("%s '%s'", t.tenant_id, t.display_name)
                else:
                    logger.warning("%s", t.tenant_id)
        return all_subscriptions

    def find_using_specific_tenant(self, tenant, credential):
        from azure.cli.core.authentication import AuthenticationWrapper
        track1_credential = AuthenticationWrapper(credential, resource=self._graph_resource_id)
        client = self._arm_client_factory(track1_credential)
        subscriptions = client.subscriptions.list()
        all_subscriptions = []
        for s in subscriptions:
            # map tenantId from REST API to homeTenantId
            if hasattr(s, "tenant_id"):
                setattr(s, 'home_tenant_id', s.tenant_id)
            setattr(s, 'tenant_id', tenant)
            all_subscriptions.append(s)
        self.tenants.append(tenant)
        return all_subscriptions

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import collections
import errno
import json
import os
import os.path
from copy import deepcopy
from enum import Enum
from six.moves import BaseHTTPServer

from knack.log import get_logger
from knack.util import CLIError

from azure.cli.core._environment import get_config_dir
from azure.cli.core._session import ACCOUNT
from azure.cli.core.util import get_file_json, in_cloud_console, open_page_in_browser, can_launch_browser
from azure.cli.core.cloud import get_active_cloud, set_cloud_subscription

logger = get_logger(__name__)

# Names below are used by azure-xplat-cli to persist account information into
# ~/.azure/azureProfile.json or osx/keychainer or windows secure storage,
# which azure-cli will share.
# Please do not rename them unless you know what you are doing.
_IS_DEFAULT_SUBSCRIPTION = 'isDefault'
_SUBSCRIPTION_ID = 'id'
_SUBSCRIPTION_NAME = 'name'
_TENANT_ID = 'tenantId'
_USER_ENTITY = 'user'
_USER_NAME = 'name'
_CLOUD_SHELL_ID = 'cloudShellID'
_SUBSCRIPTIONS = 'subscriptions'
_INSTALLATION_ID = 'installationId'
_ENVIRONMENT_NAME = 'environmentName'
_STATE = 'state'
_USER_TYPE = 'type'
_USER = 'user'
_SERVICE_PRINCIPAL = 'servicePrincipal'
_SERVICE_PRINCIPAL_ID = 'servicePrincipalId'
_SERVICE_PRINCIPAL_TENANT = 'servicePrincipalTenant'
_SERVICE_PRINCIPAL_CERT_FILE = 'certificateFile'
_SERVICE_PRINCIPAL_CERT_THUMBPRINT = 'thumbprint'
_TOKEN_ENTRY_USER_ID = 'userId'
_TOKEN_ENTRY_TOKEN_TYPE = 'tokenType'
# This could mean either real access token, or client secret of a service principal
# This naming is no good, but can't change because xplat-cli does so.
_ACCESS_TOKEN = 'accessToken'
_REFRESH_TOKEN = 'refreshToken'

TOKEN_FIELDS_EXCLUDED_FROM_PERSISTENCE = ['familyName',
                                          'givenName',
                                          'isUserIdDisplayable',
                                          'tenantId']

_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'
_COMMON_TENANT = 'common'

_TENANT_LEVEL_ACCOUNT_NAME = 'N/A(tenant level account)'

_SYSTEM_ASSIGNED_IDENTITY = 'systemAssignedIdentity'
_USER_ASSIGNED_IDENTITY = 'userAssignedIdentity'


def load_subscriptions(cli_ctx, all_clouds=False, refresh=False):
    profile = Profile(cli_ctx=cli_ctx)
    if refresh:
        profile.refresh_accounts()
    subscriptions = profile.load_cached_subscriptions(all_clouds)
    return subscriptions


def _get_authority_url(cli_ctx, tenant):
    import re
    authority_url = cli_ctx.cloud.endpoints.active_directory
    is_adfs = bool(re.match('.+(/adfs|/adfs/)$', authority_url, re.I))
    if is_adfs:
        authority_url = authority_url.rstrip('/')  # workaround: ADAL is known to reject auth urls with trailing /
    else:
        authority_url = authority_url.rstrip('/') + '/' + (tenant or _COMMON_TENANT)
    return authority_url, is_adfs


def _authentication_context_factory(cli_ctx, tenant, cache):
    import adal
    authority_url, is_adfs = _get_authority_url(cli_ctx, tenant)
    return adal.AuthenticationContext(authority_url, cache=cache, api_version=None, validate_authority=(not is_adfs))


_AUTH_CTX_FACTORY = _authentication_context_factory


def _load_tokens_from_file(file_path):
    if os.path.isfile(file_path):
        try:
            return get_file_json(file_path, throw_on_empty=False) or []
        except (CLIError, ValueError) as ex:
            raise CLIError("Failed to load token files. If you have a repro, please log an issue at "
                           "https://github.com/Azure/azure-cli/issues. At the same time, you can clean "
                           "up by running 'az account clear' and then 'az login'. (Inner Error: {})".format(ex))
    return []


def _delete_file(file_path):
    try:
        os.remove(file_path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def get_credential_types(cli_ctx):

    class CredentialType(Enum):  # pylint: disable=too-few-public-methods
        cloud = get_active_cloud(cli_ctx)
        management = cli_ctx.cloud.endpoints.management
        rbac = cli_ctx.cloud.endpoints.active_directory_graph_resource_id

    return CredentialType


def _get_cloud_console_token_endpoint():
    return os.environ.get('MSI_ENDPOINT')


# pylint: disable=too-many-lines,too-many-instance-attributes
class Profile(object):

    _global_creds_cache = None

    def __init__(self, storage=None, auth_ctx_factory=None, use_global_creds_cache=True,
                 async_persist=True, cli_ctx=None):
        from azure.cli.core import get_default_cli

        self.cli_ctx = cli_ctx or get_default_cli()
        self._storage = storage or ACCOUNT
        self.auth_ctx_factory = auth_ctx_factory or _AUTH_CTX_FACTORY

        if use_global_creds_cache:
            # for perf, use global cache
            if not Profile._global_creds_cache:
                Profile._global_creds_cache = CredsCache(self.cli_ctx, self.auth_ctx_factory,
                                                         async_persist=async_persist)
            self._creds_cache = Profile._global_creds_cache
        else:
            self._creds_cache = CredsCache(self.cli_ctx, self.auth_ctx_factory, async_persist=async_persist)

        self._management_resource_uri = self.cli_ctx.cloud.endpoints.management
        self._ad_resource_uri = self.cli_ctx.cloud.endpoints.active_directory_resource_id
        self._ad = self.cli_ctx.cloud.endpoints.active_directory
        self._msi_creds = None

    def find_subscriptions_on_login(self,
                                    interactive,
                                    username,
                                    password,
                                    is_service_principal,
                                    tenant,
                                    use_device_code=False,
                                    allow_no_subscriptions=False,
                                    subscription_finder=None):
        from azure.cli.core._debug import allow_debug_adal_connection
        allow_debug_adal_connection()
        subscriptions = []

        if not subscription_finder:
            subscription_finder = SubscriptionFinder(self.cli_ctx,
                                                     self.auth_ctx_factory,
                                                     self._creds_cache.adal_token_cache)
        if interactive:
            if not use_device_code and (in_cloud_console() or not can_launch_browser()):
                logger.info('Detect no GUI is available, so fall back to device code')
                use_device_code = True

            if not use_device_code:
                try:
                    authority_url, _ = _get_authority_url(self.cli_ctx, tenant)
                    subscriptions = subscription_finder.find_through_authorization_code_flow(
                        tenant, self._ad_resource_uri, authority_url)
                except RuntimeError:
                    use_device_code = True
                    logger.warning('Not able to launch a browser to log you in, falling back to device code...')

            if use_device_code:
                subscriptions = subscription_finder.find_through_interactive_flow(
                    tenant, self._ad_resource_uri)
        else:
            if is_service_principal:
                if not tenant:
                    raise CLIError('Please supply tenant using "--tenant"')
                sp_auth = ServicePrincipalAuth(password)
                subscriptions = subscription_finder.find_from_service_principal_id(
                    username, sp_auth, tenant, self._ad_resource_uri)
            else:
                subscriptions = subscription_finder.find_from_user_account(
                    username, password, tenant, self._ad_resource_uri)

        if not allow_no_subscriptions and not subscriptions:
            raise CLIError("No subscriptions were found for '{}'. If this is expected, use "
                           "'--allow-no-subscriptions' to have tenant level accesses".format(
                               username))

        if is_service_principal:
            self._creds_cache.save_service_principal_cred(sp_auth.get_entry_to_persist(username,
                                                                                       tenant))
        if self._creds_cache.adal_token_cache.has_state_changed:
            self._creds_cache.persist_cached_creds()

        if allow_no_subscriptions:
            t_list = [s.tenant_id for s in subscriptions]
            bare_tenants = [t for t in subscription_finder.tenants if t not in t_list]
            profile = Profile(cli_ctx=self.cli_ctx)
            subscriptions = profile._build_tenant_level_accounts(bare_tenants)  # pylint: disable=protected-access
            if not subscriptions:
                return []

        consolidated = self._normalize_properties(subscription_finder.user_id, subscriptions, is_service_principal)

        self._set_subscriptions(consolidated)
        # use deepcopy as we don't want to persist these changes to file.
        return deepcopy(consolidated)

    def _normalize_properties(self, user, subscriptions, is_service_principal):
        consolidated = []
        for s in subscriptions:
            consolidated.append({
                _SUBSCRIPTION_ID: s.id.rpartition('/')[2],
                _SUBSCRIPTION_NAME: s.display_name,
                _STATE: s.state.value,
                _USER_ENTITY: {
                    _USER_NAME: user,
                    _USER_TYPE: _SERVICE_PRINCIPAL if is_service_principal else _USER
                },
                _IS_DEFAULT_SUBSCRIPTION: False,
                _TENANT_ID: s.tenant_id,
                _ENVIRONMENT_NAME: self.cli_ctx.cloud.name
            })
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

    def find_subscriptions_in_vm_with_msi(self, identity_id=None):
        import jwt
        from requests import HTTPError
        from msrestazure.azure_active_directory import MSIAuthentication
        from msrestazure.tools import is_valid_resource_id
        resource = self.cli_ctx.cloud.endpoints.active_directory_resource_id

        if identity_id:
            if is_valid_resource_id(identity_id):
                msi_creds = MSIAuthentication(resource=resource, msi_res_id=identity_id)
                identity_type = MsiAccountTypes.user_assigned_resource_id
            else:
                try:
                    msi_creds = MSIAuthentication(resource=resource, client_id=identity_id)
                    identity_type = MsiAccountTypes.user_assigned_client_id
                except HTTPError as ex:
                    if ex.response.reason == 'Bad Request' and ex.response.status == 400:
                        identity_type = MsiAccountTypes.user_assigned_object_id
                        msi_creds = MSIAuthentication(resource=resource, object_id=identity_id)
                    else:
                        raise
        else:
            identity_type = MsiAccountTypes.system_assigned
            msi_creds = MSIAuthentication(resource=resource)

        token_entry = msi_creds.token
        token = token_entry['access_token']
        logger.info('MSI: token was retrieved. Now trying to initialize local accounts...')
        decode = jwt.decode(token, verify=False, algorithms=['RS256'])
        tenant = decode['tid']

        subscription_finder = SubscriptionFinder(self.cli_ctx, self.auth_ctx_factory, None)
        subscriptions = subscription_finder.find_from_raw_token(tenant, token)
        if not subscriptions:
            raise CLIError('No access was configured for the VM, hence no subscriptions were found')
        base_name = ('{}-{}'.format(identity_type, identity_id) if identity_id else identity_type)
        user = _USER_ASSIGNED_IDENTITY if identity_id else _SYSTEM_ASSIGNED_IDENTITY

        consolidated = self._normalize_properties(user, subscriptions, is_service_principal=True)
        for s in consolidated:
            s[_SUBSCRIPTION_NAME] = base_name
        # key-off subscription name to allow accounts with same id(but under different identities)
        self._set_subscriptions(consolidated, secondary_key_name=_SUBSCRIPTION_NAME)
        return deepcopy(consolidated)

    def find_subscriptions_in_cloud_console(self):
        import jwt

        _, token, _ = self._get_token_from_cloud_shell(self.cli_ctx.cloud.endpoints.active_directory_resource_id)
        logger.info('MSI: token was retrieved. Now trying to initialize local accounts...')
        decode = jwt.decode(token, verify=False, algorithms=['RS256'])
        tenant = decode['tid']

        subscription_finder = SubscriptionFinder(self.cli_ctx, self.auth_ctx_factory, None)
        subscriptions = subscription_finder.find_from_raw_token(tenant, token)
        if not subscriptions:
            raise CLIError('No subscriptions were found in the cloud shell')
        user = decode.get('unique_name', 'N/A')

        consolidated = self._normalize_properties(user, subscriptions, is_service_principal=False)
        for s in consolidated:
            s[_USER_ENTITY][_CLOUD_SHELL_ID] = True
        self._set_subscriptions(consolidated)
        return deepcopy(consolidated)

    def _get_token_from_cloud_shell(self, resource):  # pylint: disable=no-self-use
        from msrestazure.azure_active_directory import MSIAuthentication
        auth = MSIAuthentication(resource=resource)
        auth.set_token()
        token_entry = auth.token
        return (token_entry['token_type'], token_entry['access_token'], token_entry)

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

    def logout(self, user_or_sp):
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        result = [x for x in subscriptions
                  if user_or_sp.lower() == x[_USER_ENTITY][_USER_NAME].lower()]
        subscriptions = [x for x in subscriptions if x not in result]

        self._storage[_SUBSCRIPTIONS] = subscriptions
        self._creds_cache.remove_cached_creds(user_or_sp)

    def logout_all(self):
        self._storage[_SUBSCRIPTIONS] = []
        self._creds_cache.remove_all_cached_creds()

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
            raise CLIError("Please run 'az login' to setup account.")

        result = [x for x in subscriptions if (
            not subscription and x.get(_IS_DEFAULT_SUBSCRIPTION) or
            subscription and subscription.lower() in [x[_SUBSCRIPTION_ID].lower(), x[
                _SUBSCRIPTION_NAME].lower()])]
        if not result and subscription:
            raise CLIError("Subscription '{}' not found. "
                           "Check the spelling and casing and try again.".format(subscription))
        elif not result and not subscription:
            raise CLIError("No subscription found. Run 'az account set' to select a subscription.")
        elif len(result) > 1:
            raise CLIError("Multiple subscriptions with the name '{}' found. "
                           "Specify the subscription ID.".format(subscription))
        return result[0]

    def get_subscription_id(self, subscription=None):  # take id or name
        return self.get_subscription(subscription)[_SUBSCRIPTION_ID]

    def get_access_token_for_resource(self, username, tenant, resource):
        tenant = tenant or 'common'
        _, access_token, _ = self._creds_cache.retrieve_token_for_user(
            username, tenant, resource)
        return access_token

    @staticmethod
    def _try_parse_msi_account_name(account):
        subscription_name, user = account[_SUBSCRIPTION_NAME], account[_USER_ENTITY].get(_USER_NAME)
        if user in [_SYSTEM_ASSIGNED_IDENTITY, _USER_ASSIGNED_IDENTITY]:
            parts = subscription_name.split('-', 1)
            if parts[0] in MsiAccountTypes.valid_msi_account_types():
                return parts[0], (None if len(parts) <= 1 else parts[1])
        return None, None

    def get_login_credentials(self, resource=None, subscription_id=None, aux_subscriptions=None):
        account = self.get_subscription(subscription_id)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id

        identity_type, identity_id = Profile._try_parse_msi_account_name(account)

        external_tenants_info = []
        ext_subs = [aux_sub for aux_sub in (aux_subscriptions or []) if aux_sub != subscription_id]
        for ext_sub in ext_subs:
            sub = self.get_subscription(ext_sub)
            if sub[_TENANT_ID] != account[_TENANT_ID]:
                external_tenants_info.append((sub[_USER_ENTITY][_USER_NAME], sub[_TENANT_ID]))

        if identity_type is None:
            def _retrieve_token():
                if in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
                    return self._get_token_from_cloud_shell(resource)
                if user_type == _USER:
                    return self._creds_cache.retrieve_token_for_user(username_or_sp_id,
                                                                     account[_TENANT_ID], resource)
                return self._creds_cache.retrieve_token_for_service_principal(username_or_sp_id, resource)

            def _retrieve_tokens_from_external_tenants():
                external_tokens = []
                for u, t in external_tenants_info:
                    external_tokens.append(self._creds_cache.retrieve_token_for_user(u, t, resource))
                return external_tokens

            from azure.cli.core.adal_authentication import AdalAuthentication
            auth_object = AdalAuthentication(_retrieve_token,
                                             _retrieve_tokens_from_external_tenants if external_tenants_info else None)
        else:
            if self._msi_creds is None:
                self._msi_creds = MsiAccountTypes.msi_auth_factory(identity_type, identity_id, resource)
            auth_object = self._msi_creds

        return (auth_object,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def get_refresh_token(self, resource=None,
                          subscription=None):
        account = self.get_subscription(subscription)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id

        if user_type == _USER:
            _, _, token_entry = self._creds_cache.retrieve_token_for_user(
                username_or_sp_id, account[_TENANT_ID], resource)
            return None, token_entry.get(_REFRESH_TOKEN), token_entry[_ACCESS_TOKEN], str(account[_TENANT_ID])

        sp_secret = self._creds_cache.retrieve_secret_of_service_principal(username_or_sp_id)
        return username_or_sp_id, sp_secret, None, str(account[_TENANT_ID])

    def get_raw_token(self, resource=None, subscription=None):
        account = self.get_subscription(subscription)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        resource = resource or self.cli_ctx.cloud.endpoints.active_directory_resource_id

        identity_type, identity_id = Profile._try_parse_msi_account_name(account)
        if identity_type:
            msi_creds = MsiAccountTypes.msi_auth_factory(identity_type, identity_id, resource)
            msi_creds.set_token()
            token_entry = msi_creds.token
            creds = (token_entry['token_type'], token_entry['access_token'], token_entry)
        elif in_cloud_console() and account[_USER_ENTITY].get(_CLOUD_SHELL_ID):
            creds = self._get_token_from_cloud_shell(resource)

        elif user_type == _USER:
            creds = self._creds_cache.retrieve_token_for_user(username_or_sp_id,
                                                              account[_TENANT_ID], resource)
        else:
            creds = self._creds_cache.retrieve_token_for_service_principal(username_or_sp_id,
                                                                           resource)
        return (creds,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def refresh_accounts(self, subscription_finder=None):
        subscriptions = self.load_cached_subscriptions()
        to_refresh = subscriptions

        from azure.cli.core._debug import allow_debug_adal_connection
        allow_debug_adal_connection()
        subscription_finder = subscription_finder or SubscriptionFinder(self.cli_ctx,
                                                                        self.auth_ctx_factory,
                                                                        self._creds_cache.adal_token_cache)
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
                if is_service_principal:
                    sp_auth = ServicePrincipalAuth(self._creds_cache.retrieve_secret_of_service_principal(user_name))
                    subscriptions = subscription_finder.find_from_service_principal_id(user_name, sp_auth, tenant,
                                                                                       self._ad_resource_uri)
                else:
                    subscriptions = subscription_finder.find_from_user_account(user_name, None, None,
                                                                               self._ad_resource_uri)
            except Exception as ex:  # pylint: disable=broad-except
                logger.warning("Refreshing for '%s' failed with an error '%s'. The existing accounts were not "
                               "modified. You can run 'az login' later to explictly refresh them", user_name, ex)
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

        if self._creds_cache.adal_token_cache.has_state_changed:
            self._creds_cache.persist_cached_creds()

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
                sp_auth = ServicePrincipalAuth(self._creds_cache.retrieve_secret_of_service_principal(
                    account[_USER_ENTITY][_USER_NAME]))
                secret = getattr(sp_auth, 'secret', None)
                if secret:
                    result['clientSecret'] = secret
                else:
                    # we can output 'clientCertificateThumbprint' if asked
                    result['clientCertificate'] = sp_auth.certificate_file
                result['subscriptionId'] = account[_SUBSCRIPTION_ID]
            else:
                raise CLIError('SDK Auth file is only applicable on service principals')

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
        elif cli_account_name == MsiAccountTypes.user_assigned_client_id:
            return MSIAuthentication(resource=resource, client_id=identity)
        elif cli_account_name == MsiAccountTypes.user_assigned_object_id:
            return MSIAuthentication(resource=resource, object_id=identity)
        elif cli_account_name == MsiAccountTypes.user_assigned_resource_id:
            return MSIAuthentication(resource=resource, msi_res_id=identity)
        else:
            raise ValueError("unrecognized msi account name '{}'".format(cli_account_name))


class SubscriptionFinder(object):
    '''finds all subscriptions for a user or service principal'''

    def __init__(self, cli_ctx, auth_context_factory, adal_token_cache, arm_client_factory=None):

        self._adal_token_cache = adal_token_cache
        self._auth_context_factory = auth_context_factory
        self.user_id = None  # will figure out after log user in
        self.cli_ctx = cli_ctx

        def create_arm_client_factory(credentials):
            if arm_client_factory:
                return arm_client_factory(credentials)
            from azure.cli.core.profiles._shared import get_client_class
            from azure.cli.core.profiles import ResourceType, get_api_version
            from azure.cli.core._debug import change_ssl_cert_verification
            client_type = get_client_class(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
            api_version = get_api_version(cli_ctx, ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
            return change_ssl_cert_verification(client_type(credentials, api_version=api_version,
                                                            base_url=self.cli_ctx.cloud.endpoints.resource_manager))

        self._arm_client_factory = create_arm_client_factory
        self.tenants = []

    def find_from_user_account(self, username, password, tenant, resource):
        context = self._create_auth_context(tenant)
        if password:
            token_entry = context.acquire_token_with_username_password(resource, username, password, _CLIENT_ID)
        else:  # when refresh account, we will leverage local cached tokens
            token_entry = context.acquire_token(resource, username, _CLIENT_ID)

        if not token_entry:
            return []
        self.user_id = token_entry[_TOKEN_ENTRY_USER_ID]

        if tenant is None:
            result = self._find_using_common_tenant(token_entry[_ACCESS_TOKEN], resource)
        else:
            result = self._find_using_specific_tenant(tenant, token_entry[_ACCESS_TOKEN])
        return result

    def find_through_authorization_code_flow(self, tenant, resource, authority_url):

        # launch browser and get the code
        results = _get_authorization_code(resource, authority_url)

        if not results.get('code'):
            raise CLIError('Login failed')  # error detail is already displayed through previous steps

        # exchange the code for the token
        context = self._create_auth_context(tenant)
        token_entry = context.acquire_token_with_authorization_code(results['code'], results['reply_url'],
                                                                    resource, _CLIENT_ID, None)
        self.user_id = token_entry[_TOKEN_ENTRY_USER_ID]
        logger.warning("You have logged in. Now let us find all the subscriptions to which you have access...")
        if tenant is None:
            result = self._find_using_common_tenant(token_entry[_ACCESS_TOKEN], resource)
        else:
            result = self._find_using_specific_tenant(tenant, token_entry[_ACCESS_TOKEN])
        return result

    def find_through_interactive_flow(self, tenant, resource):
        context = self._create_auth_context(tenant)
        code = context.acquire_user_code(resource, _CLIENT_ID)
        logger.warning(code['message'])
        token_entry = context.acquire_token_with_device_code(resource, code, _CLIENT_ID)
        self.user_id = token_entry[_TOKEN_ENTRY_USER_ID]
        if tenant is None:
            result = self._find_using_common_tenant(token_entry[_ACCESS_TOKEN], resource)
        else:
            result = self._find_using_specific_tenant(tenant, token_entry[_ACCESS_TOKEN])
        return result

    def find_from_service_principal_id(self, client_id, sp_auth, tenant, resource):
        context = self._create_auth_context(tenant, False)
        token_entry = sp_auth.acquire_token(context, resource, client_id)
        self.user_id = client_id
        result = self._find_using_specific_tenant(tenant, token_entry[_ACCESS_TOKEN])
        self.tenants = [tenant]
        return result

    #  only occur inside cloud console or VM with identity
    def find_from_raw_token(self, tenant, token):
        # decode the token, so we know the tenant
        result = self._find_using_specific_tenant(tenant, token)
        self.tenants = [tenant]
        return result

    def _create_auth_context(self, tenant, use_token_cache=True):
        token_cache = self._adal_token_cache if use_token_cache else None
        return self._auth_context_factory(self.cli_ctx, tenant, token_cache)

    def _find_using_common_tenant(self, access_token, resource):
        import adal
        from msrest.authentication import BasicTokenAuthentication

        all_subscriptions = []
        token_credential = BasicTokenAuthentication({'access_token': access_token})
        client = self._arm_client_factory(token_credential)
        tenants = client.tenants.list()
        for t in tenants:
            tenant_id = t.tenant_id
            temp_context = self._create_auth_context(tenant_id)
            try:
                temp_credentials = temp_context.acquire_token(resource, self.user_id, _CLIENT_ID)
            except adal.AdalError as ex:
                # because user creds went through the 'common' tenant, the error here must be
                # tenant specific, like the account was disabled. For such errors, we will continue
                # with other tenants.
                logger.warning("Failed to authenticate '%s' due to error '%s'", t, ex)
                continue
            subscriptions = self._find_using_specific_tenant(
                tenant_id,
                temp_credentials[_ACCESS_TOKEN])
            all_subscriptions.extend(subscriptions)

        return all_subscriptions

    def _find_using_specific_tenant(self, tenant, access_token):
        from msrest.authentication import BasicTokenAuthentication

        token_credential = BasicTokenAuthentication({'access_token': access_token})
        client = self._arm_client_factory(token_credential)
        subscriptions = client.subscriptions.list()
        all_subscriptions = []
        for s in subscriptions:
            setattr(s, 'tenant_id', tenant)
            all_subscriptions.append(s)
        self.tenants.append(tenant)
        return all_subscriptions


class CredsCache(object):
    '''Caches AAD tokena and service principal secrets, and persistence will
    also be handled
    '''

    def __init__(self, cli_ctx, auth_ctx_factory=None, async_persist=True):
        # AZURE_ACCESS_TOKEN_FILE is used by Cloud Console and not meant to be user configured
        self._token_file = (os.environ.get('AZURE_ACCESS_TOKEN_FILE', None) or
                            os.path.join(get_config_dir(), 'accessTokens.json'))
        self._service_principal_creds = []
        self._auth_ctx_factory = auth_ctx_factory
        self._adal_token_cache_attr = None
        self._should_flush_to_disk = False
        self._async_persist = async_persist
        self._ctx = cli_ctx
        if async_persist:
            import atexit
            atexit.register(self.flush_to_disk)

    def persist_cached_creds(self):
        self._should_flush_to_disk = True
        if not self._async_persist:
            self.flush_to_disk()
        self.adal_token_cache.has_state_changed = False

    def flush_to_disk(self):
        if self._should_flush_to_disk:
            with os.fdopen(os.open(self._token_file, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600),
                           'w+') as cred_file:
                items = self.adal_token_cache.read_items()
                all_creds = [entry for _, entry in items]

                # trim away useless fields (needed for cred sharing with xplat)
                for i in all_creds:
                    for key in TOKEN_FIELDS_EXCLUDED_FROM_PERSISTENCE:
                        i.pop(key, None)

                all_creds.extend(self._service_principal_creds)
                cred_file.write(json.dumps(all_creds))

    def retrieve_token_for_user(self, username, tenant, resource):
        context = self._auth_ctx_factory(self._ctx, tenant, cache=self.adal_token_cache)
        token_entry = context.acquire_token(resource, username, _CLIENT_ID)
        if not token_entry:
            raise CLIError("Could not retrieve token from local cache.{}".format(
                " Please run 'az login'." if not in_cloud_console() else ''))

        if self.adal_token_cache.has_state_changed:
            self.persist_cached_creds()
        return (token_entry[_TOKEN_ENTRY_TOKEN_TYPE], token_entry[_ACCESS_TOKEN], token_entry)

    def retrieve_token_for_service_principal(self, sp_id, resource):
        self.load_adal_token_cache()
        matched = [x for x in self._service_principal_creds if sp_id == x[_SERVICE_PRINCIPAL_ID]]
        if not matched:
            raise CLIError("Please run 'az account set' to select active account.")
        cred = matched[0]
        context = self._auth_ctx_factory(self._ctx, cred[_SERVICE_PRINCIPAL_TENANT], None)
        sp_auth = ServicePrincipalAuth(cred.get(_ACCESS_TOKEN, None) or
                                       cred.get(_SERVICE_PRINCIPAL_CERT_FILE, None))
        token_entry = sp_auth.acquire_token(context, resource, sp_id)
        return (token_entry[_TOKEN_ENTRY_TOKEN_TYPE], token_entry[_ACCESS_TOKEN], token_entry)

    def retrieve_secret_of_service_principal(self, sp_id):
        self.load_adal_token_cache()
        matched = [x for x in self._service_principal_creds if sp_id == x[_SERVICE_PRINCIPAL_ID]]
        if not matched:
            raise CLIError("No matched service principal found")
        cred = matched[0]
        return cred.get(_ACCESS_TOKEN, None)

    @property
    def adal_token_cache(self):
        return self.load_adal_token_cache()

    def load_adal_token_cache(self):
        if self._adal_token_cache_attr is None:
            import adal
            all_entries = _load_tokens_from_file(self._token_file)
            self._load_service_principal_creds(all_entries)
            real_token = [x for x in all_entries if x not in self._service_principal_creds]
            self._adal_token_cache_attr = adal.TokenCache(json.dumps(real_token))
        return self._adal_token_cache_attr

    def save_service_principal_cred(self, sp_entry):
        self.load_adal_token_cache()
        matched = [x for x in self._service_principal_creds
                   if sp_entry[_SERVICE_PRINCIPAL_ID] == x[_SERVICE_PRINCIPAL_ID] and
                   sp_entry[_SERVICE_PRINCIPAL_TENANT] == x[_SERVICE_PRINCIPAL_TENANT]]
        state_changed = False
        if matched:
            # pylint: disable=line-too-long
            if (sp_entry.get(_ACCESS_TOKEN, None) != matched[0].get(_ACCESS_TOKEN, None) or
                    sp_entry.get(_SERVICE_PRINCIPAL_CERT_FILE, None) != matched[0].get(_SERVICE_PRINCIPAL_CERT_FILE, None)):
                self._service_principal_creds.remove(matched[0])
                self._service_principal_creds.append(sp_entry)
                state_changed = True
        else:
            self._service_principal_creds.append(sp_entry)
            state_changed = True

        if state_changed:
            self.persist_cached_creds()

    def _load_service_principal_creds(self, creds):
        for c in creds:
            if c.get(_SERVICE_PRINCIPAL_ID):
                self._service_principal_creds.append(c)
        return self._service_principal_creds

    def remove_cached_creds(self, user_or_sp):
        state_changed = False
        # clear AAD tokens
        tokens = self.adal_token_cache.find({_TOKEN_ENTRY_USER_ID: user_or_sp})
        if tokens:
            state_changed = True
            self.adal_token_cache.remove(tokens)

        # clear service principal creds
        matched = [x for x in self._service_principal_creds
                   if x[_SERVICE_PRINCIPAL_ID] == user_or_sp]
        if matched:
            state_changed = True
            self._service_principal_creds = [x for x in self._service_principal_creds
                                             if x not in matched]

        if state_changed:
            self.persist_cached_creds()

    def remove_all_cached_creds(self):
        # we can clear file contents, but deleting it is simpler
        _delete_file(self._token_file)


class ServicePrincipalAuth(object):

    def __init__(self, password_arg_value):
        if not password_arg_value:
            raise CLIError('missing secret or certificate in order to '
                           'authnenticate through a service principal')
        if os.path.isfile(password_arg_value):
            certificate_file = password_arg_value
            from OpenSSL.crypto import load_certificate, FILETYPE_PEM
            self.certificate_file = certificate_file
            with open(certificate_file, 'r') as file_reader:
                self.cert_file_string = file_reader.read()
                cert = load_certificate(FILETYPE_PEM, self.cert_file_string)
                self.thumbprint = cert.digest("sha1").decode()
        else:
            self.secret = password_arg_value

    def acquire_token(self, authentication_context, resource, client_id):
        if hasattr(self, 'secret'):
            return authentication_context.acquire_token_with_client_credentials(resource, client_id, self.secret)
        return authentication_context.acquire_token_with_client_certificate(resource, client_id, self.cert_file_string,
                                                                            self.thumbprint)

    def get_entry_to_persist(self, sp_id, tenant):
        entry = {
            _SERVICE_PRINCIPAL_ID: sp_id,
            _SERVICE_PRINCIPAL_TENANT: tenant,
        }
        if hasattr(self, 'secret'):
            entry[_ACCESS_TOKEN] = self.secret
        else:
            entry[_SERVICE_PRINCIPAL_CERT_FILE] = self.certificate_file
            entry[_SERVICE_PRINCIPAL_CERT_THUMBPRINT] = self.thumbprint

        return entry


class ClientRedirectServer(BaseHTTPServer.HTTPServer):  # pylint: disable=too-few-public-methods
    query_params = {}


class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    # pylint: disable=line-too-long

    def do_GET(self):
        try:
            from urllib.parse import parse_qs
        except ImportError:
            from urlparse import parse_qs  # pylint: disable=import-error

        if self.path.endswith('/favicon.ico'):  # deal with legacy IE
            self.send_response(204)
            return

        query = self.path.split('?', 1)[-1]
        query = parse_qs(query, keep_blank_values=True)
        self.server.query_params = query

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        landing_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'auth_landing_pages',
                                    'ok.html' if 'code' in query else 'fail.html')
        with open(landing_file, 'rb') as html_file:
            self.wfile.write(html_file.read())

    def log_message(self, format, *args):  # pylint: disable=redefined-builtin,unused-argument,no-self-use
        return  # this prevent http server from dumping messages to stdout


def _get_authorization_code_worker(authority_url, resource, results):
    import socket
    for port in range(8400, 9000):
        try:
            web_server = ClientRedirectServer(('localhost', port), ClientRedirectHandler)
            reply_url = "http://localhost:{}".format(port)
            break
        except socket.error:
            logger.warning("Port '%s' is taken. Trying with the next one", port)

    if reply_url is None:
        logger.warning("Error: can't reserve a port for authentication reply url")
        return

    # launch browser:
    url = ('{0}/oauth2/authorize?response_type=code&client_id={1}'
           '&redirect_uri={2}&state={3}&resource={4}&prompt=select_account')
    url = url.format(authority_url, _CLIENT_ID, reply_url, 'code', resource)
    logger.info('Open browser with url: %s', url)
    succ = open_page_in_browser(url)
    if succ is False:
        web_server.server_close()
        results['no_browser'] = True
        return

    # emit a warning for transitioning to the new experience
    logger.warning('Note, we have launched a browser for you to login. For old experience'
                   ' with device code, use "az login --use-device-code"')

    # wait for callback from browser.
    while True:
        web_server.handle_request()
        if 'error' in web_server.query_params or 'code' in web_server.query_params:
            break

    if 'error' in web_server.query_params:
        logger.warning('Authentication Error: "%s". Description: "%s" ', web_server.query_params['error'],
                       web_server.query_params.get('error_description'))
        return

    if 'code' in web_server.query_params:
        code = web_server.query_params['code']
    else:
        logger.warning('Authentication Error: Authorization code was not captured in query strings "%s"',
                       web_server.query_params)
        return
    results['code'] = code[0]
    results['reply_url'] = reply_url


def _get_authorization_code(resource, authority_url):
    import threading
    import time
    results = {}
    t = threading.Thread(target=_get_authorization_code_worker,
                         args=(authority_url, resource, results))
    t.daemon = True
    t.start()
    while True:
        time.sleep(2)  # so that ctrl+c can stop the command
        if not t.is_alive():
            break  # done
    if results.get('no_browser'):
        raise RuntimeError()
    return results

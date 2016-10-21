#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import collections
import json
import os.path
import errno

from enum import Enum

import adal
from azure.cli.core._session import ACCOUNT
from azure.cli.core._util import CLIError, get_file_json
from azure.cli.core.adal_authentication import AdalAuthentication

from azure.cli.core.cloud import get_cloud, CloudEndpoint
from azure.cli.core.context import get_active_context

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

#Names below are used by azure-xplat-cli to persist account information into
#~/.azure/azureProfile.json or osx/keychainer or windows secure storage,
#which azure-cli will share.
#Please do not rename them unless you know what you are doing.
_IS_DEFAULT_SUBSCRIPTION = 'isDefault'
_SUBSCRIPTION_ID = 'id'
_SUBSCRIPTION_NAME = 'name'
_TENANT_ID = 'tenantId'
_USER_ENTITY = 'user'
_USER_NAME = 'name'
_SUBSCRIPTIONS = 'subscriptions'
_INSTALLATION_ID = 'installationId'
_ENVIRONMENT_NAME = 'environmentName'
_STATE = 'state'
_USER_TYPE = 'type'
_USER = 'user'
_SERVICE_PRINCIPAL = 'servicePrincipal'
_SERVICE_PRINCIPAL_ID = 'servicePrincipalId'
_SERVICE_PRINCIPAL_TENANT = 'servicePrincipalTenant'
_TOKEN_ENTRY_USER_ID = 'userId'
_TOKEN_ENTRY_TOKEN_TYPE = 'tokenType'
#This could mean either real access token, or client secret of a service principal
#This naming is no good, but can't change because xplat-cli does so.
_ACCESS_TOKEN = 'accessToken'

TOKEN_FIELDS_EXCLUDED_FROM_PERSISTENCE = ['familyName',
                                          'givenName',
                                          'isUserIdDisplayable',
                                          'tenantId']

_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'
_COMMON_TENANT = 'common'

_AUTH_CTX_FACTORY = lambda authority, cache: adal.AuthenticationContext(authority, cache=cache)

CLOUD = get_cloud(get_active_context()['cloud'])

def get_authority_url(tenant=None):
    return CLOUD.endpoints[CloudEndpoint.ACTIVE_DIRECTORY] + '/' + (tenant or _COMMON_TENANT)

def _load_tokens_from_file(file_path):
    all_entries = []
    if os.path.isfile(file_path):
        all_entries = get_file_json(file_path, throw_on_empty=False) or []
    return all_entries

def _delete_file(file_path):
    try:
        os.remove(file_path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

class CredentialType(Enum): # pylint: disable=too-few-public-methods
    management = CLOUD.endpoints[CloudEndpoint.MANAGEMENT]
    rbac = CLOUD.endpoints[CloudEndpoint.ACTIVE_DIRECTORY_GRAPH_RESOURCE_ID]

class Profile(object):
    def __init__(self, storage=None, auth_ctx_factory=None):
        self._storage = storage or ACCOUNT
        factory = auth_ctx_factory or _AUTH_CTX_FACTORY
        self._creds_cache = CredsCache(factory)
        self._subscription_finder = SubscriptionFinder(factory, self._creds_cache.adal_token_cache)
        self._management_resource_uri = CLOUD.endpoints[CloudEndpoint.MANAGEMENT]

    def find_subscriptions_on_login(self, #pylint: disable=too-many-arguments
                                    interactive,
                                    username,
                                    password,
                                    is_service_principal,
                                    tenant):
        subscriptions = []
        if interactive:
            subscriptions = self._subscription_finder.find_through_interactive_flow(
                self._management_resource_uri)
        else:
            if is_service_principal:
                if not tenant:
                    raise CLIError('Please supply tenant using "--tenant"')

                subscriptions = self._subscription_finder.find_from_service_principal_id(
                    username, password, tenant, self._management_resource_uri)
            else:
                subscriptions = self._subscription_finder.find_from_user_account(
                    username, password, self._management_resource_uri)

        if not subscriptions:
            raise CLIError('No subscriptions found for this account.')

        if is_service_principal:
            self._creds_cache.save_service_principal_cred(username,
                                                          password,
                                                          tenant)
        if self._creds_cache.adal_token_cache.has_state_changed:
            self._creds_cache.persist_cached_creds()
        consolidated = Profile._normalize_properties(self._subscription_finder.user_id,
                                                     subscriptions,
                                                     is_service_principal)
        self._set_subscriptions(consolidated)
        return consolidated

    @staticmethod
    def _normalize_properties(user, subscriptions, is_service_principal):
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
                _ENVIRONMENT_NAME: CLOUD.name
                })
        return consolidated

    def _set_subscriptions(self, new_subscriptions):
        existing_ones = self.load_cached_subscriptions()
        active_one = next((x for x in existing_ones if x.get(_IS_DEFAULT_SUBSCRIPTION)), None)
        active_subscription_id = active_one[_SUBSCRIPTION_ID] if active_one else None

        #merge with existing ones
        dic = collections.OrderedDict((x[_SUBSCRIPTION_ID], x) for x in existing_ones)
        dic.update((x[_SUBSCRIPTION_ID], x) for x in new_subscriptions)
        subscriptions = list(dic.values())

        if active_one:
            new_active_one = next(
                (x for x in new_subscriptions if x[_SUBSCRIPTION_ID] == active_subscription_id),
                None)

            for s in subscriptions:
                s[_IS_DEFAULT_SUBSCRIPTION] = False

            if not new_active_one:
                new_active_one = new_subscriptions[0]
            new_active_one[_IS_DEFAULT_SUBSCRIPTION] = True
        else:
            new_subscriptions[0][_IS_DEFAULT_SUBSCRIPTION] = True

        self._cache_subscriptions_to_local_storage(subscriptions)

    def set_active_subscription(self, subscription_id_or_name):
        subscriptions = self.load_cached_subscriptions()

        subscription_id_or_name = subscription_id_or_name.lower()
        result = [x for x in subscriptions
                  if subscription_id_or_name == x[_SUBSCRIPTION_ID].lower() or
                  subscription_id_or_name == x[_SUBSCRIPTION_NAME].lower()]

        if len(result) != 1:
            raise CLIError('The subscription of "{}" does not exist or has more than'
                           ' one match.'.format(subscription_id_or_name))

        for s in subscriptions:
            s[_IS_DEFAULT_SUBSCRIPTION] = False
        result[0][_IS_DEFAULT_SUBSCRIPTION] = True

        self._cache_subscriptions_to_local_storage(subscriptions)

    def logout(self, user_or_sp):
        subscriptions = self.load_cached_subscriptions()
        result = [x for x in subscriptions
                  if user_or_sp.lower() == x[_USER_ENTITY][_USER_NAME].lower()]
        subscriptions = [x for x in subscriptions if x not in result]

        #reset the active subscription if needed
        result = [x for x in subscriptions if x.get(_IS_DEFAULT_SUBSCRIPTION)]
        if not result and subscriptions:
            subscriptions[0][_IS_DEFAULT_SUBSCRIPTION] = True

        self._cache_subscriptions_to_local_storage(subscriptions)

        self._creds_cache.remove_cached_creds(user_or_sp)

    def logout_all(self):
        self._cache_subscriptions_to_local_storage([])
        self._creds_cache.remove_all_cached_creds()

    def load_cached_subscriptions(self):
        return self._storage.get(_SUBSCRIPTIONS) or []

    def _cache_subscriptions_to_local_storage(self, subscriptions):
        self._storage[_SUBSCRIPTIONS] = subscriptions

    def get_current_account_user(self):
        try:
            active_account = self.get_subscription()
        except CLIError:
            raise CLIError('There are no active accounts.')

        return active_account[_USER_ENTITY][_USER_NAME]

    def get_subscription(self, subscription_id=None):
        subscriptions = self.load_cached_subscriptions()
        if not subscriptions:
            raise CLIError("Please run 'az login' to setup account.")

        result = [x for x in subscriptions if (
            subscription_id is None and x.get(_IS_DEFAULT_SUBSCRIPTION)) or
                  (subscription_id == x.get(_SUBSCRIPTION_ID))]
        if len(result) != 1:
            raise CLIError("Please run 'az account set' to select active account.")
        return result[0]

    def get_login_credentials(self, resource=CLOUD.endpoints[CloudEndpoint.MANAGEMENT],
                              subscription_id=None):
        account = self.get_subscription(subscription_id)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        if user_type == _USER:
            token_retriever = lambda: self._creds_cache.retrieve_token_for_user(
                username_or_sp_id, account[_TENANT_ID], resource)
            auth_object = AdalAuthentication(token_retriever)
        else:
            token_retriever = lambda: self._creds_cache.retrieve_token_for_service_principal(
                username_or_sp_id, resource)
            auth_object = AdalAuthentication(token_retriever)

        return (auth_object,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def get_installation_id(self):
        installation_id = self._storage.get(_INSTALLATION_ID)
        if not installation_id:
            import uuid
            installation_id = str(uuid.uuid1())
            self._storage[_INSTALLATION_ID] = installation_id
        return installation_id

class SubscriptionFinder(object):
    '''finds all subscriptions for a user or service principal'''
    def __init__(self, auth_context_factory, adal_token_cache, arm_client_factory=None):
        from azure.mgmt.resource.subscriptions import SubscriptionClient

        self._adal_token_cache = adal_token_cache
        self._auth_context_factory = auth_context_factory
        self.user_id = None # will figure out after log user in
        self._arm_client_factory = arm_client_factory or \
             (lambda config: SubscriptionClient(config, base_url=CLOUD.endpoints[CloudEndpoint.RESOURCE_MANAGER])) #pylint: disable=unnecessary-lambda, line-too-long

    def find_from_user_account(self, username, password, resource):
        context = self._create_auth_context(_COMMON_TENANT)
        token_entry = context.acquire_token_with_username_password(
            resource,
            username,
            password,
            _CLIENT_ID)
        self.user_id = token_entry[_TOKEN_ENTRY_USER_ID]
        result = self._find_using_common_tenant(token_entry[_ACCESS_TOKEN], resource)
        return result

    def find_through_interactive_flow(self, resource):
        context = self._create_auth_context(_COMMON_TENANT)
        code = context.acquire_user_code(resource, _CLIENT_ID)
        logger.warning(code['message'])
        token_entry = context.acquire_token_with_device_code(resource, code, _CLIENT_ID)
        self.user_id = token_entry[_TOKEN_ENTRY_USER_ID]
        result = self._find_using_common_tenant(token_entry[_ACCESS_TOKEN], resource)
        return result

    def find_from_service_principal_id(self, client_id, secret, tenant, resource):
        context = self._create_auth_context(tenant, False)
        token_entry = context.acquire_token_with_client_credentials(
            resource,
            client_id,
            secret)
        self.user_id = client_id
        result = self._find_using_specific_tenant(tenant, token_entry[_ACCESS_TOKEN])
        return result

    def _create_auth_context(self, tenant, use_token_cache=True):
        token_cache = self._adal_token_cache if use_token_cache else None
        authority = get_authority_url(tenant)
        return self._auth_context_factory(authority, token_cache)

    def _find_using_common_tenant(self, access_token, resource):
        from msrest.authentication import BasicTokenAuthentication

        all_subscriptions = []
        token_credential = BasicTokenAuthentication({'access_token': access_token})
        client = self._arm_client_factory(token_credential)
        tenants = client.tenants.list()
        for t in tenants:
            tenant_id = t.tenant_id
            temp_context = self._create_auth_context(tenant_id)
            temp_credentials = temp_context.acquire_token(resource, self.user_id, _CLIENT_ID)
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
        return all_subscriptions

class CredsCache(object):
    '''Caches AAD tokena and service principal secrets, and persistence will
    also be handled
    '''
    def __init__(self, auth_ctx_factory=None):
        self._token_file = os.path.expanduser('~/.azure/accessTokens.json')
        self._service_principal_creds = []
        self._auth_ctx_factory = auth_ctx_factory or _AUTH_CTX_FACTORY
        self.adal_token_cache = None
        self._load_creds()

    def persist_cached_creds(self):
        with os.fdopen(os.open(self._token_file, os.O_RDWR|os.O_CREAT|os.O_TRUNC, 0o600),
                       'w+') as cred_file:
            items = self.adal_token_cache.read_items()
            all_creds = [entry for _, entry in items]

            #trim away useless fields (needed for cred sharing with xplat)
            for i in all_creds:
                for key in TOKEN_FIELDS_EXCLUDED_FROM_PERSISTENCE:
                    i.pop(key, None)

            all_creds.extend(self._service_principal_creds)
            cred_file.write(json.dumps(all_creds))

        self.adal_token_cache.has_state_changed = False

    def retrieve_token_for_user(self, username, tenant, resource):
        authority = get_authority_url(tenant)
        context = self._auth_ctx_factory(authority, cache=self.adal_token_cache)
        token_entry = context.acquire_token(resource, username, _CLIENT_ID)
        if not token_entry:
            raise CLIError("Could not retrieve token from local cache, please run 'az login'.")

        if self.adal_token_cache.has_state_changed:
            self.persist_cached_creds()
        return (token_entry[_TOKEN_ENTRY_TOKEN_TYPE], token_entry[_ACCESS_TOKEN])

    def retrieve_token_for_service_principal(self, sp_id, resource):
        matched = [x for x in self._service_principal_creds if sp_id == x[_SERVICE_PRINCIPAL_ID]]
        if not matched:
            raise CLIError("Please run 'az account set' to select active account.")
        cred = matched[0]
        authority_url = get_authority_url(cred[_SERVICE_PRINCIPAL_TENANT])
        context = self._auth_ctx_factory(authority_url, None)
        token_entry = context.acquire_token_with_client_credentials(resource,
                                                                    sp_id,
                                                                    cred[_ACCESS_TOKEN])
        return (token_entry[_TOKEN_ENTRY_TOKEN_TYPE], token_entry[_ACCESS_TOKEN])

    def _load_creds(self):
        if self.adal_token_cache is not None:
            return self.adal_token_cache
        all_entries = _load_tokens_from_file(self._token_file)
        self._load_service_principal_creds(all_entries)
        real_token = [x for x in all_entries if x not in self._service_principal_creds]
        self.adal_token_cache = adal.TokenCache(json.dumps(real_token))
        return self.adal_token_cache

    def save_service_principal_cred(self, service_principal_id, secret, tenant):
        entry = {
            _SERVICE_PRINCIPAL_ID: service_principal_id,
            _SERVICE_PRINCIPAL_TENANT: tenant,
            _ACCESS_TOKEN: secret
            }

        matched = [x for x in self._service_principal_creds
                   if service_principal_id == x[_SERVICE_PRINCIPAL_ID] and
                   tenant == x[_SERVICE_PRINCIPAL_TENANT]]
        state_changed = False
        if matched:
            if matched[0][_ACCESS_TOKEN] != secret:
                matched[0] = entry
                state_changed = True
        else:
            self._service_principal_creds.append(entry)
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
        #clear AAD tokens
        tokens = self.adal_token_cache.find({_TOKEN_ENTRY_USER_ID: user_or_sp})
        if tokens:
            state_changed = True
            self.adal_token_cache.remove(tokens)

        #clear service principal creds
        matched = [x for x in self._service_principal_creds
                   if x[_SERVICE_PRINCIPAL_ID] == user_or_sp]
        if matched:
            state_changed = True
            self._service_principal_creds = [x for x in self._service_principal_creds
                                             if x not in matched]

        if state_changed:
            self.persist_cached_creds()

    def remove_all_cached_creds(self):
        #we can clear file contents, but deleting it is simpler
        _delete_file(self._token_file)

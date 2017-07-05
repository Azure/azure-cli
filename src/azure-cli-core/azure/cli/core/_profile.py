# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import collections
import errno
import json
import os.path
from copy import deepcopy
from enum import Enum

from azure.cli.core._environment import get_config_dir
from azure.cli.core._session import ACCOUNT
from azure.cli.core.util import get_file_json
from azure.cli.core.cloud import get_active_cloud, set_cloud_subscription, init_known_clouds

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

_MSI_ACCOUNT_NAME = 'MSI'

def _authentication_context_factory(cli_ctx, tenant, cache):
    import adal
    authority_url = get_active_cloud(cli_ctx).endpoints.active_directory
    is_adfs = authority_url.lower().endswith('/adfs')
    if not is_adfs:
        authority_url = authority_url + '/' + (tenant or _COMMON_TENANT)
    return adal.AuthenticationContext(authority_url, cache=cache, api_version=None,
                                      validate_authority=(not is_adfs))

_AUTH_CTX_FACTORY = _authentication_context_factory

init_known_clouds(force=True)

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


def get_credential_types(cli_ctx):

    class CredentialType(Enum):  # pylint: disable=too-few-public-methods
        cloud = get_active_cloud(cli_ctx)
        management = self.cloud.endpoints.management
        rbac = self.cloud.endpoints.active_directory_graph_resource_id

    return CredentialType

class Profile(object):
    def __init__(self, cli_ctx, storage=None, auth_ctx_factory=None, use_global_creds_cache=True):
        self.ctx = cli_ctx
        self._storage = storage or ACCOUNT
        self.auth_ctx_factory = auth_ctx_factory or _AUTH_CTX_FACTORY
        if use_global_creds_cache:
            self._creds_cache = CredsCache(cli_ctx, _AUTH_CTX_FACTORY, async_persist=True)
        else:
            self._creds_cache = CredsCache(self.auth_ctx_factory, async_persist=False)
        self._management_resource_uri = cli_ctx.cloud.endpoints.management
        self._ad_resource_uri = cli_ctx.cloud.endpoints.active_directory_resource_id
        self._msi_creds = None

    def find_subscriptions_on_login(self,
                                    interactive,
                                    username,
                                    password,
                                    is_service_principal,
                                    tenant,
                                    allow_no_subscriptions=False,
                                    subscription_finder=None):
        from azure.cli.core._debug import allow_debug_adal_connection
        allow_debug_adal_connection()
        subscriptions = []

        if not subscription_finder:
            subscription_finder = SubscriptionFinder(self.ctx,
                                                     self.auth_ctx_factory,
                                                     self._creds_cache.adal_token_cache)
        if interactive:
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
            subscriptions = Profile._build_tenant_level_accounts(bare_tenants)
            if not subscriptions:
                return []

        consolidated = self._normalize_properties(subscription_finder.user_id, subscriptions, is_service_principal)

        self._set_subscriptions(consolidated)
        # use deepcopy as we don't want to persist these changes to file.
        return deepcopy(consolidated)

    def find_subscriptions_in_cloud_console(self, tokens):
        from datetime import datetime, timedelta
        import jwt
        arm_token = tokens[0]  # cloud shell gurantees that the 1st is for ARM
        arm_token_decoded = jwt.decode(arm_token, verify=False, algorithms=['RS256'])
        tenant = arm_token_decoded['tid']
        user_id = arm_token_decoded['unique_name'].split('#')[-1]
        subscription_finder = SubscriptionFinder(self.auth_ctx_factory, None)
        subscriptions = subscription_finder.find_from_raw_token(tenant, arm_token)
        consolidated = Profile._normalize_properties(user_id, subscriptions, is_service_principal=False)
        self._set_subscriptions(consolidated)

        # construct token entries to cache
        decoded_tokens = [arm_token_decoded]
        for t in tokens[1:]:
            decoded_tokens.append(jwt.decode(t, verify=False, algorithms=['RS256']))
        final_tokens = []
        for t in decoded_tokens:
            final_tokens.append({
                '_clientId': _CLIENT_ID,
                'expiresIn': '3600',
                'expiresOn': str(datetime.utcnow() + timedelta(seconds=3600 * 24)),
                'userId': t['unique_name'].split('#')[-1],
                '_authority': CLOUD.endpoints.active_directory.rstrip('/') + '/' + t['tid'],
                'resource': t['aud'],
                'isMRRT': True,
                'accessToken': tokens[decoded_tokens.index(t)],
                'tokenType': 'Bearer',
                'oid': t['oid']
            })

        # merging with existing cached ones
        for t in final_tokens:
            cached_tokens = [entry for _, entry in self._creds_cache.adal_token_cache.read_items()]
            to_delete = [c for c in cached_tokens if (c['_clientId'].lower() == t['_clientId'].lower() and
                                                      c['resource'].lower() == t['resource'].lower() and
                                                      c['_authority'].lower() == t['_authority'].lower() and
                                                      c['userId'].lower() == t['userId'].lower())]
            if to_delete:
                self._creds_cache.adal_token_cache.remove(to_delete)
        self._creds_cache.adal_token_cache.add(final_tokens)
        self._creds_cache.persist_cached_creds()

        return deepcopy(consolidated)

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
                _ENVIRONMENT_NAME: self.ctx.cloud.name
            })
        return consolidated

    @staticmethod
    def _build_tenant_level_accounts(tenants):
        from azure.cli.core.profiles import ResourceType
        SubscriptionType = cli_ctx.cloud.get_sdk(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS,
                                                 'Subscription', mod='models')
        StateType = cli_ctx.cloud.get_sdk(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS,
                                          'SubscriptionState', mod='models')
        result = []
        for t in tenants:
            s = Profile._new_account()
            s.id = '/subscriptions/' + t
            s.subscription = t
            s.tenant_id = t
            s.display_name = 'N/A(tenant level account)'
            result.append(s)
        return result

    @staticmethod
    def _new_account():
        from azure.cli.core.profiles import get_sdk, ResourceType
        SubscriptionType, StateType = get_sdk(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS,
                                              'Subscription', 'SubscriptionState', mod='models')
        s = SubscriptionType()
        s.state = StateType.enabled
        return s

    def init_if_in_msi_env(self, user):
        _, subscription_id = Profile.split_msi_user_info(user)
        if subscription_id is None:
            return None
        logger.info('MSI: environment was detected. Now trying to initialize a local account...')
        tenant_id = Profile.get_msi_tenant_id(CLOUD.endpoints.resource_manager, subscription_id)
        s = Profile._new_account()
        s.id = '/subscriptions/' + subscription_id
        s.tenant_id = tenant_id
        s.display_name = _MSI_ACCOUNT_NAME
        consolidated = Profile._normalize_properties(user, [s], False)
        self._set_subscriptions(consolidated)
        # use deepcopy as we don't want to persist these changes to file.
        return deepcopy(consolidated)

    def _set_subscriptions(self, new_subscriptions):
        existing_ones = self.load_cached_subscriptions(all_clouds=True)
        active_one = next((x for x in existing_ones if x.get(_IS_DEFAULT_SUBSCRIPTION)), None)
        active_subscription_id = active_one[_SUBSCRIPTION_ID] if active_one else None
        active_cloud = get_active_cloud(self.ctx)
        default_sub_id = None

        # merge with existing ones
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
                new_active_one = Profile._pick_working_subscription(new_subscriptions)
        else:
            new_active_one = Profile._pick_working_subscription(new_subscriptions)

        new_active_one[_IS_DEFAULT_SUBSCRIPTION] = True
        default_sub_id = new_active_one[_SUBSCRIPTION_ID]

        set_cloud_subscription(self.ctx, active_cloud.name, default_sub_id)
        self._storage[_SUBSCRIPTIONS] = subscriptions

    @staticmethod
    def _pick_working_subscription(subscriptions):
        from azure.mgmt.resource.subscriptions.models import SubscriptionState
        s = next((x for x in subscriptions if x['state'] == SubscriptionState.enabled.value), None)
        return s or subscriptions[0]

    def set_active_subscription(self, subscription):  # take id or name
        subscriptions = self.load_cached_subscriptions(all_clouds=True)
        active_cloud = get_active_cloud(self.ctx)
        subscription = subscription.lower()
        result = [x for x in subscriptions
                  if subscription in [x[_SUBSCRIPTION_ID].lower(),
                                      x[_SUBSCRIPTION_NAME].lower()] and
                  x[_ENVIRONMENT_NAME] == active_cloud.name]

        if len(result) != 1:
            raise CLIError("The subscription of '{}' does not exist or has more than"
                           " one match in cloud '{}'.".format(subscription, active_cloud.name))

        for s in subscriptions:
            s[_IS_DEFAULT_SUBSCRIPTION] = False
        result[0][_IS_DEFAULT_SUBSCRIPTION] = True

        set_cloud_subscription(self.ctx, active_cloud.name, result[0][_SUBSCRIPTION_ID])
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
        active_cloud = self.ctx.cloud
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
        if len(result) != 1:
            raise CLIError("Please run 'az account set' to select active account.")
        return result[0]

    def get_subscription_id(self):
        return self.get_subscription()[_SUBSCRIPTION_ID]

    def get_access_token_for_resource(self, username, tenant, resource):
        tenant = tenant or 'common'
        _, access_token, _ = self._creds_cache.retrieve_token_for_user(
            username, tenant, resource)
        return access_token

    def get_login_credentials(self, resource=None,
                              subscription_id=None):
        account = self.get_subscription(subscription_id)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        resource = resource or get_active_cloud(self.ctx).endpoints.active_directory_resource_id

        def _retrieve_token():
            if account[_SUBSCRIPTION_NAME] == _MSI_ACCOUNT_NAME:
                port, _ = Profile.split_msi_user_info(username_or_sp_id)
                return Profile.get_msi_token(resource, CLOUD.endpoints.active_directory, account[_TENANT_ID], port)
            elif user_type == _USER:
                return self._creds_cache.retrieve_token_for_user(username_or_sp_id,
                                                                 account[_TENANT_ID], resource)
            return self._creds_cache.retrieve_token_for_service_principal(username_or_sp_id, resource)

        from azure.cli.core.adal_authentication import AdalAuthentication
        auth_object = AdalAuthentication(_retrieve_token)

        return (auth_object,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

    def get_refresh_token(self, resource=None,
                          subscription=None):
        account = self.get_subscription(subscription)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        resource = resource or get_active_cloud(self.ctx).endpoints.active_directory_resource_id

        if user_type == _USER:
            _, _, token_entry = self._creds_cache.retrieve_token_for_user(
                username_or_sp_id, account[_TENANT_ID], resource)
            return None, token_entry[_REFRESH_TOKEN], token_entry[_ACCESS_TOKEN], str(account[_TENANT_ID])

        sp_secret = self._creds_cache.retrieve_secret_of_service_principal(username_or_sp_id)
        return username_or_sp_id, sp_secret, None, str(account[_TENANT_ID])

    def get_raw_token(self, resource=None, subscription=None):
        account = self.get_subscription(subscription)
        user_type = account[_USER_ENTITY][_USER_TYPE]
        username_or_sp_id = account[_USER_ENTITY][_USER_NAME]
        resource = resource or self.ctx.cloud.endpoints.active_directory_resource_id

        if user_type == _USER:
            creds = self._creds_cache.retrieve_token_for_user(username_or_sp_id,
                                                              account[_TENANT_ID], resource)
        else:
            creds = self._creds_cache.retrieve_token_for_service_principal(username_or_sp_id,
                                                                           resource)
        return (creds,
                str(account[_SUBSCRIPTION_ID]),
                str(account[_TENANT_ID]))

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
            result[endpoint_mappings[e]] = getattr(get_active_cloud(self.ctx).endpoints, e)
        return result

    def get_installation_id(self):
        installation_id = self._storage.get(_INSTALLATION_ID)
        if not installation_id:
            import uuid
            installation_id = str(uuid.uuid1())
            self._storage[_INSTALLATION_ID] = installation_id
        return installation_id

    @staticmethod
    def split_msi_user_info(user):
        import uuid
        parts = user.split('@')
        if len(parts) == 2:
            try:
                uuid.UUID(parts[0])  # valid subscription id?
                int(parts[1])  # valid port?
                return parts[1], parts[0]
            except ValueError:
                pass
        return None, None

    @staticmethod
    def get_msi_tenant_id(arm_endpoint, subscription_id):
        import re
        import requests
        url = '{}/subscriptions/{}?api-version=2014-04-01'.format(arm_endpoint.rstrip('/'), subscription_id)
        logger.debug('MSI: Retrieving tenant id by invoking GET from %s', url)
        result = requests.get(url)
        if result.status_code != 401:
            raise CLIError('Failed to retrieve the tenant id of subscription {}'.format(subscription_id))
        exp = r'.+authorization_uri="(.*?)".+'
        r = re.match(exp, result.headers['www-authenticate'])
        tenant_id = r.group(1).split('/')[-1]
        logger.debug('MSI: Got tenant id: %s', tenant_id)
        return tenant_id

    @staticmethod
    def get_msi_token(resource, aad_endpoint, tenant_id, port):
        import requests
        import time
        request_uri = 'http://localhost:{}/oauth2/token'.format(port)
        payload = {
            'authority': '{}/{}'.format(aad_endpoint, tenant_id),
            'resource': resource
        }

        # retry as the token endpoint might not be available yet, one example is you use CLI in a
        # custom script extension of VMSS, which might get provisioned before the MSI extensioon
        while True:
            err = None
            try:
                result = requests.post(request_uri, data=payload)
                logger.debug("MSI: Retrieving a token from %s, with payload %s", request_uri, payload)
                if result.status_code != 200:
                    err = result.text
            except Exception as ex:  # pylint: disable=broad-except
                err = str(ex)

            if err:
                # we might need some error code checking to avoid silly waiting. The bottom line is users can
                # always press ctrl+c to stop it
                logger.warning("MSI: Failed to retrieve a token from '%s' with an error of '%s'. This could be caused "
                               "by the MSI extension not yet fullly provisioned. Will retry in 60 seconds...",
                               request_uri, err)
                time.sleep(60)
            else:
                logger.debug('MSI: token retrieved')
                break
        token_entry = json.loads(result.content.decode())
        return token_entry['token_type'], token_entry['access_token'], token_entry


class SubscriptionFinder(object):
    '''finds all subscriptions for a user or service principal'''

    def __init__(self, cli_ctx, auth_context_factory, adal_token_cache, arm_client_factory=None):

        self._adal_token_cache = adal_token_cache
        self._auth_context_factory = auth_context_factory
        self.user_id = None  # will figure out after log user in
        self.ctx = cli_ctx

        def create_arm_client_factory(credentials):
            if arm_client_factory:
                return arm_client_factory(credentials)
            from azure.cli.core.profiles._shared import get_client_class
            from azure.cli.core.profiles import ResourceType
            from azure.cli.core._debug import change_ssl_cert_verification
            client_type = get_client_class(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
            api_version = cli_ctx.cloud.get_api_version(ResourceType.MGMT_RESOURCE_SUBSCRIPTIONS)
            return change_ssl_cert_verification(client_type(credentials, api_version=api_version,
                                                            base_url=get_active_cloud(self.ctx).endpoints.resource_manager))

        self._arm_client_factory = create_arm_client_factory
        self.tenants = []

    def find_from_user_account(self, username, password, tenant, resource):
        context = self._create_auth_context(tenant)
        token_entry = context.acquire_token_with_username_password(
            resource,
            username,
            password,
            _CLIENT_ID)
        self.user_id = token_entry[_TOKEN_ENTRY_USER_ID]

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

    #  only occur inside cloud console
    def find_from_raw_token(self, tenant, token):
        # decode the token, so we know the tenant
        result = self._find_using_specific_tenant(tenant, token)
        self.tenants = [tenant]
        return result

    def _create_auth_context(self, tenant, use_token_cache=True):
        token_cache = self._adal_token_cache if use_token_cache else None
        return self._auth_context_factory(self.ctx, tenant, token_cache)

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
            raise CLIError("Could not retrieve token from local cache, please run 'az login'.")

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
        return cred[_ACCESS_TOKEN]

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
            if (sp_entry.get(_ACCESS_TOKEN, None) != getattr(matched[0], _ACCESS_TOKEN, None) or
                    sp_entry.get(_SERVICE_PRINCIPAL_CERT_FILE, None) != getattr(matched[0], _SERVICE_PRINCIPAL_CERT_FILE, None)):
                self._service_principal_creds.remove(matched[0])
                self._service_principal_creds.append(matched[0])
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

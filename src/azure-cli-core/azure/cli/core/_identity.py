# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json

from ._environment import get_config_dir
from .util import get_file_json

from knack.util import CLIError
from knack.log import get_logger

from azure.identity import (
    AuthenticationRecord,
    InteractiveBrowserCredential,
    DeviceCodeCredential,
    UsernamePasswordCredential,
    ClientSecretCredential,
    CertificateCredential,
    ManagedIdentityCredential,
    EnvironmentCredential
)

AZURE_CLI_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

logger = get_logger(__name__)

_SERVICE_PRINCIPAL_ID = 'servicePrincipalId'
_SERVICE_PRINCIPAL_TENANT = 'servicePrincipalTenant'
_ACCESS_TOKEN = 'accessToken'
_SERVICE_PRINCIPAL_CERT_FILE = 'certificateFile'
_SERVICE_PRINCIPAL_CERT_THUMBPRINT = 'thumbprint'


class Identity:
    """Class to interact with Azure Identity.
    """
    MANAGED_IDENTITY_TENANT_ID = "tenant_id"
    MANAGED_IDENTITY_CLIENT_ID = "client_id"
    MANAGED_IDENTITY_OBJECT_ID = "object_id"
    MANAGED_IDENTITY_RESOURCE_ID = "resource_id"
    MANAGED_IDENTITY_SYSTEM_ASSIGNED = 'systemAssignedIdentity'
    MANAGED_IDENTITY_USER_ASSIGNED = 'userAssignedIdentity'
    MANAGED_IDENTITY_TYPE = 'type'
    MANAGED_IDENTITY_ID_TYPE = "id_type"

    CLOUD_SHELL_IDENTITY_UNIQUE_NAME = "unique_name"

    def __init__(self, authority=None, tenant_id=None, client_id=None, scopes=None, **kwargs):
        """

        :param authority:
        :param tenant_id:
        :param client_id:
        :param scopes: Scopes for the `authenticate` method call (initial /authorize API)
        :param kwargs:
        """
        self.authority = authority
        self.tenant_id = tenant_id or "organizations"
        self.client_id = client_id or AZURE_CLI_CLIENT_ID
        self._cred_cache = kwargs.pop('cred_cache', None)
        self.allow_unencrypted = kwargs.pop('allow_unencrypted', True)
        self.scopes = scopes
        if self.scopes and not isinstance(self.scopes, (list, tuple)):
            self.scopes = (self.scopes,)
        self._msal_app_instance = None
        # Store for Service principal credential persistence
        self._msal_secret_store = MsalSecretStore(fallback_to_plaintext=self.allow_unencrypted)

        # TODO: Allow disabling SSL verification
        # The underlying requests lib of MSAL has been patched with Azure Core by MsalTransportAdapter
        # connection_verify will be received by azure.core.configuration.ConnectionConfiguration
        # However, MSAL defaults verify to True, thus overriding ConnectionConfiguration
        # Still not work yet
        from azure.cli.core._debug import change_ssl_cert_verification_track2
        self.credential_kwargs = {}
        self.credential_kwargs.update(change_ssl_cert_verification_track2())

    def _build_persistent_msal_app(self, authority):
        # Initialize _msal_app for logout, since Azure Identity doesn't provide the functionality for logout
        from msal import PublicClientApplication
        # sdk/identity/azure-identity/azure/identity/_internal/msal_credentials.py:95
        from azure.identity._internal.persistent_cache import load_user_cache

        # Store for user token persistence
        cache = load_user_cache(self.allow_unencrypted)
        msal_app = PublicClientApplication(authority=authority, client_id=self.client_id,
                                           token_cache=cache,
                                           verify=self.credential_kwargs.get('connection_verify', True))
        return msal_app

    @property
    def _msal_app(self):
        if not self._msal_app_instance:
            # Build the authority in MSAL style, like https://login.microsoftonline.com/your_tenant
            msal_authority = "https://{}/{}".format(self.authority, self.tenant_id)
            self._msal_app_instance = self._build_persistent_msal_app(msal_authority)
        return self._msal_app_instance

    def login_with_interactive_browser(self):
        # Use InteractiveBrowserCredential
        credential = InteractiveBrowserCredential(authority=self.authority,
                                                  tenant_id=self.tenant_id,
                                                  client_id=self.client_id,
                                                  enable_persistent_cache=True,
                                                  allow_unencrypted_cache=self.allow_unencrypted,
                                                  **self.credential_kwargs)
        auth_record = credential.authenticate(scopes=self.scopes)
        # todo: remove after ADAL token deprecation
        if self._cred_cache:
            self._cred_cache.add_credential(credential)
        return credential, auth_record

    def login_with_device_code(self):
        # Use DeviceCodeCredential
        def prompt_callback(verification_uri, user_code, _):
            # expires_on is discarded
            logger.warning("To sign in, use a web browser to open the page %s and enter the code %s to authenticate.",
                           verification_uri, user_code)
        try:
            credential = DeviceCodeCredential(authority=self.authority,
                                              tenant_id=self.tenant_id,
                                              client_id=self.client_id,
                                              enable_persistent_cache=True,
                                              prompt_callback=prompt_callback,
                                              allow_unencrypted_cache=self.allow_unencrypted,
                                              **self.credential_kwargs)

            auth_record = credential.authenticate(scopes=self.scopes)
            # todo: remove after ADAL token deprecation
            if self._cred_cache:
                self._cred_cache.add_credential(credential)
            return credential, auth_record
        except ValueError as ex:
            logger.debug('Device code authentication failed: %s', str(ex))
            if 'PyGObject' in str(ex):
                raise CLIError("PyGObject is required to encrypt the persistent cache. Please install that lib or "
                               "allow fallback to plaintext if encrypt credential fail via 'az configure'.")
            raise

    def login_with_username_password(self, username, password):
        # Use UsernamePasswordCredential
        credential = UsernamePasswordCredential(authority=self.authority,
                                                tenant_id=self.tenant_id,
                                                client_id=self.client_id,
                                                username=username,
                                                password=password,
                                                enable_persistent_cache=True,
                                                allow_unencrypted_cache=self.allow_unencrypted,
                                                **self.credential_kwargs)
        auth_record = credential.authenticate(scopes=self.scopes)

        # todo: remove after ADAL token deprecation
        if self._cred_cache:
            self._cred_cache.add_credential(credential)
        return credential, auth_record

    def login_with_service_principal_secret(self, client_id, client_secret):
        # Use ClientSecretCredential
        # TODO: Persist to encrypted cache
        # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/pull/44
        sp_auth = ServicePrincipalAuth(client_id, self.tenant_id, secret=client_secret)
        entry = sp_auth.get_entry_to_persist()
        self._msal_secret_store.save_service_principal_cred(entry)
        # backward compatible with ADAL, to be deprecated
        if self._cred_cache:
            self._cred_cache.save_service_principal_cred(entry)

        credential = ClientSecretCredential(self.tenant_id, client_id, client_secret, authority=self.authority)
        return credential

    def login_with_service_principal_certificate(self, client_id, certificate_path):
        # Use CertificateCredential
        # TODO: Persist to encrypted cache
        # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/pull/44
        sp_auth = ServicePrincipalAuth(client_id, self.tenant_id, certificate_file=certificate_path)
        entry = sp_auth.get_entry_to_persist()
        self._msal_secret_store.save_service_principal_cred(entry)
        # backward compatible with ADAL, to be deprecated
        if self._cred_cache:
            self._cred_cache.save_service_principal_cred(entry)

        # TODO: support use_cert_sn_issuer in CertificateCredential
        credential = CertificateCredential(self.tenant_id, client_id, certificate_path, authority=self.authority)
        return credential

    def login_with_managed_identity(self, identity_id=None):  # pylint: disable=too-many-statements
        from msrestazure.tools import is_valid_resource_id
        from requests import HTTPError
        from azure.core.exceptions import ClientAuthenticationError

        credential = None
        id_type = None
        token = None
        # scope = resource.rstrip('/') + '/.default'
        # https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/how-to-use-vm-token#get-a-token-using-http
        if identity_id:
            # Try resource ID
            if is_valid_resource_id(identity_id):
                credential = ManagedIdentityCredential(identity_config={"mi_res_id": identity_id})
                token = credential.get_token(*self.scopes)
                id_type = self.MANAGED_IDENTITY_RESOURCE_ID
            else:
                authenticated = False
                try:
                    # Try client ID
                    credential = ManagedIdentityCredential(client_id=identity_id)
                    token = credential.get_token(*self.scopes)
                    id_type = self.MANAGED_IDENTITY_CLIENT_ID
                    authenticated = True
                except ClientAuthenticationError as e:
                    logger.debug('Managed Identity authentication error: %s', e.message)
                    logger.info('Username is not an MSI client id')
                except HTTPError as ex:
                    if ex.response.reason == 'Bad Request' and ex.response.status == 400:
                        logger.info('Username is not an MSI client id')
                    else:
                        raise

                if not authenticated:
                    try:
                        # Try object ID
                        credential = ManagedIdentityCredential(identity_config={"object_id": identity_id})
                        token = credential.get_token(*self.scopes)
                        id_type = self.MANAGED_IDENTITY_OBJECT_ID
                        authenticated = True
                    except ClientAuthenticationError as e:
                        logger.debug('Managed Identity authentication error: %s', e.message)
                        logger.info('Username is not an MSI object id')
                    except HTTPError as ex:
                        if ex.response.reason == 'Bad Request' and ex.response.status == 400:
                            logger.info('Username is not an MSI object id')
                        else:
                            raise

                if not authenticated:
                    raise CLIError('Failed to connect to MSI, check your managed service identity id.')

        else:
            # Use the default managed identity. It can be either system assigned or user assigned.
            credential = ManagedIdentityCredential()
            token = credential.get_token(*self.scopes)

        decoded = Identity._decode_managed_identity_token(token)
        resource_id = decoded.get('xms_mirid')
        # User-assigned identity has resourceID as
        # /subscriptions/xxx/resourcegroups/xxx/providers/Microsoft.ManagedIdentity/userAssignedIdentities/xxx
        if resource_id and 'Microsoft.ManagedIdentity' in resource_id:
            mi_type = self.MANAGED_IDENTITY_USER_ASSIGNED
        else:
            mi_type = self.MANAGED_IDENTITY_SYSTEM_ASSIGNED

        managed_identity_info = {
            self.MANAGED_IDENTITY_TYPE: mi_type,
            # The type of the ID provided with --username, only valid for a user-assigned managed identity
            self.MANAGED_IDENTITY_ID_TYPE: id_type,
            self.MANAGED_IDENTITY_TENANT_ID: decoded['tid'],
            self.MANAGED_IDENTITY_CLIENT_ID: decoded['appid'],
            self.MANAGED_IDENTITY_OBJECT_ID: decoded['oid'],
            self.MANAGED_IDENTITY_RESOURCE_ID: resource_id,
        }
        logger.debug('Using Managed Identity: %s', json.dumps(managed_identity_info))

        return credential, managed_identity_info

    def login_in_cloud_shell(self):
        credential = ManagedIdentityCredential()
        token = credential.get_token(*self.scopes)
        decoded = Identity._decode_managed_identity_token(token)

        cloud_shell_identity_info = {
            self.MANAGED_IDENTITY_TENANT_ID: decoded['tid'],
            # For getting the user email in Cloud Shell, maybe 'email' can also be used
            self.CLOUD_SHELL_IDENTITY_UNIQUE_NAME: decoded.get('unique_name', 'N/A')
        }
        logger.warning('Using Cloud Shell Managed Identity: %s', json.dumps(cloud_shell_identity_info))
        return credential, cloud_shell_identity_info

    def logout_user(self, user):
        accounts = self._msal_app.get_accounts(user)
        logger.info('Before account removal:')
        logger.info(json.dumps(accounts))

        # `accounts` are the same user in all tenants, log out all of them
        for account in accounts:
            self._msal_app.remove_account(account)

        accounts = self._msal_app.get_accounts(user)
        logger.info('After account removal:')
        logger.info(json.dumps(accounts))

    def logout_sp(self, sp):
        # remove service principal secrets
        self._msal_secret_store.remove_cached_creds(sp)

    def logout_all(self):
        # TODO: Support multi-authority logout
        accounts = self._msal_app.get_accounts()
        logger.info('Before account removal:')
        logger.info(json.dumps(accounts))

        for account in accounts:
            self._msal_app.remove_account(account)

        accounts = self._msal_app.get_accounts()
        logger.info('After account removal:')
        logger.info(json.dumps(accounts))
        # remove service principal secrets
        self._msal_secret_store.remove_all_cached_creds()

    def get_user(self, user=None):
        accounts = self._msal_app.get_accounts(user) if user else self._msal_app.get_accounts()
        return accounts

    def get_user_credential(self, username):
        accounts = self._msal_app.get_accounts(username)

        # TODO: Confirm with MSAL team that username can uniquely identify the account
        if not accounts:
            raise CLIError("User {} doesn't exist in the credential cache. The user could have been logged out by "
                           "another application that uses Single Sign-On. "
                           "Please run `az login` to re-login.".format(username))
        account = accounts[0]
        auth_record = AuthenticationRecord(self.tenant_id, self.client_id, self.authority,
                                           account['home_account_id'], username)
        return InteractiveBrowserCredential(authentication_record=auth_record, disable_automatic_authentication=True,
                                            enable_persistent_cache=True,
                                            allow_unencrypted_cache=self.allow_unencrypted,
                                            **self.credential_kwargs)

    def get_service_principal_credential(self, client_id, use_cert_sn_issuer):
        client_secret, certificate_path = \
            self._msal_secret_store.retrieve_secret_of_service_principal(client_id, self.tenant_id)
        # TODO: support use_cert_sn_issuer in CertificateCredential
        if client_secret:
            return ClientSecretCredential(self.tenant_id, client_id, client_secret)
        if certificate_path:
            return CertificateCredential(self.tenant_id, client_id, certificate_path)
        raise CLIError("Secret of service principle {} not found. Please run 'az login'".format(client_id))

    def get_environment_credential(self):
        return EnvironmentCredential(**self.credential_kwargs)

    @staticmethod
    def get_managed_identity_credential(client_id=None):
        return ManagedIdentityCredential(client_id=client_id)

    @staticmethod
    def _decode_managed_identity_token(token):
        # As Managed Identity doesn't have ID token, we need to get an initial access token and extract info from it
        # The resource is only used for acquiring the initial access token
        from msal.oauth2cli.oidc import decode_part
        access_token = token.token

        # Access token consists of headers.claims.signature. Decode the claim part
        decoded_str = decode_part(access_token.split('.')[1])
        logger.debug('MSI token retrieved: %s', decoded_str)
        decoded = json.loads(decoded_str)
        return decoded

    def migrate_adal_to_msal(self):
        """Migrate ADAL token cache to MSAL."""
        logger.warning("Migrating token cache from ADAL to MSAL.")

        entries = AdalCredentialCache()._load_tokens_from_file()
        if not entries:
            logger.debug("No ADAL token cache found.")
            return

        for entry in entries:
            try:
                # TODO: refine the filter logic
                if 'userId' in entry:
                    # User account
                    username = entry['userId']
                    authority = entry['_authority']
                    scopes = adal_resource_to_msal_scopes(entry['resource'])
                    refresh_token = entry['refreshToken']

                    msal_app = self._build_persistent_msal_app(authority)
                    # TODO: Not work in ADFS:
                    # {'error': 'invalid_grant', 'error_description': "MSIS9614: The refresh token received in 'refresh_token' parameter is invalid."}
                    logger.warning("Migrating refresh token: username: %s, authority: %s, scopes: %s",
                                   username, authority, scopes)
                    token_dict = msal_app.acquire_token_by_refresh_token(refresh_token, scopes)
                    if 'error' in token_dict:
                        raise CLIError("Failed to migrate token from ADAL cache to MSAL cache. {}".format(token_dict))
                else:
                    # Service principal account
                    logger.warning("Migrating service principal secret: servicePrincipalId: %s, "
                                   "servicePrincipalTenant: %s",
                                   entry['servicePrincipalId'], entry['servicePrincipalTenant'])
                    self._msal_secret_store.save_service_principal_cred(entry)
            except CLIError:
                # Ignore failed tokens
                continue

        # TODO: Delete accessToken.json after migration (accessToken.json deprecation)

    def _serialize_token_cache(self):
        # ONLY FOR DEBUGGING PURPOSE. DO NOT USE IN PRODUCTION CODE.
        logger.warning("Token cache is serialized as plain text and saved to `msal.cache.json`.")
        with open(os.path.join(get_config_dir(), "msal.cache.json"), "w") as fd:
            fd.write(self._msal_app.token_cache.serialize())


TOKEN_FIELDS_EXCLUDED_FROM_PERSISTENCE = ['familyName',
                                          'givenName',
                                          'isUserIdDisplayable',
                                          'tenantId']
_TOKEN_ENTRY_USER_ID = 'userId'


class AdalCredentialCache:
    """Caches secrets in ADAL format, will be deprecated
    """

    # TODO: Persist SP to encrypted cache
    def __init__(self, async_persist=True, cli_ctx=None):

        # AZURE_ACCESS_TOKEN_FILE is used by Cloud Console and not meant to be user configured
        self._token_file = (os.environ.get('AZURE_ACCESS_TOKEN_FILE', None) or
                            os.path.join(get_config_dir(), 'accessTokens.json'))
        self._service_principal_creds = []
        self._adal_token_cache_attr = None
        self._should_flush_to_disk = False
        self._cli_ctx = cli_ctx
        self._async_persist = async_persist
        if async_persist:
            import atexit
            atexit.register(self.flush_to_disk)

    def _load_tokens_from_file(self):
        if os.path.isfile(self._token_file):
            try:
                return get_file_json(self._token_file, throw_on_empty=False) or []
            except (CLIError, ValueError) as ex:
                raise CLIError("Failed to load token files. If you have a repro, please log an issue at "
                               "https://github.com/Azure/azure-cli/issues. At the same time, you can clean "
                               "up by running 'az account clear' and then 'az login'. (Inner Error: {})".format(ex))
        return []

    def _delete_token_file(self):
        try:
            os.remove(self._token_file)
        except FileNotFoundError:
            pass

    def persist_cached_creds(self):
        self._should_flush_to_disk = True
        if not self._async_persist:
            self.flush_to_disk()

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

    def retrieve_secret_of_service_principal(self, sp_id, tenant):
        self.load_service_principal_creds()
        matched = [x for x in self._service_principal_creds if sp_id == x[_SERVICE_PRINCIPAL_ID]]
        if not matched:
            raise CLIError("Could not retrieve credential from local cache for service principal {}. "
                           "Please run 'az login' for this service principal."
                           .format(sp_id))
        matched_with_tenant = [x for x in matched if tenant == x[_SERVICE_PRINCIPAL_TENANT]]
        if matched_with_tenant:
            cred = matched_with_tenant[0]
        else:
            logger.warning("Could not retrieve credential from local cache for service principal %s under tenant %s. "
                           "Trying credential under tenant %s, assuming that is an app credential.",
                           sp_id, tenant, matched[0][_SERVICE_PRINCIPAL_TENANT])
            cred = matched[0]
        return cred.get(_ACCESS_TOKEN, None), cred.get(_SERVICE_PRINCIPAL_CERT_FILE, None)

    def save_service_principal_cred(self, sp_entry):
        self.load_adal_token_cache()
        matched = [x for x in self._service_principal_creds
                   if sp_entry[_SERVICE_PRINCIPAL_ID] == x[_SERVICE_PRINCIPAL_ID] and
                   sp_entry[_SERVICE_PRINCIPAL_TENANT] == x[_SERVICE_PRINCIPAL_TENANT]]
        state_changed = False
        if matched:
            # pylint: disable=line-too-long
            if (sp_entry.get(_ACCESS_TOKEN, None) != matched[0].get(_ACCESS_TOKEN, None) or
                    sp_entry.get(_SERVICE_PRINCIPAL_CERT_FILE, None) != matched[0].get(_SERVICE_PRINCIPAL_CERT_FILE,
                                                                                       None)):
                self._service_principal_creds.remove(matched[0])
                self._service_principal_creds.append(sp_entry)
                state_changed = True
        else:
            self._service_principal_creds.append(sp_entry)
            state_changed = True

        if state_changed:
            self.persist_cached_creds()

    # noinspection PyBroadException
    # pylint: disable=protected-access
    def add_credential(self, credential):
        try:
            query = {
                "client_id": AZURE_CLI_CLIENT_ID,
                "environment": credential._auth_record.authority,
                "home_account_id": credential._auth_record.home_account_id
            }
            refresh_token = credential._cache.find(
                credential._cache.CredentialType.REFRESH_TOKEN,
                # target=scopes,  # AAD RTs are scope-independent
                query=query)
            access_token = credential.get_token(self._cli_ctx.cloud.endpoints.active_directory_resource_id.rstrip('/') +
                                                '/.default')
            import datetime
            entry = {
                "tokenType": "Bearer",
                "expiresOn": datetime.datetime.fromtimestamp(access_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "resource": self._cli_ctx.cloud.endpoints.active_directory_resource_id,
                "userId": credential._auth_record.username,
                "accessToken": access_token.token,
                "refreshToken": refresh_token[0]['secret'],
                "_clientId": AZURE_CLI_CLIENT_ID,
                "_authority": self._cli_ctx.cloud.endpoints.active_directory.rstrip('/') +
                "/" + credential._auth_record.tenant_id,  # pylint: disable=bad-continuation
                "isMRRT": True
            }
            self.adal_token_cache.add([entry])
        except Exception as e:    # pylint: disable=broad-except
            logger.debug("Failed to store ADAL token: %s", e)
            # swallow all errors since it does not impact az

    @property
    def adal_token_cache(self):
        return self.load_adal_token_cache()

    def load_adal_token_cache(self):
        if self._adal_token_cache_attr is None:
            import adal
            all_entries = self._load_tokens_from_file()
            self.load_service_principal_creds(all_entries=all_entries)
            real_token = [x for x in all_entries if x not in self._service_principal_creds]
            self._adal_token_cache_attr = adal.TokenCache(json.dumps(real_token))
        return self._adal_token_cache_attr

    def load_service_principal_creds(self, **kwargs):
        creds = kwargs.pop("all_entries", None)
        if not creds:
            creds = self._load_tokens_from_file()
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
        self._delete_token_file()


class ServicePrincipalAuth(object):   # pylint: disable=too-few-public-methods

    def __init__(self, client_id, tenant_id, secret=None, certificate_file=None, use_cert_sn_issuer=None):
        if not (secret or certificate_file):
            raise CLIError('Missing secret or certificate in order to '
                           'authnenticate through a service principal')
        self.client_id = client_id
        self.tenant_id = tenant_id
        if certificate_file:
            from OpenSSL.crypto import load_certificate, FILETYPE_PEM
            self.certificate_file = certificate_file
            self.public_certificate = None
            with open(certificate_file, 'r') as file_reader:
                self.cert_file_string = file_reader.read()
                cert = load_certificate(FILETYPE_PEM, self.cert_file_string)
                self.thumbprint = cert.digest("sha1").decode()
                if use_cert_sn_issuer:
                    import re
                    # low-tech but safe parsing based on
                    # https://github.com/libressl-portable/openbsd/blob/master/src/lib/libcrypto/pem/pem.h
                    match = re.search(r'\-+BEGIN CERTIFICATE.+\-+(?P<public>[^-]+)\-+END CERTIFICATE.+\-+',
                                      self.cert_file_string, re.I)
                    self.public_certificate = match.group('public').strip()
        else:
            self.secret = secret

    def get_entry_to_persist(self):
        entry = {
            _SERVICE_PRINCIPAL_ID: self.client_id,
            _SERVICE_PRINCIPAL_TENANT: self.tenant_id,
        }
        if hasattr(self, 'secret'):
            entry[_ACCESS_TOKEN] = self.secret
        else:
            entry[_SERVICE_PRINCIPAL_CERT_FILE] = self.certificate_file
            entry[_SERVICE_PRINCIPAL_CERT_THUMBPRINT] = self.thumbprint

        return entry


class MsalSecretStore:
    """Caches secrets in MSAL custom secret store
    """

    def __init__(self, fallback_to_plaintext=True):
        self._token_file = os.path.join(get_config_dir(), 'msalSecrets.cache')
        self._lock_file = self._token_file + '.lock'
        self._service_principal_creds = []
        self._fallback_to_plaintext = fallback_to_plaintext

    def retrieve_secret_of_service_principal(self, sp_id, tenant):
        self._load_cached_creds()
        matched = [x for x in self._service_principal_creds if sp_id == x[_SERVICE_PRINCIPAL_ID]]
        if not matched:
            raise CLIError("Could not retrieve credential from local cache for service principal {}. "
                           "Please run 'az login' for this service principal."
                           .format(sp_id))
        matched_with_tenant = [x for x in matched if tenant == x[_SERVICE_PRINCIPAL_TENANT]]
        if matched_with_tenant:
            cred = matched_with_tenant[0]
        else:
            logger.warning("Could not retrieve credential from local cache for service principal %s under tenant %s. "
                           "Trying credential under tenant %s, assuming that is an app credential.",
                           sp_id, tenant, matched[0][_SERVICE_PRINCIPAL_TENANT])
            cred = matched[0]
        return cred.get(_ACCESS_TOKEN, None), cred.get(_SERVICE_PRINCIPAL_CERT_FILE, None)

    def save_service_principal_cred(self, sp_entry):
        self._load_cached_creds()
        matched = [x for x in self._service_principal_creds
                   if sp_entry[_SERVICE_PRINCIPAL_ID] == x[_SERVICE_PRINCIPAL_ID] and
                   sp_entry[_SERVICE_PRINCIPAL_TENANT] == x[_SERVICE_PRINCIPAL_TENANT]]
        state_changed = False
        if matched:
            # pylint: disable=line-too-long
            if (sp_entry.get(_ACCESS_TOKEN, None) != matched[0].get(_ACCESS_TOKEN, None) or
                    sp_entry.get(_SERVICE_PRINCIPAL_CERT_FILE, None) != matched[0].get(_SERVICE_PRINCIPAL_CERT_FILE,
                                                                                       None)):
                self._service_principal_creds.remove(matched[0])
                self._service_principal_creds.append(sp_entry)
                state_changed = True
        else:
            self._service_principal_creds.append(sp_entry)
            state_changed = True

        if state_changed:
            self._persist_cached_creds()

    def remove_cached_creds(self, user_or_sp):
        self._load_cached_creds()
        state_changed = False

        # clear service principal creds
        matched = [x for x in self._service_principal_creds
                   if x[_SERVICE_PRINCIPAL_ID] == user_or_sp]
        if matched:
            state_changed = True
            self._service_principal_creds = [x for x in self._service_principal_creds
                                             if x not in matched]

        if state_changed:
            self._persist_cached_creds()

    def remove_all_cached_creds(self):
        try:
            os.remove(self._token_file)
        except FileNotFoundError:
            pass

    def _persist_cached_creds(self):
        persistence = self._build_persistence()
        from msal_extensions import CrossPlatLock
        with CrossPlatLock(self._lock_file):
            persistence.save(json.dumps(self._service_principal_creds))

    def _load_cached_creds(self):
        persistence = self._build_persistence()
        from msal_extensions import CrossPlatLock
        with CrossPlatLock(self._lock_file):
            try:
                self._service_principal_creds = json.loads(persistence.load())
            except FileNotFoundError:
                pass
            except Exception as ex:
                raise CLIError("Failed to load token files. If you have a repro, please log an issue at "
                               "https://github.com/Azure/azure-cli/issues. At the same time, you can clean "
                               "up by running 'az account clear' and then 'az login'. (Inner Error: {})".format(ex))

    def _build_persistence(self):
        # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/0.2.2/sample/persistence_sample.py
        from msal_extensions import FilePersistenceWithDataProtection, \
            KeychainPersistence, \
            LibsecretPersistence, \
            FilePersistence

        import sys
        if sys.platform.startswith('win'):
            return FilePersistenceWithDataProtection(self._token_file)
        if sys.platform.startswith('darwin'):
            # todo: support darwin
            return KeychainPersistence(self._token_file, "Microsoft.Developer.IdentityService", "MSALCustomCache")
        if sys.platform.startswith('linux'):
            try:
                return LibsecretPersistence(
                    self._token_file,
                    schema_name="MSALCustomToken",
                    attributes={"MsalClientID": "Microsoft.Developer.IdentityService"}
                )
            except:  # pylint: disable=bare-except
                if not self._fallback_to_plaintext:
                    raise
                # todo: add missing lib in message
                logger.warning("Encryption unavailable. Opting in to plain text.")
        return FilePersistence(self._token_file)

    def _serialize_secrets(self):
        # ONLY FOR DEBUGGING PURPOSE. DO NOT USE IN PRODUCTION CODE.
        logger.warning("Secrets are serialized as plain text and saved to `msalSecrets.cache.json`.")
        with open(self._token_file + ".json", "w") as fd:
            fd.write(json.dumps(self._service_principal_creds))


def adal_resource_to_msal_scopes(resource):
    """Convert the ADAL resource ID to MSAL scopes by appending the /.default suffix and return a list.
    For example: 'https://management.core.windows.net/' -> ['https://management.core.windows.net/.default']
    :param resource: The ADAL resource ID
    :return: A list of scopes
    """
    if 'datalake' in resource or 'batch' in resource or 'database' in resource:
        scope = resource + '/.default'
    else:
        scope = resource.rstrip('/') + '/.default'
    return [scope]

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
    AuthProfile,
    InteractiveBrowserCredential,
    DeviceCodeCredential,
    UsernamePasswordCredential,
    ClientSecretCredential,
    CertificateCredential,
    ManagedIdentityCredential
)

_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'
logger = get_logger(__name__)

_SERVICE_PRINCIPAL_ID = 'servicePrincipalId'
_SERVICE_PRINCIPAL_TENANT = 'servicePrincipalTenant'
_ACCESS_TOKEN = 'accessToken'
_SERVICE_PRINCIPAL_CERT_FILE = 'certificateFile'
_SERVICE_PRINCIPAL_CERT_THUMBPRINT = 'thumbprint'


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
    except FileNotFoundError:
        pass


class Identity:
    """Class to interact with Azure Identity.
    """
    def __init__(self, authority, tenant_id):
        if not authority:
            raise ValueError("Unexpected CLI error: authority cannot be none.")
        self.authority = authority
        self.tenant_id = tenant_id

        # TODO: Allow disabling SSL verification
        # The underlying requests lib of MSAL has been patched with Azure Core by MsalTransportAdapter
        # connection_verify will be received by azure.core.configuration.ConnectionConfiguration
        # However, MSAL defaults verify to True, thus overriding ConnectionConfiguration
        # Still not work yet
        from azure.cli.core._debug import change_ssl_cert_verification_track2
        self.ssl_kwargs = change_ssl_cert_verification_track2()

    def login_with_interactive_browser(self):
        # Use InteractiveBrowserCredential
        if self.tenant_id:
            credential, auth_profile = InteractiveBrowserCredential.authenticate(
                client_id=_CLIENT_ID,
                authority=self.authority,
                tenant_id=self.tenant_id
            )
        else:
            credential, auth_profile = InteractiveBrowserCredential.authenticate(
                authority=self.authority,
                client_id=_CLIENT_ID
            )
        return credential, auth_profile

    def login_with_device_code(self):
        # Use DeviceCodeCredential
        message = 'To sign in, use a web browser to open the page {} and enter the code {} to authenticate.'
        prompt_callback = lambda verification_uri, user_code, expires_on: \
            logger.warning(message.format(verification_uri, user_code))
        if self.tenant_id:
            cred, auth_profile = DeviceCodeCredential.authenticate(client_id=_CLIENT_ID,
                                                                   authority=self.authority,
                                                                   tenant_id=self.tenant_id,
                                                                   prompt_callback=prompt_callback)
        else:
            cred, auth_profile = DeviceCodeCredential.authenticate(client_id=_CLIENT_ID,
                                                                   authority=self.authority,
                                                                   prompt_callback=prompt_callback)
        return cred, auth_profile

    def login_with_username_password(self, username, password):
        # Use UsernamePasswordCredential
        if self.tenant_id:
            credential, auth_profile = UsernamePasswordCredential.authenticate(
                _CLIENT_ID, username, password, authority=self.authority, tenant_id=self.tenant_id,
                **self.ssl_kwargs)
        else:
            credential, auth_profile = UsernamePasswordCredential.authenticate(
                _CLIENT_ID, username, password, authority=self.authority, **self.ssl_kwargs)
        return credential, auth_profile

    def login_with_service_principal_secret(self, client_id, client_secret):
        # Use ClientSecretCredential
        # TODO: Persist to encrypted cache
        # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/pull/44
        sp_auth = ServicePrincipalAuth(client_id, self.tenant_id, secret=client_secret)
        entry = sp_auth.get_entry_to_persist()
        cred_cache = ADALCredentialCache()
        cred_cache.save_service_principal_cred(entry)

        credential = ClientSecretCredential(self.tenant_id, client_id, client_secret, authority=self.authority)
        return credential

    def login_with_service_principal_certificate(self, client_id, certificate_path):
        # Use CertificateCredential
        # TODO: Persist to encrypted cache
        # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/pull/44
        sp_auth = ServicePrincipalAuth(client_id, self.tenant_id, certificate_file=certificate_path)
        entry = sp_auth.get_entry_to_persist()
        cred_cache = ADALCredentialCache()
        cred_cache.save_service_principal_cred(entry)

        # TODO: support use_cert_sn_issuer in CertificateCredential
        credential = CertificateCredential(self.tenant_id, client_id, certificate_path, authority=self.authority)
        return credential

    def login_with_msi(self):
        # Use ManagedIdentityCredential
        pass

    def get_user_credential(self, home_account_id, username):
        auth_profile = AuthProfile(self.authority, home_account_id, self.tenant_id, username)
        return InteractiveBrowserCredential(profile=auth_profile, silent_auth_only=True)

    def get_service_principal_credential(self, client_id, use_cert_sn_issuer):
        cred_cache = ADALCredentialCache()
        client_secret, certificate_path = cred_cache.retrieve_secret_of_service_principal(client_id, self.tenant_id)
        # TODO: support use_cert_sn_issuer in CertificateCredential
        if client_secret:
            return ClientSecretCredential(self.tenant_id, client_id, client_secret)
        if certificate_path:
            return CertificateCredential(self.tenant_id, client_id, certificate_path)
        raise CLIError("Secret of service principle {} not found. Please run 'az login'".format(client_id))

    @staticmethod
    def get_msi_credential(client_id=None):
        # TODO: support object_id and msi_res_id
        return ManagedIdentityCredential(client_id=client_id)


TOKEN_FIELDS_EXCLUDED_FROM_PERSISTENCE = ['familyName',
                                          'givenName',
                                          'isUserIdDisplayable',
                                          'tenantId']
_TOKEN_ENTRY_USER_ID = 'userId'


class ADALCredentialCache:
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
        self.load_service_principal_creds()
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
    def add_credential(self, credential):
        try:
            query = {
                "client_id": _CLIENT_ID,
                "environment": credential._profile.environment,
                "home_account_id": credential._profile.home_account_id
            }
            refresh_token = credential._cache.find(
                credential._cache.CredentialType.REFRESH_TOKEN,
                # target=scopes,  # AAD RTs are scope-independent
                query=query)
            access_token = credential.get_token(self._cli_ctx.cloud.endpoints.active_directory_resource_id.rstrip('/')
                                                + '/.default')
            import datetime
            entry = {
                "tokenType": "Bearer",
                "expiresOn": datetime.datetime.fromtimestamp(access_token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f"),
                "resource": self._cli_ctx.cloud.endpoints.active_directory_resource_id,
                "userId": credential._profile.username,
                "accessToken": access_token.token,
                "refreshToken": refresh_token[0]['secret'],
                "_clientId": _CLIENT_ID,
                "_authority": self._cli_ctx.cloud.endpoints.active_directory.rstrip('/')
                              + "/" + credential._profile.tenant_id
            }
            self.adal_token_cache.add([entry])
        except Exception as e:
            logger.debug("Failed to store ADAL token: {}".format(e))
            # swallow all errors since it does not impact az

    @property
    def adal_token_cache(self):
        return self.load_adal_token_cache()

    def load_adal_token_cache(self):
        if self._adal_token_cache_attr is None:
            import adal
            all_entries = _load_tokens_from_file(self._token_file)
            self.load_service_principal_creds(all_entries=all_entries)
            real_token = [x for x in all_entries if x not in self._service_principal_creds]
            self._adal_token_cache_attr = adal.TokenCache(json.dumps(real_token))
        return self._adal_token_cache_attr

    def load_service_principal_creds(self, **kwargs):
        creds = kwargs.pop("all_entries", None)
        if not creds:
            creds = _load_tokens_from_file(self._token_file)
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

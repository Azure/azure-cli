# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re

from azure.cli.core._environment import get_config_dir
from knack.log import get_logger
from knack.util import CLIError

from .msal_authentication import UserCredential, ServicePrincipalCredential
from .util import aad_error_handler, check_result

AZURE_CLI_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

# Service principal entry properties
_CLIENT_ID = 'client_id'
_TENANT_ID = 'tenant_id'
_SECRET = 'secret'
_CERTIFICATE = 'certificate'
_FEDERATED_TOKEN = 'federated_token'
_USE_CERT_SN_ISSUER = 'use_cert_sn_issuer'

logger = get_logger(__name__)


class Identity:  # pylint: disable=too-many-instance-attributes
    """Class to manage identities:
        - user
        - service principal
        TODO: - managed identity
    """
    # Whether token and secrets should be encrypted. Change its value to turn on/off token encryption.
    token_encryption = False

    # HTTP cache for MSAL's tenant discovery, retry-after error cache, etc.
    # It must follow singleton pattern. Otherwise, a new dbm.dumb http_cache can read out-of-sync dat and dir.
    # https://github.com/AzureAD/microsoft-authentication-library-for-python/pull/407
    http_cache = None

    def __init__(self, authority=None, tenant_id=None, client_id=None):
        """

        :param authority: AAD endpoint, like https://login.microsoftonline.com/
        :param tenant_id: Tenant GUID, like 00000000-0000-0000-0000-000000000000
        :param client_id: Client ID of the CLI application.
        """
        self.authority = authority
        self.tenant_id = tenant_id or "organizations"
        # Build the authority in MSAL style, like https://login.microsoftonline.com/your_tenant
        self.msal_authority = "{}/{}".format(self.authority, self.tenant_id)
        self.client_id = client_id or AZURE_CLI_CLIENT_ID

        config_dir = get_config_dir()
        self._token_cache_file = os.path.join(config_dir, "tokenCache")
        self._secret_file = os.path.join(config_dir, "secrets")
        self._http_cache_file = os.path.join(config_dir, "httpCache")

        # Prepare HTTP cache.
        # if not Identity.http_cache:
        #     Identity.http_cache = self._load_http_cache()

        self._msal_app_instance = None
        # Store for Service principal credential persistence
        self._msal_secret_store = ServicePrincipalStore(self._secret_file, self.token_encryption)
        self._msal_app_kwargs = {
            "authority": self.msal_authority,
            "token_cache": self._load_msal_cache()
        }

    def _load_msal_cache(self):
        from .persistence import load_persisted_token_cache
        # Store for user token persistence
        cache = load_persisted_token_cache(self._token_cache_file, self.token_encryption)
        cache._reload_if_necessary()  # pylint: disable=protected-access
        return cache

    def _load_http_cache(self):
        import atexit
        import shelve
        http_cache = persisted_http_cache = shelve.open(self._http_cache_file)
        atexit.register(persisted_http_cache.close)
        return http_cache

    def _build_persistent_msal_app(self):
        # Initialize _msal_app for logout, token migration which Azure Identity doesn't support
        from msal import PublicClientApplication
        msal_app = PublicClientApplication(self.client_id, **self._msal_app_kwargs)
        return msal_app

    @property
    def msal_app(self):
        if not self._msal_app_instance:
            self._msal_app_instance = self._build_persistent_msal_app()
        return self._msal_app_instance

    def login_with_auth_code(self, scopes=None, **kwargs):
        # Emit a warning to inform that a browser is opened.
        # Only show the path part of the URL and hide the query string.
        logger.warning("The default web browser has been opened at %s/oauth2/v2.0/authorize. "
                       "Please continue the login in the web browser. "
                       "If no web browser is available or if the web browser fails to open, use device code flow "
                       "with `az login --use-device-code`.", self.msal_authority)

        success_template, error_template = _read_response_templates()

        result = self.msal_app.acquire_token_interactive(
            scopes, prompt='select_account', success_template=success_template, error_template=error_template, **kwargs)

        if not result or 'error' in result:
            aad_error_handler(result)
        return check_result(result)

    def login_with_device_code(self, scopes=None, **kwargs):
        flow = self.msal_app.initiate_device_flow(scopes, **kwargs)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))
        logger.warning(flow["message"])
        result = self.msal_app.acquire_token_by_device_flow(flow, **kwargs)  # By default it will block
        return check_result(result)

    def login_with_username_password(self, username, password, scopes=None, **kwargs):
        result = self.msal_app.acquire_token_by_username_password(username, password, scopes, **kwargs)
        return check_result(result)

    def login_with_service_principal(self, client_id, credential, scopes=None):
        sp_auth = ServicePrincipalAuth.build_from_credential(self.tenant_id, client_id, credential)
        cred = ServicePrincipalCredential(sp_auth, **self._msal_app_kwargs)
        result = cred.acquire_token_for_client(scopes)
        check_result(result)
        entry = sp_auth.get_entry_to_persist()
        self._msal_secret_store.save_credential(entry)

    def login_with_managed_identity(self, scopes, identity_id=None):  # pylint: disable=too-many-statements
        raise NotImplementedError

    def login_in_cloud_shell(self, scopes):
        raise NotImplementedError

    def logout_user(self, user):
        accounts = self.msal_app.get_accounts(user)
        for account in accounts:
            self.msal_app.remove_account(account)

    def logout_all_users(self):
        try:
            os.remove(self._token_cache_file)
        except FileNotFoundError:
            pass

    def logout_service_principal(self, sp):
        # remove service principal secrets
        self._msal_secret_store.remove_credential(sp)

    def logout_all_service_principal(self):
        # remove service principal secrets
        self._msal_secret_store.remove_all_credentials()

    def get_user(self, user=None):
        accounts = self.msal_app.get_accounts(user) if user else self.msal_app.get_accounts()
        return accounts

    def get_user_credential(self, username):
        return UserCredential(self.client_id, username, **self._msal_app_kwargs)

    def get_service_principal_credential(self, client_id):
        entry = self._msal_secret_store.load_credential(client_id, self.tenant_id)
        sp_auth = ServicePrincipalAuth(entry)
        return ServicePrincipalCredential(sp_auth, **self._msal_app_kwargs)

    def get_managed_identity_credential(self, client_id=None):
        raise NotImplementedError

    def serialize_token_cache(self, path=None):
        path = path or os.path.join(get_config_dir(), "msal.cache.snapshot.json")
        path = os.path.expanduser(path)
        logger.warning("Token cache is exported to '%s'. The exported cache is unencrypted. "
                       "It contains login information of all logged-in users. Make sure you protect it safely.", path)

        cache = self._load_msal_cache()
        with open(path, "w") as fd:
            fd.write(cache.serialize())


class ServicePrincipalAuth:

    def __init__(self, entry):
        self.__dict__.update(entry)

        if _CERTIFICATE in entry:
            from OpenSSL.crypto import load_certificate, FILETYPE_PEM, Error
            self.public_certificate = None
            try:
                with open(self.certificate, 'r') as file_reader:
                    self.certificate_string = file_reader.read()
                    cert = load_certificate(FILETYPE_PEM, self.certificate_string)
                    self.thumbprint = cert.digest("sha1").decode().replace(':', '')
                    if entry.get(_USE_CERT_SN_ISSUER):
                        # low-tech but safe parsing based on
                        # https://github.com/libressl-portable/openbsd/blob/master/src/lib/libcrypto/pem/pem.h
                        match = re.search(r'-----BEGIN CERTIFICATE-----(?P<cert_value>[^-]+)-----END CERTIFICATE-----',
                                          self.certificate_string, re.I)
                        self.public_certificate = match.group()
            except (UnicodeDecodeError, Error) as ex:
                raise CLIError('Invalid certificate, please use a valid PEM file. Error detail: {}'.format(ex))

    @classmethod
    def build_from_credential(cls, tenant_id, client_id, credential):
        entry = {
            _CLIENT_ID: client_id,
            _TENANT_ID: tenant_id
        }
        entry.update(credential)
        return ServicePrincipalAuth(entry)

    @classmethod
    def build_credential(cls, secret_or_certificate=None, federated_token=None, use_cert_sn_issuer=None):
        """Build credential from user input. The credential looks like below, but only one key can exist.
        {
            "secret": "xxx",
            "certificate": "/path/to/cert.pem",
            "federated_token": "xxx"
        }
        """
        entry = {}
        if secret_or_certificate:
            if os.path.isfile(secret_or_certificate):
                entry[_CERTIFICATE] = secret_or_certificate
                if use_cert_sn_issuer:
                    entry[_USE_CERT_SN_ISSUER] = use_cert_sn_issuer
            else:
                entry[_SECRET] = secret_or_certificate
        elif federated_token:
            entry[_FEDERATED_TOKEN] = federated_token
        return entry

    def get_entry_to_persist(self):
        persisted_keys = [_CLIENT_ID, _TENANT_ID, _SECRET, _CERTIFICATE, _USE_CERT_SN_ISSUER, _FEDERATED_TOKEN]
        return {k: v for k, v in self.__dict__.items() if k in persisted_keys}


class ServicePrincipalStore:
    """Caches secrets in MSAL custom secret store for Service Principal authentication.
    """

    def __init__(self, secret_file, encrypt):
        from .persistence import load_secret_store
        self._secret_store = load_secret_store(secret_file, encrypt)
        self._secret_file = secret_file
        self._entries = []

    def load_credential(self, sp_id, tenant):
        self._load_persistence()
        matched = [x for x in self._entries if sp_id == x[_CLIENT_ID]]
        if not matched:
            raise CLIError("Could not retrieve credential from local cache for service principal {}. "
                           "Please run `az login` for this service principal."
                           .format(sp_id))
        matched_with_tenant = [x for x in matched if tenant == x[_TENANT_ID]]
        if matched_with_tenant:
            cred = matched_with_tenant[0]
        else:
            logger.warning("Could not retrieve credential from local cache for service principal %s under tenant %s. "
                           "Trying credential under tenant %s, assuming that is an app credential.",
                           sp_id, tenant, matched[0][_TENANT_ID])
            cred = matched[0]

        return cred

    def save_credential(self, sp_entry):
        self._load_persistence()

        self._entries = [
            x for x in self._entries
            if not (sp_entry[_CLIENT_ID] == x[_CLIENT_ID] and
                    sp_entry[_TENANT_ID] == x[_TENANT_ID])]

        self._entries.append(sp_entry)
        self._save_persistence()

    def remove_credential(self, sp_id):
        self._load_persistence()
        state_changed = False

        # clear service principal creds
        matched = [x for x in self._entries
                   if x[_CLIENT_ID] == sp_id]
        if matched:
            state_changed = True
            self._entries = [x for x in self._entries
                             if x not in matched]

        if state_changed:
            self._save_persistence()

    def remove_all_credentials(self):
        try:
            os.remove(self._secret_file)
        except FileNotFoundError:
            pass

    def _save_persistence(self):
        self._secret_store.save(self._entries)

    def _load_persistence(self):
        self._entries = self._secret_store.load()

    def _serialize_secrets(self):
        # ONLY FOR DEBUGGING PURPOSE. DO NOT USE IN PRODUCTION CODE.
        logger.warning("Secrets are serialized as plain text and saved to `msalSecrets.cache.json`.")
        with open(self._secret_file + ".json", "w") as fd:
            fd.write(json.dumps(self._entries, indent=4))


def _read_response_templates():
    """Read from success.html and error.html to strings and pass them to MSAL. """
    success_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'landing_pages', 'success.html')
    with open(success_file) as f:
        success_template = f.read()

    error_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'landing_pages', 'error.html')
    with open(error_file) as f:
        error_template = f.read()

    return success_template, error_template

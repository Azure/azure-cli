# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re

from azure.cli.core._environment import get_config_dir
from msal import PublicClientApplication

from knack.log import get_logger
from knack.util import CLIError
# Service principal entry properties
from .msal_authentication import _CLIENT_ID, _TENANT, _CLIENT_SECRET, _CERTIFICATE, _CLIENT_ASSERTION, \
    _USE_CERT_SN_ISSUER
from .msal_authentication import UserCredential, ServicePrincipalCredential
from .persistence import load_persisted_token_cache, file_extensions
from .util import check_result

AZURE_CLI_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'


logger = get_logger(__name__)


class Identity:  # pylint: disable=too-many-instance-attributes
    """Class to manage identities:
        - user
        - service principal
        - TODO: managed identity
    """
    # HTTP cache for MSAL's tenant discovery, retry-after error cache, etc.
    # It must follow singleton pattern. Otherwise, a new dbm.dumb http_cache can read out-of-sync dat and dir.
    # https://github.com/AzureAD/microsoft-authentication-library-for-python/pull/407
    http_cache = None

    def __init__(self, authority, tenant_id=None, client_id=None, encrypt=False):
        """
        :param authority: Authentication authority endpoint. For example,
            - AAD: https://login.microsoftonline.com
            - ADFS: https://adfs.redmond.azurestack.corp.microsoft.com/adfs
        :param tenant_id: Tenant GUID, like 00000000-0000-0000-0000-000000000000. If unspecified, default to
            'organizations'.
        :param client_id: Client ID of the CLI application.
        :param encrypt:  Whether to encrypt token cache and service principal entries.
        """
        self.authority = authority
        self.tenant_id = tenant_id
        self.client_id = client_id or AZURE_CLI_CLIENT_ID
        self.encrypt = encrypt

        # Build the authority in MSAL style
        self._msal_authority, self._is_adfs = _get_authority_url(authority, tenant_id)

        config_dir = get_config_dir()
        self._token_cache_file = os.path.join(config_dir, "msal_token_cache")
        self._secret_file = os.path.join(config_dir, "service_principal_entries")
        self._http_cache_file = os.path.join(config_dir, "msal_http_cache")

        # Prepare HTTP cache.
        # https://github.com/AzureAD/microsoft-authentication-library-for-python/pull/407
        # if not Identity.http_cache:
        #     Identity.http_cache = self._load_http_cache()

        self._msal_app_instance = None
        # Store for Service principal credential persistence
        self._msal_secret_store = ServicePrincipalStore(self._secret_file, self.encrypt)
        self._msal_app_kwargs = {
            "authority": self._msal_authority,
            "token_cache": self._load_msal_cache()
            # "http_cache": Identity.http_cache
        }

    def _load_msal_cache(self):
        # Store for user token persistence
        cache = load_persisted_token_cache(self._token_cache_file, self.encrypt)
        return cache

    def _load_http_cache(self):
        import atexit
        import pickle

        try:
            with open(self._http_cache_file, 'rb') as f:
                persisted_http_cache = pickle.load(f)  # Take a snapshot
        except:  # pylint: disable=bare-except
            persisted_http_cache = {}  # Ignore a non-exist or corrupted http_cache
        atexit.register(lambda: pickle.dump(
            # When exit, flush it back to the file.
            # If 2 processes write at the same time, the cache will be corrupted,
            # but that is fine. Subsequent runs would reach eventual consistency.
            persisted_http_cache, open(self._http_cache_file, 'wb')))

        return persisted_http_cache

    def _build_persistent_msal_app(self):
        # Initialize _msal_app for login and logout
        msal_app = PublicClientApplication(self.client_id, **self._msal_app_kwargs)
        return msal_app

    @property
    def msal_app(self):
        if not self._msal_app_instance:
            self._msal_app_instance = self._build_persistent_msal_app()
        return self._msal_app_instance

    def login_with_auth_code(self, scopes, **kwargs):
        # Emit a warning to inform that a browser is opened.
        # Only show the path part of the URL and hide the query string.
        logger.warning("The default web browser has been opened at %s. Please continue the login in the web browser. "
                       "If no web browser is available or if the web browser fails to open, use device code flow "
                       "with `az login --use-device-code`.", self.msal_app.authority.authorization_endpoint)

        from .util import read_response_templates
        success_template, error_template = read_response_templates()

        # For AAD, use port 0 to let the system choose arbitrary unused ephemeral port to avoid port collision
        # on port 8400 from the old design. However, ADFS only allows port 8400.
        result = self.msal_app.acquire_token_interactive(
            scopes, prompt='select_account', port=8400 if self._is_adfs else None,
            success_template=success_template, error_template=error_template, **kwargs)
        return check_result(result)

    def login_with_device_code(self, scopes, **kwargs):
        flow = self.msal_app.initiate_device_flow(scopes, **kwargs)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))
        logger.warning(flow["message"])
        result = self.msal_app.acquire_token_by_device_flow(flow, **kwargs)  # By default it will block
        return check_result(result)

    def login_with_username_password(self, username, password, scopes, **kwargs):
        result = self.msal_app.acquire_token_by_username_password(username, password, scopes, **kwargs)
        return check_result(result)

    def login_with_service_principal(self, client_id, credential, scopes):
        """
        `credential` is a dict returned by ServicePrincipalAuth.build_credential
        """
        sp_auth = ServicePrincipalAuth.build_from_credential(self.tenant_id, client_id, credential)

        # This cred means SDK credential object
        cred = ServicePrincipalCredential(sp_auth, **self._msal_app_kwargs)
        result = cred.acquire_token_for_client(scopes)
        check_result(result)

        # Only persist the service principal after a successful login
        entry = sp_auth.get_entry_to_persist()
        self._msal_secret_store.save_entry(entry)

    def login_with_managed_identity(self, scopes, identity_id=None):  # pylint: disable=too-many-statements
        raise NotImplementedError

    def login_in_cloud_shell(self, scopes):
        raise NotImplementedError

    def logout_user(self, user):
        accounts = self.msal_app.get_accounts(user)
        for account in accounts:
            self.msal_app.remove_account(account)

    def logout_all_users(self):
        for e in file_extensions.values():
            _try_remove(self._token_cache_file + e)

    def logout_service_principal(self, sp):
        # remove service principal secrets
        self._msal_secret_store.remove_entry(sp)

    def logout_all_service_principal(self):
        # remove service principal secrets
        self._msal_secret_store.remove_all_entries()

    def get_user(self, user=None):
        accounts = self.msal_app.get_accounts(user) if user else self.msal_app.get_accounts()
        return accounts

    def get_user_credential(self, username):
        return UserCredential(self.client_id, username, **self._msal_app_kwargs)

    def get_service_principal_credential(self, client_id):
        entry = self._msal_secret_store.load_entry(client_id, self.tenant_id)
        sp_auth = ServicePrincipalAuth(entry)
        return ServicePrincipalCredential(sp_auth, **self._msal_app_kwargs)

    def get_service_principal_entry(self, client_id):
        """This method is only used by --sdk-auth. DO NOT use it elsewhere."""
        return self._msal_secret_store.load_entry(client_id, self.tenant_id)

    def get_managed_identity_credential(self, client_id=None):
        raise NotImplementedError


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
            _TENANT: tenant_id,
            _CLIENT_ID: client_id
        }
        entry.update(credential)
        return ServicePrincipalAuth(entry)

    @classmethod
    def build_credential(cls, secret_or_certificate=None, client_assertion=None, use_cert_sn_issuer=None):
        """Build credential from user input. The credential looks like below, but only one key can exist.
        {
            'client_secret': 'my_secret',
            'certificate': '/path/to/cert.pem',
            'client_assertion': 'my_federated_token'
        }
        """
        entry = {}
        if secret_or_certificate:
            if os.path.isfile(secret_or_certificate):
                entry[_CERTIFICATE] = secret_or_certificate
                if use_cert_sn_issuer:
                    entry[_USE_CERT_SN_ISSUER] = use_cert_sn_issuer
            else:
                entry[_CLIENT_SECRET] = secret_or_certificate
        elif client_assertion:
            entry[_CLIENT_ASSERTION] = client_assertion
        return entry

    def get_entry_to_persist(self):
        persisted_keys = [_CLIENT_ID, _TENANT, _CLIENT_SECRET, _CERTIFICATE, _USE_CERT_SN_ISSUER, _CLIENT_ASSERTION]
        return {k: v for k, v in self.__dict__.items() if k in persisted_keys}


class ServicePrincipalStore:
    """Save secrets in MSAL custom secret store for Service Principal authentication.
    """

    def __init__(self, secret_file, encrypt):
        from .persistence import load_secret_store
        self._secret_store = load_secret_store(secret_file, encrypt)
        self._secret_file = secret_file
        self._entries = []

    def load_entry(self, sp_id, tenant):
        self._load_persistence()
        matched = [x for x in self._entries if sp_id == x[_CLIENT_ID]]
        if not matched:
            raise CLIError("Could not retrieve credential from local cache for service principal {}. "
                           "Run `az login` for this service principal."
                           .format(sp_id))
        matched_with_tenant = [x for x in matched if tenant == x[_TENANT]]
        if matched_with_tenant:
            cred = matched_with_tenant[0]
        else:
            logger.warning("Could not retrieve credential from local cache for service principal %s under tenant %s. "
                           "Trying credential under tenant %s, assuming that is an app credential.",
                           sp_id, tenant, matched[0][_TENANT])
            cred = matched[0]

        return cred

    def save_entry(self, sp_entry):
        self._load_persistence()

        self._entries = [
            x for x in self._entries
            if not (sp_entry[_CLIENT_ID] == x[_CLIENT_ID] and
                    sp_entry[_TENANT] == x[_TENANT])]

        self._entries.append(sp_entry)
        self._save_persistence()

    def remove_entry(self, sp_id):
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

    def remove_all_entries(self):
        for e in file_extensions.values():
            _try_remove(self._secret_file + e)

    def _save_persistence(self):
        self._secret_store.save(self._entries)

    def _load_persistence(self):
        self._entries = self._secret_store.load()


def _get_authority_url(authority_endpoint, tenant):
    """Convert authority endpoint (active_directory) to MSAL authority:
        - AAD: https://login.microsoftonline.com/your_tenant
        - ADFS: https://adfs.redmond.azurestack.corp.microsoft.com/adfs
    For ADFS, tenant is discarded.
    """

    # Some Azure Stack (bellevue)'s metadata returns
    #   "loginEndpoint": "https://login.microsoftonline.com/"
    # Normalize it by removing the trailing /, so that authority_url won't become
    # "https://login.microsoftonline.com//tenant_id".
    authority_endpoint = authority_endpoint.rstrip('/').lower()
    is_adfs = authority_endpoint.endswith('adfs')
    if is_adfs:
        authority_url = authority_endpoint
    else:
        authority_url = '{}/{}'.format(authority_endpoint, tenant or "organizations")
    return authority_url, is_adfs


def _try_remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

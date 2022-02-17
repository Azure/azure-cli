# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import pickle
import re

from azure.cli.core._environment import get_config_dir
from azure.cli.core.decorators import retry
from msal import PublicClientApplication

from knack.log import get_logger
from knack.util import CLIError
# Service principal entry properties
from .msal_authentication import _CLIENT_ID, _TENANT, _CLIENT_SECRET, _CERTIFICATE, _CLIENT_ASSERTION, \
    _USE_CERT_SN_ISSUER
from .msal_authentication import UserCredential, ServicePrincipalCredential
from .persistence import load_persisted_token_cache, file_extensions, load_secret_store
from .util import check_result

AZURE_CLI_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'


logger = get_logger(__name__)


class Identity:  # pylint: disable=too-many-instance-attributes
    """Class to manage identities:
        - user
        - service principal
        - TODO: managed identity
    """

    # MSAL token cache.
    # It follows singleton pattern so that all MSAL app instances share the same token cache.
    _msal_token_cache = None

    # MSAL HTTP cache for MSAL's tenant discovery, retry-after error cache, etc.
    # It *must* follow singleton pattern so that all MSAL app instances share the same HTTP cache.
    # https://github.com/AzureAD/microsoft-authentication-library-for-python/pull/407
    _msal_http_cache = None

    # Instance of ServicePrincipalStore.
    # It follows singleton pattern so that _secret_file is read only once.
    _service_principal_store_instance = None

    def __init__(self, authority, tenant_id=None, client_id=None, encrypt=False, use_msal_http_cache=True):
        """
        :param authority: Authentication authority endpoint. For example,
            - AAD: https://login.microsoftonline.com
            - ADFS: https://adfs.redmond.azurestack.corp.microsoft.com/adfs
        :param tenant_id: Tenant GUID, like 00000000-0000-0000-0000-000000000000. If unspecified, default to
            'organizations'.
        :param client_id: Client ID of the CLI application.
        :param encrypt:  Whether to encrypt MSAL token cache and service principal entries.
        """
        self.authority = authority
        self.tenant_id = tenant_id
        self.client_id = client_id or AZURE_CLI_CLIENT_ID
        self._encrypt = encrypt
        self._use_msal_http_cache = use_msal_http_cache

        # Build the authority in MSAL style
        self._msal_authority, self._is_adfs = _get_authority_url(authority, tenant_id)

        config_dir = get_config_dir()
        self._token_cache_file = os.path.join(config_dir, "msal_token_cache")
        self._secret_file = os.path.join(config_dir, "service_principal_entries")
        self._http_cache_file = os.path.join(config_dir, "msal_http_cache.bin")

        # We make _msal_app_instance an instance attribute, instead of a class attribute,
        # because MSAL apps can have different tenant IDs.
        self._msal_app_instance = None

    @property
    def _msal_app_kwargs(self):
        """kwargs for creating UserCredential or ServicePrincipalCredential.
        MSAL token cache and HTTP cache are lazily created.
        """
        if not Identity._msal_token_cache:
            Identity._msal_token_cache = self._load_msal_token_cache()

        if self._use_msal_http_cache and not Identity._msal_http_cache:
            Identity._msal_http_cache = self._load_msal_http_cache()

        return {
            "authority": self._msal_authority,
            "token_cache": Identity._msal_token_cache,
            "http_cache": Identity._msal_http_cache
        }

    @property
    def _msal_app(self):
        """A PublicClientApplication instance for user login/logout.
        The instance is lazily created.
        """
        if not self._msal_app_instance:
            self._msal_app_instance = PublicClientApplication(self.client_id, **self._msal_app_kwargs)
        return self._msal_app_instance

    def _load_msal_token_cache(self):
        # Store for user token persistence
        cache = load_persisted_token_cache(self._token_cache_file, self._encrypt)
        return cache

    @retry()
    def __load_msal_http_cache(self):
        """Load MSAL HTTP cache with retry. If it still fails at last, raise the original exception as-is."""
        logger.debug("__load_msal_http_cache: %s", self._http_cache_file)
        try:
            with open(self._http_cache_file, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            # The cache file has not been created. This is expected.
            logger.debug("%s not found. Using a fresh one.", self._http_cache_file)
            return {}

    def _dump_msal_http_cache(self):
        logger.debug("_dump_msal_http_cache: %s", self._http_cache_file)
        with open(self._http_cache_file, 'wb') as f:
            # At this point, an empty cache file will be created. Loading this cache file will
            # trigger EOFError. This can be simulated by adding time.sleep(30) here.
            # So, during loading, EOFError is ignored.
            pickle.dump(self._msal_http_cache, f)

    def _load_msal_http_cache(self):
        import atexit

        logger.debug("_load_msal_http_cache: %s", self._http_cache_file)
        try:
            persisted_http_cache = self.__load_msal_http_cache()
        except (pickle.UnpicklingError, EOFError) as ex:
            # We still get exception after retry:
            # - pickle.UnpicklingError is caused by corrupted cache file, perhaps due to concurrent writes.
            # - EOFError is caused by empty cache file created by other az instance, but hasn't been filled yet.
            logger.debug("Failed to load MSAL HTTP cache: %s. Using a fresh one.", ex)
            persisted_http_cache = {}  # Ignore a non-exist or corrupted http_cache

        # When exiting, flush it back to the file.
        # If 2 processes write at the same time, the cache will be corrupted,
        # but that is fine. Subsequent runs would reach eventual consistency.
        atexit.register(self._dump_msal_http_cache)

        return persisted_http_cache

    @property
    def _service_principal_store(self):
        """A ServicePrincipalStore instance for service principal entries persistence.
        The instance is lazily created.
        """
        if not Identity._service_principal_store_instance:
            store = load_secret_store(self._secret_file, self._encrypt)
            Identity._service_principal_store_instance = ServicePrincipalStore(store)
        return Identity._service_principal_store_instance

    def login_with_auth_code(self, scopes, **kwargs):
        # Emit a warning to inform that a browser is opened.
        # Only show the path part of the URL and hide the query string.
        logger.warning("A web browser has been opened at %s. Please continue the login in the web browser. "
                       "If no web browser is available or if the web browser fails to open, use device code flow "
                       "with `az login --use-device-code`.", self._msal_app.authority.authorization_endpoint)

        from .util import read_response_templates
        success_template, error_template = read_response_templates()

        # For AAD, use port 0 to let the system choose arbitrary unused ephemeral port to avoid port collision
        # on port 8400 from the old design. However, ADFS only allows port 8400.
        result = self._msal_app.acquire_token_interactive(
            scopes, prompt='select_account', port=8400 if self._is_adfs else None,
            success_template=success_template, error_template=error_template, **kwargs)
        return check_result(result)

    def login_with_device_code(self, scopes, **kwargs):
        flow = self._msal_app.initiate_device_flow(scopes, **kwargs)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))
        logger.warning(flow["message"])
        result = self._msal_app.acquire_token_by_device_flow(flow, **kwargs)  # By default it will block
        return check_result(result)

    def login_with_username_password(self, username, password, scopes, **kwargs):
        result = self._msal_app.acquire_token_by_username_password(username, password, scopes, **kwargs)
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
        self._service_principal_store.save_entry(entry)

    def login_with_managed_identity(self, scopes, identity_id=None):  # pylint: disable=too-many-statements
        raise NotImplementedError

    def login_in_cloud_shell(self, scopes):
        raise NotImplementedError

    def logout_user(self, user):
        accounts = self._msal_app.get_accounts(user)
        for account in accounts:
            self._msal_app.remove_account(account)

    def logout_all_users(self):
        for e in file_extensions.values():
            _try_remove(self._token_cache_file + e)

    def logout_service_principal(self, sp):
        # remove service principal secrets
        self._service_principal_store.remove_entry(sp)

    def logout_all_service_principal(self):
        # remove service principal secrets
        for e in file_extensions.values():
            _try_remove(self._secret_file + e)

    def get_user(self, user=None):
        accounts = self._msal_app.get_accounts(user) if user else self._msal_app.get_accounts()
        return accounts

    def get_user_credential(self, username):
        return UserCredential(self.client_id, username, **self._msal_app_kwargs)

    def get_service_principal_credential(self, client_id):
        entry = self._service_principal_store.load_entry(client_id, self.tenant_id)
        sp_auth = ServicePrincipalAuth(entry)
        return ServicePrincipalCredential(sp_auth, **self._msal_app_kwargs)

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
            user_expanded = os.path.expanduser(secret_or_certificate)
            if os.path.isfile(user_expanded):
                entry[_CERTIFICATE] = user_expanded
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

    def __init__(self, secret_store):
        self._secret_store = secret_store
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

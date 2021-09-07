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
from .util import aad_error_handler, resource_to_scopes, check_result

AZURE_CLI_CLIENT_ID = '04b07795-8ddb-461a-bbee-02f9e1bf7b46'

_SERVICE_PRINCIPAL_ID = 'servicePrincipalId'
_SERVICE_PRINCIPAL_TENANT = 'servicePrincipalTenant'
_ACCESS_TOKEN = 'accessToken'
_SERVICE_PRINCIPAL_SECRET = 'secret'
_SERVICE_PRINCIPAL_CERT_FILE = 'certificateFile'
_SERVICE_PRINCIPAL_CERT_THUMBPRINT = 'thumbprint'

logger = get_logger(__name__)


class Identity:  # pylint: disable=too-many-instance-attributes
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

    def __init__(self, authority=None, tenant_id=None, client_id=None, **kwargs):
        """

        :param authority:
        :param tenant_id:
        :param client_id::param kwargs:
        """
        self.authority = authority
        self.tenant_id = tenant_id or "organizations"
        # Build the authority in MSAL style, like https://login.microsoftonline.com/your_tenant
        self.msal_authority = "{}/{}".format(self.authority, self.tenant_id)
        self.client_id = client_id or AZURE_CLI_CLIENT_ID

        self._token_cache_file = os.path.join(get_config_dir(), "tokenCache.bin")
        self._secret_file = os.path.join(get_config_dir(), "secrets.bin")
        self._fallback_to_plaintext = kwargs.pop('fallback_to_plaintext', True)

        self._msal_app_instance = None
        # Store for Service principal credential persistence
        self._msal_secret_store = MsalSecretStore(self._secret_file, fallback_to_plaintext=self._fallback_to_plaintext)
        self._msal_app_kwargs = {
            "authority": self.msal_authority,
            "token_cache": self._load_msal_cache(),
            "client_capabilities": ["CP1"]
        }

        # TODO: Allow disabling SSL verification
        # The underlying requests lib of MSAL has been patched with Azure Core by MsalTransportAdapter
        # connection_verify will be received by azure.core.configuration.ConnectionConfiguration
        # However, MSAL defaults verify to True, thus overriding ConnectionConfiguration
        # Still not work yet
        from azure.cli.core._debug import change_ssl_cert_verification_track2
        self._credential_kwargs = {}
        self._credential_kwargs.update(change_ssl_cert_verification_track2())

        # Turn on NetworkTraceLoggingPolicy to show DEBUG logs.
        # WARNING: This argument is only for development purpose. It will make credentials be printed to
        #   - console log, when --debug is specified
        #   - file log, when logging.enable_log_file is enabled, even without --debug
        # Credentials include and are not limited to:
        #   - Authorization code
        #   - Device code
        #   - Refresh token
        #   - Access token
        #   - Service principal secret
        #   - Service principal certificate
        self._credential_kwargs['logging_enable'] = True

        # Make MSAL remove existing accounts on successful login.
        # self._credential_kwargs['remove_existing_account'] = True
        # from azure.cli.core._msal_patch import patch_token_cache_add
        # patch_token_cache_add(self.msal_app.remove_account)

    def _load_msal_cache(self):
        from .persistence import load_persisted_token_cache
        # Store for user token persistence
        cache = load_persisted_token_cache(self._token_cache_file, self._fallback_to_plaintext)
        cache._reload_if_necessary()  # pylint: disable=protected-access
        return cache

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

    def login_with_service_principal(self, client_id, secret_or_certificate, use_cert_sn_issuer=None, scopes=None):
        sp_auth = ServicePrincipalAuth(self.tenant_id, client_id,
                                       secret_or_certificate, use_cert_sn_issuer=use_cert_sn_issuer)
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

    def logout_all_service_principal(self, sp):
        # remove service principal secrets
        self._msal_secret_store.remove_all_credentials()

    def get_user(self, user=None):
        accounts = self.msal_app.get_accounts(user) if user else self.msal_app.get_accounts()
        return accounts

    def get_user_credential(self, username):
        return UserCredential(self.client_id, username, **self._msal_app_kwargs)

    def get_service_principal_credential(self, client_id, use_cert_sn_issuer=False):
        entry = self._msal_secret_store.load_credential(client_id, self.tenant_id)
        # TODO: support use_cert_sn_issuer in CertificateCredential
        sp_auth = ServicePrincipalAuth.build_from_entry(entry)
        return ServicePrincipalCredential(sp_auth, **self._msal_app_kwargs)

    def get_managed_identity_credential(self, client_id=None):
        raise NotImplemented

    def serialize_token_cache(self, path=None):
        path = path or os.path.join(get_config_dir(), "msal.cache.snapshot.json")
        path = os.path.expanduser(path)
        logger.warning("Token cache is exported to '%s'. The exported cache is unencrypted. "
                       "It contains login information of all logged-in users. Make sure you protect it safely.", path)

        cache = self._load_msal_cache()
        with open(path, "w") as fd:
            fd.write(cache.serialize())


class ServicePrincipalAuth:   # pylint: disable=too-few-public-methods

    def __init__(self, tenant_id, client_id, password_arg_value, use_cert_sn_issuer=None):
        if not password_arg_value:
            raise CLIError('missing secret or certificate in order to '
                           'authenticate through a service principal')

        self.client_id = client_id
        self.tenant_id = tenant_id

        if os.path.isfile(password_arg_value):
            certificate_file = password_arg_value
            from OpenSSL.crypto import load_certificate, FILETYPE_PEM, Error
            self.certificate_file = certificate_file
            self.public_certificate = None
            try:
                with open(certificate_file, 'r') as file_reader:
                    self.cert_file_string = file_reader.read()
                    cert = load_certificate(FILETYPE_PEM, self.cert_file_string)
                    self.thumbprint = cert.digest("sha1").decode().replace(':', '')
                    if use_cert_sn_issuer:
                        # low-tech but safe parsing based on
                        # https://github.com/libressl-portable/openbsd/blob/master/src/lib/libcrypto/pem/pem.h
                        match = re.search(r'-+BEGIN CERTIFICATE.+-+(?P<public>[^-]+)-+END CERTIFICATE.+-+',
                                          self.cert_file_string, re.I)
                        self.public_certificate = match.group('public').strip()
            except (UnicodeDecodeError, Error) as ex:
                raise CLIError('Invalid certificate, please use a valid PEM file. Error detail: {}'.format(ex))
        else:
            self.secret = password_arg_value

    @classmethod
    def build_from_entry(cls, entry):
        return ServicePrincipalAuth(entry.get(_SERVICE_PRINCIPAL_TENANT),
                                    entry.get(_SERVICE_PRINCIPAL_ID),
                                    entry.get(_SERVICE_PRINCIPAL_SECRET) or entry.get(_SERVICE_PRINCIPAL_CERT_FILE))

    def get_entry_to_persist(self):
        entry = {
            _SERVICE_PRINCIPAL_ID: self.client_id,
            _SERVICE_PRINCIPAL_TENANT: self.tenant_id,
        }
        if hasattr(self, 'secret'):
            entry[_SERVICE_PRINCIPAL_SECRET] = self.secret
        else:
            entry[_SERVICE_PRINCIPAL_CERT_FILE] = self.certificate_file
        return entry


class MsalSecretStore:
    """Caches secrets in MSAL custom secret store for Service Principal authentication.
    """

    def __init__(self, secret_file, fallback_to_plaintext=True):
        self._secret_file = secret_file
        self._lock_file = self._secret_file + '.lock'
        self._service_principal_creds = []
        self._fallback_to_plaintext = fallback_to_plaintext

    def load_credential(self, sp_id, tenant):
        self._load_persistence()
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

        return cred

    def save_credential(self, sp_entry):
        self._load_persistence()
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
            self._save_persistence()
        self._serialize_secrets()

    def remove_credential(self, sp_id):
        self._load_persistence()
        state_changed = False

        # clear service principal creds
        matched = [x for x in self._service_principal_creds
                   if x[_SERVICE_PRINCIPAL_ID] == sp_id]
        if matched:
            state_changed = True
            self._service_principal_creds = [x for x in self._service_principal_creds
                                             if x not in matched]

        if state_changed:
            self._save_persistence()

    def remove_all_credentials(self):
        try:
            os.remove(self._secret_file)
        except FileNotFoundError:
            pass

    def _save_persistence(self):
        from .persistence import build_persistence
        persistence = build_persistence(self._secret_file)
        from msal_extensions import CrossPlatLock
        with CrossPlatLock(self._lock_file):
            persistence.save(json.dumps(self._service_principal_creds))

    def _load_persistence(self):
        from .persistence import build_persistence
        persistence = build_persistence(self._secret_file)
        from msal_extensions import CrossPlatLock
        from msal_extensions.persistence import PersistenceNotFound
        with CrossPlatLock(self._lock_file):
            try:
                self._service_principal_creds = json.loads(persistence.load())
            except PersistenceNotFound:
                pass
            except Exception as ex:
                raise CLIError("Failed to load token files. If you can reproduce, please log an issue at "
                               "https://github.com/Azure/azure-cli/issues. At the same time, you can clean "
                               "up by running 'az account clear' and then 'az login'. (Inner Error: {})".format(ex))

    def _serialize_secrets(self):
        # ONLY FOR DEBUGGING PURPOSE. DO NOT USE IN PRODUCTION CODE.
        logger.warning("Secrets are serialized as plain text and saved to `msalSecrets.cache.json`.")
        with open(self._secret_file + ".json", "w") as fd:
            fd.write(json.dumps(self._service_principal_creds, indent=4))


def _read_response_templates():
    """Read from success.html and error.html to strings and pass them to MSAL. """
    success_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'auth_landing_pages', 'success.html')
    with open(success_file) as f:
        success_template = f.read()

    error_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'auth_landing_pages', 'error.html')
    with open(error_file) as f:
        error_template = f.read()

    return success_template, error_template

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Live tests for credential persistence encryption, using service principal authentication.

These tests exercise the real OS credential store (Windows DPAPI, macOS Keychain, Linux libsecret),
so they cannot be recorded. On Linux they need a working D-Bus session and an unlocked keyring;
where that is unavailable the CLI falls back to plaintext and the encryption tests are skipped.

Required environment variables, which default to the cli-encryption-livetest application and its
certificate under ~/.certs, so a machine set up that way needs none of them:
    AZURE_CLI_TEST_DEV_SP_NAME      service principal app ID
    AZURE_CLI_TEST_DEV_SP_TENANT    tenant ID of the service principal
    AZURE_CLI_TEST_DEV_SP_PASSWORD  service principal secret, or
    AZURE_CLI_TEST_DEV_SP_CERT      PEM file with the key and public certificate

MultiIdentityCredentialScenarioTest provisions throwaway directory identities, which needs the
Microsoft Graph application permissions Application.ReadWrite.OwnedBy, User.ReadWrite.All and
Domain.Read.All granted to that service principal. Without them the class skips rather than fails.
The identities are granted only the Reader role, and are deleted after the class; the configured
service principal that creates them is never deleted.
"""

import json
import os
import secrets
import string
import subprocess
import sys
import time
import unittest
import uuid

from azure.cli.core._environment import get_config_dir
from azure.cli.core.auth.persistence import (CREDENTIAL_STORE_NOT_CLEARED_WARNING,
                                             CREDENTIAL_STORE_UNAVAILABLE_WARNING,
                                             ENCRYPTION_FALLBACK_WARNING, KEYCHAIN_SERVICE_NAME,
                                             LIBSECRET_SCHEMA_NAME, file_extension_encrypted,
                                             file_extension_plaintext, file_extension_signal)
from azure.cli.testsdk import LiveScenarioTest

TOKEN_CACHE = 'msal_token_cache'
SECRET_STORE = 'service_principal_entries'

# The persistence type names that identify each credential inside the OS credential store,
# passed by load_persisted_token_cache and load_secret_store.
TOKEN_CACHE_TYPE = 'Token cache'
SECRET_STORE_TYPE = 'Secret store'

# Defaults for the developer setup these tests were written against: the cli-encryption-livetest
# application, authenticated with a certificate. Only the PEM holds a secret, and it stays on disk.
# The environment variables win, so another tenant needs no code change.
DEFAULT_SP_NAME = 'd4ca850a-a74f-42cb-b993-0e77fc858ec5'
DEFAULT_SP_TENANT = '0b7d2d22-21a7-44c3-975c-eb2c10efb5b6'
DEFAULT_SP_CERT = os.path.expanduser('~/.certs/cli-encryption-livetest.pem')

SP_NAME = os.environ.get('AZURE_CLI_TEST_DEV_SP_NAME') or DEFAULT_SP_NAME
SP_PASSWORD = os.environ.get('AZURE_CLI_TEST_DEV_SP_PASSWORD')
SP_CERT = os.environ.get('AZURE_CLI_TEST_DEV_SP_CERT')
SP_TENANT = os.environ.get('AZURE_CLI_TEST_DEV_SP_TENANT') or DEFAULT_SP_TENANT

if not SP_PASSWORD and not SP_CERT and os.path.isfile(DEFAULT_SP_CERT):
    SP_CERT = DEFAULT_SP_CERT


def _configured_sp_auth_args():
    """How to authenticate the configured service principal.

    --password stopped accepting a certificate, so a certificate-based service principal has to be
    passed with --certificate instead. The throwaway applications this module creates always use a
    generated secret, and are unaffected.
    """
    return ['--certificate', SP_CERT] if SP_CERT else ['-p', SP_PASSWORD]


def _path(name, extension):
    return os.path.join(get_config_dir(), name + extension)


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


def _remove_persistence_files():
    for name in (TOKEN_CACHE, SECRET_STORE):
        for extension in (file_extension_encrypted, file_extension_plaintext, file_extension_signal):
            try:
                os.remove(_path(name, extension))
            except FileNotFoundError:
                pass


def _encryption_available():
    """Ask the persistence layer whether the OS credential store can be used.

    build_persistence falls back to plaintext FilePersistence when the store is unavailable
    (no D-Bus session, locked keyring, missing gir1.2-secret-1), so is_encrypted reports the
    real outcome. Probing beats inferring from which file appeared, because it also works
    before a login has happened.
    """
    from azure.cli.core.auth.persistence import build_persistence
    probe = os.path.join(get_config_dir(), 'encryption_probe')
    try:
        return build_persistence(probe, True).is_encrypted
    finally:
        for extension in (file_extension_encrypted, file_extension_plaintext, file_extension_signal):
            try:
                os.remove(probe + extension)
            except FileNotFoundError:
                pass


def _keychain_lookup(persistence_type):
    """Read a generic password from the macOS Keychain."""
    result = subprocess.run(
        ['security', 'find-generic-password',
         '-s', KEYCHAIN_SERVICE_NAME, '-a', persistence_type, '-w'],
        capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def _libsecret_lookup(persistence_type):
    """Read a secret from libsecret, bypassing msal-extensions."""
    import gi
    gi.require_version('Secret', '1')
    from gi.repository import Secret

    schema = Secret.Schema.new(LIBSECRET_SCHEMA_NAME, Secret.SchemaFlags.NONE,
                               {'type': Secret.SchemaAttributeType.STRING})
    return Secret.password_lookup_sync(schema, {'type': persistence_type}, None)


def _os_credential_store_lookup():
    """The platform's credential store reader, or None where there is nothing to query."""
    if sys.platform.startswith('darwin'):
        return _keychain_lookup
    if sys.platform.startswith('linux'):
        return _libsecret_lookup
    return None


def _encrypted_extension():
    """The file an encrypted persistence creates.

    Windows keeps the ciphertext in the file itself; macOS and Linux keep the payload in Keychain
    or libsecret and use the file only as a modification signal.
    """
    return file_extension_encrypted if os.name == 'nt' else file_extension_signal


# Secrets that must never reach the console or a CI log: the configured service principal password,
# plus anything the multi-identity fixture generates for itself.
_generated_secrets = {s for s in (SP_PASSWORD,) if s}


def _scrub(text):
    for secret in _generated_secrets:
        text = text.replace(secret, '***')
    return text


def _run_az(args, env=None, check=True):
    """Run the CLI under test in a child process.

    Every real invocation of az is a new process that reads the credential store from scratch.
    Running in-process instead would let one test's Identity._msal_token_cache serve the next, so
    a stale persistence could satisfy a test that a real user would see fail. It also means the
    environment is read at build_persistence time, which is how the encryption and D-Bus cases are
    varied, and it keeps credentials off the console: self.cmd echoes the command line.
    """
    process = subprocess.run([sys.executable, '-m', 'azure.cli', *args],
                             capture_output=True, text=True, check=False,
                             env={**os.environ, **(env or {})})
    if check and process.returncode:
        raise AssertionError(f'az {" ".join(args[:2])} failed: {_scrub(process.stderr.strip())[:800]}')
    return process


def _run_az_json(args, env=None):
    process = _run_az([*args, '-o', 'json'], env=env)
    return json.loads(process.stdout) if process.stdout.strip() else None


def _run_az_json_when_replicated(args, timeout=120):
    """Run a Graph command that operates on a just-created directory object.

    A new object is not visible to every Graph replica immediately, and until it is the failure is
    reported as the object not existing, or as its application not being in this tenant. Only time
    fixes it, and a single attempt is flaky often enough to fail the whole class in setup.
    """
    deadline = time.time() + timeout
    while True:
        process = _run_az([*args, '-o', 'json'], check=False)
        if not process.returncode:
            return json.loads(process.stdout) if process.stdout.strip() else None
        if time.time() > deadline:
            raise AssertionError(f'az {" ".join(args[:2])} never succeeded: '
                                 f'{_scrub(process.stderr.strip())[:500]}')
        time.sleep(5)


UNREACHABLE_DBUS = 'unix:path=/nonexistent'
IDENTITY_PREFIX = 'clitest-encryption'

# A scope no login has already fetched a token for. The default ARM scope is cached in the token
# cache by the login itself, so asking for it again can be answered without ever reading the secret
# store. A service principal has no refresh token, so an uncached scope forces the persisted secret
# to be read and is the only probe that proves the store is usable rather than merely present.
UNCACHED_SCOPE = 'https://graph.microsoft.com/.default'


def _generate_password():
    """A per-run password that satisfies Entra ID complexity rules."""
    pool = string.ascii_letters + string.digits
    password = 'Az9!' + ''.join(secrets.choice(pool) for _ in range(20))
    _generated_secrets.add(password)
    return password


class DirectoryIdentity:
    """A throwaway user or application.

    Logging in needs a name and a password for both kinds, deleting needs the id the directory
    knows it by, so the two are kept apart: for an application they are different values.
    A role assignment needs a third value, because an application is granted a role through its
    service principal rather than through the application object.
    """

    def __init__(self, kind, login_name, password, directory_id, display_name, principal_id):
        self.kind = kind
        self.login_name = login_name
        self.password = password
        self.directory_id = directory_id
        self.display_name = display_name
        self.principal_id = principal_id

    @property
    def is_user(self):
        return self.kind == 'user'

    def __repr__(self):
        # Deliberately without the password: unittest prints identities in failure messages.
        return f'<{self.kind} {self.display_name}>'


class MultiIdentityCredentialScenarioTest(LiveScenarioTest):
    """Covers a profile holding several identities at once, across the encryption backends.

    The single-identity tests cannot tell "cleared everything" apart from "cleared the one thing
    that was there". Two users and two service principals make the difference observable: a logout
    must remove exactly one identity and leave the other three usable, and only 'az account clear'
    may empty the store.

    The identities are created before the tests and deleted after them, so nothing is shared with
    the developer's own directory objects and no credential needs to be configured by hand.
    """

    identities = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not (SP_NAME and SP_TENANT and (SP_PASSWORD or SP_CERT)):
            raise unittest.SkipTest(
                'Set AZURE_CLI_TEST_DEV_SP_NAME/TENANT and PASSWORD or CERT to provision identities')

        cls._admin_login()
        try:
            # Identities a previous run failed to delete would otherwise accumulate in the tenant.
            cls._sweep_leftover_identities()
            domain = cls._verified_domain()
            cls.identities = ([cls._create_user(domain, i) for i in (1, 2)] +
                              [cls._create_application(i) for i in (1, 2)])
            cls._grant_read_only_role()
            # Inside the try: unittest skips tearDownClass when setUpClass raises, so anything
            # that fails from here on has to delete the identities itself or they leak.
            cls._wait_until_usable()
        except AssertionError as ex:
            if 'Insufficient privileges' in str(ex) or 'Authorization_RequestDenied' in str(ex):
                cls._delete_identities()
                raise unittest.SkipTest(
                    'The test service principal cannot provision directory identities. Grant it the '
                    'Microsoft Graph application permissions Application.ReadWrite.OwnedBy, '
                    'User.ReadWrite.All and Domain.Read.All, then admin-consent them.') from ex
            cls._delete_identities()
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            _run_az(['account', 'clear'], check=False)
            cls._admin_login()
            cls._delete_identities()
            _run_az(['account', 'clear'], check=False)
        finally:
            super().tearDownClass()

    @classmethod
    def _delete_identities(cls):
        for identity in cls.identities:
            # Best effort: one failed delete must not strand the others in the tenant.
            noun = 'user' if identity.is_user else 'app'
            _run_az(['ad', noun, 'delete', '--id', identity.directory_id], check=False)
        cls.identities = []

    # -- provisioning ------------------------------------------------------------------------

    @classmethod
    def _admin_login(cls):
        """Sign in as the configured service principal, which owns the throwaway identities."""
        _run_az(['login', '--service-principal', '-u', SP_NAME, *_configured_sp_auth_args(),
                 '--tenant', SP_TENANT, '--allow-no-subscriptions', '-o', 'none'])

    @classmethod
    def _verified_domain(cls):
        """The tenant domain a user principal name has to be under."""
        domains = _run_az_json(['rest', '--method', 'get',
                                '--url', 'https://graph.microsoft.com/v1.0/domains'])['value']
        verified = [d for d in domains if d.get('isVerified')]
        default = next((d for d in verified if d.get('isDefault')), None)
        return (default or verified[0])['id']

    @classmethod
    def _create_user(cls, domain, index):
        display_name = f'{IDENTITY_PREFIX}-user{index}-{uuid.uuid4().hex[:8]}'
        password = _generate_password()
        # force-change-password would send the next sign-in to an interactive prompt, which a
        # username/password login cannot answer.
        created = _run_az_json(['ad', 'user', 'create',
                                '--display-name', display_name,
                                '--user-principal-name', f'{display_name}@{domain}',
                                '--password', password,
                                '--force-change-password-next-sign-in', 'false'])
        return DirectoryIdentity('user', created['userPrincipalName'], password,
                                 created['id'], display_name, created['id'])

    @classmethod
    def _create_application(cls, index):
        display_name = f'{IDENTITY_PREFIX}-app{index}-{uuid.uuid4().hex[:8]}'
        application = _run_az_json(['ad', 'app', 'create', '--display-name', display_name])
        # create-for-rbac is avoided so that the role assignment stays explicit and read-only;
        # it would otherwise grant Contributor over the whole subscription.
        service_principal = _run_az_json_when_replicated(['ad', 'sp', 'create',
                                                          '--id', application['appId']])
        credential = _run_az_json_when_replicated(['ad', 'app', 'credential', 'reset',
                                                   '--id', application['appId'], '--years', '1'])
        _generated_secrets.add(credential['password'])
        return DirectoryIdentity('sp', application['appId'], credential['password'],
                                 application['id'], display_name, service_principal['id'])

    @classmethod
    def _grant_read_only_role(cls):
        """Give every throwaway identity the Reader role, and nothing more.

        These identities only have to authenticate, so Reader is the least privilege that still
        lets a token be requested for a real resource. The grant is best effort: the admin service
        principal needs Owner or User Access Administrator to assign a role, and the tests do not
        depend on the data plane, so a directory without a visible subscription still runs them.
        """
        subscription = _run_az(['account', 'show', '-o', 'json'], check=False)
        if subscription.returncode or not subscription.stdout.strip():
            # The admin service principal signs in with --allow-no-subscriptions, so a directory
            # without one is expected. These tests only need to authenticate, so there is nothing
            # to grant and nothing to fail.
            return
        subscription_id = json.loads(subscription.stdout).get('id')
        if not subscription_id:
            return
        scope = f'/subscriptions/{subscription_id}'
        for identity in cls.identities:
            _run_az(['role', 'assignment', 'create',
                     '--assignee-object-id', identity.principal_id,
                     '--assignee-principal-type', 'User' if identity.is_user else 'ServicePrincipal',
                     '--role', 'Reader', '--scope', scope, '-o', 'none'], check=False)

    @classmethod
    def _sweep_leftover_identities(cls):
        """Delete identities a previous run failed to clean up, so they cannot accumulate."""
        for noun, key in (('user', 'displayName'), ('app', 'displayName')):
            found = _run_az_json(['ad', noun, 'list',
                                  '--filter', f"startswith({key},'{IDENTITY_PREFIX}')"]) or []
            for item in found:
                _run_az(['ad', noun, 'delete', '--id', item['id']], check=False)

    @classmethod
    def _wait_until_usable(cls, timeout=180):
        """Wait for the new identities to replicate.

        A directory object is not immediately usable for authentication, and the errors are the
        same ones a genuinely broken credential gives, so failing here beats failing inside a test.
        """
        deadline = time.time() + timeout
        for identity in cls.identities:
            while True:
                process = _run_az(cls._login_args(identity) + ['-o', 'none'], check=False)
                if not process.returncode:
                    break
                if time.time() > deadline:
                    raise AssertionError(f'{identity} never became usable: '
                                         f'{_scrub(process.stderr.strip())[:500]}')
                time.sleep(5)
        _run_az(['account', 'clear'])

    @staticmethod
    def _login_args(identity):
        if identity.is_user:
            return ['login', '--username', identity.login_name, '--password', identity.password,
                    '--tenant', SP_TENANT, '--allow-no-subscriptions']
        return ['login', '--service-principal', '-u', identity.login_name,
                '-p', identity.password, '--tenant', SP_TENANT, '--allow-no-subscriptions']

    # -- per-test state ----------------------------------------------------------------------

    def setUp(self):
        super().setUp()
        _run_az(['account', 'clear'])
        _remove_persistence_files()

    def tearDown(self):
        _run_az(['account', 'clear'], check=False)
        _run_az(['config', 'unset', 'core.encrypt_token_cache'], check=False)
        _remove_persistence_files()
        super().tearDown()

    # -- helpers -----------------------------------------------------------------------------

    @staticmethod
    def _case_env(encrypt, dbus_broken):
        """The environment that selects a persistence backend, without writing to the config file.

        AZURE_CORE_ENCRYPT_TOKEN_CACHE is the process-local form of core.encrypt_token_cache, and an
        unreachable D-Bus address is the only way to make libsecret fail without touching the
        machine's keyring setup.
        """
        env = {'AZURE_CORE_ENCRYPT_TOKEN_CACHE': 'true' if encrypt else 'false'}
        if dbus_broken:
            env['DBUS_SESSION_BUS_ADDRESS'] = UNREACHABLE_DBUS
        return env

    def _login_all(self, env):
        for identity in self.identities:
            self._login(identity, env)

    @classmethod
    def _login(cls, identity, env=None, extra_args=(), attempts=4):
        """Sign an identity in, retrying the replication errors the directory keeps returning.

        A throwaway identity can stop authenticating again minutes after it first worked, with
        AADSTS7000215 or AADSTS700016, so a single failure says nothing about the CLI.
        """
        transient = ('AADSTS7000215', 'AADSTS700016', 'AADSTS50034', 'AADSTS90002')
        for attempt in range(attempts):
            process = _run_az(cls._login_args(identity) + [*extra_args, '-o', 'none'],
                              env=env, check=False)
            if not process.returncode:
                return process
            if attempt == attempts - 1 or not any(code in process.stderr for code in transient):
                raise AssertionError(f'signing in {identity} failed: '
                                     f'{_scrub(process.stderr.strip())[:800]}')
            time.sleep(10)

    @staticmethod
    def _logged_in_names(env):
        accounts = _run_az_json(['account', 'list', '--all'], env=env) or []
        return {account['user']['name'] for account in accounts}

    @staticmethod
    def _cached_usernames(payload):
        """The users a token cache payload holds."""
        return {account.get('username', '').lower()
                for account in json.loads(payload or '{}').get('Account', {}).values()}

    @staticmethod
    def _stored_client_ids(payload):
        """The applications a secret store payload holds."""
        return {entry.get('client_id') for entry in json.loads(payload or '[]')}

    def _stored_payload(self, name, persistence_type, encrypted):
        """The persisted payload, read from wherever this backend actually keeps it."""
        if not encrypted:
            path = _path(name, file_extension_plaintext)
            return _read(path).decode('utf-8') if os.path.isfile(path) else ''
        lookup = _os_credential_store_lookup()
        if not lookup:
            # Windows DPAPI ciphertext cannot be read back without decrypting it.
            return None
        return lookup(persistence_type) or ''

    def _default_case(self):
        """The backend a developer actually runs with: encrypted when the OS store is available."""
        encrypted = _encryption_available()
        return self._case_env(encrypt=encrypted, dbus_broken=False), encrypted

    def _assert_all_credentials_present(self, env, encrypted, exclusive=True):
        """Every one of the four identities is in the right store.

        Users and service principals are persisted differently: a user leaves refresh tokens and an
        account record in the MSAL token cache, while a service principal secret goes to the secret
        store. Asserting both separately is what makes a later logout provably selective.

        `exclusive` is false when an earlier phase deliberately left the other backend populated,
        as when the encryption setting is flipped: the leftover is the point of the test, not a leak.
        """
        # The profile cannot say who is signed in here. All four identities are tenant level
        # accounts in one tenant, and _set_subscriptions keys those by tenant id alone, so each
        # login overwrites the previous one. Only the credential stores hold all four at once.
        self.assertTrue(self._logged_in_names(env), 'no identity reached the profile')

        users = [i for i in self.identities if i.is_user]
        service_principals = [i for i in self.identities if not i.is_user]

        for name, extension in ((TOKEN_CACHE, _encrypted_extension() if encrypted else file_extension_plaintext),
                                (SECRET_STORE, _encrypted_extension() if encrypted else file_extension_plaintext)):
            self.assertTrue(os.path.isfile(_path(name, extension)),
                            f'{name}{extension} was not created')
        if encrypted and exclusive:
            # The readable copy must not exist alongside the encrypted one.
            for name in (TOKEN_CACHE, SECRET_STORE):
                self.assertFalse(os.path.isfile(_path(name, file_extension_plaintext)),
                                 f'{name} was written in plaintext despite encryption')

        if encrypted:
            if _encrypted_extension() == file_extension_signal:
                # The signal file exists only to carry a modification time. A payload written there
                # would satisfy every other assertion, because they all read through the store.
                for name in (TOKEN_CACHE, SECRET_STORE):
                    self.assertEqual(os.path.getsize(_path(name, file_extension_signal)), 0,
                                     f'{name}{file_extension_signal} must not hold any payload')

            # Scanned while the credentials are live, the only point at which a leak can exist: a
            # clear deletes the files. Meaningful only with encryption on, because the plaintext
            # secret store is supposed to hold the secrets in the clear.
            for secret in _generated_secrets:
                for name in (TOKEN_CACHE, SECRET_STORE):
                    path = _path(name, _encrypted_extension())
                    if os.path.isfile(path):
                        self.assertNotIn(secret.encode(), _read(path))

        secret_store = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, encrypted)
        token_cache = self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, encrypted)
        if secret_store is None:
            # Windows DPAPI ciphertext cannot be read back, so the profile check above is all there is.
            return

        # The two persistences must occupy distinct entries in the OS credential store. Sharing one
        # made the secret store hand back the token cache's JSON object, which surfaced as a
        # TypeError on the next command instead of as a failure here.
        entries = json.loads(secret_store or '[]')
        self.assertIsInstance(entries, list, 'secret store returned token cache content')
        for entry in entries:
            self.assertIsInstance(entry, dict, 'secret store returned token cache content')
        self.assertIsInstance(json.loads(token_cache or '{}'), dict,
                              'token cache returned secret store content')

        stored_clients = self._stored_client_ids(secret_store)
        for identity in service_principals:
            self.assertIn(identity.login_name, stored_clients,
                          f'{identity} is missing from the secret store')
        for identity in users:
            self.assertNotIn(identity.login_name, stored_clients,
                             f'{identity} was written to the service principal secret store')

        cache = json.loads(token_cache or '{}')
        cached_users = self._cached_usernames(token_cache)
        for identity in users:
            self.assertIn(identity.login_name.lower(), cached_users,
                          f'{identity} is missing from the token cache')
        self.assertTrue(cache.get('RefreshToken'), 'no refresh token was persisted')

    def _assert_token_from_store(self, env, message):
        """The active identity can get a token for an uncached scope, so the store was read."""
        granted = _run_az(['account', 'get-access-token', '--scope', UNCACHED_SCOPE, '-o', 'none'],
                          env=env, check=False)
        self.assertEqual(granted.returncode, 0,
                         f'{message}: {_scrub(granted.stderr.strip())[:500]}')

    def _assert_os_store_still_holds_the_identities(self, message):
        """The payload survived, read from the credential store rather than through az.

        A token request cannot show this after a clear: the clear empties the profile, so every
        request fails afterwards whatever the store still holds.
        """
        self.assertTrue(
            self._cached_usernames(self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, True)),
            f'{message}: the token cache is empty')
        self.assertTrue(
            self._stored_client_ids(self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, True)),
            f'{message}: the secret store is empty')

    def _assert_no_token_from_store(self, env, message):
        """The same request is refused, so the store this setting selects holds nothing usable."""
        refused = _run_az(['account', 'get-access-token', '--scope', UNCACHED_SCOPE, '-o', 'none'],
                          env=env, check=False)
        self.assertNotEqual(refused.returncode, 0,
                            f'{message}: {_scrub(refused.stderr.strip())[:500]}')

    def _assert_no_credentials_remain(self, encrypted, signal_file_kept=False):
        """Nothing readable is left, in files or in the OS credential store.

        `signal_file_kept` is set after a clear run with encryption off: the credential store is
        not touched then, so the signal file stays as the evidence that it may still hold a payload.
        """
        extensions = [file_extension_encrypted, file_extension_plaintext]
        if not signal_file_kept:
            extensions.append(file_extension_signal)
        for name in (TOKEN_CACHE, SECRET_STORE):
            for extension in extensions:
                self.assertFalse(os.path.isfile(_path(name, extension)),
                                 f'{name}{extension} outlived the clear')

        secret_store = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, encrypted)
        token_cache = self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, encrypted)
        if secret_store is None:
            return
        self.assertFalse(json.loads(secret_store or '[]'), 'service principal secrets outlived the clear')
        cache = json.loads(token_cache or '{}')
        for credential_type in ('AccessToken', 'RefreshToken', 'IdToken', 'Account'):
            self.assertFalse(cache.get(credential_type), f'{credential_type} outlived the clear')

    def _run_matrix_case(self, encrypt, dbus_broken):
        """Log in all four identities, log two out one at a time, clear, then log in again."""
        env = self._case_env(encrypt, dbus_broken)
        # Encryption only really happens when it is both asked for and available.
        encrypted = encrypt and not dbus_broken and _encryption_available()

        self._login_all(env)
        self._assert_all_credentials_present(env, encrypted)

        user, service_principal = self.identities[0], self.identities[2]

        # A logout must take exactly one identity with it. The survivor is checked in the store
        # rather than the profile: all four are tenant level accounts in one tenant, so the
        # profile keeps only the identity that logged in last.
        survivor = self.identities[1]
        for identity in (user, service_principal):
            _run_az(['logout', '--username', identity.login_name], env=env)
            remaining = self._logged_in_names(env)
            self.assertNotIn(identity.login_name, remaining, f'{identity} outlived its logout')
            token_cache = self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, encrypted)
            if token_cache is not None:
                self.assertIn(survivor.login_name.lower(), self._cached_usernames(token_cache),
                              'logging out one identity removed another')

            # The other service principal's secret has to still be there to refresh with.
            payload = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, encrypted)
            if payload is not None and not identity.is_user:
                entries = json.loads(payload or '[]')
                self.assertFalse(any(e.get('client_id') == identity.login_name for e in entries))
                self.assertTrue(any(e.get('client_id') == self.identities[3].login_name
                                    for e in entries),
                                'logging out one service principal removed the other')

        # Whatever is left must still work, so the logouts did not corrupt the store.
        self._assert_token_from_store(env, 'the store stopped serving tokens after the logouts')

        _run_az(['account', 'clear'], env=env)
        self.assertFalse(self._logged_in_names(env), 'the profile still lists accounts after a clear')
        self._assert_no_credentials_remain(encrypted)

        # A cleared store must still be usable. Nothing is removed by hand here, so the login sees
        # the state the clear left behind, and it runs under the same backend that did the clear.
        self._login_all(env)
        self._assert_all_credentials_present(env, encrypted)
        # Only reachable if the service principal secrets survived the round trip: there is no
        # refresh token to fall back on, and the scope is one no login has already cached.
        self._assert_token_from_store(env, 'the store was not usable again after the clear')

    # -- one command at a time ---------------------------------------------------------------

    def test_logout_single_user_keeps_the_other_three(self):
        """'az logout --username <upn>' must take one user and leave everything else signed in."""
        env, encrypted = self._default_case()
        self._login_all(env)
        self._assert_all_credentials_present(env, encrypted)

        target = self.identities[0]
        _run_az(['logout', '--username', target.login_name], env=env)

        remaining = self._logged_in_names(env)
        self.assertNotIn(target.login_name, remaining, f'{target} outlived its logout')

        token_cache = self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, encrypted)
        if token_cache is not None:
            cached_users = self._cached_usernames(token_cache)
            self.assertNotIn(target.login_name.lower(), cached_users,
                             'the token cache still holds the logged out user')
            self.assertIn(self.identities[1].login_name.lower(), cached_users,
                          'logging out one user removed the other from the token cache')

        # The service principal secrets are unrelated to a user logout and must be untouched.
        secret_store = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, encrypted)
        if secret_store is not None:
            stored_clients = self._stored_client_ids(secret_store)
            for identity in self.identities[2:]:
                self.assertIn(identity.login_name, stored_clients,
                              'a user logout removed a service principal secret')

    def test_logout_single_application_keeps_the_other_three(self):
        """'az logout --username <appId>' must take one service principal and no more."""
        env, encrypted = self._default_case()
        self._login_all(env)
        self._assert_all_credentials_present(env, encrypted)

        target, survivor = self.identities[2], self.identities[3]
        _run_az(['logout', '--username', target.login_name], env=env)

        remaining = self._logged_in_names(env)
        self.assertNotIn(target.login_name, remaining, f'{target} outlived its logout')

        secret_store = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, encrypted)
        if secret_store is not None:
            stored_clients = self._stored_client_ids(secret_store)
            self.assertNotIn(target.login_name, stored_clients,
                             'the secret store still holds the logged out application')
            self.assertIn(survivor.login_name, stored_clients,
                          'logging out one application removed the other secret')

        # The surviving service principal must still be able to refresh with what is left.
        self._assert_token_from_store(env, 'the surviving application could not get a token')

    def test_account_clear_removes_all_four_identities(self):
        """'az account clear' is the only command allowed to empty the store."""
        env, encrypted = self._default_case()
        self._login_all(env)
        self._assert_all_credentials_present(env, encrypted)

        _run_az(['account', 'clear'], env=env)

        self.assertFalse(self._logged_in_names(env), 'the profile still lists accounts after a clear')
        self._assert_no_credentials_remain(encrypted)

    # -- switching core.encrypt_token_cache ---------------------------------------------------

    def _skip_without_both_backends(self):
        if not _encryption_available():
            self.skipTest('OS credential store unavailable, both settings would be plaintext')

    def _skip_without_a_separate_os_store(self):
        """Skip where the encrypted payload is the file itself.

        Windows DPAPI has no keyring and nothing to unlock, so a clear with encryption off removes
        the ciphertext along with the plaintext file and there is no payload left to warn about.
        The escape hatch only means something where the payload lives outside the file.
        """
        self._skip_without_both_backends()
        if _encrypted_extension() != file_extension_signal:
            self.skipTest('the encrypted payload is the file itself, nothing is left behind')

    def _assert_only_plaintext_files_exist(self):
        for name in (TOKEN_CACHE, SECRET_STORE):
            self.assertTrue(os.path.isfile(_path(name, file_extension_plaintext)),
                            f'{name}{file_extension_plaintext} was not created with encryption off')
            self.assertFalse(os.path.isfile(_path(name, _encrypted_extension())),
                             f'{name}{_encrypted_extension()} was created with encryption off')

    def test_switching_encryption_selects_which_persistence_is_used(self):
        """Flipping core.encrypt_token_cache switches which store the CLI reads and writes.

        All four identities are signed in under each setting, so the two stores hold the same
        identities and cannot be told apart by who is in them. Three independent things say which
        one is live: a token request made right after a flip and before any login, which can only
        be served by the store that setting selects; the other store's payload staying identical
        byte for byte across a phase that writes; and one identity logged out through the encrypted
        store alone, which the plaintext store keeps.

        Turning encryption on migrates nothing and deletes nothing, so the plaintext credentials
        written first are still there and are used again when the setting goes back to false.
        """
        self._skip_without_both_backends()
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        encrypted_env = self._case_env(encrypt=True, dbus_broken=False)

        # Phase 1: encryption off. Only the plaintext persistence exists, and it works.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store(plaintext_env, 'the plaintext store did not serve a token')
        plaintext_secrets = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, False)
        plaintext_cache = self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, False)

        # Phase 2, before signing in again: the encrypted store is still empty, so the same request
        # that just succeeded must now be refused. Success here would mean the CLI quietly fell
        # back to the plaintext credentials the setting is supposed to stop using.
        for name in (TOKEN_CACHE, SECRET_STORE):
            self.assertFalse(os.path.isfile(_path(name, _encrypted_extension())),
                             f'{name}{_encrypted_extension()} exists before any encrypted login')
        self._assert_no_token_from_store(
            encrypted_env, 'the plaintext credentials were used with encryption on')

        # Phase 2: sign the same four identities in again, into the encrypted store this time.
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True, exclusive=False)
        self._assert_token_from_store(encrypted_env, 'the encrypted store did not serve a token')

        # The plaintext files still hold exactly what phase 1 wrote: nothing was migrated into the
        # OS credential store, and nothing was written back out of it.
        for name in (TOKEN_CACHE, SECRET_STORE):
            self.assertTrue(os.path.isfile(_path(name, file_extension_plaintext)),
                            f'{name}{file_extension_plaintext} was removed when encryption was turned on')
        self.assertEqual(self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, False),
                         plaintext_secrets,
                         'the plaintext secret store was written while encryption was on')
        self.assertEqual(self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, False),
                         plaintext_cache,
                         'the plaintext token cache was written while encryption was on')

        # Take one identity out through the encrypted persistence. It is not the active one, so
        # the token probes are unaffected, but from here the two stores differ by a known identity.
        target = self.identities[2]
        _run_az(['logout', '--username', target.login_name], env=encrypted_env)
        encrypted_secrets = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, True)
        if encrypted_secrets is not None:  # Windows DPAPI ciphertext cannot be read back.
            self.assertNotIn(target.login_name, self._stored_client_ids(encrypted_secrets),
                             'the logout did not reach the encrypted secret store')
        self.assertIn(target.login_name,
                      self._stored_client_ids(
                          self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, False)),
                      'a logout with encryption on reached the plaintext secret store')

        # Phase 3, before signing in again: turning encryption off picks the pre-existing plaintext
        # persistence back up. No login has happened under this setting, so a token can only come
        # from what phase 1 wrote, and the identity dropped from the encrypted store is still there.
        self._assert_token_from_store(
            plaintext_env, 'the plaintext store from phase 1 was not picked back up')
        self.assertEqual(
            self._stored_client_ids(self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, False)),
            {i.login_name for i in self.identities if not i.is_user},
            'the plaintext secret store is not the one phase 1 wrote')
        self.assertEqual(self._cached_usernames(
            self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, False)),
            {i.login_name.lower() for i in self.identities if i.is_user},
            'the plaintext token cache is not the one phase 1 wrote')

        # Phase 3: writes go back to the plaintext store, and the encrypted one is left alone. The
        # mirror image of phase 2, which is what proves the setting selects the persistence in use.
        encrypted_secrets = self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, True)
        encrypted_cache = self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, True)
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_token_from_store(plaintext_env, 'the plaintext store stopped serving tokens')
        if encrypted_secrets is not None:
            self.assertEqual(self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, True),
                             encrypted_secrets,
                             'the encrypted secret store was written while encryption was off')
            self.assertEqual(self._stored_payload(TOKEN_CACHE, TOKEN_CACHE_TYPE, True),
                             encrypted_cache,
                             'the encrypted token cache was written while encryption was off')

    def test_account_clear_after_switching_encryption_clears_both_stores(self):
        """A clear after the setting was flipped must leave nothing behind in either store.

        All four identities are signed in with encryption off and then again with it on, so both
        persistences hold credentials at once. The clear runs with encryption on, and afterwards
        the machine has to be as good as new: nothing readable in either store, and a sign-in
        under either setting works again.
        """
        self._skip_without_both_backends()
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        encrypted_env = self._case_env(encrypt=True, dbus_broken=False)

        # Phase 1: encryption off, all four identities into the plaintext persistence.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store(plaintext_env, 'the plaintext store did not serve a token')

        # Phase 2: encryption on, the same four into the OS credential store. Both stores now hold
        # credentials, because turning encryption on migrates nothing and deletes nothing.
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True, exclusive=False)
        self._assert_token_from_store(encrypted_env, 'the encrypted store did not serve a token')
        for name in (TOKEN_CACHE, SECRET_STORE):
            self.assertTrue(os.path.isfile(_path(name, file_extension_plaintext)),
                            f'{name}{file_extension_plaintext} was removed when encryption was turned on')
            self.assertTrue(os.path.isfile(_path(name, _encrypted_extension())),
                            f'{name}{_encrypted_extension()} was not created with encryption on')

        # Phase 3: clear. Every persistence file goes, and neither store holds a credential. The
        # token request that succeeded under both settings a moment ago now fails under both.
        _run_az(['account', 'clear'], env=encrypted_env)
        self.assertFalse(self._logged_in_names(encrypted_env),
                         'the profile still lists accounts after a clear')
        self.assertFalse(self._logged_in_names(plaintext_env),
                         'turning encryption off after a clear brought accounts back')
        self._assert_no_credentials_remain(encrypted=True)
        self._assert_no_credentials_remain(encrypted=False)
        self._assert_no_token_from_store(encrypted_env, 'a credential outlived the clear')
        self._assert_no_token_from_store(
            plaintext_env, 'turning encryption off after a clear revived a credential')

        # Phase 4: turn encryption back off and sign in again. The clear left the plaintext
        # persistence usable, not merely empty.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store(
            plaintext_env, 'the plaintext store was not usable again after the clear')

    def test_account_clear_with_encryption_off_leaves_the_encrypted_store(self):
        """A clear with encryption off must not reach into the OS credential store.

        false -> true -> false leaves a payload in Keychain or libsecret while the setting says
        plaintext. Emptying it would mean opening the store, which is what prompts to unlock the
        keyring, and turning encryption off is largely a way to opt out of that prompt. So the
        payload is left alone, the signal file is kept as the evidence of it, and the user is told
        how to remove it.
        """
        self._skip_without_a_separate_os_store()
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        encrypted_env = self._case_env(encrypt=True, dbus_broken=False)

        # Phase 1: encryption off, all four identities into the plaintext persistence.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()

        # Phase 2: encryption on, the same four into the OS credential store.
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True, exclusive=False)
        self._assert_token_from_store(encrypted_env, 'the encrypted store did not serve a token')

        # Phase 3: encryption off again. Both stores hold credentials and the configured one is the
        # plaintext file.
        self._assert_token_from_store(plaintext_env, 'the plaintext store did not serve a token')
        for name in (TOKEN_CACHE, SECRET_STORE):
            self.assertTrue(os.path.isfile(_path(name, file_extension_plaintext)))
            self.assertTrue(os.path.isfile(_path(name, _encrypted_extension())))

        # Phase 4: clear, with encryption off. The plaintext files go, the signal file stays.
        cleared = _run_az(['account', 'clear'], env=plaintext_env)
        self.assertFalse(self._logged_in_names(plaintext_env),
                         'the profile still lists accounts after a clear')
        self._assert_no_credentials_remain(encrypted=False, signal_file_kept=True)
        self._assert_no_token_from_store(plaintext_env, 'a plaintext credential outlived the clear')
        for name in (TOKEN_CACHE, SECRET_STORE):
            self.assertTrue(os.path.isfile(_path(name, file_extension_signal)),
                            f'{name}{file_extension_signal} was removed, orphaning the credential store')

        # The warning is the whole user-facing contract of this path, and it is emitted once even
        # though a clear erases two locations.
        stderr = _scrub(cleared.stderr)
        self.assertEqual(stderr.count('OS credential store'), 1,
                         f'expected exactly one credential store warning, got: {stderr[:500]}')
        self.assertIn(CREDENTIAL_STORE_NOT_CLEARED_WARNING, stderr)

        # Phase 5: the encrypted payload is deliberately still there, and the documented way out is
        # to turn encryption back on and clear again.
        self._assert_os_store_still_holds_the_identities(
            'the encrypted credentials were cleared despite encryption being off')

        _run_az(['account', 'clear'], env=encrypted_env)
        self.assertFalse(self._logged_in_names(encrypted_env),
                         'the profile still lists accounts after the second clear')
        self._assert_no_credentials_remain(encrypted=True)
        self._assert_no_credentials_remain(encrypted=False)
        self._assert_no_token_from_store(
            encrypted_env, 'the encrypted credentials outlived a clear run with encryption on')

        # Phase 6: the warning stops once it is no longer true. Taking the advice removed the
        # signal files along with the payload, so a clear back under encryption off has nothing
        # left to warn about, and repeating the advice would send the user in a circle.
        silent = _run_az(['account', 'clear'], env=plaintext_env)
        self.assertNotIn('OS credential store', _scrub(silent.stderr),
                         'the clear still warned after the credential store had been emptied')

        # The store is still usable, not merely empty.
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True)
        self._assert_token_from_store(encrypted_env, 'the encrypted store was not usable again')

    def test_account_clear_with_encryption_off_is_idempotent(self):
        """Clearing twice after false -> true -> false must succeed both times.

        The second run finds the plaintext files already gone and the signal file still there, so
        it must neither raise nor stop warning: the credential store it warns about is still
        holding the phase 2 payload, and that is true on every run until encryption is turned on.
        """
        self._skip_without_a_separate_os_store()
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        encrypted_env = self._case_env(encrypt=True, dbus_broken=False)

        # false -> true -> false, so both stores hold credentials and the configured one is the file.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True, exclusive=False)

        for attempt in range(1, 3):
            cleared = _run_az(['account', 'clear'], env=plaintext_env)
            self.assertNotIn('Could not clear credentials', _scrub(cleared.stderr),
                             f'clear #{attempt} reported a failure')
            self.assertNotIn('Traceback', _scrub(cleared.stderr), f'clear #{attempt} raised')
            self.assertEqual(_scrub(cleared.stderr).count('OS credential store'), 1,
                             f'clear #{attempt} did not warn exactly once')
            self.assertIn(CREDENTIAL_STORE_NOT_CLEARED_WARNING, _scrub(cleared.stderr),
                          f'clear #{attempt} did not give the opt-out advice')
            self.assertFalse(self._logged_in_names(plaintext_env),
                             f'the profile still lists accounts after clear #{attempt}')
            self._assert_no_credentials_remain(encrypted=False, signal_file_kept=True)
            self._assert_no_token_from_store(
                plaintext_env, f'a plaintext credential outlived clear #{attempt}')

        # A clear with encryption on still removes everything, including the kept signal files.
        _run_az(['account', 'clear'], env=encrypted_env)
        self._assert_no_credentials_remain(encrypted=True)
        self._assert_no_credentials_remain(encrypted=False)

        # Both stores are still usable, not merely empty.
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True)
        self._assert_token_from_store(encrypted_env, 'the encrypted store was not usable again')

    def test_account_clear_with_encryption_off_never_writes_to_the_os_store(self):
        """The clear must not open the credential store, not merely leave its payload usable.

        A token request still succeeding only proves the payload is readable. It would also succeed
        after a write, and writing is the operation that prompts: libsecret unlocks the collection
        to store, and Keychain finds the item before modifying it. Comparing the stored bytes is
        what distinguishes 'left alone' from 'rewritten with something that still works'.
        """
        self._skip_without_a_separate_os_store()
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        encrypted_env = self._case_env(encrypt=True, dbus_broken=False)

        self._login_all(plaintext_env)
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True, exclusive=False)

        stores = ((TOKEN_CACHE, TOKEN_CACHE_TYPE), (SECRET_STORE, SECRET_STORE_TYPE))
        before = {name: (self._stored_payload(name, persistence_type, True),
                         os.stat(_path(name, file_extension_signal)).st_mtime_ns)
                  for name, persistence_type in stores}

        _run_az(['account', 'clear'], env=plaintext_env)

        for name, persistence_type in stores:
            payload, mtime = before[name]
            self.assertEqual(self._stored_payload(name, persistence_type, True), payload,
                             f'the clear rewrote {name} in the OS credential store')
            # A save touches the signal file, so an unchanged mtime is the second, independent
            # witness that nothing was written through the persistence.
            self.assertEqual(os.stat(_path(name, file_extension_signal)).st_mtime_ns, mtime,
                             f'{name}{file_extension_signal} was touched, so the store was written')

    def test_account_clear_with_encryption_off_is_silent_without_a_signal_file(self):
        """No warning where encryption was never used: there is nothing left behind to warn about.

        The signal file is the only evidence, so a user who has always run with the setting off
        must not be told that credentials may remain in a store nothing ever wrote to.
        """
        # setUp leaves no persistence file and an empty credential store, so nothing here has ever
        # been written with encryption on.
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        self._login_all(plaintext_env)
        self._assert_only_plaintext_files_exist()

        cleared = _run_az(['account', 'clear'], env=plaintext_env)
        self.assertNotIn('OS credential store', _scrub(cleared.stderr),
                         'a store that was never written to was reported as holding credentials')
        self._assert_no_credentials_remain(encrypted=False)

    # -- encryption requested but unavailable (no D-Bus) ---------------------------------------

    def _assert_nothing_in_os_store(self):
        """The OS credential store holds nothing, so the fallback did not leak a payload into it."""
        for name, persistence_type in ((TOKEN_CACHE, TOKEN_CACHE_TYPE), (SECRET_STORE, SECRET_STORE_TYPE)):
            self.assertFalse(os.path.isfile(_path(name, _encrypted_extension())),
                             f'{name}{_encrypted_extension()} was created without a usable keyring')
            payload = self._stored_payload(name, persistence_type, True)
            if payload:
                self.assertFalse(json.loads(payload),
                                 f'{persistence_type} reached the OS credential store without D-Bus')

    def test_first_login_without_dbus_warns_and_records_the_reason(self):
        """A first sign-in with no keyring must warn, and say why under --debug.

        The warning is the user's only notice that the credentials went to disk in the clear, and
        the debug line is the only record of what libsecret failed with. The other fallback tests
        sign in on top of an existing plaintext store, so this is the clean slate case: nothing has
        been persisted yet, encryption is asked for, and the message has to come from this login.
        """
        if not sys.platform.startswith('linux'):
            self.skipTest('only libsecret can be made unreachable through the environment')

        fallback_env = self._case_env(encrypt=True, dbus_broken=True)
        _run_az(['account', 'clear'], env=fallback_env, check=False)
        _remove_persistence_files()

        signed_in = self._login(self.identities[0], fallback_env, extra_args=['--debug'])
        stderr = _scrub(signed_in.stderr)

        self.assertIn(ENCRYPTION_FALLBACK_WARNING, stderr,
                      'the first sign-in did not warn that credentials are stored in plaintext')
        self.assertIn('Failed to initialize LibsecretPersistence', stderr,
                      'the reason encryption was unavailable was not written to the debug log')

        # A user login only fills the token cache, so an application has to sign in as well before
        # both stores can be checked.
        self._login(self.identities[2], fallback_env)

        # The warning has to be true: nothing may have reached the OS credential store.
        self._assert_only_plaintext_files_exist()
        self._assert_nothing_in_os_store()

    def test_switching_encryption_on_without_dbus_keeps_using_plaintext(self):
        """With no keyring to encrypt into, turning the setting on changes nothing observable.

        LibsecretPersistence checks the keyring when it is constructed, so an unreachable D-Bus
        makes build_persistence fall back to the plaintext file before anything is read or written.
        The setting is on, but the store in use is the same file as with the setting off.

        This is the counterpart to the case where encryption is available: there, a token request
        made right after the flip and before any login must fail, because the encrypted store is
        empty. Here the same request must succeed, because the fallback keeps reading the file
        that already holds the credentials. Failing here would mean a machine without a keyring
        appears logged out the moment the setting is turned on.
        """
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        fallback_env = self._case_env(encrypt=True, dbus_broken=True)

        # Phase 1: encryption off. Only the plaintext persistence exists, and it works.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store(plaintext_env, 'the plaintext store did not serve a token')

        # Phase 2, before signing in again: the fallback keeps the phase 1 credentials in use.
        self._assert_token_from_store(
            fallback_env, 'turning encryption on without a keyring lost the existing credentials')
        self._assert_nothing_in_os_store()

        # Phase 2: signing in with the setting on writes to that same plaintext file, and says so.
        warned = self._login(self.identities[0], fallback_env)
        self.assertIn('plaintext', _scrub(warned.stderr).lower(),
                      'falling back to plaintext was not reported at sign-in')
        self._login_all(fallback_env)
        self._assert_all_credentials_present(fallback_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_nothing_in_os_store()
        self._assert_token_from_store(fallback_env, 'the fallback store did not serve a token')

        # One store, not two: a logout through the fallback is visible with the setting off, which
        # is the opposite of what happens when the keyring is available and the two stores diverge.
        target = self.identities[2]
        _run_az(['logout', '--username', target.login_name], env=fallback_env)
        self.assertNotIn(target.login_name,
                         self._stored_client_ids(
                             self._stored_payload(SECRET_STORE, SECRET_STORE_TYPE, False)),
                         'a logout through the fallback did not reach the plaintext secret store')

        # Phase 3: turning the setting back off changes nothing either, because nothing changed
        # when it was turned on.
        self.assertNotIn(target.login_name, self._logged_in_names(plaintext_env),
                         'turning encryption off brought back the logged out application')
        self._assert_token_from_store(plaintext_env, 'the plaintext store stopped serving tokens')
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_nothing_in_os_store()

    def test_account_clear_without_dbus_clears_the_fallback_store(self):
        """A clear with the setting on but no keyring must still clear what the fallback wrote.

        Nothing ever reaches the OS credential store in this flow, so the plaintext file is the
        whole of the persisted state and removing it is enough. The clear runs under the same
        broken-D-Bus environment that wrote the credentials, so it erases through the same
        fallback persistence.
        """
        plaintext_env = self._case_env(encrypt=False, dbus_broken=False)
        fallback_env = self._case_env(encrypt=True, dbus_broken=True)

        # Phase 1: encryption off, all four identities into the plaintext persistence.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store(plaintext_env, 'the plaintext store did not serve a token')

        # Phase 2: setting on, no keyring. The same four go back to the same file.
        self._login_all(fallback_env)
        self._assert_all_credentials_present(fallback_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_nothing_in_os_store()
        self._assert_token_from_store(fallback_env, 'the fallback store did not serve a token')

        # Phase 3: clear, under the setting that wrote the credentials. There is only one store to
        # empty, and afterwards neither setting can produce a token.
        _run_az(['account', 'clear'], env=fallback_env)
        self.assertFalse(self._logged_in_names(fallback_env),
                         'the profile still lists accounts after a clear')
        self.assertFalse(self._logged_in_names(plaintext_env),
                         'turning encryption off after a clear brought accounts back')
        self._assert_no_credentials_remain(encrypted=False)
        self._assert_nothing_in_os_store()
        self._assert_no_token_from_store(fallback_env, 'a credential outlived the clear')
        self._assert_no_token_from_store(
            plaintext_env, 'turning encryption off after a clear revived a credential')

        # Phase 4: turn the setting back off and sign in again. The clear left the store usable,
        # not merely empty.
        self._login_all(plaintext_env)
        self._assert_all_credentials_present(plaintext_env, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store(
            plaintext_env, 'the plaintext store was not usable again after the clear')

    def test_account_clear_without_dbus_does_not_advise_enabling_encryption(self):
        """The warning must fit the reason the store was skipped.

        With encryption on but no keyring, build_persistence falls back to plaintext, so the clear
        takes the same path as an opt out and the same payload is left behind. The advice cannot
        be the same: 'set core.encrypt_token_cache to true' is already done, and the thing to fix
        is the keyring. It repeats for as long as it is true, and stops once the store is empty.
        """
        self._skip_without_a_separate_os_store()
        if not sys.platform.startswith('linux'):
            self.skipTest('only libsecret can be made unreachable through the environment')

        encrypted_env = self._case_env(encrypt=True, dbus_broken=False)
        fallback_env = self._case_env(encrypt=True, dbus_broken=True)

        # A signal file from a working keyring, so there is something to warn about.
        self._login_all(encrypted_env)
        self._assert_all_credentials_present(encrypted_env, encrypted=True)

        cleared = _run_az(['account', 'clear'], env=fallback_env)
        stderr = _scrub(cleared.stderr)

        self.assertEqual(stderr.count('OS credential store'), 1,
                         f'expected exactly one credential store warning, got: {stderr[:500]}')
        self.assertNotIn('core.encrypt_token_cache', stderr,
                         'a fallback was told to turn on a setting that is already on')
        self.assertIn(CREDENTIAL_STORE_UNAVAILABLE_WARNING, stderr)

        # Clearing again, still without a keyring, must warn the same way: the payload is still
        # there and nothing about the machine has changed.
        repeated = _run_az(['account', 'clear'], env=fallback_env)
        repeated_stderr = _scrub(repeated.stderr)
        self.assertNotIn('Could not clear credentials', repeated_stderr,
                         'the second clear through the fallback reported a failure')
        self.assertNotIn('Traceback', repeated_stderr, 'the second clear through the fallback raised')
        self.assertEqual(repeated_stderr.count('OS credential store'), 1,
                         f'the second clear did not warn exactly once, got: {repeated_stderr[:500]}')
        self.assertIn(CREDENTIAL_STORE_UNAVAILABLE_WARNING, repeated_stderr)

        # The payload is still there, and a clear with a working keyring still removes it.
        self._assert_os_store_still_holds_the_identities(
            'the encrypted credentials were cleared through the fallback')
        _run_az(['account', 'clear'], env=encrypted_env)
        self._assert_no_credentials_remain(encrypted=True)
        self._assert_no_token_from_store(encrypted_env, 'a credential outlived the clear')

        # Taking the advice removed the signal files, so the fallback has nothing left to warn about.
        silent = _run_az(['account', 'clear'], env=fallback_env)
        self.assertNotIn('OS credential store', _scrub(silent.stderr),
                         'the fallback still warned after the credential store had been emptied')

    # -- the matrix --------------------------------------------------------------------------

    def test_multi_identity_lifecycle_encrypted(self):
        """Credentials in the OS credential store: the case the clear used to get wrong."""
        if not _encryption_available():
            self.skipTest('OS credential store unavailable, CLI falls back to plaintext')
        self._run_matrix_case(encrypt=True, dbus_broken=False)

    def test_multi_identity_lifecycle_plaintext(self):
        """core.encrypt_token_cache=false, so the payload is in the .json file."""
        self._run_matrix_case(encrypt=False, dbus_broken=False)

    def test_multi_identity_lifecycle_encryption_requested_but_unavailable(self):
        """Encryption asked for and refused: the CLI falls back, and the clear must follow it.

        This is the headless, container and Cloud Shell case. It is reached by pointing D-Bus at a
        socket that does not exist, which no amount of keyring configuration can rescue.
        """
        if not sys.platform.startswith('linux'):
            self.skipTest('only libsecret can be made unreachable through the environment')
        self._run_matrix_case(encrypt=True, dbus_broken=True)

    def test_multi_identity_lifecycle_plaintext_without_dbus(self):
        """Neither encryption requested nor available: nothing should even try the keyring."""
        if not sys.platform.startswith('linux'):
            self.skipTest('only libsecret can be made unreachable through the environment')
        self._run_matrix_case(encrypt=False, dbus_broken=True)

    def test_encryption_is_on_by_default(self):
        """With neither the environment override nor the config file set, credentials are encrypted.

        Every other test pins the setting, so should_encrypt_token_cache's fallback is the one
        thing they cannot see: turning the default back to plaintext would leave the whole suite
        green. This is the setting a user who has never touched the config runs with.
        """
        if not _encryption_available():
            self.skipTest('OS credential store unavailable, CLI falls back to plaintext')

        # The default only governs when neither the process local override nor the config is set.
        inherited = os.environ.pop('AZURE_CORE_ENCRYPT_TOKEN_CACHE', None)
        if inherited is not None:
            self.addCleanup(os.environ.__setitem__, 'AZURE_CORE_ENCRYPT_TOKEN_CACHE', inherited)
        _run_az(['config', 'unset', 'core.encrypt_token_cache'], check=False)
        _remove_persistence_files()

        self._login_all({})
        self._assert_all_credentials_present({}, encrypted=True)
        self._assert_token_from_store({}, 'the default store did not serve a token')

    def test_opt_out_of_encryption_through_the_config_file(self):
        """core.encrypt_token_cache=false has to work through the config file, not just the env.

        Every other test here sets AZURE_CORE_ENCRYPT_TOKEN_CACHE, which is process local and never
        touches the config file. The documented way to turn encryption off is written by one
        process and read by the next, so without this the config file half of the setting would be
        untested: the ini round trip, the section and option names, and the string to bool parse.
        """
        # The config file only governs when the process local override is absent.
        inherited = os.environ.pop('AZURE_CORE_ENCRYPT_TOKEN_CACHE', None)
        if inherited is not None:
            self.addCleanup(os.environ.__setitem__, 'AZURE_CORE_ENCRYPT_TOKEN_CACHE', inherited)

        _run_az(['config', 'set', 'core.encrypt_token_cache=false'])
        _remove_persistence_files()

        self._login_all({})
        self._assert_all_credentials_present({}, encrypted=False)
        self._assert_only_plaintext_files_exist()
        self._assert_token_from_store({}, 'the store selected by the config file did not serve a token')


if __name__ == '__main__':
    unittest.main()

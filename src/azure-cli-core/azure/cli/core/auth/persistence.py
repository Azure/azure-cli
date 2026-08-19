# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This file is modified from
# https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/dev/sample/token_cache_sample.py

import json
import sys

from msal_extensions import (FilePersistenceWithDataProtection, KeychainPersistence, LibsecretPersistence,
                             FilePersistence, PersistedTokenCache, CrossPlatLock)
from msal_extensions.persistence import PersistenceNotFound

from knack.log import get_logger
from azure.cli.core.decorators import retry


logger = get_logger(__name__)

# Files extensions for encrypted and plaintext persistence
file_extension_encrypted = '.bin'
file_extension_plaintext = '.json'
file_extension_signal = '.sig'
file_extensions = [file_extension_encrypted, file_extension_plaintext, file_extension_signal]

KEYCHAIN_SERVICE_NAME = 'Microsoft Azure CLI'
LIBSECRET_SCHEMA_NAME = 'Microsoft Azure CLI'

ENCRYPTION_FALLBACK_WARNING = (
    "Encryption is unavailable on this machine, so the token cache and service principal secrets "
    "are stored in plaintext. "
    "Please follow https://aka.ms/azure-cli-credential-encryption to enable encryption.")

# Set when a persistence falls back to plaintext, so sign-in can warn about it.
_encryption_fallback = False


def load_persisted_token_cache(location, encrypt):
    persistence = build_persistence(location, encrypt, type="Token cache")
    return PersistedTokenCache(persistence)


def load_secret_store(location, encrypt):
    persistence = build_persistence(location, encrypt, type="Secret store")
    return SecretStore(persistence)


def build_persistence(location, encrypt, type=None):
    """Build a suitable persistence instance based your current OS"""
    logger.debug("build_persistence: location=%r, encrypt=%r, type=%r", location, encrypt, type)
    if encrypt:
        if sys.platform.startswith('win'):
            # For FilePersistenceWithDataProtection, location is where the credential is stored.
            path = location + file_extension_encrypted
            logger.debug("Initializing FilePersistenceWithDataProtection: location=%r", path)
            return FilePersistenceWithDataProtection(path)
        if sys.platform.startswith('darwin'):
            # For KeychainPersistence, location is only used as a signal for the credential's last modified time.
            # The credential is stored in Keychain identified by (service_name, account_name) combination.
            # msal-extensions automatically computes account_name from signal_location.
            # https://github.com/AzureAD/microsoft-authentication-extensions-for-python/pull/103
            path = location + file_extension_signal
            logger.debug("Initializing KeychainPersistence: location=%r", path)
            return KeychainPersistence(path, service_name=KEYCHAIN_SERVICE_NAME, account_name=type)
        if sys.platform.startswith('linux'):
            # For LibsecretPersistence, location is only used as a signal for the credential's last modified time.
            # The credential is stored in libsecret identified by (schema_name, attributes) combination.
            # Doesn't seem to be a reason to use attributes to further filter the credential.
            path = location + file_extension_signal
            logger.debug("Initializing LibsecretPersistence: location=%r", path)
            try:
                attributes = {"type": type} if type else {}
                return LibsecretPersistence(
                    path,
                    schema_name=LIBSECRET_SCHEMA_NAME,
                    attributes=attributes
                )
            except Exception as e:
                # LibsecretPersistence is known to be unavailable in some Linux environments.
                # Fall back to FilePersistence. The user is warned at sign-in.
                logger.debug("Failed to initialize LibsecretPersistence: %s", e)
                _record_encryption_fallback()
    # Either encryption is opted out or the OS is not supported for encryption. Use FilePersistence.
    path = location + file_extension_plaintext
    logger.debug("Initializing FilePersistence: location=%r", path)
    return FilePersistence(path)


def _record_encryption_fallback():
    global _encryption_fallback  # pylint: disable=global-statement
    _encryption_fallback = True


def erase_persistence(location, encrypt, type=None, empty_payload='{}'):  # pylint: disable=redefined-builtin
    """Overwrite a persisted payload with empty content.

    Removing the files is not enough on Linux and macOS: the credential is held by libsecret or
    Keychain and the file is only a modification signal. Write through the same persistence that
    reads it, the way logging out of a single account does.
    """
    try:
        build_persistence(location, encrypt, type=type).save(empty_payload)
    except Exception as e:  # pylint: disable=broad-except
        # Best effort. The files are removed by the caller regardless.
        logger.debug("Failed to erase persisted payload at %r: %s", location, e)


def warn_if_encryption_unavailable():
    """Warn that credentials are persisted in plaintext.

    Called at sign-in only. Every command runs in a new process, so warning once per session would
    require storing state on the machine, and warning on every command is too noisy.
    """
    if _encryption_fallback:
        logger.warning(ENCRYPTION_FALLBACK_WARNING)


class SecretStore:
    def __init__(self, persistence):
        self._lock_file = persistence.get_location() + ".lockfile"
        self._persistence = persistence

    def save(self, content):
        with CrossPlatLock(self._lock_file):
            self._persistence.save(json.dumps(content, indent=4))

    @retry()
    def load(self):
        try:
            return json.loads(self._persistence.load())
        except PersistenceNotFound:
            return []

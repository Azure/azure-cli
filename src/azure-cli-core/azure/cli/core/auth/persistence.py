# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This file is modified from
# https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/dev/sample/token_cache_sample.py

import json
import os
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

# Credentials left in the OS credential store by an earlier encrypted run, which a clear cannot
# reach. Which one applies depends on why this run is not using the store.
CREDENTIAL_STORE_UNAVAILABLE_WARNING = (
    "Credentials may remain in the OS credential store, which is currently unavailable. "
    "Clear again once it works.")
CREDENTIAL_STORE_NOT_CLEARED_WARNING = (
    "Credentials may remain in the OS credential store. It is not cleared because encryption is "
    "off, and clearing it would prompt to unlock the keyring. Set 'core.encrypt_token_cache' to "
    "true and clear again to remove them.")

# Set when a persistence falls back to plaintext, so sign-in can warn about it.
_encryption_fallback = False


def load_persisted_token_cache(location, encrypt):
    persistence = build_persistence(location, encrypt, type="Token cache")
    return PersistedTokenCache(persistence)


def load_secret_store(location, encrypt):
    persistence = build_persistence(location, encrypt, type="Secret store")
    return SecretStore(persistence)


def build_persistence(location, encrypt, type=None):  # pylint: disable=redefined-builtin
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
                label = f"{LIBSECRET_SCHEMA_NAME} - {type}" if type else LIBSECRET_SCHEMA_NAME
                return LibsecretPersistence(
                    path,
                    schema_name=LIBSECRET_SCHEMA_NAME,
                    attributes=attributes,
                    label=label
                )
            except Exception as e:  # pylint: disable=broad-except
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


def _try_remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError as e:
        logger.debug("Failed to remove %r: %s", path, e)


def _remove_persistence_files(location, keep_signal_file=False):
    # Every extension, not just the one in use, to clean up after a changed encrypt_token_cache.
    for extension in file_extensions:
        if keep_signal_file and extension == file_extension_signal:
            continue
        _try_remove(location + extension)


def _warn_about_the_os_credential_store(location):
    # A signal file means this location was written with encryption on, so the OS credential store
    # may still hold a payload. Emptying it here may prompt to unlock the keyring, which is the
    # interruption encrypt_token_cache=false opted out of, so leave the payload alone and say so.
    if not os.path.exists(location + file_extension_signal):
        return
    if _encryption_fallback:
        # Encryption is already on, so there is nothing to turn on. The keyring is what's broken.
        logger.warning(CREDENTIAL_STORE_UNAVAILABLE_WARNING)
    else:
        logger.warning(CREDENTIAL_STORE_NOT_CLEARED_WARNING)


def erase_persistence(location, encrypt, type=None, empty_payload='{}',  # pylint: disable=redefined-builtin
                      warn_if_credentials_may_remain=False):
    """Empty a persisted payload and remove its files. Returns whether it succeeded.

    With encryption on, the payload is held by libsecret or Keychain and the file is only a
    modification signal, so it is overwritten rather than deleted. With encryption off the
    credential store is not touched at all, so clearing never prompts to unlock a keyring the user
    opted out of, and the signal file is kept as the evidence that it may still hold a payload.

    :param warn_if_credentials_may_remain: Warn about what the credential store may still hold.
        Only one location should, because the warning is about the store, not the location.
    """
    try:
        persistence = build_persistence(location, encrypt, type=type)
        # Serialize against other az processes, like SecretStore.save and PersistedTokenCache do.
        with CrossPlatLock(persistence.get_location() + '.lockfile'):
            if persistence.is_encrypted:
                persistence.save(empty_payload)
            elif warn_if_credentials_may_remain:
                _warn_about_the_os_credential_store(location)
            _remove_persistence_files(location, keep_signal_file=not persistence.is_encrypted)
        return True
    except Exception as e:  # pylint: disable=broad-except
        # Clearing must not fail, but nothing was removed and the credential is still readable, so
        # this can't be silent. In practice another az process is holding the lock.
        logger.debug("Failed to erase persisted payload at %r: %s", location, e)
        logger.warning("Could not clear credentials. Run 'az account clear' again.")
        return False


def warn_if_encryption_unavailable():
    if not _encryption_fallback:
        return

    # Nothing can be installed on a platform-managed machine, so the advice would only be noise.
    from azure.cli.core.util import in_managed_environment
    if in_managed_environment():
        logger.debug("Encryption is unavailable, but the warning is suppressed in a managed environment.")
        return

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

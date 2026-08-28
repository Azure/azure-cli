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
                return LibsecretPersistence(
                    path,
                    schema_name=LIBSECRET_SCHEMA_NAME,
                    attributes=attributes
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


def _remove_persistence_files(location):
    """Remove every persistence file for a location.

    All extensions are tried, not just the one in use, so that a plaintext or DPAPI file left
    over from a previous core.encrypt_token_cache setting is cleaned up too.
    """
    for extension in file_extensions:
        _try_remove(location + extension)


def _try_erase_os_credential_store(location, type=None, empty_payload='{}'):  # pylint: disable=redefined-builtin
    """Best effort erase of a payload the OS credential store may still hold.

    On macOS and Linux the credential lives in Keychain or libsecret and the file is only a
    modification signal, so removing the file hides the payload instead of removing it: a clear run
    with core.encrypt_token_cache off would leave the credential readable as soon as the setting is
    turned back on. Windows needs nothing here, because the DPAPI file is the ciphertext itself.

    The persistence API has no delete, and macOS Keychain offers none at all, so an empty payload is
    written over it instead. Like _try_remove, a failure must not stop the clear: an unreachable
    credential store cannot be cleared by any means, so there is nothing to do but record it.
    """
    if not (sys.platform.startswith('darwin') or sys.platform.startswith('linux')):
        return
    try:
        persistence = build_persistence(location, True, type=type)
        if not persistence.is_encrypted:
            # Fell back to plaintext, so the OS credential store is unreachable from here. The
            # plaintext file is the caller's business and is dealt with there.
            return
        with CrossPlatLock(persistence.get_location() + '.lockfile'):
            persistence.save(empty_payload)
    except Exception as e:  # pylint: disable=broad-except
        logger.debug("Failed to erase the OS credential store at %r: %s", location, e)


def erase_persistence(location, encrypt, type=None, empty_payload='{}'):  # pylint: disable=redefined-builtin
    """Empty a persisted payload and remove its files. Returns whether it succeeded.

    Removing the files is not enough on Linux and macOS: the credential is held by libsecret or
    Keychain and the file is only a modification signal. Write through the same persistence that
    reads it, the way logging out of a single account does.

    The OS credential store is erased too when it is not the configured one, so that a payload
    written under a previous core.encrypt_token_cache setting does not outlive the clear.

    Emptying and removing happen under one lock, and nothing is touched unless the lock is held.
    In practice this only fails when another az process is using the credential store, and
    deleting its freshly written signal file would hide a credential rather than remove it.
    """
    try:
        persistence = build_persistence(location, encrypt, type=type)
        if not persistence.is_encrypted:
            _try_erase_os_credential_store(location, type=type, empty_payload=empty_payload)
        # Serialize against other az processes, like SecretStore.save and PersistedTokenCache do.
        with CrossPlatLock(persistence.get_location() + '.lockfile'):
            persistence.save(empty_payload)
            _remove_persistence_files(location)
        return True
    except Exception as e:  # pylint: disable=broad-except
        # Logging out must not fail, but nothing was cleared and the credential is still readable,
        # so this can't be silent. Details go to the debug log.
        logger.debug("Failed to erase persisted payload at %r: %s", location, e)
        logger.warning("Could not clear credentials. Run 'az account clear' again.")
        return False


def warn_if_encryption_unavailable():
    if not _encryption_fallback:
        return

    # The warning asks the user to make the OS credential store available, which can't be done on a
    # platform-managed machine, so it would only be noise there.
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

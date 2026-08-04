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

KEYCHAIN_SERVICE_NAME = 'Microsoft Azure CLI MSAL Token Cache'
LIBSECRET_SCHEMA_NAME = 'Microsoft Azure CLI MSAL Token Cache'

def load_persisted_token_cache(location, encrypt):
    persistence = build_persistence(location, encrypt)
    return PersistedTokenCache(persistence)


def load_secret_store(location, encrypt):
    persistence = build_persistence(location, encrypt)
    return SecretStore(persistence)


def build_persistence(location, encrypt):
    """Build a suitable persistence instance based your current OS"""
    logger.debug("build_persistence: location=%r, encrypt=%r", location, encrypt)
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
            return KeychainPersistence(path, service_name=KEYCHAIN_SERVICE_NAME)
        if sys.platform.startswith('linux'):
            # For LibsecretPersistence, location is only used as a signal for the credential's last modified time.
            # The credential is stored in libsecret identified by (schema_name, attributes) combination.
            # Doesn't seem to be a reason to use attributes to further filter the credential.
            path = location + file_extension_signal
            logger.debug("Initializing LibsecretPersistence: location=%r", path)
            try:
                return LibsecretPersistence(
                    path,
                    schema_name=LIBSECRET_SCHEMA_NAME,
                    attributes={}
                )
            except Exception as e:
                # Warn the user and continue with FilePersistence.
                # LibsecretPersistence are known to be unavailable in some Linux environments.
                logger.debug("Failed to initialize LibsecretPersistence: %s", e)
                logger.warning("TBD: Encryption is unavailable. Falling back to plaintext persistence."
                "Please follow https://aka.ms/azure-cli-credential-encryption to enable encryption.")
    # Either encryption is opted out or the OS is not supported for encryption. Use FilePersistence.
    path = location + file_extension_plaintext
    logger.debug("Initializing FilePersistence: location=%r", path)
    return FilePersistence(path)


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

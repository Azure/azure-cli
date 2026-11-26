# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This file is modified from
# https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/dev/sample/token_cache_sample.py

import json
import sys
import time

from msal_extensions import (FilePersistenceWithDataProtection, KeychainPersistence, LibsecretPersistence,
                             FilePersistence, PersistedTokenCache, CrossPlatLock)
from msal_extensions.persistence import PersistenceNotFound

from knack.log import get_logger
from azure.cli.core.decorators import retry


logger = get_logger(__name__)

# Files extensions for encrypted and plaintext persistence
file_extensions = {True: '.bin', False: '.json'}


class AzureCliTokenCache(PersistedTokenCache):
    """A token cache that gracefully handles corrupted token cache files.

    When the token cache file contains invalid JSON (e.g., due to incomplete or concurrent writes),
    the cache is reset to a fresh empty state instead of raising an exception.
    """

    def _reload_if_necessary(self):
        try:
            super()._reload_if_necessary()
        except json.JSONDecodeError as ex:
            # The token cache file may be corrupted due to incomplete or concurrent writes.
            # Reset the in-memory cache to empty so that the current operation can continue.
            # The subsequent modify() call will persist this empty cache, overwriting the
            # corrupted file on disk.
            logger.warning("Failed to deserialize token cache '%s': %s. "
                           "The in-memory cache will be reset to empty.",
                           self._persistence.get_location(), ex)
            self.deserialize(None)
            # Update the sync marker so we don't keep retrying to reload the same
            # corrupted file on every subsequent call until it's overwritten.
            self._last_sync = time.time()


def load_persisted_token_cache(location, encrypt):
    persistence = build_persistence(location, encrypt)
    return AzureCliTokenCache(persistence)


def load_secret_store(location, encrypt):
    persistence = build_persistence(location, encrypt)
    return SecretStore(persistence)


def build_persistence(location, encrypt):
    """Build a suitable persistence instance based your current OS"""
    location += file_extensions[encrypt]
    logger.debug("build_persistence: location=%r, encrypt=%r", location, encrypt)
    if encrypt:
        if sys.platform.startswith('win'):
            return FilePersistenceWithDataProtection(location)
        if sys.platform.startswith('darwin'):
            return KeychainPersistence(location, "my_service_name", "my_account_name")
        if sys.platform.startswith('linux'):
            return LibsecretPersistence(
                location,
                schema_name="my_schema_name",
                attributes={"my_attr1": "foo", "my_attr2": "bar"}
            )
    else:
        return FilePersistence(location)


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
        except json.JSONDecodeError as ex:
            logger.warning("Failed to deserialize service principal entries '%s': %s. "
                           "The entries will be treated as empty.", self._persistence.get_location(), ex)
            return []

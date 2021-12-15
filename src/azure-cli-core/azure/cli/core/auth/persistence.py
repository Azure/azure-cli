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

logger = get_logger(__name__)

# Files extensions for encrypted and plaintext persistence
file_extensions = {True: '.bin', False: '.json'}


def load_persisted_token_cache(location, encrypt):
    persistence = build_persistence(location, encrypt)
    return PersistedTokenCache(persistence)


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

    def _load(self):
        try:
            return json.loads(self._persistence.load())
        except PersistenceNotFound:
            return []

    def load(self):
        # Use optimistic locking rather than CrossPlatLock, so that multiple processes can
        # read the same file at the same time.
        retry = 3
        for attempt in range(1, retry + 1):
            try:
                return self._load()
            except Exception:  # pylint: disable=broad-except
                # Presumably other processes are writing the file, causing dirty read
                if attempt < retry:
                    logger.debug("Unable to load secret store in No. %d attempt", attempt)
                    import traceback
                    logger.debug(traceback.format_exc())
                    time.sleep(0.5)
                else:
                    raise  # End of retry. Re-raise the exception as-is.

        return []  # Not really reachable here. Just to keep pylint happy.

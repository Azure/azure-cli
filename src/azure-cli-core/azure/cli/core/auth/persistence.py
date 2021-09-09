# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This file is modified from
# https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/dev/sample/token_cache_sample.py

import json
import logging
import sys

from msal_extensions import (FilePersistenceWithDataProtection, KeychainPersistence, LibsecretPersistence,
                             FilePersistence, PersistedTokenCache, CrossPlatLock)
from msal_extensions.persistence import PersistenceNotFound

from knack.util import CLIError


def load_persisted_token_cache(location, fallback_to_plaintext):
    persistence = build_persistence(location, fallback_to_plaintext)
    return PersistedTokenCache(persistence)


def load_secret_store(location, fallback_to_plaintext):
    persistence = build_persistence(location, fallback_to_plaintext)
    return SecretStore(persistence)


def build_persistence(location, fallback_to_plaintext=False):
    """Build a suitable persistence instance based your current OS"""
    if sys.platform.startswith('win'):
        return FilePersistenceWithDataProtection(location)
    if sys.platform.startswith('darwin'):
        return KeychainPersistence(location, "my_service_name", "my_account_name")
    if sys.platform.startswith('linux'):
        try:
            return LibsecretPersistence(
                # By using same location as the fall back option below,
                # this would override the unencrypted data stored by the
                # fall back option.  It is probably OK, or even desirable
                # (in order to aggressively wipe out plain-text persisted data),
                # unless there would frequently be a desktop session and
                # a remote ssh session being active simultaneously.
                location,
                schema_name="my_schema_name",
                attributes={"my_attr1": "foo", "my_attr2": "bar"}
            )
        except:  # pylint: disable=bare-except
            if not fallback_to_plaintext:
                raise
            logging.exception("Encryption unavailable. Opting in to plain text.")
    return FilePersistence(location)


class SecretStore:
    def __init__(self, persistence):
        self._lock_file = persistence.get_location() + ".lockfile"
        self._persistence = persistence

    def save(self, content):
        with CrossPlatLock(self._lock_file):
            self._persistence.save(json.dumps(content))

    def load(self):
        with CrossPlatLock(self._lock_file):
            try:
                return json.loads(self._persistence.load())
            except PersistenceNotFound:
                return []
            except Exception as ex:
                raise CLIError("Failed to load token files. If you can reproduce, please log an issue at "
                               "https://github.com/Azure/azure-cli/issues. At the same time, you can clean "
                               "up by running 'az account clear' and then 'az login'. (Inner Error: {})".format(ex))

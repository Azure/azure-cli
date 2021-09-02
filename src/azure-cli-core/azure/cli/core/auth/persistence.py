# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This file is modified from
# https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/dev/sample/token_cache_sample.py

import logging
import sys

from msal_extensions import (FilePersistenceWithDataProtection, KeychainPersistence, LibsecretPersistence,
                             FilePersistence, PersistedTokenCache)


def load_persisted_token_cache(location, fallback_to_plaintext):
    persistence = build_persistence(location, fallback_to_plaintext)
    return PersistedTokenCache(persistence)


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
                attributes={"my_attr1": "foo", "my_attr2": "bar"},
                )
        except:  # pylint: disable=bare-except
            if not fallback_to_plaintext:
                raise
            logging.exception("Encryption unavailable. Opting in to plain text.")
    return FilePersistence(location)

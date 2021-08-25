# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This file is modified from
# https://github.com/AzureAD/microsoft-authentication-extensions-for-python/blob/dev/sample/token_cache_sample.py

import os
import sys


def load_persisted_token_cache(location, fallback_to_plaintext):
    import msal_extensions

    persistence = _get_persistence(location, fallback_to_plaintext, account_name="MSALCache")
    return msal_extensions.PersistedTokenCache(persistence)


def _get_persistence(location, fallback_to_plaintext, account_name):
    import msal_extensions

    if sys.platform.startswith("win") and "LOCALAPPDATA" in os.environ:
        return msal_extensions.FilePersistenceWithDataProtection(location)

    if sys.platform.startswith("darwin"):
        # the cache uses this file's modified timestamp to decide whether to reload
        return msal_extensions.KeychainPersistence(location, "Microsoft.Developer.IdentityService", account_name)

    if sys.platform.startswith("linux"):
        # The cache uses this file's modified timestamp to decide whether to reload. Note this path is the same
        # as that of the plaintext fallback: a new encrypted cache will stomp an unencrypted cache.
        file_path = os.path.expanduser(os.path.join("~", ".IdentityService", location))
        try:
            return msal_extensions.LibsecretPersistence(
                file_path, location, {"MsalClientID": "Microsoft.Developer.IdentityService"}, label=account_name
            )
        except ImportError:
            if not fallback_to_plaintext:
                raise ValueError(
                    "PyGObject is required to encrypt the persistent cache. Please install that library or "
                    + 'specify "allow_unencrypted_cache=True" to store the cache without encryption.'
                )
            return msal_extensions.FilePersistence(file_path)

    raise NotImplementedError("A persistent cache is not available in this environment.")

#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Assert that a sign-in with a working keyring encrypted the cache and stayed quiet.

The mirror image of check_encryption_warning.py. A warning that cannot be switched off is as much
a bug as one that never appears: users learn to ignore it, and it stops meaning anything.
"""

import json
import os
import sys

from azure.cli.core._environment import get_config_dir
from azure.cli.core.auth.persistence import (ENCRYPTION_FALLBACK_WARNING, build_persistence,
                                             file_extension_plaintext, file_extension_signal)

TOKEN_CACHE = 'msal_token_cache'


def check_libsecret_holds_the_cache(failures):
    """The signal file is empty by design, so read back what libsecret actually stored.

    Built through build_persistence so the schema and attributes come from the code under test
    rather than being restated here, where they could drift.
    """
    location = os.path.join(get_config_dir(), TOKEN_CACHE)
    persistence = build_persistence(location, True, type='Token cache')
    if type(persistence).__name__ != 'LibsecretPersistence':
        failures.append(f'encryption resolved to {type(persistence).__name__}, not libsecret')
        return
    try:
        payload = persistence.load()
    except Exception as e:  # pylint: disable=broad-except
        failures.append(f'the credential could not be read back from libsecret: {e}')
        return
    try:
        cache = json.loads(payload) if payload else {}
    except ValueError:
        failures.append('what libsecret returned is not a token cache')
        return
    # A client-credential flow issues no refresh token, so an access token is all there is to find.
    if not cache.get('AccessToken'):
        failures.append('libsecret holds no access token, so nothing was encrypted')


def main(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        stderr = f.read()

    failures = []
    if ENCRYPTION_FALLBACK_WARNING in stderr:
        failures.append('the sign-in warned about plaintext even though the keyring worked')
    if 'Failed to initialize LibsecretPersistence' in stderr:
        failures.append('libsecret was installed and unlocked but still failed to initialize')

    signal = os.path.join(get_config_dir(), TOKEN_CACHE + file_extension_signal)
    plaintext = os.path.join(get_config_dir(), TOKEN_CACHE + file_extension_plaintext)
    if not os.path.isfile(signal):
        failures.append(f'{TOKEN_CACHE}{file_extension_signal} was not written')
    if os.path.isfile(plaintext):
        failures.append(f'{TOKEN_CACHE}{file_extension_plaintext} was written despite encryption')

    check_libsecret_holds_the_cache(failures)

    for failure in failures:
        print(f'::error::{failure}')
    if failures:
        print('--- lines seen ---')
        for line in stderr.splitlines():
            if 'plaintext' in line.lower() or 'Libsecret' in line or 'Persistence' in line:
                print(line)
        return 1

    print('the keyring encrypted the cache and the sign-in said nothing about plaintext')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Assert what a sign-in with no keyring told the user about plaintext storage.

Takes the scrubbed stderr of 'az login --debug' and whether the warning is expected.

On a CI agent the warning is deliberately suppressed: it asks the user to make an OS credential
store available, which cannot be done on a platform-managed machine. The fallback itself must still
happen and must still be explained in the debug log, so 'absent' checks that only the warning went
away and nothing else did.
"""

import os
import sys

from azure.cli.core._environment import get_config_dir
from azure.cli.core.auth.persistence import (ENCRYPTION_FALLBACK_WARNING, file_extension_plaintext,
                                             file_extension_signal)

TOKEN_CACHE = 'msal_token_cache'
SECRET_STORE = 'service_principal_entries'


def main(path, warning):
    if warning not in ('present', 'absent'):
        raise SystemExit(f"expected 'present' or 'absent', got {warning!r}")

    with open(path, encoding='utf-8', errors='replace') as f:
        stderr = f.read()

    failures = []
    warned = ENCRYPTION_FALLBACK_WARNING in stderr
    if warning == 'present' and not warned:
        failures.append('the sign-in did not warn that credentials are stored in plaintext')
    if warning == 'absent' and warned:
        failures.append('the sign-in warned about plaintext storage on a platform-managed machine, '
                        'where the user cannot act on it')
    if 'Failed to initialize LibsecretPersistence' not in stderr:
        failures.append('the reason encryption was unavailable never reached the debug log')

    # The warning has to be true: the payload must be in the plaintext file and nowhere else.
    for name in (TOKEN_CACHE, SECRET_STORE):
        plaintext = os.path.join(get_config_dir(), name + file_extension_plaintext)
        signal = os.path.join(get_config_dir(), name + file_extension_signal)
        if name == TOKEN_CACHE and not os.path.isfile(plaintext):
            failures.append(f'{name}{file_extension_plaintext} was not written')
        if os.path.isfile(signal):
            failures.append(f'{name}{file_extension_signal} was written without a usable keyring')

    for failure in failures:
        print(f'::error::{failure}')
    if failures:
        print('--- warning lines seen ---')
        for line in stderr.splitlines():
            if 'plaintext' in line.lower() or 'Libsecret' in line:
                print(line)
        return 1

    told = 'warned about plaintext storage' if warning == 'present' else 'stayed quiet'
    print(f'the sign-in {told} and logged why encryption was unavailable')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))

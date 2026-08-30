#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Assert that encryption was asked for, refused, and recorded.

Run on a machine with no usable keyring. build_persistence has to hand back a plaintext
FilePersistence, note the fallback for the sign-in warning, and say in the debug log why libsecret
could not be used. Losing any one of the three leaves a user storing credentials in the clear with
nothing to tell them so.
"""

import logging
import sys
import tempfile

from azure.cli.core.auth import persistence


def main():
    debug = []
    logging.getLogger().setLevel(logging.DEBUG)
    handler = logging.Handler()
    handler.emit = lambda record: debug.append(record.getMessage())
    persistence.logger.addHandler(handler)
    persistence.logger.setLevel(logging.DEBUG)

    persistence._encryption_fallback = False  # pylint: disable=protected-access
    with tempfile.TemporaryDirectory() as directory:
        store = persistence.build_persistence(directory + '/probe', True, type='Token cache')

    failures = []
    if store.is_encrypted:
        failures.append('the persistence reports itself as encrypted, so there was no fallback '
                        'to observe on this runner')
    if not isinstance(store, persistence.FilePersistence):
        failures.append(f'expected a plaintext FilePersistence, got {type(store).__name__}')
    if not persistence._encryption_fallback:  # pylint: disable=protected-access
        failures.append('the fallback was not recorded, so sign-in would not warn about it')
    if not any('Failed to initialize LibsecretPersistence' in message for message in debug):
        failures.append('the reason libsecret was unusable never reached the debug log')

    for failure in failures:
        print(f'::error::{failure}')
    if failures:
        return 1

    print('encryption requested, refused, recorded, and explained in the debug log')
    return 0


if __name__ == '__main__':
    sys.exit(main())

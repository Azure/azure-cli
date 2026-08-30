#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Assert the plaintext fallback warning is suppressed on a real platform-managed host.

Meant to be run on an Azure Pipelines agent, a GitHub Actions runner or in Cloud Shell, and needs no
sign-in: the warning is decided by build_persistence and warn_if_encryption_unavailable alone.

The unit tests mock the environment, so they cannot show that a real host sets TF_BUILD,
GITHUB_ACTIONS or ACC_CLOUD. This runs the same code against whatever the host actually provides,
then repeats it with those variables removed, so a pass means the gate is what silenced the warning
and not a fallback that never happened.
"""

import logging
import os
import sys
import tempfile

from azure.cli.core.auth import persistence
from azure.cli.core.util import in_ci, in_cloud_console, in_managed_environment

# Every variable in_managed_environment() consults, so the control below can take them all away.
MANAGED_VARIABLES = ('TF_BUILD', 'GITHUB_ACTIONS', 'CI', 'ACC_CLOUD')


def _collect(level):
    """Capture messages the persistence logger emits at one level."""
    messages = []
    handler = logging.Handler()
    handler.emit = lambda record: messages.append(record.getMessage())
    handler.setLevel(level)
    return messages, handler


def _fall_back():
    """Ask for encryption on a machine with no usable keyring, and return the debug log."""
    debug, handler = _collect(logging.DEBUG)
    persistence.logger.addHandler(handler)
    persistence.logger.setLevel(logging.DEBUG)
    try:
        persistence._encryption_fallback = False  # pylint: disable=protected-access
        with tempfile.TemporaryDirectory() as directory:
            store = persistence.build_persistence(directory + '/probe', True, type='Token cache')
    finally:
        persistence.logger.removeHandler(handler)
    return store, debug


def _warnings_from_sign_in():
    warnings, handler = _collect(logging.WARNING)
    persistence.logger.addHandler(handler)
    try:
        persistence.warn_if_encryption_unavailable()
    finally:
        persistence.logger.removeHandler(handler)
    return [message for message in warnings if message == persistence.ENCRYPTION_FALLBACK_WARNING]


def main():
    seen = {name: os.environ.get(name) for name in MANAGED_VARIABLES}
    print('host environment: ' + ', '.join(
        f'{name}={value!r}' if value is not None else f'{name}=<unset>' for name, value in seen.items()))
    print(f'in_ci()={in_ci()}, in_cloud_console()={bool(in_cloud_console())}, '
          f'in_managed_environment()={in_managed_environment()}')

    failures = []
    if not in_managed_environment():
        failures.append('this host sets none of the variables in_managed_environment() looks for, '
                        'so the gate this checks would never apply here')

    # The fallback itself has to happen, or there would be no warning to suppress and a pass would
    # mean nothing.
    store, debug = _fall_back()
    if store.is_encrypted:
        failures.append('the persistence reports itself as encrypted, so there was no fallback to '
                        'observe on this host')
    if not isinstance(store, persistence.FilePersistence):
        failures.append(f'expected a plaintext FilePersistence, got {type(store).__name__}')
    if not persistence._encryption_fallback:  # pylint: disable=protected-access
        failures.append('the fallback was not recorded')
    if not any('Failed to initialize LibsecretPersistence' in message for message in debug):
        failures.append('the reason libsecret was unusable never reached the debug log')

    if _warnings_from_sign_in():
        failures.append('sign-in warned about plaintext storage on a platform-managed host, where '
                        'the user cannot act on it')

    # Same process, same fallback, with only those variables taken away. Without this a silent
    # warning path would pass just as happily as a working gate.
    removed = {name: os.environ.pop(name) for name in MANAGED_VARIABLES if name in os.environ}
    try:
        if not _warnings_from_sign_in():
            failures.append(f'with {", ".join(removed)} removed the sign-in still said nothing, so '
                            'the silence above was not the gate')
    finally:
        os.environ.update(removed)

    for failure in failures:
        print(f'##vso[task.logissue type=error]{failure}')
    if failures:
        return 1

    print('the fallback happened, was explained in the debug log, and the warning was suppressed '
          'only because this is a platform-managed host')
    return 0


if __name__ == '__main__':
    sys.exit(main())

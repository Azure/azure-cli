#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Store and read back a throwaway secret, to prove the keyring works before az is blamed for it.

Setting up an unlocked keyring on a headless runner is the fragile part of this job. Checking it
directly keeps a broken fixture from being reported as a broken CLI.
"""

import sys

import gi

gi.require_version('Secret', '1')
from gi.repository import Secret  # noqa: E402 pylint: disable=wrong-import-position

SCHEMA_NAME = 'azure.cli.ci.keyring.probe'
ATTRIBUTES = {'purpose': 'ci-probe'}
VALUE = 'round-trip-canary'


def main():
    schema = Secret.Schema.new(SCHEMA_NAME, Secret.SchemaFlags.NONE,
                               {'purpose': Secret.SchemaAttributeType.STRING})
    Secret.password_store_sync(schema, ATTRIBUTES, Secret.COLLECTION_DEFAULT,
                               'azure-cli CI keyring probe', VALUE, None)
    got = Secret.password_lookup_sync(schema, ATTRIBUTES, None)
    Secret.password_clear_sync(schema, ATTRIBUTES, None)

    if got != VALUE:
        print(f'::error::the keyring did not return what was stored: {got!r}')
        return 1
    print('the keyring stores and returns a secret')
    return 0


if __name__ == '__main__':
    sys.exit(main())

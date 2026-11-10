# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace

from azure.cli.core.aaz import AAZUndefined
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.search.custom import _raise_if_service_level_encryption_key_set


class ServiceLevelEncryptionKeyTest(unittest.TestCase):
    """No HTTP request is made, so these tests need no recording or api-version."""

    def test_raises_when_key_is_set(self):
        args = SimpleNamespace(
            encryption_with_cmk=SimpleNamespace(service_level_encryption_key={"keyVaultUri": "https://a"}))
        with self.assertRaises(InvalidArgumentValueError) as ctx:
            _raise_if_service_level_encryption_key_set(args)
        self.assertIn("service-level-encryption-key", str(ctx.exception))

    def test_allows_other_cmk_settings(self):
        args = SimpleNamespace(
            encryption_with_cmk=SimpleNamespace(service_level_encryption_key=AAZUndefined, enforcement="Enabled"))
        _raise_if_service_level_encryption_key_set(args)

    def test_allows_cmk_not_set(self):
        _raise_if_service_level_encryption_key_set(SimpleNamespace(encryption_with_cmk=AAZUndefined))


if __name__ == '__main__':
    unittest.main()

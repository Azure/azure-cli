#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

# pylint: disable=line-too-long
from azure.cli.command_modules.resource._validators import (validate_resource_type,
                                                            validate_parent,
                                                            _resolve_api_version as resolve_api_version)

class TestApiCheck(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_resolve_api_provider_backup(self):
        """ Verifies provider is used as backup if api-version not specified. """
        resource_type = validate_resource_type('Mock/test')
        self.assertEqual(resolve_api_version(self._get_mock_client(), resource_type), "2016-01-01")

    def test_resolve_api_provider_with_parent_backup(self):
        """ Verifies provider (with parent) is used as backup if api-version not specified. """
        resource_type = validate_resource_type('Mock/bar')
        parent = validate_parent('foo/testfoo123')
        self.assertEqual(
            resolve_api_version(self._get_mock_client(), resource_type, parent),
            "1999-01-01"
        )

    def test_resolve_api_all_previews(self):
        """ Verifies most recent preview version returned only if there are no non-preview versions. """
        resource_type = validate_resource_type('Mock/preview')
        self.assertEqual(
            resolve_api_version(self._get_mock_client(), resource_type),
            "2005-01-01-preview"
        )

    def _get_mock_client(self):
        client = MagicMock()
        provider = MagicMock()
        provider.resource_types = [
            self._get_mock_resource_type('skip', ['2000-01-01-preview', '2000-01-01']),
            self._get_mock_resource_type('test', ['2016-01-01-preview', '2016-01-01']),
            self._get_mock_resource_type('foo/bar', ['1999-01-01-preview', '1999-01-01']),
            self._get_mock_resource_type('preview', ['2005-01-01-preview', '2004-01-01-preview'])
        ]
        client.providers.get.return_value = provider
        return client

    def _get_mock_resource_type(self, name, api_versions): #pylint: disable=no-self-use
        rt = MagicMock()
        rt.resource_type = name
        rt.api_versions = api_versions
        return rt

if __name__ == '__main__':
    unittest.main()

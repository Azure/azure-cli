# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock

from knack.util import CLIError
from azure.cli.command_modules.resource.custom import (_ResourceUtils, _validate_resource_inputs,
                                                       parse_resource_id)


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

    def test_parse_resource(self):
        parts = parse_resource_id('/subscriptions/00000/resourcegroups/bocconitestlabrg138089/'
                                  'providers/microsoft.devtestlab/labs/bocconitestlab/'
                                  'virtualmachines/tasktest1')
        self.assertIsNotNone(parts.get('type'))

    def test_parse_resource_capital(self):
        parts = parse_resource_id('/subscriptions/00000/resourceGroups/bocconitestlabrg138089/'
                                  'providers/microsoft.devtestlab/labs/bocconitestlab/'
                                  'virtualmachines/tasktest1')
        self.assertIsNotNone(parts.get('type'))

    def test_validate_resource_inputs(self):
        self.assertRaises(CLIError, _validate_resource_inputs, None, None, None, None)
        self.assertRaises(CLIError, _validate_resource_inputs, 'a', None, None, None)
        self.assertRaises(CLIError, _validate_resource_inputs, 'a', 'b', None, None)
        self.assertRaises(CLIError, _validate_resource_inputs, 'a', 'b', 'c', None)
        _validate_resource_inputs('a', 'b', 'c', 'd')

    def test_resolve_api_provider_backup(self):
        # Verifies provider is used as backup if api-version not specified.
        from azure.cli.core.mock import DummyCli
        cli = DummyCli()
        rcf = self._get_mock_client()
        res_utils = _ResourceUtils(cli, resource_type='Mock/test', resource_name='vnet1',
                                   resource_group_name='rg', rcf=rcf)
        self.assertEqual(res_utils.api_version, "2016-01-01")

    def test_resolve_api_provider_with_parent_backup(self):
        # Verifies provider (with parent) is used as backup if api-version not specified.
        from azure.cli.core.mock import DummyCli
        cli = DummyCli()
        rcf = self._get_mock_client()
        res_utils = _ResourceUtils(cli, parent_resource_path='foo/testfoo123', resource_group_name='rg',
                                   resource_provider_namespace='Mock', resource_type='test',
                                   resource_name='vnet1',
                                   rcf=rcf)
        self.assertEqual(res_utils.api_version, "1999-01-01")

    def test_resolve_api_all_previews(self):
        # Verifies most recent preview version returned only if there are no non-preview versions.
        from azure.cli.core.mock import DummyCli
        cli = DummyCli()
        rcf = self._get_mock_client()
        res_utils = _ResourceUtils(cli, resource_type='Mock/preview', resource_name='vnet1',
                                   resource_group_name='rg', rcf=rcf)
        self.assertEqual(res_utils.api_version, "2005-01-01-preview")

    def test_resolve_api_provider_latest_include_preview(self):
        # Verifies provider is used as backup if api-version not specified.
        from azure.cli.core.mock import DummyCli
        cli = DummyCli()
        rcf = self._get_mock_client()
        res_utils = _ResourceUtils(cli, resource_type='Mock/test_latest', resource_name='vnet1',
                                   resource_group_name='rg', rcf=rcf)
        self.assertEqual(res_utils.api_version, "2015-01-01")

        res_utils = _ResourceUtils(cli, resource_type='Mock/test_latest', resource_name='vnet1',
                                   resource_group_name='rg', rcf=rcf, latest_include_preview=True)
        self.assertEqual(res_utils.api_version, "2016-01-01-preview")

    def _get_mock_client(self):
        client = MagicMock()
        provider = MagicMock()
        provider.resource_types = [
            self._get_mock_resource_type('skip', ['2000-01-01-preview', '2000-01-01']),
            self._get_mock_resource_type('test', ['2016-01-01-preview', '2016-01-01']),
            self._get_mock_resource_type('foo', ['1999-01-01-preview', '1999-01-01']),
            self._get_mock_resource_type('preview', ['2005-01-01-preview', '2004-01-01-preview']),
            self._get_mock_resource_type('test_latest', ['2016-01-01-preview', '2015-01-01'])
        ]
        client.providers.get.return_value = provider
        return client

    def _get_mock_resource_type(self, name, api_versions):  # pylint: disable=no-self-use
        rt = MagicMock()
        rt.resource_type = name
        rt.api_versions = api_versions
        return rt


if __name__ == '__main__':
    unittest.main()

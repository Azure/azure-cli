# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
import mock
from azure.cli.core.mock import DummyCli

TEST_ALIAS_JSON_FILE = os.path.join(os.path.dirname(__file__), 'built_in_alias_for_test.json')


class TestConfigure(unittest.TestCase):
    @mock.patch('azure.cli.command_modules.alias.alias_util.ALIAS_JSON_FILE', TEST_ALIAS_JSON_FILE)
    def test_process_args(self):
        from azure.cli.command_modules.alias.custom import process_args_with_built_in_alias
        cli = DummyCli()

        # args begin with az: az sa -> az storage account
        args = ['az', 'sa']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['az', 'storage', 'account'])

        # args without az: sa -> storage account
        args = ['sa']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['storage', 'account'])

        # args end with alias: storage account bsp -> storage account blob-service-properties
        args = ['storage', 'account', 'bsp']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['storage', 'account', 'blob-service-properties'])

        # args with multi alias: sa bsp -> storage account blob-service-properties
        args = ['sa', 'bsp']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['storage', 'account', 'blob-service-properties'])

        # args with alias and real commands: sa bsp show -h -> storage account blob-service-properties show -h
        args = ['sa', 'bsp', 'show', '-h']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['storage', 'account', 'blob-service-properties', 'show', '-h'])

        # args with argument alias:
        #   timeseriesinsights environment create --type --name -> timeseriesinsights environment longterm create --name
        args = ['timeseriesinsights', 'environment', 'create', '--type', 'longterm', '--name', 'test']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['timeseriesinsights', 'environment', 'longterm', 'create', '--name', 'test'])

        # test jinja.Template: configure --list-defaults -> config get defaults
        args = ['configure', '--list-defaults']
        process_args_with_built_in_alias(cli, args)
        self.assertEqual(args, ['config', 'get', 'defaults'])


if __name__ == '__main__':
    unittest.main()
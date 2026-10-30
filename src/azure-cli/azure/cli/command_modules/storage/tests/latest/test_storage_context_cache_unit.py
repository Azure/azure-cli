# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.command_modules.storage.aaz.latest.storage.account import FileServiceUsage
from azure.cli.command_modules.storage.aaz.latest.storage.context_cache import Create, List
from azure.cli.command_modules.storage.aaz.latest.storage.context_cache.container import Create as ContainerCreate


class StorageContextCacheCommandsTest(unittest.TestCase):

    def test_context_cache_create_arguments(self):
        self.assertEqual('2026-09-01', Create._aaz_info['version'])

        args_schema = Create.get_arguments_schema()
        self.assertTrue(args_schema.context_cache_name._required)
        self.assertTrue(args_schema.account_kind._required)
        self.assertTrue(args_schema.location._required)

    def test_context_cache_list_supports_subscription_and_resource_group_scopes(self):
        args_schema = List.get_arguments_schema()

        self.assertFalse(args_schema.resource_group._required)

    def test_context_cache_container_create_arguments(self):
        self.assertEqual('2026-09-01', ContainerCreate._aaz_info['version'])

        args_schema = ContainerCreate.get_arguments_schema()
        self.assertTrue(args_schema.context_cache_name._required)
        self.assertTrue(args_schema.context_cache_container_name._required)
        self.assertTrue(args_schema.model_name._required)
        self.assertTrue(args_schema.provider._required)
        self.assertEqual(1, args_schema.time_to_live._fmt._minimum)
        self.assertEqual(30, args_schema.time_to_live._fmt._maximum)

    def test_file_service_usage_uses_2026_api(self):
        self.assertEqual('2026-06-01', FileServiceUsage._aaz_info['version'])
        self.assertEqual(
            '/subscriptions/{}/resourcegroups/{}/providers/microsoft.storage/storageaccounts/{}/'
            'fileservices/default/usages/default',
            FileServiceUsage._aaz_info['resources'][0][1])


if __name__ == '__main__':
    unittest.main()

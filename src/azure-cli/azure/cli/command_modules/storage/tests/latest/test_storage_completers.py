#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from argparse import Namespace
from unittest import mock

from azure.cli.command_modules.storage.completers import (get_storage_name_completion_list,
                                                          get_storage_acl_name_completion_list,
                                                          file_path_completer)


class TestStorageCompleters(unittest.TestCase):

    def test_storage_name_completer_returns_empty_with_missing_legacy_service(self):
        completer = get_storage_name_completion_list(None, 'list_containers')
        self.assertEqual(completer.func(None, '', Namespace()), [])

    def test_storage_acl_name_completer_returns_empty_with_missing_legacy_service(self):
        completer = get_storage_acl_name_completion_list(None, 'container_name', 'get_container_acl')
        self.assertEqual(completer.func(None, '', Namespace(container_name='container')), [])

    @mock.patch('azure.cli.command_modules.storage.completers.validate_client_parameters')
    @mock.patch('azure.cli.command_modules.storage.completers._get_legacy_file_service_class', return_value=None)
    def test_file_path_completer_returns_empty_with_missing_legacy_service(self, _, __):
        self.assertEqual(file_path_completer.func(None, '', Namespace(share_name='share')), [])


if __name__ == '__main__':
    unittest.main()

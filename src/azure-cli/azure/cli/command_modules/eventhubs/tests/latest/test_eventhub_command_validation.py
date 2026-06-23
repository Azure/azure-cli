# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import unittest

from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub._list import List


class EventHubCommandValidationTests(unittest.TestCase):

    def test_eventhub_list_allows_short_valid_namespace_names(self):
        namespace_name_format = List._build_arguments_schema().namespace_name._fmt

        self.assertEqual(namespace_name_format._pattern, "^[a-zA-Z][a-zA-Z0-9-]{4,48}[a-zA-Z0-9]$")
        self.assertEqual(namespace_name_format._min_length, 6)
        self.assertEqual(namespace_name_format._max_length, 50)
        self.assertIsNotNone(re.fullmatch(namespace_name_format._pattern, 'oooooo'))
        self.assertIsNotNone(re.fullmatch(namespace_name_format._pattern, 'ooooooo'))
        self.assertIsNone(re.fullmatch(namespace_name_format._pattern, 'ooooo'))

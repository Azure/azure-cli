# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
import unittest

from azure.cli.command_modules.eventhubs.aaz.latest.eventhubs.eventhub._list import List


class EventHubCommandValidationTests(unittest.TestCase):

    def test_eventhub_list_namespace_name_length_constraints(self):
        namespace_name_format = List._build_arguments_schema().namespace_name._fmt
        valid_min_length_namespace = 'ns0001'
        valid_short_namespace = 'ns00001'
        invalid_under_min_length_namespace = 'ns001'
        valid_max_length_namespace = 'n' + ('0' * 48) + '1'
        invalid_over_max_length_namespace = 'n' + ('0' * 49) + '1'

        self.assertEqual(namespace_name_format._pattern, "^[a-zA-Z][a-zA-Z0-9-]{4,48}[a-zA-Z0-9]$")
        self.assertEqual(namespace_name_format._min_length, 6)
        self.assertEqual(namespace_name_format._max_length, 50)
        self.assertEqual(len(valid_min_length_namespace), namespace_name_format._min_length)
        self.assertEqual(len(valid_max_length_namespace), namespace_name_format._max_length)
        self.assertIsNotNone(re.fullmatch(namespace_name_format._pattern, valid_min_length_namespace))
        self.assertIsNotNone(re.fullmatch(namespace_name_format._pattern, valid_short_namespace))
        self.assertIsNotNone(re.fullmatch(namespace_name_format._pattern, valid_max_length_namespace))
        self.assertIsNone(re.fullmatch(namespace_name_format._pattern, invalid_under_min_length_namespace))
        self.assertIsNone(re.fullmatch(namespace_name_format._pattern, invalid_over_max_length_namespace))

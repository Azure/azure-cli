# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock
from azure.cli.core.util import CLIError


class EventHubCommandValidationTests(unittest.TestCase):

    def _make_namespace(self, name):
        ns = MagicMock()
        ns.namespace_name = name
        return ns

    def test_eventhub_list_namespace_name_valid_min_length(self):
        from azure.cli.command_modules.eventhubs._validator import validate_namespace_name
        validate_namespace_name(self._make_namespace('ns0001'))

    def test_eventhub_list_namespace_name_valid_max_length(self):
        from azure.cli.command_modules.eventhubs._validator import validate_namespace_name
        validate_namespace_name(self._make_namespace('n' + '0' * 48 + '1'))

    def test_eventhub_list_namespace_name_valid_short(self):
        from azure.cli.command_modules.eventhubs._validator import validate_namespace_name
        validate_namespace_name(self._make_namespace('ns00001'))

    def test_eventhub_list_namespace_name_too_short(self):
        from azure.cli.command_modules.eventhubs._validator import validate_namespace_name
        with self.assertRaises(CLIError):
            validate_namespace_name(self._make_namespace('ns001'))

    def test_eventhub_list_namespace_name_too_long(self):
        from azure.cli.command_modules.eventhubs._validator import validate_namespace_name
        with self.assertRaises(CLIError):
            validate_namespace_name(self._make_namespace('n' + '0' * 49 + '1'))

    def test_eventhub_list_namespace_name_none_passes(self):
        from azure.cli.command_modules.eventhubs._validator import validate_namespace_name
        validate_namespace_name(self._make_namespace(None))


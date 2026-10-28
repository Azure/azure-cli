# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import runpy
import unittest
from unittest import mock

from azure.cli.core.breaking_change import upcoming_breaking_changes
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.containerapp.custom import create_managed_environment


class ContainerappBreakingChangeTest(unittest.TestCase):
    def test_logs_destination_preannouncement(self):
        with mock.patch.dict(upcoming_breaking_changes, clear=True):
            runpy.run_module('azure.cli.command_modules.containerapp._breaking_change')
            changes = upcoming_breaking_changes['containerapp env create']
            self.assertEqual(len(changes), 1)
            change = changes[0]
            self.assertEqual(change.current_default, 'log-analytics')
            self.assertEqual(change.new_default, 'azure-monitor')
            self.assertIn('--logs-destination', change.message)
            self.assertIn('in 2.93.0', change.message)
            self.assertIn('https://github.com/Azure/azure-cli/pull/34228', change.message)
            self.assertTrue(change.to_tag(DummyCli()).always_display)

        self.assertEqual(
            inspect.signature(create_managed_environment).parameters['logs_destination'].default,
            'log-analytics',
        )

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import inspect
import runpy
import unittest
from unittest import mock

from azure.cli.core.breaking_change import AzCLIDefaultChange, upcoming_breaking_changes
from azure.cli.command_modules.containerapp.custom import create_managed_environment


class ContainerappBreakingChangeTest(unittest.TestCase):
    def test_logs_destination_preannouncement(self):
        with mock.patch.dict(upcoming_breaking_changes, clear=True):
            runpy.run_module('azure.cli.command_modules.containerapp._breaking_change')
            changes = upcoming_breaking_changes.get('containerapp env create', [])
            self.assertFalse(any(
                isinstance(change, AzCLIDefaultChange)
                and '--logs-destination' in change.args
                and change.current_default == 'log-analytics'
                and change.new_default == 'azure-monitor'
                for change in changes
            ))

        self.assertEqual(
            inspect.signature(create_managed_environment).parameters['logs_destination'].default,
            'azure-monitor',
        )

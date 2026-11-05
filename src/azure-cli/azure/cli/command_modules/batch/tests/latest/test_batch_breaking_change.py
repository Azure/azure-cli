# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import os
import runpy
import unittest
from unittest import mock

from azure.batch._operations._patch import BatchClientOperationsMixin
from azure.cli.core.breaking_change import upcoming_breaking_changes
from azure.cli.core.mock import DummyCli
from azure.cli.core.util import rmtree_with_retry


class TestBatchBreakingChange(unittest.TestCase):

    def test_batch_preannouncements(self):
        with mock.patch.dict(upcoming_breaking_changes, clear=True):
            module = runpy.run_module('azure.cli.command_modules.batch._breaking_change')
            self.assertEqual(sorted(upcoming_breaking_changes), [
                'batch node delete.retaineddata',
                'batch node reboot.retaineddata',
                'batch pool resize.retaineddata',
                'batch pool usage-metrics list'])
            for changes in upcoming_breaking_changes.values():
                self.assertEqual(len(changes), 1)
                self.assertEqual(str(changes[0].target_version), 'in ' + module['TARGET_VERSION'])
                self.assertIn('will be removed in ' + module['TARGET_VERSION'], changes[0].message)


class TestBatchRetainedDataWarning(unittest.TestCase):
    """Run the commands that accept 'retaineddata' with the SDK calls mocked, so nothing is sent to the service."""

    ACCOUNT_ARGS = ['--account-name', 'clibatch', '--account-key', 'BatchAccountKey',
                    '--account-endpoint', 'https://clibatch.eastus.batch.azure.com']
    # SDK operation: (command line, option that accepts 'retaineddata')
    COMMANDS = {
        'resize_pool': (['batch', 'pool', 'resize', '--pool-id', 'mypool', '--target-dedicated-nodes', '1'],
                        '--node-deallocation-option'),
        'remove_nodes': (['batch', 'node', 'delete', '--pool-id', 'mypool', '--node-list', 'node1'],
                         '--node-deallocation-option'),
        'reboot_node': (['batch', 'node', 'reboot', '--pool-id', 'mypool', '--node-id', 'node1'],
                        '--node-reboot-option'),
    }
    LOGGER = 'cli.azure.cli.command_modules.batch._validators'

    def setUp(self):
        # No Batch settings from AZURE_BATCH_* environment variables or the CLI config
        environ = {name: value for name, value in os.environ.items() if not name.startswith('AZURE_BATCH_')}
        environ_patch = mock.patch.dict(os.environ, environ, clear=True)
        environ_patch.start()
        self.addCleanup(environ_patch.stop)
        self.cli = DummyCli(random_config_dir=True)
        self.addCleanup(self.cli.env_patch.stop)
        self.addCleanup(rmtree_with_retry, self.cli.config.config_dir)

        self.operations = {}
        for name in self.COMMANDS:
            # The CLI builds the command's arguments from the SDK method's docstring, so the mock keeps it
            docstring = getattr(BatchClientOperationsMixin, name).__doc__
            operation_patch = mock.patch.object(BatchClientOperationsMixin, name, autospec=True, return_value=None)
            self.operations[name] = operation_patch.start()
            self.addCleanup(operation_patch.stop)
            self.operations[name].__doc__ = docstring

    def _invoke(self, operation, extra_args):
        args = self.COMMANDS[operation][0] + extra_args + self.ACCOUNT_ARGS
        self.operations[operation].reset_mock()
        self.assertEqual(self.cli.invoke(args, out_file=io.StringIO()), 0)
        self.operations[operation].assert_called_once()

    def test_batch_retained_data_warning(self):
        for operation, (args, option) in self.COMMANDS.items():
            for value in ['retaineddata', 'RetainedData']:
                with self.subTest(command=' '.join(args[:3]), value=value):
                    with self.assertLogs(self.LOGGER, 'WARNING') as logs:
                        self._invoke(operation, [option, value])
                    self.assertEqual(len(logs.records), 1)
                    self.assertIn(f"The value 'retaineddata' of '{option}' has been deprecated and will be removed",
                                  logs.records[0].getMessage())

    def test_batch_other_values_no_warning(self):
        for operation, (args, option) in self.COMMANDS.items():
            for extra_args in [[option, 'requeue'], [option, 'terminate'], [option, 'taskcompletion'], []]:
                with self.subTest(command=' '.join(args[:3]), args=extra_args):
                    with self.assertNoLogs(self.LOGGER, 'WARNING'):
                        self._invoke(operation, extra_args)

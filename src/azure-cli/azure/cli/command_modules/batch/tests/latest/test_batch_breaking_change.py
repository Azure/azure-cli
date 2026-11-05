# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import io
import json
import os
import runpy
import unittest
from unittest import mock

from azure.batch._operations._patch import BatchClientOperationsMixin
from azure.cli.command_modules.batch._validators import validate_retained_data_option
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
    # SDK operation: (command line for --json-file, JSON body without the value, JSON name of the value)
    JSON_COMMANDS = {
        'remove_nodes': (['batch', 'node', 'delete', '--pool-id', 'mypool'], {'nodeList': ['node1']},
                         'nodeDeallocationOption'),
        'reboot_node': (['batch', 'node', 'reboot', '--pool-id', 'mypool', '--node-id', 'node1'], {},
                        'nodeRebootOption'),
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

    def _invoke(self, operation, args):
        self.operations[operation].reset_mock()
        self.assertEqual(self.cli.invoke(args + self.ACCOUNT_ARGS, out_file=io.StringIO()), 0)
        self.operations[operation].assert_called_once()

    def _json_file(self, name, content):
        # In the test's own config folder, which is removed after the test
        path = os.path.join(self.cli.config.config_dir, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def test_batch_retained_data_warning(self):
        for operation, (args, option) in self.COMMANDS.items():
            for value in ['retaineddata', 'RetainedData']:
                with self.subTest(command=' '.join(args[:3]), value=value):
                    with self.assertLogs(self.LOGGER, 'WARNING') as logs:
                        self._invoke(operation, args + [option, value])
                    self.assertEqual(len(logs.records), 1)
                    self.assertIn(f"The value 'retaineddata' of '{option}' has been deprecated and will be removed",
                                  logs.records[0].getMessage())

    def test_batch_other_values_no_warning(self):
        for operation, (args, option) in self.COMMANDS.items():
            for extra_args in [[option, 'requeue'], [option, 'terminate'], [option, 'taskcompletion'], []]:
                with self.subTest(command=' '.join(args[:3]), args=extra_args):
                    with self.assertNoLogs(self.LOGGER, 'WARNING'):
                        self._invoke(operation, args + extra_args)

    def test_batch_retained_data_json_file_warning(self):
        for operation, (args, body, key) in self.JSON_COMMANDS.items():
            option = self.COMMANDS[operation][1]
            for value in ['retaineddata', 'RetainedData']:
                with self.subTest(command=' '.join(args[:3]), value=value):
                    json_file = self._json_file('body.json', json.dumps(dict(body, **{key: value})))
                    with self.assertLogs(self.LOGGER, 'WARNING') as logs:
                        self._invoke(operation, args + ['--json-file', json_file])
                    self.assertEqual(len(logs.records), 1)
                    self.assertIn(f"The value 'retaineddata' of '{option}' has been deprecated and will be removed",
                                  logs.records[0].getMessage())

    def test_batch_other_values_json_file_no_warning(self):
        for operation, (args, body, key) in self.JSON_COMMANDS.items():
            for value in ['requeue', 'terminate', 'taskcompletion', None]:
                with self.subTest(command=' '.join(args[:3]), value=value):
                    json_file = self._json_file('body.json', json.dumps(dict(body, **{key: value}) if value else body))
                    with self.assertNoLogs(self.LOGGER, 'WARNING'):
                        self._invoke(operation, args + ['--json-file', json_file])

    def test_batch_unreadable_json_file(self):
        # The usual --json-file errors: exit code 2 for a missing file, 1 for invalid JSON
        missing = os.path.join(self.cli.config.config_dir, 'missing.json')
        invalid = self._json_file('invalid.json', '{"nodeRebootOption": ')
        cases = [(missing, 2, 'Cannot access JSON request file: ' + missing),
                 (invalid, 1, f"Failed to parse file '{invalid}' with exception:")]
        for operation, (args, _, _) in self.JSON_COMMANDS.items():
            for json_file, exit_code, error in cases:
                with self.subTest(command=' '.join(args[:3]), json_file=os.path.basename(json_file)):
                    self.operations[operation].reset_mock()
                    with self.assertNoLogs(self.LOGGER, 'WARNING'), \
                            self.assertLogs('cli.azure.cli.core.azclierror', 'ERROR') as logs:
                        try:
                            code = self.cli.invoke(args + ['--json-file', json_file] + self.ACCOUNT_ARGS,
                                                   out_file=io.StringIO())
                        except SystemExit as ex:
                            code = ex.code
                    self.assertEqual(code, exit_code)
                    self.assertTrue(logs.records[0].getMessage().startswith(error))
                    self.operations[operation].assert_not_called()

    def test_batch_retained_data_loaded_json_body(self):
        namespace = argparse.Namespace(command='batch node reboot', node_reboot_option=None,
                                       json_file={'nodeRebootOption': 'retaineddata'})
        with self.assertLogs(self.LOGGER, 'WARNING') as logs:
            validate_retained_data_option(namespace)
        self.assertEqual(len(logs.records), 1)

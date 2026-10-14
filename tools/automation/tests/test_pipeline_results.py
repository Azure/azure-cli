# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Offline regression tests for CI result aggregation after package migration."""

import importlib.util
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock
import xml.etree.ElementTree as ET


class PipelineResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = Path(__file__).resolve().parents[3] / 'scripts/ci/automation_full_test.py'
        spec = importlib.util.spec_from_file_location('automation_full_test', script)
        cls.runner = importlib.util.module_from_spec(spec)
        # Loading the reporting functions must not require installing azdev,
        # resolving repositories, or running the scheduler.
        utilities = ModuleType('azdev.utilities')
        utilities.get_path_table = mock.Mock(side_effect=AssertionError('Unexpected azdev discovery'))
        with mock.patch.dict(sys.modules, {'azdev': ModuleType('azdev'), 'azdev.utilities': utilities}), \
                mock.patch.object(sys, 'argv', [str(script)]):
            spec.loader.exec_module(cls.runner)
        cls.addClassCleanup(cls.runner.logger.removeHandler, cls.runner.ch)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.patch = mock.patch.multiple(self.runner, working_directory=str(self.root), unique_job_name='job')
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.reset_result()
        self.add_source('azure-cli-telemetry/azure/cli/telemetry/tests/test_telemetry_note.py')
        self.add_source('azure-cli-core/azure/cli/core/tests/test_aaz_arg.py')

    def reset_result(self):
        self.rows = [{'Module': name, 'Status': 'Running', 'Content': ''}
                     for name in ('network', 'core', 'telemetry')]
        self.result = {'job': {'Details': [{'Details': [{'Details': [{'Details': self.rows}]}]}]}}

    def add_source(self, relative):
        path = self.root / 'src' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def aggregate(self, cases, single_suite=False):
        root = ET.Element('testsuite' if single_suite else 'testsuites')
        suite = root if single_suite else ET.SubElement(root, 'testsuite')
        for attributes, outcome in cases:
            case = ET.SubElement(suite, 'testcase', dict(name='test_example', **attributes))
            if outcome:
                kind, message = outcome
                node = ET.SubElement(case, kind)
                if message is not None:
                    node.set('message', message)
                node.text = 'Failure details'
        path = self.root / 'results.xml'
        ET.ElementTree(root).write(path, encoding='utf-8')
        returned = self.runner.get_pipeline_result(str(path), self.result)
        self.assertIs(returned, self.result)
        return {row['Module']: row for row in self.rows}

    def test_short_telemetry_classname_from_migrated_package(self):
        for filename in ('test_telemetry_note.py', 'src/azure-cli/test_telemetry_note.py'):
            with self.subTest(filename=filename):
                self.reset_result()
                rows = self.aggregate([({'classname': 'test_telemetry_note.TestTelemetryNote',
                                         'file': filename}, None)])
                self.assertEqual(rows['telemetry']['Status'], 'Succeeded')
                self.assertEqual(rows['core']['Status'], 'Running')

    def test_short_classname_without_file_uses_source_inventory(self):
        rows = self.aggregate([({'classname': 'test_aaz_arg.TestAAZArg'}, None)])
        self.assertEqual(rows['core']['Status'], 'Succeeded')

    def test_short_command_module_classname_uses_source_inventory(self):
        self.add_source('azure-cli/azure/cli/command_modules/network/tests/latest/test_network.py')
        rows = self.aggregate([({'classname': 'test_network.TestNetwork'}, None)])
        self.assertEqual(rows['network']['Status'], 'Succeeded')

    def test_existing_qualified_names_remain_supported(self):
        for classname, module in (
            ('azure.cli.command_modules.network.tests.latest.test_network.TestNetwork', 'network'),
            ('src.azure-cli.azure.cli.command_modules.network.tests.hybrid_2018_03_01.test_network.TestNetwork', 'network'),
            ('azure.cli.core.tests.test_aaz_arg.TestAAZArg', 'core'),
            ('src.azure-cli-core.azure.cli.core.tests.test_aaz_arg.TestAAZArg', 'core'),
            ('azure.cli.telemetry.tests.test_telemetry_note.TestTelemetryNote', 'telemetry'),
            ('src.azure-cli-telemetry.azure.cli.telemetry.tests.test_telemetry_note.TestTelemetryNote', 'telemetry'),
        ):
            with self.subTest(classname=classname):
                self.reset_result()
                with mock.patch.object(self.runner, '_test_file_modules',
                                       side_effect=AssertionError('Unexpected source scan')):
                    rows = self.aggregate([({'classname': classname}, None)])
                self.assertEqual(rows[module]['Status'], 'Succeeded')

    def test_file_path_identifies_module_without_classname(self):
        for file_name in (
            'src/azure-cli/azure/cli/command_modules/network/tests/latest/test_commands.py',
            r'C:\repo\src\azure-cli\azure\cli\command_modules\network\tests\test_commands.py',
        ):
            with self.subTest(file_name=file_name):
                self.reset_result()
                rows = self.aggregate([({'file': file_name}, None)])
                self.assertEqual(rows['network']['Status'], 'Succeeded')

    def test_xunit1_failure_location_and_failed_status_are_preserved(self):
        rows = self.aggregate([
            ({'classname': 'test_telemetry_note.TestTelemetryNote', 'file': 'test_telemetry_note.py',
              'line': '42'}, ('failure', 'unexpected\nvalue')),
            ({'classname': 'test_telemetry_note.TestTelemetryNote'}, None),
        ])
        self.assertEqual(rows['telemetry']['Status'], 'Failed')
        self.assertIn('unexpected<br>value', rows['telemetry']['Content'])
        self.assertIn('test_telemetry_note.py:42', rows['telemetry']['Content'])

    def test_failure_survives_a_later_report(self):
        case = {'classname': 'test_telemetry_note.TestTelemetryNote'}
        self.aggregate([(case, ('failure', 'first report failed'))])
        rows = self.aggregate([(case, None), (case, ('skipped', 'not applicable'))])
        self.assertEqual(rows['telemetry']['Status'], 'Failed')
        self.assertIn('first&nbsp;report&nbsp;failed', rows['telemetry']['Content'])

    def test_oversized_failure_keeps_existing_message_limit(self):
        rows = self.aggregate([({'classname': 'test_aaz_arg.TestAAZArg'}, ('failure', 'x' * 65536))])
        self.assertEqual(rows['core']['Status'], 'Failed')
        self.assertIn('The error message is too long', rows['core']['Content'])
        self.assertLess(len(rows['core']['Content']), 1000)

    def test_xunit2_error_without_location_or_message_is_reported(self):
        rows = self.aggregate([({'classname': 'test_aaz_arg.TestAAZArg'}, ('error', None))])
        self.assertEqual(rows['core']['Status'], 'Failed')
        self.assertIn('Failure&nbsp;details', rows['core']['Content'])

    def test_unknown_or_missing_classname_does_not_hide_failure(self):
        for count, attributes in enumerate(({'classname': 'Unexpected'}, {}, {'classname': 'a.b.command_modules'}), 1):
            with self.subTest(attributes=attributes):
                rows = self.aggregate([(attributes, ('failure', 'cannot attribute'))])
                self.assertEqual(rows['unknown']['Status'], 'Failed')
                self.assertIn('cannot&nbsp;attribute', rows['unknown']['Content'])
                self.assertEqual(rows['unknown']['Content'].count('|Failed|'), count)
                self.assertEqual(rows['core']['Status'], 'Running')
        self.assertEqual(sum(row['Module'] == 'unknown' for row in self.rows), 1)

    def test_ambiguous_short_name_is_not_assigned_to_wrong_module(self):
        self.add_source('azure-cli-core/azure/cli/core/tests/test_shared.py')
        self.add_source('azure-cli-telemetry/azure/cli/telemetry/tests/test_shared.py')
        rows = self.aggregate([({'classname': 'test_shared.TestShared'}, ('failure', 'ambiguous'))])
        self.assertEqual(rows['unknown']['Status'], 'Failed')
        self.assertEqual(rows['core']['Status'], 'Running')
        self.assertEqual(rows['telemetry']['Status'], 'Running')

    def test_single_suite_root_is_supported(self):
        rows = self.aggregate([({'classname': 'test_telemetry_note.TestTelemetryNote'}, None)], single_suite=True)
        self.assertEqual(rows['telemetry']['Status'], 'Succeeded')

    def test_reported_ci_batch_completes_after_passing_tests(self):
        network = {'classname': 'azure.cli.command_modules.network.tests.latest.test_network.TestNetwork'}
        telemetry = {'classname': 'test_telemetry_note.TestTelemetryNote',
                     'file': 'test_telemetry_note.py'}
        with mock.patch.object(self.runner, '_test_file_modules', wraps=self.runner._test_file_modules) as inventory:
            rows = self.aggregate([(network, None)] * 305 + [(telemetry, None)] * 2 +
                                  [(network, ('skipped', 'not applicable'))] * 78)
        inventory.assert_called_once_with()
        self.assertEqual(rows['network']['Status'], 'Succeeded')
        self.assertEqual(rows['telemetry']['Status'], 'Succeeded')


if __name__ == '__main__':
    unittest.main()

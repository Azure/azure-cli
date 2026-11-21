# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import io
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest import mock

from azure.cli.command_modules.network.custom import add_dns_txt_record, export_zone
from azure.cli.command_modules.network.zone_file import parse_zone_file


class DnsExportScenarioConfigurationUnitTest(unittest.TestCase):

    def _scenario_method(self, live=None, recorded=False):
        scenario_path = os.path.join(os.path.dirname(__file__), 'latest', 'test_dns_commands.py')
        recording_path = os.path.join(os.path.dirname(scenario_path), 'recordings',
                                      'test_dns_zone_export_empty_txt_recordsets.yaml')
        exists = os.path.exists

        def recording_exists(path):
            return recorded if path == recording_path else exists(path)

        with mock.patch.dict(os.environ), \
                mock.patch('os.path.exists', side_effect=recording_exists):
            if live is None:
                os.environ.pop('AZURE_TEST_RUN_LIVE', None)
            else:
                os.environ['AZURE_TEST_RUN_LIVE'] = live
            scenario = runpy.run_path(scenario_path)['DnsScenarioTest']
        return scenario.test_dns_zone_export_empty_txt_recordsets

    def test_unrecorded_dns_export_is_excluded_from_playback(self):
        for live in [None, 'false', '0', 'off']:
            with self.subTest(live=live):
                self.assertTrue(getattr(self._scenario_method(live=live), '__unittest_skip__', False))

    def test_dns_export_runs_live_without_recording(self):
        for live in ['true', 'yes', '1', 'on']:
            with self.subTest(live=live):
                self.assertFalse(getattr(self._scenario_method(live=live), '__unittest_skip__', False))

    def test_recorded_dns_export_runs_in_playback(self):
        self.assertFalse(getattr(self._scenario_method(recorded=True), '__unittest_skip__', False))


class DnsExportAuthenticationUnitTest(unittest.TestCase):

    def test_unrecorded_dns_export_is_skipped_before_resource_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario_path = os.path.join(os.path.dirname(__file__), 'latest', 'test_dns_commands.py')
            shutil.copyfile(scenario_path, os.path.join(directory, 'test_dns_commands.py'))
            environment = dict(
                os.environ,
                AZURE_TEST_RUN_LIVE='false',
                AZURE_CONFIG_DIR=directory,
                AZURE_EXTENSION_DIR=os.path.join(directory, 'extensions'),
                AZURE_EXTENSION_SYS_DIR=os.path.join(directory, 'system-extensions'),
                AZURE_CORE_COLLECT_TELEMETRY='false',
                PYTHONPATH=os.pathsep.join([directory] + [path for path in sys.path if path])
            )
            result = subprocess.run(
                [sys.executable, '-S', '-m', 'unittest', '-v',
                 'test_dns_commands.DnsScenarioTest.test_dns_zone_export_empty_txt_recordsets'],
                env=environment, capture_output=True, text=True, timeout=60, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('OK (skipped=1)', result.stderr)
            self.assertNotIn("Please run 'az login'", result.stderr)

    def test_dns_export_and_resource_preparation_require_an_account(self):
        with tempfile.TemporaryDirectory() as directory:
            file_name = os.path.join(directory, 'zone.txt')
            environment = dict(
                os.environ,
                AZURE_CONFIG_DIR=directory,
                AZURE_EXTENSION_DIR=os.path.join(directory, 'extensions'),
                AZURE_EXTENSION_SYS_DIR=os.path.join(directory, 'system-extensions'),
                AZURE_CORE_COLLECT_TELEMETRY='false',
                PYTHONPATH=os.pathsep.join(path for path in sys.path if path)
            )
            for arguments in [
                    ['network', 'dns', 'zone', 'export', '-g', 'test-rg', '-n', 'example.com',
                     '-f', file_name],
                    ['group', 'create', '-n', 'test-rg', '--location', 'westus']]:
                with self.subTest(command=arguments):
                    result = subprocess.run(
                        [sys.executable, '-S', '-m', 'azure.cli', *arguments],
                        env=environment, capture_output=True, text=True, timeout=60, check=False
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("Please run 'az login' to setup account.", result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertFalse(os.path.exists(file_name))


class DnsTxtFixtureUnitTest(unittest.TestCase):

    def test_cli_txt_fixture_preserves_empty_and_long_values(self):
        cmd = SimpleNamespace(cli_ctx=mock.sentinel.cli_ctx)
        for value, expected in [
                ([''], ['']),
                (['-validation-text'], ['-validation-text']),
                (['a' * 250 + 'b' * 250], ['a' * 250 + 'b' * 5, 'b' * 245])]:
            with self.subTest(value=value), mock.patch(
                    'azure.cli.command_modules.network.custom._add_save_record') as save_record:
                add_dns_txt_record(cmd, 'test-rg', 'example.com', 'mixed', value)
                save_record.assert_called_once_with(
                    cmd, {'value': expected}, 'txt', 'mixed', 'test-rg', 'example.com',
                    if_none_match=None)


class DnsExportUnitTest(unittest.TestCase):

    def test_dns_zone_export_empty_txt_recordsets(self):
        def record_set(name, record_type, **properties):
            return dict(name=name, type='Microsoft.Network/dnszones/' + record_type,
                        ttl=3600, **properties)

        long_value = ['a' * 250, 'b' * 250]
        records = [
            record_set('@', 'SOA', SOARecord={
                'host': 'ns1.example.com', 'email': 'hostmaster.example.com',
                'serialNumber': 1, 'refreshTime': 3600, 'retryTime': 300,
                'expireTime': 2419200, 'minimumTTL': 300
            }),
            record_set('@', 'NS', NSRecords=[{'nsdname': 'ns1.example.com.'}]),
            record_set('populated', 'TXT', TXTRecords=[{'value': ['validation-text']}]),
            record_set('empty-string', 'TXT', TXTRecords=[{'value': ['']}]),
            record_set('mixed', 'TXT', TXTRecords=[
                {'value': ['']}, {'value': ['-validation-text']}, {'value': long_value}
            ]),
            record_set('acme', 'A', ARecords=[{'ipv4Address': '192.0.2.1'}]),
            record_set('ipv6', 'AAAA', AAAARecords=[{'ipv6Address': '2001:db8::1'}]),
            record_set('www', 'CNAME', CNAMERecord={'cname': 'example.com.'}),
        ]
        target_id = '/subscriptions/test/resourceGroups/test/providers/Microsoft.Network/publicIPAddresses/ip'
        for record_type in ['A', 'AAAA', 'CNAME']:
            records.append(record_set('alias-' + record_type.lower(), record_type,
                                      targetResource={'id': target_id}))

        for empty_properties in [{'TXTRecords': None}, {'TXTRecords': []}, {}]:
            with self.subTest(empty_properties=empty_properties):
                source = records + [
                    record_set('acme', 'TXT', **empty_properties),
                    record_set('empty-only', 'TXT', **empty_properties)
                ]
                before = copy.deepcopy(source)
                stdout = io.StringIO()
                with tempfile.TemporaryDirectory() as directory:
                    file_name = os.path.join(directory, 'exported zone.txt')
                    with mock.patch(
                            'azure.cli.command_modules.network.custom._DNSRecordSetListByZone'
                    ) as list_records, redirect_stdout(stdout):
                        list_records.return_value.return_value = iter(source)
                        export_zone(SimpleNamespace(cli_ctx=mock.sentinel.cli_ctx),
                                    'test-rg', 'example.com', file_name)
                    with open(file_name) as zone_file:
                        content = zone_file.read()

                self.assertEqual(stdout.getvalue(), content + '\n')
                self.assertEqual(source, before)
                self.assertNotIn('empty-only', content)
                self.assertNotRegex(content, r'acme\s+3600 IN TXT')
                # The zone parser normalizes empty strings to EMPTY, so check the text directly.
                self.assertRegex(content, r'(?m)^empty-string\s+3600 IN TXT ""$')
                self.assertRegex(content, r'(?m)^mixed\s+3600 IN TXT ""$')
                parsed = parse_zone_file(content, 'example.com')
                self.assertEqual(parsed['populated.example.com.']['txt'][0]['txt'], ['validation-text'])
                self.assertEqual(len(parsed['empty-string.example.com.']['txt']), 1)
                self.assertEqual(len(parsed['mixed.example.com.']['txt']), 3)
                self.assertEqual(
                    [''.join(record['txt']) for record in parsed['mixed.example.com.']['txt'][1:]],
                    ['-validation-text', ''.join(long_value)]
                )
                for name in ['populated', 'empty-string', 'mixed']:
                    for record in parsed[name + '.example.com.']['txt']:
                        self.assertEqual(record['ttl'], 3600)
                soa = parsed['example.com.']['soa']
                self.assertEqual(soa['ttl'], 3600)
                self.assertEqual(int(soa['serial']), records[0]['SOARecord']['serialNumber'])
                for key in ['host', 'email']:
                    self.assertEqual(soa[key], records[0]['SOARecord'][key].rstrip('.') + '.')
                for key, service_key in [
                        ('refresh', 'refreshTime'), ('retry', 'retryTime'),
                        ('expire', 'expireTime'), ('minimum', 'minimumTTL')]:
                    self.assertEqual(soa[key], records[0]['SOARecord'][service_key])
                for name, record_type, key, value in [
                        ('acme', 'a', 'ip', '192.0.2.1'),
                        ('ipv6', 'aaaa', 'ip', '2001:db8::1'),
                        ('www', 'cname', 'alias', 'example.com.'),
                        ('@', 'ns', 'host', 'ns1.example.com.')]:
                    fqdn = 'example.com.' if name == '@' else name + '.example.com.'
                    record = parsed[fqdn][record_type]
                    if record_type != 'cname':
                        record = record[0]
                    self.assertEqual(record['ttl'], 3600)
                    self.assertEqual(record[key], value)
                for record_type in ['A', 'AAAA', 'CNAME']:
                    self.assertIn('alias-{} 3600 AZURE ALIAS {} {}'.format(
                        record_type.lower(), record_type, target_id), content)

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from io import BytesIO, TextIOWrapper
from types import SimpleNamespace
from unittest import mock


class TestCoreCLIOutput(unittest.TestCase):
    def test_create_AzOutputProducer(self):
        from azure.cli.core._output import AzOutputProducer
        from azure.cli.core.mock import DummyCli

        output_producer = AzOutputProducer(DummyCli())
        self.assertEqual(7, len(output_producer._FORMAT_DICT))  # six types: json, jsonc, table, tsv, yaml, yamlc, none
        self.assertIn('yaml', output_producer._FORMAT_DICT)
        self.assertIn('none', output_producer._FORMAT_DICT)

    # regression test for https://github.com/Azure/azure-cli/issues/9263
    def test_yaml_output_with_ordered_dict(self):
        from azure.cli.core._output import AzOutputProducer
        from azure.cli.core.mock import DummyCli
        from knack.util import CommandResultItem
        from collections import OrderedDict
        import yaml

        account_dict = {
            "environmentName": "AzureCloud",
            "id": "000000-000000",
            "isDefault": True,
            "name": "test_sub",
            "state": "Enabled",
            "tenantId": "000000-000000-000000",
            "user": {
                "name": "test@example.com",
                "type": "user"
            }
        }

        output_producer = AzOutputProducer(DummyCli())
        yaml_output = output_producer.get_formatter('yaml')(CommandResultItem(result=OrderedDict(account_dict)))
        self.assertEqual(account_dict, yaml.safe_load(yaml_output))


class TestOutputNewline(unittest.TestCase):

    def setUp(self):
        import shutil
        import tempfile
        from knack.config import CLIConfig
        self.config_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.config_dir, True)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for name in ('AZURE_CORE_OUTPUT_NEWLINE', 'AZURE_CONFIG_DIR', 'AZ_LAUNCHER'):
            os.environ.pop(name, None)
        self.cli = SimpleNamespace(config=CLIConfig(config_dir=self.config_dir, config_env_var_prefix='AZURE'),
                                   out_file=None)

    @staticmethod
    def _windows_like_stream():
        return TextIOWrapper(BytesIO(), encoding='utf-8', newline='\r\n')

    @staticmethod
    def _written(stream, text='a\r\nb\nc\n'):
        stream.write(text)
        stream.flush()
        return stream.buffer.getvalue()

    def test_output_newline_defaults_to_native(self):
        from azure.cli.core._output import get_output_newline
        self.assertEqual('native', get_output_newline(self.cli))

    def test_output_newline_bash_launcher_defaults_to_lf(self):
        from azure.cli.core._output import get_output_newline
        os.environ['AZ_LAUNCHER'] = 'bash'
        self.assertEqual('lf', get_output_newline(self.cli))

    def test_output_newline_config_overrides_launcher(self):
        from azure.cli.core._output import get_output_newline
        os.environ['AZ_LAUNCHER'] = 'bash'
        self.cli.config.set_value('core', 'output_newline', 'native')
        self.assertEqual('native', get_output_newline(self.cli))

    def test_output_newline_env_overrides_config(self):
        from azure.cli.core._output import get_output_newline
        self.cli.config.set_value('core', 'output_newline', 'native')
        os.environ['AZURE_CORE_OUTPUT_NEWLINE'] = ' LF '
        self.assertEqual('lf', get_output_newline(self.cli))

    def test_output_newline_empty_value_selects_default(self):
        from azure.cli.core._output import get_output_newline
        os.environ['AZ_LAUNCHER'] = 'bash'
        os.environ['AZURE_CORE_OUTPUT_NEWLINE'] = ''
        self.assertEqual('lf', get_output_newline(self.cli))
        # An empty env value selects the default; it does not fall back to the config file.
        self.cli.config.set_value('core', 'output_newline', 'native')
        self.assertEqual('lf', get_output_newline(self.cli))
        del os.environ['AZURE_CORE_OUTPUT_NEWLINE']
        del os.environ['AZ_LAUNCHER']
        self.cli.config.set_value('core', 'output_newline', '  ')
        self.assertEqual('native', get_output_newline(self.cli))

    def test_apply_output_newline_lf_writes_data_unchanged(self):
        from azure.cli.core._output import apply_output_newline
        os.environ['AZURE_CORE_OUTPUT_NEWLINE'] = 'lf'
        self.cli.out_file = self._windows_like_stream()
        stdout = self._windows_like_stream()
        with mock.patch('sys.stdout', stdout):
            apply_output_newline(self.cli)
        # LF stays LF, and CRLF already in the data is not doubled to '\r\r\n'.
        self.assertEqual(b'a\r\nb\nc\n', self._written(self.cli.out_file))
        self.assertEqual(b'a\r\nb\nc\n', self._written(stdout))

    def test_apply_output_newline_native_leaves_stream_untouched(self):
        from azure.cli.core._output import apply_output_newline
        self.cli.out_file = self._windows_like_stream()
        with mock.patch('sys.stdout', self.cli.out_file):
            apply_output_newline(self.cli)
        self.assertEqual(b'a\r\r\nb\r\nc\r\n', self._written(self.cli.out_file))

    def test_apply_output_newline_invalid_value_warns(self):
        from azure.cli.core import _output
        os.environ['AZURE_CORE_OUTPUT_NEWLINE'] = 'crlf'
        self.cli.out_file = self._windows_like_stream()
        with mock.patch('sys.stdout', self.cli.out_file), mock.patch.object(_output.logger, 'warning') as warning:
            _output.apply_output_newline(self.cli)
        warning.assert_called_once()
        self.assertIn('crlf', warning.call_args[0])
        self.assertEqual(b'a\r\r\nb\r\nc\r\n', self._written(self.cli.out_file))

    def test_apply_output_newline_unreadable_config_warns_instead_of_raising(self):
        from azure.cli.core import _output
        self.cli.config.set_value('core', 'output_newline', '%(missing)s')
        self.cli.out_file = self._windows_like_stream()
        with mock.patch('sys.stdout', self.cli.out_file), mock.patch.object(_output.logger, 'warning') as warning:
            _output.apply_output_newline(self.cli)
        warning.assert_called_once()
        self.assertEqual(b'a\r\r\nb\r\nc\r\n', self._written(self.cli.out_file))

    def test_apply_output_newline_skips_streams_without_reconfigure(self):
        from io import StringIO
        from azure.cli.core._output import apply_output_newline
        os.environ['AZURE_CORE_OUTPUT_NEWLINE'] = 'lf'
        self.cli.out_file = StringIO()
        with mock.patch('sys.stdout', self.cli.out_file):
            apply_output_newline(self.cli)
        self.cli.out_file.write('a\n')
        self.assertEqual('a\n', self.cli.out_file.getvalue())


if __name__ == '__main__':
    unittest.main()

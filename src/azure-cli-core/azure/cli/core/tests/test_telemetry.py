# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import tempfile
import unittest
from contextlib import ExitStack
from unittest import mock


class TestCoreTelemetry(unittest.TestCase):
    def test_suppress_all_exceptions(self):
        self._impl(Exception, 'fallback')
        self._impl(Exception, None)
        self._impl(ImportError, 'fallback_for_import_error')
        self._impl(None, None)

    def _impl(self, exception_to_raise, fallback_return):
        from azure.cli.core.decorators import suppress_all_exceptions

        @suppress_all_exceptions(fallback_return=fallback_return)
        def _error_fn():
            if not exception_to_raise:
                return 'positive result'
            else:
                raise exception_to_raise()

        if not exception_to_raise:
            self.assertEqual(_error_fn(), 'positive result')
        else:
            self.assertEqual(_error_fn(), fallback_return)

    def test_extract_parameters_correctly(self):
        from azure.cli.core.commands import AzCliCommandInvoker
        args = ['vm', 'user', 'update', '-g', 'rg', '-n', 'vm1', '-u', 'user',
                '--ssh-key-value', '-----BEGIN PRIVATE KEY-----']
        self.assertEqual(['-g', '-n', '-u', '--ssh-key-value'], AzCliCommandInvoker._extract_parameter_names(args))

        args = ['vm', 'create', '--resource-group-name', 'rg', '--name', 'vm1', '--image', 'centos']
        self.assertEqual(['--resource-group-name', '--name', '--image'], AzCliCommandInvoker._extract_parameter_names(args))

        args = ['vm', 'show', '-g', 'rg', '--name', 'vm1', '-d', '--debug']
        self.assertEqual(['-g', '--name', '-d', '--debug'], AzCliCommandInvoker._extract_parameter_names(args))

    def test_cloud_forbid_telemetry(self):
        from unittest import mock
        from azure.cli.core import telemetry
        from azure.cli.core.mock import DummyCli
        from knack.completion import ARGCOMPLETE_ENV_NAME

        az_cli = DummyCli()
        telemetry.set_application(az_cli, ARGCOMPLETE_ENV_NAME)
        # mock user turns off telemetry
        with mock.patch('knack.config.CLIConfig.getboolean', return_value=False):
            self.assertFalse(telemetry.is_telemetry_enabled())
        # mock user turns on telemetry
        with mock.patch('knack.config.CLIConfig.getboolean', return_value=True):
            self.assertTrue(telemetry.is_telemetry_enabled())
            # mock to add current cloud name in CLOUDS_FORBIDDING_TELEMETRY
            with mock.patch('azure.cli.core.cloud.CLOUDS_FORBIDDING_TELEMETRY', [az_cli.cloud.name]):
                self.assertFalse(telemetry.is_telemetry_enabled())

    @mock.patch('azure.cli.core.util.get_az_version_string')
    def test_show_version_sets_telemetry_params(self, mock_get_version):
        """Test show_version telemetry state is same regardless of available updates."""
        from azure.cli.core.mock import DummyCli
        from azure.cli.core import telemetry
        from knack.completion import ARGCOMPLETE_ENV_NAME

        mock_get_version.return_value = ("azure-cli 2.80.0", ["core", "extension1"])

        telemetry.start()

        cli = DummyCli()
        telemetry.set_application(cli, ARGCOMPLETE_ENV_NAME)

        cli.show_version()

        session = telemetry._session
        self.assertEqual(session.command, "")
        self.assertEqual(session.parameters, ["--version"])
        self.assertIsNone(session.raw_command)


class TestAgentTelemetry(unittest.TestCase):
    def setUp(self):
        from azure.cli.core import telemetry
        self.telemetry = telemetry
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        self.contexts.enter_context(mock.patch.dict(os.environ, {}, clear=True))
        self.session = telemetry.TelemetrySession(application=mock.Mock(data={'headers': {}}, cloud=None))
        self.contexts.enter_context(mock.patch.object(telemetry, '_session', self.session))

    def test_agent_signals(self):
        # Broad matching, precedence changes and raw-value returns must fail here.
        markers = [('CLAUDE_CODE_CHILD_SESSION', 'claude-code'), ('COPILOT_CLI', 'copilot-cli'),
                   ('COPILOT_AGENT', 'copilot-vscode'), ('CODEX_CI', 'codex'),
                   ('CURSOR_AGENT', 'cursor'), ('GEMINI_CLI', 'gemini-cli')]
        cases = [({}, 'unknown'), ({name: '1' for name, _ in markers}, 'multiple'),
                 ({'CLAUDE_CODE_CHILD_SESSION': '1', 'CODEX_CI': '1'}, 'multiple'),
                 ({'CLAUDECODE': '1', 'AGENT': '1', 'CI': '1', 'TERM_PROGRAM': 'vscode',
                   'VSCODE_PID': '1', 'COPILOT_AGENT_SESSION_ID': 'synthetic-id',
                   'CODEX_VERSION': '99.1', 'SHELL': 'cursor'}, 'unknown')]
        for name, expected in markers:
            cases.append(({name: '1'}, expected))
            for value in ('', '0', 'true', 'yes', '01', ' 1', '1 ', '1\n'):
                cases.append(({name: value}, 'cursor' if name == 'CURSOR_AGENT' and value else 'unknown'))
        for value in ('', 'unknown', 'x' * 97, 'github_copilot_vscode_agent' + 'x' * 97,
                      'GITHUB_COPILOT_VSCODE_AGENT', ' github_copilot_vscode_agent',
                      'github_copilot_vscode_agent\n', 'claude-code_1.2.3_agent', 'synthetic\r\nvalue'):
            cases.extend([({'AI_AGENT': value}, 'unknown'),
                          ({'AI_AGENT': value, 'CODEX_CI': '1'}, 'codex')])
        cases.append(({'AI_AGENT': 'github_copilot_vscode_agent',
                       **{name: '1' for name, _ in markers}}, 'copilot-vscode'))
        for env, expected in cases:
            with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(self.telemetry._get_agent(), expected)

    def test_agent_reads_only_allowlisted_names(self):
        env = mock.MagicMock()
        env.__iter__.side_effect = AssertionError('environment enumeration')
        env.keys.side_effect = AssertionError('environment enumeration')
        for values, expected, names in [({}, 'unknown', ['AI_AGENT', 'CLAUDE_CODE_CHILD_SESSION',
                                                        'COPILOT_CLI', 'COPILOT_AGENT', 'CODEX_CI',
                                                        'CURSOR_AGENT', 'GEMINI_CLI']),
                                        ({'AI_AGENT': 'github_copilot_vscode_agent'},
                                         'copilot-vscode', ['AI_AGENT'])]:
            env.get.side_effect = values.get
            env.get.reset_mock()
            with mock.patch.object(os, 'environ', env):
                self.assertEqual(self.telemetry._get_agent(), expected)
            self.assertCountEqual(env.get.call_args_list, [mock.call(name, None) for name in names])

    def _isolate_payload(self):
        # Keep payload construction real, replacing unrelated profile/process/cache access.
        config = mock.Mock(**{'get.return_value': 'unknown', 'getboolean.return_value': False})
        for name, value in [('_get_base_properties', {}), ('_get_installation_id', ''),
                            ('_get_user_azure_id', ''), ('_get_azure_subscription_id', ''),
                            ('_get_config', config), ('_get_env_string', ''),
                            ('_get_user_agent', ''), ('_get_shell_type', '')]:
            target = self.session if name == '_get_base_properties' else self.telemetry
            self.contexts.enter_context(mock.patch.object(target, name, return_value=value))
        self.contexts.enter_context(mock.patch('azure.cli.core._environment.get_config_dir', return_value='unused'))
        return self.contexts.enter_context(mock.patch('azure.cli.telemetry.save'))

    def test_agent_payload_lifecycle(self):
        save = self._isolate_payload()
        telemetry = self.telemetry
        key = 'Context.Default.AzureCLI.Agent'
        self.contexts.enter_context(mock.patch.object(telemetry, 'is_telemetry_enabled', return_value=True))
        os.environ.update(AI_AGENT='synthetic\r\nprivate-value', CURSOR_AGENT='synthetic-private-value')
        self.session.add_exception(ValueError('synthetic failure'), 'test')
        with self.assertNoLogs('cli.azure.cli.core.decorators', level='INFO'):
            telemetry.flush()
        events = next(iter(json.loads(save.call_args.args[1]).values()))
        self.assertEqual([event['name'] for event in events], ['azurecli/command', 'azurecli/fault'])
        for event in events:
            self.assertEqual(event['properties'][key], 'cursor')
            self.assertEqual(event['properties']['Context.Default.AzureCLI.AgenticSession'], 'False')
        self.assertNotIn('private-value', save.call_args.args[1])
        os.environ.clear()
        os.environ['CODEX_CI'] = '1'
        telemetry.set_agentic_session(True)
        self.session.add_event('azurecli/extension', {'synthetic': 'custom'})
        telemetry.conclude()
        events = next(iter(json.loads(save.call_args.args[1]).values()))
        self.assertEqual(events[0], {'name': 'azurecli/extension', 'properties': {'synthetic': 'custom'}})
        props = events[1]['properties']
        self.assertEqual(props[key], 'codex')
        self.assertEqual(props['Context.Default.AzureCLI.AgenticSession'], 'True')
        self.session.events.clear()
        self.session.add_event('azurecli/extension', {'synthetic': 'custom'})
        telemetry.suppress_new_events()
        with mock.patch.object(telemetry, '_get_agent') as detector:
            telemetry.conclude()
            detector.assert_not_called()
        self.assertEqual(next(iter(json.loads(save.call_args.args[1]).values())),
                         [{'name': 'azurecli/extension', 'properties': {'synthetic': 'custom'}}])
        self.session.events.clear()
        telemetry.suppress_new_events(unsuppress=True)
        with mock.patch.object(telemetry, '_get_agent', side_effect=RuntimeError('synthetic failure')):
            telemetry.conclude()
        props = next(iter(json.loads(save.call_args.args[1]).values()))[0]['properties']
        self.assertNotIn(key, props)

    def test_agent_consent_config_and_environment(self):
        from knack.config import CLIConfig
        save = self._isolate_payload()
        telemetry = self.telemetry
        directory = self.contexts.enter_context(tempfile.TemporaryDirectory())
        config = CLIConfig(config_dir=directory, config_env_var_prefix='AZURE', use_local_config=False)
        self.contexts.enter_context(mock.patch.object(telemetry, '_get_config', return_value=config))
        with mock.patch('azure.cli.core.cloud.cloud_forbid_telemetry', return_value=False) as forbidden:
            for finalize in (telemetry.conclude, telemetry.flush):
                for configured, override, cloud, enabled in [('true', None, False, True),
                                                            ('false', None, False, False),
                                                            ('true', 'false', False, False),
                                                            ('true', None, True, False)]:
                    with self.subTest(finalize=finalize.__name__, config=configured, env=override, cloud=cloud):
                        config.set_value('core', 'collect_telemetry', configured)
                        env = {'AZURE_CORE_COLLECT_TELEMETRY': override} if override else {}
                        forbidden.return_value = cloud
                        save.reset_mock()
                        with mock.patch.dict(os.environ, env, clear=True), \
                                mock.patch.object(telemetry, '_get_agent', return_value='unknown') as detector, \
                                mock.patch.object(self.session, 'generate_payload',
                                                  wraps=self.session.generate_payload) as payload:
                            finalize()
                            self.assertEqual(detector.called, enabled)
                            self.assertEqual(payload.called, enabled)
                            self.assertEqual(save.called, enabled)


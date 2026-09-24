# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from unittest import mock

from azure.cli.command_modules.acs import _azure_plugin as plugin
from azure.cli.core.azclierror import (
    ClientRequestError, InvalidArgumentValueError, ResourceNotFoundError, ValidationError,
)

REAL_INSTALL_PLUGIN = plugin.install_plugin

# Claude Code 2.1.267 and Copilot 1.0.86-2 isolated native inventory outputs,
# with only fixture names/paths substituted. No executable plugin content.
CLAUDE_PLUGIN = {
    'id': 'azure@private-market', 'version': '1.0.0', 'scope': 'user', 'enabled': False,
    'installPath': '/fixture/azure', 'installedAt': '2026-09-22T00:00:00.000Z',
    'lastUpdated': '2026-09-22T00:00:00.000Z',
}
COPILOT_PLUGIN = {
    'name': 'azure', 'marketplace': 'private-market', 'version': '1.0.0',
    'enabled': False, 'source': 'installed',
}
# Codex rust-v0.144.3 cli/src/plugin_cmd.rs (JsonPluginListEntry), and
# cli/tests/plugin_cli.rs (plugin_list_json_prints_installed_plugins).
CODEX_PLUGIN = {
    'pluginId': 'azure@private-market', 'name': 'azure', 'marketplaceName': 'private-market',
    'version': '1.0.0', 'installed': True, 'enabled': False,
    'source': {'source': 'local', 'path': '/fixture/plugins/azure'},
    'marketplaceSource': {'sourceType': 'local', 'source': '/fixture'},
    'installPolicy': 'AVAILABLE', 'authPolicy': 'ON_USE',
}
CLAUDE_MARKET = {
    'name': 'claude-plugins-official', 'source': 'github', 'repo': 'example/private-fork',
    'ref': 'pinned', 'installLocation': '/fixture/marketplace',
}
COPILOT_MARKET = {'name': 'azure-skills', 'source': 'GitHub: example/private-fork', 'isDefault': False}
# Codex JsonMarketplaceListEntry: source metadata is optional; refs remain host-owned.
CODEX_MARKET = {
    'name': 'azure-skills', 'root': '/fixture/pinned-marketplace',
    'marketplaceSource': {'sourceType': 'git', 'source': 'https://example.com/private-fork.git'},
}
COPILOT_MCP = {'mcpServers': {'azure': {
    'tools': ['*'], 'command': '/nonexistent/inert', 'args': ['--pinned'], 'source': 'user', 'enabled': True,
}}}


class NativeProcessFixture:
    """Only exact native argv are accepted; every call is observable."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append(tuple(argv))
        if tuple(argv) not in self.responses:
            raise AssertionError('Unexpected native command: ' + repr(argv))
        response = self.responses[tuple(argv)]
        if callable(response):
            response = response()
        if isinstance(response, BaseException):
            raise response
        if not isinstance(response, subprocess.CompletedProcess):
            stdout = response if isinstance(response, str) else json.dumps(response)
            response = subprocess.CompletedProcess(argv, 0, stdout, '')
        process = mock.Mock(returncode=response.returncode)
        process.communicate.return_value = (response.stdout, response.stderr)
        return process


class AzurePluginOptionsTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_omitted_and_false_without_hosts_are_noop_options(self):
        for enabled in (None, False):
            with self.subTest(enabled=enabled):
                self.assertIsNone(plugin.validate_plugin_options(enabled))

    def test_explicit_hosts_are_deduplicated_in_supported_order(self):
        self.assertEqual(plugin.validate_plugin_options(True, ['codex', 'claude-code', 'codex', 'github-copilot']),
                         ['claude-code', 'github-copilot', 'codex'])
        self.assertEqual(plugin.validate_plugin_options(True, ['codex']), ['codex'])

    def test_invalid_option_relationships_fail_before_any_external_work(self):
        cases = [(True, None), (True, []), (True, ['']), (True, ['pi']), (True, ['codex', 'other']),
                 (None, ['codex']), (False, ['codex']), (None, []), (False, [])]
        with mock.patch.object(plugin.shutil, 'which') as which, \
                mock.patch.object(plugin.subprocess, 'Popen') as run:
            for enabled, hosts in cases:
                with self.subTest(enabled=enabled, hosts=hosts), self.assertRaises(InvalidArgumentValueError):
                    plugin.validate_plugin_options(enabled, hosts)
        which.assert_not_called()
        run.assert_not_called()

    def test_explicit_install_rejects_sudo_but_binary_only_options_remain_valid(self):
        for variable, value in (('SUDO_USER', 'someone'), ('SUDO_UID', '0')):
            with self.subTest(variable=variable), mock.patch.dict(os.environ, {variable: value}):
                with self.assertRaisesRegex(InvalidArgumentValueError, 'sudo'):
                    plugin.validate_plugin_options(True, ['codex'])
                self.assertIsNone(plugin.validate_plugin_options())
                self.assertIsNone(plugin.validate_plugin_options(False))


class AzurePluginConsentTest(unittest.TestCase):
    def setUp(self):
        self.cmd = mock.Mock()
        self.cmd.cli_ctx.config.getboolean.return_value = False
        self.stderr = io.StringIO()
        self.stdout = io.StringIO()
        self.installed = []
        patches = (
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch('sys.stdin.isatty', return_value=True),
            mock.patch('sys.stderr', self.stderr),
            mock.patch('knack.prompting._input', side_effect=AssertionError('Unexpected prompt')),
            mock.patch.object(plugin.shutil, 'which', side_effect=lambda name: name if name == 'codex' else None),
            mock.patch.object(plugin, 'install_plugin', side_effect=self.install),
            mock.patch.object(plugin.subprocess, 'Popen', side_effect=AssertionError('Unexpected native process')),
            mock.patch('sys.stdout', self.stdout),
            mock.patch('sys.stdin.read', side_effect=AssertionError('Unexpected stdin read')),
            mock.patch('sys.stdin.readline', side_effect=AssertionError('Unexpected stdin read')),
            mock.patch('builtins.input', side_effect=AssertionError('Unexpected input')),
        )
        self.mocks = [patcher.start() for patcher in patches]
        for patcher in patches:
            self.addCleanup(patcher.stop)

    def install(self, host):
        self.installed.append(host)
        self.assertIn('MCP', self.stderr.getvalue())
        return True

    def test_false_no_tty_disabled_confirmation_and_sudo_do_not_hint_or_probe(self):
        for condition in ('false', 'no-tty', 'disabled', 'sudo-user', 'sudo-uid'):
            with self.subTest(condition=condition), self.assertNoLogs('cli.' + plugin.__name__, level='WARNING'):
                self.mocks[1].return_value = condition != 'no-tty'
                self.cmd.cli_ctx.config.getboolean.return_value = condition == 'disabled'
                environment = {'SUDO_USER': 'user'} if condition == 'sudo-user' else {}
                if condition == 'sudo-uid':
                    environment = {'SUDO_UID': '0'}
                with mock.patch.dict(os.environ, environment, clear=True):
                    plugin.maybe_install_azure_plugin(self.cmd, False if condition == 'false' else None)
                self.assertEqual(self.installed, [])
                self.assertEqual(self.stderr.getvalue(), '')
                self.assertEqual(self.stdout.getvalue(), '')
                self.mocks[4].assert_not_called()
                self.mocks[6].assert_not_called()

    def test_omitted_tty_only_hints_once_without_reading_stdin_or_probing(self):
        with self.assertLogs('cli.' + plugin.__name__, level='WARNING') as logs:
            plugin.maybe_install_azure_plugin(self.cmd)
        self.assertEqual(len(logs.records), 1)
        self.assertIn('--install-azure-plugin', logs.output[0])
        self.assertIn('--plugin-hosts', logs.output[0])
        self.assertEqual(self.installed, [])
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(self.stdout.getvalue(), '')
        self.mocks[4].assert_not_called()
        self.mocks[6].assert_not_called()

    def assert_disclosure(self):
        text = self.stderr.getvalue()
        for disclosure in ('full Azure plugin', 'user', 'global', 'MCP', 'hooks', 'Node.js 22', 'npx',
                           '@azure/mcp@latest', 'not pinned', 'native', 'enable', 'hidden', 'stale',
                           'disabled', 'authentication', 'trust', 'sovereign', 'updates'):
            self.assertIn(disclosure, text)

    def test_new_install_prints_only_selected_host_lifecycle_commands(self):
        commands = {
            'claude-code': ('claude plugin update azure@claude-plugins-official --scope user',
                            'claude plugin uninstall azure@claude-plugins-official --scope user'),
            'github-copilot': ('copilot plugin update azure@azure-skills',
                               'copilot plugin uninstall azure@azure-skills'),
            'codex': ('codex plugin marketplace upgrade azure-skills', 'codex plugin remove azure@azure-skills'),
        }
        for host, expected in commands.items():
            with self.subTest(host=host):
                self.stderr.truncate(0)
                self.stderr.seek(0)
                plugin.maybe_install_azure_plugin(self.cmd, True, [host])
                message = self.stderr.getvalue()
                for command in expected:
                    self.assertIn(command, [line.rsplit(': ', 1)[-1] for line in message.splitlines()])
                    self.assertEqual(message.count(command), 1)
                    self.assertLess(message.index('installed;'), message.index(command))
                for other, excluded in commands.items():
                    if other != host:
                        for command in excluded:
                            self.assertNotIn(command, message)
                if host == 'codex':
                    self.assertIn('marketplace-wide', message)
                    self.assertIn('other installed plugins', message)
                    self.assertNotIn('codex plugin update', message)
                    self.assertNotIn('codex plugin add', message)
                self.assertEqual(self.stdout.getvalue(), '')
                self.mocks[6].assert_not_called()

    def test_existing_private_source_gets_no_hardcoded_lifecycle_target(self):
        self.mocks[5].side_effect = REAL_INSTALL_PLUGIN
        self.mocks[4].side_effect = lambda name: name
        process = NativeProcessFixture({
            ('claude', 'plugin', 'list', '--json'): [CLAUDE_PLUGIN],
            ('copilot', 'plugin', 'list', '--json'): [COPILOT_PLUGIN],
            ('codex', 'plugin', 'list', '--available', '--json'): {'installed': [CODEX_PLUGIN], 'available': []},
        })
        self.mocks[6].side_effect = process
        plugin.maybe_install_azure_plugin(self.cmd, True, list(plugin.HOST_IDS))
        message = self.stderr.getvalue()
        self.assertEqual(message.count('Azure already reported; plugin install skipped'), 3)
        self.assertNotIn('azure@', message)
        self.assertNotIn('marketplace upgrade', message)
        self.assertEqual(len(process.calls), 3)

    def test_explicit_hosts_need_no_tty_prompts_or_detection_even_with_confirm_disabled(self):
        self.mocks[1].return_value = False
        self.cmd.cli_ctx.config.getboolean.return_value = True
        plugin.maybe_install_azure_plugin(self.cmd, True, ['codex', 'claude-code', 'codex'])
        self.assertEqual(self.installed, ['claude-code', 'codex'])
        self.mocks[4].assert_not_called()
        self.assert_disclosure()

    def test_expected_failures_continue_hosts_and_preserve_explicit_error_category(self):
        for error_type in (ClientRequestError, ResourceNotFoundError, ValidationError):
            calls = []

            def install(host):
                calls.append(host)
                if host == 'claude-code':
                    raise error_type('first host failure')
                if host == 'codex':
                    raise ValidationError('last host failure')
                return True

            self.mocks[5].side_effect = install
            with self.subTest(error=error_type), self.assertRaises(error_type) as caught:
                plugin.maybe_install_azure_plugin(self.cmd, True, ['codex', 'github-copilot', 'claude-code'])
            message = str(caught.exception)
            for part in ('kubectl', 'kubelogin', 'remain installed', 'native plugin commands', 'rollback',
                         'Claude Code', 'first host failure', 'Codex CLI', 'last host failure',
                         'GitHub Copilot CLI', 'installed'):
                self.assertIn(part, message)
            self.assertEqual(calls, ['claude-code', 'github-copilot', 'codex'])
            output = self.stderr.getvalue()
            self.assertIn('copilot plugin update azure@azure-skills', output)
            self.assertIn('copilot plugin uninstall azure@azure-skills', output)
            self.assertNotIn('claude plugin', output)
            self.assertNotIn('codex plugin', output)

    def test_report_distinguishes_install_from_skip_without_claiming_zero_marketplace_changes(self):
        self.mocks[5].side_effect = [True, False]
        plugin.maybe_install_azure_plugin(self.cmd, True, ['claude-code', 'codex'])
        message = self.stderr.getvalue()
        self.assertIn('Claude Code: installed', message)
        self.assertIn('Codex CLI: Azure already reported; plugin install skipped', message)
        self.assertIn('marketplace may have been added', message)
        self.assertNotIn('all integrations are ready', message)
        self.assertIn('claude plugin update azure@claude-plugins-official --scope user', message)
        self.assertIn('claude plugin uninstall azure@claude-plugins-official --scope user', message)
        self.assertNotIn('codex plugin', message)

    def test_programming_errors_are_not_swallowed(self):
        self.mocks[5].side_effect = TypeError('programming error')
        with self.assertRaisesRegex(TypeError, 'programming error'):
            plugin.maybe_install_azure_plugin(self.cmd, True, ['codex'])

    def test_mcp_sensitive_errors_stay_redacted_through_flow_aggregation(self):
        secret = 'synthetic-mcp-flow-secret'
        # Exercise real Task 1 parsing and redaction inside the new aggregation path.
        self.mocks[5].side_effect = REAL_INSTALL_PLUGIN
        self.mocks[4].side_effect = lambda name: name
        self.mocks[6].side_effect = NativeProcessFixture({
            ('copilot', 'plugin', 'list', '--json'): [],
            ('copilot', 'mcp', 'list', '--json'): subprocess.CompletedProcess([], 7, secret, secret),
        })
        with self.assertRaises(ClientRequestError) as caught:
            plugin.maybe_install_azure_plugin(self.cmd, True, ['github-copilot'])
        rendered = ''.join(traceback.format_exception(caught.exception))
        self.assertNotIn(secret, rendered + self.stderr.getvalue())
        self.assertIn('MCP inventory', str(caught.exception))
        self.assertIn('exit 7', str(caught.exception))

    def test_all_inventory_errors_stay_redacted_through_flow_aggregation(self):
        secret = 'synthetic-private-market-credential'
        self.mocks[5].side_effect = REAL_INSTALL_PLUGIN
        self.mocks[4].side_effect = lambda name: name
        command = ('codex', 'plugin', 'list', '--available', '--json')
        market = ('codex', 'plugin', 'marketplace', 'list', '--json')
        for failing in (command, market):
            self.mocks[6].side_effect = NativeProcessFixture({
                command: {'installed': [], 'available': []},
                failing: subprocess.CompletedProcess([], 7, secret, secret),
            })
            with self.subTest(failing=failing), self.assertRaises(ClientRequestError) as caught:
                plugin.maybe_install_azure_plugin(self.cmd, True, ['codex'])
            self.assertNotIn(secret, ''.join(traceback.format_exception(caught.exception)) + self.stderr.getvalue())
            self.assertIn('exit 7', str(caught.exception))

    def test_cancellation_reports_partial_native_state_even_when_logging_is_quiet(self):
        self.mocks[5].side_effect = REAL_INSTALL_PLUGIN
        self.mocks[4].side_effect = lambda name: name
        process = NativeProcessFixture({
            ('claude', 'plugin', 'list', '--json'): [],
            ('claude', 'plugin', 'marketplace', 'list', '--json'): [],
            ('node', '--version'): 'v22.0.0',
            ('claude', 'plugin', 'marketplace', 'add', 'anthropics/claude-plugins-official', '--scope', 'user'): '',
            ('claude', 'plugin', 'install', 'azure@claude-plugins-official', '--scope', 'user'):
                subprocess.CompletedProcess([], 1, '', 'native install refused'),
            ('copilot', 'plugin', 'list', '--json'): KeyboardInterrupt(),
        })
        self.mocks[6].side_effect = process
        with mock.patch.object(plugin.logger, 'disabled', True), self.assertRaises(KeyboardInterrupt):
            plugin.maybe_install_azure_plugin(self.cmd, True, list(plugin.HOST_IDS))
        message = self.stderr.getvalue()
        for part in ('Claude Code', 'native install refused', 'GitHub Copilot CLI: interrupted',
                     'native state is uncertain', 'kubectl and kubelogin remain installed',
                     'native plugin commands', 'No automatic retry or rollback'):
            self.assertIn(part, message)
        self.assertEqual(process.calls[-1], ('copilot', 'plugin', 'list', '--json'))
        self.assertFalse(any(call[0] == 'codex' for call in process.calls))
        self.assertNotIn('azure@', message)
        self.assertNotIn('marketplace upgrade', message)

    def test_cancellation_reports_prior_success_without_continuing(self):
        self.mocks[5].side_effect = [True, KeyboardInterrupt(), True]
        with self.assertRaises(KeyboardInterrupt):
            plugin.maybe_install_azure_plugin(self.cmd, True, list(plugin.HOST_IDS))
        self.assertEqual(self.mocks[5].call_args_list, [mock.call('claude-code'), mock.call('github-copilot')])
        self.assertIn('Claude Code: installed', self.stderr.getvalue())
        self.assertIn('GitHub Copilot CLI: interrupted', self.stderr.getvalue())
        self.assertIn('claude plugin update azure@claude-plugins-official --scope user', self.stderr.getvalue())
        self.assertIn('claude plugin uninstall azure@claude-plugins-official --scope user', self.stderr.getvalue())
        self.assertNotIn('copilot plugin', self.stderr.getvalue())
        self.assertNotIn('codex plugin', self.stderr.getvalue())

    def test_explicit_sudo_is_rejected_before_any_execution(self):
        with mock.patch.dict(os.environ, {'SUDO_UID': '123'}), self.assertRaises(InvalidArgumentValueError):
            plugin.maybe_install_azure_plugin(self.cmd, True, ['codex'])
        self.assertEqual(self.installed, [])
        self.mocks[4].assert_not_called()


class AzurePluginNativeTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(plugin.shutil, 'which', side_effect=lambda name: name)
        self.which = patcher.start()
        self.addCleanup(patcher.stop)

    def install(self, host, responses):
        self.process = NativeProcessFixture(responses)
        with mock.patch.object(plugin.subprocess, 'Popen', side_effect=self.process):
            return plugin.install_plugin(host)

    def fresh_responses(self, host, markets):
        if host == 'claude-code':
            return {
                ('claude', 'plugin', 'list', '--json'): [],
                ('claude', 'plugin', 'marketplace', 'list', '--json'): markets,
                ('claude', 'plugin', 'marketplace', 'add', 'anthropics/claude-plugins-official', '--scope', 'user'): '',
                ('claude', 'plugin', 'install', 'azure@claude-plugins-official', '--scope', 'user'): 'Installed',
                ('node', '--version'): 'v22.0.0\n',
            }
        if host == 'codex':
            return {
                ('codex', 'plugin', 'list', '--available', '--json'): {'installed': [], 'available': []},
                ('codex', 'plugin', 'marketplace', 'list', '--json'): {'marketplaces': markets},
                ('codex', 'plugin', 'marketplace', 'add', 'microsoft/azure-skills', '--json'): '{}',
                ('codex', 'plugin', 'add', 'azure@azure-skills', '--json'): '{}',
                ('node', '--version'): 'v22.0.0\n',
            }
        return {
            ('copilot', 'plugin', 'list', '--json'): [],
            ('copilot', 'mcp', 'list', '--json'): {'mcpServers': {}},
            ('copilot', 'plugin', 'marketplace', 'list', '--json'): markets,
            ('copilot', 'plugin', 'marketplace', 'add', 'microsoft/azure-skills'): '',
            ('copilot', 'plugin', 'install', 'azure@azure-skills'): 'Installed',
            ('node', '--version'): 'v22.0.0\n',
        }

    def mutations(self):
        return [call for call in self.process.calls if 'add' in call or 'install' in call]

    def test_claude_fresh_install_adds_official_marketplace_in_user_scope(self):
        self.assertTrue(self.install('claude-code', self.fresh_responses('claude-code', [])))
        self.assertEqual(self.mutations(), [
            ('claude', 'plugin', 'marketplace', 'add', 'anthropics/claude-plugins-official', '--scope', 'user'),
            ('claude', 'plugin', 'install', 'azure@claude-plugins-official', '--scope', 'user'),
        ])

    def test_copilot_fresh_install_checks_mcp_before_marketplace_add(self):
        self.assertTrue(self.install('github-copilot', self.fresh_responses('github-copilot', [])))
        self.assertEqual(self.mutations(), [
            ('copilot', 'plugin', 'marketplace', 'add', 'microsoft/azure-skills'),
            ('copilot', 'plugin', 'install', 'azure@azure-skills'),
        ])
        self.assertLess(self.process.calls.index(('copilot', 'mcp', 'list', '--json')),
                        self.process.calls.index(self.mutations()[0]))

    def test_codex_fresh_install_adds_marketplace_then_plugin_natively(self):
        self.assertTrue(self.install('codex', self.fresh_responses('codex', [])))
        self.assertEqual(self.process.calls, [
            ('codex', 'plugin', 'list', '--available', '--json'),
            ('codex', 'plugin', 'marketplace', 'list', '--json'),
            ('node', '--version'),
            ('codex', 'plugin', 'marketplace', 'add', 'microsoft/azure-skills', '--json'),
            ('codex', 'plugin', 'list', '--available', '--json'),
            ('codex', 'plugin', 'add', 'azure@azure-skills', '--json'),
        ])

    def test_existing_marketplace_keeps_native_source_and_pin(self):
        for host, market, command in (
                ('claude-code', CLAUDE_MARKET,
                 ('claude', 'plugin', 'install', 'azure@claude-plugins-official', '--scope', 'user')),
                ('github-copilot', COPILOT_MARKET, ('copilot', 'plugin', 'install', 'azure@azure-skills')),
                ('codex', CODEX_MARKET, ('codex', 'plugin', 'add', 'azure@azure-skills', '--json'))):
            with self.subTest(host=host):
                responses = self.fresh_responses(host, [copy.deepcopy(market)])
                original = copy.deepcopy(responses)
                self.assertTrue(self.install(host, responses))
                self.assertEqual(self.mutations(), [command])
                self.assertEqual(responses, original)

    def test_codex_marketplace_without_optional_source_metadata_is_not_readded(self):
        market = {'name': 'azure-skills', 'root': '/fixture/marketplace'}
        self.assertTrue(self.install('codex', self.fresh_responses('codex', [market])))
        self.assertEqual(self.mutations(), [('codex', 'plugin', 'add', 'azure@azure-skills', '--json')])

    def test_installed_azure_is_untouched_even_disabled_or_from_another_marketplace(self):
        for enabled in (True, False):
            for host, command, row in (
                    ('claude-code', ('claude', 'plugin', 'list', '--json'), CLAUDE_PLUGIN),
                    ('github-copilot', ('copilot', 'plugin', 'list', '--json'), COPILOT_PLUGIN),
                    ('codex', ('codex', 'plugin', 'list', '--available', '--json'), CODEX_PLUGIN)):
                with self.subTest(host=host, enabled=enabled):
                    entry = dict(row, enabled=enabled)
                    inventory = {'installed': [entry], 'available': []} if host == 'codex' else [entry]
                    self.which.reset_mock()
                    self.assertFalse(self.install(host, {command: inventory}))
                    self.assertEqual(self.process.calls, [command])
                    self.assertEqual(self.which.call_args_list, [mock.call(command[0])])

    def test_claude_azure_in_other_scopes_or_missing_files_is_not_repaired(self):
        for scope in ('project', 'local', 'managed'):
            row = dict(CLAUDE_PLUGIN, scope=scope, installPath='/missing/azure', projectPath='/fixture/project')
            self.assertFalse(self.install('claude-code', {('claude', 'plugin', 'list', '--json'): [row]}))
            self.assertEqual(self.mutations(), [])

    def test_copilot_direct_azure_registration_is_preserved(self):
        row = dict(COPILOT_PLUGIN, marketplace='', installedFrom='example/private-repo#pinned')
        self.assertFalse(self.install('github-copilot', {('copilot', 'plugin', 'list', '--json'): [row]}))
        self.assertEqual(self.mutations(), [])

    def test_copilot_azure_mcp_collision_blocks_fresh_install_from_every_source(self):
        for source in ('user', 'workspace', 'plugin', 'builtin'):
            for enabled in (True, False):
                responses = self.fresh_responses('github-copilot', [])
                mcp = copy.deepcopy(COPILOT_MCP)
                mcp['mcpServers']['azure'].update(source=source, enabled=enabled)
                responses[('copilot', 'mcp', 'list', '--json')] = mcp
                with self.subTest(source=source, enabled=enabled), self.assertRaisesRegex(ValidationError, 'azure.*MCP'):
                    self.install('github-copilot', responses)
                self.assertEqual(self.mutations(), [])

    def test_codex_valid_absence_allows_native_install_including_hidden_or_stale_states(self):
        # Native output cannot distinguish absence from orphaned/uncached registrations.
        # Consent covers normal install-and-enable, without reconstructing native settings.
        available = dict(CODEX_PLUGIN, installed=False)
        for inventory in ({'installed': [], 'available': []},
                          {'installed': [], 'available': [available]},
                          {'installed': [], 'available': [dict(available, enabled=True)]}):
            responses = self.fresh_responses('codex', [CODEX_MARKET])
            responses[('codex', 'plugin', 'list', '--available', '--json')] = inventory
            with self.subTest(inventory=inventory):
                self.assertTrue(self.install('codex', responses))
                self.assertEqual(self.mutations(), [('codex', 'plugin', 'add', 'azure@azure-skills', '--json')])

    def test_codex_native_policy_refusal_is_not_bypassed(self):
        responses = self.fresh_responses('codex', [CODEX_MARKET])
        responses[('codex', 'plugin', 'list', '--available', '--json')] = {
            'installed': [], 'available': [dict(CODEX_PLUGIN, installed=False, installPolicy='NOT_AVAILABLE')],
        }
        command = ('codex', 'plugin', 'add', 'azure@azure-skills', '--json')
        responses[command] = subprocess.CompletedProcess(command, 1, '', 'installation denied by policy')
        with self.assertRaisesRegex(ClientRequestError, 'Codex CLI.*denied by policy'):
            self.install('codex', responses)
        self.assertEqual(self.mutations(), [command])
        self.assertEqual(self.process.calls[-1], command)

    def test_copilot_live_azure_is_existing_even_when_disabled(self):
        for enabled in (False, True):
            row = dict(COPILOT_PLUGIN, source='live', enabled=enabled, installedFrom='/fixture/marketplace')
            command = ('copilot', 'plugin', 'list', '--json')
            self.which.reset_mock()
            with self.subTest(enabled=enabled):
                self.assertFalse(self.install('github-copilot', {command: [row]}))
                self.assertEqual(self.process.calls, [command])
                self.assertEqual(self.which.call_args_list, [mock.call('copilot')])

    def test_newly_visible_azure_after_marketplace_add_is_not_installed(self):
        for host, command, row in (
                ('claude-code', ('claude', 'plugin', 'list', '--json'), CLAUDE_PLUGIN),
                ('github-copilot', ('copilot', 'plugin', 'list', '--json'), dict(COPILOT_PLUGIN, source='live')),
                ('codex', ('codex', 'plugin', 'list', '--available', '--json'), CODEX_PLUGIN)):
            for enabled in (False, True):
                responses = self.fresh_responses(host, [])
                entry = dict(row, enabled=enabled)
                visible = {'installed': [entry], 'available': []} if host == 'codex' else [entry]
                responses[command] = iter([responses[command], visible]).__next__
                with self.subTest(host=host, enabled=enabled):
                    self.assertFalse(self.install(host, responses))
                    self.assertEqual(len(self.mutations()), 1)
                    self.assertEqual(self.mutations()[0][1:4], ('plugin', 'marketplace', 'add'))
                    self.assertEqual(self.process.calls[-1], command)
                    self.assertEqual(self.process.calls.count(command), 2)

    def test_inventory_refresh_failure_after_marketplace_add_never_installs_plugin(self):
        for host, command in (
                ('claude-code', ('claude', 'plugin', 'list', '--json')),
                ('github-copilot', ('copilot', 'plugin', 'list', '--json')),
                ('codex', ('codex', 'plugin', 'list', '--available', '--json'))):
            for response, error in (
                    ('not json', ValidationError), ({}, ValidationError),
                    (subprocess.CompletedProcess(command, 0, '[]', 'inventory warning'), ValidationError),
                    (subprocess.CompletedProcess(command, 1, '', 'policy refusal'), ClientRequestError),
                    (OSError('permission denied'), ClientRequestError),
                    (subprocess.TimeoutExpired(command, 300), ClientRequestError)):
                responses = self.fresh_responses(host, [])
                responses[command] = iter([responses[command], response]).__next__
                with self.subTest(host=host, response=response), self.assertRaises(error):
                    self.install(host, responses)
                self.assertEqual(len(self.mutations()), 1)
                self.assertEqual(self.mutations()[0][1:4], ('plugin', 'marketplace', 'add'))
                self.assertEqual(self.process.calls[-1], command)
                self.assertEqual(self.process.calls.count(command), 2)

    def test_invalid_plugin_inventory_never_becomes_absence(self):
        for host, command, bad_values in (
                ('claude-code', ('claude', 'plugin', 'list', '--json'),
                 ('not json', {}, None, [None], [{'name': 'azure'}], [dict(CLAUDE_PLUGIN, enabled='false')],
                  [dict(CLAUDE_PLUGIN, scope=None)])),
                ('github-copilot', ('copilot', 'plugin', 'list', '--json'),
                 ('help output', {}, None, [{}], [dict(COPILOT_PLUGIN, name=None)],
                  [dict(COPILOT_PLUGIN, source=None)])),
                ('codex', ('codex', 'plugin', 'list', '--available', '--json'),
                 ('help output', [], {}, {'installed': []}, {'installed': None, 'available': []},
                  {'installed': [dict(CODEX_PLUGIN, installed=False)], 'available': []},
                  {'installed': [], 'available': [CODEX_PLUGIN]},
                  {'installed': [], 'available': [dict(CODEX_PLUGIN, installed=False, pluginId='wrong')]},
                  {'installed': [], 'available': [dict(CODEX_PLUGIN, installed=False, enabled=None)]}))):
            for bad in bad_values:
                with self.subTest(host=host, bad=bad), self.assertRaises(ValidationError):
                    self.install(host, {command: bad})
                self.assertEqual(self.mutations(), [])

    def test_invalid_marketplace_inventory_never_triggers_add(self):
        for host in ('claude-code', 'github-copilot'):
            for bad in ({}, None, [None], [{}], [{'name': None}], [{'name': 'new-schema', 'source': {}}]):
                with self.subTest(host=host, bad=bad), self.assertRaises(ValidationError):
                    self.install(host, self.fresh_responses(host, bad))
                self.assertEqual(self.mutations(), [])

    def test_invalid_codex_marketplace_inventory_never_triggers_add(self):
        for bad in ([], {}, None, {'marketplaces': None}, {'marketplaces': [None]},
                    {'marketplaces': [{}]}, {'marketplaces': [dict(CODEX_MARKET, name=None)]},
                    {'marketplaces': [dict(CODEX_MARKET, root=None)]}):
            responses = self.fresh_responses('codex', [])
            responses[('codex', 'plugin', 'marketplace', 'list', '--json')] = bad
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                self.install('codex', responses)
            self.assertEqual(self.mutations(), [])

    def test_invalid_mcp_inventory_never_becomes_absence(self):
        for bad in ({}, [], {'mcpServers': []}, {'mcpServers': {'other': None}},
                    {'mcpServers': {'other': {}}}, {'mcpServers': {'other': {'source': 'user', 'enabled': 'false'}}}):
            responses = self.fresh_responses('github-copilot', [])
            responses[('copilot', 'mcp', 'list', '--json')] = bad
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                self.install('github-copilot', responses)
            self.assertEqual(self.mutations(), [])

    def test_mcp_inventory_failures_do_not_disclose_credentials(self):
        stdout_secret = 'synthetic-mcp-stdout-credential'
        stderr_secret = 'synthetic-mcp-stderr-credential'
        inventory = copy.deepcopy(COPILOT_MCP)
        inventory['mcpServers']['azure']['args'] = ['--token', stdout_secret]
        payload = json.dumps(inventory)
        real_popen = subprocess.Popen
        for case, stdout, stderr, ending, error, context in (
                ('invalid JSON', payload[:-1], '', 'sys.exit(0)', ValidationError, 'Invalid native JSON'),
                ('nonzero', payload, stderr_secret, 'sys.exit(7)', ClientRequestError, 'exit 7'),
                ('timeout', payload, stderr_secret, 'time.sleep(30)', ClientRequestError, 'timed out after'),
                ('warning', payload, stderr_secret, 'sys.exit(0)', ValidationError, 'warning')):
            calls = []
            owned = []
            script = (f'import sys, time; print({stdout!r}, flush=True); '
                      f'print({stderr!r}, file=sys.stderr, flush=True); {ending}')

            def popen(argv, **kwargs):
                calls.append(tuple(argv))
                if argv == ['copilot', 'plugin', 'list', '--json']:
                    return NativeProcessFixture({tuple(argv): []})(argv)
                if argv == ['copilot', 'mcp', 'list', '--json']:
                    process = real_popen([sys.executable, '-c', script], **kwargs)
                    owned.append(process)
                    # Register bound methods before wrapping communicate, even if an assertion fails.
                    self.addCleanup(process.communicate, timeout=5)
                    self.addCleanup(process.kill)
                    communicate = process.communicate
                    process.communicate = lambda timeout: communicate(timeout=0.2 if case == 'timeout' else timeout)
                    return process
                raise AssertionError('Unexpected native command: ' + repr(argv))

            def taskkill(argv, **kwargs):
                self.assertEqual(sys.platform, 'win32')
                self.assertEqual(len(owned), 1)
                self.assertEqual(argv, [os.path.join(os.environ['SystemRoot'], 'System32', 'taskkill.exe'),
                                        '/PID', str(owned[0].pid), '/T', '/F'])
                return subprocess.CompletedProcess(argv, 0)

            with self.subTest(case=case):
                with mock.patch.object(plugin.subprocess, 'Popen', side_effect=popen), \
                        mock.patch.object(plugin.subprocess, 'run', side_effect=taskkill), \
                        self.assertRaises(error) as caught:
                    plugin.install_plugin('github-copilot')
                message = str(caught.exception)
                for safe_context in ('GitHub Copilot CLI', 'MCP inventory', context, 'native'):
                    self.assertIn(safe_context, message)
                rendered = ''.join(traceback.format_exception(caught.exception))
                for secret in (stdout_secret, stderr_secret):
                    self.assertNotIn(secret, message)
                    self.assertNotIn(secret, rendered)
                self.assertEqual(calls, [('copilot', 'plugin', 'list', '--json'),
                                         ('copilot', 'mcp', 'list', '--json')])

    def test_mcp_inventory_failures_with_windows_cleanup_do_not_disclose_credentials(self):
        # Exercise the same real-child fixture without requiring a Windows host.
        with mock.patch.object(plugin.sys, 'platform', 'win32'), \
                mock.patch.object(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0, create=True), \
                mock.patch.dict(os.environ, {'SystemRoot': 'C:\\Windows'}):
            self.test_mcp_inventory_failures_do_not_disclose_credentials()

    def test_plugin_and_marketplace_failures_do_not_disclose_credentials(self):
        secret = 'synthetic-private-git-credential'
        payload = '{"source":{"url":"https://user:' + secret + '@example.test/repo.git"}}'
        for host, executable, args in (
                ('claude-code', 'claude', ['plugin', 'list', '--json']),
                ('github-copilot', 'copilot', ['plugin', 'list', '--json']),
                ('codex', 'codex', ['plugin', 'list', '--available', '--json'])):
            for command in ((executable, *args), (executable, 'plugin', 'marketplace', 'list', '--json')):
                for response, error, context in (
                        (payload[:-1], ValidationError, 'Invalid native JSON'),
                        (subprocess.CompletedProcess([], 0, payload, secret), ValidationError, 'warning'),
                        (subprocess.CompletedProcess([], 7, payload, secret), ClientRequestError, 'exit 7'),
                        (subprocess.TimeoutExpired(command, 300, output=payload, stderr=secret),
                         ClientRequestError, 'timed out'),
                        (OSError(secret), ClientRequestError, 'suppressed')):
                    responses = self.fresh_responses(host, [])
                    responses[command] = response
                    with self.subTest(host=host, command=command, context=context), self.assertRaises(error) as caught:
                        self.install(host, responses)
                    self.assertNotIn(secret, ''.join(traceback.format_exception(caught.exception)))
                    self.assertIn(context, str(caught.exception))
                    self.assertEqual(self.mutations(), [])

    def test_duplicate_json_members_fail_before_native_mutations(self):
        cases = (
            ('github-copilot', ('copilot', 'mcp', 'list', '--json'),
             '{"mcpServers":{"azure":{"source":"user","enabled":true}},"mcpServers":{}}'),
            ('codex', ('codex', 'plugin', 'list', '--available', '--json'),
             '{"installed":[{"name":"azure"}],"installed":[],"available":[]}'),
            ('codex', ('codex', 'plugin', 'marketplace', 'list', '--json'),
             '{"marketplaces":[{"name":"azure-skills"}],"marketplaces":[]}'),
            ('claude-code', ('claude', 'plugin', 'list', '--json'),
             '[{"id":"azure@private","id":"other@private","scope":"user","enabled":false}]'),
            ('github-copilot', ('copilot', 'mcp', 'list', '--json'),
             '{"mcpServers":{"other":{"source":"user","enabled":true,'
             '"private-key-sentinel":"secret-value-sentinel","private-key-sentinel":"last"}}}'),
        )
        for host, command, raw in cases:
            responses = self.fresh_responses(host, [])
            responses[command] = raw
            with self.subTest(host=host, command=command):
                with self.assertRaisesRegex(ValidationError, 'duplicate') as caught:
                    self.install(host, responses)
                rendered = ''.join(traceback.format_exception(caught.exception))
                self.assertNotIn('private-key-sentinel', rendered)
                self.assertNotIn('secret-value-sentinel', rendered)
                self.assertEqual(self.mutations(), [])

    def test_inventory_warning_never_becomes_absence(self):
        command = ('copilot', 'plugin', 'list', '--json')
        response = subprocess.CompletedProcess(command, 0, '[]', 'Configuration could not be loaded')
        with self.assertRaisesRegex(ValidationError, 'Native inventory warning'):
            self.install('github-copilot', {command: response})
        self.assertEqual(self.mutations(), [])

    def test_command_failure_never_retries_or_falls_through(self):
        for host in ('claude-code', 'github-copilot', 'codex'):
            responses = self.fresh_responses(host, [])
            commands = [command for command in responses if command[0] != 'node']
            for command in commands:
                broken = dict(responses)
                broken[command] = subprocess.CompletedProcess(command, 2, '', 'unsupported flag or policy refusal')
                context = 'exit 2' if 'list' in command else 'policy refusal'
                with self.subTest(host=host, command=command), self.assertRaisesRegex(ClientRequestError, context):
                    self.install(host, broken)
                self.assertEqual(self.process.calls[-1], command)
                self.assertEqual(self.process.calls.count(command), 1)

    def test_fresh_install_requires_node_and_npx_before_any_mutation(self):
        for missing in ('node', 'npx'):
            for host in ('claude-code', 'github-copilot', 'codex'):
                self.which.side_effect = lambda name: None if name == missing else name
                with self.subTest(host=host, missing=missing), self.assertRaisesRegex(ResourceNotFoundError, missing):
                    self.install(host, self.fresh_responses(host, []))
                self.assertEqual(self.mutations(), [])

    def test_node_21_or_unparseable_version_blocks_fresh_install(self):
        for version in ('v21.9.0', 'v20.19.0', '22', 'Node v22.0.0', '', 'v22.0.0\nunexpected output'):
            responses = self.fresh_responses('claude-code', [])
            responses[('node', '--version')] = version
            with self.subTest(version=version), self.assertRaisesRegex(ValidationError, 'Claude Code.*Node.js 22'):
                self.install('claude-code', responses)
            self.assertEqual(self.mutations(), [])

    def test_node_22_and_later_are_checked_once_before_native_mutations(self):
        for version in ('v22.0.0\n', 'v24.1.2', 'v25.9.0'):
            responses = self.fresh_responses('github-copilot', [])
            responses[('node', '--version')] = version
            with self.subTest(version=version):
                self.assertTrue(self.install('github-copilot', responses))
                self.assertEqual(self.process.calls.count(('node', '--version')), 1)
                self.assertLess(self.process.calls.index(('node', '--version')),
                                self.process.calls.index(self.mutations()[0]))
                self.assertIn(mock.call('npx'), self.which.call_args_list)

    def test_node_execution_failure_never_triggers_native_mutation(self):
        for error in (OSError('cannot execute node'), subprocess.TimeoutExpired(['node', '--version'], 300),
                      subprocess.CompletedProcess(['node', '--version'], 1, '', 'node failed')):
            responses = self.fresh_responses('claude-code', [])
            responses[('node', '--version')] = error
            with self.subTest(error=error), self.assertRaisesRegex(ClientRequestError, 'Claude Code.*Node.js'):
                self.install('claude-code', responses)
            self.assertEqual(self.mutations(), [])

    def test_native_oserror_and_timeout_stop_at_the_failing_operation(self):
        for host in ('claude-code', 'github-copilot', 'codex'):
            responses = self.fresh_responses(host, [])
            for command in (key for key in responses if key[0] != 'node'):
                for error in (OSError('permission denied'), subprocess.TimeoutExpired(command, 300)):
                    broken = dict(responses)
                    broken[command] = error
                    with self.subTest(host=host, command=command, error=error), self.assertRaises(ClientRequestError):
                        self.install(host, broken)
                    self.assertEqual(self.process.calls[-1], command)
                    self.assertEqual(self.process.calls.count(command), 1)

    def test_repeated_install_never_reenables_a_disabled_registration(self):
        for host, executable, row in (('claude-code', 'claude', CLAUDE_PLUGIN),
                                      ('github-copilot', 'copilot', COPILOT_PLUGIN)):
            command = (executable, 'plugin', 'list', '--json')
            responses = {command: [copy.deepcopy(row)]}
            with self.subTest(host=host):
                for _ in range(2):
                    self.assertFalse(self.install(host, responses))
                    self.assertEqual(self.process.calls, [command])
                self.assertEqual(responses[command], [row])

    def test_unknown_host_fails_before_lookup_or_process(self):
        with self.assertRaises(InvalidArgumentValueError):
            self.install('other-host', {})
        self.which.assert_not_called()
        self.assertEqual(self.process.calls, [])

    def test_missing_host_has_actionable_prerequisite_error(self):
        self.which.side_effect = None
        self.which.return_value = None
        with self.assertRaisesRegex(ResourceNotFoundError, 'Claude Code.*PATH'):
            self.install('claude-code', {})
        self.assertEqual(self.process.calls, [])


class AzurePluginProcessTest(unittest.TestCase):
    def test_child_receives_literal_arguments_and_closed_stdin(self):
        argv = [sys.executable, '-c',
                'import json, sys; print(json.dumps([sys.argv[1:], sys.stdin.read()]))',
                'spaces and ; shell | characters', '$(not-a-command)']
        result = plugin._run('claude-code', argv, 'test inventory')
        self.assertEqual(json.loads(result.stdout), [argv[3:], ''])

    def test_child_nonzero_keeps_bounded_context(self):
        argv = [sys.executable, '-c',
                'import sys; print("useful stdout"); sys.stderr.write("failure detail " + "x" * 10000); sys.exit(7)']
        with self.assertRaises(ClientRequestError) as caught:
            plugin._run('github-copilot', argv, 'plugin install')
        message = str(caught.exception)
        for part in ('GitHub Copilot CLI', 'plugin install', '7', 'useful stdout', 'failure detail', 'native'):
            self.assertIn(part, message)
        self.assertLess(len(message), 4000)
        self.assertIn('truncated', message)

    def test_child_timeout_is_finite_and_keeps_partial_output(self):
        argv = [sys.executable, '-c', 'import time; print("waiting", flush=True); time.sleep(30)']
        with self.assertRaises(ClientRequestError) as caught:
            plugin._run('codex', argv, 'plugin inventory', timeout=0.2)
        message = str(caught.exception)
        for part in ('Codex CLI', 'plugin inventory', 'timed out', 'waiting', 'native'):
            self.assertIn(part, message)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Real process-group regression uses Linux')
    def test_timeout_and_cancellation_stop_owned_descendant_before_it_can_write(self):
        import psutil

        communicate = subprocess.Popen.communicate
        for cancelled in (False, True):
            for sensitive in (False, True):
                with self.subTest(cancelled=cancelled, sensitive=sensitive), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    ready, gate, marker = (root / name for name in ('ready', 'gate', 'marker'))
                    child = (
                        'import os, pathlib, time; '
                        f'root = pathlib.Path({directory!r}); '
                        '(root / "pid").write_text(str(os.getpid())); (root / "pid").rename(root / "ready"); '
                        '\nwhile not (root / "gate").exists(): time.sleep(0.01)\n'
                        'time.sleep(0.8); (root / "marker").write_text("continued")'
                    )
                    parent = (
                        'import subprocess, sys, time; '
                        f'subprocess.Popen([sys.executable, "-c", {child!r}]); '
                        'print("partial-output-sentinel", flush=True); time.sleep(10)'
                    )
                    owned = []

                    def after_ready(process, *args, **kwargs):
                        if not owned:
                            owned.append(psutil.Process(process.pid))
                            deadline = time.monotonic() + 5
                            while not ready.exists() and time.monotonic() < deadline:
                                time.sleep(0.01)
                            self.assertTrue(ready.exists(), 'Descendant did not start')
                            owned.append(psutil.Process(int(ready.read_text())))
                            gate.touch()
                            if cancelled:
                                raise KeyboardInterrupt()
                        return communicate(process, *args, **kwargs)

                    try:
                        error = KeyboardInterrupt if cancelled else ClientRequestError
                        with mock.patch.object(subprocess.Popen, 'communicate', after_ready):
                            started = time.monotonic()
                            with self.assertRaises(error) as caught:
                                plugin._run('codex', [sys.executable, '-c', parent], 'plugin inventory',
                                            timeout=0.2, sensitive=sensitive)
                            self.assertLess(time.monotonic() - started, 3, 'Cleanup exceeded bounded deadline')
                        time.sleep(1)
                        self.assertFalse(marker.exists(), 'Owned descendant continued after timeout/cancellation')
                        self.assertTrue(all(not proc.is_running() or proc.status() == psutil.STATUS_ZOMBIE
                                            for proc in owned))
                        if not cancelled:
                            message = ''.join(traceback.format_exception(caught.exception))
                            self.assertIn('timed out', message)
                            if sensitive:
                                self.assertNotIn('partial-output-sentinel', message)
                            else:
                                self.assertIn('partial-output-sentinel', message)
                    finally:
                        # Clean up even on the unfixed runner, without killing an unrelated group.
                        for process in reversed(owned):
                            try:
                                process.kill()
                            except psutil.NoSuchProcess:
                                pass
                        psutil.wait_procs(owned, timeout=1)

    def test_windows_timeout_and_cancellation_use_bounded_owned_tree_termination(self):
        for failure in (subprocess.TimeoutExpired(['codex'], 0.2), KeyboardInterrupt()):
            process = mock.Mock(pid=321)
            process.communicate.side_effect = [failure, ('windows partial output', '')]
            with self.subTest(failure=type(failure).__name__), \
                    mock.patch.object(plugin.sys, 'platform', 'win32'), \
                    mock.patch.dict(os.environ, {'SystemRoot': 'C:\\Windows'}), \
                    mock.patch.object(subprocess, 'CREATE_NEW_PROCESS_GROUP', 512, create=True), \
                    mock.patch.object(subprocess, 'Popen', return_value=process) as popen, \
                    mock.patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as taskkill:
                error = KeyboardInterrupt if isinstance(failure, KeyboardInterrupt) else ClientRequestError
                with self.assertRaises(error) as caught:
                    plugin._run('codex', ['codex', 'plugin', 'add', 'azure@azure-skills'], 'plugin install', timeout=0.2)
                if not isinstance(failure, KeyboardInterrupt):
                    self.assertIn('windows partial output', str(caught.exception))
                self.assertEqual(popen.call_args.kwargs['creationflags'], 512)
                self.assertFalse(popen.call_args.kwargs.get('shell', False))
                self.assertEqual(taskkill.call_args.args[0], [
                    os.path.join('C:\\Windows', 'System32', 'taskkill.exe'), '/PID', '321', '/T', '/F'])
                self.assertEqual(taskkill.call_args.kwargs['stdin'], subprocess.DEVNULL)
                self.assertGreater(taskkill.call_args.kwargs['timeout'], 0)
                self.assertLessEqual(taskkill.call_args.kwargs['timeout'], 5)
                self.assertTrue(all(call.kwargs['timeout'] <= 5 for call in process.communicate.call_args_list))

    def test_posix_cancellation_uses_only_the_owned_group_including_on_macos(self):
        for platform in ('linux', 'darwin'):
            process = mock.Mock(pid=321)
            process.communicate.side_effect = [KeyboardInterrupt(), ('', '')]
            with self.subTest(platform=platform), mock.patch.object(plugin.sys, 'platform', platform), \
                    mock.patch.object(subprocess, 'Popen', return_value=process) as popen, \
                    mock.patch.object(os, 'killpg', create=True) as killpg, \
                    mock.patch.object(signal, 'SIGKILL', 9, create=True):
                with self.assertRaises(KeyboardInterrupt):
                    plugin._run('codex', ['codex'], 'plugin install')
                self.assertTrue(popen.call_args.kwargs['start_new_session'])
                killpg.assert_called_once_with(321, signal.SIGKILL)
                process.stdout.close.assert_called_once()
                process.stderr.close.assert_called_once()

    def test_unconfirmed_windows_cleanup_is_bounded_redacted_and_preserves_failure(self):
        for failure in (subprocess.TimeoutExpired(['codex'], 0.2), KeyboardInterrupt()):
            process = mock.Mock(pid=321)
            process.communicate.side_effect = [failure, subprocess.TimeoutExpired(['codex'], 5)]
            process.wait.side_effect = subprocess.TimeoutExpired(['codex'], 5)
            output = io.StringIO()
            with self.subTest(failure=type(failure).__name__), \
                    mock.patch.object(plugin.sys, 'platform', 'win32'), \
                    mock.patch.object(subprocess, 'CREATE_NEW_PROCESS_GROUP', 512, create=True), \
                    mock.patch.object(subprocess, 'Popen', return_value=process), \
                    mock.patch.object(subprocess, 'run', side_effect=OSError('private-cleanup-sentinel')), \
                    mock.patch.dict(os.environ, {'SystemRoot': 'C:\\Windows'}), mock.patch('sys.stderr', output):
                error = KeyboardInterrupt if isinstance(failure, KeyboardInterrupt) else ClientRequestError
                with self.assertRaises(error) as caught:
                    plugin._run('codex', ['codex'], 'plugin inventory', timeout=0.2, sensitive=True)
                self.assertIn('cleanup could not be confirmed', output.getvalue())
                self.assertNotIn('private-cleanup-sentinel', output.getvalue() +
                                 ''.join(traceback.format_exception(caught.exception)))
                process.kill.assert_called_once()
                process.wait.assert_called_once_with(timeout=5)
                process.stdout.close.assert_not_called()
                process.stderr.close.assert_not_called()

    def test_oserror_is_concrete_cli_error(self):
        with mock.patch.object(plugin.subprocess, 'Popen', side_effect=OSError('executable permission denied')):
            with self.assertRaisesRegex(ClientRequestError, 'Claude Code.*plugin inventory.*permission denied'):
                plugin._run('claude-code', ['claude', 'plugin', 'list', '--json'], 'plugin inventory')

    def test_runner_has_no_shell_and_finite_default_timeout(self):
        communicate = subprocess.Popen.communicate
        with mock.patch.object(subprocess.Popen, 'communicate', autospec=True, side_effect=communicate) as exchange, \
                mock.patch.object(plugin.subprocess, 'Popen', wraps=subprocess.Popen) as popen:
            plugin._run('codex', [sys.executable, '-c', 'print("ok")'], 'test inventory')
        kwargs = popen.call_args.kwargs
        self.assertFalse(kwargs.get('shell', False))
        self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
        self.assertGreater(exchange.call_args.kwargs['timeout'], 0)
        self.assertLessEqual(exchange.call_args.kwargs['timeout'], 300)

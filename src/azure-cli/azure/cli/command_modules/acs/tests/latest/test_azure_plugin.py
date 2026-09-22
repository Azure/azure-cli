# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import json
import subprocess
import sys
import traceback
import unittest
from unittest import mock

from azure.cli.command_modules.acs import _azure_plugin as plugin
from azure.cli.core.azclierror import (
    ClientRequestError, InvalidArgumentValueError, ResourceNotFoundError, ValidationError,
)

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
        if isinstance(response, Exception):
            raise response
        if isinstance(response, subprocess.CompletedProcess):
            return response
        stdout = response if isinstance(response, str) else json.dumps(response)
        return subprocess.CompletedProcess(argv, 0, stdout, '')


class AzurePluginNativeTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(plugin.shutil, 'which', side_effect=lambda name: name)
        self.which = patcher.start()
        self.addCleanup(patcher.stop)

    def install(self, host, responses):
        self.process = NativeProcessFixture(responses)
        with mock.patch.object(plugin.subprocess, 'run', side_effect=self.process):
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
        real_run = subprocess.run
        for case, stdout, stderr, ending, error, context in (
                ('invalid JSON', payload[:-1], '', 'sys.exit(0)', ValidationError, 'Invalid native JSON'),
                ('nonzero', payload, stderr_secret, 'sys.exit(7)', ClientRequestError, 'exit 7'),
                ('timeout', payload, stderr_secret, 'time.sleep(30)', ClientRequestError, 'timed out after'),
                ('warning', payload, stderr_secret, 'sys.exit(0)', ValidationError, 'warning')):
            calls = []
            script = (f'import sys, time; print({stdout!r}, flush=True); '
                      f'print({stderr!r}, file=sys.stderr, flush=True); {ending}')

            def run(argv, **kwargs):
                calls.append(tuple(argv))
                if argv == ['copilot', 'plugin', 'list', '--json']:
                    return subprocess.CompletedProcess(argv, 0, '[]', '')
                if argv == ['copilot', 'mcp', 'list', '--json']:
                    kwargs['timeout'] = 0.2 if case == 'timeout' else 5
                    return real_run([sys.executable, '-c', script], **kwargs)
                raise AssertionError('Unexpected native command: ' + repr(argv))

            with self.subTest(case=case):
                with mock.patch.object(plugin.subprocess, 'run', side_effect=run), self.assertRaises(error) as caught:
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

    def test_inventory_warning_never_becomes_absence(self):
        command = ('copilot', 'plugin', 'list', '--json')
        response = subprocess.CompletedProcess(command, 0, '[]', 'Configuration could not be loaded')
        with self.assertRaisesRegex(ValidationError, 'Configuration could not be loaded'):
            self.install('github-copilot', {command: response})
        self.assertEqual(self.mutations(), [])

    def test_command_failure_never_retries_or_falls_through(self):
        for host in ('claude-code', 'github-copilot', 'codex'):
            responses = self.fresh_responses(host, [])
            commands = [command for command in responses if command[0] != 'node']
            for command in commands:
                broken = dict(responses)
                broken[command] = subprocess.CompletedProcess(command, 2, '', 'unsupported flag or policy refusal')
                context = 'exit 2' if command[1] == 'mcp' else 'policy refusal'
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

    def test_oserror_is_concrete_cli_error(self):
        with mock.patch.object(plugin.subprocess, 'run', side_effect=OSError('executable permission denied')):
            with self.assertRaisesRegex(ClientRequestError, 'Claude Code.*plugin inventory.*permission denied'):
                plugin._run('claude-code', ['claude', 'plugin', 'list', '--json'], 'plugin inventory')

    def test_runner_has_no_shell_and_finite_default_timeout(self):
        with mock.patch.object(plugin.subprocess, 'run', wraps=subprocess.run) as run:
            plugin._run('codex', [sys.executable, '-c', 'print("ok")'], 'test inventory')
        kwargs = run.call_args.kwargs
        self.assertFalse(kwargs.get('shell', False))
        self.assertEqual(kwargs['stdin'], subprocess.DEVNULL)
        self.assertGreater(kwargs['timeout'], 0)
        self.assertLessEqual(kwargs['timeout'], 300)


class AzurePluginDiscoveryTest(unittest.TestCase):
    def test_discovery_only_checks_executable_presence(self):
        with mock.patch.object(plugin.shutil, 'which', side_effect=lambda name: '/bin/' + name if name == 'codex' else None), \
                mock.patch('subprocess.run', side_effect=AssertionError('Discovery must not execute a host')):
            self.assertEqual(plugin.discover_hosts(), ['codex'])

    def test_discovery_uses_stable_host_order(self):
        with mock.patch.object(plugin.shutil, 'which', side_effect=lambda name: '/bin/' + name):
            self.assertEqual(plugin.discover_hosts(), ['claude-code', 'github-copilot', 'codex'])

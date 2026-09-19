# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import importlib
import io
import logging
import os
import shutil
import socket
import ssl
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from contextlib import ExitStack, contextmanager
from email.message import Message
from http.client import HTTPSConnection
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request
from urllib.response import addinfourl

from knack.prompting import NoTTYException
from knack.util import CLIError
from azure.cli.command_modules.acs import _azure_skills as skills
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)


_SKILL = '---\nname: demo\ndescription: Test skill\n---\nInstructions\n'
_LICENSE = b'MIT License\nTest fixture copyright\n'
_PAYLOAD = 'bundle/.github/plugins/azure-skills/skills/'


def make_bundle(path, files=None, extra=(), license_content=_LICENSE, compression=zipfile.ZIP_DEFLATED):
    if files is None:
        files = {
            'demo/SKILL.md': _SKILL,
            'demo/references/guide.md': b'Reference content\n',
            'demo/child/SKILL.md': '---\nname: child\ndescription: Nested skill\n---\n',
        }
    with zipfile.ZipFile(path, 'w', compression) as archive:
        if license_content is not None:
            archive.writestr('bundle/LICENSE', license_content)
        for relative, content in files.items():
            archive.writestr(_PAYLOAD + relative, content)
        archive.writestr('bundle/.github/plugins/azure-skills/.mcp.json', '{}')
        archive.writestr('bundle/.github/plugins/azure-skills/hooks/hooks.json', '{}')
        for member, content in extra:
            archive.writestr(member, content)


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.patches = ExitStack()
        self.addCleanup(self.patches.close)
        self.root = Path(self.patches.enter_context(tempfile.TemporaryDirectory()))
        self.cmd = mock.Mock()
        self.cmd.cli_ctx.config.getboolean.return_value = False
        self.targets = [
            skills.AgentTarget('claude-code', 'Claude Code', self.root / 'claude/skills', True),
            skills.AgentTarget('codex', 'Codex', self.root / 'shared/skills', True),
            skills.AgentTarget('github-copilot', 'GitHub Copilot', self.root / 'copilot/skills', False),
            skills.AgentTarget('pi', 'Pi', self.root / 'pi/skills', True),
        ]
        self.discover = self.patches.enter_context(mock.patch.object(
            skills, 'discover_agents', return_value=self.targets))
        self.sudo = self.patches.enter_context(mock.patch.object(skills, '_is_sudo', return_value=False))
        self.tty = self.patches.enter_context(mock.patch.object(sys.stdin, 'isatty', return_value=True))
        self.input = self.patches.enter_context(mock.patch('knack.prompting._input', side_effect=['y', '4', 'y']))
        self.output = self.patches.enter_context(mock.patch('sys.stdout', new_callable=io.StringIO))
        self.release = skills.Release('v1.2.3', 'a' * 40)
        self.resolve = self.patches.enter_context(mock.patch.object(skills, 'resolve_release',
                                                                  return_value=self.release))
        self.archives = []

        def download(release, destination):
            self.archives.append(destination)
            make_bundle(destination)

        self.download = self.patches.enter_context(mock.patch.object(skills, 'download_archive', side_effect=download))
        self.publish = self.patches.enter_context(mock.patch.object(skills, 'publish_skills', wraps=skills.publish_skills))

    def assert_no_skill_work(self):
        self.discover.assert_not_called()
        self.resolve.assert_not_called()
        self.input.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_noninteractive_default_does_no_skill_work(self):
        self.tty.return_value = False
        skills.maybe_install_azure_skills(self.cmd)
        self.assert_no_skill_work()

    def test_false_does_no_skill_work(self):
        skills.maybe_install_azure_skills(self.cmd, False)
        self.assert_no_skill_work()
        self.tty.assert_not_called()
        self.cmd.cli_ctx.config.getboolean.assert_not_called()

    def test_disabled_confirmations_are_not_consent(self):
        self.cmd.cli_ctx.config.getboolean.return_value = True
        skills.maybe_install_azure_skills(self.cmd)
        self.assert_no_skill_work()
        self.cmd.cli_ctx.config.getboolean.assert_called_once_with('core', 'disable_confirm_prompt', fallback=False)

    def test_sudo_skips_with_unprivileged_binary_location_guidance(self):
        self.sudo.return_value = True
        with self.assertLogs(skills.logger, level='WARNING') as logs:
            skills.maybe_install_azure_skills(self.cmd)
        self.assert_no_skill_work()
        self.assertIn('unprivileged', '\n'.join(logs.output))
        self.assertIn('user-writable binary', '\n'.join(logs.output))

    def test_first_enter_defaults_to_no_before_discovery(self):
        self.input.side_effect = ['']
        skills.maybe_install_azure_skills(self.cmd)
        self.discover.assert_not_called()
        self.resolve.assert_not_called()
        self.assertIn('(y/N)', self.input.call_args.args[0])

    def test_invalid_input_reprompts_then_replaces_detected_defaults(self):
        self.input.side_effect = ['y', '1,9', '3,3', 'y']
        with self.assertLogs(skills.logger, level='WARNING') as logs:
            skills.maybe_install_azure_skills(self.cmd)
        self.assertEqual(self.input.call_count, 4)
        self.assertIn('1-4', '\n'.join(logs.output))
        self.assertIn('1,2,4', self.input.call_args_list[1].args[0])
        self.assertIn('1. Claude Code', self.output.getvalue())
        self.assertIn('not detected', self.output.getvalue())
        self.assertEqual(list(self.root.glob('*/skills/demo')), [self.root / 'copilot/skills/demo'])
        self.assertFalse(self.archives[0].parent.exists())

    def test_enter_keeps_detected_agents_and_codex_discloses_shared_visibility(self):
        self.input.side_effect = ['y', '', 'y']
        with self.assertLogs(skills.logger, level='WARNING'):
            skills.maybe_install_azure_skills(self.cmd)
        text = self.output.getvalue()
        for label in ('Claude Code', 'Codex', 'Pi', 'GitHub Copilot', 'MCP', 'hooks', 'user-level'):
            self.assertIn(label, text)
        self.assertIn('even when', text)
        self.assertEqual(len(list(self.root.glob('*/skills/demo'))), 3)
        self.assertFalse((self.root / 'copilot').exists())

    def test_no_detected_agents_and_empty_input_skips(self):
        self.discover.return_value = [skills.AgentTarget(t.identifier, t.label, t.destination, False)
                                      for t in self.targets]
        self.input.side_effect = ['y', '']
        skills.maybe_install_azure_skills(self.cmd)
        self.resolve.assert_not_called()
        self.assertEqual(self.input.call_count, 2)

    def test_none_skips_detected_defaults(self):
        self.input.side_effect = ['y', 'none']
        skills.maybe_install_azure_skills(self.cmd)
        self.resolve.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_final_enter_defaults_to_no_without_retrieval_or_writes(self):
        self.input.side_effect = ['y', '4', '']
        skills.maybe_install_azure_skills(self.cmd)
        self.resolve.assert_not_called()
        self.assertIn('(y/N)', self.input.call_args.args[0])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_prompt_cancellation_at_each_stage_keeps_binary_success(self):
        for error in (NoTTYException, EOFError, KeyboardInterrupt):
            for answers in ([], ['y'], ['y', '4']):
                with self.subTest(error=error, answers=answers):
                    self.input.side_effect = answers + [error()]
                    with self.assertLogs(skills.logger, level='WARNING') as logs:
                        skills.maybe_install_azure_skills(self.cmd)
                    self.assertIn('cancelled', '\n'.join(logs.output))
                    self.assertIn('kubectl and kubelogin', '\n'.join(logs.output))
                    self.resolve.assert_not_called()
                    self.assertEqual(list(self.root.iterdir()), [])

    def test_explicit_selection_ignores_detection_and_prompt_suppression_without_revalidation(self):
        self.cmd.cli_ctx.config.getboolean.return_value = True
        with mock.patch.object(skills, 'validate_skills_options', side_effect=AssertionError('preflight repeated')):
            skills.maybe_install_azure_skills(self.cmd, True, ['github-copilot', 'github-copilot'])
        self.input.assert_not_called()
        self.assertEqual(list(self.root.glob('*/skills/demo')), [self.root / 'copilot/skills/demo'])
        self.assertEqual(len(self.publish.call_args.args[1]), 1)

    def test_source_and_token_propagation_and_source_before_publication(self):
        def publish(trees, targets):
            self.assertTrue(any('microsoft/azure-skills' in line and self.release.commit in line
                                for line in logs.output))
            return skills.InstallReport(installed=[targets[0].destination / trees[0].name])

        self.publish.side_effect = publish
        with self.assertLogs(skills.logger, level='WARNING') as logs:
            skills.maybe_install_azure_skills(self.cmd, True, ['pi'], 'secret-token')
        self.resolve.assert_called_once_with('secret-token')
        self.download.assert_called_once_with(self.release, self.archives[0])
        text = '\n'.join(logs.output)
        self.assertNotIn('secret-token', text)
        self.assertGreaterEqual(text.count(self.release.commit), 2)
        self.assertIn(self.release.tag, text)

    def test_duplicate_destinations_are_published_once(self):
        self.discover.return_value = [skills.AgentTarget(t.identifier, t.label, self.root / 'skills', t.detected)
                                      for t in self.targets]
        with self.assertLogs(skills.logger, level='WARNING') as logs:
            skills.maybe_install_azure_skills(self.cmd, True, ['pi', 'claude-code', 'pi'])
        text = '\n'.join(logs.output)
        self.assertIn('Claude Code', text)
        self.assertIn('Pi', text)
        self.assertIn('Installed (1)', text)
        self.assertIn('Already present (0)', text)
        self.assertEqual((self.root / 'skills/demo/SKILL.md').read_text(), _SKILL)

    @unittest.skipUnless(os.name == 'posix', 'Symlink safety with lexical parent traversal')
    def test_wrapper_preserves_unsafe_lexical_path_even_when_normalized_destination_duplicates(self):
        (self.root / 'outside').mkdir()
        (self.root / 'link').symlink_to(self.root / 'outside', target_is_directory=True)
        self.discover.return_value = [
            skills.AgentTarget('claude-code', 'Claude Code', self.root / 'skills', True),
            skills.AgentTarget('pi', 'Pi', self.root / 'link/../skills', True),
        ]
        with self.assertRaisesRegex(CLIError, 'symlink|reparse'):
            skills.maybe_install_azure_skills(self.cmd, True, ['claude-code', 'pi'])
        self.assertTrue((self.root / 'skills/demo/SKILL.md').exists())
        self.assertEqual(self.publish.call_args.args[1][1].destination, self.root / 'link/../skills')

    def test_known_errors_optional_warn_explicit_raise_with_source_and_retry_guidance(self):
        for explicit in (False, True):
            for phase in ('resolve', 'download', 'stage'):
                with self.subTest(explicit=explicit, phase=phase), ExitStack() as patches:
                    self.input.side_effect = ['y', '4', 'y']
                    operation = {'resolve': 'resolve_release', 'download': 'download_archive',
                                 'stage': 'stage_bundle'}[phase]
                    patches.enter_context(mock.patch.object(skills, operation, side_effect=CLIError('test failure')))
                    with self.assertLogs(skills.logger, level='WARNING') as logs:
                        if explicit:
                            with self.assertRaisesRegex(CLIError, 'kubectl and kubelogin') as error:
                                skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
                            text = str(error.exception)
                        else:
                            skills.maybe_install_azure_skills(self.cmd)
                            text = '\n'.join(logs.output)
                    for expected in ('test failure', 'retry', 'release may have changed', 'binary installation'):
                        self.assertIn(expected, text)
                    if phase != 'resolve':
                        self.assertIn(self.release.tag, text)
                        self.assertIn(self.release.commit, text)
                    self.assertFalse(any(path.parent.exists() for path in self.archives))
                    self.assertEqual(list(self.root.iterdir()), [])

    def test_discovery_failure_does_not_suggest_an_empty_agent_list(self):
        self.discover.side_effect = OSError('cannot inspect agent directories')
        with self.assertLogs(skills.logger, level='WARNING') as logs:
            skills.maybe_install_azure_skills(self.cmd)
        text = '\n'.join(logs.output)
        self.assertIn('cannot inspect agent directories', text)
        self.assertIn('--skills-agents <selected agents>', text)
        self.resolve.assert_not_called()

    def test_temporary_filesystem_error_is_contextual_not_programming_error(self):
        with mock.patch.object(skills.tempfile, 'TemporaryDirectory', side_effect=PermissionError('denied')):
            with self.assertRaisesRegex(CLIError, 'permissions|denied'):
                skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
        with mock.patch.object(skills, 'resolve_release', side_effect=TypeError('bug')):
            with self.assertRaisesRegex(TypeError, 'bug'):
                skills.maybe_install_azure_skills(self.cmd, True, ['pi'])

    def test_all_outcomes_and_manual_recovery_explicit_raises_optional_warns(self):
        installed = self.root / 'pi/skills/installed'
        present = self.root / 'pi/skills/present'
        conflict = self.root / 'pi/skills/conflict'
        failed = self.root / 'pi/skills/failed'
        self.publish.side_effect = lambda *args: skills.InstallReport(
            installed=[installed], already_present=[present], conflicts=[conflict],
            failures=[(failed, 'Permission denied')])
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                self.input.side_effect = ['y', '4', 'y']
                with self.assertLogs(skills.logger, level='WARNING') as logs:
                    if explicit:
                        with self.assertRaisesRegex(CLIError, 'incomplete'):
                            skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
                    else:
                        skills.maybe_install_azure_skills(self.cmd)
                text = '\n'.join(logs.output)
                for expected in ('Installed (1)', 'Already present (1)', 'Skipped/conflicting (1)', 'Failed (1)',
                                 str(installed), str(present), str(conflict), str(failed), 'Permission denied',
                                 'user modifications', 'outside all agent skill discovery paths',
                                 'other Azure skill directories', 'unrelated skills', 'shared',
                                 '--install-azure-skills true --skills-agents pi', 'binary installation',
                                 'release may have changed', 'backups', self.release.tag, self.release.commit):
                    self.assertIn(expected, text)
                self.assertNotIn('installation complete', text)

    def test_release_advance_keeps_existing_content_and_reports_conflict_path_in_explicit_error(self):
        with self.assertLogs(skills.logger, level='WARNING'):
            skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
        destination = self.root / 'pi/skills/demo'
        self.resolve.return_value = skills.Release('v2.0.0', 'b' * 40)
        self.download.side_effect = lambda release, path: make_bundle(
            path, {'demo/SKILL.md': _SKILL + 'Changed upstream instructions\n'})
        with self.assertLogs(skills.logger, level='WARNING') as logs:
            with self.assertRaises(CLIError) as error:
                skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
        self.assertEqual((destination / 'SKILL.md').read_text(), _SKILL)
        self.assertIn(str(destination), str(error.exception))
        self.assertIn('v2.0.0', str(error.exception))
        self.assertIn('b' * 40, str(error.exception))
        self.assertNotIn('a' * 40, '\n'.join(logs.output))
        self.assertIn('mixed-version', str(error.exception))
        self.assertIn('release may have changed', str(error.exception))

    def test_cleanup_error_does_not_hide_partial_publication_or_cancellation(self):
        real_temporary = tempfile.TemporaryDirectory

        @contextmanager
        def cleanup_error(**kwargs):
            with real_temporary(**kwargs) as directory:
                yield directory
            raise PermissionError('temporary cleanup denied')

        self.publish.side_effect = lambda *args: skills.InstallReport(
            installed=[self.root / 'pi/skills/first'],
            failures=[(self.root / 'pi/skills/second', 'publication cancelled; earlier installations remain')])
        with mock.patch.object(skills.tempfile, 'TemporaryDirectory', cleanup_error):
            with self.assertLogs(skills.logger, level='WARNING') as logs, self.assertRaises(CLIError) as error:
                skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
        self.assertIn('cancelled', str(error.exception))
        self.assertIn('temporary cleanup denied', str(error.exception))
        self.assertIn(str(self.root / 'pi/skills/first'), '\n'.join(logs.output))
        self.assertFalse(any(path.parent.exists() for path in self.archives))

    def test_retrieval_interrupt_cleans_up_and_has_mode_specific_status(self):
        def interrupted(release, destination):
            self.archives.append(destination)
            destination.write_bytes(b'partial')
            raise KeyboardInterrupt()

        self.download.side_effect = interrupted
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                self.input.side_effect = ['y', '4', 'y']
                with self.assertLogs(skills.logger, level='WARNING') as logs:
                    if explicit:
                        with self.assertRaisesRegex(CLIError, 'cancelled') as error:
                            skills.maybe_install_azure_skills(self.cmd, True, ['pi'])
                        self.assertIn(self.release.commit, str(error.exception))
                    else:
                        skills.maybe_install_azure_skills(self.cmd)
                text = '\n'.join(logs.output)
                self.assertIn('no skills were published', text)
                self.assertIn('kubectl and kubelogin', text)
                self.publish.assert_not_called()
                self.assertFalse(any(path.parent.exists() for path in self.archives))

    def test_publication_interrupt_keeps_completed_files_reports_partial_and_cleans_temporary_state(self):
        original_publish_one = skills._publish_one

        def interrupt_second(source, destination):
            if destination.parent == self.root / 'pi/skills':
                raise KeyboardInterrupt()
            return original_publish_one(source, destination)

        with mock.patch.object(skills, '_publish_one', side_effect=interrupt_second):
            for explicit in (False, True):
                with self.subTest(explicit=explicit):
                    self.input.side_effect = ['y', '1,4', 'y']
                    with self.assertLogs(skills.logger, level='WARNING') as logs:
                        if explicit:
                            with self.assertRaisesRegex(CLIError, 'cancelled'):
                                skills.maybe_install_azure_skills(self.cmd, True, ['claude-code', 'pi'])
                        else:
                            skills.maybe_install_azure_skills(self.cmd)
                    text = '\n'.join(logs.output)
                    self.assertIn('earlier installations remain', text)
                    self.assertNotIn('installation complete', text)
                    self.assertEqual((self.root / 'claude/skills/demo/SKILL.md').read_text(), _SKILL)
                    self.assertFalse((self.root / 'pi/skills/demo').exists())
                    self.assertFalse(any(path.parent.exists() for path in self.archives))


class ConsoleConsentTests(unittest.TestCase):
    @contextmanager
    def console(self, mode, answers=''):
        from knack.cli import CLI
        from knack.log import CliLogLevel, cli_logger_names

        with ExitStack() as patches:
            home = Path(patches.enter_context(tempfile.TemporaryDirectory()))
            config = home / '.azure'
            config.mkdir()
            (config / 'config').write_text(
                f'[core]\nonly_show_errors = {mode == "config"}\n', encoding='utf-8')
            patches.enter_context(mock.patch.dict(os.environ, {
                'HOME': str(home), 'USERPROFILE': str(home), 'AZURE_CONFIG_DIR': str(config),
                'CLAUDE_CONFIG_DIR': str(home / 'custom-claude'),
                'PI_CODING_AGENT_DIR': str(home / 'custom-pi'),
            }, clear=True))
            output = io.StringIO()
            patches.enter_context(mock.patch('sys.stdout', output))
            patches.enter_context(mock.patch('sys.stderr', output))
            stdin = io.StringIO(answers)
            patches.enter_context(mock.patch('sys.stdin', stdin))
            patches.enter_context(mock.patch.object(stdin, 'isatty', return_value=True))
            # Exercise Knack's actual console filtering without retaining global logging changes.
            loggers = [logging.getLogger(name) for name in ['', *cli_logger_names]] + [skills.logger]
            for logger in loggers:
                for attribute, value in (('handlers', []), ('level', logging.NOTSET),
                                         ('propagate', True), ('disabled', False)):
                    patches.enter_context(mock.patch.object(logger, attribute, value))
            cli = CLI(cli_name='az', config_dir=str(config), config_env_var_prefix='AZURE')
            cli.logging.configure(['--only-show-errors'] if mode == 'flag' else [])
            if mode != 'default':
                self.assertEqual(cli.logging.log_level, CliLogLevel.ERROR)
                skills.logger.warning('Ordinary warnings must remain suppressed')
                self.assertEqual(output.getvalue(), '')
            resolve = patches.enter_context(mock.patch.object(
                skills, 'resolve_release', side_effect=CLIError('offline test boundary')))
            download = patches.enter_context(mock.patch.object(skills, 'download_archive'))
            publish = patches.enter_context(mock.patch.object(skills, 'publish_skills'))
            before = sorted(home.rglob('*'))
            yield mock.Mock(cli_ctx=cli), output, home, resolve
            download.assert_not_called()
            publish.assert_not_called()
            self.assertEqual(sorted(home.rglob('*')), before)

    def test_interactive_consent_survives_only_show_errors_before_final_confirmation(self):
        for mode in ('flag', 'config'):
            with self.subTest(mode=mode), self.console(mode, 'y\n1,2,4\nn\n') as (cmd, output, home, resolve):
                skills.maybe_install_azure_skills(cmd)
                text = output.getvalue()
                confirmation = 'Install Azure skills at these destinations? (y/N): '
                self.assertIn(confirmation, text)
                before_confirmation = text.split(confirmation)[0]
                for destination in (home / 'custom-claude/skills', home / '.agents/skills',
                                    home / 'custom-pi/skills'):
                    self.assertIn(str(destination), before_confirmation)
                for disclosure in ('user-level Azure skills only', 'no MCP configuration, hooks, or agent applications',
                                   'tools configured separately', 'shared ~/.agents/skills',
                                   'Pi and GitHub Copilot even when they are not selected',
                                   'Selection controls destinations, not agent enable/disable configuration'):
                    self.assertIn(disclosure, before_confirmation)
                self.assertNotIn(str(home / '.copilot/skills'), text)
                resolve.assert_not_called()

    def test_explicit_selection_keeps_suppressible_logging_without_prompts(self):
        for mode in ('default', 'flag', 'config'):
            with self.subTest(mode=mode), self.console(mode) as (cmd, output, home, resolve):
                with self.assertRaisesRegex(CLIError, 'offline test boundary'):
                    skills.maybe_install_azure_skills(cmd, True, ['codex'])
                resolve.assert_called_once_with(None)
                text = output.getvalue()
                self.assertNotIn('(y/N)', text)
                self.assertNotIn('Select agents:', text)
                if mode == 'default':
                    for disclosure in (str(home / '.agents/skills'), 'no MCP configuration, hooks',
                                       'even when they are not selected', 'offline test boundary'):
                        self.assertIn(disclosure, text)
                else:
                    self.assertEqual(text, '')

    def test_skipped_offers_do_not_emit_consent_disclosures(self):
        for mode in ('flag', 'config'):
            for reason in ('false', 'no-tty', 'disabled', 'declined', 'none'):
                with self.subTest(mode=mode, reason=reason), \
                        self.console(mode, 'y\nnone\n' if reason == 'none' else 'n\n') as (cmd, output, home, resolve):
                    if reason == 'disabled':
                        cmd.cli_ctx.config.set_value('core', 'disable_confirm_prompt', 'true')
                    with mock.patch.object(sys.stdin, 'isatty', return_value=reason != 'no-tty'):
                        skills.maybe_install_azure_skills(cmd, False if reason == 'false' else None)
                    text = output.getvalue()
                    for disclosure in ('user-level Azure skills only', 'no MCP', 'shared ~/.agents/skills',
                                       'Install Azure skills at these destinations?', str(home / '.agents/skills')):
                        self.assertNotIn(disclosure, text)
                    if reason in ('false', 'no-tty', 'disabled'):
                        self.assertEqual(text, '')
                    resolve.assert_not_called()


class CliArgumentTests(unittest.TestCase):
    def invoke(self, arguments):
        from azure.cli.core import get_default_cli
        with tempfile.TemporaryDirectory() as config, \
                mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': config}), \
                mock.patch('azure.cli.command_modules.acs.custom.k8s_install_cli',
                           autospec=True, return_value=None) as handler:
            try:
                result = get_default_cli().invoke(['aks', 'install-cli'] + arguments)
            except SystemExit as error:
                result = error.code
            return result, handler

    def test_three_state_flag_and_agent_list(self):
        cases = [(['--install-azure-skills', '--skills-agents', 'pi', 'codex'], True),
                 (['--install-azure-skills', 'true', '--skills-agents', 'pi', 'codex'], True),
                 (['--install-azure-skills', 'false'], False), ([], None)]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                result, handler = self.invoke(arguments)
                self.assertEqual(result, 0)
                self.assertIs(handler.call_args.kwargs['install_azure_skills'], expected)
                self.assertEqual(handler.call_args.kwargs['skills_agents'], ['pi', 'codex'] if expected else None)

    def test_invalid_agent_is_rejected_by_parser(self):
        with mock.patch('sys.stderr', new_callable=io.StringIO) as output:
            result, handler = self.invoke(['--install-azure-skills', '--skills-agents', 'unknown'])
        self.assertEqual(result, 2)
        self.assertIn("'unknown' is not a valid value for '--skills-agents'", output.getvalue())
        handler.assert_not_called()

    def test_source_overlay_help_explains_optional_scope_and_retry_limitations(self):
        with tempfile.TemporaryDirectory() as config:
            result = subprocess.run([sys.executable, '-B', '-m', 'azure.cli', 'aks', 'install-cli', '--help'],
                                    env=dict(os.environ, AZURE_CONFIG_DIR=config),
                                    text=True, capture_output=True, check=True)
        help_text = ' '.join(result.stdout.split())
        for expected in ('--install-azure-skills', '--skills-agents', 'Azure skills release', 'kubelogin',
                         'MCP', 'hooks', 'user-level', 'sudo', 'noninteractive', 'Codex', 'Pi', 'Copilot',
                         'first-install-only', 'binary installation', 'latest release'):
            self.assertIn(expected, help_text)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.archive = self.root / 'bundle.zip'
        self.staging = self.root / 'staged'

    def assert_rejected(self, message=None):
        with self.assertRaisesRegex(CLIError, message or '.'):
            skills.stage_bundle(self.archive, self.staging)
        self.assertFalse(self.staging.exists())
        self.assertTrue(self.archive.is_file(), 'Keep caller-owned archive for diagnostics')
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ['bundle.zip'])

    def test_preserves_nested_resources_and_license_not_plugin_config(self):
        make_bundle(self.archive)
        trees = skills.stage_bundle(self.archive, self.staging)
        self.assertEqual(trees, [self.staging / 'demo'])
        self.assertEqual((trees[0] / 'references/guide.md').read_bytes(), b'Reference content\n')
        self.assertEqual((trees[0] / 'SKILL.md').read_bytes(), _SKILL.encode())
        self.assertEqual((trees[0] / 'child/SKILL.md').read_bytes(),
                         b'---\nname: child\ndescription: Nested skill\n---\n')
        self.assertEqual((trees[0] / 'LICENSE.azure-skills').read_bytes(), _LICENSE)
        self.assertEqual(sorted(path.relative_to(self.staging).as_posix() for path in self.staging.rglob('*')
                                if path.is_file()),
                         ['demo/LICENSE.azure-skills', 'demo/SKILL.md', 'demo/child/SKILL.md',
                          'demo/references/guide.md'])

    def test_preserves_nested_onboarding_guides_without_frontmatter_byte_for_byte(self):
        guide = b'# Deploy\r\n\r\nChild supporting guide; not directly user-routable.\r\n'
        make_bundle(self.archive, {
            'azure-app-onboard/SKILL.md': _SKILL,
            'azure-app-onboard/deploy/SKILL.md': guide,
            'azure-app-onboard/prepare/steps/SKILL.md': guide,
        })
        trees = skills.stage_bundle(self.archive, self.staging)
        self.assertEqual(trees, [self.staging / 'azure-app-onboard'])
        self.assertEqual((trees[0] / 'deploy/SKILL.md').read_bytes(), guide)
        self.assertEqual((trees[0] / 'prepare/steps/SKILL.md').read_bytes(), guide)
        self.assertEqual((trees[0] / 'SKILL.md').read_bytes(), _SKILL.encode())
        self.assertEqual((trees[0] / 'LICENSE.azure-skills').read_bytes(), _LICENSE)

    def test_returns_sorted_top_level_trees_without_renaming(self):
        make_bundle(self.archive, {'zebra/SKILL.md': _SKILL, 'Alpha/SKILL.md': _SKILL})
        trees = skills.stage_bundle(self.archive, self.staging)
        self.assertEqual(trees, [self.staging / 'Alpha', self.staging / 'zebra'])
        for tree in trees:
            self.assertEqual((tree / 'LICENSE.azure-skills').read_bytes(), _LICENSE)

    def test_preserves_binary_resources_and_explicit_empty_directories(self):
        make_bundle(self.archive, {'demo/SKILL.md': _SKILL, 'demo/data.bin': bytes(range(256)),
                                   'demo/empty/': b''},
                    extra=[('bundle/', b''), (_PAYLOAD, b''), (_PAYLOAD + 'demo/', b'')])
        skills.stage_bundle(self.archive, self.staging)
        self.assertEqual((self.staging / 'demo/data.bin').read_bytes(), bytes(range(256)))
        self.assertTrue((self.staging / 'demo/empty').is_dir())

    def test_rejects_unsafe_raw_paths_even_outside_payload_before_writes(self):
        paths = ['../escape', '/absolute', '//server/share', 'C:/drive', 'C:relative',
                 'bundle/back\\slash', 'bundle/alternate:stream', 'bundle//empty',
                 'bundle/./dot', 'bundle/../escape', 'bundle/trailing.', 'bundle/trailing ',
                 'bundle/CON', 'bundle/con.txt', 'bundle/PRN', 'bundle/AUX.md', 'bundle/nul',
                 'bundle/COM1.log', 'bundle/lpt9.txt', 'bundle/COM¹', 'bundle/con .txt',
                 'bundle/bad?', 'bundle/bad*', 'bundle/bad|', 'bundle/bad<', 'bundle/bad>',
                 'bundle/bad"', 'bundle/control\x01', 'bundle/dir//', _PAYLOAD + 'demo/../../escape']
        for path in paths:
            with self.subTest(path=path):
                make_bundle(self.archive, extra=[(path, b'unsafe')])
                with mock.patch.object(Path, 'mkdir', side_effect=AssertionError('Validation must precede writes')):
                    self.assert_rejected()

    def test_rejects_trailing_backslash_even_when_zipfile_recognizes_it_as_directory(self):
        make_bundle(self.archive, extra=[('bundle/backslash\\', b'')])
        # ZipInfo also recognizes the native separator as a directory suffix on Windows.
        with mock.patch.object(zipfile.ZipInfo, 'is_dir', lambda member: member.filename.endswith(('/', '\\'))):
            self.assert_rejected()

    def test_rejects_nul_in_original_zip_name(self):
        make_bundle(self.archive, extra=[('bundle/nulXname', b'unsafe')])
        self.archive.write_bytes(self.archive.read_bytes().replace(b'nulXname', b'nul\x00name'))
        self.assert_rejected()

    def test_rejects_multiple_roots_or_file_root(self):
        for extra in ([('other/readme', b'outside')], [('bundle', b'file')]):
            with self.subTest(extra=extra):
                make_bundle(self.archive, extra=extra)
                self.assert_rejected()

    def test_rejects_duplicate_members(self):
        with self.assertWarns(UserWarning):
            make_bundle(self.archive, extra=[(_PAYLOAD + 'demo/SKILL.md', _SKILL)])
        self.assert_rejected()

    def test_rejects_case_and_unicode_collisions_including_implicit_ancestors(self):
        for first, second in [('Guide.md', 'guide.md'), ('café.txt', 'cafe\u0301.txt'),
                              ('Straße.txt', 'STRASSE.txt'), ('Docs/one', 'docs/two'),
                              ('café/one', 'cafe\u0301/two'),
                              ('a\u0345\u0300.txt', 'a\u0300\u0345.txt')]:
            with self.subTest(first=first, second=second):
                make_bundle(self.archive, extra=[(_PAYLOAD + 'demo/' + first, b'one'),
                                                (_PAYLOAD + 'demo/' + second, b'two')])
                self.assert_rejected()

    def test_rejects_file_directory_collisions_in_either_order(self):
        for first, second in [('resource', 'resource/child'), ('resource/child', 'resource'),
                              ('resource', 'resource/'), ('resource/', 'resource')]:
            with self.subTest(first=first, second=second):
                make_bundle(self.archive, extra=[(_PAYLOAD + 'demo/' + first, b''),
                                                (_PAYLOAD + 'demo/' + second, b'')])
                self.assert_rejected()

    def test_rejects_symlinks_special_files_and_inconsistent_directory_modes(self):
        for mode, suffix in [(stat.S_IFLNK, ''), (stat.S_IFIFO, ''), (stat.S_IFSOCK, ''),
                             (stat.S_IFBLK, ''), (stat.S_IFCHR, ''),
                             (stat.S_IFDIR, ''), (stat.S_IFREG, '/')]:
            with self.subTest(mode=mode, suffix=suffix):
                member = zipfile.ZipInfo('bundle/special' + suffix)
                member.create_system = 3
                member.external_attr = (mode | 0o777) << 16
                make_bundle(self.archive, extra=[(member, b'')])
                self.assert_rejected()

    def test_rejects_directories_with_advertised_content(self):
        make_bundle(self.archive, extra=[('bundle/directory/', b'not empty')])
        self.assert_rejected()

    def test_rejects_encrypted_entries_including_excluded_files(self):
        for name in ('bundle/LICENSE', 'bundle/.github/plugins/azure-skills/hooks/hooks.json'):
            for flag in (1, 64):
                with self.subTest(name=name, flag=flag):
                    make_bundle(self.archive)
                    data = bytearray(self.archive.read_bytes())
                    central = data.index(b'PK\x01\x02')
                    offset = data.index(name.encode(), central) - 46
                    flags = struct.unpack_from('<H', data, offset + 8)[0]
                    struct.pack_into('<H', data, offset + 8, flags | flag)
                    self.archive.write_bytes(data)
                    self.assert_rejected('encrypt')

    def test_rejects_entry_depth_and_advertised_size_budgets_before_writes(self):
        cases = [('ENTRY_LIMIT', 5), ('PATH_DEPTH_LIMIT', 7), ('EXPANDED_LIMIT', 10),
                 ('FILE_LIMIT', 10), ('ARCHIVE_LIMIT', 10)]
        for constant, limit in cases:
            with self.subTest(constant=constant):
                make_bundle(self.archive)
                with mock.patch.object(skills, constant, limit, create=True), \
                        mock.patch.object(Path, 'mkdir', side_effect=AssertionError('Validate budgets first')):
                    self.assert_rejected('limit')

    def test_advertised_aggregate_budget_includes_excluded_files(self):
        make_bundle(self.archive, extra=[('bundle/not-installed', b'x' * 1000)])
        with mock.patch.object(skills, 'EXPANDED_LIMIT', 500, create=True):
            self.assert_rejected('limit')

    def test_accepts_exact_entry_depth_file_and_advertised_total_limits(self):
        make_bundle(self.archive, {'demo/SKILL.md': _SKILL}, license_content=b'MIT')
        # Four entries, maximum seven path components, 63 advertised expanded bytes.
        with mock.patch.object(skills, 'ENTRY_LIMIT', 4, create=True), \
                mock.patch.object(skills, 'PATH_DEPTH_LIMIT', 7, create=True), \
                mock.patch.object(skills, 'FILE_LIMIT', 56, create=True), \
                mock.patch.object(skills, 'EXPANDED_LIMIT', 63, create=True):
            self.assertEqual(skills.stage_bundle(self.archive, self.staging), [self.staging / 'demo'])

    def test_actual_file_budget_is_enforced_while_streaming(self):
        make_bundle(self.archive, {'demo/SKILL.md': _SKILL, 'demo/resource': b'x'})
        original_open = zipfile.ZipFile.open

        def open_member(archive, member, *args, **kwargs):
            if isinstance(member, zipfile.ZipInfo) and member.filename.endswith('/resource'):
                return io.BytesIO(b'x' * 101)
            return original_open(archive, member, *args, **kwargs)

        with mock.patch.object(skills, 'FILE_LIMIT', 100, create=True), \
                mock.patch.object(zipfile.ZipFile, 'open', open_member):
            self.assert_rejected('size limit')

    def test_actual_aggregate_budget_is_shared_across_streamed_members(self):
        make_bundle(self.archive, {'demo/SKILL.md': _SKILL, 'demo/one': b'x' * 100, 'demo/two': b'y'})
        original_open = zipfile.ZipFile.open

        def open_member(archive, member, *args, **kwargs):
            if isinstance(member, zipfile.ZipInfo) and member.filename.endswith('/two'):
                return io.BytesIO(b'x' * 100)
            return original_open(archive, member, *args, **kwargs)

        with mock.patch.object(skills, 'EXPANDED_LIMIT', 200, create=True), \
                mock.patch.object(zipfile.ZipFile, 'open', open_member):
            self.assert_rejected('size limit')

    def test_license_copies_cannot_multiply_beyond_aggregate_budget(self):
        make_bundle(self.archive, {'one/SKILL.md': _SKILL, 'two/SKILL.md': _SKILL},
                    license_content=b'MIT notice' + b'x' * 90)
        with mock.patch.object(skills, 'EXPANDED_LIMIT', 300, create=True):
            self.assert_rejected('size limit')

    def test_rejects_crc_failure_and_truncation_with_cleanup(self):
        for corruption in ('crc', 'truncated', 'not-zip'):
            with self.subTest(corruption=corruption):
                make_bundle(self.archive, compression=zipfile.ZIP_STORED)
                data = self.archive.read_bytes()
                if corruption == 'crc':
                    data = data.replace(b'Reference content', b'Reference corrupt')
                elif corruption == 'truncated':
                    data = data[:-30]
                else:
                    data = b'not a zip archive'
                self.archive.write_bytes(data)
                self.assert_rejected()

    def assert_crc_valid_short_member_rejected(self, name, content):
        with zipfile.ZipFile(self.archive) as bundle:
            local = bundle.getinfo(name).header_offset
        data = bytearray(self.archive.read_bytes())
        central = data.index(name.encode(), data.index(b'PK\x01\x02')) - 46
        # Keep the actual bytes, compressed size, and CRC intact; overstate only the expanded size.
        struct.pack_into('<I', data, local + 22, len(content) + 1)
        struct.pack_into('<I', data, central + 24, len(content) + 1)
        self.archive.write_bytes(data)
        with zipfile.ZipFile(self.archive) as bundle:
            self.assertEqual(bundle.getinfo(name).file_size, len(content) + 1)
            self.assertEqual(bundle.read(name), content)
            self.assertIsNone(bundle.testzip(), 'The malformed member must still pass CRC validation')
        self.assert_rejected('advertised size')
        self.assertEqual(self.archive.read_bytes(), data)

    def test_rejects_crc_valid_empty_license_advertised_as_nonempty(self):
        make_bundle(self.archive, license_content=b'', compression=zipfile.ZIP_STORED)
        self.assert_crc_valid_short_member_rejected('bundle/LICENSE', b'')

    def test_rejects_crc_valid_resource_shorter_than_advertised(self):
        make_bundle(self.archive, compression=zipfile.ZIP_STORED)
        self.assert_crc_valid_short_member_rejected(_PAYLOAD + 'demo/references/guide.md', b'Reference content\n')

    def test_requires_payload_and_immediate_skill_file_in_every_top_level_tree(self):
        for files in ({}, {'SKILL.md': _SKILL}, {'demo/readme': 'missing'},
                      {'demo/nested/SKILL.md': _SKILL}, {'demo/SKILL.md/': b''},
                      {'demo/SKILL.md': _SKILL, 'empty/': b''},
                      {'demo/SKILL.md': _SKILL, 'other/resource': 'missing'}):
            with self.subTest(files=files):
                make_bundle(self.archive, files)
                self.assert_rejected('skill|SKILL')

    def test_rejects_invalid_frontmatter_in_top_level_skills(self):
        invalid = [b'\xff', 'No frontmatter', '---\nname: demo\ndescription: text\n',
                   '---\nname: [broken\ndescription: text\n---\n', '---\n- list\n---\n',
                   '---\n---\n', '---\nname: demo\n---\n', '---\ndescription: text\n---\n',
                   '---\nname: 42\ndescription: text\n---\n', '---\nname: demo\ndescription: []\n---\n',
                   '---\nname: " "\ndescription: text\n---\n', '---\nname: demo\ndescription: " "\n---\n',
                   '---\nname: !!python/object:unsafe {}\ndescription: text\n---\n']
        for content in invalid:
            with self.subTest(content=content):
                make_bundle(self.archive, {'demo/SKILL.md': content})
                self.assert_rejected('frontmatter|SKILL')

    def test_accepts_optional_metadata_long_descriptions_and_crlf_without_rewriting(self):
        content = ('---\r\nname: upstream-name\r\ndescription: ' + 'x' * 1100 +
                   '\r\nmetadata:\r\n  arbitrary: [1, 2]\r\n---\r\nInstructions\r\n').encode()
        make_bundle(self.archive, {'demo/SKILL.md': content})
        skills.stage_bundle(self.archive, self.staging)
        self.assertEqual((self.staging / 'demo/SKILL.md').read_bytes(), content)

    def test_accepts_block_scalar_description_containing_indented_delimiter(self):
        content = b'---\nname: demo\ndescription: |\n  ---\n  Valid description\n---\nInstructions\n'
        make_bundle(self.archive, {'demo/SKILL.md': content})
        skills.stage_bundle(self.archive, self.staging)
        self.assertEqual((self.staging / 'demo/SKILL.md').read_bytes(), content)

    def test_requires_nonempty_root_license(self):
        for license_content in (None, b''):
            with self.subTest(license_content=license_content):
                make_bundle(self.archive, license_content=license_content)
                self.assert_rejected('LICENSE|license')

    def test_preserves_identical_existing_license_notice(self):
        make_bundle(self.archive, {'demo/SKILL.md': _SKILL, 'demo/LICENSE.azure-skills': _LICENSE})
        skills.stage_bundle(self.archive, self.staging)
        self.assertEqual((self.staging / 'demo/LICENSE.azure-skills').read_bytes(), _LICENSE)

    def test_rejects_differing_or_platform_colliding_license_notice(self):
        for relative, content in [('demo/LICENSE.azure-skills', b'different'),
                                  ('demo/license.AZURE-skills', _LICENSE),
                                  ('demo/LICENSE.azure-skills/', b'')]:
            with self.subTest(relative=relative):
                make_bundle(self.archive, {'demo/SKILL.md': _SKILL, relative: content})
                self.assert_rejected('license|LICENSE')

    @unittest.skipUnless(os.name == 'posix', 'Unix executable permissions')
    def test_preserves_executable_bits_but_never_privileged_bits(self):
        member = zipfile.ZipInfo(_PAYLOAD + 'demo/run.sh')
        member.create_system = 3
        member.external_attr = (stat.S_IFREG | 0o7755) << 16
        make_bundle(self.archive, extra=[(member, b'#!/bin/sh\nexit 0\n')])
        skills.stage_bundle(self.archive, self.staging)
        mode = (self.staging / 'demo/run.sh').stat().st_mode
        self.assertEqual(mode & 0o111, 0o111)
        self.assertEqual(mode & 0o7000, 0)

    def test_existing_staging_directory_or_file_is_not_touched(self):
        make_bundle(self.archive)
        for is_directory in (False, True):
            with self.subTest(is_directory=is_directory):
                if is_directory:
                    self.staging.mkdir()
                    sentinel = self.staging / 'keep'
                else:
                    sentinel = self.staging
                sentinel.write_bytes(b'untouched')
                with self.assertRaises(CLIError):
                    skills.stage_bundle(self.archive, self.staging)
                self.assertEqual(sentinel.read_bytes(), b'untouched')
                sentinel.unlink()
                if is_directory:
                    self.staging.rmdir()

    @unittest.skipUnless(os.name == 'posix', 'Symlink staging boundary')
    def test_existing_staging_symlink_is_not_followed_or_removed(self):
        make_bundle(self.archive)
        target = self.root / 'target'
        target.mkdir()
        self.staging.symlink_to(target, target_is_directory=True)
        with self.assertRaises(CLIError):
            skills.stage_bundle(self.archive, self.staging)
        self.assertTrue(self.staging.is_symlink())
        self.assertEqual(list(target.iterdir()), [])

    def test_filesystem_failure_removes_only_owned_staging(self):
        make_bundle(self.archive)
        original_open = Path.open

        def fail_resource(path, *args, **kwargs):
            if path.name == 'guide.md':
                raise PermissionError('simulated extraction failure')
            return original_open(path, *args, **kwargs)

        with mock.patch.object(Path, 'open', fail_resource):
            self.assert_rejected()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.archive = self.root / 'bundle.zip'
        make_bundle(self.archive)
        self.trees = skills.stage_bundle(self.archive, self.root / 'staged')
        self.destination = self.root / 'home/.pi/agent/skills'
        self.target = skills.AgentTarget('pi', 'Pi', self.destination, True)
        self.skill = self.destination / 'demo'
        self.lock = self.destination.parent / '.az-azure-skills.lock'

    def publish(self):
        return skills.publish_skills(self.trees, [self.target])

    def assert_clean(self):
        self.assertFalse(self.lock.exists())
        self.assertEqual(sorted(path.name for path in self.destination.parent.iterdir()), ['skills'])
        self.assertEqual((self.trees[0] / 'references/guide.md').read_bytes(), b'Reference content\n')

    def make_link(self, link, target, directory=True):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except NotImplementedError as error:
            self.skipTest(f'Symlink creation unavailable: {error}')
        except OSError as error:
            if error.errno not in (errno.EPERM, errno.EACCES, errno.ENOSYS, errno.ENOTSUP):
                raise
            self.skipTest(f'Symlink creation unavailable: {error}')

    def test_same_bundle_is_noop_and_local_edits_are_preserved(self):
        first = self.publish()
        self.assertEqual(first.installed, [self.skill])
        self.assertEqual(first.already_present, [])
        self.assertEqual(first.conflicts, [])
        self.assertEqual(first.failures, [])
        self.assertEqual((self.skill / 'LICENSE.azure-skills').read_bytes(), _LICENSE)
        self.assertEqual((self.skill / 'child/SKILL.md').read_bytes(),
                         b'---\nname: child\ndescription: Nested skill\n---\n')
        second = self.publish()
        self.assertEqual(second.already_present, [self.skill])
        self.assertEqual(second.installed, [])
        guide = self.skill / 'references/guide.md'
        guide.write_bytes(b'local edit\n')
        third = self.publish()
        self.assertEqual(third.conflicts, [self.skill])
        self.assertEqual(third.installed, [])
        self.assertEqual(third.failures, [])
        self.assertEqual(guide.read_bytes(), b'local edit\n')
        self.assert_clean()

    def test_report_defaults_are_independent_between_lists_and_invocations(self):
        first, second = skills.InstallReport(), skills.InstallReport()
        first.installed.append(self.skill)
        first.failures.append((self.skill, 'failure'))
        self.assertEqual(first.already_present, [])
        self.assertEqual(first.conflicts, [])
        self.assertEqual(second.installed, [])
        self.assertEqual(second.already_present, [])
        self.assertEqual(second.conflicts, [])
        self.assertEqual(second.failures, [])
        self.assertEqual(self.publish().installed, [self.skill])
        self.assertEqual(self.publish().failures, [])

    def test_extra_destination_files_conflict_without_touching_unrelated_content(self):
        self.publish()
        extra = self.skill / 'local.txt'
        extra.write_bytes(b'local')
        unrelated = self.destination / 'user-skill'
        unrelated.mkdir()
        (unrelated / 'SKILL.md').write_bytes(b'user content')
        report = self.publish()
        self.assertEqual(report.conflicts, [self.skill])
        self.assertEqual(extra.read_bytes(), b'local')
        self.assertEqual((unrelated / 'SKILL.md').read_bytes(), b'user content')
        self.assert_clean()

    def test_existing_empty_directory_and_regular_file_are_conflicts(self):
        self.destination.mkdir(parents=True)
        for directory in (True, False):
            with self.subTest(directory=directory):
                if directory:
                    self.skill.mkdir()
                else:
                    self.skill.write_bytes(b'old file')
                report = self.publish()
                self.assertEqual(report.conflicts, [self.skill])
                self.assertEqual(report.failures, [])
                if directory:
                    self.assertEqual(list(self.skill.iterdir()), [])
                    self.skill.rmdir()
                else:
                    self.assertEqual(self.skill.read_bytes(), b'old file')
                    self.skill.unlink()
                self.assert_clean()

    def test_complete_tree_comparison_checks_names_bytes_types_and_license(self):
        self.publish()
        changes = ['same-size-bytes', 'license', 'missing', 'case', 'type', 'empty-directory']
        for change in changes:
            with self.subTest(change=change):
                shutil.rmtree(self.skill)
                shutil.copytree(self.trees[0], self.skill)
                guide = self.skill / 'references/guide.md'
                if change == 'same-size-bytes':
                    before = guide.stat()
                    guide.write_bytes(b'X' * before.st_size)
                    os.utime(guide, ns=(before.st_atime_ns, before.st_mtime_ns))
                elif change == 'license':
                    (self.skill / 'LICENSE.azure-skills').write_bytes(b'other license')
                elif change == 'missing':
                    guide.unlink()
                elif change == 'case':
                    guide.rename(guide.with_name('Guide.md'))
                elif change == 'type':
                    guide.unlink()
                    guide.mkdir()
                else:
                    (self.skill / 'empty').mkdir()
                self.assertFalse(skills._same_tree(self.trees[0], self.skill))
                self.assertEqual(self.publish().conflicts, [self.skill])
                self.assert_clean()

    @unittest.skipUnless(os.name == 'posix', 'Unix executable permissions')
    def test_publication_retains_executable_bits_and_ignores_other_permission_changes(self):
        source = self.trees[0] / 'references/guide.md'
        source.chmod(0o751)
        self.publish()
        guide = self.skill / 'references/guide.md'
        self.assertEqual(guide.stat().st_mode & 0o111, 0o111)
        guide.chmod(0o555)
        self.assertEqual(self.publish().already_present, [self.skill])
        guide.chmod(0o554)
        self.assertEqual(self.publish().conflicts, [self.skill])
        self.assertEqual(guide.stat().st_mode & 0o777, 0o554)

    def test_symlinked_root_ancestor_and_dangling_ancestor_fail_before_writes(self):
        for relative, dangling in [('skills', False), ('parent', False), ('parent', True)]:
            with self.subTest(relative=relative, dangling=dangling), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                outside = root / 'outside'
                if not dangling:
                    outside.mkdir()
                link = root / relative
                self.make_link(link, outside)
                destination = link if relative == 'skills' else link / 'agent/skills'
                target = skills.AgentTarget('pi', 'Pi', destination, True)
                report = skills.publish_skills(self.trees, [target])
                self.assertEqual([path for path, _ in report.failures], [destination / 'demo'])
                self.assertRegex(report.failures[0][1], 'symlink|reparse')
                self.assertEqual(report.installed, [])
                self.assertTrue(link.is_symlink())
                if not dangling:
                    self.assertEqual(list(outside.iterdir()), [])
                else:
                    self.assertFalse(outside.exists())
                self.assertEqual(sorted(path.name for path in root.iterdir()),
                                 sorted([relative] + ([] if dangling else ['outside'])))

    def test_parent_traversal_does_not_hide_symlink_before_normalization(self):
        outside = self.root / 'outside'
        outside.mkdir()
        link = self.root / 'alias'
        self.make_link(link, outside)
        destination = link / '../skills'
        report = skills.publish_skills(self.trees, [skills.AgentTarget('pi', 'Pi', destination, True)])
        self.assertEqual(len(report.failures), 1)
        self.assertFalse((self.root / 'skills').exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_discovered_symlink_parent_traversal_is_rejected_before_any_destination_write(self):
        for identifier, variable in [('pi', 'PI_CODING_AGENT_DIR'), ('claude-code', 'CLAUDE_CONFIG_DIR')]:
            for relative in (False, True):
                with self.subTest(identifier=identifier, relative=relative):
                    home = self.root / f'{identifier}-{relative}/home'
                    outside = home.parent / 'outside'
                    home.mkdir(parents=True)
                    (outside / 'child').mkdir(parents=True)
                    self.make_link(home / 'link', outside / 'child')
                    configured = home / 'link/../agent'
                    override = configured.relative_to(self.root) if relative else configured
                    with mock.patch.dict('os.environ', {variable: str(override)}, clear=True), \
                            mock.patch.object(Path, 'home', return_value=home), \
                            mock.patch('os.getcwd', return_value=str(self.root)):
                        target = next(target for target in skills.discover_agents() if target.identifier == identifier)
                        report = skills.publish_skills(self.trees, [target])
                    self.assertFalse((home / 'agent').exists(), 'Do not write the prematurely normalized destination')
                    self.assertFalse((outside / 'agent').exists(), 'Do not write through the configured symlink')
                    self.assertEqual(list(home.iterdir()), [home / 'link'])
                    self.assertEqual(list(outside.iterdir()), [outside / 'child'])
                    self.assertEqual(list((outside / 'child').iterdir()), [])
                    self.assertEqual(target.destination, configured / 'skills')
                    self.assertEqual([path for path, _ in report.failures], [configured / 'skills/demo'])
                    self.assertRegex(report.failures[0][1], 'symlink|reparse')
                    self.assertEqual(report.installed, [])
                    self.assertEqual(report.already_present, [])
                    self.assertEqual(report.conflicts, [])

    def test_discovered_safe_relative_parent_traversal_is_normalized_and_deduplicated_at_publication(self):
        home = self.root / 'home'
        (home / 'child').mkdir(parents=True)
        (home / 'config').mkdir()
        with mock.patch.dict('os.environ', {'CLAUDE_CONFIG_DIR': 'home/child/../config',
                                          'PI_CODING_AGENT_DIR': 'home/config'}, clear=True), \
                mock.patch.object(Path, 'home', return_value=home), \
                mock.patch('os.getcwd', return_value=str(self.root)):
            targets = [target for target in skills.discover_agents() if target.identifier in ('claude-code', 'pi')]
            self.assertEqual(targets[0].destination, home / 'child/../config/skills')
            self.assertTrue(all(target.destination.is_absolute() and target.detected for target in targets))
            report = skills.publish_skills(self.trees, targets)
            repeated = skills.publish_skills(self.trees, targets)
        destination = home / 'config/skills/demo'
        self.assertEqual(report.installed, [destination])
        self.assertEqual(report.already_present, [])
        self.assertEqual(report.conflicts, [])
        self.assertEqual(report.failures, [])
        self.assertEqual(repeated.already_present, [destination])
        self.assertEqual(repeated.installed, [])
        self.assertEqual(repeated.failures, [])
        self.assertEqual((destination / 'LICENSE.azure-skills').read_bytes(), _LICENSE)
        self.assertEqual((destination / 'references/guide.md').read_bytes(), b'Reference content\n')
        self.assertEqual(list((home / 'child').iterdir()), [])
        self.assertEqual(list((home / 'config').iterdir()), [home / 'config/skills'])
        self.assertEqual([target.label for target in targets], ['Claude Code', 'Pi'])
        self.assertEqual(targets[0].destination, home / 'child/../config/skills')

    def test_symlinked_skill_entries_including_dangling_are_conflicts(self):
        self.destination.mkdir(parents=True)
        for target in (self.trees[0], self.root / 'missing'):
            with self.subTest(target=target):
                self.make_link(self.skill, target)
                report = self.publish()
                self.assertEqual(report.conflicts, [self.skill])
                self.assertEqual(report.failures, [])
                self.assertTrue(self.skill.is_symlink())
                self.skill.unlink()
                self.assert_clean()

    def test_comparison_never_follows_nested_or_root_symlinks(self):
        self.publish()
        guide = self.skill / 'references/guide.md'
        guide.unlink()
        self.make_link(guide, self.trees[0] / 'references/guide.md', directory=False)
        self.assertFalse(skills._same_tree(self.trees[0], self.skill))
        self.assertFalse(skills._same_tree(self.skill, self.trees[0]))
        self.assertEqual(self.publish().conflicts, [self.skill])
        guide.unlink()
        self.make_link(guide, self.root / 'absent', directory=False)
        self.assertFalse(skills._same_tree(self.trees[0], self.skill))
        alias = self.root / 'alias'
        self.make_link(alias, self.trees[0])
        self.assertFalse(skills._same_tree(self.trees[0], alias))
        self.assertFalse(skills._same_tree(alias, self.trees[0]))

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO creation unavailable')
    def test_special_destination_file_is_conflict_without_reading_it(self):
        self.publish()
        guide = self.skill / 'references/guide.md'
        guide.unlink()
        os.mkfifo(guide)
        self.assertEqual(self.publish().conflicts, [self.skill])
        self.assertTrue(stat.S_ISFIFO(guide.lstat().st_mode))

    def test_normalized_aliases_are_deduplicated_without_losing_selected_agent_labels(self):
        self.destination.mkdir(parents=True)
        other = skills.AgentTarget('claude-code', 'Claude Code',
                                   self.destination.parent / 'skills/../skills', True)
        targets = [self.target, other]
        report = skills.publish_skills(self.trees, targets)
        self.assertEqual(report.installed, [self.skill])
        self.assertEqual(report.already_present, [])
        self.assertEqual(report.failures, [])
        self.assertEqual([(target.identifier, target.label) for target in targets],
                         [('pi', 'Pi'), ('claude-code', 'Claude Code')])
        self.assertEqual(skills.publish_skills(self.trees, targets).already_present, [self.skill])

    def test_symlink_alias_is_not_deduplicated_into_an_approved_destination(self):
        self.destination.mkdir(parents=True)
        alias = self.root / 'alias'
        self.make_link(alias, self.destination)
        targets = [self.target, skills.AgentTarget('claude-code', 'Claude Code', alias, True)]
        report = skills.publish_skills(self.trees, targets)
        self.assertEqual(report.installed, [self.skill])
        self.assertEqual([path for path, _ in report.failures], [alias / 'demo'])
        self.assertTrue(alias.is_symlink())

    def test_preexisting_lock_is_preserved_with_manual_recovery_guidance(self):
        self.destination.parent.mkdir(parents=True)
        self.lock.write_bytes(b'existing lock')
        report = self.publish()
        self.assertEqual(report.installed, [])
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertRegex(report.failures[0][1], 'no installation is running')
        self.assertIn('manually', report.failures[0][1])
        self.assertEqual(self.lock.read_bytes(), b'existing lock')
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()), [self.lock])

    def test_preexisting_symlink_lock_is_not_followed_or_removed(self):
        self.destination.parent.mkdir(parents=True)
        outside = self.root / 'missing-lock-target'
        self.make_link(self.lock, outside, directory=False)
        report = self.publish()
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertTrue(self.lock.is_symlink())
        self.assertFalse(outside.exists())
        self.assertFalse(self.destination.exists())

    @unittest.skipUnless(os.name == 'posix' and os.geteuid() != 0, 'Requires unprivileged Unix permissions')
    def test_real_permission_failure_is_per_path_and_does_not_touch_existing_files(self):
        self.destination.parent.mkdir(parents=True)
        keep = self.destination.parent / 'keep'
        keep.write_bytes(b'keep')
        self.destination.parent.chmod(0o500)
        try:
            report = self.publish()
        finally:
            self.destination.parent.chmod(0o700)
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertRegex(report.failures[0][1].lower(), 'permission|denied')
        self.assertEqual(keep.read_bytes(), b'keep')
        self.assertFalse(self.lock.exists())
        self.assertFalse(self.destination.exists())

    def test_file_ancestor_is_a_failure_and_is_not_changed(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_bytes(b'keep root file')
        report = self.publish()
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertEqual(self.destination.read_bytes(), b'keep root file')
        self.assertFalse(self.lock.exists())

    def test_cooperative_concurrent_attempt_fails_lock_while_copy_is_outside_skills_root(self):
        entered, release = threading.Event(), threading.Event()
        results, observations = [], []
        original_copytree = shutil.copytree

        def pause_copy(source, destination, *args, **kwargs):
            if Path(source) == self.trees[0]:
                temporary = Path(destination).parent
                observations.append((temporary.parent == self.destination.parent,
                                     temporary.name.startswith('.'),
                                     self.lock.exists(), self.skill.exists(),
                                     self.lock.stat().st_mode & 0o777))
                entered.set()
                if not release.wait(5):
                    raise OSError('Timed out waiting for concurrent publication test')
            return original_copytree(source, destination, *args, **kwargs)

        with mock.patch.object(skills.shutil, 'copytree', pause_copy):
            worker = threading.Thread(target=lambda: results.append(self.publish()))
            worker.start()
            try:
                self.assertTrue(entered.wait(5), 'Publication did not reach private copying')
                concurrent = self.publish()
                self.assertEqual([path for path, _ in concurrent.failures], [self.skill])
                self.assertEqual(concurrent.installed, [])
                self.assertTrue(self.lock.exists(), 'Losing attempt must not remove another installer lock')
            finally:
                release.set()
                worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(observations[0][:4], (True, True, True, False))
        if os.name == 'posix':
            self.assertEqual(observations[0][4], 0o600)
        self.assertEqual(results[0].installed, [self.skill])
        self.assertEqual(self.publish().already_present, [self.skill])
        self.assert_clean()

    def test_copy_failure_cleans_partial_sibling_but_not_unowned_siblings(self):
        self.destination.mkdir(parents=True)
        unrelated = self.destination.parent / '.az-azure-skills-user'
        unrelated.mkdir()
        (unrelated / 'keep').write_bytes(b'keep')
        original_copy = shutil.copyfile

        def fail_copy(source, destination, *args, **kwargs):
            result = original_copy(source, destination, *args, **kwargs)
            if Path(source).name == 'guide.md':
                raise OSError('injected disk failure after writing bytes')
            return result

        with mock.patch.object(skills.shutil, 'copyfile', fail_copy):
            report = self.publish()
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertIn('injected disk failure', report.failures[0][1])
        self.assertFalse(self.skill.exists())
        self.assertFalse(self.lock.exists())
        self.assertEqual((unrelated / 'keep').read_bytes(), b'keep')
        self.assertEqual(sorted(path.name for path in self.destination.parent.iterdir()),
                         ['.az-azure-skills-user', 'skills'])

    def test_later_skill_failure_keeps_success_and_same_bundle_retry_is_noop_for_it(self):
        make_bundle(self.archive, {'alpha/SKILL.md': _SKILL, 'beta/SKILL.md': _SKILL})
        self.trees = skills.stage_bundle(self.archive, self.root / 'two-skills')
        original_rename = Path.rename

        def fail_beta(path, destination):
            if Path(destination).name == 'beta':
                raise PermissionError('injected beta rename failure')
            return original_rename(path, destination)

        with mock.patch.object(Path, 'rename', fail_beta):
            first = self.publish()
        self.assertEqual(first.installed, [self.destination / 'alpha'])
        self.assertEqual([path for path, _ in first.failures], [self.destination / 'beta'])
        self.assertFalse((self.destination / 'beta').exists())
        self.assertEqual((self.destination / 'alpha/SKILL.md').read_bytes(), _SKILL.encode())
        self.assertFalse(self.lock.exists())
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])
        second = self.publish()
        self.assertEqual(second.already_present, [self.destination / 'alpha'])
        self.assertEqual(second.installed, [self.destination / 'beta'])
        self.assertEqual(second.failures, [])

    def test_failure_at_one_agent_does_not_stop_another_destination(self):
        self.destination.parent.mkdir(parents=True)
        self.lock.write_bytes(b'busy')
        other = self.root / 'other/skills'
        report = skills.publish_skills(self.trees, [self.target, skills.AgentTarget('codex', 'Codex', other, True)])
        self.assertEqual(report.installed, [other / 'demo'])
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertEqual(self.lock.read_bytes(), b'busy')

    def test_cross_release_retry_preserves_old_content_and_reports_conflict_alongside_new_skill(self):
        self.publish()
        second_archive = self.root / 'second.zip'
        make_bundle(second_archive, {'demo/SKILL.md': _SKILL + 'New release\n', 'new/SKILL.md': _SKILL})
        second_trees = skills.stage_bundle(second_archive, self.root / 'second')
        report = skills.publish_skills(second_trees, [self.target])
        self.assertEqual(report.conflicts, [self.skill])
        self.assertEqual(report.installed, [self.destination / 'new'])
        self.assertEqual(report.already_present, [])
        self.assertEqual(report.failures, [])
        self.assertEqual((self.skill / 'SKILL.md').read_bytes(), _SKILL.encode())
        self.assertEqual((self.skill / 'references/guide.md').read_bytes(), b'Reference content\n')
        self.assertEqual((self.destination / 'new/LICENSE.azure-skills').read_bytes(), _LICENSE)
        repeated = skills.publish_skills(second_trees, [self.target])
        self.assertEqual(repeated.conflicts, [self.skill])
        self.assertEqual(repeated.already_present, [self.destination / 'new'])
        self.assertEqual(repeated.installed, [])
        self.assert_clean()

    def test_partial_install_retry_with_new_release_does_not_update_earlier_success(self):
        make_bundle(self.archive, {'alpha/SKILL.md': _SKILL, 'beta/SKILL.md': _SKILL})
        first_trees = skills.stage_bundle(self.archive, self.root / 'first-release')
        original_rename = Path.rename

        def fail_beta(path, destination):
            if Path(destination).name == 'beta':
                raise PermissionError('injected first-release failure')
            return original_rename(path, destination)

        with mock.patch.object(Path, 'rename', fail_beta):
            first = skills.publish_skills(first_trees, [self.target])
        self.assertEqual(first.installed, [self.destination / 'alpha'])
        self.assertEqual([path for path, _ in first.failures], [self.destination / 'beta'])
        make_bundle(self.archive, {'alpha/SKILL.md': _SKILL + 'new alpha\n',
                                   'beta/SKILL.md': _SKILL + 'new beta\n'})
        second_trees = skills.stage_bundle(self.archive, self.root / 'next-release')
        second = skills.publish_skills(second_trees, [self.target])
        self.assertEqual(second.conflicts, [self.destination / 'alpha'])
        self.assertEqual(second.installed, [self.destination / 'beta'])
        self.assertEqual(second.already_present, [])
        self.assertEqual((self.destination / 'alpha/SKILL.md').read_bytes(), _SKILL.encode())
        self.assertEqual((self.destination / 'beta/SKILL.md').read_bytes(), (_SKILL + 'new beta\n').encode())
        self.assert_clean()

    def test_cancellation_with_cleanup_failure_still_stops_and_reports_cleanup_context(self):
        make_bundle(self.archive, {'alpha/SKILL.md': _SKILL, 'beta/SKILL.md': _SKILL, 'gamma/SKILL.md': _SKILL})
        self.trees = skills.stage_bundle(self.archive, self.root / 'three-skills')
        original_copytree, original_rmtree = shutil.copytree, shutil.rmtree

        def interrupt_beta(source, destination, *args, **kwargs):
            if Path(source).name == 'beta':
                Path(destination).mkdir()
                raise KeyboardInterrupt()
            return original_copytree(source, destination, *args, **kwargs)

        def fail_cleanup(path, *args, **kwargs):
            if (Path(path) / 'beta').exists():
                raise PermissionError(errno.EACCES, 'injected cleanup failure', str(path))
            return original_rmtree(path, *args, **kwargs)

        with mock.patch.object(skills.shutil, 'copytree', interrupt_beta), \
                mock.patch.object(skills.shutil, 'rmtree', fail_cleanup):
            report = self.publish()
        self.assertEqual(report.installed, [self.destination / 'alpha'])
        self.assertEqual([path for path, _ in report.failures], [self.destination / 'beta'])
        self.assertIn('cancel', report.failures[0][1].lower())
        self.assertIn('injected cleanup failure', report.failures[0][1])
        self.assertFalse(self.lock.exists())
        self.assertEqual(list(self.destination.iterdir()), [self.destination / 'alpha'])

    def test_cancellation_returns_prior_success_and_stops_remaining_skills_and_agents(self):
        make_bundle(self.archive, {'alpha/SKILL.md': _SKILL, 'beta/SKILL.md': _SKILL, 'gamma/SKILL.md': _SKILL})
        self.trees = skills.stage_bundle(self.archive, self.root / 'three-skills')
        original_copytree = shutil.copytree
        other = self.root / 'other/skills'

        def interrupt_beta(source, destination, *args, **kwargs):
            if Path(source).name == 'beta':
                Path(destination).mkdir()
                (Path(destination) / 'partial').write_bytes(b'partial')
                raise KeyboardInterrupt()
            return original_copytree(source, destination, *args, **kwargs)

        with mock.patch.object(skills.shutil, 'copytree', interrupt_beta):
            report = skills.publish_skills(self.trees, [self.target,
                                                     skills.AgentTarget('codex', 'Codex', other, True)])
        self.assertEqual(report.installed, [self.destination / 'alpha'])
        self.assertEqual([path for path, _ in report.failures], [self.destination / 'beta'])
        self.assertIn('cancel', report.failures[0][1].lower())
        self.assertEqual(list(self.destination.iterdir()), [self.destination / 'alpha'])
        self.assertFalse(other.parent.exists())
        self.assertFalse(self.lock.exists())
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_target_appearing_during_copy_is_not_replaced_even_when_empty(self):
        original_copytree = shutil.copytree

        def create_conflict(source, destination, *args, **kwargs):
            result = original_copytree(source, destination, *args, **kwargs)
            if Path(source) == self.trees[0]:
                self.skill.mkdir()
            return result

        with mock.patch.object(skills.shutil, 'copytree', create_conflict):
            report = self.publish()
        self.assertEqual(report.conflicts, [self.skill])
        self.assertEqual(list(self.skill.iterdir()), [])
        self.assert_clean()

    def test_ancestor_indirection_is_rechecked_after_copy(self):
        original_copytree = shutil.copytree
        outside = self.root / 'outside'
        outside.mkdir()
        probe = self.root / 'probe-link'
        self.make_link(probe, outside)
        probe.unlink()

        def redirect_root(source, destination, *args, **kwargs):
            result = original_copytree(source, destination, *args, **kwargs)
            if Path(source) == self.trees[0]:
                self.destination.rmdir()
                self.destination.symlink_to(outside, target_is_directory=True)
            return result

        with mock.patch.object(skills.shutil, 'copytree', redirect_root):
            report = self.publish()
        self.assertEqual([path for path, _ in report.failures], [self.skill])
        self.assertEqual(list(outside.iterdir()), [])
        self.assertTrue(self.destination.is_symlink())
        self.assert_clean()

    @unittest.skipUnless(os.name == 'nt', 'Windows junction/reparse-point filesystem unavailable')
    def test_windows_junctions_in_roots_and_skill_entries_are_unsafe(self):
        self.destination.parent.mkdir(parents=True)
        outside = self.root / 'outside'
        outside.mkdir()
        for junction in (self.destination, self.skill):
            with self.subTest(junction=junction):
                result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)],
                                        capture_output=True, check=False)
                if result.returncode:
                    self.skipTest(f'Junction creation unavailable: {result.stderr!r}')
                try:
                    report = self.publish()
                    if junction == self.destination:
                        self.assertEqual([path for path, _ in report.failures], [self.skill])
                    else:
                        self.assertEqual(report.conflicts, [self.skill])
                    self.assertEqual(list(outside.iterdir()), [])
                    self.assertEqual(report.installed, [])
                finally:
                    junction.rmdir()
                self.destination.mkdir(exist_ok=True)

    def test_empty_input_does_not_create_destination_or_lock(self):
        self.assertEqual(skills.publish_skills([], [self.target]), skills.InstallReport())
        self.assertEqual(skills.publish_skills(self.trees, []), skills.InstallReport())
        self.assertFalse(self.destination.parent.exists())


class _Response(io.BytesIO):
    def __init__(self, body=b'', headers=None):
        super().__init__(body)
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value
        self.read_sizes = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


class _SizedResponse(_Response):
    """Produce large chunked responses without retaining them in memory."""

    def __init__(self, size):
        super().__init__()
        self.remaining = size

    def read(self, size=-1):
        self.read_sizes.append(size)
        count = min(size, self.remaining)
        self.remaining -= count
        return b'x' * count


class ReleaseDownloadTests(unittest.TestCase):
    @mock.patch.object(skills, '_api_json', create=True)
    def test_annotated_tag_is_peeled_to_commit(self, api):
        commit = 'a' * 40
        tag_object = 'b' * 40
        api.side_effect = [
            {'tag_name': 'v1.2.49', 'draft': False, 'prerelease': False},
            {'object': {'type': 'tag', 'sha': tag_object}},
            {'object': {'type': 'commit', 'sha': commit}},
        ]
        result = skills.resolve_release('test-token')
        self.assertEqual(result, skills.Release('v1.2.49', commit))
        self.assertEqual(api.call_args_list, [
            mock.call('/releases/latest', 'test-token'),
            mock.call('/git/ref/tags/v1.2.49', 'test-token'),
            mock.call('/git/tags/' + tag_object, 'test-token'),
        ])

    @mock.patch.object(skills, '_api_json', create=True)
    def test_lightweight_tag_is_encoded_and_commit_normalized(self, api):
        api.side_effect = [
            {'tag_name': 'release/v1?#%', 'draft': False, 'prerelease': False,
             'zipball_url': 'https://attacker.invalid/archive', 'target_commitish': 'main'},
            {'object': {'type': 'commit', 'sha': 'A' * 40, 'url': 'https://attacker.invalid/commit'}},
        ]
        self.assertEqual(skills.resolve_release(), skills.Release('release/v1?#%', 'a' * 40))
        self.assertEqual(api.call_args_list, [
            mock.call('/releases/latest', None),
            mock.call('/git/ref/tags/release%2Fv1%3F%23%25', None),
        ])

    @mock.patch.object(skills, '_api_json', create=True)
    def test_invalid_stable_release_fields_are_rejected(self, api):
        for changes in ({'tag_name': None}, {'tag_name': 1}, {'tag_name': ''},
                        {'tag_name': 'x' * 256}, {'tag_name': 'v1\nAuthorization: bad'},
                        {'tag_name': 'v1\x00'}, {'draft': True}, {'draft': 0},
                        {'draft': None}, {'prerelease': True}, {'prerelease': 0},
                        {'prerelease': None}):
            with self.subTest(changes=changes):
                api.reset_mock()
                api.return_value = {'tag_name': 'v1', 'draft': False, 'prerelease': False}
                api.return_value.update(changes)
                with self.assertRaisesRegex(CLIError, 'invalid stable'):
                    skills.resolve_release()
                self.assertEqual(api.call_count, 1)
        for missing in ('tag_name', 'draft', 'prerelease'):
            with self.subTest(missing=missing):
                api.return_value = {'tag_name': 'v1', 'draft': False, 'prerelease': False}
                del api.return_value[missing]
                with self.assertRaises(CLIError):
                    skills.resolve_release()

    @mock.patch.object(skills, '_api_json', create=True)
    def test_invalid_git_objects_are_rejected(self, api):
        for obj in (None, [], 'commit', {}, {'type': 'tree', 'sha': 'a' * 40},
                    {'type': 'commit', 'sha': None}, {'type': 'commit', 'sha': 'a' * 39},
                    {'type': 'commit', 'sha': 'g' * 40}, {'type': 'commit', 'sha': 'a' * 40 + '\n'},
                    {'type': 'tag', 'sha': 'https://attacker.invalid'}):
            with self.subTest(obj=obj):
                api.side_effect = [{'tag_name': 'v1', 'draft': False, 'prerelease': False},
                                   {'object': obj}]
                with self.assertRaisesRegex(CLIError, 'resolve.*commit'):
                    skills.resolve_release()

    @mock.patch.object(skills, '_api_json', create=True)
    def test_five_annotated_tag_hops_are_allowed(self, api):
        api.side_effect = [
            {'tag_name': 'v1', 'draft': False, 'prerelease': False},
            *[{'object': {'type': 'tag', 'sha': str(index) * 40}} for index in range(5)],
            {'object': {'type': 'commit', 'sha': 'a' * 40}},
        ]
        self.assertEqual(skills.resolve_release(), skills.Release('v1', 'a' * 40))
        self.assertEqual(api.call_count, 7)

    @mock.patch.object(skills, '_api_json', create=True)
    def test_sixth_tag_hop_and_tag_cycles_are_rejected(self, api):
        api.side_effect = [
            {'tag_name': 'v1', 'draft': False, 'prerelease': False},
            *[{'object': {'type': 'tag', 'sha': 'b' * 40}} for _ in range(6)],
        ]
        with self.assertRaisesRegex(CLIError, 'resolve.*commit'):
            skills.resolve_release()
        self.assertEqual(api.call_count, 7)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_metadata_and_archive_requests_keep_token_isolated(self, build):
        responses = [_Response(b'{}'), _Response(b'archive', {'Content-Length': '7'})]
        openers = [mock.Mock(), mock.Mock()]
        for opener, response in zip(openers, responses):
            opener.open.return_value = response
        build.side_effect = openers
        self.assertEqual(skills._api_json('/releases/latest', 'secret-token'), {})
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertEqual(destination.read_bytes(), b'archive')
        metadata, archive = [opener.open.call_args.args[0] for opener in openers]
        self.assertEqual(metadata.full_url, 'https://api.github.com/repos/microsoft/azure-skills/releases/latest')
        self.assertEqual(metadata.get_header('Authorization'), 'Bearer secret-token')
        self.assertEqual(archive.full_url, 'https://codeload.github.com/microsoft/azure-skills/zip/' + 'a' * 40)
        self.assertIsNone(archive.get_header('Authorization'))
        for call in build.call_args_list:
            tls = next(handler for handler in call.args if isinstance(handler, HTTPSHandler))
            self.assertTrue(tls._context.check_hostname)
            self.assertEqual(tls._context.verify_mode, ssl.CERT_REQUIRED)
        for opener, response in zip(openers, responses):
            self.assertEqual(opener.open.call_args.kwargs, {'timeout': 30})
            self.assertTrue(response.closed)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_anonymous_metadata_has_no_authorization(self, build):
        response = _Response(b'{}')
        build.return_value.open.return_value = response
        skills._api_json('/releases/latest', None)
        self.assertIsNone(build.return_value.open.call_args.args[0].get_header('Authorization'))
        self.assertTrue(response.closed)

    def test_metadata_redirect_rejects_token_bearing_request(self):
        request = Request('https://api.github.com/repos/microsoft/azure-skills/releases/latest',
                          headers={'Authorization': 'Bearer secret-token'})
        for url in ('https://attacker.invalid/steal', 'https://api.github.com/another'):
            with self.subTest(url=url), self.assertRaisesRegex(CLIError, 'redirect'):
                skills._MetadataRedirectHandler().redirect_request(request, None, 302, 'Found', {}, url)

    def test_archive_redirects_are_restricted_to_https_codeload_origin(self):
        request = Request('https://codeload.github.com/microsoft/azure-skills/zip/' + 'a' * 40)
        handler = skills._ArchiveRedirectHandler()
        for url in ('https://attacker.invalid/zip', 'http://codeload.github.com/zip',
                    'https://codeload.github.com.attacker.invalid/zip',
                    'https://codeload.github.com:444/zip', 'https://user@codeload.github.com/zip'):
            with self.subTest(url=url), self.assertRaisesRegex(CLIError, 'redirect'):
                handler.redirect_request(request, None, 302, 'Found', {}, url)
        redirected = handler.redirect_request(
            request, None, 302, 'Found', {}, 'https://codeload.github.com/redirected')
        self.assertEqual(redirected.full_url, 'https://codeload.github.com/redirected')
        self.assertIsNone(redirected.get_header('Authorization'))

    @mock.patch.object(HTTPSHandler, 'https_open')
    def test_metadata_opener_rejects_redirect_before_second_request_and_closes_response(self, send):
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                body = _Response(headers={'Location': 'https://attacker.invalid/steal'})
                response = addinfourl(body, body.headers,
                                     'https://api.github.com/repos/microsoft/azure-skills/releases/latest', code)
                response.msg = 'Found'
                send.reset_mock()
                send.return_value = response
                with self.assertRaisesRegex(CLIError, 'redirect'):
                    skills._api_json('/releases/latest', 'secret-token')
                self.assertEqual(send.call_count, 1)
                self.assertTrue(response.closed)

    @mock.patch.object(HTTPSHandler, 'https_open')
    def test_archive_opener_rejects_redirect_before_second_request_and_closes_response(self, send):
        body = _Response(headers={'Location': 'https://attacker.invalid/steal'})
        response = addinfourl(body, body.headers,
                             'https://codeload.github.com/microsoft/azure-skills/zip/' + 'a' * 40, 302)
        response.msg = 'Found'
        send.return_value = response
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            with self.assertRaisesRegex(CLIError, 'redirect'):
                skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertEqual(send.call_count, 1)
            self.assertTrue(response.closed)
            self.assertFalse(destination.exists())

    @mock.patch.object(HTTPSHandler, 'https_open')
    def test_allowed_archive_redirect_closes_without_unbounded_body_read(self, send):
        body = _SizedResponse(67108865)
        body.headers['Location'] = '/microsoft/azure-skills/legacy.zip/' + 'a' * 40
        redirect = addinfourl(body, body.headers, 'https://codeload.github.com/original', 302)
        redirect.msg = 'Found'
        final_body = _Response(b'zip')
        final = addinfourl(final_body, final_body.headers, 'https://codeload.github.com/redirected', 200)
        final.msg = 'OK'
        send.side_effect = [redirect, final]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertEqual(destination.read_bytes(), b'zip')
        self.assertTrue(redirect.closed)
        self.assertTrue(final.closed)
        self.assertEqual(body.read_sizes, [])
        self.assertEqual(send.call_count, 2)
        for call in send.call_args_list:
            self.assertIsNone(call.args[0].get_header('Authorization'))

    @mock.patch.object(HTTPSHandler, 'https_open')
    def test_archive_redirect_loop_is_bounded_and_every_response_closed(self, send):
        responses = []

        def redirect(request):
            self.assertLess(len(responses), 12, 'Unbounded archive redirects')
            body = _Response(headers={'Location': 'https://codeload.github.com/again'})
            response = addinfourl(body, body.headers, request.full_url, 302)
            response.msg = 'Found'
            responses.append(response)
            return response

        send.side_effect = redirect
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            with self.assertRaisesRegex(CLIError, 'redirect'):
                skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertFalse(destination.exists())
        self.assertTrue(all(response.closed for response in responses))

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_metadata_rejects_malformed_json_and_nonobject_payloads(self, build):
        for body in (b'{invalid secret-token', b'\xff', b'[]', b'null', b'42',
                     b'"text"', b'[' * 2000 + b']' * 2000):
            with self.subTest(body=body[:30]):
                response = _Response(body)
                build.return_value.open.return_value = response
                with self.assertRaisesRegex(CLIError, 'metadata') as raised:
                    skills._api_json('/releases/latest', 'secret-token')
                self.assertNotIn('secret-token', str(raised.exception))
                self.assertTrue(response.closed)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_metadata_checks_advertised_and_actual_one_mib_limits(self, build):
        for response in (_Response(b'{}', {'Content-Length': '1048577'}),
                         _SizedResponse(1048577)):
            with self.subTest(headers=response.headers):
                build.return_value.open.return_value = response
                with self.assertRaisesRegex(CLIError, 'size limit'):
                    skills._api_json('/releases/latest', None)
                self.assertTrue(response.closed)
                self.assertTrue(all(0 < size <= 65536 for size in response.read_sizes))
                if response.headers:
                    self.assertEqual(response.read_sizes, [])

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_metadata_allows_exact_limit(self, build):
        body = b'{"value":"' + b'x' * (1048576 - 12) + b'"}'
        self.assertEqual(len(body), 1048576)
        response = _Response(body, {'Content-Length': '1048576'})
        build.return_value.open.return_value = response
        self.assertEqual(len(skills._api_json('/releases/latest', None)['value']), 1048564)
        self.assertTrue(response.closed)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_truncated_or_invalid_content_length_is_rejected(self, build):
        for length in ('3', '-1', 'unknown secret-token', '9' * 100):
            with self.subTest(length=length):
                response = _Response(b'{}', {'Content-Length': length})
                build.return_value.open.return_value = response
                with self.assertRaises(CLIError) as raised:
                    skills._api_json('/releases/latest', 'secret-token')
                self.assertNotIn('secret-token', str(raised.exception))
                self.assertTrue(response.closed)

    def test_copy_bounded_streams_and_enforces_actual_limit(self):
        source = _Response(b'x' * 65537)
        destination = io.BytesIO()
        self.assertEqual(skills._copy_bounded(source, destination, 65537), 65537)
        self.assertEqual(destination.getvalue(), b'x' * 65537)
        self.assertEqual(source.read_sizes, [65536, 2, 1])
        destination = io.BytesIO()
        with self.assertRaisesRegex(CLIError, 'size limit'):
            skills._copy_bounded(_Response(b'12345'), destination, 4)
        self.assertEqual(destination.getvalue(), b'')
        self.assertEqual(skills._copy_bounded(_Response(), io.BytesIO(), 0), 0)

    @mock.patch('time.monotonic', side_effect=[0, 0, 121])
    def test_copy_bounded_enforces_read_deadline(self, _clock):
        source = _Response(b'data')
        destination = io.BytesIO()
        with self.assertRaisesRegex(CLIError, 'read deadline'):
            skills._copy_bounded(source, destination, 10)
        self.assertEqual(source.read_sizes, [11])

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_archive_checks_advertised_and_actual_64_mib_limits_and_cleans_up(self, build):
        for response in (_Response(b'zip', {'Content-Length': '67108865'}),
                         _SizedResponse(67108865)):
            with self.subTest(headers=response.headers), tempfile.TemporaryDirectory() as directory:
                build.return_value.open.return_value = response
                destination = Path(directory) / 'archive.zip'
                with self.assertRaisesRegex(CLIError, 'size limit'):
                    skills.download_archive(skills.Release('v1', 'a' * 40), destination)
                self.assertFalse(destination.exists())
                self.assertTrue(response.closed)
                self.assertTrue(all(0 < size <= 65536 for size in response.read_sizes))

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_archive_read_deadline_closes_response_and_removes_partial_file(self, build):
        response = _Response(b'partial')
        build.return_value.open.return_value = response
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch('time.monotonic', side_effect=[0, 0, 121]):
            destination = Path(directory) / 'archive.zip'
            with self.assertRaisesRegex(CLIError, 'read deadline'):
                skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertFalse(destination.exists())
            self.assertTrue(response.closed)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_archive_interrupted_read_closes_response_and_removes_partial_file(self, build):
        response = _Response()
        build.return_value.open.return_value = response
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(response, 'read', side_effect=[b'partial', OSError('secret-token')]):
            destination = Path(directory) / 'archive.zip'
            with self.assertRaisesRegex(CLIError, 'archive') as raised:
                skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertNotIn('secret-token', str(raised.exception))
            self.assertFalse(destination.exists())
            self.assertTrue(response.closed)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_archive_rejects_noncommit_identifiers_before_request(self, build):
        for commit in ('main', '../outside', 'a' * 39, 'https://attacker.invalid'):
            with self.subTest(commit=commit), tempfile.TemporaryDirectory() as directory:
                destination = Path(directory) / 'archive.zip'
                with self.assertRaises(CLIError):
                    skills.download_archive(skills.Release('v1', commit), destination)
                self.assertFalse(destination.exists())
        build.assert_not_called()

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_tls_and_network_errors_are_sanitized(self, build):
        for error in (URLError('secret-token'), ssl.SSLCertVerificationError('secret-token'),
                      TimeoutError('secret-token')):
            with self.subTest(error=type(error).__name__):
                build.return_value.open.side_effect = error
                with self.assertRaisesRegex(CLIError, 'metadata') as raised:
                    skills._api_json('/releases/latest', 'secret-token')
                self.assertNotIn('secret-token', str(raised.exception))
                with tempfile.TemporaryDirectory() as directory:
                    destination = Path(directory) / 'archive.zip'
                    with self.assertRaisesRegex(CLIError, 'archive') as raised:
                        skills.download_archive(skills.Release('v1', 'a' * 40), destination)
                    self.assertNotIn('secret-token', str(raised.exception))
                    self.assertFalse(destination.exists())

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_http_error_guidance_distinguishes_limits_from_access_failures(self, build):
        cases = [
            (429, {}, b'', None, ('rate limit', '--gh-token'), ()),
            (429, {}, b'secret-token', 'secret-token', ('rate limit', 'wait'), ('--gh-token',)),
            (403, {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1700000000'},
             b'', None, ('rate limit', '1700000000', '--gh-token'), ()),
            (403, {'Retry-After': '60'}, b'', 'secret-token', ('rate limit', '60', 'wait'), ('--gh-token',)),
            (403, {}, b'{"message":"API rate limit exceeded: secret-token"}',
             'secret-token', ('rate limit', 'wait'), ('--gh-token',)),
            (403, {}, b'{"message":"Forbidden: secret-token"}',
             'secret-token', ('access', 'token'), ('rate limit',)),
            (403, {'X-RateLimit-Remaining': '5'}, b'Forbidden',
             None, ('access',), ('rate limit',)),
            (401, {}, b'secret-token', 'secret-token', ('access', 'token'), ('rate limit',)),
            (404, {}, b'secret-token', None, ('retry',), ('rate limit',)),
            (500, {}, b'secret-token', None, ('retry',), ('rate limit',)),
        ]
        for code, headers, body, token, includes, excludes in cases:
            with self.subTest(code=code, headers=headers, token=bool(token)):
                response = _Response(body)
                error = HTTPError('https://api.github.com/private', code, 'secret-token', headers, response)
                build.return_value.open.side_effect = error
                build.return_value.open.reset_mock()
                with self.assertRaises(CLIError) as raised:
                    skills._api_json('/releases/latest', token)
                message = str(raised.exception)
                self.assertIn('metadata', message)
                self.assertIn(str(code), message)
                self.assertNotIn('secret-token', message)
                for text in includes:
                    self.assertIn(text, message)
                for text in excludes:
                    self.assertNotIn(text, message)
                self.assertTrue(response.closed)
                self.assertEqual(build.return_value.open.call_count, 1)

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_error_metadata_is_numeric_and_error_body_is_bounded(self, build):
        for headers in ({'X-RateLimit-Reset': 'secret-token', 'Retry-After': 'secret-token'},
                        {'X-RateLimit-Reset': '9' * 10000, 'Retry-After': '-1'},
                        {'X-RateLimit-Reset': '1e999', 'Retry-After': '1.5'}):
            with self.subTest(headers=str(headers)[:80]):
                response = _SizedResponse(1048577)
                build.return_value.open.side_effect = HTTPError('https://api.github.com', 403,
                                                                'secret-token', headers, response)
                with self.assertRaises(CLIError) as raised:
                    skills._api_json('/releases/latest', 'secret-token')
                self.assertNotIn('secret-token', str(raised.exception))
                self.assertNotIn('rate limit', str(raised.exception))
                self.assertLess(len(str(raised.exception)), 500)
                self.assertTrue(response.closed)
                self.assertEqual(response.remaining, 0)
                self.assertTrue(all(0 < size <= 65536 for size in response.read_sizes))

    @mock.patch.object(skills, 'build_opener')
    def test_archive_rate_limit_does_not_suggest_sending_a_token(self, build):
        response = _Response(b'secret-token')
        build.return_value.open.side_effect = HTTPError('https://codeload.github.com', 429,
                                                        'secret-token', {'Retry-After': '60'}, response)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            with self.assertRaises(CLIError) as raised:
                skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            message = str(raised.exception)
            self.assertIn('archive', message)
            self.assertIn('429', message)
            self.assertIn('wait', message)
            self.assertIn('60', message)
            self.assertNotIn('--gh-token', message)
            self.assertTrue(response.closed)
            self.assertFalse(destination.exists())

    @mock.patch.object(skills, 'build_opener', create=True)
    def test_archive_http_error_is_sanitized_and_closed(self, build):
        response = _Response(b'secret-token')
        build.return_value.open.side_effect = HTTPError('https://codeload.github.com', 503,
                                                        'secret-token', {}, response)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            with self.assertRaisesRegex(CLIError, 'archive.*503') as raised:
                skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            self.assertNotIn('secret-token', str(raised.exception))
            self.assertTrue(response.closed)
            self.assertFalse(destination.exists())


class ResponseDeadlineTests(unittest.TestCase):
    @contextmanager
    def _local_response(self, prefix, chunks, interval=0.02, socket_timeout=0.1, deadline=0.2):
        """Keep real urllib/HTTPResponse/socket I/O; replace only TLS connection setup."""
        client, server = socket.socketpair()
        stop = threading.Event()
        requests = []
        sent = []

        def serve():
            try:
                with server:
                    server.settimeout(2)
                    with server.makefile('rb') as stream:
                        request = b''
                        while not request.endswith(b'\r\n\r\n'):
                            line = stream.readline()
                            if not line:
                                return
                            request += line
                        requests.append(request)
                        server.sendall(prefix)
                        for chunk in chunks:
                            if stop.wait(interval):
                                return
                            server.sendall(chunk)
                            sent.append(chunk)
            except (BrokenPipeError, ConnectionResetError):
                # The deadline deliberately closes the client before the peer finishes.
                pass

        def connect(connection):
            client.settimeout(connection.timeout)
            connection.sock = client

        worker = threading.Thread(target=serve)
        worker.start()
        try:
            with mock.patch.object(HTTPSConnection, 'connect', autospec=True, side_effect=connect), \
                    mock.patch.object(skills, '_RESPONSE_TIMEOUT', deadline), \
                    mock.patch.object(skills, '_SOCKET_TIMEOUT', socket_timeout), \
                    mock.patch.dict('os.environ', {}, clear=True):
                yield client, requests, sent
        finally:
            stop.set()
            client.close()
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive(), 'Local HTTP peer did not stop')

    def _assert_trickle_stops(self, framing, chunks, operation='metadata', status=200,
                             interval=0.02, socket_timeout=0.1):
        prefix = f'HTTP/1.1 {status} Test\r\nConnection: close\r\n'.encode() + framing
        with self._local_response(prefix, chunks, interval, socket_timeout) as (client, requests, sent), \
                tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'archive.zip'
            failure = None
            started = time.monotonic()
            try:
                if operation == 'metadata':
                    skills._api_json('/releases/latest', 'secret-token')
                else:
                    skills.download_archive(skills.Release('v1', 'a' * 40), destination)
            except CLIError as error:
                failure = str(error)
            elapsed = time.monotonic() - started
            # The peer needs >1 second to finish. Allow scheduling headroom, not the full body wait.
            self.assertLess(elapsed, 0.6, f'Response deadline did not interrupt transport I/O: {elapsed:.3f}s')
            self.assertIsNotNone(failure, 'The slow response unexpectedly completed')
            if status == 403:
                self.assertIn('HTTP 403', failure)
                self.assertIn('access', failure)
                self.assertNotIn('rate limit', failure)
            else:
                self.assertIn('read deadline', failure)
            self.assertNotIn('secret-token', failure)
            self.assertFalse(destination.exists(), 'Incomplete archive was retained')
            self.assertEqual(client.fileno(), -1, 'HTTP response retained its socket')
            self.assertLess(len(sent), len(chunks), 'Waited for the whole response before timing out')
            self.assertEqual(len(requests), 1)
            if operation == 'metadata':
                self.assertIn(b'Authorization: Bearer secret-token\r\n', requests[0])
            else:
                self.assertNotIn(b'Authorization:', requests[0])

    def test_fixed_length_metadata_trickle_cannot_extend_response_deadline(self):
        self._assert_trickle_stops(b'Content-Length: 60\r\n\r\n', [b'x'] * 60)

    def test_fixed_length_archive_trickle_is_interrupted_and_removed(self):
        # Complete one copy chunk first, so cleanup must remove already-written bytes.
        self._assert_trickle_stops(b'Content-Length: 65596\r\n\r\n' + b'x' * 65536,
                                  [b'x'] * 60, operation='archive')

    def test_chunked_archive_trickle_is_interrupted_and_removed(self):
        self._assert_trickle_stops(b'Transfer-Encoding: chunked\r\n\r\n10000\r\n' +
                                  b'x' * 65536 + b'\r\n3c\r\n',
                                  [b'x'] * 60 + [b'\r\n0\r\n\r\n'], operation='archive')

    def test_chunk_size_line_trickle_is_bounded_before_payload(self):
        self._assert_trickle_stops(b'Transfer-Encoding: chunked\r\n\r\n',
                                  [b'0'] * 60 + [b'1\r\nx\r\n0\r\n\r\n'])

    def test_chunk_trailer_trickle_is_bounded(self):
        self._assert_trickle_stops(b'Transfer-Encoding: chunked\r\n\r\n1\r\nx\r\n0\r\nX-Trailer: ',
                                  [b'x'] * 60 + [b'\r\n\r\n'])

    def test_error_diagnostic_trickle_is_bounded_and_redacted(self):
        body = b'{"message":"secret-token ' + b'x' * 40 + b'"}'
        for framing, chunks in (
                (f'Content-Length: {len(body)}\r\n\r\n'.encode(), [bytes([byte]) for byte in body]),
                (b'Transfer-Encoding: chunked\r\n\r\n' + f'{len(body):x}\r\n'.encode(),
                 [bytes([byte]) for byte in body] + [b'\r\n0\r\n\r\n'])):
            with self.subTest(framing=framing):
                self._assert_trickle_stops(framing, chunks, status=403)

    def test_blocked_receive_uses_remaining_deadline_not_socket_timeout(self):
        self._assert_trickle_stops(b'Content-Length: 1\r\n\r\n', [b'x'],
                                  interval=1.2, socket_timeout=1)

    def test_socket_inactivity_timeout_still_applies_before_deadline(self):
        prefix = b'HTTP/1.1 200 OK\r\nContent-Length: 1\r\nConnection: close\r\n\r\n'
        with self._local_response(prefix, [b'x'], interval=1.2, deadline=1) as (client, _, _):
            started = time.monotonic()
            with self.assertRaisesRegex(CLIError, 'network, TLS') as raised:
                skills._api_json('/releases/latest', 'secret-token')
            self.assertLess(time.monotonic() - started, 0.6)
            self.assertNotIn('secret-token', str(raised.exception))
            self.assertEqual(client.fileno(), -1)

    def test_fast_real_http_responses_complete_and_close(self):
        for framing, body in ((b'Content-Length: 2\r\n\r\n', b'{}'),
                              (b'Transfer-Encoding: chunked\r\n\r\n', b'2\r\n{}\r\n0\r\n\r\n')):
            with self.subTest(framing=framing):
                prefix = b'HTTP/1.1 200 OK\r\nConnection: close\r\n' + framing
                with self._local_response(prefix, [body]) as (client, _, _):
                    self.assertEqual(skills._api_json('/releases/latest', None), {})
                    self.assertEqual(client.fileno(), -1)

    def test_generic_bounded_copy_still_accepts_local_files(self):
        with tempfile.TemporaryFile() as source:
            source.write(b'x' * 65537)
            source.seek(0)
            destination = io.BytesIO()
            self.assertEqual(skills._copy_bounded(source, destination, 65537), 65537)
            self.assertEqual(destination.getvalue(), b'x' * 65537)


class AgentSelectionTests(unittest.TestCase):
    def test_selection_replaces_detected_defaults(self):
        self.assertEqual(
            skills.parse_agent_selection(' 1, 4,1 ', ['codex']),
            ['claude-code', 'pi'])

    def test_empty_input_and_none(self):
        self.assertEqual(skills.parse_agent_selection('', ['codex']), ['codex'])
        self.assertEqual(skills.parse_agent_selection('', []), [])
        self.assertEqual(skills.parse_agent_selection('none', ['codex']), [])
        self.assertEqual(skills.parse_agent_selection(' NoNe ', ['codex']), [])

    def test_whitespace_returns_independent_defaults(self):
        defaults = ['codex']
        selected = skills.parse_agent_selection(' \t ', defaults)
        selected.append('pi')
        self.assertEqual(defaults, ['codex'])
        self.assertEqual(selected, ['codex', 'pi'])

    def test_selection_uses_registry_order(self):
        self.assertEqual(
            skills.parse_agent_selection('4,3,2,1,2', []),
            ['claude-code', 'codex', 'github-copilot', 'pi'])

    def test_invalid_selection(self):
        for text in ('0', '5', '-1', '1,,4', 'claude', '1.5', '1,', ',1', 'none,1'):
            with self.subTest(text=text), self.assertRaises(CLIError):
                skills.parse_agent_selection(text, [])

    @mock.patch.dict('os.environ', {}, clear=True)
    def test_explicit_install_requires_targets(self):
        with self.assertRaises(CLIError):
            skills.validate_skills_options(True, None)
        with self.assertRaises(CLIError):
            skills.validate_skills_options(False, ['pi'])
        with self.assertRaises(CLIError):
            skills.validate_skills_options(None, ['pi'])


@mock.patch.dict('os.environ', {}, clear=True)
class SkillsPreflightTests(unittest.TestCase):
    def test_explicit_true_accepts_each_known_agent(self):
        for identifier in ('claude-code', 'codex', 'github-copilot', 'pi'):
            with self.subTest(identifier=identifier):
                self.assertIsNone(skills.validate_skills_options(True, [identifier]))

    def test_explicit_true_requires_nonempty_targets(self):
        for agents in (None, []):
            with self.subTest(agents=agents), self.assertRaises(RequiredArgumentMissingError):
                skills.validate_skills_options(True, agents)

    def test_targets_require_explicit_opt_in(self):
        for flag in (False, None):
            for agents in ([], ['pi']):
                with self.subTest(flag=flag, agents=agents), self.assertRaises(ArgumentUsageError):
                    skills.validate_skills_options(flag, agents)

    def test_unknown_identifiers_are_rejected(self):
        for agents in (['unknown'], ['pi', 'Codex'], ['']):
            with self.subTest(agents=agents), self.assertRaises(InvalidArgumentValueError):
                skills.validate_skills_options(True, agents)

    def test_false_and_omitted_need_no_targets_even_under_sudo(self):
        with mock.patch.dict('os.environ', {'SUDO_UID': '1000'}):
            self.assertIsNone(skills.validate_skills_options(False, None))
            self.assertIsNone(skills.validate_skills_options(None, None))

    def test_preflight_does_not_discover_or_touch_filesystem(self):
        with mock.patch.object(skills, 'discover_agents', side_effect=AssertionError('discovery')), \
                mock.patch.object(Path, 'home', side_effect=AssertionError('home')), \
                mock.patch('os.path.isdir', side_effect=AssertionError('filesystem')):
            self.assertIsNone(skills.validate_skills_options(True, ['pi']))
            self.assertIsNone(skills.validate_skills_options(False, None))
            self.assertIsNone(skills.validate_skills_options(None, None))

    @mock.patch('os.name', 'posix')
    def test_explicit_install_under_sudo_is_rejected(self):
        for variable in ('SUDO_UID', 'SUDO_USER'):
            with self.subTest(variable=variable), mock.patch.dict('os.environ', {variable: '1000'}):
                with self.assertRaisesRegex(CLIError, 'unprivileged'):
                    skills.validate_skills_options(True, ['pi'])

    @mock.patch('os.name', 'posix')
    def test_sudo_recognizes_either_marker_including_empty_values(self):
        for variable in ('SUDO_UID', 'SUDO_USER'):
            for value in ('1000', ''):
                with self.subTest(variable=variable, value=value):
                    with mock.patch.dict('os.environ', {variable: value}):
                        self.assertTrue(skills._is_sudo())

    @mock.patch('os.name', 'posix')
    def test_root_without_sudo_markers_is_not_sudo(self):
        with mock.patch('os.geteuid', return_value=0, create=True):
            self.assertFalse(skills._is_sudo())
            self.assertIsNone(skills.validate_skills_options(True, ['pi']))

    @mock.patch('os.name', 'nt')
    def test_windows_does_not_treat_sudo_markers_as_sudo(self):
        with mock.patch.dict('os.environ', {'SUDO_UID': '1000', 'SUDO_USER': 'someone'}):
            self.assertFalse(skills._is_sudo())
            self.assertIsNone(skills.validate_skills_options(True, ['pi']))


class AgentDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.home = Path.cwd() / 'test-home'
        patches = ExitStack()
        self.addCleanup(patches.close)
        patches.enter_context(mock.patch.dict('os.environ', {}, clear=True))
        patches.enter_context(mock.patch.object(Path, 'home', return_value=self.home))
        self.isdir = patches.enter_context(mock.patch('os.path.isdir', return_value=False))

    def test_default_destinations_and_labels_in_registry_order(self):
        targets = skills.discover_agents()
        self.assertEqual(
            [(target.identifier, target.label, target.destination, target.detected) for target in targets],
            [('claude-code', 'Claude Code', self.home / '.claude/skills', False),
             ('codex', 'Codex', self.home / '.agents/skills', False),
             ('github-copilot', 'GitHub Copilot', self.home / '.copilot/skills', False),
             ('pi', 'Pi', self.home / '.pi/agent/skills', False)])

    def test_default_configuration_directories_are_detected(self):
        directories = {self.home / '.claude', self.home / '.codex',
                       self.home / '.copilot', self.home / '.pi/agent'}
        self.isdir.side_effect = lambda path: Path(path) in directories
        self.assertEqual([target.detected for target in skills.discover_agents()], [True] * 4)

    def test_overrides_control_detection_but_codex_keeps_shared_destination(self):
        overrides = {'CLAUDE_CONFIG_DIR': str(self.home / 'claude config'),
                     'CODEX_HOME': str(self.home / 'codex-config'),
                     'PI_CODING_AGENT_DIR': str(self.home / 'pi-config')}
        self.isdir.side_effect = lambda path: Path(path) in {Path(value) for value in overrides.values()}
        with mock.patch.dict('os.environ', overrides):
            targets = skills.discover_agents()
        self.assertEqual([target.detected for target in targets], [True, True, False, True])
        self.assertEqual([target.destination for target in targets],
                         [self.home / 'claude config/skills', self.home / '.agents/skills',
                          self.home / '.copilot/skills', self.home / 'pi-config/skills'])

    def test_nonexistent_overrides_do_not_fall_back_to_default_configs(self):
        defaults = {self.home / '.claude', self.home / '.codex', self.home / '.pi/agent'}
        self.isdir.side_effect = lambda path: Path(path) in defaults
        with mock.patch.dict('os.environ', {'CLAUDE_CONFIG_DIR': str(self.home / 'missing-claude'),
                                          'CODEX_HOME': str(self.home / 'missing-codex'),
                                          'PI_CODING_AGENT_DIR': str(self.home / 'missing-pi')}):
            targets = skills.discover_agents()
        self.assertEqual([target.detected for target in targets], [False] * 4)
        self.assertEqual(targets[0].destination, self.home / 'missing-claude/skills')
        self.assertEqual(targets[3].destination, self.home / 'missing-pi/skills')

    def test_empty_and_whitespace_overrides_use_defaults(self):
        self.isdir.side_effect = lambda path: Path(path) in {
            self.home / '.claude', self.home / '.codex', self.home / '.pi/agent'}
        for value in ('', ' \t '):
            with self.subTest(value=value), mock.patch.dict('os.environ', {
                    'CLAUDE_CONFIG_DIR': value, 'CODEX_HOME': value, 'PI_CODING_AGENT_DIR': value}):
                targets = skills.discover_agents()
                self.assertEqual([target.detected for target in targets], [True, True, False, True])
                self.assertEqual(targets[0].destination, self.home / '.claude/skills')
                self.assertEqual(targets[3].destination, self.home / '.pi/agent/skills')

    def test_overrides_expand_home_and_preserve_lexical_relative_paths(self):
        self.isdir.side_effect = lambda path: Path(path) == Path.cwd() / 'codex-config'
        with mock.patch.dict('os.environ', {
                'HOME': str(self.home), 'USERPROFILE': str(self.home),
                'CLAUDE_CONFIG_DIR': '~/claude-config', 'CODEX_HOME': './codex-config',
                'PI_CODING_AGENT_DIR': 'other/../pi-config'}):
            targets = skills.discover_agents()
        self.assertEqual(targets[0].destination, self.home / 'claude-config/skills')
        self.assertEqual(targets[1].destination, self.home / '.agents/skills')
        self.assertTrue(targets[1].detected)
        self.assertEqual(targets[3].destination, Path.cwd() / 'other/../pi-config/skills')
        self.assertTrue(all(target.destination.is_absolute() for target in targets))

    @unittest.skipUnless(os.name == 'posix', 'Unix system Codex configuration')
    def test_system_codex_is_detected_even_with_nonexistent_override(self):
        self.isdir.side_effect = lambda path: Path(path) == Path('/etc/codex')
        with mock.patch.dict('os.environ', {'CODEX_HOME': str(self.home / 'missing')}):
            targets = skills.discover_agents()
        self.assertEqual([target.detected for target in targets], [False, True, False, False])
        self.assertEqual(targets[1].destination, self.home / '.agents/skills')

    def test_home_is_resolved_on_each_call(self):
        first = skills.discover_agents()
        with mock.patch.object(Path, 'home', return_value=self.home / 'another'):
            second = skills.discover_agents()
        self.assertEqual(first[0].destination, self.home / '.claude/skills')
        self.assertEqual(second[0].destination, self.home / 'another/.claude/skills')

    def test_import_does_not_inspect_filesystem(self):
        with mock.patch.object(Path, 'home', side_effect=AssertionError('home')), \
                mock.patch('os.path.isdir', side_effect=AssertionError('filesystem')):
            importlib.reload(skills)


class AgentDiscoveryFilesystemTests(unittest.TestCase):
    @mock.patch.dict('os.environ', {}, clear=True)
    def test_real_directories_not_files_and_no_discovery_writes(self):
        real_isdir = os.path.isdir
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / '.claude').mkdir()
            (home / '.codex').write_text('not a directory', encoding='utf-8')
            (home / '.copilot').mkdir()
            (home / '.pi').mkdir()
            (home / '.pi/agent').write_text('not a directory', encoding='utf-8')
            before = sorted(home.rglob('*'))

            def isolated_isdir(path):
                if Path(path).is_relative_to(home):
                    return real_isdir(path)
                return False

            with mock.patch.object(Path, 'home', return_value=home), \
                    mock.patch('os.path.isdir', side_effect=isolated_isdir):
                targets = skills.discover_agents()
            self.assertEqual([target.detected for target in targets], [True, False, True, False])
            self.assertEqual(sorted(home.rglob('*')), before)
            self.assertFalse(any(target.destination.exists() for target in targets))

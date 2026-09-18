# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from knack.util import CLIError
from azure.cli.command_modules.acs import _azure_skills as skills
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)


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

    def test_overrides_expand_home_and_normalize_relative_paths(self):
        self.isdir.side_effect = lambda path: Path(path) == Path.cwd() / 'codex-config'
        with mock.patch.dict('os.environ', {
                'HOME': str(self.home), 'USERPROFILE': str(self.home),
                'CLAUDE_CONFIG_DIR': '~/claude-config', 'CODEX_HOME': './codex-config',
                'PI_CODING_AGENT_DIR': 'other/../pi-config'}):
            targets = skills.discover_agents()
        self.assertEqual(targets[0].destination, self.home / 'claude-config/skills')
        self.assertEqual(targets[1].destination, self.home / '.agents/skills')
        self.assertTrue(targets[1].detected)
        self.assertEqual(targets[3].destination, Path.cwd() / 'pi-config/skills')

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

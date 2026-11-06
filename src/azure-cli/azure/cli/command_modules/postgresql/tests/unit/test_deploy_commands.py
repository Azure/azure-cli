# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest.mock import Mock, call, mock_open, patch

from azure.cli.command_modules.postgresql.commands import deploy_commands as custom
from azure.cli.command_modules.postgresql.utils import _flexible_server_util as _util
from azure.cli.core.azclierror import ClientRequestError
from azure.cli.core.util import is_windows


class PostgresqlDeployTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.cwd = os.path.join(temporary.name, 'work')
        self.tools = os.path.join(temporary.name, 'tools with spaces')
        os.mkdir(self.cwd)
        os.mkdir(self.tools)
        self.gh = os.path.join(self.tools, 'gh.exe' if is_windows() else 'gh')
        self.git = os.path.join(self.tools, 'git.exe' if is_windows() else 'git')
        self.files = {os.path.normcase(p) for p in (self.gh, self.git)}
        self.server = Mock(name='server')
        self.server.name = 'server'
        self.server.id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.DBforPostgreSQL/flexibleServers/server'
        self.server.fully_qualified_domain_name = 'server.example'
        self.server.network.public_network_access = 'Enabled'
        self.run = Mock(side_effect=self.run_result)
        self.process = Mock(returncode=0)
        self.process.stderr.read.return_value = b'failed'
        self.popen = Mock(return_value=self.process)
        for patcher in (
                patch.dict('os.environ', {'PATH': self.tools, 'PATHEXT': '.EXE'}),
                patch('os.getcwd', return_value=self.cwd),
                patch('os.path.isfile', side_effect=lambda p: os.path.normcase(p) in self.files),
                patch('os.access', return_value=True),
                patch('subprocess.run', self.run),
                patch('subprocess.Popen', self.popen),
                patch('builtins.open', mock_open()),
                patch.object(_util.os.path, 'exists', return_value=True),
                patch.object(_util.os, 'remove'),
                patch.object(_util.yaml, 'safe_load', return_value={
                    'jobs': {'build': {'steps': [{}, {}, {'with': {}}]}}}),
                patch.object(_util, 'get_subscription_id', return_value='sub'),
                patch.object(_util, 'create_service_principal_for_rbac', return_value={
                    'appId': 'app', 'password': 'unused', 'tenant': 'tenant', 'displayName': 'app', 'name': 'app'})):
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def run_result(args, **kwargs):
        if args[1:] == ['auth', 'status']:
            return Mock(returncode=1)
        if args[1:] == ['rev-parse', '--show-toplevel']:
            return Mock(returncode=0, stdout=b'C:/work with spaces\n')
        return Mock(returncode=0, stdout=b'')

    def setup_deploy(self):
        custom.github_actions_setup(
            Mock(), Mock(get=Mock(return_value=self.server)), 'rg', 'server', 'database',
            'user', 'unused', 'file with spaces.sql', 'owner/repo', action_name='deploy action',
            branch='topic branch', allow_push=True)

    def test_setup_pins_all_probe_login_secret_and_git_launches(self):
        self.setup_deploy()
        self.assertEqual([c.args[0] for c in self.run.call_args_list], [
            [self.gh], [self.gh, 'auth', 'status'],
            [self.git, 'rev-parse', '--show-toplevel'],
            [self.gh, 'secret', 'list', '--repo', 'owner/repo'],
            [self.git, 'rev-parse', '--show-toplevel']])
        launches = [c.args[0] for c in self.popen.call_args_list]
        self.assertEqual(launches[0], [self.gh, 'auth', 'login'])
        self.assertEqual(launches[1], [self.gh, 'secret', 'set', 'AZURE_CREDENTIALS',
                                       '--repo', 'owner/repo', '<', './temp_app_credential.txt'])
        self.assertEqual(launches[2][:7], [
            self.gh, 'secret', 'set', 'SERVER_DATABASE_POSTGRESQL_CONNECTION_STRING', '--repo', 'owner/repo', '-b'])
        self.assertEqual(len(launches[2]), 8)
        self.assertEqual(launches[3:], [
            [self.git, 'add', 'C:/work with spaces/.github/workflows/deploy action.yml'],
            [self.git, 'commit', '-m', 'Add github action file'],
            [self.git, 'push', 'origin', 'topic branch']])
        for invocation in self.popen.call_args_list:
            self.assertIs(invocation.kwargs['shell'], False)

    def test_workflow_reuses_checked_path(self):
        custom.github_actions_run('deploy action', 'topic branch')
        self.assertEqual(self.popen.call_args_list[-1].args[0],
                         [self.gh, 'workflow', 'run', 'deploy action.yml', '--ref', 'topic branch'])
        self.assertEqual([c.args[0][0] for c in self.run.call_args_list], [self.gh, self.gh])

    def test_probe_path_is_retained_after_path_changes(self):
        def probe(args, **kwargs):
            os.environ['PATH'] = self.cwd
            return self.run_result(args, **kwargs)
        self.run.side_effect = probe
        self.assertEqual(custom.gitcli_check_and_login(), self.gh)
        self.assertEqual(self.popen.call_args.args[0], [self.gh, 'auth', 'login'])

    def test_missing_path_tools_never_launch(self):
        for files in (set(), {os.path.normcase(os.path.join(self.cwd, os.path.basename(self.gh)))}):
            with self.subTest(files=files):
                self.files = files
                with self.assertRaises(FileNotFoundError):
                    custom.github_actions_run('deploy', 'main')
        self.run.assert_not_called()
        self.popen.assert_not_called()

    def test_git_helper_requires_path_tool(self):
        self.files = {os.path.normcase(os.path.join(self.cwd, os.path.basename(self.git)))}
        with self.assertRaises(FileNotFoundError):
            _util.get_git_root_dir()
        with self.assertRaises(FileNotFoundError):
            _util.run_subprocess(['git', 'add', 'file'])
        self.run.assert_not_called()
        self.popen.assert_not_called()

    def test_missing_gh_stops_secret_creation(self):
        self.files = set()
        with self.assertRaises(FileNotFoundError):
            _util.register_credential_secrets(Mock(), 'postgresql', self.server, 'owner/repo')
        _util.create_service_principal_for_rbac.assert_not_called()
        self.popen.assert_not_called()

    def test_missing_git_stops_setup_before_secret_creation(self):
        self.files = {os.path.normcase(self.gh)}
        with self.assertRaises(FileNotFoundError):
            self.setup_deploy()
        _util.create_service_principal_for_rbac.assert_not_called()
        self.assertEqual([c.args[0] for c in self.popen.call_args_list], [[self.gh, 'auth', 'login']])

    def test_non_windows_lookup_preserves_which_semantics(self):
        for executable in ('gh', './tools/gh', '/usr/local/bin/gh'):
            with self.subTest(executable=executable), \
                    patch.object(_util, 'is_windows', return_value=False), \
                    patch('shutil.which', return_value=self.gh) as which:
                self.assertEqual(_util.resolve_executable(executable), self.gh)
                which.assert_called_once_with(executable)
        with patch.object(_util, 'is_windows', return_value=False), \
                patch('shutil.which', return_value=None), self.assertRaises(FileNotFoundError):
            _util.resolve_executable('gh')

    def test_probe_nonzero_preserves_install_message(self):
        self.run.side_effect = None
        self.run.return_value = Mock(returncode=1)
        with self.assertRaisesRegex(ClientRequestError, 'Please install'):
            custom.gitcli_check_and_login()
        self.assertEqual(self.run.call_count, 1)
        self.popen.assert_not_called()

    def test_authenticated_does_not_login(self):
        self.run.side_effect = None
        self.run.return_value = Mock(returncode=0)
        self.assertEqual(custom.gitcli_check_and_login(), self.gh)
        self.popen.assert_not_called()

    def test_subprocess_preserves_argv_and_nonzero_behavior(self):
        self.process.returncode = 1
        arguments = ['gh', 'workflow', 'run', 'name with spaces.yml']
        with patch.object(_util.logger, 'warning') as warning:
            _util.run_subprocess(arguments)
            warning.assert_called_once_with('failed')
        self.assertEqual(arguments[0], 'gh')
        self.assertEqual(self.popen.call_args.args[0], [self.gh] + arguments[1:])
        self.process.returncode = 0
        self.process.stderr = None
        _util.run_subprocess([self.gh, 'auth', 'login'], stdout_show=True)
        self.assertEqual(self.popen.call_args, call([self.gh, 'auth', 'login'], shell=False))

    @unittest.skipUnless(is_windows(), 'Windows executable lookup')
    def test_windows_path_entries(self):
        self.files.add(os.path.normcase(os.path.join(self.cwd, 'gh.exe')))
        for directory in ('', '.', 'tools', r'C:tools', r'\tools', self.cwd):
            with self.subTest(directory=directory), patch.dict(
                    'os.environ', {'PATH': directory + os.pathsep + '"' + self.tools + '"'}):
                self.assertEqual(_util.resolve_executable('gh'), self.gh)
        with patch.dict('os.environ', {'PATH': self.cwd}), self.assertRaises(FileNotFoundError):
            _util.resolve_executable('gh')

    @unittest.skipUnless(is_windows(), 'Windows executable lookup')
    def test_windows_requires_native_executable(self):
        self.files = {os.path.normcase(os.path.join(self.tools, 'gh.cmd'))}
        with patch.dict('os.environ', {'PATHEXT': '.CMD;.EXE'}):
            for executable in ('gh', 'gh.cmd', os.path.join(self.tools, 'gh.cmd')):
                with self.subTest(executable=executable), self.assertRaises(FileNotFoundError):
                    _util.resolve_executable(executable)

    @unittest.skipUnless(is_windows(), 'Windows executable lookup')
    def test_windows_relative_explicit_paths_are_rejected(self):
        for executable in (r'.\gh.exe', r'tools\gh.exe', r'C:gh.exe', r'\tools\gh.exe'):
            with self.subTest(executable=executable), self.assertRaises(FileNotFoundError):
                _util.resolve_executable(executable)

    @unittest.skipUnless(is_windows(), 'Windows executable lookup')
    def test_windows_path_tool_link_to_working_directory_is_rejected(self):
        with patch.object(os.path, 'realpath', return_value=os.path.join(self.cwd, 'gh.exe')):
            with self.assertRaises(FileNotFoundError):
                _util.resolve_executable('gh')

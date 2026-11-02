# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from azure.cli.command_modules.postgresql.commands import deploy_commands as deploy
from azure.cli.command_modules.postgresql.utils import _flexible_server_util as util
from azure.cli.core.azclierror import ClientRequestError


class DeploymentRunnerTest(unittest.TestCase):

    def test_run_cmd_preserves_arguments_and_options(self):
        arguments = ['gh', 'secret', 'set', 'a value', '--body', 'literal & value']
        original = list(arguments)
        executable = os.path.abspath(os.path.join('installed tools', 'gh.exe'))
        environment = {'PATH': 'child-only-path'}
        with mock.patch.object(util, 'resolve_executable', return_value=executable), \
                mock.patch.object(util.subprocess, 'run') as run:
            result = util.run_cmd(arguments, capture_output=True, timeout=3, check=True,
                                  encoding='utf8', env=environment)

        run.assert_called_once_with([executable, *original[1:]], capture_output=True,
                                    timeout=3, check=True, encoding='utf8', env=environment)
        self.assertIs(result, run.return_value)
        self.assertEqual(arguments, original)

    def test_subprocess_preserves_arguments_in_each_output_mode(self):
        arguments = ['gh', 'secret', 'set', 'a value', '--body', 'literal & value']
        original = list(arguments)
        executable = os.path.abspath(os.path.join('installed tools', 'gh.exe'))
        for stdout_show in (None, False, True):
            with self.subTest(stdout_show=stdout_show):
                process = mock.MagicMock(returncode=0)
                with mock.patch.object(util, 'resolve_executable', return_value=executable), \
                        mock.patch.object(util.subprocess, 'Popen', return_value=process) as popen:
                    util.run_subprocess(arguments, stdout_show=stdout_show)

                expected = [executable, *original[1:]]
                if stdout_show:
                    popen.assert_called_once_with(expected)
                else:
                    popen.assert_called_once_with(expected, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait.assert_called_once_with()
                self.assertEqual(arguments, original)

    def test_unix_and_explicit_paths_keep_existing_lookup(self):
        with mock.patch.object(util.sys, 'platform', 'linux'), \
                mock.patch.object(util, 'get_safe_executable_path') as find:
            self.assertEqual(util.resolve_executable('gh'), 'gh')
        find.assert_not_called()

        with mock.patch.object(util.sys, 'platform', 'win32'), \
                mock.patch.object(util, 'get_safe_executable_path') as find:
            for executable in (os.path.abspath(os.path.join('installed tools', 'gh.exe')),
                               os.path.join('.', 'gh.exe'), os.path.join('tools', 'gh.exe')):
                with self.subTest(executable=executable):
                    self.assertEqual(util.resolve_executable(executable), executable)
        find.assert_not_called()


@unittest.skipUnless(sys.platform == 'win32', 'Windows executable search semantics')
class WindowsDeploymentToolsTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = os.path.join(temporary.name, 'project with spaces')
        self.installation = os.path.join(temporary.name, 'installed tools')
        os.makedirs(self.project)
        os.makedirs(self.installation)
        for directory in (self.project, self.installation):
            for name in ('git.exe', 'gh.exe'):
                with open(os.path.join(directory, name), 'wb'):
                    pass

        original_cwd = os.getcwd()
        os.chdir(self.project)
        self.addCleanup(os.chdir, original_cwd)
        environment = mock.patch.dict(os.environ, {
            'PATH': os.pathsep.join(['', '.', self.project, '"' + self.installation + '"']),
            'PATHEXT': '.COM;.BAT;.CMD',
        })
        environment.start()
        self.addCleanup(environment.stop)
        self.gh = os.path.join(self.installation, 'gh.exe')
        self.git = os.path.join(self.installation, 'git.exe')
        self.options = dict(capture_output=True, timeout=None, check=False, encoding=None, env=None)

    def test_workflow_run_resolves_every_launch(self):
        completed = subprocess.CompletedProcess([], 0)
        process = mock.MagicMock(returncode=0)
        with mock.patch.object(util.subprocess, 'run', return_value=completed) as run, \
                mock.patch.object(util.subprocess, 'Popen', return_value=process) as popen:
            deploy.github_actions_run('deploy database', 'feature/database')

        self.assertEqual(run.call_args_list, [
            mock.call([self.gh], **self.options),
            mock.call([self.gh, 'auth', 'status'], **self.options),
        ])
        popen.assert_called_once_with(
            [self.gh, 'workflow', 'run', 'deploy database.yml', '--ref', 'feature/database'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_setup_resolves_git_and_preserves_paths(self):
        client = mock.Mock()
        client.get.return_value = SimpleNamespace(
            name='server', network=SimpleNamespace(public_network_access='Enabled'))
        for allow_push in (False, True):
            with self.subTest(allow_push=allow_push):
                process = mock.MagicMock(returncode=0)
                with mock.patch.object(util.subprocess, 'run',
                                       return_value=subprocess.CompletedProcess([], 0)), \
                        mock.patch.object(util.subprocess, 'Popen', return_value=process) as popen, \
                        mock.patch.object(deploy, 'fill_action_template'), \
                        mock.patch.object(deploy, 'get_git_root_dir', return_value=self.project):
                    deploy.github_actions_setup(
                        None, client, 'test-rg', 'server', 'database', 'admin', 'unused',
                        'schema file.sql', 'owner/repository', action_name='deploy database',
                        branch='feature/database', allow_push=allow_push)

                action_path = self.project + util.GITHUB_ACTION_PATH + 'deploy database.yml'
                expected = [
                    mock.call([self.git, 'add', action_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE),
                    mock.call([self.git, 'commit', '-m', 'Add github action file'],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE),
                ]
                if allow_push:
                    expected.append(mock.call([self.git, 'push', 'origin', 'feature/database'],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE))
                self.assertEqual(popen.call_args_list, expected)

    def test_interactive_login_uses_resolved_tool(self):
        responses = [subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1)]
        with mock.patch.object(util.subprocess, 'run', side_effect=responses), \
                mock.patch.object(util.subprocess, 'Popen',
                                  return_value=mock.MagicMock(returncode=0)) as popen:
            deploy.gitcli_check_and_login()
        popen.assert_called_once_with([self.gh, 'auth', 'login'])

    def test_git_root_and_secret_queries_use_resolved_tools(self):
        completed = subprocess.CompletedProcess([], 0, stdout=self.project.encode('utf8'))
        with mock.patch.object(util.subprocess, 'run', return_value=completed) as run:
            self.assertEqual(util.get_git_root_dir(), self.project)
        run.assert_called_once_with([self.git, 'rev-parse', '--show-toplevel'], **self.options)

        server = SimpleNamespace(name='server', fully_qualified_domain_name='server.example.invalid')
        completed.stdout = b'AZURE_CREDENTIALS\nSERVER_DATABASE_POSTGRESQL_CONNECTION_STRING\n'
        template = 'jobs:\n  build:\n    steps:\n      - {}\n      - {}\n      - with: {}\n'
        with mock.patch.object(util.subprocess, 'run', return_value=completed) as run, \
                mock.patch.object(util, 'get_git_root_dir', return_value=self.project), \
                mock.patch.object(util.os.path, 'exists', return_value=True), \
                mock.patch('builtins.open', mock.mock_open(read_data=template)):
            util.fill_action_template(
                None, 'postgresql', server, 'database', 'admin', 'unused', 'schema.sql',
                'deploy database', 'owner/repository')
        run.assert_called_once_with([self.gh, 'secret', 'list', '--repo', 'owner/repository'], **self.options)

    def test_missing_installation_never_launches_project_tools(self):
        with mock.patch.dict(os.environ, {'PATH': os.pathsep.join(['', '.', self.project]),
                                          'SystemRoot': self.project}), \
                mock.patch.object(util.subprocess, 'run') as run, \
                mock.patch.object(util.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(ClientRequestError, 'Please install'):
                deploy.gitcli_check_and_login()
            with self.assertRaises(FileNotFoundError):
                util.get_git_root_dir()
            with self.assertRaises(FileNotFoundError):
                util.run_subprocess(['gh', 'auth', 'login'], stdout_show=True)
        run.assert_not_called()
        popen.assert_not_called()

    def test_real_launch_uses_resolved_executable(self):
        with open(os.path.join(self.project, 'cmd.exe'), 'wb') as placeholder:
            placeholder.write(b'Placeholder file.')
        system_directory = os.path.join(os.environ['SystemRoot'], 'System32')
        with mock.patch.dict(os.environ, {'PATH': system_directory}):
            result = util.run_cmd(['cmd.exe', '/d', '/c', 'echo trusted'], capture_output=True, check=True)
            util.run_subprocess(['cmd.exe', '/d', '/c', 'exit 0'], stdout_show=True)
        self.assertEqual(os.path.normcase(result.args[0]),
                         os.path.normcase(os.path.join(system_directory, 'cmd.exe')))
        self.assertEqual(result.stdout.strip(), b'trusted')

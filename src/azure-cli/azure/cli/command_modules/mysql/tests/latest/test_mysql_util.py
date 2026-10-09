# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import sys
import tempfile
import unittest
from unittest import mock
from unittest.mock import MagicMock, call, patch

from azure.cli.command_modules.mysql import _util as util
from azure.cli.command_modules.mysql._util import run_cmd
from azure.cli.command_modules.mysql import custom as deploy
from azure.cli.core.azclierror import ClientRequestError


class RunSubprocessTest(unittest.TestCase):

    def test_resolves_executable_in_each_output_mode_without_mutating_arguments(self):
        for stdout_show in (None, False, True):
            with self.subTest(stdout_show=stdout_show):
                command = ['gh', 'secret', 'set', 'a value', '--body', 'literal & value']
                original = list(command)
                executable = r'C:\Program Files\GitHub CLI\gh.exe'
                process = MagicMock(returncode=0)
                with patch.object(util, 'resolve_executable', return_value=executable) as resolve, \
                        patch.object(util.subprocess, 'Popen', return_value=process) as popen:
                    result = util.run_subprocess(command, stdout_show=stdout_show)

                resolve.assert_called_once_with('gh')
                expected = [executable] + original[1:]
                if stdout_show:
                    popen.assert_called_once_with(expected)
                else:
                    popen.assert_called_once_with(expected, stdout=util.subprocess.PIPE,
                                                  stderr=util.subprocess.PIPE)
                self.assertEqual(command, original)
                self.assertIsNot(popen.call_args[0][0], command)
                process.wait.assert_called_once_with()
                process.stderr.read.assert_not_called()
                self.assertIsNone(result)

    def test_missing_executable_does_not_spawn_or_mutate_arguments(self):
        for stdout_show in (None, False, True):
            with self.subTest(stdout_show=stdout_show):
                command = ['gh', '--version']
                with patch.object(util, 'resolve_executable', side_effect=FileNotFoundError('gh')) as resolve, \
                        patch.object(util.subprocess, 'Popen') as popen:
                    with self.assertRaises(FileNotFoundError):
                        util.run_subprocess(command, stdout_show=stdout_show)

                resolve.assert_called_once_with('gh')
                popen.assert_not_called()
                self.assertEqual(command, ['gh', '--version'])

    def test_nonzero_exit_logs_captured_stderr(self):
        process = MagicMock(returncode=1)
        process.stderr.read.return_value = b'  command failed\n'
        with patch.object(util, 'resolve_executable', return_value=r'C:\trusted\gh.exe'), \
                patch.object(util.subprocess, 'Popen', return_value=process), \
                patch.object(util.logger, 'warning') as warning:
            result = util.run_subprocess(['gh', '--version'])

        process.wait.assert_called_once_with()
        warning.assert_called_once_with('command failed')
        self.assertIsNone(result)


class GitHubActionsTest(unittest.TestCase):

    def test_workflow_launch_resolves_every_executable_on_windows(self):
        executable = r'C:\Program Files\GitHub CLI\gh.exe'
        completed = util.subprocess.CompletedProcess([], 0)
        process = MagicMock(returncode=0)
        with patch('azure.cli.command_modules.mysql._util.sys.platform', 'win32'), \
                patch('azure.cli.command_modules.mysql._util.find_executable', return_value=executable) as find, \
                patch.object(util.subprocess, 'run', return_value=completed) as run, \
                patch.object(util.subprocess, 'Popen', return_value=process) as popen:
            deploy.github_actions_run('deploy-database', 'feature/database')

        self.assertEqual(find.call_args_list, [call('gh'), call('gh'), call('gh')])
        options = dict(capture_output=True, timeout=None, check=False, encoding=None, env=None)
        self.assertEqual(run.call_args_list, [
            call([executable], **options),
            call([executable, 'auth', 'status'], **options),
        ])
        popen.assert_called_once_with(
            [executable, 'workflow', 'run', 'deploy-database.yml', '--ref', 'feature/database'],
            stdout=util.subprocess.PIPE, stderr=util.subprocess.PIPE)
        process.wait.assert_called_once_with()

    def test_missing_github_cli_reports_install_message_without_spawning(self):
        with patch('azure.cli.command_modules.mysql._util.sys.platform', 'win32'), \
                patch('azure.cli.command_modules.mysql._util.find_executable', return_value=None) as find, \
                patch.object(util.subprocess, 'run') as run, \
                patch.object(util.subprocess, 'Popen') as popen:
            with self.assertRaisesRegex(ClientRequestError, 'Please install'):
                deploy.gitcli_check_and_login()

        find.assert_called_once_with('gh')
        run.assert_not_called()
        popen.assert_not_called()


class TestResolveExecutable(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.mysql._util.sys.platform', 'linux')
    def test_unix_keeps_native_lookup(self):
        from azure.cli.command_modules.mysql._util import resolve_executable
        with mock.patch('azure.cli.command_modules.mysql._util.find_executable') as find:
            self.assertEqual(resolve_executable('gh'), 'gh')
        find.assert_not_called()

    def test_run_cmd_preserves_arguments_and_options(self):
        args = ['gh', 'workflow', 'run', 'workflow with spaces.yml']
        env = {'PATH': 'child-only-path'}
        resolved = os.path.abspath(os.path.join('installed tools', 'gh.exe'))
        with mock.patch('azure.cli.command_modules.mysql._util.resolve_executable', return_value=resolved) as resolve, \
                mock.patch('subprocess.run') as run:
            result = run_cmd(args, capture_output=True, timeout=3, check=True, encoding='utf8', env=env)
        resolve.assert_called_once_with('gh')
        run.assert_called_once_with([resolved, *args[1:]], capture_output=True, timeout=3,
                                    check=True, encoding='utf8', env=env)
        self.assertIs(result, run.return_value)
        self.assertEqual(args[0], 'gh')

    def test_missing_executable_never_launches(self):
        with mock.patch('azure.cli.command_modules.mysql._util.resolve_executable', side_effect=FileNotFoundError), \
                mock.patch('subprocess.run') as run:
            with self.assertRaises(FileNotFoundError):
                run_cmd(['gh'])
        run.assert_not_called()


@unittest.skipUnless(sys.platform == 'win32', 'Windows executable search semantics')
class TestWindowsExecutableResolution(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.hostile = os.path.join(self.temp.name, 'project')
        self.trusted = os.path.join(self.temp.name, 'installed tools')
        os.makedirs(self.hostile)
        os.makedirs(self.trusted)
        original_cwd = os.getcwd()
        os.chdir(self.hostile)
        self.addCleanup(os.chdir, original_cwd)
        self.plant = os.path.join(self.hostile, 'gh.exe')
        self.installed = os.path.join(self.trusted, 'gh.exe')
        for path in (self.plant, self.installed):
            with open(path, 'wb'):
                pass
        environment = mock.patch.dict(os.environ, {'PATH': self.trusted, 'PATHEXT': '.COM;.EXE;.BAT;.CMD'})
        environment.start()
        self.addCleanup(environment.stop)

    def test_uses_absolute_path_not_current_directory(self):
        from azure.cli.command_modules.mysql._util import find_executable, resolve_executable
        self.assertEqual(find_executable('gh'), self.installed)
        self.assertEqual(os.path.normcase(resolve_executable('gh.exe')), os.path.normcase(self.installed))

    def test_skips_empty_relative_and_current_directory_path_entries(self):
        from azure.cli.command_modules.mysql._util import resolve_executable
        relative = os.path.join(self.hostile, 'bin')
        os.makedirs(relative)
        with open(os.path.join(relative, 'gh.exe'), 'wb'):
            pass
        os.environ['PATH'] = ';'.join(['', '.', 'bin', self.hostile, self.hostile + '\\.', self.trusted])
        self.assertEqual(resolve_executable('gh'), self.installed)

    def test_quoted_path_with_spaces(self):
        from azure.cli.command_modules.mysql._util import resolve_executable
        os.environ['PATH'] = '"' + self.trusted + '"'
        self.assertEqual(resolve_executable('gh'), self.installed)

    def test_rejects_current_directory_alias_by_identity(self):
        alias = os.path.join(self.temp.name, 'project-alias')
        os.makedirs(alias)
        with open(os.path.join(alias, 'gh.exe'), 'wb'):
            pass
        os.environ['PATH'] = alias + ';' + self.trusted
        samefile = os.path.samefile

        def directory_identity(first, second):
            if first == alias:
                return samefile(self.hostile, second)
            return samefile(first, second)

        # Model an alias that realpath does not normalize to the CWD spelling.
        with mock.patch.object(util.os.path, 'samefile', side_effect=directory_identity) as identity:
            self.assertEqual(util.resolve_executable('gh'), self.installed)
        identity.assert_any_call(alias, os.getcwd())

    def test_rejects_executable_link_into_current_directory(self):
        realpath = os.path.realpath

        def link_target(path):
            return self.plant if path == self.installed else realpath(path)

        # Mock the link target so this test does not require Windows symlink privileges.
        with mock.patch.object(util.os.path, 'realpath', side_effect=link_target), \
                mock.patch.object(util.subprocess, 'run') as run:
            with self.assertRaises(FileNotFoundError):
                util.run_cmd(['gh'])
        run.assert_not_called()

    def test_rejects_executable_link_into_current_directory_alias(self):
        alias = os.path.join(self.temp.name, 'target-alias')
        realpath = os.path.realpath
        samefile = os.path.samefile

        def link_target(path):
            return os.path.join(alias, 'gh.exe') if path == self.installed else realpath(path)

        def directory_identity(first, second):
            if first == alias:
                return samefile(self.hostile, second)
            return samefile(first, second)

        with mock.patch.object(util.os.path, 'realpath', side_effect=link_target), \
                mock.patch.object(util.os.path, 'samefile', side_effect=directory_identity) as identity:
            with self.assertRaises(FileNotFoundError):
                util.resolve_executable('gh')
        identity.assert_any_call(alias, os.getcwd())

    def test_allows_executable_link_outside_current_directory(self):
        target_dir = os.path.join(self.temp.name, 'other installation')
        os.makedirs(target_dir)
        realpath = os.path.realpath

        def link_target(path):
            return os.path.join(target_dir, 'gh.exe') if path == self.installed else realpath(path)

        with mock.patch.object(util.os.path, 'realpath', side_effect=link_target), \
                mock.patch.object(util.os.path, 'samefile', wraps=os.path.samefile) as identity:
            self.assertEqual(util.resolve_executable('gh'), self.installed)
        identity.assert_any_call(target_dir, os.getcwd())

    def test_identity_errors_skip_candidate_without_launching(self):
        samefile = os.path.samefile
        for error in (FileNotFoundError, PermissionError, OSError, ValueError):
            for failed_check in (1, 2):
                with self.subTest(error=error, failed_check=failed_check):
                    calls = []

                    def directory_identity(first, second):
                        calls.append((first, second))
                        if len(calls) == failed_check:
                            raise error('Cannot verify directory identity')
                        return samefile(first, second)

                    with mock.patch.object(util.os.path, 'samefile', side_effect=directory_identity), \
                            mock.patch.object(util.subprocess, 'run') as run:
                        with self.assertRaises(FileNotFoundError):
                            util.run_cmd(['gh'])
                    run.assert_not_called()

    def test_unavailable_path_entry_does_not_hide_installed_tool(self):
        unavailable = os.path.join(self.temp.name, 'unavailable')
        os.environ['PATH'] = unavailable + ';' + self.trusted
        samefile = os.path.samefile

        def directory_identity(first, second):
            if first == unavailable:
                raise PermissionError('Cannot access PATH entry')
            return samefile(first, second)

        with mock.patch.object(util.os.path, 'samefile', side_effect=directory_identity):
            self.assertEqual(util.resolve_executable('gh'), self.installed)

    def test_missing_path_never_uses_current_directory(self):
        from azure.cli.command_modules.mysql._util import find_executable, resolve_executable
        for path in (None, '', '.', self.hostile, 'relative'):
            with self.subTest(path=path):
                if path is None:
                    os.environ.pop('PATH', None)
                else:
                    os.environ['PATH'] = path
                self.assertIsNone(find_executable('gh'))
                with mock.patch('subprocess.run') as run:
                    with self.assertRaises(FileNotFoundError) as error:
                        run_cmd(['gh'])
                self.assertEqual(error.exception.filename, 'gh')
                run.assert_not_called()
                with self.assertRaises(FileNotFoundError):
                    resolve_executable('gh')

    def test_preserves_explicit_executable_paths(self):
        from azure.cli.command_modules.mysql._util import resolve_executable
        for path in (self.installed, '.\\gh.exe', 'tools\\gh.exe'):
            with self.subTest(path=path):
                self.assertEqual(resolve_executable(path), path)

    def test_path_order_and_no_implicit_batch_execution(self):
        from azure.cli.command_modules.mysql._util import resolve_executable
        second = os.path.join(self.temp.name, 'second')
        os.makedirs(second)
        second_executable = os.path.join(second, 'gh.exe')
        with open(second_executable, 'wb'):
            pass
        for extension in ('.cmd', '.bat', '.com'):
            with open(os.path.join(self.trusted, 'gh' + extension), 'wb'):
                pass
        os.environ['PATH'] = self.trusted + ';' + second
        self.assertEqual(resolve_executable('gh'), self.installed)
        os.remove(self.installed)
        self.assertEqual(resolve_executable('gh'), second_executable)
        os.remove(second_executable)
        with self.assertRaises(FileNotFoundError):
            resolve_executable('gh')

    def test_native_exe_resolution_does_not_depend_on_pathext(self):
        from azure.cli.command_modules.mysql._util import resolve_executable
        for extensions in (None, '', '.BAT;.CMD'):
            with self.subTest(extensions=extensions):
                if extensions is None:
                    os.environ.pop('PATHEXT', None)
                else:
                    os.environ['PATHEXT'] = extensions
                self.assertEqual(resolve_executable('gh'), self.installed)

    def test_child_environment_does_not_change_executable_lookup(self):
        with mock.patch('subprocess.run') as run:
            run_cmd(['gh'], env={'PATH': self.hostile})
        self.assertEqual(run.call_args.args[0], [self.installed])
        self.assertEqual(run.call_args.kwargs['env'], {'PATH': self.hostile})

    def test_real_launch_ignores_current_directory_executable(self):
        system_directory = os.path.join(os.environ['SystemRoot'], 'System32')
        with open(os.path.join(self.hostile, 'cmd.exe'), 'wb') as plant:
            plant.write(b'Not an executable: launching this file must fail.')
        os.environ['PATH'] = system_directory
        result = run_cmd(['cmd.exe', '/d', '/c', 'echo trusted'], capture_output=True, check=True)
        self.assertEqual(os.path.normcase(result.args[0]),
                         os.path.normcase(os.path.join(system_directory, 'cmd.exe')))
        self.assertEqual(result.stdout.strip(), b'trusted')

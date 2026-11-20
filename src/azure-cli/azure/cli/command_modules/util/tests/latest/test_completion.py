# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from azure.cli.testsdk import LiveScenarioTest


class CompletionTest(LiveScenarioTest):
    # Completion exits before command invocation; self.cmd cannot run the Bash wrapper.
    def _complete(self, script, interactive=False, tempfile_mode=True):
        bash = shutil.which('bash')
        if not bash:
            self.skipTest('Bash is not installed')
        if not shutil.which('az') and not shutil.which('az.cmd'):
            self.skipTest('Azure CLI is not installed')
        if os.name == 'nt':
            platform = subprocess.run(
                [bash, '--noprofile', '--norc', '-c', 'uname -s'],
                check=True, capture_output=True, text=True).stdout
            self.assertTrue(platform.startswith('MINGW'), platform)
        for directory in (*Path(__file__).resolve().parents, Path.cwd()):
            completion = directory / 'az.completion'
            if completion.is_file():
                break
        else:
            self.skipTest('az.completion is not available in the test installation or checkout')
        with tempfile.TemporaryDirectory() as scratch:
            tempdir = Path(scratch) / 'completion files'
            tempdir.mkdir()
            (Path(scratch) / 'filesystem-only').mkdir()
            env = os.environ.copy()
            for name in list(env):
                if name.startswith(('COMP_', '_ARGCOMPLETE', 'ARGCOMPLETE_')):
                    del env[name]
            env.update({
                'TMPDIR': tempdir.as_posix(),
                'AZURE_CONFIG_DIR': (Path(scratch) / 'config').as_posix(),
                'AZURE_EXTENSION_DIR': (Path(scratch) / 'extensions').as_posix(),
                'AZURE_CORE_COLLECT_TELEMETRY': 'no',
                'AZ_COMPLETION_SCRIPT': completion.as_posix(),
            })
            if tempfile_mode:
                env['ARGCOMPLETE_USE_TEMPFILES'] = '1'
            args = [bash, '--noprofile', '--norc']
            if interactive:
                args.append('-i')
                env.update({'INPUTRC': os.devnull, 'TERM': 'dumb', 'PS1': 'completion> ', 'PS2': ''})
                script = (
                    'source "$AZ_COMPLETION_SCRIPT"\n'
                    'bind "set show-all-if-ambiguous on"\n'
                    'bind "set completion-query-items 0"\n'
                    'bind "set page-completions off"\n'
                    'bind -x \'"\\C-x\\C-t":printf "line=<%s>,point=%s\\n" '
                    '"$READLINE_LINE" "$READLINE_POINT"; READLINE_LINE=""; READLINE_POINT=0\'\n'
                    + script + 'exit\n')
                result = subprocess.run(
                    args, input=script, env=env, cwd=scratch,
                    capture_output=True, text=True, timeout=60)
            else:
                args += ['-c', 'source "$AZ_COMPLETION_SCRIPT"\n' + script]
                result = subprocess.run(
                    args, env=env, cwd=scratch, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.stderr, '')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(tempdir.iterdir()), [])
            return result.stdout + result.stderr

    def test_completion_readline(self):
        modes = (True,) if os.name == 'nt' else (False, True)
        for tempfile_mode in modes:
            with self.subTest(tempfile_mode=tempfile_mode):
                output = self._complete(
                    'az \t\t\x18\x14\n'
                    'az account s\t\t\x18\x14\n'
                    'az --output jso\t\x18\x14\n'
                    'az acc\t\x18\x14\n'
                    'az \t\t\x18\x14\n',
                    interactive=True, tempfile_mode=tempfile_mode)
                for command in ('account', 'vm', 'network', 'storage'):
                    self.assertRegex(output, r'\b' + command + r'\b')
                self.assertEqual(output.count('line=<az >,point=3\n'), 2)
                self.assertIn('line=<az account s>,point=12\n', output)
                self.assertRegex(output, r'(?m)^set +show *$')
                self.assertIn('line=<az --output json>,point=16\n', output)
                self.assertIn('line=<az account >,point=11\n', output)
                self.assertNotIn('filesystem-only', output)
                self.assertNotIn('Traceback', output)

    def test_completion_failure_recovery(self):
        output = self._complete(r'''
COMP_LINE='az '
COMP_POINT=invalid
COMP_TYPE=9
COMPREPLY=(previous)
_az_python_argcomplete az
status=$?
printf 'status=%s,count=%s\n' "$status" "${#COMPREPLY[@]}"
COMP_POINT=${#COMP_LINE}
_az_python_argcomplete az
printf 'recovered=%s\n' "${COMPREPLY[@]}"
COMP_LINE='az account s'
COMP_POINT=${#COMP_LINE}
_az_python_argcomplete az
printf 'current=%s\n' "${COMPREPLY[@]}"
''')
        self.assertIn('status=1,count=0', output.splitlines())
        self.assertIn('recovered=account', output.splitlines())
        self.assertIn('recovered=vm', output.splitlines())
        self.assertIn('current=set', output.splitlines())
        self.assertIn('current=show', output.splitlines())
        self.assertNotIn('Traceback', output)

    def test_completion_tempfile_creation_failure_recovery(self):
        output = self._complete(r'''
tempdir=$TMPDIR
TMPDIR="$tempdir/missing"
COMP_LINE='az '
COMP_POINT=${#COMP_LINE}
COMP_TYPE=9
COMPREPLY=(previous)
_az_python_argcomplete az
status=$?
printf 'status=%s,count=%s\n' "$status" "${#COMPREPLY[@]}"
TMPDIR=$tempdir
_az_python_argcomplete az
printf 'recovered=%s\n' "${COMPREPLY[@]}"
''')
        self.assertIn('status=1,count=0', output.splitlines())
        self.assertIn('recovered=account', output.splitlines())
        self.assertIn('recovered=vm', output.splitlines())

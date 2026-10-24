# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest import TestCase


class ArgcompleteShellTest(TestCase):

    def setUp(self):
        self.bash = shutil.which('bash')
        if not self.bash:
            self.skipTest('Bash is not installed')
        if os.name == 'nt':
            platform = subprocess.run(
                [self.bash, '--noprofile', '--norc', '-c', 'uname -s'],
                check=True, capture_output=True, text=True).stdout
            if not platform.startswith('MINGW'):
                self.skipTest('Windows completion tests require Git Bash')
        self.completion = Path(__file__).resolve().parents[6] / 'az.completion'
        self.assertTrue(self.completion.is_file())
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.tempdir = Path(self.scratch.name) / 'completion files'
        self.tempdir.mkdir()

    def run_completion(self, script, tempfile_mode=True, readline_input=None):
        env = os.environ.copy()
        for name in list(env):
            if name.startswith(('COMP_', '_ARGCOMPLETE', 'ARGCOMPLETE_')):
                del env[name]
        env['TMPDIR'] = self.tempdir.as_posix()
        env['AZURE_CONFIG_DIR'] = (Path(self.scratch.name) / 'config').as_posix()
        env['AZURE_EXTENSION_DIR'] = (Path(self.scratch.name) / 'extensions').as_posix()
        env['AZURE_CORE_COLLECT_TELEMETRY'] = 'no'
        if tempfile_mode:
            env['ARGCOMPLETE_USE_TEMPFILES'] = '1'
        args = [self.bash, '--noprofile', '--norc']
        if readline_input is None:
            args += ['-c', 'source "$1"\n' + script, 'completion-test', self.completion.as_posix()]
        else:
            args += ['-i']
            env['AZ_COMPLETION_SCRIPT'] = self.completion.as_posix()
            env['INPUTRC'] = os.devnull
            env['TERM'] = 'dumb'
            env['PS1'] = 'completion-test> '
            env['PS2'] = ''
            readline_input = (
                'source "$AZ_COMPLETION_SCRIPT"\n'
                'bind "set show-all-if-ambiguous on"\n'
                'bind "set completion-query-items 0"\n'
                'bind "set page-completions off"\n'
                'bind -x \'"\\C-x\\C-t":printf "line=<%s>,point=%s\\n" "$READLINE_LINE" "$READLINE_POINT"; '
                'READLINE_LINE=""; READLINE_POINT=0\'\n' + script + readline_input + 'exit\n')
        result = subprocess.run(
            args, env=env, input=readline_input, cwd=self.scratch.name,
            capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        if readline_input is None:
            self.assertEqual(result.stderr, '')
        self.assertEqual(list(self.tempdir.iterdir()), [])
        return result.stdout if readline_input is None else result.stdout + result.stderr

    def test_bash_completion_tempfile_git_bash(self):
        # Model the MSI backend without relying on Git Bash forwarding file descriptor 8.
        output = self.run_completion(r'''
az() {
    [[ $_ARGCOMPLETE == 1 && $COMP_POINT == 3 && $COMP_TYPE == 9 ]] || return 91
    [[ -f $_ARGCOMPLETE_STDOUT_FILENAME ]] || return 92
    printf 'account\vvm\vnetwork\vstorage' > "$_ARGCOMPLETE_STDOUT_FILENAME"
    printf 'completion stdout must be hidden\n'
    printf 'completion diagnostics must be hidden\n' >&2
}
COMP_LINE='az '
COMP_POINT=${#COMP_LINE}
COMP_TYPE=9
_az_python_argcomplete az
printf '%s\n' "${COMPREPLY[@]}"
complete -p az
''')
        self.assertEqual(output.splitlines()[:4], ['account', 'vm', 'network', 'storage'])
        self.assertIn('-F _az_python_argcomplete az', output)

    def test_bash_completion_descriptors(self):
        output = self.run_completion(r'''
az() {
    [[ ! ${_ARGCOMPLETE_STDOUT_FILENAME+x} && $COMP_LINE == 'az ' ]] || return 91
    printf 'account\vvm\vnetwork\vstorage' >&8
    printf 'completion stdout must be hidden\n'
    printf 'completion diagnostics must be hidden\n' >&2
}
mktemp() { return 93; }
COMP_LINE='az '
COMP_POINT=${#COMP_LINE}
COMP_TYPE=9
_az_python_argcomplete az
printf '%s\n' "${COMPREPLY[@]}"
''', tempfile_mode=False)
        self.assertEqual(output.splitlines(), ['account', 'vm', 'network', 'storage'])

    def test_bash_completion_tempfile_failure(self):
        output = self.run_completion(r'''
az() {
    [[ -f $_ARGCOMPLETE_STDOUT_FILENAME ]] || return 92
    printf 'partial' > "$_ARGCOMPLETE_STDOUT_FILENAME"
    printf 'completion failed\n' >&2
    return 37
}
COMPREPLY=(previous)
_az_python_argcomplete az
status=$?
printf 'status=%s,count=%s\n' "$status" "${#COMPREPLY[@]}"
''')
        self.assertEqual(output, 'status=37,count=0\n')

    def test_bash_completion_tempfile_creation_failure(self):
        output = self.run_completion(r'''
TMPDIR="$TMPDIR/missing"
az() { printf 'backend must not run\n' >&2; return 95; }
COMPREPLY=(previous)
_az_python_argcomplete az
status=$?
printf 'status=%s,count=%s\n' "$status" "${#COMPREPLY[@]}"
''')
        self.assertEqual(output, 'status=1,count=0\n')

    def test_bash_completion_tempfile_read_failure(self):
        output = self.run_completion(r'''
az() { rm -f "$_ARGCOMPLETE_STDOUT_FILENAME"; }
COMPREPLY=(previous)
_az_python_argcomplete az
status=$?
printf 'status=%s,count=%s\n' "$status" "${#COMPREPLY[@]}"
''')
        self.assertEqual(output, 'status=1,count=0\n')

    def test_bash_completion_tempfile_cleanup_failure(self):
        output = self.run_completion(r'''
az() {
    rm -f "$_ARGCOMPLETE_STDOUT_FILENAME" && mkdir "$_ARGCOMPLETE_STDOUT_FILENAME"
}
COMPREPLY=(previous)
_az_python_argcomplete az
status=$?
printf 'status=%s,count=%s\n' "$status" "${#COMPREPLY[@]}"
rmdir "$TMPDIR"/*
''')
        self.assertEqual(output, 'status=1,count=0\n')

    def test_bash_completion_tempfile_current_line(self):
        output = self.run_completion(r'''
az() {
    [[ $COMP_POINT == 12 && $COMP_TYPE == 9 && $_ARGCOMPLETE_COMP_WORDBREAKS == '=' ]] || return 91
    [[ -f $_ARGCOMPLETE_STDOUT_FILENAME ]] || return 92
    case "$COMP_LINE" in
        'az account s') printf 'set\vshow' > "$_ARGCOMPLETE_STDOUT_FILENAME" ;;
        'az --output ') printf 'json\vtable' > "$_ARGCOMPLETE_STDOUT_FILENAME" ;;
        'az account z') : ;;
        *) return 93 ;;
    esac
}
COMP_POINT=12
COMP_TYPE=9
COMP_WORDBREAKS='='
for COMP_LINE in 'az account s' 'az --output ' 'az account z'; do
    _az_python_argcomplete az
    printf 'count=%s' "${#COMPREPLY[@]}"
    printf ',%s' "${COMPREPLY[@]}"
    printf '\n'
done
''')
        self.assertEqual(output, 'count=2,set,show\ncount=2,json,table\ncount=0,\n')

    def test_bash_completion_tempfile_nospace(self):
        output = self.run_completion(r'''
compopt() {
    if [[ $1 == '+o' ]]; then
        return 0
    fi
    printf 'spacing=%s %s\n' "$1" "$2"
}
az() {
    [[ $_ARGCOMPLETE_SUPPRESS_SPACE == 1 && -f $_ARGCOMPLETE_STDOUT_FILENAME ]] || return 91
    printf '%s' "$COMP_LINE" > "$_ARGCOMPLETE_STDOUT_FILENAME"
}
for COMP_LINE in '--output=' 'directory/' 'https:' 'account'; do
    _az_python_argcomplete az
    printf 'candidate=%s\n' "${COMPREPLY[0]}"
done
''')
        self.assertEqual(
            output, 'spacing=-o nospace\ncandidate=--output=\n'
            'spacing=-o nospace\ncandidate=directory/\n'
            'spacing=-o nospace\ncandidate=https:\ncandidate=account\n')

    def test_bash_completion_cli(self):
        if not shutil.which('az') and not shutil.which('az.cmd'):
            self.skipTest('Azure CLI is not installed')
        # Native Windows CLI processes cannot receive Git Bash's completion descriptors.
        modes = (True,) if os.name == 'nt' else (False, True)
        for tempfile_mode in modes:
            with self.subTest(tempfile_mode=tempfile_mode):
                output = self.run_completion(r'''
COMP_LINE='az '
COMP_POINT=${#COMP_LINE}
COMP_TYPE=9
_az_python_argcomplete az
printf '%s\n' "${COMPREPLY[@]}"
COMP_LINE='az account s'
COMP_POINT=${#COMP_LINE}
_az_python_argcomplete az
printf 'partial=%s\n' "${COMPREPLY[@]}"
''', tempfile_mode=tempfile_mode)
                self.assertIn('account', output.splitlines())
                self.assertIn('vm', output.splitlines())
                self.assertIn('partial=set', output.splitlines())
                self.assertIn('partial=show', output.splitlines())

    def test_bash_readline_completion_cli(self):
        if not shutil.which('az') and not shutil.which('az.cmd'):
            self.skipTest('Azure CLI is not installed')
        (Path(self.scratch.name) / 'filesystem-only').mkdir()
        modes = (True,) if os.name == 'nt' else (False, True)
        # Ctrl-X Ctrl-T captures the edited line without executing an Azure command.
        capture = '\x18\x14\n'
        for tempfile_mode in modes:
            with self.subTest(tempfile_mode=tempfile_mode):
                output = self.run_completion(
                    '', tempfile_mode=tempfile_mode,
                    readline_input=''.join(line + capture for line in (
                        'az \t\t', 'az account s\t\t', 'az --output jso\t', 'az acc\t', 'az \t\t')))
                for command in ('account', 'vm', 'network', 'storage', 'set', 'show'):
                    self.assertIn(command, output)
                self.assertEqual(output.count('line=<az >,point=3\n'), 2)
                self.assertIn('line=<az account s>,point=12\n', output)
                self.assertIn('line=<az --output json>,point=16\n', output)
                self.assertIn('line=<az account >,point=11\n', output)
                self.assertRegex(output, r'(?m)^set +show *$')
                self.assertNotIn('filesystem-only', output)
                self.assertNotIn('Traceback', output)

    def test_bash_readline_completion_nospace(self):
        output = self.run_completion(r'''
az() {
    case "$COMP_LINE" in
        'az equal') candidate='equal=' ;;
        'az directory') candidate='directory/' ;;
        'az scheme') candidate='scheme:' ;;
    esac
    printf '%s' "$candidate" > "$_ARGCOMPLETE_STDOUT_FILENAME"
    printf 'backend stdout must be hidden\n'
    printf 'backend diagnostics must be hidden\n' >&2
}
''', readline_input='az equal\t\x18\x14\naz directory\t\x18\x14\naz scheme\t\x18\x14\n')
        self.assertIn('line=<az equal=>,point=9\n', output)
        self.assertIn('line=<az directory/>,point=13\n', output)
        self.assertIn('line=<az scheme:>,point=10\n', output)
        # Interactive Bash echoes the function definition, but not its output.
        self.assertNotIn('\nbackend stdout must be hidden\n', output)
        self.assertNotIn('\nbackend diagnostics must be hidden\n', output)

    def test_bash_readline_completion_closed_descriptors(self):
        if not shutil.which('az') and not shutil.which('az.cmd'):
            self.skipTest('Azure CLI is not installed')
        (Path(self.scratch.name) / 'filesystem-only').mkdir()
        # Run the real CLI with the same unavailable descriptors as a native MSI process.
        output = self.run_completion(
            'az() { command az "$@" 8>&- 9>&-; }\n',
            readline_input='az \t\t\x18\x14\naz acc\t\x18\x14\n')
        for command in ('account', 'vm', 'network', 'storage'):
            self.assertIn(command, output)
        self.assertIn('line=<az account >,point=11\n', output)
        self.assertNotIn('filesystem-only', output)

    def test_bash_completion_cli_failure_recovery(self):
        if not shutil.which('az') and not shutil.which('az.cmd'):
            self.skipTest('Azure CLI is not installed')
        output = self.run_completion(r'''
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
''')
        self.assertIn('status=1,count=0', output.splitlines())
        self.assertIn('recovered=account', output.splitlines())
        self.assertIn('recovered=vm', output.splitlines())

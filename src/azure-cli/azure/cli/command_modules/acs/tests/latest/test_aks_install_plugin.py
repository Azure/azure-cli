# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


# An owned executable, not a mocked subprocess result. The state follows Codex
# rust-v0.144.3 JsonPluginListEntry/JsonMarketplaceListEntry, not native config files.
_HOST_SCRIPT = r'''
import json
import os
from pathlib import Path
import sys

root = Path.cwd()
args = sys.argv[1:]
name = Path(sys.argv[0]).name
assert sys.stdin.read() == '', 'Native stdin must be closed'
assert os.environ['CODEX_HOME'] == str(root / 'codex_home')
assert (root / 'installed/kubectl').read_bytes() == b'fixture kubectl\n'
assert (root / 'installed/kubelogin').read_bytes() == b'fixture kubelogin\n'
with (root / 'native.jsonl').open('a') as stream:
    stream.write(json.dumps([name, *args]) + '\n')
if name == 'node':
    assert args == ['--version'], args
    print('v22.0.0')
    sys.exit(0)
assert name == 'codex', name
state_path = root / 'codex_home/state.json'
state = json.loads(state_path.read_text()) if state_path.exists() else {'installed': [], 'marketplaces': []}
if args == ['plugin', 'list', '--available', '--json']:
    print(json.dumps({'installed': state['installed'], 'available': []}))
elif args == ['plugin', 'marketplace', 'list', '--json']:
    print(json.dumps({'marketplaces': state['marketplaces']}))
elif args == ['plugin', 'marketplace', 'add', 'microsoft/azure-skills', '--json']:
    assert not state['marketplaces'], 'Marketplace must not be re-added'
    state['marketplaces'] = [{
        'name': 'azure-skills', 'root': str(root / 'codex_home/marketplace'),
        'marketplaceSource': {'sourceType': 'git', 'source': 'https://github.com/microsoft/azure-skills.git'},
    }]
    state_path.write_text(json.dumps(state))
    print('{}')
elif args == ['plugin', 'add', 'azure@azure-skills', '--json']:
    assert state['marketplaces'], 'Marketplace must be registered first'
    # Like native add, another add would reinstall and re-enable this plugin.
    state['installed'] = [{
        'pluginId': 'azure@azure-skills', 'name': 'azure', 'marketplaceName': 'azure-skills',
        'version': '1.0.0', 'installed': True, 'enabled': True,
        'source': {'source': 'local', 'path': str(root / 'codex_home/marketplace/azure')},
        'marketplaceSource': {'sourceType': 'git', 'source': 'https://github.com/microsoft/azure-skills.git'},
        'installPolicy': 'AVAILABLE', 'authPolicy': 'ON_USE',
    }]
    state_path.write_text(json.dumps(state))
    print('{}')
else:
    raise AssertionError('Unexpected native command: ' + repr(args))
'''


_ENV_DIRS = (
    'HOME', 'USERPROFILE', 'AZURE_CONFIG_DIR', 'AZURE_EXTENSION_DIR', 'AZURE_EXTENSION_SYS_DIR',
    'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'CLAUDE_CONFIG_DIR',
    'COPILOT_HOME', 'COPILOT_CACHE_HOME', 'CODEX_HOME', 'TMPDIR',
)


def _run_cli_scenario(mode):
    # This function runs only in a new interpreter: no caller's cached Azure
    # cloud, extensions, SDK sessions, credentials or version state can leak in.
    from contextlib import ExitStack
    import socket

    root = Path.cwd()
    blocked = []
    writable = [root / 'azure_config_dir', root / 'installed', root / 'tmpdir']
    executables = [] if mode.startswith('optional') else [str(root / 'bin' / name) for name in ('codex', 'node')]

    def forbidden(event, args):
        blocked.append(event)
        raise AssertionError('Forbidden fixture I/O: ' + event + ' ' + repr(args))

    def audit(event, args):
        # urllib3's local IPv6 capability probe binds ::1 without sending data.
        local_probe = event == 'socket.bind' and args[1] == ('::1', 0)
        if event.startswith('socket.') and event != 'socket.__new__' and not local_probe:
            forbidden(event, args)
        if event in ('os.system', 'os.exec'):
            forbidden(event, args)
        # Python 3.14 can use posix_spawn underneath the real Popen.
        if event in ('subprocess.Popen', 'os.posix_spawn') and args[0] not in executables:
            forbidden(event, args)
        paths = []
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)) and args[0] != os.devnull:
            if args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                paths = [args[0]]
        if event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate'):
            paths = [args[0]]
        if event in ('os.rename', 'os.link', 'os.symlink'):
            paths = list(args[:2])
        for path in paths:
            if not isinstance(path, (str, bytes, os.PathLike)):
                continue
            resolved = Path(os.fsdecode(path))
            # shutil.rmtree uses directory-relative unlink/rmdir on Linux.
            if event in ('os.remove', 'os.rmdir') and args[1] != -1:
                resolved = Path(os.readlink('/proc/self/fd/' + str(args[1]))) / resolved
            resolved = resolved.resolve()
            if not any(resolved == base or base in resolved.parents for base in writable):
                forbidden(event, args)

    sys.addaudithook(audit)
    with ExitStack() as stack:
        stack.enter_context(mock.patch('uuid.getnode', return_value=0x123456789ABC))
        stack.enter_context(mock.patch('requests.sessions.Session.request',
                                       side_effect=lambda *a, **kw: forbidden('requests', a)))
        # handle_version_update checks freshness even with check_version=no.
        connectivity = stack.enter_context(mock.patch('azure.cli.core.util.check_connectivity', return_value=False))
        from azure.cli.core import cloud, extension
        from azure.cli.core._config import GLOBAL_CONFIG_DIR
        from azure.cli.core.mock import DummyCli

        assert GLOBAL_CONFIG_DIR == str(root / 'azure_config_dir')
        assert cloud.CLOUD_CONFIG_FILE == str(root / 'azure_config_dir/clouds.config')
        assert extension.EXTENSIONS_DIR == str(root / 'azure_extension_dir')
        assert extension.EXTENSIONS_SYS_DIR == str(root / 'azure_extension_sys_dir')
        assert extension.DEV_EXTENSION_SOURCES == []
        assert 'ARM_CLOUD_METADATA_URL' not in os.environ
        assert not any(key.startswith('SUDO_') for key in os.environ)

        if mode == 'guards':
            # Prove attempts are counted even when a caller swallows the error.
            probes = [
                lambda: socket.getaddrinfo('fixture.invalid', 443),
                lambda: subprocess.run(['/forbidden/real-host'], check=False),
                lambda: (root / 'codex_home/config.toml').write_text('forbidden'),
            ]
            with socket.socket() as connection:
                probes.append(lambda: connection.connect(('127.0.0.1', 443)))
                for probe in probes:
                    try:
                        probe()
                    except AssertionError:
                        pass
            assert blocked == ['socket.getaddrinfo', 'subprocess.Popen', 'open', 'socket.connect'], blocked
            # Failure during the actual constructor must propagate, while the
            # parent still removes all disposable config and executable files.
            failure = RuntimeError('injected active-cloud constructor failure')
            with mock.patch.object(cloud, 'get_active_cloud', side_effect=failure):
                try:
                    DummyCli()
                except RuntimeError as ex:
                    assert ex is failure, 'Unexpected constructor failure'
                    print('Caught intended constructor failure after four blocked probes')
                    sys.exit(23)
            raise AssertionError('Startup failure was not propagated')

        cli = DummyCli()
        assert connectivity.called, 'Cold startup connectivity was not isolated'
        assert cli.cloud.name == 'AzureCloud'
        assert cli.config.config_dir == str(root / 'azure_config_dir')
        from azure.cli.command_modules.acs import custom

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as stream:
            stream.writestr('bin/linux_amd64/kubelogin', b'fixture kubelogin\n')
        payloads = {
            'https://dl.k8s.io/release/v1.2.3/bin/linux/amd64/kubectl': b'fixture kubectl\n',
            'https://github.com/Azure/kubelogin/releases/download/v4.5.6/kubelogin.zip': archive.getvalue(),
        }
        downloads = []

        def transport(request, **kwargs):
            del kwargs
            url = request.full_url
            assert url in payloads, url
            assert request.get_header('Authorization') is None
            downloads.append(url)
            return io.BytesIO(payloads[url])

        stack.enter_context(mock.patch.object(custom, 'urlopen', side_effect=transport))
        stack.enter_context(mock.patch('platform.system', return_value='Linux'))
        stack.enter_context(mock.patch('platform.machine', return_value='x86_64'))
        arguments = [
            'aks', 'install-cli', '--client-version', '1.2.3', '--kubelogin-version', '4.5.6',
            '--install-location', str(root / 'installed/kubectl'),
            '--kubelogin-install-location', str(root / 'installed/kubelogin'),
        ]
        if mode.startswith('optional'):
            assert sys.stdin.isatty(), 'Regression requires inherited TTY stdin'
            if mode == 'optional-quiet':
                arguments.append('--only-show-errors')
            assert cli.invoke(arguments) == 0
            assert not (root / 'native.jsonl').exists(), 'Optional stage executed a host/runtime'
            assert downloads == list(payloads), downloads
            for name, payload in (('kubectl', b'fixture kubectl\n'), ('kubelogin', b'fixture kubelogin\n')):
                assert (root / 'installed' / name).read_bytes() == payload
            for directory in _ENV_DIRS:
                if directory != 'AZURE_CONFIG_DIR':
                    assert list((root / directory.lower()).iterdir()) == [], directory
            assert not blocked, blocked
            print('Omitted plugin setup returned without input or native I/O')
            return
        arguments.extend(['--install-azure-plugin', '--plugin-hosts', 'codex'])
        assert cli.invoke(arguments) == 0
        state_path = root / 'codex_home/state.json'
        state = json.loads(state_path.read_text())
        assert state['installed'][0]['pluginId'] == 'azure@azure-skills'
        assert state['installed'][0]['enabled'] is True
        assert state['marketplaces'][0]['name'] == 'azure-skills'
        native_log = root / 'native.jsonl'
        calls = [json.loads(line) for line in native_log.read_text().splitlines()]
        assert calls == [
            ['codex', 'plugin', 'list', '--available', '--json'],
            ['codex', 'plugin', 'marketplace', 'list', '--json'],
            ['node', '--version'],
            ['codex', 'plugin', 'marketplace', 'add', 'microsoft/azure-skills', '--json'],
            ['codex', 'plugin', 'list', '--available', '--json'],
            ['codex', 'plugin', 'add', 'azure@azure-skills', '--json'],
        ], calls
        for name, payload in (('kubectl', b'fixture kubectl\n'), ('kubelogin', b'fixture kubelogin\n')):
            binary = root / 'installed' / name
            assert binary.read_bytes() == payload
            assert stat.S_IMODE(binary.stat().st_mode) & 0o111 == 0o111

        # Fixture-owned user change, outside CLI execution. A native reinstall
        # would turn enabled back on; even rewriting identical state is rejected.
        writable.append(root / 'codex_home')
        state['installed'][0]['enabled'] = False
        state_path.write_text(json.dumps(state))
        writable.pop()
        before = (state_path.read_bytes(), state_path.stat().st_mtime_ns)
        assert cli.invoke(arguments) == 0
        assert (state_path.read_bytes(), state_path.stat().st_mtime_ns) == before
        repeated_calls = [json.loads(line) for line in native_log.read_text().splitlines()]
        assert repeated_calls == calls + [['codex', 'plugin', 'list', '--available', '--json']], repeated_calls
        assert downloads == list(payloads) * 2, downloads
        assert list((root / 'tmpdir').iterdir()) == []
        for directory in _ENV_DIRS:
            path = root / directory.lower()
            if directory not in ('AZURE_CONFIG_DIR', 'CODEX_HOME'):
                assert list(path.iterdir()) == [], str(path)
        assert sorted(path.name for path in (root / 'codex_home').iterdir()) == ['state.json']
        assert not blocked, blocked
        print('Fresh install and disabled-existing rerun verified; no forbidden I/O')


@unittest.skipUnless(sys.platform.startswith('linux'), 'Owned executable and fd guards use Linux')
class AKSInstallPluginScenarioTest(unittest.TestCase):
    def invoke_isolated(self, mode='scenario'):
        from contextlib import ExitStack
        import pty

        with tempfile.TemporaryDirectory() as sandbox, ExitStack() as stack:
            root = Path(sandbox)
            # Allowlist, rather than inheriting tokens, sudo, ARM metadata, host
            # homes, extension dev sources or the user's executable search path.
            environment = {
                'PATH': str(root / 'bin'), 'PYTHONPATH': os.pathsep.join(path for path in sys.path if path),
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
                'AZURE_CORE_COLLECT_TELEMETRY': 'no', 'AZURE_CORE_CHECK_VERSION': 'no',
                'LANG': 'C.UTF-8',
            }
            for key in _ENV_DIRS:
                directory = root / key.lower()
                directory.mkdir()
                environment[key] = str(directory)
            environment['TMP'] = environment['TEMP'] = environment['TMPDIR']
            (root / 'azure_config_dir/config').write_text('[cloud]\nname = AzureCloud\n')
            (root / 'bin').mkdir()
            (root / 'installed').mkdir()
            for name in ('codex', 'node', 'npx'):
                executable = root / 'bin' / name
                executable.write_text('#!' + sys.executable + '\n' + _HOST_SCRIPT)
                executable.chmod(0o755)
            command = [sys.executable, '-B', str(Path(__file__).resolve()), mode]
            stdin = subprocess.DEVNULL
            if mode.startswith('optional'):
                master, stdin = pty.openpty()
                stack.callback(os.close, master)
                stack.callback(os.close, stdin)
                # A noninteractive shell can still pass a TTY to az. Keep its
                # master open without ever sending input; do not mock prompting.
                command = ['/bin/bash', '--noprofile', '--norc', '-c',
                           'case "$-" in *i*) exit 99;; esac; exec "$@"', 'fixture', *command]
            try:
                result = subprocess.run(command, cwd=root, env=environment, stdin=stdin,
                                        capture_output=True, text=True,
                                        timeout=30 if mode.startswith('optional') else 90, check=False)
            except subprocess.TimeoutExpired as ex:
                self.fail('CLI did not exit without input: ' + repr((ex.stdout, ex.stderr)))
        self.assertFalse(root.exists(), 'Fixture cleanup left host/config files behind')
        return result

    def test_install_plugin_real_cli_preserves_disabled_existing_plugin(self):
        # Hostile caller state must never reach the child, even when azdev has
        # already imported cloud/extension modules and warmed their global paths.
        with mock.patch.dict(os.environ, {
                'ARM_CLOUD_METADATA_URL': 'https://fixture.invalid/metadata', 'SUDO_UID': '123',
                'AZURE_EXTENSION_DEV_SOURCES': '/forbidden/extensions', 'CODEX_HOME': '/forbidden/codex',
                'AZURE_CONFIG_DIR': '/forbidden/azure', 'HOME': '/forbidden/home'}):
            result = self.invoke_isolated()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Fresh install and disabled-existing rerun verified; no forbidden I/O', result.stdout)

    def test_install_plugin_omitted_in_noninteractive_shell_with_inherited_tty_never_waits(self):
        for mode in ('optional', 'optional-quiet'):
            with self.subTest(mode=mode):
                result = self.invoke_isolated(mode)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, 'Omitted plugin setup returned without input or native I/O\n')
                if mode == 'optional':
                    self.assertEqual(result.stderr.count('--install-azure-plugin'), 1)
                    self.assertEqual(result.stderr.count('--plugin-hosts'), 1)
                else:
                    self.assertEqual(result.stderr, '')
                self.assertNotIn('(y/N)', result.stderr)

    def test_install_plugin_fixture_guards_and_constructor_failure_cleanup(self):
        result = self.invoke_isolated('guards')
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn('Caught intended constructor failure after four blocked probes', result.stdout)
        self.assertNotIn('Startup failure was not propagated', result.stderr)


if __name__ == '__main__':
    _run_cli_scenario(sys.argv[1])

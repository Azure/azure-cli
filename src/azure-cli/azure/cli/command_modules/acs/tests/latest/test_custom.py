# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError
import datetime
from contextlib import contextmanager
from dateutil.parser import parse

import yaml
from azure.cli.command_modules.acs._consts import (
    CONST_AZURE_POLICY_ADDON_NAME,
    CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_USING_AAD_MSI_AUTH,
)
from azure.cli.command_modules.acs.addonconfiguration import (
    _create_or_update_dcr_with_table_readiness_retry,
    ensure_default_log_analytics_workspace_for_monitoring,
)
from azure.cli.command_modules.acs.custom import (
    _download_aks_desktop_asset,
    _extract_aks_desktop_archive,
    _get_aks_desktop_platform,
    _get_aks_desktop_release,
    _get_command_context,
    _get_latest_kubelogin_version,
    _launch_aks_desktop_installer,
    _select_aks_desktop_asset,
    _update_addons,
    aks_install_desktop,
    aks_agentpool_auto_scale_add,
    aks_agentpool_auto_scale_delete,
    aks_agentpool_auto_scale_update,
    aks_agentpool_get_rollback_versions,
    aks_agentpool_rollback,
    aks_agentpool_upgrade,
    aks_enable_addons,
    aks_stop,
    aks_upgrade,
    is_monitoring_addon_enabled,
    k8s_install_cli,
    k8s_install_kubectl,
    k8s_install_kubelogin,
    merge_kubernetes_configurations,
    _update_upgrade_settings,
)
from azure.cli.command_modules.acs.managed_cluster_decorator import (
    AKSManagedClusterModels,
)
from azure.cli.command_modules.acs.tests.latest.mocks import (
    MockCLI,
    MockClient,
    MockCmd,
    MockUrlretrieveUrlValidator,
)
from azure.cli.command_modules.acs.tests.latest.utils import (
    create_kubelogin_zip,
    get_test_data_file_path,
)
from azure.cli.core.util import CLIError
from azure.cli.core.profiles import ResourceType
from azure.core.exceptions import HttpResponseError
from azure.mgmt.containerservice.models import (
    ManagedClusterAddonProfile,
)
from azure.cli.core.azclierror import (
    ClientRequestError,
    FileOperationError,
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
    ResourceNotFoundError,
    ValidationError,
)


class AcsInstallCliPluginTest(unittest.TestCase):
    def setUp(self):
        self.cmd = mock.Mock()
        self.calls = mock.Mock()
        for name, kwargs in (
                ('get_arch_for_cli_binary', {'return_value': 'arm64'}),
                ('k8s_install_kubectl', {}), ('k8s_install_kubelogin', {}),
                ('maybe_install_azure_plugin', {'create': True})):
            patcher = mock.patch('azure.cli.command_modules.acs.custom.' + name, **kwargs)
            self.calls.attach_mock(patcher.start(), name)
            self.addCleanup(patcher.stop)
        patcher = mock.patch.dict(os.environ, {}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_default_binary_arguments_and_plugin_stage_order_are_preserved(self):
        k8s_install_cli(self.cmd)
        self.assertEqual(self.calls.mock_calls, [
            mock.call.get_arch_for_cli_binary(),
            mock.call.k8s_install_kubectl(self.cmd, 'latest', None, None, arch='arm64'),
            mock.call.k8s_install_kubelogin(self.cmd, 'latest', None, None, arch='arm64', gh_token=None),
            mock.call.maybe_install_azure_plugin(self.cmd, None, None),
        ])

    def test_explicit_hosts_normalize_without_changing_binary_arguments_or_forwarding_token(self):
        k8s_install_cli(self.cmd, '1.2.3', '/kubectl', 'https://kubectl.example',
                        '4.5.6', '/kubelogin', 'https://kubelogin.example', 'binary-only-token',
                        True, ['codex', 'claude-code', 'codex'])
        self.assertEqual(self.calls.mock_calls, [
            mock.call.get_arch_for_cli_binary(),
            mock.call.k8s_install_kubectl(self.cmd, '1.2.3', '/kubectl', 'https://kubectl.example', arch='arm64'),
            mock.call.k8s_install_kubelogin(self.cmd, '4.5.6', '/kubelogin', 'https://kubelogin.example',
                                            arch='arm64', gh_token='binary-only-token'),
            mock.call.maybe_install_azure_plugin(self.cmd, True, ['claude-code', 'codex']),
        ])

    def test_false_is_forwarded_after_both_binaries(self):
        k8s_install_cli(self.cmd, install_azure_plugin=False)
        self.assertEqual(self.calls.mock_calls[-1], mock.call.maybe_install_azure_plugin(self.cmd, False, None))
        self.assertEqual(len(self.calls.mock_calls), 4)

    def test_invalid_plugin_options_are_rejected_before_binary_side_effects(self):
        for enabled, hosts in ((True, None), (True, []), (True, ['pi']), (False, ['codex']), (None, ['codex'])):
            with self.subTest(enabled=enabled, hosts=hosts), self.assertRaises(InvalidArgumentValueError):
                k8s_install_cli(self.cmd, install_azure_plugin=enabled, plugin_hosts=hosts)
            self.assertEqual(self.calls.mock_calls, [])
        with mock.patch.dict(os.environ, {'SUDO_USER': 'user'}), self.assertRaises(InvalidArgumentValueError):
            k8s_install_cli(self.cmd, install_azure_plugin=True, plugin_hosts=['codex'])
        self.assertEqual(self.calls.mock_calls, [])

    def test_either_binary_failure_prevents_plugin_stage(self):
        for binary in ('k8s_install_kubectl', 'k8s_install_kubelogin'):
            with self.subTest(binary=binary):
                self.calls.reset_mock(side_effect=True)
                getattr(self.calls, binary).side_effect = ClientRequestError('binary failed')
                with self.assertRaisesRegex(ClientRequestError, 'binary failed'):
                    k8s_install_cli(self.cmd, install_azure_plugin=True, plugin_hosts=['codex'])
                self.calls.maybe_install_azure_plugin.assert_not_called()
                if binary == 'k8s_install_kubectl':
                    self.calls.k8s_install_kubelogin.assert_not_called()


# A new interpreter keeps import-time cloud/extension paths and CLI global state
# isolated even when this file is run outside the repository's test environment.
_PLUGIN_PARSER_SCRIPT = r'''
import io
import json
import os
import sys
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from unittest import mock

blocked = []
def forbidden(*args, **kwargs):
    blocked.append(repr(args))
    raise AssertionError('Parser fixture attempted external I/O: ' + repr(args))

with ExitStack() as stack:
    for target in ('socket.getaddrinfo', 'socket.socket.connect', 'socket.socket.connect_ex',
                   'subprocess.Popen', 'os.system', 'requests.sessions.Session.request'):
        stack.enter_context(mock.patch(target, side_effect=forbidden))
    # Patch before construction: handle_version_update may query freshness even
    # when ordinary CLI version-check configuration is disabled.
    stack.enter_context(mock.patch('uuid.getnode', return_value=0x123456789ABC))
    stack.enter_context(mock.patch('azure.cli.core.util.check_connectivity', return_value=False))
    from azure.cli.core import get_default_cli
    from azure.cli.core import cloud, extension
    from azure.cli.command_modules.acs import custom, _azure_plugin
    assert cloud.CLOUD_CONFIG_FILE.startswith(os.environ['AZURE_CONFIG_DIR'])
    assert extension.EXTENSIONS_DIR == os.environ['AZURE_EXTENSION_DIR']
    cli = get_default_cli()
    assert cli.cloud.name == 'AzureCloud'
    assert cli.config.config_dir == os.environ['AZURE_CONFIG_DIR']
    cli.config.set_value('core', 'collect_telemetry', 'no')
    cli.config.set_value('core', 'check_version', 'no')
    mode, arguments = json.loads(sys.argv[1])
    if mode == 'parser':
        handler = stack.enter_context(mock.patch.object(custom, 'k8s_install_cli', autospec=True))
        handler.return_value = None
    else:
        stack.enter_context(mock.patch.object(custom, 'k8s_install_kubectl'))
        stack.enter_context(mock.patch.object(custom, 'k8s_install_kubelogin'))
        handler = stack.enter_context(mock.patch.object(_azure_plugin, 'install_plugin', return_value=True))
    output, errors = io.StringIO(), io.StringIO()
    with redirect_stdout(output), redirect_stderr(errors):
        try:
            code = cli.invoke(['aks', 'install-cli', *arguments])
        except SystemExit as ex:
            code = ex.code
    assert not blocked, blocked
    calls = [{key: value for key, value in call.kwargs.items() if key != 'cmd'}
             for call in handler.call_args_list]
    hosts = [call.args[0] for call in handler.call_args_list] if mode != 'parser' else []
    print(json.dumps({'code': code, 'calls': calls, 'hosts': hosts, 'stderr': errors.getvalue()}))
'''


class AcsInstallCliPluginParserTest(unittest.TestCase):
    def invoke_isolated(self, arguments, mode='parser'):
        with tempfile.TemporaryDirectory() as root:
            environment = {key: value for key, value in os.environ.items()
                           if not key.startswith(('AZURE_', 'ARM_', 'SUDO_', 'XDG_', 'CLAUDE_', 'COPILOT_', 'CODEX_'))}
            for key in ('HOME', 'USERPROFILE', 'AZURE_CONFIG_DIR', 'AZURE_EXTENSION_DIR', 'AZURE_EXTENSION_SYS_DIR',
                        'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'CLAUDE_CONFIG_DIR', 'COPILOT_HOME',
                        'COPILOT_CACHE_HOME', 'CODEX_HOME'):
                environment[key] = os.path.join(root, key.lower())
                os.makedirs(environment[key])
            environment.update(AZURE_CORE_COLLECT_TELEMETRY='no', AZURE_CORE_CHECK_VERSION='no',
                               PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                               PYTHONPATH=os.pathsep.join(path for path in sys.path if path))
            result = subprocess.run([sys.executable, '-B', '-c', _PLUGIN_PARSER_SCRIPT, json.dumps([mode, arguments])],
                                    cwd=root, env=environment, stdin=subprocess.DEVNULL, capture_output=True,
                                    text=True, timeout=90, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_real_parser_registers_three_states_and_all_host_choices(self):
        for arguments, enabled, hosts in (
                ([], None, None), (['--install-azure-plugin', 'false'], False, None),
                (['--install-azure-plugin', '--plugin-hosts', 'claude-code', 'github-copilot', 'codex'],
                 True, ['claude-code', 'github-copilot', 'codex']),
                (['--install-azure-plugin', 'true', '--plugin-hosts', 'codex'], True, ['codex'])):
            with self.subTest(arguments=arguments):
                result = self.invoke_isolated(arguments)
                self.assertEqual(result['code'], 0, result['stderr'])
                self.assertEqual(len(result['calls']), 1)
                self.assertEqual(result['calls'][0]['install_azure_plugin'], enabled)
                self.assertEqual(result['calls'][0]['plugin_hosts'], hosts)

    def test_real_parser_rejects_unknown_or_empty_hosts_before_handler(self):
        for hosts in (['pi'], ['vscode'], ['aks'], []):
            with self.subTest(hosts=hosts):
                result = self.invoke_isolated(['--install-azure-plugin', '--plugin-hosts', *hosts])
                self.assertEqual(result['code'], 2)
                self.assertEqual(result['calls'], [])

    def test_explicit_disclosure_is_visible_with_only_show_errors(self):
        result = self.invoke_isolated(['--install-azure-plugin', '--plugin-hosts', 'codex', '--only-show-errors'],
                                      mode='flow')
        self.assertEqual(result['code'], 0, result['stderr'])
        self.assertEqual(result['hosts'], ['codex'])
        for disclosure in ('full Azure plugin', 'user/global', 'MCP', 'hooks', '@azure/mcp@latest',
                           'hidden/stale', 'enablement', 'authentication', 'trust'):
            self.assertIn(disclosure, result['stderr'])


class AcsCustomCommandTest(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()
        self.models = AKSManagedClusterModels(MockCmd(self.cli), ResourceType.MGMT_CONTAINERSERVICE)

    def test_merge_credentials_non_existent(self):
        self.assertRaises(CLIError, merge_kubernetes_configurations, 'non', 'existent', False)

    def test_merge_credentials_broken_yaml(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        with open(existing.name, 'w+') as stream:
            stream.write('{ broken')
        self.addCleanup(os.remove, existing.name)

        obj2 = {
            'clusters': [
                'cluster2'
            ],
            'contexts': [
                'context2'
            ],
            'users': [
                'user2'
            ],
            'current-context': 'cluster2',
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        self.assertRaises(CLIError, merge_kubernetes_configurations, existing.name, addition.name, False)

    def test_merge_credentials(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster1'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context1'
                }
            ],
            'current-context': 'context1',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)
        self.addCleanup(os.remove, existing.name)

        obj2 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'current-context': 'aztest',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'user2',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        merge_kubernetes_configurations(existing.name, addition.name, False)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.assertEqual(len(merged['clusters']), 2)
        self.assertEqual(merged['clusters'], [obj1['clusters'][0], obj2['clusters'][0]])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'], [obj1['contexts'][0], obj2['contexts'][0]])
        self.assertEqual(len(merged['users']), 2)
        self.assertEqual(merged['users'], [obj1['users'][0], obj2['users'][0]])
        self.assertEqual(merged['current-context'], obj2['current-context'])

    def test_merge_admin_credentials(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'apiVersion': 'v1',
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'aztest'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'aztest'
                }
            ],
            'current-context': 'aztest',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'clusterUser_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)
        self.addCleanup(os.remove, existing.name)
        obj2 = {
            'apiVersion': 'v1',
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'aztest'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterAdmin_aztest_aztest'
                    },
                    'name': 'aztest'
                }
            ],
            'current-context': 'aztest',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'clusterAdmin_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token2'
                    }
                }
            ]
        }
        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        merge_kubernetes_configurations(existing.name, addition.name, False)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.assertEqual(len(merged['clusters']), 1)
        self.assertEqual([c['cluster'] for c in merged['clusters']],
                         [{'certificate-authority-data': 'certificateauthoritydata1',
                           'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'}])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'],
                         [{'context': {'cluster': 'aztest', 'user': 'clusterUser_aztest_aztest'},
                           'name': 'aztest'},
                          {'context': {'cluster': 'aztest', 'user': 'clusterAdmin_aztest_aztest'},
                           'name': 'aztest-admin'}])
        self.assertEqual(len(merged['users']), 2)
        self.assertEqual([u['name'] for u in merged['users']],
                         ['clusterUser_aztest_aztest', 'clusterAdmin_aztest_aztest'])
        self.assertEqual(merged['current-context'], 'aztest-admin')

    def test_merge_credentials_missing(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': None,
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context1'
                }
            ],
            'current-context': 'context1',
            'kind': 'Config',
            'preferences': {},
            'users': [
                {
                    'name': 'user1',
                    'user': {
                        'client-certificate-data': 'clientcertificatedata1',
                        'client-key-data': 'clientkeydata1',
                        'token': 'token1'
                    }
                }
            ]
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)
        self.addCleanup(os.remove, existing.name)

        obj2 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://aztest-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'aztest',
                        'user': 'clusterUser_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'current-context': 'context2',
            'kind': 'Config',
            'preferences': {},
            'users': None
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        self.addCleanup(os.remove, addition.name)

        merge_kubernetes_configurations(existing.name, addition.name, False)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.assertEqual(len(merged['clusters']), 1)
        self.assertEqual(merged['clusters'], [obj2['clusters'][0]])
        self.assertEqual(len(merged['contexts']), 2)
        self.assertEqual(merged['contexts'], [obj1['contexts'][0], obj2['contexts'][0]])
        self.assertEqual(len(merged['users']), 1)
        self.assertEqual(merged['users'], [obj1['users'][0]])
        self.assertEqual(merged['current-context'], obj2['current-context'])

    def test_merge_credentials_already_present(self):
        existing = tempfile.NamedTemporaryFile(delete=False)
        existing.close()
        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj1 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://cluster1-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster1'
                },
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://cluster2-aztest-abc123-abcd1234.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'cluster1User_aztest_aztest'
                    },
                    'name': 'context1'
                },
                {
                    'context': {
                        'cluster': 'cluster1',
                        'user': 'cluster1User_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'users': [
                {
                    'name': 'cluster1User_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token2'
                    }
                },
                {
                    'name': 'cluster2User_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token2'
                    }
                }
            ],
            'current-context': 'context1',
        }
        with open(existing.name, 'w+') as stream:
            yaml.safe_dump(obj1, stream)

        obj2 = {
            'clusters': [
                {
                    'cluster': {
                        'certificate-authority-data': 'certificateauthoritydata1',
                        'server': 'https://other2-aztest-abc456-abcd4567.hcp.eastus.azmk8s.io:443'
                    },
                    'name': 'cluster2'
                }
            ],
            'contexts': [
                {
                    'context': {
                        'cluster': 'cluster2',
                        'user': 'cluster1_aztest_aztest'
                    },
                    'name': 'context2'
                }
            ],
            'users': [
                {
                    'name': 'cluster2User_aztest_aztest',
                    'user': {
                        'client-certificate-data': 'someclientcertificatedata2',
                        'client-key-data': 'someclientkeydata2',
                        'token': 'token3'
                    }
                }
            ],
            'current-context': 'some-context',
        }

        with open(addition.name, 'w+') as stream:
            yaml.safe_dump(obj2, stream)
        with self.assertRaises(CLIError):
            merge_kubernetes_configurations(existing.name, addition.name, False)

        merge_kubernetes_configurations(existing.name, addition.name, True)
        self.addCleanup(os.remove, addition.name)

        with open(existing.name, 'r') as stream:
            merged = yaml.safe_load(stream)
        self.addCleanup(os.remove, existing.name)

        self.assertEqual(len(merged['clusters']), 2)
        expected_clusters = [
            obj1['clusters'][0],
            obj2['clusters'][0]
        ]
        self.assertEqual(merged['clusters'], expected_clusters)
        self.assertEqual(len(merged['contexts']), 2)
        expected_contexts = [
            obj1['contexts'][0],
            obj2['contexts'][0]
        ]
        self.assertEqual(merged['contexts'], expected_contexts)
        self.assertEqual(len(merged['users']), 2)
        expected_users = [
            obj1['users'][0],
            obj2['users'][0]
        ]
        self.assertEqual(merged['users'], expected_users)
        self.assertEqual(merged['current-context'], obj2['current-context'])

    @unittest.skipIf(os.name == 'nt', 'Symlink test not applicable on Windows')
    def test_merge_credentials_rejects_symlink(self):
        # Create a real kubeconfig file and a symlink pointing to it
        target = tempfile.NamedTemporaryFile(delete=False, suffix='.kubeconfig')
        target.close()
        with open(target.name, 'w') as f:
            yaml.safe_dump({'clusters': [], 'contexts': [], 'users': [],
                            'current-context': '', 'kind': 'Config'}, f)
        self.addCleanup(os.remove, target.name)

        symlink_path = target.name + '.link'
        os.symlink(target.name, symlink_path)
        self.addCleanup(lambda: os.remove(symlink_path) if os.path.islink(symlink_path) else None)

        addition = tempfile.NamedTemporaryFile(delete=False)
        addition.close()
        obj = {
            'clusters': [{'cluster': {'server': 'https://test'}, 'name': 'c1'}],
            'contexts': [{'context': {'cluster': 'c1', 'user': 'u1'}, 'name': 'ctx1'}],
            'users': [{'name': 'u1', 'user': {'token': 'tok'}}],
            'current-context': 'ctx1',
        }
        with open(addition.name, 'w') as f:
            yaml.safe_dump(obj, f)
        self.addCleanup(os.remove, addition.name)

        # Should raise CLIError when existing_file is a symlink
        with self.assertRaises(CLIError):
            merge_kubernetes_configurations(symlink_path, addition.name, False)

        # Verify the symlink target was not modified
        with open(target.name, 'r') as f:
            content = yaml.safe_load(f)
        self.assertEqual(content['clusters'], [])

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location', return_value='eastus')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client', autospec=True)
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client', autospec=True)
    def test_update_addons(self, rg_def, get_resource_groups_client, get_resources_client):
        # http_application_routing enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None

        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=True)
        self.assertIn(CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME, instance.addon_profiles)
        addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(addon_profile.enabled)

        # http_application_routing disabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=False)
        addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertFalse(addon_profile.enabled)

        # monitoring added
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=True)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertTrue(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertFalse(routing_addon_profile.enabled)

        # monitoring disabled, routing enabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=True)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(routing_addon_profile.enabled)
        self.assertEqual(sorted(list(instance.addon_profiles)), [CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME, CONST_MONITORING_ADDON_NAME])

        # azurepolicy added
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'azure-policy', enable=True)
        azurepolicy_addon_profile = instance.addon_profiles[CONST_AZURE_POLICY_ADDON_NAME]
        self.assertTrue(azurepolicy_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(routing_addon_profile.enabled)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_addon_profile.enabled)

        # azurepolicy disabled, routing enabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'azure-policy', enable=False)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'http_application_routing', enable=True)
        azurepolicy_addon_profile = instance.addon_profiles[CONST_AZURE_POLICY_ADDON_NAME]
        self.assertFalse(azurepolicy_addon_profile.enabled)
        monitoring_addon_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_addon_profile.enabled)
        routing_addon_profile = instance.addon_profiles[CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME]
        self.assertTrue(routing_addon_profile.enabled)
        self.assertEqual(sorted(list(instance.addon_profiles)), [CONST_AZURE_POLICY_ADDON_NAME, CONST_HTTP_APPLICATION_ROUTING_ADDON_NAME, CONST_MONITORING_ADDON_NAME])

        # kube-dashboard disabled, no existing dashboard addon profile
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=False)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertFalse(dashboard_addon_profile.enabled)

        # kube-dashboard enabled, no existing dashboard addon profile
        instance.addon_profiles.pop(CONST_KUBE_DASHBOARD_ADDON_NAME, None)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=True)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertTrue(dashboard_addon_profile.enabled)

        # kube-dashboard disabled, there's existing dashboard addon profile
        instance.addon_profiles.pop(CONST_KUBE_DASHBOARD_ADDON_NAME, None)
        # test lower cased key name
        instance.addon_profiles['kubedashboard'] = ManagedClusterAddonProfile(enabled=True)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=False)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertFalse(dashboard_addon_profile.enabled)

        # kube-dashboard enabled, there's existing dashboard addon profile
        instance.addon_profiles.pop(CONST_KUBE_DASHBOARD_ADDON_NAME, None)
        # test lower cased key name
        instance.addon_profiles['kubedashboard'] = ManagedClusterAddonProfile(enabled=False)
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'kube-dashboard', enable=True)
        dashboard_addon_profile = instance.addon_profiles[CONST_KUBE_DASHBOARD_ADDON_NAME]
        self.assertTrue(dashboard_addon_profile.enabled)

        # monitoring enabled and then enabled again should error
        instance = mock.Mock()
        instance.addon_profiles = None
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=True)
        with self.assertRaises(CLIError):
            instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                      'clitest000001', 'clitest000001', 'monitoring', enable=True)

        # virtual-node enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'virtual-node', enable=True, subnet_name='foo')
        self.assertIn('aciConnectorLinux', instance.addon_profiles)
        addon_profile = instance.addon_profiles['aciConnectorLinux']
        self.assertTrue(addon_profile.enabled)

        # virtual-node disabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'virtual-node', enable=False)
        addon_profile = instance.addon_profiles['aciConnectorLinux']
        self.assertFalse(addon_profile.enabled)

        # ingress-appgw enabled
        instance = mock.MagicMock()
        instance.addon_profiles = None
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'ingress-appgw', enable=True, appgw_subnet_cidr='10.2.0.0/16')
        self.assertIn('ingressApplicationGateway', instance.addon_profiles)
        addon_profile = instance.addon_profiles['ingressApplicationGateway']
        self.assertTrue(addon_profile.enabled)

        # ingress-appgw disabled
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'ingress-appgw', enable=False)
        addon_profile = instance.addon_profiles['ingressApplicationGateway']
        self.assertFalse(addon_profile.enabled)

        # monitoring enable with camelCase addon key does NOT preserve enableRetinaNetworkFlags
        instance = mock.MagicMock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(
                enabled=False,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                    'enableRetinaNetworkFlags': 'True',
                },
            ),
        }
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=True)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertTrue(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config.get('enableRetinaNetworkFlags'))

        # monitoring disable sets config to None
        instance = mock.MagicMock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(
                enabled=True,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                    'enableRetinaNetworkFlags': 'True',
                },
            ),
        }
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config)

        # monitoring disable without CNL also sets config to None
        instance = mock.MagicMock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(
                enabled=True,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                },
            ),
        }
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config)

        # monitoring disable with camelCase key (omsAgent) sets config to None
        instance = mock.MagicMock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(
                enabled=True,
                config={
                    'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
                    CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
                    'enableRetinaNetworkFlags': 'True',
                },
            ),
        }
        # The addon key normalization in _update_addons remaps camelCase to lowercase
        instance = _update_addons(MockCmd(self.cli), instance, '00000000-0000-0000-0000-000000000000',
                                  'clitest000001', 'clitest000001', 'monitoring', enable=False)
        monitoring_profile = instance.addon_profiles[CONST_MONITORING_ADDON_NAME]
        self.assertFalse(monitoring_profile.enabled)
        self.assertIsNone(monitoring_profile.config)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_emit_warnings(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'kubectl')
            k8s_install_kubectl(mock.MagicMock(), client_version='1.2.3', install_location=test_location)
            self.assertEqual(mock_url_retrieve.call_count, 1)
            # 3 warnings, 1st for arch, 2nd for download result, 3rd for updating PATH
            self.assertEqual(logger_mock.warning.call_count, 3)  # 3 warnings, one for download result
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_create_installation_dir(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'foo', 'kubectl')
            k8s_install_kubectl(mock.MagicMock(), client_version='1.2.3', install_location=test_location)
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_emit_warnings(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = os.path.realpath(tempfile.mkdtemp())  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'kubelogin')
            k8s_install_kubelogin(mock.MagicMock(), client_version='0.0.4', install_location=test_location, arch="amd64")
            self.assertEqual(mock_url_retrieve.call_count, 1)
            # 3 warnings, 1st for download result, 2nd for moving file, 3rd for updating PATH
            self.assertEqual(logger_mock.warning.call_count, 3)  # 3 warnings, one for download result
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_create_installation_dir(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = tempfile.mkdtemp()  # tempfile.TemporaryDirectory() is no available on 2.7
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            k8s_install_kubelogin(mock.MagicMock(), client_version='0.0.4', install_location=test_location, arch="amd64")
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubectl_with_custom_source_url(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = lambda _, install_location: open(install_location, 'a').close()
        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubectl')
            test_ver = '1.2.5'
            test_source_url = 'http://url1'
            k8s_install_kubectl(mock.MagicMock(), client_version=test_ver, install_location=test_location, source_url=test_source_url)
            mock_url_retrieve.assert_called_with(MockUrlretrieveUrlValidator(test_source_url, test_ver), mock.ANY)
        finally:
            shutil.rmtree(temp_dir)

    @unittest.skip('No such file or directory')
    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_with_custom_source_url(self, logger_mock, mock_url_retrieve):
        mock_url_retrieve.side_effect = create_kubelogin_zip
        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            test_ver = '1.2.6'
            test_source_url = 'http://url2'
            k8s_install_kubelogin(mock.MagicMock(), client_version=test_ver, install_location=test_location, source_url=test_source_url, arch="amd64")
            mock_url_retrieve.assert_called_with(MockUrlretrieveUrlValidator(test_source_url, test_ver), mock.ANY)
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_with_gh_token(self, logger_mock, mock_url_retrieve, mock_urlopen_read):
        """Test that gh_token parameter is properly passed to HTTP requests when installing kubelogin."""
        # Mock the GitHub API response for latest release
        mock_urlopen_read.return_value = b'{"tag_name": "v0.0.30"}'
        # Mock the zip file download
        mock_url_retrieve.side_effect = create_kubelogin_zip
        
        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')
            test_gh_token = 'ghp_test_token_123'
            
            # Install kubelogin with gh_token
            k8s_install_kubelogin(
                mock.MagicMock(),
                client_version='latest',
                install_location=test_location,
                arch="amd64",
                gh_token=test_gh_token
            )
            
            # Verify gh_token was passed to _urlopen_read for GitHub API call
            mock_urlopen_read.assert_called_once()
            call_args = mock_urlopen_read.call_args
            self.assertEqual(call_args.kwargs.get('gh_token'), test_gh_token)
            
            # Verify the installation completed
            self.assertTrue(os.path.exists(test_location))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom._urlretrieve')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_k8s_install_kubelogin_latest_version_fallback(self, logger_mock, mock_url_retrieve, mock_urlopen_read):
        """Test that the version file is used to install kubelogin when the GitHub API is rate limited."""
        mock_urlopen_read.side_effect = [
            HTTPError('https://api.github.com/repos/Azure/kubelogin/releases/latest', 403, 'rate limited', None, None),
            b'v0.0.30',
        ]
        mock_url_retrieve.side_effect = create_kubelogin_zip

        try:
            temp_dir = tempfile.mkdtemp()
            test_location = os.path.join(temp_dir, 'foo', 'kubelogin')

            k8s_install_kubelogin(
                mock.MagicMock(), client_version='latest', install_location=test_location,
                arch="amd64", gh_token='ghp_test_token_123')

            fallback_call = mock_urlopen_read.call_args_list[1]
            self.assertEqual(
                fallback_call[0][0],
                'https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-version.txt')
            self.assertIsNone(fallback_call.kwargs.get('gh_token'))
            mock_url_retrieve.assert_called_with(
                MockUrlretrieveUrlValidator('https://github.com/Azure/kubelogin/releases/download', 'v0.0.30'),
                mock.ANY)
            self.assertTrue(
                any('rate limit was exceeded' in str(call) for call in logger_mock.warning.call_args_list))
        finally:
            shutil.rmtree(temp_dir)

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_get_latest_kubelogin_version_fallback_only_on_rate_limit(self, logger_mock, mock_urlopen_read):
        """Test that the version file is only used for a rate limit, other failures are surfaced as they are."""
        api_url = 'https://api.github.com/repos/Azure/kubelogin/releases/latest'
        cases = [
            (HTTPError(api_url, 429, 'too many requests', None, None), True),
            (HTTPError(api_url, 500, 'internal server error', None, None), False),
            (URLError('[Errno -2] Name or service not known'), False),
        ]
        for error, expect_fallback in cases:
            with self.subTest(error=error):
                mock_urlopen_read.reset_mock()
                mock_urlopen_read.side_effect = [error, b'v0.0.30']

                if expect_fallback:
                    self.assertEqual(_get_latest_kubelogin_version('azurecloud'), 'v0.0.30')
                    self.assertEqual(mock_urlopen_read.call_count, 2)
                else:
                    with self.assertRaises(type(error)) as cm:
                        _get_latest_kubelogin_version('azurecloud')
                    self.assertIs(cm.exception, error)
                    mock_urlopen_read.assert_called_once()

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_get_latest_kubelogin_version_fallback_without_tag_prefix(self, logger_mock, mock_urlopen_read):
        """Test that a bare version is normalized to the release tag used to build the download url."""
        mock_urlopen_read.side_effect = [
            HTTPError('https://api.github.com/repos/Azure/kubelogin/releases/latest', 403, 'rate limited', None, None),
            b'0.0.30\n',
        ]

        self.assertEqual(_get_latest_kubelogin_version('azurecloud'), 'v0.0.30')

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_get_latest_kubelogin_version_all_sources_fail(self, logger_mock, mock_urlopen_read):
        """Test that both failures are reported when the GitHub API and the version file are unavailable."""
        mock_urlopen_read.side_effect = [
            HTTPError('https://api.github.com/repos/Azure/kubelogin/releases/latest', 403, 'rate limited', None, None),
            HTTPError('https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-version.txt',
                      500, 'internal server error', None, None),
        ]

        with self.assertRaises(ClientRequestError) as cm:
            _get_latest_kubelogin_version('azurecloud')
        self.assertIn('403', str(cm.exception))
        self.assertIn('500', str(cm.exception))

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    @mock.patch('azure.cli.command_modules.acs.custom.logger')
    def test_get_latest_kubelogin_version_unexpected_fallback_content(self, logger_mock, mock_urlopen_read):
        """Test that content which is not exactly a version is rejected, not used to build the download url."""
        for content in (b'<html>not found</html>', b'v0.0.30/../../evil', b'\xff\xfe\x00binary'):
            with self.subTest(content=content):
                mock_urlopen_read.reset_mock()
                mock_urlopen_read.side_effect = [
                    HTTPError('https://api.github.com/repos/Azure/kubelogin/releases/latest',
                              403, 'rate limited', None, None),
                    content,
                ]

                with self.assertRaises(ClientRequestError):
                    _get_latest_kubelogin_version('azurecloud')

    def test_aks_install_desktop_platform(self):
        cases = [
            ('Windows', 'AMD64', ('win', 'x64')),
            ('Windows', 'arm64', ('win', 'arm64')),
            ('Darwin', 'x86_64', ('mac', 'x64')),
            ('Darwin', 'aarch64', ('mac', 'arm64')),
            ('Linux', 'x86_64', ('linux', 'x64')),
            ('Linux', 'armv7l', ('linux', 'armv7l')),
        ]
        for system, machine, expected in cases:
            with self.subTest(system=system, machine=machine):
                with mock.patch(
                        'azure.cli.command_modules.acs.custom.platform.system',
                        return_value=system), mock.patch(
                            'azure.cli.command_modules.acs.custom.platform.machine',
                            return_value=machine):
                    self.assertEqual(_get_aks_desktop_platform(), expected)

    @mock.patch('azure.cli.command_modules.acs.custom.platform.machine', return_value='mips64')
    @mock.patch('azure.cli.command_modules.acs.custom.platform.system', return_value='Linux')
    def test_aks_install_desktop_unsupported_architecture(self, _, __):
        with self.assertRaises(ValidationError):
            _get_aks_desktop_platform()

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    def test_aks_install_desktop_specific_version(self, mock_urlopen_read):
        mock_urlopen_read.return_value = b'{"tag_name": "v0.9.1", "assets": []}'
        release, version = _get_aks_desktop_release('0.9.1')
        self.assertEqual(version, '0.9.1')
        self.assertEqual(release['tag_name'], 'v0.9.1')
        mock_urlopen_read.assert_called_once_with(
            'https://api.github.com/repos/Azure/aks-desktop/releases/tags/v0.9.1', gh_token=None)

    @mock.patch.dict(os.environ, {'GH_TOKEN': 'ignored-by-release-helper'})
    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    def test_aks_install_desktop_metadata_authentication(self, mock_urlopen_read):
        mock_urlopen_read.return_value = b'{"tag_name": "v0.9.1", "assets": []}'
        for version, endpoint in ((None, 'latest'), ('0.9.1', 'tags/v0.9.1'), ('v0.9.1', 'tags/v0.9.1')):
            for token in (None, 'fake-gh-token'):
                with self.subTest(version=version, token=token):
                    mock_urlopen_read.reset_mock()
                    release, release_version = _get_aks_desktop_release(version, gh_token=token)
                    self.assertEqual(release['tag_name'], 'v0.9.1')
                    self.assertEqual(release_version, '0.9.1')
                    mock_urlopen_read.assert_called_once_with(
                        'https://api.github.com/repos/Azure/aks-desktop/releases/' + endpoint, gh_token=token)

    @mock.patch('http.client.HTTPSConnection.connect', side_effect=AssertionError('Network connection blocked'))
    def test_aks_install_desktop_rejects_newlines_in_token(self, mock_connect):
        secret = 'fake-sensitive-token'
        for version in (None, '0.9.1'):
            for newline in ('\r', '\n', '\r\n'):
                with self.subTest(version=version, newline=repr(newline)):
                    # Keep the real urllib header validation: it can echo malformed credentials.
                    with self.assertRaises(InvalidArgumentValueError) as cm:
                        _get_aks_desktop_release(version, gh_token=secret + newline)
                    self.assertIn('GitHub token', str(cm.exception))
                    self.assertNotIn(secret, str(cm.exception))
                    self.assertNotIn(secret, ' '.join(cm.exception.recommendations))
                    mock_connect.assert_not_called()

    @mock.patch('http.client.HTTPSConnection.connect', side_effect=AssertionError('Network connection blocked'))
    def test_aks_install_desktop_valid_token_reaches_transport(self, mock_connect):
        for token in (None, 'fake-sensitive-token'):
            with self.subTest(token=token):
                mock_connect.reset_mock()
                with self.assertRaisesRegex(AssertionError, 'Network connection blocked'):
                    _get_aks_desktop_release(gh_token=token)
                mock_connect.assert_called_once()

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    def test_aks_install_desktop_rejects_empty_version(self, mock_urlopen_read):
        mock_urlopen_read.return_value = b'{"tag_name": "v0.9.1", "assets": []}'
        for version in ('', ' ', '\t', 'v'):
            with self.subTest(version=version):
                mock_urlopen_read.reset_mock()
                with self.assertRaises(InvalidArgumentValueError):
                    _get_aks_desktop_release(version)
                mock_urlopen_read.assert_not_called()

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    def test_aks_install_desktop_metadata_rate_limit(self, mock_urlopen_read):
        url = 'https://api.github.com/repos/Azure/aks-desktop/releases/latest'
        for status, headers in ((429, None), (403, {'X-RateLimit-Remaining': '0'}),
                                (403, {'Retry-After': '60'})):
            for token in (None, 'fake-gh-token'):
                with self.subTest(status=status, headers=headers, token=token):
                    mock_urlopen_read.reset_mock()
                    error = HTTPError(url, status, 'Forbidden', headers, None)
                    self.addCleanup(error.close)
                    mock_urlopen_read.side_effect = error
                    kwargs = {'gh_token': token} if token else {}
                    with self.assertRaises(ClientRequestError) as cm:
                        _get_aks_desktop_release(**kwargs)
                    message = str(cm.exception)
                    recommendation = ' '.join(cm.exception.recommendations)
                    self.assertIn('rate limit', message.lower())
                    self.assertIn(str(status), message)
                    self.assertIn(url, message)
                    self.assertIn('wait', recommendation.lower())
                    if token:
                        self.assertIn('quota', recommendation.lower())
                        self.assertNotIn('--gh-token', recommendation)
                    else:
                        self.assertIn('GH_TOKEN', recommendation)
                        self.assertNotIn('--gh-token', recommendation)
                        self.assertIn('reset', recommendation.lower())
                    self.assertNotIn('--version', recommendation)
                    self.assertNotIn('fake-gh-token', message + recommendation)
                    mock_urlopen_read.assert_called_once()

    @mock.patch('azure.cli.command_modules.acs.custom._urlopen_read')
    def test_aks_install_desktop_metadata_errors(self, mock_urlopen_read):
        url = 'https://api.github.com/repos/Azure/aks-desktop/releases/latest'
        cases = [
            (HTTPError(url, 403, 'Forbidden', None, None), '403'),
            (HTTPError(url, 403, 'Forbidden', {'X-RateLimit-Remaining': '10'}, None), '403'),
            (HTTPError(url, 401, 'Unauthorized', None, None), '401'),
            (HTTPError(url, 404, 'Not Found', None, None), '404'),
            (URLError('network unavailable'), 'network unavailable'),
            (b'not JSON', 'Expecting value'),
        ]
        for response, context in cases:
            with self.subTest(context=context, response=response):
                mock_urlopen_read.reset_mock()
                if isinstance(response, HTTPError):
                    self.addCleanup(response.close)
                mock_urlopen_read.side_effect = response if isinstance(response, Exception) else None
                mock_urlopen_read.return_value = response
                with self.assertRaises(ClientRequestError) as cm:
                    _get_aks_desktop_release()
                message = str(cm.exception)
                recommendation = ' '.join(cm.exception.recommendations)
                self.assertIn('release metadata', message)
                self.assertIn(url, message)
                self.assertIn(context, message)
                self.assertNotIn('rate limit', message.lower())
                self.assertNotIn('--version', recommendation)
                mock_urlopen_read.assert_called_once()

    @mock.patch('azure.cli.command_modules.acs.custom._launch_aks_desktop_installer')
    @mock.patch('urllib.request.build_opener')
    @mock.patch('azure.cli.command_modules.acs.custom.urlopen')
    @mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform', return_value=('win', 'x64'))
    def test_aks_install_desktop_token_only_reaches_metadata(
            self, _, mock_urlopen, mock_build_opener, mock_launch):
        metadata = (
            b'{"tag_name": "v0.9.1", "assets": [{"name": "aks-desktop-0.9.1-win-x64.exe",'
            b'"browser_download_url": "https://github.com/Azure/aks-desktop/releases/download/v0.9.1/'
            b'aks-desktop-0.9.1-win-x64.exe", "digest": "sha256:' +
            hashlib.sha256(b'installer').hexdigest().encode() + b'"}]}')

        def launch(path, system, version):
            with open(path, 'rb') as installer:
                self.assertEqual(installer.read(), b'installer')

        mock_launch.side_effect = launch
        cases = [
            ({}, None, None),
            ({'GH_TOKEN': ''}, None, None),
            ({'GH_TOKEN': 'environment-token'}, None, 'Bearer environment-token'),
            ({'GH_TOKEN': 'environment-token'}, 'explicit-token', 'Bearer explicit-token'),
            ({'GH_TOKEN': 'environment-token'}, '', None),
            ({'GH_TOKEN': 'invalid\r\ntoken'}, 'explicit-token', 'Bearer explicit-token'),
        ]
        for environment, explicit, authorization in cases:
            with self.subTest(environment=environment, explicit=explicit), \
                    mock.patch.dict(os.environ, environment, clear=True):
                mock_urlopen.reset_mock()
                mock_build_opener.reset_mock()
                mock_launch.reset_mock()
                mock_urlopen.return_value = io.BytesIO(metadata)
                mock_build_opener.return_value.open.return_value = io.BytesIO(b'installer')
                aks_install_desktop(None, version='0.9.1', gh_token=explicit)
                mock_urlopen.assert_called_once()
                metadata_request = mock_urlopen.call_args[0][0]
                self.assertEqual(metadata_request.full_url,
                                 'https://api.github.com/repos/Azure/aks-desktop/releases/tags/v0.9.1')
                self.assertEqual(metadata_request.get_header('Authorization'), authorization)
                mock_build_opener.return_value.open.assert_called_once()
                request = mock_build_opener.return_value.open.call_args[0][0]
                self.assertEqual(request.full_url,
                                 'https://github.com/Azure/aks-desktop/releases/download/v0.9.1/'
                                 'aks-desktop-0.9.1-win-x64.exe')
                self.assertIsNone(request.get_header('Authorization'))
                self.assertNotIn('token', str(request.header_items()))
                mock_launch.assert_called_once()

    @mock.patch('http.client.HTTPSConnection.connect', side_effect=AssertionError('Network connection blocked'))
    @mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform', return_value=('win', 'x64'))
    def test_aks_install_desktop_rejects_newlines_in_environment_token(self, _, mock_connect):
        secret = 'fake-environment-secret'
        for newline in ('\r', '\n', '\r\n'):
            with self.subTest(newline=repr(newline)), \
                    mock.patch.dict(os.environ, {'GH_TOKEN': secret + newline}):
                with self.assertRaises(InvalidArgumentValueError) as cm:
                    aks_install_desktop(None)
                self.assertIn('GitHub token', str(cm.exception))
                self.assertNotIn(secret, str(cm.exception))
                self.assertNotIn(secret, ' '.join(cm.exception.recommendations))
                mock_connect.assert_not_called()

    @mock.patch.dict(os.environ, {'DISPLAY': ':0'})
    @mock.patch('azure.cli.command_modules.acs.custom.shutil.which', return_value='/usr/bin/xdg-open')
    @mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                return_value={'ID': 'ubuntu', 'ID_LIKE': 'debian'})
    def test_aks_install_desktop_selects_native_linux_package(self, _, __):
        release = {
            'assets': [
                {'name': 'aks-desktop-0.9.1-linux-x64.tar.gz'},
                {'name': 'aks-desktop_0.9.1-1_amd64.deb'},
            ]
        }
        asset = _select_aks_desktop_asset(
            release, '0.9.1', 'linux', 'x64')
        self.assertEqual(asset['name'], 'aks-desktop_0.9.1-1_amd64.deb')

    def test_aks_install_desktop_linux_package_compatibility(self):
        deb = 'aks-desktop_0.9.1-1_amd64.deb'
        archive = 'aks-desktop-0.9.1-linux-x64.tar.gz'
        release = {'assets': [{'name': deb}, {'name': archive}]}
        cases = [
            ({'ID': 'debian'}, '/usr/bin/xdg-open', {'DISPLAY': ':0'}, deb),
            ({'ID': 'linuxmint', 'ID_LIKE': 'ubuntu debian'}, '/usr/bin/xdg-open', {'DISPLAY': ':0'}, deb),
            ({'ID': 'ubuntu'}, '/usr/bin/xdg-open', {'WAYLAND_DISPLAY': 'wayland-0'}, deb),
            ({'ID': 'ubuntu'}, '/usr/bin/xdg-open', {}, archive),
            ({'ID': 'ubuntu'}, '/usr/bin/xdg-open', {'DISPLAY': '', 'WAYLAND_DISPLAY': ''}, archive),
            ({'ID': 'fedora'}, '/usr/bin/xdg-open', {'DISPLAY': ':0'}, archive),
            ({'ID': 'rhel', 'ID_LIKE': 'fedora'}, '/usr/bin/xdg-open', {'DISPLAY': ':0'}, archive),
            ({'ID': 'arch'}, '/usr/bin/xdg-open', {'DISPLAY': ':0'}, archive),
            ({}, '/usr/bin/xdg-open', {'DISPLAY': ':0'}, archive),
            ({'ID': 'ubuntu'}, None, {'DISPLAY': ':0'}, archive),
        ]
        for os_release, launcher, environment, expected in cases:
            with self.subTest(os_release=os_release, launcher=launcher, environment=environment), \
                    mock.patch.dict(os.environ, environment, clear=True), mock.patch(
                        'azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                        return_value=os_release), mock.patch(
                            'azure.cli.command_modules.acs.custom.shutil.which', return_value=launcher):
                asset = _select_aks_desktop_asset(release, '0.9.1', 'linux', 'x64')
                self.assertEqual(asset['name'], expected)

    @mock.patch.dict(os.environ, {'DISPLAY': ':0'})
    @mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                side_effect=OSError('os-release unavailable'))
    def test_aks_install_desktop_missing_os_release_uses_archive(self, mock_os_release):
        release = {'assets': [
            {'name': 'aks-desktop_0.9.1-1_amd64.deb'},
            {'name': 'aks-desktop-0.9.1-linux-x64.tar.gz'},
        ]}
        asset = _select_aks_desktop_asset(release, '0.9.1', 'linux', 'x64')
        self.assertEqual(asset['name'], 'aks-desktop-0.9.1-linux-x64.tar.gz')
        mock_os_release.assert_called_once_with()

    @mock.patch.dict(os.environ, {'DISPLAY': ':0'})
    @mock.patch('azure.cli.command_modules.acs.custom.shutil.which', return_value='/usr/bin/xdg-open')
    @mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                return_value={'ID': 'debian'})
    def test_aks_install_desktop_missing_deb_uses_archive(self, mock_os_release, mock_which):
        release = {'assets': [{'name': 'aks-desktop-0.9.1-linux-x64.tar.gz'}]}
        asset = _select_aks_desktop_asset(release, '0.9.1', 'linux', 'x64')
        self.assertEqual(asset['name'], 'aks-desktop-0.9.1-linux-x64.tar.gz')
        mock_os_release.assert_called_once_with()
        mock_which.assert_called_once_with('xdg-open')

    @mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                return_value={'ID': 'fedora'})
    def test_aks_install_desktop_rejects_incompatible_only_asset(self, _):
        with self.assertRaises(ResourceNotFoundError):
            _select_aks_desktop_asset(
                {'assets': [{'name': 'aks-desktop_0.9.1-1_amd64.deb'}]},
                '0.9.1', 'linux', 'x64')

    def test_aks_install_desktop_missing_asset(self):
        with self.assertRaises(ResourceNotFoundError):
            _select_aks_desktop_asset(
                {'assets': []}, '0.9.1', 'mac', 'arm64')

    @mock.patch('urllib.request.build_opener')
    def test_aks_install_desktop_verifies_download_digest(self, mock_build_opener):
        content = b'AKS Desktop'
        response = mock.MagicMock()
        response.__enter__.return_value.read.side_effect = [content, b'']
        mock_build_opener.return_value.open.return_value = response
        asset = {
            'browser_download_url':
                'https://github.com/Azure/aks-desktop/releases/download/v0.9.1/'
                'aks-desktop-0.9.1-win-x64.exe',
            'digest': 'sha256:' + hashlib.sha256(content).hexdigest(),
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = os.path.join(temp_dir, 'installer.exe')
            _download_aks_desktop_asset(asset, destination)
            with open(destination, 'rb') as downloaded:
                self.assertEqual(downloaded.read(), content)

    @mock.patch('urllib.request.build_opener')
    def test_aks_install_desktop_rejects_invalid_digest(self, mock_build_opener):
        cases = [{}, *({'digest': digest} for digest in (
            None, 123, [], {}, '', 'sha256:', 'sha256:' + 'a' * 63,
            'sha256:' + 'a' * 65, 'sha256:' + 'g' * 64, 'sha512:' + 'a' * 64))]
        for metadata in cases:
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory() as temp_dir:
                asset = {
                    'browser_download_url':
                        'https://github.com/Azure/aks-desktop/releases/download/v0.9.1/installer.exe',
                    **metadata,
                }
                destination = os.path.join(temp_dir, 'installer.exe')
                with self.assertRaisesRegex(ClientRequestError, 'valid SHA-256 digest'):
                    _download_aks_desktop_asset(asset, destination)
                mock_build_opener.assert_not_called()
                self.assertFalse(os.path.exists(destination))

    @mock.patch('azure.cli.command_modules.acs.custom._launch_aks_desktop_installer')
    @mock.patch('urllib.request.build_opener')
    @mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_release')
    @mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform', return_value=('win', 'x64'))
    def test_aks_install_desktop_digest_failure_prevents_launch(
            self, _, mock_release, mock_build_opener, mock_launch):
        for digest, error in ((None, 'valid SHA-256 digest'), ('sha256:' + '0' * 64, 'did not match')):
            with self.subTest(digest=digest):
                mock_build_opener.reset_mock()
                response = mock.MagicMock()
                response.__enter__.return_value.read.side_effect = [b'installer', b'']
                mock_build_opener.return_value.open.return_value = response
                mock_release.return_value = ({'assets': [{
                    'name': 'aks-desktop-0.9.1-win-x64.exe',
                    'browser_download_url':
                        'https://github.com/Azure/aks-desktop/releases/download/v0.9.1/'
                        'aks-desktop-0.9.1-win-x64.exe',
                    'digest': digest,
                }]}, '0.9.1')
                with self.assertRaisesRegex(ClientRequestError, error):
                    aks_install_desktop(None)
                mock_launch.assert_not_called()
                if digest is None:
                    mock_build_opener.assert_not_called()
                else:
                    mock_build_opener.return_value.open.assert_called_once()

    @contextmanager
    def _aks_desktop_archive_extractor(self, fallback):
        if fallback:
            # Match the old API: accepting filter= must fail, and an unfiltered call is never safe.
            def legacy_extractall(archive, path='.', members=None, *, numeric_owner=False):
                raise AssertionError('The compatibility extractor must not call extractall')

            with mock.patch.object(tarfile, 'data_filter', None, create=True), \
                    mock.patch.object(tarfile.TarFile, 'extractall', legacy_extractall):
                yield
        else:
            if not hasattr(tarfile, 'data_filter'):
                self.skipTest('Native tar extraction filters unavailable')
            # Exercise pre-3.14 defaults even on newer Python.
            with mock.patch.object(tarfile.TarFile, 'extraction_filter',
                                   staticmethod(lambda member, path: member), create=True):
                yield

    @staticmethod
    def _write_aks_desktop_archive(archive_path, members):
        with tarfile.open(archive_path, 'w:gz') as archive:
            for name, member_type, linkname in members:
                member = tarfile.TarInfo(name)
                member.type = member_type
                member.linkname = linkname
                member.mode = 0o755
                if member.isfile():
                    member.size = len(b'executable')
                    archive.addfile(member, io.BytesIO(b'executable'))
                else:
                    archive.addfile(member)

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_rejects_unsafe_members(self):
        cases = [
            [('dir', tarfile.DIRTYPE, ''), ('dir/foo', tarfile.SYMTYPE, '.'),
             ('dir/foo/../../outside', tarfile.REGTYPE, '')],
            [('dir', tarfile.DIRTYPE, ''), ('dir/link', tarfile.LNKTYPE, '../outside'),
             ('dir/link', tarfile.REGTYPE, '')],
            [('../outside', tarfile.REGTYPE, '')],
            [('aks-desktop/', tarfile.SYMTYPE, '../outside')],
            [('aks-desktop\\', tarfile.SYMTYPE, '../outside')],
            [('aks-desktop/', tarfile.LNKTYPE, 'missing')],
            [('aks-desktop\\', tarfile.LNKTYPE, 'missing')],
            [('pipe', tarfile.FIFOTYPE, '')],
            [('device', tarfile.CHRTYPE, '')],
            [('device', tarfile.BLKTYPE, '')],
            [('unknown', b'Z', '')],
            [('aks-desktop', tarfile.SYMTYPE, '/etc/passwd')],
            [('aks-desktop', tarfile.LNKTYPE, '/etc/passwd')],
        ]
        for fallback in (False, True):
            for members in cases:
                with self.subTest(fallback=fallback, members=members), \
                        self._aks_desktop_archive_extractor(fallback), \
                        tempfile.TemporaryDirectory() as temp_dir:
                    archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                    destination = os.path.join(temp_dir, 'install')
                    outside = os.path.join(temp_dir, 'outside')
                    with open(outside, 'wb') as sentinel:
                        sentinel.write(b'unchanged')
                    self._write_aks_desktop_archive(archive_path, members)
                    with self.assertRaises(FileOperationError):
                        _extract_aks_desktop_archive(archive_path, destination)
                    with open(outside, 'rb') as sentinel:
                        self.assertEqual(sentinel.read(), b'unchanged')
                    for name in ('pipe', 'device', 'unknown', 'aks-desktop'):
                        self.assertFalse(os.path.lexists(os.path.join(destination, name)))

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_rejects_existing_escaping_symlinks(self):
        cases = [
            [('link/aks-desktop', tarfile.REGTYPE, '')],
            [('link', tarfile.REGTYPE, '')],
            [('link/dir', tarfile.DIRTYPE, '')],
            [('link', tarfile.SYMTYPE, 'safe')],
            [('hardlink', tarfile.LNKTYPE, 'link/aks-desktop')],
        ]
        for fallback in (False, True):
            for members in cases:
                with self.subTest(fallback=fallback, members=members), \
                        self._aks_desktop_archive_extractor(fallback), \
                        tempfile.TemporaryDirectory() as temp_dir:
                    archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                    destination = os.path.join(temp_dir, 'install')
                    outside = os.path.join(temp_dir, 'outside')
                    os.mkdir(destination)
                    os.mkdir(outside)
                    sentinel_path = os.path.join(outside, 'aks-desktop')
                    with open(sentinel_path, 'wb') as sentinel:
                        sentinel.write(b'unchanged')
                    os.symlink(outside, os.path.join(destination, 'link'))
                    self._write_aks_desktop_archive(archive_path, members)
                    with self.assertRaises(FileOperationError):
                        _extract_aks_desktop_archive(archive_path, destination)
                    with open(sentinel_path, 'rb') as sentinel:
                        self.assertEqual(sentinel.read(), b'unchanged')
                    self.assertEqual(os.listdir(outside), ['aks-desktop'])

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_preserves_safe_links(self):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                destination = os.path.join(temp_dir, 'install')
                self._write_aks_desktop_archive(archive_path, [
                    ('app/aks-desktop', tarfile.REGTYPE, ''),
                    ('app/subdir/symlink', tarfile.SYMTYPE, '../aks-desktop'),
                    ('app/hardlink', tarfile.LNKTYPE, 'app/aks-desktop'),
                    ('alias', tarfile.SYMTYPE, 'app'),
                    ('alias/resource', tarfile.REGTYPE, ''),
                ])
                _extract_aks_desktop_archive(archive_path, destination)
                for name in ('aks-desktop', 'subdir/symlink', 'hardlink', 'resource'):
                    with open(os.path.join(destination, 'app', name), 'rb') as executable:
                        self.assertEqual(executable.read(), b'executable')
                executable_path = os.path.join(destination, 'app', 'aks-desktop')
                self.assertTrue(os.stat(executable_path).st_mode & 0o100)
                self.assertEqual(os.readlink(os.path.join(destination, 'app', 'subdir', 'symlink')),
                                 '../aks-desktop')
                self.assertTrue(os.path.samefile(executable_path, os.path.join(destination, 'app', 'hardlink')))
                self.assertFalse(os.path.islink(os.path.join(destination, 'app', 'hardlink')))

    def test_aks_install_desktop_archive_supports_legacy_python(self):
        with self._aks_desktop_archive_extractor(True), tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, 'installer.tar.gz')
            destination = os.path.join(temp_dir, 'install')
            self._write_aks_desktop_archive(archive_path, [('aks-desktop', tarfile.REGTYPE, '')])
            _extract_aks_desktop_archive(archive_path, destination)
            with open(os.path.join(destination, 'aks-desktop'), 'rb') as executable:
                self.assertEqual(executable.read(), b'executable')

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_resolves_forward_hardlinks(self):
        with self._aks_desktop_archive_extractor(True), tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, 'installer.tar.gz')
            destination = os.path.join(temp_dir, 'install')
            self._write_aks_desktop_archive(archive_path, [
                ('app/first', tarfile.LNKTYPE, 'app/second'),
                ('app/second', tarfile.LNKTYPE, 'app/aks-desktop'),
                ('app/aks-desktop', tarfile.REGTYPE, ''),
            ])
            _extract_aks_desktop_archive(archive_path, destination)
            for name in ('first', 'second'):
                link = os.path.join(destination, 'app', name)
                self.assertFalse(os.path.islink(link))
                self.assertTrue(os.path.samefile(link, os.path.join(destination, 'app', 'aks-desktop')))
                with open(link, 'rb') as executable:
                    self.assertEqual(executable.read(), b'executable')

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_rejects_deferred_hardlink_collisions(self):
        for link_name, later_name in [('a', 'a'), ('alias/a', 'dir/a')]:
            with self.subTest(link_name=link_name), self._aks_desktop_archive_extractor(True), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                destination = os.path.join(temp_dir, 'install')
                with tarfile.open(archive_path, 'w:gz') as archive:
                    alias = tarfile.TarInfo('alias')
                    alias.type = tarfile.SYMTYPE
                    alias.linkname = 'dir'
                    archive.addfile(alias)
                    link = tarfile.TarInfo(link_name)
                    link.type = tarfile.LNKTYPE
                    link.linkname = 'b'
                    link.mode = 0o755
                    archive.addfile(link)
                    for name, content, mode in [(later_name, b'later-a', 0o600), ('b', b'b-content', 0o755)]:
                        member = tarfile.TarInfo(name)
                        member.size = len(content)
                        member.mode = mode
                        archive.addfile(member, io.BytesIO(content))
                with self.assertRaisesRegex(FileOperationError, 'Ambiguous.*deferred.*hardlink'):
                    _extract_aks_desktop_archive(archive_path, destination)
                for name, content, mode in [(later_name, b'later-a', 0o600), ('b', b'b-content', 0o755)]:
                    path = os.path.join(destination, name)
                    with open(path, 'rb') as extracted:
                        self.assertEqual(extracted.read(), content)
                    self.assertEqual(os.stat(path).st_mode & 0o777, mode)
                self.assertFalse(os.path.samefile(os.path.join(destination, later_name),
                                                  os.path.join(destination, 'b')))

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_rejects_deferred_hardlink_parent_rebinding(self):
        with self._aks_desktop_archive_extractor(True), tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, 'installer.tar.gz')
            destination = os.path.join(temp_dir, 'install')
            self._write_aks_desktop_archive(archive_path, [
                ('alias', tarfile.SYMTYPE, 'first'),
                ('alias/a', tarfile.LNKTYPE, 'b'),
                ('alias', tarfile.SYMTYPE, 'second'),
                ('b', tarfile.REGTYPE, ''),
            ])
            with self.assertRaisesRegex(FileOperationError, 'Ambiguous.*deferred.*hardlink'):
                _extract_aks_desktop_archive(archive_path, destination)
            self.assertEqual(os.readlink(os.path.join(destination, 'alias')), 'second')
            self.assertFalse(os.path.lexists(os.path.join(destination, 'first')))
            self.assertFalse(os.path.lexists(os.path.join(destination, 'second')))
            with open(os.path.join(destination, 'b'), 'rb') as extracted:
                self.assertEqual(extracted.read(), b'executable')

    def test_aks_install_desktop_archive_rejects_unresolved_hardlinks(self):
        cases = [
            [('first', tarfile.LNKTYPE, 'second'), ('second', tarfile.LNKTYPE, 'first')],
            [('first', tarfile.LNKTYPE, 'missing')],
            [('dir', tarfile.DIRTYPE, ''), ('first', tarfile.LNKTYPE, 'dir')],
        ]
        for members in cases:
            with self.subTest(members=members), self._aks_desktop_archive_extractor(True), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                destination = os.path.join(temp_dir, 'install')
                self._write_aks_desktop_archive(archive_path, members)
                with self.assertRaisesRegex(FileOperationError, 'hardlink'):
                    _extract_aks_desktop_archive(archive_path, destination)
                self.assertFalse(os.path.lexists(os.path.join(destination, 'first')))

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_rejects_root_replacement(self):
        for member_type in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            for name in ('.', 'app/..', 'alias'):
                with self.subTest(member_type=member_type, name=name), \
                        self._aks_desktop_archive_extractor(True), \
                        tempfile.TemporaryDirectory() as temp_dir:
                    archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                    destination = os.path.join(temp_dir, 'install')
                    os.mkdir(destination)
                    os.symlink('.', os.path.join(destination, 'alias'))
                    self._write_aks_desktop_archive(archive_path, [
                        ('aks-desktop', tarfile.REGTYPE, ''),
                        (name, member_type, 'aks-desktop'),
                    ])
                    with self.assertRaises(FileOperationError):
                        _extract_aks_desktop_archive(archive_path, destination)
                    self.assertTrue(os.path.isdir(destination))
                    self.assertFalse(os.path.islink(destination))

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_normalizes_safe_symlink_targets(self):
        with self._aks_desktop_archive_extractor(True), tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, 'installer.tar.gz')
            destination = os.path.join(temp_dir, 'install')
            self._write_aks_desktop_archive(archive_path, [
                ('app/aks-desktop', tarfile.REGTYPE, ''),
                ('app/link', tarfile.SYMTYPE, 'unused/../aks-desktop'),
            ])
            _extract_aks_desktop_archive(archive_path, destination)
            link = os.path.join(destination, 'app', 'link')
            self.assertEqual(os.readlink(link), 'aks-desktop')
            with open(link, 'rb') as executable:
                self.assertEqual(executable.read(), b'executable')

    def test_aks_install_desktop_archive_does_not_create_outside_parents(self):
        with self._aks_desktop_archive_extractor(True), tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, 'installer.tar.gz')
            destination = os.path.join(temp_dir, 'install')
            self._write_aks_desktop_archive(archive_path, [
                ('../outside/../install/app/aks-desktop', tarfile.REGTYPE, ''),
            ])
            _extract_aks_desktop_archive(archive_path, destination)
            self.assertFalse(os.path.lexists(os.path.join(temp_dir, 'outside')))
            with open(os.path.join(destination, 'app', 'aks-desktop'), 'rb') as executable:
                self.assertEqual(executable.read(), b'executable')

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_failure_does_not_launch(self, mock_popen):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                self._write_aks_desktop_archive(archive_path, [
                    ('aks-desktop', tarfile.REGTYPE, ''),
                    ('../outside', tarfile.REGTYPE, ''),
                ])
                with mock.patch('os.path.expanduser', return_value=temp_dir):
                    with self.assertRaises(FileOperationError):
                        _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                mock_popen.assert_not_called()
                self.assertEqual(os.listdir(os.path.join(temp_dir, '.local', 'share', 'aks-desktop')), [])

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_reinstall_preserves_old_on_failure(self, mock_popen):
        for fallback in (False, True):
            for failure in ('missing-executable', 'extract', 'chmod', 'backup', 'publish'):
                with self.subTest(fallback=fallback, failure=failure), \
                        self._aks_desktop_archive_extractor(fallback), \
                        tempfile.TemporaryDirectory() as temp_dir:
                    mock_popen.reset_mock()
                    archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                    install_root = os.path.join(temp_dir, '.local', 'share', 'aks-desktop')
                    install_dir = os.path.join(install_root, '0.9.1')
                    os.makedirs(install_dir)
                    for name in ('aks-desktop', 'stale'):
                        with open(os.path.join(install_dir, name), 'wb') as output:
                            output.write(b'old installation')
                    members = [('app/resource', tarfile.REGTYPE, '')]
                    if failure != 'missing-executable':
                        members.append(('app/aks-desktop', tarfile.REGTYPE, ''))
                    if failure == 'extract':
                        members.append(('../outside', tarfile.REGTYPE, ''))
                    self._write_aks_desktop_archive(archive_path, members)
                    real_replace, real_chmod = os.replace, os.chmod
                    publication_attempts = []

                    def replace(source, destination):
                        if failure == 'backup' and source == install_dir:
                            raise OSError('backup failed')
                        if failure == 'publish' and destination == install_dir:
                            publication_attempts.append(source)
                            if len(publication_attempts) == 1:
                                raise OSError('publication failed')
                        return real_replace(source, destination)

                    def chmod(path, mode, *args, **kwargs):
                        if failure == 'chmod' and os.path.basename(path) == 'aks-desktop':
                            raise OSError('chmod failed')
                        return real_chmod(path, mode, *args, **kwargs)

                    with (
                        mock.patch('os.path.expanduser', return_value=temp_dir),
                        mock.patch('azure.cli.command_modules.acs.custom.os.replace', side_effect=replace),
                        mock.patch('azure.cli.command_modules.acs.custom.os.chmod', side_effect=chmod),
                    ):
                        with self.assertRaises(FileOperationError):
                            _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                    mock_popen.assert_not_called()
                    for name in ('aks-desktop', 'stale'):
                        with open(os.path.join(install_dir, name), 'rb') as installed:
                            self.assertEqual(installed.read(), b'old installation')
                    self.assertEqual(sorted(os.listdir(install_dir)), ['aks-desktop', 'stale'])
                    self.assertEqual(os.listdir(install_root), ['0.9.1'])
                    if failure == 'publish':
                        self.assertEqual(len(publication_attempts), 2)

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_reinstall_replaces_contents(self, mock_popen):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                install_root = os.path.join(temp_dir, '.local', 'share', 'aks-desktop')
                install_dir = os.path.join(install_root, '0.9.1')
                os.makedirs(install_dir)
                with open(os.path.join(install_dir, 'stale'), 'wb') as output:
                    output.write(b'old installation')
                with tarfile.open(archive_path, 'w:gz') as archive:
                    member = tarfile.TarInfo('app/aks-desktop')
                    member.mode = 0o600
                    member.size = len(b'new executable')
                    archive.addfile(member, io.BytesIO(b'new executable'))
                real_replace = os.replace
                staged_dirs = []

                def replace(source, destination):
                    if destination == install_dir:
                        staged_dirs.append(source)
                        self.assertEqual(os.path.dirname(source), install_root)
                        self.assertNotEqual(source, install_dir)
                        executable = os.path.join(source, 'app', 'aks-desktop')
                        self.assertTrue(os.stat(executable).st_mode & 0o100)
                    return real_replace(source, destination)

                with mock.patch('os.path.expanduser', return_value=temp_dir), \
                        mock.patch('azure.cli.command_modules.acs.custom.os.replace', side_effect=replace):
                    _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                    _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                self.assertEqual(len(staged_dirs), 2)
                self.assertNotEqual(staged_dirs[0], staged_dirs[1])
                self.assertEqual(os.listdir(install_root), ['0.9.1'])
                self.assertEqual(os.listdir(install_dir), ['app'])
                executable = os.path.join(install_dir, 'app', 'aks-desktop')
                with open(executable, 'rb') as installed:
                    self.assertEqual(installed.read(), b'new executable')
                self.assertEqual(mock_popen.call_args_list, [mock.call([executable]), mock.call([executable])])
                mock_popen.reset_mock()

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_backup_cleanup_failure_still_launches(self, mock_popen):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                mock_popen.reset_mock()
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                install_root = os.path.join(temp_dir, '.local', 'share', 'aks-desktop')
                install_dir = os.path.join(install_root, '0.9.1')
                os.makedirs(os.path.join(install_dir, 'resources'))
                with open(os.path.join(install_dir, 'resources', 'old'), 'wb') as output:
                    output.write(b'old resources')
                self._write_aks_desktop_archive(archive_path, [('aks-desktop', tarfile.REGTYPE, '')])
                real_rmtree = shutil.rmtree
                backups = []

                def remove_tree(path, *args, **kwargs):
                    if os.path.basename(path).startswith('.0.9.1-backup-'):
                        backups.append(path)
                        raise PermissionError('backup cleanup denied')
                    return real_rmtree(path, *args, **kwargs)

                with mock.patch('os.path.expanduser', return_value=temp_dir), \
                        mock.patch('azure.cli.command_modules.acs.custom.shutil.rmtree', side_effect=remove_tree), \
                        mock.patch('azure.cli.command_modules.acs.custom.logger.warning') as warning:
                    _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                executable = os.path.join(install_dir, 'aks-desktop')
                mock_popen.assert_called_once_with([executable])
                with open(executable, 'rb') as installed:
                    self.assertEqual(installed.read(), b'executable')
                self.assertEqual(len(backups), 1)
                self.assertTrue(os.path.isdir(backups[0]))
                self.assertEqual(sorted(os.listdir(install_root)), [os.path.basename(backups[0]), '0.9.1'])
                self.assertIn(backups[0], str(warning.call_args_list))
                self.assertIn('backup cleanup denied', str(warning.call_args_list))

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_interrupted_publication_preserves_old(self, mock_popen):
        for interruption in ('after-backup', 'publish'):
            with self.subTest(interruption=interruption), tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                install_root = os.path.join(temp_dir, '.local', 'share', 'aks-desktop')
                install_dir = os.path.join(install_root, '0.9.1')
                os.makedirs(install_dir)
                with open(os.path.join(install_dir, 'aks-desktop'), 'wb') as output:
                    output.write(b'old executable')
                self._write_aks_desktop_archive(archive_path, [('aks-desktop', tarfile.REGTYPE, '')])
                real_replace = os.replace
                interrupted = []

                def replace(source, destination):
                    if interruption == 'after-backup' and source == install_dir:
                        real_replace(source, destination)
                        interrupted.append(source)
                        raise KeyboardInterrupt()
                    if interruption == 'publish' and destination == install_dir and not interrupted:
                        interrupted.append(source)
                        raise KeyboardInterrupt()
                    return real_replace(source, destination)

                with mock.patch('os.path.expanduser', return_value=temp_dir), \
                        mock.patch('azure.cli.command_modules.acs.custom.os.replace', side_effect=replace):
                    with self.assertRaises(KeyboardInterrupt):
                        _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                mock_popen.assert_not_called()
                with open(os.path.join(install_dir, 'aks-desktop'), 'rb') as installed:
                    self.assertEqual(installed.read(), b'old executable')
                self.assertEqual(os.listdir(install_root), ['0.9.1'])

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_failed_rollback_retains_backup(self, mock_popen):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                install_root = os.path.join(temp_dir, '.local', 'share', 'aks-desktop')
                install_dir = os.path.join(install_root, '0.9.1')
                os.makedirs(install_dir)
                with open(os.path.join(install_dir, 'aks-desktop'), 'wb') as output:
                    output.write(b'old executable')
                self._write_aks_desktop_archive(archive_path, [('aks-desktop', tarfile.REGTYPE, '')])
                real_replace = os.replace
                backups = []

                def replace(source, destination):
                    if source == install_dir:
                        backups.append(destination)
                    if destination == install_dir:
                        raise OSError('publication or rollback failed')
                    return real_replace(source, destination)

                with mock.patch('os.path.expanduser', return_value=temp_dir), \
                        mock.patch('azure.cli.command_modules.acs.custom.os.replace', side_effect=replace):
                    with self.assertRaises(FileOperationError) as cm:
                        _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                mock_popen.assert_not_called()
                self.assertEqual(len(backups), 1)
                self.assertIn(backups[0], str(cm.exception))
                self.assertIn('rollback', str(cm.exception).lower())
                with open(os.path.join(backups[0], 'aks-desktop'), 'rb') as installed:
                    self.assertEqual(installed.read(), b'old executable')
                self.assertFalse(os.path.lexists(install_dir))
                self.assertEqual(len(os.listdir(install_root)), 1)

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen')
    def test_aks_install_desktop_archive_rejects_existing_file_or_symlink(self, mock_popen):
        for fallback in (False, True):
            for existing_type in ('file', 'symlink'):
                with self.subTest(fallback=fallback, existing_type=existing_type), \
                        self._aks_desktop_archive_extractor(fallback), \
                        tempfile.TemporaryDirectory() as temp_dir:
                    mock_popen.reset_mock()
                    archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                    install_root = os.path.join(temp_dir, '.local', 'share', 'aks-desktop')
                    install_dir = os.path.join(install_root, '0.9.1')
                    outside = os.path.join(temp_dir, 'outside')
                    os.makedirs(install_root)
                    os.mkdir(outside)
                    sentinel = os.path.join(outside, 'aks-desktop') if existing_type == 'symlink' else install_dir
                    with open(sentinel, 'wb') as output:
                        output.write(b'user data')
                    if existing_type == 'symlink':
                        os.symlink(outside, install_dir)
                    self._write_aks_desktop_archive(archive_path, [('aks-desktop', tarfile.REGTYPE, '')])
                    with mock.patch('os.path.expanduser', return_value=temp_dir):
                        with self.assertRaises(FileOperationError):
                            _launch_aks_desktop_installer(archive_path, 'linux', '0.9.1')
                    mock_popen.assert_not_called()
                    with open(sentinel, 'rb') as installed:
                        self.assertEqual(installed.read(), b'user data')
                    self.assertEqual(os.path.islink(install_dir), existing_type == 'symlink')
                    self.assertEqual(os.listdir(install_root), ['0.9.1'])

    @unittest.skipIf(os.name == 'nt', 'Requires POSIX permissions')
    def test_aks_install_desktop_archive_sanitizes_permissions(self):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                destination = os.path.join(temp_dir, 'install')
                with tarfile.open(archive_path, 'w:gz') as archive:
                    directory = tarfile.TarInfo('app')
                    directory.type = tarfile.DIRTYPE
                    directory.mode = 0
                    archive.addfile(directory)
                    for name, mode in [('executable', 0o7777), ('data', 0o7033)]:
                        member = tarfile.TarInfo('app/' + name)
                        member.mode = mode
                        member.uid = member.gid = 12345
                        member.uname = member.gname = 'untrusted'
                        archive.addfile(member)
                _extract_aks_desktop_archive(archive_path, destination)
                self.assertEqual(os.stat(os.path.join(destination, 'app')).st_mode & 0o700, 0o700)
                for name, mode in [('executable', 0o755), ('data', 0o600)]:
                    info = os.stat(os.path.join(destination, 'app', name))
                    self.assertEqual(info.st_mode & 0o7777, mode)
                    self.assertEqual(info.st_uid, os.getuid())
                    self.assertEqual(info.st_gid, os.getgid())

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_replaces_link_leaf_without_following(self):
        for fallback in (False, True):
            with self.subTest(fallback=fallback), self._aks_desktop_archive_extractor(fallback), \
                    tempfile.TemporaryDirectory() as temp_dir:
                archive_path = os.path.join(temp_dir, 'installer.tar.gz')
                destination = os.path.join(temp_dir, 'install')
                self._write_aks_desktop_archive(archive_path, [
                    ('old', tarfile.REGTYPE, ''),
                    ('new', tarfile.REGTYPE, ''),
                    ('alias', tarfile.SYMTYPE, 'old'),
                    ('alias', tarfile.SYMTYPE, 'new'),
                ])
                _extract_aks_desktop_archive(archive_path, destination)
                self.assertEqual(os.readlink(os.path.join(destination, 'alias')), 'new')
                self.assertFalse(os.path.islink(os.path.join(destination, 'old')))

    @unittest.skipIf(os.name == 'nt', 'Requires Linux archive link semantics')
    def test_aks_install_desktop_archive_compat_replaces_hardlink_leaf_without_following(self):
        # Native tarfile behavior for hardlinks replacing symlinks varies across Python versions.
        with self._aks_desktop_archive_extractor(True), tempfile.TemporaryDirectory() as temp_dir:
            archive_path = os.path.join(temp_dir, 'installer.tar.gz')
            destination = os.path.join(temp_dir, 'install')
            self._write_aks_desktop_archive(archive_path, [
                ('old', tarfile.REGTYPE, ''),
                ('new', tarfile.REGTYPE, ''),
                ('hardlink', tarfile.SYMTYPE, 'old'),
                ('hardlink', tarfile.LNKTYPE, 'new'),
            ])
            _extract_aks_desktop_archive(archive_path, destination)
            self.assertFalse(os.path.islink(os.path.join(destination, 'old')))
            self.assertFalse(os.path.islink(os.path.join(destination, 'hardlink')))
            self.assertTrue(os.path.samefile(os.path.join(destination, 'hardlink'),
                                             os.path.join(destination, 'new')))

    @mock.patch('azure.cli.command_modules.acs.custom.subprocess.run')
    def test_aks_install_desktop_launches_without_shell(self, mock_run):
        _launch_aks_desktop_installer(
            'aks-desktop-0.9.1-win-x64.exe', 'win', '0.9.1')
        mock_run.assert_called_once_with(
            ['aks-desktop-0.9.1-win-x64.exe'], check=True)

    def test_aks_install_desktop_retains_gui_installer(self):
        cases = [
            ('mac', 'arm64', 'aks-desktop-0.9.1-mac-arm64.dmg', 'open'),
            ('linux', 'x64', 'aks-desktop_0.9.1-1_amd64.deb', 'xdg-open'),
        ]
        for system, arch, name, launcher in cases:
            with self.subTest(system=system), tempfile.TemporaryDirectory() as config_dir:
                paths = []

                def download(asset, path):
                    with open(path, 'wb') as output:
                        output.write(b'installer')

                def launch(args, check):
                    self.assertEqual(args[0], launcher)
                    self.assertTrue(check)
                    self.assertTrue(os.path.isfile(args[1]))
                    paths.append(args[1])

                with (
                    mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': config_dir, 'DISPLAY': ':0'}),
                    mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform',
                               return_value=(system, arch)),
                    mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_release',
                               return_value=({'assets': [{'name': name}]}, '0.9.1')),
                    mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                               return_value={'ID': 'debian'}),
                    mock.patch('azure.cli.command_modules.acs.custom.shutil.which', return_value='/usr/bin/xdg-open'),
                    mock.patch('azure.cli.command_modules.acs.custom._download_aks_desktop_asset', side_effect=download),
                    mock.patch('azure.cli.command_modules.acs.custom.subprocess.run', side_effect=launch),
                ):
                    aks_install_desktop(None, version='0.9.1')
                    aks_install_desktop(None, version='0.9.1')

                # A dispatched GUI may read the package only after this command returns.
                self.assertEqual(len(paths), 2)
                self.assertNotEqual(paths[0], paths[1])
                for path in paths:
                    self.assertTrue(os.path.isfile(path))
                    self.assertEqual(os.path.commonpath((config_dir, path)), config_dir)
                    with open(path, 'rb') as installer:
                        self.assertEqual(installer.read(), b'installer')

    def test_aks_install_desktop_failed_deb_handoff_uses_archive(self):
        deb = 'aks-desktop_0.9.1-1_amd64.deb'
        archive = 'aks-desktop-0.9.1-linux-x64.tar.gz'
        failures = [subprocess.CalledProcessError(3, ['xdg-open']),
                    FileNotFoundError(2, 'not found', 'xdg-open'),
                    PermissionError(13, 'permission denied', 'xdg-open')]
        for failure in failures:
            for archive_result in ('success', 'missing', 'invalid'):
                with self.subTest(failure=failure, archive_result=archive_result), \
                        tempfile.TemporaryDirectory() as temp_dir:
                    assets = [{'name': deb}] if archive_result == 'missing' else [{'name': deb}, {'name': archive}]
                    paths = []

                    def download(asset, path):
                        if paths:
                            self.assertFalse(os.path.exists(os.path.dirname(paths[0])))
                        paths.append(path)
                        if asset['name'] == deb:
                            with open(path, 'wb') as output:
                                output.write(b'installer')
                        else:
                            name = 'resource' if archive_result == 'invalid' else 'aks-desktop'
                            self._write_aks_desktop_archive(path, [(name, tarfile.REGTYPE, '')])

                    with (
                        mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': temp_dir, 'DISPLAY': ':0'}),
                        mock.patch('os.path.expanduser', return_value=temp_dir),
                        mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform',
                                   return_value=('linux', 'x64')),
                        mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_release',
                                   return_value=({'assets': assets}, '0.9.1')) as release,
                        mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                                   return_value={'ID': 'ubuntu'}),
                        mock.patch('azure.cli.command_modules.acs.custom.shutil.which', return_value='/bin/xdg-open'),
                        mock.patch('azure.cli.command_modules.acs.custom._download_aks_desktop_asset',
                                   side_effect=download),
                        mock.patch('azure.cli.command_modules.acs.custom.subprocess.run',
                                   side_effect=failure) as run,
                        mock.patch('azure.cli.command_modules.acs.custom.subprocess.Popen') as popen,
                    ):
                        if archive_result == 'success':
                            aks_install_desktop(None)
                            executable = os.path.join(
                                temp_dir, '.local', 'share', 'aks-desktop', '0.9.1', 'aks-desktop')
                            popen.assert_called_once_with([executable])
                            with open(executable, 'rb') as installed:
                                self.assertEqual(installed.read(), b'executable')
                        elif archive_result == 'invalid':
                            with self.assertRaisesRegex(FileOperationError, 'expected executable'):
                                aks_install_desktop(None)
                            popen.assert_not_called()
                            self.assertEqual(os.listdir(os.path.join(temp_dir, '.local', 'share', 'aks-desktop')), [])
                        else:
                            with self.assertRaises((ClientRequestError, FileOperationError)) as cm:
                                aks_install_desktop(None)
                            self.assertIn('code 3' if isinstance(failure, subprocess.CalledProcessError)
                                          else 'xdg-open', str(cm.exception))
                            popen.assert_not_called()
                        release.assert_called_once()
                        run.assert_called_once_with(['xdg-open', paths[0]], check=True)
                    self.assertEqual([os.path.basename(path) for path in paths],
                                     [deb] if archive_result == 'missing' else [deb, archive])
                    for path in paths:
                        self.assertFalse(os.path.exists(os.path.dirname(path)))

    def test_aks_install_desktop_deb_download_failure_does_not_fallback(self):
        deb = 'aks-desktop_0.9.1-1_amd64.deb'
        archive = 'aks-desktop-0.9.1-linux-x64.tar.gz'
        for failure in ('missing-digest', 'mismatch', 'network'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as config_dir:
                asset = {
                    'name': deb,
                    'browser_download_url': 'https://github.com/Azure/aks-desktop/releases/download/v0.9.1/' + deb,
                    'digest': None if failure == 'missing-digest' else 'sha256:' + '0' * 64,
                }
                with (
                    mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': config_dir, 'DISPLAY': ':0'}),
                    mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform',
                               return_value=('linux', 'x64')),
                    mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_release',
                               return_value=({'assets': [asset, {'name': archive}]}, '0.9.1')),
                    mock.patch('azure.cli.command_modules.acs.custom.platform.freedesktop_os_release',
                               return_value={'ID': 'debian'}),
                    mock.patch('azure.cli.command_modules.acs.custom.shutil.which', return_value='/bin/xdg-open'),
                    mock.patch('urllib.request.build_opener') as opener,
                    mock.patch('azure.cli.command_modules.acs.custom._launch_aks_desktop_installer') as launch,
                ):
                    opener.return_value.open.return_value = io.BytesIO(b'invalid installer')
                    if failure == 'network':
                        opener.return_value.open.side_effect = URLError('network unavailable')
                    with self.assertRaises(ClientRequestError):
                        aks_install_desktop(None)
                    launch.assert_not_called()
                    self.assertEqual(opener.return_value.open.call_count, 0 if failure == 'missing-digest' else 1)
                    self.assertEqual(os.listdir(os.path.join(config_dir, 'aks-desktop', 'installers')), [])

    def test_aks_install_desktop_cleans_installer_after_failure(self):
        for failure in ('download', 'launch'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as config_dir:
                paths = []

                def download(asset, path):
                    paths.append(path)
                    with open(path, 'wb') as output:
                        output.write(b'partial installer')
                    if failure == 'download':
                        raise ClientRequestError('download failed')

                with (
                    mock.patch.dict(os.environ, {'AZURE_CONFIG_DIR': config_dir}),
                    mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform',
                               return_value=('mac', 'arm64')),
                    mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_release',
                               return_value=({'assets': [{'name': 'aks-desktop-0.9.1-mac-arm64.dmg'}]}, '0.9.1')),
                    mock.patch('azure.cli.command_modules.acs.custom._download_aks_desktop_asset', side_effect=download),
                    mock.patch('azure.cli.command_modules.acs.custom.subprocess.run',
                               side_effect=ClientRequestError('launch failed')),
                ):
                    with self.assertRaises(ClientRequestError):
                        aks_install_desktop(None)
                self.assertEqual(len(paths), 1)
                self.assertFalse(os.path.exists(os.path.dirname(paths[0])))

    @mock.patch('azure.cli.command_modules.acs.custom._launch_aks_desktop_installer')
    @mock.patch('azure.cli.command_modules.acs.custom._download_aks_desktop_asset')
    @mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_release')
    @mock.patch('azure.cli.command_modules.acs.custom._get_aks_desktop_platform')
    def test_aks_install_desktop_cleans_synchronous_installer(self, mock_platform, mock_release,
                                                              mock_download, mock_launch):
        def download(asset, path):
            with open(path, 'wb') as output:
                output.write(b'installer')

        def launch(path, system, version):
            with open(path, 'rb') as installer:
                self.assertEqual(installer.read(), b'installer')

        mock_download.side_effect = download
        mock_launch.side_effect = launch
        cases = [
            ('win', 'x64', 'aks-desktop-0.9.1-win-x64.exe'),
            ('linux', 'arm64', 'aks-desktop-0.9.1-linux-arm64.tar.gz'),
        ]
        for system, arch, name in cases:
            with self.subTest(system=system):
                mock_download.reset_mock()
                mock_launch.reset_mock()
                mock_platform.return_value = (system, arch)
                mock_release.return_value = ({'assets': [{'name': name}]}, '0.9.1')
                aks_install_desktop(None)
                mock_download.assert_called_once()
                installer_path = mock_download.call_args[0][1]
                mock_launch.assert_called_once_with(installer_path, system, '0.9.1')
                self.assertFalse(os.path.exists(installer_path))
                self.assertFalse(os.path.exists(os.path.dirname(installer_path)))

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location', return_value='eastus')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client', autospec=True)
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client', autospec=True)
    def test_update_upgrade_settings(self, rg_def, get_resource_groups_client, get_resources_client):
        instance = mock.MagicMock()

        # Should not update mc if unset
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertIsNone(instance.upgrade_settings)

        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = True,
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2023-04-01T13:00:00Z"))

        # force_upgrade True
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertGreater(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=2)).timestamp())
        self.assertLess(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=4)).timestamp())

        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = False
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until=None)
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertGreater(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=2)).timestamp())
        self.assertLess(instance.upgrade_settings.override_settings.until.timestamp(), (datetime.datetime.utcnow() + datetime.timedelta(days=4)).timestamp())

        # force_upgrade False
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=True, upgrade_override_until=None)
        self.assertFalse(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertIsNone(instance.upgrade_settings.override_settings.until)

        instance.upgrade_settings = None
        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = True
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=True, upgrade_override_until=None)
        self.assertFalse(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertIsNone(instance.upgrade_settings.override_settings.until)

        # Update util
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertIsNone(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))
        
        instance.upgrade_settings = None
        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertIsNone(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))

        with self.assertRaises(InvalidArgumentValueError):
            _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=False, upgrade_override_until="abc")

         # Set both force_upgrade and until 
        instance.upgrade_settings = None
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))
        
        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = True,
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=False, disable_force_upgrade=True, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertFalse(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))

        instance.upgrade_settings = self.models.ClusterUpgradeSettings(
            override_settings = self.models.UpgradeOverrideSettings(
                force_upgrade = False,
                until=parse("2023-04-01T13:00:00Z")
            )
        )
        instance = _update_upgrade_settings(MockCmd(self.cli), instance, enable_force_upgrade=True, disable_force_upgrade=False, upgrade_override_until="2024-01-01T13:00:00Z")
        self.assertTrue(instance.upgrade_settings.override_settings.force_upgrade)
        self.assertEqual(instance.upgrade_settings.override_settings.until, parse("2024-01-01T13:00:00Z"))

class TestAKSCommand(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = MockCLI()
        self.cmd = MockCmd(self.cli_ctx)
        self.models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)
        self.client = MockClient()

    def test_aks_stop(self):
        # public cluster: call begin_stop
        mc_1 = self.models.ManagedCluster(location="test_location")
        self.client.get = mock.Mock(
            return_value=mc_1
        )
        self.client.begin_stop = mock.Mock(
            return_value=None
        )
        self.assertEqual(aks_stop(self.cmd, self.client, "rg", "name"), None)

        # private cluster: call begin_stop
        mc_2 = self.models.ManagedCluster(location="test_location")
        api_server_access_profile = self.models.ManagedClusterAPIServerAccessProfile()
        api_server_access_profile.enable_private_cluster = True
        mc_2.api_server_access_profile = api_server_access_profile
        self.client.get = mock.Mock(
            return_value=mc_2
        )
        self.client.begin_stop = mock.Mock(
            return_value=None
        )
        self.assertEqual(aks_stop(self.cmd, self.client, "rg", "name", False), None)

    def test_aks_upgrade_node_image_only_skips_machines_mode_pool(self):
        """Machines mode pools must be skipped during --node-image-only to avoid a known client-side error."""
        machines_pool = self.models.ManagedClusterAgentPoolProfile(name="machinespool", mode="Machines", type="VirtualMachines")
        vmss_pool = self.models.ManagedClusterAgentPoolProfile(name="nodepool1", mode="User", type="VirtualMachineScaleSets")
        mc = self.models.ManagedCluster(location="test_location")
        mc.agent_pool_profiles = [machines_pool, vmss_pool]
        mc.pod_identity_profile = None
        mc.kubernetes_version = "1.24.0"
        mc.provisioning_state = "Succeeded"
        mc.max_agent_pools = 10

        self.client.get = mock.Mock(return_value=mc)

        with mock.patch("azure.cli.command_modules.acs.custom.cf_agent_pools") as mock_cf, \
             mock.patch("azure.cli.command_modules.acs.custom._upgrade_single_nodepool_image_version") as mock_upgrade:
            mock_cf.return_value = mock.Mock()

            aks_upgrade(self.cmd, self.client, "rg", "name", node_image_only=True, yes=True)

            # Only the VMSS pool should be upgraded; the Machines mode pool must be skipped.
            upgraded_pools = [call.args[4] for call in mock_upgrade.call_args_list]
            self.assertNotIn("machinespool", upgraded_pools)
            self.assertIn("nodepool1", upgraded_pools)

    def test_aks_upgrade_kubernetes_version_skips_machines_mode_pool(self):
        """Machines mode pools must be skipped during Kubernetes version upgrade to avoid a known client-side error."""
        machines_pool = self.models.ManagedClusterAgentPoolProfile(name="machinespool", mode="Machines", type="VirtualMachines")
        vmss_pool = self.models.ManagedClusterAgentPoolProfile(name="nodepool1", mode="User", type="VirtualMachineScaleSets")
        mc = self.models.ManagedCluster(location="test_location")
        mc.agent_pool_profiles = [machines_pool, vmss_pool]
        mc.pod_identity_profile = None
        mc.kubernetes_version = "1.24.0"
        mc.provisioning_state = "Succeeded"
        mc.max_agent_pools = 10
        mc.service_principal_profile = None

        self.client.get = mock.Mock(return_value=mc)
        self.client.begin_create_or_update = mock.Mock(return_value=None)

        aks_upgrade(self.cmd, self.client, "rg", "name", kubernetes_version="1.25.0", yes=True)

        # Machines mode pool must not have orchestrator_version set; VMSS pool must be upgraded.
        self.assertIsNone(machines_pool.orchestrator_version)
        self.assertEqual(vmss_pool.orchestrator_version, "1.25.0")

    @staticmethod
    def _build_vms_agentpool(
        pool_type="VirtualMachines",
        manual_profiles=None,
        autoscale_profiles=None,
    ):
        if manual_profiles is None:
            manual_profiles = []
        instance = mock.Mock()
        instance.properties = mock.Mock()
        instance.properties.type_properties_type = pool_type
        instance.type_properties_type = pool_type
        instance.virtual_machines_profile = mock.Mock()
        instance.virtual_machines_profile.scale = mock.Mock()
        instance.virtual_machines_profile.scale.manual = manual_profiles
        instance.virtual_machines_profile.scale.autoscale = autoscale_profiles
        return instance

    def test_aks_agentpool_auto_scale_add_success(self):
        class AutoScaleProfile:
            def __init__(self, size, min_count, max_count):
                self.size = size
                self.min_count = min_count
                self.max_count = max_count

        instance = self._build_vms_agentpool(autoscale_profiles=None)
        self.client.get = mock.Mock(return_value=instance)
        self.client.begin_create_or_update = mock.Mock(return_value="ok")
        self.cmd.get_models = mock.Mock(return_value=AutoScaleProfile)

        result = aks_agentpool_auto_scale_add(
            self.cmd,
            self.client,
            "rg",
            "mc",
            "np",
            "Standard_D4s_v3",
            2,
            5,
        )

        self.assertEqual(result, "ok")
        self.assertEqual(len(instance.virtual_machines_profile.scale.autoscale), 1)
        profile = instance.virtual_machines_profile.scale.autoscale[0]
        self.assertEqual(profile.size, "Standard_D4s_v3")
        self.assertEqual(profile.min_count, 2)
        self.assertEqual(profile.max_count, 5)

    def test_aks_agentpool_auto_scale_add_non_vms_pool(self):
        instance = self._build_vms_agentpool(pool_type="VirtualMachineScaleSets", autoscale_profiles=[])
        self.client.get = mock.Mock(return_value=instance)

        with self.assertRaises(ClientRequestError):
            aks_agentpool_auto_scale_add(
                self.cmd,
                self.client,
                "rg",
                "mc",
                "np",
                "Standard_D4s_v3",
                1,
                3,
            )

    def test_aks_agentpool_auto_scale_update_missing_required(self):
        with self.assertRaises(RequiredArgumentMissingError):
            aks_agentpool_auto_scale_update(
                self.cmd,
                self.client,
                "rg",
                "mc",
                "np",
                "Standard_D2s_v3",
            )

    def test_aks_agentpool_auto_scale_update_profile_not_found(self):
        profile = mock.Mock(size="Standard_D2s_v3", min_count=1, max_count=3)
        instance = self._build_vms_agentpool(autoscale_profiles=[profile])
        self.client.get = mock.Mock(return_value=instance)

        with self.assertRaisesRegex(InvalidArgumentValueError, "doesn't exist"):
            aks_agentpool_auto_scale_update(
                self.cmd,
                self.client,
                "rg",
                "mc",
                "np",
                "Standard_D4s_v3",
                min_count=2,
            )

    def test_aks_agentpool_auto_scale_update_success(self):
        profile = mock.Mock(size="Standard_D2s_v3", min_count=1, max_count=3)
        instance = self._build_vms_agentpool(autoscale_profiles=[profile])
        self.client.get = mock.Mock(return_value=instance)
        self.client.begin_create_or_update = mock.Mock(return_value="ok")

        result = aks_agentpool_auto_scale_update(
            self.cmd,
            self.client,
            "rg",
            "mc",
            "np",
            "Standard_D2s_v3",
            node_vm_size="Standard_D8s_v3",
            min_count=2,
            max_count=6,
        )

        self.assertEqual(result, "ok")
        self.assertEqual(profile.size, "Standard_D8s_v3")
        self.assertEqual(profile.min_count, 2)
        self.assertEqual(profile.max_count, 6)

    def test_aks_agentpool_auto_scale_delete_non_vms_pool(self):
        instance = self._build_vms_agentpool(pool_type="VirtualMachineScaleSets", autoscale_profiles=[])
        self.client.get = mock.Mock(return_value=instance)

        with self.assertRaises(ClientRequestError):
            aks_agentpool_auto_scale_delete(
                self.cmd,
                self.client,
                "rg",
                "mc",
                "np",
                "Standard_D2s_v3",
            )

    def test_aks_agentpool_auto_scale_delete_profile_not_found(self):
        profile = mock.Mock(size="Standard_D2s_v3", min_count=1, max_count=3)
        instance = self._build_vms_agentpool(autoscale_profiles=[profile])
        self.client.get = mock.Mock(return_value=instance)

        with self.assertRaisesRegex(InvalidArgumentValueError, "doesn't exist"):
            aks_agentpool_auto_scale_delete(
                self.cmd,
                self.client,
                "rg",
                "mc",
                "np",
                "Standard_D4s_v3",
            )

    def test_aks_agentpool_auto_scale_delete_success(self):
        profile_1 = mock.Mock(size="Standard_D2s_v3", min_count=1, max_count=3)
        profile_2 = mock.Mock(size="Standard_D4s_v3", min_count=2, max_count=5)
        instance = self._build_vms_agentpool(autoscale_profiles=[profile_1, profile_2])
        self.client.get = mock.Mock(return_value=instance)
        self.client.begin_create_or_update = mock.Mock(return_value="ok")

        result = aks_agentpool_auto_scale_delete(
            self.cmd,
            self.client,
            "rg",
            "mc",
            "np",
            "Standard_D4s_v3",
        )

        self.assertEqual(result, "ok")
        self.assertEqual(len(instance.virtual_machines_profile.scale.autoscale), 1)
        self.assertEqual(instance.virtual_machines_profile.scale.autoscale[0].size, "Standard_D2s_v3")


class TestRunCommand(unittest.TestCase):
    def test_get_command_context_invalid_file(self):
        with self.assertRaises(CLIError) as cm:
            _get_command_context([get_test_data_file_path("notexistingfile")])
        self.assertIn('notexistingfile is not valid file, or not accessable.', str(
            cm.exception))

    def test_get_command_context_mixed(self):
        with self.assertRaises(CLIError) as cm:
            _get_command_context(
                [".", get_test_data_file_path("ns.yaml")])
        self.assertEqual(str(
            cm.exception), '. is used to attach current folder, not expecting other attachements.')

    def test_get_command_context_empty(self):
        context = _get_command_context([])
        self.assertEqual(context, "")

    def test_get_command_context_valid(self):
        context = _get_command_context(
            [get_test_data_file_path("ns.yaml"), get_test_data_file_path("dummy.json")])
        self.assertNotEqual(context, '')


class TestAddonConfigurationAzureBleuCloud(unittest.TestCase):
    """Test cases for AzureBleu Cloud region mapping in addon configuration."""

    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)
        # Set cloud name to AzureBleuCloud
        self.cmd.cli_ctx.cloud.name = 'AzureBleuCloud'

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_bleufrancecentral_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that bleufrancecentral region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'bleufrancecentral'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-BLEUC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-BLEUC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-BLEUC',
            {'location': 'bleufrancecentral'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-BLEUC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-BLEUC', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_bleufrancesouth_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that bleufrancesouth region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'bleufrancesouth'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-BLEUS/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-BLEUS'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-BLEUS',
            {'location': 'bleufrancesouth'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-BLEUS', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-BLEUS', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_unknown_bleu_region_defaults_to_bleufrancecentral(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that unknown regions in AzureBleu cloud default to bleufrancecentral."""
        # Arrange
        mock_get_rg_location.return_value = 'unknownregion'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-BLEUC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-BLEUC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with default region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-BLEUC',
            {'location': 'bleufrancecentral'}
        )
        
        # Verify the workspace resource ID contains the default region code
        self.assertIn('DefaultResourceGroup-BLEUC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-BLEUC', result)


class TestAddonConfigurationAzureDelosCloud(unittest.TestCase):
    """Test cases for AzureDelos Cloud region mapping in addon configuration."""

    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)
        # Set cloud name to AzureDelosCloud
        self.cmd.cli_ctx.cloud.name = 'AzureDelosCloud'

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_deloscloudgermanycentral_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that deloscloudgermanycentral region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'deloscloudgermanycentral'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-DELOSC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-DELOSC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-DELOSC',
            {'location': 'deloscloudgermanycentral'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-DELOSC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-DELOSC', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_deloscloudgermanynorth_region_mapping(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that deloscloudgermanynorth region maps correctly."""
        # Arrange
        mock_get_rg_location.return_value = 'deloscloudgermanynorth'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-DELOSN/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-DELOSN'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with correct region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-DELOSN',
            {'location': 'deloscloudgermanynorth'}
        )
        
        # Verify the workspace resource ID contains the correct region code
        self.assertIn('DefaultResourceGroup-DELOSN', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-DELOSN', result)

    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resources_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_resource_groups_client')
    @mock.patch('azure.cli.command_modules.acs.addonconfiguration.get_rg_location')
    def test_unknown_delos_region_defaults_to_deloscloudgermanycentral(self, mock_get_rg_location, mock_get_rg_client, mock_get_resources_client):
        """Test that unknown regions in AzureDelos cloud default to deloscloudgermanycentral."""
        # Arrange
        mock_get_rg_location.return_value = 'unknownregion'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        resource_group_name = 'test-rg'
        
        # Mock resource group client
        mock_rg_client = mock.Mock()
        mock_rg_client.check_existence.return_value = False
        mock_rg_client.create_or_update = mock.Mock()
        mock_get_rg_client.return_value = mock_rg_client
        
        # Mock resources client
        mock_resources_client = mock.Mock()
        mock_poller = mock.Mock()
        mock_result = mock.Mock()
        mock_result.id = f'/subscriptions/{subscription_id}/resourceGroups/DefaultResourceGroup-DELOSC/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-{subscription_id}-DELOSC'
        mock_poller.result.return_value = mock_result
        mock_poller.done.return_value = True
        mock_resources_client.begin_create_or_update_by_id.return_value = mock_poller
        mock_get_resources_client.return_value = mock_resources_client
        
        # Mock get_models for GenericResource
        self.cmd.get_models = mock.Mock(return_value=mock.Mock)
        
        # Act
        result = ensure_default_log_analytics_workspace_for_monitoring(
            self.cmd, subscription_id, resource_group_name
        )
        
        # Assert
        # Verify the resource group was created with default region
        mock_rg_client.create_or_update.assert_called_once_with(
            'DefaultResourceGroup-DELOSC',
            {'location': 'deloscloudgermanycentral'}
        )
        
        # Verify the workspace resource ID contains the default region code
        self.assertIn('DefaultResourceGroup-DELOSC', result)
        self.assertIn(f'DefaultWorkspace-{subscription_id}-DELOSC', result)


class TestIsMonitoringAddonEnabled(unittest.TestCase):
    """Tests for the is_monitoring_addon_enabled helper in custom.py."""

    def test_monitoring_enabled_with_lowercase_key(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(enabled=True, config={}),
        }
        self.assertTrue(is_monitoring_addon_enabled("monitoring", instance))

    def test_monitoring_enabled_with_camelcase_key(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(enabled=True, config={}),
        }
        self.assertTrue(is_monitoring_addon_enabled("monitoring", instance))

    def test_monitoring_disabled_with_camelcase_key(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            "omsAgent": ManagedClusterAddonProfile(enabled=False, config={}),
        }
        self.assertFalse(is_monitoring_addon_enabled("monitoring", instance))

    def test_no_monitoring_addon_at_all(self):
        instance = mock.Mock()
        instance.addon_profiles = {}
        self.assertFalse(is_monitoring_addon_enabled("monitoring", instance))

    def test_non_monitoring_addon(self):
        instance = mock.Mock()
        instance.addon_profiles = {
            CONST_MONITORING_ADDON_NAME: ManagedClusterAddonProfile(enabled=True, config={}),
        }
        self.assertFalse(is_monitoring_addon_enabled("http_application_routing", instance))


class TestAksEnableAddonsAutoHLSM(unittest.TestCase):
    """Tests for auto-detection of HLSM when CNL is active in aks_enable_addons."""

    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)

    def _build_instance(self, cnl_flag=None, addon_key=CONST_MONITORING_ADDON_NAME):
        """Build a mock cluster instance with monitoring addon."""
        config = {
            'logAnalyticsWorkspaceResourceID': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.OperationalInsights/workspaces/ws',
            CONST_MONITORING_USING_AAD_MSI_AUTH: 'true',
        }
        if cnl_flag is not None:
            config['enableRetinaNetworkFlags'] = cnl_flag
        instance = mock.MagicMock()
        instance.addon_profiles = {
            addon_key: ManagedClusterAddonProfile(enabled=True, config=config),
        }
        instance.service_principal_profile.client_id = "msi"
        instance.api_server_access_profile = None
        instance.location = "eastus"
        return instance

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_auto_enabled_when_cnl_active(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When CNL is active and HLSM not set, HLSM should auto-enable."""
        instance = self._build_instance(cnl_flag="True")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertTrue(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_not_auto_enabled_when_cnl_inactive(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When CNL is not active and HLSM not set, HLSM should remain None."""
        instance = self._build_instance(cnl_flag=None)
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertIsNone(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_explicit_true_not_overridden(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When HLSM is explicitly True, auto-detection should not change it."""
        instance = self._build_instance(cnl_flag="True")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring",
                          enable_high_log_scale_mode=True)

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertTrue(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_explicit_false_not_overridden_by_cnl(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When HLSM is explicitly False, auto-detection should not override even with CNL active."""
        instance = self._build_instance(cnl_flag="True")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring",
                          enable_high_log_scale_mode=False)

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertFalse(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_auto_enabled_with_cnl_lowercase_true(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """CNL flag value 'true' (lowercase) should also trigger auto-HLSM."""
        instance = self._build_instance(cnl_flag="true")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertTrue(kwargs.get("enable_high_log_scale_mode"))

    @mock.patch("azure.cli.command_modules.acs.custom.ensure_container_insights_for_monitoring")
    @mock.patch("azure.cli.command_modules.acs.custom.LongRunningOperation")
    @mock.patch("azure.cli.command_modules.acs.custom._update_addons")
    @mock.patch("azure.cli.command_modules.acs.custom.get_subscription_id", return_value="00000000-0000-0000-0000-000000000000")
    def test_hlsm_not_auto_enabled_when_cnl_false(self, _mock_sub, mock_update, mock_lro, mock_ensure):
        """When CNL flag is 'false', HLSM should not auto-enable."""
        instance = self._build_instance(cnl_flag="false")
        mock_update.return_value = instance
        mock_lro.return_value = lambda x: instance
        client = mock.Mock()
        client.get.return_value = instance

        aks_enable_addons(self.cmd, client, "rg", "cluster", "monitoring")

        mock_ensure.assert_called_once()
        _, kwargs = mock_ensure.call_args
        self.assertIsNone(kwargs.get("enable_high_log_scale_mode"))


class AksAgentpoolUpgradeTest(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)
        self.models = AKSManagedClusterModels(self.cmd, ResourceType.MGMT_CONTAINERSERVICE)

    @mock.patch("azure.cli.command_modules.acs.custom.sdk_no_wait")
    def test_aks_agentpool_upgrade_sets_max_unavailable(self, mock_sdk_no_wait):
        """Test that max_unavailable is set on upgrade_settings during agentpool upgrade."""
        AgentPoolUpgradeSettings = self.cmd.get_models(
            "AgentPoolUpgradeSettings",
            resource_type=ResourceType.MGMT_CONTAINERSERVICE,
            operation_group="managed_clusters",
        )
        instance = mock.Mock()
        instance.orchestrator_version = "1.32.0"
        instance.provisioning_state = "Succeeded"
        instance.upgrade_settings = AgentPoolUpgradeSettings()

        client = mock.Mock()
        client.get.return_value = instance

        aks_agentpool_upgrade(
            self.cmd,
            client,
            resource_group_name="rg",
            cluster_name="cluster",
            nodepool_name="nodepool1",
            kubernetes_version="1.33.0",
            max_unavailable="5",
            yes=True,
        )

        self.assertEqual(instance.upgrade_settings.max_unavailable, "5")
        mock_sdk_no_wait.assert_called_once()


class AksAgentpoolRollbackTest(unittest.TestCase):
    def setUp(self):
        self.cli = MockCLI()
        self.cmd = MockCmd(self.cli)

    def test_aks_agentpool_get_rollback_versions_returns_recently_used_versions(self):
        versions = [
            mock.Mock(
                orchestrator_version="1.32.1",
                node_image_version="AKSUbuntu-2204gen2containerd-202605.12.0",
                timestamp=datetime.datetime(2026, 5, 1),
            )
        ]
        upgrade_profile = mock.Mock(recently_used_versions=versions)
        client = mock.Mock()
        client.get_upgrade_profile.return_value = upgrade_profile

        result = aks_agentpool_get_rollback_versions(self.cmd, client, "rg", "cluster", "nodepool1")

        self.assertEqual(result, versions)
        client.get_upgrade_profile.assert_called_once_with("rg", "cluster", "nodepool1")

    @mock.patch("azure.cli.command_modules.acs._client_factory.cf_managed_clusters")
    @mock.patch("azure.cli.command_modules.acs.custom.sdk_no_wait")
    def test_aks_agentpool_rollback_uses_most_recent_version(self, mock_sdk_no_wait, mock_cf_managed_clusters):
        older_version = mock.Mock(
            orchestrator_version="1.31.9",
            node_image_version="AKSUbuntu-2204gen2containerd-202604.10.0",
            timestamp=datetime.datetime(2026, 4, 1),
        )
        most_recent_version = mock.Mock(
            orchestrator_version="1.32.1",
            node_image_version="AKSUbuntu-2204gen2containerd-202605.12.0",
            timestamp=datetime.datetime(2026, 5, 1),
        )
        upgrade_profile = mock.Mock(recently_used_versions=[older_version, most_recent_version])
        agentpool = mock.Mock()
        client = mock.Mock()
        client.get_upgrade_profile.return_value = upgrade_profile
        client.get.return_value = agentpool
        mock_cf_managed_clusters.return_value.get.return_value = mock.Mock(auto_upgrade_profile=None)
        mock_sdk_no_wait.return_value = "rollback-result"

        result = aks_agentpool_rollback(
            self.cmd,
            client,
            resource_group_name="rg",
            cluster_name="cluster",
            nodepool_name="nodepool1",
            aks_custom_headers="Header=Value",
            if_match="etag",
            no_wait=True,
        )

        self.assertEqual(result, "rollback-result")
        self.assertEqual(agentpool.orchestrator_version, "1.32.1")
        self.assertEqual(agentpool.node_image_version, "AKSUbuntu-2204gen2containerd-202605.12.0")
        mock_sdk_no_wait.assert_called_once()
        args, kwargs = mock_sdk_no_wait.call_args
        self.assertEqual(
            args[:6],
            (True, client.begin_create_or_update, "rg", "cluster", "nodepool1", agentpool),
        )
        self.assertEqual(kwargs["headers"], {"Header": "Value"})
        self.assertEqual(kwargs["etag"], "etag")

    @mock.patch("azure.cli.command_modules.acs._client_factory.cf_managed_clusters")
    @mock.patch("azure.cli.command_modules.acs.custom.sdk_no_wait")
    def test_aks_agentpool_rollback_raises_when_no_recent_versions(self, mock_sdk_no_wait, mock_cf_managed_clusters):
        upgrade_profile = mock.Mock(recently_used_versions=[])
        client = mock.Mock()
        client.get_upgrade_profile.return_value = upgrade_profile
        mock_cf_managed_clusters.return_value.get.return_value = mock.Mock(auto_upgrade_profile=None)

        with self.assertRaises(CLIError):
            aks_agentpool_rollback(self.cmd, client, "rg", "cluster", "nodepool1")

        mock_sdk_no_wait.assert_not_called()

    @mock.patch("azure.cli.command_modules.acs._client_factory.cf_managed_clusters")
    @mock.patch("azure.cli.command_modules.acs.custom.sdk_no_wait")
    def test_aks_agentpool_rollback_warns_node_image_only_for_node_os_channel(
        self, mock_sdk_no_wait, mock_cf_managed_clusters
    ):
        rollback_version = mock.Mock(
            orchestrator_version="1.34.8",
            node_image_version="AKSUbuntu-2204gen2containerd-202607.20.0",
            timestamp=datetime.datetime(2026, 8, 5),
        )
        client = mock.Mock()
        client.get_upgrade_profile.return_value = mock.Mock(recently_used_versions=[rollback_version])
        client.get.return_value = mock.Mock()
        mock_cf_managed_clusters.return_value.get.return_value = mock.Mock(
            auto_upgrade_profile=mock.Mock(
                upgrade_channel=mock.Mock(value="none"),
                node_os_upgrade_channel=mock.Mock(value="NodeImage"),
            )
        )

        with mock.patch("azure.cli.command_modules.acs.custom.logger.warning") as mock_warning:
            aks_agentpool_rollback(self.cmd, client, "rg", "cluster", "nodepool1")

        mock_warning.assert_called_once()
        warning = mock_warning.call_args.args[0]
        self.assertIn("The orchestrator version rollback will proceed", warning)
        self.assertIn("the node image rollback will not succeed", warning)
        self.assertNotIn("Rollback will not succeed until auto-upgrade is disabled", warning)
        mock_sdk_no_wait.assert_called_once()

    @mock.patch("azure.cli.command_modules.acs._client_factory.cf_managed_clusters")
    @mock.patch("azure.cli.command_modules.acs.custom.sdk_no_wait")
    def test_aks_agentpool_rollback_prioritizes_upgrade_channel_warning(
        self, mock_sdk_no_wait, mock_cf_managed_clusters
    ):
        rollback_version = mock.Mock(
            orchestrator_version="1.34.8",
            node_image_version="AKSUbuntu-2204gen2containerd-202607.20.0",
            timestamp=datetime.datetime(2026, 8, 5),
        )
        client = mock.Mock()
        client.get_upgrade_profile.return_value = mock.Mock(recently_used_versions=[rollback_version])
        client.get.return_value = mock.Mock()
        mock_cf_managed_clusters.return_value.get.return_value = mock.Mock(
            auto_upgrade_profile=mock.Mock(
                upgrade_channel=mock.Mock(value="stable"),
                node_os_upgrade_channel=mock.Mock(value="NodeImage"),
            )
        )

        with mock.patch("azure.cli.command_modules.acs.custom.logger.warning") as mock_warning:
            aks_agentpool_rollback(self.cmd, client, "rg", "cluster", "nodepool1")

        mock_warning.assert_called_once()
        warning = mock_warning.call_args.args[0]
        self.assertIn("Rollback will not succeed until auto-upgrade is disabled", warning)
        self.assertNotIn("nodeOSUpgradeChannel", warning)
        self.assertNotIn("The orchestrator version rollback will proceed", warning)
        mock_sdk_no_wait.assert_called_once()


class DcrTableReadinessRetryTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch(
            "azure.cli.command_modules.acs.addonconfiguration.time.sleep",
            return_value=None,
        )
        self.addCleanup(patcher.stop)
        self.mock_sleep = patcher.start()
        self.resources = mock.Mock()

    def test_succeeds_without_retry(self):
        result = _create_or_update_dcr_with_table_readiness_retry(
            self.resources, "dcr-id", "2022-06-01", {"properties": {}}
        )

        self.assertIs(result, self.resources.begin_create_or_update_by_id.return_value)
        self.resources.begin_create_or_update_by_id.assert_called_once_with(
            "dcr-id", "2022-06-01", {"properties": {}}
        )
        self.mock_sleep.assert_not_called()

    def test_retries_invalid_output_table_with_delay(self):
        expected = mock.Mock()
        self.resources.begin_create_or_update_by_id.side_effect = [
            CLIError("invalidoutputtable: output table is not ready"),
            CLIError("INVALIDOUTPUTTABLE: output table is not ready"),
            expected,
        ]

        result = _create_or_update_dcr_with_table_readiness_retry(
            self.resources, "dcr-id", "2022-06-01", {"properties": {}}
        )

        self.assertIs(result, expected)
        self.assertEqual(self.resources.begin_create_or_update_by_id.call_count, 3)
        self.assertEqual(self.mock_sleep.call_count, 2)

    def test_raises_after_readiness_retry_limit(self):
        from azure.cli.command_modules.acs.addonconfiguration import (
            _DCR_TABLE_READINESS_MAX_RETRIES,
        )

        self.resources.begin_create_or_update_by_id.side_effect = CLIError(
            "InvalidOutputTable: output table is not ready"
        )

        with self.assertRaisesRegex(CLIError, "InvalidOutputTable"):
            _create_or_update_dcr_with_table_readiness_retry(
                self.resources, "dcr-id", "2022-06-01", {"properties": {}}
            )

        self.assertEqual(
            self.resources.begin_create_or_update_by_id.call_count,
            _DCR_TABLE_READINESS_MAX_RETRIES + 1,
        )
        self.assertEqual(
            self.mock_sleep.call_count,
            _DCR_TABLE_READINESS_MAX_RETRIES,
        )

    def test_other_errors_keep_three_attempt_limit(self):
        self.resources.begin_create_or_update_by_id.side_effect = CLIError(
            "unrelated failure"
        )

        with self.assertRaisesRegex(CLIError, "unrelated failure"):
            _create_or_update_dcr_with_table_readiness_retry(
                self.resources, "dcr-id", "2022-06-01", {"properties": {}}
            )

        self.assertEqual(self.resources.begin_create_or_update_by_id.call_count, 3)
        self.mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()

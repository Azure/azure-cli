# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import errno
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError, URLError
import datetime
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
    _get_command_context,
    _get_latest_kubelogin_version,
    _update_addons,
    aks_agentpool_auto_scale_add,
    aks_agentpool_auto_scale_delete,
    aks_agentpool_auto_scale_update,
    aks_agentpool_get_rollback_versions,
    aks_agentpool_rollback,
    aks_agentpool_upgrade,
    aks_enable_addons,
    aks_get_credentials,
    aks_stop,
    aks_upgrade,
    is_monitoring_addon_enabled,
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
)


class AKSGetCredentialsTest(unittest.TestCase):
    # Model the converter's file selection, including its fallback when --kubeconfig is absent.
    # Run in a child interpreter so invalid cwd values and reinterpreted relative paths fail.
    _CONVERTER = textwrap.dedent("""\
        import argparse
        import os
        import yaml

        parser = argparse.ArgumentParser()
        parser.add_argument("command", choices=["convert-kubeconfig"])
        parser.add_argument("-l", "--login", required=True)
        parser.add_argument("--kubeconfig")
        options = parser.parse_args()
        path = (options.kubeconfig or os.environ.get("KUBECONFIG", "").split(os.pathsep)[0]
                or os.path.expanduser("~/.kube/config"))
        with open(path, encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
        for user in config["users"]:
            exec_info = user["user"].get("exec", {})
            if exec_info.get("command") == "kubelogin":
                args = exec_info["args"]
                for flag in ("--login", "-l"):
                    if flag in args:
                        args[args.index(flag) + 1] = options.login
        with open(path, "w", encoding="utf-8") as stream:
            yaml.safe_dump(config, stream)
        """)

    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        self.directory = resources.enter_context(tempfile.TemporaryDirectory())
        resources.callback(os.chdir, os.getcwd())
        os.chdir(self.directory)
        home = os.path.join(self.directory, "home")
        resources.enter_context(mock.patch.dict(os.environ, {"HOME": home, "USERPROFILE": home}))
        os.environ.pop("KUBECONFIG", None)

        self.cmd = mock.Mock()
        self.cmd.cli_ctx.cloud.profile = "latest"
        self.client = mock.Mock()
        self.credential = SimpleNamespace(value=None)
        response = SimpleNamespace(kubeconfigs=[self.credential])
        self.client.list_cluster_user_credentials.return_value = response
        self.client.list_cluster_admin_credentials.return_value = response
        self.kubeconfig = self._make_kubeconfig("aks")
        self.existing = self._make_kubeconfig("existing")
        self.existing["users"][0]["user"] = {"token": "existing-token"}

        self.default_path = os.path.join(home, ".kube", "config")
        self.env_first = os.path.join(self.directory, "env", "config")
        self.env_second = os.path.join(self.directory, "env", "other config")
        self.guard_files = {
            path: self._write_config(path, self._make_kubeconfig(name))
            for path, name in ((self.default_path, "default"), (self.env_first, "first"), (self.env_second, "second"))
        }

        self._subprocess_run = subprocess.run
        self.converter_script = self._CONVERTER
        self.which = resources.enter_context(mock.patch(
            "azure.cli.command_modules.acs.custom.which", return_value="kubelogin"))
        self.run = resources.enter_context(mock.patch(
            "azure.cli.command_modules.acs.custom.subprocess.run", side_effect=self._run_kubelogin))
        self.logger = resources.enter_context(mock.patch("azure.cli.command_modules.acs.custom.logger"))

    @staticmethod
    def _make_kubeconfig(name):
        user_name = "clusterUser_rg_" + name
        return {
            "apiVersion": "v1",
            "kind": "Config",
            "preferences": {},
            "clusters": [{
                "name": name,
                "cluster": {"server": "https://{}.example.com:443".format(name),
                            "certificate-authority-data": "dGVzdC1jYQ=="},
            }],
            "contexts": [{"name": name, "context": {"cluster": name, "user": user_name}}],
            "current-context": name,
            "users": [{
                "name": user_name,
                "user": {"exec": {
                    "apiVersion": "client.authentication.k8s.io/v1beta1",
                    "command": "kubelogin",
                    "args": [
                        "get-token", "--environment", "AzurePublicCloud",
                        "--server-id", "6dae42f8-4368-4678-94ff-3960e28e3630",
                        "--client-id", "80faf920-1908-4b52-b5ef-a8e7bedfc67a",
                        "--tenant-id", "00000000-0000-0000-0000-000000000000",
                        "--login", "devicecode",
                    ],
                    "provideClusterInfo": False,
                }},
            }],
        }

    @staticmethod
    def _write_config(path, config):
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(config), encoding="utf-8")
        target.chmod(0o600)
        return target.read_bytes()

    def _run_kubelogin(self, argv, **kwargs):
        # Only substitute the executable; forward every argument and kwarg to the real runtime.
        return self._subprocess_run([sys.executable, "-c", self.converter_script, *argv[1:]], **kwargs)

    def _get_credentials(self, path, **kwargs):
        self.credential.value = yaml.safe_dump(self.kubeconfig).encode("utf-8")
        result = aks_get_credentials(self.cmd, self.client, "rg", "aks", path=path, **kwargs)
        self.assertIsNone(result)

    def _assert_guards_unchanged(self, except_path=None):
        for path, content in self.guard_files.items():
            if except_path is None or path != os.path.abspath(except_path):
                self.assertEqual(Path(path).read_bytes(), content, path)

    def _assert_conversion(self, path, effective_path=None, merge_existing=True, context_name=None):
        target = effective_path if effective_path is not None else path
        if merge_existing:
            self._write_config(target, self.existing)
        self._get_credentials(path, context_name=context_name)

        expected = deepcopy(self.kubeconfig)
        expected["users"][0]["user"]["exec"]["args"][-1] = "azurecli"
        if context_name is not None:
            expected["contexts"][0]["name"] = context_name
            expected["contexts"][0]["context"]["cluster"] = context_name
            expected["clusters"][0]["name"] = context_name
            expected["current-context"] = context_name
        if merge_existing:
            for key in ("clusters", "contexts", "users"):
                expected[key] = self.existing[key] + expected[key]
        self.assertEqual(yaml.safe_load(Path(target).read_text(encoding="utf-8")), expected)
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o600)
        self._assert_guards_unchanged(except_path=target)
        self.which.assert_called_once_with("kubelogin")
        self.run.assert_called_once_with(
            ["kubelogin", "convert-kubeconfig", "-l", "azurecli", "--kubeconfig", target], check=True)
        self.logger.warning.assert_has_calls([
            mock.call('Merged "{}" as current context in {}'.format(expected["current-context"], target)),
            mock.call("Converted kubeconfig to use Azure CLI authentication."),
        ])
        self.client.list_cluster_user_credentials.assert_called_once_with(
            "rg", "aks", server_fqdn=None, format=None)
        self.client.list_cluster_admin_credentials.assert_not_called()

    def _assert_merged_without_conversion(self, path):
        self.assertEqual(yaml.safe_load(Path(path).read_text(encoding="utf-8")), self.kubeconfig)
        self.logger.warning.assert_any_call('Merged "aks" as current context in {}'.format(path))
        self.assertNotIn(
            mock.call("Converted kubeconfig to use Azure CLI authentication."), self.logger.warning.call_args_list)
        self._assert_guards_unchanged()

    def test_aks_get_credentials_bare_filename(self):
        self._assert_conversion("kubeconfig", merge_existing=False)

    def test_aks_get_credentials_dot_relative_filename(self):
        self._assert_conversion("./kubeconfig")

    def test_aks_get_credentials_nested_relative_filename(self):
        self._assert_conversion(os.path.join("nested", "kubeconfig"))

    def test_aks_get_credentials_absolute_filename(self):
        self._assert_conversion(os.path.join(self.directory, "absolute-kubeconfig"))

    def test_aks_get_credentials_path_with_spaces(self):
        self._assert_conversion(os.path.join("directory with spaces", "cluster config"))

    def test_aks_get_credentials_literal_tilde_path(self):
        self._assert_conversion(os.path.join("~", "literal-kubeconfig"))

    def test_aks_get_credentials_explicit_file_overrides_environment(self):
        os.environ["KUBECONFIG"] = os.pathsep.join((self.env_first, self.env_second))
        self._assert_conversion("explicit-kubeconfig")

    def test_aks_get_credentials_default_file(self):
        # Supply the expanded default as the command's argument loader does, within the isolated home.
        self._assert_conversion(self.default_path)

    def test_aks_get_credentials_first_environment_entry(self):
        os.environ["KUBECONFIG"] = os.pathsep.join((self.env_first, self.env_second))
        self._assert_conversion(self.default_path, effective_path=self.env_first)

    def test_aks_get_credentials_relative_environment_entry(self):
        first = os.path.join("env", "config")
        os.environ["KUBECONFIG"] = os.pathsep.join((first, self.env_second))
        self._assert_conversion(self.default_path, effective_path=first)

    def test_aks_get_credentials_empty_first_environment_entry(self):
        os.environ["KUBECONFIG"] = os.pathsep + self.env_second
        self._assert_conversion(self.default_path)
        self.logger.warning.assert_any_call("Invalid path '%s' defined in KUBECONFIG.", "")

    def test_aks_get_credentials_stdout_skips_conversion(self):
        os.environ["KUBECONFIG"] = os.pathsep.join((self.env_first, self.env_second))
        output = io.StringIO()
        with redirect_stdout(output), mock.patch(
                "azure.cli.command_modules.acs.custom.uses_kubelogin_devicecode") as detection:
            self._get_credentials("-")
        self.assertEqual(output.getvalue(), self.credential.value.decode("utf-8") + "\n")
        detection.assert_not_called()
        self.which.assert_not_called()
        self.run.assert_not_called()
        self.logger.warning.assert_not_called()
        self.assertFalse(Path("-").exists())
        self._assert_guards_unchanged()

    def test_aks_get_credentials_non_devicecode(self):
        azurecli_user = deepcopy(self.kubeconfig["users"][0]["user"])
        azurecli_user["exec"]["args"][-1] = "azurecli"
        for name, user in (
                ("azurecli", azurecli_user),
                ("legacy", {"auth-provider": {"name": "azure", "config": {"tenant-id": "test-tenant"}}})):
            with self.subTest(authentication=name):
                self.kubeconfig["users"][0]["user"] = user
                self._get_credentials(name)
                self._assert_merged_without_conversion(name)
                self.which.assert_not_called()
                self.run.assert_not_called()

    def test_aks_get_credentials_missing_kubelogin_is_nonfatal(self):
        self.which.return_value = None
        self._get_credentials("kubeconfig")
        self._assert_merged_without_conversion("kubeconfig")
        self.which.assert_called_once_with("kubelogin")
        self.run.assert_not_called()
        warning = self.logger.warning.call_args.args[0]
        self.assertIn("Please install kubelogin", warning)
        self.assertIn("'az aks install-cli'", warning)
        self.assertIn("'kubelogin convert-kubeconfig -l azurecli'", warning)

    def test_aks_get_credentials_converter_nonzero_exit_is_nonfatal(self):
        self.converter_script = "import sys; sys.exit(17)"
        self._get_credentials("kubeconfig")
        self._assert_merged_without_conversion("kubeconfig")
        self.run.assert_called_once()
        warning = self.logger.warning.call_args.args
        self.assertEqual(warning[0], "Failed to convert kubeconfig with kubelogin: %s")
        self.assertIn("non-zero exit status 17", warning[1])

    def test_aks_get_credentials_converter_startup_error_is_nonfatal(self):
        error = OSError(errno.ENOEXEC, "Exec format error")
        self.run.side_effect = error
        self._get_credentials("kubeconfig")
        self._assert_merged_without_conversion("kubeconfig")
        self.run.assert_called_once()
        self.logger.warning.assert_any_call("Error running kubelogin: %s", str(error))

    def test_aks_get_credentials_context_name(self):
        self._assert_conversion("kubeconfig", context_name="renamed")

    def test_aks_get_credentials_overwrite_existing(self):
        stale = deepcopy(self.kubeconfig)
        stale["clusters"][0]["cluster"]["server"] = "https://old.example.com:443"
        stale["users"][0]["user"] = {"token": "old-token"}
        stale["contexts"][0]["context"]["namespace"] = "old"
        stale["current-context"] = "existing"
        for key in ("clusters", "contexts", "users"):
            stale[key] += self.existing[key]
        before = self._write_config("kubeconfig", stale)

        with mock.patch("azure.cli.command_modules.acs.custom.prompt_y_n", return_value=False) as prompt:
            with self.assertRaisesRegex(CLIError, "A different object named aks already exists in clusters"):
                self._get_credentials("kubeconfig")
            prompt.assert_called_once()
            self.assertEqual(Path("kubeconfig").read_bytes(), before)
            self.which.assert_not_called()
            self.run.assert_not_called()
            self._assert_guards_unchanged()

            prompt.reset_mock()
            self._get_credentials("kubeconfig", overwrite_existing=True)
            prompt.assert_not_called()

        expected = deepcopy(self.kubeconfig)
        expected["users"][0]["user"]["exec"]["args"][-1] = "azurecli"
        for key in ("clusters", "contexts", "users"):
            expected[key] = self.existing[key] + expected[key]
        self.assertEqual(yaml.safe_load(Path("kubeconfig").read_text(encoding="utf-8")), expected)
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(os.stat("kubeconfig").st_mode), 0o600)
        self.run.assert_called_once_with(
            ["kubelogin", "convert-kubeconfig", "-l", "azurecli", "--kubeconfig", "kubeconfig"], check=True)
        self.logger.warning.assert_has_calls([
            mock.call('Merged "aks" as current context in kubeconfig'),
            mock.call("Converted kubeconfig to use Azure CLI authentication."),
        ])
        self._assert_guards_unchanged()

    def test_aks_get_credentials_merge_failure_does_not_convert(self):
        before = self._write_config("kubeconfig", self.existing)
        before_files = set(Path.cwd().iterdir())
        with mock.patch("azure.cli.command_modules.acs.custom.os.replace",
                        side_effect=PermissionError(errno.EACCES, "Permission denied")):
            with self.assertRaisesRegex(FileOperationError, "Permission denied when trying to write to"):
                self._get_credentials("kubeconfig")
        self.assertEqual(Path("kubeconfig").read_bytes(), before)
        self.assertEqual(set(Path.cwd().iterdir()), before_files)
        self.which.assert_not_called()
        self.run.assert_not_called()
        self._assert_guards_unchanged()

    @unittest.skipIf(os.name == "nt", "Symlink test not applicable on Windows")
    def test_aks_get_credentials_symlink_does_not_convert(self):
        path = Path("kubeconfig")
        path.symlink_to(self.default_path)
        with self.assertRaisesRegex(CLIError, "is a symbolic link"):
            self._get_credentials(str(path))
        self.assertTrue(path.is_symlink())
        self.assertEqual(os.readlink(path), self.default_path)
        self.which.assert_not_called()
        self.run.assert_not_called()
        self.logger.warning.assert_not_called()
        self._assert_guards_unchanged()

    def test_aks_get_credentials_admin_does_not_convert(self):
        admin_user = "clusterAdmin_rg_aks"
        self.kubeconfig["users"][0] = {
            "name": admin_user,
            "user": {"client-certificate-data": "dGVzdC1jZXJ0", "client-key-data": "dGVzdC1rZXk="},
        }
        self.kubeconfig["contexts"][0]["context"]["user"] = admin_user
        self._get_credentials("kubeconfig", admin=True)
        self.client.list_cluster_admin_credentials.assert_called_once_with("rg", "aks", server_fqdn=None)
        self.client.list_cluster_user_credentials.assert_not_called()
        merged = yaml.safe_load(Path("kubeconfig").read_text(encoding="utf-8"))
        self.assertEqual(merged["current-context"], "aks-admin")
        self.assertEqual(merged["contexts"][0]["name"], "aks-admin")
        self.which.assert_not_called()
        self.run.assert_not_called()
        self._assert_guards_unchanged()


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

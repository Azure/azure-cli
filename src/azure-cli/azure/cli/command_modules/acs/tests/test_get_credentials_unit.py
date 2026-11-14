# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import yaml

from azure.cli.command_modules.acs import custom


class AKSGetCredentialsUnitTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = os.path.realpath(directory.name)
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.directory)
        environment = mock.patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        os.environ.pop("KUBECONFIG", None)
        self.cmd = SimpleNamespace(cli_ctx=SimpleNamespace(cloud=SimpleNamespace(profile="latest")))
        self.config = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{"name": "test", "cluster": {"server": "https://127.0.0.1"}}],
            "contexts": [{"name": "test", "context": {"cluster": "test", "user": "test"}}],
            "current-context": "test",
            "users": [{"name": "test", "user": {
                "exec": {"command": "kubelogin", "args": ["get-token", "--login", "devicecode"]}
            }}],
        }
        self.client = mock.Mock()

    def _get_credentials(self, path=None, **kwargs):
        self.client.list_cluster_user_credentials.return_value = SimpleNamespace(
            kubeconfigs=[SimpleNamespace(value=yaml.safe_dump(self.config).encode("utf-8"))]
        )
        if path is not None:
            kwargs["path"] = path
        custom.aks_get_credentials(
            self.cmd, self.client, "test-group", "test", overwrite_existing=True, **kwargs
        )

    def _write_config(self, path, config):
        with open(path, "w", encoding="utf-8") as stream:
            yaml.safe_dump(config, stream)
        os.chmod(path, 0o600)

    def _read_config(self, path):
        with open(path, encoding="utf-8") as stream:
            return yaml.safe_load(stream)

    def _install_kubelogin(self, directory="bin", exit_code=0):
        directory = os.path.join(self.directory, directory)
        os.makedirs(directory, exist_ok=True)
        executable = os.path.join(directory, "kubelogin")
        # Exercise actual process launch and file selection without an AKS cluster or token.
        script = """import json
import os
import sys
args = sys.argv[1:]
if args[:3] != ["convert-kubeconfig", "-l", "azurecli"]:
    sys.exit(2)
if "--kubeconfig" in args:
    path = args[args.index("--kubeconfig") + 1]
else:
    path = os.environ.get("KUBECONFIG", os.path.expanduser("~/.kube/config")).split(os.pathsep)[0]
with open(os.environ["AKS_TEST_INVOCATION"], "w", encoding="utf-8") as stream:
    json.dump({"path": path, "cwd": os.getcwd(), "executable": sys.argv[0]}, stream)
if EXIT_CODE:
    sys.exit(EXIT_CODE)
with open(path, encoding="utf-8") as stream:
    config = stream.read()
with open(path, "w", encoding="utf-8") as stream:
    stream.write(config.replace("devicecode", "azurecli"))
"""
        with open(executable, "w", encoding="utf-8") as stream:
            stream.write("#!{}\n".format(sys.executable))
            stream.write(script.replace("EXIT_CODE", str(exit_code)))
        os.chmod(executable, 0o700)
        os.environ["AKS_TEST_INVOCATION"] = os.path.join(self.directory, "invocation.json")
        os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
        return executable

    def _assert_converted(self, path, warnings):
        config = self._read_config(path)
        self.assertEqual(config["current-context"], "test")
        user = next(user for user in config["users"] if user["name"] == "test")
        self.assertEqual(user["user"]["exec"]["args"], ["get-token", "--login", "azurecli"])
        messages = [call.args[0] % call.args[1:] for call in warnings.call_args_list]
        self.assertIn("Converted kubeconfig to use Azure CLI authentication.", messages)
        self.assertFalse(any("Error running kubelogin" in message for message in messages), messages)
        with open(os.environ["AKS_TEST_INVOCATION"], encoding="utf-8") as stream:
            invocation = json.load(stream)
        self.assertEqual(invocation["path"], os.path.abspath(path))
        self.assertEqual(invocation["cwd"], os.path.dirname(os.path.abspath(path)))
        return invocation

    @unittest.skipIf(os.name == "nt", "Executable script fixture requires a POSIX shebang")
    def test_relative_file_is_converted(self):
        self._install_kubelogin()
        with mock.patch.object(custom.logger, "warning") as warnings:
            self._get_credentials("relative-config")
        self._assert_converted("relative-config", warnings)
        self.client.list_cluster_user_credentials.assert_called_once_with(
            "test-group", "test", server_fqdn=None, format=None
        )

    @unittest.skipIf(os.name == "nt", "Executable script fixture requires a POSIX shebang")
    def test_explicit_files_override_kubeconfig(self):
        self._install_kubelogin()
        other_path = os.path.join(self.directory, "other-config")
        other_config = {"apiVersion": "v1", "kind": "Config", "users": []}
        self._write_config(other_path, other_config)
        os.environ["KUBECONFIG"] = other_path
        for path in (os.path.join(self.directory, "absolute-config"), "nested folder/config file"):
            with self.subTest(path=path), mock.patch.object(custom.logger, "warning") as warnings:
                self._get_credentials(path)
                self._assert_converted(path, warnings)
                self.assertEqual(self._read_config(other_path), other_config)
                self.assertEqual(os.environ["KUBECONFIG"], other_path)

    @unittest.skipIf(os.name == "nt", "Executable script fixture requires a POSIX shebang")
    def test_kubeconfig_first_entry_is_converted(self):
        self._install_kubelogin()
        other_config = {"apiVersion": "v1", "kind": "Config", "users": []}
        self._write_config("other-config", other_config)
        os.environ["KUBECONFIG"] = os.pathsep.join(["relative-config", "other-config"])
        with mock.patch.object(custom.logger, "warning") as warnings:
            self._get_credentials()
        self._assert_converted("relative-config", warnings)
        self.assertEqual(self._read_config("other-config"), other_config)
        self.assertEqual(os.environ["KUBECONFIG"], os.pathsep.join(["relative-config", "other-config"]))

    @unittest.skipIf(os.name == "nt", "Executable script fixture requires a POSIX shebang")
    def test_path_installations_and_precedence(self):
        for installations in (
            ("opt/homebrew/bin",), ("usr/local/bin",), ("opt/homebrew/bin", "usr/local/bin")
        ):
            with self.subTest(installations=installations):
                os.environ["PATH"] = ""
                executables = [self._install_kubelogin(directory) for directory in reversed(installations)]
                with mock.patch.object(custom.logger, "warning") as warnings:
                    self._get_credentials("relative-config")
                invocation = self._assert_converted("relative-config", warnings)
                self.assertEqual(invocation["executable"], executables[-1])

    @unittest.skipIf(os.name == "nt", "Executable script fixture requires a POSIX shebang")
    def test_merge_preserves_other_entries_and_current_context(self):
        self._install_kubelogin()
        existing = {
            "apiVersion": "v1", "kind": "Config",
            "clusters": [{"name": "other", "cluster": {"server": "https://127.0.0.2"}}],
            "contexts": [{"name": "other", "context": {"cluster": "other", "user": "other"}}],
            "current-context": "other",
            "users": [{"name": "other", "user": {"token": "synthetic-test-token"}}],
        }
        self._write_config("relative-config", existing)
        with mock.patch.object(custom.logger, "warning") as warnings:
            self._get_credentials("relative-config")
        self._assert_converted("relative-config", warnings)
        merged = self._read_config("relative-config")
        for section in ("clusters", "contexts", "users"):
            self.assertIn(existing[section][0], merged[section])

    def test_stdout_does_not_invoke_converter(self):
        with mock.patch.object(custom, "which") as which, \
                mock.patch.object(custom.subprocess, "run") as run, \
                mock.patch.object(custom.logger, "warning") as warnings, \
                mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            self._get_credentials("-")
        self.assertEqual(yaml.safe_load(output.getvalue()), self.config)
        which.assert_not_called()
        run.assert_not_called()
        warnings.assert_not_called()
        self.assertFalse(os.path.exists("-"))

    def test_missing_kubelogin_warns_without_conversion(self):
        with mock.patch.object(custom, "which", return_value=None), \
                mock.patch.object(custom.subprocess, "run") as run, \
                mock.patch.object(custom.logger, "warning") as warnings:
            self._get_credentials("relative-config")
        run.assert_not_called()
        self.assertEqual(self._read_config("relative-config"), self.config)
        messages = " ".join(call.args[0] % call.args[1:] for call in warnings.call_args_list)
        self.assertIn("kubelogin was not found on PATH", messages)
        self.assertIn("Automatic conversion to Azure CLI authentication could not be completed", messages)
        self.assertNotIn("Error running kubelogin", messages)
        self.assertNotIn("Converted kubeconfig", messages)
        self.assertIn("az aks install-cli", messages)

    @unittest.skipIf(os.name == "nt", "Executable script fixture requires a POSIX shebang")
    def test_failed_converter_does_not_report_success(self):
        self._install_kubelogin(exit_code=7)
        with mock.patch.object(custom.logger, "warning") as warnings:
            self._get_credentials(os.path.join(self.directory, "absolute-config"))
        self.assertEqual(self._read_config("absolute-config"), self.config)
        messages = " ".join(call.args[0] % call.args[1:] for call in warnings.call_args_list)
        self.assertIn("Failed to convert kubeconfig with kubelogin:", messages)
        self.assertNotIn("Converted kubeconfig", messages)
        self.assertNotIn("Error running kubelogin", messages)

    def test_os_error_does_not_report_success(self):
        with mock.patch.object(custom, "which", return_value="/missing/kubelogin"), \
                mock.patch.object(custom.subprocess, "run", side_effect=OSError("cannot execute kubelogin")), \
                mock.patch.object(custom.logger, "warning") as warnings:
            self._get_credentials("relative-config")
        self.assertEqual(self._read_config("relative-config"), self.config)
        messages = " ".join(call.args[0] % call.args[1:] for call in warnings.call_args_list)
        self.assertIn("Error running kubelogin: cannot execute kubelogin", messages)
        self.assertNotIn("Converted kubeconfig", messages)

    def test_credentials_not_requiring_conversion_do_not_need_kubelogin(self):
        for user in (
            {"exec": {"command": "kubelogin", "args": ["get-token", "--login", "azurecli"]}},
            {"token": "synthetic-test-token"},
        ):
            with self.subTest(user=user), mock.patch.object(custom, "which") as which, \
                    mock.patch.object(custom.subprocess, "run") as run:
                self.config["users"][0]["user"] = user
                self._get_credentials("relative-config")
                self.assertEqual(self._read_config("relative-config"), self.config)
                which.assert_not_called()
                run.assert_not_called()

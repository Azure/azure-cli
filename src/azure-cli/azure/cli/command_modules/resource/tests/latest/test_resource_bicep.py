# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
import semver
from types import SimpleNamespace
from unittest import mock

from knack.util import CLIError
from azure.cli.command_modules.resource._bicep import (
    BicepInstallation,
    bicep_version_greater_than_or_equal_to,
    ensure_bicep_installation,
    remove_bicep_installation,
    resolve_bicep_installation,
    run_bicep_command,
    validate_bicep_target_scope,
    _get_bicep_download_url,
    _bicep_version_check_file_path,
)
from azure.cli.command_modules.resource.custom import (
    _prepare_deployment_properties_unmodified,
    _prepare_deployment_what_if_properties,
    _prepare_stacks_templates_and_parameters,
    build_bicep_file,
    build_bicepparam_file,
    format_bicep_file,
    generate_params_file,
    install_bicep_cli,
    lint_bicep_file,
    list_bicep_cli_versions,
    publish_bicep_file,
    restore_bicep_file,
    run_bicep_cli_passthrough,
    show_bicep_cli_version,
    snapshot_bicep_file,
    uninstall_bicep_cli,
    upgrade_bicep_cli,
)
from azure.cli.core.azclierror import (
    ArgumentUsageError, ClientRequestError, FileOperationError, InvalidArgumentValueError,
    InvalidTemplateError, ValidationError,
)
from azure.cli.core.mock import DummyCli


class TestBicep(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = DummyCli(random_config_dir=True)

    @mock.patch("os.path.isfile")
    def test_run_bicep_command_raise_error_if_not_installed_and_not_auto_install(self, isfile_stub):
        isfile_stub.return_value = False

        with contextlib.suppress(FileNotFoundError):
            remove_bicep_installation(self.cli_ctx)

        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "false")
        with self.assertRaisesRegex(CLIError, 'Bicep CLI not found. Install it now by running "az bicep install".'):
            run_bicep_command(self.cli_ctx, ["--version"], auto_install=False)

    @mock.patch("azure.cli.command_modules.resource._bicep.subprocess.run")
    def test_run_bicep_command_includes_stdout_in_error(self, run_mock):
        from azure.cli.command_modules.resource._bicep import _run_command
        from azure.cli.core.azclierror import UnclassifiedUserFault

        process = mock.Mock(stdout=b"changed resource\n", stderr=b"Snapshot validation failed.\n")
        process.check_returncode.side_effect = subprocess.CalledProcessError(1, "bicep")
        run_mock.return_value = process

        with self.assertRaisesRegex(
            UnclassifiedUserFault,
            r"(?s)Snapshot validation failed\..*changed resource",
        ):
            _run_command("bicep", ["snapshot", "main.bicepparam", "--mode", "Validate"])

    @mock.patch("azure.cli.command_modules.resource._bicep._use_binary_from_path")
    @mock.patch("azure.cli.command_modules.resource._bicep.set_use_binary_from_path_config")
    @mock.patch("azure.cli.command_modules.resource._bicep.get_use_binary_from_path_config")
    @mock.patch("os.chmod")
    @mock.patch("os.stat")
    @mock.patch("os.makedirs")
    @mock.patch("io.BufferedWriter")
    @mock.patch("azure.cli.command_modules.resource._bicep.open")
    @mock.patch("azure.cli.command_modules.resource._bicep.urlopen")
    @mock.patch("os.path.exists")
    @mock.patch("os.path.dirname")
    @mock.patch("os.path.isfile")
    def test_use_bicep_cli_from_path_false_after_install(
        self,
        isfile_stub,
        dirname_stub,
        exists_stub,
        urlopen_stub,
        open_stub,
        buffered_writer_stub,
        makedirs_stub,
        stat_stub,
        chmod_stub,
        get_use_binary_from_path_config_stub,
        set_use_binary_from_path_config_mock,
        user_binary_from_path_stub,
    ):
        # Arrange
        isfile_stub.return_value = False
        dirname_stub.return_value = "tmp"
        exists_stub.return_value = True
        buffered_writer_stub.write.return_value = None

        stat_result = mock.Mock()
        stat_result.st_mode = 33206
        stat_stub.return_value = stat_result

        chmod_stub.return_value = None
        makedirs_stub.return_value = None

        response = mock.Mock()
        response.getcode.return_value = 200
        response.read.return_value = b"test"
        urlopen_stub.return_value = response

        user_binary_from_path_stub.return_value = True
        get_use_binary_from_path_config_stub.return_value = "if_found_in_ci"

        # Act
        ensure_bicep_installation(self.cli_ctx, release_tag="v0.14.85", stdout=False)

        # Assert
        set_use_binary_from_path_config_mock.assert_called_once_with(self.cli_ctx, "false")

    @mock.patch("azure.cli.command_modules.resource._bicep.get_use_binary_from_path_config")
    @mock.patch("shutil.which")
    def test_run_bicep_command_raise_error_if_bicep_cli_not_found_when_use_binary_from_path_is_true(self, which_stub, get_use_binary_from_path_config_stub):
        which_stub.return_value = None
        get_use_binary_from_path_config_stub.return_value = "true"

        with self.assertRaisesRegex(
            CLIError,
            'Could not find the "bicep" executable on PATH. To install Bicep via Azure CLI, set the "bicep.use_binary_from_path" configuration to False and run "az bicep install".',
        ):
            run_bicep_command(self.cli_ctx, ["--version"], auto_install=False)

    @mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
    @mock.patch("azure.cli.command_modules.resource._bicep.get_use_binary_from_path_config")
    @mock.patch("azure.cli.command_modules.resource._bicep._logger.debug")
    @mock.patch("azure.cli.command_modules.resource._bicep._run_command")
    @mock.patch("shutil.which")
    def test_run_bicep_command_use_bicep_cli_from_path_in_ci(self, which_stub, run_command_stub, debug_mock, get_use_binary_from_path_config_stub):
        which_stub.return_value = True
        run_command_stub.return_value = "Bicep CLI version 0.13.1 (e3ac80d678)"
        get_use_binary_from_path_config_stub.return_value = "if_found_in_ci"

        run_bicep_command(self.cli_ctx, ["--version"], auto_install=False)

        debug_mock.assert_called_with(
            "Using Bicep CLI from PATH. %s",
            "Bicep CLI version 0.13.1 (e3ac80d678)",
        )

    @mock.patch("azure.cli.command_modules.resource._bicep.get_check_version_config")
    @mock.patch("azure.cli.command_modules.resource._bicep.get_use_binary_from_path_config")
    @mock.patch("azure.cli.command_modules.resource._bicep._logger.warning")
    @mock.patch("azure.cli.command_modules.resource._bicep._run_command")
    @mock.patch("azure.cli.command_modules.resource._bicep.ensure_bicep_installation")
    @mock.patch("azure.cli.command_modules.resource._bicep.get_bicep_latest_release_tag")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.isfile")
    def test_run_bicep_command_check_version(
        self,
        isfile_stub,
        _get_bicep_installed_version_stub,
        get_bicep_latest_release_tag_stub,
        ensure_bicep_installation_mock,
        _run_command_mock,
        warning_mock,
        get_use_binary_from_path_config_stub,
        get_check_version_config_stub,
    ):
        isfile_stub.return_value = True
        _get_bicep_installed_version_stub.return_value = semver.VersionInfo.parse("1.0.0")
        get_bicep_latest_release_tag_stub.return_value = "v2.0.0"
        get_check_version_config_stub.return_value = "true"
        get_use_binary_from_path_config_stub.return_value = "false"

        run_bicep_command(self.cli_ctx, ["--version"])

        warning_mock.assert_called_once_with(
            'A new Bicep release is available: %s. Upgrade now by running "az bicep upgrade".',
            "v2.0.0",
        )

    @mock.patch("azure.cli.command_modules.resource._bicep._logger.warning")
    @mock.patch("azure.cli.command_modules.resource._bicep._run_command")
    @mock.patch("azure.cli.command_modules.resource._bicep.ensure_bicep_installation")
    @mock.patch("azure.cli.command_modules.resource._bicep.get_bicep_latest_release_tag")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.isfile")
    def test_run_bicep_command_check_version_cache_read_write(
        self,
        isfile_stub,
        _get_bicep_installed_version_stub,
        get_bicep_latest_release_tag_stub,
        ensure_bicep_installation_mock,
        _run_command_mock,
        warning_mock,
    ):
        try:
            self._remove_bicep_version_check_file()

            isfile_stub.return_value = True
            _get_bicep_installed_version_stub.return_value = semver.VersionInfo.parse("1.0.0")
            get_bicep_latest_release_tag_stub.return_value = "v2.0.0"

            run_bicep_command(self.cli_ctx, ["--version"])

            self.assertTrue(os.path.isfile(_bicep_version_check_file_path))
        finally:
            self._remove_bicep_version_check_file()

    @mock.patch("azure.cli.command_modules.resource._bicep._use_binary_from_path")
    @mock.patch("os.path.isfile")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.dirname")
    def test_ensure_bicep_installation_skip_download_if_installed_version_matches_release_tag(
        self, dirname_mock, _get_bicep_installed_version_stub, isfile_stub, user_binary_from_path_stub
    ):
        _get_bicep_installed_version_stub.return_value = semver.VersionInfo.parse("0.1.0")
        isfile_stub.return_value = True
        user_binary_from_path_stub.return_value = False

        ensure_bicep_installation(self.cli_ctx, release_tag="v0.1.0")

        dirname_mock.assert_not_called()

    @mock.patch("azure.cli.command_modules.resource._bicep.get_use_binary_from_path_config")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installation_path")
    @mock.patch("shutil.which")
    def test_ensure_bicep_installation_skip_download_if_use_binary_from_path_is_true_and_no_version_is_specified(
        self, which_stub, _get_bicep_installation_path_mock, get_use_binary_from_path_config_stub
    ):
        which_stub.return_value = True
        get_use_binary_from_path_config_stub.return_value = "true"

        ensure_bicep_installation(self.cli_ctx, release_tag=None)

        _get_bicep_installation_path_mock.assert_not_called()

    def test_validate_target_scope_raise_error_if_target_scope_does_not_match_deployment_scope(self):
        with self.assertRaisesRegex(
            InvalidTemplateError, 'The target scope "tenant" does not match the deployment scope "subscription".'
        ):
            validate_bicep_target_scope(
                "https://schema.management.azure.com/schemas/2019-08-01/tenantDeploymentTemplate.json#", "subscription"
            )

    def test_validate_target_scope_success_if_target_scope_matches_deployment_scope(self):
        for template_schema, deployment_scope in [
            ("https://schema.management.azure.com/schemas/2019-08-01/deploymentTemplate.json#", "resourceGroup"),
            (
                "https://schema.management.azure.com/schemas/2019-08-01/subscriptionDeploymentTemplate.json#",
                "subscription",
            ),
            (
                "https://schema.management.azure.com/schemas/2019-08-01/managementGroupDeploymentTemplate.json#",
                "managementGroup",
            ),
            ("https://schema.management.azure.com/schemas/2019-08-01/tenantDeploymentTemplate.json#", "tenant"),
        ]:
            with self.subTest(template_schema=template_schema, deployment_scope=deployment_scope):
                try:
                    validate_bicep_target_scope(template_schema, deployment_scope)
                except InvalidTemplateError as e:
                    self.fail(e.error_msg)
                except Exception:
                    self.fail("Encountered an unexpected exception.")

    def _remove_bicep_version_check_file(self):
        with contextlib.suppress(FileNotFoundError):
            os.remove(_bicep_version_check_file_path)

    def test_get_bicep_download_url_returns_correct_urls(self):
        download_url = _get_bicep_download_url("Windows", "arm64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-win-arm64.exe")

        download_url = _get_bicep_download_url("Windows", "x64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-win-x64.exe")

        download_url = _get_bicep_download_url("Linux", "arm64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-linux-arm64")

        download_url = _get_bicep_download_url("Linux", "aarch64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-linux-arm64")

        download_url = _get_bicep_download_url("Linux", "x64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-linux-x64")

        download_url = _get_bicep_download_url("Darwin", "arm64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-osx-arm64")

        download_url = _get_bicep_download_url("Darwin", "x64", "v0.26.54")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-osx-x64")

        download_url = _get_bicep_download_url("Darwin", "x64", "v0.26.54", "win-arm64")
        self.assertEqual(download_url, "https://downloads.bicep.azure.com/v0.26.54/bicep-win-arm64.exe")

        with self.assertRaises(CLIError):
            _get_bicep_download_url("Made Up", "x64", "v0.26.54")

    @mock.patch("azure.cli.command_modules.resource._bicep._run_command")
    @mock.patch("azure.cli.command_modules.resource._bicep._use_binary_from_path")
    def test_bicep_version_greater_than_or_equal_to_use_binary_from_path(self, use_binary_from_path_mock, run_command_mock):
        use_binary_from_path_mock.return_value = True
        run_command_mock.return_value = "Bicep CLI version 0.13.1 (e3ac80d678)"

        result = bicep_version_greater_than_or_equal_to(self.cli_ctx, "0.13.1")

        self.assertTrue(result)
        run_command_mock.assert_called_once_with("bicep", ["--version"])

    @mock.patch("azure.cli.command_modules.resource._bicep._run_command")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installation_path")
    @mock.patch("azure.cli.command_modules.resource._bicep._use_binary_from_path")
    def test_bicep_version_greater_than_or_equal_to_use_cli_managed_binary(self, use_binary_from_path_mock, get_bicep_installation_path_mock, run_command_mock):
        use_binary_from_path_mock.return_value = False
        get_bicep_installation_path_mock.return_value = ".azure/bin/bicep"
        run_command_mock.return_value = "Bicep CLI version 0.13.1 (e3ac80d678)"

        result = bicep_version_greater_than_or_equal_to(self.cli_ctx, "0.13.2")

        self.assertFalse(result)
        run_command_mock.assert_called_once_with(".azure/bin/bicep", ["--version"])


class _BicepVersionPinningTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
        self.addCleanup(directory.cleanup)
        self.root = directory.name
        self.bin_dir = os.path.join(self.root, "bin")
        self.legacy_path = self.write_file(os.path.join("bin", "bicep.exe"), "default compiler")
        environment = mock.patch.dict(os.environ, {"AZURE_CONFIG_DIR": os.path.join(self.root, "cli-config")})
        environment.start()
        self.addCleanup(environment.stop)
        self.cli_ctx = DummyCli()
        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "false")
        self.cli_ctx.config.set_value("bicep", "check_version", "false")
        self.cmd = mock.Mock(cli_ctx=self.cli_ctx)
        self.patch("_bicep_installation_dir", self.bin_dir)
        self.patch("platform.system", return_value="Windows")
        self.patch("platform.machine", return_value="AMD64")
        self.run_command = self.patch("_run_command", side_effect=self.run_compiler)
        self.get = self.patch("requests.get", side_effect=AssertionError("Unexpected network request"))
        self.urlopen = self.patch("urlopen", side_effect=AssertionError("Unexpected default compiler download"))
        self.commands = (
            (build_bicep_file, "build", "main.bicep"),
            (build_bicepparam_file, "build-params", "main.bicepparam"),
        )

    def patch(self, name, *args, **kwargs):
        patcher = mock.patch(f"azure.cli.command_modules.resource._bicep.{name}", *args, **kwargs)
        patched = patcher.start()
        self.addCleanup(patcher.stop)
        return patched

    def write_file(self, relative_path, contents):
        path = os.path.join(self.root, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(contents)
        return path

    def config(self, contents, relative_path="bicepconfig.json"):
        return self.write_file(relative_path, json.dumps(contents))

    def cache(self, version):
        return self.write_file(
            os.path.join("bin", "bicep-versions", version, "win-x64", "bicep.exe"), "cached compiler"
        )

    def run_compiler(self, executable, args, custom_env=None):
        if args == ["--version"]:
            version = ("9.0.0" if executable in ("bicep", self.legacy_path) else
                       os.path.basename(os.path.dirname(os.path.dirname(executable))))
            return f"Bicep CLI version {version}"
        return "compiled output"


class TestBicepLifecycleVersionPinning(_BicepVersionPinningTestCase):
    def setUp(self):
        super().setUp()
        self.config_path = self.config({"bicep": {"version": "0.31.92"}})
        self.cached_paths = (self.cache("0.31.92"), self.cache("0.32.0"))
        self.version_check_path = self.write_file("bicepVersionCheck.json", '{"latestReleaseTag": "v9.0.0"}')
        self.patch("_bicep_version_check_file_path", self.version_check_path)
        environment = mock.patch.dict(os.environ)
        environment.start()
        self.addCleanup(environment.stop)
        previous_directory = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous_directory)

    def assert_project_cache_unchanged(self):
        with open(self.config_path, encoding="utf-8") as file:
            self.assertEqual({"bicep": {"version": "0.31.92"}}, json.load(file))
        actual = {}
        for directory, _, filenames in os.walk(os.path.join(self.bin_dir, "bicep-versions")):
            for filename in filenames:
                path = os.path.join(directory, filename)
                with open(path, encoding="utf-8") as file:
                    actual[path] = file.read()
        self.assertEqual({path: "cached compiler" for path in self.cached_paths}, actual)

    def test_explicit_install_updates_default_without_changing_project_cache(self):
        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        self.urlopen.side_effect = None
        self.urlopen.return_value.read.return_value = b"installed default"

        install_bicep_cli(self.cmd, version="v0.32.0")

        with open(self.legacy_path, "rb") as file:
            self.assertEqual(b"installed default", file.read())
        self.assertEqual("false", self.cli_ctx.config.get("bicep", "use_binary_from_path"))
        self.run_command.assert_called_once_with(self.legacy_path, ["--version"])
        self.assert_project_cache_unchanged()
        self.get.assert_not_called()
        self.urlopen.assert_called_once_with("https://downloads.bicep.azure.com/v0.32.0/bicep-win-x64.exe")

    def test_install_without_version_keeps_existing_default_without_network_access(self):
        install_bicep_cli(self.cmd)

        with open(self.legacy_path, "rb") as file:
            self.assertEqual(b"default compiler", file.read())
        self.assertEqual("false", self.cli_ctx.config.get("bicep", "use_binary_from_path"))
        self.assert_project_cache_unchanged()
        self.get.assert_not_called()
        self.run_command.assert_not_called()
        self.urlopen.assert_not_called()

    def test_install_without_default_downloads_latest_without_using_project_cache(self):
        os.remove(self.legacy_path)
        self.get.side_effect = None
        self.get.return_value.__enter__.return_value = self.get.return_value
        self.get.return_value.json.return_value = {"tag_name": "v0.32.0"}
        self.urlopen.side_effect = None
        self.urlopen.return_value.read.return_value = b"latest default"

        install_bicep_cli(self.cmd)

        self.get.assert_called_once_with("https://aka.ms/BicepLatestRelease", verify=mock.ANY)
        self.urlopen.assert_called_once_with("https://downloads.bicep.azure.com/v0.32.0/bicep-win-x64.exe")
        with open(self.legacy_path, "rb") as file:
            self.assertEqual(b"latest default", file.read())
        self.assert_project_cache_unchanged()
        self.run_command.assert_not_called()

    def test_upgrade_updates_default_and_preserves_project_cache(self):
        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        self.get.side_effect = None
        self.get.return_value.__enter__.return_value = self.get.return_value
        self.get.return_value.json.return_value = {"tag_name": "v0.32.0"}
        self.urlopen.side_effect = None
        self.urlopen.return_value.read.return_value = b"upgraded default"

        upgrade_bicep_cli(self.cmd)

        self.get.assert_called_once_with("https://aka.ms/BicepLatestRelease", verify=mock.ANY)
        self.urlopen.assert_called_once_with("https://downloads.bicep.azure.com/v0.32.0/bicep-win-x64.exe")
        with open(self.legacy_path, "rb") as file:
            self.assertEqual(b"upgraded default", file.read())
        self.assertEqual("false", self.cli_ctx.config.get("bicep", "use_binary_from_path"))
        self.assert_project_cache_unchanged()
        self.run_command.assert_called_once_with(self.legacy_path, ["--version"])

    def test_version_reports_default_or_path_compiler_instead_of_project_pin(self):
        with mock.patch("shutil.which", return_value="external-bicep"):
            for setting, executable in (("false", self.legacy_path), ("true", "bicep")):
                with self.subTest(setting=setting):
                    self.run_command.reset_mock()
                    self.cli_ctx.config.set_value("bicep", "use_binary_from_path", setting)
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        self.assertIsNone(show_bicep_cli_version(self.cmd))
                    self.assertEqual("Bicep CLI version 9.0.0\n", output.getvalue())
                    self.assertTrue(all(call.args[0] == executable for call in self.run_command.call_args_list))
        self.assert_project_cache_unchanged()
        self.get.assert_not_called()
        self.urlopen.assert_not_called()

    def test_version_does_not_fall_back_to_project_cache_when_default_is_missing(self):
        os.remove(self.legacy_path)

        with self.assertRaisesRegex(FileOperationError, "Bicep CLI not found"):
            show_bicep_cli_version(self.cmd)

        self.assert_project_cache_unchanged()
        self.run_command.assert_not_called()
        self.get.assert_not_called()
        self.urlopen.assert_not_called()

    def test_list_versions_reports_published_releases_instead_of_cached_versions(self):
        self.get.side_effect = None
        self.get.return_value.json.return_value = [{"tag_name": "v9.1.0"}, {"tag_name": "v9.0.0"}]

        self.assertEqual(["v9.1.0", "v9.0.0"], list_bicep_cli_versions(self.cmd))

        self.get.assert_called_once_with("https://aka.ms/BicepReleases", verify=mock.ANY)
        self.assert_project_cache_unchanged()
        self.run_command.assert_not_called()
        self.urlopen.assert_not_called()

    def test_explicit_install_target_platform_updates_default_not_project_cache(self):
        self.urlopen.side_effect = None
        self.urlopen.return_value.read.return_value = b"foreign compiler"

        install_bicep_cli(self.cmd, version="v0.32.0", target_platform="win-arm64")

        with open(self.legacy_path, "rb") as file:
            self.assertEqual(b"foreign compiler", file.read())
        self.urlopen.assert_called_once_with("https://downloads.bicep.azure.com/v0.32.0/bicep-win-arm64.exe")
        self.run_command.assert_called_once_with(self.legacy_path, ["--version"])
        self.get.assert_not_called()
        self.assert_project_cache_unchanged()

    def test_uninstall_removes_default_but_preserves_reusable_project_cache_and_other_files(self):
        unrelated_paths = (
            self.write_file(os.path.join("bin", "other-tool.exe"), "unrelated"),
            self.write_file(os.path.join("bin", "bicep-0.31.92", "bicep.exe"), "other client"),
            self.write_file(os.path.join("external", "bicep.exe"), "PATH compiler"),
        )
        for attempt in range(2):
            with self.subTest(attempt=attempt):
                uninstall_bicep_cli(self.cmd)

                self.assertFalse(os.path.exists(self.legacy_path))
                self.assertFalse(os.path.exists(self.version_check_path))
                self.assert_project_cache_unchanged()
                for path, contents in zip(unrelated_paths, ("unrelated", "other client", "PATH compiler")):
                    with open(path, encoding="utf-8") as file:
                        self.assertEqual(contents, file.read())
                self.run_command.assert_not_called()

        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "false")
        build_bicep_file(self.cmd, self.write_file("main.bicep", ""))
        self.assertEqual(self.cached_paths[0], self.run_command.call_args.args[0])
        self.assertFalse(os.path.exists(self.legacy_path))
        self.get.assert_not_called()
        self.urlopen.assert_not_called()


class TestBicepBuildVersionPinning(_BicepVersionPinningTestCase):
    def test_build_commands_resolve_inherited_range_from_entrypoint_not_working_directory(self):
        self.config({"bicep": {"version": "9.0.0"}})
        self.config({"extends": "../shared/base.json"}, os.path.join("app", "bicepconfig.json"))
        self.config({"bicep": {"version": ">=0.31, <0.32"}}, os.path.join("shared", "base.json"))
        self.cache("0.31.1")
        selected = self.cache("0.31.92")
        self.cache("9.0.0")
        previous_directory = os.getcwd()
        try:
            os.chdir(self.root)
            for handler, command, filename in self.commands:
                with self.subTest(command=command):
                    self.run_command.reset_mock()
                    entrypoint = self.write_file(os.path.join("app", filename), "")
                    handler(self.cmd, entrypoint)
                    self.assertEqual([
                        mock.call(selected, ["--version"]),
                        mock.call(selected, [command, entrypoint], None),
                    ], self.run_command.call_args_list)
        finally:
            os.chdir(previous_directory)
        self.get.assert_not_called()
        self.urlopen.assert_not_called()

    def test_build_commands_honor_exact_pin_and_preserve_options_and_stdout(self):
        self.config({"bicep": {"version": "0.31.1"}})
        selected = self.cache("0.31.1")
        self.cache("0.31.92")
        for handler, command, filename in self.commands:
            for options, arguments in (
                ({"stdout": True, "outdir": "output", "no_restore": True},
                 ["--outdir", "output", "--no-restore", "--stdout"]),
                ({"outfile": "output.json"}, ["--outfile", "output.json"]),
            ):
                with self.subTest(command=command, options=options), mock.patch("builtins.print") as print_mock:
                    self.run_command.reset_mock()
                    entrypoint = self.write_file(filename, "")
                    handler(self.cmd, entrypoint, **options)
                    self.run_command.assert_called_with(selected, [command, entrypoint] + arguments, None)
                    if options.get("stdout"):
                        print_mock.assert_called_once_with("compiled output")
                    else:
                        print_mock.assert_not_called()
        self.get.assert_not_called()

    def test_nearest_config_without_constraint_preserves_default_installation(self):
        self.config({"bicep": {"version": "0.31.92"}})
        self.config({}, os.path.join("app", "bicepconfig.json"))
        acquire = self.patch("ensure_bicep_version_installation")
        for handler, command, filename in self.commands:
            with self.subTest(command=command):
                self.run_command.reset_mock()
                entrypoint = self.write_file(os.path.join("app", filename), "")
                handler(self.cmd, entrypoint)
                self.run_command.assert_called_once_with(self.legacy_path, [command, entrypoint], None)
        acquire.assert_not_called()
        self.get.assert_not_called()

    def test_build_commands_without_config_preserve_path_execution(self):
        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        acquire = self.patch("ensure_bicep_version_installation")
        with mock.patch("azure.cli.command_modules.resource._bicep_config.find_bicep_config_file", return_value=None), \
                mock.patch("shutil.which", return_value="path compiler"):
            for handler, command, filename in self.commands:
                with self.subTest(command=command):
                    self.run_command.reset_mock()
                    entrypoint = self.write_file(filename, "")
                    handler(self.cmd, entrypoint)
                    self.assertEqual([
                        mock.call("bicep", ["--version"]),
                        mock.call("bicep", [command, entrypoint], None),
                    ], self.run_command.call_args_list)
        acquire.assert_not_called()
        self.get.assert_not_called()

    @mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"})
    def test_pin_takes_precedence_over_path_without_changing_settings(self):
        self.config({"bicep": {"version": "0.31.92"}})
        selected = self.cache("0.31.92")
        with mock.patch("shutil.which") as which:
            for setting in ("true", "false", "if_found_in_ci"):
                self.cli_ctx.config.set_value("bicep", "use_binary_from_path", setting)
                for handler, command, filename in self.commands:
                    with self.subTest(setting=setting, command=command):
                        entrypoint = self.write_file(filename, "")
                        handler(self.cmd, entrypoint)
                        self.run_command.assert_called_with(selected, [command, entrypoint], None)
                        self.assertEqual(setting, self.cli_ctx.config.get("bicep", "use_binary_from_path"))
            which.assert_not_called()

    def test_invalid_configuration_or_constraint_fails_before_running_or_downloading(self):
        for config, error in (
            ({"bicep": {"version": "^0.31"}}, ValidationError),
            ({"bicep": {"version": ""}}, ValidationError),
            ({"bicep": {"version": ">0.32, <0.31"}}, ValidationError),
            ({"extends": "missing.json"}, FileOperationError),
            ({"extends": "bicepconfig.json", "bicep": {"version": "0.31.92"}}, ValidationError),
        ):
            self.config(config)
            for handler, command, filename in self.commands:
                with self.subTest(config=config, command=command):
                    entrypoint = self.write_file(filename, "")
                    with self.assertRaises(error):
                        handler(self.cmd, entrypoint)
                    self.run_command.assert_not_called()
                    self.get.assert_not_called()
                    self.urlopen.assert_not_called()

    def test_acquisition_failure_does_not_fall_back_to_default_or_path(self):
        import requests

        self.config({"bicep": {"version": "0.31.92"}})
        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        self.get.side_effect = requests.ConnectionError("offline")
        for handler, command, filename in self.commands:
            with self.subTest(command=command):
                entrypoint = self.write_file(filename, "")
                with self.assertRaisesRegex(ClientRequestError, "offline"):
                    handler(self.cmd, entrypoint)
        self.run_command.assert_not_called()
        self.urlopen.assert_not_called()

    def test_selected_installation_preserves_environment_and_skips_default_upgrade_checks(self):
        installation = BicepInstallation(semver.VersionInfo(0, 31, 92), self.cache("0.31.92"))
        args = ["build-params", "main.bicepparam", "--stdout"]
        environment = {"BICEP_PARAMETERS_OVERRIDES": '{"name": "value"}'}
        use_path = self.patch("_use_binary_from_path")
        upgrade_check = self.patch("get_bicep_latest_release_tag")
        install_default = self.patch("ensure_bicep_installation")
        self.assertEqual("compiled output", run_bicep_command(
            self.cli_ctx, args, auto_install=False, custom_env=environment, installation=installation
        ))
        self.run_command.assert_called_once_with(installation.executable_path, args, environment)
        use_path.assert_not_called()
        upgrade_check.assert_not_called()
        install_default.assert_not_called()

    def test_capability_checks_use_selected_version_instead_of_default_or_path(self):
        installation = BicepInstallation(semver.VersionInfo(0, 13, 1), self.cache("0.13.1"))
        use_path = self.patch("_use_binary_from_path")
        for minimum, supported in (("0.13.0", True), ("0.13.1", True), ("0.13.2", False)):
            with self.subTest(minimum=minimum):
                self.assertEqual(supported, bicep_version_greater_than_or_equal_to(
                    self.cli_ctx, minimum, installation=installation
                ))
        use_path.assert_not_called()
        self.run_command.assert_not_called()


class TestBicepDeploymentVersionPinning(_BicepVersionPinningTestCase):
    def setUp(self):
        super().setUp()
        self.cmd.get_models.return_value = (SimpleNamespace, SimpleNamespace, SimpleNamespace)
        self.template = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "parameters": {"name": {"type": "string", "defaultValue": "original"}},
            "resources": [],
        }
        self.using_none = False
        self.template_spec_id = None
        for attribute, name, function in (
            ("resolve", "resolve_bicep_installation", resolve_bicep_installation),
            ("install_default", "ensure_bicep_installation", ensure_bicep_installation),
        ):
            patcher = mock.patch(f"azure.cli.command_modules.resource.custom.{name}", wraps=function)
            setattr(self, attribute, patcher.start())
            self.addCleanup(patcher.stop)

    def run_compiler(self, executable, args, custom_env=None):
        if args == ["--version"]:
            return super().run_compiler(executable, args, custom_env)
        if args[0] == "build":
            return json.dumps(self.template)
        self.assertEqual("build-params", args[0])
        overrides = json.loads((custom_env or {}).get("BICEP_PARAMETERS_OVERRIDES", "{}"))
        result = {
            "parametersJson": json.dumps({"parameters": {"name": {"value": overrides.get("name", "original")}}})
        }
        if self.using_none:
            self.assertNotIn("--bicep-file", args)
        elif self.template_spec_id:
            result["templateSpecId"] = self.template_spec_id
        else:
            result["templateJson"] = json.dumps(self.template)
        return json.dumps(result)

    def prepare(self, template_file=None, parameters=None, scope="resourceGroup", stack=False, **kwargs):
        if stack:
            return _prepare_stacks_templates_and_parameters(
                self.cmd, scope, SimpleNamespace(template=None, template_link=None),
                template_file, kwargs.get("template_spec"), kwargs.get("template_uri"),
                parameters, None,
            )
        return _prepare_deployment_properties_unmodified(
            self.cmd, scope, template_file=template_file, parameters=parameters, no_prompt=True, **kwargs
        )

    def compiler_calls(self):
        return [call for call in self.run_command.call_args_list if call.args[1] != ["--version"]]

    def test_template_deployments_and_stacks_use_pinned_compiler_at_each_scope(self):
        self.config({"bicep": {"version": ">=0.31, <0.32"}})
        selected = self.cache("0.31.92")
        entrypoint = self.write_file(os.path.join("templates", "main.bicep"), "")
        for scope, schema in (
            ("resourceGroup", "deploymentTemplate"),
            ("subscription", "subscriptionDeploymentTemplate"),
            ("managementGroup", "managementGroupDeploymentTemplate"),
            ("tenant", "tenantDeploymentTemplate"),
        ):
            self.template["$schema"] = f"https://schema.management.azure.com/schemas/2019-08-01/{schema}.json#"
            for stack in (False, True):
                if stack and scope == "tenant":
                    continue
                with self.subTest(scope=scope, stack=stack):
                    self.run_command.reset_mock()
                    self.resolve.reset_mock()
                    properties = self.prepare(entrypoint, scope=scope, stack=stack)
                    actual = properties.template if stack else json.loads(properties.template)
                    self.assertEqual(self.template, actual)
                    self.resolve.assert_called_once_with(entrypoint)
                    self.run_command.assert_has_calls([
                        mock.call(selected, ["--version"]),
                        mock.call(selected, ["build", "--stdout", entrypoint], None),
                    ])
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    def test_parameter_entrypoint_controls_compiler_and_recompilation(self):
        self.config({"bicep": {"version": "9.0.0"}})
        self.config({"bicep": {"version": "0.31.92"}}, os.path.join("params", "bicepconfig.json"))
        selected = self.cache("0.31.92")
        template_file = self.write_file(os.path.join("templates", "main.bicep"), "")
        param_file = self.write_file(os.path.join("params", "main.bicepparam"), "using '../templates/main.bicep'")
        for stack in (False, True):
            for explicit_template in (None, template_file):
                with self.subTest(stack=stack, explicit_template=explicit_template):
                    self.run_command.reset_mock()
                    self.resolve.reset_mock()
                    properties = self.prepare(explicit_template, [[param_file, "name=changed"]], stack=stack)
                    self.assertEqual({"name": {"value": "changed"}}, properties.parameters)
                    self.resolve.assert_called_once_with(param_file)
                    calls = self.compiler_calls()
                    self.assertEqual(2, len(calls))
                    for call in calls:
                        self.assertEqual(selected, call.args[0])
                        self.assertEqual(["build-params", param_file], call.args[1][:2])
                        self.assertEqual(explicit_template is not None, "--bicep-file" in call.args[1])
                    self.assertEqual(
                        {"name": "changed"}, json.loads(calls[-1].args[2]["BICEP_PARAMETERS_OVERRIDES"])
                    )
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    def test_using_none_preserves_template_and_selection_with_supplemental_parameters(self):
        self.using_none = True
        self.config({"bicep": {"version": "9.0.0"}})
        self.config({"bicep": {"version": "0.31.92"}}, os.path.join("params", "bicepconfig.json"))
        selected = self.cache("0.31.92")
        param_file = self.write_file(os.path.join("params", "main.bicepparam"), "using none")
        for extension in ("bicep", "json"):
            template_file = self.write_file(f"main.{extension}", json.dumps(self.template))
            for stack in (False, True):
                for supplemental in (False, True):
                    with self.subTest(extension=extension, stack=stack, supplemental=supplemental):
                        self.run_command.reset_mock()
                        self.resolve.reset_mock()
                        parameters = [[param_file, "name=changed"]] if supplemental else [[param_file]]
                        properties = self.prepare(template_file, parameters, stack=stack)
                        actual = properties.template if stack else json.loads(properties.template)
                        self.assertEqual(self.template, actual)
                        self.assertEqual(
                            {"name": {"value": "changed" if supplemental else "original"}}, properties.parameters
                        )
                        self.resolve.assert_called_once_with(param_file)
                        calls = self.compiler_calls()
                        self.assertTrue(all(call.args[0] == selected for call in calls))
                        self.assertEqual(
                            int(extension == "bicep"), sum(call.args[1][0] == "build" for call in calls)
                        )
                        self.assertEqual(
                            2 if supplemental else 1, sum(call.args[1][0] == "build-params" for call in calls)
                        )
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    def test_pinned_capability_checks_enforce_minimum_versions_without_upgrading(self):
        param_file = self.write_file("main.bicepparam", "using './main.bicep'")
        for version, supplemental, supported in (
            ("0.13.1", False, False), ("0.14.85", False, True),
            ("0.22.5", True, False), ("0.22.6", True, True),
        ):
            self.config({"bicep": {"version": version}})
            selected = self.cache(version)
            parameters = [[param_file, "name=changed"]] if supplemental else [[param_file]]
            for stack in (False, True):
                with self.subTest(version=version, supplemental=supplemental, stack=stack):
                    self.run_command.reset_mock()
                    if supported:
                        self.prepare(parameters=parameters, stack=stack)
                        self.assertTrue(all(call.args[0] == selected for call in self.compiler_calls()))
                    else:
                        with self.assertRaisesRegex(ArgumentUsageError, "bicep.version"):
                            self.prepare(parameters=parameters, stack=stack)
                        self.run_command.assert_called_once_with(selected, ["--version"])
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    def test_unpinned_deployments_preserve_default_and_path_execution(self):
        self.config({})
        template_file = self.write_file("main.bicep", "")
        param_file = self.write_file("main.bicepparam", "using './main.bicep'")
        with mock.patch("shutil.which", return_value="path compiler"):
            for setting, executable in (("false", self.legacy_path), ("true", "bicep")):
                self.cli_ctx.config.set_value("bicep", "use_binary_from_path", setting)
                for stack in (False, True):
                    for parameters in (None, [[param_file, "name=changed"]]):
                        with self.subTest(setting=setting, stack=stack, parameters=parameters):
                            self.run_command.reset_mock()
                            properties = self.prepare(template_file, parameters, stack=stack)
                            actual = properties.template if stack else json.loads(properties.template)
                            self.assertEqual(self.template, actual)
                            calls = self.compiler_calls()
                            self.assertTrue(calls)
                            self.assertTrue(all(call.args[0] == executable for call in calls))
        self.get.assert_not_called()
        self.urlopen.assert_not_called()

    def test_json_uri_and_template_spec_deployments_do_not_resolve_a_compiler(self):
        self.config({"extends": "missing.json"})
        template_file = self.write_file("main.json", json.dumps(self.template))
        with mock.patch(
            "azure.cli.command_modules.resource.custom._urlretrieve", return_value=json.dumps(self.template).encode()
        ), mock.patch(
            "azure.cli.command_modules.resource.custom._load_template_spec_template", return_value=self.template
        ):
            for stack in (False, True):
                for inputs in (
                    {"template_file": template_file},
                    {"template_uri": "https://example.com/template.json"},
                    {"template_spec": "/subscriptions/example/templateSpecs/example/versions/1"},
                ):
                    with self.subTest(stack=stack, inputs=inputs):
                        self.prepare(stack=stack, **inputs)
        self.resolve.assert_not_called()
        self.install_default.assert_not_called()
        self.run_command.assert_not_called()
        self.get.assert_not_called()

    def test_what_if_preparation_uses_pinned_compiler(self):
        self.config({"bicep": {"version": "0.31.92"}})
        selected = self.cache("0.31.92")
        template_file = self.write_file("main.bicep", "")
        with mock.patch(
            "azure.cli.command_modules.resource.custom.get_sdk", return_value=(SimpleNamespace, SimpleNamespace)
        ):
            properties = _prepare_deployment_what_if_properties(
                self.cmd, "resourceGroup", template_file, None, None,
                "Incremental", "FullResourcePayloads", True, None, None, None,
            )
        self.assertEqual(self.template, json.loads(properties.template))
        self.run_command.assert_called_with(selected, ["build", "--stdout", template_file], None)
        self.resolve.assert_called_once_with(template_file)
        self.install_default.assert_not_called()

    def test_pinning_failures_stop_deployment_without_default_or_path_fallback(self):
        import requests

        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        template_file = self.write_file("main.bicep", "")
        param_file = self.write_file("main.bicepparam", "using './main.bicep'")
        catalog = mock.MagicMock()
        catalog.__enter__.return_value = catalog
        catalog.json.return_value = [{"tag_name": "v9.0.0"}]
        for config, response, error in (
            ({"extends": "bicepconfig.json"}, None, ValidationError),
            ({"bicep": {"version": "0.31.92"}}, requests.ConnectionError("offline"), ClientRequestError),
            ({"bicep": {"version": "0.31.92"}}, catalog, ValidationError),
        ):
            self.config(config)
            self.get.side_effect = response if isinstance(response, Exception) else None
            self.get.return_value = response
            for stack in (False, True):
                for parameters in (None, [[param_file]]):
                    with self.subTest(config=config, stack=stack, parameters=parameters):
                        with self.assertRaises(error):
                            self.prepare(template_file, parameters, stack=stack)
        self.run_command.assert_not_called()
        self.install_default.assert_not_called()
        self.urlopen.assert_not_called()

    def test_parameter_template_spec_keeps_selected_compiler_for_inline_overrides(self):
        self.config({"bicep": {"version": "0.31.92"}})
        selected = self.cache("0.31.92")
        self.template_spec_id = "/subscriptions/example/templateSpecs/example/versions/1"
        param_file = self.write_file("main.bicepparam", "using 'ts:example'")
        with mock.patch(
            "azure.cli.command_modules.resource.custom._load_template_spec_template", return_value=self.template
        ):
            for stack in (False, True):
                with self.subTest(stack=stack):
                    self.run_command.reset_mock()
                    self.resolve.reset_mock()
                    properties = self.prepare(parameters=[[param_file, "name=changed"]], stack=stack)
                    self.assertEqual(self.template_spec_id, properties.template_link.id)
                    self.assertEqual({"name": {"value": "changed"}}, properties.parameters)
                    self.assertEqual(2, len(self.compiler_calls()))
                    self.assertTrue(all(call.args[0] == selected for call in self.compiler_calls()))
                    self.resolve.assert_called_once_with(param_file)
        self.install_default.assert_not_called()
        self.get.assert_not_called()


class TestBicepFileCommandVersionPinning(_BicepVersionPinningTestCase):
    def setUp(self):
        super().setUp()
        target = "br:example.azurecr.io/modules/example:v1"
        self.file_commands = (
            (lint_bicep_file, "lint", "main.bicep", "0.7.4", {}, []),
            (restore_bicep_file, "restore", "main.bicep", "0.4.1008", {}, []),
            (generate_params_file, "generate-params", "main.bicep", "0.7.4", {}, []),
            (snapshot_bicep_file, "snapshot", "main.bicepparam", "0.41.2", {}, []),
            (format_bicep_file, "format", "main.bicep", "0.12.1", {}, []),
            (publish_bicep_file, "publish", "main.bicep", "0.4.1008",
             {"target": target}, ["--target", target]),
        )
        for attribute, name, function in (
            ("resolve", "resolve_bicep_installation", resolve_bicep_installation),
            ("install_default", "ensure_bicep_installation", ensure_bicep_installation),
        ):
            patcher = mock.patch(f"azure.cli.command_modules.resource.custom.{name}", wraps=function)
            setattr(self, attribute, patcher.start())
            self.addCleanup(patcher.stop)

    @mock.patch("builtins.print")
    def test_commands_use_highest_compatible_cache_from_inherited_entrypoint_config(self, print_mock):
        self.config({"bicep": {"version": "9.0.0"}})
        self.config({"extends": "../shared/base.json"}, os.path.join("app", "bicepconfig.json"))
        self.config({"bicep": {"version": ">=0.41, <1"}}, os.path.join("shared", "base.json"))
        self.cache("0.41.2")
        selected = self.cache("0.42.1")
        self.cache("1.0.0")
        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        for handler, command, filename, _, options, flags in self.file_commands:
            with self.subTest(command=command):
                self.resolve.reset_mock()
                self.run_command.reset_mock()
                print_mock.reset_mock()
                entrypoint = self.write_file(os.path.join("app", filename), "")
                handler(self.cmd, entrypoint, **options)
                self.resolve.assert_called_once_with(entrypoint)
                self.assertEqual([
                    mock.call(selected, ["--version"]),
                    mock.call(selected, [command, entrypoint] + flags, None),
                ], self.run_command.call_args_list)
                if command in ("lint", "snapshot"):
                    print_mock.assert_called_once_with("compiled output")
                else:
                    print_mock.assert_not_called()
        self.assertEqual("true", self.cli_ctx.config.get("bicep", "use_binary_from_path"))
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    @mock.patch("builtins.print")
    def test_pinned_commands_accept_their_exact_minimum_version(self, _):
        for handler, command, filename, minimum, options, flags in self.file_commands:
            with self.subTest(command=command):
                self.config({"bicep": {"version": minimum}})
                selected = self.cache(minimum)
                self.run_command.reset_mock()
                entrypoint = self.write_file(filename, "")
                handler(self.cmd, entrypoint, **options)
                self.run_command.assert_called_with(selected, [command, entrypoint] + flags, None)
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    def test_pinned_commands_reject_unsupported_versions_without_using_newer_default(self):
        self.config({"bicep": {"version": "0.0.0"}})
        selected = self.cache("0.0.0")
        for handler, command, filename, minimum, options, _ in self.file_commands:
            with self.subTest(command=command):
                self.run_command.reset_mock()
                entrypoint = self.write_file(filename, "")
                with self.assertRaisesRegex(ValidationError, f"bicep.version to allow {minimum}"):
                    handler(self.cmd, entrypoint, **options)
                self.run_command.assert_called_once_with(selected, ["--version"])
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    @mock.patch("builtins.print")
    def test_pinned_commands_preserve_options_and_stdout(self, print_mock):
        self.config({"bicep": {"version": "0.41.2"}})
        selected = self.cache("0.41.2")
        for handler, command, filename, options, flags in (
            (lint_bicep_file, "lint", "main.bicep",
             {"no_restore": True, "diagnostics_format": "sarif"},
             ["--no-restore", "--diagnostics-format", "sarif"]),
            (restore_bicep_file, "restore", "main.bicep", {"force": True}, ["--force"]),
            (generate_params_file, "generate-params", "main.bicep",
             {"no_restore": True, "outfile": "params.bicepparam", "output_format": "bicepparam",
              "include_params": "all", "stdout": True},
             ["--no-restore", "--outfile", "params.bicepparam", "--output-format", "bicepparam",
              "--include-params", "all", "--stdout"]),
            (snapshot_bicep_file, "snapshot", "main.bicepparam",
             {"mode": "Validate", "tenant_id": "tenant", "subscription_id": "subscription",
              "management_group_id": "management-group", "location": "westus",
              "resource_group": "resource-group", "deployment_name": "deployment"},
             ["--mode", "Validate", "--tenant-id", "tenant", "--subscription-id", "subscription",
              "--management-group-id", "management-group", "--location", "westus",
              "--resource-group", "resource-group", "--deployment-name", "deployment"]),
            (format_bicep_file, "format", "main.bicep",
             {"outdir": "output", "stdout": True}, ["--outdir", "output", "--stdout"]),
            (publish_bicep_file, "publish", "main.bicep",
             {"target": "br:example.azurecr.io/example:v1", "documentation_uri": "https://example.com/docs",
              "with_source": True, "force": True},
             ["--target", "br:example.azurecr.io/example:v1",
              "--documentation-uri", "https://example.com/docs", "--with-source", "--force"]),
        ):
            with self.subTest(command=command):
                self.run_command.reset_mock()
                print_mock.reset_mock()
                entrypoint = self.write_file(filename, "")
                handler(self.cmd, entrypoint, **options)
                self.run_command.assert_called_with(selected, [command, entrypoint] + flags, None)
                if command in ("restore", "publish"):
                    print_mock.assert_not_called()
                else:
                    print_mock.assert_called_once_with("compiled output")
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    @mock.patch("builtins.print")
    def test_format_uses_selected_version_for_old_and_new_argument_spellings(self, print_mock):
        entrypoint = self.write_file("main.bicep", "")
        for version, flags in (
            ("0.26.53", ["newline", "Auto", "indentKind", "Space", "indentSize", "4", "--insertFinalNewline"]),
            ("0.26.54", ["--newline-kind", "LF", "--indent-kind", "Space",
                         "--indent-size", "4", "--insert-final-newline"]),
        ):
            with self.subTest(version=version):
                self.config({"bicep": {"version": version}})
                selected = self.cache(version)
                format_bicep_file(
                    self.cmd, entrypoint, stdout=True, newline="Auto", indent_kind="Space",
                    indent_size="4", insert_final_newline=True,
                )
                self.run_command.assert_called_with(selected, ["format", entrypoint, "--stdout"] + flags, None)
                print_mock.assert_called_with("compiled output")
        self.install_default.assert_not_called()

    def test_publish_uses_selected_version_for_documentation_argument_and_alias_precedence(self):
        entrypoint = self.write_file("main.bicep", "")
        target = "br:example.azurecr.io/example:v1"
        for version, option in (("0.26.53", "--documentationUri"), ("0.26.54", "--documentation-uri")):
            for arguments, uri in (
                ({"documentationUri": "https://example.com/old"}, "https://example.com/old"),
                ({"documentationUri": "https://example.com/old", "documentation_uri": "https://example.com/new"},
                 "https://example.com/new"),
            ):
                with self.subTest(version=version, arguments=arguments):
                    self.config({"bicep": {"version": version}})
                    selected = self.cache(version)
                    publish_bicep_file(self.cmd, entrypoint, target, **arguments)
                    self.run_command.assert_called_with(
                        selected, ["publish", entrypoint, "--target", target, option, uri], None
                    )
        self.install_default.assert_not_called()

    def test_publish_checks_requested_feature_minimums_before_execution(self):
        entrypoint = self.write_file("main.bicep", "")
        target = "br:example.azurecr.io/example:v1"
        for minimum, below, options in (
            ("0.14.46", "0.14.45", {"documentation_uri": "https://example.com/docs"}),
            ("0.23.1", "0.23.0", {"with_source": True}),
            ("0.17.1", "0.17.0", {"force": True}),
        ):
            for version, supported in ((below, False), (minimum, True)):
                with self.subTest(version=version, options=options):
                    self.config({"bicep": {"version": version}})
                    selected = self.cache(version)
                    self.run_command.reset_mock()
                    if supported:
                        publish_bicep_file(self.cmd, entrypoint, target, **options)
                        self.assertEqual("publish", self.run_command.call_args.args[1][0])
                        self.assertEqual(selected, self.run_command.call_args.args[0])
                    else:
                        with self.assertRaisesRegex(ValidationError, f"bicep.version to allow {minimum}"):
                            publish_bicep_file(self.cmd, entrypoint, target, **options)
                        self.run_command.assert_called_once_with(selected, ["--version"])
        self.install_default.assert_not_called()
        self.get.assert_not_called()

    def test_publish_does_not_execute_when_a_later_requested_option_is_unsupported(self):
        self.config({"bicep": {"version": "0.14.46"}})
        selected = self.cache("0.14.46")
        entrypoint = self.write_file("main.bicep", "")
        with self.assertRaisesRegex(ValidationError, "publish --force"):
            publish_bicep_file(
                self.cmd, entrypoint, "br:example.azurecr.io/example:v1",
                documentation_uri="https://example.com/docs", force=True,
            )
        self.run_command.assert_called_once_with(selected, ["--version"])
        self.install_default.assert_not_called()

    @mock.patch("builtins.print")
    def test_unpinned_commands_preserve_default_and_path_execution(self, _):
        self.config({})
        with mock.patch("shutil.which", return_value="path compiler"):
            for setting, executable in (("false", self.legacy_path), ("true", "bicep")):
                self.cli_ctx.config.set_value("bicep", "use_binary_from_path", setting)
                for handler, command, filename, _, options, flags in self.file_commands:
                    with self.subTest(setting=setting, command=command):
                        self.resolve.reset_mock()
                        self.install_default.reset_mock()
                        self.run_command.reset_mock()
                        entrypoint = self.write_file(filename, "")
                        handler(self.cmd, entrypoint, **options)
                        self.resolve.assert_called_once_with(entrypoint)
                        self.run_command.assert_called_with(executable, [command, entrypoint] + flags, None)
                        self.install_default.assert_called_once()
        self.get.assert_not_called()
        self.urlopen.assert_not_called()

    def test_unpinned_publish_keeps_existing_unsupported_option_logging(self):
        self.config({})
        entrypoint = self.write_file("main.bicep", "")
        self.run_command.side_effect = lambda executable, args, custom_env=None: (
            "Bicep CLI version 0.14.45" if args == ["--version"] else ""
        )
        with mock.patch("azure.cli.command_modules.resource.custom.logger.error") as log:
            publish_bicep_file(
                self.cmd, entrypoint, "br:example.azurecr.io/example:v1",
                documentation_uri="https://example.com/docs",
            )
        log.assert_called_once()
        self.run_command.assert_called_with(
            self.legacy_path, ["publish", entrypoint, "--target", "br:example.azurecr.io/example:v1"], None
        )

    def test_configuration_and_acquisition_errors_prevent_command_side_effects(self):
        import requests

        self.cli_ctx.config.set_value("bicep", "use_binary_from_path", "true")
        for config, error in (
            ({"extends": "bicepconfig.json"}, ValidationError),
            ({"extends": "missing.json"}, FileOperationError),
            ({"bicep": {"version": "^0.41"}}, ValidationError),
            ({"bicep": {"version": "0.41.2"}}, ClientRequestError),
        ):
            self.config(config)
            self.get.side_effect = requests.ConnectionError("offline")
            for handler, command, filename, _, options, _ in self.file_commands:
                with self.subTest(command=command, config=config):
                    entrypoint = self.write_file(filename, "")
                    with self.assertRaises(error):
                        handler(self.cmd, entrypoint, **options)
        self.run_command.assert_not_called()
        self.install_default.assert_not_called()
        self.urlopen.assert_not_called()


class TestBicepSnapshot(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = DummyCli(random_config_dir=True)
        self.cmd = mock.Mock()
        self.cmd.cli_ctx = self.cli_ctx
        patcher = mock.patch(
            "azure.cli.command_modules.resource.custom.resolve_bicep_installation", return_value=None
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.bicep_version_greater_than_or_equal_to")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_snapshot_bicep_file_passes_minimum_args(
        self, ensure_bicep_installation_mock, bicep_version_check_mock, run_bicep_command_mock
    ):
        bicep_version_check_mock.return_value = True
        run_bicep_command_mock.return_value = ""

        snapshot_bicep_file(self.cmd, "main.bicepparam")

        ensure_bicep_installation_mock.assert_called_once_with(self.cli_ctx, stdout=False)
        bicep_version_check_mock.assert_called_once_with(self.cli_ctx, "0.41.2", installation=None)
        run_bicep_command_mock.assert_called_once_with(
            self.cli_ctx, ["snapshot", "main.bicepparam"], installation=None
        )

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.bicep_version_greater_than_or_equal_to")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_snapshot_bicep_file_passes_all_optional_args(
        self, ensure_bicep_installation_mock, bicep_version_check_mock, run_bicep_command_mock
    ):
        bicep_version_check_mock.return_value = True
        run_bicep_command_mock.return_value = ""

        snapshot_bicep_file(
            self.cmd,
            "main.bicepparam",
            mode="Validate",
            tenant_id="tenant-id",
            subscription_id="sub-id",
            management_group_id="mg-id",
            location="westus",
            resource_group="myRg",
            deployment_name="myDeployment",
        )

        run_bicep_command_mock.assert_called_once_with(
            self.cli_ctx,
            [
                "snapshot",
                "main.bicepparam",
                "--mode", "Validate",
                "--tenant-id", "tenant-id",
                "--subscription-id", "sub-id",
                "--management-group-id", "mg-id",
                "--location", "westus",
                "--resource-group", "myRg",
                "--deployment-name", "myDeployment",
            ],
            installation=None,
        )

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.bicep_version_greater_than_or_equal_to")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_snapshot_bicep_file_errors_when_bicep_too_old(
        self, ensure_bicep_installation_mock, bicep_version_check_mock, run_bicep_command_mock
    ):
        from azure.cli.core.azclierror import ValidationError

        bicep_version_check_mock.return_value = False

        with self.assertRaisesRegex(ValidationError, "az bicep snapshot.*0\\.41\\.2"):
            snapshot_bicep_file(self.cmd, "main.bicepparam")

        run_bicep_command_mock.assert_not_called()


class TestBicepRun(unittest.TestCase):
    def setUp(self):
        self.cli_ctx = DummyCli(random_config_dir=True)
        self.cmd = mock.Mock()
        self.cmd.cli_ctx = self.cli_ctx

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_run_bicep_cli_passthrough_forwards_split_args(self, ensure_bicep_installation_mock, run_bicep_command_mock):
        run_bicep_command_mock.return_value = ""

        run_bicep_cli_passthrough(self.cmd, "build main.bicep --stdout")

        ensure_bicep_installation_mock.assert_called_once_with(self.cli_ctx, stdout=False)
        run_bicep_command_mock.assert_called_once_with(
            self.cli_ctx, ["build", "main.bicep", "--stdout"]
        )

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_run_bicep_cli_passthrough_preserves_quoted_args(self, ensure_bicep_installation_mock, run_bicep_command_mock):
        run_bicep_command_mock.return_value = ""

        run_bicep_cli_passthrough(self.cmd, 'build "path with spaces/main.bicep"')

        run_bicep_command_mock.assert_called_once_with(
            self.cli_ctx, ["build", "path with spaces/main.bicep"]
        )

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_run_bicep_cli_passthrough_preserves_windows_path_backslashes(self, ensure_bicep_installation_mock, run_bicep_command_mock):
        run_bicep_command_mock.return_value = ""

        # Windows paths use backslashes which collide with POSIX shell escape semantics.
        # The passthrough must preserve them so the Bicep CLI receives a valid path.
        run_bicep_cli_passthrough(self.cmd, r"build D:\azure-cli\samples\main.bicep --stdout")

        run_bicep_command_mock.assert_called_once_with(
            self.cli_ctx, ["build", r"D:\azure-cli\samples\main.bicep", "--stdout"]
        )

    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command")
    @mock.patch("azure.cli.command_modules.resource.custom.ensure_bicep_installation")
    def test_run_bicep_cli_passthrough_raises_when_command_empty(self, ensure_bicep_installation_mock, run_bicep_command_mock):
        with self.assertRaisesRegex(InvalidArgumentValueError, "--command must not be empty."):
            run_bicep_cli_passthrough(self.cmd, "   ")

        run_bicep_command_mock.assert_not_called()

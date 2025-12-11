# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import contextlib
import unittest
import semver
from unittest import mock

from knack.util import CLIError
from azure.cli.command_modules.resource._bicep import (
    bicep_version_greater_than_or_equal_to,
    ensure_bicep_installation,
    remove_bicep_installation,
    run_bicep_command,
    validate_bicep_target_scope,
    _get_bicep_download_url,
    _bicep_version_check_file_path,
)
from azure.cli.core.azclierror import InvalidTemplateError
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
                except:
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
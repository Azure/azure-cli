# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import contextlib
import unittest
from unittest import mock

from knack.util import CLIError
from azure.cli.command_modules.resource._bicep import (
    ensure_bicep_installation,
    run_bicep_command,
    validate_bicep_target_scope,
    _bicep_version_check_file_path,
)
from azure.cli.core.azclierror import InvalidTemplateError


class TestBicep(unittest.TestCase):
    @mock.patch("os.path.isfile")
    def test_run_bicep_command_raise_error_if_not_installed_and_not_auto_install(self, isfile_stub):
        isfile_stub.return_value = False

        with self.assertRaisesRegex(CLIError, 'Bicep CLI not found. Install it now by running "az bicep install".'):
            run_bicep_command(["--version"], auto_install=False)

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
    ):
        isfile_stub.return_value = True
        _get_bicep_installed_version_stub.return_value = "1.0.0"
        get_bicep_latest_release_tag_stub.return_value = "v2.0.0"

        run_bicep_command(["--version"], check_version=True)

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
            _get_bicep_installed_version_stub.return_value = "1.0.0"
            get_bicep_latest_release_tag_stub.return_value = "v2.0.0"

            run_bicep_command(["--version"], check_version=True)

            self.assertTrue(os.path.isfile(_bicep_version_check_file_path))
        finally:
            self._remove_bicep_version_check_file()

    @mock.patch("os.path.isfile")
    @mock.patch("azure.cli.command_modules.resource._bicep._get_bicep_installed_version")
    @mock.patch("os.path.dirname")
    def test_ensure_bicep_installation_skip_download_if_installed_version_matches_release_tag(
        self, dirname_mock, _get_bicep_installed_version_stub, isfile_stub
    ):
        _get_bicep_installed_version_stub.return_value = "0.1.0"
        isfile_stub.return_value = True

        ensure_bicep_installation(release_tag="v0.1.0")

        dirname_mock.assert_not_called()

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

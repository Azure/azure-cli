# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from mock import MagicMock, patch
from knack.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.appservice.azure_devops_build_interactive import (
    AzureDevopsBuildInteractive
)


def interactive_patch_path(interactive_module):
    return "azure.cli.command_modules.appservice.azure_devops_build_interactive.{}".format(interactive_module)


class TestDevopsBuildCommandsMocked(unittest.TestCase):
    @patch("azure.cli.command_modules.appservice.azure_devops_build_interactive.AzureDevopsBuildProvider", new=MagicMock())
    def setUp(self):
        mock_logger = MagicMock()
        mock_cmd = MagicMock()
        mock_cmd.cli_ctx = DummyCli()
        self._client = AzureDevopsBuildInteractive(
            cmd=mock_cmd,
            logger=mock_logger,
            functionapp_name=None,
            organization_name=None,
            project_name=None,
            repository_name=None,
            overwrite_yaml=None,
            allow_force_push=None,
            github_pat=None,
            github_repository=None
        )

    @patch(interactive_patch_path("prompt_choice_list"))
    def test_check_scenario_prompt_choice_list(self, prompt_choice_list):
        self._client.check_scenario()
        prompt_choice_list.assert_called_once()

    def test_check_scenario_azure_devops(self):
        self._client.repository_name = "azure_devops_repository"
        self._client.check_scenario()
        result = self._client.scenario
        self.assertEqual(result, "AZURE_DEVOPS")

    def test_check_scenario_github_pat(self):
        self._client.github_pat = "github_pat"
        self._client.check_scenario()
        result = self._client.scenario
        self.assertEqual(result, "GITHUB_INTEGRATION")

    def test_check_scenario_github_repository(self):
        self._client.github_repository = "github_repository"
        self._client.check_scenario()
        result = self._client.scenario
        self.assertEqual(result, "GITHUB_INTEGRATION")

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_git"))
    def test_azure_devops_prechecks_no_git(self, check_git):
        check_git.return_value = False
        with self.assertRaises(CLIError):
            self._client.pre_checks_azure_devops()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_git"))
    @patch(interactive_patch_path("os.path.exists"))
    def test_azure_devops_prechecks_no_file(self, exists, check_git):
        check_git.return_value = True
        exists.return_value = False
        with self.assertRaises(CLIError):
            self._client.pre_checks_azure_devops()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_git"))
    @patch(interactive_patch_path("os.path.exists"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._find_local_repository_runtime_language"))
    def test_azure_devops_prechecks_no_file(self, _find_local_repository_runtime_language, exists, check_git):
        check_git.return_value = True
        exists.return_value = True
        _find_local_repository_runtime_language.return_value = "node"
        self._client.functionapp_language = "dotnet"
        with self.assertRaises(CLIError):
            self._client.pre_checks_azure_devops()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_git"))
    @patch(interactive_patch_path("os.path.exists"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._find_local_repository_runtime_language"))
    def test_azure_devops_prechecks(self, _find_local_repository_runtime_language, exists, check_git):
        check_git.return_value = True
        exists.return_value = True
        _find_local_repository_runtime_language.return_value = "node"
        self._client.functionapp_language = "node"
        self._client.pre_checks_azure_devops()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    def test_github_prechecks_no_file(self, check_github_file):
        check_github_file.return_value = False
        with self.assertRaises(CLIError):
            self._client.pre_checks_github()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._find_github_repository_runtime_language"))
    def test_github_prechecks_wrong_runtime(self, _find_github_repository_runtime_language, check_github_file):
        check_github_file.return_value = True
        _find_github_repository_runtime_language.return_value = "node"
        self._client.functionapp_language = "dotnet"
        with self.assertRaises(CLIError):
            self._client.pre_checks_github()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._find_github_repository_runtime_language"))
    def test_github_prechecks_no_runtime(self, _find_github_repository_runtime_language, check_github_file):
        check_github_file.return_value = True
        _find_github_repository_runtime_language.return_value = None
        self._client.functionapp_language = "dotnet"
        self._client.pre_checks_github()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._find_github_repository_runtime_language"))
    def test_github_prechecks(self, _find_github_repository_runtime_language, check_github_file):
        check_github_file.return_value = True
        _find_github_repository_runtime_language.return_value = "dotnet"
        self._client.functionapp_language = "dotnet"
        self._client.pre_checks_github()

    @patch(interactive_patch_path("get_app_settings"), MagicMock())
    @patch(interactive_patch_path("show_webapp"), MagicMock())
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._find_type"), MagicMock())
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._get_functionapp_runtime_language"), MagicMock())
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._get_functionapp_storage_name"), MagicMock())
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._select_functionapp"))
    def test_process_functionapp_prompt_choice_list(self, _select_functionapp):
        self._client.process_functionapp()
        _select_functionapp.assert_called_once()

    @patch(interactive_patch_path("AzureDevopsBuildInteractive._create_organization"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._select_organization"))
    @patch(interactive_patch_path("prompt_y_n"))
    def test_process_organization_prompt_choice_list(self, prompt_y_n, _select_organization, _create_organization):
        # Choose to select existing organization
        prompt_y_n.return_value = True
        self._client.process_organization()
        _select_organization.assert_called_once()

        # Choose to create a new organization
        prompt_y_n.return_value = False
        self._client.process_organization()
        _create_organization.assert_called_once()

    @patch(interactive_patch_path("AzureDevopsBuildInteractive._create_project"))
    @patch(interactive_patch_path("AzureDevopsBuildInteractive._select_project"))
    @patch(interactive_patch_path("prompt_y_n"))
    def test_process_project(self, prompt_y_n, _select_project, _create_project):
        # Choose to select existing project
        prompt_y_n.return_value = True
        self._client.process_project()
        _select_project.assert_called_once()

        # Choose to create a new project
        prompt_y_n.return_value = False
        self._client.process_project()
        _create_project.assert_called_once()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.create_github_yaml"))
    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("prompt_y_n"))
    def test_process_yaml_github_no_yaml(self, prompt_y_n, check_github_file, create_github_yaml):
        check_github_file.return_value = False
        self._client.process_yaml_github()
        prompt_y_n.assert_not_called()
        create_github_yaml.assert_called_once()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.create_github_yaml"))
    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("prompt_y_n"))
    def test_process_yaml_github_existing_no_consent(self, prompt_y_n, check_github_file, create_github_yaml):
        check_github_file.return_value = True
        prompt_y_n.return_value = False
        self._client.process_yaml_github()
        prompt_y_n.assert_called_once()
        create_github_yaml.assert_not_called()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.create_github_yaml"))
    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("prompt_y_n"))
    def test_process_yaml_github_existing_consent(self, prompt_y_n, check_github_file, create_github_yaml):
        check_github_file.return_value = True
        prompt_y_n.return_value = True
        self._client.process_yaml_github()
        prompt_y_n.assert_called_once()
        create_github_yaml.assert_called_once()

    @patch(interactive_patch_path("AzureDevopsBuildProvider.create_github_yaml"))
    @patch(interactive_patch_path("AzureDevopsBuildProvider.check_github_file"))
    @patch(interactive_patch_path("prompt_y_n"))
    def test_process_yaml_github_existing_overwrite(self, prompt_y_n, check_github_file, create_github_yaml):
        self._client.overwrite_yaml = True
        check_github_file.return_value = True
        self._client.process_yaml_github()
        prompt_y_n.assert_not_called()
        create_github_yaml.assert_called_once()


if __name__ == '__main__':
    unittest.main()

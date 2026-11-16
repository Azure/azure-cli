# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch

try:
    import azure.mgmt.cdn  # pylint: disable=unused-import
except ImportError:
    import sys
    import types
    cdn = types.ModuleType('azure.mgmt.cdn')
    cdn_models = types.ModuleType('azure.mgmt.cdn.models')
    cdn_models.CheckNameAvailabilityInput = type('CheckNameAvailabilityInput', (), {})
    cdn.models = cdn_models
    sys.modules['azure.mgmt.cdn'] = cdn
    sys.modules['azure.mgmt.cdn.models'] = cdn_models

from azure.cli.command_modules.synapse.manual._validators import validate_repository_type
from azure.cli.command_modules.synapse.manual.operations.workspace import create_workspace


class _Namespace:
    def __init__(self, **kwargs):
        self.repository_type = kwargs.get('repository_type', None)
        self.host_name = kwargs.get('host_name', None)
        self.account_name = kwargs.get('account_name', None)
        self.collaboration_branch = kwargs.get('collaboration_branch', None)
        self.repository_name = kwargs.get('repository_name', None)
        self.root_folder = kwargs.get('root_folder', None)
        self.project_name = kwargs.get('project_name', None)
        self.tenant_id = kwargs.get('tenant_id', None)
        self.last_commit_id = kwargs.get('last_commit_id', None)


class SynapseValidatorsTest(unittest.TestCase):
    @patch('azure.cli.command_modules.synapse.manual._validators.get_logger')
    def test_validate_repository_type_no_warning_when_no_repo_args(self, mock_get_logger):
        mock_logger = mock_get_logger.return_value
        ns = _Namespace(repository_type=None)
        validate_repository_type(ns)
        mock_logger.warning.assert_not_called()

    @patch('azure.cli.command_modules.synapse.manual._validators.get_logger')
    def test_validate_repository_type_warning_when_repo_args_without_type(self, mock_get_logger):
        mock_logger = mock_get_logger.return_value
        ns = _Namespace(repository_type=None, account_name='my-account', repository_name='my-repo')
        validate_repository_type(ns)
        mock_logger.warning.assert_called_once()
        warning_args = mock_logger.warning.call_args[0]
        formatted_args_str = warning_args[1]
        self.assertIn('--root-folder, --project-name', formatted_args_str)
        self.assertIn('--last-commit-id', formatted_args_str)
        self.assertNotIn('--root-folder--project-name', formatted_args_str)
        self.assertNotIn(' ,', formatted_args_str)

    @patch('azure.cli.command_modules.synapse.manual._validators.get_logger')
    def test_validate_repository_type_warning_when_last_commit_id_without_type(self, mock_get_logger):
        mock_logger = mock_get_logger.return_value
        ns = _Namespace(repository_type=None, last_commit_id='0123456789abcdef')
        validate_repository_type(ns)
        mock_logger.warning.assert_called_once()
        warning_args = mock_logger.warning.call_args[0]
        formatted_args_str = warning_args[1]
        self.assertIn('--last-commit-id', formatted_args_str)

    @patch('azure.cli.command_modules.synapse.manual._validators.get_logger')
    def test_validate_repository_type_no_warning_when_type_provided(self, mock_get_logger):
        mock_logger = mock_get_logger.return_value
        ns = _Namespace(repository_type='GitHub', account_name='my-account', repository_name='my-repo')
        validate_repository_type(ns)
        mock_logger.warning.assert_not_called()

    def test_create_workspace_root_folder_defaults(self):
        cmd = MagicMock()
        cmd.cli_ctx.cloud.suffixes.storage_endpoint = 'core.windows.net'
        client = MagicMock()

        # Without repository configuration, repository config should remain None
        with patch('azure.cli.command_modules.synapse.manual.operations.workspace.sdk_no_wait') as mock_sdk:
            create_workspace(cmd, client, 'rg', 'ws', 'storage', 'fs', 'user', 'pwd')
            workspace_info = mock_sdk.call_args[0][4]
            self.assertIsNone(workspace_info.workspace_repository_configuration)

        # With repository configuration and default root_folder (None passed), root_folder defaults to '/'
        with patch('azure.cli.command_modules.synapse.manual.operations.workspace.sdk_no_wait') as mock_sdk:
            create_workspace(cmd, client, 'rg', 'ws', 'storage', 'fs', 'user', 'pwd',
                             repository_type='GitHub', account_name='acc', repository_name='repo')
            workspace_info = mock_sdk.call_args[0][4]
            self.assertIsNotNone(workspace_info.workspace_repository_configuration)
            self.assertEqual(workspace_info.workspace_repository_configuration.root_folder, '/')

        # With explicit root_folder, it is preserved
        with patch('azure.cli.command_modules.synapse.manual.operations.workspace.sdk_no_wait') as mock_sdk:
            create_workspace(cmd, client, 'rg', 'ws', 'storage', 'fs', 'user', 'pwd',
                             repository_type='GitHub', account_name='acc', repository_name='repo',
                             root_folder='/custom')
            workspace_info = mock_sdk.call_args[0][4]
            self.assertEqual(workspace_info.workspace_repository_configuration.root_folder, '/custom')


if __name__ == '__main__':
    unittest.main()

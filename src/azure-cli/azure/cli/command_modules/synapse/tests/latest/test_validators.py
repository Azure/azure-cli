# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import patch

from azure.cli.command_modules.synapse.manual._validators import validate_repository_type


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
        self.assertNotIn('--root-folder--project-name', formatted_args_str)
        self.assertNotIn(' ,', formatted_args_str)

    @patch('azure.cli.command_modules.synapse.manual._validators.get_logger')
    def test_validate_repository_type_no_warning_when_type_provided(self, mock_get_logger):
        mock_logger = mock_get_logger.return_value
        ns = _Namespace(repository_type='GitHub', account_name='my-account', repository_name='my-repo')
        validate_repository_type(ns)
        mock_logger.warning.assert_not_called()


if __name__ == '__main__':
    unittest.main()

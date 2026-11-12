# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.command_modules.profile.custom import login
from azure.cli.core.mock import DummyCli
from azure.cli.core.azclierror import MutuallyExclusiveArgumentError, RequiredArgumentMissingError


class TestNoPromptLogin(unittest.TestCase):

    def setUp(self):
        self.cmd = mock.MagicMock()
        self.cmd.cli_ctx = DummyCli()

    def test_profile_login_device_code_is_incompatible(self):
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 'cannot be used'):
            login(self.cmd, no_prompt=True, use_device_code=True)

    @mock.patch('azure.cli.command_modules.profile.custom.prompt_pass')
    def test_profile_login_username_cannot_prompt_for_password(self, password_prompt):
        with self.assertRaisesRegex(RequiredArgumentMissingError, 'explicit password'):
            login(self.cmd, username='user@example.com', no_prompt=True)
        password_prompt.assert_not_called()

    @mock.patch('azure.cli.command_modules.profile.custom.Profile')
    @mock.patch('azure.cli.command_modules.profile.custom.sys')
    def test_profile_login_bypasses_subscription_selector_even_on_tty(self, sys_mock, profile_mock):
        self.cmd.cli_ctx.config = mock.MagicMock()
        self.cmd.cli_ctx.config.getboolean.return_value = True
        sys_mock.stdin.isatty.return_value = True
        sys_mock.stdout.isatty.return_value = True
        profile_mock.return_value.login.return_value = [
            {'id': 'sub', 'name': 'Sub', 'environmentName': 'AzureCloud'}]

        result = login(self.cmd, no_prompt=True)

        self.assertEqual(1, len(result))
        profile_mock.return_value.login.assert_called_once()
        self.assertTrue(profile_mock.return_value.login.call_args.kwargs['no_prompt'])
        profile_mock.return_value.set_active_subscription.assert_not_called()

    @mock.patch('azure.cli.command_modules.profile.custom.prompt_pass')
    @mock.patch('azure.cli.command_modules.profile.custom.Profile')
    def test_profile_login_explicit_password_requires_no_prompt(self, profile_mock, password_prompt):
        self.cmd.cli_ctx.config = mock.MagicMock()
        self.cmd.cli_ctx.config.getboolean.return_value = False
        profile_mock.return_value.login.return_value = []

        login(self.cmd, username='user@example.com', password='password', no_prompt=True)

        password_prompt.assert_not_called()
        args, kwargs = profile_mock.return_value.login.call_args
        self.assertFalse(args[0])  # Password authentication is not an interactive flow.
        self.assertTrue(kwargs['no_prompt'])

    @mock.patch('azure.cli.command_modules.profile.custom.Profile')
    def test_profile_login_default_remains_interactive(self, profile_mock):
        self.cmd.cli_ctx.config = mock.MagicMock()
        self.cmd.cli_ctx.config.getboolean.return_value = False
        profile_mock.return_value.login.return_value = []

        login(self.cmd)

        self.assertFalse(profile_mock.return_value.login.call_args.kwargs['no_prompt'])

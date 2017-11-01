# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.command_modules.profile.custom import list_subscriptions, get_access_token
from azure.cli.testsdk import TestCli


class ProfileCommandTest(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.profile.custom._load_subscriptions', autospec=True)
    @mock.patch('azure.cli.command_modules.profile.custom.logger', autospec=True)
    def test_list_only_enabled_one(self, logger_mock, load_subscription_mock):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()
        sub1 = {'state': 'Enabled'}
        sub2 = {'state': 'Overdued'}
        load_subscription_mock.return_value = [sub1, sub2]

        # list all
        self.assertEqual(2, len(list_subscriptions(cmd, all=True)))
        self.assertTrue(not logger_mock.warning.called)
        # list only enabled one
        result = list_subscriptions(cmd)
        self.assertEqual(1, len(result))
        self.assertEqual('Enabled', result[0]['state'])
        logger_mock.warning.assert_called_once_with(mock.ANY)

    @mock.patch('azure.cli.core._profile.Profile.get_raw_token', autospec=True)
    def test_get_row_token(self, get_raw_token_mcok):
        cmd = mock.MagicMock()
        cmd.cli_ctx = TestCli()

        # arrange
        get_raw_token_mcok.return_value = (['bearer', 'token123', {'expiresOn': '2100-01-01'}], 'sub123', 'tenant123')

        # action
        result = get_access_token(cmd)

        # assert
        get_raw_token_mcok.assert_called_with(mock.ANY, 'https://management.core.windows.net/', None)
        expected_result = {
            'tokenType': 'bearer',
            'accessToken': 'token123',
            'expiresOn': '2100-01-01',
            'subscription': 'sub123',
            'tenant': 'tenant123'
        }
        self.assertEqual(result, expected_result)

        # assert it takes customized resource, subscription
        get_access_token(cmd, subscription='foosub', resource='foores')
        get_raw_token_mcok.assert_called_with(mock.ANY, 'foores', 'foosub')

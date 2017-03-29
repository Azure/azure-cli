# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.command_modules.profile.custom import list_subscriptions


class ProfileCommandTest(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.profile.custom.load_subscriptions', autospec=True)
    def test_list_only_enabled_one(self, load_subscription_mock):
        sub1 = {'state': 'Enabled'}
        sub2 = {'state': 'Overdued'}
        load_subscription_mock.return_value = [sub1, sub2]

        # list all
        self.assertEqual(2, len(list_subscriptions(all=True)))

        # list only enabled one
        result = list_subscriptions()
        self.assertEqual(1, len(result))
        self.assertEqual('Enabled', result[0]['state'])

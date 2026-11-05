# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock

from azure.cli.command_modules.sql.custom import outbound_firewall_rule_create


class SqlOutboundFirewallRuleTest(unittest.TestCase):
    # SQL SDK 5.0 removed the outbound-rule request body from begin_create_or_update.

    def test_create_does_not_send_parameters(self):
        client = Mock()

        result = outbound_firewall_rule_create(
            client, 'server', 'resource-group', 'example.com')

        self.assertIs(result, client.begin_create_or_update.return_value)
        client.begin_create_or_update.assert_called_once_with(
            server_name='server',
            resource_group_name='resource-group',
            outbound_rule_fqdn='example.com')

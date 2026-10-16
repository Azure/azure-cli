# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock

from azure.core.paging import ItemPaged
from azure.mgmt.sql import SqlManagementClient

from azure.cli.command_modules.sql.custom import restorable_databases_list


class SqlRestorableDatabasesTest(unittest.TestCase):

    def test_list_returns_sdk_pager(self):
        client = Mock()

        result = restorable_databases_list(client, 'resource-group', 'server')

        self.assertIs(result, client.list_by_server.return_value)
        client.list_by_server.assert_called_once_with(
            'resource-group', 'server', skiptoken=None, top=None)

    def test_list_forwards_paging_options(self):
        client = Mock()

        restorable_databases_list(client, 'resource-group', 'server', skiptoken='next-page', top=5)

        client.list_by_server.assert_called_once_with(
            'resource-group', 'server', skiptoken='next-page', top=5)

    def test_list_invokes_sdk_validation_with_bound_client(self):
        with SqlManagementClient(Mock(), '00000000-0000-0000-0000-000000000000') as client:
            result = restorable_databases_list(
                client.restorable_dropped_databases, 'resource-group', 'server')

            self.assertIsInstance(result, ItemPaged)

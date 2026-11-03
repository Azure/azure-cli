# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch

from azure.cli.command_modules.postgresql.commands import migration_commands
from azure.mgmt.postgresqlflexibleservers.models import Migration


class MigrationCommandsTest(unittest.TestCase):

    def test_postgresql_migration_cutover_submits_all_databases(self):
        cmd = MagicMock()
        client = MagicMock()
        client.get.return_value = Migration(
            location='eastus',
            migration_mode='Online',
            dbs_to_migrate=['db1', 'db2'],
        )

        with patch.object(migration_commands, 'validate_citus_cluster'):
            result = migration_commands.migration_update_func(
                cmd, client, 'test-rg', 'test-server', 'test-migration', cutover=True,
            )

        client.get.assert_called_once_with('test-rg', 'test-server', 'test-migration')
        client.update.assert_called_once()
        resource_group, server_name, migration_name, parameters = client.update.call_args.args
        self.assertEqual((resource_group, server_name, migration_name),
                         ('test-rg', 'test-server', 'test-migration'))
        self.assertEqual(parameters.as_dict(), {
            'properties': {
                'triggerCutover': 'True',
                'dbsToTriggerCutoverOn': ['db1', 'db2'],
            },
        })
        self.assertIs(result, client.update.return_value)

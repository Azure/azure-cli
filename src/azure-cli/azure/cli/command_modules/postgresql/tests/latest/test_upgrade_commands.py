# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from knack.util import CLIError

from azure.cli.command_modules.postgresql.commands import upgrade_commands
from azure.cli.core.azclierror import ValidationError


class UpgradeCommandsTest(unittest.TestCase):

    def setUp(self):
        self.cmd = MagicMock()
        self.client = MagicMock()
        self.server = SimpleNamespace(
            version='16',
            storage=SimpleNamespace(type='Premium_LRS'),
            replication_role='Primary',
            cluster=SimpleNamespace(cluster_size=2),
        )
        self.client.get.return_value = self.server
        self.replicas = self._patch(upgrade_commands, 'cf_postgres_flexible_replica')
        self.replicas.return_value.list_by_server.return_value = []
        self.capabilities = self._patch(upgrade_commands, 'get_postgres_server_capability_info')
        self.capabilities.return_value = {'supported_server_versions': {'16': ['17', '18']}}
        self.resolve_poller = self._patch(upgrade_commands, 'resolve_poller')
        self.confirmation = self._patch(upgrade_commands, 'user_confirmation')
        self.precheck = self._patch(upgrade_commands, 'cf_postgres_flexible_major_version_upgrade_precheck')
        self._patch(upgrade_commands, 'validate_resource_group')
        from azure.cli.command_modules.postgresql.utils import validators
        self.server_factory = self._patch(validators, 'cf_postgres_flexible_servers')
        self.server_factory.return_value = self.client

    def _patch(self, target, name):
        patcher = patch.object(target, name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _upgrade(self, version='17', **kwargs):
        return upgrade_commands.flexible_server_version_upgrade(
            self.cmd, self.client, 'test-rg', 'test-server', version, **kwargs
        )

    def test_postgres_upgrade_elastic_cluster_and_regular_server(self):
        for cluster in (SimpleNamespace(cluster_size=2), SimpleNamespace(cluster_size=0), None):
            with self.subTest(cluster=cluster):
                self.server.cluster = cluster
                self.client.begin_update.reset_mock()
                result = self._upgrade(yes=True, validate=False)

                self.client.begin_update.assert_called_once_with(
                    resource_group_name='test-rg',
                    server_name='test-server',
                    parameters={'properties': {'version': '17'}},
                )
                self.assertIs(result, self.resolve_poller.return_value)
        self.confirmation.assert_not_called()
        self.server_factory.assert_not_called()

    def test_postgres_upgrade_elastic_cluster_rejects_validate_only(self):
        with self.assertRaises(ValidationError) as error:
            self._upgrade(validate=True)

        self.assertEqual(str(error.exception), 'Elastic cluster does not currently support this operation.')
        self.client.begin_start_major_version_upgrade_precheck.assert_not_called()
        self.precheck.assert_not_called()
        self.client.begin_update.assert_not_called()
        self.confirmation.assert_not_called()

    def test_postgres_upgrade_regular_server_validate_only(self):
        self.resolve_poller.return_value = {'name': 'precheck-id'}

        for cluster in (SimpleNamespace(cluster_size=0), None):
            with self.subTest(cluster=cluster):
                self.server.cluster = cluster
                self.client.begin_start_major_version_upgrade_precheck.reset_mock()
                self.precheck.return_value.get.reset_mock()

                result = self._upgrade(validate=True)

                self.client.begin_start_major_version_upgrade_precheck.assert_called_once_with(
                    resource_group_name='test-rg',
                    server_name='test-server',
                    body={'targetVersion': '17'},
                )
                self.precheck.return_value.get.assert_called_once_with(
                    resource_group_name='test-rg',
                    server_name='test-server',
                    precheck_validation_id='precheck-id',
                )
                self.assertIs(result, self.precheck.return_value.get.return_value)
        self.client.begin_update.assert_not_called()
        self.confirmation.assert_not_called()

    def test_postgres_upgrade_elastic_cluster_requires_confirmation(self):
        self._upgrade()

        self.confirmation.assert_called_once()
        self.client.begin_update.assert_called_once()

    def test_postgres_upgrade_elastic_cluster_rejects_same_or_lower_version(self):
        for version in ('15', '16'):
            with self.subTest(version=version):
                with self.assertRaisesRegex(CLIError, 'must be greater than the current version'):
                    self._upgrade(version=version, yes=True)
        self.client.begin_update.assert_not_called()

    def test_postgres_upgrade_elastic_cluster_preserves_storage_restriction(self):
        self.server.version = '12'
        self.server.storage.type = 'PremiumV2_LRS'

        with self.assertRaisesRegex(CLIError, 'only supported for PostgreSQL version 14 and above'):
            self._upgrade(version='13', yes=True)

        self.client.begin_update.assert_not_called()

    def test_postgres_upgrade_elastic_cluster_preserves_supported_version_check(self):
        with self.assertRaisesRegex(CLIError, 'Invalid value for --version'):
            self._upgrade(version='19', yes=True)

        self.client.begin_update.assert_not_called()

    def test_postgres_upgrade_elastic_cluster_preserves_replica_restriction(self):
        for role, replicas in (('Replica', []), ('Primary', [MagicMock()])):
            with self.subTest(role=role):
                self.server.replication_role = role
                self.replicas.return_value.list_by_server.return_value = replicas
                with self.assertRaisesRegex(CLIError, 'not yet supported for servers in a read replica setup'):
                    self._upgrade(yes=True)
        self.client.begin_update.assert_not_called()


if __name__ == '__main__':
    unittest.main()

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace

from azure.cli.command_modules.sql.custom import server_update, ServerNetworkAccessFlag


class SqlServerUpdateUnitTest(unittest.TestCase):

    @staticmethod
    def _build_server_instance(retention_days):
        return SimpleNamespace(
            identity=None,
            administrator_login_password=None,
            minimal_tls_version='1.2',
            public_network_access=ServerNetworkAccessFlag.DISABLED,
            primary_user_assigned_identity_id='existing-primary-id',
            key_id='existing-cmk-id',
            federated_client_id='existing-federated-client-id',
            retention_days=retention_days)

    def test_server_update_normalizes_legacy_negative_retention_days(self):
        server = self._build_server_instance(retention_days=-1)

        updated = server_update(server, enable_public_network=True)

        self.assertEqual(updated.public_network_access, ServerNetworkAccessFlag.ENABLED)
        self.assertEqual(updated.retention_days, 0)

    def test_server_update_keeps_retention_days_when_not_provided(self):
        server = self._build_server_instance(retention_days=5)

        updated = server_update(server, enable_public_network=True)

        self.assertEqual(updated.public_network_access, ServerNetworkAccessFlag.ENABLED)
        self.assertEqual(updated.retention_days, 5)

    def test_server_update_honors_explicit_soft_delete_retention_days(self):
        server = self._build_server_instance(retention_days=-1)

        updated = server_update(server, enable_public_network=True, soft_delete_retention_days=3)

        self.assertEqual(updated.retention_days, 3)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from types import SimpleNamespace
from unittest import mock

from azure.cli.core.mock import DummyCli
from azure.mgmt.sql.models import ManagedInstance, Sku

from azure.cli.command_modules.sql.custom import managed_instance_update


class SqlManagedInstanceUpdateTest(unittest.TestCase):

    def test_update_command_does_not_register_logical_availability_zone_argument(self):
        cli = DummyCli()

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            try:
                cli.invoke(['sql', 'mi', 'update', '-h'])
            except SystemExit:
                pass

        cmd = cli.invocation.commands_loader.command_table['sql mi update']
        self.assertNotIn('requested_logical_availability_zone', cmd.arguments)

    def test_update_clears_requested_logical_availability_zone(self):
        instance = ManagedInstance(
            location='eastus',
            sku=Sku(name='GP_Gen5', tier='GeneralPurpose', family='Gen5'),
            administrator_login='cliadmin')
        instance.requested_logical_availability_zone = 'NoPreference'

        cmd = SimpleNamespace(cli_ctx=DummyCli())

        with mock.patch('azure.cli.command_modules.sql.custom._find_managed_instance_sku_from_capabilities',
                        side_effect=lambda *_args: instance.sku), \
                mock.patch('azure.cli.command_modules.sql.custom._get_identity_object_from_type',
                           side_effect=lambda *_args: None), \
                mock.patch('azure.cli.command_modules.sql.custom._get_service_principal_object_from_type',
                           side_effect=lambda *_args: None), \
                mock.patch('azure.cli.command_modules.sql.custom._complete_maintenance_configuration_id',
                           return_value=None):
            updated = managed_instance_update(
                cmd=cmd,
                instance=instance,
                resource_group_name='rg',
                administrator_login_password='new-password')

        self.assertEqual(updated.administrator_login_password, 'new-password')
        self.assertIsNone(updated.requested_logical_availability_zone)
        self.assertNotIn('requestedLogicalAvailabilityZone',
                         updated.serialize().get('properties', {}))


if __name__ == '__main__':
    unittest.main()

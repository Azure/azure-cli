# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import pathlib
import getopt
import uuid
import sys
from knack.log import get_logger

from datetime import datetime
from time import sleep
from dateutil.tz import tzutc  # pylint: disable=import-error
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.util import CLIError
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError  # pylint: disable=unused-import
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StringContainCheck,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)

logger = get_logger(__name__)


class MigrationScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    def test_postgres_flexible_server_migration(self):
        self._test_server_migration('postgres')

    def test_postgres_flexible_server_onpremise_migration(self):
        self._test_server_migration_onpremise('postgres', True, "f31b6595-74d4-4d3c-91bd-fb93af61d8f9")
        self._test_server_migration_onpremise('postgres', False, "c73c308e-1e4e-4cfd-bc1f-7db572422598")

    def _test_server_migration(self, database_engine):
        # Set this to True or False depending on whether we are in live mode or test mode
        # livemode = True
        livemode = False

        if livemode:
            # Live mode values
            target_subscription_id = "ac0271d6-426b-4b0d-b88d-0d0e4bd693ae"
            migration_name = str(uuid.uuid4())
        else:
            # Mock test mode values
            target_subscription_id = "00000000-0000-0000-0000-000000000000"
            migration_name = "d2419e1d-4e05-4149-95d9-1d1c094e5ac5"

        target_resource_group_name = "autobot-resourcegroup-pg-eastus2euap"
        target_server_name = "autobot-e2e-pg-fs-eastus2euap"
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        properties_filepath = os.path.join(curr_dir, 'migrationPublic.json').replace('\\', '\\\\')

        print(target_subscription_id)

        # test check migration name availability -success
        result = self.cmd('{} flexible-server migration check-name-availability --subscription {} --resource-group {} --name {} --migration-name {} '
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name),
                          checks=[JMESPathCheck('nameAvailable', True)]).get_output_in_json()

        # test create migration - success
        result = self.cmd('{} flexible-server migration create --subscription {} --resource-group {} --name {} --migration-name {} --properties {} '
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name, properties_filepath),
                          checks=[JMESPathCheck('migrationMode', "Offline")]).get_output_in_json()
        migration_name = result['name']

        # test list migrations - success, with filter
        result = self.cmd('{} flexible-server migration list --subscription {} --resource-group {} --name {} --filter Active'
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name)).get_output_in_json()

        # test list migrations - success, without filter
        result = self.cmd('{} flexible-server migration list --subscription {} --resource-group {} --name {}'
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name)).get_output_in_json()

        # test show migration - success
        result = self.cmd('{} flexible-server migration show --subscription {} --resource-group {} --name {} --migration-name {}'
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name)).get_output_in_json()

        self.assertEqual(result['name'], migration_name)
        self.assertEqual(result['migrationOption'], "ValidateAndMigrate")
        self.assertEqual(result['sourceType'], "PostgreSQLSingleServer")
        self.assertEqual(result['sslMode'], "VerifyFull")

        # test update migration - error - no param
        result = self.cmd('{} flexible-server migration update --subscription {} --resource-group {} --name {} --migration-name {}'
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name), expect_failure=True)

    def _test_server_migration_onpremise(self, database_engine, validateOnly=False, migration_name=None):
        # Set this to True or False depending on whether we are in live mode or test mode
        # livemode = True
        livemode = False

        if livemode:
            # Live mode values
            target_subscription_id = "ac0271d6-426b-4b0d-b88d-0d0e4bd693ae"
            migration_name = str(uuid.uuid4())
        else:
            # Mock test mode values
            target_subscription_id = "00000000-0000-0000-0000-000000000000"

        migration_option = "ValidateAndMigrate"
        if validateOnly:
            migration_option = "Validate"

        target_resource_group_name = "autobot-resourcegroup-pg-eastus2euap"
        target_server_name = "autobot-e2e-pg-fs-eastus2euap"
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        properties_filepath = os.path.join(curr_dir, 'migrationOnPremise.json').replace('\\', '\\\\')

        print(target_subscription_id)

        # test check migration name availability -success
        self.cmd('{} flexible-server migration check-name-availability --subscription {} --resource-group {} --name {} --migration-name {} '
                 .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name),
                 checks=[JMESPathCheck('nameAvailable', True)]).get_output_in_json()

        # test create migration - success
        result = self.cmd('{} flexible-server migration create --subscription {} --resource-group {} --name {} --migration-name {} --properties {} --migration-option {}'
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name, properties_filepath, migration_option),
                          checks=[JMESPathCheck('migrationMode', "Offline"),
                                  JMESPathCheck('migrationOption', migration_option),
                                  JMESPathCheck('sourceType', "OnPremises"),
                                  JMESPathCheck('sslMode', "Prefer")]).get_output_in_json()
        migration_name = result['name']

        # test test show migration - success
        result = self.cmd('{} flexible-server migration show --subscription {} --resource-group {} --name {} --migration-name {}'
                          .format(database_engine, target_subscription_id, target_resource_group_name, target_server_name, migration_name)).get_output_in_json()

        self.assertEqual(result['name'], migration_name)
        self.assertEqual(result['migrationOption'], migration_option)
        self.assertEqual(result['sourceType'], "OnPremises")
        self.assertEqual(result['sslMode'], "Prefer")
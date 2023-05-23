# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

class CosmosDBBackupRestoreScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_provision_continuous7days', location='eastus2')
    def test_cosmosdb_sql_continuous7days(self, resource_group):
        col = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli-continuous7-', length=25),
            'db_name': db_name,
            'col': col,
            'loc': 'eastus2'
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days --locations regionName={loc} --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        assert account is not None
        assert account['backupPolicy'] is not None
        assert account['backupPolicy']['continuousModeProperties'] is not None

        continuous_tier = account['backupPolicy']['continuousModeProperties']['tier']
        assert continuous_tier == 'Continuous7Days'

        self.cmd('az cosmosdb update -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous30Days')
        updated_account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(updated_account)

        assert updated_account is not None
        assert updated_account['backupPolicy'] is not None
        assert updated_account['backupPolicy']['continuousModeProperties'] is not None

        updated_continuous_tier = updated_account['backupPolicy']['continuousModeProperties']['tier']
        assert updated_continuous_tier == 'Continuous30Days'

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_provision_continuous30days', location='eastus2')
    def test_cosmosdb_sql_continuous30days(self, resource_group):
        col = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli-continuous30-', length=25),
            'db_name': db_name,
            'col': col,
            'loc': 'eastus2'
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --locations regionName={loc} --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        assert account is not None
        assert account['backupPolicy'] is not None
        assert account['backupPolicy']['continuousModeProperties'] is not None

        continuous_tier = account['backupPolicy']['continuousModeProperties']['tier']

        # If continuous tier is not provided, then it's default to Continuous30Days
        assert continuous_tier == 'Continuous30Days'

        self.cmd('az cosmosdb update -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days')
        updated_account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(updated_account)

        assert updated_account is not None
        assert updated_account['backupPolicy'] is not None
        assert updated_account['backupPolicy']['continuousModeProperties'] is not None

        updated_continuous_tier = updated_account['backupPolicy']['continuousModeProperties']['tier']
        assert updated_continuous_tier == 'Continuous7Days'

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_migrate_periodic_to_continuous7days', location='eastus2')
    def test_cosmosdb_sql_migrate_periodic_to_continuous7days(self, resource_group):
        col = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli-periodic-', length=25),
            'db_name': db_name,
            'col': col,
            'loc': 'eastus2'
        })

        # Create periodic backup account (by default is --backup-policy-type is not specified, then it is a Periodic account)
        self.cmd('az cosmosdb create -n {acc} -g {rg} --locations regionName={loc} --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        assert account is not None
        assert account['backupPolicy'] is not None
        assert account['backupPolicy']['periodicModeProperties'] is not None

        # Migrate periodic account to Continuous 7 days
        self.cmd('az cosmosdb update -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days')
        updated_account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(updated_account)

        assert updated_account is not None
        assert updated_account['backupPolicy'] is not None
        assert updated_account['backupPolicy']['continuousModeProperties'] is not None

        updated_continuous_tier = updated_account['backupPolicy']['continuousModeProperties']['tier']
        assert updated_continuous_tier == 'Continuous7Days'

        # Update account to Continuous 30 days
        self.cmd('az cosmosdb update -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous30Days')
        updated_account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(updated_account)

        assert updated_account is not None
        assert updated_account['backupPolicy'] is not None
        assert updated_account['backupPolicy']['continuousModeProperties'] is not None

        updated_continuous_tier = updated_account['backupPolicy']['continuousModeProperties']['tier']
        assert updated_continuous_tier == 'Continuous30Days'

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_sql_oldestRestorableTime', location='eastus2')
    def test_cosmosdb_sql_oldestRestorableTime(self, resource_group):
        col = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli-continuous7-', length=25),
            'db_name': db_name,
            'col': col,
            'loc': 'eastus2'
        })

        # Create periodic backup account (by default is --backup-policy-type is not specified, then it is a Periodic account)
        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days --locations regionName={loc} --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days --locations regionName={loc} --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'ins_id': account['instanceId']
        })

        restorable_database_account_show = self.cmd('az cosmosdb restorable-database-account show --location {loc} --instance-id {ins_id}').get_output_in_json()
        account_oldest_restorable_time = restorable_database_account_show['oldestRestorableTime']
        assert account_oldest_restorable_time is not None

        restorable_accounts_list = self.cmd('az cosmosdb restorable-database-account list').get_output_in_json()
        restorable_database_account = next(acc for acc in restorable_accounts_list if acc['name'] == account['instanceId'])
        account_oldest_restorable_time = restorable_database_account['oldestRestorableTime']
        assert account_oldest_restorable_time is not None

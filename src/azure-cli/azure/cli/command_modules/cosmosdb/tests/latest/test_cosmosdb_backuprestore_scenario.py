# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from datetime import datetime, timedelta
from dateutil import parser

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

    '''
    This test will be rewritten to follow RBAC guidelines:
    https://learn.microsoft.com/en-us/azure/container-registry/container-registry-tutorial-sign-build-push
    Essentially, set-policy needs to be rewritten using RBAC instead.
    Disabling the test for now.
    '''
    @unittest.skip('Needs to be rewritten to follow updated guidelines')
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_system_identity_restore', location='eastus2')
    def test_cosmosdb_system_identity_restore(self, resource_group):
        # Source account parameters
        source_acc = self.create_random_name(prefix='cli-systemid-', length=25)
        target_acc = source_acc + "-restored"
        subscription = self.get_subscription_id()
        col = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': source_acc,
            'restored_acc': target_acc,
            'db_name': db_name,
            'col': col,
            'loc': 'eastus2',
            'subscriptionid': subscription
        })

        self.kwargs.update({
            'user1' : self.create_random_name(prefix='user1-', length = 10),
            'user2' : self.create_random_name(prefix='user2-', length = 10)
        })

        # Create new User Identity 1
        uid1 = self.cmd('az identity create -g {rg} -n {user1}').get_output_in_json()
        user_id_1 = uid1['id']
        user_principal_1 = uid1['principalId']
        default_id1 = 'UserAssignedIdentity=' + user_id_1

        # Create new User Identity 2
        uid2 = self.cmd('az identity create -g {rg} -n {user2}').get_output_in_json()
        user_id_2 = uid2['id']
        user_principal_2 = uid2['principalId']
        default_id2 = 'UserAssignedIdentity=' + user_id_2

        # Keyvault and identity parameters
        keyVaultName = self.create_random_name(prefix='clikeyvault-', length = 20)
        keyName = self.create_random_name(prefix='clikey-', length = 12)
        keyVaultKeyUri = "https://{}.vault.azure.net/keys/{}".format(keyVaultName, keyName)

        self.kwargs.update({
            'keyVaultName' : keyVaultName,
            'keyName' : keyName,
            'keyVaultKeyUri' : keyVaultKeyUri,
            'user_id_1' : user_id_1,
            'user_id_2' : user_id_2,
            'user_principal_1' : user_principal_1,
            'user_principal_2' : user_principal_2,
            'default_id1' : default_id1,
            'default_id2' : default_id2
        })

        # Create new keyvault
        self.cmd('az keyvault create --location {loc} --name {keyVaultName} --resource-group {rg}')

        # Enable purge protection for keyvault
        self.cmd('az keyvault update --subscription {subscriptionid} -g {rg} -n {keyVaultName} --enable-purge-protection true')

        # Create new key inside keyvault
        self.cmd('az keyvault key create --vault-name {keyVaultName} -n {keyName} --kty RSA --size 3072')

        # Grant key access to user1 and user2
        self.cmd('az keyvault set-policy --name {keyVaultName} --resource-group {rg} --object-id {user_principal_1} --key-permissions get unwrapKey wrapKey')
        self.cmd('az keyvault set-policy --name {keyVaultName} --resource-group {rg} --object-id {user_principal_2} --key-permissions get unwrapKey wrapKey')

        print('Finished setting up new KeyVault')

        # Create PITR account with User Identity 1
        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --locations regionName={loc} --kind GlobalDocumentDB --key-uri {keyVaultKeyUri} --assign-identity {user_id_1} --default-identity {default_id1}')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        print('Finished creating source account ' + account['id'])

        account_keyvault_uri = account['keyVaultKeyUri']
        assert keyVaultKeyUri in account_keyvault_uri

        account_defaultIdentity = account['defaultIdentity']
        assert user_id_1 in account_defaultIdentity

        self.kwargs.update({
            'ins_id': account['instanceId']
        })

        # Create database
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')

        # Create container
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {col} -p /pk ').get_output_in_json()

        print('Update the source account to use System Identity')

        # Assign system identity to source account
        sysid = self.cmd('az cosmosdb identity assign -n {acc} -g {rg}').get_output_in_json()

        self.kwargs.update({
            'system_id_principal': sysid['principalId']
        })

        # Grant KeyVault permission to the source account's system identity
        self.cmd('az keyvault set-policy --name {keyVaultName} --resource-group {rg} --object-id {system_id_principal} --key-permissions get unwrapKey wrapKey')

        # Set source account default identity to system identity
        account = self.cmd('az cosmosdb update -n {acc} -g {rg} --default-identity "SystemAssignedIdentity"').get_output_in_json()

        print('Done updating the source account to use System Identity')

        account_defaultIdentity = account['defaultIdentity']
        assert 'SystemAssignedIdentity' in account_defaultIdentity

        print('Done setting up source account with System Identity.  Starting to perform restore.')

        restorable_database_account = self.cmd('az cosmosdb restorable-database-account show --location {loc} --instance-id {ins_id}').get_output_in_json()

        account_creation_time = restorable_database_account['creationTime']
        creation_timestamp_datetime = parser.parse(account_creation_time)
        restore_ts = creation_timestamp_datetime + timedelta(minutes=4)
        import time
        time.sleep(240)
        restore_ts_string = restore_ts.isoformat()
        self.kwargs.update({
            'rts': restore_ts_string
        })

        self.kwargs.update({
            'rts': restore_ts_string,
            'loc': 'eastus2',
            'user_id_2' : user_id_2,
            'default_id2' : default_id2
        })

        self.cmd('az cosmosdb restore -n {restored_acc} -g {rg} -a {acc} --restore-timestamp {rts} --location {loc} --assign-identity {user_id_2} --default-identity {default_id2}')
        restored_account = self.cmd('az cosmosdb show -n {restored_acc} -g {rg}', checks=[
            self.check('restoreParameters.restoreMode', 'PointInTime')
        ]).get_output_in_json()

        print(restored_account)
        print('Finished restoring account ' + restored_account['id'])

        restored_account_keyvault_uri = restored_account['keyVaultKeyUri']
        assert keyVaultKeyUri in restored_account_keyvault_uri

        restored_account_defaultIdentity = restored_account['defaultIdentity']
        assert user_id_2 in restored_account_defaultIdentity
        
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_public_network_access_restore', location='eastus2')
    def test_cosmosdb_public_network_access_restore(self, resource_group):
        # Source account parameters
        source_acc = self.create_random_name(prefix='cli-systemid-', length=25)
        target_acc = source_acc + "-restored"
        subscription = self.get_subscription_id()
        col = self.create_random_name(prefix='cli', length=15)
        db_name = self.create_random_name(prefix='cli', length=15)

        self.kwargs.update({
            'acc': source_acc,
            'restored_acc': target_acc,
            'db_name': db_name,
            'col': col,
            'loc': 'eastus2',
            'subscriptionid': subscription
        })

        self.kwargs.update({
            'user1' : self.create_random_name(prefix='user1-', length = 10),
            'user2' : self.create_random_name(prefix='user2-', length = 10)
        })

        # Create PITR account
        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --locations regionName={loc} --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        print('Finished creating source account ' + account['id'])

        self.kwargs.update({
            'ins_id': account['instanceId']
        })

        # Create database
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')

        # Create container
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {col} -p /pk ').get_output_in_json()   

        print('Starting to perform restore with public network access as DISABLED.')

        restorable_database_account = self.cmd('az cosmosdb restorable-database-account show --location {loc} --instance-id {ins_id}').get_output_in_json()

        account_creation_time = restorable_database_account['creationTime']
        creation_timestamp_datetime = parser.parse(account_creation_time)
        restore_ts = creation_timestamp_datetime + timedelta(minutes=4)
        import time
        time.sleep(240)
        restore_ts_string = restore_ts.isoformat()
        self.kwargs.update({
            'rts': restore_ts_string
        })

        self.kwargs.update({
            'rts': restore_ts_string,
            'loc': 'eastus2',
            'pna': 'DISABLED'
        })

        self.cmd('az cosmosdb restore -n {restored_acc} -g {rg} -a {acc} --restore-timestamp {rts} --location {loc} --public-network-access {pna}')
        restored_account = self.cmd('az cosmosdb show -n {restored_acc} -g {rg}', checks=[
            self.check('restoreParameters.restoreMode', 'PointInTime')
        ]).get_output_in_json()

        print(restored_account)
        print('Finished restoring account ' + restored_account['id'])

        public_network_access = restored_account['publicNetworkAccess']
        assert public_network_access == 'Disabled'
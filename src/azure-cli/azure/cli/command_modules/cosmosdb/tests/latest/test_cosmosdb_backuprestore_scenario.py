# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import unittest
from unittest import mock

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
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
            'user1': self.create_random_name(prefix='user1-', length=10),
            'user2': self.create_random_name(prefix='user2-', length=10)
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
        keyVaultName = self.create_random_name(prefix='clikeyvault-', length=20)
        keyName = self.create_random_name(prefix='clikey-', length=12)
        keyVaultKeyUri = "https://{}.vault.azure.net/keys/{}".format(keyVaultName, keyName)

        self.kwargs.update({
            'keyVaultName': keyVaultName,
            'keyName': keyName,
            'keyVaultKeyUri': keyVaultKeyUri,
            'user_id_1': user_id_1,
            'user_id_2': user_id_2,
            'user_principal_1': user_principal_1,
            'user_principal_2': user_principal_2,
            'default_id1': default_id1,
            'default_id2': default_id2
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
            'user_id_2': user_id_2,
            'default_id2': default_id2
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
            'user1': self.create_random_name(prefix='user1-', length=10),
            'user2': self.create_random_name(prefix='user2-', length=10)
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_cross_region_restore', location='westcentralus')
    def test_cosmosdb_xrr(self, resource_group):
        col = self.create_random_name(prefix='cli-xrr', length=15)
        db_name = self.create_random_name(prefix='cli-xrr', length=15)
        source_acc = self.create_random_name(prefix='cli-xrr-', length=25)
        target_acc = source_acc + "-restored"
        loc = 'westcentralus'

        # This is a multi region account cross region test, for this test account will also exist in the target region
        target_loc = 'northcentralus'

        # For this new parameter source_backup_location we need to wired in the handler to understand `eastus` means `East US`.
        # Until that fix is added we have to send the location in this way for a clean run.
        source_loc_for_xrr = 'West Central US'

        self.kwargs.update({
            'acc': source_acc,
            'db_name': db_name,
            'restored_acc': target_acc,
            'col': col,
            'loc': loc,
            'target_loc': target_loc
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days --locations regionName={loc} failoverPriority=0 isZoneRedundant=False --locations regionName={target_loc} failoverPriority=1 isZoneRedundant=False --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        assert account['location'] == source_loc_for_xrr

        self.kwargs.update({
            'ins_id': account['instanceId']
        })

        # Create database
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')

        # Create container
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {col} -p /pk ').get_output_in_json()

        restorable_database_account = self.cmd('az cosmosdb restorable-database-account show --location {loc} --instance-id {ins_id}').get_output_in_json()
        print(restorable_database_account)

        # As of now cross region restore does not have forced master backup during restore.
        # So, we need to wait one hour in order to get the master backup for a restore to be performed.
        account_creation_time = restorable_database_account['creationTime']
        creation_timestamp_datetime = parser.parse(account_creation_time)
        restore_ts = creation_timestamp_datetime + timedelta(minutes=61)
        import time
        time.sleep(3662)
        restore_ts_string = restore_ts.isoformat()
        self.kwargs.update({
            'rts': restore_ts_string,
            'source_loc_for_xrr': source_loc_for_xrr
        })

        self.cmd('az cosmosdb restore -n {restored_acc} -g {rg} -a {acc} --restore-timestamp {rts} --source-backup-location "{source_loc_for_xrr}" --location {target_loc}')
        restored_account = self.cmd('az cosmosdb show -n {restored_acc} -g {rg}', checks=[
            self.check('restoreParameters.restoreMode', 'PointInTime')
        ]).get_output_in_json()

        assert restored_account['restoreParameters']['restoreSource'] == restorable_database_account['id']
        assert restored_account['restoreParameters']['restoreTimestampInUtc'] == restore_ts_string
        assert restored_account['writeLocations'][0]['locationName'] == 'North Central US'

    # Base account deleted, will be recreated and test enabled in the next release.
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_cross_region_restore', location='westcentralus')
    def test_cosmosdb_xrr_single_region_account(self, resource_group):
        col = self.create_random_name(prefix='cli-xrr', length=15)
        db_name = self.create_random_name(prefix='cli-xrr', length=15)
        source_acc = self.create_random_name(prefix='cli-xrr-', length=25)
        target_acc = source_acc + "-restored"
        loc = 'westcentralus'
        target_loc = 'northcentralus'

        # For this new parameter source_backup_location we need to wired in the handler to understand `eastus` means `East US`.
        # Until that fix is added we have to send the location in this way for a clean run.
        source_loc_for_xrr = 'West Central US'

        self.kwargs.update({
            'acc': source_acc,
            'db_name': db_name,
            'restored_acc': target_acc,
            'col': col,
            'loc': loc,
            'target_loc': target_loc
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --backup-policy-type Continuous --continuous-tier Continuous7Days --locations regionName={loc} failoverPriority=0 isZoneRedundant=False --kind GlobalDocumentDB')
        account = self.cmd('az cosmosdb show -n {acc} -g {rg}').get_output_in_json()
        print(account)

        assert account['location'] == source_loc_for_xrr

        self.kwargs.update({
            'ins_id': account['instanceId']
        })

        # Create database
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')

        # Create container
        self.cmd('az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} -n {col} -p /pk ').get_output_in_json()

        restorable_database_account = self.cmd('az cosmosdb restorable-database-account show --location {loc} --instance-id {ins_id}').get_output_in_json()
        print(restorable_database_account)

        # As of now cross region restore does not have forced master backup during restore.
        # So, we need to wait one hour in order to get the master backup for a restore to be performed.
        account_creation_time = restorable_database_account['creationTime']
        creation_timestamp_datetime = parser.parse(account_creation_time)
        restore_ts = creation_timestamp_datetime + timedelta(minutes=61)
        import time
        time.sleep(3662)
        restore_ts_string = restore_ts.isoformat()
        self.kwargs.update({
            'rts': restore_ts_string,
            'source_loc_for_xrr': source_loc_for_xrr
        })

        self.cmd('az cosmosdb restore -n {restored_acc} -g {rg} -a {acc} --restore-timestamp {rts} --source-backup-location "{source_loc_for_xrr}" --location {target_loc}')
        restored_account = self.cmd('az cosmosdb show -n {restored_acc} -g {rg}', checks=[
            self.check('restoreParameters.restoreMode', 'PointInTime')
        ]).get_output_in_json()

        assert restored_account['restoreParameters']['restoreSource'] == restorable_database_account['id']
        assert restored_account['restoreParameters']['restoreTimestampInUtc'] == restore_ts_string
        assert restored_account['restoreParameters']['sourceBackupLocation'] == source_loc_for_xrr
        assert restored_account['writeLocations'][0]['locationName'] == 'North Central US'


class CosmosDBRestoreUnitTests(unittest.TestCase):
    def setUp(self):
        # Mock dependencies that might be missing or problematic to import
        if 'azure.mgmt.cosmosdb.models' not in sys.modules:
            sys.modules['azure.mgmt.cosmosdb.models'] = mock.MagicMock()
        if 'azure.cli.core.util' not in sys.modules:
            sys.modules['azure.cli.core.util'] = mock.MagicMock()
        if 'knack.log' not in sys.modules:
            sys.modules['knack.log'] = mock.MagicMock()
        # Mocking knack.util.CLIError is crucial if it's used in custom.py
        if 'knack.util' not in sys.modules:
            mock_knack_util = mock.MagicMock()
            mock_knack_util.CLIError = Exception
            sys.modules['knack.util'] = mock_knack_util

        # Ensure Azure Core Exceptions are available
        try:
            import azure.core.exceptions
        except ImportError:
            mock_core_exceptions = mock.MagicMock()
            # Define minimal exception class
            class HttpResponseError(Exception):
                def __init__(self, message=None, response=None, **kwargs):
                    self.message = message
                    self.response = response
                    self.status_code = kwargs.get('status_code', None)
                def __str__(self):
                     return self.message or ""
            mock_core_exceptions.HttpResponseError = HttpResponseError
            mock_core_exceptions.ResourceNotFoundError = Exception
            sys.modules['azure.core.exceptions'] = mock_core_exceptions

    def test_restore_handles_forbidden_error(self):
        from azure.core.exceptions import HttpResponseError
        # Lazy import to ensure mocks are applied first
        from azure.cli.command_modules.cosmosdb.custom import _create_database_account

        # Setup mocks
        client = mock.MagicMock()

        # Simulate the LRO poller raising the specific error
        poller = mock.MagicMock()
        error_json = '{"code":"Forbidden","message":"Database Account riks-models-003-acc-westeurope does not exist"}'
        exception = HttpResponseError(message=error_json)
        exception.status_code = 403

        # side_effect raises the exception when called
        poller.result.side_effect = exception
        client.begin_create_or_update.return_value = poller

        # Simulate client.get returning the account successfully
        mock_account = mock.MagicMock()
        mock_account.provisioning_state = "Succeeded"
        client.get.return_value = mock_account

        # Parameters
        resource_group_name = "rg"
        account_name = "myaccount"

        # Call the private function directly to verify logic
        result = _create_database_account(
            client=client,
            resource_group_name=resource_group_name,
            account_name=account_name,
            locations=[],
            is_restore_request=True,
            arm_location="westeurope",
            restore_source="/subscriptions/sub/providers/Microsoft.DocumentDB/locations/westeurope/restorableDatabaseAccounts/source-id",
            restore_timestamp="2026-01-01T00:00:00+00:00"
        )

        # Assertions
        # 1. begin_create_or_update called
        client.begin_create_or_update.assert_called()
        # 2. poller.result() called (and raised exception)
        poller.result.assert_called()
        # 3. client.get called (recovery mechanism)
        client.get.assert_called_with(resource_group_name, account_name)
        # 4. Result is the account returned by get
        self.assertEqual(result, mock_account)

    def test_restore_raises_other_errors(self):
        from azure.core.exceptions import HttpResponseError
        from azure.cli.command_modules.cosmosdb.custom import _create_database_account

        # Setup mocks
        client = mock.MagicMock()
        poller = mock.MagicMock()

        # Different error
        exception = HttpResponseError(message="Some other error")
        exception.status_code = 500
        poller.result.side_effect = exception
        client.begin_create_or_update.return_value = poller

        with self.assertRaises(HttpResponseError):
             _create_database_account(
                client=client,
                resource_group_name="rg",
                account_name="myaccount",
                is_restore_request=True,
                arm_location="westeurope",
                restore_source="src",
                restore_timestamp="ts"
            )

    def test_normal_create_does_not_suppress_error(self):
        from azure.core.exceptions import HttpResponseError
        from azure.cli.command_modules.cosmosdb.custom import _create_database_account

        # Setup mocks
        client = mock.MagicMock()
        poller = mock.MagicMock()

        # Same error but NOT a restore request
        error_json = '{"code":"Forbidden","message":"Database Account riks-models-003-acc-westeurope does not exist"}'
        exception = HttpResponseError(message=error_json)
        exception.status_code = 403
        poller.result.side_effect = exception
        client.begin_create_or_update.return_value = poller

        with self.assertRaises(HttpResponseError):
             _create_database_account(
                client=client,
                resource_group_name="rg",
                account_name="myaccount",
                is_restore_request=False, # Normal create
                arm_location="westeurope"
            )

    def test_normal_create_success(self):
        from azure.cli.command_modules.cosmosdb.custom import _create_database_account

        # Setup mocks
        client = mock.MagicMock()
        poller = mock.MagicMock()
        
        # Simulate successful creation
        mock_created_account = mock.MagicMock()
        mock_created_account.provisioning_state = "Succeeded"
        poller.result.return_value = mock_created_account
        client.begin_create_or_update.return_value = poller

        # Call the private function
        result = _create_database_account(
            client=client,
            resource_group_name="rg",
            account_name="myaccount",
            is_restore_request=False,
            arm_location="westeurope"
        )

        # Assertions
        # 1. begin_create_or_update called
        client.begin_create_or_update.assert_called()
        # 2. poller.result() called
        poller.result.assert_called()
        # 3. client.get should NOT be called since result() succeeded
        client.get.assert_not_called()
        # 4. Result matches
        self.assertEqual(result, mock_created_account)
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest

from azure.cli.testsdk import ScenarioTest, record_only
import json
import os
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


id_sql = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/SQL-CLITEST-RG/providers/Microsoft.Compute/virtualMachines/sql-clitestvm-donotuse2'
item_id_sql = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourcegroups/sql-clitest-rg/providers/Microsoft.RecoveryServices/vaults/sql-clitestvault-donotuse/backupFabrics/Azure/protectionContainers/VMAppContainer;compute;sql-clitest-rg;sql-clitestvm-donotuse2/protectedItems/SQLDataBase;mssqlserver;msdb'
sub_sql = '38304e13-357e-405e-9e9a-220351dcce8c'
rg_sql = 'sql-clitest-rg'
vault_sql = 'sql-clitestvault-donotuse'
container_sql = 'VMAppContainer;Compute;sql-clitest-rg;sql-clitestvm-donotuse2'
container_friendly_sql = 'sql-clitestvm-donotuse2'
server_friendly_sql = 'sql-clitestvm-d'
item_auto_sql = 'SQLInstance;mssqlserver'
item1_sql = 'SQLDataBase;mssqlserver;msdb'
item1_sql_fname = 'msdb'
instance_name = 'sqlinstance;mssqlserver'


class BackupTests(ScenarioTest, unittest.TestCase):
    # SQL workload tests start here
    # Please make sure you have the following setup in place before running the tests -

    # For the tests using sql-clitestvm-donotuse2 and sql-clitestvault-donotuse -
    # Each test will register the container at the start and unregister at the end of the test
    # Make sure that the container is not already registered since the start of the test

    # Note: Archive test uses different subscription. Please comment them out when running the whole test suite at once. And run those tests individually.


    def register_container(self):
        # Check if the container is already registered to the vault, and if it is, if it's in soft-deleted state. Register/Re-register accordingly.
        existing_container = self.cmd('backup container show --backup-management-type AzureWorkload -g "{rg}" -v "{vault}" -n "{name}"').get_output_in_json()
        if existing_container:
            print("Found an existing container")
            if 'properties' in existing_container and \
                    'registrationStatus' in existing_container['properties'] and \
                    existing_container['properties']['registrationStatus'] == 'SoftDeleted':
                print("Container is soft-deleted - reregistering")
                self.cmd('backup container re-register --backup-management-type AzureWorkload --workload-type "{wt}" -g "{rg}" -v "{vault}" -c "{name}" --yes')
        else:
            print("Registering the container anew")
            self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

    def register_item(self):
        # Check if the item is already registered for backup. If not, register, if it is, undelete + reprotect as appropriate.
        existing_item = self.cmd('backup item show --backup-management-type AzureWorkload -g "{rg}" -v "{vault}" -c "{name}" -n "{item}"').get_output_in_json()
        if existing_item:
            print("Found an existing item")
            if 'properties' in existing_item and \
                    'isScheduledForDeferredDelete' in existing_item['properties'] and \
                    existing_item['properties']['isScheduledForDeferredDelete']:
                print("item was soft-deleted - undeleting")
                self.cmd('backup protection undelete --backup-management-type AzureWorkload --workload-type "{wt}" -c "{name}" -i "{item}" -g "{rg}" -v "{vault}"')
                time.sleep(10)
            
            existing_item = self.cmd('backup item show --backup-management-type AzureWorkload -g "{rg}" -v "{vault}" -c "{name}" -n "{item}"').get_output_in_json()
            if 'properties' in existing_item and \
                    'protectionState' in existing_item['properties'] and \
                    existing_item['properties']['protectionState'] == 'ProtectionStopped':
                print("item was in protection stopped state - resuming")
                self.cmd('backup protection resume --backup-management-type AzureWorkload --workload-type "{wt}" -g "{rg}" -v "{vault}" -c "{name}" -i "{item}" -p "{policy}"', checks=[
                    self.check("properties.entityFriendlyName", '{fitem}'),
                    self.check("properties.operation", "ConfigureBackup"),
                    self.check("properties.status", "Completed"),
                    self.check("resourceGroup", '{rg}')
                ])
        else:
            print("registering the item anew")
            self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
                self.check("properties.entityFriendlyName", '{fitem}'),
                self.check("properties.operation", "ConfigureBackup"),
                self.check("properties.status", "Completed"),
                self.check("resourceGroup", '{rg}')
            ])

    @record_only()
    def test_backup_wl_sql_container(self):

        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'fname': container_friendly_sql,
            'rg': rg_sql,
            'wt': 'MSSQL',
            'sub': sub_sql,
            'id': id_sql
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id} ')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        container_json = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{fname}'),
            self.check('properties.healthStatus', 'Healthy'),
            self.check('properties.registrationStatus', 'Registered'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.kwargs['container_name'] = container_json['name']

        self.cmd('backup container show -n {container_name} -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{fname}'),
            self.check('properties.healthStatus', 'Healthy'),
            self.check('properties.registrationStatus', 'Registered'),
            self.check('name', '{container_name}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.assertIn(self.kwargs['vault'].lower(), container_json['id'].lower())
        self.assertIn(self.kwargs['name'].lower(), container_json['name'].lower())

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?properties.friendlyName == '{fname}'])", 1)])

        self.cmd('backup container re-register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} -y --container-name {name}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_policy(self):

        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'fname': container_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': rg_sql,
            'item': item1_sql,
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': 'SQLDataBase',
            'policy_new': self.create_random_name('clitest-policy', 24)
        })
        self.kwargs['policy1_json'] = self.cmd('backup policy show -g {rg} -v {vault} -n {policy}', checks=[
            self.check('name', '{policy}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.kwargs['policy_json'] = json.dumps(self.kwargs['policy1_json'], separators=(',', ':')).replace('\'', '\\\'').replace('"', '\\"')

        self.cmd("backup policy create -g {rg} -v {vault} --policy {policy_json} --backup-management-type AzureWorkload --workload-type {wt} --name {policy_new}", checks=[
            self.check('name', '{policy_new}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup policy list -g {rg} -v {vault}', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{policy}'])", 1),
            self.check("length([?name == '{policy_new}'])", 1)
        ])

        self.kwargs['policy1_json']['properties']['settings']['isCompression'] = 'true'
        self.kwargs['policy1_json']['properties']['settings']['issqlcompression'] = 'true'
        self.kwargs['policy1_json'] = json.dumps(self.kwargs['policy1_json'], separators=(',', ':')).replace('\'', '\\\'').replace('"', '\\"')

        self.cmd("backup policy set -g {rg} -v {vault} --policy {policy1_json} -n {policy_new}", checks=[
            self.check('name', '{policy_new}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd("backup policy set -g {rg} -v {vault} --backup-management-type AzureWorkload --fix-for-inconsistent-items -n {policy_new}", checks=[
            self.check('name', '{policy_new}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup policy show -g {rg} -v {vault} -n {policy_new}', checks=[
            self.check('name', '{policy_new}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup policy delete -g {rg} -v {vault} -n {policy_new}')

        self.cmd('backup policy list -g {rg} -v {vault}', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{policy}'])", 1),
            self.check("length([?name == '{policy_new}'])", 0)
        ])

    @record_only()
    def test_backup_wl_sql_protectable_item(self):

        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': rg_sql,
            'item': item1_sql,
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': 'SQLDataBase',
            'protectable_item_name': item1_sql_fname,
            'pit_hana': 'SAPHanaDatabase'
        })

        # self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')
        self.register_container()

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --query properties.friendlyName --backup-management-type AzureWorkload').get_output_in_json()

        self.cmd('backup protectable-item list -g {rg} --vault-name {vault} --workload-type {wt}', checks=[
            self.check("length([?properties.friendlyName == 'master'])", 1)
        ])

        self.cmd('backup protectable-item show -g {rg} --vault-name {vault} --name "master" --workload-type {wt} --protectable-item-type {pit} --server-name {fname}', checks=[
            self.check('properties.friendlyName', 'master'),
            self.check('properties.protectableItemType', '{pit}'),
            self.check('properties.serverName', '{fname}'),
            self.check('resourceGroup', '{rg}')
        ])

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_rp(self):
        resource_group = rg_sql.lower()
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'rg': resource_group,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'item': item1_sql,
            'pit': 'SQLDatabase',
            'item_id': item_id_sql,
            'id': id_sql,
            'fitem': item1_sql_fname
        })

        self.register_container()
        self.register_item()

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [].name', checks=[
            self.check("length(@)", 1)
        ])

        rp1_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_sql.lower(), rp1_json[0]['id'].lower())
        self.assertIn(container_sql.lower(), rp1_json[0]['id'].lower())

        rp2_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_sql.lower(), rp2_json[0]['id'].lower())
        self.assertIn(container_sql.lower(), rp2_json[0]['id'].lower())

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @record_only()
    @unittest.skip("Covered by other scenarios")
    def test_backup_wl_sql_auto_protection(self):
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': rg_sql,
            'item': item_auto_sql,
            'fitem': item_auto_sql.split(';')[-1],
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': 'SQLInstance'
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection auto-enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-name {item} --protectable-item-type {pit} --server-name {fname} --workload-type {wt}')

        protectable_item_json = self.cmd('backup protectable-item show -v {vault} -g {rg} -n {item} --protectable-item-type {pit} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.isAutoProtected", True)]).get_output_in_json()

        self.assertIn(self.kwargs['policy'], protectable_item_json['properties']['autoProtectionPolicy'])

        self.cmd('backup protection auto-disable-for-azurewl -v {vault} -g {rg} --protectable-item-name {item} --protectable-item-type {pit} --server-name {fname} --workload-type {wt}')

        self.cmd('backup protectable-item show -v {vault} -g {rg} -n {item} --protectable-item-type {pit} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.isAutoProtected", False),
            self.check("properties.autoProtectionPolicy", None)])

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_item(self):
        resource_group = rg_sql.lower()
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'rg': resource_group,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'item': item1_sql,
            'pit': 'SQLDatabase',
            'item_id': item_id_sql,
            'id': id_sql,
            'fitem': item1_sql_fname
        })

        # self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 1)])

        # self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}')
        self.register_container()
        self.register_item()

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {name} -n {item} --backup-management-type AzureWorkload --workload-type {wt}', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'IRPending'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.assertIn(self.kwargs['vault'].lower(), item1_json['id'].lower())
        self.assertIn(self.kwargs['fname'].lower(), item1_json['properties']['containerName'].lower())
        self.assertIn(self.kwargs['fname'].lower(), item1_json['properties']['sourceResourceId'].lower())
        self.assertIn(self.kwargs['policy'].lower(), item1_json['properties']['policyId'].lower())

        self.kwargs['container1_fullname'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.cmd('backup item show -g {rg} -v {vault} -c {container1_fullname} -n {item} --backup-management-type AzureWorkload --workload-type {wt}', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'IRPending'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['item1_fullname'] = item1_json['name']

        self.cmd('backup item show -g {rg} -v {vault} -c {container1_fullname} -n {item1_fullname} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'IRPending'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup item list -g {rg} -v {vault} -c {container1} --backup-management-type AzureWorkload --workload-type SQLDataBase', checks=[
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} -c {container1_fullname} --backup-management-type AzureWorkload --workload-type SQLDataBase', checks=[
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} --backup-management-type AzureWorkload --workload-type SQLDataBase', checks=[
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item set-policy -g {rg} -v {vault} -c {container1} -n {item1_fullname} -p {policy} --backup-management-type AzureWorkload --workload-type SQLDataBase', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload --workload-type SQLDataBase').get_output_in_json()
        self.assertIn("HourlyLogBackup".lower(), item1_json['properties']['policyId'].lower())

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_protection(self):
        resource_group = rg_sql.lower()
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'rg': resource_group,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'item': item1_sql,
            'pit': 'SQLDatabase',
            'item_id': item_id_sql,
            'id': id_sql,
            'fitem': item1_sql_fname 
        })

        # self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 1)])

        # self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
        #     self.check("properties.entityFriendlyName", '{fitem}'),
        #     self.check("properties.operation", "ConfigureBackup"),
        #     self.check("properties.status", "Completed"),
        #     self.check("resourceGroup", '{rg}')
        # ])
        self.register_container()
        self.register_item()

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item} -c {name} --backup-type Full --enable-compression false', checks=[
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.assertIn("Backup", self.kwargs['backup_job']['properties']['operation'])

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'Healthy'),
            self.check('properties.protectionState', 'Protected'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup protection disable -v {vault} -g {rg} -i {item} -c {name} --backup-management-type AzureWorkload -y', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "DisableBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check("properties.friendlyName", '{fitem}'),
            self.check("properties.protectionState", "ProtectionStopped"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_restore(self):
        resource_group = rg_sql.lower()
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'rg': resource_group,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'item': item1_sql,
            'fitem': item1_sql_fname,
            'id': id_sql,
            'pit': 'SQLDatabase',
            'item_id': item_id_sql,
            'titem': item1_sql_fname + '_restored',
            'tinstance_name': instance_name
        })

        # self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 1)])

        # self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
        #     self.check("properties.entityFriendlyName", '{fitem}'),
        #     self.check("properties.operation", "ConfigureBackup"),
        #     self.check("properties.status", "Completed"),
        #     self.check("resourceGroup", '{rg}')
        # ])
        self.register_container()
        self.register_item()

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item} -c {name} --backup-type Full --enable-compression false', checks=[
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.assertIn("Backup", self.kwargs['backup_job']['properties']['operation'])

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'Healthy'),
            self.check('properties.protectionState', 'Protected'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [0]').get_output_in_json()

        self.kwargs['rp'] = self.kwargs['rp']['name']

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode AlternateWorkloadRestore --rp-name {rp} --item-name {item} --container-name {container1} --target-item-name {titem} --target-server-type SQLInstance --target-server-name {fname} --workload-type {wt} --target-instance-name {tinstance_name}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_sql_restore.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_sql_restore.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --item-name {item} --container-name {container1} --rp-name {rp}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_sql_restore.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_sql_restore.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup protection disable -v {vault} -g {rg} -c {name} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_restore_as_files(self):
        resource_group = rg_sql.lower()
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'rg': resource_group,
            'fname': server_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'item': item1_sql,
            'fitem': item1_sql_fname,
            'id': id_sql,
            'pit': 'SQLDatabase',
            'item_id': item_id_sql,
            'titem': item1_sql_fname + '_restored'
        })
        # self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 1)])

        # self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
        #     self.check("properties.entityFriendlyName", '{fitem}'),
        #     self.check("properties.operation", "ConfigureBackup"),
        #     self.check("properties.status", "Completed"),
        #     self.check("resourceGroup", '{rg}')
        # ])
        self.register_container()
        self.register_item()

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item} -c {name} --backup-type Full --enable-compression false', checks=[
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.assertIn("Backup", self.kwargs['backup_job']['properties']['operation'])

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check('properties.protectedItemHealthStatus', 'Healthy'),
            self.check('properties.protectionState', 'Protected'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [0]').get_output_in_json()
        self.kwargs['rp'] = self.kwargs['rp']['name']

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode RestoreAsFiles --rp-name {rp} --filepath "C:\" --target-container-name {container1} --item-name {item} --container-name {container1}  --workload-type {wt}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_sql_raf.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_sql_raf.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup protection disable -v {vault} -g {rg} -c {name} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        # self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
        #     self.check("length([?name == '{name}'])", 0)])

    @AllowLargeResponse()
    @record_only()
    def test_backup_wl_sql_crr(self):
        self.kwargs.update({
            'vault': "sql-clitest-vault",
            'name': "VMAppContainer;Compute;sql-clitest-rg;sql-clitest-vm",
            'fname': "sql-clitest-vm",
            'wt': 'MSSQL',
            'sub': "vsarg-MABPortalTestAutomation_NOB",
            'rg': "sql-clitest-rg",
            'item': "SQLDataBase;mssqlserver;msdb",
            'fitem': "msdb",
            'tvault': "clitest-vault-secondary-donotuse",
            'trg': "clitest-rg-donotuse",
            'tcontainer': "clitest-sql-secondary-donotuse",
            'tserver': "clitest-sql-sec",
            'tpit': 'SQLInstance',
            'titem': 'msdb_restored'
        })
        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectionState', 'Protected'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --use-secondary-region --query [0]').get_output_in_json()

        self.kwargs['rp'] = self.kwargs['rp']['name']

        #SQL CRR ALR Restore
        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode AlternateWorkloadRestore --rp-name {rp} --item-name {item} --container-name {container1} --target-item-name {titem} --target-server-type SQLInstance --target-server-name {tserver} --target-container-name {tcontainer} --workload-type {wt} --target-vault-name {tvault} --target-resource-group {trg}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_sql_crr.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_sql_crr.json --use-secondary-region', checks=[
            self.check("properties.operation", "CrossRegionRestore"),
            self.check("properties.status", "InProgress")
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job} --use-secondary-region')

        #SQL CRR RAF Restore
        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode restoreasfiles --rp-name {rp} --item-name {item} --container-name {container1} --target-container-name {tcontainer} --workload-type {wt} --target-vault-name {tvault} --target-resource-group {trg} --filepath "C:\"').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_sql_crr.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_sql_crr.json --use-secondary-region', checks=[
            self.check("properties.operation", "CrossRegionRestore"),
            self.check("properties.status", "InProgress")
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        # self.cmd('backup job wait -v {vault} -g {rg} -n {job} --use-secondary-region')

    @AllowLargeResponse()
    @record_only()
    def test_backup_wl_sql_archive (self):
        self.kwargs.update({
            'vault': "archiveccyvault1",
            'rg': "ArchiveResourceGroup",
            'sub': "AzureBackup_Functional_Testing",
            'item': "SQLDataBase;mssqlserver;msdb",
            'container': "VMAppContainer;compute;archiveresourcegroup;archsqlccyvm2"
        })
        
        # Getting the recovery point IDs (names) and storing it in a list
        rp_names = self.cmd('backup recoverypoint list --backup-management-type AzureWorkload --workload-type MSSQL -g {rg} -v {vault} -c {container} -i {item}', checks=[
        ]).get_output_in_json()

        self.kwargs['rp1'] = rp_names[0]['name']
        self.kwargs['rp1_tier'] = rp_names[0]['tierType']
        self.kwargs['rp1_is_ready_for_move'] = rp_names[0]['properties']['recoveryPointMoveReadinessInfo']['ArchivedRP']['isReadyForMove']
        
        # Check Archivable Recovery Points 
        self.cmd('backup recoverypoint list -g {rg} -v {vault} -i {item} -c {container} --backup-management-type AzureWorkload --is-ready-for-move {rp1_is_ready_for_move} --target-tier VaultArchive --query [0]', checks=[
            self.check("resourceGroup", '{rg}'),
            self.check("properties.recoveryPointMoveReadinessInfo.ArchivedRP.isReadyForMove", '{rp1_is_ready_for_move}')
        ])

        # Get Archived Recovery Points 
        self.cmd('backup recoverypoint list -g {rg} -v {vault} -i {item} -c {container} --backup-management-type AzureWorkload --tier {rp1_tier} --query [0]', checks=[
            self.check("tierType", '{rp1_tier}'),
            self.check("resourceGroup", '{rg}')
        ])

        is_move = False
        for i in rp_names:
            if i['tierType']=="VaultStandard" and i['properties']['recoveryPointMoveReadinessInfo']['ArchivedRP']['isReadyForMove']==True:
                self.kwargs['rp_move'] = i['name']
                is_move = True
                break
        
        if is_move:
            # # Move Recovery points
            self.cmd('backup recoverypoint move -g {rg} -v {vault} -i {item} -c {container} --source-tier VaultStandard --destination-tier VaultArchive --name {rp_move}', checks=[
                self.check("properties.entityFriendlyName", 'msdb [archsqlccyvm2]'),
                self.check("resourceGroup", '{rg}'),
                self.check("properties.operation", "MoveRecoveryPoint"),
                self.check("properties.status", "Completed")
            ])
        
        # Getting the recovery point ID in VaultArchive tier
        self.kwargs['rp_restore'] = self.cmd('backup recoverypoint list --backup-management-type AzureWorkload --workload-type MSSQL -g {rg} -v {vault} -c {container} -i {item} --tier VaultArchive --query [0]').get_output_in_json()
        self.kwargs['rp_restore'] = self.kwargs['rp_restore']['name']

        # # Integrated Restore
        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --item-name {item} --container-name {container} --rp-name {rp_restore}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_sql_archive.json", "w") as f:
            f.write(self.kwargs['rc'])

        # # Trigger Restore
        self.cmd('backup restore restore-azurewl -g {rg} -v {vault} --recovery-config recoveryconfig_sql_archive.json --rehydration-priority High', checks=[
            self.check("properties.operation", "RestoreWithRehydrate"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()


    def test_backup_wl_reconfigure(self):
        self.kwargs.update({
            'resource_group': 'zubairRG',
            'vault1': 'zimmut-ccy-6',
            'vault2': 'zimmut-ccy-5',
            'container': 'sql-migration-vm2',
            'item': 'model',
            'policy_name': 'HourlyLogBackup'
        })

        self.cmd('backup vault show -g "{resource_group}" -n "{vault1}"', checks=[
            self.check('name', '{vault1}'),
            self.check('resourceGroup', '{resource_group}')
        ])

        self.cmd('backup vault show -g "{resource_group}" -n "{vault2}"', checks=[
            self.check('name', '{vault2}'),
            self.check('resourceGroup', '{resource_group}')
        ])

        # Verify container and items exist in vault1
        self.cmd('backup container show -g "{resource_group}" -v "{vault1}" -n "{container}" --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{container}'),
            self.check('properties.registrationStatus', 'Registered')
        ])

        self.cmd('backup item show -g "{resource_group}" -v "{vault1}" -c "{container}" -n "{item}" --backup-management-type AzureWorkload --workload-type MSSQL', checks=[
            self.check('properties.friendlyName', '{item}'),
            self.check('properties.protectionState', 'Protected')
        ])

        # Verify policy exists in vault2
        self.cmd('backup policy show -g "{resource_group}" -v "{vault2}" -n "{policy_name}"', checks=[
            self.check('name', '{policy_name}'),
            self.check('resourceGroup', '{resource_group}')
        ])

        self.cmd('backup protection reconfigure -g "{resource_group}" -v "{vault1}" -c "{container}" -i "{item}" --backup-management-type "AzureWorkload" --workload-type "MSSQL" --new-rg "{resource_group}" --new-vault-name "{vault2}" --new-policy-name "{policy_name}"', checks=[
            self.check('properties.operation', 'ConfigureBackup'),
            self.check('properties.status', 'Completed')
        ])

        # Clean up - delete the backup item from vault2
        self.cmd('backup protection disable -g "{resource_group}" -v "{vault2}" -c "{container}" -i "{item}" --backup-management-type AzureWorkload --workload-type MSSQL --delete-backup-data true --yes')

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, record_only
import json
import os


id_sql = '/subscriptions/da364f0f-307b-41c9-9d47-b7413ec45535/resourceGroups/pstestwlRG1bca8/providers/Microsoft.Compute/virtualMachines/pstestwlvm1bca8'
id_hana = '/subscriptions/e3d2d341-4ddb-4c5d-9121-69b7e719485e/resourceGroups/IDCDemo/providers/Microsoft.Compute/virtualMachines/HANADemoIDC3'
item_id_sql = '/Subscriptions/da364f0f-307b-41c9-9d47-b7413ec45535/resourceGroups/pstestwlRG1bca8/providers/Microsoft.RecoveryServices/vaults/pstestwlRSV1bca8/backupFabrics/Azure/protectionContainers/vmappcontainer;compute;pstestwlrg1bca8;pstestwlvm1bca8/protectedItems/sqldatabase;mssqlserver;testdb1'
item_id_hana = '/Subscriptions/e3d2d341-4ddb-4c5d-9121-69b7e719485e/resourceGroups/IDCDemo/providers/Microsoft.RecoveryServices/vaults/IDCDemoVault/backupFabrics/Azure/protectionContainers/vmappcontainer;compute;IDCDemo;HANADemoIDC3/protectedItems/SAPHanaDatabase;h22;h22'
sub_sql = 'da364f0f-307b-41c9-9d47-b7413ec45535'
sub_hana = 'e3d2d341-4ddb-4c5d-9121-69b7e719485e'
rg_sql = 'pstestwlRG1bca8'
rg_hana = 'IDCDemo'
vault_sql = 'pstestwlRSV1bca8'
vault_hana = 'IDCDemoVault'
container_sql = 'VMAppContainer;Compute;pstestwlRG1bca8;pstestwlvm1bca8'
container_hana = 'VMAppContainer;Compute;IDCDemo;HANADemoIDC3'
container_friendly_sql = 'pstestwlvm1bca8'
container_friendly_hana = 'HANADemoIDC3'
item_auto_sql = 'SQLInstance;mssqlserver'
item_auto_hana = 'SAPHanaSystem;H22'
item1_sql = 'SQLDataBase;MSSQLSERVER;testdb1'
item2_sql = 'msdb'
item1_hana = 'SAPHanaDatabase;H22;h22'
item2_hana = 'SYSTEMDB'
backup_entity_friendly_name_hana = 'H22/H22 [HANADemoIDC3]'
backup_entity_friendly_name_sql = 'MSSQLSERVER/testdb1 [pstestwlvm1bca8]'
item_id_hana_2 = '/Subscriptions/e3d2d341-4ddb-4c5d-9121-69b7e719485e/resourceGroups/IDCDemo/providers/Microsoft.RecoveryServices/vaults/IDCDemoVault/backupFabrics/Azure/protectionContainers/vmappcontainer;compute;IDCDemo;HANADemoIDC3/protectedItems/SAPHanaDatabase;h22;h22_restored_sarath'


class BackupTests(ScenarioTest, unittest.TestCase):
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

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

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

        self.assertIn(vault_sql.lower(), container_json['id'].lower())
        self.assertIn(container_sql.lower(), container_json['name'].lower())

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?properties.friendlyName == '{fname}'])", 1)])

        self.cmd('backup container re-register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} -y --container-name {name}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_hana_container(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                      resource_group=rg_hana, vault_name=vault_hana, workload_type='SAPHANA',
                                      subscription=sub_hana, id=id_hana):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': container_friendly_hana,
            'rg': rg_hana,
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'id': id_hana
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

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

        self.assertIn(vault_hana.lower(), container_json['id'].lower())
        self.assertIn(container_hana.lower(), container_json['name'].lower())

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?properties.friendlyName == '{fname}'])", 1)])

        self.cmd('backup container re-register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} -y --container-name {name}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

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
    def test_backup_wl_hana_policy(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': container_friendly_hana,
            'policy': 'DemoBackup',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'DemoBackup',
            'rg': rg_hana,
            'item': item1_hana,
            'id': id_hana,
            'item_id': item_id_hana,
            'pit': 'HANADataBase',
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
    def test_backup_wl_sql_item(self):

        self.kwargs.update({
            'vault': "sarath-vault",
            'name': "VMAppContainer;Compute;sarath-rg;sarathvm",
            'fname': "sarathvm",
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': "sarath-rg",
            'item': "sqldatabase;mssqlserver;msdb",
            'fitem': "msdb",
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': 'SQLDataBase'
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}')

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {name} -n {item} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'IRPending'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.assertIn("sarath-vault", item1_json['id'].lower())
        self.assertIn("sarathvm", item1_json['properties']['containerName'].lower())
        self.assertIn("sarathvm", item1_json['properties']['sourceResourceId'].lower())
        self.assertIn(self.kwargs['default'].lower(), item1_json['properties']['policyId'].lower())

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
            self.check("length(@)", 3),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} -c {container1_fullname} --backup-management-type AzureWorkload --workload-type SQLDataBase', checks=[
            self.check("length(@)", 3),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} --backup-management-type AzureWorkload --workload-type SQLDataBase', checks=[
            self.check("length(@)", 3),
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

    @record_only()
    def test_backup_wl_hana_item(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': container_friendly_hana,
            'policy': 'HourlyLogBackup',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'HourlyLogBackup',
            'rg': "idcdemo",
            'item': "saphanadatabase;h22;h22_restored_sarath",
            'fitem': "h22_restored_sarath",
            'id': id_hana,
            'item_id': item_id_hana_2,
            'pit': 'SAPHanaDatabase'
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}')

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {name} -n {item} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'IRPending'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.assertIn(vault_hana.lower(), item1_json['id'].lower())
        self.assertIn(container_friendly_hana.lower(), item1_json['properties']['containerName'].lower())
        self.assertIn(container_friendly_hana.lower(), item1_json['properties']['sourceResourceId'].lower())
        self.assertIn(self.kwargs['default'].lower(), item1_json['properties']['policyId'].lower())

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

        self.cmd('backup item list -g {rg} -v {vault} -c {container1} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("length(@)", 6),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} -c {container1_fullname} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("length(@)", 6),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("length(@)", 8),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item set-policy -g {rg} -v {vault} -c {container1} -n {item1_fullname} -p {policy} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase').get_output_in_json()
        self.assertIn("HourlyLogBackup".lower(), item1_json['properties']['policyId'].lower())

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

    @record_only()
    def test_backup_wl_sql_protectable_item(self):

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
            'protectable_item_name': 'newdb',
            'pit_hana': 'SAPHanaDatabase'
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --query properties.friendlyName --backup-management-type AzureWorkload').get_output_in_json()

        self.cmd('backup protectable-item list -g {rg} --vault-name {vault} --workload-type {wt}', checks=[
            self.check("length([?properties.friendlyName == '{protectable_item_name}'])", 0)
        ])

        self.cmd('backup protectable-item initialize -g {rg} --vault-name {vault} --workload-type {wt} --container-name {name}')

        self.cmd('backup protectable-item list -g {rg} --vault-name {vault} --workload-type {wt}', checks=[
            self.check("length([?properties.friendlyName == '{protectable_item_name}'])", 1)
        ])

        self.cmd('backup protectable-item show -g {rg} --vault-name {vault} --name {protectable_item_name} --workload-type {wt} --protectable-item-type {pit} --server-name {fname}', checks=[
            self.check('properties.friendlyName', '{protectable_item_name}'),
            self.check('properties.protectableItemType', '{pit}'),
            self.check('properties.serverName', '{fname}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_hana_protectable_item(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': container_friendly_hana,
            'policy': 'HourlyLogBackup',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'HourlyLogBackup',
            'rg': rg_hana,
            'item': item1_hana,
            'id': id_hana,
            'item_id': item_id_hana,
            'pit': 'SAPHanaDatabase',
            'protectable_item_name': 'NEWDB',
            'pit_hana': 'SAPHanaDatabase'
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --query properties.friendlyName --backup-management-type AzureWorkload').get_output_in_json()

        self.cmd('backup protectable-item list -g {rg} --vault-name {vault} --workload-type {wt}', checks=[
            self.check("length([?properties.friendlyName == '{protectable_item_name}'])", 0)
        ])

        self.cmd('backup protectable-item initialize -g {rg} --vault-name {vault} --workload-type {wt} --container-name {name}')

        self.cmd('backup protectable-item list -g {rg} --vault-name {vault} --workload-type {wt}', checks=[
            self.check("length([?properties.friendlyName == '{protectable_item_name}'])", 1)
        ])

        self.cmd('backup protectable-item show -g {rg} --vault-name {vault} --name {protectable_item_name} --workload-type {wt} --protectable-item-type {pit} --server-name {fname}', checks=[
            self.check('properties.friendlyName', '{protectable_item_name}'),
            self.check('properties.protectableItemType', '{pit_hana}'),
            self.check('properties.serverName', '{fname}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_sql_rp(self):
        resource_group = rg_sql.lower()
        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'rg': resource_group,
            'fname': container_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'item': item1_sql,
            'pit': 'SQLDatabase',
            'item_id': item_id_sql,
            'id': id_sql
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [].name', checks=[
            self.check("length(@)", 1)
        ])

        rp1_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_sql.lower(), rp1_json[0]['id'].lower())
        self.assertIn(container_sql.lower(), rp1_json[0]['id'].lower())

        rp2_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_sql.lower(), rp2_json[0]['id'].lower())
        self.assertIn(container_sql.lower(), rp2_json[0]['id'].lower())

    @record_only()
    def test_backup_wl_hana_rp(self):

        resource_group = rg_hana.lower()
        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'rg': resource_group,
            'fname': container_friendly_hana,
            'policy': 'HourlyLogBackup',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'item': 'saphanadatabase;h22;h22_restored_sarath',
            'pit': 'HANADatabase',
            'item_id': item_id_hana,
            'id': id_hana
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [].name', checks=[
            self.check("length(@)", 1)
        ])

        rp1_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_hana.lower(), rp1_json[0]['id'].lower())
        self.assertIn(container_hana.lower(), rp1_json[0]['id'].lower())

        rp2_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_hana.lower(), rp2_json[0]['id'].lower())
        self.assertIn(container_hana.lower(), rp2_json[0]['id'].lower())

    @record_only()
    def test_backup_wl_sql_protection(self):

        self.kwargs.update({
            'vault': "sarath-vault",
            'name': "VMAppContainer;Compute;sarath-rg;sarathvm",
            'fname': "sarathvm",
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': "sarath-rg",
            'item': "sqldatabase;mssqlserver;msdb",
            'fitem': "msdb",
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': "SQLDataBase",
            'entityFriendlyName': 'MSSQLSERVER/msdb [sarathvm]'
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item} -c {name} --backup-type Full --retain-until 1-7-2020 --enable-compression false', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Backup"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

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

    @record_only()
    def test_backup_wl_hana_protection(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': container_friendly_hana,
            'policy': 'HourlyLogBackup',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'HourlyLogBackup',
            'rg': "idcdemo",
            'item': "saphanadatabase;h22;h22_restored_sarath",
            'fitem': "h22_restored_sarath",
            'id': id_hana,
            'item_id': item_id_hana,
            'pit': "SAPHanaDatabase",
            'entityFriendlyName': 'H22/H22_RESTORED_SARATH [HANADemoIDC3]'
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item} -c {name} --backup-type Full --retain-until 1-7-2020 --enable-compression false', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Backup"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

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

    @record_only()
    def test_backup_wl_sql_auto_protection(self):

        self.kwargs.update({
            'vault': vault_sql,
            'name': container_sql,
            'fname': container_friendly_sql,
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': rg_sql,
            'item': item_auto_sql,
            'fitem': item_auto_sql.split(';')[-1],
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': 'SQLInstance',
            'entityFriendlyName': backup_entity_friendly_name_sql
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection auto-enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-name {item} --protectable-item-type {pit} --server-name {fname} --workload-type {wt}')

        self.cmd('backup protection auto-disable-for-azurewl -v {vault} -g {rg} --item-name {item}')

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_hana_restore(self):

        resource_group = rg_hana.lower()
        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': container_friendly_hana,
            'policy': 'HourlyLogBackup',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'HourlyLogBackup',
            'rg': resource_group,
            'item': "saphanadatabase;h22;h22_restored_sarath",
            'fitem': "h22_restored_sarath",
            'id': id_hana,
            'item_id': item_id_hana,
            'pit': 'SAPHanaDatabase',
            'entityFriendlyName': 'H22/H22_RESTORED_SARATH [HANADemoIDC3]',
            'tpit': 'HANAInstance',
            'titem': 'H22'
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl --vault-name {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -c {name} -i {item} --backup-type Full --retain-until 1-7-2020 --enable-compression false', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Backup"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

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

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode AlternateWorkloadRestore --rp-name {rp} --item-name {item} --container-name {container1} --target-item-name {titem} --target-server-type {tpit} --target-server-name {fname} --workload-type {wt}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig.json', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --item-name {item} --container-name {container1} --rp-name {rp}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig.json', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        os.remove("recoveryconfig.json")

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase -i {item} -y', checks=[
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

    @record_only()
    def test_backup_wl_sql_restore(self):
        self.kwargs.update({
            'vault': "sarath-vault",
            'name': "VMAppContainer;Compute;sarath-rg;sarathvm",
            'fname': "sarathvm",
            'policy': 'HourlyLogBackup',
            'wt': 'MSSQL',
            'sub': sub_sql,
            'default': 'HourlyLogBackup',
            'rg': "sarath-rg",
            'item': "sqldatabase;mssqlserver;msdb",
            'fitem': "msdb",
            'id': id_sql,
            'item_id': item_id_sql,
            'pit': 'SQLDataBase',
            'entityFriendlyName': 'MSSQLSERVER/msdb [sarathvm]',
            'tpit': 'SQLInstance',
            'titem': 'MSSQLSERVER'
        })

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check('properties.friendlyName', '{fitem}'),
            self.check('properties.protectedItemHealthStatus', 'Healthy'),
            self.check('properties.protectionState', 'Protected'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [0]').get_output_in_json()

        self.kwargs['rp'] = self.kwargs['rp']['name']

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode AlternateWorkloadRestore --rp-name {rp} --item-name {item} --container-name {container1} --target-item-name {titem} --target-server-type SQLInstance --target-server-name {fname} --workload-type {wt}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig.json', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --item-name {item} --container-name {container1} --rp-name {rp}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig.json', checks=[
            self.check("properties.entityFriendlyName", '{entityFriendlyName}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        os.remove("recoveryconfig.json")

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.cmd('backup protection disable -v {vault} -g {rg} -c {name} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

    @record_only()
    def test_backup_wl_sql_restore_as_files(self):
        self.kwargs.update({
            'vault': "iaasvmsqlworkloadexistingvault1",
            'name': "VMAppContainer;compute;iaasvmsqlworkload.existing;iaassqlext-win",
            'wt': 'MSSQL',
            'sub': "38304e13-357e-405e-9e9a-220351dcce8c",
            'rg': "iaasvmsqlworkload.existing.vaults",
            'item': "SQLDataBase;mssqlserver;navigate-testdb2"
        })

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload', checks=[
            self.check('properties.protectedItemHealthStatus', 'Healthy'),
            self.check('properties.protectionState', 'Protected'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [0]').get_output_in_json()
        self.kwargs['rp'] = self.kwargs['rp']['name']

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode RestoreAsFiles --rp-name {rp} --filepath "C:\" --target-container-name {container1} --item-name {item} --container-name {container1}  --workload-type {wt}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        os.remove("recoveryconfig.json")

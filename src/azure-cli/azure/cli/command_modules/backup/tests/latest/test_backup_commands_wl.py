# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

import azure.cli.command_modules.backup.tests.latest.test_backup_commands_wl_help as wl_help

from azure.cli.testsdk import ScenarioTest


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


class BackupTests(ScenarioTest, unittest.TestCase):
    def test_backup_wl_sql_container(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                     resource_group=rg_sql, vault_name=vault_sql, workload_type='MSSQL',
                                     subscription=sub_sql, id=id_sql):

        wl_help.test_backup_wl_container(self, container_name1, container_name2, resource_group, vault_name,
                                         workload_type, subscription, id)

    def test_backup_wl_hana_container(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                      resource_group=rg_hana, vault_name=vault_hana, workload_type='SAPHANA',
                                      subscription=sub_hana, id=id_hana):

        wl_help.test_backup_wl_container(self, container_name1, container_name2, resource_group, vault_name,
                                         workload_type, subscription, id)

    def test_backup_wl_sql_policy(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                  resource_group=rg_sql, vault_name=vault_sql, policy_name='HourlyLogBackup',
                                  workload_type='MSSQL', subscription=sub_sql, item1=item1_sql, id=id_sql, item_type='SQLDataBase',
                                  item_id=item_id_sql, policy_new='new'):

        wl_help.test_backup_wl_policy(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                      workload_type, subscription, item1, id, item_type, item_id, policy_new)

    def test_backup_wl_hana_policy(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                   resource_group=rg_hana, vault_name=vault_hana, policy_name='DemoBackup',
                                   workload_type='SAPHANA', subscription=sub_hana, item1=item1_hana, id=id_hana, item_type='HANADataBase',
                                   item_id=item_id_hana, policy_new='new'):

        wl_help.test_backup_wl_policy(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                      workload_type, subscription, item1, id, item_type, item_id, policy_new)

    def test_backup_wl_sql_item(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                resource_group=rg_sql, vault_name=vault_sql, policy_name='HourlyLogBackup',
                                workload_type='MSSQL', subscription=sub_sql, item1=item1_sql, id=id_sql, item_type='SQLDataBase',
                                item_id=item_id_sql):

        wl_help.test_backup_wl_item(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                    workload_type, subscription, item1, id, item_type, item_id)

    def test_backup_wl_hana_item(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                 resource_group=rg_hana, vault_name=vault_hana, policy_name='HourlyLogBackup',
                                 workload_type='SAPHANA', subscription=sub_hana, item1=item1_hana, id=id_hana, item_type='HANADataBase',
                                 item_id=item_id_hana):

        wl_help.test_backup_wl_item(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                    workload_type, subscription, item1, id, item_type, item_id)

    def test_backup_wl_sql_protectable_item(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                            resource_group=rg_sql, vault_name=vault_sql, policy_name='HourlyLogBackup',
                                            workload_type='MSSQL', subscription=sub_sql, item1=item1_sql, id=id_sql, item_type='SQLDataBase',
                                            item_id=item_id_sql):

        wl_help.test_backup_wl_protectable_item(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                                workload_type, subscription, item1, id, item_type, item_id)

    def test_backup_wl_hana_protectable_item(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                             resource_group=rg_hana, vault_name=vault_hana, policy_name='HourlyLogBackup',
                                             workload_type='SAPHANA', subscription=sub_hana, item1=item1_hana, id=id_hana,
                                             item_type='HANADataBase', item_id=item_id_hana):

        wl_help.test_backup_wl_protectable_item(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                                workload_type, subscription, item1, id, item_type, item_id)

    def test_backup_wl_sql_rp(self, container_name=container_sql, resource_group=rg_sql, vault_name=vault_sql,
                              item_name=item1_sql, workload_type='MSSQL', subscription=sub_sql, item_type='SQLDatabase',
                              container_name2=container_friendly_sql, policy_name='HourlyLogBackup', id=id_sql,
                              item_id=item_id_sql):

        wl_help.test_backup_wl_rp(self, container_name, resource_group, vault_name, item_name, workload_type, subscription,
                                  item_type, container_name2, policy_name, id, item_id)

    def test_backup_wl_hana_rp(self, container_name=container_hana, resource_group=rg_hana, vault_name=vault_hana,
                               item_name=item1_hana, workload_type='SAPHANA', subscription=sub_hana, item_type='HANADatabase',
                               container_name2=container_friendly_hana, policy_name='HourlyLogBackup', id=id_hana,
                               item_id=item_id_hana):

        wl_help.test_backup_wl_rp(self, container_name, resource_group, vault_name, item_name, workload_type, subscription,
                                  item_type, container_name2, policy_name, id, item_id)

    def test_backup_wl_sql_protection(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                      resource_group=rg_sql, vault_name=vault_sql, policy_name='HourlyLogBackup',
                                      workload_type='MSSQL', subscription=sub_sql, item1=item1_sql, id=id_sql, item_type='SQLDataBase',
                                      item_id=item_id_sql, backup_entity_friendly_name=backup_entity_friendly_name_sql):

        wl_help.test_backup_wl_protection(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                          workload_type, subscription, item1, id, item_type, item_id, backup_entity_friendly_name)

    def test_backup_wl_hana_protection(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                       resource_group=rg_hana, vault_name=vault_hana, policy_name='HourlyLogBackup',
                                       workload_type='SAPHANA', subscription=sub_hana, item1=item1_hana, id=id_hana,
                                       item_type='HANADataBase', item_id=item_id_hana, backup_entity_friendly_name=backup_entity_friendly_name_hana):

        wl_help.test_backup_wl_protection(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                          workload_type, subscription, item1, id, item_type, item_id, backup_entity_friendly_name)

    def test_backup_wl_sql_auto_protection(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                           resource_group=rg_sql, vault_name=vault_sql, policy_name='HourlyLogBackup',
                                           workload_type='MSSQL', subscription=sub_sql, item1=item_auto_sql, id=id_sql, item_type='SQLInstance',
                                           item_id=item_id_sql, backup_entity_friendly_name=backup_entity_friendly_name_sql):

        wl_help.test_backup_wl_auto_protection(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                               workload_type, subscription, item1, id, item_type, item_id, backup_entity_friendly_name)

    def test_backup_wl_hana_restore(self, container_name1=container_hana, container_name2=container_friendly_hana,
                                    resource_group=rg_hana, vault_name=vault_hana, policy_name='HourlyLogBackup',
                                    workload_type='SAPHANA', subscription=sub_hana, item1=item1_hana, id=id_hana,
                                    item_type='HANADataBase', item_id=item_id_hana, backup_entity_friendly_name=backup_entity_friendly_name_hana,
                                    target_type='HANAInstance', target_item='H22'):

        wl_help.test_backup_wl_restore(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                       workload_type, subscription, item1, id, item_type, item_id, backup_entity_friendly_name, target_type,
                                       target_item)

    def test_backup_wl_sql_restore(self, container_name1=container_sql, container_name2=container_friendly_sql,
                                   resource_group=rg_sql, vault_name=vault_sql, policy_name='HourlyLogBackup',
                                   workload_type='MSSQL', subscription=sub_sql, item1=item1_sql, id=id_sql, item_type='SQLDataBase',
                                   item_id=item_id_sql, backup_entity_friendly_name=backup_entity_friendly_name_sql, target_type='SQLInstance',
                                   target_item='MSSQLSERVER'):

        wl_help.test_backup_wl_restore(self, container_name1, container_name2, resource_group, vault_name, policy_name,
                                       workload_type, subscription, item1, id, item_type, item_id, backup_entity_friendly_name, target_type,
                                       target_item)

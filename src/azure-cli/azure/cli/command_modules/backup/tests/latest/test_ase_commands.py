
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, record_only
import json
import os

vault_ase_reg = 'ase-rsv-ccy'
vault_ase_restore = 'ase-rsv-grs'
reg_vm_name_ase = 'VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm2'
res_vm_name_ase = 'VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm5'
reg_vm_friendly_name = 'ase-ccy-vm2'
res_vm_friendly_name = 'ase-ccy-vm5'
vm5_friendly_name = 'ase-ccy-vm5'
rg_ase = 'ase-rg-ccy'
item_friendly_name = 'asetestdb1'
backup_item_name_db1 = 'SAPAseDatabase;ab4;asetestdb1'
backup_item_name_db2 = 'SAPAseDatabase;ab4;asetestdb2'
reg_vm_id = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/ase-rg-ccy/providers/Microsoft.Compute/virtualMachines/ase-ccy-vm2'

# reg_vm_id = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/ASE-RG-CCY/providers/Microsoft.Compute/virtualMachines/ase-ccy-vm2'
# sub_ase = '38304e13-357e-405e-9e9a-220351dcce8c'
# server_friendly_name = 'ase-ccy-vm2'
# item_name = 'SAPAseDatabase;ab4;asetestdb2'


class ASEBackupTests(ScenarioTest, unittest.TestCase):

    def test_backup_wl_ase_container(self):
        self.kwargs.update({
            'vault': vault_ase_restore,
            'vm_full_name': res_vm_name_ase,
            'vm_friendly_name': res_vm_friendly_name,
            'rg': rg_ase,
            'backup_item_friendly_name': item_friendly_name,
            'backup_item_protection_state': 'Protected',
            'backup_policy': 'DailyPolicy-ma2c99lv',
            'policy_new': self.create_random_name('clitest-policy', 24),
            'reg_vm_id': reg_vm_id,
        })

        # az backup container show -n VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm5 -v ase-rsv-grs -g ase-rg-ccy --backup-management-type AzureWorkload
        self.kwargs['container'] = self.cmd('backup container show -n {vm_full_name} -v {vault} -g {rg} --backup-management-type AzureWorkload', checks = [
            self.check('name', '{vm_full_name}'),
            self.check('properties.friendlyName', '{vm_friendly_name}')
        ]).get_output_in_json()

        # az backup container list --backup-management-type AzureWorkload -v ase-rsv-grs -g ase-rg-ccy
        self.cmd('backup container list --backup-management-type AzureWorkload -v {vault} -g {rg}', checks=[
            self.check("length(@)", 2)
        ])
        
        # az backup item show --backup-management-type AzureWorkload -g ase-rg-ccy -v ase-rsv-grs -c VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm5 -n SAPAseDatabase;ab4;asetestdb1
        self.cmd('backup item show --backup-management-type AzureWorkload -g {rg} -v {vault} -c {vm_full_name} -n {backup_item_friendly_name}', checks=[
            self.check("properties.friendlyName", '{backup_item_friendly_name}'),
            self.check("properties.protectionState", '{backup_item_protection_state}'),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.isScheduledForDeferredDelete", None)
        ])

        # backup policy create
        # az backup policy show -g ase-rg-ccy -v ase-rsv-grs -n DailyPolicy-ma2c99lv
        self.kwargs['policy1_json'] = self.cmd('backup policy show -g {rg} -v {vault} -n {backup_policy}', checks=[
            self.check('name', '{backup_policy}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.kwargs['policy_json'] = json.dumps(self.kwargs['policy1_json'], separators=(',', ':')).replace('\'', '\\\'').replace('"', '\\"')

        self.cmd("backup policy create -g {rg} -v {vault} --policy {policy_json} --backup-management-type AzureWorkload --workload-type SAPAseDatabase --name {policy_new}", checks=[
            self.check('name', '{policy_new}'),
            self.check('resourceGroup', '{rg}')
        ])
        
        # backup policy delete
        self.cmd('backup policy delete -g {rg} -v {vault} -n {policy_new}')

        # az backup policy list -g ase-rg-ccy -v ase-rsv-grs --workload-type SAPAseDatabase
        self.cmd('backup policy list -g {rg} -v {vault}  --workload-type SAPAseDatabase', checks=[
            self.check("length([?name == '{backup_policy}'])", 1)
        ])

    def test_bkp_res_ase(self):
        self.kwargs.update({
            'rg': rg_ase,
            'vault': vault_ase_restore,
            'backup_item_name_db1': backup_item_name_db1,
            'backup_item_name_db2': backup_item_name_db2,
            'vm5_friendly_name': vm5_friendly_name,
            'vm5_full_name': 'VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm5',
            'name' : vm5_friendly_name

            # 'container': "VMAppContainer;Compute;ArchiveResourceGroup;ArchHanaVM1"
        })

        self.cmd('backup protection backup-now -g {rg} -v {vault} -c {vm5_friendly_name} -i {backup_item_name_db1} --backup-type Full  --enable-compression false --backup-management-type AzureWorkload')

        # az backup recoverypoint list --backup-management-type AzureWorkload --workload-type SAPAseDatabase -g ase-rg-ccy -v ase-rsv-grs -c ase-ccy-vm5 -i SAPAseDatabase;ab4;asetestdb2
        # rp_names = self.cmd('backup recoverypoint list --backup-management-type AzureWorkload --workload-type SAPAseDatabase -g {rg} -v {vault} -c {vm5_friendly_name} -i SAPAseDatabase;ab4;asetestdb2', checks=[
        # ]).get_output_in_json()

        self.kwargs['rp'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {backup_item_name_db1} --workload-type SAPAseDatabase --backup-management-type AzureWorkload --query [0]').get_output_in_json()
        # az backup recoverypoint list -g ase-rg-ccy -v ase-rsv-grs -c ase-ccy-vm5 -i SAPAseDatabase;ab4;asetestdb1 --workload-type SAPAseDatabase --backup-management-type AzureWorkload

        self.kwargs['rp'] = self.kwargs['rp']['name']

        # az backup container show -n VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm5 -v ase-rsv-grs -g ase-rg-ccy  --backup-management-type AzureWorkload --query name

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --rp-name {rp} --item-name {backup_item_name_db1} --container-name {vm5_full_name}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_ase_restore.json", "w") as f:
            f.write(self.kwargs['rc'])
        # OLR : az backup recoveryconfig show --vault-name ase-rsv-grs -g ase-rg-ccy --restore-mode OriginalWorkloadRestore --rp-name DefaultRangeRecoveryPoint --item-name SAPAseDatabase;ab4;asetestdb1 --container-name VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm5

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_ase_restore.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

    def test_registration_ase_container(self):
        self.kwargs.update({
            'vault': vault_ase_reg,
            'vm': reg_vm_friendly_name,
            'rg': rg_ase,
            'reg_vm_id': reg_vm_id,
        })

        self.cmd('backup container register -v {vault} -g {rg} --workload-type SAPAseDatabase --backup-management-type AzureWorkload --resource-id {reg_vm_id}')

        # configure protection
        # stop protection

        # self.cmd('backup container unregister -v {vault} -g {rg} -c {vm} --backup-management-type AzureWorkload -y')
        # az backup container unregister -v ase-rsv-ccy -g ase-rg-ccy -c ase-ccy-vm2 --backup-management-type AzureWorkload -y
        # az backup container unregister -v ase-rsv-ccy -g ase-rg-ccy -c VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm2
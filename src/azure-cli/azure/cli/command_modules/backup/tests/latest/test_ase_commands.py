
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, record_only
import json
import os

vault_ase_olr = 'ase-rsv-ccy'
vault_ase_crr = 'ase-rsv-grs'
container_name_ase = 'VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm2'
vm2_friendly_name = 'ase-ccy-vm2'
vm5_friendly_name = 'ase-ccy-vm5'
rg_ase = 'ase-rg-ccy'
item_friendly_name = 'asetestdb1'
backup_item_name_db1 = 'SAPAseDatabase;ab4;asetestdb1'
backup_item_name_db2 = 'SAPAseDatabase;ab4;asetestdb2'
id_ase = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/ASE-RG-CCY/providers/Microsoft.Compute/virtualMachines/ase-ccy-vm5'

# id_ase = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/ASE-RG-CCY/providers/Microsoft.Compute/virtualMachines/ase-ccy-vm2'
# sub_ase = '38304e13-357e-405e-9e9a-220351dcce8c'
# server_friendly_name = 'ase-ccy-vm2'
# item_name = 'SAPAseDatabase;ab4;asetestdb2'


class ASEBackupTests(ScenarioTest, unittest.TestCase):

    def test_backup_wl_ase_container(self):
        self.kwargs.update({
            'vault': vault_ase_olr,
            'vm': container_name_ase,
            'vm2_friendly_name': vm2_friendly_name,
            'vm5_friendly_name': vm5_friendly_name,
            'rg': rg_ase,
            'backup_item_friendly_name': item_friendly_name,
            'backup_item_protection_state': 'IRPending',
            'default': 'DefaultPolicy',
            'enhanced': 'EnhancedPolicy',
            'id_ase': id_ase,
        })

        self.kwargs['container'] = self.cmd('backup container show -n {vm} -v {vault} -g {rg} --backup-management-type AzureIaasVM', checks = [
            self.check('name', '{vm}'),
            self.check('properties.friendlyName', '{vm2_friendly_name}')
        ]).get_output_in_json()

        self.cmd('backup container list --backup-management-type AzureIaasVM -v {vault} -g {rg}', checks=[
            self.check("length(@)", 0),
            # self.check("length([?properties.friendlyName == '{vm1}'])", 1),
            # self.check("length([?properties.friendlyName == '{vm2}'])", 1)
        ])

        self.cmd('backup item show --backup-management-type AzureWorkload -g {rg} -v {vault} -c {vm} -n {backup_item_friendly_name}', checks=[
            self.check("properties.friendlyName", '{backup_item_friendly_name}'),
            self.check("properties.protectionState", '{backup_item_protection_state}'),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.isScheduledForDeferredDelete", None)
        ])

        self.cmd('backup policy list -g {rg} -v {vault}  --workload-type SAPAseDatabase', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{enhanced}'])", 1)
        ])

    def test_bkp_res_ase(self):
        self.kwargs.update({
            'rg': rg_ase,
            'vault': vault_ase_crr,
            'backup_item_name_db1': backup_item_name_db1,
            'backup_item_name_db2': backup_item_name_db2,
            # 'target_item_name': vm2_friendly_name,
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
            'vault': vault_ase_olr,
            'vm5_friendly_name': vm5_friendly_name,
            'rg': rg_ase,
            'id_ase': id_ase,
        })

        self.cmd('backup container register -v {vault} -g {rg} --workload-type SAPAseDatabase --backup-management-type AzureWorkload --resource-id {id_ase}')

        self.cmd('backup container unregister -v {vault} -g {rg} -c {vm5_friendly_name} --backup-management-type AzureWorkload -y')
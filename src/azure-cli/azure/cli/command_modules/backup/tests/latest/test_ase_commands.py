
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, record_only
import json
import os

vault_ase = 'ase-rsv-ccy'
container_name_ase = 'VMAppContainer;Compute;ase-rg-ccy;ase-ccy-vm2'
container_friendly_name_ase = 'ase-ccy-vm2'
container_2_friendly_name_ase = 'ase-ccy-vm5'
rg_ase = 'ase-rg-ccy'
item_friendly_name = 'asetestdb1'
id_ase = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/ASE-RG-CCY/providers/Microsoft.Compute/virtualMachines/ase-ccy-vm5'

# id_ase = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/ASE-RG-CCY/providers/Microsoft.Compute/virtualMachines/ase-ccy-vm2'
# sub_ase = '38304e13-357e-405e-9e9a-220351dcce8c'
# server_friendly_name = 'ase-ccy-vm2'
# item_name = 'SAPAseDatabase;ab4;asetestdb2'


class BackupTests(ScenarioTest, unittest.TestCase):

    def test_backup_wl_ase_container(self):
        self.kwargs.update({
            'vault': vault_ase,
            'vm': container_name_ase,
            'vm_friendly_name': container_friendly_name_ase,
            'container_2_friendly_name_ase': container_2_friendly_name_ase,
            'rg': rg_ase,
            'backup_item_friendly_name': item_friendly_name,
            'backup_item_protection_state': 'IRPending',
            'default': 'DefaultPolicy',
            'enhanced': 'EnhancedPolicy',
            'id_ase': id_ase,
        })

        self.kwargs['container'] = self.cmd('backup container show -n {vm} -v {vault} -g {rg} --backup-management-type AzureIaasVM', checks = [
            self.check('name', '{vm}'),
            self.check('properties.friendlyName', '{vm_friendly_name}')
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

        self.cmd('backup policy list -g {rg} -v {vault}', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{enhanced}'])", 1)
        ])

    def test_registration_ase_container(self):
        self.kwargs.update({
            'vault': vault_ase,
            'container_2_friendly_name_ase': container_2_friendly_name_ase,
            'rg': rg_ase,
            'id_ase': id_ase,
        })

        self.cmd('backup container register -v {vault} -g {rg} --workload-type SAPAseDatabase --backup-management-type AzureWorkload --resource-id {id_ase}')

        self.cmd('backup container unregister -v {vault} -g {rg} -c {container_2_friendly_name_ase} --backup-management-type AzureWorkload -y')
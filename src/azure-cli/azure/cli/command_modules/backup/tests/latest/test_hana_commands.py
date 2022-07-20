
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.testsdk import ScenarioTest, record_only
import json
import os


id_hana = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/saphana-clitest-rg/providers/Microsoft.Compute/virtualMachines/saphana-clitestvm-donotuse'
item_id_hana = '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourcegroups/saphana-clitest-rg/providers/Microsoft.RecoveryServices/vaults/saphana-clitestvm-donotuse/backupFabrics/Azure/protectionContainers/VMAppContainer;compute;saphana-clitest-rg;saphana-clitestvm-donotuse/protectedItems/SAPHanaDatabase;hxe;hxe'
sub_hana = '38304e13-357e-405e-9e9a-220351dcce8c'
rg_hana = 'saphana-clitest-rg'
vault_hana = 'saphana-clitestvault-donotuse'
container_hana = 'VMAppContainer;Compute;saphana-clitest-rg;saphana-clitestvm-donotuse'
container_friendly_hana = 'saphana-clitestvm-donotuse'
server_friendly_name = 'saphana-clitestvm-donotuse'
item_name = 'saphanadatabase;hxe;systemdb'
item_friendly_name = 'systemdb'

class BackupTests(ScenarioTest, unittest.TestCase):

    # SAP HANA workload tests start here
    # Please make sure you have the following setup in place before running the tests -

    # For the tests using saphana-clitestvm-donotuse and saphana-clitestvault-donotuse -
    # Each test will register the container at the start and unregister at the end of the test
    # Make sure that the container is not already registered since the start of the test

    # Note: HANA Archive test uses different subscription. Please comment them out when running the whole test suite at once. And run those tests individually.

    @record_only()
    def test_backup_wl_hana_archive (self):
        self.kwargs.update({
            'vault': "archiveccyvault1",
            'rg': "ArchiveResourceGroup",
            'sub': "AzureBackup_Functional_Testing",
            'item': "SAPHanaDatabase;h15;systemdb",
            'container': "VMAppContainer;Compute;ArchiveResourceGroup;ArchHanaVM1"
        })

        rp_names = self.cmd('backup recoverypoint list --backup-management-type AzureWorkload --workload-type SAPHANA -g {rg} -v {vault} -c {container} -i {item}', checks=[
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
                self.check("properties.entityFriendlyName", 'systemdb [BVTD2HSuse15]'),
                self.check("resourceGroup", '{rg}'),
                self.check("properties.operation", "MoveRecoveryPoint"),
                self.check("properties.status", "Completed")
            ])
        
        is_restorable = False
        for i in rp_names:
            if i['tierType']=="VaultArchive":
                self.kwargs['rp_restore'] = i['name']
                is_restorable = True
                break
        
        if is_restorable:
            # # Integrated Restore
            self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --item-name {item} --container-name {container} --rp-name {rp_restore}').get_output_in_json(), separators=(',', ':'))
            with open("recoveryconfig_hana_archive.json", "w") as f:
                f.write(self.kwargs['rc'])

            # # Trigger Restore
            self.cmd('backup restore restore-azurewl -g {rg} -v {vault} --recovery-config recoveryconfig_hana_archive.json --rehydration-priority High', checks=[
                self.check("properties.operation", "RestoreWithRehydrate"),
                self.check("properties.status", "InProgress"),
                self.check("resourceGroup", '{rg}')
            ]).get_output_in_json()

    @record_only()
    def test_backup_wl_hana_container(self):

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
    def test_backup_wl_hana_policy(self):

        self.kwargs.update({
            'vault': vault_hana,
            'policy': 'saphana-clitestpolicy-donotuse',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'saphana-clitestpolicy-donotuse',
            'rg': rg_hana,
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
    def test_backup_wl_hana_item(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': server_friendly_name,
            'policy': 'saphana-clitestpolicy-donotuse',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'saphana-clitestpolicy-donotuse',
            'rg': rg_hana,
            'item': item_name,
            'fitem': item_friendly_name,
            'id': id_hana,
            'pit': 'SAPHanaDatabase'
        })
        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

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
            self.check("length(@)", 1),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} -c {container1_fullname} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("length(@)", 1),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item list -g {rg} -v {vault} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("length(@)", 1),
            self.check("length([?properties.friendlyName == '{fitem}'])", 1)
        ])

        self.cmd('backup item set-policy -g {rg} -v {vault} -c {container1} -n {item1_fullname} -p {policy} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        item1_json = self.cmd('backup item show -g {rg} -v {vault} -c {container1} -n {item} --backup-management-type AzureWorkload --workload-type SAPHanaDatabase').get_output_in_json()
        self.assertIn("saphana-clitestpolicy-donotuse".lower(), item1_json['properties']['policyId'].lower())

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_hana_protectable_item(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': server_friendly_name,
            'policy': 'saphana-clitestpolicy-donotuse',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'saphana-clitestpolicy-donotuse',
            'rg': rg_hana,
            'id': id_hana,
            'pit': 'SAPHanaDatabase',
            'protectable_item_name': 'SYSTEMDB',
            'pit_hana': 'SAPHanaDatabase'
        })

        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --query properties.friendlyName --backup-management-type AzureWorkload').get_output_in_json()

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
    def test_backup_wl_hana_rp(self):

        resource_group = rg_hana.lower()
        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'rg': resource_group,
            'fname': server_friendly_name,
            'policy': 'saphana-clitestpolicy-donotuse',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'item': item_name,
            'pit': "SAPHanaDatabase",
            'id': id_hana,
            'fitem': item_friendly_name,
        })
        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt} --query [].name', checks=[
            self.check("length(@)", 1)
        ])

        rp1_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_hana.lower(), rp1_json[0]['id'].lower())
        self.assertIn(container_hana.lower(), rp1_json[0]['id'].lower())

        rp2_json = self.cmd('backup recoverypoint show-log-chain -g {rg} -v {vault} -c {name} -i {item} --workload-type {wt}').get_output_in_json()
        self.assertIn(vault_hana.lower(), rp2_json[0]['id'].lower())
        self.assertIn(container_hana.lower(), rp2_json[0]['id'].lower())

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_hana_protection(self):

        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': server_friendly_name,
            'policy': 'saphana-clitestpolicy-donotuse',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'saphana-clitestpolicy-donotuse',
            'rg': rg_hana,
            'item': item_name,
            'fitem': item_friendly_name,
            'id': id_hana,
            'pit': "SAPHanaDatabase",
            'entityFriendlyName': 'SYSTEMDB [saphana-clitestvm-donotuse]'
        })
        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl -v {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -i {item} -c {name} --backup-type Full --enable-compression false', checks=[
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.assertIn(self.kwargs['fitem'], self.kwargs['backup_job']['properties']['entityFriendlyName'].lower())
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

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])

    @record_only()
    def test_backup_wl_hana_restore(self):

        resource_group = rg_hana.lower()
        self.kwargs.update({
            'vault': vault_hana,
            'name': container_hana,
            'fname': server_friendly_name,
            'policy': 'saphana-clitestpolicy-donotuse',
            'wt': 'SAPHANA',
            'sub': sub_hana,
            'default': 'saphana-clitestpolicy-donotuse',
            'rg': resource_group,
            'item': item_name,
            'fitem': item_friendly_name,
            'id': id_hana,
            'pit': 'SAPHanaDatabase',
            'tpit': 'HANAInstance',
            'titem': 'HDB'
        })
        self.cmd('backup container register -v {vault} -g {rg} --backup-management-type AzureWorkload --workload-type {wt} --resource-id {id}')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 1)])

        self.cmd('backup protection enable-for-azurewl --vault-name {vault} -g {rg} -p {policy} --protectable-item-type {pit} --protectable-item-name {item} --server-name {fname} --workload-type {wt}', checks=[
            self.check("properties.entityFriendlyName", '{fitem}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.kwargs['container1'] = self.cmd('backup container show -n {name} -v {vault} -g {rg} --backup-management-type AzureWorkload --query name').get_output_in_json()

        self.kwargs['backup_job'] = self.cmd('backup protection backup-now -v {vault} -g {rg} -c {name} -i {item} --backup-type Full --enable-compression false', checks=[
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

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode AlternateWorkloadRestore --rp-name {rp} --item-name {item} --container-name {container1} --target-item-name {titem} --target-server-type {tpit} --target-server-name {fname} --workload-type {wt}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_hana_restore.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_hana_restore.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        self.kwargs['job'] = self.kwargs['backup_job']['name']

        self.cmd('backup job wait -v {vault} -g {rg} -n {job}')

        self.kwargs['rc'] = json.dumps(self.cmd('backup recoveryconfig show --vault-name {vault} -g {rg} --restore-mode OriginalWorkloadRestore --item-name {item} --container-name {container1} --rp-name {rp}').get_output_in_json(), separators=(',', ':'))
        with open("recoveryconfig_hana_restore.json", "w") as f:
            f.write(self.kwargs['rc'])

        self.kwargs['backup_job'] = self.cmd('backup restore restore-azurewl --vault-name {vault} -g {rg} --recovery-config recoveryconfig_hana_restore.json', checks=[
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

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

        self.cmd('backup protection disable -v {vault} -g {rg} -c {container1} --backup-management-type AzureWorkload --workload-type {wt} -i {item} -y --delete-backup-data true')

        self.cmd('backup container unregister -v {vault} -g {rg} -c {name} -y')

        self.cmd('backup container list -v {vault} -g {rg} --backup-management-type AzureWorkload', checks=[
            self.check("length([?name == '{name}'])", 0)])
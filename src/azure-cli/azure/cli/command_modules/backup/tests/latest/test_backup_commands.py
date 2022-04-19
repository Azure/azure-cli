# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from datetime import datetime, timedelta
import unittest
import time

from azure.cli.testsdk import ScenarioTest, JMESPathCheckExists, ResourceGroupPreparer, \
    StorageAccountPreparer, KeyVaultPreparer, record_only
from azure.mgmt.recoveryservicesbackup.activestamp.models import StorageType
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from .preparers import VaultPreparer, VMPreparer, ItemPreparer, PolicyPreparer, RPPreparer


def _get_vm_version(vm_type):
    if vm_type == 'Microsoft.Compute/virtualMachines':
        return 'Compute'
    elif vm_type == 'Microsoft.ClassicCompute/virtualMachines':
        return 'Classic'


class BackupTests(ScenarioTest, unittest.TestCase):
    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @StorageAccountPreparer(location="southeastasia")
    def test_backup_scenario(self, resource_group, vault_name, vm_name, storage_account):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name
        })

        # Enable Protection
        self.cmd('backup protection enable-for-vm -g {rg} -v {vault} --vm {vm} -p DefaultPolicy').get_output_in_json()

        # Get Container
        self.kwargs['container'] = self.cmd('backup container show -n {vm} -v {vault} -g {rg} --backup-management-type AzureIaasVM --query properties.friendlyName').get_output_in_json()

        # Get Item
        self.kwargs['item'] = self.cmd('backup item list -g {rg} -v {vault} -c {container} --backup-management-type AzureIaasVM --workload-type VM --query [0].properties.friendlyName').get_output_in_json()

        # Trigger Backup
        self.kwargs['retain_date'] = (datetime.utcnow() + timedelta(days=30)).strftime('%d-%m-%Y')
        self.kwargs['job'] = self.cmd('backup protection backup-now -g {rg} -v {vault} -c {container} -i {item} --backup-management-type AzureIaasVM --workload-type VM --retain-until {retain_date} --query name').get_output_in_json()
        self.cmd('backup job wait -g {rg} -v {vault} -n {job}')

        # Get Recovery Point
        self.kwargs['recovery_point'] = self.cmd('backup recoverypoint list -g {rg} -v {vault} -c {container} -i {item} --backup-management-type AzureIaasVM --workload-type VM --query [0].name').get_output_in_json()

        # Trigger Restore
        self.kwargs['job'] = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {container} -i {item} -r {recovery_point} --storage-account {sa} --query name --restore-to-staging-storage-account').get_output_in_json()
        self.cmd('backup job wait -g {rg} -v {vault} -n {job}')

        # Disable protection with retain data
        self.cmd('backup protection disable -g {rg} -v {vault} -c {container} -i {item} --backup-management-type AzureIaasVM --workload-type VM --yes')

        # Resume protection
        self.cmd('backup protection resume -g {rg} -v {vault} -c {container} -i {item} --policy-name DefaultPolicy --backup-management-type AzureIaasVM', checks=[
            self.check("properties.entityFriendlyName", '{item}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        # Disable Protection with delete data
        self.cmd('backup protection disable -g {rg} -v {vault} -c {container} -i {item} --backup-management-type AzureIaasVM --workload-type VM --delete-backup-data true --yes')

    @AllowLargeResponse()
    @ResourceGroupPreparer(location="eastasia")
    @VaultPreparer(parameter_name='vault1')
    @VaultPreparer(parameter_name='vault2')
    def test_backup_vault(self, resource_group, resource_group_location, vault1, vault2):

        self.kwargs.update({
            'loc': resource_group_location,
            'vault1': vault1,
            'vault2': vault2
        })

        self.kwargs['vault3'] = self.create_random_name('clitest-vault', 50)
        self.cmd('backup vault create -n {vault3} -g {rg} -l {loc}', checks=[
            self.check('name', '{vault3}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', '{loc}'),
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.kwargs['vault4'] = self.create_random_name('clitest-vault', 50)
        self.cmd('backup vault create -n {vault4} -g {rg} -l {loc}', checks=[
            self.check('name', '{vault4}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', '{loc}'),
            self.check('properties.provisioningState', 'Succeeded')
        ])

        number_of_test_vaults = 4

        self.cmd('backup vault list', checks=[
            self.check("length([?resourceGroup == '{rg}'])", number_of_test_vaults),
            self.check("length([?name == '{vault1}'])", 1),
            self.check("length([?name == '{vault2}'])", 1),
            self.check("length([?name == '{vault3}'])", 1),
            self.check("length([?name == '{vault4}'])", 1)
        ])

        self.cmd('backup vault list -g {rg}', checks=[
            self.check("length(@)", number_of_test_vaults),
            self.check("length([?name == '{vault1}'])", 1),
            self.check("length([?name == '{vault2}'])", 1),
            self.check("length([?name == '{vault3}'])", 1),
            self.check("length([?name == '{vault4}'])", 1)
        ])

        storage_model_types = [e.value for e in StorageType]
        vault_properties = self.cmd('backup vault backup-properties show -n {vault1} -g {rg} --query [0]', checks=[
            JMESPathCheckExists("contains({}, properties.storageModelType)".format(storage_model_types)),
            self.check('properties.storageTypeState', 'Unlocked'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        if vault_properties['properties']['storageModelType'] == StorageType.geo_redundant.value:
            new_storage_model = StorageType.locally_redundant.value
        else:
            new_storage_model = StorageType.geo_redundant.value

        self.kwargs['model'] = new_storage_model
        self.cmd('backup vault backup-properties set -n {vault1} -g {rg} --backup-storage-redundancy {model}')
        time.sleep(300)
        self.cmd('backup vault backup-properties show -n {vault1} -g {rg} --query [0]', checks=[
            self.check('properties.storageModelType', new_storage_model)
        ])

        new_storage_model = StorageType.zone_redundant.value
        self.kwargs['model'] = StorageType.zone_redundant.value
        self.cmd('backup vault backup-properties set -n {vault1} -g {rg} --backup-storage-redundancy {model}')
        time.sleep(300)
        self.cmd('backup vault backup-properties show -n {vault1} -g {rg} --query [0]', checks=[
            self.check('properties.storageModelType', new_storage_model)
        ])

        self.cmd('backup vault delete -n {vault4} -g {rg} -y')

        self.cmd('backup vault list', checks=[
            self.check("length([?resourceGroup == '{rg}'])", number_of_test_vaults - 1),
            self.check("length([?name == '{vault1}'])", 1),
            self.check("length([?name == '{vault2}'])", 1),
            self.check("length([?name == '{vault3}'])", 1)
        ])

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer(parameter_name='vm1')
    @VMPreparer(parameter_name='vm2')
    @ItemPreparer(vm_parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm2')
    def test_backup_container(self, resource_group, vault_name, vm1, vm2):

        self.kwargs.update({
            'vault': vault_name,
            'vm1': vm1,
            'vm2': vm2
        })

        container_json = self.cmd('backup container show --backup-management-type AzureIaasVM -n {vm1} -v {vault} -g {rg}', checks=[
            self.check('properties.friendlyName', '{vm1}'),
            self.check('properties.healthStatus', 'Healthy'),
            self.check('properties.registrationStatus', 'Registered'),
            self.check('properties.resourceGroup', '{rg}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        vm1_json = self.cmd('vm show -n {vm1} -g {rg}').get_output_in_json()

        self.assertIn(vault_name.lower(), container_json['id'].lower())
        self.assertIn(vm1.lower(), container_json['name'].lower())
        self.assertIn(vm1.lower(), container_json['properties']['virtualMachineId'].lower())
        self.assertEqual(container_json['properties']['virtualMachineVersion'], _get_vm_version(vm1_json['type']))

        self.cmd('backup container list --backup-management-type AzureIaasVM -v {vault} -g {rg}', checks=[
            self.check("length(@)", 2),
            self.check("length([?properties.friendlyName == '{vm1}'])", 1),
            self.check("length([?properties.friendlyName == '{vm2}'])", 1)])

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @PolicyPreparer(parameter_name='policy1')
    @PolicyPreparer(parameter_name='policy2', instant_rp_days="3")
    @VMPreparer(parameter_name='vm1')
    @VMPreparer(parameter_name='vm2')
    @ItemPreparer(vm_parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm2')
    def test_backup_policy(self, resource_group, vault_name, policy1, policy2, vm1, vm2):

        self.kwargs.update({
            'policy1': policy1,
            'policy2': policy2,
            'policy3': self.create_random_name('clitest-policy', 24),
            'default': 'DefaultPolicy',
            'enhanced': 'EnhancedPolicy',
            'vault': vault_name,
            'vm1': vm1,
            'vm2': vm2,
            'policy5': self.create_random_name('clitest-policy5', 24),
            'enhpolicy': self.create_random_name('clitest-enhpolicy', 24),
        })

        self.kwargs['policy1_json'] = self.cmd('backup policy show -g {rg} -v {vault} -n {policy1}', checks=[
            self.check('name', '{policy1}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.kwargs['enhpolicy_json'] = self.cmd('backup policy show -g {rg} -v {vault} -n {enhanced}', checks=[
            self.check('name', '{enhanced}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.cmd('backup policy list -g {rg} -v {vault}', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{enhanced}'])", 1),
            self.check("length([?name == '{policy1}'])", 1),
            self.check("length([?name == '{policy2}'])", 1)
        ])

        self.cmd('backup policy list -g {rg} -v {vault} --policy-sub-type Enhanced', checks=[
            self.check("length(@)", 1),
            self.check("length([?name == '{enhanced}'])", 1)
        ])

        self.cmd('backup policy list-associated-items -g {rg} -v {vault} -n {default}', checks=[
            self.check("length(@)", 2),
            self.check("length([?properties.friendlyName == '{}'])".format(vm1), 1),
            self.check("length([?properties.friendlyName == '{}'])".format(vm2), 1)
        ])

        self.kwargs['policy1_json']['name'] = self.kwargs['policy5']
        self.kwargs['backup-management-type'] = self.kwargs['policy1_json']['properties']['backupManagementType']
        self.kwargs['policy5_json'] = json.dumps(self.kwargs['policy1_json'])
        self.cmd("backup policy create --backup-management-type {backup-management-type} -g {rg} -v {vault} -n {policy5} --policy '{policy5_json}'")

        self.kwargs['enhpolicy_json']['name'] = self.kwargs['enhpolicy']
        self.kwargs['backup-management-type'] = self.kwargs['enhpolicy_json']['properties']['backupManagementType']
        self.kwargs['enhpolicy_json'] = json.dumps(self.kwargs['enhpolicy_json'])
        self.cmd("backup policy create --backup-management-type {backup-management-type} -g {rg} -v {vault} -n {enhpolicy} --policy '{enhpolicy_json}'", checks=[
            self.check('properties.schedulePolicy.scheduleRunFrequency', 'Hourly')
        ])

        self.cmd('backup policy delete -g {rg} -v {vault} -n {policy5}')
        self.cmd('backup policy delete -g {rg} -v {vault} -n {enhpolicy}')

        self.kwargs['policy1_json']['name'] = self.kwargs['policy3']
        if 'instantRpDetails' in self.kwargs['policy1_json']['properties']:
            self.kwargs['policy1_json']['properties']['instantRpDetails'] = {'azureBackupRgNamePrefix': 'RG_prefix', 'azureBackupRgNameSuffix': 'RG_suffix'}
        self.kwargs['policy1_json'] = json.dumps(self.kwargs['policy1_json'])

        self.cmd("backup policy set -g {rg} -v {vault} --policy '{policy1_json}'", checks=[
            self.check('name', '{policy3}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup policy list -g {rg} -v {vault}', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{policy1}'])", 1),
            self.check("length([?name == '{policy2}'])", 1),
            self.check("length([?name == '{policy3}'])", 1)
        ])

        self.cmd('backup policy delete -g {rg} -v {vault} -n {policy3}')

        self.cmd('backup policy list -g {rg} -v {vault}', checks=[
            self.check("length([?name == '{default}'])", 1),
            self.check("length([?name == '{policy1}'])", 1),
            self.check("length([?name == '{policy2}'])", 1)
        ])

        self.kwargs['policy4_json'] = self.cmd('backup policy show -g {rg} -v {vault} -n {policy2}').get_output_in_json()
        self.assertEqual(self.kwargs['policy4_json']['properties']['instantRpRetentionRangeInDays'], 3)

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer(parameter_name='vm1')
    @VMPreparer(parameter_name='vm2')
    @ItemPreparer(vm_parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm2')
    @PolicyPreparer()
    def test_backup_item(self, resource_group, vault_name, vm1, vm2, policy_name):

        self.kwargs.update({
            'vault': vault_name,
            'vm1': vm1,
            'vm2': vm2,
            'policy': policy_name,
            'default': 'DefaultPolicy'
        })
        self.kwargs['container1'] = self.cmd('backup container show --backup-management-type AzureIaasVM -n {vm1} -v {vault} -g {rg} --query properties.friendlyName').get_output_in_json()
        self.kwargs['container2'] = self.cmd('backup container show --backup-management-type AzureIaasVM -n {vm2} -v {vault} -g {rg} --query properties.friendlyName').get_output_in_json()

        item1_json = self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container1} -n {vm1}', checks=[
            self.check('properties.friendlyName', '{vm1}'),
            self.check('properties.healthStatus', 'Passed'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.assertIn(vault_name.lower(), item1_json['id'].lower())
        self.assertIn(vm1.lower(), item1_json['name'].lower())
        self.assertIn(vm1.lower(), item1_json['properties']['sourceResourceId'].lower())
        self.assertIn(vm1.lower(), item1_json['properties']['virtualMachineId'].lower())
        self.assertIn(self.kwargs['default'].lower(), item1_json['properties']['policyId'].lower())

        self.kwargs['container1_fullname'] = self.cmd('backup container show --backup-management-type AzureIaasVM -n {vm1} -v {vault} -g {rg} --query name').get_output_in_json()

        self.cmd('backup item show --workload-type VM -g {rg} -v {vault} -c {container1_fullname} -n {vm1}', checks=[
            self.check('properties.friendlyName', '{vm1}'),
            self.check('properties.healthStatus', 'Passed'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.kwargs['item1_fullname'] = item1_json['name']

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container1_fullname} -n {item1_fullname}', checks=[
            self.check('properties.friendlyName', '{vm1}'),
            self.check('properties.healthStatus', 'Passed'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('backup item list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container1}', checks=[
            self.check("length(@)", 1),
            self.check("length([?properties.friendlyName == '{vm1}'])", 1)
        ])

        self.cmd('backup item list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container1_fullname}', checks=[
            self.check("length(@)", 1),
            self.check("length([?properties.friendlyName == '{vm1}'])", 1)
        ])

        self.cmd('backup item list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container2}', checks=[
            self.check("length(@)", 1),
            self.check("length([?properties.friendlyName == '{vm2}'])", 1)
        ])

        self.cmd('backup item list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault}', checks=[
            self.check("length(@)", 2),
            self.check("length([?properties.friendlyName == '{vm1}'])", 1),
            self.check("length([?properties.friendlyName == '{vm2}'])", 1)
        ])

        self.cmd('backup item set-policy --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container1} -n {vm1} -p {policy}', checks=[
            self.check("properties.entityFriendlyName", '{vm1}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        item1_json = self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container1} -n {vm1}').get_output_in_json()
        self.assertIn(policy_name.lower(), item1_json['properties']['policyId'].lower())

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    def test_backup_rp(self, resource_group, vault_name, vm_name):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name
        })

        rp_names = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --query [].name', checks=[
            self.check("length(@)", 1)
        ]).get_output_in_json()

        self.kwargs['rp1'] = rp_names[0]
        rp1_json = self.cmd('backup recoverypoint show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} -n {rp1}', checks=[
            self.check("name", '{rp1}'),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.assertIn(vault_name.lower(), rp1_json['id'].lower())
        self.assertIn(vm_name.lower(), rp1_json['id'].lower())

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    def test_backup_protection(self, resource_group, vault_name, vm_name):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name
        })

        self.kwargs['vm_id'] = self.cmd('vm show -g {rg} -n {vm} --query id').get_output_in_json()

        protection_check = self.cmd('backup protection check-vm --vm-id {vm_id}').output
        self.assertTrue(protection_check == '')

        self.cmd('backup protection enable-for-vm -g {rg} -v {vault} --vm {vm} -p DefaultPolicy', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        vault_id = self.cmd('backup vault show -g {rg} -n {vault} --query id').get_output_in_json()

        vault_id_check = self.cmd('backup protection check-vm --vm-id {vm_id}').get_output_in_json()
        self.assertIsNotNone(vault_id_check)
        self.assertTrue(vault_id.lower() == vault_id_check.lower())

        self.cmd('backup protection disable --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --yes', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "DisableBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -n {vm}', checks=[
            self.check("properties.friendlyName", '{vm}'),
            self.check("properties.protectionState", "ProtectionStopped"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup protection disable --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --delete-backup-data true --yes', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "DeleteBackupData"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup container list --backup-management-type AzureIaasVM -v {vault} -g {rg}',
                 checks=self.check("length(@)", 0))

        protection_check = self.cmd('backup protection check-vm --vm-id {vm_id}').output
        self.assertTrue(protection_check == '')

    @AllowLargeResponse()
    @ResourceGroupPreparer(location="southeastasia")
    @ResourceGroupPreparer(parameter_name="target_resource_group", location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location="southeastasia")
    def test_backup_restore(self, resource_group, target_resource_group, vault_name, vm_name, storage_account):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'target_rg': target_resource_group,
            'rg': resource_group,
            'sa': storage_account,
            'vm_id': "VM;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'container_id': "IaasVMContainer;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'vnet_name': self.create_random_name('clitest-vnet', 30),
            'subnet_name': self.create_random_name('clitest-subnet', 30),
            'target_vm_name': self.create_random_name('clitest-tvm', 15)
        })
        self.kwargs['rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --query [0].name').get_output_in_json()

        # Original Storage Account Restore Fails
        self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --storage-account {sa} --restore-to-staging-storage-account false', expect_failure=True)

        # Trigger Restore Disks
        trigger_restore_job_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} -t {target_rg} --storage-account {sa} --restore-to-staging-storage-account', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.kwargs['job'] = trigger_restore_job_json['name']
        self.cmd('backup job wait -g {rg} -v {vault} -n {job}')

        trigger_restore_job_details = self.cmd('backup job show -g {rg} -v {vault} -n {job}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()

        property_bag = trigger_restore_job_details['properties']['extendedInfo']['propertyBag']
        self.assertEqual(property_bag['Target Storage Account Name'], storage_account)

        self.kwargs['container'] = property_bag['Config Blob Container Name']
        self.kwargs['blob'] = property_bag['Config Blob Name']

        self.cmd('storage blob exists --account-name {sa} -c {container} -n {blob}',
                 checks=self.check("exists", True))

        # Trigger Restore As unmanaged disks
        trigger_restore_job2_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --restore-as-unmanaged-disks --storage-account {sa}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.kwargs['job2'] = trigger_restore_job2_json['name']
        self.cmd('backup job wait -g {rg} -v {vault} -n {job2}')

        self.cmd('backup job show -g {rg} -v {vault} -n {job2}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        # Trigger Original Location Restore
        trigger_restore_job3_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --storage-account {sa} --restore-mode OriginalLocation', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.extendedInfo.internalPropertyBag.restoreLocationType", "OriginalLocation")
        ]).get_output_in_json()
        self.kwargs['job3'] = trigger_restore_job3_json['name']
        self.cmd('backup job wait -g {rg} -v {vault} -n {job3}')

        self.cmd('backup job show -g {rg} -v {vault} -n {job3}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        # Trigger Alternate Location Restore
        vnet_json = self.cmd('network vnet create -g {target_rg} -n {vnet_name} --subnet-name {subnet_name}',
                 checks=[
            self.check("newVNet.name", '{vnet_name}')
        ]).get_output_in_json()

        self.assertIn(self.kwargs['subnet_name'].lower(), vnet_json['newVNet']['subnets'][0]['name'].lower())

        trigger_restore_job4_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --storage-account {sa} --restore-mode AlternateLocation --target-vm-name {target_vm_name} --target-vnet-name {vnet_name} --target-subnet-name {subnet_name} --target-vnet-resource-group {target_rg} -t {target_rg}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.extendedInfo.internalPropertyBag.restoreLocationType", "AlternateLocation")
        ]).get_output_in_json()
        self.kwargs['job4'] = trigger_restore_job4_json['name']
        self.cmd('backup job wait -g {rg} -v {vault} -n {job4}')

        self.cmd('backup job show -g {rg} -v {vault} -n {job4}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])


    #@AllowLargeResponse()
    #@ResourceGroupPreparer(location="centraluseuap")
    #@ResourceGroupPreparer(parameter_name="target_resource_group", location="centraluseuap")
    #@VaultPreparer(soft_delete=False)
    #@VMPreparer()
    #@ItemPreparer()
    #@RPPreparer()
    #@StorageAccountPreparer(parameter_name="secondary_region_sa", location="eastus2euap")
    #def test_backup_crr(self, resource_group, target_resource_group, vault_name, vm_name, secondary_region_sa):

    #    self.kwargs.update({
    #        'vault': vault_name,
    #        'vm': vm_name,
    #        'target_rg': target_resource_group,
    #        'rg': resource_group,
    #        'secondary_sa': secondary_region_sa,
    #        'vm_id': "VM;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
    #        'container_id': "IaasVMContainer;iaasvmcontainerv2;" + resource_group + ";" + vm_name
    #    })
    #    self.cmd('backup vault backup-properties set -g {rg} -n {vault} --cross-region-restore-flag true', checks=[
    #        self.check("properties.crossRegionRestoreFlag", True)
    #    ]).get_output_in_json()
    #    time.sleep(300)

    #    # Trigger Cross Region Restore
    #    self.kwargs['crr_rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container_id} -i {vm_id} --use-secondary-region --query [0].name').get_output_in_json()

    #    trigger_restore_job3_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {container_id} -i {vm_id} -r {crr_rp} --storage-account {secondary_sa} -t {target_rg} --use-secondary-region', checks=[
    #        self.check("properties.entityFriendlyName", vm_name),
    #        self.check("properties.operation", "CrossRegionRestore"),
    #        self.check("properties.status", "InProgress")
    #    ]).get_output_in_json()
    #    self.kwargs['job3'] = trigger_restore_job3_json['name']

    #    self.cmd('backup job wait -g {rg} -v {vault} -n {job3} --use-secondary-region')

    #    self.cmd('backup job show -g {rg} -v {vault} -n {job3} --use-secondary-region', checks=[
    #        self.check("properties.entityFriendlyName", vm_name),
    #        self.check("properties.operation", "CrossRegionRestore"),
    #        self.check("properties.status", "Completed")
    #    ])

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location="southeastasia")
    def test_backup_job(self, resource_group, vault_name, vm_name, storage_account):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name
        })
        self.kwargs['rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --query [0].name').get_output_in_json()
        self.kwargs['job'] = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --storage-account {sa} --query name --restore-to-staging-storage-account').get_output_in_json()

        self.cmd('backup job show -g {rg} -v {vault} -n {job}', checks=[
            self.check("name", '{job}'),
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup job list -g {rg} -v {vault}',
                 checks=self.check("length([?name == '{job}'])", 1))

        self.cmd('backup job list -g {rg} -v {vault} --status InProgress',
                 checks=self.check("length([?name == '{job}'])", 1))

        self.cmd('backup job list -g {rg} -v {vault} --operation Restore',
                 checks=self.check("length([?name == '{job}'])", 1))

        self.cmd('backup job list -g {rg} -v {vault} --operation Restore --status InProgress',
                 checks=self.check("length([?name == '{job}'])", 1))

        self.cmd('backup job stop -g {rg} -v {vault} -n {job}')

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer()
    @ItemPreparer()
    def test_backup_softdelete(self, resource_group, vault_name, vm_name):
        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'rg': resource_group
        })

        self.cmd('backup protection disable --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --delete-backup-data --yes', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "DeleteBackupData"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -n {vm}', checks=[
            self.check("properties.friendlyName", '{vm}'),
            self.check("properties.protectionState", "ProtectionStopped"),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.isScheduledForDeferredDelete", True)
        ])

        self.cmd('backup protection undelete -g {rg} -v {vault} -c {vm} -i {vm} --workload-type VM --backup-management-type AzureIaasVM ', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Undelete"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup vault backup-properties set -g {rg} -n {vault} --soft-delete-feature-state Disable')

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -n {vm}', checks=[
            self.check("properties.friendlyName", '{vm}'),
            self.check("properties.protectionState", "ProtectionStopped"),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.isScheduledForDeferredDelete", None)
        ])

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @StorageAccountPreparer(location="southeastasia")
    def test_backup_disk_exclusion(self, resource_group, vault_name, vm_name, storage_account):
        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'rg': resource_group,
            'sa': storage_account
        })

        self.cmd('backup vault backup-properties set -g {rg} -n {vault} --soft-delete-feature-state Disable')

        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name mydisk1 --new --size-gb 10')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name mydisk2 --new --size-gb 10')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name mydisk3 --new --size-gb 10')

        self.cmd('backup protection enable-for-vm -g {rg} -v {vault} --vm {vm} -p DefaultPolicy --disk-list-setting include --diskslist 0 1', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -n {vm}', checks=[
            self.check('properties.friendlyName', '{vm}'),
            self.check('properties.healthStatus', 'Passed'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.extendedProperties.diskExclusionProperties.isInclusionList', True),
        ])

        self.cmd('backup protection update-for-vm -g {rg} -v {vault} -c {vm} -i {vm} --exclude-all-data-disks', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup protection update-for-vm -g {rg} -v {vault} -c {vm} -i {vm} --disk-list-setting exclude --diskslist 1', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -n {vm}', checks=[
            self.check('properties.friendlyName', '{vm}'),
            self.check('properties.healthStatus', 'Passed'),
            self.check('properties.protectionState', 'IRPending'),
            self.check('properties.protectionStatus', 'Healthy'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.extendedProperties.diskExclusionProperties.isInclusionList', False),
        ])

        self.kwargs['retain_date'] = (datetime.utcnow() + timedelta(days=30)).strftime('%d-%m-%Y')
        self.kwargs['job'] = self.cmd('backup protection backup-now -g {rg} -v {vault} -c {vm} -i {vm} --backup-management-type AzureIaasVM --workload-type VM --retain-until {retain_date} --query name').get_output_in_json()
        self.cmd('backup job wait -g {rg} -v {vault} -n {job}')

        self.kwargs['rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --query [0].name').get_output_in_json()

        trigger_restore_job_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} -t {rg} --storage-account {sa} --restore-to-staging-storage-account --restore-only-osdisk', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.kwargs['job'] = trigger_restore_job_json['name']
        self.cmd('backup job wait -g {rg} -v {vault} -n {job}')

        self.cmd('backup job show -g {rg} -v {vault} -n {job}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        trigger_restore_job_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} -t {rg} --storage-account {sa} --restore-to-staging-storage-account --diskslist 0', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.kwargs['job2'] = trigger_restore_job_json['name']
        self.cmd('backup job wait -g {rg} -v {vault} -n {job2}')

        self.cmd('backup job show -g {rg} -v {vault} -n {job2}', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

    @ResourceGroupPreparer(location="southeastasia")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location="southeastasia")
    def test_backup_archive (self, resource_group, vault_name, vm_name, storage_account):
        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'rg': resource_group,
            'sa': storage_account
        })

        # Get Container
        self.kwargs['container'] = self.cmd('backup container show -n {vm} -v {vault} -g {rg} --backup-management-type AzureIaasVM --query properties.friendlyName').get_output_in_json()
        
        # Get Item
        self.kwargs['item'] = self.cmd('backup item list -g {rg} -v {vault} -c {container} --backup-management-type AzureIaasVM --workload-type VM --query [0].properties.friendlyName').get_output_in_json()
        
        # Getting the recovery point IDs (names) and storing it in a list
        rp_names = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container} -i {item}', checks=[
            self.check("length(@)", 1)
        ]).get_output_in_json()
        
        self.kwargs['rp1'] = rp_names[0]['name']
        self.kwargs['rp1_tier'] = rp_names[0]['tierType']
        self.kwargs['rp1_is_ready_for_move'] = rp_names[0]['properties']['recoveryPointMoveReadinessInfo']['ArchivedRP']['isReadyForMove']
        
        # Check Archivable Recovery Points 
        self.cmd('backup recoverypoint list -g {rg} -v {vault} -i {item} -c {container} --backup-management-type AzureIaasVM --is-ready-for-move {rp1_is_ready_for_move} --target-tier VaultArchive --query [0]', checks=[
            self.check("resourceGroup", '{rg}'),
            self.check("properties.recoveryPointMoveReadinessInfo.ArchivedRP.isReadyForMove", '{rp1_is_ready_for_move}')
        ])

        # Get Archived Recovery Points 
        self.cmd('backup recoverypoint list -g {rg} -v {vault} -i {item} -c {container} --backup-management-type AzureIaasVM --tier {rp1_tier} --query [0]', checks=[
            self.check("tierType", '{rp1_tier}'),
            self.check("resourceGroup", '{rg}')
        ])

        # Get Recommended for Archive Recovery Points
        self.cmd('backup recoverypoint list -g {rg} -v {vault} -i {item} -c {container} --backup-management-type AzureIaasVM --recommended-for-archive', checks=[
            self.check("length(@)", 0)
        ])


    @ResourceGroupPreparer()
    @VaultPreparer()
    def test_backup_identity(self, resource_group, vault_name):
        self.kwargs.update({
            'vault': vault_name,
            'rg': resource_group,
        })


        self.kwargs['identity1'] = self.create_random_name('clitest-identity', 50)
        self.kwargs['identity1_id'] = self.cmd('identity create -n {identity1} -g {rg} --query id').get_output_in_json()
        

        self.kwargs['identity2'] = self.create_random_name('clitest-identity', 50)
        self.kwargs['identity2_id'] = self.cmd('identity create -n {identity2} -g {rg} --query id').get_output_in_json()

        self.kwargs['identity3'] = self.create_random_name('clitest-identity', 50)
        self.kwargs['identity3_id'] = self.cmd('identity create -n {identity3} -g {rg} --query id').get_output_in_json()

        userMSI_json = self.cmd('backup vault identity assign --user-assigned {identity1_id} {identity2_id} -g {rg} -n {vault}', checks=[
            self.check("identity.type", "UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()


        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())

        self.assertIn(self.kwargs['identity1_id'], userMSI)
        self.assertIn(self.kwargs['identity2_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity assign --system-assigned -g {rg} -n {vault}', checks=[
            self.check("identity.type", "SystemAssigned, UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())

        self.assertIn(self.kwargs['identity1_id'], userMSI)
        self.assertIn(self.kwargs['identity2_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity assign --user-assigned {identity3_id} -g {rg} -n {vault}', checks=[
            self.check("identity.type", "SystemAssigned, UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()


        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())

        self.assertIn(self.kwargs['identity1_id'], userMSI)
        self.assertIn(self.kwargs['identity2_id'], userMSI)
        self.assertIn(self.kwargs['identity3_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity remove --system-assigned --user-assigned {identity1_id} -g {rg} -n {vault}', checks=[
            self.check("identity.type", "UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())

        self.assertIn(self.kwargs['identity2_id'], userMSI)
        self.assertIn(self.kwargs['identity3_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity assign --system-assigned --user-assigned {identity1_id} -g {rg} -n {vault}', checks=[
            self.check("identity.type", "SystemAssigned, UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())
        
        self.assertIn(self.kwargs['identity1_id'], userMSI)
        self.assertIn(self.kwargs['identity2_id'], userMSI)
        self.assertIn(self.kwargs['identity3_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity remove --system-assigned --user-assigned -g {rg} -n {vault}', checks=[
            self.check("identity.type", "None"),
            self.check("identity.userAssignedIdentities", None),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI_json = self.cmd('backup vault identity assign --system-assigned -g {rg} -n {vault}', checks=[
            self.check("identity.type", "SystemAssigned"),
            self.check("identity.userAssignedIdentities", None),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI_json = self.cmd('backup vault identity assign --user-assigned {identity1_id} {identity2_id} -g {rg} -n {vault}', checks=[
            self.check("identity.type", "SystemAssigned, UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())
        
        self.assertIn(self.kwargs['identity1_id'], userMSI)
        self.assertIn(self.kwargs['identity2_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity remove --system-assigned -g {rg} -n {vault}', checks=[
            self.check("identity.type", "UserAssigned"),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()

        userMSI = list(userMSI_json['identity']['userAssignedIdentities'].keys())
        
        self.assertIn(self.kwargs['identity1_id'], userMSI)
        self.assertIn(self.kwargs['identity2_id'], userMSI)

        userMSI_json = self.cmd('backup vault identity remove --user-assigned -g {rg} -n {vault}', checks=[
            self.check("identity.type", "None"),
            self.check("identity.userAssignedIdentities", None),
            self.check("properties.provisioningState", "Succeeded")
        ]).get_output_in_json()


    @ResourceGroupPreparer()
    @VaultPreparer(parameter_name='vault1')
    @VaultPreparer(parameter_name='vault2')
    @KeyVaultPreparer()
    def test_backup_encryption(self, resource_group, resource_group_location, vault1, vault2, key_vault):
        self.kwargs.update({
            'loc' : resource_group_location,
            'vault1': vault1,
            'vault2': vault2,
            'rg': resource_group,
            'key_vault': key_vault,
            'key1': self.create_random_name('clitest-key1', 20),
            'key2': self.create_random_name('clitest-key2', 20),
            'identity1': self.create_random_name('clitest-identity1', 50),
            'identity2': self.create_random_name('clitest-identity2', 50),
            'identity_permissions': "get list unwrapKey wrapKey",
        })


        self.kwargs['identity1_id'] = self.cmd('identity create -n {identity1} -g {rg} --query id').get_output_in_json()
        self.kwargs['identity1_principalid'] = self.cmd('identity show -n {identity1} -g {rg} --query principalId').get_output_in_json()

        self.kwargs['identity2_id'] = self.cmd('identity create -n {identity2} -g {rg} --query id').get_output_in_json()
        self.kwargs['identity2_principalid'] = self.cmd('identity show -n {identity2} -g {rg} --query principalId').get_output_in_json()


        userMSI_v1_json = self.cmd('backup vault identity assign --user-assigned {identity1_id} {identity2_id} -g {rg} -n {vault1}').get_output_in_json()

        system_v1_json = self.cmd('backup vault identity assign --system-assigned -g {rg} -n {vault1}').get_output_in_json()

        self.kwargs['system1_principalid'] = system_v1_json['identity']['principalId']

        userMSI1_v2_json = self.cmd('backup vault identity assign --user-assigned {identity1_id} -g {rg} -n {vault2}').get_output_in_json()

        system_v2_json = self.cmd('backup vault identity assign --system-assigned -g {rg} -n {vault2}').get_output_in_json()

        self.kwargs['system2_principalid'] = system_v2_json['identity']['principalId']

        self.cmd('keyvault update --name {key_vault} --enable-soft-delete --enable-purge-protection')

        key1_json = self.cmd('keyvault key create --vault-name {key_vault} -n {key1} --kty RSA --disabled false --ops decrypt encrypt sign unwrapKey verify wrapKey --size 2048', checks=[
            self.check("attributes.enabled", True),
            self.check('key.kty', "RSA"),
        ]).get_output_in_json()

        keyOps1 = key1_json['key']['keyOps']
        self.assertIn("decrypt", keyOps1)
        self.assertIn("encrypt", keyOps1)
        self.assertIn("sign", keyOps1)
        self.assertIn("unwrapKey", keyOps1)
        self.assertIn("verify", keyOps1)
        self.assertIn("wrapKey", keyOps1)

        key2_json = self.cmd('keyvault key create --vault-name {key_vault} -n {key2} --kty RSA --disabled false --ops decrypt encrypt sign unwrapKey verify wrapKey --size 2048', checks=[
            self.check("attributes.enabled", True),
            self.check('key.kty', "RSA"),
        ]).get_output_in_json()

        keyOps2 = key2_json['key']['keyOps']
        self.assertIn("decrypt", keyOps2)
        self.assertIn("encrypt", keyOps2)
        self.assertIn("sign", keyOps2)
        self.assertIn("unwrapKey", keyOps2)
        self.assertIn("verify", keyOps2)
        self.assertIn("wrapKey", keyOps2)


        self.kwargs['key1_id'] = key1_json['key']['kid']
        self.kwargs['key2_id'] = key2_json['key']['kid']

        policy1_json = self.cmd('keyvault set-policy --name {key_vault} --object-id {identity1_principalid} --key-permissions {identity_permissions}').get_output_in_json()
        identity1_has_access = False

        access_policy1 = policy1_json['properties']['accessPolicies']
        for element in access_policy1:
            if element['objectId'] == self.kwargs['identity1_principalid']:
                access_policy1 = element
                identity1_has_access = True
            
        self.assertEqual(identity1_has_access, True)
        key_permissions = access_policy1['permissions']['keys']
        self.assertIn("list", key_permissions)
        self.assertIn("wrapKey", key_permissions)
        self.assertIn("get", key_permissions)
        self.assertIn("unwrapKey", key_permissions)

        policy2_json = self.cmd('keyvault set-policy --name {key_vault} --object-id {identity2_principalid} --key-permissions {identity_permissions}').get_output_in_json()
        identity2_has_access = False

        access_policy2 = policy2_json['properties']['accessPolicies']
        for element in access_policy2:
            if element['objectId'] == self.kwargs['identity2_principalid']:
                access_policy2 = element
                identity2_has_access = True
            
        self.assertEqual(identity2_has_access, True)
        key_permissions = access_policy2['permissions']['keys']
        self.assertIn("list", key_permissions)
        self.assertIn("wrapKey", key_permissions)
        self.assertIn("get", key_permissions)
        self.assertIn("unwrapKey", key_permissions)

        policy3_json = self.cmd('keyvault set-policy --name {key_vault} --object-id {system1_principalid} --key-permissions {identity_permissions}').get_output_in_json()
        system1_has_access = False

        access_policy3 = policy3_json['properties']['accessPolicies']
        for element in access_policy3:
            if element['objectId'] == self.kwargs['system1_principalid']:
                access_policy3 = element
                system1_has_access = True
            
        self.assertEqual(system1_has_access, True)
        key_permissions = access_policy3['permissions']['keys']
        self.assertIn("list", key_permissions)
        self.assertIn("wrapKey", key_permissions)
        self.assertIn("get", key_permissions)
        self.assertIn("unwrapKey", key_permissions)

        policy4_json = self.cmd('keyvault set-policy --name {key_vault} --object-id {system2_principalid} --key-permissions {identity_permissions}').get_output_in_json()
        system2_has_access = False

        access_policy4 = policy4_json['properties']['accessPolicies']
        for element in access_policy4:
            if element['objectId'] == self.kwargs['system2_principalid']:
                access_policy4 = element
                system2_has_access = True
            
        self.assertEqual(system2_has_access, True)
        key_permissions = access_policy4['permissions']['keys']
        self.assertIn("list", key_permissions)
        self.assertIn("wrapKey", key_permissions)
        self.assertIn("get", key_permissions)
        self.assertIn("unwrapKey", key_permissions)


        self.cmd('backup vault encryption update --encryption-key-id {key1_id} --mi-user-assigned {identity1_id} -g {rg} -n {vault1}')

        self.cmd('backup vault encryption show -n {vault1} -g {rg}', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', '{identity1_id}'),
            self.check('properties.useSystemAssignedIdentity', False),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id {key1_id} --mi-user-assigned {identity2_id} -g {rg} -n {vault1}')

        self.cmd('backup vault encryption show -n {vault1} -g {rg}', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', '{identity2_id}'),
            self.check('properties.useSystemAssignedIdentity', False),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id {key2_id} --mi-system-assigned -g {rg} -n {vault1}')

        self.cmd('backup vault encryption show -n {vault1} -g {rg}', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key2_id}'),
            self.check('properties.userAssignedIdentity', None),
            self.check('properties.useSystemAssignedIdentity', True),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id {key1_id} -g {rg} -n {vault1}')

        self.cmd('backup vault encryption show -n {vault1} -g {rg}', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', None),
            self.check('properties.useSystemAssignedIdentity', True),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])


        self.cmd('backup vault encryption update --encryption-key-id {key2_id} --mi-system-assigned --infrastructure-encryption Enabled -g {rg} -n {vault2}')

        self.cmd('backup vault encryption show -n {vault2} -g {rg}', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Enabled"),
            self.check('properties.keyUri', '{key2_id}'),
            self.check('properties.userAssignedIdentity', None),
            self.check('properties.useSystemAssignedIdentity', True),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id {key1_id} --mi-user-assigned {identity1_id} -g {rg} -n {vault2}')

        self.cmd('backup vault encryption show -n {vault2} -g {rg}', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Enabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', '{identity1_id}'),
            self.check('properties.useSystemAssignedIdentity', False),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

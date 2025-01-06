# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from datetime import datetime, timedelta
import unittest
import time
import random

from azure.cli.testsdk import ScenarioTest, JMESPathCheckExists, ResourceGroupPreparer, \
    StorageAccountPreparer, KeyVaultPreparer, record_only, live_only
from azure.mgmt.recoveryservicesbackup.activestamp.models import StorageType
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from .preparers import VaultPreparer, VMPreparer, ItemPreparer, PolicyPreparer, RPPreparer, \
    DESPreparer, KeyPreparer


def _get_vm_version(vm_type):
    if vm_type == 'Microsoft.Compute/virtualMachines':
        return 'Compute'
    elif vm_type == 'Microsoft.ClassicCompute/virtualMachines':
        return 'Classic'


class BackupTests(ScenarioTest, unittest.TestCase):
    def wait_for_restore_complete(self, job_id):
        self.kwargs.update({'job_id': job_id})

        status = "InProgress"
        iteration = wait_iteration = 0
        while status == "InProgress":
            iteration += 1
            if wait_iteration < 6:
                wait_iteration += 1
            time.sleep(2**wait_iteration + (random.randint(0, 1000) / 1000))
            status = self.cmd('az backup job show --ids {job_id} --query properties.status').get_output_in_json()

            if iteration > 30:
                break
        
        return status


    @ResourceGroupPreparer(location="eastus2euap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @StorageAccountPreparer(location="eastus2euap")
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
    @ResourceGroupPreparer(location="eastus2euap")
    @VaultPreparer(parameter_name='vault1')
    @VaultPreparer(parameter_name='vault2')
    # @PolicyPreparer(parameter_name='policy')
    def test_backup_vault(self, resource_group, resource_group_location, vault1, vault2):

        self.kwargs.update({
            'loc': resource_group_location,
            'vault1': vault1,
            'vault2': vault2,
            # 'policy': policy
        })

        self.kwargs['vault3'] = self.create_random_name('clitest-vault', 50)
        self.cmd('backup vault create -n {vault3} -g {rg} -l {loc}', checks=[
            self.check('name', '{vault3}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', '{loc}'),
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.publicNetworkAccess', 'Enabled'),
            self.check('properties.monitoringSettings.azureMonitorAlertSettings.alertsForAllJobFailures', 'Enabled'),
            self.check('properties.monitoringSettings.classicAlertSettings.alertsForCriticalOperations', 'Enabled'),
            self.check('properties.restoreSettings.crossSubscriptionRestoreSettings.crossSubscriptionRestoreState', 'Enabled')
        ])

        self.kwargs['vault4'] = self.create_random_name('clitest-vault', 50)
        self.cmd('backup vault create -n {vault4} -g {rg} -l {loc} --public-network-access Disable --immutability-state Unlocked --cross-subscription-restore-state Disable', checks=[
            self.check('name', '{vault4}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', '{loc}'),
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.publicNetworkAccess', 'Disabled'),
            self.check('properties.securitySettings.immutabilitySettings.state', 'Unlocked'),
            self.check('properties.restoreSettings.crossSubscriptionRestoreSettings.crossSubscriptionRestoreState', 'Disabled')
        ])

        self.cmd('backup vault update -n {vault4} -g {rg} --public-network-access Enable', checks=[
            self.check('properties.publicNetworkAccess', 'Enabled')
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
        vault_properties_redundancy = self.cmd('backup vault show -n {vault1} -g {rg} --query "properties.redundancySettings"').get_output_in_json()

        if vault_properties_redundancy['standardTierStorageRedundancy'] == StorageType.geo_redundant.value:
            new_storage_model = StorageType.locally_redundant.value
        else:
            new_storage_model = StorageType.geo_redundant.value

        self.kwargs['model'] = new_storage_model
        self.cmd('backup vault update -n {vault1} -g {rg} --backup-storage-redundancy {model}')
        time.sleep(300)
        self.cmd('backup vault show -n {vault1} -g {rg} --query "properties.redundancySettings"', checks=[
            self.check('standardTierStorageRedundancy', new_storage_model)
        ])

        new_storage_model = StorageType.zone_redundant.value
        self.kwargs['model'] = new_storage_model
        self.cmd('backup vault update -n {vault1} -g {rg} --backup-storage-redundancy {model}')
        time.sleep(300)
        self.cmd('backup vault show -n {vault1} -g {rg} --query "properties.redundancySettings"', checks=[
            self.check('standardTierStorageRedundancy', new_storage_model)
        ])

        self.cmd('backup vault backup-properties set -g {rg} -n {vault1} --hybrid-backup-security-features Disable', checks=[
            self.check("properties.enhancedSecurityState", 'Disabled'),
        ])

        self.cmd('backup vault backup-properties set -g {rg} -n {vault1} --hybrid-backup-security-features Enable', checks=[
            self.check("properties.enhancedSecurityState", 'Enabled'),
        ])

        self.cmd('backup vault backup-properties set -g {rg} -n {vault1} --classic-alerts Disable --job-failure-alerts Disable', checks=[
            self.check('properties.monitoringSettings.azureMonitorAlertSettings.alertsForAllJobFailures', 'Disabled'),
            self.check('properties.monitoringSettings.classicAlertSettings.alertsForCriticalOperations', 'Disabled')
        ])

        # self.kwargs['policy_json'] = self.cmd('backup policy show -g {rg} -v {vault4} -n DefaultPolicy', checks=[
        #     self.check('name', 'DefaultPolicy'),
        #     self.check('resourceGroup', '{rg}')
        # ]).get_output_in_json()
        
        # self.kwargs['policy_json']['properties']["retentionPolicy"] = {}
        # self.kwargs['policy_json']['properties']['retentionPolicy']['dailySchedule'] = {}
        # self.kwargs['policy_json']['properties']['retentionPolicy']['dailySchedule']['retentionDuration'] = {"count": 20, "durationType": "Days"}

        # Immutable vault testing.
        self.cmd('backup vault update -n {vault4} -g {rg} --immutability-state Disabled --cross-subscription-restore-state Enable', checks=[
            self.check('properties.securitySettings.immutabilitySettings.state', 'Disabled'),
            self.check('properties.restoreSettings.crossSubscriptionRestoreSettings.crossSubscriptionRestoreState', 'Enabled')
        ])

        # self.cmd('backup policy set -g {rg} -v {vault4} --policy {policy_json}', checks=[
        #     self.check('properties.retentionPolicy.dailySchedule.retentionDuration.count', 20)
        # ])

        # self.kwargs['policy_json']['properties']['retentionPolicy']['dailySchedule']['retentionDuration']['count'] = 10

        self.cmd('backup vault update -n {vault4} -g {rg} --immutability-state Unlocked --cross-subscription-restore-state PermanentlyDisable', checks=[
            self.check('properties.securitySettings.immutabilitySettings.state', 'Unlocked'),
            self.check('properties.restoreSettings.crossSubscriptionRestoreSettings.crossSubscriptionRestoreState', 'PermanentlyDisabled')
        ])

        # self.cmd('backup policy set -g {rg} -v {vault4} --policy {policy_json}', expect_failure=True)

        self.cmd('backup vault delete -n {vault4} -g {rg} -y')

        self.cmd('backup vault list', checks=[
            self.check("length([?resourceGroup == '{rg}'])", number_of_test_vaults - 1),
            self.check("length([?name == '{vault1}'])", 1),
            self.check("length([?name == '{vault2}'])", 1),
            self.check("length([?name == '{vault3}'])", 1)
        ])

    @ResourceGroupPreparer(location="centraluseuap")
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

    @ResourceGroupPreparer(location="eastus2euap")
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

        self.cmd('backup policy list -g {rg} -v {vault} --move-to-archive-tier Enabled', checks=[
            self.check("length(@)", 0)
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

        # set monthly retention policy
        self.kwargs['policy1_json']['properties']["retentionPolicy"]["monthlySchedule"] = {}
        self.kwargs['policy1_json']['properties']["retentionPolicy"]["monthlySchedule"]["retentionDuration"] = {"count": 60, "durationType": "Months"}
        self.kwargs['policy1_json']['properties']["retentionPolicy"]["monthlySchedule"]["retentionScheduleDaily"] = {"daysOfTheMonth": [{"date": 1, "isLast": False}]}
        self.kwargs['policy1_json']['properties']["retentionPolicy"]["monthlySchedule"]["retentionScheduleFormatType"] = "Daily"
        self.kwargs['policy1_json']['properties']["retentionPolicy"]["monthlySchedule"]["retentionScheduleWeekly"] = None
        self.kwargs['policy1_json']['properties']["retentionPolicy"]["monthlySchedule"]["retentionTimes"] = self.kwargs['policy1_json']['properties']["retentionPolicy"]["dailySchedule"]["retentionTimes"]

        # set smart tiering policy
        self.kwargs['policy1_json']['properties']["tieringPolicy"] = {"ArchivedRP": {"duration": 0, "durationType": "Invalid", "tieringMode": "TierRecommended"}}

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

        self.cmd('backup policy list -g {rg} -v {vault} --move-to-archive-tier Enabled', checks=[
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

    @ResourceGroupPreparer(location="centraluseuap")
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

    @ResourceGroupPreparer(location="eastus2euap")
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

    @ResourceGroupPreparer(location="centraluseuap")
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
    @ResourceGroupPreparer(location="eastus2euap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @live_only()
    @unittest.skip("Test temporarily skipped as the Resource appears to be deleted")
    def test_backup_csr(self, resource_group, vault_name, vm_name):
        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'target_sub': "da364f0f-307b-41c9-9d47-b7413ec45535", 
            'target_rg': "clitest-iaasvm-rg-donotuse",
            'rg': resource_group,
            'sa_id': "/subscriptions/da364f0f-307b-41c9-9d47-b7413ec45535/resourceGroups/clitest-iaasvm-rg-donotuse/providers/Microsoft.Storage/storageAccounts/clitestiaasvmsadonotuse",
            'vm_id': "VM;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'container_id': "IaasVMContainer;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'vnet_name': self.create_random_name('clitest-vnet', 30),
            'subnet_name': self.create_random_name('clitest-subnet', 30),
            'target_vm_name': self.create_random_name('clitest-tvm', 15)
        })
        self.kwargs['rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --query [0].name').get_output_in_json()

        trigger_restore_job_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --target-subscription {target_sub} -t {target_rg} --storage-account {sa_id} --restore-to-staging-storage-account', checks=[
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


        vnet_json = self.cmd('network vnet create -g {target_rg} -n {vnet_name} --subnet-name {subnet_name} --subscription {target_sub}',
                 checks=[
            self.check("newVNet.name", '{vnet_name}')
        ]).get_output_in_json()

        self.assertIn(self.kwargs['subnet_name'].lower(), vnet_json['newVNet']['subnets'][0]['name'].lower())

        trigger_restore_job4_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} --storage-account {sa_id} --restore-mode AlternateLocation --target-vm-name {target_vm_name} --target-vnet-name {vnet_name} --target-subnet-name {subnet_name} --target-vnet-resource-group {target_rg} -t {target_rg} --target-subscription {target_sub}', checks=[
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


    # Prerequisites in case resource gets deleted - VM backed up in vault such that it is associated with a disk access set and RP contains isPrivateAccessEnabledOnAnyDisk
    def test_backup_diskaccess_restore(self):
        self.kwargs.update({
            'rg': 'zubairRG',
            'vault': 'ztestvault1',
            'container_name': 'zvm-jsdk2',
            'item_name': 'zvm-jsdk2',
            'sa': 'zubairsaccy',
            'target_rg': 'zubairRG',
            'target_vm_name': 'zvm-jsdk2-clitestrestore',
            'target_vnet_name': 'zvm-jsdk1-vnet',
            'target_vnet_rg': 'zubairRG',
            'target_subnet_name': 'default',
            'target_disk_access_id': '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/zubairRG/providers/Microsoft.Compute/diskAccesses/clitest-access1'
        })
        self.cmd('vm delete -g {rg} -n {target_vm_name} --yes')

        rp_details = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container_name} -i {item_name} --query [0]').get_output_in_json()
        self.assertTrue(rp_details['properties']['isPrivateAccessEnabledOnAnyDisk'])

        self.kwargs['rp'] = rp_details['name']

        base_command = 'az backup restore restore-disks -g {rg} -v {vault} --container-name {container_name} --item-name {item_name} --storage-account {sa} --rp-name {rp} '
        base_command += '--target-resource-group {target_rg} --target-vm-name {target_vm_name} --target-vnet-name {target_vnet_name} --target-vnet-resource-group {target_vnet_rg} --target-subnet-name {target_subnet_name}'
        target_disk_access_option = ' --target-disk-access-id {target_disk_access_id}'

        # Command should fail as the RP contains isPrivateEAccessEnabledOnAnyDisk is true
        self.cmd(base_command, expect_failure=True)
        
        # for same as source option, command should fail when target disk option is provided, but pass otherwise
        same_as_source_command = base_command + ' --disk-access-option SameAsOnSourceDisks'
        self.cmd(same_as_source_command + target_disk_access_option, expect_failure=True)
        job_out = self.cmd(same_as_source_command, checks=[
            self.check("properties.entityFriendlyName", '{container_name}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.wait_for_restore_complete(job_out["id"])
        self.cmd('vm delete -g {rg} -n {target_vm_name} --yes')

        # for enable public access option, command should fail when target disk option is provided, but pass otherwise
        public_command = base_command + ' --disk-access-option EnablePublicAccessForAllDisks'
        self.cmd(public_command + target_disk_access_option, expect_failure=True)
        job_out = self.cmd(public_command, checks=[
            self.check("properties.entityFriendlyName", '{container_name}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.wait_for_restore_complete(job_out["id"])
        self.cmd('vm delete -g {rg} -n {target_vm_name} --yes')

        # for enable private access option, command should fail when target disk option is NOT provided, but pass otherwise
        private_command = base_command + ' --disk-access-option EnablePrivateAccessForAllDisks'
        self.cmd(private_command, expect_failure=True)
        job_out = self.cmd(private_command + target_disk_access_option, checks=[
            self.check("properties.entityFriendlyName", '{container_name}'),
            self.check("properties.operation", "Restore"),
            self.check("properties.status", "InProgress"),
            self.check("resourceGroup", '{rg}')
        ]).get_output_in_json()
        self.wait_for_restore_complete(job_out["id"])
        self.cmd('vm delete -g {rg} -n {target_vm_name} --yes')


    @AllowLargeResponse()
    @ResourceGroupPreparer(location="eastus2euap")
    @ResourceGroupPreparer(parameter_name="target_resource_group", location="eastus2euap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location="eastus2euap")
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(location="centraluseuap")
    @ResourceGroupPreparer(parameter_name="target_resource_group", location="centraluseuap")
    @ResourceGroupPreparer(parameter_name="storage_account_resource_group", location="centraluseuap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location="centraluseuap", resource_group_parameter_name="storage_account_resource_group")
    def test_backup_restore_when_storage_in_different_rg(self, resource_group, target_resource_group, vault_name, vm_name, storage_account, storage_account_resource_group):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'target_rg': target_resource_group,
            'rg': resource_group,
            'sa': storage_account,
            'sa_rg': storage_account_resource_group,
            'vm_id': "VM;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'container_id': "IaasVMContainer;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'vnet_name': self.create_random_name('clitest-vnet', 30),
            'subnet_name': self.create_random_name('clitest-subnet', 30),
            'target_vm_name': self.create_random_name('clitest-tvm', 15)
        })

        self.kwargs['rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -i {vm} --query [0].name').get_output_in_json()

        # Trigger Restore Disks
        trigger_restore_job_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {vm} -i {vm} -r {rp} -t {target_rg} --storage-account {sa} --storage-account-resource-group {sa_rg}', checks=[
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

        self.cmd('storage blob exists --account-name {sa} -c {container} -n {blob}', checks=self.check("exists", True))

    # @unittest.skip("Test skipped due to temporary test infrastructure issues")
    @AllowLargeResponse()
    @ResourceGroupPreparer(location="centraluseuap")
    @ResourceGroupPreparer(parameter_name="target_resource_group", location="centraluseuap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(parameter_name="secondary_region_sa", location="eastus2euap")
    def test_backup_crr(self, resource_group, target_resource_group, vault_name, vm_name, secondary_region_sa):

       self.kwargs.update({
           'vault': vault_name,
           'vm': vm_name,
           'target_rg': target_resource_group,
           'rg': resource_group,
           'secondary_sa': secondary_region_sa,
           'vm_id': "VM;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
           'container_id': "IaasVMContainer;iaasvmcontainerv2;" + resource_group + ";" + vm_name
       })
       self.cmd('backup vault update -g {rg} -n {vault} --cross-region-restore-flag Enabled', checks=[
           self.check('properties.redundancySettings.crossRegionRestore', 'Enabled')
       ]).get_output_in_json()
       time.sleep(300)

       # Trigger Cross Region Restore
       self.kwargs['crr_rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container_id} -i {vm_id} --use-secondary-region --query [0].name').get_output_in_json()

       trigger_restore_job3_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {container_id} -i {vm_id} -r {crr_rp} --storage-account {secondary_sa} -t {target_rg} --use-secondary-region', checks=[
           self.check("properties.entityFriendlyName", vm_name),
           self.check("properties.operation", "CrossRegionRestore"),
           self.check("properties.status", "InProgress")
       ]).get_output_in_json()
       self.kwargs['job3'] = trigger_restore_job3_json['name']

       self.cmd('backup job wait -g {rg} -v {vault} -n {job3} --use-secondary-region')

       self.cmd('backup job show -g {rg} -v {vault} -n {job3} --use-secondary-region', checks=[
           self.check("properties.entityFriendlyName", vm_name),
           self.check("properties.operation", "CrossRegionRestore"),
           self.check("properties.status", "Completed")
       ])

    @unittest.skip("Test skipped due to service-side flag being disabled")
    @AllowLargeResponse()
    @ResourceGroupPreparer(location="centraluseuap")
    @ResourceGroupPreparer(parameter_name="target_resource_group", location="centraluseuap")
    @KeyVaultPreparer()
    @KeyPreparer()
    @DESPreparer()
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(parameter_name="secondary_region_sa", location="eastus2euap")
    def test_backup_crr_des(self, resource_group, target_resource_group, vault_name, vm_name, des_name, secondary_region_sa):

        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'des_name': des_name,
            'target_rg': target_resource_group,
            'rg': resource_group,
            'secondary_sa': secondary_region_sa,
            'vm_id': "VM;iaasvmcontainerv2;" + resource_group + ";" + vm_name,
            'container_id': "IaasVMContainer;iaasvmcontainerv2;" + resource_group + ";" + vm_name
        })

        self.cmd('backup vault update -g {rg} -n {vault} --cross-region-restore-flag Enabled', checks=[
            self.check('properties.redundancySettings.crossRegionRestore', 'Enabled')
        ]).get_output_in_json()
        time.sleep(300)

        # Trigger Cross Region Restore
        self.kwargs['crr_rp'] = self.cmd('backup recoverypoint list --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {container_id} -i {vm_id} --use-secondary-region --query [0].name').get_output_in_json()

        # Get the Disk-Encryption-Set ID from the name
        self.kwargs['des_id'] = self.cmd('disk-encryption-set show -g {rg} -n {des_name}').get_output_in_json()["id"]
        trigger_restore_job4_json = self.cmd('backup restore restore-disks -g {rg} -v {vault} -c {container_id} -i {vm_id} -r {crr_rp} --storage-account {secondary_sa} -t {target_rg} --disk-encryption-set-id {des_id} --use-secondary-region', checks=[
            self.check("properties.entityFriendlyName", vm_name),
            self.check("properties.operation", "CrossRegionRestore"),
            self.check("properties.status", "InProgress")
        ]).get_output_in_json()
        self.kwargs['job4'] = trigger_restore_job4_json['name']

        self.cmd('backup job wait -g {rg} -v {vault} -n {job4} --use-secondary-region')

        self.cmd('backup job show -g {rg} -v {vault} -n {job4} --use-secondary-region', checks=[
            self.check("properties.entityFriendlyName", vm_name),
            self.check("properties.operation", "CrossRegionRestore"),
            self.check("properties.status", "Completed")
        ])   

    @ResourceGroupPreparer(location="centraluseuap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location=" centraluseuap")
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
            self.check("properties.extendedInfo.tasksList[0].endTime", None),
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

    @ResourceGroupPreparer(location="centraluseuap")
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

        self.cmd('backup vault list-soft-deleted-containers --backup-management-type AzureIaasVM -g {rg} -n {vault}', checks=[
            self.check("length(@)", 1),
            self.check("[0].properties.friendlyName", "{vm}")
        ])

        self.cmd('backup protection undelete -g {rg} -v {vault} -c {vm} -i {vm} --workload-type VM --backup-management-type AzureIaasVM ', checks=[
            self.check("properties.entityFriendlyName", '{vm}'),
            self.check("properties.operation", "Undelete"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup vault backup-properties set -g {rg} -n {vault} --soft-delete-feature-state Disable')
        # TODO: once the soft delete feature move is enabled across the board, use the following lines instead 
        # self.cmd('backup vault create -g {rg} -v {vault} -l {location} --soft-delete-state Disable')

        self.cmd('backup item show --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm} -n {vm}', checks=[
            self.check("properties.friendlyName", '{vm}'),
            self.check("properties.protectionState", "ProtectionStopped"),
            self.check("resourceGroup", '{rg}'),
            self.check("properties.isScheduledForDeferredDelete", None)
        ])

    @ResourceGroupPreparer(location="eastus2euap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @StorageAccountPreparer(location="eastus2euap")
    def test_backup_disk_exclusion(self, resource_group, vault_name, vm_name, storage_account):
        self.kwargs.update({
            'vault': vault_name,
            'vm': vm_name,
            'rg': resource_group,
            'sa': storage_account
        })

        self.cmd('backup vault backup-properties set -g {rg} -n {vault} --soft-delete-feature-state Disable')
        # TODO: once the soft delete feature move is enabled across the board, use the following lines instead 
        # self.cmd('backup vault create -g {rg} -v {vault} -l {location} --soft-delete-state Disable')

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

    @ResourceGroupPreparer(location="eastus2euap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer(location="eastus2euap")
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

    @ResourceGroupPreparer(location="eastus2euap")
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
            'identity_rbac_permissions': "Key Vault Crypto Service Encryption User",
            'user_rbac_permissions': "Key Vault Administrator"
        })

        subscription = self.cmd('account show --query "id"').get_output_in_json()
        user_principal_id = self.cmd('account show --query "user.name"').get_output_in_json()
        self.kwargs["user_principal_id"] = user_principal_id
        self.kwargs['key_vault_id'] = "subscriptions/{}/resourceGroups/{}/providers/Microsoft.KeyVault/vaults/{}".format(
            subscription, resource_group, key_vault)
        # Uncomment during live runs
        # self.cmd('role assignment create --role "{user_rbac_permissions}" --scope "{key_vault_id}" --assignee "{user_principal_id}"')

        self.kwargs['identity1_id'] = self.cmd('identity create -n "{identity1}" -g "{rg}" --query id').get_output_in_json()
        self.kwargs['identity1_principalid'] = self.cmd('identity show -n "{identity1}" -g "{rg}" --query principalId').get_output_in_json()

        self.kwargs['identity2_id'] = self.cmd('identity create -n "{identity2}" -g "{rg}" --query id').get_output_in_json()
        self.kwargs['identity2_principalid'] = self.cmd('identity show -n "{identity2}" -g "{rg}" --query principalId').get_output_in_json()


        userMSI_v1_json = self.cmd('backup vault identity assign --user-assigned "{identity1_id}" "{identity2_id}" -g "{rg}" -n "{vault1}"').get_output_in_json()

        system_v1_json = self.cmd('backup vault identity assign --system-assigned -g "{rg}" -n "{vault1}"').get_output_in_json()

        self.kwargs['system1_principalid'] = system_v1_json['identity']['principalId']

        userMSI1_v2_json = self.cmd('backup vault identity assign --user-assigned "{identity1_id}" -g "{rg}" -n "{vault2}"').get_output_in_json()

        system_v2_json = self.cmd('backup vault identity assign --system-assigned -g "{rg}" -n "{vault2}"').get_output_in_json()

        self.kwargs['system2_principalid'] = system_v2_json['identity']['principalId']

        self.cmd('keyvault update --name "{key_vault}" --enable-purge-protection')

        key1_json = self.cmd('keyvault key create --vault-name "{key_vault}" -n "{key1}" --kty RSA --disabled false --ops decrypt encrypt sign unwrapKey verify wrapKey --size 2048', checks=[
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

        key2_json = self.cmd('keyvault key create --vault-name "{key_vault}" -n "{key2}" --kty RSA --disabled false --ops decrypt encrypt sign unwrapKey verify wrapKey --size 2048', checks=[
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

        # Uncomment during live runs
        # role_id = '/subscriptions/{}/providers/Microsoft.Authorization/roleDefinitions/e147488a-f6f5-4113-8e2d-b22465e65bf6'.format(subscription)
        # rbac1_json = self.cmd('role assignment create --scope "{key_vault_id}" --assignee "{identity1_principalid}" --role "{identity_rbac_permissions}"').get_output_in_json()
        # self.assertEqual(rbac1_json['roleDefinitionId'], role_id)

        # rbac2_json = self.cmd('role assignment create --scope "{key_vault_id}" --assignee "{identity2_principalid}" --role "{identity_rbac_permissions}"').get_output_in_json()
        # self.assertEqual(rbac2_json['roleDefinitionId'], role_id)

        # rbac3_json = self.cmd('role assignment create --scope "{key_vault_id}" --assignee "{system1_principalid}" --role "{identity_rbac_permissions}"').get_output_in_json()
        # self.assertEqual(rbac3_json['roleDefinitionId'], role_id)

        # rbac4_json = self.cmd('role assignment create --scope "{key_vault_id}" --assignee "{system2_principalid}" --role "{identity_rbac_permissions}"').get_output_in_json()
        # self.assertEqual(rbac4_json['roleDefinitionId'], role_id)

        self.cmd('backup vault encryption update --encryption-key-id "{key1_id}" --mi-user-assigned "{identity1_id}" -g "{rg}" -n "{vault1}"')

        self.cmd('backup vault encryption show -n "{vault1}" -g "{rg}"', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', '{identity1_id}'),
            self.check('properties.useSystemAssignedIdentity', False),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id "{key1_id}" --mi-user-assigned "{identity2_id}" -g "{rg}" -n "{vault1}"')

        self.cmd('backup vault encryption show -n "{vault1}" -g "{rg}"', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', '{identity2_id}'),
            self.check('properties.useSystemAssignedIdentity', False),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id "{key2_id}" --mi-system-assigned -g "{rg}" -n "{vault1}"')

        self.cmd('backup vault encryption show -n "{vault1}" -g "{rg}"', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key2_id}'),
            self.check('properties.userAssignedIdentity', None),
            self.check('properties.useSystemAssignedIdentity', True),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id "{key1_id}" -g "{rg}" -n "{vault1}"')

        self.cmd('backup vault encryption show -n "{vault1}" -g "{rg}"', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Disabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', None),
            self.check('properties.useSystemAssignedIdentity', True),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])


        self.cmd('backup vault encryption update --encryption-key-id "{key2_id}" --mi-system-assigned --infrastructure-encryption Enabled -g "{rg}" -n "{vault2}"')

        self.cmd('backup vault encryption show -n "{vault2}" -g "{rg}"', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Enabled"),
            self.check('properties.keyUri', '{key2_id}'),
            self.check('properties.userAssignedIdentity', None),
            self.check('properties.useSystemAssignedIdentity', True),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

        self.cmd('backup vault encryption update --encryption-key-id "{key1_id}" --mi-user-assigned "{identity1_id}" -g "{rg}" -n "{vault2}"')

        self.cmd('backup vault encryption show -n "{vault2}" -g "{rg}"', checks=[
            self.check("properties.encryptionAtRestType", "CustomerManaged"),
            self.check("properties.infrastructureEncryptionState", "Enabled"),
            self.check('properties.keyUri', '{key1_id}'),
            self.check('properties.userAssignedIdentity', '{identity1_id}'),
            self.check('properties.useSystemAssignedIdentity', False),
            self.check('properties.lastUpdateStatus', 'Succeeded')
        ])

    @ResourceGroupPreparer(location="centraluseuap")
    @VaultPreparer(soft_delete=False)
    @VMPreparer(parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm1')
    @PolicyPreparer(parameter_name='policy1', instant_rp_days='4')
    @PolicyPreparer(parameter_name='policy2', instant_rp_days='2')
    def test_backup_rg_mapping(self, resource_group, vault_name, vm1, policy1, policy2):
        self.kwargs.update({
            'vault': vault_name,
            'vm1': vm1,
            'policy1': policy1,
            'policy2': policy2,
            'default': 'DefaultPolicy',
            'resource_graph': '/subscriptions/38304e13-357e-405e-9e9a-220351dcce8c/resourceGroups/clitest-rg/providers/Microsoft.DataProtection/resourceGuards/clitest-resource-guard'
        })
        # associate vault with an already present resource guard
        self.cmd('backup vault resource-guard-mapping update -g {rg} -n {vault} --resource-guard-id {resource_graph}', checks=[
            self.check('name', 'VaultProxy'),
            self.check('length(properties.resourceGuardOperationDetails)', 9)
        ])

        self.cmd('backup vault resource-guard-mapping show -g {rg} -n {vault}', checks=[
            self.check('name', 'VaultProxy'),
            self.check('length(properties.resourceGuardOperationDetails)', 9)
        ])

        # Try disabling soft delete
        self.cmd('backup vault backup-properties set -g {rg} -n {vault} --soft-delete-feature-state Disable', checks=[
            self.check('properties.softDeleteFeatureState', 'Disabled')
        ])
        # TODO: once the soft delete feature move is enabled across the board, use the following lines instead 
        # self.cmd('backup vault create -g {rg} -v {vault} -l {location} --soft-delete-state Disable', checks=[
        #     self.check('properties.securitySettings.softDeleteSettings.softDeleteState', 'Disabled')
        # ])

        time.sleep(300)

        # try modifying protection using the second policy
        self.cmd('backup item set-policy --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm1} -n {vm1} -p {policy1}', checks=[
            self.check("properties.entityFriendlyName", '{vm1}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        self.cmd('backup item set-policy --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm1} -n {vm1} -p {policy2}', checks=[
            self.check("properties.entityFriendlyName", '{vm1}'),
            self.check("properties.operation", "ConfigureBackup"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        # try deleting protection
        self.cmd('backup protection disable --backup-management-type AzureIaasVM --workload-type VM -g {rg} -v {vault} -c {vm1} -i {vm1} --delete-backup-data --yes', checks=[
            self.check("properties.entityFriendlyName", '{vm1}'),
            self.check("properties.operation", "DeleteBackupData"),
            self.check("properties.status", "Completed"),
            self.check("resourceGroup", '{rg}')
        ])

        # try deleting resource guard mapping
        self.cmd('backup vault resource-guard-mapping delete -n {vault} -g {rg} -y')

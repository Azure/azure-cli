# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from datetime import datetime, timedelta
import unittest

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, JMESPathCheckExists, ResourceGroupPreparer, \
    StorageAccountPreparer
from azure.mgmt.recoveryservices.models import StorageModelType

from .preparers import VaultPreparer, VMPreparer, ItemPreparer, PolicyPreparer, RPPreparer


def _get_vm_version(vm_type):
    if vm_type == 'Microsoft.Compute/virtualMachines':
        return 'Compute'
    elif vm_type == 'Microsoft.ClassicCompute/virtualMachines':
        return 'Classic'


class BackupTests(ScenarioTest, unittest.TestCase):
    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer()
    @StorageAccountPreparer()
    def test_backup_restore(self, resource_group, vault_name, vm_name, storage_account):
        # Enable Protection
        self.cmd('backup protection enable-for-vm -g {} -v {} --vm {} -p DefaultPolicy'
                 .format(resource_group, vault_name, vm_name)).get_output_in_json()

        # Get Container
        container = self.cmd('backup container show -n {} -v {} -g {} --query properties.friendlyName'
                             .format(vm_name, vault_name, resource_group)).get_output_in_json()

        # Get Item
        item = self.cmd('backup item list -g {} -v {} -c {} --query [0].properties.friendlyName'
                        .format(resource_group, vault_name, container)).get_output_in_json()

        # Trigger Backup
        retain_date = datetime.utcnow() + timedelta(days=30)
        backup_cmd_string = 'backup protection backup-now'
        backup_cmd_string += ' -g {} -v {}'.format(resource_group, vault_name)
        backup_cmd_string += ' -c {} -i {}'.format(container, item)
        backup_cmd_string += ' --retain-until {} --query name'.format(retain_date.strftime('%d-%m-%Y'))
        trigger_backup_job_name = self.cmd(backup_cmd_string).get_output_in_json()
        self.cmd('backup job wait -g {} -v {} -n {}'.format(resource_group, vault_name, trigger_backup_job_name))

        # Get Recovery Point
        recovery_point = self.cmd('backup recoverypoint list -g {} -v {} -c {} -i {} --query [0].name'
                                  .format(resource_group, vault_name, container, item)).get_output_in_json()

        # Trigger Restore
        restore_cmd_string = 'backup restore restore-disks'
        restore_cmd_string += ' -g {} -v {}'.format(resource_group, vault_name)
        restore_cmd_string += ' -c {} -i {} -r {}'.format(container, item, recovery_point)
        restore_cmd_string += ' --storage-account {} --query name'.format(storage_account)
        trigger_restore_job_name = self.cmd(restore_cmd_string).get_output_in_json()
        self.cmd('backup job wait -g {} -v {} -n {}'.format(resource_group, vault_name, trigger_restore_job_name))

        # Disable Protection
        self.cmd('backup protection disable -g {} -v {} -c {} -i {} --delete-backup-data true --yes'
                 .format(resource_group, vault_name, container, item))

    @ResourceGroupPreparer()
    @VaultPreparer(parameter_name='vault1')
    @VaultPreparer(parameter_name='vault2')
    def test_vault_commands(self, resource_group, resource_group_location, vault1, vault2):
        vault3 = self.create_random_name('clitest-vault', 50)
        self.cmd('backup vault create -n {} -g {} -l {}'
                 .format(vault3, resource_group, resource_group_location), checks=[
                     JMESPathCheck('name', vault3),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('location', resource_group_location),
                     JMESPathCheck('properties.provisioningState', 'Succeeded')])

        self.cmd('backup vault list', checks=[
            JMESPathCheck("length([?resourceGroup == '{}'])".format(resource_group), 3),
            JMESPathCheck("length([?name == '{}'])".format(vault1), 1),
            JMESPathCheck("length([?name == '{}'])".format(vault2), 1),
            JMESPathCheck("length([?name == '{}'])".format(vault3), 1)])

        self.cmd('backup vault list -g {}'.format(resource_group), checks=[
            JMESPathCheck("length(@)", 3),
            JMESPathCheck("length([?name == '{}'])".format(vault1), 1),
            JMESPathCheck("length([?name == '{}'])".format(vault2), 1),
            JMESPathCheck("length([?name == '{}'])".format(vault3), 1)
        ])

        storage_model_types = [e.value for e in StorageModelType]
        vault_properties = self.cmd('backup vault backup-properties show -n {} -g {}'
                                    .format(vault1, resource_group), checks=[
                                        JMESPathCheckExists("contains({}, storageModelType)"
                                                            .format(storage_model_types)),
                                        JMESPathCheck('storageTypeState', 'Unlocked'),
                                        JMESPathCheck('resourceGroup', resource_group)]).get_output_in_json()

        if vault_properties['storageModelType'] == StorageModelType.geo_redundant.value:
            new_storage_model = StorageModelType.locally_redundant.value
        else:
            new_storage_model = StorageModelType.geo_redundant.value

        self.cmd('backup vault backup-properties set -n {} -g {} --backup-storage-redundancy {}'
                 .format(vault1, resource_group, new_storage_model))

        self.cmd('backup vault backup-properties show -n {} -g {}'.format(vault1, resource_group), checks=[
            JMESPathCheck('storageModelType', new_storage_model)
        ])

        self.cmd('backup vault delete -n {} -g {} -y'.format(vault3, resource_group))

        self.cmd('backup vault list', checks=[
            JMESPathCheck("length([?resourceGroup == '{}'])".format(resource_group), 2),
            JMESPathCheck("length([?name == '{}'])".format(vault1), 1),
            JMESPathCheck("length([?name == '{}'])".format(vault2), 1)
        ])

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer(parameter_name='vm1')
    @VMPreparer(parameter_name='vm2')
    @ItemPreparer(vm_parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm2')
    def test_container_commands(self, resource_group, vault_name, vm1, vm2):
        container_json = self.cmd('backup container show -n {} -v {} -g {}'
                                  .format(vm1, vault_name, resource_group), checks=[
                                      JMESPathCheck('properties.friendlyName', vm1),
                                      JMESPathCheck('properties.healthStatus', 'Healthy'),
                                      JMESPathCheck('properties.registrationStatus', 'Registered'),
                                      JMESPathCheck('properties.resourceGroup', resource_group),
                                      JMESPathCheck('resourceGroup', resource_group)]).get_output_in_json()

        vm1_json = self.cmd('vm show -n {} -g {}'.format(vm1, resource_group)).get_output_in_json()

        self.assertIn(vault_name.lower(), container_json['id'].lower())
        self.assertIn(vm1.lower(), container_json['name'].lower())
        self.assertIn(vm1.lower(), container_json['properties']['virtualMachineId'].lower())
        self.assertEqual(container_json['properties']['virtualMachineVersion'], _get_vm_version(vm1_json['type']))

        self.cmd('backup container list -v {} -g {}'.format(vault_name, resource_group), checks=[
            JMESPathCheck("length(@)", 2),
            JMESPathCheck("length([?properties.friendlyName == '{}'])".format(vm1), 1),
            JMESPathCheck("length([?properties.friendlyName == '{}'])".format(vm2), 1)])

    @ResourceGroupPreparer()
    @VaultPreparer()
    @PolicyPreparer(parameter_name='policy1')
    @PolicyPreparer(parameter_name='policy2')
    @VMPreparer(parameter_name='vm1')
    @VMPreparer(parameter_name='vm2')
    @ItemPreparer(vm_parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm2')
    def test_policy_commands(self, resource_group, vault_name, policy1, policy2, vm1, vm2):
        policy3 = self.create_random_name('clitest-policy', 24)
        default_policy = 'DefaultPolicy'

        policy1_json = self.cmd('backup policy show -g {} -v {} -n {}'
                                .format(resource_group, vault_name, policy1), checks=[
                                    JMESPathCheck('name', policy1),
                                    JMESPathCheck('resourceGroup', resource_group)]).get_output_in_json()

        self.cmd('backup policy list -g {} -v {}'.format(resource_group, vault_name), checks=[
            JMESPathCheck("length(@)", 4),
            JMESPathCheck("length([?name == '{}'])".format(default_policy), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy1), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy2), 1)])

        self.cmd('backup policy list-associated-items -g {} -v {} -n {}'
                 .format(resource_group, vault_name, default_policy), checks=[
                     JMESPathCheck("length(@)", 2),
                     JMESPathCheck("length([?properties.friendlyName == '{}'])".format(vm1), 1),
                     JMESPathCheck("length([?properties.friendlyName == '{}'])".format(vm2), 1)])

        policy1_json['name'] = policy3
        policy1_json = json.dumps(policy1_json)

        self.cmd('backup policy set -g {} -v {} --policy \'{}\''
                 .format(resource_group, vault_name, policy1_json), checks=[
                     JMESPathCheck('name', policy3),
                     JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('backup policy list -g {} -v {}'.format(resource_group, vault_name), checks=[
            JMESPathCheck("length(@)", 5),
            JMESPathCheck("length([?name == '{}'])".format(default_policy), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy1), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy2), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy3), 1)])

        self.cmd('backup policy delete -g {} -v {} -n {}'.format(resource_group, vault_name, policy3))

        self.cmd('backup policy list -g {} -v {}'.format(resource_group, vault_name), checks=[
            JMESPathCheck("length(@)", 4),
            JMESPathCheck("length([?name == '{}'])".format(default_policy), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy1), 1),
            JMESPathCheck("length([?name == '{}'])".format(policy2), 1)])

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer(parameter_name='vm1')
    @VMPreparer(parameter_name='vm2')
    @ItemPreparer(vm_parameter_name='vm1')
    @ItemPreparer(vm_parameter_name='vm2')
    @PolicyPreparer()
    def test_item_commands(self, resource_group, vault_name, vm1, vm2, policy_name):
        container1 = self.cmd('backup container show -n {} -v {} -g {} --query properties.friendlyName'
                              .format(vm1, vault_name, resource_group)).get_output_in_json()
        container2 = self.cmd('backup container show -n {} -v {} -g {} --query properties.friendlyName'
                              .format(vm2, vault_name, resource_group)).get_output_in_json()

        default_policy = 'DefaultPolicy'

        item1_json = self.cmd('backup item show -g {} -v {} -c {} -n {}'
                              .format(resource_group, vault_name, container1, vm1), checks=[
                                  JMESPathCheck('properties.friendlyName', vm1),
                                  JMESPathCheck('properties.healthStatus', 'Passed'),
                                  JMESPathCheck('properties.protectionState', 'IRPending'),
                                  JMESPathCheck('properties.protectionStatus', 'Healthy'),
                                  JMESPathCheck('resourceGroup', resource_group)]).get_output_in_json()

        self.assertIn(vault_name.lower(), item1_json['id'].lower())
        self.assertIn(vm1.lower(), item1_json['name'].lower())
        self.assertIn(vm1.lower(), item1_json['properties']['sourceResourceId'].lower())
        self.assertIn(vm1.lower(), item1_json['properties']['virtualMachineId'].lower())
        self.assertIn(default_policy.lower(), item1_json['properties']['policyId'].lower())

        self.cmd('backup item list -g {} -v {} -c {}'
                 .format(resource_group, vault_name, container1), checks=[
                     JMESPathCheck("length(@)", 1),
                     JMESPathCheck("length([?properties.friendlyName == '{}'])".format(vm1), 1)])

        self.cmd('backup item list -g {} -v {} -c {}'
                 .format(resource_group, vault_name, container2), checks=[
                     JMESPathCheck("length(@)", 1),
                     JMESPathCheck("length([?properties.friendlyName == '{}'])".format(vm2), 1)])

        self.cmd('backup item set-policy -g {} -v {} -c {} -n {} -p {}'
                 .format(resource_group, vault_name, container1, vm1, policy_name), checks=[
                     JMESPathCheck("properties.entityFriendlyName", vm1),
                     JMESPathCheck("properties.operation", "ConfigureBackup"),
                     JMESPathCheck("properties.status", "Completed"),
                     JMESPathCheck("resourceGroup", resource_group)])

        item1_json = self.cmd('backup item show -g {} -v {} -c {} -n {}'
                              .format(resource_group, vault_name, container1, vm1)).get_output_in_json()
        self.assertIn(policy_name.lower(), item1_json['properties']['policyId'].lower())

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @RPPreparer()
    def test_rp_commands(self, resource_group, vault_name, vm_name):
        rp_names = self.cmd('backup recoverypoint list -g {} -v {} -c {} -i {} --query [].name'
                            .format(resource_group, vault_name, vm_name, vm_name), checks=[
                                JMESPathCheck("length(@)", 2)]).get_output_in_json()

        rp1_name = rp_names[0]
        rp1_json = self.cmd('backup recoverypoint show -g {} -v {} -c {} -i {} -n {}'
                            .format(resource_group, vault_name, vm_name, vm_name, rp1_name), checks=[
                                JMESPathCheck("name", rp1_name),
                                JMESPathCheck("resourceGroup", resource_group)]).get_output_in_json()
        self.assertIn(vault_name.lower(), rp1_json['id'].lower())
        self.assertIn(vm_name.lower(), rp1_json['id'].lower())

        rp2_name = rp_names[1]
        rp2_json = self.cmd('backup recoverypoint show -g {} -v {} -c {} -i {} -n {}'
                            .format(resource_group, vault_name, vm_name, vm_name, rp2_name), checks=[
                                JMESPathCheck("name", rp2_name),
                                JMESPathCheck("resourceGroup", resource_group)]).get_output_in_json()
        self.assertIn(vault_name.lower(), rp2_json['id'].lower())
        self.assertIn(vm_name.lower(), rp2_json['id'].lower())

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer()
    def test_protection_commands(self, resource_group, vault_name, vm_name):
        self.cmd('backup protection enable-for-vm -g {} -v {} --vm {} -p DefaultPolicy'
                 .format(resource_group, vault_name, vm_name), checks=[
                     JMESPathCheck("properties.entityFriendlyName", vm_name),
                     JMESPathCheck("properties.operation", "ConfigureBackup"),
                     JMESPathCheck("properties.status", "Completed"),
                     JMESPathCheck("resourceGroup", resource_group)])

        self.cmd('backup protection disable -g {} -v {} -c {} -i {} --yes'
                 .format(resource_group, vault_name, vm_name, vm_name), checks=[
                     JMESPathCheck("properties.entityFriendlyName", vm_name),
                     JMESPathCheck("properties.operation", "DisableBackup"),
                     JMESPathCheck("properties.status", "Completed"),
                     JMESPathCheck("resourceGroup", resource_group)])

        self.cmd('backup item show -g {} -v {} -c {} -n {}'
                 .format(resource_group, vault_name, vm_name, vm_name), checks=[
                     JMESPathCheck("properties.friendlyName", vm_name),
                     JMESPathCheck("properties.protectionState", "ProtectionStopped"),
                     JMESPathCheck("resourceGroup", resource_group)])

        self.cmd('backup protection disable -g {} -v {} -c {} -i {} --delete-backup-data true --yes'
                 .format(resource_group, vault_name, vm_name, vm_name), checks=[
                     JMESPathCheck("properties.entityFriendlyName", vm_name),
                     JMESPathCheck("properties.operation", "DeleteBackupData"),
                     JMESPathCheck("properties.status", "Completed"),
                     JMESPathCheck("resourceGroup", resource_group)])

        self.cmd('backup container list -v {} -g {}'
                 .format(vault_name, resource_group), checks=[
                     JMESPathCheck("length(@)", 0)])

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer()
    def test_restore_commands(self, resource_group, vault_name, vm_name, storage_account):
        rp_name = self.cmd('backup recoverypoint list -g {} -v {} -c {} -i {} --query [0].name'
                           .format(resource_group, vault_name, vm_name, vm_name)).get_output_in_json()

        # Trigger Restore
        restore_cmd_string = 'backup restore restore-disks'
        restore_cmd_string += ' -g {} -v {}'.format(resource_group, vault_name)
        restore_cmd_string += ' -c {} -i {} -r {}'.format(vm_name, vm_name, rp_name)
        restore_cmd_string += ' --storage-account {}'.format(storage_account)
        trigger_restore_job_json = self.cmd(restore_cmd_string, checks=[
            JMESPathCheck("properties.entityFriendlyName", vm_name),
            JMESPathCheck("properties.operation", "Restore"),
            JMESPathCheck("properties.status", "InProgress"),
            JMESPathCheck("resourceGroup", resource_group)
        ]).get_output_in_json()
        trigger_restore_job_name = trigger_restore_job_json['name']
        self.cmd('backup job wait -g {} -v {} -n {}'.format(resource_group, vault_name, trigger_restore_job_name))

        trigger_restore_job_details = self.cmd('backup job show -g {} -v {} -n {}'
                                               .format(resource_group, vault_name, trigger_restore_job_name), checks=[
                                                   JMESPathCheck("properties.entityFriendlyName", vm_name),
                                                   JMESPathCheck("properties.operation", "Restore"),
                                                   JMESPathCheck("properties.status", "Completed"),
                                                   JMESPathCheck("resourceGroup", resource_group)
                                               ]).get_output_in_json()

        property_bag = trigger_restore_job_details['properties']['extendedInfo']['propertyBag']
        self.assertEqual(property_bag['Target Storage Account Name'], storage_account)

        restore_container = property_bag['Config Blob Container Name']
        restore_blob = property_bag['Config Blob Name']

        self.cmd('storage blob exists --account-name {} -c {} -n {}'
                 .format(storage_account, restore_container, restore_blob), checks=[
                     JMESPathCheck("exists", True)])

    @ResourceGroupPreparer()
    @VaultPreparer()
    @VMPreparer()
    @ItemPreparer()
    @RPPreparer()
    @StorageAccountPreparer()
    def test_job_commands(self, resource_group, vault_name, vm_name, storage_account):
        rp_name = self.cmd('backup recoverypoint list -g {} -v {} -c {} -i {} --query [0].name'
                           .format(resource_group, vault_name, vm_name, vm_name)).get_output_in_json()

        restore_cmd_string = 'backup restore restore-disks'
        restore_cmd_string += ' -g {} -v {}'.format(resource_group, vault_name)
        restore_cmd_string += ' -c {} -i {} -r {}'.format(vm_name, vm_name, rp_name)
        restore_cmd_string += ' --storage-account {} --query name'.format(storage_account)
        trigger_restore_job_name = self.cmd(restore_cmd_string).get_output_in_json()

        self.cmd('backup job show -g {} -v {} -n {}'
                 .format(resource_group, vault_name, trigger_restore_job_name), checks=[
                     JMESPathCheck("name", trigger_restore_job_name),
                     JMESPathCheck("properties.entityFriendlyName", vm_name),
                     JMESPathCheck("properties.operation", "Restore"),
                     JMESPathCheck("properties.status", "InProgress"),
                     JMESPathCheck("resourceGroup", resource_group)])

        self.cmd('backup job list -g {} -v {}'.format(resource_group, vault_name), checks=[
            JMESPathCheck("length([?name == '{}'])".format(trigger_restore_job_name), 1)])

        self.cmd('backup job list -g {} -v {} --status InProgress'.format(resource_group, vault_name), checks=[
            JMESPathCheck("length([?name == '{}'])".format(trigger_restore_job_name), 1)])

        self.cmd('backup job list -g {} -v {} --operation Restore'.format(resource_group, vault_name), checks=[
            JMESPathCheck("length([?name == '{}'])".format(trigger_restore_job_name), 1)])

        self.cmd('backup job list -g {} -v {} --operation Restore --status InProgress'
                 .format(resource_group, vault_name), checks=[
                     JMESPathCheck("length([?name == '{}'])".format(trigger_restore_job_name), 1)])

        self.cmd('backup job stop -g {} -v {} -n {}'.format(resource_group, vault_name, trigger_restore_job_name))

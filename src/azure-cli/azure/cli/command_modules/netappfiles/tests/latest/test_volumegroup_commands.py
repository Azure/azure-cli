# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import time
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.decorators import serial_test

LOCATION = "northeurope"
VNET_LOCATION = "northeurope"
VNET_NAME = "vnetnortheurope-anf"
RESOURCE_GROUP = "sdk-net-test-qa2"
PPG = "/subscriptions/69a75bda-882e-44d5-8431-63421204132a/resourceGroups/sdk-net-test-qa2/providers/Microsoft.Compute/proximityPlacementGroups/sdk_test_northeurope_ppg"


class AzureNetAppFilesVolumeGroupServiceScenarioTest(ScenarioTest):
    def prepare_for_volume_group_creation(self):
        # Create account and pool
        self.kwargs.update({
            'loc': LOCATION,
            'rg': RESOURCE_GROUP,
            'acc': self.create_random_name(prefix='cli-acc-', length=24),
            'pool': self.create_random_name(prefix='cli-pool-', length=24),
            'service_level': 'Premium',
            'pool_size': 20,
            'qos': 'Manual'
        })
        self.cmd("az netappfiles account create -g {rg} -a {acc} -l {loc}")
        self.cmd("az netappfiles pool create -g {rg} -a {acc} -p {pool} -l {loc} --service-level {service_level} "
                 "--size {pool_size} --qos-type {qos}")
#    @unittest.skip('(drp failure) DRP stamp pinning failing on the environment, no way to test until fixed')
    def test_create_get_list_delete_volume_group(self):
        # Create Volume Group with defaults
        self.prepare_for_volume_group_creation()
        self.kwargs.update({
            'vg_name': 'cli-test-volume-group-001',
            'vnet': VNET_NAME,
            'application_identifier': "sh1",
            'application_type': "SAP-HANA",
            'ppg': PPG,
            'zones': 1,
            'sap_sid': "CLI",
            'gpr': "'key1=value1' 'key2=value2'"
        })
        self.cmd("az netappfiles volume-group create -g {rg} -a {acc} -p {pool} --volume-group-name {vg_name} "
                 "--vnet {vnet} --zones {zones} --application-identifier {application_identifier} -l {loc} --application-type {application_type} --gp-rules {gpr}",
                 checks=[
                     self.check('name', '{acc}/{vg_name}'),
                     self.check('groupMetaData.volumesCount', 5),
                     self.check('groupMetaData.applicationIdentifier', '{application_identifier}'),
                     self.check('length(volumes)', 5)
                 ])

        # Get Volume Group
        self.cmd("az netappfiles volume-group show -g {rg} -a {acc} --volume-group-name {vg_name}",
                 checks=[
                     self.check('name', '{acc}/{vg_name}'),
                     self.check('groupMetaData.volumesCount', 5),
                     self.check('groupMetaData.applicationIdentifier', '{application_identifier}'),
                     self.check('length(volumes)', 5)
                 ])

        # List Volume Groups
        self.cmd("az netappfiles volume-group list -g {rg} -a {acc}",
                 checks=[
                     self.check('length(@)', 1)
                 ])

        # Cleanup
        self.kwargs.update({
            'vol_1': 'sh1-data-mnt00001',
            'vol_2': 'sh1-log-mnt00001',
            'vol_3': 'sh1-shared',
            'vol_4': 'sh1-data-backup',
            'vol_5': 'sh1-log-backup'
        })
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_1} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_2} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_3} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_4} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_5} --yes")

        if (self.is_live or self.in_recording):
            time.sleep(20)
        # Delete Volume Group
        self.cmd("az netappfiles volume-group delete -g {rg} -a {acc} --volume-group-name {vg_name} -y --yes")

        # Delete pool and account
        self.cmd("az netappfiles pool delete -g {rg} -a {acc} -p {pool} -y")
        if (self.is_live or self.in_recording):
            time.sleep(20)
        self.cmd("az netappfiles account delete -g {rg} -a {acc} -y")

    #@unittest.skip('(drp failure) DRP stamp pinning failing on the environment, no way to test until fixed')
    def test_oracle_volume_groups(self):
        # Create Volume Group with minimum size
        self.prepare_for_volume_group_creation()
        self.kwargs.update({
            'vg_name': 'cli-test-volume-group-001',
            'vnet': VNET_NAME,
            'ppg': PPG,
            'zones': 1,
            'application_identifier': "or1",
            'application_type': "ORACLE",
            'add_snap_cap': 0,
            'size': 100,
            'throughput': 64
        })
        self.cmd("az netappfiles volume-group create -g {rg} -a {acc} -p {pool} --group-name {vg_name} --vnet {vnet} "
                 "--zones {zones} --application-identifier {application_identifier} --application-type {application_type} -l {loc} --add-snapshot-capacity {add_snap_cap} "
                 "--database-size {size} --database-throughput 120 --number-of-volumes 2",
                 checks=[
                     self.check('name', '{acc}/{vg_name}'),
                     self.check('groupMetaData.volumesCount', 6),
                     self.check('groupMetaData.applicationIdentifier', '{application_identifier}'),
                     self.check('length(volumes)', 6)
                 ])


        # Cleanup
        self.kwargs.update({
            'vol_1': 'or1-ora-data1',
            'vol_2': 'or1-ora-data2',
            'vol_3': 'or1-ora-log',
            'vol_4': 'or1-ora-binary',
            'vol_5': 'or1-ora-backup',
            'vol_6': 'or1-ora-log-mirror'
        })
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_1} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_2} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_3} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_4} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_5} --yes")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_6} --yes")

        if (self.is_live or self.in_recording):
            time.sleep(20)
        # Delete Volume Group
        self.cmd("az netappfiles volume-group delete -g {rg} -a {acc} --group-name {vg_name} -y")
        if (self.is_live or self.in_recording):
            time.sleep(20)
        # Delete pool and account
        self.cmd("az netappfiles pool delete -g {rg} -a {acc} -p {pool} -y")
        if (self.is_live or self.in_recording):
            time.sleep(20)
        self.cmd("az netappfiles account delete -g {rg} -a {acc} -y")

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
        self.cmd("az account set -s 69a75bda-882e-44d5-8431-63421204132a")
        self.cmd("az netappfiles account create -g {rg} -a {acc} -l {loc}")
        self.cmd("az netappfiles pool create -g {rg} -a {acc} -p {pool} -l {loc} --service-level {service_level} "
                 "--size {pool_size} --qos-type {qos}")

    @serial_test()
    def test_create_get_list_delete_volume_group(self):
        # Create Volume Group with defaults
        self.prepare_for_volume_group_creation()
        self.kwargs.update({
            'vg_name': 'cli-test-volume-group-001',
            'vnet': VNET_NAME,
            'ppg': PPG,
            'sap_sid': "CLI",
            'gpr': "'key1=value1' 'key2=value2'"
        })
        self.cmd("az netappfiles volume-group create -g {rg} -a {acc} -p {pool} --volume-group-name {vg_name} "
                 "--vnet {vnet} --ppg {ppg} --sap-sid {sap_sid} -l {loc} --global-placement-rules {gpr}",
                 checks=[
                     self.check('name', '{acc}/{vg_name}'),
                     self.check('groupMetaData.groupName', '{vg_name}'),
                     self.check('groupMetaData.volumesCount', 5),
                     self.check('groupMetaData.applicationIdentifier', 'DEV'),
                     self.check('length(volumes)', 5)
                 ])

        # Get Volume Group
        self.cmd("az netappfiles volume-group show -g {rg} -a {acc} -n {vg_name}",
                 checks=[
                     self.check('name', '{acc}/{vg_name}'),
                     self.check('groupMetaData.groupName', '{vg_name}'),
                     self.check('groupMetaData.volumesCount', 5),
                     self.check('groupMetaData.applicationIdentifier', 'DEV'),
                     self.check('length(volumes)', 5)
                 ])

        # List Volume Groups
        self.cmd("az netappfiles volume-group list -g {rg} -a {acc}",
                 checks=[
                     self.check('length(@)', 1)
                 ])

        # Cleanup
        self.kwargs.update({
            'vol_1': 'CLI-log-backup',
            'vol_2': 'CLI-data-backup',
            'vol_3': 'CLI-shared',
            'vol_4': 'CLI-log-mnt00001',
            'vol_5': 'CLI-data-mnt00001'
        })
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_1}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_2}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_3}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_4}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_5}")

        # Delete Volume Group
        self.cmd("az netappfiles volume-group delete -g {rg} -a {acc} -n {vg_name} -y")

        # Delete pool and account
        self.cmd("az netappfiles pool delete -g {rg} -a {acc} -p {pool}")
        self.cmd("az netappfiles account delete -g {rg} -a {acc}")

    def test_hrs_volume_groups(self):
        # Create Volume Group with minimum size
        self.prepare_for_volume_group_creation()
        self.kwargs.update({
            'vg_name': 'cli-test-volume-group-001',
            'vnet': VNET_NAME,
            'ppg': PPG,
            'sap_sid': "CLI",
            'add_snap_cap': 0,
            'size': 100,
            'throughput': 64
        })
        self.cmd("az netappfiles volume-group create -g {rg} -a {acc} -p {pool} --name {vg_name} "
                 "--vnet {vnet} --ppg {ppg} --sap-sid {sap_sid} -l {loc} "
                 "--add-snapshot-capacity {add_snap_cap} --data-size {size} --data-throughput {throughput} "
                 "--log-size {size} --log-throughput {throughput} --shared-size {size} "
                 "--shared-throughput {throughput} --data-backup-size {size} --data-backup-throughput {throughput} "
                 "--log-backup-size {size} --log-backup-throughput {throughput}",
                 checks=[
                     self.check('name', '{acc}/{vg_name}'),
                     self.check('groupMetaData.groupName', '{vg_name}'),
                     self.check('groupMetaData.volumesCount', 5),
                     self.check('groupMetaData.applicationIdentifier', 'DEV'),
                     self.check('length(volumes)', 5)
                 ])

        # Create HRS Volume Group
        # self.prepare_for_volume_group_creation()
        self.kwargs.update({
            'vg_ha_name': 'cli-test-volume-group-HA',
            'system_role': 'HA'
        })
        self.cmd("az netappfiles volume-group create -g {rg} -a {acc} -p {pool} --volume-group-name {vg_ha_name} "
                 "--vnet {vnet} --ppg {ppg} --sap-sid {sap_sid} -l {loc} "
                 "--add-snapshot-capacity {add_snap_cap} --data-size {size} --data-throughput {throughput} "
                 "--log-size {size} --log-throughput {throughput} --shared-size {size} "
                 "--shared-throughput {throughput} --data-backup-size {size} --data-backup-throughput {throughput} "
                 "--log-backup-size {size} --log-backup-throughput {throughput} --system-role {system_role}",
                 checks=[
                     self.check('name', '{acc}/{vg_ha_name}'),
                     self.check('groupMetaData.groupName', '{vg_ha_name}'),
                     self.check('groupMetaData.volumesCount', 5),
                     self.check('groupMetaData.applicationIdentifier', 'DEV'),
                     self.check('length(volumes)', 5)
                 ])

        # Cleanup
        self.kwargs.update({
            'vol_1': 'CLI-log-backup',
            'vol_2': 'CLI-data-backup',
            'vol_3': 'CLI-shared',
            'vol_4': 'CLI-log-mnt00001',
            'vol_5': 'CLI-data-mnt00001'
        })
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_1}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_2}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_3}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_4}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_5}")

        self.kwargs.update({
            'vol_1': 'HA-CLI-log-backup',
            'vol_2': 'HA-CLI-data-backup',
            'vol_3': 'HA-CLI-shared',
            'vol_4': 'HA-CLI-log-mnt00001',
            'vol_5': 'HA-CLI-data-mnt00001'
        })
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_1}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_2}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_3}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_4}")
        self.cmd("az netappfiles volume delete -g {rg} -a {acc} -p {pool} -v {vol_5}")

        # Delete Volume Group
        self.cmd("az netappfiles volume-group delete -g {rg} -a {acc} -n {vg_name} -y")
        self.cmd("az netappfiles volume-group delete -g {rg} -a {acc} -n {vg_ha_name} -y")

        # Delete pool and account
        self.cmd("az netappfiles pool delete -g {rg} -a {acc} -p {pool}")
        self.cmd("az netappfiles account delete -g {rg} -a {acc}")

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

LOCATION = "southcentralusstage"
VNET_LOCATION = "southcentralus"
VOLUME_DEFAULT = "--service-level 'Premium' --usage-threshold 100"
vnet_name = "cli-vnet-lefr-02"
subnet_name = "default"


class AzureNetAppFilesSnapshotPolicyServiceScenarioTest(ScenarioTest):
    def setup_vnet(self, vnet_name, subnet_name):
        self.cmd("az network vnet create -n %s -g {rg} -l %s --address-prefix 10.5.0.0/16" %
                 (vnet_name, VNET_LOCATION))
        self.cmd("az network vnet subnet create -n %s --vnet-name %s --address-prefixes '10.5.0.0/24' "
                 "--delegations 'Microsoft.Netapp/volumes' -g {rg}" % (subnet_name, vnet_name))

    def current_subscription(self):
        subs = self.cmd("az account show").get_output_in_json()
        return subs['id']

    def create_volume(self, account_name, pool_name, volume_name, snapshot_policy_id=None, volume_only=False):
        if not volume_only:
            # create vnet and pool
            self.setup_vnet(vnet_name, subnet_name)
            self.cmd("netappfiles pool create -g {rg} -a %s -p %s -l %s --service-level 'Premium' --size 4" %
                     (account_name, pool_name, LOCATION))

        snapshot = "--snapshot-policy-id %s" % snapshot_policy_id if snapshot_policy_id is not None else ""

        # create volume
        return self.cmd("netappfiles volume create -g {rg} -a %s -p %s -v %s -l %s --vnet %s --subnet %s "
                        "--file-path %s %s %s" %
                        (account_name, pool_name, volume_name, LOCATION, vnet_name, subnet_name, volume_name,
                         VOLUME_DEFAULT, snapshot)).get_output_in_json()

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_policy_', additional_tags={'owner': 'cli_test'})
    def test_create_delete_snapshot_policies(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        snapshot_policy_name = self.create_random_name(prefix='cli-sn-pol-', length=16)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create snapshot policy using long parameter names and validate result
        hourly_snapshots_to_keep = 1
        hourly_minute = 10
        daily_snapshots_to_keep = 2
        daily_minute = 20
        daily_hour = 2
        weekly_snapshots_to_keep = 3
        weekly_minute = 30
        weekly_hour = 3
        weekly_day = "Monday"
        monthly_snapshots_to_keep = 4
        monthly_minute = 40
        monthly_hour = 4
        monthly_days_of_month = "1,3,20"
        enabled = True
        tags = "Tag1=Value1"
        snapshot_policy = self.cmd("az netappfiles snapshot policy create -g {rg} -a %s --snapshot-policy-name %s "
                                   "--location %s --hourly-snapshots %s --daily-snapshots %s "
                                   "--weekly-snapshots %s --monthly-snapshots %s --hourly-minute %s "
                                   "--daily-minute %s --weekly-minute %s --monthly-minute %s --daily-hour %s "
                                   "--weekly-hour %s --monthly-hour %s --weekly-day %s --monthly-days %s "
                                   "--enabled %s --tags %s" %
                                   (account_name, snapshot_policy_name, LOCATION, hourly_snapshots_to_keep,
                                    daily_snapshots_to_keep, weekly_snapshots_to_keep, monthly_snapshots_to_keep,
                                    hourly_minute, daily_minute, weekly_minute, monthly_minute, daily_hour, weekly_hour,
                                    monthly_hour, weekly_day, monthly_days_of_month, enabled, tags)).get_output_in_json()
        assert snapshot_policy['name'] == account_name + "/" + snapshot_policy_name
        assert snapshot_policy['hourlySchedule']['snapshotsToKeep'] == hourly_snapshots_to_keep
        assert snapshot_policy['hourlySchedule']['minute'] == hourly_minute
        assert snapshot_policy['dailySchedule']['snapshotsToKeep'] == daily_snapshots_to_keep
        assert snapshot_policy['dailySchedule']['minute'] == daily_minute
        assert snapshot_policy['dailySchedule']['hour'] == daily_hour
        assert snapshot_policy['weeklySchedule']['snapshotsToKeep'] == weekly_snapshots_to_keep
        assert snapshot_policy['weeklySchedule']['minute'] == weekly_minute
        assert snapshot_policy['weeklySchedule']['hour'] == weekly_hour
        assert snapshot_policy['weeklySchedule']['day'] == weekly_day
        assert snapshot_policy['monthlySchedule']['snapshotsToKeep'] == monthly_snapshots_to_keep
        assert snapshot_policy['monthlySchedule']['minute'] == monthly_minute
        assert snapshot_policy['monthlySchedule']['hour'] == monthly_hour
        assert snapshot_policy['monthlySchedule']['daysOfMonth'] == monthly_days_of_month
        assert snapshot_policy['enabled'] == enabled
        assert snapshot_policy['tags']['Tag1'] == 'Value1'
        assert snapshot_policy['provisioningState'] is not None

        # validate snapshot policy exist
        snapshot_policy_list = self.cmd("az netappfiles snapshot policy list -g {rg} -a '%s'" %
                                        account_name).get_output_in_json()
        assert len(snapshot_policy_list) == 1

        # delete snapshot policy
        self.cmd("az netappfiles snapshot policy delete -g {rg} -a %s --snapshot-policy-name %s" %
                 (account_name, snapshot_policy_name))

        # create snapshot policy using short parameter names and validate result
        snapshot_policy = self.cmd("az netappfiles snapshot policy create -g {rg} -a %s "
                                   "--snapshot-policy-name %s -l %s -u %s -d %s -w %s -m %s "
                                   "--hourly-minute %s --daily-minute %s --weekly-minute %s --monthly-minute %s "
                                   "--daily-hour %s --weekly-hour %s --monthly-hour %s --weekly-day %s "
                                   "--monthly-days %s --enabled %s --tags %s" %
                                   (account_name, snapshot_policy_name, LOCATION, hourly_snapshots_to_keep,
                                    daily_snapshots_to_keep, weekly_snapshots_to_keep, monthly_snapshots_to_keep,
                                    hourly_minute, daily_minute, weekly_minute, monthly_minute, daily_hour, weekly_hour,
                                    monthly_hour, weekly_day, monthly_days_of_month, enabled, tags)).get_output_in_json()
        assert snapshot_policy['name'] == account_name + "/" + snapshot_policy_name
        assert snapshot_policy['hourlySchedule']['snapshotsToKeep'] == hourly_snapshots_to_keep
        assert snapshot_policy['hourlySchedule']['minute'] == hourly_minute
        assert snapshot_policy['dailySchedule']['snapshotsToKeep'] == daily_snapshots_to_keep
        assert snapshot_policy['dailySchedule']['minute'] == daily_minute
        assert snapshot_policy['dailySchedule']['hour'] == daily_hour
        assert snapshot_policy['weeklySchedule']['snapshotsToKeep'] == weekly_snapshots_to_keep
        assert snapshot_policy['weeklySchedule']['minute'] == weekly_minute
        assert snapshot_policy['weeklySchedule']['hour'] == weekly_hour
        assert snapshot_policy['weeklySchedule']['day'] == weekly_day
        assert snapshot_policy['monthlySchedule']['snapshotsToKeep'] == monthly_snapshots_to_keep
        assert snapshot_policy['monthlySchedule']['minute'] == monthly_minute
        assert snapshot_policy['monthlySchedule']['hour'] == monthly_hour
        assert snapshot_policy['monthlySchedule']['daysOfMonth'] == monthly_days_of_month
        assert snapshot_policy['enabled'] == enabled
        assert snapshot_policy['tags']['Tag1'] == 'Value1'

        # delete snapshot policy
        self.cmd("az netappfiles snapshot policy delete -g {rg} -a %s --snapshot-policy-name %s" %
                 (account_name, snapshot_policy_name))

        # validate snapshot policy doesn't exist
        snapshot_policy_list = self.cmd("az netappfiles snapshot policy list -g {rg} -a '%s'" %
                                        account_name).get_output_in_json()
        assert len(snapshot_policy_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_policy_', additional_tags={'owner': 'cli_test'})
    def test_list_snapshot_policy(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create 3 snapshot policies
        snapshot_policies = [self.create_random_name(prefix='cli', length=16),
                             self.create_random_name(prefix='cli', length=16),
                             self.create_random_name(prefix='cli', length=16)]
        hourly_snapshots_to_keep = 1
        hourly_minute = 10
        for snapshot_policy_name in snapshot_policies:
            self.cmd("az netappfiles snapshot policy create -g {rg} -a %s --snapshot-policy-name %s -l %s -u %s --hourly-minute %s" %
                     (account_name, snapshot_policy_name, LOCATION, hourly_snapshots_to_keep, hourly_minute))

        # validate that both snapshot policies exist
        snapshot_policy_list = self.cmd("az netappfiles snapshot policy list -g {rg} -a '%s'" %
                                        account_name).get_output_in_json()
        assert len(snapshot_policy_list) == 3

        # delete all snapshot policies
        for snapshot_policy_name in snapshot_policies:
            self.cmd("az netappfiles snapshot policy delete -g {rg} -a %s --snapshot-policy-name %s" %
                     (account_name, snapshot_policy_name))

        # validate that no snapshot policies exist
        snapshot_policy_list = self.cmd("az netappfiles snapshot policy list -g {rg} -a '%s'" %
                                        account_name).get_output_in_json()
        assert len(snapshot_policy_list) == 0

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_policy_', additional_tags={'owner': 'cli_test'})
    def test_get_snapshot_policy_by_name(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create snapshot policy
        snapshot_policy_name = self.create_random_name(prefix='cli-sn-pol-', length=16)
        hourly_snapshots = 1
        hourly_minute = 10
        self.cmd("az netappfiles snapshot policy create -g {rg} -a %s --snapshot-policy-name %s -l %s -u %s --hourly-minute %s" %
                 (account_name, snapshot_policy_name, LOCATION, hourly_snapshots, hourly_minute)).get_output_in_json()

        # get snapshot policy by name and validate
        snapshot_policy = self.cmd("az netappfiles snapshot policy show -g {rg} -a %s --snapshot-policy-name %s" %
                                   (account_name, snapshot_policy_name)).get_output_in_json()
        assert snapshot_policy['name'] == account_name + '/' + snapshot_policy_name
        assert snapshot_policy['hourlySchedule']['snapshotsToKeep'] == hourly_snapshots
        assert snapshot_policy['hourlySchedule']['minute'] == hourly_minute

        # get snapshot policy by resource id and validate
        snapshot_policy_from_id = self.cmd("az netappfiles snapshot policy show --ids %s" %
                                           snapshot_policy['id']).get_output_in_json()
        assert snapshot_policy_from_id['name'] == account_name + '/' + snapshot_policy_name
        assert snapshot_policy['hourlySchedule']['snapshotsToKeep'] == hourly_snapshots
        assert snapshot_policy['hourlySchedule']['minute'] == hourly_minute

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_policy_', additional_tags={'owner': 'cli_test'})
    def test_update_snapshot_policy(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION)).get_output_in_json()

        # create snapshot policy
        snapshot_policy_name = self.create_random_name(prefix='cli-sn-pol-', length=16)
        hourly_snapshots_to_keep = 1
        hourly_minute = 10
        daily_snapshots_to_keep = 2
        daily_minute = 20
        daily_hour = 2
        weekly_snapshots_to_keep = 3
        weekly_minute = 30
        weekly_hour = 3
        weekly_day = "Monday"
        monthly_snapshots_to_keep = 4
        monthly_minute = 40
        monthly_hour = 4
        monthly_days_of_month = "2,5,30"
        enabled = True
        tags = "Tag1=Value1"
        self.cmd("az netappfiles snapshot policy create -g {rg} -a %s --snapshot-policy-name %s -l %s -u %s -d %s -w %s -m %s "
                 "--hourly-minute %s --daily-minute %s --weekly-minute %s --monthly-minute %s --daily-hour %s "
                 "--weekly-hour %s --monthly-hour %s --weekly-day %s --monthly-days %s --enabled %s --tags %s" %
                 (account_name, snapshot_policy_name, LOCATION, hourly_snapshots_to_keep,
                  daily_snapshots_to_keep, weekly_snapshots_to_keep, monthly_snapshots_to_keep,
                  hourly_minute, daily_minute, weekly_minute, monthly_minute, daily_hour, weekly_hour,
                  monthly_hour, weekly_day, monthly_days_of_month, enabled, tags)).get_output_in_json()

        # update snapshot policy
        hourly_snapshots_to_keep = 5
        hourly_minute = 50
        daily_snapshots_to_keep = 6
        daily_minute = 0
        daily_hour = 6
        weekly_snapshots_to_keep = 7
        weekly_minute = 10
        weekly_hour = 7
        weekly_day = "Wednesday"
        monthly_snapshots_to_keep = 8
        monthly_minute = 20
        monthly_hour = 8
        monthly_days_of_month = "1,2,20"
        enabled = False
        self.cmd("az netappfiles snapshot policy update -g {rg} -a %s --snapshot-policy-name %s -l %s -u %s -d %s -w %s -m %s "
                 "--hourly-minute %s --daily-minute %s --weekly-minute %s --monthly-minute %s --daily-hour %s "
                 "--weekly-hour %s --monthly-hour %s --weekly-day %s --monthly-days %s --enabled %s" %
                 (account_name, snapshot_policy_name, LOCATION, hourly_snapshots_to_keep,
                  daily_snapshots_to_keep, weekly_snapshots_to_keep, monthly_snapshots_to_keep,
                  hourly_minute, daily_minute, weekly_minute, monthly_minute, daily_hour, weekly_hour,
                  monthly_hour, weekly_day, monthly_days_of_month, enabled)).get_output_in_json()

        # get updated snapshot policy and validate update
        snapshot_policy = self.cmd("az netappfiles snapshot policy show -g {rg} -a %s --snapshot-policy-name %s" %
                                   (account_name, snapshot_policy_name)).get_output_in_json()
        assert snapshot_policy['name'] == account_name + "/" + snapshot_policy_name
        assert snapshot_policy['hourlySchedule']['snapshotsToKeep'] == hourly_snapshots_to_keep
        assert snapshot_policy['hourlySchedule']['minute'] == hourly_minute
        assert snapshot_policy['dailySchedule']['snapshotsToKeep'] == daily_snapshots_to_keep
        assert snapshot_policy['dailySchedule']['minute'] == daily_minute
        assert snapshot_policy['dailySchedule']['hour'] == daily_hour
        assert snapshot_policy['weeklySchedule']['snapshotsToKeep'] == weekly_snapshots_to_keep
        assert snapshot_policy['weeklySchedule']['minute'] == weekly_minute
        assert snapshot_policy['weeklySchedule']['hour'] == weekly_hour
        assert snapshot_policy['weeklySchedule']['day'] == weekly_day
        assert snapshot_policy['monthlySchedule']['snapshotsToKeep'] == monthly_snapshots_to_keep
        assert snapshot_policy['monthlySchedule']['minute'] == monthly_minute
        assert snapshot_policy['monthlySchedule']['hour'] == monthly_hour
        assert snapshot_policy['monthlySchedule']['daysOfMonth'] == monthly_days_of_month
        assert snapshot_policy['enabled'] == enabled
        assert snapshot_policy['tags']['Tag1'] == 'Value1'

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_policy_', additional_tags={'owner': 'cli_test'})
    def test_snapshot_policy_list_volumes(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION))

        # create snapshot policy
        snapshot_policy_name = self.create_random_name(prefix='cli-sn-pol-', length=16)
        hourly_snapshots_to_keep = 1
        hourly_minute = 10
        enabled = True
        self.cmd("az netappfiles snapshot policy create -g {rg} -a %s --snapshot-policy-name %s -l %s -u %s --hourly-minute %s --enabled %s"
                 % (account_name, snapshot_policy_name, LOCATION, hourly_snapshots_to_keep, hourly_minute, enabled))

        snapshot_policy = self.cmd("az netappfiles snapshot policy show -g {rg} -a %s --snapshot-policy-name %s" %
                                   (account_name, snapshot_policy_name)).get_output_in_json()

        # create volume
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.create_volume(account_name, pool_name, volume_name, snapshot_policy_id=snapshot_policy['id'])

        list_volumes = self.cmd("az netappfiles snapshot policy volumes -g {rg} -a %s --snapshot-policy-name %s" %
                                (account_name, snapshot_policy_name)).get_output_in_json()

        assert len(list_volumes['value']) == 1

        # create second volume
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.create_volume(account_name, pool_name, volume_name, snapshot_policy_id=snapshot_policy['id'],
                           volume_only=True)

        list_volumes = self.cmd("az netappfiles snapshot policy volumes -g {rg} -a %s --snapshot-policy-name %s" %
                                (account_name, snapshot_policy_name)).get_output_in_json()

        assert len(list_volumes['value']) == 2

    @ResourceGroupPreparer(name_prefix='cli_netappfiles_test_snapshot_policy_', additional_tags={'owner': 'cli_test'})
    def test_assign_snapshot_policy_to_volume(self):
        # create account
        account_name = self.create_random_name(prefix='cli-acc-', length=24)
        self.cmd("az netappfiles account create -g {rg} -a '%s' -l %s" % (account_name, LOCATION))

        # create volume
        pool_name = self.create_random_name(prefix='cli-pool-', length=24)
        volume_name = self.create_random_name(prefix='cli-vol-', length=24)
        self.create_volume(account_name, pool_name, volume_name)

        # create snapshot policy
        snapshot_policy_name = self.create_random_name(prefix='cli-sn-pol-', length=16)
        hourly_snapshots_to_keep = 1
        hourly_minute = 10
        enabled = True
        self.cmd("az netappfiles snapshot policy create -g {rg} -a %s --snapshot-policy-name %s -l %s -u %s "
                 "--hourly-minute %s --enabled %s" % (account_name, snapshot_policy_name, LOCATION,
                                                      hourly_snapshots_to_keep, hourly_minute, enabled))
        snapshot_policy = self.cmd("az netappfiles snapshot policy show -g {rg} -a %s --snapshot-policy-name %s" %
                                   (account_name, snapshot_policy_name)).get_output_in_json()

        # assign snapshot policy to the volume
        self.cmd("az netappfiles volume update -g {rg} -a %s -p %s -v %s --snapshot-policy-id %s" %
                 (account_name, pool_name, volume_name, snapshot_policy['id']))

        volume = self.cmd("az netappfiles volume show -g {rg} -a %s -p %s -v %s" %
                          (account_name, pool_name, volume_name)).get_output_in_json()
        assert volume['dataProtection']['snapshot']['snapshotPolicyId'] == snapshot_policy['id']

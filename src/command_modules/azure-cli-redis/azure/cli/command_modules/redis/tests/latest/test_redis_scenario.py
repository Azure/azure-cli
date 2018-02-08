# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class RedisCacheTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_redis')
    def test_redis_cache(self, resource_group):

        self.kwargs = {
            'rg': resource_group,
            'loc': 'WestUS',
            'name': self.create_random_name(prefix='redis', length=24),
            'sku': 'premium',
            'sku2': 'basic',
            'size': 'P1',
            'name2': self.create_random_name(prefix='redis', length=24),
            'size2': 'C0',
            'settings': "{\\\"hello\\\":1}",
            'schedule_entries': "[{\"dayOfWeek\":\"Monday\",\"startHourUtc\":\"00\",\"maintenanceWindow\":\"PT5H\"}]"
        }

        self.cmd('az redis create -n {name} -g {rg} -l {loc} --sku {sku} --vm-size {size}')

        self.cmd('az redis create -n {name2} -g {rg} -l {loc} --sku {sku2} --vm-size {size2} --tenant-settings {settings}')
        self.cmd('az redis show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('provisioningState', 'Creating')
        ])
        self.cmd('az redis list -g {rg}')
        self.cmd('az redis list-all')
        self.cmd('az redis list-keys -n {name} -g {rg}')
        self.cmd('az redis patch-schedule show -n {name} -g {rg}')
        self.cmd('az redis patch-schedule set -n {name} -g {rg} --schedule-entries {schedule_entries}')
        self.cmd('az redis firewall-rules list -n {name} -g {rg}')
        self.cmd('az redis linked-server list -n {name} -g {rg}')

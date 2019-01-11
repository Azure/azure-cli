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
            'loc': 'WestUS2',
            'name': self.create_random_name(prefix='redis', length=24),
            'sku': 'premium',
            'sku2': 'basic',
            'size': 'P1',
            'name2': self.create_random_name(prefix='redis', length=24),
            'size2': 'C0',
            'tls_version': '1.2',
            'tags': "{\\\"test\\\":\\\"tryingzones\\\"}",
            'zones': "{\\\"1\\\",\\\"2\\\"}",
            'settings': "{\\\"hello\\\":1}",
            'schedule_entries': "[{\\\"dayOfWeek\\\":\\\"Monday\\\",\\\"startHourUtc\\\":\\\"00\\\",\\\"maintenanceWindow\\\":\\\"PT5H\\\"}]",
            'schedule_entries_update': "[{\\\"dayOfWeek\\\":\\\"Tuesday\\\",\\\"startHourUtc\\\":\\\"01\\\",\\\"maintenanceWindow\\\":\\\"PT10H\\\"}]"
        }

        self.cmd('az redis create -n {name} -g {rg} -l {loc} --sku {sku} --vm-size {size} --minimum-tls-version {tls_version} --tags {tags} --zones {zones}')

        self.cmd('az redis create -n {name2} -g {rg} -l {loc} --sku {sku2} --vm-size {size2} --tenant-settings {settings}')
        self.cmd('az redis show -n {name} -g {rg}', checks=[
            self.check('name', '{name}'),
            self.check('provisioningState', 'Creating')
        ])
        self.cmd('az redis list')
        self.cmd('az redis list -g {rg}')
        self.cmd('az redis list-keys -n {name} -g {rg}')
        self.cmd('az redis patch-schedule create -n {name} -g {rg} --schedule-entries {schedule_entries}')
        self.cmd('az redis patch-schedule update -n {name} -g {rg} --schedule-entries {schedule_entries_update}')
        self.cmd('az redis patch-schedule show -n {name} -g {rg}')
        self.cmd('az redis patch-schedule delete -n {name} -g {rg}')
        self.cmd('az redis firewall-rules list -n {name} -g {rg}')
        self.cmd('az redis server-link list -n {name} -g {rg}')

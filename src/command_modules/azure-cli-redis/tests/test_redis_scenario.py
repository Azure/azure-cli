# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer

class RedisCacheTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_create_redis_cache(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.cmd('az redis create -n {} -g {} -l {} --sku {} --vm-size {}'.format(
            name, resource_group, 'WestUS', 'Basic','C0'))
        self.cmd('az redis show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('provisioningState', 'Creating')
        ])
        self.cmd('az redis list -g {}'.format(resource_group))
        self.cmd('az redis list-keys -n {} -g {}'.format(name, resource_group))

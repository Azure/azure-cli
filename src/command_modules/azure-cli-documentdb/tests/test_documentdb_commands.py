# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer


class DocumentDBTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_create_database_account(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.cmd(
            'az documentdb create -n {} -g {} '
            '--enable-automatic-failover {} --default-consistency-level {}'
            .format(name, resource_group, 'true', 'ConsistentPrefix'))
        self.cmd('az documentdb show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('properties.enableAutomaticFailover', 'true'),
            JMESPathCheck('properties.consistencyPolicy.defaultConsistencyLevel',
                          'ConsistentPrefix'),
        ])
        self.cmd('az documentdb list -g {}'.format(resource_group))
        self.cmd('az documentdb list-keys -n {} -g {}'.format(name, resource_group))
        self.cmd('az documentdb regenerate-key -n {} -g {} --key-kind {}'
                 .format(name, resource_group, 'primary'))
        self.cmd('az documentdb delete -n {} -g {}'.format(name, resource_group))

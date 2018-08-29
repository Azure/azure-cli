# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class ExampleTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_example')  # name_prefix not required, but can be useful
    def test_example(self, resource_group):

        # kwargs will already have resource_group with the key 'rg'
        self.kwargs = {
            'loc': 'WestUS',
            'name': self.create_random_name(prefix='redis', length=24),
        }

        # refer to kwarg keys directly in-line
        self.cmd('az example create -n {name} -g {rg} -l {loc}', check=[
            self.check('name', '{name}'),  # use kwarg keys within your checks
            self.check('resourceGroup', '{rg}'),
            self.check('location', '{loc}')
        ])
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class MediaServicesTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_ams')  # name_prefix not required, but can be useful
    def test_ams(self, resource_group):

        # kwargs will already have resource_group with the key 'rg'
        self.kwargs = {
            'location': 'east-us',
            'name': self.create_random_name(prefix='myms', length=24),
            'rg': self.create_random_name(prefix='myrg', length=24),
        }

        # refer to kwarg keys directly in-line
        self.cmd('az ams create -n {name} -rg {rg} --location {location}', check=[
            self.check('name', '{name}'),  # use kwarg keys within your checks
            self.check('rg', '{rg}'),
            self.check('location', '{location}')
        ])
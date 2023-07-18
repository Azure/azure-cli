# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import time


class MapsCreatorTest(ScenarioTest):

    @ResourceGroupPreparer(key='rg')
    def test_maps_creator(self, resource_group):
        tag_key = self.create_random_name(prefix='key-', length=10)
        tag_value = self.create_random_name(prefix='val-', length=10)

        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'creator_name': self.create_random_name(prefix='cli-', length=20),
            'sku': 's0',
            'skus1': 's1',
            'storage_units': 5,
            'tags': tag_key + '=' + tag_value,
        })

        self.cmd('az maps account create -n {name} -g {rg} --sku {skus1} --accept-tos')

        creator = self.cmd('az maps creator create -n {name} --creator-name {creator_name}'
                 ' -g {rg} --storage-units {storage_units} -l westus2',
                 checks=[
                     self.check('name', '{creator_name}'),
                     self.check('resourceGroup', '{rg}'),
                     self.check('properties.provisioningState', 'Created'),
                     self.check('properties.storageUnits', '{storage_units}'),
                     self.not_exists('tags')
                 ]).get_output_in_json()

        self.cmd('az maps creator update -n {name} --creator-name {creator_name} -g {rg} --storage-units 10 --tags {tags}',
                 checks=[
                     self.check('properties.provisioningState', 'Succeeded'),
                     self.check('properties.storageUnits', 10),
                     self.check('tags', {tag_key: tag_value})
                 ])

        af = self.cmd('az maps creator show -n {name} -g {rg} --creator-name {creator_name}', checks=[
            self.check('id', creator['id']),
            self.check('name', '{creator_name}'),
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('properties.storageUnits', 10),
            self.check('resourceGroup', '{rg}'),
            self.check('tags', {tag_key: tag_value})
        ]).get_output_in_json()

        self.cmd('az maps creator list -g {rg} -n {name}', checks=[
            self.check('length(@)', 1),
            self.check('type(@)', 'array'),
            self.check('[0].id', creator['id']),
            self.check('[0].name', '{creator_name}'),
            self.check('[0].properties.provisioningState', 'Succeeded'),
            self.check('[0].properties.storageUnits', 10),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].tags', {tag_key: tag_value})
        ]).get_output_in_json()

        self.cmd('az maps creator delete -n {name} --creator-name {creator_name} -g {rg} -y')
        time.sleep(20)
        self.cmd('az maps creator list -n {name} -g {rg}', checks=self.is_empty())

    @ResourceGroupPreparer(key='rg')
    def test_maps_map(self, resource_group):
        self.cmd('maps map list-operation', checks=[
            self.check('length(@)!="0"', True)
        ])

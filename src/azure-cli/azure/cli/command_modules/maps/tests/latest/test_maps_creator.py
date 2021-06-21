# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class MapsTest(ScenarioTest):

    @ResourceGroupPreparer(key='rg')
    def test_maps_creator(self, resource_group):
        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'creator_name': self.create_random_name(prefix='cli-', length=10),
            'sku': 's0',
            'skus1': 's1',
            'storage_units': 5,
            'tags': tag_key + '=' + tag_value,
            'key_type_primary': 'primary',
            'key_type_secondary': 'secondary'
        })
        self.cmd('az maps account create -n {name} -g {rg} --sku {skus1} --accept-tos')
        self.cmd('az maps creator create -n {name} --creator-name {creator_name}'
                 ' -g {rg} --storage-units {storage_units} -l westus2',
                 checks=[
                     self.check('name', '{creator_name}'),
                     self.check('resourceGroup', '{rg}'),
                     self.check('properties.provisioningState', 'Created'),
                     self.check('properties.storageUnits', 'storage_units'),
                     self.not_exists('tags')
                 ])
        self.cmd('az maps creator update -n {name} --creator-name {creator_name} -g {rg} --storage-units 10',
                 checks=[
                     self.check('properties.provisioningState', 'Succeeded'),
                     self.check('properties.storageUnits', 10)
                 ])
    @ResourceGroupPreparer(key='rg')
    def test_maps_map(self, resource_group):
        self.cmd('maps maps list-operation')

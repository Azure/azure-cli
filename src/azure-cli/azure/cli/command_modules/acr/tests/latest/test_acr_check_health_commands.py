# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

class AcrCheckHealthCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_check_health(self, repository_name, image):
        registry_name = self.create_random_name('clireg', 20)
        image = 'latest'
        self.kwargs.update({
            'registry': registry_name,
            'ignore_errors': False,
            'yes': False,
            'vnet': None,
            'repository': repository_name,
            'image': image,
            'reason': 'OK'
        })
        
        # Test the check_health command with the --ignore-errors flag
        self.cmd('acr check-health --name {registry_name} --ignore-errors ',
            checks=[self.check('name', '{registry_name}'),
                    self.check('ignoreErrors', False),
                    self.check('vnet', None)])

        # Test the check_health command to check if blobs can be pulled from the registry
        self.cmd('acr check-health --name {registry_name} --repository {repository_name} --image {image}',
            checks=[self.check('name', '{registry_name}'),
                    self.check('repository', '{repository_name}'),
                    self.check('image', '{image}'),
                    self.check('reason', 'OK')])
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


# pylint: disable=line-too-long
class ApimProductScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_apim-', parameter_name_for_location='resource_group_location')
    @ApiManagementPreparer(parameter_name='apim_name', sku_name='Consumption')
    def test_apim_product(self, resource_group, apim_name):
        # Set variable for product operations
        product_id = self.create_random_name('apim_product-', 50)
        description = 'foo-bar'
        state = 'published'

        self.kwargs.update({
            'apim_name': apim_name,
            'product_id': product_id,
            'description': description,
            'state': state,
            'tags': ["foo=boo"]
        })

        # Delete the default Products Starter and unlimited
        self.cmd('apim product delete -n {apim_name} -g {rg} -p Starter')
        self.cmd('apim product delete -n {apim_name} -g {rg} -p Unlimited')

        # Create a single product within the APIM instance
        self.cmd('apim product create -n {apim_name} -g {rg} -p {product_id}', checks=[
            self.check('name', '{product_id}')
        ])

        self.cmd('apim product update -n {apim_name} -g {rg} -p {product_id} --description {description} --state {state}',
                 checks=[
                     self.check('description', '{description}'),
                     self.check('state', '{state}')])

        self.cmd('apim product show -n {apim_name} -g {rg} -p {product_id}', checks=[
            self.check('description', '{description}'),
            self.check('state', '{state}')
        ])

        self.cmd('apim product delete -n {apim_name} -g {rg} -p {product_id}')

        final_count = len(self.cmd('apim product list -n {apim_name} -g {rg}').get_output_in_json())
        self.assertLessEqual(final_count, 0)  # 0 used here since the default APIM products were deleted

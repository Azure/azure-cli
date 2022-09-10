# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimProductApiScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_apim_product_api-')
    @ApiManagementPreparer(sku_name='Consumption')
    def test_apim_product_api(self):
        self._test_setup()

        # add API to product
        self.cmd('apim product api create -g {rg} -n {apim} -p {product_id} -a {api_id}')

        product_api_count = len(self.cmd('apim product api list -g {rg} -n {apim} --product-id {product_id}').get_output_in_json())
        self.assertEqual(1, product_api_count)

        # check API exists in product
        self.cmd('apim product api check -g {rg} -n {apim} --product-id {product_id} --api-id {api_id}', checks=[
                self.check('associated', True)])

        # delete API from product
        self.cmd('apim product api delete -g {rg} -n {apim} --product-id {product_id} --api-id {api_id}')

        product_api_count = len(self.cmd('apim product api list -g {rg} -n {apim} --product-id {product_id}').get_output_in_json())
        self.assertEqual(0, product_api_count)


    def _test_setup(self):
        self.kwargs.update({
            'api_id': self.create_random_name('api-', 10),
            'product_id': 'productid',
            'product_name': 'productname'
        })
        self.cmd('apim api create -g {rg} -n {apim} --api-id {api_id} --path /api/{api_id} --display-name {api_id}')
        self.cmd('apim product create -g {rg} -n {apim} -p {product_id} --display-name {product_name}')

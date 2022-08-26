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
        self.kwargs.update({
            'api_id': self.create_random_name('az-cli', 10),
            'product_id': 'productid',
            'product_name': 'productname'
        })

        # list APIs in a product
        initial_productapi_count = len(self.cmd('apim product api list -g {rg} -n {apim} --product-id {product_id}').get_output_in_json())

        # add API to product
        self.cmd('apim product api create -g {rg} -n {apim} --product-id {product_id} --api-id {api_id}')
        current_productapi_count = len(self.cmd('apim product api list -g {rg} -n {apim} --product-id {product_id}').get_output_in_json())
        self.assertEqual(initial_productapi_count, current_productapi_count - 1)

        # check API exists in product
        self.cmd('apim product api check -g {rg} -n {apim} --product-id {product_id} --api-id {api_id}')

        # delete API from product
        self.cmd('apim product api delete -g {rg} -n {apim} --product-id {product_id} --api-id {api_id}')
        final_productapi_count = len(self.cmd('apim product api list -g {rg} -n {apim} --product-id {product_id}').get_output_in_json())
        self.assertEqual(initial_productapi_count, final_productapi_count)

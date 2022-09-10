# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, ApiManagementPreparer)


class ApimProductScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_apim_product-')
    @ApiManagementPreparer(sku_name='Consumption')
    def test_apim_product(self):
        self.kwargs.update({
            'product_id': self.create_random_name('apim_product-', 20),
            'display_name': 'apim product',
            'description': 'product description',
            'state': 'published',
            'tags': ["foo=boo"]
        })

        self.cmd('apim product create -n {apim} -g {rg} -p {product_id} --display-name "{display_name}"', checks=[
            self.check('displayName', '{display_name}'),
            self.check('name', '{product_id}')
        ])

        self.cmd('apim product show -n {apim} -g {rg} -p {product_id}', checks=[
            self.check('state', 'notPublished')
        ])

        self.cmd('apim product update -n {apim} -g {rg} -p {product_id} --description "{description}" --state {state}',
                 checks=[
                     self.check('description', '{description}'),
                     self.check('state', '{state}')])

        self.cmd('apim product delete -n {apim} -g {rg} -p {product_id}')

        final_count = len(self.cmd('apim product list -n {apim} -g {rg}').get_output_in_json())
        self.assertLessEqual(final_count, 0)  # 0 used here since the default APIM products were deleted

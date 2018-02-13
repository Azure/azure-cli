# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from datetime import datetime
from azure.cli.testsdk import ScenarioTest, record_only


@record_only()
class AzureConsumptionServiceScenarioTest(ScenarioTest):
    def _validate_usage(self, usage, includeMeterDetails=False):
        self.assertIsNotNone(usage)
        self.assertEqual(usage['type'], 'Microsoft.Consumption/usageDetails')
        self.assertTrue(usage['id'] and usage['name'])
        self.assertTrue(usage['usageStart'] and usage['usageEnd'])
        self.assertTrue(usage['usageStart'] <= usage['usageEnd'])
        self.assertIsNotNone(usage['billingPeriodId'])
        self.assertIsNotNone(usage['instanceName'])
        self.assertIsNotNone(usage['currency'])
        self.assertIsNotNone(usage['meterId'])
        self.assertTrue(usage['pretaxCost'] and usage['usageQuantity'] and usage['billableQuantity'])
        if includeMeterDetails:
            self.assertIsNotNone(usage['meterDetails'])
            self.assertIsNotNone(usage['meterDetails']['meterName'])
        else:
            self.assertIsNone(usage['meterDetails'])

    def _validate_pricesheet(self, pricesheet, includeMeterDetails=False):
        self.assertIsNotNone(pricesheet)
        self.assertEqual(pricesheet['type'], 'Microsoft.Consumption/pricesheets')
        self.assertTrue(pricesheet['id'] and pricesheet['name'])
        self.assertIsNotNone(pricesheet['pricesheets'][0]['billingPeriodId'])
        self.assertIsNotNone(pricesheet['pricesheets'][0]['currencyCode'])
        self.assertIsNotNone(pricesheet['pricesheets'][0]['meterId'])
        self.assertIsNotNone(pricesheet['pricesheets'][0]['unitOfMeasure'])
        self.assertTrue(pricesheet['pricesheets'][0]['unitPrice'] and pricesheet['pricesheets'][0]['includedQuantity'] and pricesheet['pricesheets'][0]['partNumber'])
        if includeMeterDetails:
            self.assertIsNotNone(pricesheet['pricesheets'][0]['meterDetails'])
            self.assertIsNotNone(pricesheet['pricesheets'][0]['meterDetails']['meterName'])
        else:
            self.assertIsNone(pricesheet['pricesheets'][0]['meterDetails'])

    def test_consumption_pricesheet_billing_period(self):
        pricesheet = self.cmd('consumption pricesheet billing period get -p 20171001').get_output_in_json()
        self.assertTrue(pricesheet)
        self._validate_pricesheet(pricesheet, False)

    def test_consumption_pricesheet(self):
        pricesheet = self.cmd('consumption pricesheet get').get_output_in_json()
        self.assertTrue(pricesheet)
        self._validate_pricesheet(pricesheet, False)

    def test_consumption_usage_list(self):
        usages_list = self.cmd('consumption usage list -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_list_usages_subscription_custom_date_range(self):
        self.kwargs.update({
            'start_date': '2017-09-11T23:59:59Z',
            'end_date': '2017-09-12T03:59:59Z'
        })

        usages_list = self.cmd('consumption usage list -s {start_date} -e {end_date} -t 5').get_output_in_json()
        self.assertTrue(usages_list)


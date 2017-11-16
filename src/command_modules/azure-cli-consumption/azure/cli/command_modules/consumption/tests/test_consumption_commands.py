# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime
from azure.cli.testsdk import ScenarioTest


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

    def test_list_usages_billing_period(self):
        billing_period = '201710'
        usages_list = self.cmd('consumption usage list -p {} -t 5'.format(billing_period)).get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_list_usages_billing_period_expand(self):
        billing_period = '201710'
        usages_list = self.cmd('consumption usage list -p {} -a -m -t 5'.format(billing_period)).get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], True)

    def test_list_usages_subscription(self):
        usages_list = self.cmd('consumption usage list -t 5 -a').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_list_usages_subscription_custom_date_range(self):
        usages_list = self.cmd('consumption usage list -s 2017-10-11T23:59:59Z -e 2017-10-12T03:59:59Z').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(all((datetime.strptime(usage_date['usageEnd'], "%Y-%m-%dT%H:%M:%SZ") >= datetime.strptime('2017-10-11T23:59:59Z', "%Y-%m-%dT%H:%M:%SZ") and datetime.strptime(usage_date['usageEnd'], "%Y-%m-%dT%H:%M:%SZ") <= datetime.strptime('2017-10-12T23:59:59Z', "%Y-%m-%dT%H:%M:%SZ")) for usage_date in usages_list))

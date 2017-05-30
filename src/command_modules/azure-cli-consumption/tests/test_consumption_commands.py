# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, JMESPathCheck


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
        billing_period = '201705-1'
        usages_list = self.cmd('consumption usage list -p {} -s 2017-04-02 -t 5'.format(billing_period)).get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)
        self.assertTrue(usages_list[0]['billingPeriodId'].endswith(billing_period))

    def test_list_usages_billing_period_expand(self):
        billing_period = '201705-1'
        usages_list = self.cmd('consumption usage list -p {} -a -m -t 5'.format(billing_period)).get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], True)
        self.assertTrue(usages_list[0]['billingPeriodId'].endswith(billing_period))

    def test_list_usages_invoice(self):
        invoice_name = '201705-217089190378988'
        usages_list = self.cmd('consumption usage list -i {} -s 2017-03-03 -e 2017-04-04 -m -t 5'.format(invoice_name)).get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], True)
        self.assertTrue(usages_list[0]['invoiceId'].endswith(invoice_name))

    def test_list_usages_subscription(self):
        usages_list = self.cmd('consumption usage list -e 2017-04-01 -t 5 -a').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

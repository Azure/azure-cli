# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long
from datetime import datetime
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
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

    def _validate_reservation_summaries(self, reservationsummaries):
        self.assertIsNotNone(reservationsummaries)
        self.assertTrue(reservationsummaries['id'])
        self.assertTrue(reservationsummaries['name'])
        self.assertEqual(reservationsummaries['type'], 'Microsoft.Consumption/reservationSummaries')
        self.assertTrue(reservationsummaries['avgUtilizationPercentage'])
        self.assertTrue(reservationsummaries['maxUtilizationPercentage'])
        self.assertTrue(reservationsummaries['minUtilizationPercentage'])
        self.assertTrue(reservationsummaries['reservationId'])
        self.assertTrue(reservationsummaries['reservationOrderId'])
        self.assertTrue(reservationsummaries['reservedHours'])
        self.assertTrue(reservationsummaries['skuName'])
        self.assertTrue(reservationsummaries['usageDate'])
        self.assertTrue(reservationsummaries['usedHours'])

    def _validate_reservation_details(self, reservationdetails):
        self.assertIsNotNone(reservationdetails)
        self.assertTrue(reservationdetails['id'])
        self.assertTrue(reservationdetails['name'])
        self.assertEqual(reservationdetails['type'], 'Microsoft.Consumption/reservationDetails')
        self.assertTrue(reservationdetails['instanceId'])
        self.assertTrue(reservationdetails['reservationId'])
        self.assertTrue(reservationdetails['reservationOrderId'])
        self.assertTrue(reservationdetails['reservedHours'])
        self.assertTrue(reservationdetails['skuName'])
        self.assertTrue(reservationdetails['totalReservedQuantity'])
        self.assertTrue(reservationdetails['usageDate'])
        self.assertTrue(reservationdetails['usedHours'])

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

    def _validate_marketplace(self, marketplace, billing_period_id=None):
        self.assertIsNotNone(marketplace)
        self.assertTrue(marketplace['id'])
        self.assertTrue(marketplace['name'])
        self.assertIsNotNone(marketplace['type'])
        self.assertIsNotNone(marketplace['instanceName'])
        self.assertIsNotNone(marketplace['instanceId'])
        self.assertIsNotNone(marketplace['currency'])
        self.assertIsNotNone(marketplace['pretaxCost'])
        self.assertIsNotNone(marketplace['isEstimated'])
        self.assertIsNotNone(marketplace['orderNumber'])
        if billing_period_id:
            self.assertTrue(billing_period_id in marketplace['billingPeriodId'])
        else:
            self.assertIsNotNone(marketplace['billingPeriodId'])

    def _validate_budget(self, output_budget):
        self.assertIsNotNone(output_budget)
        self.assertTrue(output_budget['amount'])
        self.assertTrue(output_budget['timeGrain'])
        self.assertTrue(output_budget['timePeriod'])
        self.assertTrue(output_budget['name'])

    @AllowLargeResponse()
    def test_consumption_pricesheet_billing_period(self):
        pricesheet = self.cmd('consumption pricesheet show --billing-period-name 20171001').get_output_in_json()
        self.assertTrue(pricesheet)
        self._validate_pricesheet(pricesheet, False)

    @AllowLargeResponse()
    def test_consumption_pricesheet(self):
        pricesheet = self.cmd('consumption pricesheet show').get_output_in_json()
        self.assertTrue(pricesheet)
        self._validate_pricesheet(pricesheet, False)

    def test_consumption_usage_list(self):
        usages_list = self.cmd('consumption usage list -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_consumption_usage_list_properties(self):
        usages_list = self.cmd('consumption usage list -t 5 -a').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_consumption_usage_by_billing_period(self):
        usages_list = self.cmd('consumption usage list -p 201710 -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_consumption_usage_list_expand(self):
        usages_list = self.cmd('consumption usage list -a -m -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], True)

    def test_consumption_usage_by_billing_period_expand(self):
        usages_list = self.cmd('consumption usage list -p 201710 -a -m -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], True)

    def test_list_usages_subscription_custom_date_range(self):
        self.kwargs.update({
            'start_date': '2017-10-11T23:59:59Z',
            'end_date': '2017-10-12T03:59:59Z'
        })

        usages_list = self.cmd('consumption usage list -s {start_date} -e {end_date} -t 5').get_output_in_json()
        self.assertTrue(usages_list)

        def usage_date_check(usage_date):
            check_after = datetime.strptime(usage_date['usageEnd'], "%Y-%m-%dT%H:%M:%SZ") >= \
                datetime.strptime('2017-10-11T23:59:59Z', "%Y-%m-%dT%H:%M:%SZ")
            check_before = datetime.strptime(usage_date['usageEnd'], "%Y-%m-%dT%H:%M:%SZ") <= \
                datetime.strptime('2017-10-12T23:59:59Z', "%Y-%m-%dT%H:%M:%SZ")
            return check_after and check_before
        self.assertTrue(all(usage_date_check(usage_date) for usage_date in usages_list))

    def test_list_reservations_summaries_monthly(self):
        reservations_summaries_monthly_list = self.cmd('consumption reservation summary list --grain "monthly" --reservation-order-id ca69259e-bd4f-45c3-bf28-3f353f9cce9b').get_output_in_json()
        self.assertTrue(reservations_summaries_monthly_list)
        self._validate_reservation_summaries(reservations_summaries_monthly_list[0])

    def test_list_reservations_summaries_monthly_with_reservationid(self):
        reservations_summaries_monthly_withreservationid_list = self.cmd('consumption reservation summary list --grain "monthly" --reservation-order-id ca69259e-bd4f-45c3-bf28-3f353f9cce9b --reservation-id f37f4b70-52ba-4344-a8bd-28abfd21d640').get_output_in_json()
        self.assertTrue(reservations_summaries_monthly_withreservationid_list)
        self._validate_reservation_summaries(reservations_summaries_monthly_withreservationid_list[0])

    def test_list_reservations_summaries_daily(self):
        reservations_summaries_daily_list = self.cmd('consumption reservation summary list --grain "daily" --reservation-order-id ca69259e-bd4f-45c3-bf28-3f353f9cce9b -s "2017-12-01" -e "2017-12-07"').get_output_in_json()
        self.assertTrue(reservations_summaries_daily_list)
        self._validate_reservation_summaries(reservations_summaries_daily_list[0])

    def test_list_reservations_summaries_daily_with_reservationid(self):
        reservations_summaries_daily_withreservationid_list = self.cmd('consumption reservation summary list --grain "daily" --reservation-order-id ca69259e-bd4f-45c3-bf28-3f353f9cce9b --reservation-id f37f4b70-52ba-4344-a8bd-28abfd21d640 -s "2017-12-01" -e "2017-12-07"').get_output_in_json()
        self.assertTrue(reservations_summaries_daily_withreservationid_list)
        self._validate_reservation_summaries(reservations_summaries_daily_withreservationid_list[0])

    def test_list_reservations_details(self):
        reservations_details_list = self.cmd('consumption reservation detail list --reservation-order-id ca69259e-bd4f-45c3-bf28-3f353f9cce9b -s "2017-12-01" -e "2017-12-07"').get_output_in_json()
        self.assertTrue(reservations_details_list)
        self._validate_reservation_details(reservations_details_list[0])

    def test_list_reservations_details_with_reservationid(self):
        reservations_details_list = self.cmd('consumption reservation detail list --reservation-order-id ca69259e-bd4f-45c3-bf28-3f353f9cce9b --reservation-id f37f4b70-52ba-4344-a8bd-28abfd21d640 -s "2017-12-01" -e "2017-12-07"').get_output_in_json()
        self.assertTrue(reservations_details_list)
        self._validate_reservation_details(reservations_details_list[0])

    def test_consumption_marketplace_list(self):
        marketplace_list = self.cmd('consumption marketplace list').get_output_in_json()
        self.assertTrue(marketplace_list)
        all(self._validate_marketplace(marketplace_item) for marketplace_item in marketplace_list)

    def test_consumption_marketplace_list_billing_period_filter(self):
        marketplace_list = self.cmd('consumption marketplace list --billing-period-name 201804-1 --top 1').get_output_in_json()
        self.assertTrue(marketplace_list)
        self.assertTrue(len(marketplace_list) == 1)
        all(self._validate_marketplace(marketplace_item) for marketplace_item in marketplace_list)

    def test_consumption_marketplace_list_billing_period(self):
        marketplace_list = self.cmd('consumption marketplace list --billing-period-name 201804-1').get_output_in_json()
        self.assertTrue(marketplace_list)
        all(self._validate_marketplace(marketplace_item, '201804-1') for marketplace_item in marketplace_list)

    def test_consumption_budget_usage_create(self):
        output_budget = self.cmd('az consumption budget create --budget-name usagetypebudget1 --amount 20 -s 2018-02-01 -e 2018-10-01 --time-grain annually --category usage --meter-filter 0dfadad2-6e4f-4078-85e1-90c230d4d482').get_output_in_json()
        self.assertTrue(output_budget)
        self._validate_budget(output_budget)

    def test_consumption_budget_create(self):
        output_budget = self.cmd('consumption budget create --budget-name "costbudget" --category "cost" --amount 100.0 -s "2018-02-01" -e "2018-10-01" --time-grain "monthly"').get_output_in_json()
        self.assertTrue(output_budget)
        self._validate_budget(output_budget)

    def test_consumption_budget_delete(self):
        output = self.cmd('consumption budget delete --budget-name "costbudget"')
        self.assertTrue(output)

    def test_consumption_budget_show(self):
        output_budget = self.cmd('consumption budget show --budget-name "havTest01"').get_output_in_json()
        self.assertTrue(output_budget)
        self._validate_budget(output_budget)

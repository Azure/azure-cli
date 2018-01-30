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
#TODO
    def _validate_pricesheet(self, pricesheet, includeMeterDetails = false){
        self.assertIsNotNone(pricesheet)
        self.assertEqual(pricesheet['type'], 'Microsoft.Consumption/pricesheets')
        self.assertEqual(pricesheet['name'], 'default')
        self.assertTrue(pricesheet['id'])
        self.assertIsNotNone(pricesheet['billingPeriodId'])
        self.assertIsNotNone(pricesheet['meterId'])
        self.assertIsNotNone(pricesheet['meterName'])
        self.assertIsNotNone(pricesheet['unitOfMeasure'])
        self.assertIsNotNone(pricesheet['includedQuantity'])
        self.assertIsNotNone(pricesheet['partNumber'])
        self.assertIsNotNone(pricesheet['unitPrice'])
        self.assertIsNotNone(pricesheet['currencyCode'])

        if includeMeterDetails:
            self.assertIsNotNone(pricesheet['meterDetails'])
            self.assertIsNotNone(pricesheet['meterDetails']['meterName'])
            self.assertIsNotNone(pricesheet['meterDetails']['meterCategory'])
            self.assertIsNotNone(pricesheet['meterDetails']['meterLocation'])
            self.assertIsNotNone(pricesheet['meterDetails']['totalIncludedQuantity'])
            self.assertIsNotNone(pricesheet['meterDetails']['pretaxStandardRate'])
        else:
            self.assertIsNone(pricesheet['meterDetails'])

    def test_list_usages_billing_period(self):
        self.kwargs.update({
            'billing_period': '201710'
        })

        usages_list = self.cmd('consumption usage list -p {billing_period} -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_list_usages_billing_period_expand(self):
        self.kwargs.update({
            'billing_period': '201710'
        })

        usages_list = self.cmd('consumption usage list -p {billing_period} -a -m -t 5').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], True)

    def test_list_usages_subscription(self):
        usages_list = self.cmd('consumption usage list -t 5 -a').get_output_in_json()
        self.assertTrue(usages_list)
        self.assertTrue(len(usages_list) <= 5)
        self._validate_usage(usages_list[0], False)

    def test_list_usages_subscription_custom_date_range(self):
        self.kwargs.update({
            'start_date': '2017-10-11T23:59:59Z',
            'end_date': '2017-10-12T03:59:59Z'
        })

        usages_list = self.cmd('consumption usage list -s {start_date} -e {end_date}').get_output_in_json()
        self.assertTrue(usages_list)

        def usage_date_check(usage_date):
            check_after = datetime.strptime(usage_date['usageEnd'], "%Y-%m-%dT%H:%M:%SZ") >= \
                datetime.strptime('2017-10-11T23:59:59Z', "%Y-%m-%dT%H:%M:%SZ")
            check_before = datetime.strptime(usage_date['usageEnd'], "%Y-%m-%dT%H:%M:%SZ") <= \
                datetime.strptime('2017-10-12T23:59:59Z', "%Y-%m-%dT%H:%M:%SZ")
            return check_after and check_before
        self.assertTrue(all(usage_date_check(usage_date) for usage_date in usages_list))

    def test_list_reservations_summaries_monthly(self):
        reservations_summaries_monthly_list = self.cmd('consumption reservations summaries list -g ''monthly'' -r ca69259e-bd4f-45c3-bf28-3f353f9cce9b').get_output_in_json()
        self.assertTrue(reservations_summaries_monthly_list)
        self._validate_reservation_summaries(reservations_summaries_monthly_list[0])

    def test_list_reservations_summaries_monthly_withreservationid(self):
        reservations_summaries_monthly_withreservationid_list = self.cmd('consumption reservations summaries list -g ''monthly'' -r ca69259e-bd4f-45c3-bf28-3f353f9cce9b -i f37f4b70-52ba-4344-a8bd-28abfd21d640').get_output_in_json()
        self.assertTrue(reservations_summaries_monthly_withreservationid_list)
        self._validate_reservation_summaries(reservations_summaries_monthly_withreservationid_list[0])

    def test_list_reservations_summaries_daily(self):
        reservations_summaries_daily_list = self.cmd('consumption reservations summaries list -g ''daily'' -r ca69259e-bd4f-45c3-bf28-3f353f9cce9b -s ''2017-12-01'' -e ''2017-12-07''').get_output_in_json()
        self.assertTrue(reservations_summaries_daily_list)
        self._validate_reservation_summaries(reservations_summaries_daily_list[0])

    def test_list_reservations_summaries_daily_withreservationid(self):
        reservations_summaries_daily_withreservationid_list = self.cmd('consumption reservations summaries list -g ''daily'' -r ca69259e-bd4f-45c3-bf28-3f353f9cce9b -i f37f4b70-52ba-4344-a8bd-28abfd21d640 -s ''2017-12-01'' -e ''2017-12-07''').get_output_in_json()
        self.assertTrue(reservations_summaries_daily_withreservationid_list)
        self._validate_reservation_summaries(reservations_summaries_daily_withreservationid_list[0])

    def test_list_reservations_details(self):
        reservations_details_list = self.cmd('consumption reservations details list -r ca69259e-bd4f-45c3-bf28-3f353f9cce9b -s ''2017-12-01'' -e ''2017-12-07''').get_output_in_json()
        self.assertTrue(reservations_details_list)
        self._validate_reservation_details(reservations_details_list[0])

    def test_list_reservations_details_withreservationid(self):
        reservations_details_list = self.cmd('consumption reservations details list -r ca69259e-bd4f-45c3-bf28-3f353f9cce9b -i f37f4b70-52ba-4344-a8bd-28abfd21d640 -s ''2017-12-01'' -e ''2017-12-07''').get_output_in_json()
        self.assertTrue(reservations_details_list)
        self._validate_reservation_details(reservations_details_list[0])

#TODO
    def test_pricesheet_with_subscriptionid(self):
        pricesheet_output = self.cmd('consumption price sheet ....').get_output_in_json()
        #self.assertTrue(pricesheet_get)
        self._validate_pricesheet(pricesheet_output[0], false)
#TODO
    def test_pricesheet_with_subscriptionid_with_meter_details(self):
        pricesheet_output = self.cmd('consumption price sheet ....').get_output_in_json()
        #self.assertTrue(pricesheet_get)
        self._validate_pricesheet(pricesheet_output[0], true)
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only


class AzureBillingServiceScenarioTest(ScenarioTest):
    def _validate_invoice(self, invoice, include_url=False):
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice['type'], 'Microsoft.Billing/invoices')
        self.assertTrue(invoice['id'] and invoice['name'])
        self.assertTrue(invoice['invoicePeriodStartDate'] and invoice['invoicePeriodEndDate'])
        self.assertTrue(invoice['invoicePeriodStartDate'] <= invoice['invoicePeriodEndDate'])
        self.assertIsNotNone(invoice['billingPeriodIds'])
        if include_url:
            self.assertIsNotNone(invoice['downloadUrl'])
        else:
            self.assertIsNone(invoice['downloadUrl'])

    @record_only()
    def test_list_invoices_no_url(self):
        # list
        invoices_list = self.cmd('billing invoice list').get_output_in_json()
        self.assertTrue(invoices_list)
        self._validate_invoice(invoices_list[0], False)
        # get
        self.kwargs.update({
            'invoice_name': invoices_list[0]['name']
        })
        invoice = self.cmd('billing invoice show -n {invoice_name}').get_output_in_json()
        self._validate_invoice(invoice, True)

    @record_only()
    def test_list_invoices_with_url(self):
        invoices_list = self.cmd('billing invoice list -d').get_output_in_json()
        self.assertTrue(invoices_list)
        self._validate_invoice(invoices_list[0], True)

    @record_only()
    def test_get_latest_invoice(self):
        create_cmd = 'billing invoice show'
        invoice = self.cmd(create_cmd).get_output_in_json()
        self._validate_invoice(invoice, True)

    @record_only()
    def test_list_billing_periods(self):
        # list
        periods_list = self.cmd('billing period list').get_output_in_json()
        self.assertTrue(periods_list)
        # get
        period_name = periods_list[0]['name']
        self.kwargs.update({
            'period_name': period_name
        })
        self.cmd('billing period show -n {period_name}', checks=self.check('name', period_name))

    @record_only()
    def test_list_enrollment_accounts(self):
        # list
        enrollment_accounts_list = self.cmd('billing enrollment-account list').get_output_in_json()
        self.assertTrue(enrollment_accounts_list)
        # get
        enrollment_account_name = enrollment_accounts_list[0]['name']
        self.kwargs.update({
            'enrollment_account_name': enrollment_account_name
        })
        self.cmd('billing enrollment-account show -n {enrollment_account_name}', checks=self.check('name', enrollment_account_name))

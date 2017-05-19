# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck)

class AzureBillingServiceScenarioTest(ScenarioTest):
    def _validate_invoice(self, invoice, includeUrl=False):
        assert invoice
        assert invoice['type']=='Microsoft.Billing/invoices'
        assert invoice['id'] and invoice['name'] 
        assert invoice['invoicePeriodStartDate'] and invoice['invoicePeriodEndDate'] 
        assert invoice['invoicePeriodStartDate'] <= invoice['invoicePeriodEndDate'] 
        assert invoice['billingPeriodIds'] 
        if includeUrl:
            assert invoice['downloadUrl']
        else:
            assert not 'downloadUrl' in invoice

    def test_list_invoices_no_url(self):
        #list
        invoices_list = self.cmd('billing invoice list').get_output_in_json()
        assert len(invoices_list) > 0
        self._validate_invoice(invoices_list[0], False)
        #get
        invoice_name = invoices_list[0]['name']
        invoice = self.cmd('billing invoice show -n {}'.format(invoice_name)).get_output_in_json()
        self._validate_invoice(invoice, True)

    def test_list_invoices_with_url(self):
        invoices_list = self.cmd('billing invoice list -g').get_output_in_json()
        assert len(invoices_list) > 0
        self._validate_invoice(invoices_list[0], True)

    def test_get_latest_invoice(self):
        create_cmd = 'billing invoice show-latest'
        invoice = self.cmd(create_cmd).get_output_in_json()
        self._validate_invoice(invoice, True)

    def test_list_billing_periods(self):
        #list
        periods_list = self.cmd('billing period list').get_output_in_json()
        assert len(periods_list) > 0
        #get
        period_name = periods_list[0]['name']
        period = self.cmd('billing period show -n {}'.format(period_name),
                 checks=JMESPathCheck('name', period_name))
    
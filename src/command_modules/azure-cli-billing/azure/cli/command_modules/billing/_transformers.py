# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict


def transform_invoice_output(result):
    new_entry = OrderedDict()
    new_entry['id'] = result.id
    new_entry['name'] = result.name
    new_entry['type'] = result.type
    new_entry['invoicePeriodStartDate'] = result.invoice_period_start_date.strftime("%Y-%m-%d")
    new_entry['invoicePeriodEndDate'] = result.invoice_period_end_date.strftime("%Y-%m-%d")
    if result.download_url:
        new_entry['downloadUrl'] = result.download_url
    if result.billing_period_ids:
        new_entry['billingPeriodIds'] = result.billing_period_ids
    return new_entry


def transform_invoice_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_invoice_output(item))
    return new_result


def transform_billing_period_output(result):
    new_entry = OrderedDict()
    new_entry['id'] = result.id
    new_entry['name'] = result.name
    new_entry['type'] = result.type
    new_entry['billingPeriodStartDate'] = result.billing_period_start_date.strftime("%Y-%m-%d")
    new_entry['billingPeriodEndDate'] = result.billing_period_end_date.strftime("%Y-%m-%d")
    if result.invoice_ids:
        new_entry['invoiceIds'] = result.invoice_ids
    return new_entry


def transform_billing_period_list_output(result):
    new_result = []
    for item in result:
        new_result.append(transform_billing_period_output(item))
    return new_result

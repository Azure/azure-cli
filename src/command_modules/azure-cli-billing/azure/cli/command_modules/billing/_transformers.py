# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def transform_invoice_output(result):
    result.invoice_period_start_date = result.invoice_period_start_date.strftime("%Y-%m-%d")
    result.invoice_period_end_date = result.invoice_period_end_date.strftime("%Y-%m-%d")
    return result


def transform_invoice_list_output(result):
    return [transform_invoice_output(item) for item in result]


def transform_billing_period_output(result):
    result.billing_period_start_date = result.billing_period_start_date.strftime("%Y-%m-%d")
    result.billing_period_end_date = result.billing_period_end_date.strftime("%Y-%m-%d")
    return result


def transform_billing_period_list_output(result):
    return [transform_billing_period_output(item) for item in result]

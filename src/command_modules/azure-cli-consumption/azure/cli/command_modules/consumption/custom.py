# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from datetime import timedelta
from azure.cli.command_modules.consumption._client_factory import cf_consumption


def cli_consumption_list_usage(client, invoice_name=None, billing_period_name=None, top=None, include_additional_properties=False, include_meter_details=False, start_date=None, end_date=None):
    """List all usage details of the subscription"""
    if include_additional_properties and include_meter_details:
        expand = 'additionalProperties,meterDetails'
    elif include_additional_properties:
        expand = 'additionalProperties'
    elif include_meter_details:
        expand = 'meterDetails'
    else:
        expand = None

    if billing_period_name:
        scope = "/subscriptions/{}/providers/Microsoft.Billing/billingPeriods/{}".format(cf_consumption().config.subscription_id, billing_period_name)
    elif invoice_name:
        scope = "/subscriptions/{}/providers/Microsoft.Billing/invoices/{}".format(cf_consumption().config.subscription_id, invoice_name)
    else:
        scope = "/subscriptions/{}".format(cf_consumption().config.subscription_id)

    filter_from = None
    filter_to = None
    filter_expression = None
    if start_date:
        # pylint: disable=no-member
        from_time = start_date + timedelta(days=1) - timedelta(seconds=1)
        filter_from = "usageEnd ge {}".format(from_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_expression = filter_from
    if end_date:
        # pylint: disable=no-member
        to_time = end_date + timedelta(days=1) - timedelta(seconds=1)
        filter_to = "usageEnd le {}".format(to_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_expression = filter_to
    if filter_from and filter_to:
        filter_expression = "{} and {}".format(filter_from, filter_to)

    return list(client.list(scope, expand=expand, filter=filter_expression, top=top))

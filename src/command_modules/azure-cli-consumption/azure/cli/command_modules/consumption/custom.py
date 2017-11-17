# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.command_modules.consumption._client_factory import cf_consumption


def cli_consumption_list_usage(client, billing_period_name=None, top=None, include_additional_properties=False, include_meter_details=False, start_date=None, end_date=None):
    """List all usage details of the subscription"""
    if include_additional_properties and include_meter_details:
        expand = 'properties/additionalProperties,properties/meterDetails'
    elif include_additional_properties:
        expand = 'properties/additionalProperties'
    elif include_meter_details:
        expand = 'properties/meterDetails'
    else:
        expand = None

    if billing_period_name:
        scope = "/subscriptions/{}/providers/Microsoft.Billing/billingPeriods/{}".format(cf_consumption().config.subscription_id, billing_period_name)
    else:
        scope = "/subscriptions/{}".format(cf_consumption().config.subscription_id)

    filter_from = None
    filter_to = None
    filter_expression = None
    if start_date and end_date:
        filter_from = "properties/usageEnd ge \'{}\'".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_to = "properties/usageEnd le \'{}\'".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_expression = "{} and {}".format(filter_from, filter_to)
    if top:
        pages = client.list(scope, expand=expand, filter=filter_expression, top=top)
        return list(pages.advance_page())
    return list(client.list(scope, expand=expand, filter=filter_expression))

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def cli_consumption_list_usage(client, billing_period_name=None, top=None, include_additional_properties=False, include_meter_details=False, start_date=None, end_date=None):
    if include_additional_properties and include_meter_details:
        expand = 'properties/additionalProperties,properties/meterDetails'
    elif include_additional_properties:
        expand = 'properties/additionalProperties'
    elif include_meter_details:
        expand = 'properties/meterDetails'
    else:
        expand = None

    filter_from = None
    filter_to = None
    filter_expression = None
    if start_date and end_date:
        filter_from = "properties/usageEnd ge \'{}\'".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_to = "properties/usageEnd le \'{}\'".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_expression = "{} and {}".format(filter_from, filter_to)

    if billing_period_name and top:
        return list(client.list_by_billing_period(billing_period_name, expand=expand, filter=filter_expression, top=top).advance_page())
    elif billing_period_name and not top:
        return list(client.list_by_billing_period(expand=expand, filter=filter_expression))
    elif not billing_period_name and top:
        return list(client.list(expand=expand, filter=filter_expression, top=top).advance_page())
    return client.list(expand=expand, filter=filter_expression)


def cli_consumption_list_reservation_summary(client, grain, reservation_order_id, reservation_id=None, start_date=None, end_date=None):
    filter_from = None
    filter_to = None
    filter_expression = None
    if start_date and end_date:
        filter_from = "properties/UsageDate ge {}".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_to = "properties/UsageDate le {}".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_expression = "{} and {}".format(filter_from, filter_to)
        if reservation_id:
            return list(client.list_by_reservation_order_and_reservation(reservation_order_id, reservation_id, grain=grain, filter=filter_expression))
        return list(client.list_by_reservation_order(reservation_order_id, grain=grain, filter=filter_expression))

    if reservation_id:
        return list(client.list_by_reservation_order_and_reservation(reservation_order_id, reservation_id, grain=grain))
    return list(client.list_by_reservation_order(reservation_order_id, grain=grain))


def cli_consumption_list_reservation_detail(client, reservation_order_id, start_date, end_date, reservation_id=None):
    filter_from = None
    filter_to = None
    filter_expression = None
    filter_from = "properties/UsageDate ge {}".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    filter_to = "properties/UsageDate le {}".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    filter_expression = "{} and {}".format(filter_from, filter_to)
    if reservation_id:
        return list(client.list_by_reservation_order_and_reservation(reservation_order_id, reservation_id, filter=filter_expression))
    return list(client.list_by_reservation_order(reservation_order_id, filter=filter_expression))


def cli_consumption_list_pricesheet_show(client, billing_period_name=None, include_meter_details=False):
    if include_meter_details:
        expand_properties = 'properties/meterDetails'
    else:
        expand_properties = None

    if billing_period_name:
        return client.get_by_billing_period(billing_period_name, expand=expand_properties)
    return client.get(expand=expand_properties)


def cli_consumption_list_marketplace(client, billing_period_name=None, start_date=None, end_date=None, top=None):
    filter_from = None
    filter_to = None
    filter_expression = None
    if start_date and end_date:
        filter_from = "properties/usageEnd ge \'{}\'".format(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_to = "properties/usageEnd le \'{}\'".format(end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
        filter_expression = "{} and {}".format(filter_from, filter_to)

    if billing_period_name and top:
        return list(client.list_by_billing_period(billing_period_name, filter=filter_expression, top=top).advance_page())
    elif billing_period_name and not top:
        return list(client.list_by_billing_period(billing_period_name, filter=filter_expression))
    elif not billing_period_name and top:
        return list(client.list(filter=filter_expression, top=top).advance_page())
    return client.list(filter=filter_expression)
